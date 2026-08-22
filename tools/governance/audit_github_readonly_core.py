#!/usr/bin/env python3
"""Read-only Oteryn governance drift audit.

Offline mode validates the desired-state contract. Live mode reads GitHub REST only;
it never mutates settings. A caller must provide GH_TOKEN or GITHUB_TOKEN.
"""
from __future__ import annotations

import argparse
import base64
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


def allowed_required_checks(item: dict) -> set[str]:
    allowed = expected_checks(item)
    if item.get("gate_mode") == "transition":
        target = item.get("target_gate")
        if isinstance(target, str) and target:
            allowed.add(target)
    return allowed


def required_contexts_match(item: dict, observed: set[str]) -> bool:
    expected = expected_checks(item)
    return expected <= observed <= allowed_required_checks(item)


def actions_permissions_enabled(payload: object) -> bool:
    return isinstance(payload, dict) and payload.get("enabled") is True


def _strip_yaml_comment(raw: str) -> str:
    quote = None
    escaped = False
    out = []
    for char in raw:
        if escaped:
            out.append(char)
            escaped = False
            continue
        if char == "\\" and quote == '"':
            out.append(char)
            escaped = True
            continue
        if char in {"'", '"'}:
            if quote is None:
                quote = char
            elif quote == char:
                quote = None
            out.append(char)
            continue
        if char == "#" and quote is None:
            break
        out.append(char)
    return "".join(out).rstrip()


def _yaml_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] == '"':
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return value[1:-1]
        return decoded if isinstance(decoded, str) else value[1:-1]
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return value[1:-1].replace("''", "'")
    return value


def _yaml_mapping_field(body: str) -> tuple[bool, str, str] | None:
    match = re.fullmatch(
        r"""(?P<dash>-\s*)?(?P<key>[A-Za-z0-9_-]+|"[^"]+"|'[^']+')\s*:\s*(?P<value>.*)""",
        body.strip(),
    )
    if not match:
        return None
    key_token = match.group("key")
    if key_token.startswith('"') and "\\" in key_token:
        try:
            key = json.loads(key_token)
        except json.JSONDecodeError:
            return None
        if not isinstance(key, str):
            return None
    else:
        key = _yaml_scalar(key_token)
    return bool(match.group("dash")), key, match.group("value").strip()


WRITE_CAPABLE_TOKEN_SCOPES = {
    "actions", "attestations", "checks", "contents", "deployments", "discussions",
    "id-token", "issues", "packages", "pages", "pull-requests", "security-events", "statuses",
}


def _simple_flow_mapping(value: str) -> dict[str, str] | None:
    value = value.strip()
    if not (value.startswith("{") and value.endswith("}")):
        return None
    inner = value[1:-1].strip()
    if not inner:
        return {}
    parts: list[str] = []
    current: list[str] = []
    quote: str | None = None
    escaped = False
    for char in inner:
        if escaped:
            current.append(char)
            escaped = False
            continue
        if char == "\\" and quote == '"':
            current.append(char)
            escaped = True
            continue
        if char in {"'", '"'}:
            if quote is None:
                quote = char
            elif quote == char:
                quote = None
            current.append(char)
            continue
        if char == "," and quote is None:
            parts.append("".join(current).strip())
            current = []
            continue
        if char in "{}[]" and quote is None:
            return None
        current.append(char)
    if quote is not None:
        return None
    parts.append("".join(current).strip())
    result: dict[str, str] = {}
    for part in parts:
        field = _yaml_mapping_field(part)
        if field is None or field[0] or not field[1] or field[1] in result:
            return None
        result[field[1]] = _yaml_scalar(field[2])
    return result


def _permissions_write_wide(values: dict[str, str]) -> bool:
    return WRITE_CAPABLE_TOKEN_SCOPES <= {key for key, value in values.items() if value == "write"}


