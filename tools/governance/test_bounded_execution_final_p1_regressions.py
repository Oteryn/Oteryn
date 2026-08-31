import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from bounded_execution_guard import (  # noqa: E402
    ExecutionContext,
    GuardError,
    _checkpoint_digest,
    decide as raw_decide,
    make_material_fact_envelope,
    make_review_binding,
)
from bounded_execution_test_support import TestEvidenceAuthority  # noqa: E402
from durable_checkpoint_outbox import SqliteCheckpointOutbox  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
POLICY = json.loads(
    (ROOT / "ecosystem/bounded-autonomous-execution-policy.json").read_text(encoding="utf-8")
)
RISK_CLASSES = tuple(POLICY["loop_breaker"]["risk_classes"])


def ledger():
    return {
        name: {"status": "AUDITED_PASS", "reason": "batched closeout audit complete"}
        for name in RISK_CLASSES
    }


def snapshot(**overrides):
    value = {
        "repository": "Oteryn/Oteryn",
        "task_id": "OTERYN-FINAL-P1-REGRESSIONS",
        "state": "RUNNING",
        "phase": "implementation",
        "task_head_sha": "a" * 40,
        "candidate_frozen": False,
        "blocking_dependency": "",
        "dependency_kind": "",
        "gate_state": "pending",
        "review_generation": "review-1",
        "review_fingerprint": "f" * 64,
        "evidence_generation": "evidence-1",
        "first_material_failure": "",
        "identical_failure_cycles": 0,
        "heavy_validation_runs": 0,
        "external_review_invocations": 0,
        "same_head_gate_rechecks": 0,
        "completion_verified": False,
        "material_change": False,
        "material_change_reason": "",
        "material_change_evidence": "",
        "material_fact_id": "",
        "material_fact_head": "",
        "material_fact_verified": False,
        "repair_generation_id": "",
        "repair_base_head": "",
        "late_material_findings": 0,
        "post_freeze_material_head_changes": 0,
        "audited_late_material_findings": 0,
        "audited_post_freeze_material_head_changes": 0,
        "final_qualification_runs_since_audit": 0,
        "risk_ledger": ledger(),
    }
    value.update(overrides)
    return value


