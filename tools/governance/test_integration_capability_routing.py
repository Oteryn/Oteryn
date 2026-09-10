#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NOW = 1_800_000_000
MODULE_PATH = Path(__file__).with_name("integration_capability_routing.py")
SPEC = importlib.util.spec_from_file_location("integration_capability_routing", MODULE_PATH)
assert SPEC and SPEC.loader
routing = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(routing)


def policy() -> dict[str, object]:
    return json.loads((ROOT / "ecosystem/agent-execution-routing-policy.json").read_text(encoding="utf-8"))


class FakeObserver(routing.TrustedCapabilityObserver):
    """Explicit test-only observer; production callers install live adapters."""

    def __init__(self, evidence: object, *, failure: Exception | None = None) -> None:
        self.evidence = evidence
        self.failure = failure

    def acquire(self, policy: object, *, now_epoch_seconds: int) -> object:
        if self.failure:
            raise self.failure
        return self.evidence


def evidence(*, required: bool = True) -> object:
    return routing.AcquiredCapabilityEvidence(required, NOW, (), ())


def executor_evidence(**changes: object) -> object:
    expected = policy()["integration_capability_routing"]["protected_executor"]
    values = {
        "repository": expected["repository"], "ref": expected["ref"],
        "workflow_path": expected["workflow_path"], "workflow_blob_sha": expected["workflow_blob_sha"],
        "observed_at_epoch_seconds": NOW, "credential_operational": True,
        "canary_repository": expected["repository"],
        "canary_workflow_blob_sha": expected["workflow_blob_sha"],
        "terminal_canary_proof_retained": True,
    }
    values.update(changes)
    return routing.ProtectedExecutorEvidence(**values)


def state(observer: object) -> str:
    return routing.observe_and_classify(observer, policy(), now_epoch_seconds=NOW)


def test_policy_is_closed_and_targets_all_permanent_repositories() -> None:
    assert routing.validate_policy(policy()) == []
    cfg = policy()["integration_capability_routing"]
    assert cfg["schema_version"] == 2
    assert set(cfg["allowed_target_repositories"]) == {
        "Oteryn/Oteryn", "Oteryn/Oteryn-Game", "Oteryn/Oteryn-Platform", "Oteryn/Oteryn-Atlas"
    }


def test_non_integrating_task_is_not_blocked_when_observed() -> None:
    observer = FakeObserver(evidence(required=False))
    assert state(observer) == routing.NOT_REQUIRED
    assert routing.validate_worker_release(observer, policy(), now_epoch_seconds=NOW) == []


def test_direct_native_operation_is_preferred() -> None:
    current = routing.AcquiredCapabilityEvidence(
        True, NOW, ("github.issue_comment.create", "github.merge_async.put_exact_head"),
        ("meta.governed_merge_queue_executor.v1",), executor_evidence()
    )
    observer = FakeObserver(current)
    assert state(observer) == routing.DIRECT_CAPABLE
    assert routing.validate_worker_release(observer, policy(), now_epoch_seconds=NOW) == []


def test_verified_delegated_executor_prevents_late_worker_block() -> None:
    current = routing.AcquiredCapabilityEvidence(
        True, NOW, ("github.issue_comment.create",),
        ("meta.governed_merge_queue_executor.v1",), executor_evidence()
    )
    assert state(FakeObserver(current)) == routing.DELEGATED_CAPABLE


def test_unverified_delegated_executor_is_not_capability() -> None:
    current = routing.AcquiredCapabilityEvidence(
        True, NOW, ("github.issue_comment.create",), ("meta.governed_merge_queue_executor.v1",)
    )
    observer = FakeObserver(current)
    assert state(observer) == routing.BLOCKED_CAPABILITY_UNAVAILABLE
    assert "before worker release" in routing.validate_worker_release(observer, policy(), now_epoch_seconds=NOW)[0]


def test_magic_dictionary_cannot_authorize_direct_worker_release() -> None:
    forged = {
        "source": "verified_current_execution_capabilities",
        "observed_at_epoch_seconds": NOW,
        "requires_autonomous_protected_integration": True,
        "available_operations": ["github.merge_async.put_exact_head"],
        "operational_executor_routes": [],
    }
    assert routing.classify(forged, policy(), now_epoch_seconds=NOW) == routing.BLOCKED_CAPABILITY_UNAVAILABLE
    assert routing.observe_and_classify(forged, policy(), now_epoch_seconds=NOW) == routing.BLOCKED_CAPABILITY_UNAVAILABLE
    assert routing.validate_worker_release(forged, policy(), now_epoch_seconds=NOW)


