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
    "Oteryn/Oteryn": "d9419b05eb98c81279297563c11fc90e4fe708ac",
    "Oteryn/Oteryn-Game": "775a09091743af395ecb8f1e440cb9c286bc0dd2",
    "Oteryn/Oteryn-Platform": "84d504c98acc8134eb4c9545711010b74c987974",
    "Oteryn/Oteryn-Atlas": "be09b84ad96d7e67571a460b55d9546b59bc89a7",
}
EXPECTED_OBSERVATIONS = {
    "route": "Authenticated GitHub REST repository metadata only",
    "repositories": {
        "Oteryn/Oteryn": {"environment_count": 0, "deployment_records_observed": 0, "release_records_observed": 0},
        "Oteryn/Oteryn-Game": {"environment_count": 0, "deployment_records_observed": 0, "release_records_observed": 0},
        "Oteryn/Oteryn-Atlas": {"environment_count": 0, "deployment_records_observed": 0, "release_records_observed": 0},
        "Oteryn/Oteryn-Platform": {
            "environment_count": 3,
            "release_records_observed": 0,
            "environment_names": ["production", "production-cloudflare", "synology-staging"],
            "latest_deployments": [
                {"environment": "production", "deployment_id": 5577006747, "source_sha": "7a8def78f86f5fc128448e3e7c11d191a1ebe595", "created_at": "2026-07-23T17:35:36Z", "latest_status": "failure", "status_time": "2026-07-23T17:35:52Z"},
                {"environment": "production-cloudflare", "deployment_id": 6338740997, "source_sha": "ba5f8ca3c9f99b7947b8aee24883aa304314076b", "created_at": "2026-09-08T22:50:59Z", "latest_status": "waiting", "status_time": "2026-09-08T22:51:00Z"},
                {"environment": "synology-staging", "deployment_id": 6414573336, "source_sha": "224e5f0719114652a42f60ad63e28ce7559097c5", "created_at": "2026-09-12T21:26:46Z", "latest_status": "success", "status_time": "2026-09-12T21:44:06Z"},
            ],
        },
    },
    "redaction": "No secret values, environment variables, URLs, logs, host identifiers, service payloads, or private configuration were requested or retained.",
}
EXPECTED_DISPOSITION = {
    "source": {"state": "PROVEN_BOUNDED", "claim": "The exact canonical obligation and current repository source heads are identified."},
    "deployment_metadata": {"state": "PROVEN_BOUNDED", "claim": "GitHub records the listed environments and historical deployment statuses at the observation time."},
    "configuration_health_snapshot": {"state": "UNKNOWN_BLOCKED", "claim": "No authorized readable evidence exposed a redacted private runtime configuration and health snapshot bound to an exact deployed release."},
    "infra_state_closure": "UNKNOWN_BLOCKED",
    "product_or_deployment_readiness": "NOT_ESTABLISHED",
}
EXPECTED_RECHECK_TRIGGER = "AUDIT186-LEAD receives an immutable, dated, redacted provider-owner snapshot containing every required field, or a separately authorized read-only runtime route becomes available; then verify the exact release binding and direct health evidence before reassessing INFRA-STATE."
EXPECTED_HANDOFF = "Keep INFRA-STATE open as UNKNOWN/BLOCKED. This packet is assurance evidence only and proposes no canonical audit-accounting mutation."
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

    if not isinstance(canonical, dict) or canonical != EXPECTED_CANONICAL_OBLIGATION:
        errors.append("canonical obligation drifted from the exact fail-closed claim")
    if not isinstance(disposition, dict) or disposition != EXPECTED_DISPOSITION:
        errors.append("INFRA disposition drifted from the bounded open state")
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

    if not isinstance(observations, dict) or observations != EXPECTED_OBSERVATIONS:
        errors.append("authorized read-only observations drifted from the exact recorded payload")
    for key in _iter_keys(packet):
        compact = key.replace("_", "")
        if any(fragment in key or fragment.replace("_", "") in compact for fragment in FORBIDDEN_KEY_FRAGMENTS):
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
    if packet.get("recheck_trigger") != EXPECTED_RECHECK_TRIGGER:
        errors.append("recheck trigger must preserve the exact fail-closed reassessment condition")
    if packet.get("handoff") != EXPECTED_HANDOFF:
        errors.append("handoff must preserve the exact fail-closed open disposition")
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
