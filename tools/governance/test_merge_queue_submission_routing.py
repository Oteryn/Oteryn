#!/usr/bin/env python3
"""Regressions for GitHub-native exact-head Merge Queue submission routing."""

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
BASE_REF = "main"
PR_HEAD = "a" * 40
OTHER_HEAD = "c" * 40
ATTEMPT_ID = "attempt-20260909-0001"
REQUEST_UUID = "630b9d5e-3f2a-4f7e-8b0c-2d5f9a8c1e42"
NOW = 1_800_000_000


def attempt(**overrides):
    values = {
        "attempt_id": ATTEMPT_ID,
        "repository": REPOSITORY,
        "pr_number": PR_NUMBER,
        "base_ref": BASE_REF,
        "live_pr_head_sha": PR_HEAD,
    }
    values.update(overrides)
    return routing.SubmissionAttempt(**values)


def freeze(**overrides):
    values = {"repository": REPOSITORY, "pr_number": PR_NUMBER, "head_sha": PR_HEAD}
    values.update(overrides)
    return routing.CandidateFreeze(**values)


def capabilities(**overrides):
    values = {
        "async_merge_available": False,
        "async_merge_expected_head_fence": False,
        "async_merge_merge_queue_action": False,
        "explicit_enqueue_available": False,
        "explicit_enqueue_expected_head_fence": False,
        "protected_executor_available": False,
        "protected_executor_expected_head_fence": False,
        "protected_executor_trusted_default_branch": False,
        "integration_authorized": True,
        "pr_eligible": True,
    }
    values.update(overrides)
    return routing.SubmissionCapabilities(**values)


def route(*, current_attempt=None, current_freeze=None, current_capabilities=None):
    return routing.choose_submission_route(
        current_attempt or attempt(),
        current_freeze or freeze(),
        current_capabilities or capabilities(),
    )


def async_receipt(**overrides):
    values = {
        "route": routing.ASYNC_MERGE_QUEUE,
        "attempt_id": ATTEMPT_ID,
        "repository": REPOSITORY,
        "pr_number": PR_NUMBER,
        "base_ref": BASE_REF,
        "expected_head_sha": PR_HEAD,
        "merge_action": "merge_queue",
        "request_uuid": REQUEST_UUID,
        "http_status": 202,
        "observed_at_epoch_seconds": NOW,
    }
    values.update(overrides)
    return routing.AsyncMergeReceipt(**values)


def enqueue_receipt(**overrides):
    values = {
        "route": routing.EXPLICIT_ENQUEUE,
        "attempt_id": ATTEMPT_ID,
        "repository": REPOSITORY,
        "pr_number": PR_NUMBER,
        "base_ref": BASE_REF,
        "expected_head_sha": PR_HEAD,
        "merge_queue_entry_id": "MQE_queueentry0001",
        "observed_at_epoch_seconds": NOW,
    }
    values.update(overrides)
    return routing.EnqueueReceipt(**values)


def verify_async(current_receipt=None, *, started_at=NOW - 1, now=NOW):
    return routing.verify_async_merge_receipt(
        attempt(),
        current_receipt or async_receipt(),
        submission_started_at_epoch_seconds=started_at,
        now_epoch_seconds=now,
    )


def verify_enqueue(current_receipt=None, *, current_route=routing.EXPLICIT_ENQUEUE, started_at=NOW - 1, now=NOW):
    return routing.verify_enqueue_receipt(
        current_route,
        attempt(),
        current_receipt or enqueue_receipt(route=current_route),
        submission_started_at_epoch_seconds=started_at,
        now_epoch_seconds=now,
    )


def test_native_async_merge_queue_is_preferred() -> None:
    safe = capabilities(
        async_merge_available=True,
        async_merge_expected_head_fence=True,
        async_merge_merge_queue_action=True,
        explicit_enqueue_available=True,
        explicit_enqueue_expected_head_fence=True,
        protected_executor_available=True,
        protected_executor_expected_head_fence=True,
        protected_executor_trusted_default_branch=True,
    )
    assert route(current_capabilities=safe) == routing.ASYNC_MERGE_QUEUE


def test_async_merge_requires_exact_head_fence_and_explicit_merge_queue_action() -> None:
    safe = capabilities(
        async_merge_available=True,
        async_merge_expected_head_fence=True,
        async_merge_merge_queue_action=True,
    )
    assert route(current_capabilities=safe) == routing.ASYNC_MERGE_QUEUE
    assert route(current_capabilities=safe._replace(async_merge_expected_head_fence=False)) == routing.BLOCKED_CAPABILITY_UNAVAILABLE
    assert route(current_capabilities=safe._replace(async_merge_merge_queue_action=False)) == routing.BLOCKED_CAPABILITY_UNAVAILABLE


def test_unsafe_async_surface_does_not_suppress_safe_enqueue_fallback() -> None:
    values = capabilities(
        async_merge_available=True,
        async_merge_expected_head_fence=False,
        async_merge_merge_queue_action=True,
        explicit_enqueue_available=True,
        explicit_enqueue_expected_head_fence=True,
    )
    assert route(current_capabilities=values) == routing.EXPLICIT_ENQUEUE


