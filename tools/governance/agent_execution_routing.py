#!/usr/bin/env python3
"""Deterministically validate Oteryn agent execution-routing packets.

The caller supplies both policy and current GitHub facts. This module makes
no network, host, Remote Desktop, service, or tool calls.
"""
from __future__ import annotations

import argparse
from collections import deque
import json
from pathlib import Path
import re


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


def _is_closed_value(value: object, allowed_values: set[str]) -> bool:
    """Return whether a JSON string belongs to a policy's closed values."""
    return isinstance(value, str) and value in allowed_values


def _path_prefix(path: str) -> str:
    normalized = path.replace("\\", "/").strip("/")
    wildcard = normalized.find("*")
    if wildcard >= 0:
        normalized = normalized[:wildcard].rstrip("/")
    return normalized


def _is_safe_repository_relative_path(path: object) -> bool:
    """Return whether a path glob stays safely within the repository root."""
    if not isinstance(path, str) or not path.strip():
        return False
    normalized = path.strip()
    if (
        normalized.startswith("/")
        or "\\" in normalized
        or ":" in normalized
        or any(ord(character) < 32 for character in normalized)
    ):
        return False
    return all(part not in {"", ".", ".."} for part in normalized.split("/"))


_LITERAL_PATH_SEGMENT = re.compile(r"^[\w .-]+$", re.UNICODE)


def _is_supported_path_glob(path: object) -> bool:
    """Return whether a path uses literal segments and only ``*`` wildcards.

    A wildcard run may contain one or two stars; all other characters must be
    ordinary repository path characters. This deliberately excludes brace,
    extglob, character-class, and shell-expansion syntax.
    """
    if not isinstance(path, str) or "\\" in path:
        return False
    for segment in path.split("/"):
        if not segment:
            return False
        literal_parts = re.split(r"\*{1,2}", segment)
        if any("*" in part for part in literal_parts):
            return False
        if any(part and not _LITERAL_PATH_SEGMENT.fullmatch(part) for part in literal_parts):
            return False
    return True


def _paths_overlap(left: str, right: str) -> bool:
    left_prefix = _path_prefix(left)
    right_prefix = _path_prefix(right)
    if not left_prefix or not right_prefix:
        return bool(left_prefix == right_prefix or "*" in left or "*" in right)
    return (
        left_prefix == right_prefix
        or left_prefix.startswith(right_prefix + "/")
        or right_prefix.startswith(left_prefix + "/")
    )


def _validate_preflight(
    execution: dict[str, object], live_state: dict[str, object], policy: dict[str, object], errors: list[str]
) -> None:
    preflight = execution.get("github_preflight")
    if not isinstance(preflight, dict) or not preflight:
        errors.append("github_preflight is required")
        return
    required_fields = sorted(_closed_values(policy, "resume_preflight_required_fields"))
    for field in required_fields:
        if field not in preflight:
            errors.append(f"github_preflight missing required field: {field}")
        if field not in live_state:
            errors.append(f"live_state missing required field: {field}")
    verified_at = preflight.get("verified_at")
    if "verified_at" in preflight and (not isinstance(verified_at, str) or not verified_at.strip()):
        errors.append("github_preflight.verified_at must be a timestamp string")
    for field in required_fields:
        if field in preflight and field in live_state and preflight[field] != live_state[field]:
            errors.append(f"github_preflight.{field} does not match live_state")


