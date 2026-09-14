#!/usr/bin/env python3
"""Verify the bounded AUDIT186 RUNTIME-02 INFRA-STATE packet."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PACKET = ROOT / "docs/evidence/organization-audit-20260907/runtime-assurance/infra-state-20260914.json"
SHA = re.compile(r"^[0-9a-f]{40}$")
EXPECTED_PACKET_ID = "AUDIT186-RUNTIME-02-INFRA-STATE-20260914"
EXPECTED_OBSERVATION_TIME = "2026-09-14T17:27:23Z"
EXPECTED_AUTHORITY = {
    "canonical_audit": "Oteryn/Oteryn#185@2d877271afa8f177983f3c6147472372adca0ed1",
    "programme": "Oteryn/Oteryn#203@82bc113797ecdc70d79aee628d339136b816e15d",
    "release_checkpoint": "Oteryn/Oteryn#186-comment-5666964258",
    "worker_seed": "Oteryn/Oteryn#208@75ee8b09dc6caac7bfc2a5bdddf3cfbab02c462e",
}
EXPECTED_SOURCE_COORDINATES = {
    "Oteryn/Oteryn": "d9419b05eb98c81279297563c11fc90e4fe708ac",
    "Oteryn/Oteryn-Game": "775a09091743af395ecb8f1e440cb9c286bc0dd2",
    "Oteryn/Oteryn-Platform": "84d504c98acc8134eb4c9545711010b74c987974",
    "Oteryn/Oteryn-Atlas": "be09b84ad96d7e67571a460b55d9546b59bc89a7",
}
FORBIDDEN_KEY_FRAGMENTS = (
    "secret",
    "token",
    "password",
    "credential",
    "private_key",
    "api_key",
    "environment_url",
    "log_url",
)


def _iter_keys(value: object):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key).lower()
            yield from _iter_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_keys(child)


def validate(packet: dict[str, object]) -> list[str]:
    errors: list[str] = []
    canonical = packet.get("canonical_obligation", {})
    disposition = packet.get("disposition", {})
    observations = packet.get("authorized_read_only_observations", {})
    additional = packet.get("smallest_additional_observation", {})

    if packet.get("schema_version") != 1 or packet.get("packet_id") != EXPECTED_PACKET_ID:
        errors.append("packet identity or schema drifted")
    if packet.get("obligation") != "INFRA-STATE":
        errors.append("packet must cover only INFRA-STATE")
    if packet.get("observation_time") != EXPECTED_OBSERVATION_TIME:
        errors.append("observation time drifted from the recorded read")
    if packet.get("authority") != EXPECTED_AUTHORITY:
        errors.append("authority coordinates drifted")

    expected_closure = "Authorized read-only configuration/health snapshot with redaction and exact release."
    if not isinstance(canonical, dict) or canonical.get("closure_condition") != expected_closure:
        errors.append("canonical closure condition drifted")
    if not isinstance(disposition, dict) or disposition.get("infra_state_closure") != "UNKNOWN_BLOCKED":
        errors.append("INFRA-STATE must remain UNKNOWN_BLOCKED")
    if not isinstance(disposition, dict) or disposition.get("product_or_deployment_readiness") != "NOT_ESTABLISHED":
        errors.append("readiness must remain NOT_ESTABLISHED")

    coordinates = packet.get("source_coordinates", {})
    if (
        not isinstance(coordinates, dict)
        or coordinates != EXPECTED_SOURCE_COORDINATES
        or any(not isinstance(value, str) or not SHA.fullmatch(value) for value in coordinates.values())
    ):
        errors.append("source coordinates drifted from the exact observed repository heads")

    if not isinstance(observations, dict) or observations.get("route") != "Authenticated GitHub REST repository metadata only":
        errors.append("observation route must remain bounded to GitHub metadata")
    for key in _iter_keys(packet):
        if any(fragment in key for fragment in FORBIDDEN_KEY_FRAGMENTS):
            errors.append(f"packet contains forbidden sensitive key: {key}")

    limitations = packet.get("limitations", [])
    required_limits = ("not a direct service-health observation", "does not establish present health", "no exact release")
    joined = " ".join(limitations).lower() if isinstance(limitations, list) else ""
    for phrase in required_limits:
        if phrase not in joined:
            errors.append(f"missing fail-closed limitation: {phrase}")

    if not isinstance(additional, dict) or additional.get("current_readability") != "BLOCKED_UNAVAILABLE":
        errors.append("private runtime observation readability must remain BLOCKED_UNAVAILABLE")
    fields = additional.get("required_fields", []) if isinstance(additional, dict) else []
    if not isinstance(fields, list) or "exact deployed release and source digest" not in fields or "direct health checks and results" not in fields:
        errors.append("additional observation must bind exact release and direct health")
    if not packet.get("recheck_trigger"):
        errors.append("exact recheck trigger is required")
    return errors


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PACKET
    packet = json.loads(path.read_text(encoding="utf-8"))
    errors = validate(packet)
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: bounded INFRA-STATE packet remains fail-closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
