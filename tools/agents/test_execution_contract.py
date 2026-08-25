import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

class ExecutionContractTests(unittest.TestCase):
    def test_central_contract_requires_bounded_wait_and_stall_states(self):
        text = (ROOT / "docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md").read_text(encoding="utf-8")
        for marker in ["WAITING_EXTERNAL", "STALLED", "candidate_frozen", "progress_fingerprint", "failure_fingerprint", "no-op/retrigger", "must end the active session"]:
            self.assertIn(marker, text)
        self.assertIn("EXECUTION_STATE_CONTRACT.json", text)
        self.assertIn("new or materially updated substantial task", text)

    def test_meta_gate_executes_bounded_execution_regressions(self):
        text = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertIn("python3 -m unittest tools.agents.test_execution_guard -v", text)
        self.assertIn("python3 -m unittest tools.agents.test_execution_contract -v", text)
        self.assertIn("python3 -m unittest tools.agents.test_execution_state -v", text)
        self.assertIn("python3 -m unittest tools.governance.test_ai_review_recheck_workflow -v", text)

    def test_root_bootstrap_forbids_trigger_commits_and_active_waiting(self):
        text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("no-op/retrigger commit", text)
        self.assertIn("WAITING_EXTERNAL", text)
        self.assertIn("must not remain active", text)

if __name__ == "__main__":
    unittest.main()