def dependabot_github_actions_entry_valid(text: str) -> bool:
    rows = []
    for raw in text.splitlines():
        if "\t" in raw:
            return False
        line = _strip_yaml_comment(raw)
        if not line.strip():
            continue
        rows.append((len(line) - len(line.lstrip(" ")), line.strip()))
    top_level_keys: set[str] = set()
    for indent, body in rows:
        if indent != 0:
            continue
        field = _yaml_mapping_field(body)
        if field is None or field[0] or not field[1] or field[1] in top_level_keys:
            return False
        top_level_keys.add(field[1])
    if not any(
        indent == 0 and (field := _yaml_mapping_field(body)) is not None
        and not field[0] and field[1] == "version" and _yaml_scalar(field[2]) == "2"
        for indent, body in rows
    ):
        return False
    try:
        updates_index = next(
            i for i, (indent, body) in enumerate(rows)
            if indent == 0 and (field := _yaml_mapping_field(body)) is not None
            and not field[0] and field[1] == "updates" and field[2] == ""
        )
    except StopIteration:
        return False
    i = updates_index + 1
    if i >= len(rows) or rows[i][0] == 0:
        return False
    item_indent = rows[i][0]
    while i < len(rows):
        indent, body = rows[i]
        if indent == 0:
            break
        if indent != item_indent or not body.startswith("-"):
            return False
        entry = []
        while i < len(rows):
            child_indent, child_body = rows[i]
            if child_indent == 0 or (entry and child_indent == item_indent and child_body.startswith("-")):
                break
            entry.append((child_indent, child_body))
            i += 1
        ecosystem = None
        directory = None
        interval = None
        schedule_indent = None
        schedule_child_indent = None
        seen_item_fields: set[str] = set()
        field_indent = item_indent + 2
        for offset, (child_indent, child_body) in enumerate(entry):
            field = _yaml_mapping_field(child_body)
            is_inline_item = offset == 0 and field is not None and field[0] and child_indent == item_indent
            is_item_field = field is not None and (
                is_inline_item or (not field[0] and child_indent == field_indent)
            )
            if schedule_indent is not None and child_indent <= schedule_indent and not is_inline_item:
                schedule_indent = None
                schedule_child_indent = None
            if is_item_field:
                if field[1] in seen_item_fields:
                    return False
                seen_item_fields.add(field[1])
            if is_item_field and field[1] == "package-ecosystem":
                ecosystem = _yaml_scalar(field[2])
            elif is_item_field and field[1] == "directory":
                directory = _yaml_scalar(field[2])
            elif is_item_field and field[1] == "schedule" and field[2] == "":
                schedule_indent = field_indent if is_inline_item else child_indent
                schedule_child_indent = schedule_indent + 2
            elif (
                schedule_indent is not None
                and field is not None and not field[0]
                and child_indent == schedule_child_indent
                and field[1] == "interval"
            ):
                interval = _yaml_scalar(field[2])
        if ecosystem == "github-actions":
            return directory == "/" and interval in {"daily", "weekly", "monthly", "quarterly", "semiannually", "yearly"}
    return False

def _codeowners_glob_regex(pattern: str) -> str:
    out = []
    i = 0
    while i < len(pattern):
        char = pattern[i]
        if char == "*":
            if i + 1 < len(pattern) and pattern[i + 1] == "*":
                out.append(".*")
                i += 2
                continue
            out.append("[^/]*")
        elif char == "?":
            out.append("[^/]")
        else:
            out.append(re.escape(char))
        i += 1
    return "".join(out)


def codeowners_pattern_covers(pattern: str, path: str) -> bool:
    pattern = pattern.strip()
    path = path.lstrip("/")
    if pattern in {"*", "**", "/**"}:
        return True
    anchored = pattern.startswith("/")
    normalized = pattern.lstrip("/")
    if normalized.endswith("/"):
        prefix = normalized.rstrip("/") + "/"
        return path.startswith(prefix)
    regex = _codeowners_glob_regex(normalized)
    if "/" not in normalized and not anchored:
        return any(re.fullmatch(regex, part) is not None for part in path.split("/"))
    return re.fullmatch(regex, path) is not None


