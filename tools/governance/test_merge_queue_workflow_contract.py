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


def test_legacy_ai_merge_group_adapter_is_retired() -> None:
    assert not MERGE_GROUP_ADAPTER.exists()


def test_ci_has_one_external_gate_only() -> None:
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    assert "\n  ai-review-gate:\n" not in workflow
    assert "ai_review_policy.py" not in workflow
    assert "trusted_review_attestation.py" not in workflow
    assert "verify_ai_review_evidence.py" not in workflow


if __name__ == "__main__":
    test_meta_gate_qualifies_pull_requests_and_exact_merge_group_candidates()
    test_legacy_ai_merge_group_adapter_is_retired()
    test_ci_has_one_external_gate_only()
    print("merge queue workflow contract PASS")
