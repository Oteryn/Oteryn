#!/usr/bin/env python3
"""Focused regressions for the META-owned central agent-policy bundle."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import tempfile
from unittest import mock
import urllib.error

MODULE_PATH = Path(__file__).with_name("central_agent_policy.py")
SPEC = importlib.util.spec_from_file_location("central_agent_policy", MODULE_PATH)
assert SPEC and SPEC.loader
central = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(central)

ADOPTION_PATH = Path(__file__).with_name("provider_policy_adoption.py")
ADOPTION_SPEC = importlib.util.spec_from_file_location("provider_policy_adoption", ADOPTION_PATH)
assert ADOPTION_SPEC and ADOPTION_SPEC.loader
adoption = importlib.util.module_from_spec(ADOPTION_SPEC)
ADOPTION_SPEC.loader.exec_module(adoption)

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


def resolved_authority(
    *,
    commit: str = FULL_SHA,
    repository: str = "Oteryn/Oteryn",
    merged: bool = True,
) -> dict[str, object]:
    policy = central.load_policy(REPO_ROOT)
    surfaces = {
        relative: (REPO_ROOT / relative).read_text(encoding="utf-8")
        for relative in policy["canonical_human_surfaces"].values()
    }
    return {
        "repository": repository,
        "commit": commit,
        "merged_to_protected_main": merged,
        "policy": copy.deepcopy(policy),
        "human_surfaces": surfaces,
    }


def trusted_resolver(repository: str, commit: str) -> dict[str, object] | None:
    if repository == "Oteryn/Oteryn" and commit == FULL_SHA:
        return resolved_authority()
    return None


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


def test_meta_bundle_tracks_current_continuation_and_skill_precedence() -> None:
    policy = central.load_policy(REPO_ROOT)
    machine_authorities = policy["machine_authorities"]
    for relative in (
        "ecosystem/agent-continuation-policy.json",
        "docs/agents/contracts/PERSISTENT_AUTONOMOUS_CONTINUATION_POLICY.md",
    ):
        assert relative in machine_authorities

    text = (REPO_ROOT / "docs/agents/policy/ORGANIZATION_AGENT_POLICY.md").read_text(encoding="utf-8")
    for marker in (
        "WAITING_EXTERNAL",
        "STALLED",
        "no-op/retrigger",
        "subordinate execution aids",
        "additional approval gates",
        "duplicate planning artifacts",
    ):
        assert marker in text


def test_meta_ci_wires_central_policy_once_into_existing_meta_gate() -> None:
    text = (REPO_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert text.count("python3 tools/governance/test_central_agent_policy.py") == 1
    assert text.count("python3 tools/governance/central_agent_policy.py") == 1
    assert "Path('ecosystem/organization-agent-policy.json')" in text
    assert "Path('docs/agents/policy/ORGANIZATION_AGENT_POLICY.md')" in text


def test_provider_binding_accepts_only_exact_immutable_meta_coordinates() -> None:
    policy = central.load_policy(REPO_ROOT)
    assert central.validate_provider_binding(
        valid_binding(),
        policy=policy,
        authority_resolver=trusted_resolver,
    ) == []

    for bad_commit in ("main", "01234567", FULL_SHA.upper(), "g" * 40, ""):
        malformed = valid_binding()
        malformed["authority_commit"] = bad_commit
        errors = central.validate_provider_binding(malformed, authority_resolver=trusted_resolver)
        assert "authority_commit must be a lowercase full 40-hex commit SHA" in errors


def test_provider_binding_is_closed_and_cannot_fork_meta_identity() -> None:
    malformed = valid_binding()
    malformed["extra_policy"] = "local override"
    assert "provider binding keys must match the canonical closed schema" in central.validate_provider_binding(
        malformed,
        authority_resolver=trusted_resolver,
    )

    malformed = valid_binding()
    malformed["authority_repository"] = "Oteryn/Oteryn-Game"
    assert "authority_repository must be Oteryn/Oteryn" in central.validate_provider_binding(
        malformed,
        authority_resolver=trusted_resolver,
    )

    malformed = valid_binding()
    malformed["policy_id"] = "GAME_AGENT_POLICY"
    assert "policy_id must be OTERYN_ORGANIZATION_AGENT_POLICY" in central.validate_provider_binding(
        malformed,
        authority_resolver=trusted_resolver,
    )


def test_provider_binding_resolves_and_authenticates_pinned_meta_commit() -> None:
    policy = central.load_policy(REPO_ROOT)

    assert central.validate_provider_binding(
        valid_binding(),
        policy=policy,
        authority_resolver=trusted_resolver,
    ) == []

    nonexistent = valid_binding()
    nonexistent["authority_commit"] = "0" * 40
    errors = central.validate_provider_binding(
        nonexistent,
        policy=policy,
        authority_resolver=trusted_resolver,
    )
    assert "authority_commit could not be resolved and authenticated from META" in errors

    def unrelated_resolver(repository: str, commit: str) -> dict[str, object]:
        return resolved_authority(commit=commit, merged=False)

    errors = central.validate_provider_binding(
        valid_binding(),
        policy=policy,
        authority_resolver=unrelated_resolver,
    )
    assert "authority_commit is not verified as merged to protected META main" in errors


def test_provider_binding_fails_closed_without_authority_resolver() -> None:
    errors = central.validate_provider_binding(valid_binding())
    assert "provider binding validation requires an authenticated META authority resolver" in errors

    policy = central.load_policy(REPO_ROOT)
    errors = central.validate_provider_binding(valid_binding(), policy=policy)
    assert "provider binding validation requires an authenticated META authority resolver" in errors


def test_provider_overlay_references_binding_without_copying_global_policy() -> None:
    lean = """# Game agent instructions

