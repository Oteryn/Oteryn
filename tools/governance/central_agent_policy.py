#!/usr/bin/env python3
"""Validate the META-owned organization agent-policy bundle and provider boundaries."""
from __future__ import annotations

import base64
import json
from pathlib import Path
import re
from typing import Any, Callable
import urllib.error
import urllib.parse
import urllib.request

POLICY_PATH = Path("ecosystem/organization-agent-policy.json")
POLICY_ID = "OTERYN_ORGANIZATION_AGENT_POLICY"
POLICY_VERSION = "3.0.0"
AUTHORITY_REPOSITORY = "Oteryn/Oteryn"
BINDING_PATH = "docs/agents/META_AGENT_POLICY_BINDING.json"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
ALLOWED_PROVIDERS = (
    "Oteryn/Oteryn-Atlas",
    "Oteryn/Oteryn-Game",
    "Oteryn/Oteryn-Platform",
)
SERIAL_EXCEPTION_RE = re.compile(
    r"\bserial\s+(?:work|execution)\s+requires?\s+(?:an?\s+)?(?:explicit|recorded)\s+(?:reason|exception)\b",
    re.IGNORECASE,
)
AuthorityResolver = Callable[[str, str], object]

EXPECTED_POLICY_KEYS = {
    "schema_version",
    "policy_id",
    "policy_version",
    "authority_repository",
    "canonical_human_surfaces",
    "machine_authorities",
    "provider_binding_schema",
    "forbidden_provider_sections",
    "forbidden_task_prompt_sections",
}
EXPECTED_SURFACES = {
    "organization_policy": "docs/agents/policy/ORGANIZATION_AGENT_POLICY.md",
    "prompting_standard": "docs/agents/policy/PROMPTING_STANDARD.md",
    "prompt_eval_standard": "docs/agents/policy/PROMPT_EVAL_STANDARD.md",
}
EXPECTED_BINDING_KEYS = {
    "schema_version",
    "policy_id",
    "policy_version",
    "authority_repository",
    "authority_commit",
    "organization_policy_path",
    "prompting_standard_path",
    "prompt_eval_standard_path",
}


def _is_exact_int(value: object, expected: int) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value == expected


def load_policy(root: Path) -> dict[str, Any]:
    path = root / POLICY_PATH
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("organization agent policy root must be an object")
    return data


