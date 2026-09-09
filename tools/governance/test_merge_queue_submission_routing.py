#!/usr/bin/env python3
"""Regressions for exact-head-fenced GitHub Merge Queue submission routing."""

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


def receipt(**overrides):
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


def verify(current_receipt=None, *, current_route=routing.EXPLICIT_ENQUEUE, started_at=NOW - 1, now=NOW):
    return routing.verify_enqueue_receipt(
        current_route,
        attempt(),
        current_receipt or receipt(route=current_route),
        submission_started_at_epoch_seconds=started_at,
        now_epoch_seconds=now,
    )


def test_explicit_enqueue_requires_server_side_expected_head_fence() -> None:
    assert route(
        current_capabilities=capabilities(
            explicit_enqueue_available=True,
            explicit_enqueue_expected_head_fence=True,
        )
    ) == routing.EXPLICIT_ENQUEUE
    assert route(
        current_capabilities=capabilities(
            explicit_enqueue_available=True,
            explicit_enqueue_expected_head_fence=False,
        )
    ) == routing.BLOCKED_CAPABILITY_UNAVAILABLE


def test_protected_executor_requires_trusted_default_branch_and_expected_head_fence() -> None:
    safe = capabilities(
        protected_executor_available=True,
        protected_executor_expected_head_fence=True,
        protected_executor_trusted_default_branch=True,
    )
    assert route(current_capabilities=safe) == routing.PROTECTED_EXECUTOR_ENQUEUE
    assert route(
        current_capabilities=safe._replace(protected_executor_expected_head_fence=False)
    ) == routing.BLOCKED_CAPABILITY_UNAVAILABLE
    assert route(
        current_capabilities=safe._replace(protected_executor_trusted_default_branch=False)
    ) == routing.BLOCKED_CAPABILITY_UNAVAILABLE


def test_no_generic_auto_merge_route_exists() -> None:
    values = {value for name, value in vars(routing).items() if name.isupper() and isinstance(value, str)}
    assert "AUTO_MERGE_MQ_SUBMISSION" not in values
    assert "ENABLE_PULL_REQUEST_AUTO_MERGE" not in values
    assert "DIRECT_MERGE" not in values
    assert "MERGE_PULL_REQUEST" not in values
    assert route() == routing.BLOCKED_CAPABILITY_UNAVAILABLE


def test_authority_eligibility_and_exact_candidate_freeze_fail_closed() -> None:
    safe = capabilities(
        explicit_enqueue_available=True,
        explicit_enqueue_expected_head_fence=True,
    )
    assert route(current_capabilities=safe._replace(integration_authorized=False)) == routing.BLOCKED_NOT_AUTHORIZED
    assert route(current_capabilities=safe._replace(pr_eligible=False)) == routing.BLOCKED_NOT_ELIGIBLE
    assert route(current_freeze=freeze(head_sha=OTHER_HEAD), current_capabilities=safe) == routing.BLOCKED_FROZEN_HEAD_MISMATCH
    assert route(current_attempt=attempt(live_pr_head_sha=OTHER_HEAD), current_capabilities=safe) == routing.BLOCKED_FROZEN_HEAD_MISMATCH


def test_invalid_targets_and_branch_coordinates_fail_closed() -> None:
    safe = capabilities(
        explicit_enqueue_available=True,
        explicit_enqueue_expected_head_fence=True,
    )
    assert route(current_attempt=attempt(repository="Oteryn/Other"), current_capabilities=safe) == routing.BLOCKED_STALE_STATE
    for repository in ([], {}, set()):
        assert route(current_attempt=attempt(repository=repository), current_capabilities=safe) == routing.BLOCKED_STALE_STATE
    for base_ref in ("release", "", "@", "-foo", "/main", "main/", "foo//bar", "foo..bar", "main."):
        assert route(current_attempt=attempt(base_ref=base_ref), current_capabilities=safe) == routing.BLOCKED_STALE_STATE


def test_enqueue_receipt_must_bind_exact_route_attempt_target_head_and_queue_entry() -> None:
    assert verify() == routing.ENQUEUED
    assert verify(receipt(attempt_id="attempt-20260909-9999")) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN
    assert verify(receipt(repository="Oteryn/Oteryn-Game")) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN
    assert verify(receipt(pr_number=PR_NUMBER + 1)) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN
    assert verify(receipt(base_ref="release")) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN
    assert verify(receipt(expected_head_sha=OTHER_HEAD)) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN
    assert verify(receipt(merge_queue_entry_id="wrong")) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN
    executor_receipt = receipt(route=routing.PROTECTED_EXECUTOR_ENQUEUE)
    assert verify(executor_receipt, current_route=routing.PROTECTED_EXECUTOR_ENQUEUE) == routing.ENQUEUED
    assert verify(executor_receipt, current_route=routing.EXPLICIT_ENQUEUE) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN


def test_enqueue_receipt_time_is_current_and_post_attempt_start() -> None:
    assert verify(started_at=NOW, now=NOW) == routing.ENQUEUED
    assert verify(receipt(observed_at_epoch_seconds=NOW - 2), started_at=NOW - 1) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN
    assert verify(receipt(observed_at_epoch_seconds=NOW + 1), now=NOW) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN
    stale_now = NOW + routing.MAX_RECEIPT_AGE_SECONDS + 1
    assert verify(receipt(observed_at_epoch_seconds=NOW), started_at=NOW - 1, now=stale_now) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN


def test_policy_requires_explicit_enqueue_and_rejects_auto_merge_substitution() -> None:
    text = POLICY.read_text(encoding="utf-8")
    for marker in (
        "`enqueuePullRequest`",
        "`expectedHeadOid`",
        "protected-default-branch executor",
        "`enablePullRequestAutoMerge` is not an enqueue capability",
        "No bypass, direct merge or generic auto-merge substitutes for an unavailable enqueue tool",
        "returned Merge Queue entry",
    ):
        assert marker in text, marker


def main() -> int:
    failures = []
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            failures.append((name, exc))
    if failures:
        for name, exc in failures:
            print(f"FAIL {name}: {exc}")
        return 1
    print(f"PASS {len(tests)} exact-head Merge Queue submission regressions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
