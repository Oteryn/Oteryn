#!/usr/bin/env python3
"""Adversarial tests for the AUDIT186 RUNTIME-02 verifier."""

from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("verify_audit186_runtime_02.py")
SPEC = importlib.util.spec_from_file_location("verify_audit186_runtime_02", MODULE_PATH)
assert SPEC and SPEC.loader
verifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verifier)


def packet() -> dict[str, object]:
    return verifier.load_packet(verifier.DEFAULT_PACKET)


def test_canonical_packet_passes() -> None:
    assert verifier.validate(packet()) == []


def test_rejects_contradictory_extra_conclusion() -> None:
    candidate = packet()
    candidate["conclusion"] = "INFRA-STATE is PROVEN and production is healthy"
    assert "packet top-level keys drifted from the exact schema" in verifier.validate(candidate)


def test_rejects_false_closure_and_readiness() -> None:
    candidate = packet()
    candidate["disposition"]["infra_state_closure"] = "PROVEN"
    candidate["disposition"]["product_or_deployment_readiness"] = "READY"
    errors = verifier.validate(candidate)
    assert "INFRA disposition drifted from the bounded open state" in errors
    assert "INFRA-STATE must remain UNKNOWN_OPEN" in errors
    assert "readiness must remain NOT_ESTABLISHED" in errors


def test_rejects_nested_health_promotion() -> None:
    candidate = packet()
    candidate["disposition"]["configuration_health_snapshot"] = {
        "state": "PROVEN",
        "claim": "GitHub deployment metadata establishes direct runtime health and deployment readiness.",
    }
    assert "INFRA disposition drifted from the bounded open state" in verifier.validate(candidate)


def test_rejects_closure_condition_drift() -> None:
    candidate = packet()
    candidate["canonical_obligation"]["closure_condition"] = "green deployment"
    assert "canonical obligation drifted from the exact fail-closed claim" in verifier.validate(candidate)


def test_rejects_canonical_obligation_health_promotion() -> None:
    candidate = packet()
    candidate["canonical_obligation"]["effect"] = "Infrastructure health and deployment readiness are established."
    assert "canonical obligation drifted from the exact fail-closed claim" in verifier.validate(candidate)


def test_rejects_additional_observation_contract_drift() -> None:
    mutations = (
        lambda d: d["smallest_additional_observation"].update(needed="No observation needed."),
        lambda d: d["smallest_additional_observation"].update(current_authorization="Production mutation is authorized."),
        lambda d: d["smallest_additional_observation"]["required_fields"].remove("provider/runtime identity"),
        lambda d: d["smallest_additional_observation"]["required_fields"].remove("exact deployed release and source digest"),
        lambda d: d["smallest_additional_observation"].update(current_readability="AVAILABLE"),
    )
    for mutate in mutations:
        candidate = packet()
        mutate(candidate)
        assert "additional observation contract drifted from the exact authorized requirement" in verifier.validate(candidate)


def test_rejects_limitations_drift() -> None:
    candidate = packet()
    candidate["limitations"].append("Infrastructure health and deployment readiness are established.")
    assert "limitations drifted from the exact fail-closed list" in verifier.validate(candidate)

    candidate = packet()
    candidate["limitations"].pop()
    assert "limitations drifted from the exact fail-closed list" in verifier.validate(candidate)


def test_rejects_sensitive_payload_keys() -> None:
    keys = (
        "api_token", "cookie", "session-cookie", "connection_string", "connection-string",
        "personal_data", "personal-data", "database_dump", "database-dump", "backup",
        "private_deployment_state", "private-deployment-state",
    )
    for key in keys:
        candidate = deepcopy(packet())
        candidate["authorized_read_only_observations"]["nested"] = {key: "redacted-is-still-not-needed"}
        errors = verifier.validate(candidate)
        assert any(error.startswith("packet contains forbidden sensitive key:") for error in errors), key


def test_rejects_observation_payload_drift() -> None:
    mutations = (
        lambda d: d["authorized_read_only_observations"].update(verification_state="PROVEN"),
        lambda d: d["authorized_read_only_observations"].update(environment_count=3),
        lambda d: d["authorized_read_only_observations"]["unverified_fact_classes"].remove("repository deployment-record counts"),
    )
    for mutate in mutations:
        candidate = packet()
        mutate(candidate)
        assert "authorized read-only observations drifted from the exact recorded payload" in verifier.validate(candidate)


