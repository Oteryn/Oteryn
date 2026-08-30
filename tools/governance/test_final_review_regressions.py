#!/usr/bin/env python3
"""Regressions for findings from the final execution-policy deep review."""
from __future__ import annotations

import test_verify_ai_review_evidence as evidence
import test_verify_ai_review_evidence_compat_v1 as compat


def test_completed_summary_with_exact_clean_review_needs_no_reaction_event() -> None:
    _, _, final = compat.core_tests.make_repo()
    found = evidence._verify_summary(
        reactions=[],
        extra_reviews=[
            evidence._p2_review(
                final,
                body=evidence._codex_review_envelope(final),
            )
        ],
    )
    assert found["review_source_kind"] == "issue_comment_result"
    assert found["review_source_commit_id"] == final


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
