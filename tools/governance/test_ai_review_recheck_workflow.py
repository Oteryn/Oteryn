from pathlib import Path


def test_review_evidence_recheck_is_same_head_and_non_mutating() -> None:
    root = Path(__file__).resolve().parents[2]
    workflow = (root / ".github/workflows/governance-ai-review-recheck.yml").read_text(encoding="utf-8")
    assert "pull_request_review:" in workflow
    assert "issue_comment:" in workflow
    assert "actions: write" in workflow
    assert "contents: read" in workflow
    assert "pull-requests: read" in workflow
    assert "actions/checkout" not in workflow
    assert "git commit" not in workflow
    assert "git push" not in workflow
    assert "/rerun" in workflow
    assert "head_sha" in workflow
    assert "pull_request_target" in workflow
    assert "governance-ai-review.yml" in workflow
    assert "chatgpt-codex-connector[bot]" in workflow
