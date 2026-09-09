#!/usr/bin/env python3
"""Regressions for connector-native GitHub Merge Queue submission routing."""

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
REPOSITORY = "Oteryn/Oteryn-Platform"
PR_NUMBER = 1367
BASE_REF = "main"
PR_HEAD = "a" * 40
OTHER_HEAD = "c" * 40
WORKFLOW_SHA = "d" * 40
INTEGRATION_HEAD = "b" * 40
ATTEMPT_ID = "attempt-20260909-0001"
RUN_ID = 34290000001
RUN_ATTEMPT = 1
COMMENT_ID = 5593000001
PROOF_COMMENT_ID = 5593000002
NOW = 1_800_000_000
OBSERVED_AT = NOW - 3
LIVE_HEAD_AT = NOW - 1
OBSERVATION_ID = f"mq-preflight-{RUN_ID}-{RUN_ATTEMPT}-{COMMENT_ID}"
QUEUE_ID = "MQ_queue123456789"
RESOURCE_PATH = f"/{REPOSITORY}/queue/{BASE_REF}"
QUEUE_URL = f"https://github.com{RESOURCE_PATH}"


def attempt(**overrides):
    values = {"attempt_id": ATTEMPT_ID, "repository": REPOSITORY, "pr_number": PR_NUMBER, "base_ref": BASE_REF, "live_pr_head_sha": PR_HEAD}
    values.update(overrides)
    return routing.SubmissionAttempt(**values)


def branch_observation(**overrides):
    values = {
        "attempt_id": ATTEMPT_ID,
        "observation_id": OBSERVATION_ID,
        "source": routing.PREFLIGHT_SOURCE,
        "control_repository": routing.CONTROL_REPOSITORY,
        "control_issue_number": routing.CONTROL_ISSUE_NUMBER,
        "repository": REPOSITORY,
        "pr_number": PR_NUMBER,
        "base_ref": BASE_REF,
        "pr_head_sha": PR_HEAD,
        "merge_queue_required": True,
        "queue_id": QUEUE_ID,
        "resource_path": RESOURCE_PATH,
        "url": QUEUE_URL,
        "trigger_comment_id": COMMENT_ID,
        "proof_comment_id": PROOF_COMMENT_ID,
        "proof_comment_author_login": routing.PREFLIGHT_PROOF_AUTHOR,
        "workflow_run_id": RUN_ID,
        "workflow_run_attempt": RUN_ATTEMPT,
        "workflow_sha": WORKFLOW_SHA,
        "observed_at_epoch_seconds": OBSERVED_AT,
        "expires_at_epoch_seconds": OBSERVED_AT + routing.MAX_PREMUTATION_RULE_AGE_SECONDS,
    }
    values.update(overrides)
    return routing.BranchQueueObservation(**values)


def proof_comment(observation=None, **overrides):
    observation = observation or branch_observation()
    canonical = json.dumps(routing._proof_payload(observation), sort_keys=True, separators=(",", ":"))
    values = {
        "repository": routing.CONTROL_REPOSITORY,
        "issue_number": routing.CONTROL_ISSUE_NUMBER,
        "comment_id": observation.proof_comment_id,
        "author_login": routing.PREFLIGHT_PROOF_AUTHOR,
        "body": "OTERYN_MQ_PREFLIGHT_V1\n```json\n" + canonical + "\n```",
        "observed_at_epoch_seconds": NOW - 1,
    }
    values.update(overrides)
    return routing.ProofCommentObservation(**values)


def workflow_run(**overrides):
    values = {
        "repository": routing.CONTROL_REPOSITORY,
        "workflow_run_id": RUN_ID,
        "workflow_run_attempt": RUN_ATTEMPT,
        "workflow_path": routing.PREFLIGHT_WORKFLOW_PATH,
        "event": "issue_comment",
        "status": "completed",
        "conclusion": "success",
        "head_branch": "main",
        "head_sha": WORKFLOW_SHA,
        "observed_at_epoch_seconds": NOW - 1,
    }
    values.update(overrides)
    return routing.WorkflowRunObservation(**values)


def live_head(**overrides):
    values = {
        "source": routing.LIVE_HEAD_SOURCE,
        "repository": REPOSITORY,
        "pr_number": PR_NUMBER,
        "base_ref": BASE_REF,
        "pr_head_sha": PR_HEAD,
        "observed_at_epoch_seconds": LIVE_HEAD_AT,
    }
    values.update(overrides)
    return routing.LiveHeadObservation(**values)


def freeze(**overrides):
    values = {"repository": REPOSITORY, "pr_number": PR_NUMBER, "head_sha": PR_HEAD}
    values.update(overrides)
    return routing.CandidateFreeze(**values)


def capabilities(**overrides):
    values = {"explicit_enqueue_available": False, "auto_merge_available": True, "integration_authorized": True, "pr_eligible": True}
    values.update(overrides)
    return routing.SubmissionCapabilities(**values)


