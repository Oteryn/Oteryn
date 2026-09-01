Warning: truncated output (original token count: 32644)
Total output lines: 2995

#!/usr/bin/env python3
"""Read-only Oteryn governance drift audit.

Offline mode validates the desired-state contract. Live mode reads GitHub's REST
and GraphQL APIs only; it never mutates settings. A caller must provide GH_TOKEN
or GITHUB_TOKEN.
"""
from __future__ import annotations

import argparse
import base64
import fnmatch
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DESIRED_PATH = ROOT / "ecosystem" / "governance-desired-state.json"
API = "https://api.github.com"
HISTORICAL_PREFIXES = (
    "docs/evidence/",
    "docs/agents/tasks/archive/",
    "docs/migration/",
    "docs/architecture/adr/",
    "docs/recovery/",
)
HISTORICAL_FILES = {"ecosystem/repositories.json"}
POLICY_DECLARATION_FILES = {"ecosystem/governance-desired-state.json"}
WORKFLOW_RUN_RE = re.compile(r"^https://github\.com/[^/]+/[^/]+/actions/runs/(\d+)(?:/|$)")
V2_REQUIRED_CONTEXTS = {
    "Oteryn/Oteryn": ["meta-gate"],
    "Oteryn/Oteryn-Game": ["game-gate"],
    "Oteryn/Oteryn-Platform": ["platform-gate"],
    "Oteryn/Oteryn-Atlas": ["atlas-gate"],
}
CANONICAL_V2_ROLLOUT_REPOSITORY = "Oteryn/Oteryn"
CANONICAL_V2_ROLLOUT_ISSUE = 102
CANONICAL_V2_ROLLOUT_LOCATOR = f"{CANONICAL_V2_ROLLOUT_REPOSITORY}#{CANONICAL_V2_ROLLOUT_ISSUE}"
ROLLOUT_STATE_FIELDS = {
    "repository",
    "required_checks",
    "required_check_sources",
    "main_protected",
    "squash_only",
    "delete_branch_on_merge",
    "merge_queue",
    "protection",
}
ROLLOUT_PROTECTION_FIELDS = {
    "pull_requests",
    "force_pushes",
    "deletions",
    "broad_bypass",
    "strict_required_status_checks",
    "required_approving_review_count",
    "require_code_owner_review",
    "require_conversation_resolution",
    "required_linear_history",
}
LIFECYCLE_RECORD_TYPES = {"PENDING_BASELINE", "PRE_TRANSITION", "TERMINAL"}
CONTROL_PLANE_R2_NON_AUTHORITY_PREFIXES = (
    "docs/evidence/",
    "docs/agents/tasks/archive/",
)
CONTROL_PLANE_OWNER_AUTHORIZATION_RECORD_TYPE = "CONTROL_PLANE_R2_OWNER_AUTHORIZATION"
CONTROL_PLANE_OWNER_AUTHORIZATION_FIELDS = {
    "record_type",
    "repository",
    "pull_request",
    "material_head_sha",
    "scope",
    "authorize_integration",
}
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def expected_checks(item: dict) -> set[str]:
    checks = item.get("required_checks")
    if checks is None and item.get("required_gate"):
        checks = [item["required_gate"]]
    if not isinstance(checks, list) or not checks or not all(isinstance(value, str) and value for value in checks):
        raise SystemExit(f"repository lacks required checks: {item}")
    if len(set(checks)) != len(checks):
        raise SystemExit(f"duplicate required checks: {item}")
    return set(checks)


def expected_check_app_id(item: dict) -> int:
    app_id = item.get("required_check_app_id")
    if not isinstance(app_id, int) or app_id <= 0:
        raise SystemExit(f"repository lacks required_check_app_id: {item}")
    return app_id


def expected_sources_satisfied(sources: dict[str, set[int | None]], expected: set[str], app_id: int) -> bool:
    return all(sources.get(context) == {app_id} for context in expected)


def allowed_required_checks(item: dict) -> set[str]:
    return expected_checks(item)


def required_contexts_match(item: dict, observed: set[str]) -> bool:
    return expected_checks(item) == observed


def _parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _normalized_rollout_state(value: object) -> dict | None:
    if not isinstance(value, dict) or set(value) != ROLLOUT_STATE_FIELDS:
        return None
    repository = value.get("repository")
    checks = value.get("required_checks")
    sources = value.get("required_check_sources")
    protection = value.get("protection")
    if (
        not isinstance(repository, str)
        or not repository
        or not isinstance(checks, list)
        or not checks
        or not all(isinstance(check, str) and check for check in checks)
        or len(checks) != len(set(checks))
        or not isinstance(sources, dict)
        or set(sources) != set(checks)
        or not isinstance(protection, dict)
        or set(protection) != ROLLOUT_PROTECTION_FIELDS
    ):
        return None
    normalized_sources: dict[str, list[int | None]] = {}
    for check in checks:
        app_ids = sources.get(check)
        if (
            not isinstance(app_ids, list)
            or not app_ids
            or not all(
                app_id is None
                or (isinstance(app_id, int) and not isinstance(app_id, bool) and app_id > 0)
                for app_id in app_ids
            )
            or len(app_ids) != len(set(app_ids))
        ):
            return None
        normalized_sources[check] = sorted(
            app_ids, key=lambda app_id: (-1 if app_id is None else app_id)
        )
    if not all(isinstance(value.get(field), bool) for field in (
        "main_protected", "squash_only", "delete_branch_on_merge", "merge_queue",
    )):
        return None
    if not all(isinstance(protection.get(field), bool) for field in (
        "pull_requests", "force_pushes", "deletions", "broad_bypass",
        "strict_required_status_checks", "require_code_owner_review",
        "require_conversation_resolution", "required_linear_history",
    )):
        return None
    if not isinstance(protection.get("required_approving_review_count"), int) or isinstance(
        protection["required_approving_review_count"], bool
    ) or protection["required_approving_review_count"] < 0:
        return None
    return {
        "repository": repository,
        "required_checks": sorted(checks),
        "required_check_sources": {
            check: normalized_sources[check]
            for check in sorted(normalized_sources)
        },
        "main_protected": value["main_protected"],
        "squash_only": value["squash_only"],
        "delete_branch_on_merge": value["delete_branch_on_merge"],
        "merge_queue": value["merge_queue"],
        "protection": {
            field: protection[field]
            for field in sorted(ROLLOUT_PROTECTION_FIELDS)
        },
    }


def target_rollout_state(item: dict) -> dict:
    required_checks = item.get("required_checks")
    state = {
        "repository": item.get("repository"),
        "required_checks": required_checks,
        "required_check_sources": (
            {
                check: [item.get("required_check_app_id")]
                for check in required_checks
            }
            if isinstance(required_checks, list)
            else {}
        ),
        "main_protected": item.get("main_protected"),
        "squash_only": item.get("squash_only"),
        "delete_branch_on_merge": item.get("delete_branch_on_merge"),
        "merge_queue": item.get("merge_queue"),
        "protection": item.get("protection"),
    }
    normalized = _normalized_rollout_state(state)
    if normalized is None:
        raise ValueError(f"invalid desired rollout state: {item}")
    return normalized


def rollout_state_fingerprint(state: object) -> str:
    normalized = _normalized_rollout_state(state)
    if normalized is None:
        raise ValueError("invalid rollout state readback")
    payload = json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _rollout_states_match(left: object, right: object) -> bool:
    normalized_left = _normalized_rollout_state(left)
    normalized_right = _normalized_rollout_state(right)
    return normalized_left is not None and normalized_left == normalized_right


def _rollout_state_difference_paths(before: dict, after: dict, prefix: str = "") -> set[str]:
    differences: set[str] = set()
    for key in set(before) | set(after):
        path = f"{prefix}.{key}" if prefix else key
        if key not in before or key not in after:
            differences.add(path)
            continue
        old = before[key]
        new = after[key]
        if isinstance(old, dict) and isinstance(new, dict):
            differences.update(_rollout_state_difference_paths(old, new, path))
        elif old != new:
            differences.add(path)
    return differences


def _allowed_rollout_deviations(differences: set[str], allowed: object) -> bool:
    if not isinstance(allowed, list):
        return False
    return all(
        any(difference == path or difference.startswith(path + ".") for path in allowed)
        for difference in differences
    )


def _decode_json_comment_body(body: object) -> dict | None:
    if not isinstance(body, str):
        return None
    candidate = body.strip()
    if candidate.startswith("```json") and candidate.endswith("```"):
        candidate = candidate[len("```json"): -3].strip()
    try:
        decoded = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    return decoded if isinstance(decoded, dict) else None


def _decode_lifecycle_body(body: object) -> dict | None:
    return _decode_json_comment_body(body)


def _malformed_lifecycle_hints(body: object) -> dict | None:
    """Extract only identity hints from an invalid JSON lifecycle candidate.

    A lifecycle record is intended to be a standalone JSON object.  We must not
    treat arbitrary prose as governance evidence, but an unparseable JSON object
    carrying lifecycle identity fields cannot be silently ignored either.
    """
    if not isinstance(body, str):
        return None
    candidate = body.strip()
    if candidate.startswith("```json"):
        candidate = candidate[len("```json"):].strip()
    if not candidate.startswith("{"):
        return None

    lifecycle_keys = (
        "record_type",
        "repository",
        "transition_id",
        "pre_transition_comment_id",
        "pre_state_fingerprint",
        "post_state_fingerprint",
    )
    if not any(re.search(rf'"{key}"\s*:', candidate) for key in lifecycle_keys):
        return None

    hints: dict[str, object] = {}
    for key in ("record_type", "repository", "transition_id"):
        match = re.search(rf'"{key}"\s*:\s*"([^"\\]*)"', candidate)
        if match is not None:
            hints[key] = match.group(1)
    pre_match = re.search(r'"pre_transition_comment_id"\s*:\s*(\d+)', candidate)
    if pre_match is not None:
        hints["pre_transition_comment_id"] = int(pre_match.group(1))
    return hints


def _is_lifecycle_candidate(body: dict) -> bool:
    return body.get("record_type") in LIFECYCLE_RECORD_TYPES or any(
        key in body for key in ("transition_id", "pre_state_fingerprint", "post_state_fingerprint")
    )


def _read_lifecycle_records(records: object) -> tuple[list[dict] | None, list[dict]]:
    """Return direct-read records and malformed lifecycle candidates for later scoping."""
    if records is None:
        return None, []
    if not isinstance(records, list):
        return None, []
    parsed: list[dict] = []
    malformed: list[dict] = []
    seen_ids: set[int] = set()
    for comment in records:
        if not isinstance(comment, dict):
            return None, []
        raw_body = comment.get("body")
        body = _decode_lifecycle_body(raw_body)
        if body is None:
            hints = _malformed_lifecycle_hints(raw_body)
            if hints is not None:
                malformed.append({"id": comment.get("id"), "hints": hints})
            continue
        if not _is_lifecycle_candidate(body):
            continue
        if body.get("record_type") not in LIFECYCLE_RECORD_TYPES:
            malformed.append({"id": comment.get("id"), "body": body})
            continue
        comment_id = comment.get("id")
        created_at = _parse_timestamp(comment.get("created_at"))
        updated_at = comment.get("updated_at")
        if (
            not isinstance(comment_id, int)
            or comment_id <= 0
            or comment_id in seen_ids
            or created_at is None
            or updated_at != comment.get("created_at")
            or comment.get("in_reply_to_id") not in (None, "")
        ):
            malformed.append({"id": comment_id, "body": body})
            continue
        seen_ids.add(comment_id)
        parsed.append({"id": comment_id, "created_at": created_at, "body": body})
    return parsed, malformed


def _malformed_lifecycle_evidence_is_relevant(
    malformed_records: list[dict], records: list[dict], wanted: dict
) -> bool:
    """Only malformed evidence for this provider can invalidate its lifecycle.

    All providers share the canonical Issue.  A malformed record must therefore
    identify this repository directly, or link to this repository's exact
    pre-transition record, before it can affect this repository's classification.
    """
    repository = wanted.get("repository")
    pre_repository_by_comment_id: dict[int, str] = {}
    transition_ids: set[str] = set()
    for record in records:
        body = record.get("body")
        if not isinstance(body, dict) or body.get("record_type") != "PRE_TRANSITION":
            continue
        record_repository = body.get("repository")
        comment_id = record.get("id")
        if isinstance(record_repository, str) and isinstance(comment_id, int):
            pre_repository_by_comment_id[comment_id] = record_repository
        transition_id = body.get("transition_id")
        if record_repository == repository and isinstance(transition_id, str):
            transition_ids.add(transition_id)
    for record in malformed_records:
        body = record.get("body", record.get("hints"))
        if not isinstance(body, dict):
            continue
        terminal_shaped = (
            body.get("record_type") == "TERMINAL"
            or "pre_transition_comment_id" in body
            or "terminal_status" in body
        )
        linked_repository = pre_repository_by_comment_id.get(
            body.get("pre_transition_comment_id")
        )
        if terminal_shaped:
            if linked_repository is not None:
                if linked_repository == repository:
                    return True
                continue
            if (
                body.get("repository") == repository
                or body.get("transition_id") in transition_ids
            ):
                return True
        elif (
            body.get("repository") == repository
            or body.get("transition_id") in transition_ids
        ):
            return True
    return False


