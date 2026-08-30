#!/usr/bin/env python3
"""Regressions for findings from the final execution-policy deep review."""
from __future__ import annotations

import test_verify_ai_review_evidence as evidence
import test_verify_ai_review_evidence_compat_v1 as compat


def _clean_review(final: str, *, review_id: int = 701, login: str = "chatgpt-codex-connector[bot]", head: str | None = None) -> dict:
    reviewed_head = head or final
    return evidence._p2_review(
        reviewed_head,
        review_id=review_id,
        login=login,
        body=evidence._codex_review_envelope(reviewed_head),
    )


def test_completed_summary_with_exact_clean_review_needs_no_reaction_event() -> None:
    _, _, final = compat.core_tests.make_repo()
    found = evidence._verify_summary(
        reactions=[],
        extra_reviews=[_clean_review(final)],
    )
    assert found["review_source_kind"] == "issue_comment_result"
    assert found["review_source_commit_id"] == final


def test_clean_review_completion_is_unique_and_exact_head() -> None:
    _, _, final = compat.core_tests.make_repo()
    compat.core_tests.expect_fail(
        lambda: evidence._verify_summary(
            reactions=[],
            extra_reviews=[_clean_review(final), _clean_review(final, review_id=703)],
        )
    )
    compat.core_tests.expect_fail(
        lambda: evidence._verify_summary(
            reactions=[],
            extra_reviews=[_clean_review(final, head="f" * 40)],
        )
    )
    compat.core_tests.expect_fail(
        lambda: evidence._verify_summary(
            reactions=[],
            extra_reviews=[_clean_review(final, login="untrusted-bot")],
        )
    )


def test_clean_review_completion_never_suppresses_inline_finding() -> None:
    _, _, final = compat.core_tests.make_repo()
    compat.core_tests.expect_fail(
        lambda: evidence._verify_summary(
            reactions=[],
            extra_reviews=[_clean_review(final)],
            review_comments=[
                evidence._p2_inline(review_id=701, body="[P1] Exact-head blocking finding")
            ],
        )
    )


def main() -> int:
    tests = [
        value for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print(f"final deep-review regressions PASS: {len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