def route(*, current_attempt=None, observation=None, proof=None, workflow=None, head_read=None, current_freeze=None, current_capabilities=None, now=NOW):
    current_observation = observation or branch_observation()
    return routing.choose_submission_route(
        current_attempt or attempt(), current_observation, proof or proof_comment(current_observation),
        workflow or workflow_run(), head_read or live_head(), current_freeze or freeze(),
        current_capabilities or capabilities(), now_epoch_seconds=now,
    )


def queue_entry(**overrides):
    values = {"attempt_id": ATTEMPT_ID, "observation_id": "queue-observation-0001", "repository": REPOSITORY, "pr_number": PR_NUMBER, "pr_head_sha": PR_HEAD, "queue_entry_id": "queue-entry-00000001", "active": True, "observed_at_epoch_seconds": NOW - 1}
    values.update(overrides)
    return routing.QueueEntryObservation(**values)


def member(**overrides):
    values = {"repository": REPOSITORY, "pr_number": PR_NUMBER, "pr_head_sha": PR_HEAD}
    values.update(overrides)
    return routing.MergeGroupMember(**values)


def merge_group(**overrides):
    values = {"attempt_id": ATTEMPT_ID, "observation_id": "merge-group-observation-0001", "integration_head_sha": INTEGRATION_HEAD, "members": (member(),), "observed_at_epoch_seconds": NOW - 1}
    values.update(overrides)
    return routing.MergeGroupObservation(**values)


def verify(items, *, submitted_at=NOW - 2, current_route=None):
    return routing.verify_queue_admission(
        routing.AUTO_MERGE_MQ_SUBMISSION if current_route is None else current_route,
        attempt(), items, submission_completed_at_epoch_seconds=submitted_at, now_epoch_seconds=NOW,
    )


def test_auto_merge_requires_authenticated_central_preflight_successful_run_and_live_comment() -> None:
    assert route() == routing.AUTO_MERGE_MQ_SUBMISSION
    for changes in (
        {"source": "cached_policy"},
        {"control_repository": "Oteryn/Oteryn-Platform"},
        {"control_issue_number": 190},
        {"repository": "Oteryn/Oteryn-Game"},
        {"pr_number": PR_NUMBER + 1},
        {"pr_head_sha": OTHER_HEAD},
        {"queue_id": "wrong"},
        {"proof_comment_id": 0},
        {"proof_comment_author_login": "blakinio"},
        {"workflow_sha": OTHER_HEAD},
    ):
        changed = branch_observation(**changes)
        assert route(observation=changed, proof=proof_comment(changed)) == routing.BLOCKED_STALE_STATE, changes
    for changes in (
        {"repository": "Oteryn/Oteryn-Platform"},
        {"workflow_run_id": RUN_ID + 1},
        {"workflow_run_attempt": RUN_ATTEMPT + 1},
        {"workflow_path": ".github/workflows/ci.yml"},
        {"event": "pull_request"},
        {"status": "in_progress"},
        {"conclusion": "failure"},
        {"head_branch": "other"},
        {"head_sha": OTHER_HEAD},
    ):
        assert route(workflow=workflow_run(**changes)) == routing.BLOCKED_STALE_STATE, changes


def test_proof_comment_must_be_fresh_github_authored_exact_body_and_identity() -> None:
    observation = branch_observation()
    assert route(observation=observation, proof=proof_comment(observation)) == routing.AUTO_MERGE_MQ_SUBMISSION
    for changes in (
        {"repository": "Oteryn/Oteryn-Platform"},
        {"issue_number": 190},
        {"comment_id": PROOF_COMMENT_ID + 1},
        {"author_login": "blakinio"},
        {"body": "OTERYN_MQ_PREFLIGHT_V1\n```json\n{}\n```"},
        {"observed_at_epoch_seconds": OBSERVED_AT - 1},
        {"observed_at_epoch_seconds": NOW - routing.MAX_PREMUTATION_RULE_AGE_SECONDS - 1},
    ):
        assert route(observation=observation, proof=proof_comment(observation, **changes)) == routing.BLOCKED_STALE_STATE, changes


def test_live_head_must_be_fresh_exact_and_after_preflight() -> None:
    assert route() == routing.AUTO_MERGE_MQ_SUBMISSION
    for changes in (
        {"source": "cached_pr"},
        {"repository": "Oteryn/Oteryn-Game"},
        {"pr_number": PR_NUMBER + 1},
        {"base_ref": "release"},
        {"pr_head_sha": OTHER_HEAD},
        {"observed_at_epoch_seconds": OBSERVED_AT - 1},
        {"observed_at_epoch_seconds": NOW - routing.MAX_LIVE_HEAD_AGE_SECONDS - 1},
    ):
        assert route(head_read=live_head(**changes)) == routing.BLOCKED_STALE_STATE, changes


