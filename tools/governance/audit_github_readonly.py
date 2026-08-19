#!/usr/bin/env python3
"""Read-only Oteryn governance drift audit.

Offline mode validates the desired-state contract. Live mode reads GitHub REST only;
it never mutates settings. A caller must provide GH_TOKEN or GITHUB_TOKEN.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DESIRED_PATH = ROOT / "ecosystem" / "governance-desired-state.json"
API = "https://api.github.com"
HISTORICAL_PREFIXES = (
    "docs/evidence/",
    "docs/agents/tasks/archive/",
    "docs/migration/",
    "docs/architecture/adr/",
)
HISTORICAL_FILES = {"ecosystem/repositories.json"}


def load_desired() -> dict:
    data = json.loads(DESIRED_PATH.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise SystemExit("governance desired-state schema_version must be 1")
    repos = data.get("permanent_repositories")
    if not isinstance(repos, list) or len(repos) != 4:
        raise SystemExit("exactly four permanent repositories are required")
    coordinates = [item.get("repository") for item in repos]
    expected = {
        "Oteryn/Oteryn",
        "Oteryn/Oteryn-Game",
        "Oteryn/Oteryn-Platform",
        "Oteryn/Oteryn-Atlas",
    }
    if set(coordinates) != expected or len(coordinates) != len(expected):
        raise SystemExit(f"unexpected permanent repository set: {coordinates}")
    for item in repos:
        if not isinstance(item.get("repository_id"), int):
            raise SystemExit(f"missing repository_id: {item}")
        if item.get("gate_mode") not in {"stable", "transition"}:
            raise SystemExit(f"invalid gate_mode: {item}")
        if item["gate_mode"] == "stable" and not item.get("required_gate"):
            raise SystemExit(f"stable repository lacks required_gate: {item}")
    return data


class Audit:
    def __init__(self, token: str) -> None:
        self.token = token
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def api(self, path: str, *, allow_404: bool = False):
        req = urllib.request.Request(
            API + path,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "oteryn-governance-readonly-audit",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            if allow_404 and exc.code == 404:
                return None
            raise RuntimeError(f"GET {path} -> HTTP {exc.code}") from exc
        return json.loads(raw) if raw else None

    def check(self, condition: bool, message: str) -> None:
        if not condition:
            self.errors.append(message)

    def required_contexts(self, repo: str) -> set[str]:
        contexts: set[str] = set()
        rulesets = self.api(f"/repos/{repo}/rulesets") or []
        for summary in rulesets:
            if summary.get("enforcement") != "active":
                continue
            detail = self.api(f"/repos/{repo}/rulesets/{summary['id']}")
            for rule in detail.get("rules", []):
                if rule.get("type") != "required_status_checks":
                    continue
                for check in rule.get("parameters", {}).get("required_status_checks", []):
                    context = check.get("context")
                    if context:
                        contexts.add(context)
        protection = self.api(
            f"/repos/{repo}/branches/main/protection/required_status_checks",
            allow_404=True,
        )
        if protection:
            contexts.update(protection.get("contexts", []))
            contexts.update(c.get("context") for c in protection.get("checks", []) if c.get("context"))
        return contexts

    def latest_check_names(self, repo: str) -> set[str]:
        pulls = self.api(f"/repos/{repo}/pulls?state=all&sort=updated&direction=desc&per_page=20") or []
        for pr in pulls:
            head = pr.get("head", {})
            head_repo = (head.get("repo") or {}).get("full_name")
            if head_repo != repo:
                continue
            sha = head.get("sha")
            if not sha:
                continue
            runs = self.api(f"/repos/{repo}/commits/{sha}/check-runs?per_page=100") or {}
            return {run.get("name") for run in runs.get("check_runs", []) if run.get("name")}
        return set()

    def file_exists(self, repo: str, path: str) -> bool:
        quoted = "/".join(urllib.parse.quote(part, safe="") for part in path.split("/"))
        return self.api(f"/repos/{repo}/contents/{quoted}", allow_404=True) is not None

    def audit_repo(self, wanted: dict) -> None:
        repo = wanted["repository"]
        live = self.api(f"/repos/{repo}")
        self.check(live.get("full_name") == repo, f"{repo}: canonical coordinate drift")
        self.check(live.get("id") == wanted["repository_id"], f"{repo}: repository ID drift")
        self.check(live.get("default_branch") == "main", f"{repo}: default branch is not main")
        self.check(not live.get("archived"), f"{repo}: permanent repository unexpectedly archived")
        self.check(bool(live.get("allow_squash_merge")), f"{repo}: squash merge disabled")
        if wanted.get("squash_only"):
            self.check(not live.get("allow_merge_commit"), f"{repo}: merge commits unexpectedly enabled")
            self.check(not live.get("allow_rebase_merge"), f"{repo}: rebase merge unexpectedly enabled")
        if wanted.get("delete_branch_on_merge"):
            self.check(bool(live.get("delete_branch_on_merge")), f"{repo}: merged branch auto-delete disabled")

        branch = self.api(f"/repos/{repo}/branches/main")
        self.check(bool(branch.get("protected")) == bool(wanted.get("main_protected")), f"{repo}: main protection drift")
        required = self.required_contexts(repo)
        if wanted["gate_mode"] == "stable":
            self.check(wanted["required_gate"] in required, f"{repo}: stable required gate missing: {wanted['required_gate']}")
        else:
            expected = set(wanted.get("required_checks") or [wanted.get("required_gate")]) - {None}
            self.check(expected <= required, f"{repo}: transition required checks drift: expected {sorted(expected)}, got {sorted(required)}")

        emitted = self.latest_check_names(repo)
        gate_to_observe = wanted.get("required_gate")
        if gate_to_observe:
            self.check(gate_to_observe in emitted, f"{repo}: required gate not emitted on latest representative internal PR head")
        elif wanted.get("required_checks"):
            self.check(set(wanted["required_checks"]) <= emitted, f"{repo}: transition checks not emitted on latest representative internal PR head")

        sec = live.get("security_and_analysis") or {}
        expected_sec = wanted.get("security") or {}
        mapping = {
            "secret_scanning": "secret_scanning",
            "push_protection": "secret_scanning_push_protection",
            "dependabot_security_updates": "dependabot_security_updates",
        }
        for key, api_key in mapping.items():
            if expected_sec.get(key):
                self.check((sec.get(api_key) or {}).get("status") == "enabled", f"{repo}: security baseline missing {key}")
        for path in ("SECURITY.md", ".github/CODEOWNERS"):
            self.check(self.file_exists(repo, path), f"{repo}: missing {path}")

        permissions = self.api(f"/repos/{repo}/actions/permissions")
        if permissions.get("allowed_actions") == "all":
            self.warnings.append(f"{repo}: Actions policy remains broad (allowed_actions=all)")

    def coordinate_scan(self, desired: dict) -> None:
        policy = desired.get("mutable_coordinate_policy") or {}
        needles = list(policy.get("forbidden") or []) + list(policy.get("historical_reference_only") or [])
        for repo_item in desired["permanent_repositories"]:
            repo = repo_item["repository"]
            for needle in needles:
                q = urllib.parse.quote_plus(f'"{needle}" repo:{repo}')
                result = self.api(f"/search/code?q={q}&per_page=100") or {}
                for item in result.get("items", []):
                    path = item.get("path", "")
                    historical = path in HISTORICAL_FILES or path.startswith(HISTORICAL_PREFIXES)
                    if needle in policy.get("forbidden", []) and not historical:
                        self.errors.append(f"{repo}: stale mutable coordinate {needle} in {path}")
                    elif needle in policy.get("historical_reference_only", []) and not historical:
                        self.warnings.append(f"{repo}: legacy coordinate outside historical path: {needle} in {path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true", help="validate desired-state only")
    parser.add_argument("--scan-coordinates", action="store_true", help="also query GitHub code search")
    args = parser.parse_args()
    desired = load_desired()
    if args.offline:
        print(f"offline desired-state validation PASS: {len(desired['permanent_repositories'])} permanent repositories")
        return 0
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("UNKNOWN: live audit requires GH_TOKEN or GITHUB_TOKEN", file=sys.stderr)
        return 2
    audit = Audit(token)
    try:
        for repo in desired["permanent_repositories"]:
            audit.audit_repo(repo)
        if args.scan_coordinates:
            audit.coordinate_scan(desired)
    except RuntimeError as exc:
        print(f"UNKNOWN: {exc}", file=sys.stderr)
        return 2
    for warning in audit.warnings:
        print(f"WARN: {warning}")
    for error in audit.errors:
        print(f"FAIL: {error}")
    if audit.errors:
        return 1
    print(f"PASS: live governance audit; warnings={len(audit.warnings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())