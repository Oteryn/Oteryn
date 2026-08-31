#!/usr/bin/env python3
"""Fail-closed contract checks for GitHub-native Merge Queue workflows."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CI_WORKFLOW = ROOT / ".github/workflows/ci.yml"
MERGE_GROUP_ADAPTER = ROOT / ".github/workflows/merge-group-ai-review-adapter.yml"


def _job_body(workflow: str, job_name: str) -> str:
    match = re.search(
        rf"(?ms)^  {re.escape(job_name)}:\n(?P<body>.*?)(?=^  [A-Za-z][^\n]*:\n|\Z)",
        workflow,
    )
    if not match:
        raise AssertionError(f"missing {job_name!r} job")
    return match.group("body")


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


def test_merge_group_adapter_is_inert_and_fail_closed() -> None:
    workflow = MERGE_GROUP_ADAPTER.read_text(encoding="utf-8")

    assert "  merge_group:\n    types: [checks_requested]" in workflow
    assert "permissions: {}" in workflow
    assert len(re.findall(r"(?m)^  ai-review-gate:\n", workflow)) == 1

    gate = _job_body(workflow, "ai-review-gate")
    assert not re.search(r"(?m)^    if:", gate)
    assert '[[ "$EVENT_NAME" == "merge_group" ]]' in gate
    assert '[[ "$EVENT_ACTION" == "checks_requested" ]]' in gate
    assert '[[ "$MERGE_GROUP_BASE_REF" == "refs/heads/main" ]]' in gate
    assert '[[ "$GITHUB_SHA" == "$MERGE_GROUP_HEAD_SHA" ]]' in gate

    for forbidden in (
        "pull_request",
        "push:",
        "workflow_dispatch",
        "workflow_call",
        "actions/checkout",
        "secrets.",
        "github.event.pull_request",
    ):
        assert forbidden not in workflow, forbidden


def test_ci_keeps_pr_review_authority_outside_meta_gate() -> None:
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    assert "\n  ai-review-gate:\n" not in workflow


if __name__ == "__main__":
    test_meta_gate_qualifies_pull_requests_and_exact_merge_group_candidates()
    test_merge_group_adapter_is_inert_and_fail_closed()
    test_ci_keeps_pr_review_authority_outside_meta_gate()
    print("merge queue workflow contract PASS")