def test_explicit_enqueue_and_protected_executor_remain_safe_fallbacks() -> None:
    assert route(
        current_capabilities=capabilities(
            explicit_enqueue_available=True,
            explicit_enqueue_expected_head_fence=True,
        )
    ) == routing.EXPLICIT_ENQUEUE
    executor = capabilities(
        protected_executor_available=True,
        protected_executor_expected_head_fence=True,
        protected_executor_trusted_default_branch=True,
    )
    assert route(current_capabilities=executor) == routing.PROTECTED_EXECUTOR_ENQUEUE
    assert route(current_capabilities=executor._replace(protected_executor_trusted_default_branch=False)) == routing.BLOCKED_CAPABILITY_UNAVAILABLE


def test_no_generic_auto_merge_or_direct_merge_route_exists() -> None:
    values = {value for name, value in vars(routing).items() if name.isupper() and isinstance(value, str)}
    for forbidden in (
        "AUTO_MERGE_MQ_SUBMISSION",
        "ENABLE_PULL_REQUEST_AUTO_MERGE",
        "DIRECT_MERGE",
        "MERGE_PULL_REQUEST",
    ):
        assert forbidden not in values
    assert route() == routing.BLOCKED_CAPABILITY_UNAVAILABLE


def test_authority_eligibility_and_exact_candidate_freeze_fail_closed() -> None:
    safe = capabilities(
        async_merge_available=True,
        async_merge_expected_head_fence=True,
        async_merge_merge_queue_action=True,
    )
    assert route(current_capabilities=safe._replace(integration_authorized=False)) == routing.BLOCKED_NOT_AUTHORIZED
    assert route(current_capabilities=safe._replace(pr_eligible=False)) == routing.BLOCKED_NOT_ELIGIBLE
    assert route(current_freeze=freeze(head_sha=OTHER_HEAD), current_capabilities=safe) == routing.BLOCKED_FROZEN_HEAD_MISMATCH
    assert route(current_attempt=attempt(live_pr_head_sha=OTHER_HEAD), current_capabilities=safe) == routing.BLOCKED_FROZEN_HEAD_MISMATCH


def test_invalid_targets_and_branch_coordinates_fail_closed() -> None:
    safe = capabilities(
        async_merge_available=True,
        async_merge_expected_head_fence=True,
        async_merge_merge_queue_action=True,
    )
    assert route(current_attempt=attempt(repository="Oteryn/Other"), current_capabilities=safe) == routing.BLOCKED_STALE_STATE
    for repository in ([], {}, set()):
        assert route(current_attempt=attempt(repository=repository), current_capabilities=safe) == routing.BLOCKED_STALE_STATE
    for base_ref in ("release", "", "@", "-foo", "/main", "main/", "foo//bar", "foo..bar", "main."):
        assert route(current_attempt=attempt(base_ref=base_ref), current_capabilities=safe) == routing.BLOCKED_STALE_STATE


def test_async_receipt_proves_only_exact_202_merge_queue_request_acceptance() -> None:
    assert verify_async() == routing.SUBMISSION_ACCEPTED
    for changes in (
        {"route": routing.EXPLICIT_ENQUEUE},
        {"attempt_id": "attempt-20260909-9999"},
        {"repository": "Oteryn/Oteryn-Game"},
        {"pr_number": PR_NUMBER + 1},
        {"base_ref": "release"},
        {"expected_head_sha": OTHER_HEAD},
        {"merge_action": "default"},
        {"merge_action": "direct_merge"},
        {"request_uuid": "not-a-uuid"},
        {"http_status": 200},
        {"http_status": 409},
    ):
        assert verify_async(async_receipt(**changes)) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN, changes


def test_async_receipt_time_is_current_and_post_attempt_start() -> None:
    assert verify_async(started_at=NOW, now=NOW) == routing.SUBMISSION_ACCEPTED
    assert verify_async(async_receipt(observed_at_epoch_seconds=NOW - 2), started_at=NOW - 1) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN
    assert verify_async(async_receipt(observed_at_epoch_seconds=NOW + 1), now=NOW) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN
    stale_now = NOW + routing.MAX_RECEIPT_AGE_SECONDS + 1
    assert verify_async(async_receipt(observed_at_epoch_seconds=NOW), started_at=NOW - 1, now=stale_now) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN


def test_graphql_enqueue_receipt_still_binds_exact_target_and_queue_entry() -> None:
    assert verify_enqueue() == routing.ENQUEUED
    assert verify_enqueue(enqueue_receipt(expected_head_sha=OTHER_HEAD)) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN
    assert verify_enqueue(enqueue_receipt(merge_queue_entry_id="wrong")) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN
    executor_receipt = enqueue_receipt(route=routing.PROTECTED_EXECUTOR_ENQUEUE)
    assert verify_enqueue(executor_receipt, current_route=routing.PROTECTED_EXECUTOR_ENQUEUE) == routing.ENQUEUED
    assert verify_enqueue(executor_receipt, current_route=routing.EXPLICIT_ENQUEUE) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN


def test_policy_prefers_native_async_merge_queue_and_keeps_safe_fallbacks() -> None:
    text = POLICY.read_text(encoding="utf-8")
    for marker in (
        "`merge-async`",
        '`merge_action="merge_queue"`',
        "exact qualified/frozen PR head",
        "`enqueuePullRequest`",
        "`expectedHeadOid`",
        "`enablePullRequestAutoMerge` is not a governed agent enqueue capability",
        "`direct_merge`",
        "asynchronous merge request UUID",
    ):
        assert marker in text, marker


def main() -> int:
    failures = []
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        try:
            fn()
        except Exception as exc:
            failures.append((name, exc))
    if failures:
        for name, exc in failures:
            print(f"FAIL {name}: {exc}")
        return 1
    print(f"PASS {len(tests)} GitHub-native Merge Queue routing regressions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
