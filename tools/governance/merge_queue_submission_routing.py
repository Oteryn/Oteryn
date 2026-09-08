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
BLOCKED_CAPABILITY_UNAVAILABLE = "BLOCKED_CAPABILITY_UNAVAILABLE"
ENQUEUED = "ENQUEUED"
BLOCKED_QUEUE_ADMISSION_UNPROVEN = "BLOCKED_QUEUE_ADMISSION_UNPROVEN"

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
QUEUE_ADMISSION_EVIDENCE = frozenset(
    {
        "added_to_merge_queue",
        "merge_queue_entry",
        "merge_group",
    }
)


class SubmissionCapabilities(NamedTuple):
    merge_queue_required: bool
    explicit_enqueue_available: bool
    auto_merge_available: bool
    integration_authorized: bool
    pr_eligible: bool
    candidate_frozen: bool


class QueueAdmissionEvidence(NamedTuple):
    kind: str
    repository: str
    pr_number: int
    pr_head_sha: str
    integration_head_sha: str | None = None


def choose_submission_route(capabilities: SubmissionCapabilities) -> str:
    """Choose the least-ambiguous protected submission route without bypassing MQ."""
    if not capabilities.integration_authorized:
        return BLOCKED_NOT_AUTHORIZED
    if not capabilities.pr_eligible or not capabilities.candidate_frozen:
        return BLOCKED_NOT_ELIGIBLE
    if not capabilities.merge_queue_required:
        return NOT_MQ_TARGET
    if capabilities.explicit_enqueue_available:
        return EXPLICIT_ENQUEUE
    if capabilities.auto_merge_available:
        return AUTO_MERGE_MQ_SUBMISSION
    return BLOCKED_CAPABILITY_UNAVAILABLE


def verify_queue_admission(
    route: str,
    evidence: Iterable[QueueAdmissionEvidence],
    *,
    expected_repository: str,
    expected_pr_number: int,
    expected_pr_head_sha: str,
) -> str:
    """Require same-PR, same-head GitHub evidence before calling a submission enqueued."""
    if route not in {EXPLICIT_ENQUEUE, AUTO_MERGE_MQ_SUBMISSION}:
        return BLOCKED_QUEUE_ADMISSION_UNPROVEN
    if not expected_repository or expected_pr_number < 1 or SHA_RE.fullmatch(expected_pr_head_sha) is None:
        return BLOCKED_QUEUE_ADMISSION_UNPROVEN

    for item in evidence:
        if not isinstance(item, QueueAdmissionEvidence):
            continue
        if item.kind not in QUEUE_ADMISSION_EVIDENCE:
            continue
        if (
            item.repository != expected_repository
            or item.pr_number != expected_pr_number
            or item.pr_head_sha != expected_pr_head_sha
        ):
            continue
        if SHA_RE.fullmatch(item.pr_head_sha) is None:
            continue
        if item.kind == "merge_group" and (
            item.integration_head_sha is None or SHA_RE.fullmatch(item.integration_head_sha) is None
        ):
            continue
        return ENQUEUED
    return BLOCKED_QUEUE_ADMISSION_UNPROVEN
