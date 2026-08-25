import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from bounded_execution_guard import (  # noqa: E402
    GuardError,
    decide,
    progress_fingerprint,
)


POLICY = {
    "schema_version": 1,
    "states": ["RUNNING", "WAITING_EXTERNAL", "BLOCKED", "STALLED", "READY", "DONE"],
    "progress_fingerprint_fields": [
        "repository",
        "task_id",
        "task_head_sha",
        "phase",
        "blocking_dependency",
        "dependency_kind",
        "gate_state",
        "review_generation",
        "first_material_failure",
    ],
    "retry_budgets": {
        "identical_failure_cycles": 2,
        "heavy_validation_attempts": 2,
        "external_review_invocations_per_fingerprint": 1,
        "same_head_gate_rechecks_per_evidence_generation": 1,
    },
    "candidate_freeze": {
        "forbidden_actions_without_material_change": ["mutate", "retrigger"]
    },
    "session_release_states": ["WAITING_EXTERNAL", "BLOCKED", "STALLED", "DONE"],
}


def snapshot(**overrides):
    value = {
        "repository": "Oteryn/Oteryn",
        "task_id": "OTERYN-STALL-GUARD-001",
        "state": "RUNNING",
        "phase": "validate",
        "task_head_sha": "a" * 40,
        "candidate_frozen": False,
        "blocking_dependency": "",
        "dependency_kind": "",
        "gate_state": "pending",
        "review_generation": "",
        "first_material_failure": "",
        "identical_failure_cycles": 0,
        "heavy_validation_runs": 0,
        "external_review_invocations": 0,
        "same_head_gate_rechecks": 0,
        "completion_verified": False,
        "material_change": False,
        "updated_at": "2026-08-25T14:00:00Z",
        "narration": "first observation",
    }
    value.update(overrides)
    return value


class ProgressFingerprintTests(unittest.TestCase):
    def test_fingerprint_ignores_timestamp_and_narration(self):
        first = snapshot()
        second = copy.deepcopy(first)
        second["updated_at"] = "2026-08-25T15:00:00Z"
        second["narration"] = "different chat text"
        self.assertEqual(
            progress_fingerprint(first, POLICY),
            progress_fingerprint(second, POLICY),
        )

    def test_fingerprint_changes_when_material_gate_state_changes(self):
        first = snapshot(gate_state="failure")
        second = snapshot(gate_state="success")
        self.assertNotEqual(
            progress_fingerprint(first, POLICY),
            progress_fingerprint(second, POLICY),
        )


