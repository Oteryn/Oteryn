#!/usr/bin/env python3
"""Deterministic protected-integration capability routing.

This module does not grant merge authority. It classifies whether the current
execution surface can carry an already-authorized protected integration either
directly through native merge-async or through the bounded META executor.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

NOT_REQUIRED = "NOT_REQUIRED"
DIRECT_CAPABLE = "DIRECT_CAPABLE"
DELEGATED_CAPABLE = "DELEGATED_CAPABLE"
BLOCKED_CAPABILITY_UNAVAILABLE = "BLOCKED_CAPABILITY_UNAVAILABLE"

SNAPSHOT_SOURCE = "verified_current_execution_capabilities"


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, dict) else {}


def _unique_strings(value: object) -> tuple[str, ...] | None:
    if not isinstance(value, list):
        return None
    if not all(isinstance(item, str) and item.strip() and item == item.strip() for item in value):
        return None
    items = tuple(value)
    return items if len(set(items)) == len(items) else None


def integration_policy(policy: Mapping[str, object]) -> Mapping[str, object]:
    return _mapping(policy.get("integration_capability_routing"))


def validate_policy(policy: Mapping[str, object]) -> list[str]:
    cfg = integration_policy(policy)
    errors: list[str] = []
    if cfg.get("schema_version") != 1:
        errors.append("integration_capability_routing.schema_version must be 1")
    if cfg.get("require_preflight_before_worker_release") is not True:
        errors.append("integration capability preflight must be required before worker release")
    states = _unique_strings(cfg.get("states"))
    expected_states = (
        NOT_REQUIRED,
        DIRECT_CAPABLE,
        DELEGATED_CAPABLE,
        BLOCKED_CAPABILITY_UNAVAILABLE,
    )
    if states != expected_states:
        errors.append("integration capability states must be the canonical ordered set")
    for key in ("direct_operation", "delegated_route", "delegated_request_operation", "control_repository"):
        value = cfg.get(key)
        if not isinstance(value, str) or not value.strip() or value != value.strip():
            errors.append(f"integration_capability_routing.{key} must be a non-empty string")
    issue = cfg.get("control_issue")
    if not isinstance(issue, int) or isinstance(issue, bool) or issue <= 0:
        errors.append("integration_capability_routing.control_issue must be a positive integer")
    targets = cfg.get("allowed_target_repositories")
    if not isinstance(targets, dict) or not targets:
        errors.append("integration_capability_routing.allowed_target_repositories must be a non-empty object")
    else:
        expected = {
            "Oteryn/Oteryn": "meta-gate",
            "Oteryn/Oteryn-Game": "game-gate",
            "Oteryn/Oteryn-Platform": "platform-gate",
            "Oteryn/Oteryn-Atlas": "atlas-gate",
        }
        if targets != expected:
            errors.append("integration capability target repository/gate map must match permanent repositories")
    return errors


def classify(snapshot: Mapping[str, object], policy: Mapping[str, object]) -> str:
    errors = validate_policy(policy)
    if errors:
        raise ValueError("; ".join(errors))

    required = snapshot.get("requires_autonomous_protected_integration")
    if not isinstance(required, bool):
        raise ValueError("requires_autonomous_protected_integration must be boolean")
    if not required:
        return NOT_REQUIRED

    if snapshot.get("source") != SNAPSHOT_SOURCE:
        return BLOCKED_CAPABILITY_UNAVAILABLE

    available = _unique_strings(snapshot.get("available_operations"))
    routes = _unique_strings(snapshot.get("operational_executor_routes"))
    if available is None or routes is None:
        return BLOCKED_CAPABILITY_UNAVAILABLE

    cfg = integration_policy(policy)
    direct = cfg["direct_operation"]
    delegated = cfg["delegated_route"]
    request = cfg["delegated_request_operation"]

    if direct in available:
        return DIRECT_CAPABLE
    if request in available and delegated in routes:
        return DELEGATED_CAPABLE
    return BLOCKED_CAPABILITY_UNAVAILABLE


def validate_worker_release(snapshot: Mapping[str, object], policy: Mapping[str, object]) -> list[str]:
    state = classify(snapshot, policy)
    if state == BLOCKED_CAPABILITY_UNAVAILABLE:
        return [
            "protected integration capability unavailable before worker release: "
            "neither direct native merge-async nor the verified bounded META executor is callable"
        ]
    return []


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    args = parser.parse_args()
    try:
        state = classify(load_json(args.snapshot), load_json(args.policy))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "INVALID", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps({"status": state}, sort_keys=True))
    return 0 if state != BLOCKED_CAPABILITY_UNAVAILABLE else 2


if __name__ == "__main__":
    raise SystemExit(main())
