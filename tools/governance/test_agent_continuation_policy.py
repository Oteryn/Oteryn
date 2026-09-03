#!/usr/bin/env python3
"""Regression tests for the #108 persistent continuation contract."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from agent_continuation_policy import (
    ContinuationPolicyError,
    ExecutionSurfaceUnavailable,
    StableTaskLineageKey,
    TrustedCapabilitySnapshot,
    TrustedTaskIdentity,
    load_policy,
    select_execution_surface,
    validate_continuation_snapshot,
    validate_policy,
)


ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "ecosystem/agent-continuation-policy.json"

WORKER_DISPOSITIONS = {
    "continue_current",
    "release_waiting",
    "rotate_resumable",
    "stop_reinvoke_required",
    "terminal",
}
RESUME_MECHANISMS = {
    "same_session",
    "github_native",
    "scheduled_task",
    "work_event_trigger",
    "work_persistent",
    "owner_reinvoke",
    "none_terminal",
}
EXECUTION_SURFACES = {"chat", "github_native", "work", "codex"}
REQUIRED_SNAPSHOT_FIELDS = {
    "repository",
    "task_id",
    "checkpoint_lineage_token",
    "task_branch",
    "pr_applicable",
    "pr_id",
    "task_head_sha",
    "phase",
    "bounded_lifecycle_state",
    "last_material_progress",
    "completed_work",
    "evidence_refs",
    "bounded_continuity_ref",
    "blockers",
    "context_pressure",
    "worker_disposition",
    "resume_mechanism",
    "resume_locator",
    "next_action",
}


def lineage() -> StableTaskLineageKey:
    return StableTaskLineageKey(
        repository="Oteryn/Oteryn",
        task_id="108",
        checkpoint_lineage_token="continuation-lineage-108",
    )


def trusted_task(**changes: object) -> TrustedTaskIdentity:
    values: dict[str, object] = {
        "lineage_key": lineage(),
        "task_branch": "governance/chat-first-persistent-autonomy-108",
        "pr_applicable": True,
        "pr_id": "139",
        "task_head_sha": "a" * 40,
        "expected_next_action": "implement the continuation policy",
    }
    values.update(changes)
    return TrustedTaskIdentity(**values)  # type: ignore[arg-type]


def snapshot(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "repository": "Oteryn/Oteryn",
        "task_id": "108",
        "checkpoint_lineage_token": "continuation-lineage-108",
        "task_branch": "governance/chat-first-persistent-autonomy-108",
        "pr_applicable": True,
        "pr_id": "139",
        "task_head_sha": "a" * 40,
        "phase": "implementation",
        "bounded_lifecycle_state": "RUNNING",
        "last_material_progress": "RED continuation contract specified",
        "completed_work": [],
        "evidence_refs": [],
        "bounded_continuity_ref": "bounded://Oteryn/Oteryn/108/current",
        "blockers": [],
        "context_pressure": "normal",
        "worker_disposition": "continue_current",
        "resume_mechanism": "same_session",
        "resume_locator": None,
        "next_action": "implement the continuation policy",
    }
    value.update(changes)
    return value


class FakeLineageAuthority:
    def __init__(self, predecessor: dict[str, object] | None = None, *, proves_none: bool = True) -> None:
        self.predecessor = copy.deepcopy(predecessor)
        self.proves_none = proves_none
        self.keys: list[StableTaskLineageKey] = []

    def latest_predecessor(self, key: StableTaskLineageKey) -> dict[str, object] | None:
        self.keys.append(key)
        return copy.deepcopy(self.predecessor)

    def proves_no_predecessor(self, key: StableTaskLineageKey) -> bool:
        self.keys.append(key)
        return self.proves_none


class FakeTransitionAuthority:
    def __init__(self, *, allowed: bool = True) -> None:
        self.allowed = allowed
        self.calls: list[tuple[dict[str, object], TrustedTaskIdentity, str]] = []

    def proves_transition(
        self,
        historical: dict[str, object],
        current_task: TrustedTaskIdentity,
        current_bounded_state: str,
    ) -> bool:
        self.calls.append((copy.deepcopy(historical), current_task, current_bounded_state))
        return self.allowed


class FakeBoundedAuthority:
    RELEASED = {"WAITING_EXTERNAL", "BLOCKED", "STALLED", "DONE"}
    TERMINAL = {"DONE"}

    def __init__(
        self,
        state: str = "RUNNING",
        *,
        matches_current: bool = True,
        preserves_continuity: bool = True,
    ) -> None:
        self.state = state
        self.matches_current = matches_current
        self.preserves_continuity = preserves_continuity

    def current_state(self, trusted: TrustedTaskIdentity) -> str:
        return self.state

    def releases_worker_ownership(self, state: str, trusted: TrustedTaskIdentity) -> bool:
        return state in self.RELEASED

    def is_terminal(self, state: str, trusted: TrustedTaskIdentity) -> bool:
        return state in self.TERMINAL

    def matches_current_retry_and_evidence_state(
        self, proposed: dict[str, object], trusted: TrustedTaskIdentity
    ) -> bool:
        return self.matches_current

    def preserves_retry_and_evidence_continuity(
        self,
        previous: dict[str, object],
        proposed: dict[str, object],
        trusted: TrustedTaskIdentity,
    ) -> bool:
        return self.preserves_continuity


class FakeMechanismVerifier:
    def __init__(
        self,
        *,
        live_bound: bool = True,
        replacement_worker: bool = True,
        automatic_available: bool = False,
        historical_event: bool = True,
        owner_reinvoke: bool = True,
    ) -> None:
        self.live_bound = live_bound
        self.replacement_worker = replacement_worker
        self.automatic_available = automatic_available
        self.historical_event = historical_event
        self.owner_reinvoke = owner_reinvoke
        self.live_calls: list[tuple[str, str, TrustedTaskIdentity, str]] = []
        self.replacement_calls: list[tuple[str, str, TrustedTaskIdentity, str]] = []
        self.automatic_calls = 0
        self.event_calls = 0
        self.owner_calls = 0

    def is_live_and_bound(
        self,
        mechanism: str,
        locator: str,
        trusted: TrustedTaskIdentity,
        expected_next_action: str,
    ) -> bool:
        self.live_calls.append((mechanism, locator, trusted, expected_next_action))
        return self.live_bound

    def proves_replacement_or_persistent_worker(
        self,
        mechanism: str,
        locator: str,
        trusted: TrustedTaskIdentity,
        expected_next_action: str,
    ) -> bool:
        self.replacement_calls.append((mechanism, locator, trusted, expected_next_action))
        return self.replacement_worker

    def has_automatic_continuation(
        self,
        trusted: TrustedTaskIdentity,
        expected_next_action: str,
    ) -> bool:
        self.automatic_calls += 1
        return self.automatic_available

    def verify_historical_resume_event(
        self, historical: dict[str, object], trusted: TrustedTaskIdentity
    ) -> bool:
        self.event_calls += 1
        return self.historical_event

    def verify_owner_reinvocation(
        self, historical: dict[str, object], trusted: TrustedTaskIdentity
    ) -> bool:
        self.owner_calls += 1
        return self.owner_reinvoke


class FakeRemainingWorkAuthority:
    def __init__(self, *, safe_without_worker: bool = True) -> None:
        self.safe_without_worker = safe_without_worker
        self.calls = 0

    def all_remaining_work_can_complete_without_agent_worker(
        self, trusted: TrustedTaskIdentity
    ) -> bool:
        self.calls += 1
        return self.safe_without_worker


class FakeCapabilityAuthority:
    def __init__(
        self,
        result: TrustedCapabilitySnapshot,
        *,
        current_time: str = "2026-09-02T18:10:00Z",
    ) -> None:
        self.result = result
        self._current_time = current_time
        self.calls: list[tuple[TrustedTaskIdentity, str | None]] = []
        self.time_calls = 0

    def current_snapshot(
        self, trusted: TrustedTaskIdentity, required_capability: str | None
    ) -> TrustedCapabilitySnapshot:
        self.calls.append((trusted, required_capability))
        return self.result

    def current_time(self, trusted: TrustedTaskIdentity) -> str:
        self.time_calls += 1
        return self._current_time


def capability_snapshot(
    *,
    required_capability: str | None = "chat_tools",
    compatible: tuple[str, ...] = ("chat",),
    available: tuple[str, ...] = ("chat",),
    authorized: tuple[str, ...] = ("chat",),
    exhausted: bool = False,
    evidence: tuple[str, ...] = ("capability://current-session",),
) -> TrustedCapabilitySnapshot:
    return TrustedCapabilitySnapshot(
        observed_at="2026-09-02T18:10:00Z",
        required_capability=required_capability,
        compatible_surfaces=compatible,
        available_surfaces=available,
        authorized_surfaces=authorized,
        safe_fallbacks_exhausted=exhausted,
        evidence_refs=evidence,
    )


class PersistentContinuationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(POLICY_PATH)
        validate_policy(cls.policy)

    def validate(
        self,
        value: dict[str, object],
        *,
        task: TrustedTaskIdentity | None = None,
        lineage_authority: FakeLineageAuthority | None = None,
        transition_authority: FakeTransitionAuthority | None = None,
        bounded_authority: FakeBoundedAuthority | None = None,
        mechanism_verifier: FakeMechanismVerifier | None = None,
        remaining_work_authority: FakeRemainingWorkAuthority | None = None,
        mode: str = "checkpoint_write",
    ) -> None:
        validate_continuation_snapshot(
            self.policy,
            value,
            trusted_task=task or trusted_task(),
            lineage_authority=lineage_authority or FakeLineageAuthority(),
            transition_authority=transition_authority or FakeTransitionAuthority(),
            bounded_authority=bounded_authority or FakeBoundedAuthority(),
            mechanism_verifier=mechanism_verifier or FakeMechanismVerifier(),
            remaining_work_authority=remaining_work_authority or FakeRemainingWorkAuthority(),
            validation_mode=mode,
        )

    def assertRejected(self, value: dict[str, object], **kwargs: object) -> None:
        with self.assertRaises(ContinuationPolicyError):
            self.validate(value, **kwargs)  # type: ignore[arg-type]

    def test_policy_is_closed_and_does_not_duplicate_bounded_lifecycle(self) -> None:
        self.assertEqual(self.policy["schema_version"], 1)
        self.assertEqual(self.policy["policy_id"], "oteryn-agent-continuation-v1")
        self.assertEqual(self.policy["continuation_authority"], "Oteryn/Oteryn#108")
        self.assertEqual(self.policy["bounded_execution_authority"], "Oteryn/Oteryn#69")
        self.assertEqual(set(self.policy["worker_dispositions"]), WORKER_DISPOSITIONS)
        self.assertEqual(set(self.policy["resume_mechanisms"]), RESUME_MECHANISMS)
        self.assertEqual(set(self.policy["execution_surfaces"]), EXECUTION_SURFACES)
        self.assertEqual(self.policy["blocked_result"], "BLOCKED_CAPABILITY_UNAVAILABLE")
        self.assertEqual(len(self.policy["coordinates"]), 6)
        for forbidden in ("states", "bounded_states", "retry_budgets", "retry_counts"):
            self.assertNotIn(forbidden, self.policy)

    def test_policy_rejects_unknown_top_level_keys(self) -> None:
        malformed = copy.deepcopy(self.policy)
        malformed["retry_budgets"] = {"identical_failure_cycles": 999}
        with self.assertRaises(ContinuationPolicyError):
            validate_policy(malformed)

    def test_snapshot_uses_exact_closed_semantic_minimum(self) -> None:
        self.assertEqual(set(snapshot()), REQUIRED_SNAPSHOT_FIELDS)
        self.validate(snapshot())
        for field in sorted(REQUIRED_SNAPSHOT_FIELDS):
            malformed = snapshot()
            del malformed[field]
            self.assertRejected(malformed)
        malformed = snapshot(untrusted_extra_field="forbidden")
        self.assertRejected(malformed)

    def test_snapshot_scalar_shapes_fail_closed(self) -> None:
        string_fields = (
            "task_id",
            "checkpoint_lineage_token",
            "task_branch",
            "phase",
            "bounded_lifecycle_state",
            "last_material_progress",
            "bounded_continuity_ref",
            "next_action",
        )
        for field in string_fields:
            for invalid in ("", "   ", 1, True, {}, []):
                self.assertRejected(snapshot(**{field: invalid}))
        for invalid in ("", "Oteryn", "Oteryn/Oteryn/Extra", 1, None):
            self.assertRejected(snapshot(repository=invalid))
        for invalid in ("A" * 40, "a" * 39, "a" * 41, "z" * 40, 1, None):
            self.assertRejected(snapshot(task_head_sha=invalid))

    def test_pr_applicability_and_pr_id_are_exact(self) -> None:
        for invalid in (0, 1, "true", None, []):
            self.assertRejected(snapshot(pr_applicable=invalid))
        for invalid in (None, "", "   ", 123, True):
            self.assertRejected(snapshot(pr_applicable=True, pr_id=invalid))
        self.validate(snapshot(pr_applicable=False, pr_id=None), task=trusted_task(pr_applicable=False, pr_id=None))
        self.assertRejected(snapshot(pr_applicable=False, pr_id="139"), task=trusted_task(pr_applicable=False, pr_id=None))

    def test_list_shapes_are_unique_nonempty_strings(self) -> None:
        for field in ("completed_work", "evidence_refs", "blockers"):
            self.validate(snapshot(**{field: []}))
            self.validate(snapshot(**{field: ["evidence://one", "evidence://two"]}))
            for invalid in (
                "not-a-list",
                ["duplicate", "duplicate"],
                [""],
                ["   "],
                [1],
                [{}],
            ):
                self.assertRejected(snapshot(**{field: invalid}))

    def test_context_pressure_and_closed_vocabularies_are_exact(self) -> None:
        for valid in ("not_applicable", "normal", "elevated", "rotate_required"):
            self.validate(snapshot(context_pressure=valid))
        for invalid in (None, True, 42, {}, [], "token_count_12345", "unknown"):
            self.assertRejected(snapshot(context_pressure=invalid))
        self.assertRejected(snapshot(worker_disposition="WAITING"))
        self.assertRejected(snapshot(resume_mechanism="background_magic"))

    def test_stable_lineage_and_mutable_coordinates_are_bound_to_trusted_task(self) -> None:
        self.validate(snapshot())
        self.assertRejected(snapshot(task_id="109"))
        self.assertRejected(snapshot(checkpoint_lineage_token="other-lineage"))
        self.assertRejected(snapshot(repository="Oteryn/Other"))
        self.assertRejected(snapshot(task_branch="other-branch"))
        self.assertRejected(snapshot(pr_id="999"))
        self.assertRejected(snapshot(task_head_sha="b" * 40))
        self.assertRejected(snapshot(next_action="stale action"))

    def test_first_checkpoint_must_match_current_bounded_continuity(self) -> None:
        self.assertRejected(
            snapshot(),
            bounded_authority=FakeBoundedAuthority(matches_current=False),
        )
        self.assertRejected(
            snapshot(),
            lineage_authority=FakeLineageAuthority(predecessor=None, proves_none=False),
        )

    def test_successor_checkpoint_delegates_retry_evidence_continuity(self) -> None:
        predecessor = snapshot(last_material_progress="earlier progress")
        self.validate(
            snapshot(),
            lineage_authority=FakeLineageAuthority(predecessor=predecessor, proves_none=False),
            bounded_authority=FakeBoundedAuthority(preserves_continuity=True),
        )
        self.assertRejected(
            snapshot(),
            lineage_authority=FakeLineageAuthority(predecessor=predecessor, proves_none=False),
            bounded_authority=FakeBoundedAuthority(preserves_continuity=False),
        )

    def test_checkpoint_write_lifecycle_must_match_current_bounded_state(self) -> None:
        self.assertRejected(snapshot(bounded_lifecycle_state="READY"), bounded_authority=FakeBoundedAuthority("RUNNING"))

    def test_continue_current_requires_active_nonterminal_bounded_state(self) -> None:
        self.validate(snapshot(), bounded_authority=FakeBoundedAuthority("RUNNING"))
        self.assertRejected(snapshot(), bounded_authority=FakeBoundedAuthority("WAITING_EXTERNAL"))
        self.assertRejected(snapshot(), bounded_authority=FakeBoundedAuthority("DONE"))

    def test_release_waiting_scheduled_work_requires_released_nonterminal_and_bound_locator(self) -> None:
        for mechanism in ("scheduled_task", "work_event_trigger", "work_persistent"):
            value = snapshot(
                bounded_lifecycle_state="WAITING_EXTERNAL",
                worker_disposition="release_waiting",
                resume_mechanism=mechanism,
                resume_locator=f"resume://{mechanism}/108",
            )
            verifier = FakeMechanismVerifier(live_bound=True, replacement_worker=False)
            self.validate(
                value,
                bounded_authority=FakeBoundedAuthority("WAITING_EXTERNAL"),
                mechanism_verifier=verifier,
            )
            self.assertEqual(verifier.live_calls[-1][3], trusted_task().expected_next_action)
            self.assertEqual(verifier.replacement_calls, [])
            self.assertRejected(
                value,
                bounded_authority=FakeBoundedAuthority("READY"),
                mechanism_verifier=FakeMechanismVerifier(live_bound=True),
            )
            self.assertRejected(
                value,
                bounded_authority=FakeBoundedAuthority("WAITING_EXTERNAL"),
                mechanism_verifier=FakeMechanismVerifier(live_bound=False),
            )
            self.assertRejected(
                {**value, "resume_locator": None},
                bounded_authority=FakeBoundedAuthority("WAITING_EXTERNAL"),
            )

    def test_release_waiting_github_native_requires_locator_and_whole_task_proof(self) -> None:
        value = snapshot(
            bounded_lifecycle_state="WAITING_EXTERNAL",
            worker_disposition="release_waiting",
            resume_mechanism="github_native",
            resume_locator="github://merge-queue/Oteryn/Oteryn/139",
        )
        self.validate(
            value,
            bounded_authority=FakeBoundedAuthority("WAITING_EXTERNAL"),
            remaining_work_authority=FakeRemainingWorkAuthority(safe_without_worker=True),
        )
        self.assertRejected(
            {**value, "resume_locator": None},
            bounded_authority=FakeBoundedAuthority("WAITING_EXTERNAL"),
        )
        self.assertRejected(
            value,
            bounded_authority=FakeBoundedAuthority("WAITING_EXTERNAL"),
            remaining_work_authority=FakeRemainingWorkAuthority(safe_without_worker=False),
        )
        self.assertRejected(value, bounded_authority=FakeBoundedAuthority("READY"))

    def test_rotate_requires_active_nonterminal_and_real_bound_worker_mechanism(self) -> None:
        for mechanism in ("scheduled_task", "work_event_trigger", "work_persistent"):
            value = snapshot(
                worker_disposition="rotate_resumable",
                resume_mechanism=mechanism,
                resume_locator=f"resume://{mechanism}/replacement",
            )
            verifier = FakeMechanismVerifier(live_bound=True, replacement_worker=True)
            self.validate(
                value,
                bounded_authority=FakeBoundedAuthority("RUNNING"),
                mechanism_verifier=verifier,
            )
            self.assertEqual(len(verifier.replacement_calls), 1)
            self.assertRejected(
                value,
                bounded_authority=FakeBoundedAuthority("RUNNING"),
                mechanism_verifier=FakeMechanismVerifier(live_bound=True, replacement_worker=False),
            )
            self.assertRejected(
                {**value, "bounded_lifecycle_state": "WAITING_EXTERNAL"},
                bounded_authority=FakeBoundedAuthority("WAITING_EXTERNAL"),
            )
        self.assertRejected(snapshot(worker_disposition="rotate_resumable", resume_mechanism="github_native", resume_locator="github://x"))

    def test_owner_reinvoke_requires_released_nonterminal_state(self) -> None:
        value = snapshot(
            bounded_lifecycle_state="BLOCKED",
            worker_disposition="stop_reinvoke_required",
            resume_mechanism="owner_reinvoke",
            resume_locator=None,
        )
        self.validate(value, bounded_authority=FakeBoundedAuthority("BLOCKED"))
        self.assertRejected(
            {**value, "bounded_lifecycle_state": "READY"},
            bounded_authority=FakeBoundedAuthority("READY"),
        )
        self.assertRejected(
            {**value, "bounded_lifecycle_state": "DONE"},
            bounded_authority=FakeBoundedAuthority("DONE"),
        )

    def test_terminal_requires_bounded_terminality_and_rejects_stalled(self) -> None:
        terminal = snapshot(
            bounded_lifecycle_state="DONE",
            worker_disposition="terminal",
            resume_mechanism="none_terminal",
            resume_locator=None,
        )
        self.validate(terminal, bounded_authority=FakeBoundedAuthority("DONE"))
        self.assertRejected(
            {**terminal, "bounded_lifecycle_state": "STALLED"},
            bounded_authority=FakeBoundedAuthority("STALLED"),
        )
        for disposition, mechanism, locator in (
            ("continue_current", "same_session", None),
            ("release_waiting", "github_native", "github://done"),
            ("rotate_resumable", "scheduled_task", "resume://done"),
            ("stop_reinvoke_required", "owner_reinvoke", None),
        ):
            self.assertRejected(
                snapshot(
                    bounded_lifecycle_state="DONE",
                    worker_disposition=disposition,
                    resume_mechanism=mechanism,
                    resume_locator=locator,
                ),
                bounded_authority=FakeBoundedAuthority("DONE"),
            )

    def test_invalid_pairings_fail_closed(self) -> None:
        self.assertRejected(snapshot(worker_disposition="continue_current", resume_mechanism="scheduled_task", resume_locator="resume://x"))
        self.assertRejected(snapshot(worker_disposition="terminal", resume_mechanism="same_session"))
        self.assertRejected(snapshot(worker_disposition="release_waiting", resume_mechanism="owner_reinvoke"))

    def test_resume_read_authenticates_history_then_reconciles_fresh_lifecycle(self) -> None:
        historical = snapshot(
            bounded_lifecycle_state="WAITING_EXTERNAL",
            worker_disposition="release_waiting",
            resume_mechanism="scheduled_task",
            resume_locator="resume://scheduled/108",
            task_head_sha="a" * 40,
            next_action="wait for CI",
        )
        current = trusted_task(task_head_sha="b" * 40, expected_next_action="read back protected main")
        lineage_authority = FakeLineageAuthority(predecessor=historical, proves_none=False)
        transition_authority = FakeTransitionAuthority(allowed=True)
        verifier = FakeMechanismVerifier(historical_event=True)
        self.validate(
            historical,
            task=current,
            lineage_authority=lineage_authority,
            transition_authority=transition_authority,
            bounded_authority=FakeBoundedAuthority("DONE"),
            mechanism_verifier=verifier,
            mode="resume_read",
        )
        self.assertEqual(verifier.event_calls, 1)
        self.assertEqual(transition_authority.calls[-1][2], "DONE")
        self.assertRejected(
            historical,
            task=current,
            lineage_authority=FakeLineageAuthority(predecessor=historical, proves_none=False),
            transition_authority=FakeTransitionAuthority(allowed=False),
            bounded_authority=FakeBoundedAuthority("DONE"),
            mechanism_verifier=FakeMechanismVerifier(historical_event=True),
            mode="resume_read",
        )

    def test_resume_read_requires_current_bounded_retry_evidence_truth(self) -> None:
        historical = snapshot(
            bounded_lifecycle_state="WAITING_EXTERNAL",
            worker_disposition="release_waiting",
            resume_mechanism="scheduled_task",
            resume_locator="resume://scheduled/108",
            task_head_sha="a" * 40,
            next_action="wait for CI",
        )
        current = trusted_task(task_head_sha="b" * 40, expected_next_action="read back protected main")
        common = {
            "task": current,
            "lineage_authority": FakeLineageAuthority(predecessor=historical, proves_none=False),
            "transition_authority": FakeTransitionAuthority(allowed=True),
            "mechanism_verifier": FakeMechanismVerifier(historical_event=True),
            "mode": "resume_read",
        }

        self.assertRejected(
            historical,
            bounded_authority=FakeBoundedAuthority(
                "READY",
                matches_current=False,
                preserves_continuity=True,
            ),
            **common,
        )
        self.validate(
            historical,
            bounded_authority=FakeBoundedAuthority(
                "READY",
                matches_current=True,
                preserves_continuity=False,
            ),
            **common,
        )

    def test_resume_read_rejects_rewritten_historical_checkpoint(self) -> None:
        historical = snapshot(
            bounded_lifecycle_state="WAITING_EXTERNAL",
            worker_disposition="release_waiting",
            resume_mechanism="scheduled_task",
            resume_locator="resume://scheduled/108",
        )
        rewritten = {**historical, "task_head_sha": "b" * 40}
        self.assertRejected(
            rewritten,
            lineage_authority=FakeLineageAuthority(predecessor=historical, proves_none=False),
            bounded_authority=FakeBoundedAuthority("READY"),
            mode="resume_read",
        )

    def test_owner_reinvoke_resume_uses_owner_authentication_not_automatic_event(self) -> None:
        historical = snapshot(
            bounded_lifecycle_state="BLOCKED",
            worker_disposition="stop_reinvoke_required",
            resume_mechanism="owner_reinvoke",
            resume_locator=None,
        )
        verifier = FakeMechanismVerifier(owner_reinvoke=True)
        self.validate(
            historical,
            lineage_authority=FakeLineageAuthority(predecessor=historical, proves_none=False),
            bounded_authority=FakeBoundedAuthority("RUNNING"),
            mechanism_verifier=verifier,
            mode="resume_read",
        )
        self.assertEqual(verifier.owner_calls, 1)
        self.assertEqual(verifier.event_calls, 0)

    def test_selector_uses_trusted_capability_authority(self) -> None:
        authority = FakeCapabilityAuthority(capability_snapshot())
        selected = select_execution_surface(
            self.policy,
            trusted_task=trusted_task(),
            required_capability="chat_tools",
            capability_authority=authority,
        )
        self.assertEqual(selected, "chat")
        self.assertEqual(len(authority.calls), 1)
        self.assertEqual(authority.time_calls, 1)

    def test_selector_respects_capability_compatibility_and_authorization(self) -> None:
        work = FakeCapabilityAuthority(
            capability_snapshot(
                required_capability="event_triggered_connected_app",
                compatible=("work",),
                available=("work", "codex"),
                authorized=("work", "codex"),
            )
        )
        self.assertEqual(
            select_execution_surface(
                self.policy,
                trusted_task=trusted_task(),
                required_capability="event_triggered_connected_app",
                capability_authority=work,
            ),
            "work",
        )
        codex_only = FakeCapabilityAuthority(
            capability_snapshot(
                required_capability="event_triggered_connected_app",
                compatible=("work",),
                available=("codex",),
                authorized=("codex",),
                exhausted=True,
            )
        )
        with self.assertRaises(ExecutionSurfaceUnavailable):
            select_execution_surface(
                self.policy,
                trusted_task=trusted_task(),
                required_capability="event_triggered_connected_app",
                capability_authority=codex_only,
            )

    def test_selector_blocks_only_after_safe_fallbacks_are_exhausted(self) -> None:
        exhausted = FakeCapabilityAuthority(
            capability_snapshot(
                required_capability="software_development_loop",
                compatible=("codex",),
                available=(),
                authorized=(),
                exhausted=True,
            )
        )
        with self.assertRaisesRegex(ExecutionSurfaceUnavailable, "BLOCKED_CAPABILITY_UNAVAILABLE"):
            select_execution_surface(
                self.policy,
                trusted_task=trusted_task(),
                required_capability="software_development_loop",
                capability_authority=exhausted,
            )
        incomplete = FakeCapabilityAuthority(
            capability_snapshot(
                required_capability="software_development_loop",
                compatible=("codex",),
                available=(),
                authorized=(),
                exhausted=False,
            )
        )
        with self.assertRaises(ContinuationPolicyError):
            select_execution_surface(
                self.policy,
                trusted_task=trusted_task(),
                required_capability="software_development_loop",
                capability_authority=incomplete,
            )

    def test_selector_rejects_unverifiable_capability_evidence(self) -> None:
        empty_evidence = FakeCapabilityAuthority(capability_snapshot(evidence=()))
        with self.assertRaises(ContinuationPolicyError):
            select_execution_surface(
                self.policy,
                trusted_task=trusted_task(),
                required_capability="chat_tools",
                capability_authority=empty_evidence,
            )


if __name__ == "__main__":
    unittest.main()
