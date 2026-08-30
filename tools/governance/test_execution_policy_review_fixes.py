#!/usr/bin/env python3
"""Focused regressions for review findings on execution-policy convergence."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rdc = _load(ROOT / "tools/governance/test_remote_desktop_action_gate.py", "rdc_fixtures")
execution_guard = _load(ROOT / "tools/agents/execution_guard.py", "execution_guard_review_fixes")


def _healthy_snapshot() -> dict[str, object]:
    return {
        "schema_version": 1,
        "repository": "Oteryn/Oteryn",
        "pr_number": 107,
        "task_head_sha": "a" * 40,
        "integration_main_sha": "",
        "candidate_frozen": False,
        "candidate_head_sha": "",
        "current_action": "implement",
        "waiting_reason": "",
        "failure_code": "",
        "previous_progress_fingerprint": "",
        "identical_cycle_count": 0,
        "retry_count": 0,
        "retry_limit": 0,
        "external_event_can_change": False,
        "material_repository_change": False,
        "terminal_verified": False,
        "blocked": False,
        "noop_retrigger_intent": False,
    }


def test_call_gate_validates_declarations_after_matching_entry() -> None:
    packet = rdc.start_process_exception_packet()
    execution = packet["execution_routing"]
    assert isinstance(execution, dict)
    declarations = execution["requested_remote_desktop_calls"]
    assert isinstance(declarations, list)
    declarations.append(
        {
            "tool": "Remote_Desktop_Commander.start_process",
            "arguments": [],
        }
    )
    errors = rdc.call_gate.validate_remote_desktop_call(
        "diagnose_self_hosted_runner",
        "Remote_Desktop_Commander.start_process",
        {"command": "docker ps --format {{.ID}}", "timeout_ms": 5000},
        packet=packet,
        live_state=rdc.live_state(),
        policy=rdc.policy(),
    )
    assert errors == ["requested_remote_desktop_calls contains an invalid declaration"]


def test_call_gate_rejects_duplicate_after_matching_entry() -> None:
    packet = rdc.start_process_exception_packet()
    execution = packet["execution_routing"]
    assert isinstance(execution, dict)
    declarations = execution["requested_remote_desktop_calls"]
    assert isinstance(declarations, list)
    first = declarations[0]
    assert isinstance(first, dict)
    declarations.append({"tool": first["tool"], "arguments": dict(first["arguments"])})
    errors = rdc.call_gate.validate_remote_desktop_call(
        "diagnose_self_hosted_runner",
        "Remote_Desktop_Commander.start_process",
        {"command": "docker ps --format {{.ID}}", "timeout_ms": 5000},
        packet=packet,
        live_state=rdc.live_state(),
        policy=rdc.policy(),
    )
    assert errors == ["requested_remote_desktop_calls contains a duplicate declaration"]


def test_call_gate_preserves_json_boolean_vs_integer_types() -> None:
    packet = rdc.start_process_exception_packet()
    execution = packet["execution_routing"]
    assert isinstance(execution, dict)
    declarations = execution["requested_remote_desktop_calls"]
    assert isinstance(declarations, list) and isinstance(declarations[0], dict)
    declarations[0]["arguments"] = {
        "command": "docker ps --format {{.ID}}",
        "timeout_ms": True,
    }
    errors = rdc.call_gate.validate_remote_desktop_call(
        "diagnose_self_hosted_runner",
        "Remote_Desktop_Commander.start_process",
        {"command": "docker ps --format {{.ID}}", "timeout_ms": 1},
        packet=packet,
        live_state=rdc.live_state(),
        policy=rdc.policy(),
    )
    assert errors == ["remote desktop call arguments do not match routing packet"]


def test_retry_counters_reject_json_booleans() -> None:
    for key in ("identical_cycle_count", "retry_count", "retry_limit"):
        snapshot = _healthy_snapshot()
        snapshot[key] = True
        try:
            execution_guard.evaluate_snapshot(snapshot)
        except ValueError as exc:
            assert f"{key} must be a non-negative integer" in str(exc)
        else:
            raise AssertionError(f"{key}=true must fail closed")


def test_zero_retry_budget_does_not_stall_failure_free_initial_work() -> None:
    result = execution_guard.evaluate_snapshot(_healthy_snapshot())
    assert result["decision"] == "CONTINUE"
    assert result["next_state"] == "RUNNING"


def test_same_head_recheck_listens_for_final_codex_summary_edit() -> None:
    workflow = (ROOT / ".github/workflows/governance-ai-review-recheck.yml").read_text(encoding="utf-8")
    assert "issue_comment:\n    types: [created, edited]" in workflow


def main() -> int:
    tests = [
        value for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print(f"execution policy review-fix regressions PASS: {len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
