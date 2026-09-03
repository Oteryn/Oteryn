#!/usr/bin/env python3
"""Deterministic policy validation for Oteryn persistent task continuation.

This module owns continuation semantics only. Bounded lifecycle/retry authority,
GitHub state, resume mechanism liveness and execution capability discovery are
supplied through trusted adapters and are not reimplemented here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Protocol


class ContinuationPolicyError(ValueError):
    """Raised when continuation policy or evidence fails closed."""


class ExecutionSurfaceUnavailable(RuntimeError):
    """Raised only after trusted evidence proves safe compatible fallbacks exhausted."""


@dataclass(frozen=True)
class StableTaskLineageKey:
    repository: str
    task_id: str
    checkpoint_lineage_token: str


@dataclass(frozen=True)
class TrustedTaskIdentity:
    lineage_key: StableTaskLineageKey
    task_branch: str
    pr_applicable: bool
    pr_id: str | None
    task_head_sha: str
    expected_next_action: str


@dataclass(frozen=True)
class TrustedCapabilitySnapshot:
    observed_at: str
    required_capability: str | None
    compatible_surfaces: tuple[str, ...]
    available_surfaces: tuple[str, ...]
    authorized_surfaces: tuple[str, ...]
    safe_fallbacks_exhausted: bool
    evidence_refs: tuple[str, ...]


class CheckpointLineageAuthority(Protocol):
    def latest_predecessor(self, key: StableTaskLineageKey) -> dict[str, object] | None: ...
    def proves_no_predecessor(self, key: StableTaskLineageKey) -> bool: ...


class CheckpointTransitionAuthority(Protocol):
    def proves_transition(
        self,
        historical: dict[str, object],
        current_task: TrustedTaskIdentity,
        current_bounded_state: str,
    ) -> bool: ...


class BoundedLifecycleAuthority(Protocol):
    def current_state(self, trusted_task: TrustedTaskIdentity) -> str: ...
    def releases_worker_ownership(self, state: str, trusted_task: TrustedTaskIdentity) -> bool: ...
    def is_terminal(self, state: str, trusted_task: TrustedTaskIdentity) -> bool: ...
    def matches_current_retry_and_evidence_state(
        self, proposed: dict[str, object], trusted_task: TrustedTaskIdentity
    ) -> bool: ...
    def preserves_retry_and_evidence_continuity(
        self,
        previous: dict[str, object],
        proposed: dict[str, object],
        trusted_task: TrustedTaskIdentity,
    ) -> bool: ...


class ResumeMechanismVerifier(Protocol):
    def is_live_and_bound(
        self,
        mechanism: str,
        locator: str,
        trusted_task: TrustedTaskIdentity,
        expected_next_action: str,
    ) -> bool: ...
    def proves_replacement_or_persistent_worker(
        self,
        mechanism: str,
        locator: str,
        trusted_task: TrustedTaskIdentity,
        expected_next_action: str,
    ) -> bool: ...
    def has_automatic_continuation(
        self,
        trusted_task: TrustedTaskIdentity,
        expected_next_action: str,
    ) -> bool: ...
    def verify_historical_resume_event(
        self, historical: dict[str, object], trusted_task: TrustedTaskIdentity
    ) -> bool: ...
    def verify_owner_reinvocation(
        self, historical: dict[str, object], trusted_task: TrustedTaskIdentity
    ) -> bool: ...


class RemainingWorkAuthority(Protocol):
    def all_remaining_work_can_complete_without_agent_worker(
        self, trusted_task: TrustedTaskIdentity
    ) -> bool: ...


class ExecutionCapabilityAuthority(Protocol):
    def current_snapshot(
        self, trusted_task: TrustedTaskIdentity, required_capability: str | None
    ) -> TrustedCapabilitySnapshot: ...
    def current_time(self, trusted_task: TrustedTaskIdentity) -> str: ...


_POLICY_KEYS = {
    "schema_version",
    "policy_id",
    "continuation_authority",
    "bounded_execution_authority",
    "coordinates",
    "worker_dispositions",
    "resume_mechanisms",
    "automatic_resume_mechanisms",
    "disposition_mechanism_compatibility",
    "execution_surfaces",
    "capability_surface_compatibility",
    "capability_snapshot_freshness",
    "context_pressure_values",
    "blocked_result",
}
_COORDINATES = [
    "task",
    "worker_session",
    "tool_command",
    "external_wait",
    "retry_no_progress",
    "context_pressure",
]
_WORKER_DISPOSITIONS = [
    "continue_current",
    "release_waiting",
    "rotate_resumable",
    "stop_reinvoke_required",
    "terminal",
]
_RESUME_MECHANISMS = [
    "same_session",
    "github_native",
    "scheduled_task",
    "work_event_trigger",
    "work_persistent",
    "owner_reinvoke",
    "none_terminal",
]
_AUTOMATIC_MECHANISMS = [
    "github_native",
    "scheduled_task",
    "work_event_trigger",
    "work_persistent",
]
_COMPATIBILITY = {
    "continue_current": ["same_session"],
    "release_waiting": ["github_native", "scheduled_task", "work_event_trigger", "work_persistent"],
    "rotate_resumable": ["scheduled_task", "work_event_trigger", "work_persistent"],
    "stop_reinvoke_required": ["owner_reinvoke"],
    "terminal": ["none_terminal"],
}
_EXECUTION_SURFACES = ["chat", "github_native", "work", "codex"]
_CAPABILITY_SURFACES = {
    "chat_tools": ["chat"],
    "github_deterministic": ["github_native"],
    "event_triggered_connected_app": ["work"],
    "persistent_cloud_execution": ["work"],
    "software_development_loop": ["codex"],
}
_CONTEXT_PRESSURE = ["not_applicable", "normal", "elevated", "rotate_required"]
_SNAPSHOT_FIELDS = {
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
_REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_SHA = re.compile(r"^[0-9a-f]{40}$")
_UTC_RFC3339 = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")


def _is_exact_bool(value: object) -> bool:
    return isinstance(value, bool)


def _nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _unique_nonempty_strings(value: object, *, allow_empty: bool = False) -> bool:
    if not isinstance(value, (list, tuple)):
        return False
    if not allow_empty and not value:
        return False
    return all(_nonempty_string(item) for item in value) and len(set(value)) == len(value)


def _utc_timestamp(value: object) -> bool:
    if not isinstance(value, str) or not _UTC_RFC3339.fullmatch(value):
        return False
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return False
    return parsed.tzinfo == timezone.utc


def _parse_utc(value: object) -> datetime:
    if not _utc_timestamp(value):
        raise ContinuationPolicyError("trusted timestamp is invalid")
    assert isinstance(value, str)
    return datetime.fromisoformat(value[:-1] + "+00:00")


def load_policy(path: Path) -> dict[str, object]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ContinuationPolicyError("continuation policy must be a JSON object")
    return loaded


def validate_policy(policy: dict[str, object]) -> None:
    if set(policy) != _POLICY_KEYS:
        raise ContinuationPolicyError("continuation policy must use the closed schema")
    if policy.get("schema_version") != 1 or isinstance(policy.get("schema_version"), bool):
        raise ContinuationPolicyError("continuation policy schema_version must be 1")
    if policy.get("policy_id") != "oteryn-agent-continuation-v1":
        raise ContinuationPolicyError("unexpected continuation policy id")
    if policy.get("continuation_authority") != "Oteryn/Oteryn#108":
        raise ContinuationPolicyError("continuation authority must be Oteryn/Oteryn#108")
    if policy.get("bounded_execution_authority") != "Oteryn/Oteryn#69":
        raise ContinuationPolicyError("bounded authority must remain Oteryn/Oteryn#69")
    if policy.get("coordinates") != _COORDINATES:
        raise ContinuationPolicyError("continuation coordinates must be canonical and independent")
    if policy.get("worker_dispositions") != _WORKER_DISPOSITIONS:
        raise ContinuationPolicyError("worker dispositions must be canonical")
    if policy.get("resume_mechanisms") != _RESUME_MECHANISMS:
        raise ContinuationPolicyError("resume mechanisms must be canonical")
    if policy.get("automatic_resume_mechanisms") != _AUTOMATIC_MECHANISMS:
        raise ContinuationPolicyError("automatic resume mechanism set must be canonical")
    if policy.get("disposition_mechanism_compatibility") != _COMPATIBILITY:
        raise ContinuationPolicyError("disposition/mechanism compatibility must be canonical")
    if policy.get("execution_surfaces") != _EXECUTION_SURFACES:
        raise ContinuationPolicyError("execution surfaces must be canonical")
    if policy.get("capability_surface_compatibility") != _CAPABILITY_SURFACES:
        raise ContinuationPolicyError("capability/surface compatibility must be canonical")
    freshness = policy.get("capability_snapshot_freshness")
    if not isinstance(freshness, dict) or set(freshness) != {"max_age_seconds"}:
        raise ContinuationPolicyError("capability snapshot freshness must use the closed schema")
    max_age = freshness.get("max_age_seconds")
    if not isinstance(max_age, int) or isinstance(max_age, bool) or max_age != 900:
        raise ContinuationPolicyError("capability snapshot max age must be 900 seconds")
    if policy.get("context_pressure_values") != _CONTEXT_PRESSURE:
        raise ContinuationPolicyError("context pressure vocabulary must be canonical")
    if policy.get("blocked_result") != "BLOCKED_CAPABILITY_UNAVAILABLE":
        raise ContinuationPolicyError("blocked result must be canonical")


def _validate_trusted_task(task: TrustedTaskIdentity) -> None:
    key = task.lineage_key
    if not _REPOSITORY.fullmatch(key.repository):
        raise ContinuationPolicyError("trusted repository identity is invalid")
    if not _nonempty_string(key.task_id) or not _nonempty_string(key.checkpoint_lineage_token):
        raise ContinuationPolicyError("trusted stable lineage is incomplete")
    if not _nonempty_string(task.task_branch) or not _SHA.fullmatch(task.task_head_sha):
        raise ContinuationPolicyError("trusted mutable task coordinates are invalid")
    if not _is_exact_bool(task.pr_applicable):
        raise ContinuationPolicyError("trusted pr_applicable must be boolean")
    if task.pr_applicable:
        if not _nonempty_string(task.pr_id):
            raise ContinuationPolicyError("trusted PR identity is required")
    elif task.pr_id is not None:
        raise ContinuationPolicyError("trusted non-PR task must not carry pr_id")
    if not _nonempty_string(task.expected_next_action):
        raise ContinuationPolicyError("trusted next action is required")


def _validate_snapshot_shape(policy: dict[str, object], snapshot: dict[str, object]) -> None:
    if set(snapshot) != _SNAPSHOT_FIELDS:
        raise ContinuationPolicyError("continuation snapshot must use the closed semantic-minimum field set")
    if not isinstance(snapshot["repository"], str) or not _REPOSITORY.fullmatch(snapshot["repository"]):
        raise ContinuationPolicyError("repository must be an exact owner/name coordinate")
    for field in (
        "task_id",
        "checkpoint_lineage_token",
        "task_branch",
        "phase",
        "bounded_lifecycle_state",
        "last_material_progress",
        "bounded_continuity_ref",
        "next_action",
    ):
        if not _nonempty_string(snapshot[field]):
            raise ContinuationPolicyError(f"{field} must be a non-empty string")
    if not _is_exact_bool(snapshot["pr_applicable"]):
        raise ContinuationPolicyError("pr_applicable must be an exact boolean")
    if snapshot["pr_applicable"]:
        if not _nonempty_string(snapshot["pr_id"]):
            raise ContinuationPolicyError("pr_id is required for PR-backed tasks")
    elif snapshot["pr_id"] is not None:
        raise ContinuationPolicyError("pr_id must be null for non-PR tasks")
    if not isinstance(snapshot["task_head_sha"], str) or not _SHA.fullmatch(snapshot["task_head_sha"]):
        raise ContinuationPolicyError("task_head_sha must be lowercase 40-hex")
    for field in ("completed_work", "evidence_refs", "blockers"):
        if not _unique_nonempty_strings(snapshot[field], allow_empty=True) or not isinstance(snapshot[field], list):
            raise ContinuationPolicyError(f"{field} must be a JSON list of unique non-empty strings")
    if snapshot["context_pressure"] not in policy["context_pressure_values"]:
        raise ContinuationPolicyError("context_pressure is not canonical")
    if snapshot["worker_disposition"] not in policy["worker_dispositions"]:
        raise ContinuationPolicyError("worker_disposition is not canonical")
    if snapshot["resume_mechanism"] not in policy["resume_mechanisms"]:
        raise ContinuationPolicyError("resume_mechanism is not canonical")
    automatic = set(policy["automatic_resume_mechanisms"])
    if snapshot["resume_mechanism"] in automatic:
        if not _nonempty_string(snapshot["resume_locator"]):
            raise ContinuationPolicyError("automatic resume mechanism requires a concrete locator")
    elif snapshot["resume_locator"] is not None:
        raise ContinuationPolicyError("non-automatic mechanism must not fabricate a locator")


def _validate_stable_lineage(snapshot: dict[str, object], trusted_task: TrustedTaskIdentity) -> None:
    key = trusted_task.lineage_key
    if (
        snapshot["repository"] != key.repository
        or snapshot["task_id"] != key.task_id
        or snapshot["checkpoint_lineage_token"] != key.checkpoint_lineage_token
    ):
        raise ContinuationPolicyError("snapshot stable lineage does not match trusted task")


def _validate_current_coordinates(snapshot: dict[str, object], trusted_task: TrustedTaskIdentity) -> None:
    expected = {
        "task_branch": trusted_task.task_branch,
        "pr_applicable": trusted_task.pr_applicable,
        "pr_id": trusted_task.pr_id,
        "task_head_sha": trusted_task.task_head_sha,
        "next_action": trusted_task.expected_next_action,
    }
    for field, value in expected.items():
        if snapshot[field] != value:
            raise ContinuationPolicyError(f"snapshot {field} does not match current trusted task")


def _validate_pair(
    policy: dict[str, object],
    snapshot: dict[str, object],
    trusted_task: TrustedTaskIdentity,
    bounded_authority: BoundedLifecycleAuthority,
    mechanism_verifier: ResumeMechanismVerifier,
    remaining_work_authority: RemainingWorkAuthority,
    *,
    state_for_pair: str,
    verify_future_mechanism: bool,
) -> None:
    disposition = str(snapshot["worker_disposition"])
    mechanism = str(snapshot["resume_mechanism"])
    compatibility = policy["disposition_mechanism_compatibility"]
    if mechanism not in compatibility[disposition]:
        raise ContinuationPolicyError("invalid disposition/resume mechanism pairing")

    released = bounded_authority.releases_worker_ownership(state_for_pair, trusted_task)
    terminal = bounded_authority.is_terminal(state_for_pair, trusted_task)

    if disposition == "terminal":
        if not terminal:
            raise ContinuationPolicyError("terminal disposition requires bounded terminality")
    else:
        if terminal:
            raise ContinuationPolicyError("bounded terminal state rejects every nonterminal disposition")
        if disposition == "continue_current" and released:
            raise ContinuationPolicyError("continue_current requires nonreleased bounded ownership")
        if disposition in {"release_waiting", "stop_reinvoke_required"} and not released:
            raise ContinuationPolicyError(f"{disposition} requires released bounded ownership")
        if disposition == "rotate_resumable" and released:
            raise ContinuationPolicyError("rotate_resumable requires an active nonreleased bounded state")

    if not verify_future_mechanism:
        return

    if disposition == "stop_reinvoke_required" and mechanism_verifier.has_automatic_continuation(
        trusted_task,
        trusted_task.expected_next_action,
    ):
        raise ContinuationPolicyError("owner reinvocation is invalid while automatic continuation exists")

    if mechanism in {"scheduled_task", "work_event_trigger", "work_persistent"}:
        locator = str(snapshot["resume_locator"])
        if not mechanism_verifier.is_live_and_bound(
            mechanism,
            locator,
            trusted_task,
            trusted_task.expected_next_action,
        ):
            raise ContinuationPolicyError("automatic worker mechanism is not live/authorized/task/action bound")
        if disposition == "rotate_resumable" and not mechanism_verifier.proves_replacement_or_persistent_worker(
            mechanism,
            locator,
            trusted_task,
            trusted_task.expected_next_action,
        ):
            raise ContinuationPolicyError("rotate_resumable requires verified replacement or persistent worker")
    elif disposition == "release_waiting" and mechanism == "github_native":
        if not remaining_work_authority.all_remaining_work_can_complete_without_agent_worker(trusted_task):
            raise ContinuationPolicyError("GitHub-native release cannot strand later worker work")


def validate_continuation_snapshot(
    policy: dict[str, object],
    snapshot: dict[str, object],
    *,
    trusted_task: TrustedTaskIdentity,
    lineage_authority: CheckpointLineageAuthority,
    transition_authority: CheckpointTransitionAuthority,
    bounded_authority: BoundedLifecycleAuthority,
    mechanism_verifier: ResumeMechanismVerifier,
    remaining_work_authority: RemainingWorkAuthority,
    validation_mode: str,
) -> None:
    validate_policy(policy)
    _validate_trusted_task(trusted_task)
    if validation_mode not in {"checkpoint_write", "resume_read"}:
        raise ContinuationPolicyError("validation_mode must be checkpoint_write or resume_read")
    if not isinstance(snapshot, dict):
        raise ContinuationPolicyError("continuation snapshot must be an object")
    _validate_snapshot_shape(policy, snapshot)
    _validate_stable_lineage(snapshot, trusted_task)

    if validation_mode == "checkpoint_write":
        _validate_current_coordinates(snapshot, trusted_task)
        current_state = bounded_authority.current_state(trusted_task)
        if snapshot["bounded_lifecycle_state"] != current_state:
            raise ContinuationPolicyError("checkpoint lifecycle state does not match bounded authority")
        predecessor = lineage_authority.latest_predecessor(trusted_task.lineage_key)
        if predecessor is None:
            if not lineage_authority.proves_no_predecessor(trusted_task.lineage_key):
                raise ContinuationPolicyError("absence of continuation predecessor is not authoritative")
            if not bounded_authority.matches_current_retry_and_evidence_state(snapshot, trusted_task):
                raise ContinuationPolicyError("first checkpoint does not match current bounded continuity state")
        else:
            if not bounded_authority.preserves_retry_and_evidence_continuity(
                predecessor, snapshot, trusted_task
            ):
                raise ContinuationPolicyError("checkpoint would reset or widen bounded retry/evidence state")
        _validate_pair(
            policy,
            snapshot,
            trusted_task,
            bounded_authority,
            mechanism_verifier,
            remaining_work_authority,
            state_for_pair=current_state,
            verify_future_mechanism=True,
        )
        return

    historical = lineage_authority.latest_predecessor(trusted_task.lineage_key)
    if historical is None or historical != snapshot:
        raise ContinuationPolicyError("resume_read requires the exact latest authenticated historical checkpoint")
    historical_state = str(snapshot["bounded_lifecycle_state"])
    _validate_pair(
        policy,
        snapshot,
        trusted_task,
        bounded_authority,
        mechanism_verifier,
        remaining_work_authority,
        state_for_pair=historical_state,
        verify_future_mechanism=False,
    )
    mechanism = str(snapshot["resume_mechanism"])
    if mechanism in set(policy["automatic_resume_mechanisms"]):
        if not mechanism_verifier.verify_historical_resume_event(snapshot, trusted_task):
            raise ContinuationPolicyError("historical automatic resume event is not authenticated")
    elif mechanism == "owner_reinvoke":
        if not mechanism_verifier.verify_owner_reinvocation(snapshot, trusted_task):
            raise ContinuationPolicyError("owner reinvocation is not authenticated")
    else:
        raise ContinuationPolicyError("resume_read requires an actual automatic event or owner reinvocation")

    fresh_state = bounded_authority.current_state(trusted_task)
    if not transition_authority.proves_transition(snapshot, trusted_task, fresh_state):
        raise ContinuationPolicyError("historical-to-fresh task/lifecycle transition is not authoritative")
    if not bounded_authority.matches_current_retry_and_evidence_state(snapshot, trusted_task):
        raise ContinuationPolicyError("fresh bounded retry/evidence state does not match current authority")
    bounded_authority.releases_worker_ownership(fresh_state, trusted_task)
    bounded_authority.is_terminal(fresh_state, trusted_task)


def _validate_capability_snapshot(
    policy: dict[str, object],
    snapshot: TrustedCapabilitySnapshot,
    required_capability: str | None,
    current_time: str,
) -> None:
    if not isinstance(snapshot, TrustedCapabilitySnapshot):
        raise ContinuationPolicyError("capability evidence must come from the trusted snapshot type")
    if snapshot.required_capability != required_capability:
        raise ContinuationPolicyError("capability snapshot is bound to a different requirement")
    observed_at = _parse_utc(snapshot.observed_at)
    current_at = _parse_utc(current_time)
    freshness = policy["capability_snapshot_freshness"]
    assert isinstance(freshness, dict)
    max_age = freshness["max_age_seconds"]
    assert isinstance(max_age, int) and not isinstance(max_age, bool)
    age_seconds = (current_at - observed_at).total_seconds()
    if age_seconds < 0:
        raise ContinuationPolicyError("capability snapshot is from the future")
    if age_seconds > max_age:
        raise ContinuationPolicyError("capability snapshot is stale")
    if not _unique_nonempty_strings(snapshot.evidence_refs):
        raise ContinuationPolicyError("trusted capability evidence references are required")
    known = set(policy["execution_surfaces"])
    for name, values in (
        ("compatible", snapshot.compatible_surfaces),
        ("available", snapshot.available_surfaces),
        ("authorized", snapshot.authorized_surfaces),
    ):
        if not _unique_nonempty_strings(values, allow_empty=True) or not set(values).issubset(known):
            raise ContinuationPolicyError(f"{name} surface evidence is malformed")
    if not _is_exact_bool(snapshot.safe_fallbacks_exhausted):
        raise ContinuationPolicyError("safe_fallbacks_exhausted must be an exact boolean")
    if required_capability is not None:
        mapping = policy["capability_surface_compatibility"]
        if required_capability not in mapping:
            raise ContinuationPolicyError("required capability has no policy mapping")
        if not set(snapshot.compatible_surfaces).issubset(set(mapping[required_capability])):
            raise ContinuationPolicyError("trusted capability snapshot claims an incompatible surface")


def select_execution_surface(
    policy: dict[str, object],
    *,
    trusted_task: TrustedTaskIdentity,
    required_capability: str | None,
    capability_authority: ExecutionCapabilityAuthority,
) -> str:
    validate_policy(policy)
    _validate_trusted_task(trusted_task)
    facts = capability_authority.current_snapshot(trusted_task, required_capability)
    current_time = capability_authority.current_time(trusted_task)
    _validate_capability_snapshot(policy, facts, required_capability, current_time)

    eligible = (
        set(facts.compatible_surfaces)
        & set(facts.available_surfaces)
        & set(facts.authorized_surfaces)
    )
    for surface in policy["execution_surfaces"]:
        if surface in eligible:
            return surface
    if facts.safe_fallbacks_exhausted:
        raise ExecutionSurfaceUnavailable(str(policy["blocked_result"]))
    raise ContinuationPolicyError("safe compatible fallback evaluation is incomplete")
