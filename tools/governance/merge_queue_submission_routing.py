#!/usr/bin/env python3
"""Governed native exact-head GitHub Merge Queue submission contract.

Oteryn accepts REST ``merge-async`` with the qualified PR head in ``sha`` and
explicit ``merge_action=merge_queue`` as the native autonomous queue route.
GitHub does not expose an expected-base precondition on that mutation, so the
contract requires fresh exact-target preflight plus immediate post-submission
live readback. That readback detects a retarget race; it does not pretend to
make the mutation atomically base-fenced.
"""

from __future__ import annotations

import re
from typing import NamedTuple

ASYNC_MERGE_QUEUE = "ASYNC_MERGE_QUEUE"
SUBMISSION_ACCEPTED = "SUBMISSION_ACCEPTED"
POST_SUBMISSION_TARGET_CONFIRMED = "POST_SUBMISSION_TARGET_CONFIRMED"
RECONCILE_REQUIRED = "RECONCILE_REQUIRED"

BLOCKED_NOT_AUTHORIZED = "BLOCKED_NOT_AUTHORIZED"
BLOCKED_NOT_ELIGIBLE = "BLOCKED_NOT_ELIGIBLE"
BLOCKED_STALE_STATE = "BLOCKED_STALE_STATE"
BLOCKED_FROZEN_HEAD_MISMATCH = "BLOCKED_FROZEN_HEAD_MISMATCH"
BLOCKED_CAPABILITY_UNAVAILABLE = "BLOCKED_CAPABILITY_UNAVAILABLE"
BLOCKED_RECEIPT_INVALID = "BLOCKED_RECEIPT_INVALID"
BLOCKED_POST_SUBMISSION_TARGET_MISMATCH = "BLOCKED_POST_SUBMISSION_TARGET_MISMATCH"

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
ATTEMPT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{15,127}$")
AUTHORIZATION_SOURCE = "live_authenticated_target_authorization"
POST_SUBMISSION_SOURCE = "live_post_submission_target_readback"
MAX_AUTHORIZATION_AGE_SECONDS = 10
MAX_POST_SUBMISSION_AGE_SECONDS = 10
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
    """Fresh authenticated authorization/eligibility for one exact candidate."""

    source: str
    repository: str
    pr_number: int
    base_ref: str
    pr_head_sha: str
    integration_authorized: bool
    pr_eligible: bool
    observed_at_epoch_seconds: int


class DocumentedQueuePrimitive(NamedTuple):
    """Repository-owned facts for one documented GitHub queue mutation."""

    operation: str
    queue_specific: bool
    expected_head_fence: bool
    expected_base_queue_fence: bool
    operationally_approved: bool


class MergeAsyncRequest(NamedTuple):
    """Exact request contract for GitHub REST merge-async."""

    method: str
    endpoint: str
    repository: str
    pr_number: int
    sha: str
    merge_action: str


class AsyncMergeReceipt(NamedTuple):
    """Observed acceptance/reconciliation evidence for one merge-async request."""

    attempt_id: str
    repository: str
    pr_number: int
    base_ref: str
    expected_head_sha: str
    merge_action: str
    http_status: int
    request_uuid: str
    observed_at_epoch_seconds: int


class PostSubmissionTargetObservation(NamedTuple):
    """Immediate live PR readback after an accepted queue request."""

    source: str
    repository: str
    pr_number: int
    base_ref: str
    pr_head_sha: str
    observed_at_epoch_seconds: int


# ``merge-async`` is the selected Oteryn native route. Its exact-head fence and
# explicit queue action are strong enough for the accepted operational standard;
# the missing expected-base coordinate is mitigated by mandatory live pre/post
# target validation. GraphQL enqueuePullRequest is documented but is not selected
# by this policy revision.
DOCUMENTED_QUEUE_PRIMITIVES = (
    DocumentedQueuePrimitive(
        operation="merge-async",
        queue_specific=True,
        expected_head_fence=True,
        expected_base_queue_fence=False,
        operationally_approved=True,
    ),
    DocumentedQueuePrimitive(
        operation="enqueuePullRequest",
        queue_specific=True,
        expected_head_fence=True,
        expected_base_queue_fence=False,
        operationally_approved=False,
    ),
)


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


def primitive_is_operational_exact_head_route(primitive: object) -> bool:
    """Return true only for a reviewed queue-specific exact-head route."""

    return (
        isinstance(primitive, DocumentedQueuePrimitive)
        and primitive.queue_specific is True
        and primitive.expected_head_fence is True
        and primitive.operationally_approved is True
    )


def current_documented_operational_routes() -> tuple[str, ...]:
    """Reviewed GitHub primitives approved by the current Oteryn policy."""

    return tuple(
        primitive.operation
        for primitive in DOCUMENTED_QUEUE_PRIMITIVES
        if primitive_is_operational_exact_head_route(primitive)
    )