class FinalMaterialAuthorityP1Tests(unittest.TestCase):
    def _context(self, previous, *, trusted_envelopes=()):
        binding = make_review_binding(
            POLICY,
            repository=previous["repository"],
            task_id=previous["task_id"],
            base_head_sha="b" * 40,
            head_sha=previous["task_head_sha"],
            tier="R2",
            classifier_revision="final-p1-regression-v1",
            risk_fingerprint="f" * 64,
        )
        previous["review_binding"] = binding
        directory = tempfile.TemporaryDirectory()
        outbox = SqliteCheckpointOutbox(Path(directory.name) / "checkpoint.db")
        outbox.seed_checkpoint(
            previous["repository"], previous["task_id"],
            _checkpoint_digest(previous), snapshot=previous,
        )
        authority = TestEvidenceAuthority(
            {binding["binding_id"]}, set(trusted_envelopes)
        )
        return directory, ExecutionContext(authority, outbox)

    def test_unverified_material_envelope_cannot_create_progress_for_mutation(self):
        previous = snapshot()
        envelope = make_material_fact_envelope(
            POLICY,
            repository=previous["repository"],
            task_id=previous["task_id"],
            frozen_head_sha=previous["task_head_sha"],
            reason="review_finding",
            source_evidence="review-thread:3890490509",
        )
        directory, context = self._context(previous, trusted_envelopes=())
        try:
            current = copy.deepcopy(previous)
            current["review_binding"] = previous["review_binding"]
            current["material_fact_envelope"] = envelope
            result = raw_decide(previous, current, "mutate", POLICY, context=context)
        finally:
            directory.cleanup()

        self.assertFalse(result.allowed)
        self.assertIn("trusted_material_fact_envelope_required", result.reason)

    def test_terminal_risk_ledger_cannot_be_edited_during_final_qualification(self):
        previous = snapshot(
            state="READY",
            phase="LOOP_BREAKER_AUDIT",
            candidate_frozen=True,
            late_material_findings=2,
            audited_late_material_findings=2,
            final_qualification_runs_since_audit=0,
        )
        directory, context = self._context(previous)
        try:
            current = copy.deepcopy(previous)
            current["review_binding"] = previous["review_binding"]
            current["phase"] = "final_qualification"
            current["final_qualification_runs_since_audit"] = 1
            current["risk_ledger"]["identity_binding"] = {
                "status": "NOT_APPLICABLE",
                "reason": "caller changed terminal audit result",
            }
            with self.assertRaisesRegex(
                GuardError,
                "risk ledger may change only through record_loop_breaker_audit",
            ):
                raw_decide(
                    previous,
                    current,
                    "enter_final_qualification",
                    POLICY,
                    context=context,
                )
        finally:
            directory.cleanup()

    def test_external_wait_denial_persists_only_wait_coordinates_not_action_fields(self):
        previous = snapshot(
            state="READY",
            phase="LOOP_BREAKER_AUDIT",
            candidate_frozen=False,
            late_material_findings=2,
            audited_late_material_findings=2,
            final_qualification_runs_since_audit=0,
        )
        directory, context = self._context(previous)
        try:
            current = copy.deepcopy(previous)
            current["review_binding"] = previous["review_binding"]
            current["blocking_dependency"] = "external:review-evidence"
            current["dependency_kind"] = "external"
            current["gate_state"] = "waiting"
            current["candidate_frozen"] = True
            current["phase"] = "final_qualification"
            current["final_qualification_runs_since_audit"] = 1

            result = raw_decide(
                previous,
                current,
                "enter_final_qualification",
                POLICY,
                context=context,
            )
            record = context.checkpoint_outbox.load_checkpoint(
                previous["repository"], previous["task_id"]
            )
        finally:
            directory.cleanup()

        self.assertFalse(result.allowed)
        self.assertEqual(result.state, "WAITING_EXTERNAL")
        self.assertIsNotNone(record)
        self.assertEqual(record.snapshot["state"], "WAITING_EXTERNAL")
        self.assertEqual(record.snapshot["blocking_dependency"], "external:review-evidence")
        self.assertEqual(record.snapshot["dependency_kind"], "external")
        self.assertEqual(record.snapshot["gate_state"], "waiting")
        self.assertFalse(record.snapshot["candidate_frozen"])
        self.assertEqual(record.snapshot["phase"], "LOOP_BREAKER_AUDIT")
        self.assertEqual(record.snapshot["final_qualification_runs_since_audit"], 0)

    def test_initial_retry_is_consumed_once_per_material_progress_scope(self):
        previous = snapshot()
        directory, context = self._context(previous)
        try:
            first = copy.deepcopy(previous)
            first["review_binding"] = previous["review_binding"]
            first_result = raw_decide(previous, first, "retry", POLICY, context=context)
            self.assertTrue(first_result.allowed)

            claimed = context.checkpoint_outbox.claim_pending_dispatch(
                previous["repository"], previous["task_id"]
            )
            self.assertIsNotNone(claimed)
            self.assertTrue(
                context.checkpoint_outbox.begin_dispatch(
                    claimed.reservation_key, claimed.dispatch_generation
                )
            )
            self.assertTrue(
                context.checkpoint_outbox.acknowledge_dispatch(
                    claimed.reservation_key, claimed.dispatch_generation
                )
            )

            durable = context.checkpoint_outbox.load_checkpoint(
                previous["repository"], previous["task_id"]
            )
            self.assertIsNotNone(durable)
            second_previous = durable.snapshot
            second = copy.deepcopy(second_previous)
            second["review_generation"] = "descriptive-generation-churn"
            second_result = raw_decide(
                second_previous,
                second,
                "retry",
                POLICY,
                context=context,
            )
        finally:
            directory.cleanup()

        self.assertFalse(second_result.allowed)
        self.assertIn("initial_attempt", second_result.reason)


if __name__ == "__main__":
    unittest.main()
