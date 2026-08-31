"""Explicit trusted fixtures for bounded-execution unit tests.

Production callers must supply a real classifier/evidence authority and a
durable checkpoint outbox.  Tests use this module to provide a narrowly scoped
authority that accepts only the canonical records installed for that individual
test invocation.
"""

from __future__ import annotations

import copy
import tempfile
from pathlib import Path
from typing import Any

from bounded_execution_guard import (
    ExecutionContext,
    _checkpoint_digest,
    decide as guard_decide,
    make_material_fact_envelope,
    make_review_binding,
)
from durable_checkpoint_outbox import SqliteCheckpointOutbox


class TestEvidenceAuthority:
    __test__ = False

    def __init__(self, review_binding_ids: set[str], envelope_ids: set[str]):
        self.review_binding_ids = review_binding_ids
        self.envelope_ids = envelope_ids

    def verify_review_binding(self, binding: dict[str, Any]) -> bool:
        return binding.get("binding_id") in self.review_binding_ids

    def verify_material_fact_envelope(self, envelope: dict[str, Any]) -> bool:
        return envelope.get("envelope_id") in self.envelope_ids

    def verify_completion(self, candidate: dict[str, Any]) -> bool:
        return candidate.get("completion_verified") is True


def _prepared(snapshot: dict[str, Any] | None, policy: dict[str, Any]) -> dict[str, Any] | None:
    if snapshot is None:
        return None
    prepared = copy.deepcopy(snapshot)
    if prepared.get("review_binding") is None:
        prepared["review_binding"] = make_review_binding(
            policy,
            repository=prepared["repository"],
            task_id=prepared["task_id"],
            base_head_sha="b" * 40,
            head_sha=prepared["task_head_sha"],
            tier="R2",
            classifier_revision="bounded-execution-test-v1",
            risk_fingerprint=prepared.get("review_fingerprint") or "f" * 64,
        )
    if prepared.get("material_fact_envelope") is None and (
        prepared.get("material_change") or prepared.get("repair_generation_id")
    ):
        frozen_head = (
            prepared.get("material_fact_head")
            or prepared.get("repair_base_head")
            or prepared["task_head_sha"]
        )
        prepared["material_fact_envelope"] = make_material_fact_envelope(
            policy,
            repository=prepared["repository"],
            task_id=prepared["task_id"],
            frozen_head_sha=frozen_head,
            reason=prepared.get("material_change_reason") or "review_finding",
            source_evidence=prepared.get("material_change_evidence") or "test-control-plane-evidence",
        )
    if prepared.get("material_fact_envelope") is not None and prepared.get("repair_generation_id"):
        prepared["repair_generation_id"] = prepared["material_fact_envelope"]["envelope_id"]
    return prepared


def decide(previous: dict[str, Any] | None, current: dict[str, Any], action: str, policy: dict[str, Any]):
    """Evaluate with per-call explicit trusted test dependencies."""

    prepared_previous = _prepared(previous, policy)
    prepared_current = _prepared(current, policy)
    assert prepared_current is not None
    bindings = {
        snapshot["review_binding"]["binding_id"]
        for snapshot in (prepared_previous, prepared_current)
        if snapshot is not None and snapshot.get("review_binding") is not None
    }
    envelopes = {
        snapshot["material_fact_envelope"]["envelope_id"]
        for snapshot in (prepared_previous, prepared_current)
        if snapshot is not None and snapshot.get("material_fact_envelope") is not None
    }
    with tempfile.TemporaryDirectory() as directory:
        outbox = SqliteCheckpointOutbox(Path(directory) / "checkpoint.db")
        if prepared_previous is not None:
            outbox.seed_checkpoint(
                prepared_previous["repository"],
                prepared_previous["task_id"],
                _checkpoint_digest(prepared_previous),
                snapshot=prepared_previous,
            )
        return guard_decide(
            prepared_previous,
            prepared_current,
            action,
            policy,
            context=ExecutionContext(TestEvidenceAuthority(bindings, envelopes), outbox),
        )


def decide_with_acknowledged_audit(previous: dict[str, Any], current: dict[str, Any], policy: dict[str, Any]):
    """Record an audit only after its exact durable dispatch has been claimed and ACKed."""

    prepared_previous = _prepared(previous, policy)
    prepared_current = _prepared(current, policy)
    assert prepared_previous is not None and prepared_current is not None
    binding = prepared_current["review_binding"]
    scope = tuple(binding[key] for key in (
        "repository", "task_id", "tier", "policy_id", "policy_digest",
        "classifier_revision", "risk_fingerprint",
    )) + (
        f"task_head_sha:{prepared_current['task_head_sha']}",
        "loop_breaker_audit_generation:"
        f"{prepared_current['late_material_findings']}:"
        f"{prepared_current['post_freeze_material_head_changes']}",
    )
    with tempfile.TemporaryDirectory() as directory:
        outbox = SqliteCheckpointOutbox(Path(directory) / "checkpoint.db")
        checkpoint = _checkpoint_digest(prepared_previous)
        outbox.seed_checkpoint(prepared_previous["repository"], prepared_previous["task_id"], checkpoint, snapshot=prepared_previous)
        reservation = outbox.reserve(
            repository=prepared_previous["repository"], task_id=prepared_previous["task_id"],
            expected_checkpoint=checkpoint, next_checkpoint=checkpoint,
            next_snapshot=prepared_previous, action="run_loop_breaker_audit", scope=scope,
        )
        assert reservation.committed
        assert outbox.claim_dispatch(reservation.reservation_key)
        assert outbox.begin_dispatch(reservation.reservation_key, 1)
        assert outbox.acknowledge_dispatch(reservation.reservation_key)
        authority = TestEvidenceAuthority({binding["binding_id"]}, set())
        return guard_decide(prepared_previous, prepared_current, "record_loop_breaker_audit", policy, context=ExecutionContext(authority, outbox))
