#!/usr/bin/env python3
"""Deterministically validate Oteryn agent execution-routing packets.

The caller supplies both policy and current GitHub facts. This module makes
no network, host, Remote Desktop, service, or tool calls.
"""
from __future__ import annotations

import argparse
from collections import deque
from datetime import datetime, timezone
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
_REPOSITORY_COORDINATE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_GIT_SHA = re.compile(r"^[0-9a-fA-F]{40}$")
_REMOTE_DESKTOP_TOOL = re.compile(r"^Remote_Desktop_Commander\.[A-Za-z0-9_]+$")

_UTC_RFC3339 = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")

_CANONICAL_RESUME_PREFLIGHT_FIELDS = (
    "verified_at",
    "repository",
    "default_branch_sha",
    "governing_issue",
    "pull_request",
    "task_head_sha",
)


def _parse_utc_rfc3339(value: object) -> datetime | None:
    """Parse an unambiguous RFC3339 timestamp written explicitly in UTC."""
    if not isinstance(value, str) or not _UTC_RFC3339.fullmatch(value):
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None
    return parsed if parsed.tzinfo == timezone.utc else None


def _is_unique_string_list(value: object) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(member, str) and member for member in value)
        and len(set(value)) == len(value)
    )


def _policy_errors(policy: dict[str, object]) -> list[str]:
    """Reject malformed policy data before it can authorize a packet."""
    errors: list[str] = []
    targets_value = policy.get("execution_targets")
    runners_value = policy.get("runner_classes")
    if not _is_unique_string_list(targets_value):
        errors.append("policy execution_targets must be a non-empty list of unique strings")
    if not _is_unique_string_list(runners_value):
        errors.append("policy runner_classes must be a non-empty list of unique strings")

    reasons_value = policy.get("remote_desktop_reasons")
    actions_value = policy.get("remote_desktop_actions")
    if not _is_unique_string_list(reasons_value):
        errors.append("policy remote_desktop_reasons must be a non-empty list of unique strings")
    if not _is_unique_string_list(actions_value):
        errors.append("policy remote_desktop_actions must be a non-empty list of unique strings")

    reasons = set(reasons_value) if _is_unique_string_list(reasons_value) else set()
    actions = set(actions_value) if _is_unique_string_list(actions_value) else set()
    compatibility_value = policy.get("remote_desktop_reason_action_compatibility")
    if not isinstance(compatibility_value, dict) or set(compatibility_value) != reasons:
        errors.append(
            "policy remote_desktop_reason_action_compatibility must map every and only remote_desktop_reason"
        )
    else:
        for reason, compatible_actions in compatibility_value.items():
            if not _is_unique_string_list(compatible_actions):
                errors.append(
                    f"policy remote_desktop_reason_action_compatibility.{reason} must be a non-empty list of unique actions"
                )
            elif not set(compatible_actions).issubset(actions):
                errors.append(
                    f"policy remote_desktop_reason_action_compatibility.{reason} contains an unknown action"
                )

    known_tools_value = policy.get("known_remote_desktop_tools")
    forbidden_tools_value = policy.get("always_forbidden_remote_desktop_tools")
    if not _is_unique_string_list(known_tools_value) or any(
        not _REMOTE_DESKTOP_TOOL.fullmatch(tool) for tool in _list(known_tools_value) if isinstance(tool, str)
    ):
        errors.append("policy known_remote_desktop_tools must be unique Remote_Desktop_Commander tool identifiers")
    if not _is_unique_string_list(forbidden_tools_value) or any(
        not _REMOTE_DESKTOP_TOOL.fullmatch(tool) for tool in _list(forbidden_tools_value) if isinstance(tool, str)
    ):
        errors.append(
            "policy always_forbidden_remote_desktop_tools must be unique Remote_Desktop_Commander tool identifiers"
        )
    known_tools = set(known_tools_value) if _is_unique_string_list(known_tools_value) else set()
    forbidden_tools = set(forbidden_tools_value) if _is_unique_string_list(forbidden_tools_value) else set()
    if known_tools & forbidden_tools:
        errors.append("policy Remote Desktop known and always-forbidden tool sets must be disjoint")

    lane_rules = policy.get("parallel_lane_rules")
    if not isinstance(lane_rules, dict):
        errors.append("policy parallel_lane_rules must be an object")
    else:
        strategies_value = lane_rules.get("strategies")
        if (
            not _is_unique_string_list(strategies_value)
            or set(strategies_value) != {"single_agent", "parallel_when_beneficial"}
        ):
            errors.append(
                "policy parallel_lane_rules.strategies must be the canonical effort-aware strategy set"
            )
        effort_levels_value = lane_rules.get("effort_levels")
        if (
            not _is_unique_string_list(effort_levels_value)
            or set(effort_levels_value) != {"low", "medium", "high"}
        ):
            errors.append("policy parallel_lane_rules.effort_levels must be the canonical effort set")
        if lane_rules.get("decision_basis_required") is not True:
            errors.append("policy parallel_lane_rules.decision_basis_required must be true")
        single_agent_lane_count = lane_rules.get("single_agent_lane_count")
        if (
            not isinstance(single_agent_lane_count, int)
            or isinstance(single_agent_lane_count, bool)
            or single_agent_lane_count != 1
        ):
            errors.append("policy parallel_lane_rules.single_agent_lane_count must be 1")
        parallel_minimum_lanes = lane_rules.get("parallel_minimum_lanes")
        if (
            not isinstance(parallel_minimum_lanes, int)
            or isinstance(parallel_minimum_lanes, bool)
            or parallel_minimum_lanes != 2
        ):
            errors.append("policy parallel_lane_rules.parallel_minimum_lanes must be 2")
        if lane_rules.get("unique_branch_and_worktree") is not True:
            errors.append("policy parallel_lane_rules.unique_branch_and_worktree must be true")

    required_fields = policy.get("resume_preflight_required_fields")
    if required_fields != list(_CANONICAL_RESUME_PREFLIGHT_FIELDS):
        errors.append(
            "policy resume_preflight_required_fields must be the exact canonical list of unique required identities"
        )

    targets = set(targets_value) if _is_unique_string_list(targets_value) else set()
    runners = set(runners_value) if _is_unique_string_list(runners_value) else set()
    matrix_value = policy.get("target_runner_compatibility")
    if not isinstance(matrix_value, dict):
        errors.append("policy target_runner_compatibility must be an object")
    else:
        matrix_keys = set(matrix_value)
        if matrix_keys != targets:
            errors.append("policy target_runner_compatibility must map every and only execution target")
        for target, compatible_runners in matrix_value.items():
            if not isinstance(target, str) or target not in targets:
                continue
            if not _is_unique_string_list(compatible_runners):
                errors.append(
                    f"policy target_runner_compatibility.{target} must be a non-empty list of runner classes"
                )
            elif not set(compatible_runners).issubset(runners):
                errors.append(
                    f"policy target_runner_compatibility.{target} contains a runner class outside policy runner_classes"
                )

    freshness = policy.get("preflight_freshness")
    if not isinstance(freshness, dict):
        errors.append("policy preflight_freshness must be an object")
    else:
        max_age_seconds = freshness.get("max_age_seconds")
        if not isinstance(max_age_seconds, int) or isinstance(max_age_seconds, bool) or max_age_seconds < 0:
            errors.append("policy preflight_freshness.max_age_seconds must be a non-negative integer")
    return errors


