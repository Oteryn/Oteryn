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
REPOSITORY = "Oteryn/Oteryn"
PR_NUMBER = 188
BASE_REF = "main"
PR_HEAD = "a" * 40
OTHER_HEAD = "c" * 40
INTEGRATION_HEAD = "b" * 40
ATTEMPT_ID = "attempt-20260908-0001"
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


def branch_observation(**overrides):
    values = {
        "attempt_id": ATTEMPT_ID,
        "observation_id": "branch-observation-0001",
        "source": "branch_rules",
        "repository": REPOSITORY,
        "base_ref": BASE_REF,
        "merge_queue_required": True,
        "observed_at_epoch_seconds": NOW - 2,
    }
    values.update(overrides)
    return routing.BranchQueueObservation(**values)


def freeze(**overrides):
    values = {
        "repository": REPOSITORY,
        "pr_number": PR_NUMBER,
        "head_sha": PR_HEAD,
    }
    values.update(overrides)
    return routing.CandidateFreeze(**values)


def capabilities(**overrides):
    values = {
        "explicit_enqueue_available": False,
        "auto_merge_available": True,
        "integration_authorized": True,
        "pr_eligible": True,
    }
    values.update(overrides)
    return routing.SubmissionCapabilities(**values)


def route(*, current_attempt=None, observation=None, current_freeze=None, current_capabilities=None, now=NOW):
    return routing.choose_submission_route(
        current_attempt or attempt(),
        observation or branch_observation(),
        current_freeze or freeze(),
        current_capabilities or capabilities(),
        now_epoch_seconds=now,
    )


def queue_entry(**overrides):
    values = {
        "attempt_id": ATTEMPT_ID,
        "observation_id": "queue-observation-0001",
        "repository": REPOSITORY,
        "pr_number": PR_NUMBER,
        "pr_head_sha": PR_HEAD,
        "queue_entry_id": "queue-entry-00000001",
        "active": True,
        "observed_at_epoch_seconds": NOW - 1,
    }
    values.update(overrides)
    return routing.QueueEntryObservation(**values)


def member(**overrides):
    values = {
        "repository": REPOSITORY,
        "pr_number": PR_NUMBER,
        "pr_head_sha": PR_HEAD,
    }
    values.update(overrides)
    return routing.MergeGroupMember(**values)


def merge_group(**overrides):
    values = {
        "attempt_id": ATTEMPT_ID,
        "observation_id": "merge-group-observation-0001",
        "integration_head_sha": INTEGRATION_HEAD,
        "members": (member(),),
        "observed_at_epoch_seconds": NOW - 1,
    }
    values.update(overrides)
    return routing.MergeGroupObservation(**values)


def verify(items, *, current_attempt=None, submitted_at=NOW - 2, now=NOW, current_route=None):
    return routing.verify_queue_admission(
        routing.AUTO_MERGE_MQ_SUBMISSION if current_route is None else current_route,
        current_attempt or attempt(),
        items,
        submission_completed_at_epoch_seconds=submitted_at,
        now_epoch_seconds=now,
    )


def test_explicit_enqueue_is_preferred_when_exposed() -> None:
    result = route(current_capabilities=capabilities(explicit_enqueue_available=True))
    assert result == routing.EXPLICIT_ENQUEUE


def test_auto_merge_is_valid_only_for_fresh_required_mq_state() -> None:
    assert route() == routing.AUTO_MERGE_MQ_SUBMISSION
    assert route(observation=branch_observation(merge_queue_required=False)) == routing.NOT_MQ_TARGET
    stale = branch_observation(
        observed_at_epoch_seconds=NOW - routing.MAX_PREMUTATION_RULE_AGE_SECONDS - 1
    )
    assert route(observation=stale) == routing.BLOCKED_STALE_STATE
    future = branch_observation(observed_at_epoch_seconds=NOW + 1)
    assert route(observation=future) == routing.BLOCKED_STALE_STATE


