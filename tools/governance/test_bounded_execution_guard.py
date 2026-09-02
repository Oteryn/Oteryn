#!/usr/bin/env python3
"""Regression tests for the narrow bounded-execution contract."""

from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from bounded_execution_guard import GuardError, decide, failure_fingerprint, progress_fingerprint


ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "ecosystem/bounded-autonomous-execution-policy.json"
POLICY = json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def snapshot(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "repository": "Oteryn/Oteryn",
        "task_id": "69",
        "task_head_sha": "a" * 40,
        "phase": "implementation",
        "blocking_dependency": "",
        "dependency_kind": "none",
        "gate_state": "pending",
        "first_material_failure": "",
        "state": "RUNNING",
        "candidate_frozen": False,
        "material_reason": "",
        "identical_failure_cycles": 0,
        "heavy_validation_attempts": 0,
        "completion_verified": False,
    }
    value.update(changes)
    return value


class NarrowBoundedExecutionTests(unittest.TestCase):
    def test_policy_has_closed_narrow_schema(self) -> None:
        self.assertEqual(
            set(POLICY),
            {
                "schema_version", "policy_id", "lifecycle_authority", "states",
                "progress_fingerprint_fields", "retry_budgets", "candidate_freeze",
                "dependency_semantics", "session_release_states",
            },
        )
        self.assertEqual(len(POLICY["retry_budgets"]), 2)

    def test_narration_and_timestamp_are_not_progress(self) -> None:
        before = snapshot(narration="first", updated_at="yesterday")
        after = snapshot(narration="different", updated_at="today")
        self.assertEqual(progress_fingerprint(before, POLICY), progress_fingerprint(after, POLICY))

    def test_fingerprints_are_deterministic_and_material(self) -> None:
        before = snapshot()
        after = snapshot(task_head_sha="b" * 40)
        self.assertNotEqual(progress_fingerprint(before, POLICY), progress_fingerprint(after, POLICY))
        self.assertEqual(failure_fingerprint(before), failure_fingerprint(copy.deepcopy(before)))

    def test_unchanged_retry_exhaustion_stalls_and_releases(self) -> None:
        current = snapshot(first_material_failure="unit:test_x", identical_failure_cycles=2)
        decision = decide(POLICY, current, "retry", previous=copy.deepcopy(current))
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.state, "STALLED")
        self.assertTrue(decision.release_session)

    def test_zero_retry_denies_after_initial_failure(self) -> None:
        policy = copy.deepcopy(POLICY)
        policy["retry_budgets"]["identical_failure_cycles"] = 0
        current = snapshot(first_material_failure="unit:test_x")
        self.assertFalse(decide(policy, current, "retry", previous=current).allowed)

    def test_heavy_validation_exhaustion_stalls(self) -> None:
        current = snapshot(heavy_validation_attempts=2)
        decision = decide(POLICY, current, "run_heavy_validation", previous=current)
        self.assertEqual((decision.allowed, decision.state, decision.release_session), (False, "STALLED", True))

    def test_retry_and_validation_increment_their_bounded_counters(self) -> None:
        failed = snapshot(first_material_failure="unit:test_x")
        retry = decide(POLICY, failed, "retry", previous=failed)
        heavy = decide(POLICY, snapshot(), "run_heavy_validation", previous=snapshot())
        self.assertEqual(retry.snapshot["identical_failure_cycles"], 1)
        self.assertEqual(heavy.snapshot["heavy_validation_attempts"], 1)

    def test_external_and_owner_dependencies_release(self) -> None:
        external = snapshot(blocking_dependency="ci:123", dependency_kind="external")
        owner = snapshot(blocking_dependency="owner decision", dependency_kind="owner")
        ext = decide(POLICY, external, "mutate")
        blocked = decide(POLICY, owner, "retry")
        self.assertEqual((ext.allowed, ext.state, ext.release_session), (False, "WAITING_EXTERNAL", True))
        self.assertEqual((blocked.allowed, blocked.state, blocked.release_session), (False, "BLOCKED", True))

    def test_observe_remains_allowed_in_released_states(self) -> None:
        for state in ("WAITING_EXTERNAL", "BLOCKED", "STALLED"):
            decision = decide(POLICY, snapshot(state=state), "observe")
            self.assertTrue(decision.allowed)
            self.assertTrue(decision.release_session)

    def test_unchanged_released_task_cannot_resume_operational_work(self) -> None:
        previous = snapshot(state="STALLED")
        current = snapshot(state="RUNNING")
        decision = decide(POLICY, current, "mutate", previous=previous)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.state, "STALLED")

    def test_actual_material_change_resumes_work(self) -> None:
        previous = snapshot(state="WAITING_EXTERNAL", blocking_dependency="ci:1", dependency_kind="external")
        current = snapshot(task_head_sha="b" * 40, gate_state="passed")
        decision = decide(POLICY, current, "mutate", previous=previous)
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.state, "RUNNING")

    def test_frozen_mutate_and_retrigger_fail_without_real_reason(self) -> None:
        previous = snapshot(candidate_frozen=True)
        for action in ("mutate", "retrigger"):
            self.assertFalse(decide(POLICY, copy.deepcopy(previous), action, previous=previous).allowed)
        changed = snapshot(candidate_frozen=True, task_head_sha="b" * 40, material_reason="failing_required_test")
        self.assertTrue(decide(POLICY, changed, "mutate", previous=previous).allowed)

    def test_unfrozen_noop_mutation_and_retrigger_are_denied(self) -> None:
        previous = snapshot()
        for action in ("mutate", "retrigger"):
            decision = decide(POLICY, copy.deepcopy(previous), action, previous=previous)
            self.assertFalse(decision.allowed)
            self.assertIn("unchanged", decision.reason)

    def test_main_only_change_is_not_a_snapshot_coordinate(self) -> None:
        self.assertNotIn("main_sha", POLICY["progress_fingerprint_fields"])

    def test_done_requires_verified_fact_and_is_terminal(self) -> None:
        with self.assertRaises(GuardError):
            decide(POLICY, snapshot(state="DONE"), "observe")
        completed = snapshot(state="READY", completion_verified=True)
        done = decide(POLICY, completed, "complete", previous=snapshot(state="READY"))
        self.assertEqual((done.allowed, done.state), (True, "DONE"))
        terminal = copy.deepcopy(done.snapshot)
        self.assertFalse(decide(POLICY, terminal, "mutate", previous=terminal).allowed)
        self.assertTrue(decide(POLICY, terminal, "observe", previous=terminal).allowed)

    def test_cli_emits_deterministic_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "snapshot.json"
            path.write_text(json.dumps(snapshot()), encoding="utf-8")
            result = subprocess.run(
                ["python3", str(ROOT / "tools/governance/bounded_execution_guard.py"),
                 "--policy", str(POLICY_PATH), "--snapshot", str(path), "--action", "observe"],
                check=True, capture_output=True, text=True,
            )
        self.assertTrue(json.loads(result.stdout)["allowed"])


if __name__ == "__main__":
    unittest.main()
