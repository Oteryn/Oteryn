#!/usr/bin/env python3
"""Deterministic bounded-autonomous-execution guard."""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Protocol

from durable_checkpoint_outbox import CheckpointOutboxAdapter, checkpoint_digest

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
FINGERPRINT_RE = re.compile(r"^[0-9a-f]{64}$")
CANONICAL_STATES = {"RUNNING", "WAITING_EXTERNAL", "BLOCKED", "STALLED", "READY", "DONE"}
CANONICAL_RELEASE_STATES = {"WAITING_EXTERNAL", "BLOCKED", "STALLED", "DONE"}
CANONICAL_RISK_CLASSES = (
    "identity_binding",
    "authority_relay",
    "epoch_deadline",
    "retry_budget",
    "concurrency_replay",
    "transaction_persistence",
    "negative_paths",
    "ci_governance",
)
CANONICAL_LEDGER_STATUSES = {"PENDING", "AUDITED_PASS", "NOT_APPLICABLE"}
CANONICAL_LEDGER_TERMINAL_STATUSES = {"AUDITED_PASS", "NOT_APPLICABLE"}
RETRY_COUNTER_FIELDS = (
    "identical_failure_cycles",
    "heavy_validation_runs",
    "external_review_invocations",
    "same_head_gate_rechecks",
)
ACTION_COUNTER_FIELDS = {
    "retry": "identical_failure_cycles",
    "request_external_review": "external_review_invocations",
    "run_heavy_validation": "heavy_validation_runs",
    "same_head_gate_recheck": "same_head_gate_rechecks",
}
ACTION_COUNTER_BUDGETS = {
    "retry": "identical_failure_cycles",
    "request_external_review": "external_review_invocations_per_fingerprint",
    "run_heavy_validation": "heavy_validation_attempts",
    "same_head_gate_recheck": "same_head_gate_rechecks_per_evidence_generation",
}
CANONICAL_MATERIAL_CHANGE_REASONS = {
    "review_finding",
    "failing_required_test",
    "semantic_reconciliation",
    "changed_governing_authority",
}
CANONICAL_FROZEN_FORBIDDEN_ACTIONS = {"mutate", "retrigger"}
LOOP_BREAKER_COUNTER_FIELDS = (
    "late_material_findings",
    "post_freeze_material_head_changes",
    "audited_late_material_findings",
    "audited_post_freeze_material_head_changes",
    "final_qualification_runs_since_audit",
)
LOOP_BREAKER_FINAL_ACTIONS = {
    "request_external_review",
    "run_heavy_validation",
    "same_head_gate_recheck",
    "enter_final_qualification",
    "complete",
}
LOOP_BREAKER_POST_ADMISSION_ACTIONS = {
    "request_external_review",
    "run_heavy_validation",
    "same_head_gate_recheck",
    "complete",
}
OBSERVATION_IMMUTABLE_FIELDS = (
    "state",
    "candidate_frozen",
    "material_change",
    "material_change_reason",
    "material_change_evidence",
    "material_fact_id",
    "material_fact_head",
    "material_fact_verified",
    "material_fact_envelope",
    "repair_generation_id",
    "repair_base_head",
    "review_binding",
    "completion_verified",
    "risk_ledger",
    *RETRY_COUNTER_FIELDS,
    *LOOP_BREAKER_COUNTER_FIELDS,
)
SUPPORTED_ACTIONS = {
    "observe",
    "retry",
    "mutate",
    "retrigger",
    "complete",
    "request_external_review",
    "run_heavy_validation",
    "same_head_gate_recheck",
    "run_loop_breaker_audit",
    "enter_final_qualification",
    "open_material_repair",
    "refreeze_candidate",
    "record_loop_breaker_audit",
}
MAX_ORGANIZATION_LOOP_BREAKER_THRESHOLD = 2
CANONICAL_SNAPSHOT_REQUIRED_FIELDS = frozenset({
    "repository", "task_id", "state", "phase", "task_head_sha",
    "candidate_frozen", "blocking_dependency", "dependency_kind", "gate_state",
    "review_generation", "review_fingerprint", "evidence_generation",
    "first_material_failure", "identical_failure_cycles", "heavy_validation_runs",
    "external_review_invocations", "same_head_gate_rechecks", "completion_verified",
    "material_change", "material_change_reason", "material_change_evidence",
    "material_fact_id", "material_fact_head", "material_fact_verified",
    "repair_generation_id", "repair_base_head", "late_material_findings",
    "post_freeze_material_head_changes", "audited_late_material_findings",
    "audited_post_freeze_material_head_changes", "final_qualification_runs_since_audit",
})
CANONICAL_SNAPSHOT_OPTIONAL_FIELDS = frozenset({
    "review_binding", "material_fact_envelope", "risk_ledger", "updated_at", "narration"
})


CANONICAL_PROGRESS_FINGERPRINT_FIELDS = (
    "repository",
    "task_id",
    "task_head_sha",
    "phase",
    "blocking_dependency",
    "dependency_kind",
    "gate_state",
    "review_binding_scope",
    "first_material_failure",
    "material_fact_envelope_id",
)
EXPECTED_COUNTER_SCOPES = {
    "identical_failure_cycles": ["task_head_sha", "failure_fingerprint"],
    "heavy_validation_runs": ["task_head_sha"],
    "external_review_invocations": ["review_binding_scope"],
    "same_head_gate_rechecks": ["task_head_sha", "review_binding_scope"],
}


class GuardError(ValueError):
    """Raised when policy or snapshot input is malformed."""


class TrustedEvidenceAuthority(Protocol):
    """Control-plane verifier for evidence not asserted by a work snapshot."""

    def verify_review_binding(self, binding: dict[str, Any]) -> bool: ...

    def verify_material_fact_envelope(self, envelope: dict[str, Any]) -> bool: ...

    def verify_completion(self, candidate: dict[str, Any]) -> bool: ...


@dataclasses.dataclass(frozen=True)
class ExecutionContext:
    """Trusted dependencies required before a guard result may be executed."""

    evidence_authority: TrustedEvidenceAuthority
    checkpoint_outbox: CheckpointOutboxAdapter


@dataclasses.dataclass(frozen=True)
class Decision:
    allowed: bool
    state: str
    reason: str
    release_session: bool
    progress_fingerprint: str
    failure_fingerprint: str
    reservation_key: str = ""

    def as_dict(self) -> dict[str, object]:
        return dataclasses.asdict(self)


