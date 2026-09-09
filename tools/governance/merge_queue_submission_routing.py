#!/usr/bin/env python3
"""Fail-closed routing for exact-target GitHub Merge Queue submission.

A governed autonomous submission must bind both the qualified PR head and the
intended base/queue at the mutation boundary. Post-mutation readback cannot make
an already-applied wrong-base enqueue safe under concurrency. Generic auto-merge
and direct merge are intentionally not representable.
"""

from __future__ import annotations

import re
from typing import NamedTuple

ASYNC_MERGE_QUEUE = "ASYNC_MERGE_QUEUE"
EXPLICIT_ENQUEUE = "EXPLICIT_ENQUEUE"
PROTECTED_EXECUTOR_ENQUEUE = "PROTECTED_EXECUTOR_ENQUEUE"
BLOCKED_NOT_AUTHORIZED = "BLOCKED_NOT_AUTHORIZED"
BLOCKED_NOT_ELIGIBLE = "BLOCKED_NOT_ELIGIBLE"
BLOCKED_STALE_STATE = "BLOCKED_STALE_STATE"
BLOCKED_FROZEN_HEAD_MISMATCH = "BLOCKED_FROZEN_HEAD_MISMATCH"
BLOCKED_CAPABILITY_UNAVAILABLE = "BLOCKED_CAPABILITY_UNAVAILABLE"
SUBMISSION_ACCEPTED = "SUBMISSION_ACCEPTED"
ENQUEUED = "ENQUEUED"
BLOCKED_QUEUE_ADMISSION_UNPROVEN = "BLOCKED_QUEUE_ADMISSION_UNPROVEN"

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
ATTEMPT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{15,127}$")
QUEUE_ENTRY_RE = re.compile(r"^MQE_[A-Za-z0-9_-]+$")
UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
AUTHORIZATION_SOURCE = "live_authenticated_target_authorization"
MAX_AUTHORIZATION_AGE_SECONDS = 10
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


class SubmissionAuthorization(NamedTuple):
    """Fresh authenticated authorization/eligibility for one exact target candidate."""

    source: str
    repository: str
    pr_number: int
    base_ref: str
    pr_head_sha: str
    integration_authorized: bool
    pr_eligible: bool
    observed_at_epoch_seconds: int


class SubmissionCapabilities(NamedTuple):
    """Authenticated mutation guarantees exposed by the caller.

    The expected-base fields mean a server-side/atomic precondition on the same
    mutation that adds the PR to a queue. A preceding base read or a later queue
    readback does not satisfy these fields.
    """

    async_merge_available: bool
    async_merge_expected_head_fence: bool
    async_merge_expected_base_fence: bool
    async_merge_merge_queue_action: bool
    explicit_enqueue_available: bool
    explicit_enqueue_expected_head_fence: bool
    explicit_enqueue_expected_base_fence: bool
    protected_executor_available: bool
    protected_executor_expected_head_fence: bool
    protected_executor_expected_base_fence: bool
    protected_executor_trusted_default_branch: bool


class AsyncMergeReceipt(NamedTuple):
    route: str
    attempt_id: str
    repository: str
    pr_number: int
    base_ref: str
    expected_head_sha: str
    merge_action: str
    request_uuid: str
    http_status: int
    observed_at_epoch_seconds: int


class EnqueueReceipt(NamedTuple):
    route: str
    attempt_id: str
    repository: str
    pr_number: int
    base_ref: str
    expected_head_sha: str
    merge_queue_entry_id: str
    merge_queue_id: str
    merge_queue_resource_path: str
    merge_queue_url: str
    observed_at_epoch_seconds: int


def _fullmatch(pattern: re.Pattern[str], value: object) -> bool:
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def _valid_branch_name(value: object) -> bool:
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
    return isinstance(capabilities, SubmissionCapabilities) and all(
        isinstance(value, bool) for value in capabilities
    )


def _authorization_matches(
    attempt: SubmissionAttempt,
    authorization: object,
    *,
    now_epoch_seconds: object,
) -> bool:
    return (
        isinstance(authorization, SubmissionAuthorization)
        and authorization.source == AUTHORIZATION_SOURCE
        and authorization.repository == attempt.repository
        and authorization.pr_number == attempt.pr_number
        and authorization.base_ref == attempt.base_ref
        and authorization.pr_head_sha == attempt.live_pr_head_sha
        and _fullmatch(SHA_RE, authorization.pr_head_sha)
        and isinstance(authorization.integration_authorized, bool)
        and isinstance(authorization.pr_eligible, bool)
        and isinstance(authorization.observed_at_epoch_seconds, int)
        and not isinstance(authorization.observed_at_epoch_seconds, bool)
        and isinstance(now_epoch_seconds, int)
        and not isinstance(now_epoch_seconds, bool)
        and 0 <= authorization.observed_at_epoch_seconds <= now_epoch_seconds
        and now_epoch_seconds - authorization.observed_at_epoch_seconds
        <= MAX_AUTHORIZATION_AGE_SECONDS
    )


def _valid_time_window(
    observed_at_epoch_seconds: object,
    *,
    submission_started_at_epoch_seconds: object,
    now_epoch_seconds: object,
) -> bool:
    return (
        isinstance(submission_started_at_epoch_seconds, int)
        and not isinstance(submission_started_at_epoch_seconds, bool)
        and isinstance(now_epoch_seconds, int)
        and not isinstance(now_epoch_seconds, bool)
        and isinstance(observed_at_epoch_seconds, int)
        and not isinstance(observed_at_epoch_seconds, bool)
        and submission_started_at_epoch_seconds >= 0
        and now_epoch_seconds >= submission_started_at_epoch_seconds
        and submission_started_at_epoch_seconds
        <= observed_at_epoch_seconds
        <= now_epoch_seconds
        and now_epoch_seconds - observed_at_epoch_seconds <= MAX_RECEIPT_AGE_SECONDS
    )


