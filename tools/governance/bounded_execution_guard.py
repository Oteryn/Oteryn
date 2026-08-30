Warning: truncated output (original token count: 9156)
Total output lines: 792

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
    i…7156 tokens truncated… False, progress, failure)
        return _decision(True, "READY", "qualification admission is within the current bounded audit generation", False, progress, failure)

    if requested_action == "complete":
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
