#!/usr/bin/env python3
"""Fail-closed contract checks for GitHub-native Merge Queue workflows."""

from __future__ import annotations

import json
import re
from pathlib import Path

from governance_drift_audit import audit_snapshot


ROOT = Path(__file__).resolve().parents[2]
CI_WORKFLOW = ROOT / ".github/workflows/ci.yml"
DESIRED_STATE = ROOT / "ecosystem/governance-desired-state.json"
MERGE_GROUP_ADAPTER = ROOT / ".github/workflows/merge-group-ai-review-adapter.yml"
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


def _job_body(workflow: str, job_name: str) -> str:
    match = re.search(
        rf"(?ms)^  {re.escape(job_name)}:\n(?P<body>.*?)(?=^  [A-Za-z][^\n]*:\n|\Z)",
        workflow,
    )
    if not match:
        raise AssertionError(f"missing {job_name!r} job")
    return match.group("body")


def _desired_state() -> dict:
    return json.loads(DESIRED_STATE.read_text(encoding="utf-8"))


def _matching_live_state() -> dict:
    desired = _desired_state()
    rows = []
    for expected in desired["permanent_repositories"]:
        rows.append(
            {
                "repository": expected["repository"],
                **{field: expected[field] for field in ENFORCEMENT_FIELDS},
            }
        )
    return {"repositories": rows}


def test_meta_gate_qualifies_pull_requests_and_exact_merge_group_candidates() -> None:
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")

    assert "  pull_request:\n    branches: [main]" in workflow
    assert "  merge_group:\n    types: [checks_requested]" in workflow
    assert workflow.count("\n  meta-gate:\n") == 1
    assert "github.event.merge_group.head_sha || github.event.pull_request.head.sha || github.sha" in workflow
    assert "github.event.merge_group.base_sha || github.event.before || ''" in workflow

    gate = _job_body(workflow, "meta-gate")
    assert "MERGE_GROUP_HEAD_SHA: ${{ github.event.merge_group.head_sha || '' }}" in gate
    assert "MERGE_GROUP_BASE_REF: ${{ github.event.merge_group.base_ref || '' }}" in gate
    assert '[[ "$GITHUB_SHA" == "$MERGE_GROUP_HEAD_SHA" ]]' in gate
    assert '[[ "$MERGE_GROUP_BASE_REF" == "refs/heads/main" ]]' in gate


def test_meta_gate_executes_bounded_execution_guard_regressions() -> None:
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    gate = _job_body(workflow, "meta-gate")

    assert "python3 tools/governance/test_bounded_execution_guard.py" in gate


def test_legacy_ai_merge_group_adapter_is_retired() -> None:
    assert not MERGE_GROUP_ADAPTER.exists()


def test_ci_has_one_external_gate_only() -> None:
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    assert "\n  ai-review-gate:\n" not in workflow
    assert "ai_review_policy.py" not in workflow
    assert "trusted_review_attestation.py" not in workflow
    assert "verify_ai_review_evidence.py" not in workflow


def test_drift_audit_accepts_exact_target_snapshot() -> None:
    report = audit_snapshot(_desired_state(), _matching_live_state())

    assert report["status"] == "TARGET"
    assert [row["status"] for row in report["repositories"]] == ["TARGET"] * 4
    assert all(not row["drift"] and not row["unknown"] for row in report["repositories"])


def test_drift_audit_reports_known_mismatch_as_drift() -> None:
    live = _matching_live_state()
    platform = next(row for row in live["repositories"] if row["repository"] == "Oteryn/Oteryn-Platform")
    platform["strict_required_status_checks"] = True

    report = audit_snapshot(_desired_state(), live)
    row = next(item for item in report["repositories"] if item["repository"] == "Oteryn/Oteryn-Platform")

    assert report["status"] == "DRIFT"
    assert row["status"] == "DRIFT"
    assert row["drift"] == [
        {
            "field": "strict_required_status_checks",
            "expected": False,
            "actual": True,
        }
    ]


def test_drift_audit_preserves_unobservable_field_as_unknown() -> None:
    live = _matching_live_state()
    platform = next(row for row in live["repositories"] if row["repository"] == "Oteryn/Oteryn-Platform")
    del platform["broad_bypass"]

    report = audit_snapshot(_desired_state(), live)
    row = next(item for item in report["repositories"] if item["repository"] == "Oteryn/Oteryn-Platform")

    assert report["status"] == "UNKNOWN"
    assert row["status"] == "UNKNOWN"
    assert row["drift"] == []
    assert row["unknown"] == ["broad_bypass"]


def test_drift_audit_rejects_duplicate_repository_snapshot() -> None:
    live = _matching_live_state()
    live["repositories"].append(dict(live["repositories"][0]))

    try:
        audit_snapshot(_desired_state(), live)
    except ValueError as exc:
        assert "duplicate" in str(exc).lower()
    else:
        raise AssertionError("duplicate live repository snapshot must fail closed")


if __name__ == "__main__":
    test_meta_gate_qualifies_pull_requests_and_exact_merge_group_candidates()
    test_meta_gate_executes_bounded_execution_guard_regressions()
    test_legacy_ai_merge_group_adapter_is_retired()
    test_ci_has_one_external_gate_only()
    test_drift_audit_accepts_exact_target_snapshot()
    test_drift_audit_reports_known_mismatch_as_drift()
    test_drift_audit_preserves_unobservable_field_as_unknown()
    test_drift_audit_rejects_duplicate_repository_snapshot()
    print("merge queue workflow contract PASS")
