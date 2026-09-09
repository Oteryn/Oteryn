#!/usr/bin/env python3
"""Fail-closed routing for GitHub-native Merge Queue submission capabilities."""

from __future__ import annotations

import json
import re
from typing import Iterable, NamedTuple

EXPLICIT_ENQUEUE = "EXPLICIT_ENQUEUE"
AUTO_MERGE_MQ_SUBMISSION = "AUTO_MERGE_MQ_SUBMISSION"
NOT_MQ_TARGET = "NOT_MQ_TARGET"
BLOCKED_NOT_AUTHORIZED = "BLOCKED_NOT_AUTHORIZED"
BLOCKED_NOT_ELIGIBLE = "BLOCKED_NOT_ELIGIBLE"
BLOCKED_STALE_STATE = "BLOCKED_STALE_STATE"
BLOCKED_FROZEN_HEAD_MISMATCH = "BLOCKED_FROZEN_HEAD_MISMATCH"
BLOCKED_CAPABILITY_UNAVAILABLE = "BLOCKED_CAPABILITY_UNAVAILABLE"
ENQUEUED = "ENQUEUED"
BLOCKED_QUEUE_ADMISSION_UNPROVEN = "BLOCKED_QUEUE_ADMISSION_UNPROVEN"

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
ATTEMPT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{15,127}$")
OBSERVATION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{15,127}$")
QUEUE_ID_RE = re.compile(r"^MQ_[A-Za-z0-9_-]+$")
MAX_PREMUTATION_RULE_AGE_SECONDS = 30
MAX_LIVE_HEAD_AGE_SECONDS = 10
MAX_POSTMUTATION_EVIDENCE_AGE_SECONDS = 60
PREFLIGHT_SOURCE = "protected_meta_control_preflight"
LIVE_HEAD_SOURCE = "connector_live_pr_read"
CONTROL_REPOSITORY = "Oteryn/Oteryn"
CONTROL_ISSUE_NUMBER = 189
PREFLIGHT_WORKFLOW_PATH = ".github/workflows/merge-queue-preflight.yml"
PREFLIGHT_PROOF_AUTHOR = "github-actions[bot]"
ALLOWED_TARGET_REPOSITORIES = frozenset(
    {
        "Oteryn/Oteryn",
        "Oteryn/Oteryn-Game",
        "Oteryn/Oteryn-Platform",
        "Oteryn/Oteryn-Atlas",
    }
)


class SubmissionAttempt(NamedTuple):
    attempt_id: str
    repository: str
    pr_number: int
    base_ref: str
    live_pr_head_sha: str


class BranchQueueObservation(NamedTuple):
    attempt_id: str
    observation_id: str
    source: str
    control_repository: str
    control_issue_number: int
    repository: str
    pr_number: int
    base_ref: str
    pr_head_sha: str
    merge_queue_required: bool
    queue_id: str | None
    resource_path: str | None
    url: str | None
    trigger_comment_id: int
    proof_comment_id: int
    proof_comment_author_login: str
    workflow_run_id: int
    workflow_run_attempt: int
    workflow_sha: str
    observed_at_epoch_seconds: int
    expires_at_epoch_seconds: int


class ProofCommentObservation(NamedTuple):
    repository: str
    issue_number: int
    comment_id: int
    author_login: str
    body: str
    observed_at_epoch_seconds: int


class WorkflowRunObservation(NamedTuple):
    repository: str
    workflow_run_id: int
    workflow_run_attempt: int
    workflow_path: str
    event: str
    status: str
    conclusion: str
    head_branch: str
    head_sha: str
    observed_at_epoch_seconds: int


class LiveHeadObservation(NamedTuple):
    source: str
    repository: str
    pr_number: int
    base_ref: str
    pr_head_sha: str
    observed_at_epoch_seconds: int


class CandidateFreeze(NamedTuple):
    repository: str
    pr_number: int
    head_sha: str


class SubmissionCapabilities(NamedTuple):
    explicit_enqueue_available: bool
    auto_merge_available: bool
    integration_authorized: bool
    pr_eligible: bool


