#!/usr/bin/env python3
"""Deterministic bounded-autonomous-execution guard."""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import re
from pathlib import Path
from typing import Any

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
}
MAX_ORGANIZATION_LOOP_BREAKER_THRESHOLD = 2
CANONICAL_PROGRESS_FINGERPRINT_FIELDS = (
    "repository",
    "task_id",
    "task_head_sha",
    "phase",
    "blocking_dependency",
    "dependency_kind",
    "gate_state",
    "review_generation",
    "review_fingerprint",
    "evidence_generation",
    "first_material_failure",
    "material_fact_id",
    "material_fact_head",
)
EXPECTED_COUNTER_SCOPES = {
    "identical_failure_cycles": ["task_head_sha", "failure_fingerprint"],
    "heavy_validation_runs": ["task_head_sha"],
    "external_review_invocations": ["review_fingerprint"],
    "same_head_gate_rechecks": ["task_head_sha", "evidence_generation"],
}


class GuardError(ValueError):
    """Raised when policy or snapshot input is malformed."""


@dataclasses.dataclass(frozen=True)
class Decision:
    allowed: bool
    state: str
    reason: str
    release_session: bool
    progress_fingerprint: str
    failure_fingerprint: str

    def as_dict(self) -> dict[str, object]:
        return dataclasses.asdict(self)


