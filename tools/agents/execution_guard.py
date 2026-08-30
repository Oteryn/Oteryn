#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REQUIRED = {
    "schema_version",
    "repository",
    "pr_number",
    "task_head_sha",
    "integration_main_sha",
    "candidate_frozen",
    "candidate_head_sha",
    "current_action",
    "waiting_reason",
    "failure_code",
    "previous_progress_fingerprint",
    "identical_cycle_count",
    "retry_count",
    "retry_limit",
    "external_event_can_change",
    "material_repository_change",
    "terminal_verified",
    "blocked",
    "noop_retrigger_intent",
}


def _validate(snapshot: dict[str, Any]) -> None:
    if set(snapshot) != REQUIRED:
        missing = sorted(REQUIRED - set(snapshot))
        extra = sorted(set(snapshot) - REQUIRED)
        raise ValueError(f"snapshot fields mismatch: missing={missing} extra={extra}")
    if snapshot["schema_version"] != 1:
        raise ValueError("unsupported schema_version")
    if not isinstance(snapshot["repository"], str) or snapshot["repository"].count("/") != 1:
        raise ValueError("repository must use owner/name")
    if not isinstance(snapshot["pr_number"], int) or snapshot["pr_number"] < 1:
        raise ValueError("pr_number must be positive")
    task_head = snapshot["task_head_sha"]
    if not isinstance(task_head, str) or not SHA_RE.fullmatch(task_head):
        raise ValueError("task_head_sha must be a 40-hex SHA")
    for key in ("integration_main_sha", "candidate_head_sha"):
        value = snapshot[key]
        if not isinstance(value, str) or (value and not SHA_RE.fullmatch(value)):
            raise ValueError(f"{key} must be empty or a 40-hex SHA")
    for key in ("candidate_frozen", "external_event_can_change", "material_repository_change", "terminal_verified", "blocked", "noop_retrigger_intent"):
        if not isinstance(snapshot[key], bool):
            raise ValueError(f"{key} must be boolean")
    for key in ("identical_cycle_count", "retry_count", "retry_limit"):
        if not isinstance(snapshot[key], int) or snapshot[key] < 0:
            raise ValueError(f"{key} must be a non-negative integer")
    for key in ("current_action", "waiting_reason", "failure_code", "previous_progress_fingerprint"):
        if not isinstance(snapshot[key], str):
            raise ValueError(f"{key} must be a string")
    if snapshot["candidate_frozen"] and snapshot["candidate_head_sha"] != task_head:
        raise ValueError("frozen candidate head must equal task head")
    if snapshot["current_action"] == "integrate_main" and not SHA_RE.fullmatch(snapshot["integration_main_sha"]):
        raise ValueError("integration_main_sha must be set for integrate_main")


def _fingerprint(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def evaluate_snapshot(snapshot: dict[str, Any]) -> dict[str, str]:
    _validate(snapshot)
    progress_payload = {
        "repository": snapshot["repository"],
        "pr_number": snapshot["pr_number"],
        "task_head_sha": snapshot["task_head_sha"],
        "integration_main_sha": snapshot["integration_main_sha"],
        "current_action": snapshot["current_action"],
        "waiting_reason": snapshot["waiting_reason"],
        "failure_code": snapshot["failure_code"],
    }
    failure_payload = {
        "repository": snapshot["repository"],
        "pr_number": snapshot["pr_number"],
        "task_head_sha": snapshot["task_head_sha"],
        "integration_main_sha": snapshot["integration_main_sha"],
        "current_action": snapshot["current_action"],
        "failure_code": snapshot["failure_code"],
        "waiting_reason": snapshot["waiting_reason"],
    }
    progress = _fingerprint(progress_payload)
    failure = _fingerprint(failure_payload) if snapshot["failure_code"] else ""

    if snapshot["blocked"] or snapshot["noop_retrigger_intent"]:
        reason = "no-op/retrigger mutation is prohibited" if snapshot["noop_retrigger_intent"] else "task is explicitly blocked"
        decision, state = "BLOCK", "BLOCKED"
    elif snapshot["terminal_verified"]:
        decision, state, reason = "DONE", "DONE", "terminal completion is verified"
    elif snapshot["material_repository_change"]:
        decision, state, reason = "CONTINUE", "RUNNING", "material repository change starts a new execution generation"
    elif snapshot["external_event_can_change"] and snapshot["waiting_reason"]:
        decision, state, reason = "WAIT", "WAITING_EXTERNAL", f"external event pending: {snapshot['waiting_reason']}"
    elif (
        snapshot["previous_progress_fingerprint"] == progress
        and snapshot["identical_cycle_count"] >= 2
        and snapshot["retry_count"] >= snapshot["retry_limit"]
    ):
        decision, state, reason = "STALL", "STALLED", "identical material state exceeded bounded retry budget"
    elif (
        snapshot["failure_code"]
        and snapshot["retry_count"] >= snapshot["retry_limit"]
        and snapshot["retry_limit"] == 0
    ):
        decision, state, reason = "STALL", "STALLED", "no retry is permitted for this failure"
    else:
        decision, state, reason = "CONTINUE", "RUNNING", "bounded execution may continue"

    return {
        "decision": decision,
        "next_state": state,
        "progress_fingerprint": progress,
        "failure_fingerprint": failure,
        "reason": reason,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate bounded autonomous execution state")
    parser.add_argument("--input", type=Path, default=None)
    args = parser.parse_args(argv)
    try:
        raw = args.input.read_text(encoding="utf-8") if args.input else sys.stdin.read()
        snapshot = json.loads(raw)
        if not isinstance(snapshot, dict):
            raise ValueError("snapshot must be a JSON object")
        result = evaluate_snapshot(snapshot)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
