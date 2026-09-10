#!/usr/bin/env python3
"""Deterministic protected-integration capability routing.

This module does not grant merge authority. It classifies whether the current
execution surface can carry an already-authorized protected integration either
directly through native merge-async or through the bounded META executor.
"""

from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Mapping

NOT_REQUIRED = "NOT_REQUIRED"
DIRECT_CAPABLE = "DIRECT_CAPABLE"
DELEGATED_CAPABLE = "DELEGATED_CAPABLE"
BLOCKED_CAPABILITY_UNAVAILABLE = "BLOCKED_CAPABILITY_UNAVAILABLE"

SNAPSHOT_SOURCE = "verified_current_execution_capabilities"
EXECUTOR_READBACK_SOURCE = "live_protected_meta_executor_readback"
CANARY_SOURCE = "retained_terminal_executor_canary"
DEFAULT_MAX_AGE_SECONDS = 300


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
    maximum_age = cfg.get("snapshot_max_age_seconds")
    if not isinstance(maximum_age, int) or isinstance(maximum_age, bool) or maximum_age <= 0:
        errors.append("integration_capability_routing.snapshot_max_age_seconds must be positive")
    executor = cfg.get("protected_executor")
    if not isinstance(executor, dict) or executor != {
        "repository": "Oteryn/Oteryn",
        "ref": "refs/heads/main",
        "workflow_path": ".github/workflows/governed-merge-queue-executor.yml",
        "workflow_blob_sha": executor.get("workflow_blob_sha") if isinstance(executor, dict) else None,
    } or not isinstance(executor.get("workflow_blob_sha"), str) or len(executor["workflow_blob_sha"]) != 40:
        errors.append("integration_capability_routing.protected_executor must bind protected META workflow identity")
    targets = cfg.get("allowed_target_repositories")
    if not isinstance(targets, dict) or not targets:
        errors.append("integration_capability_routing.allowed_target_repositories must be a non-empty object")
    else:
        expected_targets = {
            "Oteryn/Oteryn": {"gate": "meta-gate", "source_workflows": [{"path": ".github/workflows/ci.yml", "event": "pull_request", "workflow_id": 336924336}]},
            "Oteryn/Oteryn-Game": {"gate": "game-gate", "source_workflows": [{"path": ".github/workflows/merge-gate.yml", "event": "pull_request", "workflow_id": 336912904}]},
            "Oteryn/Oteryn-Platform": {"gate": "platform-gate", "source_workflows": [{"path": ".github/workflows/ci.yml", "event": "pull_request", "workflow_id": 315878887}]},
            "Oteryn/Oteryn-Atlas": {"gate": None, "source_workflows": [
                {"path": ".github/workflows/merge-authority-audit.yml", "event": "pull_request_target", "workflow_id": 351151514},
                {"path": ".github/workflows/verification-shadow.yml", "event": "pull_request_target", "workflow_id": 353763418},
            ]},
        }
        if targets != expected_targets:
            errors.append("integration capability target workflow identities must match canonical repositories")
    return errors


def _fresh(observed: object, now: object, maximum_age: int) -> bool:
    return (
        isinstance(observed, int) and not isinstance(observed, bool)
        and isinstance(now, int) and not isinstance(now, bool)
        and 0 <= observed <= now and now - observed <= maximum_age
    )


def _delegated_executor_is_operational(
    snapshot: Mapping[str, object], cfg: Mapping[str, object], *, now_epoch_seconds: int
) -> bool:
    expected = _mapping(cfg.get("protected_executor"))
    readback = _mapping(snapshot.get("protected_meta_executor_readback"))
    canary = _mapping(readback.get("retained_canary_evidence"))
    return (
        readback.get("source") == EXECUTOR_READBACK_SOURCE
        and readback.get("repository") == expected.get("repository")
        and readback.get("ref") == expected.get("ref")
        and readback.get("workflow_path") == expected.get("workflow_path")
        and readback.get("workflow_blob_sha") == expected.get("workflow_blob_sha")
        and readback.get("credential_operational") is True
        and _fresh(readback.get("observed_at_epoch_seconds"), now_epoch_seconds, int(cfg["snapshot_max_age_seconds"]))
        and canary.get("source") == CANARY_SOURCE
        and canary.get("repository") == expected.get("repository")
        and canary.get("workflow_blob_sha") == expected.get("workflow_blob_sha")
        and canary.get("terminal_proof_retained") is True
    )


def classify(
    snapshot: Mapping[str, object], policy: Mapping[str, object], *, now_epoch_seconds: int | None = None
) -> str:
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

    now = int(time.time()) if now_epoch_seconds is None else now_epoch_seconds
    maximum_age = int(integration_policy(policy).get("snapshot_max_age_seconds", DEFAULT_MAX_AGE_SECONDS))
    if not _fresh(snapshot.get("observed_at_epoch_seconds"), now, maximum_age):
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
    if (
        request in available
        and delegated in routes
        and _delegated_executor_is_operational(snapshot, cfg, now_epoch_seconds=now)
    ):
        return DELEGATED_CAPABLE
    return BLOCKED_CAPABILITY_UNAVAILABLE


def validate_worker_release(
    snapshot: Mapping[str, object], policy: Mapping[str, object], *, now_epoch_seconds: int | None = None
) -> list[str]:
    state = classify(snapshot, policy, now_epoch_seconds=now_epoch_seconds)
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