class QueueEntryObservation(NamedTuple):
    attempt_id: str
    observation_id: str
    repository: str
    pr_number: int
    pr_head_sha: str
    queue_entry_id: str
    active: bool
    observed_at_epoch_seconds: int


class MergeGroupMember(NamedTuple):
    repository: str
    pr_number: int
    pr_head_sha: str


class MergeGroupObservation(NamedTuple):
    attempt_id: str
    observation_id: str
    integration_head_sha: str
    members: tuple[MergeGroupMember, ...]
    observed_at_epoch_seconds: int


def _fullmatch(pattern: re.Pattern[str], value: object) -> bool:
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def _boolean_fields(value: object, names: tuple[str, ...]) -> bool:
    return all(isinstance(getattr(value, name, None), bool) for name in names)


def _valid_branch_name(value: object) -> bool:
    """Apply `git check-ref-format --branch` constraints to a branch shorthand."""
    if not isinstance(value, str) or not value or value == "@" or value.startswith("-"):
        return False
    identity = f"refs/heads/{value}"
    return (
        not identity.endswith(".")
        and not any(
            part == "" or part.startswith(".") or part.endswith(".lock")
            for part in identity.split("/")
        )
        and ".." not in identity
        and "@{" not in identity
        and not any(
            ord(char) <= 32 or ord(char) == 127 or char in "~^:?*[\\"
            for char in identity
        )
    )


def _allowed_repository(value: object) -> bool:
    return (
        isinstance(value, str)
        and value in ALLOWED_TARGET_REPOSITORIES
        and _fullmatch(REPOSITORY_RE, value)
    )


def _valid_attempt(attempt: SubmissionAttempt) -> bool:
    return (
        isinstance(attempt, SubmissionAttempt)
        and _fullmatch(ATTEMPT_RE, attempt.attempt_id)
        and _allowed_repository(attempt.repository)
        and _positive_int(attempt.pr_number)
        and _valid_branch_name(attempt.base_ref)
        and _fullmatch(SHA_RE, attempt.live_pr_head_sha)
    )


def _fresh(observed_at: object, now: object, max_age: int) -> bool:
    return (
        isinstance(observed_at, int)
        and not isinstance(observed_at, bool)
        and isinstance(now, int)
        and not isinstance(now, bool)
        and isinstance(max_age, int)
        and not isinstance(max_age, bool)
        and max_age >= 0
        and 0 <= observed_at <= now
        and now - observed_at <= max_age
    )


def _proof_payload(observation: BranchQueueObservation) -> dict[str, object]:
    return {
        "schema_version": 1,
        "attempt_id": observation.attempt_id,
        "observation_id": observation.observation_id,
        "source": observation.source,
        "control_repository": observation.control_repository,
        "control_issue_number": observation.control_issue_number,
        "repository": observation.repository,
        "pr_number": observation.pr_number,
        "base_ref": observation.base_ref,
        "pr_head_sha": observation.pr_head_sha,
        "merge_queue_required": observation.merge_queue_required,
        "queue_id": observation.queue_id,
        "resource_path": observation.resource_path,
        "url": observation.url,
        "trigger_comment_id": observation.trigger_comment_id,
        "proof_comment_id": observation.proof_comment_id,
        "proof_comment_author_login": observation.proof_comment_author_login,
        "workflow_run_id": observation.workflow_run_id,
        "workflow_run_attempt": observation.workflow_run_attempt,
        "workflow_sha": observation.workflow_sha,
        "observed_at_epoch_seconds": observation.observed_at_epoch_seconds,
        "expires_at_epoch_seconds": observation.expires_at_epoch_seconds,
    }


