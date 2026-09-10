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
    return json.loads(
        (ROOT / "ecosystem/agent-execution-routing-policy.json").read_text(encoding="utf-8")
    )


def snapshot(*, required: bool = True) -> dict[str, object]:
    return {
        "source": routing.SNAPSHOT_SOURCE,
        "observed_at_epoch_seconds": NOW,
        "requires_autonomous_protected_integration": required,
        "available_operations": [],
        "operational_executor_routes": [],
    }


def test_policy_is_closed_and_targets_all_permanent_repositories() -> None:
    assert routing.validate_policy(policy()) == []
    cfg = policy()["integration_capability_routing"]
    assert set(cfg["allowed_target_repositories"]) == {
        "Oteryn/Oteryn", "Oteryn/Oteryn-Game", "Oteryn/Oteryn-Platform", "Oteryn/Oteryn-Atlas"
    }
    assert cfg["control_repository"] == "Oteryn/Oteryn"
    assert cfg["control_issue"] == 196


def test_non_integrating_task_is_not_blocked() -> None:
    assert routing.classify(snapshot(required=False), policy(), now_epoch_seconds=NOW) == routing.NOT_REQUIRED
    assert routing.validate_worker_release(snapshot(required=False), policy(), now_epoch_seconds=NOW) == []


def test_direct_native_operation_is_preferred() -> None:
    current = snapshot()
    current["available_operations"] = [
        "github.issue_comment.create",
        "github.merge_async.put_exact_head",
    ]
    current["operational_executor_routes"] = ["meta.governed_merge_queue_executor.v1"]
    assert routing.classify(current, policy(), now_epoch_seconds=NOW) == routing.DIRECT_CAPABLE
    assert routing.validate_worker_release(current, policy(), now_epoch_seconds=NOW) == []


def test_verified_delegated_executor_prevents_late_worker_block() -> None:
    current = snapshot()
    current["available_operations"] = ["github.issue_comment.create"]
    current["operational_executor_routes"] = ["meta.governed_merge_queue_executor.v1"]
    expected = policy()["integration_capability_routing"]["protected_executor"]
    current["protected_meta_executor_readback"] = {
        "source": routing.EXECUTOR_READBACK_SOURCE, **expected,
        "observed_at_epoch_seconds": NOW, "credential_operational": True,
        "retained_canary_evidence": {
            "source": routing.CANARY_SOURCE, "repository": expected["repository"],
            "workflow_blob_sha": expected["workflow_blob_sha"], "terminal_proof_retained": True,
        },
    }
    assert routing.classify(current, policy(), now_epoch_seconds=NOW) == routing.DELEGATED_CAPABLE
    assert routing.validate_worker_release(current, policy(), now_epoch_seconds=NOW) == []


def test_unverified_delegated_executor_is_not_capability() -> None:
    current = snapshot()
    current["available_operations"] = ["github.issue_comment.create"]
    assert routing.classify(current, policy(), now_epoch_seconds=NOW) == routing.BLOCKED_CAPABILITY_UNAVAILABLE
    errors = routing.validate_worker_release(current, policy(), now_epoch_seconds=NOW)
    assert len(errors) == 1 and "before worker release" in errors[0]


def test_wrong_snapshot_source_fails_closed() -> None:
    current = snapshot()
    current["source"] = "self_asserted"
    current["available_operations"] = ["github.merge_async.put_exact_head"]
    assert routing.classify(current, policy(), now_epoch_seconds=NOW) == routing.BLOCKED_CAPABILITY_UNAVAILABLE


def test_missing_or_duplicate_capability_lists_fail_closed() -> None:
    for key, value in (
        ("available_operations", None),
        ("available_operations", ["github.merge_async.put_exact_head"] * 2),
        ("operational_executor_routes", None),
        ("operational_executor_routes", ["meta.governed_merge_queue_executor.v1"] * 2),
    ):
        current = snapshot()
        current[key] = value
        assert routing.classify(current, policy(), now_epoch_seconds=NOW) == routing.BLOCKED_CAPABILITY_UNAVAILABLE


def test_stale_future_and_missing_snapshot_observations_fail_closed() -> None:
    for observed in (None, NOW - 301, NOW + 1, True):
        current = snapshot()
        current["observed_at_epoch_seconds"] = observed
        current["available_operations"] = ["github.merge_async.put_exact_head"]
        assert routing.classify(current, policy(), now_epoch_seconds=NOW) == routing.BLOCKED_CAPABILITY_UNAVAILABLE


def test_delegated_route_rejects_stale_or_self_asserted_executor_proof() -> None:
    expected = policy()["integration_capability_routing"]["protected_executor"]
    base = snapshot()
    base["available_operations"] = ["github.issue_comment.create"]
    base["operational_executor_routes"] = ["meta.governed_merge_queue_executor.v1"]
    valid = {
        "source": routing.EXECUTOR_READBACK_SOURCE, **expected,
        "observed_at_epoch_seconds": NOW, "credential_operational": True,
        "retained_canary_evidence": {
            "source": routing.CANARY_SOURCE, "repository": expected["repository"],
            "workflow_blob_sha": expected["workflow_blob_sha"], "terminal_proof_retained": True,
        },
    }
    for field, value in (
        ("source", "self_asserted"), ("ref", "refs/heads/feature"),
        ("workflow_blob_sha", "a" * 40), ("credential_operational", False),
        ("observed_at_epoch_seconds", NOW - 301),
        ("retained_canary_evidence", {"source": "self_asserted"}),
    ):
        current = dict(base)
        proof = dict(valid)
        proof[field] = value
        current["protected_meta_executor_readback"] = proof
        assert routing.classify(current, policy(), now_epoch_seconds=NOW) == routing.BLOCKED_CAPABILITY_UNAVAILABLE


def test_malformed_policy_cannot_authorize_a_route() -> None:
    cases = []
    for mutate in (
        lambda cfg: cfg.update(schema_version=2),
        lambda cfg: cfg.update(require_preflight_before_worker_release=False),
        lambda cfg: cfg.update(control_issue=0),
        lambda cfg: cfg.update(states=["DIRECT_CAPABLE"]),
        lambda cfg: cfg["allowed_target_repositories"].update({"Oteryn/Other": "other-gate"}),
    ):
        candidate = policy()
        cfg = candidate["integration_capability_routing"]
        mutate(cfg)
        cases.append(candidate)
    for candidate in cases:
        assert routing.validate_policy(candidate)
        try:
            routing.classify(snapshot(), candidate, now_epoch_seconds=NOW)
        except ValueError:
            pass
        else:
            raise AssertionError("malformed policy authorized integration capability")


def main() -> int:
    tests = [
        value
        for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    for test in tests:
        test()
    print(f"{len(tests)} integration capability routing tests PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
