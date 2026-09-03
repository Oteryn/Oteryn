#!/usr/bin/env python3
"""Focused RED regressions for Codex findings on PR #139.

These tests intentionally isolate only the reviewed trust-boundary gaps:
- rotation must prove a replacement/persistent worker, not mere locator liveness;
- owner reinvocation must not be claimed while real automatic continuation exists;
- capability evidence must be fresh against trusted current time.
"""
from __future__ import annotations

import unittest

from agent_continuation_policy import (
    ContinuationPolicyError,
    select_execution_surface,
    validate_continuation_snapshot,
)
from test_agent_continuation_policy import (
    FakeBoundedAuthority,
    FakeCapabilityAuthority,
    FakeLineageAuthority,
    FakeMechanismVerifier,
    FakeRemainingWorkAuthority,
    FakeTransitionAuthority,
    capability_snapshot,
    load_policy,
    POLICY_PATH,
    snapshot,
    trusted_task,
)


class WorkerAwareMechanismVerifier(FakeMechanismVerifier):
    def __init__(
        self,
        *,
        live_bound: bool = True,
        replacement_worker: bool = True,
        automatic_available: bool = False,
    ) -> None:
        super().__init__(live_bound=live_bound)
        self.replacement_worker = replacement_worker
        self.automatic_available = automatic_available
        self.worker_proof_calls = 0
        self.automatic_probe_calls = 0

    def proves_replacement_or_persistent_worker(
        self,
        mechanism: str,
        locator: str,
        trusted: object,
        expected_next_action: str,
    ) -> bool:
        self.worker_proof_calls += 1
        return self.replacement_worker

    def has_automatic_continuation(
        self,
        trusted: object,
        expected_next_action: str,
    ) -> bool:
        self.automatic_probe_calls += 1
        return self.automatic_available


class TimeBoundCapabilityAuthority(FakeCapabilityAuthority):
    def __init__(self, result: object, *, current_time: str) -> None:
        super().__init__(result)  # type: ignore[arg-type]
        self._current_time = current_time
        self.time_calls = 0

    def current_time(self, trusted: object) -> str:
        self.time_calls += 1
        return self._current_time


class ReviewRepairRegressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(POLICY_PATH)

    def validate_checkpoint(
        self,
        value: dict[str, object],
        *,
        bounded: FakeBoundedAuthority,
        verifier: WorkerAwareMechanismVerifier,
    ) -> None:
        validate_continuation_snapshot(
            self.policy,
            value,
            trusted_task=trusted_task(),
            lineage_authority=FakeLineageAuthority(),
            transition_authority=FakeTransitionAuthority(),
            bounded_authority=bounded,
            mechanism_verifier=verifier,
            remaining_work_authority=FakeRemainingWorkAuthority(),
            validation_mode="checkpoint_write",
        )

    def test_rotate_rejects_live_locator_without_replacement_worker_proof(self) -> None:
        value = snapshot(
            worker_disposition="rotate_resumable",
            resume_mechanism="scheduled_task",
            resume_locator="resume://scheduled/notification-only",
        )
        verifier = WorkerAwareMechanismVerifier(
            live_bound=True,
            replacement_worker=False,
        )
        with self.assertRaisesRegex(
            ContinuationPolicyError,
            "replacement or persistent worker",
        ):
            self.validate_checkpoint(
                value,
                bounded=FakeBoundedAuthority("RUNNING"),
                verifier=verifier,
            )

    def test_owner_reinvoke_rejects_when_automatic_continuation_exists(self) -> None:
        value = snapshot(
            bounded_lifecycle_state="BLOCKED",
            worker_disposition="stop_reinvoke_required",
            resume_mechanism="owner_reinvoke",
            resume_locator=None,
        )
        verifier = WorkerAwareMechanismVerifier(automatic_available=True)
        with self.assertRaisesRegex(
            ContinuationPolicyError,
            "automatic continuation",
        ):
            self.validate_checkpoint(
                value,
                bounded=FakeBoundedAuthority("BLOCKED"),
                verifier=verifier,
            )

    def test_capability_snapshot_policy_has_bounded_freshness(self) -> None:
        self.assertEqual(
            self.policy.get("capability_snapshot_freshness"),
            {"max_age_seconds": 900},
        )

    def test_selector_rejects_stale_capability_snapshot(self) -> None:
        stale = capability_snapshot()
        authority = TimeBoundCapabilityAuthority(
            stale,
            current_time="2026-09-02T18:25:01Z",
        )
        with self.assertRaisesRegex(ContinuationPolicyError, "capability snapshot is stale"):
            select_execution_surface(
                self.policy,
                trusted_task=trusted_task(),
                required_capability="chat_tools",
                capability_authority=authority,
            )


if __name__ == "__main__":
    unittest.main()