def _proof_comment_matches(
    observation: BranchQueueObservation,
    proof_comment: ProofCommentObservation,
    *,
    now_epoch_seconds: int,
) -> bool:
    if not isinstance(proof_comment, ProofCommentObservation):
        return False
    canonical = json.dumps(_proof_payload(observation), sort_keys=True, separators=(",", ":"))
    expected_body = "OTERYN_MQ_PREFLIGHT_V1\n```json\n" + canonical + "\n```"
    return (
        proof_comment.repository == CONTROL_REPOSITORY
        and proof_comment.issue_number == CONTROL_ISSUE_NUMBER
        and proof_comment.comment_id == observation.proof_comment_id
        and proof_comment.author_login == PREFLIGHT_PROOF_AUTHOR
        and proof_comment.author_login == observation.proof_comment_author_login
        and proof_comment.body == expected_body
        and _fresh(
            proof_comment.observed_at_epoch_seconds,
            now_epoch_seconds,
            MAX_PREMUTATION_RULE_AGE_SECONDS,
        )
        and proof_comment.observed_at_epoch_seconds >= observation.observed_at_epoch_seconds
    )


def _workflow_run_matches(
    observation: BranchQueueObservation,
    workflow: WorkflowRunObservation,
    *,
    now_epoch_seconds: int,
) -> bool:
    return (
        isinstance(workflow, WorkflowRunObservation)
        and workflow.repository == CONTROL_REPOSITORY
        and workflow.workflow_run_id == observation.workflow_run_id
        and workflow.workflow_run_attempt == observation.workflow_run_attempt
        and workflow.workflow_path == PREFLIGHT_WORKFLOW_PATH
        and workflow.event == "issue_comment"
        and workflow.status == "completed"
        and workflow.conclusion == "success"
        and workflow.head_branch == "main"
        and workflow.head_sha == observation.workflow_sha
        and _fullmatch(SHA_RE, workflow.head_sha)
        and _fresh(
            workflow.observed_at_epoch_seconds,
            now_epoch_seconds,
            MAX_PREMUTATION_RULE_AGE_SECONDS,
        )
    )


def _branch_observation_matches(
    attempt: SubmissionAttempt,
    observation: BranchQueueObservation,
    proof_comment: ProofCommentObservation,
    workflow: WorkflowRunObservation,
    *,
    now_epoch_seconds: int,
) -> bool:
    if not isinstance(observation, BranchQueueObservation):
        return False
    if observation.attempt_id != attempt.attempt_id or observation.source != PREFLIGHT_SOURCE:
        return False
    if (
        observation.control_repository != CONTROL_REPOSITORY
        or observation.control_issue_number != CONTROL_ISSUE_NUMBER
        or observation.repository != attempt.repository
        or observation.pr_number != attempt.pr_number
        or observation.base_ref != attempt.base_ref
        or observation.pr_head_sha != attempt.live_pr_head_sha
    ):
        return False
    if not _fullmatch(SHA_RE, observation.pr_head_sha) or not _fullmatch(SHA_RE, observation.workflow_sha):
        return False
    if not all(
        _positive_int(value)
        for value in (
            observation.trigger_comment_id,
            observation.proof_comment_id,
            observation.workflow_run_id,
            observation.workflow_run_attempt,
        )
    ):
        return False
    if observation.proof_comment_author_login != PREFLIGHT_PROOF_AUTHOR:
        return False
    expected_observation_id = (
        f"mq-preflight-{observation.workflow_run_id}-"
        f"{observation.workflow_run_attempt}-{observation.trigger_comment_id}"
    )
    if observation.observation_id != expected_observation_id:
        return False
    if not isinstance(observation.merge_queue_required, bool):
        return False
    if not _fresh(
        observation.observed_at_epoch_seconds,
        now_epoch_seconds,
        MAX_PREMUTATION_RULE_AGE_SECONDS,
    ):
        return False
    if (
        not isinstance(observation.expires_at_epoch_seconds, int)
        or isinstance(observation.expires_at_epoch_seconds, bool)
        or observation.expires_at_epoch_seconds
        != observation.observed_at_epoch_seconds + MAX_PREMUTATION_RULE_AGE_SECONDS
        or now_epoch_seconds > observation.expires_at_epoch_seconds
    ):
        return False
    if not _proof_comment_matches(observation, proof_comment, now_epoch_seconds=now_epoch_seconds):
        return False
    if not _workflow_run_matches(observation, workflow, now_epoch_seconds=now_epoch_seconds):
        return False

    if observation.merge_queue_required is False:
        return observation.queue_id is None and observation.resource_path is None and observation.url is None

    expected_resource_path = f"/{attempt.repository}/queue/{attempt.base_ref}"
    expected_url = f"https://github.com{expected_resource_path}"
    return (
        _fullmatch(QUEUE_ID_RE, observation.queue_id)
        and observation.resource_path == expected_resource_path
        and observation.url == expected_url
    )


