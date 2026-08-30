import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ai_review_recheck import process_event, select_rerun_run_id  # noqa: E402


POLICY = {
    "reviewer_source_logins": {
        "codex": ["chatgpt-codex-connector[bot]"],
        "codex_spark": ["chatgpt-codex-connector[bot]"],
    }
}

REPOSITORY = "Oteryn/Oteryn"
HEAD = "a" * 40
BASE = "b" * 40
PR_NUMBER = 69


def pr_payload(head=HEAD, base=BASE, repo=REPOSITORY, number=PR_NUMBER, state="open"):
    return {
        "number": number,
        "state": state,
        "head": {"sha": head, "repo": {"full_name": repo}},
        "base": {"sha": base, "ref": "main"},
    }


def review_event(actor="chatgpt-codex-connector[bot]", review_commit=HEAD):
    return {
        "sender": {"login": actor},
        "review": {"commit_id": review_commit},
        "pull_request": {"number": PR_NUMBER},
    }


def issue_comment_event(
    actor="chatgpt-codex-connector[bot]",
    *,
    reviewed_commit=HEAD[:10],
    include_reviewed_commit=True,
    extra_reviewed_commit=None,
):
    body = "Codex review result"
    if include_reviewed_commit:
        body += f"\n\n**Reviewed commit:** `{reviewed_commit}`"
    if extra_reviewed_commit is not None:
        body += f"\n\n**Reviewed commit:** `{extra_reviewed_commit}`"
    return {
        "sender": {"login": actor},
        "issue": {
            "number": PR_NUMBER,
            "pull_request": {
                "url": f"https://api.github.com/repos/Oteryn/Oteryn/pulls/{PR_NUMBER}"
            },
        },
        "comment": {"body": body},
    }


class FakeClient:
    def __init__(self, *, pr=None, runs=None, second_pr=None):
        self.pr = pr or pr_payload()
        self.second_pr = second_pr
        self.runs = list(runs or [])
        self.rerun_calls = []
        self.get_pr_calls = []
        self.list_gate_run_calls = []

    def get_pull_request(self, number):
        self.get_pr_calls.append(number)
        if self.second_pr is not None and len(self.get_pr_calls) > 1:
            return self.second_pr
        return self.pr

    def list_gate_runs(self, head_sha, base_sha, pr_number):
        self.list_gate_run_calls.append((head_sha, base_sha, pr_number))
        return list(self.runs)

    def rerun(self, run_id):
        self.rerun_calls.append(run_id)


def run_payload(
    run_id=100,
    *,
    head=HEAD,
    base=BASE,
    pr_number=PR_NUMBER,
    status="completed",
    conclusion="failure",
    attempt=1,
    created="2026-08-25T14:00:00Z",
):
    return {
        "id": run_id,
        "head_sha": base,
        "event": "pull_request_target",
        "status": status,
        "conclusion": conclusion,
        "run_attempt": attempt,
        "created_at": created,
        "pull_requests": [
            {
                "number": pr_number,
                "head": {"sha": head},
                "base": {"sha": base},
            }
        ],
    }


class SelectorTests(unittest.TestCase):
    def test_selects_latest_failed_attempt_one_for_exact_coordinates(self):
        runs = [
            run_payload(100, created="2026-08-25T13:00:00Z"),
            run_payload(101, created="2026-08-25T14:00:00Z"),
            run_payload(102, head="c" * 40, created="2026-08-25T15:00:00Z"),
        ]
        self.assertEqual(select_rerun_run_id(runs, HEAD, BASE, PR_NUMBER), 101)

    def test_same_head_run_for_other_pr_is_not_eligible(self):
        runs = [run_payload(200, pr_number=70)]
        self.assertIsNone(select_rerun_run_id(runs, HEAD, BASE, PR_NUMBER))

    def test_does_not_rerun_success_in_progress_or_attempt_two(self):
        for run in (
            run_payload(status="completed", conclusion="success"),
            run_payload(status="in_progress", conclusion=None),
            run_payload(status="completed", conclusion="failure", attempt=2),
        ):
            with self.subTest(run=run):
                self.assertIsNone(
                    select_rerun_run_id([run], HEAD, BASE, PR_NUMBER)
                )


