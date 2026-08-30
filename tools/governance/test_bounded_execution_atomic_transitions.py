import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from bounded_execution_guard import (  # noqa: E402
    ExecutionContext,
    GuardError,
    _checkpoint_digest,
    decide as raw_decide,
    make_review_binding,
)
from bounded_execution_test_support import decide  # noqa: E402
from durable_checkpoint_outbox import Reservation  # noqa: E402


ROOT = Path(__file__).resolve().parents[2]
POLICY = json.loads(
    (ROOT / "ecosystem/bounded-autonomous-execution-policy.json").read_text(encoding="utf-8")
)
RISK_CLASSES = tuple(POLICY["loop_breaker"]["risk_classes"])


def terminal_ledger():
    return {
        name: {"status": "AUDITED_PASS", "reason": "atomic transition regression fixture"}
        for name in RISK_CLASSES
    }


def pending_ledger():
    value = terminal_ledger()
    value[RISK_CLASSES[0]] = {"status": "PENDING", "reason": "awaiting audit"}
    return value


def snapshot(**overrides):
    value = {
        "repository": "Oteryn/Oteryn",
        "task_id": "OTERYN-BOUNDED-ATOMIC-TRANSITIONS",
        "state": "READY",
        "phase": "final_qualification",
        "task_head_sha": "a" * 40,
        "candidate_frozen": True,
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
        "risk_ledger": terminal_ledger(),
    }
    value.update(overrides)
    return value


class AllowEvidenceAuthority:
    def verify_review_binding(self, binding):
        return True

    def verify_material_fact_envelope(self, envelope):
        return True

    def verify_completion(self, candidate):
        return True


class DenyCompletionAuthority(AllowEvidenceAuthority):
    def verify_completion(self, candidate):
        return False


class RecordingOutbox:
    def __init__(self):
        self.next_checkpoint = None
        self.action = None

    def reserve(
        self,
        *,
        repository,
        task_id,
        expected_checkpoint,
        next_checkpoint,
        action,
        scope,
    ):
        self.next_checkpoint = next_checkpoint
        self.action = action
        return Reservation(True, "atomic-transition-test", "reservation_committed")

    def transition(
        self,
        *,
        repository,
        task_id,
        expected_checkpoint,
        next_checkpoint,
        reason,
        scope,
    ):
        self.next_checkpoint = next_checkpoint
        self.action = None
        return Reservation(True, "atomic-transition-test", "transition_committed")

    def claim_dispatch(self, reservation_key):
        return True


def with_binding(value):
    prepared = copy.deepcopy(value)
    prepared["review_binding"] = make_review_binding(
        POLICY,
        repository=prepared["repository"],
        task_id=prepared["task_id"],
        base_head_sha="b" * 40,
        head_sha=prepared["task_head_sha"],
        tier="R2",
        classifier_revision="atomic-transition-test-v1",
        risk_fingerprint=prepared["review_fingerprint"],
    )
    return prepared