Organization policy: resolve `docs/agents/META_AGENT_POLICY_BINDING.json` before material mutation.

## Domain invariants
Native Rust, protocol-oteryn, server authority and session-generation fencing remain Game-owned constraints.
"""
    assert central.validate_provider_overlay("Oteryn/Oteryn-Game", lean) == []

    copied = lean + "\n## Remote Desktop execution routing\nRemote_Desktop_Commander.ping is allowed for routine inspection.\n"
    errors = central.validate_provider_overlay("Oteryn/Oteryn-Game", copied)
    assert "provider overlay must not copy organization-wide policy sections" in errors
    assert "provider overlay must not define Remote Desktop connector policy" in errors


def test_provider_overlay_rejects_verbatim_canonical_policy_section() -> None:
    policy = central.load_policy(REPO_ROOT)
    lean = """# Game agent instructions
Resolve `docs/agents/META_AGENT_POLICY_BINDING.json` before material mutation.
## Domain invariants
Game-owned safety constraints remain local.
"""
    copied = lean + (
        "\n## Execution shape\n"
        " \n"
        "Use `single_agent` when one capable worker is proportionate. Use `parallel_when_beneficial` only when at least two materially independent workstreams justify coordination cost. One mutating owner per writable lane remains the default safety boundary; read-only analysis may fan out when it has clear value.\n\n"
        "Parallelism is an optimization, not a completion criterion. Serial work does not require an apology or a fabricated exception.\n"
    )
    errors = central.validate_provider_overlay("Oteryn/Oteryn-Game", copied, policy=policy)
    assert "provider overlay must not copy organization-wide policy sections" in errors


def test_provider_overlay_enforces_declared_provider_allowlist() -> None:
    policy = central.load_policy(REPO_ROOT)
    lean = """# Provider instructions
Resolve `docs/agents/META_AGENT_POLICY_BINDING.json` before material mutation.
## Domain invariants
Repository-local safety constraints remain local.
"""
    for provider in policy["provider_binding_schema"]["allowed_providers"]:
        assert central.validate_provider_overlay(provider, lean, policy=policy) == []
    errors = central.validate_provider_overlay("Oteryn/Oteryn-Gmae", lean, policy=policy)
    assert "provider repository is not allowed by central META policy" in errors


def test_provider_overlay_rejects_copied_continuation_authority() -> None:
    policy = central.load_policy(REPO_ROOT)
    lean = """# Game agent instructions
Resolve `docs/agents/META_AGENT_POLICY_BINDING.json` before material mutation.
## Domain invariants
Game-owned safety constraints remain local.
"""
    copied = (
        lean
        + "\n## Bounded autonomy, retry and continuation\n"
        + "Local continuation follows ecosystem/agent-continuation-policy.json and "
        + "docs/agents/contracts/PERSISTENT_AUTONOMOUS_CONTINUATION_POLICY.md.\n"
    )
    errors = central.validate_provider_overlay("Oteryn/Oteryn-Game", copied, policy=policy)
    assert "provider overlay must not copy organization-wide policy sections" in errors
    assert "provider overlay must not directly redefine META machine modules" in errors


def test_provider_overlay_rejects_copied_bounded_execution_contract() -> None:
    policy = central.load_policy(REPO_ROOT)
    copied = """# Game agent instructions
