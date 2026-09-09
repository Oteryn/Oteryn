#!/usr/bin/env python3
"""Regressions for the current exact-target Merge Queue guard."""

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
REPOSITORY = "Oteryn/Oteryn-Platform"
PR_NUMBER = 1367
PR_HEAD = "a" * 40
OTHER_HEAD = "c" * 40
ATTEMPT_ID = "attempt-20260909-0001"
NOW = 1_800_000_000


def attempt(**overrides):
    values = {
        "attempt_id": ATTEMPT_ID,
        "repository": REPOSITORY,
        "pr_number": PR_NUMBER,
        "base_ref": "main",
        "live_pr_head_sha": PR_HEAD,
    }
    values.update(overrides)
    return routing.SubmissionAttempt(**values)


def freeze(**overrides):
    values = {"repository": REPOSITORY, "pr_number": PR_NUMBER, "head_sha": PR_HEAD}
    values.update(overrides)
    return routing.CandidateFreeze(**values)


def authorization(**overrides):
    values = {
        "source": routing.AUTHORIZATION_SOURCE,
        "repository": REPOSITORY,
        "pr_number": PR_NUMBER,
        "base_ref": "main",
        "pr_head_sha": PR_HEAD,
        "integration_authorized": True,
        "pr_eligible": True,
        "observed_at_epoch_seconds": NOW,
    }
    values.update(overrides)
    return routing.SubmissionAuthorization(**values)


def route(*, current_attempt=None, current_freeze=None, current_authorization=None, now=NOW):
    return routing.choose_submission_route(
        current_attempt or attempt(),
        current_freeze or freeze(),
        current_authorization or authorization(),
        now_epoch_seconds=now,
    )


def test_current_documented_primitives_have_no_atomic_exact_target_route() -> None:
    by_operation = {p.operation: p for p in routing.DOCUMENTED_QUEUE_PRIMITIVES}
    assert set(by_operation) == {"merge-async", "enqueuePullRequest"}
    for primitive in by_operation.values():
        assert primitive.queue_specific is True
        assert primitive.expected_head_fence is True
        assert primitive.expected_base_queue_fence is False
        assert not routing.primitive_has_atomic_exact_target_fence(primitive)
    assert routing.current_documented_atomic_routes() == ()
    assert route() == routing.BLOCKED_CAPABILITY_UNAVAILABLE


def test_callers_cannot_assert_hypothetical_capabilities() -> None:
    # The guard exposes no caller-supplied capability object and no positive
    # route/receipt verification surface. A future GitHub primitive must change
    # reviewed repository source instead of flipping a runtime boolean.
    for forbidden_name in (
        "SubmissionCapabilities",
        "AsyncMergeReceipt",
        "EnqueueReceipt",
        "verify_async_merge_receipt",
        "verify_enqueue_receipt",
        "ASYNC_MERGE_QUEUE",
        "EXPLICIT_ENQUEUE",
        "PROTECTED_EXECUTOR_ENQUEUE",
        "SUBMISSION_ACCEPTED",
        "ENQUEUED",
    ):
        assert not hasattr(routing, forbidden_name), forbidden_name


def test_even_a_synthetic_atomic_primitive_is_not_runtime_authority() -> None:
    synthetic = routing.DocumentedQueuePrimitive(
        operation="futureAtomicQueue",
        queue_specific=True,
        expected_head_fence=True,
        expected_base_queue_fence=True,
    )
    assert routing.primitive_has_atomic_exact_target_fence(synthetic)
    # It is not part of repository-owned DOCUMENTED_QUEUE_PRIMITIVES, and the
    # route function has no parameter through which a caller can inject it.
    assert synthetic not in routing.DOCUMENTED_QUEUE_PRIMITIVES
    assert route() == routing.BLOCKED_CAPABILITY_UNAVAILABLE


def test_authorization_and_eligibility_remain_exact_target_bound() -> None:
    assert route(current_authorization=authorization(integration_authorized=False)) == routing.BLOCKED_NOT_AUTHORIZED
    assert route(current_authorization=authorization(pr_eligible=False)) == routing.BLOCKED_NOT_ELIGIBLE
    for changes in (
        {"source": "cached_authorization"},
        {"repository": "Oteryn/Oteryn-Game"},
        {"pr_number": PR_NUMBER + 1},
        {"base_ref": "release"},
        {"pr_head_sha": OTHER_HEAD},
        {"observed_at_epoch_seconds": NOW - routing.MAX_AUTHORIZATION_AGE_SECONDS - 1},
        {"observed_at_epoch_seconds": NOW + 1},
        {"integration_authorized": 1},
        {"pr_eligible": 1},
    ):
        assert route(current_authorization=authorization(**changes)) == routing.BLOCKED_STALE_STATE, changes


def test_exact_candidate_freeze_fails_closed() -> None:
    assert route(current_freeze=freeze(head_sha=OTHER_HEAD)) == routing.BLOCKED_FROZEN_HEAD_MISMATCH
    moved_attempt = attempt(live_pr_head_sha=OTHER_HEAD)
    moved_auth = authorization(pr_head_sha=OTHER_HEAD)
    assert route(current_attempt=moved_attempt, current_authorization=moved_auth) == routing.BLOCKED_FROZEN_HEAD_MISMATCH


def test_invalid_targets_and_branch_coordinates_fail_closed() -> None:
    assert route(current_attempt=attempt(repository="Oteryn/Other")) == routing.BLOCKED_STALE_STATE
    for repository in ([], {}, set()):
        assert route(current_attempt=attempt(repository=repository)) == routing.BLOCKED_STALE_STATE
    for base_ref in ("release", "", "@", "-foo", "/main", "main/", "foo//bar", "foo..bar", "main."):
        assert route(current_attempt=attempt(base_ref=base_ref)) == routing.BLOCKED_STALE_STATE


def test_no_generic_auto_merge_direct_merge_or_cleanup_route_exists() -> None:
    text = MODULE_PATH.read_text(encoding="utf-8")
    for forbidden in (
        "enablePullRequestAutoMerge",
        "mergePullRequest",
        "dequeuePullRequest(",
        "direct_merge",
    ):
        assert forbidden not in text, forbidden


def test_policy_requires_atomic_head_and_base_queue_fence_and_reviewed_source_change() -> None:
    text = POLICY.read_text(encoding="utf-8")
    for marker in (
        "atomic head-and-base/queue fence",
        "does not expose an expected base/queue precondition",
        "`dequeuePullRequest` targets the pull request ID",
        "Post-mutation readback cannot repair",
        "Do not model an unknown future capability as a caller-asserted boolean",
        "`BLOCKED_CAPABILITY_UNAVAILABLE`",
        "`enablePullRequestAutoMerge` is not a governed agent enqueue capability",
    ):
        assert marker in text, marker


def main() -> int:
    failures = []
    tests = [(name, fn) for name, fn in sorted(globals().items())
             if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        try:
            fn()
        except Exception as exc:
            failures.append((name, exc))
    if failures:
        for name, exc in failures:
            print(f"FAIL {name}: {exc}")
        return 1
    print(f"PASS {len(tests)} exact-target Merge Queue guard regressions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
