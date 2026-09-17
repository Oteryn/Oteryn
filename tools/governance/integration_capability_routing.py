#!/usr/bin/env python3
"""Typed-evidence routing for protected-integration capability.

Capability classification is deterministic. Worker-release authority accepts only
fresh typed current-session evidence; raw mappings and serialized snapshots are not
authority. Live adapters may assemble that evidence, but no dedicated observer or
sealed-observation wrapper is required.
"""

from dataclasses import dataclass, field
import json
from pathlib import Path
import re
import time
from typing import Mapping, Protocol

NOT_REQUIRED = "NOT_REQUIRED"
DIRECT_CAPABLE = "DIRECT_CAPABLE"
DELEGATED_CAPABLE = "DELEGATED_CAPABLE"
BLOCKED_CAPABILITY_UNAVAILABLE = "BLOCKED_CAPABILITY_UNAVAILABLE"

DEFAULT_MAX_AGE_SECONDS = 300
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
LOGIN_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")
_DECISION_SEAL = object()


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, dict) else {}


def _unique_strings(value: object) -> tuple[str, ...] | None:
    if not isinstance(value, list):
        return None
    if not all(isinstance(item, str) and item.strip() and item == item.strip() for item in value):
        return None
    items = tuple(value)
    return items if len(set(items)) == len(items) else None


def _valid_string_tuple(value: object) -> bool:
    return (
        isinstance(value, tuple)
        and all(isinstance(item, str) and item.strip() and item == item.strip() for item in value)
        and len(set(value)) == len(value)
    )


def integration_policy(policy: Mapping[str, object]) -> Mapping[str, object]:
    return _mapping(policy.get("integration_capability_routing"))


def validate_policy(policy: Mapping[str, object]) -> list[str]:
    cfg = integration_policy(policy)
    errors: list[str] = []
    if cfg.get("schema_version") != 2:
        errors.append("integration_capability_routing.schema_version must be 2")
    if cfg.get("require_preflight_before_worker_release") is not True:
        errors.append("integration capability preflight must be required before worker release")
    if cfg.get("delegated_identity_binding") != "control_actor_equals_credential_principal":
        errors.append("delegated capability must bind the control actor to the credential principal")
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
    } or not isinstance(executor.get("workflow_blob_sha"), str) or SHA_RE.fullmatch(executor["workflow_blob_sha"]) is None:
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
    protected_main_sha: str
    observed_at_epoch_seconds: int
    credential_operational: bool
    canary_repository: str
    canary_workflow_blob_sha: str
    canary_protected_main_sha: str
    terminal_canary_proof_retained: bool
    credential_principal: str


@dataclass(frozen=True)
class AcquiredCapabilityEvidence:
    """Typed facts acquired from the current execution session."""

    requires_autonomous_protected_integration: bool
    observed_at_epoch_seconds: int
    available_operations: tuple[str, ...]
    operational_executor_routes: tuple[str, ...]
    protected_executor: ProtectedExecutorEvidence | None = None
    control_comment_actor: str | None = None


@dataclass(frozen=True)
class CapabilityDecision:
    """Sealed scheduling decision retaining delegated request authority bindings."""

    state: str
    delegated_protected_main_sha: str | None
    _seal: object = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if self._seal is not _DECISION_SEAL:
            raise ValueError("capability decisions must be produced from typed current-session evidence")


class CurrentSessionToolDiscovery(Protocol):
    def discover_operations(self) -> tuple[int, tuple[str, ...], str | None]: ...


class ProtectedMetaExecutorObserver(Protocol):
    def readback(self) -> tuple[tuple[str, ...], ProtectedExecutorEvidence | None]: ...


def acquire_current_session_evidence(
    *,
    required: bool,
    tools: CurrentSessionToolDiscovery,
    executor: ProtectedMetaExecutorObserver,
) -> AcquiredCapabilityEvidence:
    """Assemble typed evidence from live current-session discovery/readback adapters."""
    observed_at, operations, control_actor = tools.discover_operations()
    routes, executor_evidence = executor.readback()
    return AcquiredCapabilityEvidence(
        required,
        observed_at,
        operations,
        routes,
        executor_evidence,
        control_actor,
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
        and isinstance(evidence.protected_main_sha, str)
        and SHA_RE.fullmatch(evidence.protected_main_sha) is not None
        and evidence.credential_operational is True
        and _fresh(evidence.observed_at_epoch_seconds, now_epoch_seconds, int(cfg["observation_max_age_seconds"]))
        and evidence.canary_repository == expected.get("repository")
        and evidence.canary_workflow_blob_sha == expected.get("workflow_blob_sha")
        and isinstance(evidence.canary_protected_main_sha, str)
        and SHA_RE.fullmatch(evidence.canary_protected_main_sha) is not None
        and evidence.canary_protected_main_sha == evidence.protected_main_sha
        and evidence.terminal_canary_proof_retained is True
    )