class AtomicTransitionRegressionTests(unittest.TestCase):
    def test_completion_reserves_terminal_done_checkpoint(self):
        previous = with_binding(snapshot(completion_verified=False))
        current = with_binding(snapshot(completion_verified=True))
        outbox = RecordingOutbox()

        result = raw_decide(
            previous,
            current,
            "complete",
            POLICY,
            context=ExecutionContext(AllowEvidenceAuthority(), outbox),
        )

        self.assertTrue(result.allowed)
        self.assertEqual(result.state, "DONE")
        expected = copy.deepcopy(current)
        expected["state"] = "DONE"
        self.assertEqual(outbox.next_checkpoint, _checkpoint_digest(expected))
        self.assertNotEqual(outbox.next_checkpoint, _checkpoint_digest(current))

    def test_completion_requires_trusted_exact_candidate_evidence(self):
        previous = with_binding(snapshot(completion_verified=False))
        current = with_binding(snapshot(completion_verified=True))
        outbox = RecordingOutbox()

        result = raw_decide(
            previous,
            current,
            "complete",
            POLICY,
            context=ExecutionContext(DenyCompletionAuthority(), outbox),
        )

        self.assertFalse(result.allowed)
        self.assertEqual(result.state, "READY")
        self.assertIn("trusted_completion", result.reason)
        self.assertIsNone(outbox.next_checkpoint)

    def test_async_review_reserves_waiting_external_and_releases_worker(self):
        previous = snapshot(state="READY", external_review_invocations=0)
        current = copy.deepcopy(previous)
        current["external_review_invocations"] = 1

        result = decide(previous, current, "request_external_review", POLICY)

        self.assertTrue(result.allowed)
        self.assertEqual(result.state, "WAITING_EXTERNAL")
        self.assertTrue(result.release_session)

    def test_audited_generation_advances_only_via_record_audit_action(self):
        previous = snapshot(
            state="READY",
            phase="LOOP_BREAKER_AUDIT",
            late_material_findings=2,
            audited_late_material_findings=0,
            risk_ledger=pending_ledger(),
        )
        current = copy.deepcopy(previous)
        current["audited_late_material_findings"] = 2
        current["risk_ledger"] = terminal_ledger()

        with self.assertRaisesRegex(GuardError, "record_loop_breaker_audit"):
            decide(previous, current, "mutate", POLICY)

    def test_external_dependency_observation_reserves_waiting_checkpoint_before_release(self):
        current = with_binding(
            snapshot(
                state="READY",
                phase="implementation",
                candidate_frozen=False,
                blocking_dependency="external-review:123",
                dependency_kind="external",
            )
        )
        outbox = RecordingOutbox()

        result = raw_decide(
            None,
            current,
            "observe",
            POLICY,
            context=ExecutionContext(AllowEvidenceAuthority(), outbox),
        )

        self.assertTrue(result.allowed)
        self.assertEqual(result.state, "WAITING_EXTERNAL")
        self.assertTrue(result.release_session)
        expected = copy.deepcopy(current)
        expected["state"] = "WAITING_EXTERNAL"
        self.assertEqual(outbox.next_checkpoint, _checkpoint_digest(expected))

    def test_completion_requires_prior_durable_frozen_final_candidate(self):
        previous = with_binding(
            snapshot(
                state="READY",
                phase="implementation",
                candidate_frozen=False,
                completion_verified=False,
            )
        )
        current = with_binding(
            snapshot(
                state="READY",
                phase="final_qualification",
                candidate_frozen=True,
                completion_verified=True,
            )
        )
        outbox = RecordingOutbox()

        result = raw_decide(
            previous,
            current,
            "complete",
            POLICY,
            context=ExecutionContext(AllowEvidenceAuthority(), outbox),
        )

        self.assertFalse(result.allowed)
        self.assertEqual(result.state, "READY")
        self.assertIn("previous", result.reason)
        self.assertIsNone(outbox.next_checkpoint)

    def test_denied_external_operational_action_persists_waiting_without_dispatch(self):
        previous = with_binding(
            snapshot(
                state="READY",
                phase="implementation",
                candidate_frozen=False,
                blocking_dependency="external-review:123",
                dependency_kind="external",
            )
        )
        current = copy.deepcopy(previous)
        outbox = RecordingOutbox()

        result = raw_decide(
            previous,
            current,
            "mutate",
            POLICY,
            context=ExecutionContext(AllowEvidenceAuthority(), outbox),
        )

        self.assertFalse(result.allowed)
        self.assertEqual(result.state, "WAITING_EXTERNAL")
        self.assertTrue(result.release_session)
        expected = copy.deepcopy(current)
        expected["state"] = "WAITING_EXTERNAL"
        self.assertEqual(outbox.next_checkpoint, _checkpoint_digest(expected))
        self.assertIsNone(outbox.action)

    def test_exhausted_async_action_persists_waiting_without_dispatch(self):
        for action, field in (
            ("request_external_review", "external_review_invocations"),
            ("same_head_gate_recheck", "same_head_gate_rechecks"),
        ):
            with self.subTest(action=action):
                previous = with_binding(snapshot(state="READY", **{field: 1}))
                current = copy.deepcopy(previous)
                current[field] = 2
                outbox = RecordingOutbox()

                result = raw_decide(
                    previous,
                    current,
                    action,
                    POLICY,
                    context=ExecutionContext(AllowEvidenceAuthority(), outbox),
                )

                self.assertFalse(result.allowed)
                self.assertEqual(result.state, "WAITING_EXTERNAL")
                self.assertTrue(result.release_session)
                expected = copy.deepcopy(current)
                expected["state"] = "WAITING_EXTERNAL"
                self.assertEqual(outbox.next_checkpoint, _checkpoint_digest(expected))
                self.assertIsNone(outbox.action)

    def test_terminal_ledger_certification_requires_record_action_even_when_counters_match(self):
        previous = snapshot(
            state="READY",
            phase="LOOP_BREAKER_AUDIT",
            candidate_frozen=False,
            late_material_findings=2,
            audited_late_material_findings=2,
            risk_ledger=pending_ledger(),
        )
        current = copy.deepcopy(previous)
        current["risk_ledger"] = terminal_ledger()

        with self.assertRaisesRegex(GuardError, "record_loop_breaker_audit"):
            decide(previous, current, "mutate", POLICY)


if __name__ == "__main__":
    unittest.main()
