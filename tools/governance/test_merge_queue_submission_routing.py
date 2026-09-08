#!/usr/bin/env python3
"""Regressions for connector-native GitHub Merge Queue submission routing."""

from __future__ import annotations

import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("merge_queue_submission_routing.py")
SPEC = importlib.util.spec_from_file_location("merge_queue_submission_routing", MODULE_PATH)
assert SPEC and SPEC.loader
routing = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(routing)

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "docs/agents/policy/ORGANIZATION_AGENT_POLICY.md"


def capabilities(**overrides: bool):
    values = {
        "merge_queue_required": True,
        "explicit_enqueue_available": False,
        "auto_merge_available": True,
        "integration_authorized": True,
        "pr_eligible": True,
    }
    values.update(overrides)
    return routing.SubmissionCapabilities(**values)


def test_explicit_enqueue_is_preferred_when_exposed() -> None:
    route = routing.choose_submission_route(capabilities(explicit_enqueue_available=True))
    assert route == routing.EXPLICIT_ENQUEUE


def test_auto_merge_is_valid_only_as_required_mq_submission_route() -> None:
    assert routing.choose_submission_route(capabilities()) == routing.AUTO_MERGE_MQ_SUBMISSION
    assert routing.choose_submission_route(capabilities(merge_queue_required=False)) == routing.NOT_MQ_TARGET


def test_missing_authority_or_eligibility_fails_before_tool_choice() -> None:
    assert routing.choose_submission_route(capabilities(integration_authorized=False)) == routing.BLOCKED_NOT_AUTHORIZED
    assert routing.choose_submission_route(capabilities(pr_eligible=False)) == routing.BLOCKED_NOT_ELIGIBLE


def test_missing_native_submission_capability_fails_closed() -> None:
    route = routing.choose_submission_route(
        capabilities(explicit_enqueue_available=False, auto_merge_available=False)
    )
    assert route == routing.BLOCKED_CAPABILITY_UNAVAILABLE


def test_queue_admission_requires_direct_github_evidence() -> None:
    for route in (routing.EXPLICIT_ENQUEUE, routing.AUTO_MERGE_MQ_SUBMISSION):
        assert routing.verify_queue_admission(route, []) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN
        assert routing.verify_queue_admission(route, ["checks_green"]) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN
        for evidence in routing.QUEUE_ADMISSION_EVIDENCE:
            assert routing.verify_queue_admission(route, [evidence]) == routing.ENQUEUED


def test_non_mq_or_blocked_routes_cannot_be_promoted_by_queue_like_text() -> None:
    for route in (
        routing.NOT_MQ_TARGET,
        routing.BLOCKED_NOT_AUTHORIZED,
        routing.BLOCKED_NOT_ELIGIBLE,
        routing.BLOCKED_CAPABILITY_UNAVAILABLE,
    ):
        assert routing.verify_queue_admission(route, ["added_to_merge_queue"]) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN


def test_no_direct_merge_route_exists() -> None:
    route_values = {
        value
        for name, value in vars(routing).items()
        if name.isupper() and isinstance(value, str)
    }
    assert "DIRECT_MERGE" not in route_values
    assert "MERGE_PULL_REQUEST" not in route_values


def test_canonical_policy_explains_verified_auto_merge_to_mq_boundary() -> None:
    text = POLICY.read_text(encoding="utf-8")
    for marker in (
        "Prefer an explicit native enqueue action",
        "`enablePullRequestAutoMerge`",
        "`added_to_merge_queue`",
        "`merge_group` candidate",
        "not a direct-merge fallback or protection bypass",
        "No bypass or direct merge substitutes for an unavailable enqueue tool",
    ):
        assert marker in text


def main() -> int:
    failures: list[tuple[str, Exception]] = []
    tests = [(name, test) for name, test in sorted(globals().items()) if name.startswith("test_") and callable(test)]
    for name, test in tests:
        try:
            test()
        except Exception as exc:  # noqa: BLE001 - compact deterministic harness
            failures.append((name, exc))
    if failures:
        for name, exc in failures:
            print(f"FAIL {name}: {exc}")
        return 1
    print(f"PASS {len(tests)} Merge Queue submission routing regressions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
