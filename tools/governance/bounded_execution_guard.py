#!/usr/bin/env python3
"""Deterministic bounded-autonomous-execution guard.

The module is intentionally network-free. It evaluates durable lifecycle snapshots
and returns a fail-closed decision without interpreting chat/session narrative.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
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
EXPECTED_COUNTER_SCOPES = {
    "identical_failure_cycles": ["task_head_sha", "failure_fingerprint"],
    "heavy_validation_runs": ["task_head_sha"],
    "external_review_invocations": ["task_head_sha", "review_generation"],
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


def _canonical_digest(value: dict[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _positive_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def _non_negative_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise GuardError("bounded execution policy schema_version must be 1")
    states = policy.get("states")
    if (
        not isinstance(states, list)
        or set(states) != CANONICAL_STATES
        or len(states) != len(CANONICAL_STATES)
    ):
        raise GuardError("bounded execution states do not match the canonical state set")
    release_states = policy.get("session_release_states")
    if (
        not isinstance(release_states, list)
        or set(release_states) != CANONICAL_RELEASE_STATES
        or len(release_states) != len(CANONICAL_RELEASE_STATES)
    ):
        raise GuardError("session_release_states do not match the canonical release-state set")
    fields = policy.get("progress_fingerprint_fields")
    if not isinstance(fields, list) or not fields or not all(
        isinstance(item, str) and item for item in fields
    ):
        raise GuardError("progress_fingerprint_fields must be a non-empty string list")
    if "evidence_generation" not in fields:
        raise GuardError("progress_fingerprint_fields must include evidence_generation")

    budgets = policy.get("retry_budgets")
    required_budgets = {
        "identical_failure_cycles",
        "heavy_validation_attempts",
        "external_review_invocations_per_fingerprint",
        "same_head_gate_rechecks_per_evidence_generation",
    }
    if not isinstance(budgets, dict) or set(budgets) != required_budgets:
        raise GuardError("retry_budgets fields do not match the canonical policy")
    if any(not _positive_integer(budgets[key]) for key in required_budgets):
        raise GuardError("all retry budgets must be positive integers")

    counter_scopes = policy.get("retry_counter_scopes")
    if counter_scopes != EXPECTED_COUNTER_SCOPES:
        raise GuardError("retry_counter_scopes do not match the canonical generation scopes")

    freeze = policy.get("candidate_freeze")
    forbidden = (
        freeze.get("forbidden_actions_without_material_change")
        if isinstance(freeze, dict)
        else None
    )
    if not isinstance(forbidden, list) or not forbidden or not all(
        isinstance(item, str) and item for item in forbidden
    ):
        raise GuardError("candidate_freeze forbidden action list is invalid")

    loop = policy.get("loop_breaker")
    if not isinstance(loop, dict):
        raise GuardError("loop_breaker policy is required")
    for key in (
        "late_material_finding_threshold",
        "post_freeze_material_head_change_threshold",
        "final_qualification_generations_per_audit",
    ):
        if not _positive_integer(loop.get(key)):
            raise GuardError(f"loop_breaker.{key} must be a positive integer")
    if loop["final_qualification_generations_per_audit"] != 1:
        raise GuardError("loop breaker permits exactly one final qualification generation per audit")
    severities = loop.get("material_finding_severities")
    if not isinstance(severities, list) or set(severities) != {"P0", "P1", "P2"}:
        raise GuardError("loop breaker material finding severities must be P0/P1/P2")
    risk_classes = loop.get("risk_classes")
    if (
        not isinstance(risk_classes, list)
        or tuple(risk_classes) != CANONICAL_RISK_CLASSES
    ):
        raise GuardError("loop breaker risk classes do not match the canonical ledger")
    ledger_statuses = loop.get("ledger_statuses")
    if (
        not isinstance(ledger_statuses, list)
        or set(ledger_statuses) != CANONICAL_LEDGER_STATUSES
        or len(ledger_statuses) != len(CANONICAL_LEDGER_STATUSES)
    ):
        raise GuardError("loop breaker ledger statuses are invalid")
    terminal_statuses = loop.get("ledger_terminal_statuses")
    if (
        not isinstance(terminal_statuses, list)
        or set(terminal_statuses) != CANONICAL_LEDGER_TERMINAL_STATUSES
        or len(terminal_statuses) != len(CANONICAL_LEDGER_TERMINAL_STATUSES)
    ):
        raise GuardError("loop breaker terminal ledger statuses are invalid")

    dependency_kinds = policy.get("dependency_kinds")
    if not isinstance(dependency_kinds, list) or not all(
        isinstance(item, str) and item for item in dependency_kinds
    ):
        raise GuardError("dependency_kinds must be a non-empty string list")


def _validate_risk_ledger(snapshot: dict[str, Any], policy: dict[str, Any]) -> None:
    ledger = snapshot.get("risk_ledger")
    if not isinstance(ledger, dict) or set(ledger) != set(CANONICAL_RISK_CLASSES):
        raise GuardError("snapshot.risk_ledger must contain every canonical risk class exactly once")
    allowed_statuses = set(policy["loop_breaker"]["ledger_statuses"])
    for risk_class in CANONICAL_RISK_CLASSES:
        entry = ledger.get(risk_class)
        if not isinstance(entry, dict) or set(entry) != {"status", "reason"}:
            raise GuardError(
                f"snapshot.risk_ledger.{risk_class} must contain exactly status and reason"
            )
        status = entry.get("status")
        reason = entry.get("reason")
        if status not in allowed_statuses:
            raise GuardError(f"snapshot.risk_ledger.{risk_class}.status is invalid")
        if not isinstance(reason, str):
            raise GuardError(f"snapshot.risk_ledger.{risk_class}.reason must be a string")
        if status == "NOT_APPLICABLE" and not reason.strip():
            raise GuardError(
                f"snapshot.risk_ledger.{risk_class} NOT_APPLICABLE requires a reason"
            )


def validate_snapshot(snapshot: dict[str, Any], policy: dict[str, Any]) -> None:
    if not isinstance(snapshot, dict):
        raise GuardError("snapshot must be an object")
    repository = snapshot.get("repository")
    if not isinstance(repository, str) or repository.count("/") != 1:
        raise GuardError("snapshot.repository must use owner/name form")
    task_id = snapshot.get("task_id")
    if not isinstance(task_id, str) or not task_id.strip():
        raise GuardError("snapshot.task_id must be non-empty")
    state = snapshot.get("state")
    if state not in policy["states"]:
        raise GuardError(f"snapshot.state is not canonical: {state!r}")
    phase = snapshot.get("phase")
    if not isinstance(phase, str) or not phase.strip():
        raise GuardError("snapshot.phase must be non-empty")
    head = snapshot.get("task_head_sha")
    if not isinstance(head, str) or SHA_RE.fullmatch(head) is None:
        raise GuardError("snapshot.task_head_sha must be a lowercase 40-hex SHA")
    for key in ("candidate_frozen", "completion_verified", "material_change"):
        if not isinstance(snapshot.get(key), bool):
            raise GuardError(f"snapshot.{key} must be boolean")
    if state == "DONE" and not snapshot["completion_verified"]:
        raise GuardError("snapshot state DONE requires completion_verified=true")
    for key in (
        "blocking_dependency",
        "dependency_kind",
        "gate_state",
        "review_generation",
        "evidence_generation",
        "first_material_failure",
    ):
        if not isinstance(snapshot.get(key), str):
            raise GuardError(f"snapshot.{key} must be a string")
    for key in (*RETRY_COUNTER_FIELDS, *LOOP_BREAKER_COUNTER_FIELDS):
        value = snapshot.get(key)
        if not _non_negative_integer(value):
            raise GuardError(f"snapshot.{key} must be a non-negative integer")
    if snapshot["audited_late_material_findings"] > snapshot["late_material_findings"]:
        raise GuardError("audited late-finding count cannot exceed observed late findings")
    if (
        snapshot["audited_post_freeze_material_head_changes"]
        > snapshot["post_freeze_material_head_changes"]
    ):
        raise GuardError("audited post-freeze head-change count cannot exceed observed head changes")
    allowed_dependency_kinds = {"", *policy["dependency_kinds"]}
    if snapshot["dependency_kind"] not in allowed_dependency_kinds:
        raise GuardError("snapshot.dependency_kind is invalid")
    _validate_risk_ledger(snapshot, policy)


def progress_fingerprint(snapshot: dict[str, Any], policy: dict[str, Any]) -> str:
    validate_policy(policy)
    validate_snapshot(snapshot, policy)
    selected = {
        field: snapshot.get(field, "")
        for field in policy["progress_fingerprint_fields"]
    }
    return _canonical_digest(selected)


def failure_fingerprint(snapshot: dict[str, Any]) -> str:
    selected = {
        "repository": snapshot.get("repository", ""),
        "task_id": snapshot.get("task_id", ""),
        "task_head_sha": snapshot.get("task_head_sha", ""),
        "blocking_dependency": snapshot.get("blocking_dependency", ""),
        "dependency_kind": snapshot.get("dependency_kind", ""),
        "gate_state": snapshot.get("gate_state", ""),
        "evidence_generation": snapshot.get("evidence_generation", ""),
        "first_material_failure": snapshot.get("first_material_failure", ""),
    }
    return _canonical_digest(selected)


def _decision(
    *,
    allowed: bool,
    state: str,
    reason: str,
    release_session: bool,
    progress: str,
    failure: str,
) -> Decision:
    return Decision(
        allowed=allowed,
        state=state,
        reason=reason,
        release_session=release_session,
        progress_fingerprint=progress,
        failure_fingerprint=failure,
    )


def _counter_scope(snapshot: dict[str, Any], field: str) -> tuple[str, ...]:
    if field == "identical_failure_cycles":
        return (snapshot["task_head_sha"], failure_fingerprint(snapshot))
    if field == "heavy_validation_runs":
        return (snapshot["task_head_sha"],)
    if field == "external_review_invocations":
        return (snapshot["task_head_sha"], snapshot["review_generation"])
    if field == "same_head_gate_rechecks":
        return (snapshot["task_head_sha"], snapshot["evidence_generation"])
    raise GuardError(f"unknown retry counter field: {field}")


def _ledger_terminal(snapshot: dict[str, Any], policy: dict[str, Any]) -> bool:
    terminal = set(policy["loop_breaker"]["ledger_terminal_statuses"])
    return all(
        snapshot["risk_ledger"][risk_class]["status"] in terminal
        for risk_class in CANONICAL_RISK_CLASSES
    )


def _loop_breaker_triggered(snapshot: dict[str, Any], policy: dict[str, Any]) -> bool:
    loop = policy["loop_breaker"]
    return (
        snapshot["late_material_findings"] >= loop["late_material_finding_threshold"]
        or snapshot["post_freeze_material_head_changes"]
        >= loop["post_freeze_material_head_change_threshold"]
    )


def _loop_breaker_audit_current(snapshot: dict[str, Any], policy: dict[str, Any]) -> bool:
    return (
        _ledger_terminal(snapshot, policy)
        and snapshot["audited_late_material_findings"] == snapshot["late_material_findings"]
        and snapshot["audited_post_freeze_material_head_changes"]
        == snapshot["post_freeze_material_head_changes"]
    )


def _validate_monotonic_history(previous: dict[str, Any], current: dict[str, Any]) -> None:
    for field in RETRY_COUNTER_FIELDS:
        if _counter_scope(previous, field) == _counter_scope(current, field):
            if current[field] < previous[field]:
                raise GuardError(
                    f"snapshot.{field} cannot decrease within its durable generation scope"
                )
    for field in (
        "late_material_findings",
        "post_freeze_material_head_changes",
        "audited_late_material_findings",
        "audited_post_freeze_material_head_changes",
    ):
        if current[field] < previous[field]:
            raise GuardError(f"snapshot.{field} cannot decrease")
    previous_audit = (
        previous["audited_late_material_findings"],
        previous["audited_post_freeze_material_head_changes"],
    )
    current_audit = (
        current["audited_late_material_findings"],
        current["audited_post_freeze_material_head_changes"],
    )
    if (
        previous_audit == current_audit
        and current["final_qualification_runs_since_audit"]
        < previous["final_qualification_runs_since_audit"]
    ):
        raise GuardError(
            "snapshot.final_qualification_runs_since_audit cannot decrease within one audit generation"
        )


def decide(
    previous: dict[str, Any] | None,
    current: dict[str, Any],
    requested_action: str,
    policy: dict[str, Any],
) -> Decision:
    """Return the bounded action verdict for the current lifecycle snapshot."""

    validate_policy(policy)
    validate_snapshot(current, policy)
    if previous is not None:
        validate_snapshot(previous, policy)
        if (
            previous["repository"] != current["repository"]
            or previous["task_id"] != current["task_id"]
        ):
            raise GuardError("previous/current snapshots must describe the same task")
        _validate_monotonic_history(previous, current)

    supported_actions = {
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
    if requested_action not in supported_actions:
        raise GuardError(f"unsupported requested action: {requested_action!r}")

    progress = progress_fingerprint(current, policy)
    failure = failure_fingerprint(current)
    budgets = policy["retry_budgets"]
    release_states = set(policy["session_release_states"])
    previous_progress = (
        progress_fingerprint(previous, policy) if previous is not None else None
    )
    same_progress = previous is not None and progress == previous_progress

    if current["state"] == "DONE" and requested_action not in {"observe", "complete"}:
        return _decision(
            allowed=False,
            state="DONE",
            reason="DONE is terminal; operational/retrigger actions are forbidden",
            release_session=True,
            progress=progress,
            failure=failure,
        )

    if current["dependency_kind"] == "external" and current["blocking_dependency"]:
        return _decision(
            allowed=requested_action == "observe",
            state="WAITING_EXTERNAL",
            reason=(
                "external dependency is pending; only observation is allowed until a material fact changes"
            ),
            release_session=True,
            progress=progress,
            failure=failure,
        )

    if previous is not None and previous["state"] in {"BLOCKED", "STALLED"} and same_progress:
        if requested_action != "complete":
            return _decision(
                allowed=requested_action == "observe",
                state=previous["state"],
                reason="released task cannot resume operational work without material progress",
                release_session=True,
                progress=progress,
                failure=failure,
            )

    if current["state"] in {"BLOCKED", "STALLED"} and requested_action not in {"observe", "complete"}:
        return _decision(
            allowed=False,
            state=current["state"],
            reason="blocked or stalled task is non-actionable until material progress is recorded",
            release_session=True,
            progress=progress,
            failure=failure,
        )

    loop_breaker_triggered = _loop_breaker_triggered(current, policy)
    loop_breaker_current = _loop_breaker_audit_current(current, policy)

    if requested_action == "run_loop_breaker_audit":
        if not loop_breaker_triggered:
            return _decision(
                allowed=False,
                state=current["state"],
                reason="LOOP_BREAKER_AUDIT is not required before a configured threshold is reached",
                release_session=current["state"] in release_states,
                progress=progress,
                failure=failure,
            )
        if current["phase"] != "LOOP_BREAKER_AUDIT":
            return _decision(
                allowed=False,
                state=current["state"],
                reason="LOOP_BREAKER_AUDIT must be entered explicitly before running the batched risk audit",
                release_session=False,
                progress=progress,
                failure=failure,
            )
        if loop_breaker_current:
            return _decision(
                allowed=False,
                state=current["state"],
                reason="LOOP_BREAKER_AUDIT is already current for the observed finding/head-change generation",
                release_session=False,
                progress=progress,
                failure=failure,
            )
        return _decision(
            allowed=True,
            state=current["state"],
            reason="LOOP_BREAKER_AUDIT may run as one bounded batched risk-ledger generation",
            release_session=False,
            progress=progress,
            failure=failure,
        )

    if (
        loop_breaker_triggered
        and not loop_breaker_current
        and requested_action in LOOP_BREAKER_FINAL_ACTIONS
    ):
        return _decision(
            allowed=False,
            state="READY" if current["state"] == "RUNNING" else current["state"],
            reason=(
                "LOOP_BREAKER_AUDIT_REQUIRED: late findings/head movement exceeded the bounded closeout threshold; "
                "complete one batched risk-ledger audit before another final qualification generation"
            ),
            release_session=False,
            progress=progress,
            failure=failure,
        )

    if requested_action == "enter_final_qualification":
        if not _ledger_terminal(current, policy):
            return _decision(
                allowed=False,
                state="READY",
                reason="final qualification requires every applicable risk class to be AUDITED_PASS or justified NOT_APPLICABLE",
                release_session=False,
                progress=progress,
                failure=failure,
            )
        if loop_breaker_triggered:
            limit = policy["loop_breaker"]["final_qualification_generations_per_audit"]
            if current["final_qualification_runs_since_audit"] >= limit:
                return _decision(
                    allowed=False,
                    state="READY",
                    reason="final qualification generation budget for the current LOOP_BREAKER_AUDIT is exhausted",
                    release_session=False,
                    progress=progress,
                    failure=failure,
                )
        return _decision(
            allowed=True,
            state="READY",
            reason="risk ledger is terminal and one final qualification generation is authorized",
            release_session=False,
            progress=progress,
            failure=failure,
        )

    if requested_action == "complete":
        if not _ledger_terminal(current, policy):
            return _decision(
                allowed=False,
                state=current["state"] if current["state"] in release_states else "READY",
                reason="DONE is forbidden until the risk ledger is terminal",
                release_session=current["state"] in release_states,
                progress=progress,
                failure=failure,
            )
        if not current["completion_verified"]:
            fallback = (
                current["state"]
                if current["state"] in release_states
                else "READY"
            )
            return _decision(
                allowed=False,
                state=fallback,
                reason="DONE is forbidden until completion is independently verified",
                release_session=fallback in release_states,
                progress=progress,
                failure=failure,
            )
        return _decision(
            allowed=True,
            state="DONE",
            reason="completion evidence and terminal risk ledger are verified",
            release_session=True,
            progress=progress,
            failure=failure,
        )

    forbidden_when_frozen = set(
        policy["candidate_freeze"]["forbidden_actions_without_material_change"]
    )
    if (
        current["candidate_frozen"]
        and requested_action in forbidden_when_frozen
        and not current["material_change"]
    ):
        if current["state"] in release_states:
            state = current["state"]
        elif current["dependency_kind"] == "external":
            state = "WAITING_EXTERNAL"
        elif current["state"] == "RUNNING":
            state = "READY"
        else:
            state = current["state"]
        return _decision(
            allowed=False,
            state=state,
            reason="candidate is frozen; mutation/retrigger without a material change is forbidden",
            release_session=state in release_states,
            progress=progress,
            failure=failure,
        )

    if requested_action == "request_external_review" and (
        current["external_review_invocations"]
        >= budgets["external_review_invocations_per_fingerprint"]
    ):
        return _decision(
            allowed=False,
            state="WAITING_EXTERNAL",
            reason="external-review invocation budget for this review generation is exhausted",
            release_session=True,
            progress=progress,
            failure=failure,
        )

    if requested_action == "same_head_gate_recheck" and (
        current["same_head_gate_rechecks"]
        >= budgets["same_head_gate_rechecks_per_evidence_generation"]
    ):
        return _decision(
            allowed=False,
            state="WAITING_EXTERNAL",
            reason="same-head gate recheck budget for this evidence generation is exhausted",
            release_session=True,
            progress=progress,
            failure=failure,
        )

    if requested_action == "run_heavy_validation" and (
        current["heavy_validation_runs"] >= budgets["heavy_validation_attempts"]
    ):
        return _decision(
            allowed=False,
            state="STALLED",
            reason="heavy-validation budget is exhausted; isolate the failure before another full run",
            release_session=True,
            progress=progress,
            failure=failure,
        )

    if (
        requested_action == "retry"
        and current["first_material_failure"]
        and current["identical_failure_cycles"] >= budgets["identical_failure_cycles"]
    ):
        return _decision(
            allowed=False,
            state="STALLED",
            reason="identical failure budget is exhausted without material progress",
            release_session=True,
            progress=progress,
            failure=failure,
        )

    return _decision(
        allowed=True,
        state=current["state"],
        reason="requested action remains within the bounded execution policy",
        release_session=current["state"] in release_states,
        progress=progress,
        failure=failure,
    )


def _load_json(path: str) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise GuardError(f"{path}: expected a JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate bounded autonomous execution state"
    )
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