def choose_submission_route(
    attempt: SubmissionAttempt,
    freeze: CandidateFreeze,
    authorization: SubmissionAuthorization,
    capabilities: SubmissionCapabilities,
    *,
    now_epoch_seconds: int,
) -> str:
    """Choose only a queue route that atomically fences exact head and base."""
    if not _valid_attempt(attempt) or not _valid_capabilities(capabilities):
        return BLOCKED_STALE_STATE
    if not _authorization_matches(
        attempt,
        authorization,
        now_epoch_seconds=now_epoch_seconds,
    ):
        return BLOCKED_STALE_STATE
    if not authorization.integration_authorized:
        return BLOCKED_NOT_AUTHORIZED
    if not authorization.pr_eligible:
        return BLOCKED_NOT_ELIGIBLE
    if not _freeze_matches(attempt, freeze):
        return BLOCKED_FROZEN_HEAD_MISMATCH

    if (
        capabilities.async_merge_available
        and capabilities.async_merge_expected_head_fence
        and capabilities.async_merge_expected_base_fence
        and capabilities.async_merge_merge_queue_action
    ):
        return ASYNC_MERGE_QUEUE

    if (
        capabilities.explicit_enqueue_available
        and capabilities.explicit_enqueue_expected_head_fence
        and capabilities.explicit_enqueue_expected_base_fence
    ):
        return EXPLICIT_ENQUEUE

    if (
        capabilities.protected_executor_available
        and capabilities.protected_executor_expected_head_fence
        and capabilities.protected_executor_expected_base_fence
        and capabilities.protected_executor_trusted_default_branch
    ):
        return PROTECTED_EXECUTOR_ENQUEUE

    return BLOCKED_CAPABILITY_UNAVAILABLE


def verify_async_merge_receipt(
    attempt: SubmissionAttempt,
    receipt: AsyncMergeReceipt,
    *,
    submission_started_at_epoch_seconds: int,
    now_epoch_seconds: int,
) -> str:
    """Validate the immediate receipt only after a base-fenced route was selected."""
    if not _valid_attempt(attempt) or not isinstance(receipt, AsyncMergeReceipt):
        return BLOCKED_QUEUE_ADMISSION_UNPROVEN
    if not _valid_time_window(
        receipt.observed_at_epoch_seconds,
        submission_started_at_epoch_seconds=submission_started_at_epoch_seconds,
        now_epoch_seconds=now_epoch_seconds,
    ):
        return BLOCKED_QUEUE_ADMISSION_UNPROVEN
    if (
        receipt.route != ASYNC_MERGE_QUEUE
        or receipt.attempt_id != attempt.attempt_id
        or receipt.repository != attempt.repository
        or receipt.pr_number != attempt.pr_number
        or receipt.base_ref != attempt.base_ref
        or receipt.expected_head_sha != attempt.live_pr_head_sha
        or not _fullmatch(SHA_RE, receipt.expected_head_sha)
        or receipt.merge_action != "merge_queue"
        or receipt.http_status != 202
        or not _fullmatch(UUID_RE, receipt.request_uuid)
    ):
        return BLOCKED_QUEUE_ADMISSION_UNPROVEN
    return SUBMISSION_ACCEPTED


def verify_enqueue_receipt(
    route: str,
    attempt: SubmissionAttempt,
    receipt: EnqueueReceipt,
    *,
    submission_started_at_epoch_seconds: int,
    now_epoch_seconds: int,
) -> str:
    """Accept only an exact-target, exact-main-queue receipt after a safe route."""
    if not isinstance(route, str) or route not in {
        EXPLICIT_ENQUEUE,
        PROTECTED_EXECUTOR_ENQUEUE,
    }:
        return BLOCKED_QUEUE_ADMISSION_UNPROVEN
    if not _valid_attempt(attempt) or not isinstance(receipt, EnqueueReceipt):
        return BLOCKED_QUEUE_ADMISSION_UNPROVEN
    if not _valid_time_window(
        receipt.observed_at_epoch_seconds,
        submission_started_at_epoch_seconds=submission_started_at_epoch_seconds,
        now_epoch_seconds=now_epoch_seconds,
    ):
        return BLOCKED_QUEUE_ADMISSION_UNPROVEN

    expected_resource_path = f"/{attempt.repository}/queue/{attempt.base_ref}"
    expected_url = f"https://github.com/{attempt.repository}/queue/{attempt.base_ref}"
    if (
        receipt.route != route
        or receipt.attempt_id != attempt.attempt_id
        or receipt.repository != attempt.repository
        or receipt.pr_number != attempt.pr_number
        or receipt.base_ref != attempt.base_ref
        or receipt.expected_head_sha != attempt.live_pr_head_sha
        or not _fullmatch(SHA_RE, receipt.expected_head_sha)
        or not _fullmatch(QUEUE_ENTRY_RE, receipt.merge_queue_entry_id)
        or not isinstance(receipt.merge_queue_id, str)
        or not receipt.merge_queue_id
        or receipt.merge_queue_resource_path != expected_resource_path
        or receipt.merge_queue_url != expected_url
    ):
        return BLOCKED_QUEUE_ADMISSION_UNPROVEN
    return ENQUEUED