def choose_submission_route(
    attempt: SubmissionAttempt,
    freeze: CandidateFreeze,
    authorization: SubmissionAuthorization,
    *,
    now_epoch_seconds: int,
) -> str:
    """Select native merge-async only after fresh exact-target preflight."""

    if not _valid_attempt(attempt):
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

    if current_documented_operational_routes() == ("merge-async",):
        return ASYNC_MERGE_QUEUE
    return BLOCKED_CAPABILITY_UNAVAILABLE


def build_merge_async_request(
    attempt: SubmissionAttempt,
    freeze: CandidateFreeze,
    authorization: SubmissionAuthorization,
    *,
    now_epoch_seconds: int,
) -> MergeAsyncRequest | None:
    """Build the only approved native request; never infer default/direct mode."""

    if (
        choose_submission_route(
            attempt,
            freeze,
            authorization,
            now_epoch_seconds=now_epoch_seconds,
        )
        != ASYNC_MERGE_QUEUE
    ):
        return None
    return MergeAsyncRequest(
        method="PUT",
        endpoint=f"/repos/{attempt.repository}/pulls/{attempt.pr_number}/merge-async",
        repository=attempt.repository,
        pr_number=attempt.pr_number,
        sha=attempt.live_pr_head_sha,
        merge_action="merge_queue",
    )


def verify_async_merge_receipt(
    attempt: SubmissionAttempt,
    receipt: object,
    *,
    now_epoch_seconds: int,
) -> str:
    """Verify request acceptance; 200/409 require reconciliation, not success."""

    if not _valid_attempt(attempt) or not isinstance(receipt, AsyncMergeReceipt):
        return BLOCKED_RECEIPT_INVALID
    if (
        receipt.attempt_id != attempt.attempt_id
        or receipt.repository != attempt.repository
        or receipt.pr_number != attempt.pr_number
        or receipt.base_ref != attempt.base_ref
        or receipt.expected_head_sha != attempt.live_pr_head_sha
        or receipt.merge_action != "merge_queue"
        or not _fullmatch(SHA_RE, receipt.expected_head_sha)
        or not isinstance(receipt.http_status, int)
        or isinstance(receipt.http_status, bool)
        or not isinstance(receipt.observed_at_epoch_seconds, int)
        or isinstance(receipt.observed_at_epoch_seconds, bool)
        or not isinstance(now_epoch_seconds, int)
        or isinstance(now_epoch_seconds, bool)
        or not 0 <= receipt.observed_at_epoch_seconds <= now_epoch_seconds
        or now_epoch_seconds - receipt.observed_at_epoch_seconds > MAX_RECEIPT_AGE_SECONDS
    ):
        return BLOCKED_RECEIPT_INVALID
    if receipt.http_status in (200, 409):
        return RECONCILE_REQUIRED
    if receipt.http_status != 202 or not _fullmatch(UUID_RE, receipt.request_uuid):
        return BLOCKED_RECEIPT_INVALID
    return SUBMISSION_ACCEPTED


def verify_post_submission_target(
    attempt: SubmissionAttempt,
    receipt: AsyncMergeReceipt,
    observation: object,
    *,
    now_epoch_seconds: int,
) -> str:
    """Require immediate live target readback after accepted submission."""

    if (
        verify_async_merge_receipt(
            attempt,
            receipt,
            now_epoch_seconds=now_epoch_seconds,
        )
        != SUBMISSION_ACCEPTED
    ):
        return BLOCKED_RECEIPT_INVALID
    if not isinstance(observation, PostSubmissionTargetObservation):
        return BLOCKED_POST_SUBMISSION_TARGET_MISMATCH
    if (
        observation.source != POST_SUBMISSION_SOURCE
        or observation.repository != attempt.repository
        or observation.pr_number != attempt.pr_number
        or observation.base_ref != attempt.base_ref
        or observation.pr_head_sha != attempt.live_pr_head_sha
        or not _fullmatch(SHA_RE, observation.pr_head_sha)
        or not isinstance(observation.observed_at_epoch_seconds, int)
        or isinstance(observation.observed_at_epoch_seconds, bool)
        or not isinstance(now_epoch_seconds, int)
        or isinstance(now_epoch_seconds, bool)
        or not 0 <= observation.observed_at_epoch_seconds <= now_epoch_seconds
        or now_epoch_seconds - observation.observed_at_epoch_seconds
        > MAX_POST_SUBMISSION_AGE_SECONDS
    ):
        return BLOCKED_POST_SUBMISSION_TARGET_MISMATCH
    return POST_SUBMISSION_TARGET_CONFIRMED
