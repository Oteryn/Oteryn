#!/usr/bin/env python3
"""Focused behavior tests for Remote Desktop authorization and provider policy adoption."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("agent_execution_routing.py")
SPEC = importlib.util.spec_from_file_location("agent_execution_routing", MODULE_PATH)
assert SPEC and SPEC.loader
routing = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(routing)

CALL_GATE_PATH = Path(__file__).with_name("remote_desktop_call_gate.py")
CALL_GATE_SPEC = importlib.util.spec_from_file_location("remote_desktop_call_gate", CALL_GATE_PATH)
assert CALL_GATE_SPEC and CALL_GATE_SPEC.loader
call_gate = importlib.util.module_from_spec(CALL_GATE_SPEC)
CALL_GATE_SPEC.loader.exec_module(call_gate)

ADOPTION_PATH = Path(__file__).with_name("provider_policy_adoption.py")
ADOPTION_SPEC = importlib.util.spec_from_file_location("provider_policy_adoption", ADOPTION_PATH)
assert ADOPTION_SPEC and ADOPTION_SPEC.loader
adoption = importlib.util.module_from_spec(ADOPTION_SPEC)
ADOPTION_SPEC.loader.exec_module(adoption)

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
            "effort": "medium",
            "lane_strategy": "single_agent",
            "decision_basis": "RDC authorization uses one shared policy fixture",
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
    tool = tools.get(reason, "Remote_Desktop_Commander.get_config")
    execution.update(
        {
            "execution_target": "host_exception",
            "runner_class": "not_applicable",
            "remote_desktop": "exception",
            "remote_desktop_reason": reason,
            "equivalent_ci": None,
            "requested_host_actions": [actions.get(reason, "inspect_host_only_service")],
            "requested_remote_desktop_tools": [tool],
            "requested_remote_desktop_calls": [{"tool": tool, "arguments": {}}],
        }
    )
    return packet


def start_process_exception_packet() -> dict[str, object]:
    packet = exception_packet("self_hosted_runner_diagnosis")
    execution = packet["execution_routing"]
    assert isinstance(execution, dict)
    tool = "Remote_Desktop_Commander.start_process"
    execution["requested_remote_desktop_tools"] = [tool]
    execution["requested_remote_desktop_calls"] = [
        {
            "tool": tool,
            "arguments": {"command": "docker ps --format {{.ID}}", "timeout_ms": 5000},
        }
    ]
    return packet


def test_policy_has_exact_reason_action_mapping() -> None:
    assert policy()["remote_desktop_reason_action_compatibility"] == {
        "host_only_service": ["inspect_host_only_service"],
        "lan_or_hardware": ["perform_lan_or_hardware_acceptance"],
        "self_hosted_runner_diagnosis": ["diagnose_self_hosted_runner"],
    }


def test_policy_schema_version_must_be_exactly_two() -> None:
    for invalid_version in (None, 1, 3, "2"):
        malformed = policy()
        if invalid_version is None:
            del malformed["schema_version"]
        else:
            malformed["schema_version"] = invalid_version
        errors = routing.validate_packet(default_packet(), live_state=live_state(), policy=malformed)
        assert "policy schema_version must be 2" in errors


def test_call_gate_schema_version_rejects_json_boolean() -> None:
    malformed = policy()
    config = malformed["remote_desktop_call_gate"]
    assert isinstance(config, dict)
    config["schema_version"] = True
    errors = call_gate.validate_remote_desktop_call(
        "diagnose_self_hosted_runner",
        "Remote_Desktop_Commander.start_process",
        {"command": "docker ps --format {{.ID}}", "timeout_ms": 5000},
        packet=start_process_exception_packet(),
        live_state=live_state(),
        policy=malformed,
    )
    assert "policy remote_desktop_call_gate.schema_version must be 1" in errors


def test_canonical_instructions_gate_every_direct_remote_desktop_call() -> None:
    agents_text = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    contract_text = (
        REPO_ROOT / "docs" / "agents" / "contracts" / "AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md"
    ).read_text(encoding="utf-8")
    for text in (agents_text, contract_text):
        assert "every direct `Remote_Desktop_Commander.*` invocation" in text
        assert "local connector/tool registration" in text
        assert "positive per-call" in text
        assert "must not invoke `Remote_Desktop_Commander.list_devices`" in text
        assert "A Remote Desktop `DENY` is not automatically a blocker" in text
        assert "validate_remote_desktop_call" in text
        assert "exact call arguments" in text


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


def test_malformed_direct_call_identifiers_fail_closed() -> None:
    packet = exception_packet("lan_or_hardware")
    for malformed_tool in (None, [], {}, 7):
        errors = routing.validate_remote_desktop_action(
            "perform_lan_or_hardware_acceptance",
            malformed_tool,
            packet=packet,
            live_state=live_state(),
            policy=policy(),
        )
        assert errors == ["remote desktop tool identifier is invalid"]
    for malformed_action in (None, [], {}, 7):
        errors = routing.validate_remote_desktop_action(
            malformed_action,
            "Remote_Desktop_Commander.ping",
            packet=packet,
            live_state=live_state(),
            policy=policy(),
        )
        assert errors == ["host action identifier is invalid"]


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


def test_exact_call_arguments_are_required_for_remote_desktop() -> None:
    packet = start_process_exception_packet()
    assert call_gate.validate_remote_desktop_call(
        "diagnose_self_hosted_runner",
        "Remote_Desktop_Commander.start_process",
        {"command": "docker ps --format {{.ID}}", "timeout_ms": 5000},
        packet=packet,
        live_state=live_state(),
        policy=policy(),
    ) == []
    errors = call_gate.validate_remote_desktop_call(
        "diagnose_self_hosted_runner",
        "Remote_Desktop_Commander.start_process",
        {"command": "docker rm -f production", "timeout_ms": 5000},
        packet=packet,
        live_state=live_state(),
        policy=policy(),
    )
    assert errors == ["remote desktop call arguments do not match routing packet"]


def test_device_id_is_bound_to_exact_call() -> None:
    packet = exception_packet("lan_or_hardware")
    execution = packet["execution_routing"]
    assert isinstance(execution, dict)
    execution["requested_remote_desktop_calls"] = [
        {
            "tool": "Remote_Desktop_Commander.ping",
            "arguments": {"deviceId": "approved-host"},
        }
    ]
    assert call_gate.validate_remote_desktop_call(
        "perform_lan_or_hardware_acceptance",
        "Remote_Desktop_Commander.ping",
        {"deviceId": "approved-host"},
        packet=packet,
        live_state=live_state(),
        policy=policy(),
    ) == []
    errors = call_gate.validate_remote_desktop_call(
        "perform_lan_or_hardware_acceptance",
        "Remote_Desktop_Commander.ping",
        {"deviceId": "other-host"},
        packet=packet,
        live_state=live_state(),
        policy=policy(),
    )
    assert errors == ["remote desktop call arguments do not match routing packet"]


def test_provider_policy_adoption_rejects_historical_parallel_first_contract() -> None:
    stale = (
        "Resolve `docs/agents/META_AGENT_POLICY_BINDING.json` before material mutation. "
        "The local authority is ecosystem/agent-execution-routing-policy.json. "
        "A substantial task packet must plan parallel-first. Serial work requires an explicit reason."
    )
    errors = adoption.validate_provider_agents_text("Oteryn/Oteryn-Game", stale)
    assert "parallel-first execution wording is forbidden" in errors
    assert "provider overlay must not directly redefine META machine modules" in errors


def test_provider_policy_adoption_rejects_direct_meta_module_contract() -> None:
    stale = (
        "Resolve `docs/agents/META_AGENT_POLICY_BINDING.json` before material mutation. "
        "The current protected META execution policy is ecosystem/agent-execution-routing-policy.json. "
        "Use `single_agent` by default and `parallel_when_beneficial` when useful."
    )
    errors = adoption.validate_provider_agents_text("Oteryn/Oteryn-Platform", stale)
    assert "provider overlay must not directly redefine META machine modules" in errors


def test_provider_policy_adoption_accepts_central_binding_overlay() -> None:
    current = (
        "# Atlas agent instructions\n\n"
        "Resolve `docs/agents/META_AGENT_POLICY_BINDING.json` before material mutation.\n\n"
        "## Domain invariants\n"
        "Projection, provenance, rendering and deployment-revision constraints remain Atlas-owned.\n"
    )
    assert adoption.validate_provider_agents_text("Oteryn/Oteryn-Atlas", current) == []


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