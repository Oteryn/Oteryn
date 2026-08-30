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
from bounded_execution_test_support import TestEvidenceAuthority, decide  # noqa: E402
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
        "task_id": "OTERYN-ANTI-LOOP-CLOSEOUT",
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
        "risk_ledger": ledger(),
    }
    value.update(overrides)
    return value


class FrozenLineageTests(unittest.TestCase):
    def test_explicit_unfreeze_consumes_one_post_freeze_repair_generation(self):
        previous = snapshot(
            candidate_frozen=True,
            material_change_reason="review_finding",
            material_fact_id="d" * 64,
            material_fact_head="a" * 40,
            material_fact_verified=True,
        )
        current = copy.deepcopy(previous)
        current["candidate_frozen"] = False
        current["material_change"] = True
        current["material_change_evidence"] = "review-thread:3888776292"
        current["evidence_generation"] = "evidence-2"
        current["repair_generation_id"] = "d" * 64
        current["repair_base_head"] = "a" * 40
        with self.assertRaises(GuardError):
            decide(previous, current, "observe", POLICY)

        current["post_freeze_material_head_changes"] = 1
        result = decide(previous, current, "open_material_repair", POLICY)
        self.assertTrue(result.allowed)

    def test_head_move_inside_already_open_repair_does_not_need_second_increment(self):
        previous = snapshot(
            candidate_frozen=False,
            material_change=True,
            material_change_reason="review_finding",
            material_change_evidence="review-thread:3888776292",
            material_fact_id="d" * 64,
            material_fact_head="a" * 40,
            material_fact_verified=True,
            repair_generation_id="d" * 64,
            repair_base_head="a" * 40,
            post_freeze_material_head_changes=1,
        )
        current = copy.deepcopy(previous)
        current["task_head_sha"] = "b" * 40
        result = decide(previous, current, "mutate", POLICY)
        self.assertTrue(result.allowed)


class FreezeAdmissionTests(unittest.TestCase):
    def test_pre_threshold_final_qualification_requires_frozen_candidate(self):
        current = snapshot(candidate_frozen=False)
        result = decide(None, current, "enter_final_qualification", POLICY)
        self.assertFalse(result.allowed)
        self.assertIn("frozen", result.reason.lower())

    def test_every_final_qualification_action_requires_frozen_candidate(self):
        previous = snapshot(candidate_frozen=False, completion_verified=True)
        for action in (
            "request_external_review",
            "run_heavy_validation",
            "same_head_gate_recheck",
            "complete",
        ):
            with self.subTest(action=action):
                current = copy.deepcopy(previous)
                counter = {
                    "request_external_review": "external_review_invocations",
                    "run_heavy_validation": "heavy_validation_runs",
                    "same_head_gate_recheck": "same_head_gate_rechecks",
                }.get(action)
                if counter is not None:
                    current[counter] = 1
                result = decide(previous, current, action, POLICY)
                self.assertFalse(result.allowed)
                self.assertIn("frozen", result.reason.lower())

    def test_loop_breaker_qualification_requires_frozen_candidate(self):
        previous = snapshot(
            late_material_findings=2,
            audited_late_material_findings=2,
            candidate_frozen=False,
            final_qualification_runs_since_audit=0,
        )
        current = copy.deepcopy(previous)
        current["final_qualification_runs_since_audit"] = 1
        result = decide(previous, current, "enter_final_qualification", POLICY)
        self.assertFalse(result.allowed)
        self.assertIn("frozen", result.reason.lower())

    def test_post_admission_final_review_requires_candidate_to_remain_frozen(self):
        previous = snapshot(
            phase="LOOP_BREAKER_AUDIT",
            late_material_findings=2,
            audited_late_material_findings=2,
            candidate_frozen=True,
            material_change_reason="review_finding",
            material_fact_id="d" * 64,
            material_fact_head="a" * 40,
            material_fact_verified=True,
            final_qualification_runs_since_audit=0,
        )
        admitted = copy.deepcopy(previous)
        admitted["phase"] = "final_qualification"
        admitted["final_qualification_runs_since_audit"] = 1
        self.assertTrue(
            decide(previous, admitted, "enter_final_qualification", POLICY).allowed
        )

        unfrozen = copy.deepcopy(admitted)
        unfrozen["candidate_frozen"] = False
        unfrozen["material_change"] = True
        unfrozen["material_change_evidence"] = "review-thread:3888776294"
        unfrozen["evidence_generation"] = "evidence-2"
        unfrozen["post_freeze_material_head_changes"] = 1
        unfrozen["repair_generation_id"] = "d" * 64
        unfrozen["repair_base_head"] = "a" * 40
        with self.assertRaises(GuardError):
            decide(admitted, unfrozen, "request_external_review", POLICY)