def _digest(value: dict[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def policy_digest(policy: dict[str, Any]) -> str:
    """Return the immutable identity of the validated policy document."""

    return _digest(policy)


def _review_binding_payload(binding: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in binding.items() if key != "binding_id"}


def _material_envelope_payload(envelope: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in envelope.items() if key != "envelope_id"}


def make_review_binding(
    policy: dict[str, Any],
    *,
    repository: str,
    task_id: str,
    base_head_sha: str,
    head_sha: str,
    tier: str,
    classifier_revision: str,
    risk_fingerprint: str,
) -> dict[str, Any]:
    """Build a canonical binding for a classifier/attestation authority to sign."""

    binding = {
        "repository": repository,
        "task_id": task_id,
        "base_head_sha": base_head_sha,
        "head_sha": head_sha,
        "tier": tier,
        "policy_id": policy.get("policy_id"),
        "policy_digest": policy_digest(policy),
        "classifier_revision": classifier_revision,
        "risk_fingerprint": risk_fingerprint,
    }
    return {**binding, "binding_id": _digest(binding)}


def make_material_fact_envelope(
    policy: dict[str, Any],
    *,
    repository: str,
    task_id: str,
    frozen_head_sha: str,
    reason: str,
    source_evidence: str,
) -> dict[str, Any]:
    """Build the canonical material-fact envelope an authority must verify."""

    envelope = {
        "repository": repository,
        "task_id": task_id,
        "frozen_head_sha": frozen_head_sha,
        "policy_id": policy.get("policy_id"),
        "policy_digest": policy_digest(policy),
        "reason": reason,
        "source_evidence": source_evidence,
        "source_evidence_digest": hashlib.sha256(source_evidence.encode("utf-8")).hexdigest(),
    }
    return {**envelope, "envelope_id": _digest(envelope)}


def _review_binding_scope(binding: dict[str, Any] | None) -> tuple[str, ...]:
    if binding is None:
        # An absent trusted binding is intentionally not a new scope.  It can
        # never reset the review budget and cannot authorize execution.
        return ("unbound",)
    return (
        binding["repository"],
        binding["task_id"],
        binding["tier"],
        binding["policy_id"],
        binding["policy_digest"],
        binding["classifier_revision"],
        binding["risk_fingerprint"],
    )


def _review_scope_digest(binding: dict[str, Any] | None) -> str:
    return _digest({"scope": list(_review_binding_scope(binding))})


def _material_envelope_id(snapshot: dict[str, Any]) -> str:
    envelope = snapshot.get("material_fact_envelope")
    return envelope["envelope_id"] if isinstance(envelope, dict) else ""


def _non_negative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _positive_int(value: object) -> bool:
    return _non_negative_int(value) and value >= 1


def _validate_review_binding_shape(
    binding: object,
    snapshot: dict[str, Any],
    policy: dict[str, Any],
) -> None:
    if not isinstance(binding, dict):
        raise GuardError("snapshot.review_binding must be an object when present")
    expected = {
        "repository",
        "task_id",
        "base_head_sha",
        "head_sha",
        "tier",
        "policy_id",
        "policy_digest",
        "classifier_revision",
        "risk_fingerprint",
        "binding_id",
    }
    if set(binding) != expected:
        raise GuardError("review binding must contain its exact canonical coordinates")
    if binding["repository"] != snapshot["repository"] or binding["task_id"] != snapshot["task_id"]:
        raise GuardError("review binding must be tied to the snapshot repository and task")
    if binding["head_sha"] != snapshot["task_head_sha"]:
        raise GuardError("review binding must be tied to the snapshot technical head")
    for key in ("base_head_sha", "head_sha"):
        if not isinstance(binding[key], str) or SHA_RE.fullmatch(binding[key]) is None:
            raise GuardError(f"review binding {key} must be a lowercase 40-hex SHA")
    for key in ("tier", "classifier_revision"):
        if not isinstance(binding[key], str) or not binding[key].strip():
            raise GuardError(f"review binding {key} must be a non-empty string")
    if binding["policy_id"] != policy["policy_id"] or binding["policy_digest"] != policy_digest(policy):
        raise GuardError("review binding policy identity does not match the loaded policy")
    for key in ("risk_fingerprint", "binding_id"):
        if not isinstance(binding[key], str) or FINGERPRINT_RE.fullmatch(binding[key]) is None:
            raise GuardError(f"review binding {key} must be a lowercase 64-hex digest")
    if binding["binding_id"] != _digest(_review_binding_payload(binding)):
        raise GuardError("review binding canonical digest does not match its coordinates")


def _validate_material_envelope_shape(
    envelope: object,
    snapshot: dict[str, Any],
    policy: dict[str, Any],
) -> None:
    if not isinstance(envelope, dict):
        raise GuardError("snapshot.material_fact_envelope must be an object when present")
    expected = {
        "repository",
        "task_id",
        "frozen_head_sha",
        "policy_id",
        "policy_digest",
        "reason",
        "source_evidence",
        "source_evidence_digest",
        "envelope_id",
    }
    if set(envelope) != expected:
        raise GuardError("material fact envelope must contain its exact canonical coordinates")
    if envelope["repository"] != snapshot["repository"] or envelope["task_id"] != snapshot["task_id"]:
        raise GuardError("material fact envelope must be tied to the snapshot repository and task")
    if not isinstance(envelope["frozen_head_sha"], str) or SHA_RE.fullmatch(envelope["frozen_head_sha"]) is None:
        raise GuardError("material fact envelope frozen_head_sha must be a lowercase 40-hex SHA")
    if envelope["policy_id"] != policy["policy_id"] or envelope["policy_digest"] != policy_digest(policy):
        raise GuardError("material fact envelope policy identity does not match the loaded policy")
    if envelope["reason"] not in CANONICAL_MATERIAL_CHANGE_REASONS:
        raise GuardError("material fact envelope reason is not permitted by candidate-freeze policy")
    if not isinstance(envelope["source_evidence"], str) or not envelope["source_evidence"].strip():
        raise GuardError("material fact envelope requires source evidence")
    if (
        not isinstance(envelope["source_evidence_digest"], str)
        or FINGERPRINT_RE.fullmatch(envelope["source_evidence_digest"]) is None
        or envelope["source_evidence_digest"]
        != hashlib.sha256(envelope["source_evidence"].encode("utf-8")).hexdigest()
    ):
        raise GuardError("material fact envelope evidence digest does not match source evidence")
    if (
        not isinstance(envelope["envelope_id"], str)
        or FINGERPRINT_RE.fullmatch(envelope["envelope_id"]) is None
        or envelope["envelope_id"] != _digest(_material_envelope_payload(envelope))
    ):
        raise GuardError("material fact envelope canonical digest does not match its coordinates")


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise GuardError("bounded execution policy schema_version must be 1")
    if not isinstance(policy.get("policy_id"), str) or not policy["policy_id"].strip():
        raise GuardError("bounded execution policy_id must be a non-empty immutable identifier")
    if set(policy.get("states", [])) != CANONICAL_STATES or len(policy.get("states", [])) != len(CANONICAL_STATES):
        raise GuardError("bounded execution states do not match the canonical state set")
    if set(policy.get("session_release_states", [])) != CANONICAL_RELEASE_STATES or len(policy.get("session_release_states", [])) != len(CANONICAL_RELEASE_STATES):
        raise GuardError("session_release_states do not match the canonical release-state set")

    fields = policy.get("progress_fingerprint_fields")
    if fields != list(CANONICAL_PROGRESS_FINGERPRINT_FIELDS):
        raise GuardError("progress_fingerprint_fields must match the canonical material field set")

    budgets = policy.get("retry_budgets")
    expected_budgets = {
        "identical_failure_cycles",
        "heavy_validation_attempts",
        "external_review_invocations_per_fingerprint",
        "same_head_gate_rechecks_per_evidence_generation",
    }
    if not isinstance(budgets, dict) or set(budgets) != expected_budgets:
        raise GuardError("retry_budgets fields do not match the canonical policy")
    if any(not _non_negative_int(budgets[k]) for k in expected_budgets):
        raise GuardError("all retry budgets must be non-negative integers")
    if policy.get("retry_counter_scopes") != EXPECTED_COUNTER_SCOPES:
        raise GuardError("retry_counter_scopes do not match the canonical generation scopes")

    freeze = policy.get("candidate_freeze")
    forbidden = freeze.get("forbidden_actions_without_material_change") if isinstance(freeze, dict) else None
    if not isinstance(forbidden, list) or not forbidden or not all(isinstance(x, str) and x for x in forbidden):
        raise GuardError("candidate_freeze forbidden action list is invalid")
    if (
        not CANONICAL_FROZEN_FORBIDDEN_ACTIONS.issubset(set(forbidden))
        or len(set(forbidden)) != len(forbidden)
        or any(action not in SUPPORTED_ACTIONS for action in forbidden)
    ):
        raise GuardError("candidate_freeze forbidden action list must retain canonical forbidden actions")
    material_reasons = freeze.get("material_change_reasons") if isinstance(freeze, dict) else None
    if (
        not isinstance(material_reasons, list)
        or set(material_reasons) != CANONICAL_MATERIAL_CHANGE_REASONS
        or len(material_reasons) != len(CANONICAL_MATERIAL_CHANGE_REASONS)
    ):
        raise GuardError("candidate_freeze material change reasons are not canonical")

    loop = policy.get("loop_breaker")
    if not isinstance(loop, dict):
        raise GuardError("loop_breaker policy is required")
    for key in (
        "late_material_finding_threshold",
        "post_freeze_material_head_change_threshold",
        "final_qualification_generations_per_audit",
    ):
        if not _positive_int(loop.get(key)):
            raise GuardError(f"loop_breaker.{key} must be a positive integer")
    for key in ("late_material_finding_threshold", "post_freeze_material_head_change_threshold"):
        if loop[key] > MAX_ORGANIZATION_LOOP_BREAKER_THRESHOLD:
            raise GuardError(
                f"loop_breaker.{key} may be stricter but cannot exceed the organization threshold of {MAX_ORGANIZATION_LOOP_BREAKER_THRESHOLD}"
            )
    if loop["final_qualification_generations_per_audit"] != 1:
        raise GuardError("loop breaker permits exactly one final qualification generation per audit")
    if set(loop.get("material_finding_severities", [])) != {"P0", "P1", "P2"}:
        raise GuardError("loop breaker material finding severities must be P0/P1/P2")
    if tuple(loop.get("risk_classes", [])) != CANONICAL_RISK_CLASSES:
        raise GuardError("loop breaker risk classes do not match the canonical ledger")
    if set(loop.get("ledger_statuses", [])) != CANONICAL_LEDGER_STATUSES:
        raise GuardError("loop breaker ledger statuses are invalid")
    if set(loop.get("ledger_terminal_statuses", [])) != CANONICAL_LEDGER_TERMINAL_STATUSES:
        raise GuardError("loop breaker terminal ledger statuses are invalid")

    dependency_kinds = policy.get("dependency_kinds")
    if not isinstance(dependency_kinds, list) or not dependency_kinds or not all(isinstance(x, str) and x for x in dependency_kinds):
        raise GuardError("dependency_kinds must be a non-empty string list")
    if len(set(dependency_kinds)) != len(dependency_kinds):
        raise GuardError("dependency_kinds must be unique")
    if "external" not in dependency_kinds:
        raise GuardError("dependency_kinds must retain canonical external support")


def _loop_triggered(snapshot: dict[str, Any], policy: dict[str, Any]) -> bool:
    loop = policy["loop_breaker"]
    return (
        snapshot["late_material_findings"] >= loop["late_material_finding_threshold"]
        or snapshot["post_freeze_material_head_changes"] >= loop["post_freeze_material_head_change_threshold"]
    )


def _ledger_required(snapshot: dict[str, Any], policy: dict[str, Any]) -> bool:
    return (
        _loop_triggered(snapshot, policy)
        or snapshot["audited_late_material_findings"] > 0
        or snapshot["audited_post_freeze_material_head_changes"] > 0
        or snapshot["final_qualification_runs_since_audit"] > 0
        or snapshot["phase"] == "LOOP_BREAKER_AUDIT"
    )


def _validate_ledger(snapshot: dict[str, Any], policy: dict[str, Any], required: bool) -> None:
    ledger = snapshot.get("risk_ledger")
    if ledger is None and not required:
        return
    if not isinstance(ledger, dict) or set(ledger) != set(CANONICAL_RISK_CLASSES):
        raise GuardError("snapshot.risk_ledger must contain every canonical risk class exactly once")
    allowed = set(policy["loop_breaker"]["ledger_statuses"])
    for risk_class in CANONICAL_RISK_CLASSES:
        entry = ledger[risk_class]
        if not isinstance(entry, dict) or set(entry) != {"status", "reason"}:
            raise GuardError(f"snapshot.risk_ledger.{risk_class} must contain exactly status and reason")
        if entry["status"] not in allowed:
            raise GuardError(f"snapshot.risk_ledger.{risk_class}.status is invalid")
        if not isinstance(entry["reason"], str):
            raise GuardError(f"snapshot.risk_ledger.{risk_class}.reason must be a string")
        if entry["status"] == "NOT_APPLICABLE" and not entry["reason"].strip():
            raise GuardError(f"snapshot.risk_ledger.{risk_class} NOT_APPLICABLE requires a reason")


def _ledger_terminal(snapshot: dict[str, Any], policy: dict[str, Any]) -> bool:
    ledger = snapshot.get("risk_ledger")
    if not isinstance(ledger, dict):
        return False
    terminal = set(policy["loop_breaker"]["ledger_terminal_statuses"])
    return all(
        isinstance(ledger.get(name), dict) and ledger[name].get("status") in terminal
        for name in CANONICAL_RISK_CLASSES
    )


def validate_snapshot(snapshot: dict[str, Any], policy: dict[str, Any]) -> None:
    if not isinstance(snapshot, dict):
        raise GuardError("snapshot must be an object")
    keys = set(snapshot)
    missing = CANONICAL_SNAPSHOT_REQUIRED_FIELDS - keys
    unknown = keys - CANONICAL_SNAPSHOT_REQUIRED_FIELDS - CANONICAL_SNAPSHOT_OPTIONAL_FIELDS
    if missing or unknown:
        raise GuardError(
            f"snapshot must contain canonical fields only; missing={sorted(missing)!r}, unknown={sorted(unknown)!r}"
        )
    if not isinstance(snapshot.get("repository"), str) or snapshot["repository"].count("/") != 1:
        raise GuardError("snapshot.repository must use owner/name form")
    if not isinstance(snapshot.get("task_id"), str) or not snapshot["task_id"].strip():
        raise GuardError("snapshot.task_id must be non-empty")
    if snapshot.get("state") not in policy["states"]:
        raise GuardError(f"snapshot.state is not canonical: {snapshot.get('state')!r}")
    if not isinstance(snapshot.get("phase"), str) or not snapshot["phase"].strip():
        raise GuardError("snapshot.phase must be non-empty")
    head = snapshot.get("task_head_sha")
    if not isinstance(head, str) or SHA_RE.fullmatch(head) is None:
        raise GuardError("snapshot.task_head_sha must be a lowercase 40-hex SHA")
    for key in ("candidate_frozen", "completion_verified", "material_change"):
        if not isinstance(snapshot.get(key), bool):
            raise GuardError(f"snapshot.{key} must be boolean")
    if snapshot["state"] == "DONE" and not snapshot["completion_verified"]:
        raise GuardError("snapshot state DONE requires completion_verified=true")
    for key in (
        "blocking_dependency",
        "dependency_kind",
        "gate_state",
        "review_generation",
        "review_fingerprint",
        "evidence_generation",
        "first_material_failure",
        "material_change_reason",
        "material_change_evidence",
        "material_fact_id",
        "material_fact_head",
        "repair_generation_id",
        "repair_base_head",
    ):
        if not isinstance(snapshot.get(key), str):
            raise GuardError(f"snapshot.{key} must be a string")
    # ``review_fingerprint`` remains accepted only for a backwards-compatible
    # snapshot shape.  It is never a budget scope or an authorization input;
    # only review_binding can serve those roles.
    if snapshot["review_fingerprint"] and FINGERPRINT_RE.fullmatch(snapshot["review_fingerprint"]) is None:
        raise GuardError("snapshot.review_fingerprint must be empty or a lowercase 64-hex legacy digest")
    if not isinstance(snapshot.get("material_fact_verified"), bool):
        raise GuardError("snapshot.material_fact_verified must be boolean")

    review_binding = snapshot.get("review_binding")
    if review_binding is not None:
        _validate_review_binding_shape(review_binding, snapshot, policy)
    material_envelope = snapshot.get("material_fact_envelope")
    if material_envelope is not None:
        _validate_material_envelope_shape(material_envelope, snapshot, policy)
    if snapshot["material_change"] and material_envelope is None:
        raise GuardError("material_change requires a trusted material fact envelope")

    repair_recorded = bool(snapshot["repair_generation_id"])
    if repair_recorded:
        if FINGERPRINT_RE.fullmatch(snapshot["repair_generation_id"]) is None:
            raise GuardError("repair_generation_id must be a lowercase 64-hex identifier")
        if SHA_RE.fullmatch(snapshot["repair_base_head"]) is None:
            raise GuardError("repair_base_head must be a lowercase 40-hex SHA")
        if material_envelope is None:
            raise GuardError("repair generation requires a trusted material fact envelope")
        if snapshot["repair_generation_id"] != material_envelope["envelope_id"]:
            raise GuardError("repair generation must be bound to its material fact envelope")
    elif snapshot["repair_base_head"]:
        raise GuardError("repair_base_head requires repair_generation_id")
    if snapshot["material_change"] and not snapshot["material_change_evidence"].strip():
        raise GuardError("material_change requires a durable evidence reference")
    for key in (*RETRY_COUNTER_FIELDS, *LOOP_BREAKER_COUNTER_FIELDS):
        if not _non_negative_int(snapshot.get(key)):
            raise GuardError(f"snapshot.{key} must be a non-negative integer")
    if snapshot["audited_late_material_findings"] > snapshot["late_material_findings"]:
        raise GuardError("audited late-finding count cannot exceed observed late findings")
    if snapshot["audited_post_freeze_material_head_changes"] > snapshot["post_freeze_material_head_changes"]:
        raise GuardError("audited post-freeze head-change count cannot exceed observed head changes")
    if snapshot["dependency_kind"] not in {"", *policy["dependency_kinds"]}:
        raise GuardError("snapshot.dependency_kind is invalid")
    _validate_ledger(snapshot, policy, _ledger_required(snapshot, policy))
    if snapshot["state"] == "DONE" and _loop_triggered(snapshot, policy) and not _ledger_terminal(snapshot, policy):
        raise GuardError("snapshot state DONE requires a terminal loop-breaker risk ledger")


def progress_fingerprint(snapshot: dict[str, Any], policy: dict[str, Any]) -> str:
    validate_policy(policy)
    validate_snapshot(snapshot, policy)
    material = {
        field: (
            _review_scope_digest(snapshot.get("review_binding"))
            if field == "review_binding_scope"
            else _material_envelope_id(snapshot)
            if field == "material_fact_envelope_id"
            else snapshot.get(field, "")
        )
        for field in policy["progress_fingerprint_fields"]
    }
    return _digest(material)


def failure_fingerprint(snapshot: dict[str, Any]) -> str:
    return _digest(
        {
            "repository": snapshot.get("repository", ""),
            "task_id": snapshot.get("task_id", ""),
            "task_head_sha": snapshot.get("task_head_sha", ""),
            "blocking_dependency": snapshot.get("blocking_dependency", ""),
            "dependency_kind": snapshot.get("dependency_kind", ""),
            "gate_state": snapshot.get("gate_state", ""),
            "first_material_failure": snapshot.get("first_material_failure", ""),
        }
    )


def _counter_scope(snapshot: dict[str, Any], field: str) -> tuple[str, ...]:
    if field == "identical_failure_cycles":
        return (snapshot["task_head_sha"], failure_fingerprint(snapshot))
    if field == "heavy_validation_runs":
        return (snapshot["task_head_sha"],)
    if field == "external_review_invocations":
        return _review_binding_scope(snapshot.get("review_binding"))
    if field == "same_head_gate_rechecks":
        return (snapshot["task_head_sha"], *_review_binding_scope(snapshot.get("review_binding")))
    raise GuardError(f"unknown retry counter field: {field}")


def _loop_audit_current(snapshot: dict[str, Any], policy: dict[str, Any]) -> bool:
    return (
        _ledger_terminal(snapshot, policy)
        and snapshot["audited_late_material_findings"] == snapshot["late_material_findings"]
        and snapshot["audited_post_freeze_material_head_changes"] == snapshot["post_freeze_material_head_changes"]
    )


def _validate_history(
    previous: dict[str, Any],
    current: dict[str, Any],
    action: str,
    policy: dict[str, Any],
) -> None:
    if action == "observe":
        for field in OBSERVATION_IMMUTABLE_FIELDS:
            if current.get(field) != previous.get(field):
                raise GuardError(
                    f"observe cannot alter protected execution field {field}; use a reserved control-plane action"
                )

    consuming_field = ACTION_COUNTER_FIELDS.get(action)
    for field in RETRY_COUNTER_FIELDS:
        same_scope = _counter_scope(previous, field) == _counter_scope(current, field)
        if same_scope:
            if current[field] < previous[field]:
                raise GuardError(f"snapshot.{field} cannot decrease within its durable generation scope")
            if current[field] > previous[field] and field != consuming_field:
                raise GuardError(
                    f"snapshot.{field} may increase only while its own bounded action is reserved"
                )
        elif field != consuming_field and current[field] != 0:
            raise GuardError(
                f"snapshot.{field} must reset to zero when its durable generation scope changes"
            )

    for field in (
        "late_material_findings",
        "post_freeze_material_head_changes",
        "audited_late_material_findings",
        "audited_post_freeze_material_head_changes",
    ):
        if current[field] < previous[field]:
            raise GuardError(f"snapshot.{field} cannot decrease")

    head_changed = current["task_head_sha"] != previous["task_head_sha"]
    if (
        head_changed
        and (_loop_triggered(previous, policy) or _loop_triggered(current, policy))
        and _ledger_terminal(previous, policy)
        and _ledger_terminal(current, policy)
    ):
        raise GuardError(
            "a terminal loop-breaker audit ledger is bound to its audited technical head and must reopen on head change"
        )
    repair_opening = previous["candidate_frozen"] and not current["candidate_frozen"]
    repair_open = bool(previous["repair_generation_id"])
    post_freeze_increased = (
        current["post_freeze_material_head_changes"]
        > previous["post_freeze_material_head_changes"]
    )
    if repair_opening:
        if action != "open_material_repair":
            raise GuardError("a frozen candidate may unfreeze only through open_material_repair")
        envelope = current.get("material_fact_envelope")
        if not isinstance(envelope, dict):
            raise GuardError("repair opening requires a trusted material fact envelope")
        if envelope["frozen_head_sha"] != previous["task_head_sha"]:
            raise GuardError("material fact envelope must be bound to the prior frozen candidate head")
        if not current["material_change"]:
            raise GuardError("repair opening requires a material change derived from the trusted envelope")
        if (
            current["post_freeze_material_head_changes"]
            != previous["post_freeze_material_head_changes"] + 1
        ):
            raise GuardError(
                "a technical head move from a frozen candidate must increment post_freeze_material_head_changes exactly once"
            )
        if current["repair_generation_id"] != envelope["envelope_id"]:
            raise GuardError(
                "repair opening must establish the durable generation identifier for its material fact envelope"
            )
        if current["repair_base_head"] != previous["task_head_sha"]:
            raise GuardError("repair opening must retain the prior frozen head as its repair base")
    elif previous["candidate_frozen"] and head_changed:
        raise GuardError(
            "a frozen candidate cannot move technical head without first opening a durable repair generation"
        )
    elif post_freeze_increased:
        raise GuardError(
            "post_freeze_material_head_changes may increase only when a frozen candidate opens a durable repair generation"
        )

    if not previous["candidate_frozen"] and not current["candidate_frozen"] and repair_open:
        for field in ("material_fact_envelope", "repair_generation_id", "repair_base_head"):
            if current[field] != previous[field]:
                raise GuardError("an open repair generation must retain its trusted material fact and base coordinates")
    if action == "refreeze_candidate":
        if previous["candidate_frozen"] or not current["candidate_frozen"] or not repair_open:
            raise GuardError("refreeze_candidate must transition an open repair from candidate_frozen=false to true")
    if not previous["candidate_frozen"] and current["candidate_frozen"] and repair_open:
        if action != "refreeze_candidate":
            raise GuardError("refreeze requires the reserved refreeze_candidate control-plane action")
        for field in ("material_fact_envelope", "repair_generation_id", "repair_base_head"):
            if current[field] != previous[field]:
                raise GuardError("refreeze must retain the repair generation's durable material fact")
        if current["task_head_sha"] == previous["repair_base_head"]:
            raise GuardError("refreeze requires a new technical head beyond the repair base")
        if _review_binding_scope(current.get("review_binding")) == _review_binding_scope(previous.get("review_binding")):
            raise GuardError(
                "refreeze requires a changed trusted review risk binding, not a SHA-only move"
            )

    ledger_certified = not _ledger_terminal(previous, policy) and _ledger_terminal(current, policy)
    if ledger_certified and action != "record_loop_breaker_audit":
        raise GuardError("terminal risk-ledger certification may occur only through record_loop_breaker_audit")

    audit_advanced = (
        current["audited_late_material_findings"] > previous["audited_late_material_findings"]
        or current["audited_post_freeze_material_head_changes"] > previous["audited_post_freeze_material_head_changes"]
    )
    if audit_advanced:
        if action != "record_loop_breaker_audit":
            raise GuardError("audited loop-breaker state may advance only through record_loop_breaker_audit")
        if previous["phase"] != "LOOP_BREAKER_AUDIT" and current["phase"] != "LOOP_BREAKER_AUDIT":
            raise GuardError("audited loop-breaker counters may advance only in LOOP_BREAKER_AUDIT")
        if _ledger_terminal(previous, policy):
            raise GuardError(
                "a renewed LOOP_BREAKER_AUDIT must reopen at least one risk class before advancing audited counters"
            )
        if not _ledger_terminal(current, policy):
            raise GuardError("audited loop-breaker counters require a terminal risk ledger")
        if (
            current["audited_late_material_findings"] != current["late_material_findings"]
            or current["audited_post_freeze_material_head_changes"] != current["post_freeze_material_head_changes"]
        ):
            raise GuardError("a completed LOOP_BREAKER_AUDIT must cover the whole observed generation")
        if current["final_qualification_runs_since_audit"] != 0:
            raise GuardError("a renewed LOOP_BREAKER_AUDIT must reset final qualification generation consumption to zero")

    previous_audit = (
        previous["audited_late_material_findings"],
        previous["audited_post_freeze_material_head_changes"],
    )
    current_audit = (
        current["audited_late_material_findings"],
        current["audited_post_freeze_material_head_changes"],
    )
    if (
        current_audit == previous_audit
        and current["final_qualification_runs_since_audit"] < previous["final_qualification_runs_since_audit"]
    ):
        raise GuardError("snapshot.final_qualification_runs_since_audit cannot decrease within one audit generation")
    if (
        current["final_qualification_runs_since_audit"] > previous["final_qualification_runs_since_audit"]
        and action != "enter_final_qualification"
    ):
        raise GuardError("final qualification generation consumption may increase only on enter_final_qualification")


def _decision(
    allowed: bool,
    state: str,
    reason: str,
    release_session: bool,
    progress: str,
    failure: str,
) -> Decision:
    return Decision(allowed, state, reason, release_session, progress, failure)


def _checkpoint_digest(snapshot: dict[str, Any]) -> str:
    """Use material durable identity for CAS while persisting the full snapshot."""

    return checkpoint_digest(snapshot)


def _execution_prerequisite_reason(
    context: ExecutionContext | None,
    current: dict[str, Any],
    action: str,
) -> str | None:
    if action == "observe":
        return None
    if context is None:
        return "reservation_required: durable checkpoint/outbox and trusted authority are not configured"
    if action == "open_material_repair":
        envelope = current.get("material_fact_envelope")
        if not isinstance(envelope, dict) or not context.evidence_authority.verify_material_fact_envelope(envelope):
            return "trusted_material_fact_envelope_required: repair evidence is absent, mismatched, or unverified"
    # An already-observed external dependency is non-dispatch control-plane work:
    # let the external-wait branch persist WAITING_EXTERNAL even without review authority.
    if current["dependency_kind"] == "external" and current["blocking_dependency"] and action != "complete":
        return None
    binding = current.get("review_binding")
    if not isinstance(binding, dict) or not context.evidence_authority.verify_review_binding(binding):
        return "trusted_review_binding_required: review binding is absent, mismatched, or unverified"
    return None


def _dispatch_scope(current: dict[str, Any], action: str) -> tuple[str, ...]:
    scope = list(_review_binding_scope(current.get("review_binding")))
    if action == "run_loop_breaker_audit":
        scope.append(
            "loop_breaker_audit_generation:"
            f"{current['late_material_findings']}:"
            f"{current['post_freeze_material_head_changes']}"
        )
    return tuple(scope)


def _reserve_execution(
    context: ExecutionContext,
    previous: dict[str, Any] | None,
    current: dict[str, Any],
    action: str,
    state: str,
    reason: str,
    release_session: bool,
    progress: str,
    failure: str,
) -> Decision:
    next_snapshot = current if state == current["state"] else {**current, "state": state}
    reservation = context.checkpoint_outbox.reserve(
        repository=current["repository"],
        task_id=current["task_id"],
        expected_checkpoint=_checkpoint_digest(previous) if previous is not None else None,
        next_checkpoint=_checkpoint_digest(next_snapshot),
        next_snapshot=next_snapshot,
        action=action,
        scope=_dispatch_scope(current, action),
    )
    if not reservation.committed:
        return Decision(
            False,
            state,
            reservation.reason,
            release_session,
            progress,
            failure,
            reservation.reservation_key,
        )
    return Decision(True, state, reason, release_session, progress, failure, reservation.reservation_key)


def _transition_state(
    context: ExecutionContext,
    previous: dict[str, Any] | None,
    current: dict[str, Any],
    state: str,
    reason: str,
    *,
    allowed: bool,
    release_session: bool,
    progress: str,
    failure: str,
) -> Decision:
    next_snapshot = current if state == current["state"] else {**current, "state": state}
    transition = context.checkpoint_outbox.transition(
        repository=current["repository"],
        task_id=current["task_id"],
        expected_checkpoint=_checkpoint_digest(previous) if previous is not None else None,
        next_checkpoint=_checkpoint_digest(next_snapshot),
        next_snapshot=next_snapshot,
        reason=reason,
        scope=_review_binding_scope(current.get("review_binding")),
    )
    if not transition.committed:
        return Decision(
            False,
            current["state"],
            transition.reason,
            False,
            progress,
            failure,
            transition.reservation_key,
        )
    return Decision(
        allowed,
        state,
        reason,
        release_session,
        progress,
        failure,
        transition.reservation_key,
    )


def _action_counter_consumption_reason(
    previous: dict[str, Any] | None,
    current: dict[str, Any],
    action: str,
) -> str | None:
    field = ACTION_COUNTER_FIELDS.get(action)
    if field is None:
        return None
    if action == "retry" and not current["first_material_failure"] and current[field] == 0:
        # This is the initial attempt before any material failure; it is not a retry.
        return None
    if previous is None:
        return f"{action} requires a durable previous snapshot before reserving its counter"
    if _counter_scope(previous, field) != _counter_scope(current, field):
        return f"{action} cannot consume its counter while changing its durable generation scope"
    expected = previous[field] + 1
    if current[field] != expected:
        return (
            f"{action} must consume exactly one {field} counter increment "
            f"from {previous[field]} to {expected}"
        )
    return None


def _counter_denial_state(action: str, current: dict[str, Any]) -> tuple[str, bool]:
    if action in {"request_external_review", "same_head_gate_recheck"}:
        return "WAITING_EXTERNAL", True
    if action in {"retry", "run_heavy_validation"}:
        return "STALLED", True
    return current["state"], current["state"] in CANONICAL_RELEASE_STATES


def decide(
    previous: dict[str, Any] | None,
    current: dict[str, Any],
    requested_action: str,
    policy: dict[str, Any],
    *,
    context: ExecutionContext | None = None,
) -> Decision:
    validate_policy(policy)
    validate_snapshot(current, policy)
    if requested_action not in SUPPORTED_ACTIONS:
        raise GuardError(f"unsupported requested action: {requested_action!r}")

    if previous is not None:
        validate_snapshot(previous, policy)
        if previous["repository"] != current["repository"] or previous["task_id"] != current["task_id"]:
            raise GuardError("previous/current snapshots must describe the same task")
        _validate_history(previous, current, requested_action, policy)

    progress = progress_fingerprint(current, policy)
    failure = failure_fingerprint(current)
    release_states = set(policy["session_release_states"])
    previous_progress = progress_fingerprint(previous, policy) if previous is not None else None
    same_progress = previous is not None and progress == previous_progress

    prerequisite_reason = _execution_prerequisite_reason(context, current, requested_action)
    if prerequisite_reason is not None:
        state = current["state"]
        return _decision(
            False,
            state,
            prerequisite_reason,
            state in release_states,
            progress,
            failure,
        )

    def allow(state: str, reason: str, release_session: bool) -> Decision:
        if requested_action == "observe":
            return _decision(True, state, reason, release_session, progress, failure)
        assert context is not None
        return _reserve_execution(
            context,
            previous,
            current,
            requested_action,
            state,
            reason,
            release_session,
            progress,
            failure,
        )

    if previous is not None and previous["state"] == "DONE":
        return _decision(
            requested_action == "observe",
            "DONE",
            "a previously verified DONE snapshot is terminal; only observation is allowed",
            True,
            progress,
            failure,
        )

    if current["state"] == "DONE" and requested_action not in {"observe", "complete"}:
        return _decision(False, "DONE", "DONE is terminal; operational/retrigger actions are forbidden", True, progress, failure)

    if current["state"] == "WAITING_EXTERNAL":
        return _decision(
            requested_action == "observe",
            "WAITING_EXTERNAL",
            "WAITING_EXTERNAL releases ownership; only observation is allowed until explicit material progress",
            True,
            progress,
            failure,
        )

    if current["dependency_kind"] == "external" and current["blocking_dependency"] and current["state"] != "WAITING_EXTERNAL":
        if requested_action == "observe":
            if context is None:
                return _decision(
                    False,
                    current["state"],
                    "reservation_required: external waiting must be durably reserved before ownership is released",
                    False,
                    progress,
                    failure,
                )
            return _transition_state(
                context,
                previous,
                current,
                "WAITING_EXTERNAL",
                "external dependency is pending",
                allowed=True,
                release_session=True,
                progress=progress,
                failure=failure,
            )
        if requested_action != "complete":
            assert context is not None
            return _transition_state(
                context,
                previous,
                current,
                "WAITING_EXTERNAL",
                "external dependency is pending; operational work is forbidden",
                allowed=False,
                release_session=True,
                progress=progress,
                failure=failure,
            )

    if previous is not None and previous["state"] not in release_states and same_progress and requested_action in {"mutate", "retrigger"}:
        return _decision(
            False,
            current["state"],
            "unchanged operational action requires material progress",
            current["state"] in release_states,
            progress,
            failure,
        )

    if previous is not None and previous["state"] in {"WAITING_EXTERNAL", "BLOCKED", "STALLED"} and same_progress and requested_action != "complete":
        return _decision(
            requested_action == "observe",
            previous["state"],
            "released task cannot resume operational work without material progress",
            True,
            progress,
            failure,
        )

    if current["state"] in {"BLOCKED", "STALLED"} and requested_action not in {"observe", "complete"}:
        if (
            previous is not None
            and previous["state"] not in release_states
            and context is not None
        ):
            return _transition_state(
                context, previous, current, current["state"],
                "blocked or stalled task is non-actionable until material progress is recorded",
                allowed=False, release_session=True, progress=progress, failure=failure,
            )
        return _decision(
            False,
            current["state"],
            "blocked or stalled task is non-actionable until material progress is recorded",
            True,
            progress,
            failure,
        )

    final_candidate_actions = {
        "enter_final_qualification",
        "request_external_review",
        "run_heavy_validation",
        "same_head_gate_recheck",
        "complete",
    }
    if (
        requested_action in final_candidate_actions
        and not current["candidate_frozen"]
        and (
            requested_action == "enter_final_qualification"
            or current["phase"] == "final_qualification"
        )
    ):
        return _decision(
            False,
            "READY" if current["state"] == "RUNNING" else current["state"],
            "final qualification requires the exact technical candidate to remain frozen",
            current["state"] in release_states,
            progress,
            failure,
        )

    loop_triggered = _loop_triggered(current, policy)
    loop_current = _loop_audit_current(current, policy)

    if (
        loop_triggered
        and current["final_qualification_runs_since_audit"] > 0
        and requested_action in LOOP_BREAKER_POST_ADMISSION_ACTIONS
        and not current["candidate_frozen"]
    ):
        return _decision(
            False,
            "READY",
            "final qualification actions require the technical candidate to remain frozen",
            False,
            progress,
            failure,
        )

    if requested_action == "run_loop_breaker_audit":
        if not loop_triggered:
            return _decision(False, current["state"], "LOOP_BREAKER_AUDIT is not required before a configured threshold is reached", current["state"] in release_states, progress, failure)
        if current["phase"] != "LOOP_BREAKER_AUDIT":
            return _decision(False, current["state"], "LOOP_BREAKER_AUDIT must be entered explicitly before running the batched risk audit", False, progress, failure)
        if loop_current:
            return _decision(False, current["state"], "LOOP_BREAKER_AUDIT is already current for the observed generation", False, progress, failure)
        return allow(current["state"], "LOOP_BREAKER_AUDIT may run as one bounded batched risk-ledger generation", False)

    if requested_action == "record_loop_breaker_audit":
        assert context is not None
        audit_scope = _dispatch_scope(current, "run_loop_breaker_audit")
        if not context.checkpoint_outbox.has_acknowledged_dispatch(
            current["repository"], current["task_id"], "run_loop_breaker_audit", audit_scope
        ):
            return _decision(
                False,
                current["state"],
                "loop-breaker audit ledger certification requires the exact audit dispatch generation to be dispatched and acknowledged",
                current["state"] in release_states,
                progress,
                failure,
            )

    if loop_triggered and not loop_current and requested_action in LOOP_BREAKER_FINAL_ACTIONS:
        state = "READY" if current["state"] == "RUNNING" else current["state"]
        return _decision(
            False,
            state,
            "LOOP_BREAKER_AUDIT_REQUIRED: complete one batched risk-ledger audit before another final qualification generation",
            False,
            progress,
            failure,
        )

    if (
        loop_triggered
        and loop_current
        and requested_action in LOOP_BREAKER_POST_ADMISSION_ACTIONS
        and current["final_qualification_runs_since_audit"] != 1
    ):
        state = "READY" if current["state"] == "RUNNING" else current["state"]
        return _decision(False, state, "final qualification admission is required before final checks/review/completion", False, progress, failure)

    if requested_action == "enter_final_qualification":
        if current["phase"] != "final_qualification":
            return _decision(False, "READY", "enter_final_qualification must persist phase final_qualification", False, progress, failure)
        if (
            previous is None
            or not previous["candidate_frozen"]
            or previous["task_head_sha"] != current["task_head_sha"]
        ):
            return _decision(False, "READY", "enter_final_qualification requires the previous durable checkpoint to already contain the same frozen technical candidate", False, progress, failure)
        if loop_triggered:
            if previous is None:
                return _decision(False, "READY", "record the durable pre-admission audit snapshot before consuming final qualification", False, progress, failure)
            expected = previous["final_qualification_runs_since_audit"] + 1
            consumed = current["final_qualification_runs_since_audit"]
            limit = policy["loop_breaker"]["final_qualification_generations_per_audit"]
            if consumed != expected:
                return _decision(False, "READY", "record exactly one newly consumed final qualification generation before admission", False, progress, failure)
            if consumed > limit:
                return _decision(False, "READY", "final qualification generation budget for the current LOOP_BREAKER_AUDIT is exhausted", False, progress, failure)
        return allow("READY", "qualification admission is within the current bounded audit generation", False)

    if requested_action == "complete":
        if (
            previous is None
            or not previous["candidate_frozen"]
            or previous["phase"] != "final_qualification"
            or previous["task_head_sha"] != current["task_head_sha"]
        ):
            state = current["state"] if current["state"] in release_states else "READY"
            return _decision(
                False,
                state,
                "DONE requires a previous durable checkpoint for the same frozen final_qualification candidate",
                state in release_states,
                progress,
                failure,
            )
        if (
            not current["candidate_frozen"]
            or current["phase"] != "final_qualification"
        ):
            state = current["state"] if current["state"] in release_states else "READY"
            return _decision(
                False,
                state,
                "DONE is forbidden until the exact technical candidate is frozen in final qualification",
                state in release_states,
                progress,
                failure,
            )
        if loop_triggered and not _ledger_terminal(current, policy):
            state = current["state"] if current["state"] in release_states else "READY"
            return _decision(False, state, "DONE is forbidden until the loop-breaker risk ledger is terminal", state in release_states, progress, failure)
        if not current["completion_verified"]:
            state = current["state"] if current["state"] in release_states else "READY"
            return _decision(False, state, "DONE is forbidden until completion verification is requested", state in release_states, progress, failure)
        assert context is not None
        if not context.evidence_authority.verify_completion(current):
            state = current["state"] if current["state"] in release_states else "READY"
            return _decision(
                False,
                state,
                "trusted_completion_required: exact candidate completion evidence is absent, mismatched, or unverified",
                state in release_states,
                progress,
                failure,
            )
        return allow("DONE", "trusted completion evidence is verified", True)

    forbidden_when_frozen = set(policy["candidate_freeze"]["forbidden_actions_without_material_change"])
    if current["candidate_frozen"] and requested_action in forbidden_when_frozen:
        if current["state"] in release_states:
            state = current["state"]
        elif current["dependency_kind"] == "external":
            state = "WAITING_EXTERNAL"
        elif current["state"] == "RUNNING":
            state = "READY"
        else:
            state = current["state"]
        return _decision(
            False,
            state,
            "candidate is frozen; mutation/retrigger requires a separately recorded durable repair-unfreeze transition and never accepts a self-attested flag",
            state in release_states,
            progress,
            failure,
        )

    counter_field = ACTION_COUNTER_FIELDS.get(requested_action)
    if counter_field is not None:
        consumption_reason = _action_counter_consumption_reason(
            previous, current, requested_action
        )
        if consumption_reason is not None:
            state, release = _counter_denial_state(requested_action, current)
            return _decision(False, state, consumption_reason, release, progress, failure)

        budget = policy["retry_budgets"][ACTION_COUNTER_BUDGETS[requested_action]]
        counter_value = current[counter_field]
        exhausted = (
            requested_action == "retry"
            and bool(current["first_material_failure"])
            and counter_value >= budget
        ) or (requested_action != "retry" and counter_value > budget)
        if exhausted:
            state, release = _counter_denial_state(requested_action, current)
            reason = f"{requested_action} counter budget is exhausted for its durable generation"
            if state in release_states:
                assert context is not None
                return _transition_state(
                    context,
                    previous,
                    current,
                    state,
                    reason,
                    allowed=False,
                    release_session=release,
                    progress=progress,
                    failure=failure,
                )
            return _decision(False, state, reason, release, progress, failure)

    if requested_action in {"request_external_review", "same_head_gate_recheck"}:
        return allow(
            "WAITING_EXTERNAL",
            "external evidence is pending after the bounded asynchronous action",
            True,
        )

    return allow(
        current["state"],
        "requested action remains within the bounded execution policy",
        current["state"] in release_states,
    )


def _load_json(path: str) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise GuardError(f"{path}: expected a JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate bounded autonomous execution state")
    parser.add_argument("--policy", required=True)
    parser.add_argument("--current", required=True)
    parser.add_argument("--previous")
    parser.add_argument("--action", required=True)
    args = parser.parse_args()

    policy = _load_json(args.policy)
    current = _load_json(args.current)
    previous = _load_json(args.previous) if args.previous else None
    result = decide(previous, current, args.action, policy)
    print(json.dumps(result.as_dict(), sort_keys=True))
    return 0 if result.allowed else 2


if __name__ == "__main__":
    raise SystemExit(main())