def _global_rollout_transitions_are_serial(records: list[dict]) -> bool:
    """Require every provider cutover on the shared canonical Issue to be serial."""
    pre_by_id: dict[int, dict] = {}
    for record in records:
        body = record.get("body")
        if (
            isinstance(body, dict)
            and body.get("record_type") == "PRE_TRANSITION"
            and body.get("repository") in V2_REQUIRED_CONTEXTS
            and isinstance(body.get("transition_id"), str)
            and body["transition_id"]
        ):
            pre_by_id[record["id"]] = record
    terminals_by_pre: dict[int, list[dict]] = {}
    for record in records:
        body = record.get("body")
        if not isinstance(body, dict) or body.get("record_type") != "TERMINAL":
            continue
        linked = body.get("pre_transition_comment_id")
        pre = pre_by_id.get(linked)
        if pre is None:
            continue
        if body.get("transition_id") != pre["body"].get("transition_id"):
            return False
        terminals_by_pre.setdefault(linked, []).append(record)
    ordered = sorted(pre_by_id.values(), key=lambda record: (record["created_at"], record["id"]))
    rollout_order = tuple(V2_REQUIRED_CONTEXTS)
    phase = -1
    for record in ordered:
        position = rollout_order.index(record["body"]["repository"])
        if position < phase or position > phase + 1:
            return False
        phase = max(phase, position)
    for previous, current in zip(ordered, ordered[1:]):
        previous_terminals = terminals_by_pre.get(previous["id"], [])
        if len(previous_terminals) != 1 or previous_terminals[0]["created_at"] >= current["created_at"]:
            return False
    return True


def _pending_record_identifies_repository(record: dict, repository: object) -> bool:
    """Keep schema-invalid pending duplicates in the exactly-one decision when scoped."""
    body = record.get("body")
    if (
        not isinstance(repository, str)
        or not repository
        or not isinstance(body, dict)
        or body.get("record_type") != "PENDING_BASELINE"
    ):
        return False
    if body.get("repository") == repository:
        return True
    readback = _normalized_rollout_state(body.get("pre_state_readback"))
    return readback is not None and readback["repository"] == repository


def _valid_pending_record(record: dict, wanted: dict) -> dict | None:
    body = record["body"]
    if (
        body.get("record_type") != "PENDING_BASELINE"
        or body.get("repository") != wanted.get("repository")
        or _parse_timestamp(body.get("captured_at")) is None
        or "started_at" in body
        or "closed_at" in body
    ):
        return None
    readback = _normalized_rollout_state(body.get("pre_state_readback"))
    if readback is None or readback["repository"] != wanted.get("repository"):
        return None
    try:
        fingerprint = rollout_state_fingerprint(readback)
    except ValueError:
        return None
    if body.get("pre_state_fingerprint") != fingerprint:
        return None
    return readback


def _valid_pre_transition_record(record: dict, wanted: dict, baseline: dict) -> dict | None:
    body = record["body"]
    transition_id = body.get("transition_id")
    allowed_deviations = body.get("allowed_deviations")
    if (
        body.get("record_type") != "PRE_TRANSITION"
        or not isinstance(transition_id, str)
        or not transition_id
        or body.get("repository") != wanted.get("repository")
        or body.get("issue_or_pr") != CANONICAL_V2_ROLLOUT_LOCATOR
        or _parse_timestamp(body.get("expires_at")) is None
        or body.get("pre_state_fingerprint") != rollout_state_fingerprint(baseline)
        or not isinstance(allowed_deviations, list)
        or not allowed_deviations
        or not all(isinstance(path, str) and path for path in allowed_deviations)
        or len(allowed_deviations) != len(set(allowed_deviations))
        or body.get("success_condition") != {"moving_base_canary": "required"}
        or not isinstance(body.get("rollback_condition"), dict)
        or not body["rollback_condition"]
        or "started_at" in body
        or "closed_at" in body
    ):
        return None
    return body


def _valid_moving_base_receipt(value: object, wanted: dict) -> bool:
    if not isinstance(value, dict):
        return False
    required = {
        "repository", "pr_a", "a_head", "main_before_b", "pr_b", "main_after_b",
        "base_sha", "a_head_unchanged", "merge_group_sha", "aggregate_gate_run", "main_after_a",
    }
    if set(value) != required or value.get("repository") != wanted.get("repository"):
        return False
    if (
        not isinstance(value.get("pr_a"), int)
        or value["pr_a"] <= 0
        or not isinstance(value.get("pr_b"), int)
        or value["pr_b"] <= 0
        or value["pr_a"] == value["pr_b"]
    ):
        return False
    for field in (
        "a_head", "main_before_b", "main_after_b", "base_sha", "a_head_unchanged",
        "merge_group_sha", "main_after_a",
    ):
        if not isinstance(value.get(field), str) or SHA_RE.fullmatch(value[field]) is None:
            return False
    if (
        value["a_head_unchanged"] != value["a_head"]
        or value["base_sha"] != value["main_after_b"]
        or value["main_after_b"] == value["main_before_b"]
        or value["main_after_a"] == value["main_after_b"]
    ):
        return False
    gate = value.get("aggregate_gate_run")
    return (
        isinstance(gate, dict)
        and set(gate) == {"context", "head_sha", "conclusion", "run_id"}
        and gate.get("context") == wanted.get("required_checks", [None])[0]
        and gate.get("head_sha") == value["merge_group_sha"]
        and gate.get("conclusion") == "success"
        and isinstance(gate.get("run_id"), int)
        and gate["run_id"] > 0
    )


def _valid_terminal_record(record: dict, pre_record: dict, baseline: dict, wanted: dict) -> tuple[str, dict] | None:
    body = record["body"]
    expires_at = _parse_timestamp(pre_record["body"].get("expires_at"))
    status = body.get("terminal_status")
    terminal_fields = {
        "record_type", "transition_id", "pre_transition_comment_id", "terminal_status",
        "post_state_fingerprint", "post_state_readback",
    }
    expected_fields = terminal_fields | ({"moving_base_receipt"} if status == "SUCCESS" else set())
    if (
        body.get("record_type") != "TERMINAL"
        or body.get("transition_id") != pre_record["body"].get("transition_id")
        or body.get("pre_transition_comment_id") != pre_record["id"]
        or status not in {"SUCCESS", "ROLLED_BACK"}
        or set(body) != expected_fields
        or expires_at is None
        or record["created_at"] > expires_at
        or "started_at" in body
        or "closed_at" in body
    ):
        return None
    post_state = _normalized_rollout_state(body.get("post_state_readback"))
    if post_state is None or post_state["repository"] != wanted.get("repository"):
        return None
    try:
        post_fingerprint = rollout_state_fingerprint(post_state)
    except ValueError:
        return None
    if body.get("post_state_fingerprint") != post_fingerprint:
        return None
    if status == "SUCCESS":
        if not _rollout_states_match(post_state, target_rollout_state(wanted)):
            return None
        if not _valid_moving_base_receipt(body.get("moving_base_receipt"), wanted):
            return None
    else:
        if body.get("post_state_fingerprint") != pre_record["body"].get("pre_state_fingerprint") or not _rollout_states_match(post_state, baseline):
            return None
    return status, post_state


def classify_rollout_state(
    wanted: dict,
    live_state: object,
    lifecycle_records: object,
    *,
    now: object,
    success_receipt_verifier=None,
) -> str:
    """Classify one repository from direct lifecycle-comment and settings readback.

    `SUCCESS` is a valid terminal receipt whose effective target state is `TARGET`.
    `PENDING` and `ROLLED_BACK` are deliberately non-target terminal states.
    """
    live = _normalized_rollout_state(live_state)
    records, malformed_records = _read_lifecycle_records(lifecycle_records)
    current_time = _parse_timestamp(now)
    if live_state is None or lifecycle_records is None or current_time is None:
        return "UNKNOWN"
    if records is None:
        return "UNKNOWN"
    if live is None or live["repository"] != wanted.get("repository"):
        return "DRIFT"
    if _malformed_lifecycle_evidence_is_relevant(malformed_records, records, wanted):
        return "DRIFT"

    repository = wanted.get("repository")
    pending_candidates = [
        record for record in records
        if _pending_record_identifies_repository(record, repository)
    ]
    if len(pending_candidates) != 1:
        return "DRIFT"
    baseline = _valid_pending_record(pending_candidates[0], wanted)
    if baseline is None:
        return "DRIFT"

    all_pre_records = [
        record for record in records
        if record["body"].get("record_type") == "PRE_TRANSITION"
    ]
    pre_records = [
        record for record in all_pre_records
        if record["body"].get("repository") == repository
    ]
    if pre_records:
        first_pre = min(pre_records, key=lambda record: (record["created_at"], record["id"]))
        pending_record = pending_candidates[0]
        if (pending_record["created_at"], pending_record["id"]) >= (
            first_pre["created_at"], first_pre["id"]
        ):
            return "DRIFT"
    transitions: dict[str, dict] = {}
    for record in pre_records:
        pre = _valid_pre_transition_record(record, wanted, baseline)
        if pre is None or pre["transition_id"] in transitions:
            return "DRIFT"
        transitions[pre["transition_id"]] = record
    for record in all_pre_records:
        body = record["body"]
        if (
            body.get("transition_id") in transitions
            and body.get("repository") != repository
            and not isinstance(body.get("repository"), str)
        ):
            return "DRIFT"

    pre_records_by_id = {record["id"]: record for record in all_pre_records}
    terminals_by_transition: dict[str, list[dict]] = {}
    for record in records:
        body = record["body"]
        if body.get("record_type") != "TERMINAL":
            continue
        linked_pre = pre_records_by_id.get(body.get("pre_transition_comment_id"))
        if linked_pre is None:
            if body.get("repository") == repository or body.get("transition_id") in transitions:
                return "DRIFT"
            continue
        if linked_pre["body"].get("repository") != repository:
            continue
        transition_id = body.get("transition_id")
        pre = transitions.get(transition_id)
        if pre is None or pre["id"] != linked_pre["id"]:
            return "DRIFT"
        terminals_by_transition.setdefault(transition_id, []).append(record)
    terminal_results: dict[str, tuple[str, dict, dict]] = {}
    for transition_id, terminal_records in terminals_by_transition.items():
        if len(terminal_records) != 1:
            return "DRIFT"
        terminal_record = terminal_records[0]
        result = _valid_terminal_record(terminal_record, transitions[transition_id], baseline, wanted)
        if result is None:
            return "DRIFT"
        status, post_state = result
        terminal_results[transition_id] = (status, post_state, terminal_record)

    ordered_pre_records = sorted(
        transitions.values(), key=lambda record: (record["created_at"], record["id"])
    )
    for previous, current in zip(ordered_pre_records, ordered_pre_records[1:]):
        previous_terminal = terminal_results.get(previous["body"]["transition_id"])
        if (
            previous_terminal is None
            or previous_terminal[2]["created_at"] >= current["created_at"]
        ):
            return "DRIFT"

    if transitions and not _global_rollout_transitions_are_serial(records):
        return "DRIFT"

    active = [record for transition_id, record in transitions.items() if transition_id not in terminal_results]
    if len(active) > 1:
        return "DRIFT"
    if active:
        pre = active[0]["body"]
        expires_at = _parse_timestamp(pre.get("expires_at"))
        if expires_at is None or current_time > expires_at:
            return "DRIFT"
        differences = _rollout_state_difference_paths(baseline, live)
        if not _allowed_rollout_deviations(differences, pre["allowed_deviations"]):
            return "DRIFT"
        return "TRANSITION"

    if terminal_results:
        status, post_state, terminal_record = max(
            terminal_results.values(),
            key=lambda value: (value[2]["created_at"], value[2]["id"]),
        )
        if status == "SUCCESS":
            if not _rollout_states_match(live, post_state):
                return "DRIFT"
            if success_receipt_verifier is None:
                return "UNKNOWN"
            direct_evidence = success_receipt_verifier(
                wanted,
                transitions[terminal_record["body"]["transition_id"]],
                terminal_record,
            )
            if direct_evidence not in {"SUCCESS", "DRIFT", "UNKNOWN"}:
                return "UNKNOWN"
            return direct_evidence
        return "ROLLED_BACK" if _rollout_states_match(live, post_state) else "DRIFT"
    return "PENDING" if _rollout_states_match(live, baseline) else "DRIFT"


