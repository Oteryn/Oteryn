import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class AiReviewRecheckWorkflowTests(unittest.TestCase):
    def test_review_evidence_recheck_is_same_head_non_mutating_and_paginated(self):
        workflow = (ROOT / ".github/workflows/governance-ai-review-recheck.yml").read_text(encoding="utf-8")
        self.assertIn("pull_request_review:", workflow)
        self.assertIn("issue_comment:", workflow)
        self.assertIn("actions: write", workflow)
        self.assertIn("contents: read", workflow)
        self.assertIn("pull-requests: read", workflow)
        self.assertNotIn("actions/checkout", workflow)
        self.assertNotIn("git commit", workflow)
        self.assertNotIn("git push", workflow)
        self.assertIn("/rerun", workflow)
        self.assertIn("head_sha", workflow)
        self.assertIn("live_base_sha", workflow)
        self.assertIn("linked_head", workflow)
        self.assertIn("linked_base", workflow)
        self.assertIn("current_base", workflow)
        self.assertNotIn('run.get("head_sha") != head_sha', workflow)
        self.assertIn("page = 1", workflow)
        self.assertIn("per_page=100&page={page}", workflow)
        self.assertIn("if len(batch) < 100:", workflow)
        self.assertIn("page += 1", workflow)
        self.assertIn("bounded 10000-run scan", workflow)
        self.assertIn("pull_request_target", workflow)
        self.assertIn("governance-ai-review.yml", workflow)
        self.assertIn("chatgpt-codex-connector[bot]", workflow)

    def test_execution_policy_review_fix_regressions(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools/governance/test_execution_policy_review_fixes.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
