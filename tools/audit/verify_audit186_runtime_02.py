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
EXPECTED_CANONICAL_OBLIGATION = {
    "source": "docs/evidence/organization-audit-20260907/unknowns.json@2d877271afa8f177983f3c6147472372adca0ed1",
    "missing": "Private production runtime configuration",
    "reason": "No host exception or production access used.",
    "effect": "No infrastructure health or deployment readiness conclusion.",
    "owner_route": "Provider operations owners",
    "closure_condition": "Authorized read-only configuration/health snapshot with redaction and exact release.",
}
EXPECTED_SOURCE_COORDINATES = {
    "verification_state": "UNVERIFIED",
    "claim": "These recorded values are not current-head facts: no independently revalidatable sanitized default-branch or ref observation coordinates and no immutable response identity were retained.",
    "recorded_values": {
        "Oteryn/Oteryn": "d9419b05eb98c81279297563c11fc90e4fe708ac",
        "Oteryn/Oteryn-Game": "775a09091743af395ecb8f1e440cb9c286bc0dd2",
        "Oteryn/Oteryn-Platform": "84d504c98acc8134eb4c9545711010b74c987974",
        "Oteryn/Oteryn-Atlas": "be09b84ad96d7e67571a460b55d9546b59bc89a7",
    },
}
EXPECTED_OBSERVATIONS = {
    "route": "Authenticated GitHub REST repository metadata only",
    "verification_state": "UNVERIFIED",
    "claim": "No independently revalidatable sanitized response coordinates or immutable response digests were retained for the REST reads.",
    "unverified_fact_classes": [
        "repository environment counts",
        "repository deployment-record counts",
        "repository release-record counts",
        "environment names",
        "latest-deployment identity, source, creation time, status, and status time",
    ],
    "redaction": "No secret values, environment variables, URLs, logs, host identifiers, service payloads, or private configuration were requested or retained.",
}
EXPECTED_DISPOSITION = {
    "source": {"state": "UNKNOWN_UNVERIFIED", "claim": "The canonical obligation is identified, but the recorded repository source-coordinate values are unverified because independently revalidatable default-branch or ref evidence was not retained."},
    "deployment_metadata": {"state": "UNKNOWN_UNVERIFIED", "claim": "REST-derived counts and latest-deployment facts are not treated as proven because independently revalidatable sanitized observation coordinates or immutable response digests were not retained."},
    "configuration_health_snapshot": {"state": "UNKNOWN", "claim": "No exact private-runtime route or action and no observed access blocker are durably evidenced; direct runtime configuration and health readability remains unknown."},
    "infra_state_closure": "UNKNOWN_OPEN",
    "product_or_deployment_readiness": "NOT_ESTABLISHED",
}
EXPECTED_LIMITATIONS = [
    "Recorded repository source-coordinate values are explicitly unverified because no independently revalidatable sanitized default-branch or ref observation coordinates and no immutable response identity were retained.",
    "REST-derived environment, deployment, release, and latest-deployment facts are explicitly unverified because no independently revalidatable sanitized response coordinates or immutable response digests were retained.",
    "Unverified GitHub orchestration metadata does not establish an external deployment, an exact release, present runtime health, production health, or deployment readiness.",
    "No provider-owner release-to-runtime attestation was retained or observed; readability is unverified because no exact private-runtime route or action was identified, inspected, or attempted.",
    "No production, provider, administrative, DNS, database, deployment, runner, environment, secret, or host mutation was authorized or performed.",
]
EXPECTED_ADDITIONAL_OBSERVATION = {
    "needed": "One provider-operations-owner-authorized, dated, redacted read-only snapshot for each claimed production runtime, binding sanitized configuration and direct health results to an exact deployed release/source digest.",
    "required_fields": [
        "provider/runtime identity",
        "observation time",
        "exact deployed release and source digest",
        "sanitized configuration invariants",
        "direct health checks and results",
        "authorized verifier identity or immutable evidence digest",
    ],
    "current_authorization": "Read-only observation is authorized in principle by this batch; no exact private-runtime route or action was identified, inspected, or attempted in this session.",
    "current_readability": "UNKNOWN",
}
EXPECTED_RECHECK_TRIGGER = "AUDIT186-LEAD receives independently revalidatable sanitized default-branch or ref observation coordinates with immutable response identity before reassessing source-coordinate truth, and receives an immutable, dated, redacted provider-owner snapshot containing every required field or identifies and separately authorizes an exact read-only runtime route and records its observed result before reassessing INFRA-STATE."
EXPECTED_HANDOFF = "Keep INFRA-STATE open as UNKNOWN. Recorded source-coordinate values and REST-derived deployment facts are unverified; no provider-owner release-to-runtime attestation was retained or observed, and runtime readability remains unknown because no exact private-runtime route or action was identified, inspected, or attempted. Readiness remains NOT_ESTABLISHED, and this packet proposes no canonical audit-accounting mutation."
EXPECTED_TOP_LEVEL_KEYS = {
    "schema_version",
    "packet_id",
    "obligation",
    "observation_time",
    "authority",
    "canonical_obligation",
    "source_coordinates",
    "authorized_read_only_observations",
    "disposition",
    "limitations",
    "smallest_additional_observation",
    "recheck_trigger",
    "handoff",
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
    "cookie",
    "connection_string",
    "connectionstring",
    "personal_data",
    "personaldata",
    "database_dump",
    "databasedump",
    "backup",
    "private_deployment_state",
    "privatedeploymentstate",
)