def terminal_v2_closeout_permitted(classifications: object) -> bool:
    if not isinstance(classifications, dict) or set(classifications) != set(V2_REQUIRED_CONTEXTS):
        return False
    return all(effective_rollout_state(state) == "TARGET" for state in classifications.values())


def effective_rollout_state(classification: object) -> str:
    """Expose the target/non-target lifecycle state used by closeout gates.

    A valid terminal `SUCCESS` receipt is the only way the direct-read classifier
    reaches the desired target configuration, so it deliberately maps to TARGET.
    """
    return "TARGET" if classification == "SUCCESS" else str(classification)


def is_control_plane_r2(paths: object) -> bool:
    """Return whether a candidate needs the GS-5 owner-confirmation path.

    Aggregate-gate fan-in can be implemented outside a fixed directory, so a
    path allowlist would let a new implementation path evade the control.  The
    intentionally conservative contract treats every material repository path
    as R2 except directories explicitly reserved for historical, non-authority
    records.  Missing, malformed, or empty path input fails closed as R2.
    """
    if (
        not isinstance(paths, list)
        or not paths
        or not all(isinstance(path, str) and path for path in paths)
    ):
        return True
    return any(
        not any(path.startswith(prefix) for prefix in CONTROL_PLANE_R2_NON_AUTHORITY_PREFIXES)
        for path in paths
    )


def _unknown_control_plane_owner_authorization(
    repository: object,
    pull_request: object,
    material_head_sha: object,
    scope: object,
) -> dict:
    return {
        "status": "UNKNOWN",
        "repository": repository,
        "pull_request": pull_request,
        "material_head_sha": material_head_sha,
        "scope": scope,
    }


def _matching_control_plane_owner_authorization_comment(
    comment: object,
    *,
    repository: str,
    pull_request: int,
    material_head_sha: str,
    scope: str,
) -> dict | None:
    if not isinstance(comment, dict):
        return None
    comment_id = comment.get("id")
    user = comment.get("user")
    body = _decode_json_comment_body(comment.get("body"))
    created_at = comment.get("created_at")
    if (
        not isinstance(comment_id, int)
        or isinstance(comment_id, bool)
        or comment_id <= 0
        or not isinstance(user, dict)
        or not isinstance(user.get("login"), str)
        or not user["login"]
        or user.get("type") != "User"
        or comment.get("updated_at") != created_at
        or _parse_timestamp(created_at) is None
        or not isinstance(body, dict)
        or set(body) != CONTROL_PLANE_OWNER_AUTHORIZATION_FIELDS
        or body.get("record_type") != CONTROL_PLANE_OWNER_AUTHORIZATION_RECORD_TYPE
        or body.get("repository") != repository
        or body.get("pull_request") != pull_request
        or not isinstance(body.get("pull_request"), int)
        or isinstance(body.get("pull_request"), bool)
        or body.get("material_head_sha") != material_head_sha
        or not isinstance(body.get("material_head_sha"), str)
        or SHA_RE.fullmatch(body["material_head_sha"]) is None
        or body.get("scope") != scope
        or not isinstance(body.get("scope"), str)
        or not body["scope"].strip()
        or body.get("authorize_integration") is not True
    ):
        return None
    return {
        "comment_id": comment_id,
        "author_login": user["login"],
        "actor_type": user["type"],
        "repository": repository,
        "pull_request": pull_request,
        "material_head_sha": material_head_sha,
        "scope": scope,
        "authorize_integration": True,
    }


def _matches_control_plane_owner_authorization_identity(
    comment: object,
    *,
    repository: str,
    pull_request: int,
    material_head_sha: str,
    scope: str,
) -> bool:
    """Match the immutable identity before deciding whether its evidence is valid.

    A malformed, edited, bot-authored, or otherwise invalid duplicate must not be
    filtered away before the exactly-one authorization invariant is enforced.
    """
    if not isinstance(comment, dict):
        return False
    body = _decode_json_comment_body(comment.get("body"))
    if isinstance(body, dict):
        return (
            body.get("record_type") == CONTROL_PLANE_OWNER_AUTHORIZATION_RECORD_TYPE
            and body.get("repository") == repository
            and isinstance(body.get("pull_request"), int)
            and not isinstance(body.get("pull_request"), bool)
            and body.get("pull_request") == pull_request
            and body.get("material_head_sha") == material_head_sha
            and body.get("scope") == scope
        )
    return _malformed_control_plane_owner_authorization_identity_matches(
        comment.get("body"),
        repository=repository,
        pull_request=pull_request,
        material_head_sha=material_head_sha,
        scope=scope,
    )


def _malformed_control_plane_owner_authorization_identity_matches(
    body: object,
    *,
    repository: str,
    pull_request: int,
    material_head_sha: str,
    scope: str,
) -> bool:
    """Fail closed for an invalid JSON comment that names this authorization.

    The exactly-one owner-authorization invariant applies before an individual
    comment is accepted as valid evidence.  A JSON-looking duplicate therefore
    remains relevant when its identity fields are recoverable even if its JSON
    document is truncated or otherwise malformed.
    """
    if not isinstance(body, str):
        return False
    candidate = body.strip()
    if candidate.startswith("```json"):
        candidate = candidate[len("```json"):].strip()
    if not candidate.startswith("{"):
        return False

    string_fields = {
        "record_type": CONTROL_PLANE_OWNER_AUTHORIZATION_RECORD_TYPE,
        "repository": repository,
        "material_head_sha": material_head_sha,
        "scope": scope,
    }
    for field, expected in string_fields.items():
        match = re.search(rf'"{field}"\s*:\s*"([^"\\]*)"', candidate)
        if match is None or match.group(1) != expected:
            return False
    pull_request_match = re.search(r'"pull_request"\s*:\s*(\d+)', candidate)
    return (
        pull_request_match is not None
        and int(pull_request_match.group(1)) == pull_request
    )


def actions_permissions_enabled(payload: object) -> bool:
    return isinstance(payload, dict) and payload.get("enabled") is True


def _strip_yaml_comment(raw: str) -> str:
    quote = None
    escaped = False
    out = []
    for char in raw:
        if escaped:
            out.append(char)
            escaped = False
            continue
        if char == "\\" and quote == '"':
            out.append(char)
            escaped = True
            continue
        if char in {"'", '"'}:
            if quote is None:
                quote = char
            elif quote == char:
                quote = None
            out.append(char)
            continue
        if char == "#" and quote is None:
            break
        out.append(char)
    return "".join(out).rstrip()


def _yaml_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] == '"':
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return value[1:-1]
        return decoded if isinstance(decoded, str) else value[1:-1]
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return value[1:-1].replace("''", "'")
    return value


def _yaml_mapping_field(body: str) -> tuple[bool, str, str] | None:
    match = re.fullmatch(
        r"""(?P<dash>-\s*)?(?P<key>[A-Za-z0-9_-]+|"[^"]+"|'[^']+')\s*:\s*(?P<value>.*)""",
        body.strip(),
    )
    if not match:
        return None
    key_token = match.group("key")
    if key_token.startswith('"') and "\\" in key_token:
        try:
            key = json.loads(key_token)
        except json.JSONDecodeError:
            return None
        if not isinstance(key, str):
            return None
    else:
        key = _yaml_scalar(key_token)
    return bool(match.group("dash")), key, match.group("value").strip()


WRITE_CAPABLE_TOKEN_SCOPES = {
    "actions", "attestations", "checks", "contents", "deployments", "discussions",
    "id-token", "issues", "packages", "pages", "pull-requests", "security-events", "statuses",
}


def _simple_flow_mapping(value: str) -> dict[str, str] | None:
    value = value.strip()
    if not (value.startswith("{") and value.endswith("}")):
        return None
    inner = value[1:-1].strip()
    if not inner:
        return {}
    parts: list[str] = []
    current: list[str] = []
    quote: str | None = None
    escaped = False
    for char in inner:
        if escaped:
            current.append(char)
            escaped = False
            continue
        if char == "\\" and quote == '"':
            current.append(char)
            escaped = True
            continue
        if char in {"'", '"'}:
            if quote is None:
                quote = char
            elif quote == char:
                quote = None
            current.append(char)
            continue
        if char == "," and quote is None:
            parts.append("".join(current).strip())
            current = []
            continue
        if char in "{}[]" and quote is None:
            return None
        current.append(char)
    if quote is not None:
        return None
    parts.append("".join(current).strip())
    result: dict[str, str] = {}
    for part in parts:
        field = _yaml_mapping_field(part)
        if field is None or field[0] or not field[1] or field[1] in result:
            return None
        result[field[1]] = _yaml_scalar(field[2])
    return result


def _permissions_write_wide(values: dict[str, str]) -> bool:
    return WRITE_CAPABLE_TOKEN_SCOPES <= {key for key, value in values.items() if value == "write"}


def dependabot_github_actions_entry_valid(text: str) -> bool:
    rows = []
    for raw in text.splitlines():
        if "\t" in raw:
            return False
        line = _strip_yaml_comment(raw)
        if not line.strip():
            continue
        rows.append((len(line) - len(line.lstrip(" ")), line.strip()))
    top_level_keys: set[str] = set()
    for indent, body in rows:
        if indent != 0:
            continue
        field = _yaml_mapping_field(body)
        if field is None or field[0] or not field[1] or field[1] in top_level_keys:
            return False
        top_level_keys.add(field[1])
    if not any(
        indent == 0 and (field := _yaml_mapping_field(body)) is not None
        and not field[0] and field[1] == "version" and _yaml_scalar(field[2]) == "2"
        for indent, body in rows
    ):
        return False
    try:
        updates_index = next(
            i for i, (indent, body) in enumerate(rows)
            if indent == 0 and (field := _yaml_mapping_field(body)) is not None
            and not field[0] and field[1] == "updates" and field[2] == ""
        )
    except StopIteration:
        return False
    i = updates_index + 1
    if i >= len(rows) or rows[i][0] == 0:
        return False
    item_indent = rows[i][0]
    while i < len(rows):
        indent, body = rows[i]
        if indent == 0:
            break
        if indent != item_indent or not body.startswith("-"):
            return False
        entry = []
        while i < len(rows):
            child_indent, child_body = rows[i]
            if child_indent == 0 or (entry and child_indent == item_indent and child_body.startswith("-")):
                break
            entry.append((child_indent, child_body))
            i += 1
        ecosystem = None
        directory = None
        interval = None
        schedule_indent = None
        schedule_child_indent = None
        seen_item_fields: set[str] = set()
        field_indent = item_indent + 2
        for offset, (child_indent, child_body) in enumerate(entry):
            field = _yaml_mapping_field(child_body)
            is_inline_item = offset == 0 and field is not None and field[0] and child_indent == item_indent
            is_item_field = field is not None and (
                is_inline_item or (not field[0] and child_indent == field_indent)
            )
            if schedule_indent is not None and child_indent <= schedule_indent and not is_inline_item:
                schedule_indent = None
                schedule_child_indent = None
            if is_item_field:
                if field[1] in seen_item_fields:
                    return False
                seen_item_fields.add(field[1])
            if is_item_field and field[1] == "package-ecosystem":
                ecosystem = _yaml_scalar(field[2])
            elif is_item_field and field[1] == "directory":
                directory = _yaml_scalar(field[2])
            elif is_item_field and field[1] == "schedule" and field[2] == "":
                schedule_indent = field_indent if is_inline_item else child_indent
                schedule_child_indent = schedule_indent + 2
            elif (
                schedule_indent is not None
                and field is not None and not field[0]
                and child_indent == schedule_child_indent
                and field[1] == "interval"
            ):
                interval = _yaml_scalar(field[2])
        if ecosystem == "github-actions":
            return directory == "/" and interval in {"daily", "weekly", "monthly", "quarterly", "semiannually", "yearly"}
    return False

def _codeowners_glob_regex(pattern: str) -> str:
    out = []
    i = 0
    while i < len(pattern):
        char = pattern[i]
        if char == "*":
            if i + 1 < len(pattern) and pattern[i + 1] == "*":
                out.append(".*")
                i += 2
                continue
            out.append("[^/]*")
        elif char == "?":
            out.append("[^/]")
        else:
            out.append(re.escape(char))
        i += 1
    return "".join(out)


def codeowners_pattern_covers(pattern: str, path: str) -> bool:
    pattern = pattern.strip()
    path = path.lstrip("/")
    if pattern in {"*", "**", "/**"}:
        return True
    anchored = pattern.startswith("/")
    normalized = pattern.lstrip("/")
    if normalized.endswith("/"):
        # Unlike .gitignore, CODEOWNERS does not make a trailing slash a
        # recursive directory rule.  Require an explicit /** for descendants.
        return path.rstrip("/") == normalized.rstrip("/")
    regex = _codeowners_glob_regex(normalized)
    if "/" not in normalized and not anchored:
        return any(re.fullmatch(regex, part) is not None for part in path.split("/"))
    return re.fullmatch(regex, path) is not None