def validate_meta_bundle(root: Path, policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if set(policy) != EXPECTED_POLICY_KEYS:
        errors.append("organization policy keys must match the canonical closed schema")
    if not _is_exact_int(policy.get("schema_version"), 1):
        errors.append("organization policy schema_version must be 1")
    if policy.get("policy_id") != POLICY_ID:
        errors.append(f"organization policy_id must be {POLICY_ID}")
    if policy.get("policy_version") != POLICY_VERSION:
        errors.append(f"organization policy_version must be {POLICY_VERSION}")
    if policy.get("authority_repository") != AUTHORITY_REPOSITORY:
        errors.append(f"organization authority_repository must be {AUTHORITY_REPOSITORY}")

    surfaces = policy.get("canonical_human_surfaces")
    if surfaces != EXPECTED_SURFACES:
        errors.append("canonical_human_surfaces must match the central META paths")
    else:
        for name, relative in surfaces.items():
            path = root / relative
            if not path.is_file() or path.stat().st_size == 0:
                errors.append(f"missing or empty central human policy surface: {relative}")
                continue
            try:
                if not path.read_text(encoding="utf-8").strip():
                    errors.append(f"missing or empty central human policy surface: {relative}")
            except (OSError, UnicodeError):
                errors.append(f"missing or unreadable central human policy surface: {relative}")

    machine_authorities = policy.get("machine_authorities")
    if not isinstance(machine_authorities, list) or not machine_authorities:
        errors.append("machine_authorities must be a non-empty list")
    else:
        for relative in machine_authorities:
            if not isinstance(relative, str) or not relative.strip():
                errors.append("machine_authorities entries must be non-empty paths")
                continue
            path = root / relative
            if not path.is_file() or path.stat().st_size == 0:
                errors.append(f"missing or empty referenced machine authority: {relative}")

    schema = policy.get("provider_binding_schema")
    if not isinstance(schema, dict):
        errors.append("provider_binding_schema must be an object")
    else:
        if not _is_exact_int(schema.get("schema_version"), 1):
            errors.append("provider_binding_schema.schema_version must be 1")
        if schema.get("required_keys") != sorted(EXPECTED_BINDING_KEYS):
            errors.append("provider_binding_schema.required_keys must match the canonical binding schema")
        if schema.get("authority_commit_pattern") != SHA_RE.pattern:
            errors.append("provider binding authority_commit_pattern must require lowercase full SHA")
        if schema.get("allowed_providers") != list(ALLOWED_PROVIDERS):
            errors.append("provider_binding_schema.allowed_providers must name exactly Game/Platform/Atlas")

    provider_sections = policy.get("forbidden_provider_sections")
    task_sections = policy.get("forbidden_task_prompt_sections")
    if (
        not isinstance(provider_sections, list)
        or not provider_sections
        or not all(isinstance(v, str) and v.strip() for v in provider_sections)
    ):
        errors.append("forbidden_provider_sections must be a non-empty string list")
    if (
        not isinstance(task_sections, list)
        or not task_sections
        or not all(isinstance(v, str) and v.strip() for v in task_sections)
    ):
        errors.append("forbidden_task_prompt_sections must be a non-empty string list")

    return errors


def _github_json(url: str, *, timeout: float) -> object:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def _github_text_at_commit(repository: str, commit: str, relative: str, *, timeout: float) -> str:
    quoted_path = urllib.parse.quote(relative, safe="/")
    url = f"https://api.github.com/repos/{repository}/contents/{quoted_path}?ref={commit}"
    payload = _github_json(url, timeout=timeout)
    if not isinstance(payload, dict) or payload.get("encoding") != "base64":
        raise ValueError(f"GitHub contents response is invalid for {relative}")
    encoded = payload.get("content")
    if not isinstance(encoded, str) or not encoded:
        raise ValueError(f"GitHub contents response is empty for {relative}")
    return base64.b64decode(encoded).decode("utf-8")


def resolve_meta_authority_via_github(
    repository: str,
    commit: str,
    *,
    timeout: float = 15.0,
) -> dict[str, object] | None:
    """Read branch protection and ancestry separately, bound to one main snapshot.

    This verifies GitHub's protected flag, not the contents of every ruleset.
    The result is a snapshot for a trusted caller, not perpetual authorization.
    """
    if repository != AUTHORITY_REPOSITORY or not isinstance(commit, str) or SHA_RE.fullmatch(commit) is None:
        return None
    try:
        commit_payload = _github_json(
            f"https://api.github.com/repos/{repository}/commits/{commit}",
            timeout=timeout,
        )
        if not isinstance(commit_payload, dict) or commit_payload.get("sha") != commit:
            return None
        branch = _github_json(
            f"https://api.github.com/repos/{repository}/branches/main", timeout=timeout,
        )
        if not isinstance(branch, dict) or branch.get("name") != "main" or branch.get("protected") is not True:
            return None
        branch_commit = branch.get("commit")
        main_sha = branch_commit.get("sha") if isinstance(branch_commit, dict) else None
        if not isinstance(main_sha, str) or SHA_RE.fullmatch(main_sha) is None:
            return None
        compare_payload = _github_json(
            f"https://api.github.com/repos/{repository}/compare/{commit}...{main_sha}",
            timeout=timeout,
        )
        if not isinstance(compare_payload, dict) or compare_payload.get("status") not in ("ahead", "identical"):
            return None
        for key in ("base_commit", "merge_base_commit"):
            coordinate = compare_payload.get(key)
            if not isinstance(coordinate, dict) or coordinate.get("sha") != commit:
                return None

        policy_text = _github_text_at_commit(repository, commit, str(POLICY_PATH), timeout=timeout)
        policy = json.loads(policy_text)
        if not isinstance(policy, dict):
            return None
        surfaces = policy.get("canonical_human_surfaces")
        if surfaces != EXPECTED_SURFACES:
            return None
        human_surfaces: dict[str, str] = {}
        for relative in surfaces.values():
            if not isinstance(relative, str) or not relative:
                return None
            text = _github_text_at_commit(repository, commit, relative, timeout=timeout)
            if not text.strip():
                return None
            human_surfaces[relative] = text
        return {
            "repository": repository,
            "commit": commit,
            "merged_to_protected_main": True,
            "protected_main_sha": main_sha,
            "branch_protected": True,
            "policy": policy,
            "human_surfaces": human_surfaces,
        }
    except (
        urllib.error.HTTPError,
        urllib.error.URLError,
        TimeoutError,
        json.JSONDecodeError,
        UnicodeDecodeError,
        ValueError,
    ):
        return None


def _validate_resolved_authority(
    resolved: object,
    binding: dict[str, object],
    *,
    expected_policy: dict[str, Any] | None,
) -> list[str]:
    if not isinstance(resolved, dict):
        return ["authority_commit could not be resolved and authenticated from META"]

    errors: list[str] = []
    if resolved.get("repository") != AUTHORITY_REPOSITORY or resolved.get("commit") != binding.get("authority_commit"):
        errors.append("resolved META authority coordinates do not match provider binding")
    if resolved.get("merged_to_protected_main") is not True:
        errors.append("authority_commit is not verified as merged to protected META main")

    resolved_policy = resolved.get("policy")
    if not isinstance(resolved_policy, dict):
        errors.append("resolved META authority policy is missing or invalid")
    else:
        actual_paths = {
            "organization_policy": binding.get("organization_policy_path"),
            "prompting_standard": binding.get("prompting_standard_path"),
            "prompt_eval_standard": binding.get("prompt_eval_standard_path"),
        }
        if resolved_policy.get("policy_id") != binding.get("policy_id"):
            errors.append("resolved META policy_id does not match provider binding")
        if resolved_policy.get("policy_version") != binding.get("policy_version"):
            errors.append("resolved META policy_version does not match provider binding")
        if resolved_policy.get("authority_repository") != binding.get("authority_repository"):
            errors.append("resolved META authority repository does not match provider binding")
        if resolved_policy.get("canonical_human_surfaces") != actual_paths:
            errors.append("resolved META canonical paths do not match provider binding")
        if expected_policy is not None and resolved_policy != expected_policy:
            errors.append("resolved META policy does not match the expected central policy")

        human_surfaces = resolved.get("human_surfaces")
        expected_surface_paths = set(actual_paths.values())
        if not isinstance(human_surfaces, dict) or set(human_surfaces) != expected_surface_paths:
            errors.append("resolved META human policy surfaces do not match provider binding")
        elif not all(isinstance(value, str) and value.strip() for value in human_surfaces.values()):
            errors.append("resolved META human policy surfaces must be non-empty text")
    return errors


def validate_provider_binding(
    binding: object,
    *,
    policy: dict[str, Any] | None = None,
    authority_resolver: AuthorityResolver | None = None,
) -> list[str]:
    if not isinstance(binding, dict):
        return ["provider binding must be an object"]

    errors: list[str] = []
    if set(binding) != EXPECTED_BINDING_KEYS:
        errors.append("provider binding keys must match the canonical closed schema")
    if not _is_exact_int(binding.get("schema_version"), 1):
        errors.append("provider binding schema_version must be 1")
    if binding.get("policy_id") != POLICY_ID:
        errors.append(f"policy_id must be {POLICY_ID}")
    if binding.get("policy_version") != POLICY_VERSION:
        errors.append(f"policy_version must be {POLICY_VERSION}")
    if binding.get("authority_repository") != AUTHORITY_REPOSITORY:
        errors.append(f"authority_repository must be {AUTHORITY_REPOSITORY}")
    authority_commit = binding.get("authority_commit")
    valid_authority_commit = isinstance(authority_commit, str) and SHA_RE.fullmatch(authority_commit) is not None
    if not valid_authority_commit:
        errors.append("authority_commit must be a lowercase full 40-hex commit SHA")
    if authority_resolver is None:
        errors.append("provider binding validation requires an authenticated META authority resolver")

    expected_paths = EXPECTED_SURFACES
    actual_paths = {
        "organization_policy": binding.get("organization_policy_path"),
        "prompting_standard": binding.get("prompting_standard_path"),
        "prompt_eval_standard": binding.get("prompt_eval_standard_path"),
    }
    if actual_paths != expected_paths:
        errors.append("provider binding canonical paths must match META policy")

    if policy is not None and not isinstance(policy, dict):
        errors.append("expected META policy must be an object")
    elif policy is not None:
        if policy.get("policy_id") != binding.get("policy_id") or policy.get("policy_version") != binding.get("policy_version"):
            errors.append("provider binding policy identity/version must match META policy")
        if policy.get("canonical_human_surfaces") != actual_paths:
            if "provider binding canonical paths must match META policy" not in errors:
                errors.append("provider binding canonical paths must match META policy")

    # Malformed input is not a reason to perform network resolution. In particular,
    # reject non-string paths before constructing the resolved surface-path set.
    if not errors and authority_resolver is not None:
        try:
            resolved = authority_resolver(AUTHORITY_REPOSITORY, authority_commit)
        except Exception:
            resolved = None
        errors.extend(_validate_resolved_authority(resolved, binding, expected_policy=policy))
    return errors


# These are bounded structural/legacy-text diagnostics, not a natural-language
# permission engine. Actual authorization remains in the existing machine gates.
LEGACY_HEADINGS = [
    "## Remote Desktop execution routing",
    "## Canonical Codex review routing",
    "## Parallel-agent Git concurrency",
    "## GitHub-first execution",
    "## Bounded autonomy, retry and continuation",
]
EXECUTION_MODULES = (
    "ecosystem/agent-execution-routing-policy.json",
    "ecosystem/bounded-autonomous-execution-policy.json",
    "ecosystem/agent-continuation-policy.json",
    "docs/agents/contracts/agent_execution_access_and_continuation_policy.md",
    "docs/agents/contracts/bounded_autonomous_execution_policy.md",
    "docs/agents/contracts/persistent_autonomous_continuation_policy.md",
)
REVIEW_MODULES = ("codex_review_policy.json", "owner_funded_ai_policy", "docs/governance/ai_review_policy.md")


def _operative_markdown(text: str) -> str:
    """Exclude comments, fenced examples and quoted evidence from text lint only.

    This convention is not proof that an agent ignores those bytes. Do not use a
    successful text-lint result to authorize tools, merges or provider adoption.
    """
    text = re.sub(r"<!--.*?(?:-->|$)", "", text, flags=re.DOTALL)
    lines: list[str] = []
    fence: tuple[str, int] | None = None
    for line in text.splitlines():
        stripped = line.strip()
        delimiter = re.match(r"^(`{3,}|~{3,})(.*)$", stripped)
        if fence is not None:
            if delimiter and delimiter[1][0] == fence[0] and len(delimiter[1]) >= fence[1] and not delimiter[2].strip():
                fence = None
            lines.append("")
            continue
        if delimiter:
            fence = (delimiter[1][0], len(delimiter[1]))
            lines.append("")
        elif stripped.startswith(">"):
            lines.append("")
        else:
            lines.append(line)
    return "\n".join(lines)


def _normalized(text: str) -> str:
    return " ".join(text.casefold().split())


def _heading_title(text: str) -> str:
    text = re.sub(r"^#{1,6}\s+", "", text.strip())
    text = re.sub(r"\s+#+\s*$", "", text)
    return _normalized(re.sub(r"[*_`]", "", text))


def _contains_forbidden_section(text: str, sections: object) -> bool:
    if not isinstance(sections, list):
        return False
    lines = _operative_markdown(text).splitlines()
    headings = {_heading_title(line) for line in lines if re.match(r"^\s{0,3}#{1,6}\s+", line)}
    for before, line in zip(lines, lines[1:]):
        if before.strip() and re.fullmatch(r"\s{0,3}(?:=+|-+)\s*", line):
            headings.add(_heading_title(before))
    body = _normalized("\n".join(lines))
    for section in sections:
        if not isinstance(section, str):
            continue
        if section.lstrip().startswith("#"):
            if _heading_title(section) in headings:
                return True
        elif _normalized(section) in body:
            return True
    return False


def _section_list(policy: dict[str, Any] | None, key: str) -> list[str] | None:
    if policy is None:
        return LEGACY_HEADINGS
    if not isinstance(policy, dict):
        return None
    value = policy.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(v, str) and v.strip() for v in value):
        return None
    return value