def test_rest_facts_and_runtime_readability_remain_unverified_or_unknown() -> None:
    candidate = packet()
    observations = candidate["authorized_read_only_observations"]
    assert observations["verification_state"] == "UNVERIFIED"
    assert "repositories" not in observations
    assert candidate["disposition"]["deployment_metadata"]["state"] == "UNKNOWN_UNVERIFIED"
    assert candidate["disposition"]["configuration_health_snapshot"]["state"] == "UNKNOWN"
    assert candidate["smallest_additional_observation"]["current_readability"] == "UNKNOWN"

    candidate["smallest_additional_observation"]["current_readability"] = "BLOCKED_UNAVAILABLE"
    assert "additional observation contract drifted from the exact authorized requirement" in verifier.validate(candidate)


def test_rejects_handoff_promotion() -> None:
    candidate = packet()
    candidate["handoff"] = "INFRA-STATE is closed and PROVEN; mark PR ready."
    assert "handoff must preserve the exact fail-closed open disposition" in verifier.validate(candidate)


def test_rejects_recheck_trigger_promotion() -> None:
    candidate = packet()
    candidate["recheck_trigger"] = "INFRA-STATE is proven; mark the PR Ready now."
    assert "recheck trigger must preserve the exact fail-closed reassessment condition" in verifier.validate(candidate)


def test_rejects_partial_or_unbound_source_coordinates() -> None:
    candidate = packet()
    candidate["source_coordinates"]["recorded_values"].pop("Oteryn/Oteryn-Atlas")
    assert "source coordinates drifted from the exact unverified recorded values" in verifier.validate(candidate)
    candidate = packet()
    candidate["source_coordinates"]["recorded_values"]["Oteryn/Oteryn-Platform"] = "84d504c"
    assert "source coordinates drifted from the exact unverified recorded values" in verifier.validate(candidate)


def test_rejects_same_shape_wrong_source_coordinate() -> None:
    candidate = packet()
    candidate["source_coordinates"]["recorded_values"]["Oteryn/Oteryn-Platform"] = "0" * 40
    assert "source coordinates drifted from the exact unverified recorded values" in verifier.validate(candidate)


def test_rejects_source_coordinate_promotion_without_retained_evidence() -> None:
    candidate = packet()
    candidate["source_coordinates"]["verification_state"] = "PROVEN_BOUNDED"
    assert "source coordinates drifted from the exact unverified recorded values" in verifier.validate(candidate)

    candidate = packet()
    candidate["disposition"]["source"] = {
        "state": "PROVEN_BOUNDED",
        "claim": "The recorded values are current repository heads.",
    }
    assert "INFRA disposition drifted from the bounded open state" in verifier.validate(candidate)


def test_rejects_authority_or_observation_drift() -> None:
    candidate = packet()
    candidate["authority"]["programme"] = "Oteryn/Oteryn#203@" + "0" * 40
    assert "authority coordinates drifted" in verifier.validate(candidate)
    candidate = packet()
    candidate["observation_time"] = "2026-09-14T17:27:24Z"
    assert "observation time drifted from the recorded read" in verifier.validate(candidate)


def test_rejects_packet_identity_drift() -> None:
    candidate = packet()
    candidate["packet_id"] = "AUDIT186-RUNTIME-02-INFRA-STATE-OTHER"
    assert "packet identity or schema drifted" in verifier.validate(candidate)


def test_rejects_boolean_schema_version() -> None:
    candidate = packet()
    candidate["schema_version"] = True
    assert "packet identity or schema drifted" in verifier.validate(candidate)


def test_rejects_duplicate_json_keys() -> None:
    raw = '{"handoff":"INFRA-STATE is PROVEN","handoff":"canonical"}'
    try:
        json.loads(raw, object_pairs_hook=verifier._reject_duplicate_keys)
    except ValueError as error:
        assert "duplicate JSON object key: handoff" in str(error)
    else:
        raise AssertionError("duplicate JSON object key was accepted")


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"PASS: {len(tests)} tests")