def test_only_four_oteryn_targets_and_unhashable_repository_fail_closed() -> None:
    assert routing.ALLOWED_TARGET_REPOSITORIES == {"Oteryn/Oteryn", "Oteryn/Oteryn-Game", "Oteryn/Oteryn-Platform", "Oteryn/Oteryn-Atlas"}
    assert route(current_attempt=attempt(repository="Oteryn/Other")) == routing.BLOCKED_STALE_STATE
    for repository in ([], {}, set()):
        assert route(current_attempt=attempt(repository=repository)) == routing.BLOCKED_STALE_STATE


def test_preflight_freshness_freeze_authority_and_capability_fail_closed() -> None:
    stale_at = NOW - routing.MAX_PREMUTATION_RULE_AGE_SECONDS - 1
    stale = branch_observation(observed_at_epoch_seconds=stale_at, expires_at_epoch_seconds=stale_at + routing.MAX_PREMUTATION_RULE_AGE_SECONDS)
    assert route(observation=stale, proof=proof_comment(stale)) == routing.BLOCKED_STALE_STATE
    assert route(current_freeze=freeze(head_sha=OTHER_HEAD)) == routing.BLOCKED_FROZEN_HEAD_MISMATCH
    assert route(current_attempt=attempt(live_pr_head_sha=OTHER_HEAD)) == routing.BLOCKED_FROZEN_HEAD_MISMATCH
    assert route(current_capabilities=capabilities(integration_authorized=False)) == routing.BLOCKED_NOT_AUTHORIZED
    assert route(current_capabilities=capabilities(pr_eligible=False)) == routing.BLOCKED_NOT_ELIGIBLE
    assert route(current_capabilities=capabilities(auto_merge_available=False)) == routing.BLOCKED_CAPABILITY_UNAVAILABLE
    assert route(current_capabilities=capabilities(explicit_enqueue_available=True)) == routing.EXPLICIT_ENQUEUE


def test_post_mutation_queue_evidence_is_strictly_later_and_exact() -> None:
    assert verify([queue_entry()]) == routing.ENQUEUED
    assert verify([queue_entry(observed_at_epoch_seconds=NOW - 2)]) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN
    assert verify([queue_entry(pr_head_sha=OTHER_HEAD)]) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN
    assert verify([queue_entry(repository="Oteryn/Oteryn-Game")]) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN
    assert verify([queue_entry(active=False)]) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN
    assert verify([merge_group()]) == routing.ENQUEUED
    assert verify([merge_group(observed_at_epoch_seconds=NOW - 2)]) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN
    assert verify([merge_group(members=(member(pr_number=999),))]) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN


def test_historical_timeline_blocked_routes_invalid_refs_and_direct_merge_never_pass() -> None:
    historical = {"event": "added_to_merge_queue", "repository": REPOSITORY, "pr_number": PR_NUMBER, "pr_head_sha": PR_HEAD}
    assert verify([historical]) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN
    for blocked in (routing.NOT_MQ_TARGET, routing.BLOCKED_NOT_AUTHORIZED, routing.BLOCKED_NOT_ELIGIBLE, routing.BLOCKED_STALE_STATE, routing.BLOCKED_FROZEN_HEAD_MISMATCH, routing.BLOCKED_CAPABILITY_UNAVAILABLE):
        assert verify([queue_entry()], current_route=blocked) == routing.BLOCKED_QUEUE_ADMISSION_UNPROVEN
    for base_ref in ("", "@", "-foo", "/main", "main/", "foo//bar", "foo..bar", "main.", ".main", "main.lock", "foo@{bar", "foo bar", "foo~bar", "foo^bar", "foo:bar", "foo?bar", "foo*bar", "foo[bar", "foo\\bar"):
        assert route(current_attempt=attempt(base_ref=base_ref)) == routing.BLOCKED_STALE_STATE
    values = {v for k, v in vars(routing).items() if k.isupper() and isinstance(v, str)}
    assert "DIRECT_MERGE" not in values and "MERGE_PULL_REQUEST" not in values


def test_policy_documents_authenticated_attempt_bound_route() -> None:
    text = POLICY.read_text(encoding="utf-8")
    for marker in (
        "`enablePullRequestAutoMerge`",
        "`/oteryn-mq-preflight <attempt_id> <owner/repo> <pr_number> <expected_head_sha>`",
        "`Oteryn/Oteryn#189`",
        "currently has `write`, `maintain` or `admin` permission",
        "GitHub-authored proof comment",
        "`issue_comment` workflow run on META `main` completed successfully",
        "fresh connector live-head read",
        "strictly after the connector mutation returns",
        "Historical `added_to_merge_queue` timeline events alone are not terminal admission proof",
        "No bypass or direct merge substitutes for an unavailable enqueue tool",
    ):
        assert marker in text, marker


def main() -> int:
    failures = []
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for name, fn in tests:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            failures.append((name, exc))
    if failures:
        for name, exc in failures:
            print(f"FAIL {name}: {exc}")
        return 1
    print(f"PASS {len(tests)} Merge Queue submission routing regressions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
