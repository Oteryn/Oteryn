import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from bounded_execution_guard import GuardError, decide  # noqa: E402


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
        "evidence_generation": "evidence-1",
        "first_material_failure": "",
        "identical_failure_cycles": 0,
        "heavy_validation_runs": 0,
        "external_review_invocations": 0,
        "same_head_gate_rechecks": 0,
        "completion_verified": False,
        "material_change": False,
        "material_change_reason": "",
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
        previous = snapshot(candidate_frozen=True)
        current = copy.deepcopy(previous)
        current["candidate_frozen"] = False
        current["material_change"] = True
        current["material_change_reason"] = "review_finding"
        current["late_material_findings"] = 1
        with self.assertRaises(GuardError):
            decide(previous, current, "observe", POLICY)

        current["post_freeze_material_head_changes"] = 1
        result = decide(previous, current, "observe", POLICY)
        self.assertTrue(result.allowed)

    def test_head_move_inside_already_open_repair_does_not_need_second_increment(self):
        previous = snapshot(
            candidate_frozen=False,
            material_change=True,
            material_change_reason="review_finding",
            late_material_findings=1,
            post_freeze_material_head_changes=1,
        )
        current = copy.deepcopy(previous)
        current["task_head_sha"] = "b" * 40
        result = decide(previous, current, "observe", POLICY)
        self.assertTrue(result.allowed)


class FreezeAdmissionTests(unittest.TestCase):
    def test_pre_threshold_final_qualification_requires_frozen_candidate(self):
        current = snapshot(candidate_frozen=False)
        result = decide(None, current, "enter_final_qualification", POLICY)
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
        unfrozen["material_change_reason"] = "review_finding"
        unfrozen["late_material_findings"] = 3
        unfrozen["post_freeze_material_head_changes"] = 1
        result = decide(admitted, unfrozen, "request_external_review", POLICY)
        self.assertFalse(result.allowed)
        self.assertIn("frozen", result.reason.lower())


class MaterialChangeEvidenceTests(unittest.TestCase):
    def test_frozen_mutation_rejects_material_change_without_durable_evidence(self):
        previous = snapshot(candidate_frozen=True)
        current = copy.deepcopy(previous)
        current["material_change"] = True
        current["material_change_reason"] = "review_finding"
        result = decide(previous, current, "mutate", POLICY)
        self.assertFalse(result.allowed)
        self.assertIn("material", result.reason.lower())

    def test_frozen_mutation_rejects_unrecognized_material_change_reason(self):
        previous = snapshot(candidate_frozen=True)
        current = copy.deepcopy(previous)
        current["material_change"] = True
        current["material_change_reason"] = "because_i_said_so"
        current["evidence_generation"] = "evidence-2"
        result = decide(previous, current, "mutate", POLICY)
        self.assertFalse(result.allowed)
        self.assertIn("reason", result.reason.lower())

    def test_review_finding_reason_is_bound_to_late_finding_increment(self):
        previous = snapshot(candidate_frozen=True)
        current = copy.deepcopy(previous)
        current["material_change"] = True
        current["material_change_reason"] = "review_finding"
        current["late_material_findings"] = 1
        result = decide(previous, current, "mutate", POLICY)
        self.assertTrue(result.allowed)

    def test_frozen_retrigger_is_forbidden_even_with_material_change_evidence(self):
        previous = snapshot(candidate_frozen=True)
        current = copy.deepcopy(previous)
        current["material_change"] = True
        current["material_change_reason"] = "review_finding"
        current["late_material_findings"] = 1
        result = decide(previous, current, "retrigger", POLICY)
        self.assertFalse(result.allowed)
        self.assertIn("retrigger", result.reason.lower())


class DoneTerminalityTests(unittest.TestCase):
    def test_previous_done_cannot_transition_back_to_running(self):
        previous = snapshot(state="DONE", completion_verified=True)
        current = snapshot(
            state="RUNNING",
            candidate_frozen=False,
            completion_verified=False,
        )
        with self.assertRaises(GuardError):
            decide(previous, current, "mutate", POLICY)

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
