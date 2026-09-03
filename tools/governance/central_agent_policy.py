#!/usr/bin/env python3
"""Validate the META-owned organization agent-policy bundle and provider boundaries."""
from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

POLICY_PATH = Path("ecosystem/organization-agent-policy.json")
POLICY_ID = "OTERYN_ORGANIZATION_AGENT_POLICY"
POLICY_VERSION = "3.0.0"
AUTHORITY_REPOSITORY = "Oteryn/Oteryn"
BINDING_PATH = "docs/agents/META_AGENT_POLICY_BINDING.json"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
PARALLEL_FIRST_RE = re.compile(r"\bparallel[-_]first\b", re.IGNORECASE)
SERIAL_EXCEPTION_RE = re.compile(
    r"\bserial\s+(?:work|execution)\s+requires?\s+(?:an?\s+)?(?:explicit|recorded)\s+(?:reason|exception)\b",
    re.IGNORECASE,
)

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
        for relative in surfaces.values():
            path = root / relative
            if not path.is_file() or path.stat().st_size == 0:
                errors.append(f"missing or empty central human policy surface: {relative}")

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
        expected_providers = [
            "Oteryn/Oteryn-Atlas",
            "Oteryn/Oteryn-Game",
            "Oteryn/Oteryn-Platform",
        ]
        if schema.get("allowed_providers") != expected_providers:
            errors.append("provider_binding_schema.allowed_providers must name exactly Game/Platform/Atlas")

    provider_sections = policy.get("forbidden_provider_sections")
    task_sections = policy.get("forbidden_task_prompt_sections")
    if not isinstance(provider_sections, list) or not all(isinstance(v, str) and v for v in provider_sections):
        errors.append("forbidden_provider_sections must be a non-empty string list")
    if not isinstance(task_sections, list) or not all(isinstance(v, str) and v for v in task_sections):
        errors.append("forbidden_task_prompt_sections must be a non-empty string list")

    if surfaces == EXPECTED_SURFACES:
        organization_text = (root / EXPECTED_SURFACES["organization_policy"]).read_text(encoding="utf-8")
        prompting_text = (root / EXPECTED_SURFACES["prompting_standard"]).read_text(encoding="utf-8")
        eval_text = (root / EXPECTED_SURFACES["prompt_eval_standard"]).read_text(encoding="utf-8")
        for marker in (
            "one rule, one authority",
            "single_agent",
            "parallel_when_beneficial",
            BINDING_PATH,
            "immutable META commit",
        ):
            if marker not in organization_text:
                errors.append(f"organization policy missing marker: {marker}")
        for marker in (
            "ROLE / OUTCOME",
            "AUTHORITY / SCOPE DELTA",
            "LIVE LOCATORS",
            "DOMAIN CONSTRAINTS / DEPENDENCIES",
            "ACCEPTANCE / VALIDATION DELTA",
            "STOP / HANDOFF DELTA",
            "Omit a section when it has no task-specific content.",
        ):
            if marker not in prompting_text:
                errors.append(f"prompting standard missing marker: {marker}")
        for marker in (
            "ablation",
            "same representative cases",
            "Safety-critical regression tolerance is zero.",
        ):
            if marker not in eval_text:
                errors.append(f"prompt eval standard missing marker: {marker}")
    return errors


def validate_provider_binding(
    binding: object,
    *,
    policy: dict[str, Any] | None = None,
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
    if not isinstance(authority_commit, str) or SHA_RE.fullmatch(authority_commit) is None:
        errors.append("authority_commit must be a lowercase full 40-hex commit SHA")

    expected_paths = EXPECTED_SURFACES
    actual_paths = {
        "organization_policy": binding.get("organization_policy_path"),
        "prompting_standard": binding.get("prompting_standard_path"),
        "prompt_eval_standard": binding.get("prompt_eval_standard_path"),
    }
    if actual_paths != expected_paths:
        errors.append("provider binding canonical paths must match META policy")

    if policy is not None:
        if policy.get("policy_id") != binding.get("policy_id") or policy.get("policy_version") != binding.get("policy_version"):
            errors.append("provider binding policy identity/version must match META policy")
        if policy.get("canonical_human_surfaces") != actual_paths:
            if "provider binding canonical paths must match META policy" not in errors:
                errors.append("provider binding canonical paths must match META policy")
    return errors


def _contains_forbidden_section(text: str, sections: object) -> bool:
    if not isinstance(sections, list):
        return False
    lowered = text.lower()
    return any(isinstance(section, str) and section.lower() in lowered for section in sections)


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
    if "META_AGENT_POLICY_BINDING.json" not in text:
        errors.append(f"provider overlay must resolve {BINDING_PATH}")

    sections = (
        policy.get("forbidden_provider_sections")
        if isinstance(policy, dict)
        else [
            "## Remote Desktop execution routing",
            "## Canonical Codex review routing",
            "## Parallel-agent Git concurrency",
            "## GitHub-first execution",
        ]
    )
    if _contains_forbidden_section(text, sections):
        errors.append("provider overlay must not copy organization-wide policy sections")

    lowered = text.lower()
    if "remote_desktop_commander." in lowered:
        errors.append("provider overlay must not define Remote Desktop connector policy")
    if PARALLEL_FIRST_RE.search(text) or SERIAL_EXCEPTION_RE.search(text):
        errors.append("parallel-first execution wording is forbidden")

    direct_modules = (
        "ecosystem/agent-execution-routing-policy.json",
        "ecosystem/bounded-autonomous-execution-policy.json",
        "docs/governance/ai_review_policy.md",
        "docs/agents/contracts/agent_execution_access_and_continuation_policy.md",
    )
    if any(module in lowered for module in direct_modules):
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
    sections = (
        policy.get("forbidden_task_prompt_sections")
        if isinstance(policy, dict)
        else [
            "## Remote Desktop execution routing",
            "## Canonical Codex review routing",
            "## GitHub-first execution",
            "## Parallel-agent Git concurrency",
        ]
    )
    if _contains_forbidden_section(text, sections):
        errors.append("task prompt must not copy organization-wide policy sections")

    lowered = text.lower()
    if "codex_review_policy.json" in lowered or "owner_funded_ai_policy" in lowered:
        errors.append("task prompt must not embed global AI-review policy")
    if "remote_desktop_commander." in lowered or "ecosystem/agent-execution-routing-policy.json" in lowered:
        errors.append("task prompt must not embed global execution-routing policy")
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
