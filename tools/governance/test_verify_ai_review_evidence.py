#!/usr/bin/env python3
from __future__ import annotations

import test_verify_ai_review_evidence_compat_v1 as _v1


def test_observed_dynamic_clean_flair_passes() -> None:
    for flair in (
        "Already looking forward to the next diff.",
        "Another round soon, please!",
    ):
        repo, _, final = _v1.core_tests.make_repo()
        current = _v1.core_tests.issue_comment(
            10, _v1.core_tests.request_body(final), stamp="2026-08-20T10:00:00Z",
        )
        result = _v1.core_tests.codex_result(
            11,
            final[:10],
            stamp="2026-08-20T10:01:00Z",
            text=_v1._live_clean_text(final, flair),
        )
        found = _v1._verify_with_only_current_anchor([current, result], repo, final, current)
        assert found["review_source_kind"] == "issue_comment_result"
        assert found["review_source_commit_id"] == final


def test_every_unobserved_clean_flair_fails_closed() -> None:
    for flair in (
        "Critical defect detected.",
        "Merge is unsafe.",
        "Blocking regression detected.",
        "Wonderful future diff.",
        "Ship it but P1 remains.",
    ):
        repo, _, final = _v1.core_tests.make_repo()
        current = _v1.core_tests.issue_comment(
            10, _v1.core_tests.request_body(final), stamp="2026-08-20T10:00:00Z",
        )
        result = _v1.core_tests.codex_result(
            11,
            final[:10],
            stamp="2026-08-20T10:01:00Z",
            text=_v1._live_clean_text(final, flair),
        )
        _v1.core_tests.expect_fail(
            lambda: _v1._verify_with_only_current_anchor([current, result], repo, final, current)
        )


def main() -> int:
    inherited = [
        value for name, value in sorted(vars(_v1).items())
        if name.startswith("test_") and callable(value)
    ]
    local = [
        value for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    tests = inherited + local
    for test in tests:
        test()
        print("PASS", test.__name__)
    print(f"ai review evidence tests PASS: {len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