class MaterialChangeEvidenceTests(unittest.TestCase):
    def test_frozen_snapshot_cannot_self_attest_a_new_material_fact(self):
        previous = snapshot(candidate_frozen=True)
        current = copy.deepcopy(previous)
        current["material_change_reason"] = "review_finding"
        current["material_fact_id"] = "d" * 64
        current["material_fact_head"] = "a" * 40
        current["material_fact_verified"] = True

        with self.assertRaises(GuardError):
            decide(previous, current, "observe", POLICY)


class TrustedAuthorityAndReservationTests(unittest.TestCase):
    def test_standalone_consuming_action_fails_closed_with_reservation_required(self):
        result = raw_decide(None, snapshot(candidate_frozen=False), "complete", POLICY)

        self.assertFalse(result.allowed)
        self.assertIn("reservation_required", result.reason)

    def test_untrusted_material_fact_envelope_cannot_open_repair(self):
        previous = snapshot(candidate_frozen=True)
        previous["review_binding"] = make_review_binding(
            POLICY,
            repository=previous["repository"],
            task_id=previous["task_id"],
            base_head_sha="b" * 40,
            head_sha=previous["task_head_sha"],
            tier="R2",
            classifier_revision="classifier-v1",
            risk_fingerprint="f" * 64,
        )
        current = copy.deepcopy(previous)
        current["candidate_frozen"] = False
        current["material_change"] = True
        current["material_change_evidence"] = "review-thread:material"
        current["post_freeze_material_head_changes"] = 1
        current["material_fact_envelope"] = make_material_fact_envelope(
            POLICY,
            repository=current["repository"],
            task_id=current["task_id"],
            frozen_head_sha=previous["task_head_sha"],
            reason="review_finding",
            source_evidence="review-thread:material",
        )
        current["repair_generation_id"] = current["material_fact_envelope"]["envelope_id"]
        current["repair_base_head"] = previous["task_head_sha"]
        with tempfile.TemporaryDirectory() as directory:
            outbox = SqliteCheckpointOutbox(Path(directory) / "checkpoint.db")
            outbox.seed_checkpoint(
                previous["repository"], previous["task_id"], _checkpoint_digest(previous), snapshot=previous
            )
            context = ExecutionContext(
                TestEvidenceAuthority({previous["review_binding"]["binding_id"]}, set()),
                outbox,
            )
            result = raw_decide(
                previous,
                current,
                "open_material_repair",
                POLICY,
                context=context,
            )

        self.assertFalse(result.allowed)
        self.assertIn("trusted_material_fact_envelope_required", result.reason)

    def test_untrusted_review_binding_cannot_reset_review_budget(self):
        previous = snapshot(external_review_invocations=1)
        previous["review_binding"] = make_review_binding(
            POLICY,
            repository=previous["repository"],
            task_id=previous["task_id"],
            base_head_sha="b" * 40,
            head_sha=previous["task_head_sha"],
            tier="R2",
            classifier_revision="classifier-v1",
            risk_fingerprint="f" * 64,
        )
        current = copy.deepcopy(previous)
        current["external_review_invocations"] = 0
        current["review_binding"] = make_review_binding(
            POLICY,
            repository=current["repository"],
            task_id=current["task_id"],
            base_head_sha="b" * 40,
            head_sha=current["task_head_sha"],
            tier="R2",
            classifier_revision="classifier-v1",
            risk_fingerprint="e" * 64,
        )
        with tempfile.TemporaryDirectory() as directory:
            outbox = SqliteCheckpointOutbox(Path(directory) / "checkpoint.db")
            outbox.seed_checkpoint(
                previous["repository"], previous["task_id"], _checkpoint_digest(previous), snapshot=previous
            )
            context = ExecutionContext(
                TestEvidenceAuthority({previous["review_binding"]["binding_id"]}, set()),
                outbox,
            )
            result = raw_decide(previous, current, "mutate", POLICY, context=context)

        self.assertFalse(result.allowed)
        self.assertIn("trusted_review_binding_required", result.reason)

    def test_durable_outbox_allows_one_cas_winner_and_one_dispatch(self):
        with tempfile.TemporaryDirectory() as directory:
            outbox = SqliteCheckpointOutbox(Path(directory) / "checkpoint.db")
            snapshot_r = {"revision": "r"}
            snapshot_r1 = {"revision": "r+1"}
            snapshot_other = {"revision": "other"}
            checkpoint_r = _checkpoint_digest(snapshot_r)
            checkpoint_r1 = _checkpoint_digest(snapshot_r1)
            checkpoint_other = _checkpoint_digest(snapshot_other)
            outbox.seed_checkpoint(
                "Oteryn/Oteryn", "OTERYN-CAS", checkpoint_r, snapshot=snapshot_r
            )
            winner = outbox.reserve(
                repository="Oteryn/Oteryn",
                task_id="OTERYN-CAS",
                expected_checkpoint=checkpoint_r,
                next_checkpoint=checkpoint_r1,
                next_snapshot=snapshot_r1,
                action="retry",
                scope=("risk",),
            )
            replay = outbox.reserve(
                repository="Oteryn/Oteryn",
                task_id="OTERYN-CAS",
                expected_checkpoint=checkpoint_r,
                next_checkpoint=checkpoint_r1,
                next_snapshot=snapshot_r1,
                action="retry",
                scope=("risk",),
            )
            loser = outbox.reserve(
                repository="Oteryn/Oteryn",
                task_id="OTERYN-CAS",
                expected_checkpoint=checkpoint_r,
                next_checkpoint=checkpoint_other,
                next_snapshot=snapshot_other,
                action="retry",
                scope=("risk",),
            )

            self.assertTrue(winner.committed)
            self.assertFalse(replay.committed)
            self.assertEqual(replay.reason, "reservation_replay")
            self.assertFalse(loser.committed)
            self.assertEqual(loser.reason, "checkpoint_cas_conflict")
            loaded = outbox.load_checkpoint("Oteryn/Oteryn", "OTERYN-CAS")
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded.checkpoint, checkpoint_r1)
            self.assertEqual(loaded.snapshot, snapshot_r1)
            self.assertTrue(outbox.claim_dispatch(winner.reservation_key))
            self.assertFalse(outbox.claim_dispatch(winner.reservation_key))

    def test_durable_outbox_persists_recoverable_snapshot_for_takeover(self):
        previous = snapshot(
            state="READY",
            phase="implementation",
            candidate_frozen=False,
        )
        first = copy.deepcopy(previous)
        first["gate_state"] = "running"
        second = copy.deepcopy(first)
        second["state"] = "WAITING_EXTERNAL"
        second["blocking_dependency"] = "provider-result:pending"
        second["dependency_kind"] = "external"

        with tempfile.TemporaryDirectory() as directory:
            outbox = SqliteCheckpointOutbox(Path(directory) / "checkpoint.db")
            outbox.seed_checkpoint(
                previous["repository"],
                previous["task_id"],
                _checkpoint_digest(previous),
                snapshot=previous,
            )
            seeded = outbox.load_checkpoint(previous["repository"], previous["task_id"])
            self.assertEqual(seeded.checkpoint, _checkpoint_digest(previous))
            self.assertEqual(seeded.snapshot, previous)

            reserved = outbox.reserve(
                repository=previous["repository"],
                task_id=previous["task_id"],
                expected_checkpoint=_checkpoint_digest(previous),
                next_checkpoint=_checkpoint_digest(first),
                next_snapshot=first,
                action="retry",
                scope=(),
            )
            self.assertTrue(reserved.committed)
            after_reserve = outbox.load_checkpoint(previous["repository"], previous["task_id"])
            self.assertEqual(after_reserve.checkpoint, _checkpoint_digest(first))
            self.assertEqual(after_reserve.snapshot, first)

            transitioned = outbox.transition(
                repository=previous["repository"],
                task_id=previous["task_id"],
                expected_checkpoint=_checkpoint_digest(first),
                next_checkpoint=_checkpoint_digest(second),
                next_snapshot=second,
                reason="external dependency is pending",
                scope=(),
            )
            self.assertTrue(transitioned.committed)
            after_transition = outbox.load_checkpoint(previous["repository"], previous["task_id"])
            self.assertEqual(after_transition.checkpoint, _checkpoint_digest(second))
            self.assertEqual(after_transition.snapshot, second)

    def test_frozen_candidate_rejects_self_attested_material_change(self):
        previous = snapshot(candidate_frozen=True)
        current = copy.deepcopy(previous)
        current["material_change"] = True
        current["material_change_reason"] = "review_finding"
        current["material_change_evidence"] = "review-thread:3888786165"
        current["material_fact_id"] = "d" * 64
        current["material_fact_head"] = "a" * 40
        current["material_fact_verified"] = True
        current["repair_generation_id"] = "d" * 64
        current["repair_base_head"] = "a" * 40

        result = decide(previous, current, "mutate", POLICY)

        self.assertFalse(result.allowed)
        self.assertIn("unfreeze", result.reason.lower())

    def test_unfreeze_requires_permitted_reason_and_durable_evidence(self):
        previous = snapshot(candidate_frozen=True)
        current = copy.deepcopy(previous)
        current["candidate_frozen"] = False
        current["material_change"] = True
        current["post_freeze_material_head_changes"] = 1

        with self.assertRaises(GuardError):
            decide(previous, current, "observe", POLICY)

        previous = snapshot(
            candidate_frozen=True,
            material_change_reason="review_finding",
            material_fact_id="d" * 64,
            material_fact_head="a" * 40,
            material_fact_verified=True,
        )
        current = copy.deepcopy(previous)
        current["candidate_frozen"] = False
        current["material_change"] = True
        current["material_change_evidence"] = "review-thread:3888786165"
        current["evidence_generation"] = "evidence-2"
        current["post_freeze_material_head_changes"] = 1
        current["repair_generation_id"] = "d" * 64
        current["repair_base_head"] = "a" * 40
        result = decide(previous, current, "open_material_repair", POLICY)
        self.assertTrue(result.allowed)

    def test_unfreeze_rejects_fact_that_is_not_bound_to_frozen_head(self):
        previous = snapshot(
            candidate_frozen=True,
            material_change_reason="review_finding",
            material_fact_id="d" * 64,
            material_fact_head="b" * 40,
            material_fact_verified=True,
        )
        current = copy.deepcopy(previous)
        current["candidate_frozen"] = False
        current["material_change"] = True
        current["material_change_evidence"] = "review-thread:3888786165"
        current["post_freeze_material_head_changes"] = 1
        current["repair_generation_id"] = "d" * 64
        current["repair_base_head"] = "a" * 40

        with self.assertRaises(GuardError):
            decide(previous, current, "open_material_repair", POLICY)

    def test_refreeze_action_must_commit_frozen_transition(self):
        previous = snapshot(
            candidate_frozen=False,
            material_change=True,
            material_change_reason="review_finding",
            material_change_evidence="review-thread:3889619678",
            material_fact_id="d" * 64,
            material_fact_head="a" * 40,
            material_fact_verified=True,
            repair_generation_id="d" * 64,
            repair_base_head="a" * 40,
            post_freeze_material_head_changes=1,
            review_fingerprint="f" * 64,
        )
        current = copy.deepcopy(previous)

        with self.assertRaisesRegex(GuardError, "refreeze"):
            decide(previous, current, "refreeze_candidate", POLICY)

    def test_refreeze_requires_new_trusted_review_risk_binding(self):
        previous = snapshot(
            candidate_frozen=False,
            material_change=True,
            material_change_reason="review_finding",
            material_change_evidence="review-thread:3888786165",
            material_fact_id="d" * 64,
            material_fact_head="a" * 40,
            material_fact_verified=True,
            repair_generation_id="d" * 64,
            repair_base_head="a" * 40,
            post_freeze_material_head_changes=1,
            review_fingerprint="f" * 64,
        )
        current = copy.deepcopy(previous)
        current["candidate_frozen"] = True
        current["task_head_sha"] = "b" * 40

        with self.assertRaises(GuardError):
            decide(previous, current, "refreeze_candidate", POLICY)

        current["review_fingerprint"] = "e" * 64
        result = decide(previous, current, "refreeze_candidate", POLICY)
        self.assertTrue(result.allowed)


