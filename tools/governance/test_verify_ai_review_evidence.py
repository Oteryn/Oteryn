#!/usr/bin/env python3
from __future__ import annotations

from datetime import timedelta

from test_verify_ai_review_evidence_core import *


def _iso(stamp) -> str:
    return stamp.isoformat().replace("+00:00", "Z")


def _verify_with_only_current_anchor(comments, repo, final, current_request):
    return m.verify_records(
        comments,
        policy=POLICY,
        repo_root=repo,
        tier="R2",
        fingerprint=ISSUE_FP,
        head=final,
        repository="Oteryn/Test",
        pr_number=7,
        token="x",
        reviews=[request_anchor(current_request, final)],
        review_comments=[],
    )


def test_pre_registry_unstructured_request_does_not_poison_post_rollout_head() -> None:
    repo, rollout, final = make_repo()
    original_rollout = m.REQUEST_ANCHOR_ROLLOUT_COMMIT
    m.REQUEST_ANCHOR_ROLLOUT_COMMIT = rollout
    try:
        cutoff = m._request_anchor_rollout_time(repo)
        assert cutoff is not None
        historical = issue_comment(
            9,
            "@codex review\n\nlegacy request created before immutable anchors existed",
            stamp=_iso(cutoff - timedelta(seconds=2)),
        )
        current = issue_comment(
            10,
            request_body(final),
            stamp=_iso(cutoff + timedelta(seconds=1)),
        )
        result = codex_result(
            11,
            final[:10],
            stamp=_iso(cutoff + timedelta(seconds=2)),
        )
        found = _verify_with_only_current_anchor([historical, current, result], repo, final, current)
        assert found["review_source_kind"] == "issue_comment_result"
        assert found["review_source_commit_id"] == final
    finally:
        m.REQUEST_ANCHOR_ROLLOUT_COMMIT = original_rollout


def test_post_registry_unanchored_malformed_request_remains_ambiguous() -> None:
    repo, rollout, final = make_repo()
    original_rollout = m.REQUEST_ANCHOR_ROLLOUT_COMMIT
    m.REQUEST_ANCHOR_ROLLOUT_COMMIT = rollout
    try:
        cutoff = m._request_anchor_rollout_time(repo)
        assert cutoff is not None
        malformed = issue_comment(
            9,
            "@codex review\n\nmalformed request after registry rollout",
            stamp=_iso(cutoff + timedelta(seconds=1)),
        )
        current = issue_comment(
            10,
            request_body(final),
            stamp=_iso(cutoff + timedelta(seconds=2)),
        )
        result = codex_result(
            11,
            final[:10],
            stamp=_iso(cutoff + timedelta(seconds=3)),
        )
        expect_fail(lambda: _verify_with_only_current_anchor(
            [malformed, current, result], repo, final, current
        ))
    finally:
        m.REQUEST_ANCHOR_ROLLOUT_COMMIT = original_rollout


def main() -> int:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print(f"ai review evidence tests PASS: {len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
