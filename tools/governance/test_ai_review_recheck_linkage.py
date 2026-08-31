import copy
import json
import sys
import tempfile
import unittest
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ai_review_recheck import GitHubClient, process_event, select_rerun_run_id  # noqa: E402
from bounded_execution_guard import (  # noqa: E402
    ExecutionContext,
    GuardError,
    _checkpoint_digest,
    decide as raw_decide,
    make_material_fact_envelope,
    make_review_binding,
)
from bounded_execution_test_support import (  # noqa: E402
    TestEvidenceAuthority,
    decide as bounded_decide,
)
from durable_checkpoint_outbox import SqliteCheckpointOutbox  # noqa: E402
from test_ai_review_recheck import (  # noqa: E402
    FakeClient,
    PR_NUMBER as RECHECK_PR_NUMBER,
    REPOSITORY as RECHECK_REPOSITORY,
    run_payload as recheck_run_payload,
)
from test_bounded_execution_closeout_batch import (  # noqa: E402
    POLICY as BOUNDED_POLICY,
    RISK_CLASSES,
    ledger,
    snapshot,
)


HEAD = "a" * 40
BASE = "b" * 40
PR_NUMBER = 69
ROOT = Path(__file__).resolve().parents[2]
AI_POLICY = json.loads(
    (ROOT / "ecosystem/ai-review-policy.json").read_text(encoding="utf-8")
)
P2_EVIDENCE_WAKEUP_MARKER = "<!-- OTERYN_AI_REVIEW_EVIDENCE_WAKEUP_V1 -->"


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


def _bound_snapshot(**overrides):
    value = snapshot(**overrides)
    value["review_binding"] = make_review_binding(
        BOUNDED_POLICY,
        repository=value["repository"],
        task_id=value["task_id"],
        base_head_sha="b" * 40,
        head_sha=value["task_head_sha"],
        tier="R2",
        classifier_revision="final-findings-red-v1",
        risk_fingerprint=value["review_fingerprint"],
    )
    return value