class DecisionTests(unittest.TestCase):
    def test_frozen_candidate_denies_retrigger_without_material_change(self):
        current = snapshot(candidate_frozen=True, state="READY")
        result = decide(None, current, "retrigger", POLICY)
        self.assertFalse(result.allowed)
        self.assertEqual(result.state, "READY")
        self.assertIn("frozen", result.reason.lower())

    def test_frozen_denial_releases_blocked_and_stalled_sessions(self):
        for state in ("BLOCKED", "STALLED"):
            with self.subTest(state=state):
                current = snapshot(candidate_frozen=True, state=state)
                result = decide(None, current, "retrigger", POLICY)
                self.assertFalse(result.allowed)
                self.assertEqual(result.state, state)
                self.assertTrue(result.release_session)

    def test_external_dependency_becomes_waiting_and_releases_session(self):
        previous = snapshot(
            candidate_frozen=True,
            state="WAITING_EXTERNAL",
            blocking_dependency="external_review",
            dependency_kind="external",
            gate_state="failure",
            first_material_failure="review evidence not ready",
        )
        current = copy.deepcopy(previous)
        current["updated_at"] = "2026-08-25T14:05:00Z"
        result = decide(previous, current, "observe", POLICY)
        self.assertTrue(result.allowed)
        self.assertEqual(result.state, "WAITING_EXTERNAL")
        self.assertTrue(result.release_session)

    def test_external_dependency_denies_operational_actions_until_fact_changes(self):
        current = snapshot(
            state="WAITING_EXTERNAL",
            blocking_dependency="external_review",
            dependency_kind="external",
            gate_state="failure",
            first_material_failure="review evidence not ready",
        )
        for action in (
            "mutate",
            "retry",
            "retrigger",
            "run_heavy_validation",
            "request_external_review",
            "same_head_gate_recheck",
        ):
            with self.subTest(action=action):
                result = decide(current, copy.deepcopy(current), action, POLICY)
                self.assertFalse(result.allowed)
                self.assertEqual(result.state, "WAITING_EXTERNAL")
                self.assertTrue(result.release_session)

    def test_second_identical_local_failure_stalls_instead_of_retrying_again(self):
        previous = snapshot(
            gate_state="failure",
            first_material_failure="same deterministic failure",
            identical_failure_cycles=1,
        )
        current = copy.deepcopy(previous)
        current["identical_failure_cycles"] = 2
        result = decide(previous, current, "retry", POLICY)
        self.assertFalse(result.allowed)
        self.assertEqual(result.state, "STALLED")
        self.assertTrue(result.release_session)

    def test_retry_counters_cannot_regress_without_material_progress(self):
        counter_names = (
            "identical_failure_cycles",
            "heavy_validation_runs",
            "external_review_invocations",
            "same_head_gate_rechecks",
        )
        for counter in counter_names:
            with self.subTest(counter=counter):
                previous = snapshot(**{counter: 1})
                current = snapshot(**{counter: 0})
                with self.assertRaises(GuardError):
                    decide(previous, current, "observe", POLICY)

    def test_retry_counters_may_restart_after_material_progress(self):
        previous = snapshot(
            task_head_sha="a" * 40,
            identical_failure_cycles=2,
            heavy_validation_runs=2,
            external_review_invocations=1,
            same_head_gate_rechecks=1,
        )
        current = snapshot(task_head_sha="b" * 40)
        result = decide(previous, current, "observe", POLICY)
        self.assertTrue(result.allowed)

    def test_unverified_done_snapshot_is_invalid_for_every_action(self):
        current = snapshot(state="DONE", completion_verified=False)
        with self.assertRaises(GuardError):
            decide(None, current, "observe", POLICY)

    def test_done_requires_verified_completion(self):
        current = snapshot(state="READY", completion_verified=False)
        result = decide(None, current, "complete", POLICY)
        self.assertFalse(result.allowed)
        self.assertNotEqual(result.state, "DONE")

        verified = snapshot(state="READY", completion_verified=True)
        result = decide(None, verified, "complete", POLICY)
        self.assertTrue(result.allowed)
        self.assertEqual(result.state, "DONE")

    def test_rejected_completion_preserves_release_states(self):
        for state in ("WAITING_EXTERNAL", "BLOCKED", "STALLED"):
            with self.subTest(state=state):
                current = snapshot(state=state, completion_verified=False)
                result = decide(None, current, "complete", POLICY)
                self.assertFalse(result.allowed)
                self.assertEqual(result.state, state)
                self.assertTrue(result.release_session)

    def test_unchanged_blocked_or_stalled_task_cannot_resume_operational_work(self):
        for state in ("BLOCKED", "STALLED"):
            previous = snapshot(state=state, first_material_failure="unchanged failure")
            current = snapshot(
                state="RUNNING",
                first_material_failure="unchanged failure",
            )
            for action in ("mutate", "retry", "run_heavy_validation"):
                with self.subTest(state=state, action=action):
                    result = decide(previous, current, action, POLICY)
                    self.assertFalse(result.allowed)
                    self.assertEqual(result.state, state)
                    self.assertTrue(result.release_session)

    def test_external_review_budget_prevents_duplicate_invocation(self):
        current = snapshot(external_review_invocations=1)
        result = decide(None, current, "request_external_review", POLICY)
        self.assertFalse(result.allowed)
        self.assertEqual(result.state, "WAITING_EXTERNAL")
        self.assertTrue(result.release_session)

    def test_heavy_validation_budget_prevents_third_full_run(self):
        current = snapshot(
            gate_state="failure",
            first_material_failure="full suite still fails",
            heavy_validation_runs=2,
        )
        result = decide(None, current, "run_heavy_validation", POLICY)
        self.assertFalse(result.allowed)
        self.assertEqual(result.state, "STALLED")


if __name__ == "__main__":
    unittest.main()
