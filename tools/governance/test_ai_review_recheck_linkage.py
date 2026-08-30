import sys
import unittest
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ai_review_recheck import GitHubClient, select_rerun_run_id  # noqa: E402


HEAD = "a" * 40
BASE = "b" * 40
PR_NUMBER = 69


def linked_pr(number=PR_NUMBER, head=HEAD, base=BASE):
    return {
        "number": number,
        "head": {"sha": head},
        "base": {"sha": base},
    }


def run_payload(
    run_id=100,
    *,
    run_head=BASE,
    linked=None,
    status="completed",
    conclusion="failure",
    attempt=1,
    created="2026-08-30T07:00:00Z",
):
    return {
        "id": run_id,
        "head_sha": run_head,
        "event": "pull_request_target",
        "status": status,
        "conclusion": conclusion,
        "run_attempt": attempt,
        "created_at": created,
        "pull_requests": [linked or linked_pr()],
    }


class LinkedPullRequestSelectionTests(unittest.TestCase):
    def test_pull_request_target_run_binds_candidate_through_linked_pr(self):
        run = run_payload(run_head=BASE)
        self.assertEqual(
            select_rerun_run_id([run], HEAD, BASE, PR_NUMBER),
            100,
        )

    def test_wrong_linked_candidate_head_is_not_eligible(self):
        run = run_payload(linked=linked_pr(head="c" * 40))
        self.assertIsNone(select_rerun_run_id([run], HEAD, BASE, PR_NUMBER))

    def test_wrong_linked_base_is_not_eligible(self):
        run = run_payload(linked=linked_pr(base="c" * 40))
        self.assertIsNone(select_rerun_run_id([run], HEAD, BASE, PR_NUMBER))

    def test_same_head_run_for_other_pr_is_not_eligible(self):
        run = run_payload(linked=linked_pr(number=70))
        self.assertIsNone(select_rerun_run_id([run], HEAD, BASE, PR_NUMBER))


class PagingClient(GitHubClient):
    def __init__(self):
        super().__init__("Oteryn/Oteryn", "token")
        self.paths = []
        self.pages = {
            1: [run_payload(run_id=i, linked=linked_pr(number=1000 + i)) for i in range(1, 101)],
            2: [run_payload(run_id=777)],
        }

    def _request(self, path: str, *, method: str = "GET"):
        self.paths.append((path, method))
        if method != "GET":
            return None
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(path).query)
        page = int(query.get("page", ["1"])[0])
        return {"workflow_runs": self.pages.get(page, [])}


class PaginationTests(unittest.TestCase):
    def test_gate_run_discovery_paginates_without_candidate_head_query_filter(self):
        client = PagingClient()
        runs = client.list_gate_runs(HEAD, BASE, PR_NUMBER)
        self.assertEqual(select_rerun_run_id(runs, HEAD, BASE, PR_NUMBER), 777)
        paths = [path for path, _ in client.paths]
        self.assertTrue(any("page=1" in path for path in paths))
        self.assertTrue(any("page=2" in path for path in paths))
        self.assertTrue(all("head_sha=" not in path for path in paths))


class TrustedWorkflowBaseBindingTests(unittest.TestCase):
    def test_write_capable_workflow_is_never_loaded_from_pr_review_candidate_context(self):
        workflow = (
            Path(__file__).resolve().parents[2]
            / ".github"
            / "workflows"
            / "governance-ai-review-recheck.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("actions: write", workflow)
        self.assertNotIn("pull_request_review:", workflow)
        self.assertIn("issue_comment:", workflow)
        self.assertIn("id: live-pr", workflow)
        self.assertIn("/pulls/{pr_number}", workflow)
        self.assertIn("ref: ${{ steps.live-pr.outputs.base_sha }}", workflow)
        self.assertIn("EXPECTED_BASE_SHA: ${{ steps.live-pr.outputs.base_sha }}", workflow)
        self.assertIn("git rev-parse HEAD", workflow)
        self.assertIn('live_base_ref = str(((payload.get("base") or {}).get("ref")) or "")', workflow)
        self.assertIn('live_default_branch = str(repository_payload.get("default_branch") or "")', workflow)
        self.assertIn("live_base_ref != expected_base_ref or live_default_branch != expected_base_ref", workflow)
        self.assertLess(
            workflow.index("EXPECTED_BASE_SHA: ${{ steps.live-pr.outputs.base_sha }}"),
            workflow.index("python3 tools/governance/ai_review_recheck.py"),
        )


if __name__ == "__main__":
    unittest.main()