class EventTests(unittest.TestCase):
    def test_untrusted_actor_is_noop(self):
        client = FakeClient(runs=[run_payload()])
        result = process_event(
            "pull_request_review",
            review_event(actor="random-user"),
            REPOSITORY,
            POLICY,
            client,
        )
        self.assertEqual(result.action, "NOOP_UNTRUSTED_ACTOR")
        self.assertEqual(client.rerun_calls, [])
        self.assertEqual(client.get_pr_calls, [])

    def test_trusted_review_for_current_exact_head_reruns_once(self):
        client = FakeClient(runs=[run_payload(123)])
        result = process_event(
            "pull_request_review",
            review_event(),
            REPOSITORY,
            POLICY,
            client,
        )
        self.assertEqual(result.action, "RERUN")
        self.assertEqual(result.run_id, 123)
        self.assertEqual(client.rerun_calls, [123])
        self.assertEqual(client.get_pr_calls, [PR_NUMBER, PR_NUMBER])
        self.assertEqual(client.list_gate_run_calls, [(HEAD, BASE, PR_NUMBER)])

    def test_stale_review_commit_does_not_rerun_current_head(self):
        client = FakeClient(runs=[run_payload(123)])
        result = process_event(
            "pull_request_review",
            review_event(review_commit="c" * 40),
            REPOSITORY,
            POLICY,
            client,
        )
        self.assertEqual(result.action, "NOOP_STALE_REVIEW")
        self.assertEqual(client.rerun_calls, [])

    def test_issue_comment_result_resolves_current_pr_then_reruns(self):
        client = FakeClient(runs=[run_payload(321)])
        result = process_event(
            "issue_comment",
            issue_comment_event(),
            REPOSITORY,
            POLICY,
            client,
        )
        self.assertEqual(result.action, "RERUN")
        self.assertEqual(client.get_pr_calls, [PR_NUMBER, PR_NUMBER])
        self.assertEqual(client.rerun_calls, [321])
        self.assertEqual(client.list_gate_run_calls, [(HEAD, BASE, PR_NUMBER)])

    def test_issue_comment_result_for_old_head_is_noop(self):
        client = FakeClient(runs=[run_payload(321)])
        result = process_event(
            "issue_comment",
            issue_comment_event(reviewed_commit=("c" * 40)[:10]),
            REPOSITORY,
            POLICY,
            client,
        )
        self.assertEqual(result.action, "NOOP_STALE_REVIEW")
        self.assertEqual(client.list_gate_run_calls, [])
        self.assertEqual(client.rerun_calls, [])

    def test_issue_comment_without_reviewed_commit_is_not_a_result(self):
        client = FakeClient(runs=[run_payload(321)])
        result = process_event(
            "issue_comment",
            issue_comment_event(include_reviewed_commit=False),
            REPOSITORY,
            POLICY,
            client,
        )
        self.assertEqual(result.action, "NOOP_NOT_REVIEW_RESULT")
        self.assertEqual(client.get_pr_calls, [])
        self.assertEqual(client.list_gate_run_calls, [])
        self.assertEqual(client.rerun_calls, [])

    def test_issue_comment_with_multiple_reviewed_commits_is_ambiguous(self):
        client = FakeClient(runs=[run_payload(321)])
        result = process_event(
            "issue_comment",
            issue_comment_event(extra_reviewed_commit=HEAD[:10]),
            REPOSITORY,
            POLICY,
            client,
        )
        self.assertEqual(result.action, "NOOP_AMBIGUOUS_REVIEW_RESULT")
        self.assertEqual(client.get_pr_calls, [])
        self.assertEqual(client.list_gate_run_calls, [])
        self.assertEqual(client.rerun_calls, [])

    def test_cross_repository_pr_fails_closed(self):
        client = FakeClient(pr=pr_payload(repo="Other/Repo"), runs=[run_payload()])
        with self.assertRaises(ValueError):
            process_event(
                "pull_request_review",
                review_event(),
                REPOSITORY,
                POLICY,
                client,
            )

    def test_pr_move_between_selection_and_rerun_is_noop(self):
        client = FakeClient(
            runs=[run_payload(123)],
            second_pr=pr_payload(head="c" * 40),
        )
        result = process_event(
            "pull_request_review",
            review_event(),
            REPOSITORY,
            POLICY,
            client,
        )
        self.assertEqual(result.action, "NOOP_PR_MOVED")
        self.assertEqual(client.rerun_calls, [])


class WorkflowSafetyTests(unittest.TestCase):
    def test_workflow_checks_out_trusted_base_not_event_sha(self):
        root = Path(__file__).resolve().parents[2]
        workflow = (
            root / ".github/workflows/governance-ai-review-recheck.yml"
        ).read_text(encoding="utf-8")
        self.assertNotIn("ref: ${{ github.sha }}", workflow)
        self.assertIn("github.event.pull_request.base.sha", workflow)
        self.assertIn("github.event.repository.default_branch", workflow)
        self.assertIn("actions: write", workflow)
        self.assertIn("contents: read", workflow)
        self.assertNotIn("contents: write", workflow)


if __name__ == "__main__":
    unittest.main()