def _statements(text: str) -> list[str]:
    body = re.sub(r"(?m)^\s{0,3}#{1,6}\s+.*$", "", _operative_markdown(text))
    result: list[str] = []
    for block in re.split(r"\n\s*\n", body):
        result.extend(re.split(r"(?<=[.!?])\s+", " ".join(block.split())))
    return result


def _is_audit_or_negative(statement: str) -> bool:
    # Restrict this exemption to an explicit sentence prefix, not any occurrence
    # of 'not' somewhere in a paragraph containing an unrelated positive command.
    return re.match(
        r"^(?:[-*+]\s+|\d+[.)]\s+)?(?:(?:agents?|workers?|you)\s+)?(?:do\s+not|never|must\s+not|"
        r"remove|retire|audit|inspect|compare)\b", statement, re.IGNORECASE,
    ) is not None


def _parallel_directive(text: str) -> bool:
    term = r"parallel[-_ ]first"
    for statement in _statements(text):
        if _is_audit_or_negative(statement):
            continue
        if SERIAL_EXCEPTION_RE.search(statement):
            return True
        if re.search(rf"\b(?:must|shall|always|use|require|enforce)\b[^.!?]*\b{term}\b", statement, re.IGNORECASE):
            return True
        if re.search(rf"\b{term}\b[^.!?]*\b(?:is|remains)\s+(?:mandatory|required)\b", statement, re.IGNORECASE):
            return True
    return False


