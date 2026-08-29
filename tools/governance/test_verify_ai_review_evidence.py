#!/usr/bin/env python3
from __future__ import annotations

import test_verify_ai_review_evidence_compat_v1 as _v1


def test_observed_dynamic_clean_flair_passes() -> None:
    for flair in (
        "Already looking forward to the next diff.",
        "Another round soon, please!",
        "Keep it up!",
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


def _summary_body(prefix: str, *, completed: str = "2026-08-20T10:01:00Z",
                  trigger: str = "Manual request") -> str:
    return (
        "<!-- codex-pull-request-review-summary -->\n\n"
        "## Codex Review Summary\n\n"
        "This comment shows the latest Codex review activity on this pull request.\n\n"
        "| Review | Status | Commit | Review trigger |\n"
        "| --- | --- | --- | --- |\n"
        f"| 📝 **Code Review** | ✅ **Completed** <relative-time datetime=\"{completed}\">"
        f"{completed}</relative-time> | `{prefix}` | {trigger} |\n\n"
        "Codex reacts with 👀 while any review is running, comments if it has suggestions, "
        "and reacts with 👍 once all reviews finish with no findings.\n"
    )


def _summary_comment(prefix: str, *, completed: str = "2026-08-20T10:01:00Z",
                     trigger: str = "Manual request", app_slug: str = "chatgpt-codex-connector",
                     updated: str = "2026-08-20T10:01:02Z") -> dict:
    comment = _v1.core_tests.issue_comment(
        11,
        _summary_body(prefix, completed=completed, trigger=trigger),
        login="chatgpt-codex-connector[bot]",
        association="NONE",
        stamp="2026-08-20T09:00:00Z",
        updated_stamp=updated,
    )
    comment["performed_via_github_app"] = {"slug": app_slug}
    return comment


def _reaction(*, login: str = "chatgpt-codex-connector[bot]",
              stamp: str = "2026-08-20T10:01:01Z", reaction_id: int = 99) -> dict:
    return {
        "id": reaction_id,
        "content": "+1",
        "created_at": stamp,
        "user": {"login": login},
    }


def _verify_summary(*, summary: dict | None = None, reactions: list[dict] | None = None,
                    request_updated: str | None = None, extra_reviews: list[dict] | None = None) -> dict:
    repo, _, final = _v1.core_tests.make_repo()
    current = _v1.core_tests.issue_comment(
        10,
        _v1.core_tests.request_body(final),
        stamp="2026-08-20T10:00:00Z",
        updated_stamp=request_updated,
    )
    return _v1.m.verify_records(
        [current, summary or _summary_comment(final[:10])],
        policy=_v1.POLICY,
        repo_root=repo,
        tier="R2",
        fingerprint=_v1.core_tests.ISSUE_FP,
        head=final,
        repository="Oteryn/Test",
        pr_number=7,
        token="x",
        reviews=[_v1.core_tests.request_anchor(current, final), *(extra_reviews or [])],
        review_comments=[],
        pr_reactions=[_reaction()] if reactions is None else reactions,
    )


def test_current_codex_completed_summary_plus_pr_reaction_passes() -> None:
    found = _verify_summary()
    assert found["review_source_kind"] == "issue_comment_result"
    assert found["review_source_author"] == "chatgpt-codex-connector[bot]"


def test_current_codex_summary_requires_trusted_pr_reaction() -> None:
    _v1.core_tests.expect_fail(lambda: _verify_summary(reactions=[]))
    _v1.core_tests.expect_fail(
        lambda: _verify_summary(reactions=[_reaction(login="someone-else")])
    )


def test_current_codex_summary_rejects_wrong_reviewed_commit() -> None:
    _v1.core_tests.expect_fail(
        lambda: _verify_summary(summary=_summary_comment("f" * 10))
    )


def test_current_codex_summary_rejects_non_manual_trigger() -> None:
    _v1.core_tests.expect_fail(
        lambda: _verify_summary(summary=_summary_comment("0" * 10, trigger="Automatic"))
    )


def test_current_codex_summary_rejects_wrong_github_app() -> None:
    _v1.core_tests.expect_fail(
        lambda: _verify_summary(summary=_summary_comment("0" * 10, app_slug="other-app"))
    )


def test_current_codex_summary_requires_completion_after_request() -> None:
    _v1.core_tests.expect_fail(
        lambda: _verify_summary(
            summary=_summary_comment("0" * 10, completed="2026-08-20T09:59:59Z"),
            reactions=[_reaction(stamp="2026-08-20T10:01:01Z")],
        )
    )


def test_current_codex_summary_requires_one_post_completion_reaction() -> None:
    _v1.core_tests.expect_fail(
        lambda: _verify_summary(
            reactions=[_reaction(reaction_id=1), _reaction(reaction_id=2, stamp="2026-08-20T10:01:02Z")]
        )
    )
    _v1.core_tests.expect_fail(
        lambda: _verify_summary(reactions=[_reaction(stamp="2026-08-20T10:00:30Z")])
    )


def test_current_codex_summary_does_not_relax_edited_request_rejection() -> None:
    _v1.core_tests.expect_fail(
        lambda: _verify_summary(request_updated="2026-08-20T10:00:01Z")
    )


def test_current_codex_summary_preserves_blocking_review_finding() -> None:
    repo, _, final = _v1.core_tests.make_repo()
    current = _v1.core_tests.issue_comment(
        10, _v1.core_tests.request_body(final), stamp="2026-08-20T10:00:00Z",
    )
    summary = _summary_comment(final[:10])
    blocker = _v1.core_tests.codex_review(700, final, body_text="[P1] Security boundary bypass")
    _v1.core_tests.expect_fail(
        lambda: _v1.m.verify_records(
            [current, summary],
            policy=_v1.POLICY,
            repo_root=repo,
            tier="R2",
            fingerprint=_v1.core_tests.ISSUE_FP,
            head=final,
            repository="Oteryn/Test",
            pr_number=7,
            token="x",
            reviews=[_v1.core_tests.request_anchor(current, final), blocker],
            review_comments=[],
            pr_reactions=[_reaction()],
        )
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
