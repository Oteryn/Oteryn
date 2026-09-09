#!/usr/bin/env python3
"""Regressions for exact-target Merge Queue submission routing."""

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


def authorization(**overrides):
    values = {
        "source": routing.AUTHORIZATION_SOURCE,
        "repository": REPOSITORY,
        "pr_number": PR_NUMBER,
        "base_ref": BASE_REF,
        "pr_head_sha": PR_HEAD,
        "integration_authorized": True,
        "pr_eligible": True,
        "observed_at_epoch_seconds": NOW,
    }
    values.update(overrides)
    return routing.SubmissionAuthorization(**values)


def capabilities(**overrides):
    values = {
        "async_merge_available": False,
        "async_merge_expected_head_fence": False,
        "async_merge_expected_base_fence": False,
        "async_merge_merge_queue_action": False,
        "explicit_enqueue_available": False,
        "explicit_enqueue_expected_head_fence": False,
        "explicit_enqueue_expected_base_fence": False,
        "protected_executor_available": False,
        "protected_executor_expected_head_fence": False,
        "protected_executor_expected_base_fence": False,
        "protected_executor_trusted_default_branch": False,
    }
    values.update(overrides)
    return routing.SubmissionCapabilities(**values)


def route(*, current_attempt=None, current_freeze=None, current_authorization=None,
          current_capabilities=None, now=NOW):
    return routing.choose_submission_route(
        current_attempt or attempt(),
        current_freeze or freeze(),
        current_authorization or authorization(),
        current_capabilities or capabilities(),
        now_epoch_seconds=now,
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
        "merge_queue_id": "MQ_platform_main_001",
        "merge_queue_resource_path": f"/{REPOSITORY}/queue/main",
        "merge_queue_url": f"https://github.com/{REPOSITORY}/queue/main",
        "observed_at_epoch_seconds": NOW,
    }
    values.update(overrides)
    return routing.EnqueueReceipt(**values)


def verify_async(current_receipt=None, *, started_at=NOW - 1, now=NOW):
    return routing.verify_async_merge_receipt(
        attempt(), current_receipt or async_receipt(),
        submission_started_at_epoch_seconds=started_at,
        now_epoch_seconds=now,
    )


def verify_enqueue(current_receipt=None, *, current_route=routing.EXPLICIT_ENQUEUE,
                   started_at=NOW - 1, now=NOW):
    return routing.verify_enqueue_receipt(
        current_route, attempt(),
        current_receipt or enqueue_receipt(route=current_route),
        submission_started_at_epoch_seconds=started_at,
        now_epoch_seconds=now,
    )


def test_documented_head_fenced_surfaces_are_not_safe_without_atomic_base_fence() -> None:
    current_async = capabilities(
        async_merge_available=True,
        async_merge_expected_head_fence=True,
        async_merge_merge_queue_action=True,
    )
    assert route(current_capabilities=current_async) == routing.BLOCKED_CAPABILITY_UNAVAILABLE

    current_graphql = capabilities(
        explicit_enqueue_available=True,
        explicit_enqueue_expected_head_fence=True,
    )
    assert route(current_capabilities=current_graphql) == routing.BLOCKED_CAPABILITY_UNAVAILABLE

    current_executor = capabilities(
        protected_executor_available=True,
        protected_executor_expected_head_fence=True,
        protected_executor_trusted_default_branch=True,
    )
    assert route(current_capabilities=current_executor) == routing.BLOCKED_CAPABILITY_UNAVAILABLE


def test_hypothetical_atomic_base_fenced_native_route_is_preferred() -> None:
    safe = capabilities(
        async_merge_available=True,
        async_merge_expected_head_fence=True,
        async_merge_expected_base_fence=True,
        async_merge_merge_queue_action=True,
        explicit_enqueue_available=True,
        explicit_enqueue_expected_head_fence=True,
        explicit_enqueue_expected_base_fence=True,
        protected_executor_available=True,
        protected_executor_expected_head_fence=True,
        protected_executor_expected_base_fence=True,
        protected_executor_trusted_default_branch=True,
    )
    assert route(current_capabilities=safe) == routing.ASYNC_MERGE_QUEUE


def test_atomic_base_fence_is_required_on_every_route() -> None:
    async_safe = capabilities(
        async_merge_available=True,
        async_merge_expected_head_fence=True,
        async_merge_expected_base_fence=True,
        async_merge_merge_queue_action=True,
    )
    assert route(current_capabilities=async_safe) == routing.ASYNC_MERGE_QUEUE
    assert route(current_capabilities=async_safe._replace(
        async_merge_expected_base_fence=False)) == routing.BLOCKED_CAPABILITY_UNAVAILABLE

    enqueue_safe = capabilities(
        explicit_enqueue_available=True,
        explicit_enqueue_expected_head_fence=True,
        explicit_enqueue_expected_base_fence=True,
    )
    assert route(current_capabilities=enqueue_safe) == routing.EXPLICIT_ENQUEUE
    assert route(current_capabilities=enqueue_safe._replace(
        explicit_enqueue_expected_base_fence=False)) == routing.BLOCKED_CAPABILITY_UNAVAILABLE

    executor_safe = capabilities(
        protected_executor_available=True,
        protected_executor_expected_head_fence=True,
        protected_executor_expected_base_fence=True,
        protected_executor_trusted_default_branch=True,
    )
    assert route(current_capabilities=executor_safe) == routing.PROTECTED_EXECUTOR_ENQUEUE
    assert route(current_capabilities=executor_safe._replace(
        protected_executor_expected_base_fence=False)) == routing.BLOCKED_CAPABILITY_UNAVAILABLE


