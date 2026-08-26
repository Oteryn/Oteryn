#!/usr/bin/env python3
"""Deterministically validate Oteryn agent execution-routing packets.

The caller supplies both policy and current GitHub facts. This module makes
no network, host, Remote Desktop, service, or tool calls.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_policy(path: Path) -> dict[str, object]:
    """Load a JSON policy object without consulting external state."""
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("policy must be a JSON object")
    return loaded


def _mapping(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _closed_values(policy: dict[str, object], key: str) -> set[str]:
    return {value for value in _list(policy.get(key)) if isinstance(value, str)}


def _path_prefix(path: str) -> str:
    normalized = path.replace("\\", "/").strip("/")
    wildcard = normalized.find("*")
    if wildcard >= 0:
        normalized = normalized[:wildcard].rstrip("/")
    return normalized


def _paths_overlap(left: str, right: str) -> bool:
    left_prefix = _path_prefix(left)
    right_prefix = _path_prefix(right)
    if not left_prefix or not right_prefix:
        return left == right
    return (
        left_prefix == right_prefix
        or left_prefix.startswith(right_prefix + "/")
        or right_prefix.startswith(left_prefix + "/")
    )


def _lease_resources(lane: dict[str, object]) -> set[str]:
    resources: set[str] = set()
    for lease in _list(lane.get("shared_leases")):
        if isinstance(lease, str) and lease:
            resources.add(lease)
        elif isinstance(lease, dict):
            resource = lease.get("resource")
            holder = lease.get("holder")
            release_condition = lease.get("release_condition")
            if (
                isinstance(resource, str)
                and resource
                and isinstance(holder, str)
                and holder
                and isinstance(release_condition, str)
                and release_condition
            ):
                resources.add(resource)
    return resources


def _validate_preflight(
    execution: dict[str, object], live_state: dict[str, object], policy: dict[str, object], errors: list[str]
) -> None:
    preflight = execution.get("github_preflight")
    if not isinstance(preflight, dict) or not preflight:
        errors.append("github_preflight is required")
        return
    for field in sorted(_closed_values(policy, "resume_preflight_required_fields")):
        if field not in preflight:
            errors.append(f"github_preflight missing required field: {field}")
    verified_at = preflight.get("verified_at")
    if "verified_at" in preflight and (not isinstance(verified_at, str) or not verified_at.strip()):
        errors.append("github_preflight.verified_at must be a timestamp string")
    for field, expected in live_state.items():
        if field not in preflight:
            continue
        if preflight[field] != expected:
            errors.append(f"github_preflight.{field} does not match live_state")


def _validate_lanes(parallel: dict[str, object], policy: dict[str, object], errors: list[str]) -> None:
    rules = _mapping(policy.get("parallel_lane_rules"))
    strategies = {value for value in _list(rules.get("strategies")) if isinstance(value, str)}
    strategy = parallel.get("lane_strategy")
    lanes_value = parallel.get("lanes")
    lanes = [lane for lane in _list(lanes_value) if isinstance(lane, dict)]
    if not isinstance(lanes_value, list):
        errors.append("parallel_execution.lanes must be a list")
    if len(lanes) != len(_list(lanes_value)):
        errors.append("parallel_execution.lanes must contain objects")
    if strategy not in strategies:
        if len(lanes) > 1:
            errors.append("multi-lane task requires lane_strategy")
        else:
            errors.append("lane_strategy is not allowed")
    if strategy == "serial_with_reason":
        serial_reason = parallel.get("serial_reason")
        if not isinstance(serial_reason, str) or not serial_reason.strip():
            errors.append("serial_with_reason requires serial_reason")

    required_lane_fields = {value for value in _list(rules.get("required_lane_fields")) if isinstance(value, str)}
    lane_ids: set[str] = set()
    lane_paths: list[tuple[str, list[str], set[str]]] = []
    for lane in lanes:
        identifier = lane.get("id")
        display_identifier = identifier if isinstance(identifier, str) and identifier else "<unnamed>"
        if not isinstance(identifier, str) or not identifier:
            errors.append("lane id is required")
        elif identifier in lane_ids:
            errors.append(f"duplicate lane id: {identifier}")
        else:
            lane_ids.add(identifier)
        for field in required_lane_fields:
            if field not in lane:
                errors.append(f"lane '{display_identifier}' missing required field: {field}")
        owned_paths = [path for path in _list(lane.get("owned_paths")) if isinstance(path, str) and path]
        if not owned_paths:
            errors.append(f"lane '{display_identifier}' requires owned_paths")
        if not isinstance(lane.get("depends_on", []), list):
            errors.append(f"lane '{display_identifier}' depends_on must be a list")
        branch_and_worktree = lane.get("branch_and_worktree")
        if not isinstance(branch_and_worktree, str) or not branch_and_worktree.strip():
            errors.append(f"lane '{display_identifier}' requires branch_and_worktree")
        if not isinstance(lane.get("shared_leases", []), list):
            errors.append(f"lane '{display_identifier}' shared_leases must be a list")
        lane_paths.append((display_identifier, owned_paths, _lease_resources(lane)))

    for lane in lanes:
        identifier = lane.get("id") if isinstance(lane.get("id"), str) else "<unnamed>"
        for dependency in _list(lane.get("depends_on")):
            if not isinstance(dependency, str) or dependency not in lane_ids:
                errors.append(f"lane '{identifier}' depends_on unknown lane '{dependency}'")
            elif dependency == identifier:
                errors.append(f"lane '{identifier}' cannot depend_on itself")

    for index, (left_id, left_paths, left_leases) in enumerate(lane_paths):
        for right_id, right_paths, right_leases in lane_paths[index + 1 :]:
            overlapping_paths = any(
                _paths_overlap(left_path, right_path)
                for left_path in left_paths
                for right_path in right_paths
            )
            if overlapping_paths and not (left_leases & right_leases):
                errors.append("parallel lanes have overlapping owned_paths")

    constrained_resources = [
        resource
        for resource in _list(parallel.get("constrained_resources"))
        if isinstance(resource, str) and resource
    ]
    leased_resources = set().union(*(leases for _, _, leases in lane_paths)) if lane_paths else set()
    for resource in constrained_resources:
        if resource not in leased_resources:
            errors.append(f"constrained resource requires a lease: {resource}")

    integration_order = parallel.get("integration_order")
    valid_order = (
        isinstance(integration_order, list)
        and all(isinstance(identifier, str) for identifier in integration_order)
        and set(integration_order) == lane_ids
        and len(integration_order) == len(lane_ids)
    )
    if not valid_order:
        errors.append("integration_order must list every lane exactly once")


def validate_packet(
    packet: dict[str, object], *, live_state: dict[str, object], policy: dict[str, object]
) -> list[str]:
    """Return deterministic errors for a packet; an empty list means valid."""
    errors: list[str] = []
    execution = packet.get("execution_routing")
    if not isinstance(execution, dict):
        return ["execution_routing is required"]

    target = execution.get("execution_target")
    if target not in _closed_values(policy, "execution_targets"):
        errors.append("execution_target is not allowed")
    runner_class = execution.get("runner_class")
    if runner_class not in _closed_values(policy, "runner_classes"):
        errors.append("runner_class is not allowed")
    remote_desktop = execution.get("remote_desktop")
    if remote_desktop not in {"denied", "exception"}:
        errors.append("remote_desktop must be denied or exception")
    if target == "host_exception" and remote_desktop != "exception":
        errors.append("host_exception requires remote_desktop=exception")
    if remote_desktop == "exception" and target != "host_exception":
        errors.append("remote_desktop exception requires execution_target=host_exception")
    if remote_desktop == "exception":
        reason = execution.get("remote_desktop_reason")
        allowed_reasons = _closed_values(policy, "remote_desktop_reasons")
        if not isinstance(reason, str) or not reason:
            errors.append("remote_desktop exception requires a closed reason")
        elif reason not in allowed_reasons:
            errors.append("remote_desktop_reason is not an allowed exception")
    elif execution.get("remote_desktop_reason") not in {None, "not_applicable"}:
        errors.append("remote_desktop_reason requires remote_desktop=exception")

    equivalent_ci = execution.get("equivalent_ci")
    forbidden_actions = _closed_values(policy, "forbidden_remote_desktop_actions_when_equivalent_ci")
    requested_actions = _list(execution.get("requested_host_actions"))
    if equivalent_ci and any(action in forbidden_actions for action in requested_actions):
        errors.append("equivalent_ci prohibits RDC polling")
    if equivalent_ci and remote_desktop == "exception":
        errors.append("remote_desktop exception requires no equivalent_ci")

    _validate_preflight(execution, _mapping(live_state), policy, errors)
    parallel = packet.get("parallel_execution")
    if not isinstance(parallel, dict):
        errors.append("parallel_execution is required")
    else:
        _validate_lanes(parallel, policy, errors)
    return errors


def _load_json_object(path: Path, label: str) -> dict[str, object]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"{label} must be a JSON object")
    return loaded


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--live-state", type=Path, required=True)
    arguments = parser.parse_args(argv)
    try:
        policy = load_policy(arguments.policy)
        packet = _load_json_object(arguments.packet, "packet")
        live_state = _load_json_object(arguments.live_state, "live-state")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    errors = validate_packet(packet, live_state=live_state, policy=policy)
    if errors:
        print("\n".join(errors))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