Resolve `docs/agents/META_AGENT_POLICY_BINDING.json` before material mutation.
## Local lifecycle constraints
Local retry authority is docs/agents/contracts/BOUNDED_AUTONOMOUS_EXECUTION_POLICY.md.
"""
    errors = central.validate_provider_overlay("Oteryn/Oteryn-Game", copied, policy=policy)
    assert "provider overlay must not directly redefine META machine modules" in errors


def test_legacy_provider_adoption_validator_delegates_to_central_lean_overlay() -> None:
    lean = """# Atlas agent instructions
Resolve `docs/agents/META_AGENT_POLICY_BINDING.json` before material mutation.
## Domain invariants
Projection, provenance, rendering and deployment-revision constraints remain Atlas-owned.
"""
    assert adoption.validate_provider_agents_text("Oteryn/Oteryn-Atlas", lean) == []

    copied = lean + "\nThe local authority is ecosystem/agent-execution-routing-policy.json.\n"
    errors = adoption.validate_provider_agents_text("Oteryn/Oteryn-Atlas", copied)
    assert "provider overlay must not directly redefine META machine modules" in errors


def test_provider_overlay_rejects_parallel_first_and_direct_meta_module_forks() -> None:
    stale = """# Atlas agent instructions
Resolve `docs/agents/META_AGENT_POLICY_BINDING.json`.
A substantial task must plan parallel-first. Serial work requires an explicit reason.
The local authority is ecosystem/agent-execution-routing-policy.json.
"""
    errors = central.validate_provider_overlay("Oteryn/Oteryn-Atlas", stale)
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


def test_task_prompt_rejects_verbatim_canonical_policy_section() -> None:
    policy = central.load_policy(REPO_ROOT)
    copied = (
        "ROLE / OUTCOME\n"
        "Repair the allocated task.\n\n"
        "## Integration\n"
        "\t\n"
        "GitHub protected-branch enforcement, the repository's single aggregate gate and GitHub Merge Queue are integration authority where configured. Deterministic CI qualifies the applicable exact candidate; custom review fingerprints, envelopes, attestations, formal R0/R1/R2 states, `ai-review-gate` as merge authority and custom proof ledgers remain retired by ADR 0005.\n\n"
        "Do not bypass Merge Queue or replace it with a direct merge merely because a connector lacks an enqueue operation.\n"
    )
    errors = central.validate_task_prompt_text(copied, policy=policy)
    assert "task prompt must not copy organization-wide policy sections" in errors


def test_task_prompt_rejects_copied_bounded_continuation_and_ai_authority() -> None:
    policy = central.load_policy(REPO_ROOT)
    copied = """ROLE / OUTCOME
Repair the allocated task.

