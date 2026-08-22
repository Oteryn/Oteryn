#!/usr/bin/env python3
"""Read-only Oteryn governance drift audit.

Offline mode validates the desired-state contract. Live mode reads GitHub REST only;
it never mutates settings. A caller must provide GH_TOKEN or GITHUB_TOKEN.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
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
    "docs/recovery/",
)
HISTORICAL_FILES = {"ecosystem/repositories.json"}
POLICY_DECLARATION_FILES = {"ecosystem/governance-desired-state.json"}
WORKFLOW_RUN_RE = re.compile(r"^https://github\.com/[^/]+/[^/]+/actions/runs/(\d+)(?:/|$)")


def expected_checks(item: dict) -> set[str]:
    checks = item.get("required_checks")
    if checks is None and item.get("required_gate"):
        checks = [item["required_gate"]]
    if not isinstance(checks, list) or not checks or not all(isinstance(value, str) and value for value in checks):
        raise SystemExit(f"repository lacks required checks: {item}")
    if len(set(checks)) != len(checks):
        raise SystemExit(f"duplicate required checks: {item}")
    return set(checks)


def expected_check_app_id(item: dict) -> int:
    app_id = item.get("required_check_app_id")
    if not isinstance(app_id, int) or app_id <= 0:
        raise SystemExit(f"repository lacks required_check_app_id: {item}")
    return app_id


def expected_sources_satisfied(sources: dict[str, set[int | None]], expected: set[str], app_id: int) -> bool:
    return all(sources.get(context) == {app_id} for context in expected)


def merge_sources(*groups: dict[str, set[int | None]]) -> dict[str, set[int | None]]:
    merged: dict[str, set[int | None]] = {}
    for group in groups:
        for context, apps in group.items():
            merged.setdefault(context, set()).update(apps)
    return merged


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
        expected_checks(item)
        expected_check_app_id(item)
        for field in ("main_protected", "squash_only", "delete_branch_on_merge"):
            if not isinstance(item.get(field), bool):
                raise SystemExit(f"repository lacks boolean {field}: {item}")
        security = item.get("security")
        required_security = ("secret_scanning", "push_protection", "dependabot_security_updates")
        if not isinstance(security, dict) or set(security) != set(required_security):
            raise SystemExit(f"repository has incomplete security contract: {item}")
        if not all(isinstance(security.get(field), bool) for field in required_security):
            raise SystemExit(f"repository security controls must be booleans: {item}")
        if item.get("gate_mode") == "transition":
            target = item.get("target_gate")
            if not isinstance(target, str) or not target:
                raise SystemExit(f"transition repository lacks target_gate: {item}")
    admins = data.get("administrative_repositories")
    if not isinstance(admins, list):
        raise SystemExit("administrative_repositories must be an array")
    for item in admins:
        if not isinstance(item.get("repository_id"), int) or not item.get("repository"):
            raise SystemExit(f"invalid administrative repository entry: {item}")
        if item.get("terminal_state") == "ARCHIVED_READ_ONLY" and item.get("archived") is not True:
            raise SystemExit(f"archived terminal state must require archived=true: {item}")
    return data


def _ref_pattern_matches(pattern: str, *, branch: str, default_branch: str) -> bool:
    ref = f"refs/heads/{branch}"
    if pattern == "~ALL":
        return True
    if pattern == "~DEFAULT_BRANCH":
        return branch == default_branch
    return fnmatch.fnmatchcase(ref, pattern)


def ruleset_applies_to_branch(detail: dict, *, branch: str, default_branch: str) -> bool:
    if detail.get("enforcement") != "active" or detail.get("target") != "branch":
        return False
    ref_name = (detail.get("conditions") or {}).get("ref_name") or {}
    includes = ref_name.get("include") or []
    excludes = ref_name.get("exclude") or []
    if includes and not any(
        _ref_pattern_matches(pattern, branch=branch, default_branch=default_branch)
        for pattern in includes
    ):
        return False
    if any(
        _ref_pattern_matches(pattern, branch=branch, default_branch=default_branch)
        for pattern in excludes
    ):
        return False
    return True


class Audit:
    def __init__(self, token: str) -> None:
        self.token = token
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self._workflow_runs: dict[tuple[str, int], dict] = {}

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
                status = response.status
        except urllib.error.HTTPError as exc:
            if allow_404 and exc.code == 404:
                return None
            raise RuntimeError(f"GET {path} -> HTTP {exc.code}") from exc
        if not raw:
            return {"_http_status": status}
        return json.loads(raw)

    def check(self, condition: bool, message: str) -> None:
        if not condition:
            self.errors.append(message)

    @staticmethod
    def _add_source(sources: dict[str, set[int | None]], context: str | None, app_id: int | None) -> None:
        if context:
            sources.setdefault(context, set()).add(app_id if isinstance(app_id, int) else None)

    def _workflow_run(self, repo: str, check_run: dict) -> dict | None:
        match = WORKFLOW_RUN_RE.match(str(check_run.get("details_url") or ""))
        if not match:
            return None
        run_id = int(match.group(1))
        key = (repo, run_id)
        if key not in self._workflow_runs:
            payload = self.api(f"/repos/{repo}/actions/runs/{run_id}")
            if not isinstance(payload, dict):
                return None
            self._workflow_runs[key] = payload
        return self._workflow_runs[key]

    def _protected_flow_sources(
        self,
        repo: str,
        payload: dict,
        *,
        event: str,
        allowed_head_shas: set[str],
        pr_number: int | None = None,
    ) -> dict[str, set[int | None]]:
        sources: dict[str, set[int | None]] = {}
        for check_run in payload.get("check_runs", []):
            workflow = self._workflow_run(repo, check_run)
            if not workflow:
                continue
            if workflow.get("event") != event or workflow.get("head_sha") not in allowed_head_shas:
                continue
            if pr_number is not None:
                associated = {
                    item.get("number")
                    for item in check_run.get("pull_requests", [])
                    if isinstance(item, dict)
                }
                if pr_number not in associated:
                    continue
            self._add_source(sources, check_run.get("name"), (check_run.get("app") or {}).get("id"))
        return sources

    def required_context_sources(
        self,
        repo: str,
        *,
        branch: str = "main",
        default_branch: str = "main",
    ) -> dict[str, set[int | None]]:
        sources: dict[str, set[int | None]] = {}
        rulesets = self.api(f"/repos/{repo}/rulesets") or []
        for summary in rulesets:
            if summary.get("enforcement") != "active":
                continue
            detail = self.api(f"/repos/{repo}/rulesets/{summary['id']}")
            if not ruleset_applies_to_branch(detail, branch=branch, default_branch=default_branch):
                continue
            for rule in detail.get("rules", []):
                if rule.get("type") != "required_status_checks":
                    continue
                for check in rule.get("parameters", {}).get("required_status_checks", []):
                    self._add_source(sources, check.get("context"), check.get("integration_id"))
        protection = self.api(
            f"/repos/{repo}/branches/{urllib.parse.quote(branch, safe='')}/protection/required_status_checks",
            allow_404=True,
        )
        if protection:
            bound_contexts: set[str] = set()
            for check in protection.get("checks", []):
                context = check.get("context")
                if context:
                    bound_contexts.add(context)
                self._add_source(sources, context, check.get("app_id"))
            for context in protection.get("contexts", []):
                if context not in bound_contexts:
                    self._add_source(sources, context, None)
        return sources

    def representative_check_sources(
        self,
        repo: str,
        expected: set[str],
        expected_app_id: int,
    ) -> dict[str, set[int | None]]:
        """Prove emission from a protected push or one current internal PR containing main."""
        branch = self.api(f"/repos/{repo}/branches/main") or {}
        main_sha = ((branch.get("commit") or {}).get("sha") or "").strip()
        if not main_sha:
            return {}
        main_runs = self.api(f"/repos/{repo}/commits/{main_sha}/check-runs?per_page=100") or {}
        main_sources = self._protected_flow_sources(
            repo,
            main_runs,
            event="push",
            allowed_head_shas={main_sha},
        )
        if expected_sources_satisfied(main_sources, expected, expected_app_id):
            return main_sources

        def score(candidate: dict[str, set[int | None]]) -> int:
            return sum(candidate.get(context) == {expected_app_id} for context in expected)

        best = main_sources
        pulls = self.api(f"/repos/{repo}/pulls?state=open&base=main&sort=updated&direction=desc&per_page=20") or []
        for pr in pulls:
            head = pr.get("head", {})
            base = pr.get("base", {})
            head_repo = (head.get("repo") or {}).get("full_name")
            pr_number = pr.get("number")
            if head_repo != repo or base.get("ref") != "main" or not isinstance(pr_number, int):
                continue
            sha = head.get("sha")
            if not sha:
                continue
            comparison = self.api(f"/repos/{repo}/compare/{main_sha}...{sha}") or {}
            merge_base = (comparison.get("merge_base_commit") or {}).get("sha")
            if comparison.get("status") not in {"ahead", "identical"} or merge_base != main_sha:
                continue
            runs = self.api(f"/repos/{repo}/commits/{sha}/check-runs?per_page=100") or {}
            pr_sources = self._protected_flow_sources(
                repo,
                runs,
                event="pull_request",
                allowed_head_shas={sha},
                pr_number=pr_number,
            )
            target_sources = self._protected_flow_sources(
                repo,
                runs,
                event="pull_request_target",
                allowed_head_shas={main_sha},
                pr_number=pr_number,
            )
            sources = merge_sources(pr_sources, target_sources)
            if expected_sources_satisfied(sources, expected, expected_app_id):
                return sources
            if score(sources) > score(best):
                best = sources
        return best

    def dependabot_security_updates_enabled(self, repo: str) -> bool:
        fixes = self.api(f"/repos/{repo}/automated-security-fixes", allow_404=True)
        return isinstance(fixes, dict) and (
            fixes.get("_http_status") == 204 or fixes.get("enabled") is True
        )

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
        expected = expected_checks(wanted)
        expected_app = expected_check_app_id(wanted)
        required_sources = self.required_context_sources(
            repo,
            branch="main",
            default_branch=live.get("default_branch") or "main",
        )
        required_names = set(required_sources)
        self.check(expected <= required_names, f"{repo}: required checks drift: expected {sorted(expected)}, got {sorted(required_names)}")
        for context in expected:
            observed_apps = required_sources.get(context, set())
            self.check(
                observed_apps == {expected_app},
                f"{repo}: required check {context!r} App binding drift: expected {expected_app}, got {sorted(str(value) for value in observed_apps)}",
            )

        emitted = self.representative_check_sources(repo, expected, expected_app)
        emitted_names = set(emitted)
        self.check(
            expected <= emitted_names,
            f"{repo}: required checks not proven on current protected push or a current internal PR containing current main: expected {sorted(expected)}, observed {sorted(emitted_names)}",
        )
        for context in expected:
            observed_apps = emitted.get(context, set())
            self.check(
                observed_apps == {expected_app},
                f"{repo}: emitted check {context!r} App drift: expected {expected_app}, got {sorted(str(value) for value in observed_apps)}",
            )
        if wanted.get("gate_mode") == "transition" and wanted.get("target_gate") and wanted["target_gate"] not in required_names:
            self.warnings.append(f"{repo}: transition target gate not required yet: {wanted['target_gate']}")

        sec = live.get("security_and_analysis") or {}
        expected_sec = wanted.get("security") or {}
        mapping = {
            "secret_scanning": "secret_scanning",
            "push_protection": "secret_scanning_push_protection",
        }
        for key, api_key in mapping.items():
            if expected_sec.get(key):
                self.check((sec.get(api_key) or {}).get("status") == "enabled", f"{repo}: security baseline missing {key}")
        if expected_sec.get("dependabot_security_updates"):
            self.check(self.dependabot_security_updates_enabled(repo), f"{repo}: security baseline missing dependabot_security_updates")
        for path in ("SECURITY.md", ".github/CODEOWNERS"):
            self.check(self.file_exists(repo, path), f"{repo}: missing {path}")

        permissions = self.api(f"/repos/{repo}/actions/permissions")
        if permissions.get("allowed_actions") == "all":
            self.warnings.append(f"{repo}: Actions policy remains broad (allowed_actions=all)")

    def audit_administrative_repo(self, wanted: dict) -> None:
        repo = wanted["repository"]
        live = self.api(f"/repos/{repo}")
        self.check(live.get("id") == wanted["repository_id"], f"{repo}: administrative repository ID drift")
        if "archived" in wanted:
            self.check(bool(live.get("archived")) == bool(wanted["archived"]), f"{repo}: archived terminal-state drift")

    def _search_all_code(self, repo: str, needle: str) -> list[dict]:
        q = urllib.parse.quote_plus(f'"{needle}" repo:{repo}')
        items: list[dict] = []
        total: int | None = None
        for page in range(1, 11):
            result = self.api(f"/search/code?q={q}&per_page=100&page={page}") or {}
            if result.get("incomplete_results") is True:
                raise RuntimeError(f"code search incomplete for {repo} / {needle}")
            current_total = result.get("total_count")
            if not isinstance(current_total, int) or current_total < 0:
                raise RuntimeError(f"code search missing total_count for {repo} / {needle}")
            if current_total > 1000:
                raise RuntimeError(f"code search exceeds GitHub 1000-result completeness cap for {repo} / {needle}")
            if total is None:
                total = current_total
            elif total != current_total:
                raise RuntimeError(f"code search changed during pagination for {repo} / {needle}")
            page_items = result.get("items")
            if not isinstance(page_items, list):
                raise RuntimeError(f"code search malformed items for {repo} / {needle}")
            items.extend(item for item in page_items if isinstance(item, dict))
            if len(items) >= total:
                return items[:total]
            if not page_items:
                break
        if total is None or len(items) < total:
            raise RuntimeError(f"code search pagination incomplete for {repo} / {needle}")
        return items[:total]

    def coordinate_scan(self, desired: dict) -> None:
        policy = desired.get("mutable_coordinate_policy") or {}
        needles = list(policy.get("forbidden") or []) + list(policy.get("historical_reference_only") or [])
        for repo_item in desired["permanent_repositories"]:
            repo = repo_item["repository"]
            for needle in needles:
                for item in self._search_all_code(repo, needle):
                    path = item.get("path", "")
                    if path in POLICY_DECLARATION_FILES:
                        continue
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
        for repo in desired.get("administrative_repositories", []):
            audit.audit_administrative_repo(repo)
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