def codeowners_text_covers_paths(text: str, required_paths: list[str]) -> bool:
    rules = []
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if len(parts) < 2 or not any(owner.startswith("@") or "@" in owner for owner in parts[1:]):
            return False
        rules.append(parts[0])
    return bool(rules) and all(any(codeowners_pattern_covers(pattern, path) for pattern in rules) for path in required_paths)


def _workflow_activity_filter_covers(
    rows: list[tuple[int, str]], start: int, event_indent: int, value: str, event: str
) -> bool:
    required = {"opened", "synchronize", "reopened"}
    if event not in {"pull_request", "pull_request_target"}:
        return False
    if value:
        if not (value.startswith("[") and value.endswith("]")):
            return False
        values = {_yaml_scalar(item) for item in value[1:-1].split(",") if item.strip()}
        return required <= values
    values: set[str] = set()
    for child_indent, child_body in rows[start + 1:]:
        if child_indent <= event_indent:
            break
        if child_indent != event_indent + 2 or not child_body.startswith("- "):
            return False
        values.add(_yaml_scalar(child_body[2:]))
    return required <= values


def workflow_event_unfiltered(text: str, event: str) -> bool:
    """Return whether a workflow declares an event without path filtering."""
    rows = []
    for raw in text.splitlines():
        line = _strip_yaml_comment(raw)
        if line.strip():
            if re.match(r'''^\s*(?:-\s*)?&[^\s:]+\s+[^\s:]+\s*:''', line):
                return False
            rows.append((len(line) - len(line.lstrip(" ")), line.strip()))
    for index, (indent, body) in enumerate(rows):
        field = _yaml_mapping_field(body)
        if field is None or field[0] or indent != 0 or field[1] != "on":
            continue
        raw_value = field[2]
        if raw_value:
            scalar = _yaml_scalar(raw_value)
            if scalar == event:
                return True
            if raw_value.startswith("[") and raw_value.endswith("]"):
                values = [_yaml_scalar(value) for value in raw_value[1:-1].split(",")]
                return event in values
            return False
        for child_index in range(index + 1, len(rows)):
            child_indent, child_body = rows[child_index]
            if child_indent <= indent:
                break
            child = _yaml_mapping_field(child_body)
            if child is None or child[0] or child_indent != indent + 2 or child[1] != event:
                continue
            event_value = child[2]
            if event_value and event_value != "{}":
                return False
            for nested_index, (nested_indent, nested_body) in enumerate(rows[child_index + 1:], child_index + 1):
                if nested_indent <= child_indent:
                    break
                nested = _yaml_mapping_field(nested_body)
                if nested is not None and nested[1] in {"paths", "paths-ignore"}:
                    return False
                if nested is not None and nested[1] == "types" and not _workflow_activity_filter_covers(
                    rows, nested_index, nested_indent, nested[2], event
                ):
                    return False
            return True
        return False
    return False


def workflow_text_secure(text: str, *, require_top_permissions: bool = True) -> bool:
    has_top_permissions = False
    permissions_indent: int | None = None
    permissions_values: dict[str, str] = {}

    def close_permissions_block() -> bool:
        nonlocal permissions_indent, permissions_values
        if permissions_indent is None:
            return True
        safe = not _permissions_write_wide(permissions_values)
        permissions_indent = None
        permissions_values = {}
        return safe

    for raw in text.splitlines():
        line = _strip_yaml_comment(raw)
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        body = line.strip()
        if permissions_indent is not None and indent <= permissions_indent:
            if not close_permissions_block():
                return False
        field = _yaml_mapping_field(body)
        if field is None:
            compact = body.lstrip("- ").strip()
            if re.match(r'''^&[^\s:]+\s+[^\s:]+\s*:''', compact):
                return False
            if re.match(r'''^\*[^\s:]+\s*:''', compact):
                return False
            if re.match(r'''^"[^"\n]*\\[^"\n]*"\s*:''', compact):
                return False
            if compact.startswith("{") and compact.endswith("}") and re.search(
                r'''(?:^|,)\s*(?:uses|permissions|"uses"|"permissions"|'uses'|'permissions')\s*:''',
                compact[1:-1],
            ):
                return False
            continue
        is_sequence, key, raw_value = field
        if ("{" in raw_value or "[" in raw_value) and re.search(
            r'''(?:^|[,\[{])\s*(?:uses|permissions|"uses"|"permissions"|'uses'|'permissions')\s*:''',
            raw_value,
        ):
            return False
        if ("{" in raw_value or "[" in raw_value) and re.search(r'''"[^"\n]*\\[^"\n]*"\s*:''', raw_value):
            return False
        if permissions_indent is not None and not is_sequence and indent == permissions_indent + 2:
            if raw_value.startswith(("&", "*")):
                return False
            permissions_values[key] = _yaml_scalar(raw_value)
        if key == "permissions":
            if indent == 0 and not is_sequence:
                has_top_permissions = True
            scalar = _yaml_scalar(raw_value)
            if scalar == "write-all" or raw_value.startswith(("&", "*")):
                return False
            if raw_value == "":
                if permissions_indent is not None and not close_permissions_block():
                    return False
                permissions_indent = indent
                permissions_values = {}
            elif raw_value.lstrip().startswith("{"):
                mapping = _simple_flow_mapping(raw_value)
                if mapping is None or _permissions_write_wide(mapping):
                    return False
        if key == "uses":
            value = _yaml_scalar(raw_value)
            if value.startswith("./"):
                continue
            if value.startswith("docker://"):
                if not re.fullmatch(r"docker://[^@\s]+@sha256:[0-9a-fA-F]{64}", value):
                    return False
                continue
            if "@" not in value:
                return False
            ref = value.rsplit("@", 1)[1]
            if not re.fullmatch(r"[0-9a-fA-F]{40}", ref):
                return False
    if not close_permissions_block():
        return False
    return has_top_permissions or not require_top_permissions


def local_action_references(text: str) -> set[str] | None:
    references: set[str] = set()
    for raw in text.splitlines():
        line = _strip_yaml_comment(raw)
        if not line.strip():
            continue
        field = _yaml_mapping_field(line.strip())
        if field is None:
            continue
        _, key, raw_value = field
        if key != "uses":
            continue
        value = _yaml_scalar(raw_value)
        if not value.startswith("./"):
            continue
        normalized = value[2:].rstrip("/")
        if not normalized or normalized.startswith("/") or "/../" in f"/{normalized}/" or normalized.startswith("../"):
            return None
        references.add(normalized)
    return references


def merge_sources(*groups: dict[str, set[int | None]]) -> dict[str, set[int | None]]:
    merged: dict[str, set[int | None]] = {}
    for group in groups:
        for context, apps in group.items():
            merged.setdefault(context, set()).update(apps)
    return merged


def load_desired() -> dict:
    data = json.loads(DESIRED_PATH.read_text(encoding="utf-8"))
    if data.get("schema_version") != 2:
        raise SystemExit("governance desired-state schema_version must be 2")
    repos = data.get("permanent_repositories")
    if not isinstance(repos, list) or len(repos) != 4:
        raise SystemExit("exactly four permanent repositories are required")
    coordinates = [item.get("repository") for item in repos]
    expected = set(V2_REQUIRED_CONTEXTS)
    if set(coordinates) != expected or len(coordinates) != len(expected):
        raise SystemExit(f"unexpected permanent repository set: {coordinates}")
    for item in repos:
        if not isinstance(item.get("repository_id"), int):
            raise SystemExit(f"missing repository_id: {item}")
        if item.get("required_checks") != V2_REQUIRED_CONTEXTS[item["repository"]]:
            raise SystemExit(f"repository must require exactly its V2 aggregate gate: {item}")
        if "gate_mode" in item or "target_gate" in item:
            raise SystemExit(f"repository must not retain a desired-state gate transition: {item}")
        if item.get("merge_queue") is not True:
            raise SystemExit(f"repository must require merge_queue=true: {item}")
        expected_checks(item)
        expected_check_app_id(item)
        for field in ("main_protected", "squash_only", "delete_branch_on_merge"):
            if item.get(field) is not True:
                raise SystemExit(f"repository must require {field}=true: {item}")
        protection = item.get("protection")
        required_protection = {
            "pull_requests": True,
            "force_pushes": False,
            "deletions": False,
            "broad_bypass": False,
            "strict_required_status_checks": False,
            "required_approving_review_count": 0,
            "require_code_owner_review": False,
            "require_conversation_resolution": True,
            "required_linear_history": True,
        }
        if protection != required_protection:
            raise SystemExit(f"repository has incomplete or weakened protection contract: {item}")
        security = item.get("security")
        required_security = (
            "private_vulnerability_reporting", "secret_scanning",
            "push_protection", "dependabot_security_updates",
            "github_actions_dependency_updates", "workflow_supply_chain",
        )
        if not isinstance(security, dict) or set(security) != set(required_security):
            raise SystemExit(f"repository has incomplete security contract: {item}")
        if not all(security.get(field) is True for field in required_security):
            raise SystemExit(f"repository security controls must all be true: {item}")
        codeowner_paths = item.get("codeowners_required_paths")
        if not isinstance(codeowner_paths, list) or not codeowner_paths or not all(
            isinstance(path, str) and path and not path.startswith("/") for path in codeowner_paths
        ):
            raise SystemExit(f"repository has invalid codeowners_required_paths: {item}")
        if len(set(codeowner_paths)) != len(codeowner_paths):
            raise SystemExit(f"repository has duplicate codeowners_required_paths: {item}")
    policy = data.get("mutable_coordinate_policy")
    if not isinstance(policy, dict) or set(policy) != {"forbidden", "historical_reference_only"}:
        raise SystemExit("mutable_coordinate_policy must contain forbidden and historical_reference_only")
    for field in ("forbidden", "historical_reference_only"):
        values = policy.get(field)
        if not isinstance(values, list) or not values or not all(isinstance(value, str) and value for value in values):
            raise SystemExit(f"mutable_coordinate_policy.{field} must be a non-empty string array")
        if len(set(values)) != len(values):
            raise SystemExit(f"mutable_coordinate_policy.{field} contains duplicates")

    admins = data.get("administrative_repositories")
    if not isinstance(admins, list) or len(admins) != 1:
        raise SystemExit("exactly one administrative repository is required")
    expected_admin = ("Oteryn/Oteryn-Platform-Migration-Backup-20260818", 1338405017)
    if (admins[0].get("repository"), admins[0].get("repository_id")) != expected_admin:
        raise SystemExit(f"unexpected administrative repository identity: {admins[0]}")
    required_admin_fields = {
        "repository", "repository_id", "classification", "terminal_state",
        "archived", "retention_authority", "retention_release",
    }
    for item in admins:
        if not isinstance(item, dict) or set(item) != required_admin_fields:
            raise SystemExit(f"administrative repository has incomplete contract: {item}")
        if not isinstance(item["repository_id"], int) or item["repository_id"] <= 0:
            raise SystemExit(f"invalid administrative repository_id: {item}")
        for field in ("repository", "classification", "terminal_state", "retention_authority"):
            if not isinstance(item[field], str) or not item[field].strip():
                raise SystemExit(f"administrative repository lacks {field}: {item}")
        if not isinstance(item["archived"], bool):
            raise SystemExit(f"administrative repository archived must be boolean: {item}")
        if item["terminal_state"] == "ARCHIVED_READ_ONLY" and item["archived"] is not True:
            raise SystemExit(f"archived terminal state must require archived=true: {item}")
        release = item.get("retention_release")
        if not isinstance(release, dict) or set(release) != {"tag", "assets"}:
            raise SystemExit(f"administrative repository has invalid retention_release: {item}")
        if not isinstance(release.get("tag"), str) or not release["tag"].strip():
            raise SystemExit(f"administrative repository has invalid retention release tag: {item}")
        assets = release.get("assets")
        if not isinstance(assets, dict) or len(assets) != 6:
            raise SystemExit(f"administrative repository must pin six retention assets: {item}")
        digest_re = re.compile(r"^sha256:[0-9a-f]{64}$")
        for name, identity in assets.items():
            if not isinstance(name, str) or not name or not isinstance(identity, dict) or set(identity) != {"size", "digest"}:
                raise SystemExit(f"invalid retention asset identity: {name!r} / {identity!r}")
            if not isinstance(identity.get("size"), int) or identity["size"] <= 0 or not isinstance(identity.get("digest"), str) or not digest_re.fullmatch(identity["digest"]):
                raise SystemExit(f"invalid retention asset size/digest: {name!r} / {identity!r}")
    return data


