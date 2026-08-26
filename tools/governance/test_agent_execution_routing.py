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


def policy() -> dict[str, object]:
    path = Path(__file__).parents[2] / "ecosystem" / "agent-execution-routing-policy.json"
    return json.loads(path.read_text(encoding="utf-8"))


def live_state() -> dict[str, object]:
    return {
        "verified_at": "2026-08-26T12:00:00Z",
        "repository": REPO,
        "default_branch": "main",
        "default_branch_sha": SHA,
        "governing_issue": 85,
        "pull_request": None,
        "task_head_sha": None,
    }


def preflight() -> dict[str, object]:
    return {
        "verified_at": "2026-08-26T12:00:00Z",
        "repository": REPO,
        "default_branch_sha": SHA,
        "governing_issue": 85,
        "pull_request": None,
        "task_head_sha": None,
    }


def lane(identifier: str, paths: list[str], *, depends_on: list[str] | None = None) -> dict[str, object]:
    return {
        "id": identifier,
        "owned_paths": paths,
        "depends_on": depends_on or [],
        "branch_and_worktree": "required",
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
            "lane_strategy": "parallel_first",
            "lanes": [lane("policy", ["docs/agents/schemas/**"])],
            "integration_order": ["policy"],
        },
    }


def exception_packet(reason: str) -> dict[str, object]:
    packet = default_packet()
    execution = packet["execution_routing"]
    assert isinstance(execution, dict)
    execution.update({"execution_target": "host_exception", "remote_desktop": "exception", "remote_desktop_reason": reason, "equivalent_ci": None})
    return packet


def test_default_actions_packet_passes() -> None:
    assert routing.validate_packet(default_packet(), live_state=live_state(), policy=policy()) == []


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


def test_multi_lane_task_requires_parallel_plan() -> None:
    packet = default_packet()
    parallel = packet["parallel_execution"]
    assert isinstance(parallel, dict)
    parallel["lanes"] = [lane("one", ["src/one/**"]), lane("two", ["src/two/**"])]
    parallel["lane_strategy"] = None
    assert "multi-lane task requires lane_strategy" in routing.validate_packet(packet, live_state=live_state(), policy=policy())


def test_overlapping_parallel_lanes_fail() -> None:
    packet = default_packet()
    parallel = packet["parallel_execution"]
    assert isinstance(parallel, dict)
    parallel["lanes"] = [
        lane("contract", ["docs/agents/contracts/**"]),
        lane("specific-file", ["docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md"]),
    ]
    assert "parallel lanes have overlapping owned_paths" in routing.validate_packet(packet, live_state=live_state(), policy=policy())


def test_unknown_lane_dependency_fails() -> None:
    packet = default_packet()
    parallel = packet["parallel_execution"]
    assert isinstance(parallel, dict)
    parallel["lanes"] = [lane("policy", ["docs/agents/schemas/**"], depends_on=["missing"])]
    assert "lane 'policy' depends_on unknown lane 'missing'" in routing.validate_packet(
        packet, live_state=live_state(), policy=policy()
    )


def test_serial_plan_requires_a_concrete_reason() -> None:
    packet = default_packet()
    parallel = packet["parallel_execution"]
    assert isinstance(parallel, dict)
    parallel["lane_strategy"] = "serial_with_reason"
    assert "serial_with_reason requires serial_reason" in routing.validate_packet(
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
    assert "requested_host_actions must be a list of supported action strings" in errors
    assert "equivalent_ci prohibits RDC polling" in errors

    for malformed_actions in ({"action": "poll_docker_logs"}, ["poll_docker_logs", {}], ["unknown_action"]):
        packet = default_packet()
        execution = packet["execution_routing"]
        assert isinstance(execution, dict)
        execution["requested_host_actions"] = malformed_actions
        errors = routing.validate_packet(packet, live_state=live_state(), policy=policy())
        assert "requested_host_actions must be a list of supported action strings" in errors


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
