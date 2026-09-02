#!/usr/bin/env python3
"""Deterministic guard for Oteryn's minimum bounded-execution contract.

This module decides coordination policy only and has no external-service authority.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping


CANONICAL_POLICY_KEYS = {
    "schema_version", "policy_id", "lifecycle_authority", "states",
    "progress_fingerprint_fields", "retry_budgets", "candidate_freeze",
    "dependency_semantics", "session_release_states",
}
CANONICAL_STATES = ["RUNNING", "WAITING_EXTERNAL", "BLOCKED", "STALLED", "READY", "DONE"]
CANONICAL_FIELDS = [
    "repository", "task_id", "task_head_sha", "phase", "blocking_dependency",
    "dependency_kind", "gate_state", "first_material_failure",
]
REQUIRED_SNAPSHOT_FIELDS = set(CANONICAL_FIELDS) | {
    "state", "candidate_frozen", "material_reason", "identical_failure_cycles",
    "heavy_validation_attempts", "completion_verified",
}
ALLOWED_OBSERVER_FIELDS = {"narration", "updated_at"}
ACTIONS = {"observe", "mutate", "retrigger", "retry", "run_heavy_validation", "complete"}
STABLE_TASK_IDENTITY_FIELDS = ("repository", "task_id")


class GuardError(ValueError):
    """Raised when policy or snapshot input is malformed or contradictory."""


@dataclass(frozen=True)
class Decision:
    allowed: bool
    state: str
    reason: str
    release_session: bool
    progress_fingerprint: str
    failure_fingerprint: str
    snapshot: dict[str, Any]


def _digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_policy(policy: Mapping[str, Any]) -> None:
    if set(policy) != CANONICAL_POLICY_KEYS:
        raise GuardError("policy must use the closed narrow schema")
    if policy.get("schema_version") != 1 or policy.get("states") != CANONICAL_STATES:
        raise GuardError("policy has noncanonical version or lifecycle states")
    if policy.get("progress_fingerprint_fields") != CANONICAL_FIELDS:
        raise GuardError("progress fingerprint fields must equal the canonical material set")
    budgets = policy.get("retry_budgets")
    if not isinstance(budgets, dict) or set(budgets) != {"identical_failure_cycles", "heavy_validation_attempts"}:
        raise GuardError("policy must define only the two local retry budgets")
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in budgets.values()):
        raise GuardError("retry budgets must be non-negative integers")
    freeze = policy.get("candidate_freeze")
    if not isinstance(freeze, dict) or freeze.get("forbidden_unchanged_actions") != ["mutate", "retrigger"]:
        raise GuardError("candidate freeze must forbid unchanged mutate and retrigger")
    if not isinstance(freeze.get("material_reasons"), list) or not freeze["material_reasons"]:
        raise GuardError("candidate freeze must define material reasons")
    expected_dependencies = {
        "external": "WAITING_EXTERNAL", "owner": "BLOCKED",
        "permission": "BLOCKED", "policy": "BLOCKED",
    }
    if policy.get("dependency_semantics") != expected_dependencies:
        raise GuardError("dependency semantics must retain the canonical mappings")
    if policy.get("session_release_states") != ["WAITING_EXTERNAL", "BLOCKED", "STALLED", "DONE"]:
        raise GuardError("session release states must be canonical")


def validate_snapshot(snapshot: Mapping[str, Any], policy: Mapping[str, Any]) -> None:
    validate_policy(policy)
    missing = REQUIRED_SNAPSHOT_FIELDS - set(snapshot)
    unknown = set(snapshot) - REQUIRED_SNAPSHOT_FIELDS - ALLOWED_OBSERVER_FIELDS
    if missing or unknown:
        raise GuardError(f"snapshot fields invalid; missing={sorted(missing)}, unknown={sorted(unknown)}")
    if snapshot["state"] not in policy["states"]:
        raise GuardError("snapshot state is not canonical")
    for key in ("candidate_frozen", "completion_verified"):
        if not isinstance(snapshot[key], bool):
            raise GuardError(f"{key} must be boolean")
    for key in ("identical_failure_cycles", "heavy_validation_attempts"):
        if isinstance(snapshot[key], bool) or not isinstance(snapshot[key], int) or snapshot[key] < 0:
            raise GuardError(f"{key} must be a non-negative integer")
    for key in CANONICAL_FIELDS + ["material_reason"]:
        if not isinstance(snapshot[key], str):
            raise GuardError(f"{key} must be a string")
    allowed_dependency_kinds = {"none", *policy["dependency_semantics"]}
    if snapshot["dependency_kind"] not in allowed_dependency_kinds:
        raise GuardError("dependency_kind is not canonical")
    if snapshot["blocking_dependency"] and snapshot["dependency_kind"] == "none":
        raise GuardError("blocking_dependency requires a canonical blocking dependency_kind")
    if snapshot["state"] == "DONE" and not snapshot["completion_verified"]:
        raise GuardError("DONE requires caller-provided completion verification")


def progress_fingerprint(snapshot: Mapping[str, Any], policy: Mapping[str, Any]) -> str:
    validate_snapshot(snapshot, policy)
    return _digest({field: snapshot[field] for field in policy["progress_fingerprint_fields"]})


def failure_fingerprint(snapshot: Mapping[str, Any]) -> str:
    return _digest({
        "repository": snapshot.get("repository", ""),
        "task_id": snapshot.get("task_id", ""),
        "task_head_sha": snapshot.get("task_head_sha", ""),
        "phase": snapshot.get("phase", ""),
        "blocking_dependency": snapshot.get("blocking_dependency", ""),
        "dependency_kind": snapshot.get("dependency_kind", ""),
        "gate_state": snapshot.get("gate_state", ""),
        "first_material_failure": snapshot.get("first_material_failure", ""),
    })


def _validate_predecessor_history(current: Mapping[str, Any], previous: Mapping[str, Any]) -> None:
    for field in STABLE_TASK_IDENTITY_FIELDS:
        if current[field] != previous[field]:
            raise GuardError(f"previous snapshot {field} does not match current task identity")

    if (
        failure_fingerprint(current) == failure_fingerprint(previous)
        and current["identical_failure_cycles"] < previous["identical_failure_cycles"]
    ):
        raise GuardError("identical_failure_cycles cannot regress within one failure scope")

    if (
        current["task_head_sha"] == previous["task_head_sha"]
        and current["heavy_validation_attempts"] < previous["heavy_validation_attempts"]
    ):
        raise GuardError("heavy_validation_attempts cannot regress on the same technical head")


def _effective_current(current: Mapping[str, Any], previous: Mapping[str, Any] | None) -> dict[str, Any]:
    result = copy.deepcopy(dict(current))
    if (
        previous is not None
        and previous["candidate_frozen"]
        and current["task_head_sha"] == previous["task_head_sha"]
    ):
        result["candidate_frozen"] = True
    return result


def _decision(policy: Mapping[str, Any], current: Mapping[str, Any], allowed: bool,
              state: str, reason: str, snapshot: dict[str, Any] | None = None) -> Decision:
    result = copy.deepcopy(snapshot if snapshot is not None else dict(current))
    result["state"] = state
    if state == "DONE":
        result["completion_verified"] = True
    return Decision(
        allowed, state, reason, state in policy["session_release_states"],
        progress_fingerprint(result, policy), failure_fingerprint(result), result,
    )


def decide(policy: Mapping[str, Any], current: Mapping[str, Any], action: str,
           *, previous: Mapping[str, Any] | None = None) -> Decision:
    validate_snapshot(current, policy)
    if previous is not None:
        validate_snapshot(previous, policy)
        _validate_predecessor_history(current, previous)
    if action not in ACTIONS:
        raise GuardError(f"unsupported action: {action}")

    effective = _effective_current(current, previous)

    if previous is not None and previous["state"] == "DONE":
        return _decision(policy, previous, action == "observe", "DONE", "DONE is terminal")
    if effective["state"] == "DONE":
        return _decision(policy, effective, action == "observe", "DONE", "DONE is terminal")

    dependency_state = policy["dependency_semantics"].get(effective["dependency_kind"])
    if effective["blocking_dependency"] and dependency_state:
        return _decision(policy, effective, action == "observe", dependency_state,
                         "dependency prevents operational work")

    changed = previous is None or progress_fingerprint(effective, policy) != progress_fingerprint(previous, policy)
    if previous is not None and previous["state"] in {"WAITING_EXTERNAL", "BLOCKED", "STALLED"} and not changed:
        if action == "observe":
            return _decision(policy, previous, True, previous["state"], "observation allowed while released")
        return _decision(policy, previous, False, previous["state"], "material progress required to resume")

    if action == "observe":
        return _decision(policy, effective, True, effective["state"], "observation allowed")

    if previous is None:
        return _decision(policy, effective, False, effective["state"],
                         "previous snapshot required for operational action")

    if action in {"mutate", "retrigger"} and not changed:
        return _decision(policy, effective, False, effective["state"],
                         "unchanged candidates cannot be mutated or retriggered")

    if effective["candidate_frozen"] and action in policy["candidate_freeze"]["forbidden_unchanged_actions"]:
        valid_reason = effective["material_reason"] in policy["candidate_freeze"]["material_reasons"]
        if not changed or not valid_reason:
            return _decision(policy, effective, False, effective["state"],
                             "frozen candidate requires a recorded material reason and change")

    if action == "retry":
        if not effective["first_material_failure"]:
            return _decision(policy, effective, False, effective["state"], "retry requires a material failure")
        limit = policy["retry_budgets"]["identical_failure_cycles"]
        if effective["identical_failure_cycles"] >= limit:
            return _decision(policy, effective, False, "STALLED", "identical failure retry budget exhausted")
        result = copy.deepcopy(effective)
        result["identical_failure_cycles"] += 1
        return _decision(policy, effective, True, "RUNNING", "bounded retry admitted", result)

    if action == "run_heavy_validation":
        limit = policy["retry_budgets"]["heavy_validation_attempts"]
        if effective["heavy_validation_attempts"] >= limit:
            return _decision(policy, effective, False, "STALLED", "heavy validation budget exhausted")
        result = copy.deepcopy(effective)
        result["heavy_validation_attempts"] += 1
        return _decision(policy, effective, True, effective["state"], "bounded heavy validation admitted", result)

    if action == "complete":
        if not effective["completion_verified"]:
            return _decision(policy, effective, False, effective["state"], "completion verification required")
        return _decision(policy, effective, True, "DONE", "completion fact accepted")

    return _decision(policy, effective, True, "RUNNING", "operational action admitted")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--action", required=True)
    args = parser.parse_args()
    policy = json.loads(args.policy.read_text(encoding="utf-8"))
    current = json.loads(args.snapshot.read_text(encoding="utf-8"))
    previous = json.loads(args.previous.read_text(encoding="utf-8")) if args.previous else None
    print(json.dumps(asdict(decide(policy, current, args.action, previous=previous)), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
