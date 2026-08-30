import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class ExecutionContractTests(unittest.TestCase):
    def test_bounded_contract_is_canonical_meta_authority(self):
        policy_path = ROOT / "docs/agents/contracts/BOUNDED_AUTONOMOUS_EXECUTION_POLICY.md"
        machine_path = ROOT / "ecosystem/bounded-autonomous-execution-policy.json"

        self.assertTrue(
            machine_path.exists(),
            "bounded lifecycle authority is not canonical yet: merge/reconcile META #71 first",
        )
        text = policy_path.read_text(encoding="utf-8")
        machine = json.loads(machine_path.read_text(encoding="utf-8"))

        for marker in [
            "Lifecycle authority: `Oteryn/Oteryn#69`",
            "Machine-readable authority: `ecosystem/bounded-autonomous-execution-policy.json`",
            "WAITING_EXTERNAL",
            "STALLED",
            "candidate_frozen",
            "progress_fingerprint",
            "failure_fingerprint",
            "no-op/retrigger",
            "MaterialFactEnvelope",
            "reservation_required",
            "LOOP_BREAKER_AUDIT",
            "Canonical risk ledger",
            "same_head_gate_rechecks",
            "external_review_invocations",
        ]:
            self.assertIn(marker, text)

        self.assertEqual(machine.get("policy_id"), "oteryn-bounded-autonomous-execution-v1")
        self.assertIn("same_head_gate_rechecks", machine.get("retry_budgets", {}))
        self.assertIn("external_review_invocations", machine.get("retry_budgets", {}))
        self.assertIn("evidence_generation", machine.get("progress_fingerprint_fields", []))

    def test_meta_gate_executes_bounded_execution_regressions(self):
        text = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertIn("python3 -m unittest tools.agents.test_execution_guard -v", text)
        self.assertIn("python3 -m unittest tools.agents.test_execution_contract -v", text)
        self.assertIn("python3 -m unittest tools.agents.test_execution_state -v", text)
        self.assertIn("python3 -m unittest tools.governance.test_ai_review_recheck_workflow -v", text)

    def test_root_bootstrap_forbids_trigger_commits_and_active_waiting(self):
        text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("BOUNDED_AUTONOMOUS_EXECUTION_POLICY.md", text)
        self.assertIn("no-op/retrigger commit", text)
        self.assertIn("WAITING_EXTERNAL", text)
        self.assertIn("must release the active worker", text)


if __name__ == "__main__":
    unittest.main()