class DoneTerminalityTests(unittest.TestCase):
    def test_observe_cannot_claim_a_done_transition(self):
        previous = snapshot(completion_verified=True)
        current = copy.deepcopy(previous)
        current["state"] = "DONE"

        with self.assertRaises(GuardError):
            decide(previous, current, "observe", POLICY)

    def test_previous_done_cannot_transition_back_to_running(self):
        previous = snapshot(state="DONE", completion_verified=True)
        current = snapshot(
            state="RUNNING",
            completion_verified=False,
        )
        result = decide(previous, current, "mutate", POLICY)
        self.assertFalse(result.allowed)
        self.assertEqual(result.state, "DONE")
        self.assertTrue(result.release_session)

    def test_previous_done_allows_observation_only(self):
        previous = snapshot(state="DONE", completion_verified=True)
        current = copy.deepcopy(previous)
        observed = decide(previous, current, "observe", POLICY)
        self.assertTrue(observed.allowed)
        self.assertEqual(observed.state, "DONE")
        self.assertTrue(observed.release_session)

        completed = decide(previous, current, "complete", POLICY)
        self.assertFalse(completed.allowed)
        self.assertEqual(completed.state, "DONE")
        self.assertTrue(completed.release_session)


class CounterTransitionTests(unittest.TestCase):
    def test_consuming_action_cannot_change_its_review_generation_scope(self):
        previous = snapshot(external_review_invocations=0, review_fingerprint="f" * 64)
        current = copy.deepcopy(previous)
        current["external_review_invocations"] = 1
        current["review_fingerprint"] = "e" * 64

        result = decide(previous, current, "request_external_review", POLICY)
        self.assertFalse(result.allowed)
        self.assertIn("generation", result.reason.lower())

    def test_action_cannot_consume_an_unrelated_counter(self):
        previous = snapshot()
        current = copy.deepcopy(previous)
        current["heavy_validation_runs"] = 1

        with self.assertRaises(GuardError):
            decide(previous, current, "request_external_review", POLICY)


