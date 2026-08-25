import ast
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.agents.execution_guard import evaluate_snapshot

HEAD = "a" * 40
MAIN1 = "b" * 40
MAIN2 = "c" * 40


def snap(**overrides):
    value = {
        "schema_version": 1,
        "repository": "Oteryn/Oteryn",
        "pr_number": 73,
        "task_head_sha": HEAD,
        "integration_main_sha": MAIN1,
        "candidate_frozen": True,
        "candidate_head_sha": HEAD,
        "current_action": "verify_external_review",
        "waiting_reason": "external_review_evidence",
        "failure_code": "evidence_absent",
        "previous_progress_fingerprint": "",
        "identical_cycle_count": 0,
        "retry_count": 0,
        "retry_limit": 0,
        "external_event_can_change": True,
        "material_repository_change": False,
        "terminal_verified": False,
        "blocked": False,
        "noop_retrigger_intent": False,
    }
    value.update(overrides)
    return value


class ExecutionGuardTests(unittest.TestCase):
    def test_frozen_external_review_absence_waits_without_retry(self):
        result = evaluate_snapshot(snap())
        self.assertEqual(result["decision"], "WAIT")
        self.assertEqual(result["next_state"], "WAITING_EXTERNAL")

    def test_identical_failure_past_budget_stalls(self):
        first = evaluate_snapshot(snap(current_action="run_ci", waiting_reason="", failure_code="unit_failure", external_event_can_change=False, retry_limit=1))
        second = evaluate_snapshot(snap(current_action="run_ci", waiting_reason="", failure_code="unit_failure", external_event_can_change=False, retry_limit=1, retry_count=1, identical_cycle_count=2, previous_progress_fingerprint=first["progress_fingerprint"]))
        self.assertEqual(second["decision"], "STALL")
        self.assertEqual(second["next_state"], "STALLED")

    def test_material_change_allows_continue(self):
        result = evaluate_snapshot(snap(current_action="run_ci", waiting_reason="", failure_code="unit_failure", external_event_can_change=False, retry_limit=1, retry_count=1, identical_cycle_count=5, material_repository_change=True))
        self.assertEqual(result["decision"], "CONTINUE")

    def test_dependency_pending_waits_immediately(self):
        result = evaluate_snapshot(snap(current_action="check_dependency", waiting_reason="dependency_pending", failure_code="", external_event_can_change=True))
        self.assertEqual(result["decision"], "WAIT")

    def test_distinct_integration_main_allows_refresh(self):
        old = evaluate_snapshot(snap(current_action="integrate_main", waiting_reason="", failure_code="base_advanced", external_event_can_change=False, retry_limit=1))
        new = evaluate_snapshot(snap(current_action="integrate_main", integration_main_sha=MAIN2, waiting_reason="", failure_code="base_advanced", external_event_can_change=False, retry_limit=1, previous_progress_fingerprint=old["progress_fingerprint"], identical_cycle_count=3))
        self.assertEqual(new["decision"], "CONTINUE")

    def test_noop_retrigger_is_blocked(self):
        result = evaluate_snapshot(snap(noop_retrigger_intent=True))
        self.assertEqual(result["decision"], "BLOCK")
        self.assertEqual(result["next_state"], "BLOCKED")

    def test_noop_retrigger_precedes_terminal_done(self):
        result = evaluate_snapshot(snap(terminal_verified=True, noop_retrigger_intent=True, waiting_reason="", failure_code=""))
        self.assertEqual(result["decision"], "BLOCK")
        self.assertEqual(result["next_state"], "BLOCKED")

    def test_terminal_verified_is_done(self):
        result = evaluate_snapshot(snap(terminal_verified=True, waiting_reason="", failure_code=""))
        self.assertEqual(result["decision"], "DONE")

    def test_frozen_head_mismatch_is_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_snapshot(snap(candidate_head_sha="d" * 40))

    def test_cli_reads_json_file(self):
        root = Path(__file__).resolve().parents[2]
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as handle:
            json.dump(snap(), handle)
            path = handle.name
        proc = subprocess.run([sys.executable, str(root / "tools/agents/execution_guard.py"), "--input", path], cwd=root, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["decision"], "WAIT")

    def test_cli_reads_stdin(self):
        root = Path(__file__).resolve().parents[2]
        proc = subprocess.run(
            [sys.executable, str(root / "tools/agents/execution_guard.py")],
            cwd=root,
            input=json.dumps(snap()),
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["next_state"], "WAITING_EXTERNAL")

    def test_cli_invalid_schema_is_fail_closed(self):
        root = Path(__file__).resolve().parents[2]
        proc = subprocess.run(
            [sys.executable, str(root / "tools/agents/execution_guard.py")],
            cwd=root,
            input=json.dumps({"schema_version": 1}),
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("snapshot fields mismatch", proc.stderr)

    def test_guard_has_no_network_or_mutating_file_calls(self):
        root = Path(__file__).resolve().parents[2]
        source = (root / "tools/agents/execution_guard.py").read_text(encoding="utf-8-sig")
        tree = ast.parse(source)
        forbidden_import_roots = {"http", "requests", "socket", "urllib"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                self.assertTrue(all(alias.name.split(".", 1)[0] not in forbidden_import_roots for alias in node.names))
            elif isinstance(node, ast.ImportFrom):
                self.assertNotIn((node.module or "").split(".", 1)[0], forbidden_import_roots)
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                self.assertNotIn(node.func.attr, {"write_text", "write_bytes", "unlink", "rename", "replace", "mkdir", "touch"})


if __name__ == "__main__":
    unittest.main()
