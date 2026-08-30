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
    value = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    value["progress_fingerprint_fields"] = list(value["progress_fingerprint_fields"])
    if "evidence_generation" not in value["progress_fingerprint_fields"]:
        value["progress_fingerprint_fields"].append("evidence_generation")
    value.setdefault(
        "loop_breaker",
        {
            "late_material_finding_threshold": 2,
            "post_freeze_material_head_change_threshold": 2,
            "risk_classes": list(RISK_CLASSES),
            "ledger_terminal_statuses": ["AUDITED_PASS", "NOT_APPLICABLE"],
            "final_qualification_generations_per_audit": 1,
        },
    )
    return value


def clear_ledger():
    return {
        name: {"status": "AUDITED_PASS", "reason": "independent audit complete"}
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
        raw = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        self.assertIn("evidence_generation", raw["progress_fingerprint_fields"])
        loop = raw["loop_breaker"]
        self.assertEqual(loop["late_material_finding_threshold"], 2)
        self.assertEqual(loop["post_freeze_material_head_change_threshold"], 2)
        self.assertEqual(tuple(loop["risk_classes"]), RISK_CLASSES)
        self.assertEqual(loop["final_qualification_generations_per_audit"], 1)

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

    def test_initial_attempt_is_not_blocked_without_a_failure(self):
        current = snapshot(
            state="RUNNING",
            candidate_frozen=False,
            identical_failure_cycles=2,
            first_material_failure="",
        )
        result = decide(None, current, "retry", policy())
        self.assertTrue(result.allowed)


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

    def test_not_applicable_risk_class_requires_reason(self):
        ledger = clear_ledger()
        ledger["transaction_persistence"] = {
            "status": "NOT_APPLICABLE",
            "reason": "",
        }
        current = snapshot(risk_ledger=ledger)
        with self.assertRaises(GuardError):
            decide(None, current, "observe", policy())

    def test_incomplete_risk_ledger_cannot_mark_audit_current(self):
        ledger = clear_ledger()
        ledger["authority_relay"] = {"status": "PENDING", "reason": ""}
        current = snapshot(
            late_material_findings=2,
            audited_late_material_findings=2,
            risk_ledger=ledger,
        )
        result = decide(None, current, "request_external_review", policy())
        self.assertFalse(result.allowed)
        self.assertIn("loop_breaker", result.reason.lower())

    def test_clear_audit_allows_exactly_one_new_final_qualification_generation(self):
        current = snapshot(
            late_material_findings=2,
            audited_late_material_findings=2,
            post_freeze_material_head_changes=2,
            audited_post_freeze_material_head_changes=2,
            final_qualification_runs_since_audit=0,
        )
        result = decide(None, current, "enter_final_qualification", policy())
        self.assertTrue(result.allowed)

        consumed = copy.deepcopy(current)
        consumed["final_qualification_runs_since_audit"] = 1
        result = decide(current, consumed, "enter_final_qualification", policy())
        self.assertFalse(result.allowed)
        self.assertIn("qualification", result.reason.lower())

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