def _same_valid_actor(actor: object, principal: object) -> bool:
    return (
        isinstance(actor, str)
        and isinstance(principal, str)
        and LOGIN_RE.fullmatch(actor) is not None
        and LOGIN_RE.fullmatch(principal) is not None
        and actor.casefold() == principal.casefold()
    )


def decide(evidence: object, policy: Mapping[str, object], *, now_epoch_seconds: int | None = None) -> CapabilityDecision:
    """Classify typed current-session evidence and retain delegated canary binding."""
    errors = validate_policy(policy)
    if errors:
        raise ValueError("; ".join(errors))
    if not isinstance(evidence, AcquiredCapabilityEvidence):
        return CapabilityDecision(BLOCKED_CAPABILITY_UNAVAILABLE, None, _DECISION_SEAL)
    if not isinstance(evidence.requires_autonomous_protected_integration, bool):
        return CapabilityDecision(BLOCKED_CAPABILITY_UNAVAILABLE, None, _DECISION_SEAL)
    if not _valid_string_tuple(evidence.available_operations):
        return CapabilityDecision(BLOCKED_CAPABILITY_UNAVAILABLE, None, _DECISION_SEAL)
    if not _valid_string_tuple(evidence.operational_executor_routes):
        return CapabilityDecision(BLOCKED_CAPABILITY_UNAVAILABLE, None, _DECISION_SEAL)
    if not evidence.requires_autonomous_protected_integration:
        return CapabilityDecision(NOT_REQUIRED, None, _DECISION_SEAL)
    now = int(time.time()) if now_epoch_seconds is None else now_epoch_seconds
    cfg = integration_policy(policy)
    maximum_age = int(cfg.get("observation_max_age_seconds", DEFAULT_MAX_AGE_SECONDS))
    if not _fresh(evidence.observed_at_epoch_seconds, now, maximum_age):
        return CapabilityDecision(BLOCKED_CAPABILITY_UNAVAILABLE, None, _DECISION_SEAL)
    if cfg["direct_operation"] in evidence.available_operations:
        return CapabilityDecision(DIRECT_CAPABLE, None, _DECISION_SEAL)
    if (cfg["delegated_request_operation"] in evidence.available_operations
            and cfg["delegated_route"] in evidence.operational_executor_routes
            and _delegated_executor_is_operational(evidence.protected_executor, cfg, now_epoch_seconds=now)
            and _same_valid_actor(
                evidence.control_comment_actor,
                evidence.protected_executor.credential_principal
                if evidence.protected_executor is not None else None,
            )):
        assert evidence.protected_executor is not None
        return CapabilityDecision(
            DELEGATED_CAPABLE,
            evidence.protected_executor.canary_protected_main_sha,
            _DECISION_SEAL,
        )
    return CapabilityDecision(BLOCKED_CAPABILITY_UNAVAILABLE, None, _DECISION_SEAL)


def classify(evidence: object, policy: Mapping[str, object], *, now_epoch_seconds: int | None = None) -> str:
    """Compatibility classifier; delegated request construction must use ``decide``."""
    return decide(evidence, policy, now_epoch_seconds=now_epoch_seconds).state


def build_delegated_request(
    decision: object, *, repository: str, pr_number: int, expected_head_sha: str
) -> str:
    """Construct the canonical control request only from its sealed canary binding."""
    if (not isinstance(decision, CapabilityDecision)
            or decision._seal is not _DECISION_SEAL
            or decision.state != DELEGATED_CAPABLE
            or not isinstance(decision.delegated_protected_main_sha, str)
            or SHA_RE.fullmatch(decision.delegated_protected_main_sha) is None):
        raise ValueError("a sealed delegated-capable decision is required")
    if not isinstance(repository, str) or not repository.strip():
        raise ValueError("repository must be non-empty")
    if not isinstance(pr_number, int) or isinstance(pr_number, bool) or pr_number <= 0:
        raise ValueError("pull request number must be positive")
    if not isinstance(expected_head_sha, str) or SHA_RE.fullmatch(expected_head_sha) is None:
        raise ValueError("expected head SHA must be lowercase hexadecimal")
    return (f"/oteryn-mq-submit {repository} {pr_number} {expected_head_sha} "
            f"{decision.delegated_protected_main_sha}")


def validate_worker_release(
    evidence: object,
    policy: Mapping[str, object],
    *,
    now_epoch_seconds: int | None = None,
) -> list[str]:
    decision = decide(evidence, policy, now_epoch_seconds=now_epoch_seconds)
    if decision.state == BLOCKED_CAPABILITY_UNAVAILABLE:
        return ["protected integration capability unavailable before worker release: "
                "no fresh typed current-session evidence proved direct native merge-async "
                "or the bounded META executor"]
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
                      "reason": "no current-session capability evidence was supplied to this standalone CLI"},
                     sort_keys=True))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
