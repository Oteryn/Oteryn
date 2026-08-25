import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class AiReviewRecheckWorkflowTests(unittest.TestCase):
    def test_review_evidence_recheck_is_same_head_and_non_mutating(self):
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
        self.assertIn("pull_request_target", workflow)
        self.assertIn("governance-ai-review.yml", workflow)
        self.assertIn("chatgpt-codex-connector[bot]", workflow)


if __name__ == "__main__":
    unittest.main()
