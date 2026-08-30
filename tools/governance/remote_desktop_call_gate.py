#!/usr/bin/env python3
"""Fail-closed per-call authorization for Remote Desktop connector invocations.

The existing execution-routing action gate remains authoritative for the host
exception, fresh GitHub preflight, semantic host action and connector tool.
This module adds exact argument binding immediately before the connector call.
"""
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from typing import Any

try:  # Normal execution when tools/governance is on sys.path.
    import agent_execution_routing as routing
except ModuleNotFoundError:  # Direct import through importlib in regression tests.
    module_path = Path(__file__).with_name("agent_execution_routing.py")
    spec = importlib.util.spec_from_file_location("agent_execution_routing", module_path)
    assert spec and spec.loader
    routing = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(routing)


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _is_json_value(value: object) -> bool:
    if value is None or isinstance(value, (str, bool)):
        return True
    if type(value) is int:
        return True
    if type(value) is float:
        return math.isfinite(value)
    if isinstance(value, list):
        return all(_is_json_value(member) for member in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _is_json_value(member) for key, member in value.items())
    return False


def _call_gate_config(policy: dict[str, object]) -> tuple[set[str], list[str]]:
    config = policy.get("remote_desktop_call_gate")
    if not isinstance(config, dict):
        return set(), ["policy remote_desktop_call_gate must be an object"]
    errors: list[str] = []
    if config.get("schema_version") != 1:
        errors.append("policy remote_desktop_call_gate.schema_version must be 1")
    if config.get("argument_binding") != "exact_after_nonsemantic_filter":
        errors.append(
            "policy remote_desktop_call_gate.argument_binding must be exact_after_nonsemantic_filter"
        )
    nonsemantic = config.get("nonsemantic_arguments")
    if (
        not isinstance(nonsemantic, list)
        or any(not isinstance(name, str) or not name for name in nonsemantic)
        or len(set(name for name in nonsemantic if isinstance(name, str))) != len(nonsemantic)
    ):
        errors.append(
            "policy remote_desktop_call_gate.nonsemantic_arguments must be a list of unique non-empty strings"
        )
        return set(), errors
    return set(nonsemantic), errors


def _normalize_arguments(arguments: dict[str, Any], nonsemantic: set[str]) -> dict[str, Any]:
    return {key: value for key, value in arguments.items() if key not in nonsemantic}


def _canonical_arguments(arguments: dict[str, Any], nonsemantic: set[str]) -> str:
    """Return a deterministic, JSON-type-sensitive representation for exact binding."""
    return json.dumps(
        _normalize_arguments(arguments, nonsemantic),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def validate_remote_desktop_call(
    host_action: str,
    remote_tool: str,
    tool_arguments: object,
    *,
    packet: dict[str, object] | None,
    live_state: dict[str, object] | None,
    policy: dict[str, object],
) -> list[str]:
    """Validate one exact Remote Desktop connector invocation.

    A successful result authorizes only this semantic action, connector tool and
    normalized argument set for the supplied fresh packet/live-state snapshot.
    It does not authorize a later or different invocation.
    """
    action_errors = routing.validate_remote_desktop_action(
        host_action,
        remote_tool,
        packet=packet,
        live_state=live_state,
        policy=policy,
    )
    if action_errors:
        return action_errors

    nonsemantic, config_errors = _call_gate_config(policy)
    if config_errors:
        return config_errors
    if not isinstance(tool_arguments, dict) or not _is_json_value(tool_arguments):
        return ["remote desktop call arguments are invalid"]

    if not isinstance(packet, dict):
        return ["remote desktop call requires current routing packet"]
    execution = _mapping(packet.get("execution_routing"))
    requested_tools = execution.get("requested_remote_desktop_tools")
    if not isinstance(requested_tools, list):
        return ["remote desktop call requires exact argument declaration"]

    declarations = execution.get("requested_remote_desktop_calls")
    if not isinstance(declarations, list) or not declarations:
        return ["remote desktop call requires exact argument declaration"]

    canonical_actual = _canonical_arguments(tool_arguments, nonsemantic)
    canonical_seen: set[tuple[str, str]] = set()
    matched = False
    for declaration in declarations:
        if not isinstance(declaration, dict) or set(declaration) != {"tool", "arguments"}:
            return ["requested_remote_desktop_calls contains an invalid declaration"]
        declared_tool = declaration.get("tool")
        declared_arguments = declaration.get("arguments")
        if (
            not isinstance(declared_tool, str)
            or declared_tool not in requested_tools
            or not isinstance(declared_arguments, dict)
            or not _is_json_value(declared_arguments)
        ):
            return ["requested_remote_desktop_calls contains an invalid declaration"]
        canonical_declared = _canonical_arguments(declared_arguments, nonsemantic)
        key = (declared_tool, canonical_declared)
        if key in canonical_seen:
            return ["requested_remote_desktop_calls contains a duplicate declaration"]
        canonical_seen.add(key)
        if declared_tool == remote_tool and canonical_declared == canonical_actual:
            matched = True

    if matched:
        return []
    return ["remote desktop call arguments do not match routing packet"]