def _is_supported_path_glob(path: object) -> bool:
    """Return whether each path segment is a literal, ``*``, or ``**``.

    Wildcards are complete path segments, never filename fragments. This
    deliberately excludes brace, extglob, character-class, and shell-
    expansion syntax, including star runs longer than two characters.
    """
    if not isinstance(path, str) or "\\" in path:
        return False
    for segment in path.split("/"):
        if not segment:
            return False
        if segment in {"*", "**"}:
            continue
        if "*" in segment or not _LITERAL_PATH_SEGMENT.fullmatch(segment):
            return False
    return True


def _is_positive_identifier(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _has_valid_preflight_identity(field: str, value: object) -> bool:
    if field == "repository":
        return isinstance(value, str) and bool(_REPOSITORY_COORDINATE.fullmatch(value))
    if field in {"default_branch_sha", "task_head_sha"}:
        return isinstance(value, str) and bool(_GIT_SHA.fullmatch(value))
    if field in {"governing_issue", "pull_request"}:
        return _is_positive_identifier(value)
    if field == "verified_at":
        return _parse_utc_rfc3339(value) is not None
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
    for field in required_fields:
        preflight_valid = field in preflight and _has_valid_preflight_identity(field, preflight.get(field))
        live_state_valid = field in live_state and _has_valid_preflight_identity(field, live_state.get(field))
        if field in preflight and not preflight_valid:
            errors.append(f"github_preflight.{field} has invalid identity")
        if field in live_state and not live_state_valid:
            errors.append(f"live_state.{field} has invalid identity")
        if preflight_valid and live_state_valid and preflight[field] != live_state[field]:
            errors.append(f"github_preflight.{field} does not match live_state")

    evaluated_at = live_state.get("evaluated_at")
    if "evaluated_at" not in live_state:
        errors.append("live_state missing evaluation timestamp: evaluated_at")
        return
    evaluation_time = _parse_utc_rfc3339(evaluated_at)
    if evaluation_time is None:
        errors.append("live_state.evaluated_at has invalid UTC RFC3339 timestamp")
        return

    preflight_time = _parse_utc_rfc3339(preflight.get("verified_at"))
    live_preflight_time = _parse_utc_rfc3339(live_state.get("verified_at"))
    if "verified_at" in preflight and preflight_time is None:
        errors.append("github_preflight.verified_at has invalid UTC RFC3339 timestamp")
    if "verified_at" in live_state and live_preflight_time is None:
        errors.append("live_state.verified_at has invalid UTC RFC3339 timestamp")
    if preflight_time is None:
        return
    if preflight_time > evaluation_time:
        errors.append("github_preflight.verified_at is later than live_state.evaluated_at")
        return
    freshness = _mapping(policy.get("preflight_freshness"))
    max_age_seconds = freshness.get("max_age_seconds")
    if isinstance(max_age_seconds, int) and not isinstance(max_age_seconds, bool):
        if (evaluation_time - preflight_time).total_seconds() > max_age_seconds:
            errors.append("github_preflight.verified_at exceeds policy freshness limit")


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
    effort_levels = {value for value in _list(rules.get("effort_levels")) if isinstance(value, str)}
    effort = parallel.get("effort")
    if not _is_closed_value(effort, effort_levels):
        errors.append("parallel_execution.effort is not allowed")
    decision_basis = parallel.get("decision_basis")
    if not isinstance(decision_basis, str) or not decision_basis.strip():
        errors.append("parallel_execution.decision_basis is required")

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
    if strategy == "single_agent" and len(lanes) != 1:
        errors.append("single_agent requires exactly one lane")
    if strategy == "parallel_when_beneficial" and len(lanes) < 2:
        errors.append("parallel_when_beneficial requires at least two lanes")
    if strategy == "parallel_when_beneficial" and not _list(parallel.get("integration_order")):
        errors.append("parallel_when_beneficial requires a non-empty integration_order")

    required_lane_fields = {value for value in _list(rules.get("required_lane_fields")) if isinstance(value, str)}
    lane_ids: set[str] = set()
    lane_paths: list[tuple[str, list[str]]] = []
    branch_and_worktrees: dict[str, list[str]] = {}
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
        else:
            branch_and_worktrees.setdefault(branch_and_worktree, []).append(display_identifier)
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

    if rules.get("unique_branch_and_worktree") is True:
        for lane_identifiers in branch_and_worktrees.values():
            if len(lane_identifiers) > 1:
                errors.append("parallel lanes cannot share branch_and_worktree")

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
    policy_errors = _policy_errors(policy)
    if policy_errors:
        return policy_errors
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
    elif isinstance(target, str):
        matrix = _mapping(policy.get("target_runner_compatibility"))
        if runner_class not in _list(matrix.get(target)):
            errors.append("runner_class is incompatible with execution_target")

    remote_desktop = execution.get("remote_desktop")
    if not _is_closed_value(remote_desktop, {"denied", "exception"}):
        errors.append("remote_desktop must be denied or exception")
    if target == "host_exception" and remote_desktop != "exception":
        errors.append("host_exception requires remote_desktop=exception")
    if remote_desktop == "exception" and target != "host_exception":
        errors.append("remote_desktop exception requires execution_target=host_exception")

    reason = execution.get("remote_desktop_reason")
    allowed_reasons = _closed_values(policy, "remote_desktop_reasons")
    if remote_desktop == "exception":
        if not isinstance(reason, str) or not reason:
            errors.append("remote_desktop exception requires a closed reason")
        elif reason not in allowed_reasons:
            errors.append("remote_desktop_reason is not an allowed exception")
    elif reason is not None and reason != "not_applicable":
        errors.append("remote_desktop_reason requires remote_desktop=exception")

    equivalent_ci = execution.get("equivalent_ci")
    valid_equivalent_ci = equivalent_ci is None or (
        isinstance(equivalent_ci, str) and bool(equivalent_ci.strip())
    )
    if "equivalent_ci" not in execution or not valid_equivalent_ci:
        errors.append("equivalent_ci must be null or a non-empty workflow identifier string")
    equivalent_ci_exists = isinstance(equivalent_ci, str) and bool(equivalent_ci.strip())

    forbidden_actions = _closed_values(policy, "forbidden_remote_desktop_actions_when_equivalent_ci")
    permitted_host_actions = _closed_values(policy, "remote_desktop_actions")
    requested_actions_value = execution.get("requested_host_actions")
    requested_actions = _list(requested_actions_value)
    if requested_actions_value is not None and (
        not isinstance(requested_actions_value, list)
        or any(not isinstance(action, str) or action not in permitted_host_actions for action in requested_actions)
        or len(set(action for action in requested_actions if isinstance(action, str))) != len(requested_actions)
    ):
        errors.append("requested_host_actions must be a list of permitted host action strings")

    compatibility = _mapping(policy.get("remote_desktop_reason_action_compatibility"))
    if remote_desktop == "exception" and isinstance(reason, str) and reason in allowed_reasons:
        compatible_actions = set(
            action for action in _list(compatibility.get(reason)) if isinstance(action, str)
        )
        if any(
            isinstance(action, str) and action in permitted_host_actions and action not in compatible_actions
            for action in requested_actions
        ):
            errors.append("requested_host_actions are incompatible with remote_desktop_reason")

    polling_actions = (
        [requested_actions_value]
        if isinstance(requested_actions_value, str)
        else [action for action in requested_actions if isinstance(action, str)]
    )
    if equivalent_ci_exists and any(action in forbidden_actions for action in polling_actions):
        errors.append("equivalent_ci prohibits RDC polling")
    if remote_desktop == "exception" and equivalent_ci is not None:
        errors.append("remote_desktop exception requires no equivalent_ci")
    if remote_desktop == "exception":
        if not isinstance(requested_actions_value, list) or not requested_actions:
            errors.append("remote_desktop exception requires non-empty requested_host_actions")
        elif equivalent_ci is not None:
            errors.append("requested_host_actions require equivalent_ci=null")
    elif requested_actions:
        errors.append("requested_host_actions require remote_desktop=exception")

    known_tools = _closed_values(policy, "known_remote_desktop_tools")
    requested_tools_value = execution.get("requested_remote_desktop_tools")
    requested_tools = _list(requested_tools_value)
    if requested_tools_value is not None and (
        not isinstance(requested_tools_value, list)
        or not requested_tools
        or any(not isinstance(tool, str) or tool not in known_tools for tool in requested_tools)
        or len(set(tool for tool in requested_tools if isinstance(tool, str))) != len(requested_tools)
    ):
        errors.append("requested_remote_desktop_tools must contain only known permitted tool identifiers")
    if remote_desktop == "exception":
        if not isinstance(requested_tools_value, list) or not requested_tools:
            errors.append("remote_desktop exception requires non-empty requested_remote_desktop_tools")
    elif requested_tools:
        errors.append("requested_remote_desktop_tools require remote_desktop=exception")

    _validate_preflight(execution, _mapping(live_state), policy, errors)
    parallel = packet.get("parallel_execution")
    if not isinstance(parallel, dict):
        errors.append("parallel_execution is required")
    else:
        _validate_lanes(parallel, policy, errors)
    return errors


def validate_remote_desktop_action(
    host_action: str,
    remote_tool: str,
    *,
    packet: dict[str, object] | None,
    live_state: dict[str, object] | None,
    policy: dict[str, object],
) -> list[str]:
    """Return no errors only when this exact direct Remote Desktop call is allowed."""
    policy_errors = _policy_errors(policy)
    if policy_errors:
        return policy_errors

    if not isinstance(remote_tool, str) or not remote_tool:
        return ["remote desktop tool identifier is invalid"]
    if not isinstance(host_action, str) or not host_action:
        return ["host action identifier is invalid"]
    if remote_tool in _closed_values(policy, "always_forbidden_remote_desktop_tools"):
        return ["remote desktop tool is always forbidden by policy"]
    if remote_tool not in _closed_values(policy, "known_remote_desktop_tools"):
        return ["remote desktop tool is not policy-known"]
    if not isinstance(packet, dict) or not isinstance(live_state, dict):
        return ["remote desktop direct call requires current packet and live_state"]

    packet_errors = validate_packet(packet, live_state=live_state, policy=policy)
    if packet_errors:
        return ["remote desktop direct call requires valid routing packet", *packet_errors]

    execution = _mapping(packet.get("execution_routing"))
    if execution.get("execution_target") != "host_exception" or execution.get("remote_desktop") != "exception":
        return ["remote desktop direct call requires validated host_exception"]

    reason = execution.get("remote_desktop_reason")
    compatibility = _mapping(policy.get("remote_desktop_reason_action_compatibility"))
    if host_action not in _list(compatibility.get(reason)):
        return ["host action is incompatible with remote_desktop_reason"]
    if host_action not in _list(execution.get("requested_host_actions")):
        return ["host action was not requested by the routing packet"]
    if remote_tool not in _list(execution.get("requested_remote_desktop_tools")):
        return ["remote desktop tool was not requested by the routing packet"]
    return []


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
