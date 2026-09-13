#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NOW = 1_800_000_000
PROTECTED_MAIN_SHA = "0123456789abcdef0123456789abcdef01234567"
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
    return routing.AcquiredCapabilityEvidence(
        required, NOW, (), (), control_comment_actor="maintainer-user"
    )


def executor_evidence(**changes: object) -> object:
    expected = policy()["integration_capability_routing"]["protected_executor"]
    values = {
        "repository": expected["repository"], "ref": expected["ref"],
        "workflow_path": expected["workflow_path"], "workflow_blob_sha": expected["workflow_blob_sha"],
        "protected_main_sha": PROTECTED_MAIN_SHA,
        "observed_at_epoch_seconds": NOW, "credential_operational": True,
        "canary_repository": expected["repository"],
        "canary_workflow_blob_sha": expected["workflow_blob_sha"],
        "canary_protected_main_sha": PROTECTED_MAIN_SHA,
        "terminal_canary_proof_retained": True,
        "credential_principal": "maintainer-user",
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
        ("meta.governed_merge_queue_executor.v1",), executor_evidence(), "maintainer-user"
    )
    assert state(FakeObserver(current)) == routing.DELEGATED_CAPABLE


def test_delegated_request_retains_sealed_canary_sha() -> None:
    canary_x = PROTECTED_MAIN_SHA
    current_main_y = "a" * 40
    current = routing.AcquiredCapabilityEvidence(
        True, NOW, ("github.issue_comment.create",),
        ("meta.governed_merge_queue_executor.v1",), executor_evidence(), "maintainer-user"
    )
    decision = routing.observe_and_decide(FakeObserver(current), policy(), now_epoch_seconds=NOW)
    request = routing.build_delegated_request(
        decision, repository="Oteryn/Oteryn-Game", pr_number=528,
        expected_head_sha=current_main_y,
    )
    assert request.endswith(f" {current_main_y} {canary_x}")


def test_forged_decision_or_sha_cannot_replace_sealed_canary() -> None:
    for forged in (
        {"state": routing.DELEGATED_CAPABLE, "delegated_protected_main_sha": "a" * 40},
        object(),
    ):
        try:
            routing.build_delegated_request(
                forged, repository="Oteryn/Oteryn-Game", pr_number=528,
                expected_head_sha="a" * 40,
            )
        except ValueError:
            pass
        else:
            raise AssertionError("forged delegated decision constructed a request")
    try:
        routing.CapabilityDecision(routing.DELEGATED_CAPABLE, "a" * 40, object())
    except ValueError:
        pass
    else:
        raise AssertionError("caller manufactured a delegated decision")


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
            "protected_main_sha": PROTECTED_MAIN_SHA,
            "observed_at_epoch_seconds": NOW, "credential_operational": True,
            "retained_canary_evidence": {
                "source": "retained_terminal_executor_canary", "repository": expected["repository"],
                "workflow_blob_sha": expected["workflow_blob_sha"],
                "protected_main_sha": PROTECTED_MAIN_SHA,
                "terminal_proof_retained": True,
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
        {"protected_main_sha": "not-a-sha"}, {"canary_protected_main_sha": "not-a-sha"},
        {"canary_protected_main_sha": "a" * 40},
        {"credential_principal": ""},
    ):
        current = routing.AcquiredCapabilityEvidence(
            True, NOW, ("github.issue_comment.create",),
            ("meta.governed_merge_queue_executor.v1",), executor_evidence(**changes),
            "maintainer-user",
        )
        assert state(FakeObserver(current)) == routing.BLOCKED_CAPABILITY_UNAVAILABLE


def test_delegated_canary_is_invalidated_by_any_protected_main_change() -> None:
    current = routing.AcquiredCapabilityEvidence(
        True, NOW, ("github.issue_comment.create",),
        ("meta.governed_merge_queue_executor.v1",),
        executor_evidence(protected_main_sha="a" * 40, canary_protected_main_sha="b" * 40),
        "maintainer-user",
    )
    assert state(FakeObserver(current)) == routing.BLOCKED_CAPABILITY_UNAVAILABLE


def test_executor_workflow_rejects_github_reruns() -> None:
    text = (ROOT / ".github/workflows/governed-merge-queue-executor.yml").read_text(encoding="utf-8")
    assert "github.run_attempt == 1" in text


def test_delegated_route_requires_control_actor_to_match_credential_principal() -> None:
    for actor, principal in (
        (None, "maintainer-user"), ("maintainer-user", ""),
        ("different-user", "maintainer-user"), ("bad actor", "bad actor"),
    ):
        current = routing.AcquiredCapabilityEvidence(
            True, NOW, ("github.issue_comment.create",),
            ("meta.governed_merge_queue_executor.v1",),
            executor_evidence(credential_principal=principal), actor,
        )
        assert state(FakeObserver(current)) == routing.BLOCKED_CAPABILITY_UNAVAILABLE


def test_direct_route_is_independent_of_delegated_actor_identity() -> None:
    current = routing.AcquiredCapabilityEvidence(
        True, NOW, ("github.merge_async.put_exact_head",), (), None, None
    )
    assert state(FakeObserver(current)) == routing.DIRECT_CAPABLE


def test_policy_binds_current_executor_workflow_blob() -> None:
    import hashlib
    cfg = policy()["integration_capability_routing"]["protected_executor"]
    workflow = (ROOT / cfg["workflow_path"]).read_bytes()
    header = f"blob {len(workflow)}\0".encode("ascii")
    assert hashlib.sha1(header + workflow).hexdigest() == cfg["workflow_blob_sha"]


def test_current_session_adapter_acquires_instead_of_accepting_serialized_input() -> None:
    class Tools:
        def discover_operations(self) -> tuple[int, tuple[str, ...], str]:
            return NOW, ("github.merge_async.put_exact_head",), "maintainer-user"

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
