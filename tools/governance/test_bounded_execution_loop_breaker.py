Warning: truncated output (original token count: 3678)
Total output lines: 378

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
        "risk_ledger": clear_ledger(),
    }
    value.update(overrides)
    return value


class PolicyContractTests(unittest.TestCase):
    def test_policy_declares_evidence_generation_and_loop_breaker(self):
        raw = policy()
        self.assertIn("evidence_generation", raw["progress_fingerprint_fields"])
        self.assertIn("review_fingerprint", raw["progress_fingerprint_fields"])
        self.assertEqual(
            raw["retry_counter_scopes"]["external_review_invocations"],
            ["review_fingerprint"],
        )
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
        current = snapsho…1678 tokens truncated…edger()
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
