#!/usr/bin/env python3
"""Validate sanitized v3.10 organization recovery closeout evidence."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

EXPECTED_GAPS = {f"GAP-RECOVERY-{index:03d}" for index in range(1, 7)}
ALLOWED_STATUSES = {"PASS", "UNKNOWN", "BLOCKED_OWNER_DECISION"}
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SENSITIVE_KEYS = {
    "secret_value",
    "token",
    "password",
    "private_key",
    "credential_value",
    "recovery_code",
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _walk(value: Any, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            _require(key not in SENSITIVE_KEYS, f"sensitive key forbidden at {path}.{key}")
            _walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk(child, f"{path}[{index}]")


def validate(data: dict[str, Any]) -> None:
    _require(data.get("schema_version") == 1, "schema_version must be 1")
    _require(
        data.get("prompt_id") == "OTERYN-V310-ORGANIZATION-RECOVERY-CLOSEOUT",
        "unexpected prompt_id",
    )
    _require(data.get("contains_secret_values") is False, "secret values must not be retained")
    _walk(data)

    repositories = data.get("repository_heads")
    _require(isinstance(repositories, dict), "repository_heads must be an object")
    expected_repositories = {
        "Oteryn/Oteryn",
        "Oteryn/Oteryn-Game",
        "Oteryn/Oteryn-Platform",
        "Oteryn/Oteryn-Atlas",
    }
    _require(set(repositories) == expected_repositories, "unexpected permanent repository set")
    for coordinate, entry in repositories.items():
        _require(isinstance(entry, dict), f"{coordinate}: repository head must be an object")
        sha = entry.get("main_sha")
        _require(isinstance(sha, str) and SHA_RE.fullmatch(sha) is not None, f"{coordinate}: invalid main_sha")
        _require(entry.get("protected") is True, f"{coordinate}: main must be observed protected")

    gaps = data.get("recovery_gaps")
    _require(isinstance(gaps, dict), "recovery_gaps must be an object")
    _require(set(gaps) == EXPECTED_GAPS, "recovery_gaps must contain exactly GAP-RECOVERY-001..006")

    non_pass = []
    for gap_id, gap in gaps.items():
        _require(isinstance(gap, dict), f"{gap_id}: gap entry must be an object")
        status = gap.get("status")
        _require(status in ALLOWED_STATUSES, f"{gap_id}: invalid status {status!r}")
        evidence = gap.get("evidence")
        _require(isinstance(evidence, list) and evidence, f"{gap_id}: evidence must be a non-empty list")

        if status == "PASS":
            generated = gap.get("generation_evidence")
            restored = gap.get("restore_or_reconstruction_evidence")
            _require(isinstance(generated, list) and generated, f"{gap_id}: PASS requires generation evidence")
            _require(isinstance(restored, list) and restored, f"{gap_id}: PASS requires restore/reconstruction evidence")
        elif status == "UNKNOWN":
            reason = gap.get("unknown_reason")
            _require(isinstance(reason, str) and reason.strip(), f"{gap_id}: UNKNOWN requires unknown_reason")
            non_pass.append(gap_id)
        else:
            decisions = gap.get("owner_decisions_required")
            _require(isinstance(decisions, list) and decisions, f"{gap_id}: BLOCKED requires owner decisions")
            non_pass.append(gap_id)

    completion_status = data.get("completion_status")
    merge_eligible = data.get("merge_eligible")
    if non_pass:
        _require(completion_status == "BLOCKED", "non-PASS gaps require BLOCKED completion_status")
        _require(merge_eligible is False, "non-PASS gaps must not be merge eligible")
    else:
        _require(completion_status == "DONE", "all-PASS evidence requires DONE completion_status")
        _require(merge_eligible is True, "all-PASS evidence must be merge eligible")

    scope_confirmation = data.get("scope_confirmation")
    _require(
        isinstance(scope_confirmation, str) and scope_confirmation.strip(),
        "scope_confirmation is required",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "evidence",
        nargs="?",
        default="docs/evidence/OTERYN-V310-ORGANIZATION-RECOVERY-CLOSEOUT-20260824.json",
    )
    args = parser.parse_args()
    path = Path(args.evidence)
    data = json.loads(path.read_text(encoding="utf-8"))
    validate(data)
    print(
        f"v3.10 organization recovery evidence PASS: {len(data['recovery_gaps'])} gaps validated; "
        f"terminal={data['completion_status']}; merge_eligible={data['merge_eligible']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