def _normalize_key(key: object) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(key).lower()).strip("_")


def _iter_keys(value: object):
    if isinstance(value, dict):
        for key, child in value.items():
            yield _normalize_key(key)
            yield from _iter_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_keys(child)


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def load_packet(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys)


def validate(packet: dict[str, object]) -> list[str]:
    errors: list[str] = []
    canonical = packet.get("canonical_obligation", {})
    disposition = packet.get("disposition", {})
    observations = packet.get("authorized_read_only_observations", {})
    additional = packet.get("smallest_additional_observation", {})

    if set(packet) != EXPECTED_TOP_LEVEL_KEYS:
        errors.append("packet top-level keys drifted from the exact schema")
    if (
        type(packet.get("schema_version")) is not int
        or packet.get("schema_version") != 1
        or packet.get("packet_id") != EXPECTED_PACKET_ID
    ):
        errors.append("packet identity or schema drifted")
    if packet.get("obligation") != "INFRA-STATE":
        errors.append("packet must cover only INFRA-STATE")
    if packet.get("observation_time") != EXPECTED_OBSERVATION_TIME:
        errors.append("observation time drifted from the recorded read")
    if packet.get("authority") != EXPECTED_AUTHORITY:
        errors.append("authority coordinates drifted")

    if not isinstance(canonical, dict) or canonical != EXPECTED_CANONICAL_OBLIGATION:
        errors.append("canonical obligation drifted from the exact fail-closed claim")
    if not isinstance(disposition, dict) or disposition != EXPECTED_DISPOSITION:
        errors.append("INFRA disposition drifted from the bounded open state")
    if not isinstance(disposition, dict) or disposition.get("infra_state_closure") != "UNKNOWN_OPEN":
        errors.append("INFRA-STATE must remain UNKNOWN_OPEN")
    if not isinstance(disposition, dict) or disposition.get("product_or_deployment_readiness") != "NOT_ESTABLISHED":
        errors.append("readiness must remain NOT_ESTABLISHED")

    coordinates = packet.get("source_coordinates", {})
    recorded_values = coordinates.get("recorded_values", {}) if isinstance(coordinates, dict) else {}
    if (
        not isinstance(coordinates, dict)
        or coordinates != EXPECTED_SOURCE_COORDINATES
        or not isinstance(recorded_values, dict)
        or any(not isinstance(value, str) or not SHA.fullmatch(value) for value in recorded_values.values())
    ):
        errors.append("source coordinates drifted from the exact unverified recorded values")

    if not isinstance(observations, dict) or observations != EXPECTED_OBSERVATIONS:
        errors.append("authorized read-only observations drifted from the exact recorded payload")
    for key in _iter_keys(packet):
        compact = key.replace("_", "")
        if any(fragment in key or fragment.replace("_", "") in compact for fragment in FORBIDDEN_KEY_FRAGMENTS):
            errors.append(f"packet contains forbidden sensitive key: {key}")

    if packet.get("limitations") != EXPECTED_LIMITATIONS:
        errors.append("limitations drifted from the exact fail-closed list")

    if not isinstance(additional, dict) or additional != EXPECTED_ADDITIONAL_OBSERVATION:
        errors.append("additional observation contract drifted from the exact authorized requirement")
    if packet.get("recheck_trigger") != EXPECTED_RECHECK_TRIGGER:
        errors.append("recheck trigger must preserve the exact fail-closed reassessment condition")
    if packet.get("handoff") != EXPECTED_HANDOFF:
        errors.append("handoff must preserve the exact fail-closed open disposition")
    return errors


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PACKET
    try:
        packet = load_packet(path)
    except (json.JSONDecodeError, ValueError) as error:
        print("FAIL")
        print(f"- {error}")
        return 1
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