def _ref_pattern_matches(pattern: str, *, branch: str, default_branch: str) -> bool:
    ref = f"refs/heads/{branch}"
    if pattern == "~ALL":
        return True
    if pattern == "~DEFAULT_BRANCH":
        return branch == default_branch
    return fnmatch.fnmatchcase(ref, pattern)


def ruleset_applies_to_branch(detail: dict, *, branch: str, default_branch: str) -> bool:
    if detail.get("enforcement") != "active" or detail.get("target") != "branch":
        return False
    ref_name = (detail.get("conditions") or {}).get("ref_name") or {}
    includes = ref_name.get("include") or []
    excludes = ref_name.get("exclude") or []
    if includes and not any(
        _ref_pattern_matches(pattern, branch=branch, default_branch=default_branch)
        for pattern in includes
    ):
        return False
    if any(
        _ref_pattern_matches(pattern, branch=branch, default_branch=default_branch)
        for pattern in excludes
    ):
        return False
    return True


class Audit:
    def __init__(self, token: str) -> None:
        self.token = token
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.unknowns: list[str] = []
        self.rollout_classifications: dict[str, str] = {}
        self._workflow_runs: dict[tuple[str, int], dict] = {}
        self._workflow_definitions: dict[tuple[str, int], dict | None] = {}
        self._workflow_trigger_validity: dict[tuple[str, int, str], bool] = {}

    def api(self, path: str, *, allow_404: bool = False):
        req = urllib.request.Request(
            API + path,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "oteryn-governance-readonly-audit",
            },
      …2644 tokens truncated…eturn "UNKNOWN"
        return classify_rollout_state(
            wanted,
            live_state,
            comments,
            now=now,
            success_receipt_verifier=self.verify_moving_base_receipt_direct,
        )

    def verify_moving_base_receipt_direct(
        self, wanted: dict, pre_transition_record: dict, terminal_record: dict
    ) -> str:
        """Classify direct moving-base evidence without hiding readable mismatch."""
        direct_match = self._moving_base_receipt_matches_direct(
            wanted, pre_transition_record, terminal_record
        )
        if direct_match is None:
            return "UNKNOWN"
        return "SUCCESS" if direct_match else "DRIFT"

    def _moving_base_receipt_matches_direct(
        self, wanted: dict, pre_transition_record: dict, terminal_record: dict
    ) -> bool | None:
        """Bind a terminal SUCCESS receipt to direct, read-only GitHub evidence.

        Lifecycle comments identify the intended bounded operation, but cannot prove
        it happened.  This verifier reads the real PR, commit, merge-group, check,
        and protected-main objects named by that receipt.  A missing or inconsistent
        object is deliberately not sufficient to classify a repository as target.
        """
        receipt = terminal_record.get("body", {}).get("moving_base_receipt")
        if not _valid_moving_base_receipt(receipt, wanted):
            return False
        if not isinstance(receipt, dict):
            return False
        repository = receipt["repository"]
        pr_a = receipt["pr_a"]
        pr_b = receipt["pr_b"]
        gate = receipt["aggregate_gate_run"]
        expected_context = wanted["required_checks"][0]
        expected_app_id = wanted.get("required_check_app_id")
        if not isinstance(expected_app_id, int) or isinstance(expected_app_id, bool) or expected_app_id <= 0:
            return False

        def matching_pull(payload: object, number: int, *, head_sha: str | None = None, merge_sha: str | None = None) -> bool:
            if not isinstance(payload, dict):
                return False
            base = payload.get("base")
            base_repo = base.get("repo") if isinstance(base, dict) else None
            if (
                payload.get("number") != number
                or payload.get("merged") is not True
                or not isinstance(payload.get("merged_at"), str)
                or not isinstance(base, dict)
                or base.get("ref") != "main"
                or not isinstance(base_repo, dict)
                or base_repo.get("full_name") != repository
            ):
                return False
            if head_sha is not None:
                head = payload.get("head")
                if not isinstance(head, dict) or head.get("sha") != head_sha:
                    return False
            return merge_sha is None or payload.get("merge_commit_sha") == merge_sha

        def has_successful_check(
            payload: object,
            *,
            sha: str,
            require_pr: int | None,
            require_run: int | None,
        ) -> dict | None:
            if not isinstance(payload, dict) or not isinstance(payload.get("check_runs"), list):
                return None
            for check_run in payload["check_runs"]:
                if not isinstance(check_run, dict):
                    continue
                app = check_run.get("app")
                if (
                    check_run.get("name") != expected_context
                    or not isinstance(app, dict)
                    or app.get("id") != expected_app_id
                    or check_run.get("head_sha") != sha
                    or check_run.get("conclusion") != "success"
                ):
                    continue
                if require_pr is not None:
                    pull_requests = check_run.get("pull_requests")
                    if not isinstance(pull_requests, list):
                        continue
                    associated = {
                        item.get("number") for item in pull_requests
                        if isinstance(item, dict)
                    }
                    if require_pr not in associated:
                        continue
                if require_run is not None:
                    match = WORKFLOW_RUN_RE.match(str(check_run.get("details_url") or ""))
                    if match is None or int(match.group(1)) != require_run:
                        continue
                return check_run
            return None

        try:
            pull_a = self.api(f"/repos/{repository}/pulls/{pr_a}", allow_404=True)
            pull_b = self.api(f"/repos/{repository}/pulls/{pr_b}", allow_404=True)
            a_checks = self.api(
                f"/repos/{repository}/commits/{receipt['a_head']}/check-runs?per_page=100",
                allow_404=True,
            )
            after_b = self.api(f"/repos/{repository}/commits/{receipt['main_after_b']}", allow_404=True)
            after_a = self.api(f"/repos/{repository}/commits/{receipt['main_after_a']}", allow_404=True)
            b_advance = self.api(
                f"/repos/{repository}/compare/{receipt['main_before_b']}...{receipt['main_after_b']}",
                allow_404=True,
            )
            aggregate_run = self.api(
                f"/repos/{repository}/actions/runs/{gate['run_id']}", allow_404=True
            )
            merge_group_commit = self.api(
                f"/repos/{repository}/commits/{receipt['merge_group_sha']}", allow_404=True
            )
            merge_group_checks = self.api(
                f"/repos/{repository}/commits/{receipt['merge_group_sha']}/check-runs?per_page=100",
                allow_404=True,
            )
            queue_timeline = self._pull_request_queue_timeline(repository, pr_a)
            protected_main = self.api(f"/repos/{repository}/branches/main", allow_404=True)
        except (RuntimeError, ValueError):
            return None

        if not matching_pull(
            pull_a, pr_a, head_sha=receipt["a_head"], merge_sha=receipt["main_after_a"]
        ):
            return False
        if not matching_pull(pull_b, pr_b, merge_sha=receipt["main_after_b"]):
            return False
        a_check = has_successful_check(
            a_checks, sha=receipt["a_head"], require_pr=pr_a, require_run=None
        )
        if a_check is None:
            return False
        try:
            protected_a_sources = merge_sources(
                self._protected_flow_sources(
                    repository,
                    {"check_runs": [a_check]},
                    event="pull_request",
                    allowed_head_shas={receipt["a_head"]},
                    workflow_ref=receipt["a_head"],
                    pr_number=pr_a,
                ),
                self._protected_flow_sources(
                    repository,
                    {"check_runs": [a_check]},
                    event="pull_request_target",
                    allowed_head_shas={receipt["a_head"]},
                    workflow_ref=receipt["main_before_b"],
                    pr_number=pr_a,
                ),
            )
        except (RuntimeError, ValueError):
            return None
        if protected_a_sources.get(expected_context) != {expected_app_id}:
            return False
        after_b_parents = after_b.get("parents") if isinstance(after_b, dict) else None
        if (
            not isinstance(after_b, dict)
            or after_b.get("sha") != receipt["main_after_b"]
            or not isinstance(after_b_parents, list)
            or receipt["main_before_b"] not in {
                parent.get("sha") for parent in after_b_parents if isinstance(parent, dict)
            }
            or not isinstance(b_advance, dict)
            or b_advance.get("status") != "ahead"
        ):
            return False
        after_a_parents = after_a.get("parents") if isinstance(after_a, dict) else None
        after_a_committer = after_a.get("committer") if isinstance(after_a, dict) else None
        if (
            not isinstance(after_a, dict)
            or after_a.get("sha") != receipt["main_after_a"]
            or not isinstance(after_a_parents, list)
            or receipt["main_after_b"] not in {
                parent.get("sha") for parent in after_a_parents if isinstance(parent, dict)
            }
            or not isinstance(after_a_committer, dict)
            or after_a_committer.get("login") != "github-merge-queue[bot]"
        ):
            return False
        if (
            not isinstance(aggregate_run, dict)
            or aggregate_run.get("id") != gate["run_id"]
            or aggregate_run.get("event") != "merge_group"
            or aggregate_run.get("head_sha") != receipt["merge_group_sha"]
            or aggregate_run.get("status") != "completed"
            or aggregate_run.get("conclusion") != "success"
        ):
            return False
        if (
            not isinstance(merge_group_commit, dict)
            or merge_group_commit.get("sha") != receipt["merge_group_sha"]
            or not isinstance(merge_group_commit.get("parents"), list)
            or len(merge_group_commit["parents"]) != 2
            or not all(isinstance(parent, dict) for parent in merge_group_commit["parents"])
            or merge_group_commit["parents"][0].get("sha") != receipt["base_sha"]
            or merge_group_commit["parents"][1].get("sha") != receipt["a_head"]
        ):
            return False
        merge_group_check = has_successful_check(
            merge_group_checks,
            sha=receipt["merge_group_sha"],
            require_pr=None,
            require_run=gate["run_id"],
        )
        if merge_group_check is None:
            return False
        try:
            protected_merge_group_sources = self._protected_flow_sources(
                repository,
                {"check_runs": [merge_group_check]},
                event="merge_group",
                allowed_head_shas={receipt["merge_group_sha"]},
                workflow_ref=receipt["base_sha"],
            )
        except (RuntimeError, ValueError):
            return None
        if protected_merge_group_sources.get(expected_context) != {expected_app_id}:
            return False
        a_green_at = _parse_timestamp(a_check.get("completed_at"))
        b_merged_at = _parse_timestamp(pull_b.get("merged_at")) if isinstance(pull_b, dict) else None
        a_merged_at = _parse_timestamp(pull_a.get("merged_at")) if isinstance(pull_a, dict) else None
        merge_group_started_at = _parse_timestamp(
            aggregate_run.get("run_started_at") or aggregate_run.get("created_at")
        ) if isinstance(aggregate_run, dict) else None
        merge_group_completed_at = _parse_timestamp(merge_group_check.get("completed_at"))
        transition_started_at = pre_transition_record.get("created_at")
        transition_closed_at = terminal_record.get("created_at")
        if (
            a_green_at is None
            or b_merged_at is None
            or a_merged_at is None
            or merge_group_started_at is None
            or merge_group_completed_at is None
            or not isinstance(transition_started_at, datetime)
            or not isinstance(transition_closed_at, datetime)
            or a_green_at < transition_started_at
            or a_green_at > b_merged_at
            or b_merged_at > merge_group_started_at
            or merge_group_started_at > merge_group_completed_at
            or merge_group_completed_at > a_merged_at
            or a_merged_at > transition_closed_at
        ):
            return False
        merged_event_indexes: list[int] = []
        added_event_indexes: list[int] = []
        for index, event in enumerate(queue_timeline):
            event_type = event.get("__typename")
            event_at = _parse_timestamp(event.get("createdAt"))
            if event_type == "MergedEvent":
                commit = event.get("commit")
                if (
                    event_at == a_merged_at
                    and isinstance(commit, dict)
                    and commit.get("oid") == receipt["main_after_a"]
                ):
                    merged_event_indexes.append(index)
            elif (
                event_type == "AddedToMergeQueueEvent"
                and event_at is not None
                and b_merged_at <= event_at <= merge_group_started_at
            ):
                added_event_indexes.append(index)
        if len(merged_event_indexes) != 1:
            return False
        merged_event_index = merged_event_indexes[0]
        eligible_additions = [index for index in added_event_indexes if index < merged_event_index]
        if not eligible_additions:
            return False
        queue_entry_index = max(eligible_additions)
        if any(
            event.get("__typename") == "RemovedFromMergeQueueEvent"
            for event in queue_timeline[queue_entry_index + 1:merged_event_index]
        ):
            return False
        protected_main_commit = (
            protected_main.get("commit") if isinstance(protected_main, dict) else None
        )
        if (
            not isinstance(protected_main, dict)
            or protected_main.get("protected") is not True
            or not isinstance(protected_main_commit, dict)
            or not isinstance(protected_main_commit.get("sha"), str)
        ):
            return False
        main_head = protected_main_commit["sha"]
        if main_head == receipt["main_after_a"]:
            return True
        try:
            integrated = self.api(
                f"/repos/{repository}/compare/{receipt['main_after_a']}...{main_head}",
                allow_404=True,
            )
        except (RuntimeError, ValueError):
            return None
        integration_base = integrated.get("merge_base_commit") if isinstance(integrated, dict) else None
        return (
            isinstance(integrated, dict)
            and integrated.get("status") == "ahead"
            and isinstance(integration_base, dict)
            and integration_base.get("sha") == receipt["main_after_a"]
        )

    def check(self, condition: bool, message: str) -> None:
        if not condition:
            self.errors.append(message)

    @staticmethod
    def _add_source(sources: dict[str, set[int | None]], context: str | None, app_id: int | None) -> None:
        if context:
            sources.setdefault(context, set()).add(app_id if isinstance(app_id, int) else None)

    def _workflow_run(self, repo: str, check_run: dict) -> dict | None:
        match = WORKFLOW_RUN_RE.match(str(check_run.get("details_url") or ""))
        if not match:
            return None
        run_id = int(match.group(1))
        key = (repo, run_id)
        if key not in self._workflow_runs:
            payload = self.api(f"/repos/{repo}/actions/runs/{run_id}")
            if not isinstance(payload, dict):
                return None
            self._workflow_runs[key] = payload
        return self._workflow_runs[key]

    def _workflow_definition(self, repo: str, workflow_run: dict) -> dict | None:
        workflow_id = workflow_run.get("workflow_id")
        if not isinstance(workflow_id, int) or workflow_id <= 0:
            return None
        key = (repo, workflow_id)
        if key not in self._workflow_definitions:
            payload = self.api(f"/repos/{repo}/actions/workflows/{workflow_id}", allow_404=True)
            self._workflow_definitions[key] = payload if isinstance(payload, dict) else None
        return self._workflow_definitions[key]

    def _workflow_event_unfiltered(self, repo: str, definition: dict, event: str, *, ref: str) -> bool:
        workflow_id = definition.get("id")
        path = definition.get("path")
        if not isinstance(workflow_id, int) or workflow_id <= 0 or not isinstance(path, str) or not path:
            return False
        key = (repo, workflow_id, event, ref)
        if key not in self._workflow_trigger_validity:
            quoted_path = "/".join(urllib.parse.quote(part, safe="") for part in path.split("/"))
            quoted_ref = urllib.parse.quote(ref, safe="")
            text = self._decoded_contents(self.api(f"/repos/{repo}/contents/{quoted_path}?ref={quoted_ref}", allow_404=True))
            self._workflow_trigger_validity[key] = text is not None and workflow_event_unfiltered(text, event)
        return self._workflow_trigger_validity[key]

    def _protected_flow_sources(
        self,
        repo: str,
        payload: dict,
        *,
        event: str,
        allowed_head_shas: set[str],
        workflow_ref: str,
        pr_number: int | None = None,
    ) -> dict[str, set[int | None]]:
        sources: dict[str, set[int | None]] = {}
        for check_run in payload.get("check_runs", []):
            workflow = self._workflow_run(repo, check_run)
            if not workflow:
                continue
            definition = self._workflow_definition(repo, workflow)
            if not definition or definition.get("state") != "active":
                continue
            if not self._workflow_event_unfiltered(repo, definition, event, ref=workflow_ref):
                continue
            if workflow.get("event") != event or workflow.get("head_sha") not in allowed_head_shas:
                continue
            if pr_number is not None:
                associated = {
                    item.get("number")
                    for item in check_run.get("pull_requests", [])
                    if isinstance(item, dict)
                }
                if pr_number not in associated:
                    continue
            self._add_source(sources, check_run.get("name"), (check_run.get("app") or {}).get("id"))
        return sources

    def required_context_sources(
        self,
        repo: str,
        *,
        branch: str = "main",
        default_branch: str = "main",
    ) -> dict[str, set[int | None]]:
        sources: dict[str, set[int | None]] = {}
        rulesets = self.api_list(f"/repos/{repo}/rulesets")
        for summary in rulesets:
            if summary.get("enforcement") != "active":
                continue
            detail = self.api(f"/repos/{repo}/rulesets/{summary['id']}")
            if not ruleset_applies_to_branch(detail, branch=branch, default_branch=default_branch):
                continue
            for rule in detail.get("rules", []):
                if rule.get("type") != "required_status_checks":
                    continue
                for check in rule.get("parameters", {}).get("required_status_checks", []):
                    self._add_source(sources, check.get("context"), check.get("integration_id"))
        protection = self.api(
            f"/repos/{repo}/branches/{urllib.parse.quote(branch, safe='')}/protection/required_status_checks",
            allow_404=True,
        )
        if protection:
            bound_contexts: set[str] = set()
            for check in protection.get("checks", []):
                context = check.get("context")
                if context:
                    bound_contexts.add(context)
                self._add_source(sources, context, check.get("app_id"))
            for context in protection.get("contexts", []):
                if context not in bound_contexts:
                    self._add_source(sources, context, None)
        # An unbound occurrence adds no App constraint.  When another
        # applicable surface binds the same context to one or more concrete
        # Apps, retain only those concrete constraints; distinct concrete App
        # IDs remain visible as a conflict.
        return {
            context: ({app_id for app_id in app_ids if app_id is not None} or {None})
            for context, app_ids in sources.items()
        }

    def _applicable_rulesets(
        self, repo: str, *, branch: str, default_branch: str
    ) -> list[dict]:
        applicable: list[dict] = []
        for summary in self.api_list(f"/repos/{repo}/rulesets"):
            if summary.get("enforcement") != "active":
                continue
            detail = self.api(f"/repos/{repo}/rulesets/{summary['id']}")
            if not isinstance(detail, dict):
                raise RuntimeError(f"GET /repos/{repo}/rulesets/{summary['id']} -> expected object payload")
            if ruleset_applies_to_branch(detail, branch=branch, default_branch=default_branch):
                applicable.append(detail)
        return applicable

    @staticmethod
    def _ruleset_rollout_controls(applicable: list[dict]) -> dict[str, bool | int | None]:
        rules = [
            rule for detail in applicable for rule in detail.get("rules", []) if isinstance(rule, dict)
        ]
        rule_types = {rule.get("type") for rule in rules}
        pull_rules = [rule for rule in rules if rule.get("type") == "pull_request"]
        status_rules = [rule for rule in rules if rule.get("type") == "required_status_checks"]
        bypasses = [detail.get("bypass_actors") for detail in applicable]

        counts: list[int] = []
        codeowner_flags: list[bool] = []
        conversation_resolution_flags: list[bool] = []
        for rule in pull_rules:
            parameters = rule.get("parameters")
            count = parameters.get("required_approving_review_count") if isinstance(parameters, dict) else None
            codeowner = parameters.get("require_code_owner_review") if isinstance(parameters, dict) else None
            last_push = parameters.get("require_last_push_approval") if isinstance(parameters, dict) else None
            required_reviewers = parameters.get("required_reviewers", []) if isinstance(parameters, dict) else None
            conversation_resolution = (
                parameters.get("required_review_thread_resolution")
                if isinstance(parameters, dict) else None
            )
            reviewer_minimums = [
                reviewer.get("minimum_approvals")
                for reviewer in required_reviewers
                if isinstance(reviewer, dict)
            ] if isinstance(required_reviewers, list) else []
            reviewers_valid = (
                isinstance(required_reviewers, list)
                and len(reviewer_minimums) == len(required_reviewers)
                and all(
                    isinstance(minimum, int) and not isinstance(minimum, bool) and minimum >= 0
                    for minimum in reviewer_minimums
                )
            )
            if (
                not isinstance(count, int) or isinstance(count, bool) or count < 0
                or not isinstance(last_push, bool)
                or not reviewers_valid
            ):
                counts = []
                codeowner_flags = []
                break
            if not isinstance(codeowner, bool):
                counts = []
                codeowner_flags = []
                break
            counts.append(max([count, int(last_push), *reviewer_minimums]))
            codeowner_flags.append(codeowner)
            if isinstance(conversation_resolution, bool):
                conversation_resolution_flags.append(conversation_resolution)
        review_count: int | None
        codeowner_review: bool | None
        if not pull_rules:
            review_count, codeowner_review = 0, False
        elif len(counts) != len(pull_rules) or len(codeowner_flags) != len(pull_rules):
            review_count, codeowner_review = None, None
        else:
            review_count, codeowner_review = max(counts), any(codeowner_flags)
        conversation_resolution: bool | None
        if not pull_rules:
            conversation_resolution = False
        elif len(conversation_resolution_flags) != len(pull_rules):
            conversation_resolution = None
        else:
            conversation_resolution = any(conversation_resolution_flags)

        strict_values: list[bool] = []
        for rule in status_rules:
            parameters = rule.get("parameters")
            strict = parameters.get("strict_required_status_checks_policy") if isinstance(parameters, dict) else None
            checks = parameters.get("required_status_checks") if isinstance(parameters, dict) else None
            if not isinstance(checks, list):
                strict_values = []
                break
            if not checks:
                continue
            if not isinstance(strict, bool):
                strict_values = []
                break
            strict_values.append(strict)
        strict: bool | None
        if not status_rules:
            strict = False
        elif any(
            not isinstance(rule.get("parameters"), dict)
            or not isinstance(rule["parameters"].get("required_status_checks"), list)
            or (
                bool(rule["parameters"]["required_status_checks"])
                and not isinstance(rule["parameters"].get("strict_required_status_checks_policy"), bool)
            )
            for rule in status_rules
        ):
            strict = None
        else:
            strict = any(strict_values) if strict_values else False
        return {
            "pull_requests": "pull_request" in rule_types,
            "force_pushes": "non_fast_forward" not in rule_types,
            "deletions": "deletion" not in rule_types,
            "broad_bypass": (
                any(bool(value) for value in bypasses)
                if all(isinstance(value, list) for value in bypasses) else None
            ),
            "strict_required_status_checks": strict,
            "required_approving_review_count": review_count,
            "require_code_owner_review": codeowner_review,
            "require_conversation_resolution": conversation_resolution,
            "required_linear_history": "required_linear_history" in rule_types,
            "merge_queue": "merge_queue" in rule_types,
        }

    @staticmethod
    def _classic_rollout_controls(protection: object) -> dict[str, bool | int | None] | None:
        """Return classic protection controls, or ``None`` when no classic surface exists."""
        if protection is None:
            return None
        if not isinstance(protection, dict):
            return {key: None for key in (
                "pull_requests", "force_pushes", "deletions", "broad_bypass",
                "strict_required_status_checks", "required_approving_review_count",
                "require_code_owner_review", "require_conversation_resolution",
                "required_linear_history", "merge_queue",
            )}
        reviews = protection.get("required_pull_request_reviews")
        if reviews is None:
            pull_requests, review_count, codeowner_review, has_pr_bypass = False, 0, False, False
        elif isinstance(reviews, dict):
            count = reviews.get("required_approving_review_count")
            codeowner = reviews.get("require_code_owner_reviews")
            last_push = reviews.get("require_last_push_approval")
            bypass_allowances = reviews.get("bypass_pull_request_allowances") or {}
            pull_requests = True
            review_count = (
                max(count, int(last_push))
                if isinstance(count, int) and not isinstance(count, bool) and count >= 0
                and isinstance(last_push, bool)
                else None
            )
            codeowner_review = codeowner if isinstance(codeowner, bool) else None
            has_pr_bypass = (
                any(bool(bypass_allowances.get(kind)) for kind in ("users", "teams", "apps"))
                if isinstance(bypass_allowances, dict) else None
            )
        else:
            pull_requests = review_count = codeowner_review = has_pr_bypass = None

        allow_force_pushes = (protection.get("allow_force_pushes") or {}).get("enabled")
        allow_deletions = (protection.get("allow_deletions") or {}).get("enabled")
        enforce_admins = (protection.get("enforce_admins") or {}).get("enabled")
        status_checks = protection.get("required_status_checks")
        if status_checks is None:
            strict = False
        elif isinstance(status_checks, dict):
            strict = status_checks.get("strict") if isinstance(status_checks.get("strict"), bool) else None
        else:
            strict = None
        broad_bypass = (
            (not enforce_admins) or has_pr_bypass
            if isinstance(enforce_admins, bool) and isinstance(has_pr_bypass, bool) else None
        )
        conversation_resolution = protection.get("required_conversation_resolution")
        if conversation_resolution is None:
            require_conversation_resolution = False
        elif isinstance(conversation_resolution, dict):
            enabled = conversation_resolution.get("enabled")
            require_conversation_resolution = enabled if isinstance(enabled, bool) else None
        else:
            require_conversation_resolution = None
        linear_history = protection.get("required_linear_history")
        if linear_history is None:
            required_linear_history = False
        elif isinstance(linear_history, dict):
            enabled = linear_history.get("enabled")
            required_linear_history = enabled if isinstance(enabled, bool) else None
        else:
            required_linear_history = None
        return {
            "pull_requests": pull_requests,
            "force_pushes": allow_force_pushes if isinstance(allow_force_pushes, bool) else None,
            "deletions": allow_deletions if isinstance(allow_deletions, bool) else None,
            "broad_bypass": broad_bypass,
            "strict_required_status_checks": strict,
            "required_approving_review_count": review_count,
            "require_code_owner_review": codeowner_review,
            "require_conversation_resolution": require_conversation_resolution,
            "required_linear_history": required_linear_history,
            # The classic protection payload does not expose this setting.
            # Read it from the effective branch-rule surface instead.
            "merge_queue": None,
        }

    def _effective_branch_merge_queue(self, repo: str, *, branch: str) -> bool | None:
        """Read the effective Merge Queue rule for a branch, including classic protection."""
        path = f"/repos/{repo}/rules/branches/{urllib.parse.quote(branch, safe='')}"
        page = 1
        found = False
        while True:
            payload = self.api(f"{path}?per_page=100&page={page}", allow_404=True)
            if payload is None:
                return None
            if not isinstance(payload, list) or any(not isinstance(rule, dict) for rule in payload):
                return None
            found = found or any(rule.get("type") == "merge_queue" for rule in payload)
            if len(payload) < 100:
                return found
            page += 1

    @staticmethod
    def _compose_rollout_protection_controls(
        ruleset: dict[str, bool | int | None] | None,
        classic: dict[str, bool | int | None] | None,
    ) -> dict[str, bool | int | None]:
        """Compose overlapping enforcement surfaces; neither can hide the other."""
        unknown = {
            "pull_requests": None,
            "force_pushes": None,
            "deletions": None,
            "broad_bypass": None,
            "strict_required_status_checks": None,
            "required_approving_review_count": None,
            "require_code_owner_review": None,
            "require_conversation_resolution": None,
            "required_linear_history": None,
            "merge_queue": None,
        }
        if ruleset is None and classic is None:
            return unknown
        if ruleset is None:
            return classic if classic is not None else unknown
        if classic is None:
            return ruleset

        def both(value_a: object, value_b: object) -> bool | None:
            return value_a and value_b if isinstance(value_a, bool) and isinstance(value_b, bool) else None

        def either(value_a: object, value_b: object) -> bool | None:
            return value_a or value_b if isinstance(value_a, bool) and isinstance(value_b, bool) else None

        rule_count = ruleset.get("required_approving_review_count")
        classic_count = classic.get("required_approving_review_count")
        return {
            "pull_requests": either(ruleset.get("pull_requests"), classic.get("pull_requests")),
            "force_pushes": both(ruleset.get("force_pushes"), classic.get("force_pushes")),
            "deletions": both(ruleset.get("deletions"), classic.get("deletions")),
            "broad_bypass": either(ruleset.get("broad_bypass"), classic.get("broad_bypass")),
            "strict_required_status_checks": either(
                ruleset.get("strict_required_status_checks"), classic.get("strict_required_status_checks")
            ),
            "required_approving_review_count": (
                max(rule_count, classic_count)
                if isinstance(rule_count, int) and not isinstance(rule_count, bool)
                and isinstance(classic_count, int) and not isinstance(classic_count, bool)
                else None
            ),
            "require_code_owner_review": either(
                ruleset.get("require_code_owner_review"), classic.get("require_code_owner_review")
            ),
            "require_conversation_resolution": either(
                ruleset.get("require_conversation_resolution"),
                classic.get("require_conversation_resolution"),
            ),
            "required_linear_history": either(
                ruleset.get("required_linear_history"),
                classic.get("required_linear_history"),
            ),
            "merge_queue": either(ruleset.get("merge_queue"), classic.get("merge_queue")),
        }

    def _read_composed_rollout_protection_controls(
        self, repo: str, *, branch: str, default_branch: str
    ) -> dict[str, bool | int | None]:
        applicable = self._applicable_rulesets(repo, branch=branch, default_branch=default_branch)
        protection = self.api(
            f"/repos/{repo}/branches/{urllib.parse.quote(branch, safe='')}/protection",
            allow_404=True,
        )
        ruleset_controls = self._ruleset_rollout_controls(applicable) if applicable else None
        controls = self._compose_rollout_protection_controls(
            ruleset_controls,
            self._classic_rollout_controls(protection),
        )
        effective_merge_queue = self._effective_branch_merge_queue(repo, branch=branch)
        ruleset_merge_queue = (
            ruleset_controls.get("merge_queue") if ruleset_controls is not None else False
        )
        controls["merge_queue"] = (
            True
            if ruleset_merge_queue is True or effective_merge_queue is True
            else False
            if ruleset_merge_queue is False and effective_merge_queue is False
            else None
        )
        return controls

    def main_protection_controls(
        self, repo: str, *, branch: str = "main", default_branch: str = "main"
    ) -> dict[str, bool | None]:
        try:
            controls = self._read_composed_rollout_protection_controls(
                repo, branch=branch, default_branch=default_branch
            )
        except (RuntimeError, ValueError):
            controls = self._compose_rollout_protection_controls(None, None)
        return {
            field: controls.get(field)
            for field in (
                "pull_requests", "force_pushes", "deletions", "broad_bypass",
                "strict_required_status_checks",
            )
        }

    def rollout_protection_controls(
        self, repo: str, *, branch: str = "main", default_branch: str = "main"
    ) -> dict[str, bool | int | None]:
        """Compose every applicable ruleset and classic branch-protection surface."""
        try:
            return self._read_composed_rollout_protection_controls(
                repo, branch=branch, default_branch=default_branch
            )
        except (RuntimeError, ValueError):
            return self._compose_rollout_protection_controls(None, None)

    def rollout_state_readback(self, repo: str) -> dict | None:
        """Build the compact, direct settings readback stored in lifecycle records."""
        live = self.api(f"/repos/{repo}")
        if not isinstance(live, dict):
            return None
        default_branch = live.get("default_branch") if isinstance(live.get("default_branch"), str) else None
        if default_branch != "main":
            return None
        branch = self.api(f"/repos/{repo}/branches/main")
        if not isinstance(branch, dict):
            return None
        try:
            required_sources = self.required_context_sources(repo, branch="main", default_branch=default_branch)
            controls = self.rollout_protection_controls(repo, branch="main", default_branch=default_branch)
        except (RuntimeError, ValueError):
            return None
        if not isinstance(controls, dict):
            return None
        if not isinstance(controls.get("required_approving_review_count"), int) or isinstance(controls.get("required_approving_review_count"), bool):
            return None
        if not all(isinstance(value, bool) for value in (
            branch.get("protected"), live.get("allow_squash_merge"), live.get("allow_merge_commit"),
            live.get("allow_rebase_merge"), live.get("delete_branch_on_merge"), controls.get("merge_queue"),
            controls.get("pull_requests"), controls.get("force_pushes"), controls.get("deletions"),
            controls.get("broad_bypass"), controls.get("strict_required_status_checks"),
            controls.get("require_code_owner_review"), controls.get("require_conversation_resolution"),
        )):
            return None
        state = {
            "repository": repo,
            "required_checks": sorted(required_sources),
            "required_check_sources": {
                context: sorted(app_ids, key=lambda app_id: (-1 if app_id is None else app_id))
                for context, app_ids in sorted(required_sources.items())
            },
            "main_protected": branch["protected"],
            "squash_only": live["allow_squash_merge"] and not live["allow_merge_commit"] and not live["allow_rebase_merge"],
            "delete_branch_on_merge": live["delete_branch_on_merge"],
            "merge_queue": controls["merge_queue"],
            "protection": {
                "pull_requests": controls["pull_requests"],
                "force_pushes": controls["force_pushes"],
                "deletions": controls["deletions"],
                "broad_bypass": controls["broad_bypass"],
                "strict_required_status_checks": controls["strict_required_status_checks"],
                "required_approving_review_count": controls["required_approving_review_count"],
                "require_code_owner_review": controls["require_code_owner_review"],
                "require_conversation_resolution": controls["require_conversation_resolution"],
                "required_linear_history": controls["required_linear_history"],
            },
        }
        return _normalized_rollout_state(state)

    def private_vulnerability_reporting_enabled(self, repo: str) -> bool:
        state = self.api(f"/repos/{repo}/private-vulnerability-reporting", allow_404=True)
        return isinstance(state, dict) and (
            state.get("_http_status") == 204 or state.get("enabled") is True
        )

    def representative_check_sources(
        self,
        repo: str,
        expected: set[str],
        expected_app_id: int,
    ) -> dict[str, set[int | None]]:
        """Prove required gate emission from one current internal PR containing main."""
        branch = self.api(f"/repos/{repo}/branches/main") or {}
        main_sha = ((branch.get("commit") or {}).get("sha") or "").strip()
        if not main_sha:
            return {}
        def score(candidate: dict[str, set[int | None]]) -> int:
            return sum(candidate.get(context) == {expected_app_id} for context in expected)

        best: dict[str, set[int | None]] = {}
        pulls = self.api(f"/repos/{repo}/pulls?state=open&base=main&sort=updated&direction=desc&per_page=20") or []
        for pr in pulls:
            head = pr.get("head", {})
            base = pr.get("base", {})
            head_repo = (head.get("repo") or {}).get("full_name")
            pr_number = pr.get("number")
            if head_repo != repo or base.get("ref") != "main" or not isinstance(pr_number, int):
                continue
            sha = head.get("sha")
            if not sha:
                continue
            comparison = self.api(f"/repos/{repo}/compare/{main_sha}...{sha}") or {}
            merge_base = (comparison.get("merge_base_commit") or {}).get("sha")
            if comparison.get("status") not in {"ahead", "identical"} or merge_base != main_sha:
                continue
            runs = self.api(f"/repos/{repo}/commits/{sha}/check-runs?per_page=100") or {}
            pr_sources = self._protected_flow_sources(
                repo,
                runs,
                event="pull_request",
                allowed_head_shas={sha},
                workflow_ref=sha,
                pr_number=pr_number,
            )
            target_sources = self._protected_flow_sources(
                repo,
                runs,
                event="pull_request_target",
                allowed_head_shas={main_sha},
                workflow_ref=main_sha,
                pr_number=pr_number,
            )
            sources = merge_sources(pr_sources, target_sources)
            if expected_sources_satisfied(sources, expected, expected_app_id):
                return sources
            if score(sources) > score(best):
                best = sources
        return best

    def dependabot_security_updates_enabled(self, repo: str) -> bool:
        fixes = self.api(f"/repos/{repo}/automated-security-fixes", allow_404=True)
        return isinstance(fixes, dict) and (
            fixes.get("_http_status") == 204 or fixes.get("enabled") is True
        )

    def file_exists(self, repo: str, path: str) -> bool:
        quoted = "/".join(urllib.parse.quote(part, safe="") for part in path.split("/"))
        return self.api(f"/repos/{repo}/contents/{quoted}", allow_404=True) is not None

    @staticmethod
    def _decoded_contents(payload: object) -> str | None:
        if not isinstance(payload, dict) or not isinstance(payload.get("content"), str):
            return None
        try:
            return base64.b64decode(payload["content"]).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return None

    def github_actions_dependency_updates_configured(self, repo: str) -> bool:
        payload = self.api(f"/repos/{repo}/contents/.github/dependabot.yml", allow_404=True)
        text = self._decoded_contents(payload)
        return text is not None and dependabot_github_actions_entry_valid(text)

    def codeowners_baseline_valid(self, repo: str, required_paths: list[str]) -> bool:
        payload = self.api(f"/repos/{repo}/contents/.github/CODEOWNERS", allow_404=True)
        text = self._decoded_contents(payload)
        errors = self.api(f"/repos/{repo}/codeowners/errors", allow_404=True)
        return (
            text is not None
            and isinstance(errors, dict)
            and errors.get("errors") == []
            and codeowners_text_covers_paths(text, required_paths)
        )

    def workflow_supply_chain_valid(self, repo: str) -> bool:
        listing = self.api(f"/repos/{repo}/contents/.github/workflows", allow_404=True)
        if not isinstance(listing, list):
            return False
        workflows = [
            item for item in listing
            if isinstance(item, dict) and item.get("type") == "file"
            and str(item.get("name") or "").lower().endswith((".yml", ".yaml"))
        ]
        if not workflows:
            return False
        inspected: set[str] = set()

        def validate(path: str, *, require_top_permissions: bool) -> bool:
            if path in inspected:
                return True
            inspected.add(path)
            quoted = "/".join(urllib.parse.quote(part, safe="") for part in path.split("/"))
            text = self._decoded_contents(self.api(f"/repos/{repo}/contents/{quoted}", allow_404=True))
            if text is None or not workflow_text_secure(text, require_top_permissions=require_top_permissions):
                return False
            references = local_action_references(text)
            if references is None:
                return False
            for reference in references:
                if reference.startswith(".github/workflows/") and reference.endswith((".yml", ".yaml")):
                    if not validate(reference, require_top_permissions=True):
                        return False
                    continue
                primary = f"{reference}/action.yml"
                primary_quoted = "/".join(urllib.parse.quote(part, safe="") for part in primary.split("/"))
                if self.api(f"/repos/{repo}/contents/{primary_quoted}", allow_404=True) is not None:
                    if not validate(primary, require_top_permissions=False):
                        return False
                    continue
                if not validate(f"{reference}/action.yaml", require_top_permissions=False):
                    return False
            return True

        for item in workflows:
            path = item.get("path")
            if not isinstance(path, str) or not path or not validate(path, require_top_permissions=True):
                return False
        return True

    def retained_release_valid(self, repo: str, wanted: dict) -> bool:
        tag = wanted.get("tag")
        assets = wanted.get("assets")
        if not isinstance(tag, str) or not isinstance(assets, dict):
            return False
        release = self.api(f"/repos/{repo}/releases/tags/{urllib.parse.quote(tag, safe='')}", allow_404=True)
        if not isinstance(release, dict) or release.get("tag_name") != tag:
            return False
        observed = {
            asset.get("name"): {"size": asset.get("size"), "digest": asset.get("digest")}
            for asset in release.get("assets", [])
            if isinstance(asset, dict) and isinstance(asset.get("name"), str)
        }
        return all(observed.get(name) == identity for name, identity in assets.items())

    def audit_repo(self, wanted: dict) -> None:
        repo = wanted["repository"]
        live = self.api(f"/repos/{repo}")
        self.check(live.get("full_name") == repo, f"{repo}: canonical coordinate drift")
        self.check(live.get("id") == wanted["repository_id"], f"{repo}: repository ID drift")
        self.check(live.get("default_branch") == "main", f"{repo}: default branch is not main")
        self.check(not live.get("archived"), f"{repo}: permanent repository unexpectedly archived")
        self.check(bool(live.get("allow_squash_merge")), f"{repo}: squash merge disabled")
        if wanted.get("squash_only"):
            self.check(not live.get("allow_merge_commit"), f"{repo}: merge commits unexpectedly enabled")
            self.check(not live.get("allow_rebase_merge"), f"{repo}: rebase merge unexpectedly enabled")
        if wanted.get("delete_branch_on_merge"):
            self.check(bool(live.get("delete_branch_on_merge")), f"{repo}: merged branch auto-delete disabled")

        rollout_state = self.rollout_state_readback(repo)
        classification = self.classify_rollout_readback(
            wanted,
            rollout_state,
            now=datetime.now(timezone.utc).isoformat(),
        )
        self.rollout_classifications[repo] = classification
        if classification == "DRIFT":
            self.errors.append(f"{repo}: rollout lifecycle DRIFT")
        elif classification == "UNKNOWN":
            message = f"{repo}: rollout lifecycle UNKNOWN (required direct readback unavailable)"
            self.unknowns.append(message)
            self.warnings.append(message)
        target_active = classification in {"SUCCESS", "TARGET"}

        branch = self.api(f"/repos/{repo}/branches/main")
        self.check(bool(branch.get("protected")) == bool(wanted.get("main_protected")), f"{repo}: main protection drift")
        if target_active:
            expected = expected_checks(wanted)
            expected_app = expected_check_app_id(wanted)
            required_sources = self.required_context_sources(
                repo,
                branch="main",
                default_branch=live.get("default_branch") or "main",
            )
            required_names = set(required_sources)
            allowed_names = allowed_required_checks(wanted)
            self.check(required_contexts_match(wanted, required_names), f"{repo}: required checks drift: expected {sorted(expected)}, allowed {sorted(allowed_names)}, got {sorted(required_names)}")
            proof_names = required_names & allowed_names
            for context in proof_names:
                observed_apps = required_sources.get(context, set())
                self.check(observed_apps == {expected_app}, f"{repo}: required check {context!r} App binding drift: expected {expected_app}, got {sorted(str(value) for value in observed_apps)}")
            emitted = self.representative_check_sources(repo, proof_names, expected_app)
            emitted_names = set(emitted)
            self.check(proof_names <= emitted_names, f"{repo}: required checks not proven on current protected push or a current internal PR containing current main: expected {sorted(proof_names)}, observed {sorted(emitted_names)}")
            for context in proof_names:
                observed_apps = emitted.get(context, set())
                self.check(observed_apps == {expected_app}, f"{repo}: emitted check {context!r} App drift: expected {expected_app}, got {sorted(str(value) for value in observed_apps)}")

            actual_protection = self.rollout_protection_controls(
                repo, branch="main", default_branch=live.get("default_branch") or "main"
            )
            for control, expected_value in wanted["protection"].items():
                self.check(
                    actual_protection.get(control) == expected_value,
                    f"{repo}: protection control {control} drift: expected {expected_value}, got {actual_protection.get(control)}",
                )

        sec = live.get("security_and_analysis") or {}
        expected_sec = wanted.get("security") or {}
        mapping = {
            "secret_scanning": "secret_scanning",
            "push_protection": "secret_scanning_push_protection",
        }
        for key, api_key in mapping.items():
            if expected_sec.get(key):
                self.check((sec.get(api_key) or {}).get("status") == "enabled", f"{repo}: security baseline missing {key}")
        if expected_sec.get("dependabot_security_updates"):
            self.check(self.dependabot_security_updates_enabled(repo), f"{repo}: security baseline missing dependabot_security_updates")
        if expected_sec.get("private_vulnerability_reporting"):
            self.check(
                self.private_vulnerability_reporting_enabled(repo),
                f"{repo}: security baseline missing private_vulnerability_reporting",
            )
        if expected_sec.get("github_actions_dependency_updates"):
            self.check(
                self.github_actions_dependency_updates_configured(repo),
                f"{repo}: security baseline missing github_actions_dependency_updates",
            )
        self.check(self.file_exists(repo, "SECURITY.md"), f"{repo}: missing SECURITY.md")
        self.check(
            self.codeowners_baseline_valid(repo, wanted["codeowners_required_paths"]),
            f"{repo}: CODEOWNERS missing, invalid, or lacks required critical-path coverage",
        )
        if expected_sec.get("workflow_supply_chain"):
            self.check(
                self.workflow_supply_chain_valid(repo),
                f"{repo}: workflow supply-chain baseline missing explicit permissions or full-SHA action pins",
            )

        permissions = self.api(f"/repos/{repo}/actions/permissions")
        self.check(actions_permissions_enabled(permissions), f"{repo}: GitHub Actions disabled")
        if permissions.get("allowed_actions") == "all":
            self.warnings.append(f"{repo}: Actions policy remains broad (allowed_actions=all)")

    def audit_administrative_repo(self, wanted: dict) -> None:
        repo = wanted["repository"]
        live = self.api(f"/repos/{repo}")
        self.check(live.get("full_name") == repo, f"{repo}: administrative coordinate drift")
        self.check(live.get("id") == wanted["repository_id"], f"{repo}: administrative repository ID drift")
        if "archived" in wanted:
            self.check(bool(live.get("archived")) == bool(wanted["archived"]), f"{repo}: archived terminal-state drift")
        self.check(
            self.retained_release_valid(repo, wanted["retention_release"]),
            f"{repo}: retained transfer-cut Release assets drift",
        )

    def _search_all_code(self, repo: str, needle: str) -> list[dict]:
        q = urllib.parse.quote_plus(f'"{needle}" repo:{repo}')
        items: list[dict] = []
        total: int | None = None
        for page in range(1, 11):
            result = self.api(f"/search/code?q={q}&per_page=100&page={page}") or {}
            if result.get("incomplete_results") is True:
                raise RuntimeError(f"code search incomplete for {repo} / {needle}")
            current_total = result.get("total_count")
            if not isinstance(current_total, int) or current_total < 0:
                raise RuntimeError(f"code search missing total_count for {repo} / {needle}")
            if current_total > 1000:
                raise RuntimeError(f"code search exceeds GitHub 1000-result completeness cap for {repo} / {needle}")
            if total is None:
                total = current_total
            elif total != current_total:
                raise RuntimeError(f"code search changed during pagination for {repo} / {needle}")
            page_items = result.get("items")
            if not isinstance(page_items, list):
                raise RuntimeError(f"code search malformed items for {repo} / {needle}")
            items.extend(item for item in page_items if isinstance(item, dict))
            if len(items) >= total:
                return items[:total]
            if not page_items:
                break
        if total is None or len(items) < total:
            raise RuntimeError(f"code search pagination incomplete for {repo} / {needle}")
        return items[:total]

    def coordinate_scan(self, desired: dict) -> None:
        policy = desired.get("mutable_coordinate_policy") or {}
        needles = list(policy.get("forbidden") or []) + list(policy.get("historical_reference_only") or [])
        for repo_item in desired["permanent_repositories"]:
            repo = repo_item["repository"]
            for needle in needles:
                for item in self._search_all_code(repo, needle):
                    path = item.get("path", "")
                    if path in POLICY_DECLARATION_FILES:
                        continue
                    historical = path in HISTORICAL_FILES or path.startswith(HISTORICAL_PREFIXES)
                    if needle in policy.get("forbidden", []) and not historical:
                        self.errors.append(f"{repo}: stale mutable coordinate {needle} in {path}")
                    elif needle in policy.get("historical_reference_only", []) and not historical:
                        self.warnings.append(f"{repo}: legacy coordinate outside historical path: {needle} in {path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true", help="validate desired-state only")
    parser.add_argument("--scan-coordinates", action="store_true", help="also query GitHub code search")
    parser.add_argument(
        "--terminal-closeout",
        action="store_true",
        help="reject V2 closeout unless every permanent repository has reached its target",
    )
    parser.add_argument(
        "--verify-control-plane-owner-authorization",
        action="store_true",
        help="read the current PR, owner comment, and owner role for one GS-5 decision",
    )
    parser.add_argument("--repository", help="repository for --verify-control-plane-owner-authorization")
    parser.add_argument("--pull-request", type=int, help="pull request for --verify-control-plane-owner-authorization")
    parser.add_argument("--material-head-sha", help="current head for --verify-control-plane-owner-authorization")
    parser.add_argument("--control-plane-scope", help="exact owner-approved scope for --verify-control-plane-owner-authorization")
    args = parser.parse_args()
    if args.offline:
        if args.terminal_closeout or args.verify_control_plane_owner_authorization:
            print("UNKNOWN: requested verification requires direct GitHub readback", file=sys.stderr)
            return 2
        desired = load_desired()
        print(f"offline desired-state validation PASS: {len(desired['permanent_repositories'])} permanent repositories")
        return 0
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("UNKNOWN: live audit requires GH_TOKEN or GITHUB_TOKEN", file=sys.stderr)
        return 2
    audit = Audit(token)
    if args.verify_control_plane_owner_authorization:
        required = {
            "--repository": args.repository,
            "--pull-request": args.pull_request,
            "--material-head-sha": args.material_head_sha,
            "--control-plane-scope": args.control_plane_scope,
        }
        missing = [flag for flag, value in required.items() if value is None or value == ""]
        if missing:
            parser.error(
                "--verify-control-plane-owner-authorization requires " + ", ".join(missing)
            )
        evidence = audit.control_plane_owner_authorization(
            args.repository,
            args.pull_request,
            args.material_head_sha,
            args.control_plane_scope,
        )
        print(json.dumps(evidence, sort_keys=True))
        return 0 if evidence.get("status") == "VERIFIED" else 2
    desired = load_desired()
    try:
        for repo in desired["permanent_repositories"]:
            audit.audit_repo(repo)
        for repo in desired.get("administrative_repositories", []):
            audit.audit_administrative_repo(repo)
        if args.scan_coordinates:
            audit.coordinate_scan(desired)
        if args.terminal_closeout and not terminal_v2_closeout_permitted(audit.rollout_classifications):
            audit.errors.append(
                "V2 terminal closeout rejected: every permanent repository must be TARGET/SUCCESS; "
                f"got {audit.rollout_classifications}"
            )
    except RuntimeError as exc:
        print(f"UNKNOWN: {exc}", file=sys.stderr)
        return 2
    for warning in audit.warnings:
        print(f"WARN: {warning}")
    for repo, classification in sorted(audit.rollout_classifications.items()):
        print(f"ROLLOUT: {repo}: {classification}")
    for error in audit.errors:
        print(f"FAIL: {error}")
    if audit.errors:
        return 1
    if audit.unknowns:
        return 2
    print(f"PASS: live governance audit; warnings={len(audit.warnings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
