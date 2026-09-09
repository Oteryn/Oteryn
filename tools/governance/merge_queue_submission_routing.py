#!/usr/bin/env python3
"""Current-contract guard for exact-target GitHub Merge Queue submission.

Oteryn requires one mutation to atomically fence both the qualified PR head and
the intended base/queue. The currently documented GitHub queue primitives can
fence the head but do not expose an expected base/queue precondition, so this
module deliberately has no positive autonomous submission route. A future
primitive must be added here by reviewed code change; callers cannot enable one
by asserting capability booleans.
"""

from __future__ import annotations

import re
from typing import NamedTuple

BLOCKED_NOT_AUTHORIZED = "BLOCKED_NOT_AUTHORIZED"
BLOCKED_NOT_ELIGIBLE = "BLOCKED_NOT_ELIGIBLE"
BLOCKED_STALE_STATE = "BLOCKED_STALE_STATE"
BLOCKED_FROZEN_HEAD_MISMATCH = "BLOCKED_FROZEN_HEAD_MISMATCH"
BLOCKED_CAPABILITY_UNAVAILABLE = "BLOCKED_CAPABILITY_UNAVAILABLE"

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
ATTEMPT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{15,127}$")
AUTHORIZATION_SOURCE = "live_authenticated_target_authorization"
MAX_AUTHORIZATION_AGE_SECONDS = 10
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
    """Semantic guarantees documented for a GitHub queue mutation.

    These values are repository-owned policy evidence, not caller-provided
    capability switches. Changing them is a material governance code change.
    """

    operation: str
    queue_specific: bool
    expected_head_fence: bool
    expected_base_queue_fence: bool


# Current GitHub documentation exposes an exact-head fence on both native queue
# paths, but no expected base/queue coordinate on the same mutation. Keep these
# facts explicit so deterministic tests fail if someone tries to treat either
# current primitive as an atomic exact-target route.
DOCUMENTED_QUEUE_PRIMITIVES = (
    DocumentedQueuePrimitive(
        operation="merge-async",
        queue_specific=True,
        expected_head_fence=True,
        expected_base_queue_fence=False,
    ),
    DocumentedQueuePrimitive(
        operation="enqueuePullRequest",
        queue_specific=True,
        expected_head_fence=True,
        expected_base_queue_fence=False,
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


def primitive_has_atomic_exact_target_fence(primitive: object) -> bool:
    """Return true only for a repository-declared atomic exact-target primitive."""

    return (
        isinstance(primitive, DocumentedQueuePrimitive)
        and primitive.queue_specific is True
        and primitive.expected_head_fence is True
        and primitive.expected_base_queue_fence is True
    )


def current_documented_atomic_routes() -> tuple[str, ...]:
    """Current reviewed GitHub primitives satisfying Oteryn's complete fence."""

    return tuple(
        primitive.operation
        for primitive in DOCUMENTED_QUEUE_PRIMITIVES
        if primitive_has_atomic_exact_target_fence(primitive)
    )


def choose_submission_route(
    attempt: SubmissionAttempt,
    freeze: CandidateFreeze,
    authorization: SubmissionAuthorization,
    *,
    now_epoch_seconds: int,
) -> str:
    """Fail closed until reviewed source declares a real atomic queue primitive.

    Caller-provided capability claims are intentionally absent. If GitHub adds a
    mutation-time expected-base/queue fence, update DOCUMENTED_QUEUE_PRIMITIVES
    and the invocation adapter in a separately reviewed material change.
    """

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

    # No current documented primitive satisfies both atomic coordinates. Do not
    # accept a synthetic/hypothetical capability from the caller as authority.
    if not current_documented_atomic_routes():
        return BLOCKED_CAPABILITY_UNAVAILABLE

    # A future source change must add a concrete invocation adapter and return
    # type together with the primitive update. This guard intentionally refuses
    # to infer execution authority from documentation facts alone.
    return BLOCKED_CAPABILITY_UNAVAILABLE
