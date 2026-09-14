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
FORBIDDEN_KEYS = {"secret", "token", "password", "credential", "environment_url", "log_url"}


def validate(packet: dict[str, object]) -> list[str]:
    errors: list[str] = []
    canonical = packet.get("canonical_obligation", {})
    disposition = packet.get("disposition", {})
    observations = packet.get("authorized_read_only_observations", {})
    additional = packet.get("smallest_additional_observation", {})

    if packet.get("obligation") != "INFRA-STATE":
        errors.append("packet must cover only INFRA-STATE")
    expected_closure = "Authorized read-only configuration/health snapshot with redaction and exact release."
    if not isinstance(canonical, dict) or canonical.get("closure_condition") != expected_closure:
        errors.append("canonical closure condition drifted")
    if not isinstance(disposition, dict) or disposition.get("infra_state_closure") != "UNKNOWN_BLOCKED":
        errors.append("INFRA-STATE must remain UNKNOWN_BLOCKED")
    if not isinstance(disposition, dict) or disposition.get("product_or_deployment_readiness") != "NOT_ESTABLISHED":
        errors.append("readiness must remain NOT_ESTABLISHED")

    coordinates = packet.get("source_coordinates", {})
    if not isinstance(coordinates, dict) or set(coordinates) != {
        "Oteryn/Oteryn", "Oteryn/Oteryn-Game", "Oteryn/Oteryn-Platform", "Oteryn/Oteryn-Atlas"
    } or any(not isinstance(value, str) or not SHA.fullmatch(value) for value in coordinates.values()):
        errors.append("source coordinates must contain exactly four full commit SHAs")

    if not isinstance(observations, dict) or observations.get("route") != "Authenticated GitHub REST repository metadata only":
        errors.append("observation route must remain bounded to GitHub metadata")
    serialized = json.dumps(packet, sort_keys=True).lower()
    for key in FORBIDDEN_KEYS:
        if f'"{key}"' in serialized:
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
