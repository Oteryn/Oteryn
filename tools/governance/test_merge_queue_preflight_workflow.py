#!/usr/bin/env python3
"""Static contract checks for the protected Merge Queue preflight workflows."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WRAPPER = ROOT / ".github/workflows/merge-queue-preflight.yml"
REUSABLE = ROOT / ".github/workflows/merge-queue-preflight-reusable.yml"


def test_wrapper_is_default_branch_issue_comment_only() -> None:
    text = WRAPPER.read_text(encoding="utf-8")
    for marker in (
        "issue_comment:",
        "types: [created]",
        "github.event.issue.pull_request",
        "startsWith(github.event.comment.body, '/oteryn-mq-preflight ')",
        "uses: ./.github/workflows/merge-queue-preflight-reusable.yml",
        "command_body: ${{ github.event.comment.body }}",
        "repository: ${{ github.repository }}",
        "pr_number: ${{ github.event.issue.number }}",
        "trigger_comment_id: ${{ github.event.comment.id }}",
    ):
        assert marker in text
    for forbidden in ("pull_request_target:", "pull_request:", "workflow_dispatch:"):
        assert forbidden not in text


def test_preflight_permissions_are_read_only_except_proof_comment() -> None:
    for path in (WRAPPER, REUSABLE):
        text = path.read_text(encoding="utf-8")
        assert "contents: read" in text
        assert "pull-requests: read" in text
        assert "issues: write" in text
        assert "contents: write" not in text
        assert "pull-requests: write" not in text
        assert "actions: write" not in text
        assert "checks: write" not in text
        assert "statuses: write" not in text
        assert "id-token: write" not in text


def test_reusable_never_submits_or_merges() -> None:
    text = REUSABLE.read_text(encoding="utf-8")
    assert "workflow_call:" in text
    for forbidden in (
        "enqueuePullRequest",
        "enablePullRequestAutoMerge",
        "gh pr merge",
        "merge_pull_request",
        "git push",
        "actions/checkout",
    ):
        assert forbidden not in text


def test_reusable_binds_comment_pr_head_and_queue_identity() -> None:
    text = REUSABLE.read_text(encoding="utf-8")
    for marker in (
        "ALLOWED_ASSOCIATIONS = {\"OWNER\", \"MEMBER\", \"COLLABORATOR\"}",
        "/oteryn-mq-preflight <attempt_id> <40-char-head-sha>",
        'pr.get("state") != "open"',
        'pr.get("draft") is not False',
        'base_repo.get("full_name") != REPOSITORY',
        'head_repo.get("full_name") != REPOSITORY',
        'base_ref != "main"',
        "live_head_sha != expected_head_sha",
        "repository(owner: $owner, name: $name)",
        "mergeQueue {",
        'expected_resource_path = f"/{REPOSITORY}/queue/{base_ref}"',
        'expected_url = f"https://github.com{expected_resource_path}"',
        '"source": "protected_issue_comment_preflight"',
        '"pr_head_sha": live_head_sha',
        '"queue_id": queue_id',
        '"resource_path": resource_path',
        '"url": url',
        '"trigger_comment_id": COMMENT_ID',
        '"workflow_run_id": RUN_ID',
        '"workflow_run_attempt": RUN_ATTEMPT',
        '"expires_at_epoch_seconds": observed_at + MAX_AGE_SECONDS',
        "OTERYN_MQ_PREFLIGHT_V1=",
    ):
        assert marker in text


def test_preflight_observation_is_minted_after_live_reads() -> None:
    text = REUSABLE.read_text(encoding="utf-8")
    queue_read = text.index('queue_payload = request_json(')
    queue_identity = text.index('if resource_path != expected_resource_path or url != expected_url:')
    observed_at = text.index('observed_at = int(time.time())')
    proof = text.index('proof = {')
    post_comment = text.index('payload={"body": comment_body}')
    assert queue_read < queue_identity < observed_at < proof < post_comment


def main() -> int:
    failures = []
    tests = [
        (name, fn)
        for name, fn in sorted(globals().items())
        if name.startswith("test_") and callable(fn)
    ]
    for name, fn in tests:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 - compact deterministic harness
            failures.append((name, exc))
    if failures:
        for name, exc in failures:
            print(f"FAIL {name}: {exc}")
        return 1
    print(f"PASS {len(tests)} Merge Queue preflight workflow regressions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