def _has_dependency_cycle(lanes: list[dict[str, object]], lane_ids: set[str]) -> bool:
    dependencies = {
        identifier: {
            dependency
            for dependency in _list(lane.get("depends_on"))
            if isinstance(dependency, str) and dependency in lane_ids
        }
        for lane in lanes
        if isinstance((identifier := lane.get("id")), str) and identifier in lane_ids
    }
    dependents = {identifier: [] for identifier in lane_ids}
    remaining_dependencies = {
        identifier: len(dependencies.get(identifier, set())) for identifier in lane_ids
    }
    for identifier, dependency_ids in dependencies.items():
        for dependency in dependency_ids:
            dependents[dependency].append(identifier)

    ready = deque(sorted(identifier for identifier, count in remaining_dependencies.items() if count == 0))
    processed = 0
    while ready:
        identifier = ready.popleft()
        processed += 1
        for dependent in sorted(dependents[identifier]):
            remaining_dependencies[dependent] -= 1
            if remaining_dependencies[dependent] == 0:
                ready.append(dependent)
    return processed != len(lane_ids)


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
    if not _is_closed_value(strategy, strategies):
        if len(lanes) > 1:
            errors.append("multi-lane task requires lane_strategy")
        else:
            errors.append("lane_strategy is not allowed")
    if strategy == "parallel_first" and not lanes:
        errors.append("parallel_first requires at least one lane")
    if strategy == "parallel_first" and not _list(parallel.get("integration_order")):
        errors.append("parallel_first requires a non-empty integration_order")
    if strategy == "serial_with_reason":
        serial_reason = parallel.get("serial_reason")
        if not isinstance(serial_reason, str) or not serial_reason.strip():
            errors.append("serial_with_reason requires serial_reason")

    required_lane_fields = {value for value in _list(rules.get("required_lane_fields")) if isinstance(value, str)}
    lane_ids: set[str] = set()
    lane_paths: list[tuple[str, list[str]]] = []
    lease_claims: dict[str, list[tuple[str, object, object, bool]]] = {}
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
        owned_paths_value = lane.get("owned_paths")
        owned_paths = [path for path in _list(owned_paths_value) if _is_safe_repository_relative_path(path)]
        if not isinstance(owned_paths_value, list) or len(owned_paths) != len(_list(owned_paths_value)):
            errors.append(
                f"lane '{display_identifier}' owned_paths must be a list of non-empty safe repository-relative strings"
            )
        for path in _list(owned_paths_value):
            if _is_safe_repository_relative_path(path) and not _is_supported_path_glob(path):
                errors.append("owned_paths must use only '*' and '**' wildcards")
        if not owned_paths:
            errors.append(f"lane '{display_identifier}' requires owned_paths")
        if not isinstance(lane.get("depends_on", []), list):
            errors.append(f"lane '{display_identifier}' depends_on must be a list")
        branch_and_worktree = lane.get("branch_and_worktree")
        if not isinstance(branch_and_worktree, str) or not branch_and_worktree.strip():
            errors.append(f"lane '{display_identifier}' requires branch_and_worktree")
        if not isinstance(lane.get("shared_leases", []), list):
            errors.append(f"lane '{display_identifier}' shared_leases must be a list")
        for lease in _list(lane.get("shared_leases")):
            if not isinstance(lease, dict):
                errors.append(f"lane '{display_identifier}' shared_leases must contain structured leases")
                continue
            resource = lease.get("resource")
            holder = lease.get("holder")
            release_condition = lease.get("release_condition")
            valid_structure = (
                isinstance(resource, str)
                and bool(resource.strip())
                and isinstance(holder, str)
                and bool(holder.strip())
                and isinstance(release_condition, str)
                and bool(release_condition.strip())
            )
            if not valid_structure:
                errors.append(f"lane '{display_identifier}' shared_leases must contain structured leases")
            if isinstance(resource, str) and resource.strip():
                lease_claims.setdefault(resource, []).append(
                    (display_identifier, holder, release_condition, valid_structure)
                )
        lane_paths.append((display_identifier, owned_paths))

    for lane in lanes:
        identifier = lane.get("id") if isinstance(lane.get("id"), str) else "<unnamed>"
        for dependency in _list(lane.get("depends_on")):
            if not isinstance(dependency, str) or dependency not in lane_ids:
                errors.append(f"lane '{identifier}' depends_on unknown lane '{dependency}'")
            elif dependency == identifier:
                errors.append(f"lane '{identifier}' cannot depend_on itself")

    if _has_dependency_cycle(lanes, lane_ids):
        errors.append("parallel lane dependencies must be acyclic")

    lease_resources_by_lane: dict[str, set[str]] = {identifier: set() for identifier in lane_ids}
    for resource, claims in lease_claims.items():
        holders = {
            holder
            for _, holder, _, _ in claims
            if isinstance(holder, str) and holder in lane_ids
        }
        declarers = {declarer for declarer, _, _, _ in claims if declarer in lane_ids}
        all_claims_structured = all(valid_structure for _, _, _, valid_structure in claims)
        if len(holders) != 1:
            errors.append(f"lease '{resource}' holder must name exactly one lane")
        holder = next(iter(holders), None)
        if holder is not None and holder not in declarers:
            errors.append(f"lease '{resource}' holder must declare the resource")
        if len(holders) == 1 and holder in declarers and all_claims_structured:
            for declarer, _, _, _ in claims:
                if declarer in lease_resources_by_lane:
                    lease_resources_by_lane[declarer].add(resource)

    for index, (left_id, left_paths) in enumerate(lane_paths):
        for right_id, right_paths in lane_paths[index + 1 :]:
            overlapping_paths = any(
                _paths_overlap(left_path, right_path)
                for left_path in left_paths
                for right_path in right_paths
            )
            if overlapping_paths and not (
                lease_resources_by_lane.get(left_id, set()) & lease_resources_by_lane.get(right_id, set())
            ):
                errors.append("parallel lanes have overlapping owned_paths")

    constrained_resources_value = parallel.get("constrained_resources", [])
    constrained_resources = [
        resource for resource in _list(constrained_resources_value) if isinstance(resource, str) and resource.strip()
    ]
    if not isinstance(constrained_resources_value, list) or len(constrained_resources) != len(
        _list(constrained_resources_value)
    ):
        errors.append("constrained_resources must be a list of non-empty strings")
    leased_resources = set().union(*lease_resources_by_lane.values()) if lease_resources_by_lane else set()
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
    else:
        integration_positions = {identifier: index for index, identifier in enumerate(integration_order)}
        for lane in lanes:
            identifier = lane.get("id")
            if not isinstance(identifier, str) or identifier not in lane_ids:
                continue
            for dependency in _list(lane.get("depends_on")):
                if (
                    isinstance(dependency, str)
                    and dependency in lane_ids
                    and integration_positions[dependency] > integration_positions[identifier]
                ):
                    errors.append("integration_order must place dependencies before dependents")
                    return


