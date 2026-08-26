#!/usr/bin/env python3
"""Behavior tests for the agent execution-routing contract.

The validator is deliberately imported from a sibling module so this file is
red until Task 2 supplies the implementation.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("agent_execution_routing.py")
SPEC = importlib.util.spec_from_file_location("agent_execution_routing", MODULE_PATH)
assert SPEC and SPEC.loader
routing = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(routing)

REPO = "Oteryn/Oteryn"
SHA = "d79df968c1aba98373455399732fc71ab71e6a5d"


def policy() -> dict[str, object]:
    path = Path(__file__).parents[2] / "docs" / "agents" / "schemas" / "agent_execution_routing.schema.json"
    return json.loads(path.read_text(encoding="utf-8"))


def live_state() -> dict[str, object]:
    return {
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


def test_equivalent_ci_forbids_rdc_polling() -> None:
    packet = exception_packet("self_hosted_runner_diagnosis")
    execution = packet["execution_routing"]
    assert isinstance(execution, dict)
    execution["equivalent_ci"] = ".github/workflows/ci.yml:meta-gate"
    execution["requested_host_actions"] = ["poll_docker_logs"]
    assert "equivalent_ci prohibits RDC polling" in routing.validate_packet(packet, live_state=live_state(), policy=policy())


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