def _local_controller(text: str, modules: tuple[str, ...], *, copied: bool) -> bool:
    for statement in _statements(text):
        if _is_audit_or_negative(statement) or not any(module in statement.casefold() for module in modules):
            continue
        if copied or re.search(
            r"\blocal(?:\s+(?:retry|routing|review|continuation|execution))?\s+(?:authority|controller)\s+(?:is|=|:)"
            r"|\bas\s+(?:the\s+)?local\s+(?:task\s+)?controllers?\b",
            statement, re.IGNORECASE,
        ):
            return True
    return False


def _remote_tool_grant(text: str, *, copied: bool) -> bool:
    for statement in _statements(text):
        if _is_audit_or_negative(statement) or "remote_desktop_commander." not in statement.casefold():
            continue
        if copied or re.search(
            r"\b(?:is|are)\s+(?:always\s+)?(?:allowed|permitted|authorized)\b"
            r"|\b(?:may|can|must|shall)\s+(?:invoke|use|call)\b", statement, re.IGNORECASE,
        ):
            return True
    return False


def _allowed_providers(policy: dict[str, Any] | None) -> tuple[str, ...]:
    if policy is None:
        return ALLOWED_PROVIDERS
    if not isinstance(policy, dict):
        return ()
    schema = policy.get("provider_binding_schema")
    if not isinstance(schema, dict) or schema.get("allowed_providers") != list(ALLOWED_PROVIDERS):
        return ()
    return ALLOWED_PROVIDERS


