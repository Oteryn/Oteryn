import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from bounded_execution_guard import GuardError, decide, progress_fingerprint  # noqa: E402


ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "ecosystem/bounded-autonomous-execution-policy.json"
RISK_CLASSES = (
    "identity_binding",
    "authority_relay",
    "epoch_deadline",
    "retry_budget",
    "concurrency_replay",
    "transaction_persistence",
    "negative_paths",
    "ci_governance",
)


def policy():
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def clear_ledger():
    return {
        name: {"status": "AUDITED_PASS", "reason": "independent audit complete"}
        for name in RISK_CLASSES
    }


def pending_ledger(risk_class="identity_binding"):
    ledger = clear_ledger()
    ledger[risk_class] = {"status": "PENDING", "reason": ""}
    return ledger


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
        "late_material_findings": 0,
        "post_freeze_material_head_changes": 0,
        "audited_late_material_findings": 0,
        "audited_post_freeze_material_head_changes": 0,
        "final_qualification_runs_since_audit": 0,
        "risk_ledger": clear_ledger(),
    }
    value.update(overrides)
    return value


class PolicyContractTests(unittest.TestCase):
    def test_policy_declares_evidence_generation_and_loop_breaker(self):
        raw = policy()
        self.assertIn("evidence_generation", raw["progress_fingerprint_fields"])
        loop = raw["loop_breaker"]
        self.assertEqual(loop["late_material_finding_threshold"], 2)
        self.assertEqual(loop["post_freeze_material_head_change_threshold"], 2)
        self.assertEqual(tuple(loop["risk_classes"]), RISK_CLASSES)
        self.assertEqual(loop["final_qualification_generations_per_audit"], 1)

    def test_provider_cannot_weaken_organization_loop_breaker_thresholds(self):
        for key in (
            "late_material_finding_threshold",
            "post_freeze_material_head_change_threshold",
        ):
            with self.subTest(key=key):
                weakened = policy()
                weakened["loop_breaker"][key] = 3
                with self.assertRaises(GuardError):
                    decide(None, snapshot(), "observe", weakened)

    def test_material_evidence_generation_changes_progress_fingerprint(self):
        first = snapshot(evidence_generation="evidence-1")
        second = snapshot(evidence_generation="evidence-2")
        self.assertNotEqual(
            progress_fingerprint(first, policy()),
            progress_fingerprint(second, policy()),
        )


class RetryScopeRegressionTests(unittest.TestCase):
    def test_exhausted_retry_without_previous_stays_stalled(self):
        current = snapshot(
            state="RUNNING",
            candidate_frozen=False,
            gate_state="failure",
            first_material_failure="same deterministic failure",
            identical_failure_cycles=2,
        )
        result = decide(None, current, "retry", policy())
        self.assertFalse(result.allowed)
        self.assertEqual(result.state, "STALLED")

    def test_external_review_counter_cannot_reset_on_unrelated_phase_change(self):
        previous = snapshot(phase="repair", external_review_invocations=1)
        current = copy.deepcopy(previous)
        current["phase"] = "validate"
        current["external_review_invocations"] = 0
        with self.assertRaises(GuardError):
            decide(previous, current, "observe", policy())

    def test_same_head_recheck_counter_cannot_reset_on_gate_change_same_evidence(self):
        previous = snapshot(gate_state="failure", same_head_gate_rechecks=1)
        current = copy.deepcopy(previous)
        current["gate_state"] = "pending"
        current["same_head_gate_rechecks"] = 0
        with self.assertRaises(GuardError):
            decide(previous, current, "observe", policy())

    def test_boolean_retry_counter_is_rejected(self):
        current = snapshot(identical_failure_cycles=True)
        with self.assertRaises(GuardError):
            decide(None, current, "observe", policy())

    def test_zero_retry_budget_still_allows_initial_attempt_before_failure(self):
        zero = policy()
        zero["retry_budgets"]["identical_failure_cycles"] = 0
        current = snapshot(
            state="RUNNING",
            candidate_frozen=False,
            identical_failure_cycles=0,
            first_material_failure="",
        )
        result = decide(None, current, "retry", zero)
        self.assertTrue(result.allowed)

    def test_zero_retry_budget_blocks_retry_after_first_material_failure(self):
        zero = policy()
        zero["retry_budgets"]["identical_failure_cycles"] = 0
        current = snapshot(
            state="RUNNING",
            candidate_frozen=False,
            gate_state="failure",
            identical_failure_cycles=0,
            first_material_failure="deterministic failure",
        )
        result = decide(None, current, "retry", zero)
        self.assertFalse(result.allowed)
        self.assertEqual(result.state, "STALLED")