def test_mq_rule_observation_must_match_same_attempt_repository_and_base() -> None:
    assert route(observation=branch_observation(attempt_id="different-attempt-0001")) == routing.BLOCKED_STALE_STATE
    assert route(observation=branch_observation(repository="Oteryn/Oteryn-Platform")) == routing.BLOCKED_STALE_STATE
    assert route(observation=branch_observation(base_ref="release")) == routing.BLOCKED_STALE_STATE
    assert route(observation=branch_observation(source="cached_policy")) == routing.BLOCKED_STALE_STATE


def test_malformed_rule_source_is_fail_closed() -> None:
    for source in ([], {}, set()):
        assert route(observation=branch_observation(source=source)) == routing.BLOCKED_STALE_STATE


def test_freeze_is_bound_to_same_repository_pr_and_live_head() -> None:
    assert route(current_freeze=freeze(repository="Oteryn/Oteryn-Platform")) == routing.BLOCKED_FROZEN_HEAD_MISMATCH
    assert route(current_freeze=freeze(pr_number=999)) == routing.BLOCKED_FROZEN_HEAD_MISMATCH
    assert route(current_freeze=freeze(head_sha=OTHER_HEAD)) == routing.BLOCKED_FROZEN_HEAD_MISMATCH
    moved = attempt(live_pr_head_sha=OTHER_HEAD)
    assert route(current_attempt=moved) == routing.BLOCKED_FROZEN_HEAD_MISMATCH


def test_missing_authority_or_eligibility_fails_before_tool_choice() -> None:
    assert route(current_capabilities=capabilities(integration_authorized=False)) == routing.BLOCKED_NOT_AUTHORIZED
    assert route(current_capabilities=capabilities(pr_eligible=False)) == routing.BLOCKED_NOT_ELIGIBLE


def test_missing_native_submission_capability_fails_closed() -> None:
    result = route(
        current_capabilities=capabilities(
            explicit_enqueue_available=False,
            auto_merge_available=False,
        )
    )
    assert result == routing.BLOCKED_CAPABILITY_UNAVAILABLE


def test_queue_entry_must_be_current_post_submission_and_exact_identity() -> None:
    assert verify([queue_entry()]) == routing.ENQUEUED
    assert verify([queue_entry(active=False)]) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN
    assert verify([queue_entry(attempt_id="different-attempt-0001")]) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN
    assert verify([queue_entry(repository="Oteryn/Oteryn-Platform")]) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN
    assert verify([queue_entry(pr_number=999)]) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN
    assert verify([queue_entry(pr_head_sha=OTHER_HEAD)]) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN
    assert verify([queue_entry(observed_at_epoch_seconds=NOW - 3)], submitted_at=NOW - 2) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN
    stale = queue_entry(
        observed_at_epoch_seconds=NOW - routing.MAX_POSTMUTATION_EVIDENCE_AGE_SECONDS - 1
    )
    assert verify([stale], submitted_at=NOW - routing.MAX_POSTMUTATION_EVIDENCE_AGE_SECONDS - 2) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN


def test_historical_added_to_queue_event_is_not_terminal_admission_evidence() -> None:
    historical_event = {
        "event": "added_to_merge_queue",
        "repository": REPOSITORY,
        "pr_number": PR_NUMBER,
        "pr_head_sha": PR_HEAD,
    }
    assert verify([historical_event]) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN


def test_merge_group_requires_same_observation_membership_for_exact_pr_head() -> None:
    assert verify([merge_group()]) == routing.ENQUEUED
    assert verify([merge_group(members=(member(pr_number=999),))]) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN
    assert verify([merge_group(members=(member(pr_head_sha=OTHER_HEAD),))]) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN
    assert verify([merge_group(members=(member(repository="Oteryn/Oteryn-Platform"),))]) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN
    assert verify([merge_group(integration_head_sha="not-a-sha")]) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN
    assert verify([merge_group(members=())]) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN
    mixed = merge_group(
        members=(
            member(repository="Oteryn/Oteryn-Platform", pr_number=44, pr_head_sha=OTHER_HEAD),
            member(),
        )
    )
    assert verify([mixed]) == routing.ENQUEUED


