#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy

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
        ":tada:",
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


def _p2_review(head: str, *, review_id: int = 701,
               login: str = "chatgpt-codex-connector[bot]",
               state: str = "COMMENTED",
               body: str = "",
               submitted_at: str = "2026-08-20T10:01:00Z") -> dict:
    return {
        "id": review_id,
        "commit_id": head,
        "state": state,
        "body": body,
        "submitted_at": submitted_at,
        "user": {"login": login},
        "pull_request_url": "https://api.github.com/repos/Oteryn/Test/pulls/7",
    }


def _p2_inline(review_id: int = 701, *, login: str = "chatgpt-codex-connector[bot]",
               body: str = "[P2] Document the reusable permission contract",
               comment_id: int = 702) -> dict:
    return {
        "id": comment_id,
        "pull_request_review_id": review_id,
        "body": body,
        "created_at": "2026-08-20T10:01:00Z",
        "updated_at": "2026-08-20T10:01:00Z",
        "user": {"login": login},
        "pull_request_url": "https://api.github.com/repos/Oteryn/Test/pulls/7",
    }


def _p2_thread(*, comment_id: int = 702, resolved: bool = True, tracker: str = "Tracked in #114.",
               disposition_login: str = "blakinio",
               disposition_association: str = "MEMBER",
               disposition_edited: bool = False) -> dict:
    return {
        "id": "thread-702",
        "isResolved": resolved,
        "comments": {
            "nodes": [
                {
                    "fullDatabaseId": str(comment_id),
                    "body": "[P2] Document the reusable permission contract",
                    "author": {"login": "chatgpt-codex-connector[bot]"},
                    "authorAssociation": "NONE",
                    "createdAt": "2026-08-20T10:01:00Z",
                    "lastEditedAt": None,
                },
                {
                    "fullDatabaseId": "703",
                    "body": tracker,
                    "author": {"login": disposition_login},
                    "authorAssociation": disposition_association,
                    "createdAt": "2026-08-20T10:01:01Z",
                    "lastEditedAt": (
                        "2026-08-20T10:01:02Z" if disposition_edited else None
                    ),
                },
            ],
            "pageInfo": {"hasNextPage": False},
        },
    }


def _tracker_issue(number: int = 114) -> dict:
    return {
        "number": number,
        "state": "open",
        "repository_url": "https://api.github.com/repos/Oteryn/Test",
        "url": f"https://api.github.com/repos/Oteryn/Test/issues/{number}",
    }


def _policy() -> dict:
    policy = deepcopy(_v1.POLICY)
    policy["p2_follow_up"] = {
        "outcome": "ACCEPTED_WITH_FOLLOW_UP",
        "thread_must_be_resolved": True,
        "tracker_reply_format": "Tracked in #<issue>.",
        "tracker_must_be_open_same_repository_issue": True,
        "trusted_maintainer_associations": ["OWNER", "MEMBER", "COLLABORATOR"],
    }
    return policy


def _codex_review_envelope(head: str, *, extra: str = "") -> str:
    prefix = head[:10]
    lines = [
        "### 💡 Codex Review",
        "Here are some automated review suggestions for this pull request.",
        f"**Reviewed commit:** `{prefix}`",
        "<details> <summary>ℹ️ About Codex in GitHub</summary>",
        "<br/>",
        "[Your team has set up Codex to review pull requests in this repo]"
        "(https://chatgpt.com/codex/cloud/settings/general). Reviews are triggered when you",
        "- Open a pull request for review",
        "- Mark a draft as ready",
        '- Comment "@codex review".',
        "If Codex has suggestions, it will comment; otherwise it will react with 👍.",
        'Codex can also answer questions or update the PR. Try commenting "@codex address that feedback".',
        "</details>",
    ]
    if extra:
        lines.insert(3, extra)
    return "\n\n".join(lines)


