#!/usr/bin/env python3
"""Compare a caller-supplied GitHub enforcement snapshot with Governance V2.

This tool is deliberately offline and read-only. It does not call GitHub, mutate
settings, persist lifecycle state, or repair drift. Missing observations remain
UNKNOWN instead of being guessed from documentation or defaults.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DESIRED_STATE = ROOT / "ecosystem/governance-desired-state.json"
ENFORCEMENT_FIELDS = (
    "required_gate",
    "merge_queue",
    "strict_required_status_checks",
    "required_approvals",
    "codeowner_review_required",
    "conversation_resolution",
    "linear_history",
    "force_pushes",
    "deletions",
    "broad_bypass",
)
STATUS_EXIT_CODES = {"TARGET": 0, "DRIFT": 1, "UNKNOWN": 2}


def _rows(document: dict[str, Any], key: str, label: str) -> list[dict[str, Any]]:
    rows = document.get(key)
    if not isinstance(rows, list):
        raise ValueError(f"{label} {key!r} must be an array")
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError(f"{label} {key!r} entries must be objects")
    return rows


def _index_repositories(rows: list[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        repository = row.get("repository")
        if not isinstance(repository, str) or not repository.strip():
            raise ValueError(f"{label} repository must be a non-empty string")
        if repository in indexed:
            raise ValueError(f"duplicate {label} repository: {repository}")
        indexed[repository] = row
    return indexed


def _same_value(expected: Any, actual: Any) -> bool:
    """Compare policy values without treating bool and int as interchangeable."""
    return type(expected) is type(actual) and expected == actual


def audit_snapshot(desired_state: dict[str, Any], live_state: dict[str, Any]) -> dict[str, Any]:
    """Return TARGET, DRIFT or UNKNOWN for each permanent repository.

    `live_state` is a normalized observation supplied by the caller. A missing
    repository or enforcement field is UNKNOWN. A known mismatch is DRIFT and
    takes precedence over UNKNOWN for that repository and for the aggregate.
    """
    if desired_state.get("schema_version") != 2:
        raise ValueError("desired state schema_version must be 2")

    desired_rows = _rows(desired_state, "permanent_repositories", "desired state")
    live_rows = _rows(live_state, "repositories", "live state")
    desired_by_repo = _index_repositories(desired_rows, "desired-state")
    live_by_repo = _index_repositories(live_rows, "live-state")

    unexpected = sorted(set(live_by_repo) - set(desired_by_repo))
    if unexpected:
        raise ValueError(f"unexpected live-state repositories: {unexpected}")

    repository_reports: list[dict[str, Any]] = []
    for desired in desired_rows:
        repository = desired["repository"]
        missing_desired = [field for field in ENFORCEMENT_FIELDS if field not in desired]
        if missing_desired:
            raise ValueError(f"{repository}: desired state missing enforcement fields: {missing_desired}")

        live = live_by_repo.get(repository)
        if live is None:
            repository_reports.append(
                {
                    "repository": repository,
                    "status": "UNKNOWN",
                    "drift": [],
                    "unknown": list(ENFORCEMENT_FIELDS),
                }
            )
            continue

        drift: list[dict[str, Any]] = []
        unknown: list[str] = []
        for field in ENFORCEMENT_FIELDS:
            if field not in live or live[field] is None:
                unknown.append(field)
                continue
            expected = desired[field]
            actual = live[field]
            if not _same_value(expected, actual):
                drift.append({"field": field, "expected": expected, "actual": actual})

        status = "DRIFT" if drift else "UNKNOWN" if unknown else "TARGET"
        repository_reports.append(
            {
                "repository": repository,
                "status": status,
                "drift": drift,
                "unknown": unknown,
            }
        )

    statuses = {row["status"] for row in repository_reports}
    aggregate = "DRIFT" if "DRIFT" in statuses else "UNKNOWN" if "UNKNOWN" in statuses else "TARGET"
    return {"status": aggregate, "repositories": repository_reports}


def _load_json(path: Path) -> dict[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError(f"{path}: JSON root must be an object")
    return document


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare a normalized live GitHub enforcement snapshot with Governance V2 desired state."
    )
    parser.add_argument("--live-state", type=Path, required=True, help="caller-supplied normalized GitHub snapshot JSON")
    parser.add_argument(
        "--desired-state",
        type=Path,
        default=DEFAULT_DESIRED_STATE,
        help="Governance V2 desired-state JSON",
    )
    args = parser.parse_args()

    try:
        report = audit_snapshot(_load_json(args.desired_state), _load_json(args.live_state))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"status": "INVALID", "error": str(exc)}, sort_keys=True))
        return 3

    print(json.dumps(report, indent=2, sort_keys=True))
    return STATUS_EXIT_CODES[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
