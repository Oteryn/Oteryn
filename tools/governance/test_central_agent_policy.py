#!/usr/bin/env python3
"""Focused regressions for the META-owned central agent-policy bundle."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import tempfile

MODULE_PATH = Path(__file__).with_name("central_agent_policy.py")
SPEC = importlib.util.spec_from_file_location("central_agent_policy", MODULE_PATH)
assert SPEC and SPEC.loader
central = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(central)

REPO_ROOT = Path(__file__).parents[2]
FULL_SHA = "0123456789abcdef0123456789abcdef01234567"


def valid_binding() -> dict[str, object]:
    return {
        "schema_version": 1,
        "policy_id": "OTERYN_ORGANIZATION_AGENT_POLICY",
        "policy_version": "3.0.0",
        "authority_repository": "Oteryn/Oteryn",
        "authority_commit": FULL_SHA,
        "organization_policy_path": "docs/agents/policy/ORGANIZATION_AGENT_POLICY.md",
        "prompting_standard_path": "docs/agents/policy/PROMPTING_STANDARD.md",
        "prompt_eval_standard_path": "docs/agents/policy/PROMPT_EVAL_STANDARD.md",
    }


def test_meta_bundle_is_complete_and_self_consistent() -> None:
    policy = central.load_policy(REPO_ROOT)
    assert central.validate_meta_bundle(REPO_ROOT, policy) == []


def test_meta_bundle_rejects_empty_forbidden_section_lists() -> None:
    policy = central.load_policy(REPO_ROOT)
    for key in ("forbidden_provider_sections", "forbidden_task_prompt_sections"):
        malformed = copy.deepcopy(policy)
        malformed[key] = []
        errors = central.validate_meta_bundle(REPO_ROOT, malformed)
        assert f"{key} must be a non-empty string list" in errors


def test_meta_bundle_reports_missing_human_surface_without_throwing() -> None:
    policy = central.load_policy(REPO_ROOT)
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        for relative in policy["machine_authorities"]:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("authority\n", encoding="utf-8")
        for relative in policy["canonical_human_surfaces"].values():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("placeholder\n", encoding="utf-8")
        missing = root / policy["canonical_human_surfaces"]["organization_policy"]
        missing.unlink()
        errors = central.validate_meta_bundle(root, policy)
        assert "missing or empty central human policy surface: docs/agents/policy/ORGANIZATION_AGENT_POLICY.md" in errors


def test_provider_binding_accepts_only_exact_immutable_meta_coordinates() -> None:
    assert central.validate_provider_binding(valid_binding()) == []

    for bad_commit in ("main", "01234567", FULL_SHA.upper(), "g" * 40, ""):
        malformed = valid_binding()
        malformed["authority_commit"] = bad_commit
        errors = central.validate_provider_binding(malformed)
        assert "authority_commit must be a lowercase full 40-hex commit SHA" in errors


def test_provider_binding_is_closed_and_cannot_fork_meta_identity() -> None:
    malformed = valid_binding()
    malformed["extra_policy"] = "local override"
    assert "provider binding keys must match the canonical closed schema" in central.validate_provider_binding(malformed)

    malformed = valid_binding()
    malformed["authority_repository"] = "Oteryn/Oteryn-Game"
    assert "authority_repository must be Oteryn/Oteryn" in central.validate_provider_binding(malformed)

    malformed = valid_binding()
    malformed["policy_id"] = "GAME_AGENT_POLICY"
    assert "policy_id must be OTERYN_ORGANIZATION_AGENT_POLICY" in central.validate_provider_binding(malformed)


def test_provider_overlay_references_binding_without_copying_global_policy() -> None:
    lean = """# Game agent instructions

Organization policy: resolve `docs/agents/META_AGENT_POLICY_BINDING.json` before material mutation.

## Domain invariants
Native Rust, protocol-oteryn, server authority and session-generation fencing remain Game-owned constraints.
"""
    assert central.validate_provider_overlay("Game", lean) == []

    copied = lean + "\n## Remote Desktop execution routing\nRemote_Desktop_Commander.ping is allowed for routine inspection.\n"
    errors = central.validate_provider_overlay("Game", copied)
    assert "provider overlay must not copy organization-wide policy sections" in errors
    assert "provider overlay must not define Remote Desktop connector policy" in errors


def test_provider_overlay_rejects_parallel_first_and_direct_meta_module_forks() -> None:
    stale = """# Atlas agent instructions
Resolve `docs/agents/META_AGENT_POLICY_BINDING.json`.
A substantial task must plan parallel-first. Serial work requires an explicit reason.
The local authority is ecosystem/agent-execution-routing-policy.json.
"""
    errors = central.validate_provider_overlay("Atlas", stale)
    assert "parallel-first execution wording is forbidden" in errors
    assert "provider overlay must not directly redefine META machine modules" in errors


def test_task_prompt_may_be_small_but_cannot_recreate_global_policy() -> None:
    lean = """ROLE / OUTCOME
Repair the allocated durability receipt bug.

AUTHORITY / SCOPE DELTA
Write only the paths allocated by the live task.

ACCEPTANCE / VALIDATION DELTA
Focused persistence regression plus exact-head repository gate.
"""
    assert central.validate_task_prompt_text(lean) == []

    copied = lean + "\n## Canonical Codex review routing\nResolve CODEX_REVIEW_POLICY.json before every review.\n"
    errors = central.validate_task_prompt_text(copied)
    assert "task prompt must not copy organization-wide policy sections" in errors
    assert "task prompt must not embed global AI-review policy" in errors


def test_binding_paths_must_match_central_policy() -> None:
    policy = central.load_policy(REPO_ROOT)
    malformed = copy.deepcopy(valid_binding())
    malformed["prompting_standard_path"] = "docs/agents/PROMPTING_STANDARD.md"
    errors = central.validate_provider_binding(malformed, policy=policy)
    assert "provider binding canonical paths must match META policy" in errors


def main() -> int:
    failures: list[tuple[str, Exception]] = []
    for name, test in sorted(globals().items()):
        if name.startswith("test_") and callable(test):
            try:
                test()
            except Exception as exc:  # pragma: no cover - command-line harness
                failures.append((name, exc))
                print(f"FAIL {name}: {exc}")
    if failures:
        raise SystemExit(f"{len(failures)} central agent-policy test(s) failed")
    print("PASS central agent-policy tests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
