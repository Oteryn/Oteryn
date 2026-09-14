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
    return json.loads(verifier.DEFAULT_PACKET.read_text(encoding="utf-8"))


def test_canonical_packet_passes() -> None:
    assert verifier.validate(packet()) == []


def test_rejects_false_closure_and_readiness() -> None:
    candidate = packet()
    candidate["disposition"]["infra_state_closure"] = "PROVEN"
    candidate["disposition"]["product_or_deployment_readiness"] = "READY"
    errors = verifier.validate(candidate)
    assert "INFRA-STATE must remain UNKNOWN_BLOCKED" in errors
    assert "readiness must remain NOT_ESTABLISHED" in errors


def test_rejects_closure_condition_drift() -> None:
    candidate = packet()
    candidate["canonical_obligation"]["closure_condition"] = "green deployment"
    assert "canonical closure condition drifted" in verifier.validate(candidate)


def test_rejects_missing_release_or_direct_health_requirement() -> None:
    for field in ("exact deployed release and source digest", "direct health checks and results"):
        candidate = packet()
        candidate["smallest_additional_observation"]["required_fields"].remove(field)
        assert "additional observation must bind exact release and direct health" in verifier.validate(candidate)


def test_rejects_sensitive_payload_keys() -> None:
    candidate = deepcopy(packet())
    candidate["authorized_read_only_observations"]["nested"] = {"api_token": "redacted-is-still-not-needed"}
    errors = verifier.validate(candidate)
    assert any(error.startswith("packet contains forbidden sensitive key: api_token") for error in errors)


def test_rejects_partial_or_unbound_source_coordinates() -> None:
    candidate = packet()
    candidate["source_coordinates"].pop("Oteryn/Oteryn-Atlas")
    assert "source coordinates drifted from the exact observed repository heads" in verifier.validate(candidate)
    candidate = packet()
    candidate["source_coordinates"]["Oteryn/Oteryn-Platform"] = "84d504c"
    assert "source coordinates drifted from the exact observed repository heads" in verifier.validate(candidate)


def test_rejects_same_shape_wrong_source_coordinate() -> None:
    candidate = packet()
    candidate["source_coordinates"]["Oteryn/Oteryn-Platform"] = "0" * 40
    assert "source coordinates drifted from the exact observed repository heads" in verifier.validate(candidate)


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


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"PASS: {len(tests)} tests")
