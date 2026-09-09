#!/usr/bin/env python3
"""Regressions for the native exact-head Merge Queue submission contract."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("merge_queue_submission_routing.py")
SPEC = importlib.util.spec_from_file_location("merge_queue_submission_routing", MODULE_PATH)
assert SPEC and SPEC.loader
routing = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(routing)

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "docs/agents/policy/ORGANIZATION_AGENT_POLICY.md"
POLICY_JSON = ROOT / "ecosystem/organization-agent-policy.json"
REPOSITORY = "Oteryn/Oteryn-Platform"
PR_NUMBER = 1367
PR_HEAD = "a" * 40
OTHER_HEAD = "c" * 40
ATTEMPT_ID = "attempt-20260909-0001"
REQUEST_UUID = "123e4567-e89b-12d3-a456-426614174000"
RECEIPT_SEQUENCE = 100
POST_SEQUENCE = 101
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


def receipt(**overrides):
    values = {
        "attempt_id": ATTEMPT_ID,
        "repository": REPOSITORY,
        "pr_number": PR_NUMBER,
        "base_ref": "main",
        "expected_head_sha": PR_HEAD,
        "merge_action": "merge_queue",
        "http_status": 202,
        "request_uuid": REQUEST_UUID,
        "observed_at_epoch_seconds": NOW,
        "executor_sequence": RECEIPT_SEQUENCE,
    }
    values.update(overrides)
    return routing.AsyncMergeReceipt(**values)


def post_observation(**overrides):
    values = {
        "source": routing.POST_SUBMISSION_SOURCE,
        "repository": REPOSITORY,
        "pr_number": PR_NUMBER,
        "base_ref": "main",
        "pr_head_sha": PR_HEAD,
        "accepted_request_uuid": REQUEST_UUID,
        "observed_at_epoch_seconds": NOW,
        "executor_sequence": POST_SEQUENCE,
    }
    values.update(overrides)
    return routing.PostSubmissionTargetObservation(**values)


def route(*, current_attempt=None, current_freeze=None, current_authorization=None,
          execution_auth=routing.AUTH_DIRECT_NATIVE, now=NOW):
    return routing.choose_submission_route(
        current_attempt or attempt(),
        current_freeze or freeze(),
        current_authorization or authorization(),
        execution_auth=execution_auth,
        now_epoch_seconds=now,
    )


def test_merge_async_is_the_only_current_operational_exact_head_route() -> None:
    by_operation = {p.operation: p for p in routing.DOCUMENTED_QUEUE_PRIMITIVES}
    assert set(by_operation) == {"merge-async", "enqueuePullRequest"}
    assert routing.primitive_is_operational_exact_head_route(by_operation["merge-async"])
    assert not routing.primitive_is_operational_exact_head_route(by_operation["enqueuePullRequest"])
    assert routing.current_documented_operational_routes() == ("merge-async",)
    assert route() == routing.ASYNC_MERGE_QUEUE


def test_only_direct_native_or_fine_grained_pat_auth_is_operational() -> None:
    assert routing.mutation_auth_is_operational(routing.AUTH_DIRECT_NATIVE)
    assert routing.mutation_auth_is_operational(routing.AUTH_FINE_GRAINED_PAT)
    for auth in (
        routing.AUTH_GITHUB_TOKEN,
        routing.AUTH_CUSTOM_GITHUB_APP,
        "graphql",
        "auto_merge",
        "",
        None,
        True,
    ):
        assert not routing.mutation_auth_is_operational(auth), auth
        assert route(execution_auth=auth) == routing.BLOCKED_CAPABILITY_UNAVAILABLE
    assert route(execution_auth=routing.AUTH_FINE_GRAINED_PAT) == routing.ASYNC_MERGE_QUEUE


def test_callers_cannot_inject_hypothetical_execution_capabilities() -> None:
    assert not hasattr(routing, "SubmissionCapabilities")
    synthetic = routing.DocumentedQueuePrimitive(
        operation="futureQueue",
        queue_specific=True,
        expected_head_fence=True,
        expected_base_queue_fence=True,
        operationally_approved=True,
    )
    assert routing.primitive_is_operational_exact_head_route(synthetic)
    assert synthetic not in routing.DOCUMENTED_QUEUE_PRIMITIVES
    assert routing.current_documented_operational_routes() == ("merge-async",)


def test_merge_async_request_is_exact_head_explicit_queue_and_auth_bound() -> None:
    for auth in (routing.AUTH_DIRECT_NATIVE, routing.AUTH_FINE_GRAINED_PAT):
        request = routing.build_merge_async_request(
            attempt(), freeze(), authorization(), execution_auth=auth, now_epoch_seconds=NOW
        )
        assert request is not None
        assert request.method == "PUT"
        assert request.endpoint == f"/repos/{REPOSITORY}/pulls/{PR_NUMBER}/merge-async"
        assert request.sha == PR_HEAD
        assert request.merge_action == "merge_queue"
    assert routing.build_merge_async_request(
        attempt(), freeze(), authorization(), execution_auth=routing.AUTH_GITHUB_TOKEN,
        now_epoch_seconds=NOW,
    ) is None


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


def test_async_receipt_acceptance_and_reconciliation_semantics() -> None:
    assert routing.verify_async_merge_receipt(
        attempt(), receipt(), now_epoch_seconds=NOW
    ) == routing.SUBMISSION_ACCEPTED
    for status in (200, 409):
        assert routing.verify_async_merge_receipt(
            attempt(), receipt(http_status=status, request_uuid=""), now_epoch_seconds=NOW
        ) == routing.RECONCILE_REQUIRED
    for changes in (
        {"attempt_id": "attempt-20260909-other"},
        {"repository": "Oteryn/Oteryn-Game"},
        {"pr_number": PR_NUMBER + 1},
        {"base_ref": "release"},
        {"expected_head_sha": OTHER_HEAD},
        {"merge_action": "default"},
        {"merge_action": "direct_merge"},
        {"http_status": 201},
        {"request_uuid": "not-a-uuid"},
        {"observed_at_epoch_seconds": NOW - routing.MAX_RECEIPT_AGE_SECONDS - 1},
        {"observed_at_epoch_seconds": NOW + 1},
        {"executor_sequence": 0},
        {"executor_sequence": True},
    ):
        assert routing.verify_async_merge_receipt(
            attempt(), receipt(**changes), now_epoch_seconds=NOW
        ) == routing.BLOCKED_RECEIPT_INVALID, changes


def test_post_submission_target_readback_is_mandatory_and_exact() -> None:
    current_receipt = receipt()
    assert routing.verify_post_submission_target(
        attempt(), current_receipt, post_observation(), now_epoch_seconds=NOW
    ) == routing.POST_SUBMISSION_TARGET_CONFIRMED
    for sequence in (RECEIPT_SEQUENCE - 1, RECEIPT_SEQUENCE):
        assert routing.verify_post_submission_target(
            attempt(), current_receipt, post_observation(executor_sequence=sequence),
            now_epoch_seconds=NOW,
        ) == routing.BLOCKED_POST_SUBMISSION_TARGET_MISMATCH
    for changes in (
        {"source": "cached_post_readback"},
        {"repository": "Oteryn/Oteryn-Game"},
        {"pr_number": PR_NUMBER + 1},
        {"base_ref": "release"},
        {"pr_head_sha": OTHER_HEAD},
        {"accepted_request_uuid": "223e4567-e89b-12d3-a456-426614174000"},
        {"observed_at_epoch_seconds": NOW - routing.MAX_POST_SUBMISSION_AGE_SECONDS - 1},
        {"observed_at_epoch_seconds": NOW + 1},
        {"executor_sequence": 0},
        {"executor_sequence": True},
    ):
        assert routing.verify_post_submission_target(
            attempt(), current_receipt, post_observation(**changes), now_epoch_seconds=NOW
        ) == routing.BLOCKED_POST_SUBMISSION_TARGET_MISMATCH, changes


def test_no_generic_auto_merge_direct_merge_or_ambiguous_cleanup_route_exists() -> None:
    text = MODULE_PATH.read_text(encoding="utf-8")
    for forbidden in (
        "enablePullRequestAutoMerge",
        "mergePullRequest",
        "dequeuePullRequest(",
        "direct_merge",
    ):
        assert forbidden not in text, forbidden


def test_policy_declares_app_free_auth_and_terminal_proof() -> None:
    text = POLICY.read_text(encoding="utf-8")
    for marker in (
        "Policy version: `3.1.0`",
        "merge_action=\"merge_queue\"",
        "does **not** require or authorize creating a dedicated custom GitHub App",
        "fine-grained personal access token",
        "keep built-in `GITHUB_TOKEN` read-only",
        "Do not use `GITHUB_TOKEN` as the queue mutation credential",
        "`BLOCKED_CAPABILITY_UNAVAILABLE`",
        "`merge_group` aggregate gate",
    ):
        assert marker in text, marker
    policy_json = json.loads(POLICY_JSON.read_text(encoding="utf-8"))
    assert policy_json["policy_version"] == "3.1.0"


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
    print(f"PASS {len(tests)} native exact-head Merge Queue regressions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