class ActionCounterConsumptionTests(unittest.TestCase):
    def _assert_consumed_counter(self, action, field):
        previous = snapshot(candidate_frozen=True)
        current = copy.deepcopy(previous)
        current[field] = 1
        result = decide(previous, current, action, POLICY)
        self.assertTrue(result.allowed, (action, result))

        replay = decide(current, copy.deepcopy(current), action, POLICY)
        self.assertFalse(replay.allowed, (action, replay))
        self.assertIn("counter", replay.reason.lower())

    def test_external_review_consumes_counter(self):
        self._assert_consumed_counter(
            "request_external_review", "external_review_invocations"
        )

    def test_same_head_recheck_consumes_counter(self):
        self._assert_consumed_counter(
            "same_head_gate_recheck", "same_head_gate_rechecks"
        )

    def test_heavy_validation_consumes_counter(self):
        self._assert_consumed_counter("run_heavy_validation", "heavy_validation_runs")

    def test_identical_retry_consumes_counter(self):
        previous = snapshot(
            state="RUNNING",
            candidate_frozen=False,
            gate_state="failure",
            first_material_failure="same deterministic failure",
            identical_failure_cycles=0,
        )
        current = copy.deepcopy(previous)
        current["identical_failure_cycles"] = 1
        result = decide(previous, current, "retry", POLICY)
        self.assertTrue(result.allowed)

        replay = decide(current, copy.deepcopy(current), "retry", POLICY)
        self.assertFalse(replay.allowed)
        self.assertIn("counter", replay.reason.lower())

    def test_consuming_action_requires_durable_previous_snapshot(self):
        current = snapshot(external_review_invocations=0)
        result = decide(None, current, "request_external_review", POLICY)
        self.assertFalse(result.allowed)
        self.assertIn("previous", result.reason.lower())


class WaitingStateTests(unittest.TestCase):
    def test_waiting_external_without_coordinates_still_denies_operational_work(self):
        current = snapshot(
            state="WAITING_EXTERNAL",
            blocking_dependency="",
            dependency_kind="",
        )
        for action in (
            "mutate",
            "retry",
            "retrigger",
            "run_heavy_validation",
            "request_external_review",
            "same_head_gate_recheck",
            "enter_final_qualification",
        ):
            with self.subTest(action=action):
                result = decide(None, current, action, POLICY)
                self.assertFalse(result.allowed)
                self.assertEqual(result.state, "WAITING_EXTERNAL")
                self.assertTrue(result.release_session)

        observed = decide(None, current, "observe", POLICY)
        self.assertTrue(observed.allowed)
        self.assertEqual(observed.state, "WAITING_EXTERNAL")
        self.assertTrue(observed.release_session)


if __name__ == "__main__":
    unittest.main()