def validate_provider_overlay(
    provider: str,
    text: str,
    *,
    policy: dict[str, Any] | None = None,
) -> list[str]:
    if not isinstance(provider, str) or not provider.strip():
        return ["provider name is invalid"]
    if not isinstance(text, str) or not text.strip():
        return [f"{provider}: provider overlay text is empty"]
    errors: list[str] = []
    if provider not in _allowed_providers(policy):
        errors.append("provider repository is not allowed by central META policy")
    active = _operative_markdown(text)
    if re.search(r"(?<![\w/.-])" + re.escape(BINDING_PATH) + r"(?![\w/.-])", active) is None:
        errors.append(f"provider overlay must resolve {BINDING_PATH}")
    sections = _section_list(policy, "forbidden_provider_sections")
    if sections is None:
        errors.append("forbidden_provider_sections must be a non-empty string list")
    copied = _contains_forbidden_section(active, sections)
    if copied:
        errors.append("provider overlay must not copy organization-wide policy sections")
    if _remote_tool_grant(active, copied=copied):
        errors.append("provider overlay must not define Remote Desktop connector policy")
    if _parallel_directive(active):
        errors.append("parallel-first execution wording is forbidden")
    if _local_controller(active, EXECUTION_MODULES + REVIEW_MODULES, copied=copied):
        errors.append("provider overlay must not directly redefine META machine modules")
    return errors


def validate_task_prompt_text(
    text: str,
    *,
    policy: dict[str, Any] | None = None,
) -> list[str]:
    if not isinstance(text, str) or not text.strip():
        return ["task prompt text is empty"]
    errors: list[str] = []
    active = _operative_markdown(text)
    sections = _section_list(policy, "forbidden_task_prompt_sections")
    if sections is None:
        errors.append("forbidden_task_prompt_sections must be a non-empty string list")
    copied = _contains_forbidden_section(active, sections)
    if copied:
        errors.append("task prompt must not copy organization-wide policy sections")
    if _local_controller(active, REVIEW_MODULES, copied=copied):
        errors.append("task prompt must not embed global AI-review policy")
    if _local_controller(active, EXECUTION_MODULES, copied=copied) or _remote_tool_grant(active, copied=copied):
        errors.append("task prompt must not embed global execution-routing policy")
    if _parallel_directive(active):
        errors.append("parallel-first execution wording is forbidden")
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    try:
        policy = load_policy(root)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"FAIL central agent policy: {exc}")
        return 1
    errors = validate_meta_bundle(root, policy)
    if errors:
        for error in errors:
            print(f"FAIL central agent policy: {error}")
        return 1
    print(f"PASS central agent policy {policy['policy_version']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