def codeowners_text_covers_paths(text: str, required_paths: list[str]) -> bool:
    rules = []
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if len(parts) < 2 or not any(owner.startswith("@") or "@" in owner for owner in parts[1:]):
            return False
        rules.append(parts[0])
    return bool(rules) and all(any(codeowners_pattern_covers(pattern, path) for pattern in rules) for path in required_paths)


def workflow_text_secure(text: str) -> bool:
    has_top_permissions = False
    permissions_indent: int | None = None
    permissions_values: dict[str, str] = {}

    def close_permissions_block() -> bool:
        nonlocal permissions_indent, permissions_values
        if permissions_indent is None:
            return True
        safe = not _permissions_write_wide(permissions_values)
        permissions_indent = None
        permissions_values = {}
        return safe

    for raw in text.splitlines():
        line = _strip_yaml_comment(raw)
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        body = line.strip()
        if permissions_indent is not None and indent <= permissions_indent:
            if not close_permissions_block():
                return False
        field = _yaml_mapping_field(body)
        if field is None:
            compact = body.lstrip("- ").strip()
            if re.match(r'''^"[^"\n]*\\[^"\n]*"\s*:''', compact):
                return False
            if compact.startswith("{") and compact.endswith("}") and re.search(
                r'''(?:^|,)\s*(?:uses|permissions|"uses"|"permissions"|'uses'|'permissions')\s*:''',
                compact[1:-1],
            ):
                return False
            continue
        is_sequence, key, raw_value = field
        if ("{" in raw_value or "[" in raw_value) and re.search(
            r'''(?:^|[,\[{])\s*(?:uses|permissions|"uses"|"permissions"|'uses'|'permissions')\s*:''',
            raw_value,
        ):
            return False
        if permissions_indent is not None and not is_sequence and indent == permissions_indent + 2:
            permissions_values[key] = _yaml_scalar(raw_value)
        if key == "permissions":
            if indent == 0 and not is_sequence:
                has_top_permissions = True
            scalar = _yaml_scalar(raw_value)
            if scalar == "write-all" or raw_value.startswith(("&", "*")):
                return False
            if raw_value == "":
                if permissions_indent is not None and not close_permissions_block():
                    return False
                permissions_indent = indent
                permissions_values = {}
            elif raw_value.lstrip().startswith("{"):
                mapping = _simple_flow_mapping(raw_value)
                if mapping is None or _permissions_write_wide(mapping):
                    return False
        if key == "uses":
            value = _yaml_scalar(raw_value)
            if value.startswith("./"):
                continue
            if value.startswith("docker://"):
                if not re.fullmatch(r"docker://[^@\s]+@sha256:[0-9a-fA-F]{64}", value):
                    return False
                continue
            if "@" not in value:
                return False
            ref = value.rsplit("@", 1)[1]
            if not re.fullmatch(r"[0-9a-fA-F]{40}", ref):
                return False
    if not close_permissions_block():
        return False
    return has_top_permissions


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
            if item.get(field) is not True:
                raise SystemExit(f"repository must require {field}=true: {item}")
        protection = item.get("protection")
        required_protection = {"pull_requests": True, "force_pushes": False, "deletions": False, "broad_bypass": False}
        if protection != required_protection:
            raise SystemExit(f"repository has incomplete or weakened protection contract: {item}")
        security = item.get("security")
        required_security = (
            "private_vulnerability_reporting", "secret_scanning",
            "push_protection", "dependabot_security_updates",
            "github_actions_dependency_updates", "workflow_supply_chain",
        )
        if not isinstance(security, dict) or set(security) != set(required_security):
            raise SystemExit(f"repository has incomplete security contract: {item}")
        if not all(security.get(field) is True for field in required_security):
            raise SystemExit(f"repository security controls must all be true: {item}")
        if item.get("gate_mode") == "transition":
            target = item.get("target_gate")
            if not isinstance(target, str) or not target:
                raise SystemExit(f"transition repository lacks target_gate: {item}")
        codeowner_paths = item.get("codeowners_required_paths")
        if not isinstance(codeowner_paths, list) or not codeowner_paths or not all(
            isinstance(path, str) and path and not path.startswith("/") for path in codeowner_paths
        ):
            raise SystemExit(f"repository has invalid codeowners_required_paths: {item}")
        if len(set(codeowner_paths)) != len(codeowner_paths):
            raise SystemExit(f"repository has duplicate codeowners_required_paths: {item}")
    policy = data.get("mutable_coordinate_policy")
    if not isinstance(policy, dict) or set(policy) != {"forbidden", "historical_reference_only"}:
        raise SystemExit("mutable_coordinate_policy must contain forbidden and historical_reference_only")
    for field in ("forbidden", "historical_reference_only"):
        values = policy.get(field)
        if not isinstance(values, list) or not values or not all(isinstance(value, str) and value for value in values):
            raise SystemExit(f"mutable_coordinate_policy.{field} must be a non-empty string array")
        if len(set(values)) != len(values):
            raise SystemExit(f"mutable_coordinate_policy.{field} contains duplicates")

    admins = data.get("administrative_repositories")
    if not isinstance(admins, list) or len(admins) != 1:
        raise SystemExit("exactly one administrative repository is required")
    expected_admin = ("Oteryn/Oteryn-Platform-Migration-Backup-20260818", 1338405017)
    if (admins[0].get("repository"), admins[0].get("repository_id")) != expected_admin:
        raise SystemExit(f"unexpected administrative repository identity: {admins[0]}")
    required_admin_fields = {
        "repository", "repository_id", "classification", "terminal_state",
        "archived", "retention_authority", "retention_release",
    }
    for item in admins:
        if not isinstance(item, dict) or set(item) != required_admin_fields:
            raise SystemExit(f"administrative repository has incomplete contract: {item}")
        if not isinstance(item["repository_id"], int) or item["repository_id"] <= 0:
            raise SystemExit(f"invalid administrative repository_id: {item}")
        for field in ("repository", "classification", "terminal_state", "retention_authority"):
            if not isinstance(item[field], str) or not item[field].strip():
                raise SystemExit(f"administrative repository lacks {field}: {item}")
        if not isinstance(item["archived"], bool):
            raise SystemExit(f"administrative repository archived must be boolean: {item}")
        if item["terminal_state"] == "ARCHIVED_READ_ONLY" and item["archived"] is not True:
            raise SystemExit(f"archived terminal state must require archived=true: {item}")
        release = item.get("retention_release")
        if not isinstance(release, dict) or set(release) != {"tag", "assets"}:
            raise SystemExit(f"administrative repository has invalid retention_release: {item}")
        if not isinstance(release.get("tag"), str) or not release["tag"].strip():
            raise SystemExit(f"administrative repository has invalid retention release tag: {item}")
        assets = release.get("assets")
        if not isinstance(assets, dict) or len(assets) != 6:
            raise SystemExit(f"administrative repository must pin six retention assets: {item}")
        digest_re = re.compile(r"^sha256:[0-9a-f]{64}$")
        for name, identity in assets.items():
            if not isinstance(name, str) or not name or not isinstance(identity, dict) or set(identity) != {"size", "digest"}:
                raise SystemExit(f"invalid retention asset identity: {name!r} / {identity!r}")
            if not isinstance(identity.get("size"), int) or identity["size"] <= 0 or not isinstance(identity.get("digest"), str) or not digest_re.fullmatch(identity["digest"]):
                raise SystemExit(f"invalid retention asset size/digest: {name!r} / {identity!r}")
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
        self._workflow_definitions: dict[tuple[str, int], dict | None] = {}

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

    def _workflow_definition(self, repo: str, workflow_run: dict) -> dict | None:
        workflow_id = workflow_run.get("workflow_id")
        if not isinstance(workflow_id, int) or workflow_id <= 0:
            return None
        key = (repo, workflow_id)
        if key not in self._workflow_definitions:
            payload = self.api(f"/repos/{repo}/actions/workflows/{workflow_id}", allow_404=True)
            self._workflow_definitions[key] = payload if isinstance(payload, dict) else None
        return self._workflow_definitions[key]

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
            definition = self._workflow_definition(repo, workflow)
            if not definition or definition.get("state") != "active":
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

    def main_protection_controls(
        self, repo: str, *, branch: str = "main", default_branch: str = "main"
    ) -> dict[str, bool]:
        applicable: list[dict] = []
        for summary in self.api(f"/repos/{repo}/rulesets") or []:
            if summary.get("enforcement") != "active":
                continue
            detail = self.api(f"/repos/{repo}/rulesets/{summary['id']}")
            if ruleset_applies_to_branch(detail, branch=branch, default_branch=default_branch):
                applicable.append(detail)
        if applicable:
            rule_types = {
                rule.get("type") for detail in applicable for rule in detail.get("rules", [])
                if isinstance(rule, dict)
            }
            return {
                "pull_requests": "pull_request" in rule_types,
                "force_pushes": "non_fast_forward" not in rule_types,
                "deletions": "deletion" not in rule_types,
                "broad_bypass": any(bool(detail.get("bypass_actors")) for detail in applicable),
            }
        protection = self.api(
            f"/repos/{repo}/branches/{urllib.parse.quote(branch, safe='')}/protection",
            allow_404=True,
        )
        if not protection:
            return {"pull_requests": False, "force_pushes": True, "deletions": True, "broad_bypass": True}
        bypass_allowances = (
            (protection.get("required_pull_request_reviews") or {}).get("bypass_pull_request_allowances") or {}
        )
        has_pr_bypass = any(bool(bypass_allowances.get(kind)) for kind in ("users", "teams", "apps"))
        return {
            "pull_requests": protection.get("required_pull_request_reviews") is not None,
            "force_pushes": bool((protection.get("allow_force_pushes") or {}).get("enabled")),
            "deletions": bool((protection.get("allow_deletions") or {}).get("enabled")),
            "broad_bypass": (
                not bool((protection.get("enforce_admins") or {}).get("enabled")) or has_pr_bypass
            ),
        }

    def private_vulnerability_reporting_enabled(self, repo: str) -> bool:
        state = self.api(f"/repos/{repo}/private-vulnerability-reporting", allow_404=True)
        return isinstance(state, dict) and state.get("enabled") is True

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

    @staticmethod
    def _decoded_contents(payload: object) -> str | None:
        if not isinstance(payload, dict) or not isinstance(payload.get("content"), str):
            return None
        try:
            return base64.b64decode(payload["content"]).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return None

    def github_actions_dependency_updates_configured(self, repo: str) -> bool:
        payload = self.api(f"/repos/{repo}/contents/.github/dependabot.yml", allow_404=True)
        text = self._decoded_contents(payload)
        return text is not None and dependabot_github_actions_entry_valid(text)

    def codeowners_baseline_valid(self, repo: str, required_paths: list[str]) -> bool:
        payload = self.api(f"/repos/{repo}/contents/.github/CODEOWNERS", allow_404=True)
        text = self._decoded_contents(payload)
        errors = self.api(f"/repos/{repo}/codeowners/errors", allow_404=True)
        return (
            text is not None
            and isinstance(errors, dict)
            and errors.get("errors") == []
            and codeowners_text_covers_paths(text, required_paths)
        )

    def workflow_supply_chain_valid(self, repo: str) -> bool:
        listing = self.api(f"/repos/{repo}/contents/.github/workflows", allow_404=True)
        if not isinstance(listing, list):
            return False
        workflows = [
            item for item in listing
            if isinstance(item, dict) and item.get("type") == "file"
            and str(item.get("name") or "").lower().endswith((".yml", ".yaml"))
        ]
        if not workflows:
            return False
        for item in workflows:
            path = item.get("path")
            if not isinstance(path, str) or not path:
                return False
            payload = self.api(f"/repos/{repo}/contents/{'/'.join(urllib.parse.quote(part, safe='') for part in path.split('/'))}")
            text = self._decoded_contents(payload)
            if text is None or not workflow_text_secure(text):
                return False
        return True

    def retained_release_valid(self, repo: str, wanted: dict) -> bool:
        tag = wanted.get("tag")
        assets = wanted.get("assets")
        if not isinstance(tag, str) or not isinstance(assets, dict):
            return False
        release = self.api(f"/repos/{repo}/releases/tags/{urllib.parse.quote(tag, safe='')}", allow_404=True)
        if not isinstance(release, dict) or release.get("tag_name") != tag:
            return False
        observed = {
            asset.get("name"): {"size": asset.get("size"), "digest": asset.get("digest")}
            for asset in release.get("assets", [])
            if isinstance(asset, dict) and isinstance(asset.get("name"), str)
        }
        return all(observed.get(name) == identity for name, identity in assets.items())

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
        allowed_names = allowed_required_checks(wanted)
        self.check(required_contexts_match(wanted, required_names), f"{repo}: required checks drift: expected {sorted(expected)}, allowed {sorted(allowed_names)}, got {sorted(required_names)}")
        proof_names = required_names & allowed_names
        for context in proof_names:
            observed_apps = required_sources.get(context, set())
            self.check(observed_apps == {expected_app}, f"{repo}: required check {context!r} App binding drift: expected {expected_app}, got {sorted(str(value) for value in observed_apps)}")
        emitted = self.representative_check_sources(repo, proof_names, expected_app)
        emitted_names = set(emitted)
        self.check(proof_names <= emitted_names, f"{repo}: required checks not proven on current protected push or a current internal PR containing current main: expected {sorted(proof_names)}, observed {sorted(emitted_names)}")
        for context in proof_names:
            observed_apps = emitted.get(context, set())
            self.check(observed_apps == {expected_app}, f"{repo}: emitted check {context!r} App drift: expected {expected_app}, got {sorted(str(value) for value in observed_apps)}")
        if wanted.get("gate_mode") == "transition" and wanted.get("target_gate") and wanted["target_gate"] not in required_names:
            self.warnings.append(f"{repo}: transition target gate not required yet: {wanted['target_gate']}")

        actual_protection = self.main_protection_controls(
            repo, branch="main", default_branch=live.get("default_branch") or "main"
        )
        for control, expected_value in wanted["protection"].items():
            self.check(
                actual_protection.get(control) is expected_value,
                f"{repo}: protection control {control} drift: expected {expected_value}, got {actual_protection.get(control)}",
            )

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
        if expected_sec.get("private_vulnerability_reporting"):
            self.check(
                self.private_vulnerability_reporting_enabled(repo),
                f"{repo}: security baseline missing private_vulnerability_reporting",
            )
        if expected_sec.get("github_actions_dependency_updates"):
            self.check(
                self.github_actions_dependency_updates_configured(repo),
                f"{repo}: security baseline missing github_actions_dependency_updates",
            )
        self.check(self.file_exists(repo, "SECURITY.md"), f"{repo}: missing SECURITY.md")
        self.check(
            self.codeowners_baseline_valid(repo, wanted["codeowners_required_paths"]),
            f"{repo}: CODEOWNERS missing, invalid, or lacks required critical-path coverage",
        )
        if expected_sec.get("workflow_supply_chain"):
            self.check(
                self.workflow_supply_chain_valid(repo),
                f"{repo}: workflow supply-chain baseline missing explicit permissions or full-SHA action pins",
            )

        permissions = self.api(f"/repos/{repo}/actions/permissions")
        self.check(actions_permissions_enabled(permissions), f"{repo}: GitHub Actions disabled")
        if permissions.get("allowed_actions") == "all":
            self.warnings.append(f"{repo}: Actions policy remains broad (allowed_actions=all)")

    def audit_administrative_repo(self, wanted: dict) -> None:
        repo = wanted["repository"]
        live = self.api(f"/repos/{repo}")
        self.check(live.get("full_name") == repo, f"{repo}: administrative coordinate drift")
        self.check(live.get("id") == wanted["repository_id"], f"{repo}: administrative repository ID drift")
        if "archived" in wanted:
            self.check(bool(live.get("archived")) == bool(wanted["archived"]), f"{repo}: archived terminal-state drift")
        self.check(
            self.retained_release_valid(repo, wanted["retention_release"]),
            f"{repo}: retained transfer-cut Release assets drift",
        )

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
