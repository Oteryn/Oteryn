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


def _verify_summary(*, summary_prefix: str | None = None,
                    completed: str = "2026-08-20T10:01:00Z",
                    trigger: str = "Manual request",
                    app_slug: str = "chatgpt-codex-connector",
                    updated: str = "2026-08-20T10:01:02Z",
                    reactions: list[dict] | None = None,
                    request_updated: str | None = None,
                    extra_reviews: list[dict] | None = None) -> dict:
    repo, _, final = _v1.core_tests.make_repo()
    current = _v1.core_tests.issue_comment(
        10,
        _v1.core_tests.request_body(final),
        stamp="2026-08-20T10:00:00Z",
        updated_stamp=request_updated,
    )
    summary = _summary_comment(
        summary_prefix or final[:10],
        completed=completed,
        trigger=trigger,
        app_slug=app_slug,
        updated=updated,
    )
    return _v1.m.verify_records(
        [current, summary],
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
    _v1.core_tests.expect_fail(lambda: _verify_summary(summary_prefix="f" * 10))


def test_current_codex_summary_rejects_non_manual_trigger() -> None:
    _v1.core_tests.expect_fail(lambda: _verify_summary(trigger="Automatic"))


def test_current_codex_summary_rejects_wrong_github_app() -> None:
    _v1.core_tests.expect_fail(lambda: _verify_summary(app_slug="other-app"))


def test_current_codex_summary_requires_completion_after_request() -> None:
    _v1.core_tests.expect_fail(
        lambda: _verify_summary(
            completed="2026-08-20T09:59:59Z",
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


def test_current_codex_summary_preserves_blocking_finding_in_summary_body() -> None:
    repo, _, final = _v1.core_tests.make_repo()
    current = _v1.core_tests.issue_comment(
        10, _v1.core_tests.request_body(final), stamp="2026-08-20T10:00:00Z",
    )
    summary = _summary_comment(final[:10])
    summary["body"] += "\n[P1] Security boundary bypass"
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
            reviews=[_v1.core_tests.request_anchor(current, final)],
            review_comments=[],
            pr_reactions=[_reaction()],
        )
    )


def _observed_duplicate_echo_body(
    prefix: str, *, first_line: str,
    extra: str = "",
) -> str:
    return (
        f"{first_line}\n\n"
        f"**Reviewed commit:** `{prefix}`\n\n"
        "<details> <summary>ℹ️ About Codex in GitHub</summary>\n"
        "<br/>\n\n"
        "[Your team has set up Codex to review pull requests in this repo]"
        "(https://chatgpt.com/codex/cloud/settings/general). Reviews are triggered when you\n"
        "- Open a pull request for review\n"
        "- Mark a draft as ready\n"
        "- Comment \"@codex review\".\n\n"
        "If Codex has suggestions, it will comment; otherwise it will react with 👍.\n\n\n\n\n"
        "Codex can also answer questions or update the PR. Try commenting "
        f"\"@codex address that feedback\".{extra}\n"
        "            \n"
        "</details>"
    )


def _verify_summary_merge_reuse_with_echoes(
    *, echo_prefix: str | None = None, echo_stamp: str = "2026-08-20T10:00:59Z",
    echo_extra: str = "", echo_count: int = 1,
    echo_first_line: str = "Codex Review: Didn't find any major issues. Delightful!",
) -> dict:
    repo, reviewed, _ = _v1.core_tests.make_repo()
    _v1.core_tests.git(repo, "reset", "--hard", reviewed)
    _v1.core_tests.git(repo, "checkout", "-b", "task-summary-reuse")
    _v1.core_tests.git(repo, "checkout", "master")
    upstream = repo / "upstream.py"
    upstream.write_text("VALUE = 1\n", encoding="utf-8")
    _v1.core_tests.git(repo, "add", ".")
    _v1.core_tests.git(repo, "commit", "-m", "independent upstream")
    integration_base = _v1.core_tests.git(repo, "rev-parse", "HEAD")
    _v1.core_tests.git(repo, "checkout", "task-summary-reuse")
    _v1.core_tests.git(repo, "merge", "--no-ff", "master", "-m", "merge current main")
    final = _v1.core_tests.git(repo, "rev-parse", "HEAD")

    request = _v1.core_tests.issue_comment(
        10, _v1.core_tests.request_body(reviewed), stamp="2026-08-20T10:00:00Z",
    )
    summary = _summary_comment(reviewed[:10])
    echoes: list[dict] = []
    for index in range(echo_count):
        prefix = echo_prefix or reviewed[:10]
        echo = _v1.core_tests.codex_result(
            12 + index,
            prefix,
            stamp=echo_stamp,
            text=_observed_duplicate_echo_body(
                prefix,
                first_line=echo_first_line,
                extra=echo_extra,
            ),
        )
        echo["performed_via_github_app"] = {"slug": "chatgpt-codex-connector"}
        echoes.append(echo)

    policy = dict(_v1.POLICY)
    policy["activation"] = dict(_v1.POLICY["activation"])
    policy["_trusted_integration_base_sha"] = integration_base
    return _v1.m.verify_records(
        [request, summary, *echoes],
        policy=policy,
        repo_root=repo,
        tier="R2",
        fingerprint=_v1.core_tests.ISSUE_FP,
        head=final,
        repository="Oteryn/Test",
        pr_number=7,
        token="x",
        reviews=[_v1.core_tests.request_anchor(request, reviewed)],
        review_comments=[],
        pr_reactions=[_reaction()],
    )


def test_current_codex_summary_reuses_review_after_clean_merge_up_with_duplicate_echo() -> None:
    found = _verify_summary_merge_reuse_with_echoes()
    assert found["review_source_kind"] == "issue_comment_result"


def test_current_codex_summary_does_not_suppress_wrong_head_clean_echo() -> None:
    _v1.core_tests.expect_fail(
        lambda: _verify_summary_merge_reuse_with_echoes(echo_prefix="f" * 10)
    )


def test_current_codex_summary_does_not_suppress_post_reaction_clean_echo() -> None:
    _v1.core_tests.expect_fail(
        lambda: _verify_summary_merge_reuse_with_echoes(echo_stamp="2026-08-20T10:01:02Z")
    )


def test_current_codex_summary_does_not_suppress_blocking_clean_echo() -> None:
    _v1.core_tests.expect_fail(
        lambda: _verify_summary_merge_reuse_with_echoes(echo_extra="\n[P1] Security boundary bypass")
    )


def test_current_codex_summary_does_not_suppress_contradictory_clean_echo() -> None:
    _v1.core_tests.expect_fail(
        lambda: _verify_summary_merge_reuse_with_echoes(
            echo_first_line="Codex Review: Didn't find any major issues. Merge is unsafe."
        )
    )


def test_current_codex_summary_does_not_suppress_contradictory_echo_details() -> None:
    for extra in ("\nMerge is unsafe.", "\n[P2] Results are wrong"):
        _v1.core_tests.expect_fail(
            lambda extra=extra: _verify_summary_merge_reuse_with_echoes(echo_extra=extra)
        )


def test_current_codex_summary_rejects_multiple_same_generation_clean_echoes() -> None:
    _v1.core_tests.expect_fail(
        lambda: _verify_summary_merge_reuse_with_echoes(echo_count=2)
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