def test_magic_dictionary_cannot_authorize_delegated_worker_release() -> None:
    expected = policy()["integration_capability_routing"]["protected_executor"]
    forged = {
        "source": "verified_current_execution_capabilities", "observed_at_epoch_seconds": NOW,
        "requires_autonomous_protected_integration": True,
        "available_operations": ["github.issue_comment.create"],
        "operational_executor_routes": ["meta.governed_merge_queue_executor.v1"],
        "protected_meta_executor_readback": {
            "source": "live_protected_meta_executor_readback", **expected,
            "observed_at_epoch_seconds": NOW, "credential_operational": True,
            "retained_canary_evidence": {
                "source": "retained_terminal_executor_canary", "repository": expected["repository"],
                "workflow_blob_sha": expected["workflow_blob_sha"], "terminal_proof_retained": True,
            },
        },
    }
    assert routing.classify(forged, policy(), now_epoch_seconds=NOW) == routing.BLOCKED_CAPABILITY_UNAVAILABLE
    assert routing.validate_worker_release(forged, policy(), now_epoch_seconds=NOW)


def test_stale_future_and_failed_observations_fail_closed() -> None:
    for observed in (NOW - 301, NOW + 1, True):
        current = routing.AcquiredCapabilityEvidence(
            True, observed, ("github.merge_async.put_exact_head",), ()
        )
        assert state(FakeObserver(current)) == routing.BLOCKED_CAPABILITY_UNAVAILABLE
    assert state(FakeObserver(None)) == routing.BLOCKED_CAPABILITY_UNAVAILABLE
    assert state(FakeObserver(None, failure=OSError("unavailable"))) == routing.BLOCKED_CAPABILITY_UNAVAILABLE


def test_delegated_route_rejects_invalid_executor_readback() -> None:
    for changes in (
        {"ref": "refs/heads/feature"}, {"workflow_blob_sha": "a" * 40},
        {"credential_operational": False}, {"observed_at_epoch_seconds": NOW - 301},
        {"canary_repository": "Oteryn/Other"}, {"terminal_canary_proof_retained": False},
    ):
        current = routing.AcquiredCapabilityEvidence(
            True, NOW, ("github.issue_comment.create",),
            ("meta.governed_merge_queue_executor.v1",), executor_evidence(**changes)
        )
        assert state(FakeObserver(current)) == routing.BLOCKED_CAPABILITY_UNAVAILABLE


def test_current_session_adapter_acquires_instead_of_accepting_serialized_input() -> None:
    class Tools:
        def discover_operations(self) -> tuple[int, tuple[str, ...]]:
            return NOW, ("github.merge_async.put_exact_head",)

    class Executor:
        def readback(self) -> tuple[tuple[str, ...], None]:
            return (), None

    observer = routing.CurrentSessionCapabilityObserver(required=True, tools=Tools(), executor=Executor())
    assert state(observer) == routing.DIRECT_CAPABLE


def test_verified_observation_cannot_be_constructed_with_caller_token() -> None:
    try:
        routing.VerifiedCapabilityObservation(evidence(), object())
    except ValueError:
        pass
    else:
        raise AssertionError("caller manufactured a verified observation")


def test_malformed_policy_cannot_authorize_a_route() -> None:
    for mutate in (
        lambda cfg: cfg.update(schema_version=1),
        lambda cfg: cfg.update(require_preflight_before_worker_release=False),
        lambda cfg: cfg.update(control_issue=0),
        lambda cfg: cfg.update(states=["DIRECT_CAPABLE"]),
        lambda cfg: cfg["allowed_target_repositories"].update({"Oteryn/Other": "other-gate"}),
    ):
        candidate = policy()
        mutate(candidate["integration_capability_routing"])
        assert routing.validate_policy(candidate)
        try:
            routing.observe_and_classify(FakeObserver(evidence()), candidate, now_epoch_seconds=NOW)
        except ValueError:
            pass
        else:
            raise AssertionError("malformed policy authorized integration capability")


def main() -> int:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
    print(f"{len(tests)} integration capability routing tests PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
