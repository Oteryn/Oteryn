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
    budgets = policy.get("retry_budgets")
    required_budgets = {
        "identical_failure_cycles",
        "heavy_validation_attempts",
        "external_review_invocations_per_fingerprint",
        "same_head_gate_rechecks_per_evidence_generation",
    }
    if not isinstance(budgets, dict) or set(budgets) != required_budgets:
        raise GuardError("retry_budgets fields do not match the canonical policy")
    if any(
        not isinstance(budgets[key], int)
        or isinstance(budgets[key], bool)
        or budgets[key] < 1
        for key in required_budgets
    ):
        raise GuardError("all retry budgets must be positive integers")
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
        "first_material_failure",
    ):
        if not isinstance(snapshot.get(key), str):
            raise GuardError(f"snapshot.{key} must be a string")
    for key in (
        "identical_failure_cycles",
        "heavy_validation_runs",
        "external_review_invocations",
        "same_head_gate_rechecks",
    ):
        value = snapshot.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise GuardError(f"snapshot.{key} must be a non-negative integer")
    if snapshot["dependency_kind"] not in {
        "",
        "external",
        "local",
        "owner",
        "permission",
        "policy",
    }:
        raise GuardError("snapshot.dependency_kind is invalid")


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

    supported_actions = {
        "observe",
        "retry",
        "mutate",
        "retrigger",
        "complete",
        "request_external_review",
        "run_heavy_validation",
        "same_head_gate_recheck",
    }
    if requested_action not in supported_actions:
        raise GuardError(f"unsupported requested action: {requested_action!r}")

    progress = progress_fingerprint(current, policy)
    failure = failure_fingerprint(current)
    budgets = policy["retry_budgets"]
    release_states = set(policy["session_release_states"])

    if requested_action == "complete":
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
            reason="completion evidence is verified",
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
            reason="external-review invocation budget for this fingerprint is exhausted",
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

    same_progress = (
        previous is not None
        and progress == progress_fingerprint(previous, policy)
    )
    same_failure = (
        previous is not None
        and failure == failure_fingerprint(previous)
    )

    if current["dependency_kind"] == "external" and current["blocking_dependency"]:
        return _decision(
            allowed=True,
            state="WAITING_EXTERNAL",
            reason="external dependency is pending; persist state and release the worker session",
            release_session=True,
            progress=progress,
            failure=failure,
        )

    if (
        requested_action == "retry"
        and same_progress
        and same_failure
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
