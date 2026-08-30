#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "docs/agents/EXECUTION_STATE_CONTRACT.json"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
FP_RE = re.compile(r"^[0-9a-f]{64}$")


def _load_contract(path: Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("schema_version") != 1:
        raise ValueError("execution-state contract must use schema_version 1")
    fields = raw.get("durable_fields")
    statuses = raw.get("allowed_statuses")
    migration = raw.get("migration")
    if not isinstance(fields, dict) or not fields:
        raise ValueError("execution-state contract durable_fields must be a non-empty object")
    if not isinstance(statuses, list) or not all(isinstance(item, str) and item for item in statuses):
        raise ValueError("execution-state contract allowed_statuses must be a string list")
    if not isinstance(migration, dict) or migration.get("legacy_records_readable") is not True:
        raise ValueError("execution-state contract must keep legacy records readable")
    return raw


def _non_negative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _valid_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = dt.datetime.fromisoformat(text)
    except ValueError:
        return False
    return parsed.tzinfo is not None


def validate_checkpoint(
    checkpoint: dict[str, Any],
    *,
    require_bounded_fields: bool,
    contract_path: Path = DEFAULT_CONTRACT,
) -> list[str]:
    contract = _load_contract(contract_path)
    errors: list[str] = []
    if not isinstance(checkpoint, dict):
        return ["checkpoint must be an object"]

    status = checkpoint.get("status")
    allowed = set(contract["allowed_statuses"])
    if not isinstance(status, str) or status not in allowed:
        errors.append(f"status must be one of {sorted(allowed)}")

    durable = set(contract["durable_fields"])
    missing = sorted(durable - set(checkpoint))
    if require_bounded_fields and missing:
        errors.append(f"missing bounded fields: {', '.join(missing)}")
        return errors
    if not require_bounded_fields and missing:
        return errors

    candidate_frozen = checkpoint.get("candidate_frozen")
    if not isinstance(candidate_frozen, bool):
        errors.append("candidate_frozen must be boolean")

    candidate_head = checkpoint.get("candidate_head_sha")
    if not isinstance(candidate_head, str) or (candidate_head and not SHA_RE.fullmatch(candidate_head)):
        errors.append("candidate_head_sha must be empty or a lowercase 40-hex SHA")

    failure_fingerprint = checkpoint.get("failure_fingerprint")
    for key in ("progress_fingerprint", "failure_fingerprint"):
        value = checkpoint.get(key)
        if not isinstance(value, str) or (value and not FP_RE.fullmatch(value)):
            errors.append(f"{key} must be empty or a lowercase SHA-256 fingerprint")

    for key in ("identical_cycle_count", "retry_count", "retry_limit"):
        if not _non_negative_int(checkpoint.get(key)):
            errors.append(f"{key} must be a non-negative integer")

    waiting_for = checkpoint.get("waiting_for")
    if not isinstance(waiting_for, str):
        errors.append("waiting_for must be a string")
        waiting_for = ""

    if not _valid_timestamp(checkpoint.get("last_material_progress_at")):
        errors.append("last_material_progress_at must be offset-aware ISO-8601")

    if candidate_frozen is True:
        task_head = checkpoint.get("task_head_sha")
        if not isinstance(task_head, str) or not SHA_RE.fullmatch(task_head):
            errors.append("frozen checkpoint requires task_head_sha as a lowercase 40-hex SHA")
        elif candidate_head != task_head:
            errors.append("frozen candidate_head_sha must equal task_head_sha")

    if status == "RUNNING" and waiting_for:
        errors.append("RUNNING must not have waiting_for populated")
    if status == "WAITING_EXTERNAL" and not waiting_for:
        errors.append("WAITING_EXTERNAL requires waiting_for")

    retry_count = checkpoint.get("retry_count")
    retry_limit = checkpoint.get("retry_limit")
    identical_cycle_count = checkpoint.get("identical_cycle_count")
    if all(_non_negative_int(value) for value in (retry_count, retry_limit, identical_cycle_count)):
        recorded_failure_without_retry = (
            isinstance(failure_fingerprint, str)
            and bool(failure_fingerprint)
            and retry_limit == 0
        )
        exhausted = recorded_failure_without_retry or retry_count > retry_limit or (
            identical_cycle_count >= 2 and retry_count >= retry_limit
        )
        if exhausted and status not in set(contract["transition_rules"]["retry_exhaustion_terminal_states"]):
            errors.append("retry budget exhausted; status must be STALLED or WAITING_EXTERNAL")

    return errors
