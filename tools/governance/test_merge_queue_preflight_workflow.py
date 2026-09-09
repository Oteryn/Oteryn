#!/usr/bin/env python3
"""Static contract checks for the protected organization Merge Queue preflight."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WRAPPER = ROOT / ".github/workflows/merge-queue-preflight.yml"
REUSABLE = ROOT / ".github/workflows/merge-queue-preflight-reusable.yml"


def test_wrapper_is_central_default_branch_issue_comment_only() -> None:
    text = WRAPPER.read_text(encoding="utf-8")
    for marker in (
        "issue_comment:",
        "types: [created]",
        "github.repository == 'Oteryn/Oteryn'",
        "github.event.issue.number == 189",
        "!github.event.issue.pull_request",
        "startsWith(github.event.comment.body, '/oteryn-mq-preflight ')",
        "uses: ./.github/workflows/merge-queue-preflight-reusable.yml",
        "author_association: ${{ github.event.comment.author_association }}",
        "comment_author_login: ${{ github.event.comment.user.login }}",
        "control_repository: ${{ github.repository }}",
        "control_issue_number: ${{ github.event.issue.number }}",
        "trigger_comment_id: ${{ github.event.comment.id }}",
    ):
        assert marker in text
    for forbidden in ("pull_request_target:", "pull_request:", "workflow_dispatch:"):
        assert forbidden not in text


def test_preflight_permissions_cannot_mutate_target_repository() -> None:
    for path in (WRAPPER, REUSABLE):
        text = path.read_text(encoding="utf-8")
        assert "contents: read" in text
        assert "pull-requests: read" in text
        assert "issues: write" in text
        for forbidden in (
            "contents: write",
            "pull-requests: write",
            "actions: write",
            "checks: write",
            "statuses: write",
            "id-token: write",
        ):
            assert forbidden not in text


def test_reusable_never_executes_candidate_or_submits_merge() -> None:
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


def test_reusable_is_bound_to_meta_control_issue_actor_and_current_permission() -> None:
    text = REUSABLE.read_text(encoding="utf-8")
    for marker in (
        'CONTROL_REPOSITORY_EXPECTED = "Oteryn/Oteryn"',
        "CONTROL_ISSUE_EXPECTED = 189",
        'EVENT_NAME != "issue_comment"',
        'EVENT_HAS_PR != "false"',
        "EVENT_REPOSITORY != CONTROL_REPOSITORY_EXPECTED",
        "EVENT_ISSUE_NUMBER != CONTROL_ISSUE_EXPECTED",
        "EVENT_COMMENT_ID != COMMENT_ID",
        "EVENT_COMMENT_BODY != COMMAND_BODY",
        "EVENT_AUTHOR_ASSOCIATION != AUTHOR_ASSOCIATION",
        "EVENT_COMMENT_AUTHOR_LOGIN != COMMENT_AUTHOR_LOGIN",
        'ALLOWED_PERMISSIONS = {"write", "maintain", "admin"}',
        '/collaborators/{actor}/permission',
        "effective_permission not in ALLOWED_PERMISSIONS",
        "preflight inputs are not bound to META control Issue #189",
    ):
        assert marker in text


def test_reusable_allows_exactly_four_targets_and_binds_pr_head_queue() -> None:
    text = REUSABLE.read_text(encoding="utf-8")
    for marker in (
        '"Oteryn/Oteryn"',
        '"Oteryn/Oteryn-Game"',
        '"Oteryn/Oteryn-Platform"',
        '"Oteryn/Oteryn-Atlas"',
        "/oteryn-mq-preflight <attempt_id> <owner/repo> <pr_number> <40-char-head-sha>",
        'pr.get("state") != "open"',
        'pr.get("draft") is not False',
        'base_ref != "main"',
        "live_head_sha != expected_head_sha",
        "repository(owner: $owner, name: $name)",
        "mergeQueue {",
        'expected_resource_path = f"/{target_repository}/queue/{base_ref}"',
        'expected_url = f"https://github.com{expected_resource_path}"',
        '"source": "protected_meta_control_preflight"',
        '"control_repository": CONTROL_REPOSITORY',
        '"control_issue_number": CONTROL_ISSUE_NUMBER',
        '"repository": target_repository',
        '"pr_number": pr_number',
        '"pr_head_sha": live_head_sha',
        '"queue_id": queue_id',
        '"workflow_sha": WORKFLOW_SHA',
        '"expires_at_epoch_seconds": observed_at + MAX_AGE_SECONDS',
        "OTERYN_MQ_PREFLIGHT_V1=",
    ):
        assert marker in text


def test_proof_comment_is_github_authored_self_bound_and_read_back() -> None:
    text = REUSABLE.read_text(encoding="utf-8")
    for marker in (
        'PROOF_AUTHOR = "github-actions[bot]"',
        'payload={"body": f"OTERYN_MQ_PREFLIGHT_PENDING {attempt_id}"}',
        'proof_comment_id = placeholder.get("id")',
        'proof_author = ((placeholder.get("user") or {}).get("login"))',
        'proof_author != PROOF_AUTHOR',
        '"proof_comment_id": proof_comment_id',
        '"proof_comment_author_login": proof_author',
        'f"https://api.github.com/repos/{CONTROL_REPOSITORY}/issues/comments/{proof_comment_id}"',
        'method="PATCH"',
        'updated_id != proof_comment_id',
        'updated_author != PROOF_AUTHOR',
        'updated.get("body") != comment_body',
    ):
        assert marker in text


def test_proof_is_minted_only_after_permission_pr_and_queue_reads() -> None:
    text = REUSABLE.read_text(encoding="utf-8")
    permission_read = text.index('/collaborators/{actor}/permission')
    pr_read = text.index('pr = request_json(f"https://api.github.com/repos/{target_repository}/pulls/{pr_number}")')
    queue_read = text.index('queue_payload = request_json(')
    placeholder = text.index('placeholder = request_json(')
    observed_at = text.index('observed_at = int(time.time())')
    proof = text.index('proof = {')
    patch = text.index('method="PATCH"')
    assert permission_read < pr_read < queue_read < placeholder < observed_at < proof < patch


def main() -> int:
    failures = []
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            failures.append((name, exc))
    if failures:
        for name, exc in failures:
            print(f"FAIL {name}: {exc}")
        return 1
    print(f"PASS {len(tests)} Merge Queue preflight workflow regressions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
