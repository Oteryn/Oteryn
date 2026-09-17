#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = ROOT / ".github/workflows/governed-merge-queue-executor.yml"


def _workflow() -> str:
    return WORKFLOW_PATH.read_text(encoding="utf-8")


def test_meta_checkout_fence_uses_event_sha_not_target_protected_main() -> None:
    workflow = _workflow()
    verify_step = workflow.split(
        "- name: Verify checked-out protected META main", 1
    )[1].split("- name: Execute governed native merge-async request", 1)[0]

    assert "META_EVENT_SHA: ${{ github.sha }}" in verify_step
    assert "steps.parse.outputs.protected_main_sha" not in verify_step
    assert 'checked_out_main" != "$META_EVENT_SHA"' in verify_step


def test_target_protected_main_fence_remains_separate_executor_input() -> None:
    workflow = _workflow()
    execute_step = workflow.split(
        "- name: Execute governed native merge-async request", 1
    )[1]

    assert (
        "TARGET_PROTECTED_MAIN_SHA: ${{ steps.parse.outputs.protected_main_sha }}"
        in execute_step
    )
    assert '--protected-main-sha "$TARGET_PROTECTED_MAIN_SHA"' in execute_step