def _live_head_matches(
    attempt: SubmissionAttempt,
    preflight: BranchQueueObservation,
    live_head: LiveHeadObservation,
    *,
    now_epoch_seconds: int,
) -> bool:
    return (
        isinstance(live_head, LiveHeadObservation)
        and live_head.source == LIVE_HEAD_SOURCE
        and live_head.repository == attempt.repository
        and live_head.pr_number == attempt.pr_number
        and live_head.base_ref == attempt.base_ref
        and live_head.pr_head_sha == attempt.live_pr_head_sha
        and _fullmatch(SHA_RE, live_head.pr_head_sha)
        and isinstance(live_head.observed_at_epoch_seconds, int)
        and not isinstance(live_head.observed_at_epoch_seconds, bool)
        and live_head.observed_at_epoch_seconds >= preflight.observed_at_epoch_seconds
        and _fresh(
            live_head.observed_at_epoch_seconds,
            now_epoch_seconds,
            MAX_LIVE_HEAD_AGE_SECONDS,
        )
    )


def _freeze_matches(attempt: SubmissionAttempt, freeze: CandidateFreeze) -> bool:
    return (
        isinstance(freeze, CandidateFreeze)
        and freeze.repository == attempt.repository
        and freeze.pr_number == attempt.pr_number
        and freeze.head_sha == attempt.live_pr_head_sha
        and _fullmatch(SHA_RE, freeze.head_sha)
    )


def choose_submission_route(
    attempt: SubmissionAttempt,
    branch_observation: BranchQueueObservation,
    proof_comment_observation: ProofCommentObservation,
    workflow_run_observation: WorkflowRunObservation,
    live_head_observation: LiveHeadObservation,
    freeze: CandidateFreeze,
    capabilities: SubmissionCapabilities,
    *,
    now_epoch_seconds: int,
) -> str:
    """Choose a protected submission route from authenticated fresh GitHub observations."""
    if not _valid_attempt(attempt):
        return BLOCKED_STALE_STATE
    if not isinstance(capabilities, SubmissionCapabilities) or not _boolean_fields(
        capabilities,
        ("explicit_enqueue_available", "auto_merge_available", "integration_authorized", "pr_eligible"),
    ):
        return BLOCKED_STALE_STATE
    if not capabilities.integration_authorized:
        return BLOCKED_NOT_AUTHORIZED
    if not capabilities.pr_eligible:
        return BLOCKED_NOT_ELIGIBLE
    if not _freeze_matches(attempt, freeze):
        return BLOCKED_FROZEN_HEAD_MISMATCH
    if not _branch_observation_matches(
        attempt,
        branch_observation,
        proof_comment_observation,
        workflow_run_observation,
        now_epoch_seconds=now_epoch_seconds,
    ):
        return BLOCKED_STALE_STATE
    if not _live_head_matches(
        attempt,
        branch_observation,
        live_head_observation,
        now_epoch_seconds=now_epoch_seconds,
    ):
        return BLOCKED_STALE_STATE
    if not branch_observation.merge_queue_required:
        return NOT_MQ_TARGET
    if capabilities.explicit_enqueue_available:
        return EXPLICIT_ENQUEUE
    if capabilities.auto_merge_available:
        return AUTO_MERGE_MQ_SUBMISSION
    return BLOCKED_CAPABILITY_UNAVAILABLE


def _observation_is_post_submission(
    *,
    attempt_id: object,
    observation_id: object,
    observed_at_epoch_seconds: object,
    submission_completed_at_epoch_seconds: object,
    now_epoch_seconds: object,
) -> bool:
    return (
        _fullmatch(ATTEMPT_RE, attempt_id)
        and _fullmatch(OBSERVATION_RE, observation_id)
        and isinstance(submission_completed_at_epoch_seconds, int)
        and not isinstance(submission_completed_at_epoch_seconds, bool)
        and isinstance(observed_at_epoch_seconds, int)
        and not isinstance(observed_at_epoch_seconds, bool)
        and observed_at_epoch_seconds > submission_completed_at_epoch_seconds
        and _fresh(observed_at_epoch_seconds, now_epoch_seconds, MAX_POSTMUTATION_EVIDENCE_AGE_SECONDS)
    )