def _digest(value: dict[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _non_negative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _positive_int(value: object) -> bool:
    return _non_negative_int(value) and value >= 1


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise GuardError("bounded execution policy schema_version must be 1")
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
    if FINGERPRINT_RE.fullmatch(snapshot["review_fingerprint"]) is None:
        raise GuardError("snapshot.review_fingerprint must be a lowercase 64-hex canonical fingerprint")
    if not isinstance(snapshot.get("material_fact_verified"), bool):
        raise GuardError("snapshot.material_fact_verified must be boolean")

    fact_fields = (
        snapshot["material_change_reason"],
        snapshot["material_fact_id"],
        snapshot["material_fact_head"],
        snapshot["material_fact_verified"],
    )
    fact_recorded = any(value not in ("", False) for value in fact_fields)
    if fact_recorded:
        if snapshot["material_change_reason"] not in CANONICAL_MATERIAL_CHANGE_REASONS:
            raise GuardError("material fact reason is not permitted by candidate-freeze policy")
        if FINGERPRINT_RE.fullmatch(snapshot["material_fact_id"]) is None:
            raise GuardError("material_fact_id must be a lowercase 64-hex immutable identifier")
        if SHA_RE.fullmatch(snapshot["material_fact_head"]) is None:
            raise GuardError("material_fact_head must be a lowercase 40-hex SHA")
        if not snapshot["material_fact_verified"]:
            raise GuardError("material fact must be independently verified before it can open repair")
    elif snapshot["material_change"]:
        raise GuardError("material_change requires a verified durable material fact")

    repair_recorded = bool(snapshot["repair_generation_id"])
    if repair_recorded:
        if FINGERPRINT_RE.fullmatch(snapshot["repair_generation_id"]) is None:
            raise GuardError("repair_generation_id must be a lowercase 64-hex identifier")
        if SHA_RE.fullmatch(snapshot["repair_base_head"]) is None:
            raise GuardError("repair_base_head must be a lowercase 40-hex SHA")
        if not fact_recorded:
            raise GuardError("repair generation requires its verified material fact")
        if snapshot["repair_generation_id"] != snapshot["material_fact_id"]:
            raise GuardError("repair generation must be bound to its immutable material fact")
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
    return _digest({field: snapshot.get(field, "") for field in policy["progress_fingerprint_fields"]})


def failure_fingerprint(snapshot: dict[str, Any]) -> str:
    return _digest(
        {
            "repository": snapshot.get("repository", ""),
            "task_id": snapshot.get("task_id", ""),
            "task_head_sha": snapshot.get("task_head_sha", ""),
            "blocking_dependency": snapshot.get("blocking_dependency", ""),
            "dependency_kind": snapshot.get("dependency_kind", ""),
            "gate_state": snapshot.get("gate_state", ""),
            "evidence_generation": snapshot.get("evidence_generation", ""),
            "first_material_failure": snapshot.get("first_material_failure", ""),
        }
    )


def _counter_scope(snapshot: dict[str, Any], field: str) -> tuple[str, ...]:
    if field == "identical_failure_cycles":
        return (snapshot["task_head_sha"], failure_fingerprint(snapshot))
    if field == "heavy_validation_runs":
        return (snapshot["task_head_sha"],)
    if field == "external_review_invocations":
        return (snapshot["review_fingerprint"],)
    if field == "same_head_gate_rechecks":
        return (snapshot["task_head_sha"], snapshot["evidence_generation"])
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
    repair_opening = previous["candidate_frozen"] and not current["candidate_frozen"]
    repair_open = bool(previous["repair_generation_id"])
    post_freeze_increased = (
        current["post_freeze_material_head_changes"]
        > previous["post_freeze_material_head_changes"]
    )
    material_fact_fields = (
        "material_change_reason",
        "material_fact_id",
        "material_fact_head",
        "material_fact_verified",
    )
    if repair_opening:
        if not previous["material_fact_verified"]:
            raise GuardError(
                "frozen candidate may open repair only from a verified durable material fact"
            )
        if previous["material_fact_head"] != previous["task_head_sha"]:
            raise GuardError("material fact must be bound to the prior frozen candidate head")
        if any(current[field] != previous[field] for field in material_fact_fields):
            raise GuardError(
                "repair opening must consume the immutable material fact already recorded on the frozen candidate"
            )
        if not current["material_change"]:
            raise GuardError("repair opening requires a material change derived from the durable fact")
        if (
            current["post_freeze_material_head_changes"]
            != previous["post_freeze_material_head_changes"] + 1
        ):
            raise GuardError(
                "a technical head move from a frozen candidate must increment post_freeze_material_head_changes exactly once"
            )
        if current["repair_generation_id"] != previous["material_fact_id"]:
            raise GuardError(
                "repair opening must establish the durable generation identifier for its material fact"
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
        for field in (*material_fact_fields, "repair_generation_id", "repair_base_head"):
            if current[field] != previous[field]:
                raise GuardError("an open repair generation must retain its material fact and base coordinates")
    if not previous["candidate_frozen"] and current["candidate_frozen"] and repair_open:
        for field in (*material_fact_fields, "repair_generation_id", "repair_base_head"):
            if current[field] != previous[field]:
                raise GuardError("refreeze must retain the repair generation's durable material fact")
        if current["task_head_sha"] == previous["repair_base_head"]:
            raise GuardError("refreeze requires a new technical head beyond the repair base")
        if current["review_fingerprint"] == previous["review_fingerprint"]:
            raise GuardError(
                "refreeze requires a changed canonical review fingerprint, not a SHA-only move"
            )

    audit_advanced = (
        current["audited_late_material_findings"] > previous["audited_late_material_findings"]
        or current["audited_post_freeze_material_head_changes"] > previous["audited_post_freeze_material_head_changes"]
    )
    if audit_advanced:
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
            return _decision(True, "WAITING_EXTERNAL", "external dependency is pending", True, progress, failure)
        if requested_action != "complete":
            return _decision(False, "WAITING_EXTERNAL", "external dependency is pending; operational work is forbidden", True, progress, failure)

    if previous is not None and previous["state"] in {"BLOCKED", "STALLED"} and same_progress and requested_action != "complete":
        return _decision(
            requested_action == "observe",
            previous["state"],
            "released task cannot resume operational work without material progress",
            True,
            progress,
            failure,
        )

    if current["state"] in {"BLOCKED", "STALLED"} and requested_action not in {"observe", "complete"}:
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
        and current["phase"] == "final_qualification"
        and not current["candidate_frozen"]
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
        return _decision(True, current["state"], "LOOP_BREAKER_AUDIT may run as one bounded batched risk-ledger generation", False, progress, failure)

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
        return _decision(True, "READY", "qualification admission is within the current bounded audit generation", False, progress, failure)

    if requested_action == "complete":
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
            return _decision(False, state, "DONE is forbidden until completion is independently verified", state in release_states, progress, failure)
        return _decision(True, "DONE", "completion evidence is verified", True, progress, failure)

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
            return _decision(
                False,
                state,
                f"{requested_action} counter budget is exhausted for its durable generation",
                release,
                progress,
                failure,
            )

    return _decision(
        True,
        current["state"],
        "requested action remains within the bounded execution policy",
        current["state"] in release_states,
        progress,
        failure,
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
