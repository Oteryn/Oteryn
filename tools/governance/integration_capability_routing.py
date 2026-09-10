#!/usr/bin/env python3
"""Trusted-observer routing for protected-integration capability.

Capability classification is deterministic, but worker-release authority never
accepts serialized evidence.  A trusted observer acquires live evidence and the
module seals the resulting observation before classification.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import json
from pathlib import Path
import time
from typing import Mapping, Protocol

NOT_REQUIRED = "NOT_REQUIRED"
DIRECT_CAPABLE = "DIRECT_CAPABLE"
DELEGATED_CAPABLE = "DELEGATED_CAPABLE"
BLOCKED_CAPABILITY_UNAVAILABLE = "BLOCKED_CAPABILITY_UNAVAILABLE"

DEFAULT_MAX_AGE_SECONDS = 300
_OBSERVATION_SEAL = object()


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, dict) else {}


def _unique_strings(value: object) -> tuple[str, ...] | None:
    if not isinstance(value, list):
        return None
    if not all(isinstance(item, str) and item.strip() and item == item.strip() for item in value):
        return None
    items = tuple(value)
    return items if len(set(items)) == len(items) else None


def integration_policy(policy: Mapping[str, object]) -> Mapping[str, object]:
    return _mapping(policy.get("integration_capability_routing"))


def validate_policy(policy: Mapping[str, object]) -> list[str]:
    cfg = integration_policy(policy)
    errors: list[str] = []
    if cfg.get("schema_version") != 2:
        errors.append("integration_capability_routing.schema_version must be 2")
    if cfg.get("require_preflight_before_worker_release") is not True:
        errors.append("integration capability preflight must be required before worker release")
    states = _unique_strings(cfg.get("states"))
    expected_states = (NOT_REQUIRED, DIRECT_CAPABLE, DELEGATED_CAPABLE, BLOCKED_CAPABILITY_UNAVAILABLE)
    if states != expected_states:
        errors.append("integration capability states must be the canonical ordered set")
    for key in ("direct_operation", "delegated_route", "delegated_request_operation", "control_repository"):
        value = cfg.get(key)
        if not isinstance(value, str) or not value.strip() or value != value.strip():
            errors.append(f"integration_capability_routing.{key} must be a non-empty string")
    issue = cfg.get("control_issue")
    if not isinstance(issue, int) or isinstance(issue, bool) or issue <= 0:
        errors.append("integration_capability_routing.control_issue must be a positive integer")
    maximum_age = cfg.get("observation_max_age_seconds")
    if not isinstance(maximum_age, int) or isinstance(maximum_age, bool) or maximum_age <= 0:
        errors.append("integration_capability_routing.observation_max_age_seconds must be positive")
    executor = cfg.get("protected_executor")
    if not isinstance(executor, dict) or executor != {
        "repository": "Oteryn/Oteryn",
        "ref": "refs/heads/main",
        "workflow_path": ".github/workflows/governed-merge-queue-executor.yml",
        "workflow_blob_sha": executor.get("workflow_blob_sha") if isinstance(executor, dict) else None,
    } or not isinstance(executor.get("workflow_blob_sha"), str) or len(executor["workflow_blob_sha"]) != 40:
        errors.append("integration_capability_routing.protected_executor must bind protected META workflow identity")
    targets = cfg.get("allowed_target_repositories")
    expected_targets = {
        "Oteryn/Oteryn": {"gate": "meta-gate", "source_workflows": [{"path": ".github/workflows/ci.yml", "event": "pull_request", "workflow_id": 336924336}]},
        "Oteryn/Oteryn-Game": {"gate": "game-gate", "source_workflows": [{"path": ".github/workflows/merge-gate.yml", "event": "pull_request", "workflow_id": 336912904}]},
        "Oteryn/Oteryn-Platform": {"gate": "platform-gate", "source_workflows": [{"path": ".github/workflows/ci.yml", "event": "pull_request", "workflow_id": 315878887}]},
        "Oteryn/Oteryn-Atlas": {"gate": None, "source_workflows": [
            {"path": ".github/workflows/merge-authority-audit.yml", "event": "pull_request_target", "workflow_id": 351151514},
            {"path": ".github/workflows/verification-shadow.yml", "event": "pull_request_target", "workflow_id": 353763418},
        ]},
    }
    if targets != expected_targets:
        errors.append("integration capability target workflow identities must match canonical repositories")
    return errors


@dataclass(frozen=True)
class ProtectedExecutorEvidence:
    repository: str
    ref: str
    workflow_path: str
    workflow_blob_sha: str
    observed_at_epoch_seconds: int
    credential_operational: bool
    canary_repository: str
    canary_workflow_blob_sha: str
    terminal_canary_proof_retained: bool


@dataclass(frozen=True)
class AcquiredCapabilityEvidence:
    requires_autonomous_protected_integration: bool
    observed_at_epoch_seconds: int
    available_operations: tuple[str, ...]
    operational_executor_routes: tuple[str, ...]
    protected_executor: ProtectedExecutorEvidence | None = None


@dataclass(frozen=True)
class VerifiedCapabilityObservation:
    """Opaque observation sealed only by ``TrustedCapabilityObserver.observe``."""

    evidence: AcquiredCapabilityEvidence
    _seal: object = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if self._seal is not _OBSERVATION_SEAL:
            raise ValueError("verified capability observations must be produced by a trusted observer")


class TrustedCapabilityObserver(ABC):
    """Installed trust boundary for live tool discovery and executor readback."""

    @abstractmethod
    def acquire(self, policy: Mapping[str, object], *, now_epoch_seconds: int) -> AcquiredCapabilityEvidence:
        """Acquire live evidence; test suites may implement an explicit fake observer."""

    def observe(self, policy: Mapping[str, object], *, now_epoch_seconds: int | None = None) -> VerifiedCapabilityObservation:
        now = int(time.time()) if now_epoch_seconds is None else now_epoch_seconds
        evidence = self.acquire(policy, now_epoch_seconds=now)
        if not isinstance(evidence, AcquiredCapabilityEvidence):
            raise TypeError("trusted observer returned an invalid evidence type")
        return VerifiedCapabilityObservation(evidence, _OBSERVATION_SEAL)


class CurrentSessionToolDiscovery(Protocol):
    def discover_operations(self) -> tuple[int, tuple[str, ...]]: ...


class ProtectedMetaExecutorObserver(Protocol):
    def readback(self) -> tuple[tuple[str, ...], ProtectedExecutorEvidence | None]: ...


class CurrentSessionCapabilityObserver(TrustedCapabilityObserver):
    """Production adapter boundary; inputs are live discovery/readback interfaces."""

    def __init__(self, *, required: bool, tools: CurrentSessionToolDiscovery,
                 executor: ProtectedMetaExecutorObserver) -> None:
        self._required = required
        self._tools = tools
        self._executor = executor

    def acquire(self, policy: Mapping[str, object], *, now_epoch_seconds: int) -> AcquiredCapabilityEvidence:
        observed_at, operations = self._tools.discover_operations()
        routes, executor_evidence = self._executor.readback()
        return AcquiredCapabilityEvidence(
            self._required, observed_at, operations, routes, executor_evidence
        )


def _fresh(observed: object, now: object, maximum_age: int) -> bool:
    return (isinstance(observed, int) and not isinstance(observed, bool)
            and isinstance(now, int) and not isinstance(now, bool)
            and 0 <= observed <= now and now - observed <= maximum_age)


def _delegated_executor_is_operational(
    evidence: ProtectedExecutorEvidence | None, cfg: Mapping[str, object], *, now_epoch_seconds: int
) -> bool:
    if not isinstance(evidence, ProtectedExecutorEvidence):
        return False
    expected = _mapping(cfg.get("protected_executor"))
    return (
        evidence.repository == expected.get("repository")
        and evidence.ref == expected.get("ref")
        and evidence.workflow_path == expected.get("workflow_path")
        and evidence.workflow_blob_sha == expected.get("workflow_blob_sha")
        and evidence.credential_operational is True
        and _fresh(evidence.observed_at_epoch_seconds, now_epoch_seconds, int(cfg["observation_max_age_seconds"]))
        and evidence.canary_repository == expected.get("repository")
        and evidence.canary_workflow_blob_sha == expected.get("workflow_blob_sha")
        and evidence.terminal_canary_proof_retained is True
    )


def classify(observation: object, policy: Mapping[str, object], *, now_epoch_seconds: int | None = None) -> str:
    """Purely classify a sealed observation; arbitrary mappings fail closed."""
    errors = validate_policy(policy)
    if errors:
        raise ValueError("; ".join(errors))
    if not isinstance(observation, VerifiedCapabilityObservation) or observation._seal is not _OBSERVATION_SEAL:
        return BLOCKED_CAPABILITY_UNAVAILABLE
    evidence = observation.evidence
    if not evidence.requires_autonomous_protected_integration:
        return NOT_REQUIRED
    now = int(time.time()) if now_epoch_seconds is None else now_epoch_seconds
    cfg = integration_policy(policy)
    maximum_age = int(cfg.get("observation_max_age_seconds", DEFAULT_MAX_AGE_SECONDS))
    if not _fresh(evidence.observed_at_epoch_seconds, now, maximum_age):
        return BLOCKED_CAPABILITY_UNAVAILABLE
    if cfg["direct_operation"] in evidence.available_operations:
        return DIRECT_CAPABLE
    if (cfg["delegated_request_operation"] in evidence.available_operations
            and cfg["delegated_route"] in evidence.operational_executor_routes
            and _delegated_executor_is_operational(evidence.protected_executor, cfg, now_epoch_seconds=now)):
        return DELEGATED_CAPABLE
    return BLOCKED_CAPABILITY_UNAVAILABLE


def observe_and_classify(observer: object, policy: Mapping[str, object], *, now_epoch_seconds: int | None = None) -> str:
    """Production authority entry point: acquire through an installed observer."""
    if not isinstance(observer, TrustedCapabilityObserver):
        return BLOCKED_CAPABILITY_UNAVAILABLE
    now = int(time.time()) if now_epoch_seconds is None else now_epoch_seconds
    try:
        observation = observer.observe(policy, now_epoch_seconds=now)
    except (OSError, TypeError, ValueError):
        return BLOCKED_CAPABILITY_UNAVAILABLE
    return classify(observation, policy, now_epoch_seconds=now)


def validate_worker_release(observer: object, policy: Mapping[str, object], *, now_epoch_seconds: int | None = None) -> list[str]:
    state = observe_and_classify(observer, policy, now_epoch_seconds=now_epoch_seconds)
    if state == BLOCKED_CAPABILITY_UNAVAILABLE:
        return ["protected integration capability unavailable before worker release: "
                "no trusted observer proved direct native merge-async or the bounded META executor"]
    return []


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, required=True)
    args = parser.parse_args()
    try:
        policy = load_json(args.policy)
        errors = validate_policy(policy)
        if errors:
            raise ValueError("; ".join(errors))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "INVALID", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps({"status": BLOCKED_CAPABILITY_UNAVAILABLE,
                      "reason": "no trusted capability observer is installed in this CLI"}, sort_keys=True))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