def _queue_entry_matches(
    attempt: SubmissionAttempt,
    observation: QueueEntryObservation,
    *,
    submission_completed_at_epoch_seconds: int,
    now_epoch_seconds: int,
) -> bool:
    return (
        isinstance(observation, QueueEntryObservation)
        and observation.attempt_id == attempt.attempt_id
        and _observation_is_post_submission(
            attempt_id=observation.attempt_id,
            observation_id=observation.observation_id,
            observed_at_epoch_seconds=observation.observed_at_epoch_seconds,
            submission_completed_at_epoch_seconds=submission_completed_at_epoch_seconds,
            now_epoch_seconds=now_epoch_seconds,
        )
        and observation.repository == attempt.repository
        and observation.pr_number == attempt.pr_number
        and observation.pr_head_sha == attempt.live_pr_head_sha
        and _fullmatch(SHA_RE, observation.pr_head_sha)
        and _fullmatch(OBSERVATION_RE, observation.queue_entry_id)
        and observation.active is True
    )


def _merge_group_matches(
    attempt: SubmissionAttempt,
    observation: MergeGroupObservation,
    *,
    submission_completed_at_epoch_seconds: int,
    now_epoch_seconds: int,
) -> bool:
    if not isinstance(observation, MergeGroupObservation):
        return False
    if observation.attempt_id != attempt.attempt_id:
        return False
    if not _observation_is_post_submission(
        attempt_id=observation.attempt_id,
        observation_id=observation.observation_id,
        observed_at_epoch_seconds=observation.observed_at_epoch_seconds,
        submission_completed_at_epoch_seconds=submission_completed_at_epoch_seconds,
        now_epoch_seconds=now_epoch_seconds,
    ):
        return False
    if not _fullmatch(SHA_RE, observation.integration_head_sha):
        return False
    if not isinstance(observation.members, tuple) or not observation.members:
        return False
    for member in observation.members:
        if not isinstance(member, MergeGroupMember):
            return False
        if not _allowed_repository(member.repository):
            return False
        if not _positive_int(member.pr_number) or not _fullmatch(SHA_RE, member.pr_head_sha):
            return False
    expected = MergeGroupMember(
        repository=attempt.repository,
        pr_number=attempt.pr_number,
        pr_head_sha=attempt.live_pr_head_sha,
    )
    return expected in observation.members


def verify_queue_admission(
    route: str,
    attempt: SubmissionAttempt,
    evidence: Iterable[QueueEntryObservation | MergeGroupObservation],
    *,
    submission_completed_at_epoch_seconds: int,
    now_epoch_seconds: int,
) -> str:
    """Accept only a strictly post-mutation live queue read or merge-group membership."""
    if not isinstance(route, str) or route not in {EXPLICIT_ENQUEUE, AUTO_MERGE_MQ_SUBMISSION}:
        return BLOCKED_QUEUE_ADMISSION_UNPROVEN
    if not _valid_attempt(attempt) or not isinstance(evidence, Iterable):
        return BLOCKED_QUEUE_ADMISSION_UNPROVEN
    try:
        for item in evidence:
            if _queue_entry_matches(
                attempt,
                item,
                submission_completed_at_epoch_seconds=submission_completed_at_epoch_seconds,
                now_epoch_seconds=now_epoch_seconds,
            ):
                return ENQUEUED
            if _merge_group_matches(
                attempt,
                item,
                submission_completed_at_epoch_seconds=submission_completed_at_epoch_seconds,
                now_epoch_seconds=now_epoch_seconds,
            ):
                return ENQUEUED
    except (TypeError, ValueError):
        return BLOCKED_QUEUE_ADMISSION_UNPROVEN
    return BLOCKED_QUEUE_ADMISSION_UNPROVEN