## Bounded autonomy, retry and continuation
Follow ecosystem/agent-continuation-policy.json,
docs/agents/contracts/PERSISTENT_AUTONOMOUS_CONTINUATION_POLICY.md,
docs/agents/contracts/BOUNDED_AUTONOMOUS_EXECUTION_POLICY.md,
and docs/governance/AI_REVIEW_POLICY.md as local task controllers.
"""
    errors = central.validate_task_prompt_text(copied, policy=policy)
    assert "task prompt must not copy organization-wide policy sections" in errors
    assert "task prompt must not embed global AI-review policy" in errors
    assert "task prompt must not embed global execution-routing policy" in errors


def test_binding_paths_must_match_central_policy() -> None:
    policy = central.load_policy(REPO_ROOT)
    malformed = copy.deepcopy(valid_binding())
    malformed["prompting_standard_path"] = "docs/agents/PROMPTING_STANDARD.md"
    errors = central.validate_provider_binding(
        malformed,
        policy=policy,
        authority_resolver=trusted_resolver,
    )
    assert "provider binding canonical paths must match META policy" in errors


# Instruction-debt audit D15/D19/D20 and input-boundary regressions.
# Markdown lint is deliberately not an authorization or model-behavior proof.
LEAN_OVERLAY = "# Provider\nResolve `docs/agents/META_AGENT_POLICY_BINDING.json`.\n"
MAIN_SHA = "abcdef01" * 5


def test_optimization_detects_legacy_headings_without_a_fixed_heading_level() -> None:
    for heading in (
        "# Remote Desktop execution routing",
        "### Remote Desktop execution routing",
        "###### REMOTE DESKTOP EXECUTION ROUTING ######",
        "## **Remote Desktop execution routing**",
        "Remote Desktop execution routing\n--------------------------------",
    ):
        text = LEAN_OVERLAY + "\n" + heading + "\nLocal procedure.\n"
        assert "provider overlay must not copy organization-wide policy sections" in central.validate_provider_overlay("Oteryn/Oteryn-Game", text), heading
        assert "task prompt must not copy organization-wide policy sections" in central.validate_task_prompt_text(text), heading


def test_optimization_accepts_inert_examples_and_audit_references() -> None:
    examples = (
        "Remove the historical heading `## Remote Desktop execution routing`.\n",
        "```markdown\n## Remote Desktop execution routing\nRemote_Desktop_Commander.ping is allowed.\n```\n",
        "~~~markdown\n## Canonical Codex review routing\nRead CODEX_REVIEW_POLICY.json.\n~~~\n",
        "> ## Remote Desktop execution routing\n> Old example, not active instructions.\n",
        "<!--\n## Parallel-agent Git concurrency\nA task must plan parallel-first.\n-->\n",
        "Audit `docs/governance/AI_REVIEW_POLICY.md` and `ecosystem/agent-execution-routing-policy.json`.\n",
        "When investigating continuation, consult `docs/agents/contracts/PERSISTENT_AUTONOMOUS_CONTINUATION_POLICY.md`.\n",
        "Audit calls to `Remote_Desktop_Commander.ping`; do not invoke it.\n",
    )
    for example in examples:
        assert central.validate_provider_overlay("Oteryn/Oteryn-Game", LEAN_OVERLAY + example) == [], example
        assert central.validate_task_prompt_text("Audit instruction debt.\n" + example) == [], example


def test_optimization_binding_reference_must_be_active_and_exact() -> None:
    for text in (
        "# Provider\n```\ndocs/agents/META_AGENT_POLICY_BINDING.json\n```\n",
        "# Provider\n<!-- docs/agents/META_AGENT_POLICY_BINDING.json -->\n",
        "# Provider\n> docs/agents/META_AGENT_POLICY_BINDING.json\n",
        "# Provider\nUse `other/META_AGENT_POLICY_BINDING.json`.\n",
    ):
        assert central.validate_provider_overlay("Oteryn/Oteryn-Game", text), text


def test_optimization_distinguishes_parallel_directives_from_removal_and_negation() -> None:
    for text in (
        "Do not use parallel-first execution.",
        "Never require parallel-first execution.",
        "Remove the historical parallel-first requirement.",
        "Audit whether serial work requires an explicit reason in the old prompt.",
    ):
        assert central.validate_provider_overlay("Oteryn/Oteryn-Game", LEAN_OVERLAY + text) == [], text
        assert central.validate_task_prompt_text(text) == [], text
    for text in (
        "A substantial task must plan parallel-first.",
        "Always use parallel first execution.",
        "Use parallel_first execution.",
        "Parallel-first execution is mandatory.",
        "Serial work requires an explicit reason.",
    ):
        assert "parallel-first execution wording is forbidden" in central.validate_provider_overlay("Oteryn/Oteryn-Game", LEAN_OVERLAY + text), text
        assert "parallel-first execution wording is forbidden" in central.validate_task_prompt_text(text), text


def test_optimization_retains_rejection_of_local_controllers_and_tool_grants() -> None:
    for text in (
        "The local authority is ecosystem/agent-execution-routing-policy.json.",
        "Local retry authority is docs/agents/contracts/BOUNDED_AUTONOMOUS_EXECUTION_POLICY.md.",
        "Follow docs/governance/AI_REVIEW_POLICY.md as local task controllers.",
        "Remote_Desktop_Commander.ping is allowed for routine inspection.",
        "Agents may invoke Remote_Desktop_Commander.ping for routine inspection.",
    ):
        assert central.validate_provider_overlay("Oteryn/Oteryn-Game", LEAN_OVERLAY + text), text
        assert central.validate_task_prompt_text(text), text


def test_optimization_invalid_binding_fails_before_resolver_or_unhashable_path() -> None:
    for field, value in (
        ("organization_policy_path", []),
        ("prompting_standard_path", {}),
        ("prompt_eval_standard_path", ["bad"]),
        ("schema_version", True),
        ("extra_key", "unexpected"),
    ):
        binding = valid_binding()
        binding[field] = value
        resolver = mock.Mock(return_value=resolved_authority())
        errors = central.validate_provider_binding(binding, authority_resolver=resolver)
        assert errors, field
        resolver.assert_not_called()


def test_optimization_overlay_cannot_expand_the_canonical_provider_allowlist() -> None:
    policy = copy.deepcopy(central.load_policy(REPO_ROOT))
    policy["provider_binding_schema"]["allowed_providers"].append("Oteryn/Unallocated")
    assert central.validate_provider_overlay("Oteryn/Unallocated", LEAN_OVERLAY, policy=policy)


def test_optimization_invalid_policy_lists_fail_closed_in_standalone_checks() -> None:
    for value in ([], None, [""], ["   "], "not-a-list"):
        policy = copy.deepcopy(central.load_policy(REPO_ROOT))
        policy["forbidden_provider_sections"] = value
        policy["forbidden_task_prompt_sections"] = value
        assert central.validate_provider_overlay("Oteryn/Oteryn-Game", LEAN_OVERLAY, policy=policy), value
        assert central.validate_task_prompt_text("Repair a small bug.", policy=policy), value


def _mock_github_resolution(*, protected: object = True, status: str = "ahead", malformed_surfaces: bool = False):
    """Mock API protocol inputs only; this is not live GitHub adoption evidence."""
    policy = copy.deepcopy(central.load_policy(REPO_ROOT))
    if malformed_surfaces:
        policy["canonical_human_surfaces"] = {"organization_policy": "../../unexpected"}
    seen: list[str] = []

    def read_json(url: str, *, timeout: float) -> object:
        seen.append(url)
        if url.endswith("/commits/" + FULL_SHA):
            return {"sha": FULL_SHA}
        if url.endswith("/branches/main"):
            return {"name": "main", "protected": protected, "commit": {"sha": MAIN_SHA}}
        if "/compare/" in url:
            return {"status": status, "base_commit": {"sha": FULL_SHA}, "merge_base_commit": {"sha": FULL_SHA}}
        raise AssertionError("unexpected API request: " + url)

    def read_text(repository: str, commit: str, relative: str, *, timeout: float) -> str:
        assert repository == "Oteryn/Oteryn" and commit == FULL_SHA
        if relative == str(central.POLICY_PATH):
            return json.dumps(policy)
        return "Immutable policy fixture.\n"

    return read_json, read_text, seen


def test_optimization_resolver_checks_protection_and_pins_the_ancestry_read() -> None:
    read_json, read_text, seen = _mock_github_resolution()
    with mock.patch.object(central, "_github_json", side_effect=read_json), mock.patch.object(central, "_github_text_at_commit", side_effect=read_text):
        resolved = central.resolve_meta_authority_via_github("Oteryn/Oteryn", FULL_SHA)
    assert resolved is not None
    assert resolved["merged_to_protected_main"] is True
    assert resolved["protected_main_sha"] == MAIN_SHA
    assert resolved["branch_protected"] is True
    assert f"https://api.github.com/repos/Oteryn/Oteryn/compare/{FULL_SHA}...{MAIN_SHA}" in seen
    assert not any(url.endswith("...main") for url in seen)


def test_optimization_ancestry_alone_cannot_attest_branch_protection() -> None:
    for protected in (False, None, 1, "true"):
        read_json, read_text, _seen = _mock_github_resolution(protected=protected)
        with mock.patch.object(central, "_github_json", side_effect=read_json), mock.patch.object(central, "_github_text_at_commit", side_effect=read_text) as text_reader:
            assert central.resolve_meta_authority_via_github("Oteryn/Oteryn", FULL_SHA) is None, protected
            text_reader.assert_not_called()


def test_optimization_nonancestor_does_not_fetch_policy_bodies() -> None:
    for status in ("behind", "diverged", "unknown"):
        read_json, read_text, _seen = _mock_github_resolution(status=status)
        with mock.patch.object(central, "_github_json", side_effect=read_json), mock.patch.object(central, "_github_text_at_commit", side_effect=read_text) as text_reader:
            assert central.resolve_meta_authority_via_github("Oteryn/Oteryn", FULL_SHA) is None, status
            text_reader.assert_not_called()


def test_optimization_resolver_handles_bad_coordinates_and_network_failure() -> None:
    for commit in (None, [], 1, "main", "g" * 40):
        with mock.patch.object(central, "_github_json") as reader:
            assert central.resolve_meta_authority_via_github("Oteryn/Oteryn", commit) is None
            reader.assert_not_called()
    with mock.patch.object(central, "_github_json", side_effect=urllib.error.URLError("unavailable")):
        assert central.resolve_meta_authority_via_github("Oteryn/Oteryn", FULL_SHA) is None


def test_optimization_resolver_rejects_noncanonical_policy_paths_before_reading_them() -> None:
    read_json, read_text, _seen = _mock_github_resolution(malformed_surfaces=True)
    with mock.patch.object(central, "_github_json", side_effect=read_json), mock.patch.object(central, "_github_text_at_commit", side_effect=read_text) as text_reader:
        assert central.resolve_meta_authority_via_github("Oteryn/Oteryn", FULL_SHA) is None
        assert text_reader.call_count == 1


def test_optimization_invalid_utf8_policy_surface_is_a_validation_error() -> None:
    policy = central.load_policy(REPO_ROOT)
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        relative = policy["canonical_human_surfaces"]["organization_policy"]
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"\xff")
        errors = central.validate_meta_bundle(root, policy)
        assert any(relative in error for error in errors)


def test_optimization_minimal_local_bootstrap_is_not_a_copied_controller() -> None:
    policy = central.load_policy(REPO_ROOT)
    bootstrap = LEAN_OVERLAY + "Use `single_agent` when one capable worker is proportionate.\n"
    assert central.validate_provider_overlay("Oteryn/Oteryn-Game", bootstrap, policy=policy) == []


def test_optimization_document_wording_is_not_a_machine_schema() -> None:
    policy = central.load_policy(REPO_ROOT)
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        for relative in policy["machine_authorities"]:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("test fixture, not live policy\n", encoding="utf-8")
        for relative in policy["canonical_human_surfaces"].values():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# Alternative human wording\n\nNon-empty documentation, no mandatory section template.\n", encoding="utf-8")
        assert central.validate_meta_bundle(root, policy) == []
        for relative in policy["canonical_human_surfaces"].values():
            (root / relative).write_text(" \n\t\n", encoding="utf-8")
        assert central.validate_meta_bundle(root, policy)


def test_optimization_binding_rejects_nonobject_expected_policy() -> None:
    for value in ([], "invalid", 1):
        resolver = mock.Mock(return_value=resolved_authority())
        assert central.validate_provider_binding(valid_binding(), policy=value, authority_resolver=resolver)
        resolver.assert_not_called()


def test_optimization_protection_snapshot_and_compare_identity_fail_closed() -> None:
    read_json, read_text, _seen = _mock_github_resolution()
    variants = (
        ("compare", {"status": [], "base_commit": {"sha": FULL_SHA}, "merge_base_commit": {"sha": FULL_SHA}}),
        ("branch", {"name": "other", "protected": True, "commit": {"sha": MAIN_SHA}}),
        ("branch", {"name": "main", "protected": True, "commit": {"sha": "a" * 42}}),
        ("branch", {"name": "main", "protected": True, "commit": []}),
        ("compare", {"status": "ahead", "base_commit": {"sha": MAIN_SHA}, "merge_base_commit": {"sha": FULL_SHA}}),
        ("compare", {"status": "ahead", "base_commit": {"sha": FULL_SHA}, "merge_base_commit": {"sha": MAIN_SHA}}),
    )
    for target, payload in variants:
        def corrupt(url: str, *, timeout: float) -> object:
            if target == "branch" and url.endswith("/branches/main"):
                return payload
            if target == "compare" and "/compare/" in url:
                return payload
            return read_json(url, timeout=timeout)
        with mock.patch.object(central, "_github_json", side_effect=corrupt), mock.patch.object(central, "_github_text_at_commit", side_effect=read_text) as reader:
            assert central.resolve_meta_authority_via_github("Oteryn/Oteryn", FULL_SHA) is None, payload
            reader.assert_not_called()


def test_optimization_negation_does_not_hide_a_following_positive_requirement() -> None:
    for text in ("Agents must not use parallel-first.", "Parallel-first execution is not required."):
        assert central.validate_task_prompt_text(text) == [], text
    text = "Do not copy old policy. Always use parallel-first."
    assert "parallel-first execution wording is forbidden" in central.validate_task_prompt_text(text)


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
