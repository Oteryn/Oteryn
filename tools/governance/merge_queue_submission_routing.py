#!/usr/bin/env python3
"""Fail-closed routing for GitHub-native Merge Queue submission capabilities."""

from __future__ import annotations

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
REF_RE = re.compile(r"^[A-Za-z0-9._/-]+$")
ATTEMPT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{15,127}$")
OBSERVATION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{15,127}$")
MAX_PREMUTATION_RULE_AGE_SECONDS = 30
MAX_POSTMUTATION_EVIDENCE_AGE_SECONDS = 60
SUPPORTED_BRANCH_RULE_SOURCES = frozenset({"branch_rules", "graphql_queue_config"})


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
    repository: str
    base_ref: str
    merge_queue_required: bool
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


def _valid_attempt(attempt: SubmissionAttempt) -> bool:
    return (
        isinstance(attempt, SubmissionAttempt)
        and _fullmatch(ATTEMPT_RE, attempt.attempt_id)
        and _fullmatch(REPOSITORY_RE, attempt.repository)
        and _positive_int(attempt.pr_number)
        and _fullmatch(REF_RE, attempt.base_ref)
        and ".." not in attempt.base_ref.split("/")
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


def _branch_observation_matches(
    attempt: SubmissionAttempt,
    observation: BranchQueueObservation,
    *,
    now_epoch_seconds: int,
) -> bool:
    return (
        isinstance(observation, BranchQueueObservation)
        and observation.attempt_id == attempt.attempt_id
        and _fullmatch(OBSERVATION_RE, observation.observation_id)
        and observation.source in SUPPORTED_BRANCH_RULE_SOURCES
        and observation.repository == attempt.repository
        and observation.base_ref == attempt.base_ref
        and isinstance(observation.merge_queue_required, bool)
        and _fresh(
            observation.observed_at_epoch_seconds,
            now_epoch_seconds,
            MAX_PREMUTATION_RULE_AGE_SECONDS,
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
    freeze: CandidateFreeze,
    capabilities: SubmissionCapabilities,
    *,
    now_epoch_seconds: int,
) -> str:
    """Choose a protected submission route from fresh, same-attempt GitHub state."""
    if not _valid_attempt(attempt):
        return BLOCKED_STALE_STATE
    if not isinstance(capabilities, SubmissionCapabilities) or not _boolean_fields(
        capabilities,
        (
            "explicit_enqueue_available",
            "auto_merge_available",
            "integration_authorized",
            "pr_eligible",
        ),
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
        and observed_at_epoch_seconds >= submission_completed_at_epoch_seconds
        and _fresh(
            observed_at_epoch_seconds,
            now_epoch_seconds,
            MAX_POSTMUTATION_EVIDENCE_AGE_SECONDS,
        )
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
        if not _fullmatch(REPOSITORY_RE, member.repository) or not _positive_int(member.pr_number):
            return False
        if not _fullmatch(SHA_RE, member.pr_head_sha):
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
    """Accept only fresh current queue state or same-observation merge-group membership."""
    if route not in {EXPLICIT_ENQUEUE, AUTO_MERGE_MQ_SUBMISSION}:
        return BLOCKED_QUEUE_ADMISSION_UNPROVEN
    if not _valid_attempt(attempt):
        return BLOCKED_QUEUE_ADMISSION_UNPROVEN
    if not isinstance(evidence, Iterable):
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
