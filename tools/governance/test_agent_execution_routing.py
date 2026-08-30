#!/usr/bin/env python3
"""Behavior tests for the agent execution-routing contract.

The validator is deliberately imported from a sibling module so this file is
red until Task 2 supplies the implementation.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

MODULE_PATH = Path(__file__).with_name("agent_execution_routing.py")
SPEC = importlib.util.spec_from_file_location("agent_execution_routing", MODULE_PATH)
assert SPEC and SPEC.loader
routing = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(routing)

REPO = "Oteryn/Oteryn"
SHA = "d79df968c1aba98373455399732fc71ab71e6a5d"
GOVERNING_ISSUE = 85
PULL_REQUEST = 87
TASK_HEAD_SHA = "f4cda70de8bc61008226c6be2983cff34600f86d"


def policy() -> dict[str, object]:
    path = Path(__file__).parents[2] / "ecosystem" / "agent-execution-routing-policy.json"
    return json.loads(path.read_text(encoding="utf-8"))


def live_state() -> dict[str, object]:
    return {
        "verified_at": "2026-08-26T12:00:00Z",
        "evaluated_at": "2026-08-26T12:05:00Z",
        "repository": REPO,
        "default_branch": "main",
        "default_branch_sha": SHA,
        "governing_issue": GOVERNING_ISSUE,
        "pull_request": PULL_REQUEST,
        "task_head_sha": TASK_HEAD_SHA,
    }


def preflight() -> dict[str, object]:
    return {
        "verified_at": "2026-08-26T12:00:00Z",
        "repository": REPO,
        "default_branch_sha": SHA,
        "governing_issue": GOVERNING_ISSUE,
        "pull_request": PULL_REQUEST,
        "task_head_sha": TASK_HEAD_SHA,
    }


def lane(identifier: str, paths: list[str], *, depends_on: list[str] | None = None) -> dict[str, object]:
    return {
        "id": identifier,
        "owned_paths": paths,
        "depends_on": depends_on or [],
        "branch_and_worktree": f"governance/{identifier}:worktrees/{identifier}",
        "shared_leases": [],
    }


def default_packet() -> dict[str, object]:
    return {
        "execution_routing": {
            "execution_target": "github_actions",
            "runner_class": "github_hosted",
            "equivalent_ci": ".github/workflows/ci.yml:meta-gate",
            "remote_desktop": "denied",
            "remote_desktop_reason": "not_applicable",
            "github_preflight": preflight(),
        },
        "parallel_execution": {
            "effort": "medium",
            "lane_strategy": "single_agent",
            "decision_basis": "one shared governance contract is faster with one writer",
            "lanes": [lane("policy", ["docs/agents/schemas/**"])],
            "integration_order": ["policy"],
        },
    }


def exception_packet(reason: str) -> dict[str, object]:
    packet = default_packet()
    execution = packet["execution_routing"]
    assert isinstance(execution, dict)
    actions_by_reason = {
        "host_only_service": ["inspect_host_only_service"],
        "lan_or_hardware": ["perform_lan_or_hardware_acceptance"],
        "self_hosted_runner_diagnosis": ["diagnose_self_hosted_runner"],
    }
    tools_by_reason = {
        "host_only_service": ["Remote_Desktop_Commander.get_config"],
        "lan_or_hardware": ["Remote_Desktop_Commander.ping"],
        "self_hosted_runner_diagnosis": ["Remote_Desktop_Commander.list_processes"],
    }
    execution.update(
        {
            "execution_target": "host_exception",
            "runner_class": "not_applicable",
            "remote_desktop": "exception",
            "remote_desktop_reason": reason,
            "equivalent_ci": None,
            "requested_host_actions": actions_by_reason.get(reason, ["inspect_host_only_service"]),
            "requested_remote_desktop_tools": tools_by_reason.get(
                reason, ["Remote_Desktop_Commander.get_config"]
            ),
        }
    )
    return packet


def test_default_actions_packet_passes() -> None:
    assert routing.validate_packet(default_packet(), live_state=live_state(), policy=policy()) == []


def test_preflight_timestamps_require_strict_utc_rfc3339_and_freshness() -> None:
    cases = (
        ("github_preflight", "verified_at", "2026-08-26 12:00:00Z", "has invalid UTC RFC3339 timestamp"),
        ("github_preflight", "verified_at", "2026-08-26T12:06:00Z", "is later than live_state.evaluated_at"),
        ("github_preflight", "verified_at", "2026-08-26T11:49:59Z", "exceeds policy freshness limit"),
        ("live_state", "evaluated_at", "not-a-timestamp", "has invalid UTC RFC3339 timestamp"),
    )
    for location, field, value, expected_error in cases:
        packet = default_packet()
        current_live_state = live_state()
        if location == "github_preflight":
            execution = packet["execution_routing"]
            assert isinstance(execution, dict)
            preflight_data = execution["github_preflight"]
            assert isinstance(preflight_data, dict)
            preflight_data[field] = value
        else:
            current_live_state[field] = value
        errors = routing.validate_packet(packet, live_state=current_live_state, policy=policy())
        assert any(expected_error in error for error in errors)


def test_missing_evaluation_timestamp_fails_closed() -> None:
    current_live_state = live_state()
    del current_live_state["evaluated_at"]
    errors = routing.validate_packet(default_packet(), live_state=current_live_state, policy=policy())
    assert "live_state missing evaluation timestamp: evaluated_at" in errors


def test_policy_drives_preflight_limit_and_target_runner_matrix() -> None:
    packet = default_packet()
    execution = packet["execution_routing"]
    assert isinstance(execution, dict)
    preflight_data = execution["github_preflight"]
    assert isinstance(preflight_data, dict)
    preflight_data["verified_at"] = "2026-08-26T12:03:00Z"
    current_live_state = live_state()
    current_live_state["verified_at"] = "2026-08-26T12:03:00Z"

    tightened_policy = policy()
    freshness = tightened_policy["preflight_freshness"]
    assert isinstance(freshness, dict)
    freshness["max_age_seconds"] = 60
    errors = routing.validate_packet(packet, live_state=current_live_state, policy=tightened_policy)
    assert "github_preflight.verified_at exceeds policy freshness limit" in errors

    widened_policy = policy()
    freshness = widened_policy["preflight_freshness"]
    assert isinstance(freshness, dict)
    freshness["max_age_seconds"] = 180
    assert routing.validate_packet(packet, live_state=current_live_state, policy=widened_policy) == []

    incompatible_policy = policy()
    matrix = incompatible_policy["target_runner_compatibility"]
    assert isinstance(matrix, dict)
    matrix["github_actions"] = ["organization_product_isolated"]
    errors = routing.validate_packet(default_packet(), live_state=live_state(), policy=incompatible_policy)
    assert "runner_class is incompatible with execution_target" in errors


def test_malformed_policy_freshness_and_matrix_fail_closed() -> None:
    malformed_policies = []
    missing_target_policy = policy()
    matrix = missing_target_policy["target_runner_compatibility"]
    assert isinstance(matrix, dict)
    del matrix["host_exception"]
    malformed_policies.append(missing_target_policy)

    unknown_runner_policy = policy()
    matrix = unknown_runner_policy["target_runner_compatibility"]
    assert isinstance(matrix, dict)
    matrix["github_actions"] = ["untrusted_runner"]
    malformed_policies.append(unknown_runner_policy)

    malformed_freshness_policy = policy()
    freshness = malformed_freshness_policy["preflight_freshness"]
    assert isinstance(freshness, dict)
    freshness["max_age_seconds"] = -1
    malformed_policies.append(malformed_freshness_policy)

    for malformed_policy in malformed_policies:
        errors = routing.validate_packet(default_packet(), live_state=live_state(), policy=malformed_policy)
        assert any(error.startswith("policy ") for error in errors)


def test_malformed_effort_planning_policy_fails_closed() -> None:
    cases = (
        ("strategies", ["parallel_first"], "policy parallel_lane_rules.strategies must be the canonical effort-aware strategy set"),
        ("effort_levels", ["medium"], "policy parallel_lane_rules.effort_levels must be the canonical effort set"),
        ("decision_basis_required", False, "policy parallel_lane_rules.decision_basis_required must be true"),
        ("single_agent_lane_count", 2, "policy parallel_lane_rules.single_agent_lane_count must be 1"),
        ("parallel_minimum_lanes", 1, "policy parallel_lane_rules.parallel_minimum_lanes must be 2"),
    )
    for field, invalid_value, expected_error in cases:
        malformed_policy = policy()
        rules = malformed_policy["parallel_lane_rules"]
        assert isinstance(rules, dict)
        rules.update(
            {
                "strategies": ["single_agent", "parallel_when_beneficial"],
                "effort_levels": ["low", "medium", "high"],
                "decision_basis_required": True,
                "single_agent_lane_count": 1,
                "parallel_minimum_lanes": 2,
            }
        )
        rules[field] = invalid_value
        errors = routing.validate_packet(default_packet(), live_state=live_state(), policy=malformed_policy)
        assert expected_error in errors


def test_resume_required_fields_policy_is_exact_and_fail_closed() -> None:
    malformed_values = (
        [],
        ["verified_at"],
        ["verified_at", "repository", "default_branch_sha", "governing_issue", "pull_request", "task_head_sha", "task_head_sha"],
        ["verified_at", "repository", "default_branch_sha", "governing_issue", "pull_request", "unknown"],
        ["verified_at", "repository", "default_branch_sha", "governing_issue", "pull_request", None],
        "verified_at",
        None,
    )
    for malformed_value in malformed_values:
        malformed_policy = policy()
        malformed_policy["resume_preflight_required_fields"] = malformed_value
        errors = routing.validate_packet(default_packet(), live_state=live_state(), policy=malformed_policy)
        assert "policy resume_preflight_required_fields must be the exact canonical list of unique required identities" in errors


def test_malformed_required_fields_cannot_make_null_identities_pass() -> None:
    malformed_policy = policy()
    malformed_policy["resume_preflight_required_fields"] = ["verified_at"]
    packet = default_packet()
    execution = packet["execution_routing"]
    assert isinstance(execution, dict)
    packet_preflight = execution["github_preflight"]
    assert isinstance(packet_preflight, dict)
    packet_preflight.update({"repository": None, "default_branch_sha": None, "governing_issue": None, "pull_request": None, "task_head_sha": None})
    current_live_state = live_state()
    current_live_state.update({"repository": None, "default_branch_sha": None, "governing_issue": None, "pull_request": None, "task_head_sha": None})
    errors = routing.validate_packet(packet, live_state=current_live_state, policy=malformed_policy)
    assert errors == ["policy resume_preflight_required_fields must be the exact canonical list of unique required identities"]


def test_undeclared_remote_desktop_exception_fails() -> None:
    packet = default_packet()
    execution = packet["execution_routing"]
    assert isinstance(execution, dict)
    execution["execution_target"] = "host_exception"
    assert "host_exception requires remote_desktop=exception" in routing.validate_packet(packet, live_state=live_state(), policy=policy())


def test_missing_remote_desktop_reason_fails() -> None:
    packet = exception_packet("not_applicable")
    execution = packet["execution_routing"]
    assert isinstance(execution, dict)
    execution["remote_desktop_reason"] = None
    assert "remote_desktop exception requires a closed reason" in routing.validate_packet(packet, live_state=live_state(), policy=policy())


def test_non_closed_remote_desktop_reason_fails() -> None:
    packet = exception_packet("available_shell")
    assert "remote_desktop_reason is not an allowed exception" in routing.validate_packet(packet, live_state=live_state(), policy=policy())


def test_remote_desktop_exception_requires_a_host_exception_route() -> None:
    packet = default_packet()
    execution = packet["execution_routing"]
    assert isinstance(execution, dict)
    execution.update({"remote_desktop": "exception", "remote_desktop_reason": "lan_or_hardware"})
    assert "remote_desktop exception requires execution_target=host_exception" in routing.validate_packet(
        packet, live_state=live_state(), policy=policy()
    )


def test_equivalent_ci_forbids_rdc_polling() -> None:
    packet = exception_packet("self_hosted_runner_diagnosis")
    execution = packet["execution_routing"]
    assert isinstance(execution, dict)
    execution["equivalent_ci"] = ".github/workflows/ci.yml:meta-gate"
    execution["requested_host_actions"] = ["poll_docker_logs"]
    assert "equivalent_ci prohibits RDC polling" in routing.validate_packet(packet, live_state=live_state(), policy=policy())


def test_remote_desktop_exception_requires_no_equivalent_ci() -> None:
    packet = exception_packet("self_hosted_runner_diagnosis")
    execution = packet["execution_routing"]
    assert isinstance(execution, dict)
    execution["equivalent_ci"] = ".github/workflows/ci.yml:meta-gate"
    assert "remote_desktop exception requires no equivalent_ci" in routing.validate_packet(
        packet, live_state=live_state(), policy=policy()
    )


def test_parallel_lanes_cannot_share_a_writable_branch_and_worktree() -> None:
    packet = default_packet()
    parallel = packet["parallel_execution"]
    assert isinstance(parallel, dict)
    first = lane("first", ["docs/first/**"])
    second = lane("second", ["src/second/**"])
    second["branch_and_worktree"] = first["branch_and_worktree"]
    parallel["lanes"] = [first, second]
    parallel["integration_order"] = ["first", "second"]

    errors = routing.validate_packet(packet, live_state=live_state(), policy=policy())

    assert "parallel lanes cannot share branch_and_worktree" in errors


def test_host_exception_requires_a_non_empty_permitted_action_record() -> None:
    packet = exception_packet("host_only_service")
    execution = packet["execution_routing"]
    assert isinstance(execution, dict)
    del execution["requested_host_actions"]

    errors = routing.validate_packet(packet, live_state=live_state(), policy=policy())

    assert "remote_desktop exception requires non-empty requested_host_actions" in errors


def test_host_exception_rejects_actions_outside_the_policy_list() -> None:
    packet = exception_packet("host_only_service")
    execution = packet["execution_routing"]
    assert isinstance(execution, dict)
    execution["requested_host_actions"] = ["change_host_configuration"]

    errors = routing.validate_packet(packet, live_state=live_state(), policy=policy())

    assert "requested_host_actions must be a list of permitted host action strings" in errors


def test_host_exception_accepts_a_policy_permitted_least_privilege_action() -> None:
    packet = exception_packet("lan_or_hardware")

    assert routing.validate_packet(packet, live_state=live_state(), policy=policy()) == []


def test_missing_resume_preflight_fails() -> None:
    packet = default_packet()
    execution = packet["execution_routing"]
    assert isinstance(execution, dict)
    execution["github_preflight"] = {}
    assert "github_preflight is required" in routing.validate_packet(packet, live_state=live_state(), policy=policy())


def test_stale_resume_preflight_fails() -> None:
    packet = default_packet()
    execution = packet["execution_routing"]
    assert isinstance(execution, dict)
    preflight_data = execution["github_preflight"]
    assert isinstance(preflight_data, dict)
    preflight_data["default_branch_sha"] = "a" * 40
    assert "github_preflight.default_branch_sha does not match live_state" in routing.validate_packet(packet, live_state=live_state(), policy=policy())


def test_missing_resume_preflight_fields_fail() -> None:
    required_fields = [
        "verified_at",
        "repository",
        "default_branch_sha",
        "governing_issue",
        "pull_request",
        "task_head_sha",
    ]
    for field in required_fields:
        packet = default_packet()
        execution = packet["execution_routing"]
        assert isinstance(execution, dict)
        preflight_data = execution["github_preflight"]
        assert isinstance(preflight_data, dict)
        del preflight_data[field]
        errors = routing.validate_packet(packet, live_state=live_state(), policy=policy())
        assert f"github_preflight missing required field: {field}" in errors


def test_resume_preflight_identity_mismatches_fail() -> None:
    mismatches = {
        "repository": "Oteryn/other-repository",
        "governing_issue": 999,
        "pull_request": 999,
        "task_head_sha": "a" * 40,
    }
    for field, value in mismatches.items():
        packet = default_packet()
        execution = packet["execution_routing"]
        assert isinstance(execution, dict)
        preflight_data = execution["github_preflight"]
        assert isinstance(preflight_data, dict)
        preflight_data[field] = value
        errors = routing.validate_packet(packet, live_state=live_state(), policy=policy())
        assert f"github_preflight.{field} does not match live_state" in errors


def test_resume_preflight_rejects_missing_or_malformed_identities_before_comparison() -> None:
    invalid_values = {
        "repository": (None, "", "Oteryn", "Oteryn/"),
        "default_branch_sha": (None, "", "a" * 39, "g" * 40),
        "governing_issue": (None, 0, -1, "85"),
        "pull_request": (None, 0, -1, "87"),
        "task_head_sha": (None, "", "a" * 39, "g" * 40),
    }
    for field, values in invalid_values.items():
        for value in values:
            packet = default_packet()
            execution = packet["execution_routing"]
            assert isinstance(execution, dict)
            preflight_data = execution["github_preflight"]
            assert isinstance(preflight_data, dict)
            preflight_data[field] = value
            errors = routing.validate_packet(packet, live_state=live_state(), policy=policy())
            assert f"github_preflight.{field} has invalid identity" in errors

            current_state = live_state()
            current_state[field] = value
            errors = routing.validate_packet(default_packet(), live_state=current_state, policy=policy())
            assert f"live_state.{field} has invalid identity" in errors


def test_runner_class_must_be_compatible_with_execution_target() -> None:
    allowed_routes = {
        "github_actions": ("github_hosted", "organization_product_isolated"),
        "isolated_workspace": ("isolated_workspace",),
        "host_exception": ("not_applicable",),
    }
    for target, runner_classes in allowed_routes.items():
        for runner_class in runner_classes:
            packet = exception_packet("lan_or_hardware") if target == "host_exception" else default_packet()
            execution = packet["execution_routing"]
            assert isinstance(execution, dict)
            execution["execution_target"] = target
            execution["runner_class"] = runner_class
            assert routing.validate_packet(packet, live_state=live_state(), policy=policy()) == []

    packet = default_packet()
    execution = packet["execution_routing"]
    assert isinstance(execution, dict)
    execution["execution_target"] = "isolated_workspace"
    assert "runner_class is incompatible with execution_target" in routing.validate_packet(
        packet, live_state=live_state(), policy=policy()
    )


def test_multi_lane_task_requires_parallel_plan() -> None:
    packet = default_packet()
    parallel = packet["parallel_execution"]
    assert isinstance(parallel, dict)
    parallel["lanes"] = [lane("one", ["src/one/**"]), lane("two", ["src/two/**"])]
    parallel["lane_strategy"] = None
    assert "multi-lane task requires lane_strategy" in routing.validate_packet(packet, live_state=live_state(), policy=policy())


def test_single_agent_is_a_first_class_strategy_without_serial_exception() -> None:
    packet = default_packet()
    parallel = packet["parallel_execution"]
    assert isinstance(parallel, dict)
    assert "serial_reason" not in parallel
    assert routing.validate_packet(packet, live_state=live_state(), policy=policy()) == []


def test_single_agent_requires_exactly_one_lane() -> None:
    packet = default_packet()
    parallel = packet["parallel_execution"]
    assert isinstance(parallel, dict)
    parallel["lanes"] = [lane("one", ["src/one/**"]), lane("two", ["src/two/**"])]
    parallel["integration_order"] = ["one", "two"]
    assert "single_agent requires exactly one lane" in routing.validate_packet(
        packet, live_state=live_state(), policy=policy()
    )


def test_parallel_when_beneficial_requires_at_least_two_lanes() -> None:
    packet = default_packet()
    parallel = packet["parallel_execution"]
    assert isinstance(parallel, dict)
    parallel["lane_strategy"] = "parallel_when_beneficial"
    errors = routing.validate_packet(packet, live_state=live_state(), policy=policy())
    assert "parallel_when_beneficial requires at least two lanes" in errors


def test_parallel_when_beneficial_accepts_two_independent_lanes() -> None:
    packet = default_packet()
    parallel = packet["parallel_execution"]
    assert isinstance(parallel, dict)
    parallel["lane_strategy"] = "parallel_when_beneficial"
    parallel["decision_basis"] = "two disjoint workstreams can progress independently"
    parallel["lanes"] = [lane("one", ["src/one/**"]), lane("two", ["src/two/**"])]
    parallel["integration_order"] = ["one", "two"]
    assert routing.validate_packet(packet, live_state=live_state(), policy=policy()) == []


def test_effort_and_decision_basis_are_required() -> None:
    for field, expected_error in (
        ("effort", "parallel_execution.effort is not allowed"),
        ("decision_basis", "parallel_execution.decision_basis is required"),
    ):
        packet = default_packet()
        parallel = packet["parallel_execution"]
        assert isinstance(parallel, dict)
        del parallel[field]
        errors = routing.validate_packet(packet, live_state=live_state(), policy=policy())
        assert expected_error in errors


def test_effort_must_use_the_closed_policy_set() -> None:
    packet = default_packet()
    parallel = packet["parallel_execution"]
    assert isinstance(parallel, dict)
    parallel["effort"] = "extreme"
    assert "parallel_execution.effort is not allowed" in routing.validate_packet(
        packet, live_state=live_state(), policy=policy()
    )


def test_overlapping_parallel_lanes_fail() -> None:
    packet = default_packet()
    parallel = packet["parallel_execution"]
    assert isinstance(parallel, dict)
    parallel["lanes"] = [
        lane("contract", ["docs/agents/contracts/**"]),
        lane("specific-file", ["docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md"]),
    ]
    assert "parallel lanes have overlapping owned_paths" in routing.validate_packet(packet, live_state=live_state(), policy=policy())


def test_unsupported_question_mark_glob_cannot_hide_owned_path_conflict() -> None:
    packet = default_packet()
    parallel = packet["parallel_execution"]
    assert isinstance(parallel, dict)
    parallel["lanes"] = [lane("glob", ["src/?.py"]), lane("specific", ["src/a.py"])]
    parallel["integration_order"] = ["glob", "specific"]
    errors = routing.validate_packet(packet, live_state=live_state(), policy=policy())
    assert "owned_paths must use only '*' and '**' wildcards" in errors


def test_unsupported_character_class_glob_cannot_hide_owned_path_conflict() -> None:
    packet = default_packet()
    parallel = packet["parallel_execution"]
    assert isinstance(parallel, dict)
    parallel["lanes"] = [lane("glob", ["src/[ab].py"]), lane("specific", ["src/a.py"])]
    parallel["integration_order"] = ["glob", "specific"]
    errors = routing.validate_packet(packet, live_state=live_state(), policy=policy())
    assert "owned_paths must use only '*' and '**' wildcards" in errors


def test_unsupported_brace_glob_cannot_hide_owned_path_conflict() -> None:
    packet = default_packet()
    parallel = packet["parallel_execution"]
    assert isinstance(parallel, dict)
    parallel["lanes"] = [lane("glob", ["src/{a,b}.py"]), lane("specific", ["src/a.py"])]
    parallel["integration_order"] = ["glob", "specific"]
    errors = routing.validate_packet(packet, live_state=live_state(), policy=policy())
    assert "owned_paths must use only '*' and '**' wildcards" in errors


def test_unsupported_extglob_prefixes_cannot_hide_owned_path_conflict() -> None:
    for prefix in ("!", "@", "+", "?", "*"):
        packet = default_packet()
        parallel = packet["parallel_execution"]
        assert isinstance(parallel, dict)
        parallel["lanes"] = [lane("glob", [f"src/{prefix}(a).py"]), lane("specific", ["src/a.py"])]
        parallel["integration_order"] = ["glob", "specific"]
        errors = routing.validate_packet(packet, live_state=live_state(), policy=policy())
        assert "owned_paths must use only '*' and '**' wildcards" in errors


def test_wildcards_must_be_complete_path_segments() -> None:
    for path in ("src/a*.py", "src/foo**bar.py", "src/***", "src/****"):
        packet = default_packet()
        parallel = packet["parallel_execution"]
        assert isinstance(parallel, dict)
        parallel["lanes"] = [lane("invalid", [path])]
        parallel["integration_order"] = ["invalid"]
        errors = routing.validate_packet(packet, live_state=live_state(), policy=policy())
        assert "owned_paths must use only '*' and '**' wildcards" in errors


def test_partial_segment_wildcard_cannot_hide_owned_path_conflict() -> None:
    packet = default_packet()
    parallel = packet["parallel_execution"]
    assert isinstance(parallel, dict)
    parallel["lanes"] = [lane("glob", ["src/*"]), lane("specific", ["src/ab.py"])]
    parallel["integration_order"] = ["glob", "specific"]
    errors = routing.validate_packet(packet, live_state=live_state(), policy=policy())
    assert "parallel lanes have overlapping owned_paths" in errors


def test_partial_segment_wildcard_collision_is_rejected() -> None:
    packet = default_packet()
    parallel = packet["parallel_execution"]
    assert isinstance(parallel, dict)
    parallel["lanes"] = [lane("glob", ["src/a*.py"]), lane("specific", ["src/ab.py"])]
    parallel["integration_order"] = ["glob", "specific"]
    errors = routing.validate_packet(packet, live_state=live_state(), policy=policy())
    assert "owned_paths must use only '*' and '**' wildcards" in errors


def test_token_wildcard_segments_remain_valid() -> None:
    for path in ("src/*", "src/**", "src/lib", "docs/agents/schemas/**"):
        packet = default_packet()
        parallel = packet["parallel_execution"]
        assert isinstance(parallel, dict)
        parallel["lanes"] = [lane("valid", [path])]
        parallel["integration_order"] = ["valid"]
        assert routing.validate_packet(packet, live_state=live_state(), policy=policy()) == []


def test_backslash_owned_path_is_rejected() -> None:
    packet = default_packet()
    parallel = packet["parallel_execution"]
    assert isinstance(parallel, dict)
    parallel["lanes"] = [lane("path", [r"src\\*.py"])]
    errors = routing.validate_packet(packet, live_state=live_state(), policy=policy())
    assert any("owned_paths must be a list of non-empty safe repository-relative strings" in error for error in errors)


def test_unknown_lane_dependency_fails() -> None:
    packet = default_packet()
    parallel = packet["parallel_execution"]
    assert isinstance(parallel, dict)
    parallel["lanes"] = [lane("policy", ["docs/agents/schemas/**"], depends_on=["missing"])]
    assert "lane 'policy' depends_on unknown lane 'missing'" in routing.validate_packet(
        packet, live_state=live_state(), policy=policy()
    )


def test_constrained_resource_requires_a_lease() -> None:
    packet = default_packet()
    parallel = packet["parallel_execution"]
    assert isinstance(parallel, dict)
    parallel["constrained_resources"] = ["heavy-test-slot"]
    assert "constrained resource requires a lease: heavy-test-slot" in routing.validate_packet(
        packet, live_state=live_state(), policy=policy()
    )


def test_closed_enum_non_strings_are_deterministic_errors() -> None:
    invalid_values = {
        "execution_target": [],
        "runner_class": {},
        "remote_desktop": [],
        "remote_desktop_reason": {},
    }
    expected_errors = {
        "execution_target": "execution_target is not allowed",
        "runner_class": "runner_class is not allowed",
        "remote_desktop": "remote_desktop must be denied or exception",
        "remote_desktop_reason": "remote_desktop_reason requires remote_desktop=exception",
    }
    for field, value in invalid_values.items():
        packet = default_packet()
        execution = packet["execution_routing"]
        assert isinstance(execution, dict)
        execution[field] = value
        errors = routing.validate_packet(packet, live_state=live_state(), policy=policy())
        assert expected_errors[field] in errors


def test_missing_or_partial_live_state_fails_fresh_preflight() -> None:
    empty_errors = routing.validate_packet(default_packet(), live_state={}, policy=policy())
    assert "live_state missing required field: repository" in empty_errors
    assert "live_state missing required field: default_branch_sha" in empty_errors

    partial_errors = routing.validate_packet(
        default_packet(),
        live_state={"repository": REPO},
        policy=policy(),
    )
    assert "live_state missing required field: default_branch_sha" in partial_errors


def test_dependency_cycles_are_rejected() -> None:
    packet = default_packet()
    parallel = packet["parallel_execution"]
    assert isinstance(parallel, dict)
    parallel["lanes"] = [
        lane("one", ["src/one/**"], depends_on=["two"]),
        lane("two", ["src/two/**"], depends_on=["three"]),
        lane("three", ["src/three/**"], depends_on=["one"]),
    ]
    parallel["integration_order"] = ["one", "two", "three"]
    assert "parallel lane dependencies must be acyclic" in routing.validate_packet(
        packet, live_state=live_state(), policy=policy()
    )


def test_large_dependency_cycle_is_rejected_without_recursion_error() -> None:
    packet = default_packet()
    parallel = packet["parallel_execution"]
    assert isinstance(parallel, dict)
    lane_count = 1_101
    lane_ids = [f"lane-{index}" for index in range(lane_count)]
    parallel["lanes"] = [
        lane(identifier, [f"src/{identifier}/**"], depends_on=[lane_ids[(index + 1) % lane_count]])
        for index, identifier in enumerate(lane_ids)
    ]
    parallel["integration_order"] = lane_ids
    errors = routing.validate_packet(packet, live_state=live_state(), policy=policy())
    assert "parallel lane dependencies must be acyclic" in errors


def test_structured_leases_require_one_valid_holder_and_release_condition() -> None:
    packet = default_packet()
    parallel = packet["parallel_execution"]
    assert isinstance(parallel, dict)
    first = lane("first", ["src/shared/**"])
    second = lane("second", ["src/shared/file.py"])
    first["shared_leases"] = ["shared-resource"]
    second["shared_leases"] = [
        {"resource": "shared-resource", "holder": "missing", "release_condition": "merged"}
    ]
    parallel["lanes"] = [first, second]
    parallel["constrained_resources"] = ["shared-resource"]
    parallel["integration_order"] = ["first", "second"]
    errors = routing.validate_packet(packet, live_state=live_state(), policy=policy())
    assert "lane 'first' shared_leases must contain structured leases" in errors
    assert "lease 'shared-resource' holder must name exactly one lane" in errors


def test_lease_holder_must_declare_the_resource() -> None:
    packet = default_packet()
    parallel = packet["parallel_execution"]
    assert isinstance(parallel, dict)
    first = lane("first", ["src/first/**"])
    second = lane("second", ["src/second/**"])
    second["shared_leases"] = [
        {"resource": "heavy-test-slot", "holder": "first", "release_condition": "merged"}
    ]
    parallel["lanes"] = [first, second]
    parallel["constrained_resources"] = ["heavy-test-slot"]
    parallel["integration_order"] = ["first", "second"]
    errors = routing.validate_packet(packet, live_state=live_state(), policy=policy())
    assert "lease 'heavy-test-slot' holder must declare the resource" in errors


def test_requested_host_actions_must_be_a_supported_string_list() -> None:
    packet = default_packet()
    execution = packet["execution_routing"]
    assert isinstance(execution, dict)
    execution["requested_host_actions"] = "poll_docker_logs"
    errors = routing.validate_packet(packet, live_state=live_state(), policy=policy())
    assert "requested_host_actions must be a list of permitted host action strings" in errors
    assert "equivalent_ci prohibits RDC polling" in errors

    for malformed_actions in ({"action": "poll_docker_logs"}, ["poll_docker_logs", {}], ["unknown_action"]):
        packet = default_packet()
        execution = packet["execution_routing"]
        assert isinstance(execution, dict)
        execution["requested_host_actions"] = malformed_actions
        errors = routing.validate_packet(packet, live_state=live_state(), policy=policy())
        assert "requested_host_actions must be a list of permitted host action strings" in errors


def test_integration_order_requires_dependencies_first() -> None:
    packet = default_packet()
    parallel = packet["parallel_execution"]
    assert isinstance(parallel, dict)
    parallel["lanes"] = [
        lane("dependent", ["src/dependent/**"], depends_on=["dependency"]),
        lane("dependency", ["src/dependency/**"]),
    ]
    parallel["integration_order"] = ["dependent", "dependency"]
    errors = routing.validate_packet(packet, live_state=live_state(), policy=policy())
    assert "integration_order must place dependencies before dependents" in errors


def test_structured_leases_reject_multiple_holders_and_missing_release_condition() -> None:
    packet = default_packet()
    parallel = packet["parallel_execution"]
    assert isinstance(parallel, dict)
    first = lane("first", ["src/first/**"])
    second = lane("second", ["src/second/**"])
    first["shared_leases"] = [
        {"resource": "heavy-test-slot", "holder": "first", "release_condition": "merged"}
    ]
    second["shared_leases"] = [
        {"resource": "heavy-test-slot", "holder": "second", "release_condition": ""}
    ]
    parallel["lanes"] = [first, second]
    parallel["constrained_resources"] = ["heavy-test-slot"]
    parallel["integration_order"] = ["first", "second"]
    errors = routing.validate_packet(packet, live_state=live_state(), policy=policy())
    assert "lane 'second' shared_leases must contain structured leases" in errors
    assert "lease 'heavy-test-slot' holder must name exactly one lane" in errors


def test_cli_returns_zero_for_valid_packet_and_one_for_invalid_packet() -> None:
    script = Path(__file__).with_name("agent_execution_routing.py")
    with tempfile.TemporaryDirectory() as temporary_directory:
        directory = Path(temporary_directory)
        policy_path = directory / "policy.json"
        packet_path = directory / "packet.json"
        live_state_path = directory / "live-state.json"
        policy_path.write_text(json.dumps(policy()), encoding="utf-8")
        packet_path.write_text(json.dumps(default_packet()), encoding="utf-8")
        live_state_path.write_text(json.dumps(live_state()), encoding="utf-8")
        command = [
            sys.executable,
            str(script),
            "--policy",
            str(policy_path),
            "--packet",
            str(packet_path),
            "--live-state",
            str(live_state_path),
        ]
        assert subprocess.run(command, check=False, capture_output=True, text=True).returncode == 0

        invalid_packet = default_packet()
        invalid_execution = invalid_packet["execution_routing"]
        assert isinstance(invalid_execution, dict)
        invalid_execution["execution_target"] = "untrusted_host"
        packet_path.write_text(json.dumps(invalid_packet), encoding="utf-8")
        failed = subprocess.run(command, check=False, capture_output=True, text=True)
        assert failed.returncode == 1
        assert "execution_target is not allowed" in failed.stdout


def test_cli_enforces_lane_isolation_and_remote_desktop_action_scope() -> None:
    script = Path(__file__).with_name("agent_execution_routing.py")
    with tempfile.TemporaryDirectory() as temporary_directory:
        directory = Path(temporary_directory)
        policy_path = directory / "policy.json"
        packet_path = directory / "packet.json"
        live_state_path = directory / "live-state.json"
        policy_path.write_text(json.dumps(policy()), encoding="utf-8")
        live_state_path.write_text(json.dumps(live_state()), encoding="utf-8")
        command = [
            sys.executable,
            str(script),
            "--policy",
            str(policy_path),
            "--packet",
            str(packet_path),
            "--live-state",
            str(live_state_path),
        ]

        duplicate_worktree = default_packet()
        parallel = duplicate_worktree["parallel_execution"]
        assert isinstance(parallel, dict)
        first = lane("first", ["docs/first/**"])
        second = lane("second", ["src/second/**"])
        second["branch_and_worktree"] = first["branch_and_worktree"]
        parallel["lanes"] = [first, second]
        parallel["integration_order"] = ["first", "second"]
        packet_path.write_text(json.dumps(duplicate_worktree), encoding="utf-8")
        duplicate_result = subprocess.run(command, check=False, capture_output=True, text=True)
        assert duplicate_result.returncode == 1
        assert "parallel lanes cannot share branch_and_worktree" in duplicate_result.stdout

        missing_actions = exception_packet("host_only_service")
        missing_execution = missing_actions["execution_routing"]
        assert isinstance(missing_execution, dict)
        del missing_execution["requested_host_actions"]
        packet_path.write_text(json.dumps(missing_actions), encoding="utf-8")
        missing_result = subprocess.run(command, check=False, capture_output=True, text=True)
        assert missing_result.returncode == 1
        assert "remote_desktop exception requires non-empty requested_host_actions" in missing_result.stdout

        unrecognized_action = exception_packet("host_only_service")
        unrecognized_execution = unrecognized_action["execution_routing"]
        assert isinstance(unrecognized_execution, dict)
        unrecognized_execution["requested_host_actions"] = ["change_host_configuration"]
        packet_path.write_text(json.dumps(unrecognized_action), encoding="utf-8")
        unrecognized_result = subprocess.run(command, check=False, capture_output=True, text=True)
        assert unrecognized_result.returncode == 1
        assert "requested_host_actions must be a list of permitted host action strings" in unrecognized_result.stdout

        permitted_action = exception_packet("self_hosted_runner_diagnosis")
        packet_path.write_text(json.dumps(permitted_action), encoding="utf-8")
        permitted_result = subprocess.run(command, check=False, capture_output=True, text=True)
        assert permitted_result.returncode == 0


def test_cli_rejects_partial_and_long_wildcard_segments() -> None:
    script = Path(__file__).with_name("agent_execution_routing.py")
    with tempfile.TemporaryDirectory() as temporary_directory:
        directory = Path(temporary_directory)
        policy_path = directory / "policy.json"
        packet_path = directory / "packet.json"
        live_state_path = directory / "live-state.json"
        policy_path.write_text(json.dumps(policy()), encoding="utf-8")
        live_state_path.write_text(json.dumps(live_state()), encoding="utf-8")
        command = [
            sys.executable,
            str(script),
            "--policy", str(policy_path),
            "--packet", str(packet_path),
            "--live-state", str(live_state_path),
        ]
        for path, concrete in (
            ("src/a*.py", "src/ab.py"),
            ("src/foo**bar.py", "src/fooxbar.py"),
            ("src/***", "src/aZZ.py"),
            ("src/****", "src/aZZ.py"),
        ):
            packet = default_packet()
            parallel = packet["parallel_execution"]
            assert isinstance(parallel, dict)
            parallel["lanes"] = [lane("invalid", [path]), lane("specific", [concrete])]
            parallel["integration_order"] = ["invalid", "specific"]
            packet_path.write_text(json.dumps(packet), encoding="utf-8")
            result = subprocess.run(command, check=False, capture_output=True, text=True)
            assert result.returncode == 1
            assert "owned_paths must use only '*' and '**' wildcards" in result.stdout


def test_cli_returns_policy_error_for_non_string_closed_enum() -> None:
    script = Path(__file__).with_name("agent_execution_routing.py")
    with tempfile.TemporaryDirectory() as temporary_directory:
        directory = Path(temporary_directory)
        policy_path = directory / "policy.json"
        packet_path = directory / "packet.json"
        live_state_path = directory / "live-state.json"
        invalid_packet = default_packet()
        execution = invalid_packet["execution_routing"]
        assert isinstance(execution, dict)
        execution["execution_target"] = []
        policy_path.write_text(json.dumps(policy()), encoding="utf-8")
        packet_path.write_text(json.dumps(invalid_packet), encoding="utf-8")
        live_state_path.write_text(json.dumps(live_state()), encoding="utf-8")
        failed = subprocess.run(
            [
                sys.executable,
                str(script),
                "--policy",
                str(policy_path),
                "--packet",
                str(packet_path),
                "--live-state",
                str(live_state_path),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        assert failed.returncode == 1
        assert "execution_target is not allowed" in failed.stdout
        assert "Traceback" not in failed.stderr


def test_cli_rejects_invalid_preflight_identity() -> None:
    script = Path(__file__).with_name("agent_execution_routing.py")
    with tempfile.TemporaryDirectory() as temporary_directory:
        directory = Path(temporary_directory)
        policy_path = directory / "policy.json"
        packet_path = directory / "packet.json"
        live_state_path = directory / "live-state.json"
        invalid_packet = default_packet()
        execution = invalid_packet["execution_routing"]
        assert isinstance(execution, dict)
        packet_preflight = execution["github_preflight"]
        assert isinstance(packet_preflight, dict)
        packet_preflight["task_head_sha"] = None
        invalid_live_state = live_state()
        invalid_live_state["task_head_sha"] = None
        policy_path.write_text(json.dumps(policy()), encoding="utf-8")
        packet_path.write_text(json.dumps(invalid_packet), encoding="utf-8")
        live_state_path.write_text(json.dumps(invalid_live_state), encoding="utf-8")
        failed = subprocess.run(
            [
                sys.executable,
                str(script),
                "--policy",
                str(policy_path),
                "--packet",
                str(packet_path),
                "--live-state",
                str(live_state_path),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        assert failed.returncode == 1
        assert "github_preflight.task_head_sha has invalid identity" in failed.stdout
        assert "live_state.task_head_sha has invalid identity" in failed.stdout
        assert "Traceback" not in failed.stderr


def test_cli_rejects_malformed_required_fields_policy_with_null_identities() -> None:
    script = Path(__file__).with_name("agent_execution_routing.py")
    with tempfile.TemporaryDirectory() as temporary_directory:
        directory = Path(temporary_directory)
        policy_path = directory / "policy.json"
        packet_path = directory / "packet.json"
        live_state_path = directory / "live-state.json"
        packet = default_packet()
        execution = packet["execution_routing"]
        assert isinstance(execution, dict)
        packet_preflight = execution["github_preflight"]
        assert isinstance(packet_preflight, dict)
        packet_preflight.update({"repository": None, "default_branch_sha": None, "governing_issue": None, "pull_request": None, "task_head_sha": None})
        current_live_state = live_state()
        current_live_state.update({"repository": None, "default_branch_sha": None, "governing_issue": None, "pull_request": None, "task_head_sha": None})
        malformed_policy = policy()
        malformed_policy["resume_preflight_required_fields"] = ["verified_at"]
        policy_path.write_text(json.dumps(malformed_policy), encoding="utf-8")
        packet_path.write_text(json.dumps(packet), encoding="utf-8")
        live_state_path.write_text(json.dumps(current_live_state), encoding="utf-8")
        failed = subprocess.run(
            [sys.executable, str(script), "--policy", str(policy_path), "--packet", str(packet_path), "--live-state", str(live_state_path)],
            check=False,
            capture_output=True,
            text=True,
        )
        assert failed.returncode == 1
        assert "policy resume_preflight_required_fields must be the exact canonical list of unique required identities" in failed.stdout
        assert "Traceback" not in failed.stderr


def test_cli_rejects_timestamp_and_policy_matrix_bypasses() -> None:
    script = Path(__file__).with_name("agent_execution_routing.py")
    with tempfile.TemporaryDirectory() as temporary_directory:
        directory = Path(temporary_directory)
        policy_path = directory / "policy.json"
        packet_path = directory / "packet.json"
        live_state_path = directory / "live-state.json"
        command = [
            sys.executable,
            str(script),
            "--policy",
            str(policy_path),
            "--packet",
            str(packet_path),
            "--live-state",
            str(live_state_path),
        ]

        def assert_rejected(
            packet: dict[str, object], current_live_state: dict[str, object], current_policy: dict[str, object], error: str
        ) -> None:
            policy_path.write_text(json.dumps(current_policy), encoding="utf-8")
            packet_path.write_text(json.dumps(packet), encoding="utf-8")
            live_state_path.write_text(json.dumps(current_live_state), encoding="utf-8")
            result = subprocess.run(command, check=False, capture_output=True, text=True)
            assert result.returncode == 1
            assert error in result.stdout
            assert "Traceback" not in result.stderr

        malformed_packet = default_packet()
        execution = malformed_packet["execution_routing"]
        assert isinstance(execution, dict)
        preflight_data = execution["github_preflight"]
        assert isinstance(preflight_data, dict)
        preflight_data["verified_at"] = "2026-08-26T12:00:00+00:00"
        assert_rejected(
            malformed_packet,
            live_state(),
            policy(),
            "github_preflight.verified_at has invalid UTC RFC3339 timestamp",
        )

        stale_packet = default_packet()
        execution = stale_packet["execution_routing"]
        assert isinstance(execution, dict)
        preflight_data = execution["github_preflight"]
        assert isinstance(preflight_data, dict)
        preflight_data["verified_at"] = "2026-08-26T11:49:59Z"
        assert_rejected(
            stale_packet,
            live_state(),
            policy(),
            "github_preflight.verified_at exceeds policy freshness limit",
        )

        missing_evaluation_time = live_state()
        del missing_evaluation_time["evaluated_at"]
        assert_rejected(
            default_packet(),
            missing_evaluation_time,
            policy(),
            "live_state missing evaluation timestamp: evaluated_at",
        )

        malformed_policy = policy()
        matrix = malformed_policy["target_runner_compatibility"]
        assert isinstance(matrix, dict)
        matrix["github_actions"] = "github_hosted"
        assert_rejected(
            default_packet(),
            live_state(),
            malformed_policy,
            "policy target_runner_compatibility.github_actions must be a non-empty list of runner classes",
        )


def test_cli_rejects_fail_open_execution_routing_bypasses() -> None:
    script = Path(__file__).with_name("agent_execution_routing.py")
    with tempfile.TemporaryDirectory() as temporary_directory:
        directory = Path(temporary_directory)
        policy_path = directory / "policy.json"
        packet_path = directory / "packet.json"
        live_state_path = directory / "live-state.json"
        policy_path.write_text(json.dumps(policy()), encoding="utf-8")
        live_state_path.write_text(json.dumps(live_state()), encoding="utf-8")
        command = [
            sys.executable,
            str(script),
            "--policy",
            str(policy_path),
            "--packet",
            str(packet_path),
            "--live-state",
            str(live_state_path),
        ]

        def assert_rejected(packet: dict[str, object], expected_error: str) -> str:
            packet_path.write_text(json.dumps(packet), encoding="utf-8")
            result = subprocess.run(command, check=False, capture_output=True, text=True)
            assert result.returncode == 1
            assert expected_error in result.stdout
            assert "Traceback" not in result.stderr
            return result.stdout

        for invalid_equivalent_ci in ([], {}, "", False, 0):
            packet = exception_packet("lan_or_hardware")
            execution = packet["execution_routing"]
            assert isinstance(execution, dict)
            execution["equivalent_ci"] = invalid_equivalent_ci
            assert_rejected(packet, "equivalent_ci must be null or a non-empty workflow identifier string")

        packet = default_packet()
        execution = packet["execution_routing"]
        assert isinstance(execution, dict)
        execution["equivalent_ci"] = None
        execution["requested_host_actions"] = ["poll_docker_logs"]
        assert_rejected(packet, "requested_host_actions require remote_desktop=exception")

        packet = default_packet()
        parallel = packet["parallel_execution"]
        assert isinstance(parallel, dict)
        parallel["lanes"] = []
        parallel["integration_order"] = []
        assert_rejected(packet, "single_agent requires exactly one lane")

        packet = default_packet()
        parallel = packet["parallel_execution"]
        assert isinstance(parallel, dict)
        parallel["constrained_resources"] = "heavy-test-slot"
        assert_rejected(packet, "constrained_resources must be a list of non-empty strings")

        packet = default_packet()
        parallel = packet["parallel_execution"]
        assert isinstance(parallel, dict)
        parallel["lanes"] = [lane("policy", ["docs/agents/**", 7])]
        assert_rejected(packet, "owned_paths must be a list of non-empty safe repository-relative strings")

        for unsupported_glob in (
            "src/?.py",
            "src/[ab].py",
            "src/{a,b}.py",
            "src/!(a).py",
            "src/@(a).py",
            "src/+(a).py",
            "src/?(a).py",
            "src/*(a).py",
        ):
            packet = default_packet()
            parallel = packet["parallel_execution"]
            assert isinstance(parallel, dict)
            parallel["lanes"] = [lane("glob", [unsupported_glob]), lane("specific", ["src/a.py"])]
            parallel["integration_order"] = ["glob", "specific"]
            assert_rejected(packet, "owned_paths must use only '*' and '**' wildcards")

        packet = default_packet()
        parallel = packet["parallel_execution"]
        assert isinstance(parallel, dict)
        parallel["lanes"] = [
            lane("all", ["**"]),
            lane("specific", ["src/a.py"]),
        ]
        parallel["integration_order"] = ["all", "specific"]
        assert_rejected(packet, "parallel lanes have overlapping owned_paths")


if __name__ == "__main__":
    failures = []
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            try:
                test()
            except Exception as exc:  # pragma: no cover - command-line harness
                failures.append((name, exc))
                print(f"FAIL {name}: {exc}")
    if failures:
        raise SystemExit(f"{len(failures)} test(s) failed")
    print("PASS agent execution routing tests")