def _maintainer_wakeup_event():
    return {
        "sender": {"login": "blakinio"},
        "issue": {
            "number": RECHECK_PR_NUMBER,
            "pull_request": {
                "url": (
                    "https://api.github.com/repos/Oteryn/Oteryn/pulls/"
                    f"{RECHECK_PR_NUMBER}"
                )
            },
        },
        "comment": {
            "body": P2_EVIDENCE_WAKEUP_MARKER,
            "author_association": "OWNER",
        },
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
        self.assertNotIn("pull_request_review_comment:", workflow)
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


class FinalFindingRegressionTests(unittest.TestCase):
    def test_completed_loop_breaker_ledger_is_invalidated_by_later_head_change(self):
        previous = snapshot(
            state="READY",
            phase="LOOP_BREAKER_AUDIT",
            candidate_frozen=False,
            late_material_findings=2,
            audited_late_material_findings=2,
            risk_ledger=ledger(),
        )
        current = copy.deepcopy(previous)
        current["task_head_sha"] = "b" * 40

        with self.assertRaisesRegex(GuardError, "audit|ledger|head"):
            bounded_decide(previous, current, "mutate", BOUNDED_POLICY)

    def test_qualification_requires_previous_checkpoint_to_already_be_frozen(self):
        previous = snapshot(
            state="READY",
            phase="implementation",
            candidate_frozen=False,
        )
        current = copy.deepcopy(previous)
        current["candidate_frozen"] = True
        current["phase"] = "final_qualification"

        result = bounded_decide(
            previous, current, "enter_final_qualification", BOUNDED_POLICY
        )

        self.assertFalse(result.allowed)
        self.assertIn("previous", result.reason.lower())
        self.assertIn("frozen", result.reason.lower())

    def test_audit_ledger_certification_requires_acknowledged_audit_dispatch(self):
        pending = ledger()
        pending[RISK_CLASSES[0]] = {"status": "PENDING", "reason": "awaiting audit"}
        previous = snapshot(
            state="READY",
            phase="LOOP_BREAKER_AUDIT",
            candidate_frozen=False,
            late_material_findings=2,
            audited_late_material_findings=0,
            risk_ledger=pending,
        )
        current = copy.deepcopy(previous)
        current["audited_late_material_findings"] = 2
        current["risk_ledger"] = ledger()

        result = bounded_decide(
            previous, current, "record_loop_breaker_audit", BOUNDED_POLICY
        )

        self.assertFalse(result.allowed)
        self.assertIn("audit", result.reason.lower())
        self.assertIn("dispatch", result.reason.lower())

    def test_external_wait_cannot_persist_unverified_repair_fields(self):
        previous = _bound_snapshot(
            state="READY",
            phase="implementation",
            candidate_frozen=True,
        )
        current = copy.deepcopy(previous)
        current["candidate_frozen"] = False
        current["material_change"] = True
        current["material_change_reason"] = "review_finding"
        current["material_change_evidence"] = "review-thread:untrusted"
        current["post_freeze_material_head_changes"] = 1
        current["blocking_dependency"] = "provider-result:pending"
        current["dependency_kind"] = "external"
        current["material_fact_envelope"] = make_material_fact_envelope(
            BOUNDED_POLICY,
            repository=current["repository"],
            task_id=current["task_id"],
            frozen_head_sha=previous["task_head_sha"],
            reason="review_finding",
            source_evidence=current["material_change_evidence"],
        )
        current["repair_generation_id"] = current["material_fact_envelope"]["envelope_id"]
        current["repair_base_head"] = previous["task_head_sha"]

        with tempfile.TemporaryDirectory() as directory:
            outbox = SqliteCheckpointOutbox(Path(directory) / "checkpoint.db")
            outbox.seed_checkpoint(
                previous["repository"],
                previous["task_id"],
                _checkpoint_digest(previous),
                snapshot=previous,
            )
            context = ExecutionContext(
                TestEvidenceAuthority({previous["review_binding"]["binding_id"]}, set()),
                outbox,
            )
            result = raw_decide(
                previous,
                current,
                "open_material_repair",
                BOUNDED_POLICY,
                context=context,
            )
            loaded = outbox.load_checkpoint(previous["repository"], previous["task_id"])

        self.assertFalse(result.allowed)
        self.assertIn("trusted_material_fact_envelope_required", result.reason)
        self.assertIsNotNone(loaded)
        self.assertTrue(loaded.snapshot["candidate_frozen"])
        self.assertEqual(loaded.snapshot["repair_generation_id"], "")

    def test_new_blocked_state_is_persisted_before_worker_release(self):
        previous = _bound_snapshot(
            state="READY",
            phase="implementation",
            candidate_frozen=False,
        )
        current = copy.deepcopy(previous)
        current["state"] = "BLOCKED"
        current["blocking_dependency"] = "owner-decision:required"
        current["dependency_kind"] = "owner"

        with tempfile.TemporaryDirectory() as directory:
            outbox = SqliteCheckpointOutbox(Path(directory) / "checkpoint.db")
            outbox.seed_checkpoint(
                previous["repository"],
                previous["task_id"],
                _checkpoint_digest(previous),
                snapshot=previous,
            )
            context = ExecutionContext(
                TestEvidenceAuthority({previous["review_binding"]["binding_id"]}, set()),
                outbox,
            )
            result = raw_decide(
                previous,
                current,
                "mutate",
                BOUNDED_POLICY,
                context=context,
            )
            loaded = outbox.load_checkpoint(previous["repository"], previous["task_id"])

        self.assertFalse(result.allowed)
        self.assertEqual(result.state, "BLOCKED")
        self.assertTrue(result.release_session)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.snapshot["state"], "BLOCKED")
        self.assertEqual(loaded.snapshot["blocking_dependency"], "owner-decision:required")

    def test_maintainer_p2_evidence_marker_wakes_exact_head_recheck(self):
        client = FakeClient(runs=[recheck_run_payload(901)], active_evidence=True)

        result = process_event(
            "issue_comment",
            _maintainer_wakeup_event(),
            RECHECK_REPOSITORY,
            AI_POLICY,
            client,
            sleep_fn=lambda _: None,
        )

        self.assertEqual(result.action, "RERUN")
        self.assertEqual(client.rerun_calls, [901])

    def test_p2_closeout_contract_requires_explicit_wakeup_producer(self):
        docs = (ROOT / "docs/governance/AI_REVIEW_POLICY.md").read_text(encoding="utf-8")
        start = docs.index("`ACCEPTED_WITH_FOLLOW_UP`")
        closeout = docs[start : start + 2600]

        self.assertIn("Tracked in #<issue>.", closeout)
        self.assertIn(P2_EVIDENCE_WAKEUP_MARKER, closeout)
        self.assertLess(
            closeout.index("Tracked in #<issue>."),
            closeout.index(P2_EVIDENCE_WAKEUP_MARKER),
        )
        lowered = closeout.lower()
        self.assertIn("top-level pull-request conversation comment", lowered)
        self.assertIn("wake-up producer only", lowered)
        self.assertIn("grants no review authority", lowered)

    def test_maintainer_p2_evidence_marker_is_wakeup_only_not_authority(self):
        client = FakeClient(runs=[recheck_run_payload(902)], active_evidence=False)

        result = process_event(
            "issue_comment",
            _maintainer_wakeup_event(),
            RECHECK_REPOSITORY,
            AI_POLICY,
            client,
            sleep_fn=lambda _: None,
        )

        self.assertEqual(result.action, "NOOP_UNVERIFIED_REVIEW_GENERATION")
        self.assertEqual(client.rerun_calls, [])

    def test_qualification_admission_must_persist_final_qualification_phase(self):
        previous = snapshot(
            state="READY",
            phase="LOOP_BREAKER_AUDIT",
            candidate_frozen=True,
            late_material_findings=2,
            audited_late_material_findings=2,
            final_qualification_runs_since_audit=0,
            risk_ledger=ledger(),
        )
        current = copy.deepcopy(previous)
        current["final_qualification_runs_since_audit"] = 1

        result = bounded_decide(
            previous, current, "enter_final_qualification", BOUNDED_POLICY
        )

        self.assertFalse(result.allowed)
        self.assertIn("final_qualification", result.reason)

    def test_caller_controlled_generation_strings_do_not_create_material_progress(self):
        for field in ("review_generation", "evidence_generation"):
            with self.subTest(field=field):
                previous = snapshot(
                    state="RUNNING",
                    phase="implementation",
                    candidate_frozen=False,
                )
                current = copy.deepcopy(previous)
                current[field] = f"forged-{field}-2"

                result = bounded_decide(previous, current, "mutate", BOUNDED_POLICY)

                self.assertFalse(result.allowed)
                self.assertIn("progress", result.reason.lower())


if __name__ == "__main__":
    unittest.main()
