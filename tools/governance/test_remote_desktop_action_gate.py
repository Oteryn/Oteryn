#!/usr/bin/env python3
"""Focused behavior tests for the Remote Desktop per-action authorization gate."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("agent_execution_routing.py")
SPEC = importlib.util.spec_from_file_location("agent_execution_routing", MODULE_PATH)
assert SPEC and SPEC.loader
routing = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(routing)

REPO_ROOT = Path(__file__).parents[2]
REPO = "Oteryn/Oteryn"
SHA = "d79df968c1aba98373455399732fc71ab71e6a5d"
GOVERNING_ISSUE = 85
PULL_REQUEST = 87
TASK_HEAD_SHA = "f4cda70de8bc61008226c6be2983cff34600f86d"


def policy() -> dict[str, object]:
    path = REPO_ROOT / "ecosystem" / "agent-execution-routing-policy.json"
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


def lane() -> dict[str, object]:
    return {
        "id": "policy",
        "owned_paths": ["docs/agents/schemas/**"],
        "depends_on": [],
        "branch_and_worktree": "governance/policy:worktrees/policy",
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
            "lanes": [lane()],
            "integration_order": ["policy"],
        },
    }


def exception_packet(reason: str) -> dict[str, object]:
    packet = default_packet()
    execution = packet["execution_routing"]
    assert isinstance(execution, dict)
    actions = {
        "host_only_service": "inspect_host_only_service",
        "lan_or_hardware": "perform_lan_or_hardware_acceptance",
        "self_hosted_runner_diagnosis": "diagnose_self_hosted_runner",
    }
    tools = {
        "host_only_service": "Remote_Desktop_Commander.get_config",
        "lan_or_hardware": "Remote_Desktop_Commander.ping",
        "self_hosted_runner_diagnosis": "Remote_Desktop_Commander.list_processes",
    }
    execution.update(
        {
            "execution_target": "host_exception",
            "runner_class": "not_applicable",
            "remote_desktop": "exception",
            "remote_desktop_reason": reason,
            "equivalent_ci": None,
            "requested_host_actions": [actions.get(reason, "inspect_host_only_service")],
            "requested_remote_desktop_tools": [tools.get(reason, "Remote_Desktop_Commander.get_config")],
        }
    )
    return packet


def test_policy_has_exact_reason_action_mapping() -> None:
    assert policy()["remote_desktop_reason_action_compatibility"] == {
        "host_only_service": ["inspect_host_only_service"],
        "lan_or_hardware": ["perform_lan_or_hardware_acceptance"],
        "self_hosted_runner_diagnosis": ["diagnose_self_hosted_runner"],
    }


def test_canonical_instructions_gate_every_direct_remote_desktop_call() -> None:
    agents_text = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    contract_text = (
        REPO_ROOT / "docs" / "agents" / "contracts" / "AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md"
    ).read_text(encoding="utf-8")
    for text in (agents_text, contract_text):
        assert "every direct `Remote_Desktop_Commander.*` invocation" in text
        assert "local connector/tool registration" in text
        assert "positive per-action" in text
        assert "must not invoke `Remote_Desktop_Commander.list_devices`" in text
        assert "A Remote Desktop `DENY` is not automatically a blocker" in text


def test_exception_requires_remote_tool_declaration() -> None:
    packet = exception_packet("lan_or_hardware")
    execution = packet["execution_routing"]
    assert isinstance(execution, dict)
    del execution["requested_remote_desktop_tools"]
    errors = routing.validate_packet(packet, live_state=live_state(), policy=policy())
    assert "remote_desktop exception requires non-empty requested_remote_desktop_tools" in errors


def test_unknown_remote_tool_is_rejected_by_packet_validation() -> None:
    packet = exception_packet("lan_or_hardware")
    execution = packet["execution_routing"]
    assert isinstance(execution, dict)
    execution["requested_remote_desktop_tools"] = ["Remote_Desktop_Commander.future_unknown_tool"]
    errors = routing.validate_packet(packet, live_state=live_state(), policy=policy())
    assert "requested_remote_desktop_tools must contain only known permitted tool identifiers" in errors


def test_packet_rejects_action_incompatible_with_reason() -> None:
    packet = exception_packet("lan_or_hardware")
    execution = packet["execution_routing"]
    assert isinstance(execution, dict)
    execution["requested_host_actions"] = ["inspect_host_only_service"]
    errors = routing.validate_packet(packet, live_state=live_state(), policy=policy())
    assert "requested_host_actions are incompatible with remote_desktop_reason" in errors


def test_malformed_reason_action_mapping_fails_closed() -> None:
    malformed = policy()
    malformed["remote_desktop_reason_action_compatibility"] = {
        "host_only_service": ["perform_lan_or_hardware_acceptance"]
    }
    errors = routing.validate_packet(default_packet(), live_state=live_state(), policy=malformed)
    assert "policy remote_desktop_reason_action_compatibility must map every and only remote_desktop_reason" in errors


def test_policy_tool_sets_must_be_disjoint() -> None:
    malformed = policy()
    malformed["always_forbidden_remote_desktop_tools"] = ["Remote_Desktop_Commander.ping"]
    errors = routing.validate_packet(default_packet(), live_state=live_state(), policy=malformed)
    assert "policy Remote Desktop known and always-forbidden tool sets must be disjoint" in errors


def test_list_devices_without_exception_is_denied() -> None:
    errors = routing.validate_remote_desktop_action(
        "perform_lan_or_hardware_acceptance",
        "Remote_Desktop_Commander.list_devices",
        packet=default_packet(),
        live_state=live_state(),
        policy=policy(),
    )
    assert "remote desktop direct call requires validated host_exception" in errors


def test_metadata_like_calls_without_exception_are_denied() -> None:
    for host_action, tool in (
        ("inspect_host_only_service", "Remote_Desktop_Commander.get_config"),
        ("perform_lan_or_hardware_acceptance", "Remote_Desktop_Commander.who_am_i"),
        ("perform_lan_or_hardware_acceptance", "Remote_Desktop_Commander.ping"),
    ):
        errors = routing.validate_remote_desktop_action(
            host_action,
            tool,
            packet=default_packet(),
            live_state=live_state(),
            policy=policy(),
        )
        assert "remote desktop direct call requires validated host_exception" in errors


def test_filesystem_process_and_terminal_calls_without_exception_are_denied() -> None:
    for tool in (
        "Remote_Desktop_Commander.read_file",
        "Remote_Desktop_Commander.list_processes",
        "Remote_Desktop_Commander.start_process",
    ):
        errors = routing.validate_remote_desktop_action(
            "inspect_host_only_service",
            tool,
            packet=default_packet(),
            live_state=live_state(),
            policy=policy(),
        )
        assert "remote desktop direct call requires validated host_exception" in errors


def test_unknown_tool_fails_closed() -> None:
    errors = routing.validate_remote_desktop_action(
        "perform_lan_or_hardware_acceptance",
        "Remote_Desktop_Commander.future_unknown_tool",
        packet=exception_packet("lan_or_hardware"),
        live_state=live_state(),
        policy=policy(),
    )
    assert "remote desktop tool is not policy-known" in errors


def test_missing_packet_or_live_state_fails_closed() -> None:
    for packet_value, live_state_value in ((None, live_state()), (exception_packet("lan_or_hardware"), None)):
        errors = routing.validate_remote_desktop_action(
            "perform_lan_or_hardware_acceptance",
            "Remote_Desktop_Commander.ping",
            packet=packet_value,
            live_state=live_state_value,
            policy=policy(),
        )
        assert "remote desktop direct call requires current packet and live_state" in errors


def test_wrong_semantic_action_for_reason_is_denied() -> None:
    errors = routing.validate_remote_desktop_action(
        "inspect_host_only_service",
        "Remote_Desktop_Commander.ping",
        packet=exception_packet("lan_or_hardware"),
        live_state=live_state(),
        policy=policy(),
    )
    assert "host action is incompatible with remote_desktop_reason" in errors


def test_undeclared_tool_is_denied_even_when_exception_is_valid() -> None:
    errors = routing.validate_remote_desktop_action(
        "perform_lan_or_hardware_acceptance",
        "Remote_Desktop_Commander.list_devices",
        packet=exception_packet("lan_or_hardware"),
        live_state=live_state(),
        policy=policy(),
    )
    assert "remote desktop tool was not requested by the routing packet" in errors


def test_stale_preflight_denies_direct_call() -> None:
    packet = exception_packet("lan_or_hardware")
    execution = packet["execution_routing"]
    assert isinstance(execution, dict)
    packet_preflight = execution["github_preflight"]
    assert isinstance(packet_preflight, dict)
    packet_preflight["verified_at"] = "2026-08-26T11:49:59Z"
    errors = routing.validate_remote_desktop_action(
        "perform_lan_or_hardware_acceptance",
        "Remote_Desktop_Commander.ping",
        packet=packet,
        live_state=live_state(),
        policy=policy(),
    )
    assert "remote desktop direct call requires valid routing packet" in errors
    assert "github_preflight.verified_at exceeds policy freshness limit" in errors


def test_always_forbidden_tool_cannot_be_authorized() -> None:
    packet = exception_packet("lan_or_hardware")
    execution = packet["execution_routing"]
    assert isinstance(execution, dict)
    execution["requested_remote_desktop_tools"] = ["Remote_Desktop_Commander.shutdown"]
    errors = routing.validate_remote_desktop_action(
        "perform_lan_or_hardware_acceptance",
        "Remote_Desktop_Commander.shutdown",
        packet=packet,
        live_state=live_state(),
        policy=policy(),
    )
    assert "remote desktop tool is always forbidden by policy" in errors


def test_exact_reason_action_and_tool_is_allowed() -> None:
    assert routing.validate_remote_desktop_action(
        "perform_lan_or_hardware_acceptance",
        "Remote_Desktop_Commander.ping",
        packet=exception_packet("lan_or_hardware"),
        live_state=live_state(),
        policy=policy(),
    ) == []


if __name__ == "__main__":
    failures: list[tuple[str, Exception]] = []
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            try:
                test()
            except Exception as exc:  # pragma: no cover - command-line harness
                failures.append((name, exc))
                print(f"FAIL {name}: {exc}")
    if failures:
        raise SystemExit(f"{len(failures)} test(s) failed")
    print("PASS Remote Desktop per-action gate tests")