def validate_packet(
    packet: dict[str, object], *, live_state: dict[str, object], policy: dict[str, object]
) -> list[str]:
    """Return deterministic errors for a packet; an empty list means valid."""
    errors: list[str] = []
    execution = packet.get("execution_routing")
    if not isinstance(execution, dict):
        return ["execution_routing is required"]

    target = execution.get("execution_target")
    if not _is_closed_value(target, _closed_values(policy, "execution_targets")):
        errors.append("execution_target is not allowed")
    runner_class = execution.get("runner_class")
    if not _is_closed_value(runner_class, _closed_values(policy, "runner_classes")):
        errors.append("runner_class is not allowed")
    remote_desktop = execution.get("remote_desktop")
    if not _is_closed_value(remote_desktop, {"denied", "exception"}):
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
    elif execution.get("remote_desktop_reason") is not None and execution.get("remote_desktop_reason") != "not_applicable":
        errors.append("remote_desktop_reason requires remote_desktop=exception")

    equivalent_ci = execution.get("equivalent_ci")
    valid_equivalent_ci = equivalent_ci is None or (
        isinstance(equivalent_ci, str) and bool(equivalent_ci.strip())
    )
    if "equivalent_ci" not in execution or not valid_equivalent_ci:
        errors.append("equivalent_ci must be null or a non-empty workflow identifier string")
    equivalent_ci_exists = isinstance(equivalent_ci, str) and bool(equivalent_ci.strip())
    forbidden_actions = _closed_values(policy, "forbidden_remote_desktop_actions_when_equivalent_ci")
    requested_actions_value = execution.get("requested_host_actions")
    requested_actions = _list(requested_actions_value)
    if requested_actions_value is not None and (
        not isinstance(requested_actions_value, list)
        or any(not isinstance(action, str) or action not in forbidden_actions for action in requested_actions)
    ):
        errors.append("requested_host_actions must be a list of supported action strings")
    polling_actions = (
        [requested_actions_value]
        if isinstance(requested_actions_value, str)
        else [action for action in requested_actions if isinstance(action, str)]
    )
    if equivalent_ci_exists and any(
        action in forbidden_actions for action in polling_actions
    ):
        errors.append("equivalent_ci prohibits RDC polling")
    if remote_desktop == "exception" and equivalent_ci is not None:
        errors.append("remote_desktop exception requires no equivalent_ci")
    if requested_actions:
        if remote_desktop != "exception":
            errors.append("requested_host_actions require remote_desktop=exception")
        elif equivalent_ci is not None:
            errors.append("requested_host_actions require equivalent_ci=null")

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