def test_non_mq_or_blocked_routes_cannot_be_promoted_by_queue_evidence() -> None:
    for current_route in (
        routing.NOT_MQ_TARGET,
        routing.BLOCKED_NOT_AUTHORIZED,
        routing.BLOCKED_NOT_ELIGIBLE,
        routing.BLOCKED_STALE_STATE,
        routing.BLOCKED_FROZEN_HEAD_MISMATCH,
        routing.BLOCKED_CAPABILITY_UNAVAILABLE,
    ):
        assert verify([queue_entry()], current_route=current_route) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN


def test_malformed_route_selector_is_fail_closed() -> None:
    for current_route in ([], {}, set()):
        assert verify([queue_entry()], current_route=current_route) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN


def test_invalid_git_branch_names_fail_closed() -> None:
    invalid = (
        "",
        "@",
        "/main",
        "main/",
        "foo//bar",
        "foo..bar",
        "main.",
        ".main",
        "foo/.bar",
        "main.lock",
        "foo/bar.lock",
        "foo@{bar",
        "foo bar",
        "foo~bar",
        "foo^bar",
        "foo:bar",
        "foo?bar",
        "foo*bar",
        "foo[bar",
        "foo\\bar",
    )
    for base_ref in invalid:
        assert route(current_attempt=attempt(base_ref=base_ref)) == routing.BLOCKED_STALE_STATE, base_ref
    for base_ref in ("main", "release/1.2", "feature/foo-bar"):
        current_attempt = attempt(base_ref=base_ref)
        observation = branch_observation(base_ref=base_ref)
        assert route(current_attempt=current_attempt, observation=observation) == routing.AUTO_MERGE_MQ_SUBMISSION


def test_malformed_attempt_identity_fails_closed() -> None:
    assert route(current_attempt=attempt(attempt_id="short")) == routing.BLOCKED_STALE_STATE
    assert route(current_attempt=attempt(repository="bad")) == routing.BLOCKED_STALE_STATE
    assert route(current_attempt=attempt(pr_number=0)) == routing.BLOCKED_STALE_STATE
    assert route(current_attempt=attempt(base_ref="../main")) == routing.BLOCKED_STALE_STATE
    assert route(current_attempt=attempt(live_pr_head_sha="bad")) == routing.BLOCKED_STALE_STATE


def test_no_direct_merge_route_exists() -> None:
    route_values = {
        value
        for name, value in vars(routing).items()
        if name.isupper() and isinstance(value, str)
    }
    assert "DIRECT_MERGE" not in route_values
    assert "MERGE_PULL_REQUEST" not in route_values


def test_canonical_policy_explains_fresh_safe_auto_merge_to_mq_boundary() -> None:
    text = POLICY.read_text(encoding="utf-8")
    for marker in (
        "Prefer an explicit native enqueue action",
        "`enablePullRequestAutoMerge`",
        "fresh live GitHub branch-rule or queue-configuration observation",
        "same repository, base branch and submission attempt",
        "frozen candidate must bind the same repository, PR number and current head SHA",
        "fresh current queue-entry readback",
        "merge-group observation whose own membership includes that exact PR and head",
        "Historical `added_to_merge_queue` timeline events alone are not terminal admission proof",
        "not a direct-merge fallback or protection bypass",
        "No bypass or direct merge substitutes for an unavailable enqueue tool",
    ):
        assert marker in text


def main() -> int:
    failures: list[tuple[str, Exception]] = []
    tests = [
        (name, test)
        for name, test in sorted(globals().items())
        if name.startswith("test_") and callable(test)
    ]
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