def _verify_summary(*, summary_prefix: str | None = None,
                    completed: str = "2026-08-20T10:01:00Z",
                    trigger: str = "Manual request",
                    app_slug: str = "chatgpt-codex-connector",
                    updated: str = "2026-08-20T10:01:02Z",
                    reactions: list[dict] | None = None,
                    request_updated: str | None = None,
                    extra_reviews: list[dict] | None = None,
                    review_comments: list[dict] | None = None,
                    extra_comments: list[dict] | None = None,
                    review_threads: list[dict] | None = None,
                    tracker_issues: dict[int, dict] | None = None,
                    policy: dict | None = None) -> dict:
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
    kwargs = {
        "reviews": [_v1.core_tests.request_anchor(current, final), *(extra_reviews or [])],
        "review_comments": review_comments or [],
        "pr_reactions": [_reaction()] if reactions is None else reactions,
    }
    if review_threads is not None:
        kwargs["review_threads"] = review_threads
    if tracker_issues is not None:
        kwargs["tracker_issues"] = tracker_issues
    return _v1.m.verify_records(
        [current, summary, *(extra_comments or [])],
        policy=_policy() if policy is None else policy,
        repo_root=repo,
        tier="R2",
        fingerprint=_v1.core_tests.ISSUE_FP,
        head=final,
        repository="Oteryn/Test",
        pr_number=7,
        token="x",
        **kwargs,
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


def test_current_codex_summary_rejects_unresolved_p2_without_reaction() -> None:
    repo, _, final = _v1.core_tests.make_repo()
    _v1.core_tests.expect_fail(lambda: _verify_summary(
        reactions=[], extra_reviews=[_p2_review(final)], review_comments=[_p2_inline()],
    ))


def test_current_codex_summary_accepts_resolved_tracked_p2_without_reaction() -> None:
    repo, _, final = _v1.core_tests.make_repo()
    found = _verify_summary(
        reactions=[],
        extra_reviews=[_p2_review(final, body=_codex_review_envelope(final))],
        review_comments=[_p2_inline()],
        review_threads=[_p2_thread()],
        tracker_issues={114: _tracker_issue()},
    )
    assert found["review_source_kind"] == "issue_comment_result"
    assert found["review_outcome"] == "ACCEPTED_WITH_FOLLOW_UP"
    assert found["follow_up_issue_numbers"] == [114]


def test_current_codex_summary_ignores_inert_p2_repair_reply_before_exact_tracker() -> None:
    repo, _, final = _v1.core_tests.make_repo()
    thread = _p2_thread()
    thread["comments"]["nodes"].insert(1, {
        "fullDatabaseId": "704",
        "body": "I will repair the documentation in the next change.",
        "author": {"login": "blakinio"},
        "authorAssociation": "MEMBER",
        "createdAt": "2026-08-20T10:01:00.500Z",
        "lastEditedAt": "2026-08-20T10:01:00.750Z",
    })

    found = _verify_summary(
        reactions=[],
        extra_reviews=[_p2_review(final, body=_codex_review_envelope(final))],
        review_comments=[_p2_inline()],
        review_threads=[thread],
        tracker_issues={114: _tracker_issue()},
    )

    assert found["review_outcome"] == "ACCEPTED_WITH_FOLLOW_UP"
    assert found["follow_up_issue_numbers"] == [114]


def test_current_codex_summary_accepts_publication_timestamp_drift_for_unedited_p2() -> None:
    repo, _, final = _v1.core_tests.make_repo()
    inline = _p2_inline()
    inline["updated_at"] = "2026-08-20T10:01:02Z"

    found = _verify_summary(
        reactions=[],
        extra_reviews=[_p2_review(final, body=_codex_review_envelope(final))],
        review_comments=[inline],
        review_threads=[_p2_thread()],
        tracker_issues={114: _tracker_issue()},
    )
    assert found["review_outcome"] == "ACCEPTED_WITH_FOLLOW_UP"
    assert found["finding_comment_ids"] == [702]


def test_current_codex_summary_rejects_p2_from_unrequested_reviewer() -> None:
    repo, _, final = _v1.core_tests.make_repo()
    fast_login = "codex-spark-reviewer[bot]"
    policy = _policy()
    policy["reviewer_source_logins"] = {
        "codex": ["chatgpt-codex-connector[bot]"],
        "codex_spark": [fast_login],
    }
    thread = _p2_thread()
    thread["comments"]["nodes"][0]["author"]["login"] = fast_login

    _v1.core_tests.expect_fail(lambda: _verify_summary(
        reactions=[],
        extra_reviews=[_p2_review(
            final, login=fast_login, body=_codex_review_envelope(final),
        )],
        review_comments=[_p2_inline(login=fast_login)],
        review_threads=[thread],
        tracker_issues={114: _tracker_issue()},
        policy=policy,
    ))


def test_current_codex_summary_accepts_64_bit_graphql_comment_identity() -> None:
    repo, _, final = _v1.core_tests.make_repo()
    comment_id = 3_889_251_323
    found = _verify_summary(
        reactions=[], extra_reviews=[_p2_review(final)],
        review_comments=[_p2_inline(comment_id=comment_id)],
        review_threads=[_p2_thread(comment_id=comment_id)],
        tracker_issues={114: _tracker_issue()},
    )
    assert found["finding_comment_ids"] == [comment_id]


def test_current_codex_summary_rejects_unresolved_tracked_p2_without_reaction() -> None:
    repo, _, final = _v1.core_tests.make_repo()
    _v1.core_tests.expect_fail(lambda: _verify_summary(
        reactions=[], extra_reviews=[_p2_review(final)], review_comments=[_p2_inline()],
        review_threads=[_p2_thread(resolved=False)], tracker_issues={114: _tracker_issue()},
    ))


def test_current_codex_summary_rejects_unresolved_p2_even_with_clean_reaction() -> None:
    repo, _, final = _v1.core_tests.make_repo()
    _v1.core_tests.expect_fail(lambda: _verify_summary(
        extra_reviews=[_p2_review(final)], review_comments=[_p2_inline()],
    ))


def test_current_codex_summary_rejects_p2_outside_eligible_review_even_with_clean_reaction() -> None:
    repo, _, final = _v1.core_tests.make_repo()
    cases = [
        (_p2_review(final, state="CHANGES_REQUESTED"), _p2_inline()),
        (_p2_review(final, submitted_at="2026-08-20T10:01:01Z"), _p2_inline()),
        (_p2_review(final, review_id=703), _p2_inline(review_id=703)),
    ]
    for review, inline in cases:
        _v1.core_tests.expect_fail(lambda: _verify_summary(
            extra_reviews=[review], review_comments=[inline],
        ))


def test_current_codex_summary_rejects_ambiguous_or_top_level_p2_with_clean_reaction() -> None:
    repo, _, final = _v1.core_tests.make_repo()
    _v1.core_tests.expect_fail(lambda: _verify_summary(
        extra_reviews=[_p2_review(final), _p2_review(final, review_id=703)],
        review_comments=[_p2_inline(), _p2_inline(review_id=703)],
    ))
    top_level_p2 = _v1.core_tests.issue_comment(
        12,
        "[P2] This finding is not attached to an inline review thread",
        login="chatgpt-codex-connector[bot]",
        stamp="2026-08-20T10:01:01Z",
    )
    _v1.core_tests.expect_fail(lambda: _verify_summary(extra_comments=[top_level_p2]))


def test_current_codex_summary_allows_top_level_reviewer_text_without_finding() -> None:
    note = _v1.core_tests.issue_comment(
        12,
        "Review completed; no actionable findings in this pass.",
        login="chatgpt-codex-connector[bot]",
        stamp="2026-08-20T10:01:01Z",
    )
    found = _verify_summary(extra_comments=[note])
    assert found["review_source_kind"] == "issue_comment_result"


def test_current_codex_summary_rejects_every_top_level_finding_severity() -> None:
    finding_cases = (
        ("[P0] Critical boundary failure", "2026-08-20T10:01:01Z"),
        ("P1 Blocking correctness failure", "2026-08-20T10:01:01Z"),
        ("<sub><sub>![P2 Badge](badge)</sub></sub> Follow-up required", "2026-08-20T10:01:01Z"),
        ("- **[P3] Unknown severity must fail closed", "2026-08-20T10:00:00Z"),
        ("* <sub>![P17 Badge](badge)</sub> Escalated unknown severity", "2026-08-20T10:01:01Z"),
    )
    for comment_id, (body, stamp) in enumerate(finding_cases, start=12):
        finding = _v1.core_tests.issue_comment(
            comment_id,
            body,
            login="chatgpt-codex-connector[bot]",
            stamp=stamp,
        )
        _v1.core_tests.expect_fail(
            lambda finding=finding: _verify_summary(extra_comments=[finding])
        )


def test_current_codex_summary_rejects_unclassified_or_escalated_review_body() -> None:
    repo, _, final = _v1.core_tests.make_repo()
    for state in ("COMMENTED", "CHANGES_REQUESTED"):
        _v1.core_tests.expect_fail(lambda: _verify_summary(
            extra_reviews=[_p2_review(
                final, state=state, body="Please fix the unsafe boundary before merge."
            )],
        ))
    _v1.core_tests.expect_fail(lambda: _verify_summary(
        extra_reviews=[_p2_review(
            final, body=_codex_review_envelope(final, extra="Please fix the unsafe boundary before merge.")
        )],
    ))


def test_current_codex_summary_preserves_clean_approved_review_path() -> None:
    repo, _, final = _v1.core_tests.make_repo()
    found = _verify_summary(extra_reviews=[_p2_review(final, state="APPROVED")])
    assert found["review_source_kind"] == "issue_comment_result"
    _v1.core_tests.expect_fail(lambda: _verify_summary(
        extra_reviews=[_p2_review(
            final, state="APPROVED", body="Please fix the unsafe boundary before merge."
        )],
    ))


def test_issue_comment_clean_result_rejects_current_head_p2_without_summary() -> None:
    repo, _, final = _v1.core_tests.make_repo()
    current = _v1.core_tests.issue_comment(
        10, _v1.core_tests.request_body(final), stamp="2026-08-20T10:00:00Z",
    )
    result = _v1.core_tests.codex_result(
        11, final[:10], stamp="2026-08-20T10:01:00Z",
        text=_v1._live_clean_text(final, "Keep it up!"),
    )
    _v1.core_tests.expect_fail(lambda: _v1.m.verify_records(
        [current, result],
        policy=_policy(),
        repo_root=repo,
        tier="R2",
        fingerprint=_v1.core_tests.ISSUE_FP,
        head=final,
        repository="Oteryn/Test",
        pr_number=7,
        token="x",
        reviews=[
            _v1.core_tests.request_anchor(current, final),
            _p2_review(final),
        ],
        review_comments=[_p2_inline()],
    ))


def test_issue_comment_clean_result_rejects_unenveloped_current_head_findings() -> None:
    repo, _, final = _v1.core_tests.make_repo()
    current = _v1.core_tests.issue_comment(
        10, _v1.core_tests.request_body(final), stamp="2026-08-20T10:00:00Z",
    )
    result = _v1.core_tests.codex_result(
        11, final[:10], stamp="2026-08-20T10:01:00Z",
        text=_v1._live_clean_text(final, "Keep it up!"),
    )
    anchor = _v1.core_tests.request_anchor(current, final)
    top_level_p2 = _v1.core_tests.issue_comment(
        12, "[P2] Do not accept a top-level finding", login="chatgpt-codex-connector[bot]",
        stamp="2026-08-20T10:01:01Z",
    )
    cases = [
        ([anchor, _p2_review(final, body="Unsafe boundary before merge.")], [], [current, result]),
        ([anchor, _p2_review(final, state="CHANGES_REQUESTED", body="Unsafe boundary before merge.")], [], [current, result]),
        ([anchor, _p2_review(final, state="APPROVED", body="Unsafe boundary before merge.")], [], [current, result]),
        ([anchor, _p2_review(final)], [_p2_inline(body="Unsafe boundary before merge.")], [current, result]),
        ([anchor], [_p2_inline(review_id=999)], [current, result]),
        ([anchor], [_p2_inline(review_id=999, body="[P1] Unsafe boundary before merge.")], [current, result]),
        ([anchor], [_p2_inline(review_id=999, body="Unsafe orphan classification")], [current, result]),
        ([_p2_review("not-a-sha", review_id=999)], [_p2_inline(
            review_id=999, body="[P1] Unsafe malformed review head"
        )], [current, result]),
        ([anchor], [], [current, result, top_level_p2]),
    ]
    for reviews, review_comments, comments in cases:
        _v1.core_tests.expect_fail(lambda reviews=reviews, review_comments=review_comments, comments=comments:
            _v1.m.verify_records(
                comments,
                policy=_policy(),
                repo_root=repo,
                tier="R2",
                fingerprint=_v1.core_tests.ISSUE_FP,
                head=final,
                repository="Oteryn/Test",
                pr_number=7,
                token="x",
                reviews=reviews,
                review_comments=review_comments,
            )
        )


def test_current_codex_summary_rejects_edited_or_untrusted_p2_disposition() -> None:
    repo, _, final = _v1.core_tests.make_repo()
    for thread in (
        _p2_thread(disposition_edited=True),
        _p2_thread(disposition_association="CONTRIBUTOR"),
        _p2_thread(disposition_login=""),
    ):
        _v1.core_tests.expect_fail(lambda: _verify_summary(
            reactions=[], extra_reviews=[_p2_review(final)], review_comments=[_p2_inline()],
            review_threads=[thread], tracker_issues={114: _tracker_issue()},
        ))


def test_current_codex_summary_rejects_evidence_shaped_or_duplicate_p2_replies() -> None:
    repo, _, final = _v1.core_tests.make_repo()
    malformed_trackers = (
        "Tracked in #0.",
        "Tracked in #114. Follow-up details.",
        " Tracked in #114.",
        "Tracked in #114. ",
        "Tracked in #114.\n",
        "[P0] Critical reply",
        "[P1] Blocking reply",
        "P3 Unknown-severity reply",
    )
    for tracker in malformed_trackers:
        _v1.core_tests.expect_fail(lambda tracker=tracker: _verify_summary(
            reactions=[],
            extra_reviews=[_p2_review(final)],
            review_comments=[_p2_inline()],
            review_threads=[_p2_thread(tracker=tracker)],
            tracker_issues={114: _tracker_issue()},
        ))

    misordered = _p2_thread()
    misordered["comments"]["nodes"][1]["createdAt"] = "2026-08-20T10:01:00Z"
    _v1.core_tests.expect_fail(lambda: _verify_summary(
        reactions=[],
        extra_reviews=[_p2_review(final)],
        review_comments=[_p2_inline()],
        review_threads=[misordered],
        tracker_issues={114: _tracker_issue()},
    ))

    edited_root = _p2_thread()
    edited_root["comments"]["nodes"][0]["lastEditedAt"] = "2026-08-20T10:01:02Z"
    _v1.core_tests.expect_fail(lambda: _verify_summary(
        reactions=[],
        extra_reviews=[_p2_review(final)],
        review_comments=[_p2_inline()],
        review_threads=[edited_root],
        tracker_issues={114: _tracker_issue()},
    ))

    duplicate = _p2_thread()
    duplicate["comments"]["nodes"].append({
        "fullDatabaseId": "704",
        "body": "Tracked in #115.",
        "author": {"login": "blakinio"},
        "authorAssociation": "MEMBER",
        "createdAt": "2026-08-20T10:01:02Z",
        "lastEditedAt": None,
    })
    _v1.core_tests.expect_fail(lambda: _verify_summary(
        reactions=[],
        extra_reviews=[_p2_review(final)],
        review_comments=[_p2_inline()],
        review_threads=[duplicate],
        tracker_issues={114: _tracker_issue(), 115: _tracker_issue(115)},
    ))


def test_current_codex_summary_rejects_bad_p2_tracker_identity_or_state() -> None:
    repo, _, final = _v1.core_tests.make_repo()
    invalid_issues = []
    closed = _tracker_issue()
    closed["state"] = "closed"
    invalid_issues.append(closed)
    cross_repository = _tracker_issue()
    cross_repository["repository_url"] = "https://api.github.com/repos/Oteryn/Other"
    invalid_issues.append(cross_repository)
    pull_request = _tracker_issue()
    pull_request["pull_request"] = {}
    invalid_issues.append(pull_request)
    for issue in invalid_issues:
        _v1.core_tests.expect_fail(lambda: _verify_summary(
            reactions=[], extra_reviews=[_p2_review(final)], review_comments=[_p2_inline()],
            review_threads=[_p2_thread()], tracker_issues={114: issue},
        ))


def test_current_codex_summary_rejects_unclassified_current_generation_inline() -> None:
    repo, _, final = _v1.core_tests.make_repo()
    inline = _p2_inline(body="Please account for this review concern")
    _v1.core_tests.expect_fail(lambda: _verify_summary(
        reactions=[], extra_reviews=[_p2_review(final)], review_comments=[inline],
        review_threads=[_p2_thread()], tracker_issues={114: _tracker_issue()},
    ))


def test_current_codex_summary_rejects_orphan_blocking_inline_finding() -> None:
    for severity in ("P0", "P1"):
        _v1.core_tests.expect_fail(lambda severity=severity: _verify_summary(
            review_comments=[_p2_inline(
                review_id=999, body=f"[{severity}] Unsafe boundary before merge."
            )],
        ))
    _v1.core_tests.expect_fail(lambda: _verify_summary(
        review_comments=[_p2_inline(review_id=999, body="Unsafe orphan classification")],
    ))
    for malformed_id in (None, 701.9, True):
        _v1.core_tests.expect_fail(lambda malformed_id=malformed_id: _verify_summary(
            review_comments=[_p2_inline(
                review_id=malformed_id, body="Unsafe malformed classification"
            )],
        ))
    for malformed_head in (None, "", "not-a-sha", True):
        _v1.core_tests.expect_fail(lambda malformed_head=malformed_head: _verify_summary(
            extra_reviews=[_p2_review(malformed_head, review_id=999)],
            review_comments=[_p2_inline(review_id=999, body="[P1] Unsafe malformed review head")],
        ))


def test_current_codex_summary_rejects_p2_from_wrong_head() -> None:
    _v1.core_tests.expect_fail(
        lambda: _verify_summary(
            reactions=[],
            extra_reviews=[_p2_review("f" * 40)],
            review_comments=[_p2_inline()],
        )
    )


def test_current_codex_summary_rejects_p2_from_untrusted_reviewer() -> None:
    _v1.core_tests.expect_fail(
        lambda: _verify_summary(
            reactions=[],
            extra_reviews=[_p2_review("a" * 40, login="untrusted-bot")],
            review_comments=[_p2_inline(login="untrusted-bot")],
        )
    )


def test_current_codex_summary_rejects_p2_without_inline_finding() -> None:
    repo, _, final = _v1.core_tests.make_repo()
    _v1.core_tests.expect_fail(
        lambda: _verify_summary(reactions=[], extra_reviews=[_p2_review(final)])
    )


def test_current_codex_summary_preserves_p1_blocking_with_p2_completion() -> None:
    repo, _, final = _v1.core_tests.make_repo()
    _v1.core_tests.expect_fail(
        lambda: _verify_summary(
            reactions=[],
            extra_reviews=[_p2_review(final)],
            review_comments=[
                _p2_inline(),
                _p2_inline(review_id=701, body="[P1] Security boundary bypass"),
            ],
        )
    )


def test_current_codex_summary_rejects_p2_submitted_after_completion() -> None:
    repo, _, final = _v1.core_tests.make_repo()
    _v1.core_tests.expect_fail(
        lambda: _verify_summary(
            reactions=[],
            extra_reviews=[_p2_review(final, submitted_at="2026-08-20T10:01:01Z")],
            review_comments=[_p2_inline()],
        )
    )


def test_current_codex_summary_rejects_ambiguous_exact_p2_reviews() -> None:
    repo, _, final = _v1.core_tests.make_repo()
    _v1.core_tests.expect_fail(
        lambda: _verify_summary(
            reactions=[],
            extra_reviews=[_p2_review(final), _p2_review(final, review_id=703)],
            review_comments=[_p2_inline()],
        )
    )


def test_current_codex_summary_rejects_p2_with_ambiguous_trusted_reactions() -> None:
    repo, _, final = _v1.core_tests.make_repo()
    _v1.core_tests.expect_fail(
        lambda: _verify_summary(
            reactions=[_reaction(reaction_id=1), _reaction(reaction_id=2)],
            extra_reviews=[_p2_review(final)],
            review_comments=[_p2_inline()],
        )
    )


def test_current_codex_summary_rejects_fractional_p2_review_identity() -> None:
    repo, _, final = _v1.core_tests.make_repo()
    _v1.core_tests.expect_fail(
        lambda: _verify_summary(
            reactions=[],
            extra_reviews=[_p2_review(final)],
            review_comments=[_p2_inline(review_id=701.9)],
        )
    )


def test_current_codex_summary_rejects_fractional_p2_parent_review_identity() -> None:
    repo, _, final = _v1.core_tests.make_repo()
    _v1.core_tests.expect_fail(
        lambda: _verify_summary(
            reactions=[],
            extra_reviews=[_p2_review(final, review_id=701.9)],
            review_comments=[_p2_inline()],
        )
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
    descendant_p2: bool = False,
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
        reviews=[_v1.core_tests.request_anchor(request, reviewed), *(
            [_p2_review(final)] if descendant_p2 else []
        )],
        review_comments=[_p2_inline()] if descendant_p2 else [],
        pr_reactions=[_reaction()],
    )


def test_classic_clean_merge_up_rechecks_the_anchored_generation_for_p2() -> None:
    repo, reviewed, _ = _v1.core_tests.make_repo()
    _v1.core_tests.git(repo, "reset", "--hard", reviewed)
    _v1.core_tests.git(repo, "checkout", "-b", "task-classic-reuse")
    _v1.core_tests.git(repo, "checkout", "master")
    (repo / "upstream.py").write_text("VALUE = 1\n", encoding="utf-8")
    _v1.core_tests.git(repo, "add", ".")
    _v1.core_tests.git(repo, "commit", "-m", "independent upstream")
    integration_base = _v1.core_tests.git(repo, "rev-parse", "HEAD")
    _v1.core_tests.git(repo, "checkout", "task-classic-reuse")
    _v1.core_tests.git(repo, "merge", "--no-ff", "master", "-m", "merge current main")
    final = _v1.core_tests.git(repo, "rev-parse", "HEAD")
    request = _v1.core_tests.issue_comment(
        10, _v1.core_tests.request_body(reviewed), stamp="2026-08-20T10:00:00Z",
    )
    result = _v1.core_tests.codex_result(11, reviewed[:10], stamp="2026-08-20T10:01:00Z")
    policy = dict(_policy())
    policy["activation"] = dict(policy["activation"])
    policy["_trusted_integration_base_sha"] = integration_base
    for finding_head in (reviewed, final):
        _v1.core_tests.expect_fail(lambda finding_head=finding_head: _v1.m.verify_records(
            [request, result], policy=policy, repo_root=repo, tier="R2",
            fingerprint=_v1.core_tests.ISSUE_FP, head=final, repository="Oteryn/Test",
            pr_number=7, token="x",
            reviews=[_v1.core_tests.request_anchor(request, reviewed), _p2_review(finding_head)],
            review_comments=[_p2_inline()],
        ))


def test_current_codex_summary_reuses_review_after_clean_merge_up_with_duplicate_echo() -> None:
    found = _verify_summary_merge_reuse_with_echoes()
    assert found["review_source_kind"] == "issue_comment_result"


def test_current_codex_summary_reuses_review_after_clean_merge_up_with_tada_duplicate_echo() -> None:
    found = _verify_summary_merge_reuse_with_echoes(
        echo_first_line="Codex Review: Didn't find any major issues. :tada:"
    )
    assert found["review_source_kind"] == "issue_comment_result"


def test_current_codex_summary_reuses_review_after_clean_merge_up_with_keep_it_up_duplicate_echo() -> None:
    found = _verify_summary_merge_reuse_with_echoes(
        echo_first_line="Codex Review: Didn't find any major issues. Keep it up!"
    )
    assert found["review_source_kind"] == "issue_comment_result"


def test_current_codex_summary_reuses_review_after_clean_merge_up_with_swish_duplicate_echo() -> None:
    found = _verify_summary_merge_reuse_with_echoes(
        echo_first_line="Codex Review: Didn't find any major issues. Swish!"
    )
    assert found["review_source_kind"] == "issue_comment_result"
    assert found["review_source_url"].endswith("issuecomment-11")


def test_direct_swish_clean_result_remains_authoritative() -> None:
    repo, _, final = _v1.core_tests.make_repo()
    current = _v1.core_tests.issue_comment(
        10, _v1.core_tests.request_body(final), stamp="2026-08-20T10:00:00Z",
    )
    echo = _v1.core_tests.codex_result(
        11,
        final[:10],
        stamp="2026-08-20T10:01:00Z",
        text=_observed_duplicate_echo_body(
            final[:10],
            first_line="Codex Review: Didn't find any major issues. Swish!",
        ),
    )
    echo["performed_via_github_app"] = {"slug": "chatgpt-codex-connector"}

    found = _v1._verify_with_only_current_anchor([current, echo], repo, final, current)
    assert found["review_source_kind"] == "issue_comment_result"
    assert found["review_source_url"].endswith("issuecomment-11")


def test_all_compat_v1_direct_flairs_are_guarded_duplicate_echoes() -> None:
    for flair in (
        "Swish!",
        "Hooray!",
        "Chef's kiss.",
        "Breezy!",
        "Nice work!",
        "Bravo.",
        ":rocket:",
        "More of your lovely PRs please.",
        "You're on a roll.",
    ):
        found = _verify_summary_merge_reuse_with_echoes(
            echo_first_line=f"Codex Review: Didn't find any major issues. {flair}"
        )
        assert found["review_source_url"].endswith("issuecomment-11")


def test_duplicate_only_flairs_are_not_direct_authoritative_results() -> None:
    for flair in ("Delightful!", ":tada:"):
        repo, _, final = _v1.core_tests.make_repo()
        current = _v1.core_tests.issue_comment(
            10, _v1.core_tests.request_body(final), stamp="2026-08-20T10:00:00Z",
        )
        echo = _v1.core_tests.codex_result(
            11,
            final[:10],
            stamp="2026-08-20T10:01:00Z",
            text=_observed_duplicate_echo_body(
                final[:10],
                first_line=f"Codex Review: Didn't find any major issues. {flair}",
            ),
        )
        echo["performed_via_github_app"] = {"slug": "chatgpt-codex-connector"}
        _v1.core_tests.expect_fail(
            lambda: _v1._verify_with_only_current_anchor([current, echo], repo, final, current)
        )


def test_current_codex_summary_reuse_rejects_descendant_p2() -> None:
    _v1.core_tests.expect_fail(
        lambda: _verify_summary_merge_reuse_with_echoes(descendant_p2=True)
    )


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


def test_current_codex_summary_does_not_suppress_invalid_tada_clean_echoes() -> None:
    first_line = "Codex Review: Didn't find any major issues. :tada:"
    cases = (
        {"echo_prefix": "f" * 10},
        {"echo_stamp": "2026-08-20T10:01:02Z"},
        {"echo_extra": "\nExtra prose."},
        {"echo_extra": "\n[P1] Security boundary bypass"},
        {"echo_count": 2},
    )
    for case in cases:
        _v1.core_tests.expect_fail(
            lambda case=case: _verify_summary_merge_reuse_with_echoes(
                echo_first_line=first_line, **case
            )
        )


def test_tada_echo_requires_every_duplicate_identity_and_envelope_invariant() -> None:
    repo, reviewed, _ = _v1.core_tests.make_repo()
    summary = _summary_comment(reviewed[:10])
    request_at = _v1.m._utc_timestamp("2026-08-20T10:00:00Z")
    reaction_at = _v1.m._utc_timestamp("2026-08-20T10:01:01Z")
    assert request_at is not None and reaction_at is not None

    def observed_echo(*, prefix: str = reviewed[:10], stamp: str = "2026-08-20T10:00:59Z") -> dict:
        echo = _v1.core_tests.codex_result(
            12,
            prefix,
            stamp=stamp,
            text=_observed_duplicate_echo_body(
                prefix,
                first_line="Codex Review: Didn't find any major issues. :tada:",
            ),
        )
        echo["performed_via_github_app"] = {"slug": "chatgpt-codex-connector"}
        return echo

    def echoes(comments: list[dict]) -> list[dict]:
        return _v1.m._same_generation_clean_echoes(
            comments,
            summary=summary,
            trusted_logins={"chatgpt-codex-connector[bot]"},
            repo_root=repo,
            reviewed_head=reviewed,
            request_at=request_at,
            reaction_at=reaction_at,
            repository="Oteryn/Test",
            pr_number=7,
        )

    valid = observed_echo()
    assert echoes([summary, valid]) == [valid]

    wrong_login = observed_echo()
    wrong_login["user"]["login"] = "other-bot"
    wrong_app = observed_echo()
    wrong_app["performed_via_github_app"] = {"slug": "other-app"}
    wrong_pr = observed_echo()
    wrong_pr["issue_url"] = "https://api.github.com/repos/Oteryn/Test/issues/8"
    wrong_pr["html_url"] = "https://github.com/Oteryn/Test/pull/8#issuecomment-12"
    edited = observed_echo()
    edited["updated_at"] = "2026-08-20T10:01:00Z"
    wrong_head = observed_echo(prefix="f" * 10)
    outside_window = observed_echo(stamp="2026-08-20T10:01:02Z")
    extra_prose = observed_echo()
    extra_prose["body"] += "\nExtra prose."
    for invalid in (
        wrong_login,
        wrong_app,
        wrong_pr,
        edited,
        wrong_head,
        outside_window,
        extra_prose,
    ):
        assert echoes([summary, invalid]) == []

    finding_content = observed_echo()
    finding_content["body"] += "\n[P1] Security boundary bypass"
    _v1.core_tests.expect_fail(lambda: echoes([summary, finding_content]))

    second = observed_echo()
    second["id"] = 13
    second["html_url"] = "https://github.com/Oteryn/Test/pull/7#issuecomment-13"
    _v1.core_tests.expect_fail(lambda: echoes([summary, valid, second]))


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
