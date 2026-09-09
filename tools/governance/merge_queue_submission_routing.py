#!/usr/bin/env python3
"""Fail-closed routing for exact-head-fenced GitHub Merge Queue enqueue capabilities.

This module classifies already-authenticated capability facts. It never grants merge
or repository authority and it deliberately has no ordinary auto-merge route.
"""

from __future__ import annotations

import re
from typing import NamedTuple

EXPLICIT_ENQUEUE = "EXPLICIT_ENQUEUE"
PROTECTED_EXECUTOR_ENQUEUE = "PROTECTED_EXECUTOR_ENQUEUE"
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
QUEUE_ENTRY_RE = re.compile(r"^MQE_[A-Za-z0-9_-]+$")
MAX_RECEIPT_AGE_SECONDS = 60
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


class CandidateFreeze(NamedTuple):
    repository: str
    pr_number: int
    head_sha: str


class SubmissionCapabilities(NamedTuple):
    """Authenticated facts about exact-head-fenced enqueue operations available now."""

    explicit_enqueue_available: bool
    explicit_enqueue_expected_head_fence: bool
    protected_executor_available: bool
    protected_executor_expected_head_fence: bool
    protected_executor_trusted_default_branch: bool
    integration_authorized: bool
    pr_eligible: bool


class EnqueueReceipt(NamedTuple):
    """Receipt returned by the exact enqueue operation, not a historical timeline event."""

    route: str
    attempt_id: str
    repository: str
    pr_number: int
    base_ref: str
    expected_head_sha: str
    merge_queue_entry_id: str
    observed_at_epoch_seconds: int


def _fullmatch(pattern: re.Pattern[str], value: object) -> bool:
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def _valid_branch_name(value: object) -> bool:
    """Apply the relevant `git check-ref-format --branch` constraints."""
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


def _valid_attempt(attempt: object) -> bool:
    return (
        isinstance(attempt, SubmissionAttempt)
        and _fullmatch(ATTEMPT_RE, attempt.attempt_id)
        and _allowed_repository(attempt.repository)
        and _positive_int(attempt.pr_number)
        and attempt.base_ref == "main"
        and _valid_branch_name(attempt.base_ref)
        and _fullmatch(SHA_RE, attempt.live_pr_head_sha)
    )


def _freeze_matches(attempt: SubmissionAttempt, freeze: object) -> bool:
    return (
        isinstance(freeze, CandidateFreeze)
        and freeze.repository == attempt.repository
        and freeze.pr_number == attempt.pr_number
        and freeze.head_sha == attempt.live_pr_head_sha
        and _fullmatch(SHA_RE, freeze.head_sha)
    )


def _valid_capabilities(capabilities: object) -> bool:
    if not isinstance(capabilities, SubmissionCapabilities):
        return False
    return all(isinstance(value, bool) for value in capabilities)


def choose_submission_route(
    attempt: SubmissionAttempt,
    freeze: CandidateFreeze,
    capabilities: SubmissionCapabilities,
) -> str:
    """Choose only a queue-specific operation with a server-side exact-head fence.

    `enablePullRequestAutoMerge` is intentionally not representable here. If an
    explicit enqueue operation is unavailable, the only accepted alternative is a
    protected-default-branch executor whose mutation is still GraphQL
    `enqueuePullRequest(expectedHeadOid=...)` for the frozen candidate.
    """
    if not _valid_attempt(attempt) or not _valid_capabilities(capabilities):
        return BLOCKED_STALE_STATE
    if not capabilities.integration_authorized:
        return BLOCKED_NOT_AUTHORIZED
    if not capabilities.pr_eligible:
        return BLOCKED_NOT_ELIGIBLE
    if not _freeze_matches(attempt, freeze):
        return BLOCKED_FROZEN_HEAD_MISMATCH

    if capabilities.explicit_enqueue_available:
        if capabilities.explicit_enqueue_expected_head_fence:
            return EXPLICIT_ENQUEUE
        return BLOCKED_CAPABILITY_UNAVAILABLE

    if capabilities.protected_executor_available:
        if (
            capabilities.protected_executor_expected_head_fence
            and capabilities.protected_executor_trusted_default_branch
        ):
            return PROTECTED_EXECUTOR_ENQUEUE
        return BLOCKED_CAPABILITY_UNAVAILABLE

    return BLOCKED_CAPABILITY_UNAVAILABLE


def verify_enqueue_receipt(
    route: str,
    attempt: SubmissionAttempt,
    receipt: EnqueueReceipt,
    *,
    submission_started_at_epoch_seconds: int,
    now_epoch_seconds: int,
) -> str:
    """Accept only the immediate exact-target receipt from the enqueue mutation."""
    if route not in {EXPLICIT_ENQUEUE, PROTECTED_EXECUTOR_ENQUEUE}:
        return BLOCKED_QUEUE_ADMISSION_UNPROVEN
    if not _valid_attempt(attempt) or not isinstance(receipt, EnqueueReceipt):
        return BLOCKED_QUEUE_ADMISSION_UNPROVEN
    if (
        not isinstance(submission_started_at_epoch_seconds, int)
        or isinstance(submission_started_at_epoch_seconds, bool)
        or not isinstance(now_epoch_seconds, int)
        or isinstance(now_epoch_seconds, bool)
        or submission_started_at_epoch_seconds < 0
        or now_epoch_seconds < submission_started_at_epoch_seconds
    ):
        return BLOCKED_QUEUE_ADMISSION_UNPROVEN
    if (
        not isinstance(receipt.observed_at_epoch_seconds, int)
        or isinstance(receipt.observed_at_epoch_seconds, bool)
        or receipt.observed_at_epoch_seconds < submission_started_at_epoch_seconds
        or receipt.observed_at_epoch_seconds > now_epoch_seconds
        or now_epoch_seconds - receipt.observed_at_epoch_seconds > MAX_RECEIPT_AGE_SECONDS
    ):
        return BLOCKED_QUEUE_ADMISSION_UNPROVEN
    if (
        receipt.route != route
        or receipt.attempt_id != attempt.attempt_id
        or receipt.repository != attempt.repository
        or receipt.pr_number != attempt.pr_number
        or receipt.base_ref != attempt.base_ref
        or receipt.expected_head_sha != attempt.live_pr_head_sha
        or not _fullmatch(SHA_RE, receipt.expected_head_sha)
        or not _fullmatch(QUEUE_ENTRY_RE, receipt.merge_queue_entry_id)
    ):
        return BLOCKED_QUEUE_ADMISSION_UNPROVEN
    return ENQUEUED