def test_unsafe_async_surface_does_not_suppress_future_safe_enqueue_fallback() -> None:
    values = capabilities(
        async_merge_available=True,
        async_merge_expected_head_fence=True,
        async_merge_expected_base_fence=False,
        async_merge_merge_queue_action=True,
        explicit_enqueue_available=True,
        explicit_enqueue_expected_head_fence=True,
        explicit_enqueue_expected_base_fence=True,
    )
    assert route(current_capabilities=values) == routing.EXPLICIT_ENQUEUE


def test_no_generic_auto_merge_or_direct_merge_route_exists() -> None:
    values = {value for name, value in vars(routing).items()
              if name.isupper() and isinstance(value, str)}
    for forbidden in (
        "AUTO_MERGE_MQ_SUBMISSION",
        "ENABLE_PULL_REQUEST_AUTO_MERGE",
        "DIRECT_MERGE",
        "MERGE_PULL_REQUEST",
    ):
        assert forbidden not in values
    assert route() == routing.BLOCKED_CAPABILITY_UNAVAILABLE


def test_authorization_and_eligibility_are_exact_target_bound_and_fresh() -> None:
    safe = capabilities(
        async_merge_available=True,
        async_merge_expected_head_fence=True,
        async_merge_expected_base_fence=True,
        async_merge_merge_queue_action=True,
    )
    assert route(current_authorization=authorization(integration_authorized=False),
                 current_capabilities=safe) == routing.BLOCKED_NOT_AUTHORIZED
    assert route(current_authorization=authorization(pr_eligible=False),
                 current_capabilities=safe) == routing.BLOCKED_NOT_ELIGIBLE
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
        assert route(current_authorization=authorization(**changes),
                     current_capabilities=safe) == routing.BLOCKED_STALE_STATE, changes


def test_exact_candidate_freeze_still_fail_closed() -> None:
    safe = capabilities(
        async_merge_available=True,
        async_merge_expected_head_fence=True,
        async_merge_expected_base_fence=True,
        async_merge_merge_queue_action=True,
    )
    assert route(current_freeze=freeze(head_sha=OTHER_HEAD),
                 current_capabilities=safe) == routing.BLOCKED_FROZEN_HEAD_MISMATCH
    moved_attempt = attempt(live_pr_head_sha=OTHER_HEAD)
    moved_auth = authorization(pr_head_sha=OTHER_HEAD)
    assert route(current_attempt=moved_attempt, current_authorization=moved_auth,
                 current_capabilities=safe) == routing.BLOCKED_FROZEN_HEAD_MISMATCH


def test_invalid_targets_and_branch_coordinates_fail_closed() -> None:
    safe = capabilities(
        async_merge_available=True,
        async_merge_expected_head_fence=True,
        async_merge_expected_base_fence=True,
        async_merge_merge_queue_action=True,
    )
    assert route(current_attempt=attempt(repository="Oteryn/Other"),
                 current_capabilities=safe) == routing.BLOCKED_STALE_STATE
    for repository in ([], {}, set()):
        assert route(current_attempt=attempt(repository=repository),
                     current_capabilities=safe) == routing.BLOCKED_STALE_STATE
    for base_ref in ("release", "", "@", "-foo", "/main", "main/", "foo//bar", "foo..bar", "main."):
        assert route(current_attempt=attempt(base_ref=base_ref),
                     current_capabilities=safe) == routing.BLOCKED_STALE_STATE


def test_async_receipt_is_not_terminal_integration_proof() -> None:
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


def test_enqueue_receipt_retains_exact_target_and_queue_identity() -> None:
    assert verify_enqueue() == routing.ENQUEUED
    for changes in (
        {"expected_head_sha": OTHER_HEAD},
        {"merge_queue_entry_id": "wrong"},
        {"merge_queue_id": ""},
        {"merge_queue_resource_path": f"/{REPOSITORY}/queue/release"},
        {"merge_queue_url": f"https://github.com/{REPOSITORY}/queue/release"},
    ):
        assert verify_enqueue(enqueue_receipt(**changes)) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN, changes


def test_policy_requires_atomic_head_and_base_queue_fence() -> None:
    text = POLICY.read_text(encoding="utf-8")
    for marker in (
        "atomic head-and-base/queue fence",
        "`expectedHeadOid`",
        "does not expose an expected base/queue precondition",
        "`dequeuePullRequest` targets the pull request ID",
        "post-mutation readback cannot repair",
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
    print(f"PASS {len(tests)} exact-target Merge Queue routing regressions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