class LoopBreakerRegressionTests(unittest.TestCase):
    def test_done_retrigger_is_denied(self):
        current = snapshot(
            state="DONE",
            completion_verified=True,
            candidate_frozen=False,
        )
        result = decide(None, current, "retrigger", policy())
        self.assertFalse(result.allowed)
        self.assertEqual(result.state, "DONE")

    def test_risk_ledger_is_not_required_before_loop_breaker_threshold(self):
        current = snapshot(state="RUNNING", candidate_frozen=False)
        current.pop("risk_ledger")
        result = decide(None, current, "observe", policy())
        self.assertTrue(result.allowed)

    def test_risk_ledger_is_required_once_loop_breaker_threshold_is_reached(self):
        current = snapshot(late_material_findings=2)
        current.pop("risk_ledger")
        with self.assertRaises(GuardError):
            decide(None, current, "observe", policy())

    def test_second_late_finding_blocks_final_review_until_fresh_audit(self):
        current = snapshot(
            late_material_findings=2,
            audited_late_material_findings=0,
        )
        result = decide(None, current, "request_external_review", policy())
        self.assertFalse(result.allowed)
        self.assertIn("loop_breaker", result.reason.lower())

    def test_second_post_freeze_head_change_blocks_heavy_final_validation(self):
        current = snapshot(
            post_freeze_material_head_changes=2,
            audited_post_freeze_material_head_changes=0,
        )
        result = decide(None, current, "run_heavy_validation", policy())
        self.assertFalse(result.allowed)
        self.assertIn("loop_breaker", result.reason.lower())

    def test_post_freeze_head_move_must_increment_head_change_counter(self):
        previous = snapshot(
            task_head_sha="a" * 40,
            candidate_frozen=True,
            post_freeze_material_head_changes=0,
        )
        current = snapshot(
            task_head_sha="b" * 40,
            candidate_frozen=False,
            material_change=True,
            post_freeze_material_head_changes=0,
        )
        with self.assertRaises(GuardError):
            decide(previous, current, "observe", policy())

    def test_audited_counters_cannot_advance_outside_loop_breaker_phase(self):
        previous = snapshot(
            late_material_findings=2,
            audited_late_material_findings=0,
        )
        current = copy.deepcopy(previous)
        current["audited_late_material_findings"] = 2
        with self.assertRaises(GuardError):
            decide(previous, current, "observe", policy())

    def test_not_applicable_risk_class_requires_reason(self):
        ledger = clear_ledger()
        ledger["transaction_persistence"] = {
            "status": "NOT_APPLICABLE",
            "reason": "",
        }
        current = snapshot(late_material_findings=2, risk_ledger=ledger)
        with self.assertRaises(GuardError):
            decide(None, current, "observe", policy())

    def test_incomplete_risk_ledger_cannot_mark_audit_current(self):
        current = snapshot(
            late_material_findings=2,
            audited_late_material_findings=2,
            risk_ledger=pending_ledger("authority_relay"),
        )
        result = decide(None, current, "request_external_review", policy())
        self.assertFalse(result.allowed)
        self.assertIn("loop_breaker", result.reason.lower())

    def test_loop_breaker_audit_may_advance_audited_counters_after_reopened_ledger(self):
        previous = snapshot(
            phase="LOOP_BREAKER_AUDIT",
            late_material_findings=2,
            audited_late_material_findings=0,
            risk_ledger=pending_ledger(),
        )
        current = copy.deepcopy(previous)
        current["risk_ledger"] = clear_ledger()
        current["audited_late_material_findings"] = 2
        result = decide(previous, current, "observe", policy())
        self.assertTrue(result.allowed)

    def test_audit_cannot_self_advance_from_already_terminal_ledger(self):
        previous = snapshot(
            phase="LOOP_BREAKER_AUDIT",
            late_material_findings=2,
            audited_late_material_findings=0,
            risk_ledger=clear_ledger(),
        )
        current = copy.deepcopy(previous)
        current["audited_late_material_findings"] = 2
        with self.assertRaises(GuardError):
            decide(previous, current, "observe", policy())

    def test_final_qualification_admission_must_consume_the_single_generation(self):
        current = snapshot(
            late_material_findings=2,
            audited_late_material_findings=2,
            post_freeze_material_head_changes=2,
            audited_post_freeze_material_head_changes=2,
            final_qualification_runs_since_audit=0,
        )
        result = decide(None, current, "enter_final_qualification", policy())
        self.assertFalse(result.allowed)
        self.assertIn("record", result.reason.lower())

        admitted = copy.deepcopy(current)
        admitted["final_qualification_runs_since_audit"] = 1
        result = decide(current, admitted, "enter_final_qualification", policy())
        self.assertTrue(result.allowed)

        duplicate = copy.deepcopy(admitted)
        duplicate["final_qualification_runs_since_audit"] = 2
        result = decide(admitted, duplicate, "enter_final_qualification", policy())
        self.assertFalse(result.allowed)
        self.assertIn("qualification", result.reason.lower())

    def test_final_actions_require_consumed_qualification_generation_after_audit(self):
        for action in (
            "request_external_review",
            "run_heavy_validation",
            "same_head_gate_recheck",
            "complete",
        ):
            with self.subTest(action=action):
                current = snapshot(
                    late_material_findings=2,
                    audited_late_material_findings=2,
                    final_qualification_runs_since_audit=0,
                    completion_verified=True,
                )
                result = decide(None, current, action, policy())
                self.assertFalse(result.allowed)
                self.assertIn("qualification", result.reason.lower())

    def test_final_actions_are_admitted_after_single_generation_is_consumed(self):
        counter_by_action = {
            "request_external_review": "external_review_invocations",
            "run_heavy_validation": "heavy_validation_runs",
            "same_head_gate_recheck": "same_head_gate_rechecks",
        }
        for action in (
            "request_external_review",
            "run_heavy_validation",
            "same_head_gate_recheck",
            "complete",
        ):
            with self.subTest(action=action):
                previous = snapshot(
                    late_material_findings=2,
                    audited_late_material_findings=2,
                    final_qualification_runs_since_audit=1,
                    completion_verified=True,
                )
                current = copy.deepcopy(previous)
                if action in counter_by_action:
                    current[counter_by_action[action]] = 1
                result = decide(previous, current, action, policy())
                self.assertTrue(result.allowed)

    def test_new_late_finding_after_audit_reopens_loop_breaker(self):
        current = snapshot(
            late_material_findings=3,
            audited_late_material_findings=2,
            final_qualification_runs_since_audit=1,
        )
        result = decide(None, current, "request_external_review", policy())
        self.assertFalse(result.allowed)
        self.assertIn("loop_breaker", result.reason.lower())


if __name__ == "__main__":
    unittest.main()
