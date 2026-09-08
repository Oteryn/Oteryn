#!/usr/bin/env python3
"""Fail-closed routing for GitHub-native Merge Queue submission capabilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

EXPLICIT_ENQUEUE = "EXPLICIT_ENQUEUE"
AUTO_MERGE_MQ_SUBMISSION = "AUTO_MERGE_MQ_SUBMISSION"
NOT_MQ_TARGET = "NOT_MQ_TARGET"
BLOCKED_NOT_AUTHORIZED = "BLOCKED_NOT_AUTHORIZED"
BLOCKED_NOT_ELIGIBLE = "BLOCKED_NOT_ELIGIBLE"
BLOCKED_CAPABILITY_UNAVAILABLE = "BLOCKED_CAPABILITY_UNAVAILABLE"
ENQUEUED = "ENQUEUED"
BLOCKED_QUEUE_ADMISSION_UNPROVEN = "BLOCKED_QUEUE_ADMISSION_UNPROVEN"

QUEUE_ADMISSION_EVIDENCE = frozenset(
    {
        "added_to_merge_queue",
        "merge_queue_entry",
        "merge_group",
    }
)


@dataclass(frozen=True)
class SubmissionCapabilities:
    merge_queue_required: bool
    explicit_enqueue_available: bool
    auto_merge_available: bool
    integration_authorized: bool
    pr_eligible: bool


def choose_submission_route(capabilities: SubmissionCapabilities) -> str:
    """Choose the least-ambiguous protected submission route without bypassing MQ."""
    if not capabilities.integration_authorized:
        return BLOCKED_NOT_AUTHORIZED
    if not capabilities.pr_eligible:
        return BLOCKED_NOT_ELIGIBLE
    if not capabilities.merge_queue_required:
        return NOT_MQ_TARGET
    if capabilities.explicit_enqueue_available:
        return EXPLICIT_ENQUEUE
    if capabilities.auto_merge_available:
        return AUTO_MERGE_MQ_SUBMISSION
    return BLOCKED_CAPABILITY_UNAVAILABLE


def verify_queue_admission(route: str, evidence: Iterable[str]) -> str:
    """Require direct GitHub evidence before calling either submission route enqueued."""
    if route not in {EXPLICIT_ENQUEUE, AUTO_MERGE_MQ_SUBMISSION}:
        return BLOCKED_QUEUE_ADMISSION_UNPROVEN
    observed = {item for item in evidence if isinstance(item, str)}
    if observed & QUEUE_ADMISSION_EVIDENCE:
        return ENQUEUED
    return BLOCKED_QUEUE_ADMISSION_UNPROVEN
