#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("verify_ai_review_evidence.py")
spec = importlib.util.spec_from_file_location("verify_ai_review_evidence", SCRIPT)
assert spec and spec.loader
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
POLICY = json.loads(
    (Path(__file__).resolve().parents[2] / "ecosystem/ai-review-policy.json").read_text(encoding="utf-8")
)


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()


def make_repo(*, non_neutral_after_review: bool = False) -> tuple[Path, str, str]:
    repo = Path(tempfile.mkdtemp(prefix="oteryn-review-evidence-"))
    git(repo, "init")
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "test")
    (repo / "a.txt").write_text("one\n", encoding="utf-8")
    git(repo, "add", "a.txt")
    git(repo, "commit", "-m", "reviewed")
    reviewed = git(repo, "rev-parse", "HEAD")
    if non_neutral_after_review:
        (repo / "a.txt").write_text("two\n", encoding="utf-8")
        git(repo, "commit", "-am", "non-neutral")
    else:
        evidence = repo / "docs/evidence/run.md"
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_text("PASS\n", encoding="utf-8")
        git(repo, "add", ".")
        git(repo, "commit", "-m", "neutral evidence")
    final = git(repo, "rev-parse", "HEAD")
    return repo, reviewed, final


def body(head: str, fp: str, *, tier="R2", klass="deep", reviewer="codex",
         source_url="https://github.com/Oteryn/Test/pull/7#pullrequestreview-9", findings="0") -> str:
    return "\n".join([
        "<!-- OTERYN_AI_REVIEW_V1 -->",
        f"REVIEW_TIER: {tier}", f"REVIEW_FINGERPRINT: {fp}", f"REVIEWED_HEAD: {head}",
        f"REVIEWER_CLASS: {klass}", f"REVIEWER_ID: {reviewer}", "RESULT: PASS",
        f"REVIEW_SOURCE_URL: {source_url}", f"FINDINGS: {findings}",
    ])

def attestation(head: str, fp: str, **kw) -> dict:
    association = kw.pop("association", "OWNER")
    attestor = kw.pop("attestor", "blakinio")
    return {"id": 1, "author_association": association, "user": {"login": attestor}, "body": body(head, fp, **kw)}


def source(head: str, fp: str, **kw) -> dict:
    login = kw.pop("login", "chatgpt-codex-connector[bot]")
    commit_id = kw.pop("commit_id", head)
    state = kw.pop("state", "COMMENTED")
    return {
        "html_url": "https://github.com/Oteryn/Test/pull/7#pullrequestreview-9",
        "pull_request_url": "https://api.github.com/repos/Oteryn/Test/pulls/7",
        "user": {"login": login},
        "commit_id": commit_id,
        "state": state,
        "body": body(head, fp, **kw),
    }


def run_verify(comment: dict, src: dict, repo: Path, final: str, *, tier="R2", fp="abc",
               comments: list[dict] | None = None,
               comment_edit_histories: dict[int, list[dict]] | None = None,
               reviews: list[dict] | None = None,
               review_comments: list[dict] | None = None):
    original = m.fetch_review_source
    m.fetch_review_source = lambda repository, pr_number, source_url, token: ("pull_request_review", src)
    try:
        return m.verify_records(
            [comment] if comments is None else comments, policy=POLICY, repo_root=repo, tier=tier, fingerprint=fp,
            head=final, repository="Oteryn/Test", pr_number=7, token="x",
            comment_edit_histories=comment_edit_histories or {},
            reviews=reviews or [], review_comments=review_comments or [],
        )
    finally:
        m.fetch_review_source = original

def expect_fail(fn) -> None:
    try:
        fn()
    except RuntimeError:
        return
    raise AssertionError("verification unexpectedly passed")


def test_matching_authenticated_source_passes() -> None:
    repo, reviewed, final = make_repo()
    found = run_verify(attestation(reviewed, "abc"), source(reviewed, "abc"), repo, final)
    assert found["review_source_author"] == "chatgpt-codex-connector[bot]"
    assert found["review_source_commit_id"] == reviewed


def test_legacy_pass_cannot_bypass_current_p1_inline_finding() -> None:
    repo, reviewed, final = make_repo()
    review = {
        "id": 777, "commit_id": reviewed, "body": "",
        "user": {"login": "chatgpt-codex-connector[bot]"},
        "pull_request_url": "https://api.github.com/repos/Oteryn/Test/pulls/7",
    }
    inline = {
        "id": 778, "pull_request_review_id": 777,
        "body": "[P1] Security boundary bypass",
        "user": {"login": "chatgpt-codex-connector[bot]"},
        "pull_request_url": "https://api.github.com/repos/Oteryn/Test/pulls/7",
    }
    expect_fail(lambda: run_verify(
        attestation(reviewed, "abc"), source(reviewed, "abc"), repo, final,
        reviews=[review], review_comments=[inline],
    ))


def test_legacy_pass_cannot_bypass_current_p1_top_level_finding() -> None:
    repo, reviewed, final = make_repo()
    legacy = attestation(reviewed, "abc")
    request = issue_comment(10, request_body(reviewed), stamp="2026-08-20T10:00:00Z")
    blocker = issue_comment(11, "[P1] Security boundary bypass",
                            login="chatgpt-codex-connector[bot]", association="NONE",
                            stamp="2026-08-20T10:01:00Z")
    expect_fail(lambda: run_verify(
        legacy, source(reviewed, "abc"), repo, final, comments=[legacy, request, blocker],
    ))


def test_legacy_pass_cannot_bypass_p1_after_edited_request() -> None:
    repo, reviewed, final = make_repo()
    legacy = attestation(reviewed, "abc")
    original = request_body(reviewed)
    request = issue_comment(10, original, stamp="2026-08-20T10:00:00Z",
                            updated_stamp="2026-08-20T10:02:00Z")
    blocker = issue_comment(11, "[P1] Security boundary bypass",
                            login="chatgpt-codex-connector[bot]", association="NONE",
                            stamp="2026-08-20T10:01:00Z")
    histories = edit_history(10, (original, "2026-08-20T10:00:00Z"),
                             (original, "2026-08-20T10:02:00Z"))
    expect_fail(lambda: run_verify(
        legacy, source(reviewed, "abc"), repo, final, comments=[legacy, request, blocker],
        comment_edit_histories=histories,
    ))


def test_legacy_pass_cannot_bypass_p1_after_request_body_removed() -> None:
    repo, reviewed, final = make_repo()
    legacy = attestation(reviewed, "abc")
    original = request_body(reviewed)
    request = issue_comment(10, "ordinary text after edit",
                            stamp="2026-08-20T10:00:00Z", updated_stamp="2026-08-20T10:02:00Z")
    blocker = issue_comment(11, "[P1] Security boundary bypass",
                            login="chatgpt-codex-connector[bot]", association="NONE",
                            stamp="2026-08-20T10:01:00Z")
    histories = edit_history(10, (original, "2026-08-20T10:00:00Z"),
                             ("ordinary text after edit", "2026-08-20T10:02:00Z"))
    expect_fail(lambda: run_verify(
        legacy, source(reviewed, "abc"), repo, final, comments=[legacy, request, blocker],
        comment_edit_histories=histories,
    ))


def test_self_authored_external_source_fails() -> None:
    repo, reviewed, final = make_repo()
    expect_fail(lambda: run_verify(attestation(reviewed, "abc"), source(reviewed, "abc", login="blakinio"), repo, final))


def test_untrusted_source_author_fails() -> None:
    repo, reviewed, final = make_repo()
    expect_fail(lambda: run_verify(attestation(reviewed, "abc"), source(reviewed, "abc", login="evil-bot"), repo, final))


def test_source_body_mismatch_fails() -> None:
    repo, reviewed, final = make_repo()
    expect_fail(lambda: run_verify(attestation(reviewed, "abc"), source(reviewed, "wrong"), repo, final))

def test_untrusted_attestor_fails() -> None:
    repo, reviewed, final = make_repo()
    expect_fail(lambda: run_verify(attestation(reviewed, "abc", association="NONE"), source(reviewed, "abc"), repo, final))


def test_spark_cannot_satisfy_r2() -> None:
    repo, reviewed, final = make_repo()
    c = attestation(reviewed, "abc", reviewer="codex_spark")
    s = source(reviewed, "abc", reviewer="codex_spark")
    expect_fail(lambda: run_verify(c, s, repo, final))


def test_deep_codex_can_satisfy_r1() -> None:
    repo, reviewed, final = make_repo()
    c = attestation(reviewed, "abc", tier="R1", klass="deep")
    s = source(reviewed, "abc", tier="R1", klass="deep")
    assert run_verify(c, s, repo, final, tier="R1")["reviewer_id"] == "codex"


def test_duplicate_fields_are_rejected() -> None:
    text = body("a" * 40, "abc") + "\nRESULT: PASS"
    assert m.parse_record(text) is None


def test_wrong_server_commit_id_fails() -> None:
    repo, reviewed, final = make_repo()
    expect_fail(lambda: run_verify(attestation(reviewed, "abc"), source(reviewed, "abc", commit_id="f" * 40), repo, final))

def test_dismissed_review_fails() -> None:
    repo, reviewed, final = make_repo()
    expect_fail(lambda: run_verify(attestation(reviewed, "abc"), source(reviewed, "abc", state="DISMISSED"), repo, final))


def test_nonzero_findings_fail() -> None:
    repo, reviewed, final = make_repo()
    expect_fail(lambda: run_verify(attestation(reviewed, "abc"), source(reviewed, "abc", findings="1"), repo, final))


def test_non_neutral_post_review_commit_fails() -> None:
    repo, reviewed, final = make_repo(non_neutral_after_review=True)
    expect_fail(lambda: run_verify(attestation(reviewed, "abc"), source(reviewed, "abc"), repo, final))


def test_source_url_must_be_exact_same_pr_review() -> None:
    urls = [
        "https://github.com/Oteryn/Test/pull/7#issuecomment-9",
        "https://github.com/Oteryn/Test/pull/7x#pullrequestreview-9",
        "https://github.com/Oteryn/Test/pull/8#pullrequestreview-9",
        "https://github.com/Oteryn/Test/pull/7#pullrequestreview-9/evil",
    ]
    for url in urls:
        try:
            m.fetch_review_source("Oteryn/Test", 7, url, "x")
        except RuntimeError:
            continue
        raise AssertionError(url)


def test_nonexistent_review_source_fails_closed() -> None:
    original = m.fetch_json
    m.fetch_json = lambda url, token: (_ for _ in ()).throw(RuntimeError("404"))
    try:
        try:
            m.fetch_review_source("Oteryn/Test", 7, "https://github.com/Oteryn/Test/pull/7#pullrequestreview-9", "x")
        except RuntimeError:
            return
        raise AssertionError("missing review unexpectedly fetched")
    finally:
        m.fetch_json = original



def test_merge_commit_after_review_fails_even_when_paths_are_neutral() -> None:
    repo, reviewed, _ = make_repo()
    git(repo, "reset", "--hard", reviewed)
    git(repo, "checkout", "-b", "side")
    f = repo / "docs/evidence/side.md"; f.parent.mkdir(parents=True, exist_ok=True); f.write_text("side\n", encoding="utf-8")
    git(repo, "add", "."); git(repo, "commit", "-m", "side evidence")
    git(repo, "checkout", "master")
    f = repo / "docs/evidence/main.md"; f.parent.mkdir(parents=True, exist_ok=True); f.write_text("main\n", encoding="utf-8")
    git(repo, "add", "."); git(repo, "commit", "-m", "main evidence")
    git(repo, "merge", "--no-ff", "side", "-m", "merge evidence")
    final = git(repo, "rev-parse", "HEAD")
    expect_fail(lambda: run_verify(attestation(reviewed, "abc"), source(reviewed, "abc"), repo, final))


ISSUE_FP = "f" * 64


def request_body(head: str, fp: str = ISSUE_FP, *, tier: str = "R2",
                 klass: str = "deep", reviewer: str = "codex") -> str:
    return "\n".join([
        "@codex review", "", m.REQUEST_MARKER,
        f"REVIEW_TIER: {tier}",
        f"REVIEW_FINGERPRINT: {fp}",
        f"REVIEWED_HEAD: {head}",
        f"REVIEWER_CLASS: {klass}",
        f"REVIEWER_ID: {reviewer}",
    ])


def issue_comment(comment_id: int, text: str, *, login: str = "blakinio",
                  association: str = "OWNER", stamp: str = "2026-08-20T10:00:00Z",
                  updated_stamp: str | None = None,
                  repository: str = "Oteryn/Test", pr: int = 7) -> dict:
    return {
        "id": comment_id, "node_id": f"IC_TEST_{comment_id}",
        "body": text, "created_at": stamp,
        "updated_at": stamp if updated_stamp is None else updated_stamp,
        "author_association": association, "user": {"login": login},
        "issue_url": f"https://api.github.com/repos/{repository}/issues/{pr}",
        "html_url": f"https://github.com/{repository}/pull/{pr}#issuecomment-{comment_id}",
    }


def edit_history(comment_id: int, *versions: tuple[str, str]) -> dict[int, list[dict]]:
    return {
        comment_id: [
            {"body": body, "edited_at": edited_at}
            for body, edited_at in versions
        ]
    }


def codex_result(comment_id: int, prefix: str, *,
                 login: str = "chatgpt-codex-connector[bot]",
                 stamp: str = "2026-08-20T10:01:00Z",
                 repository: str = "Oteryn/Test", pr: int = 7,
                 text: str | None = None) -> dict:
    body_text = text if text is not None else (
        "Codex Review: Didn't find any major issues. What shall we delve into next?\n\n"
        f"**Reviewed commit:** `{prefix}`\n\n"
        "<details> <summary>?? About Codex in GitHub</summary>\n"
        "standard Codex review wrapper\n"
        "</details>"
    )
    return issue_comment(
        comment_id, body_text, login=login, association="NONE", stamp=stamp,
        repository=repository, pr=pr,
    )


def codex_review(review_id: int, head: str, *, body_text: str = "") -> dict:
    return {
        "id": review_id, "commit_id": head, "body": body_text,
        "user": {"login": "chatgpt-codex-connector[bot]"},
        "pull_request_url": "https://api.github.com/repos/Oteryn/Test/pulls/7",
    }


def codex_inline(review_id: int, text: str) -> dict:
    return {
        "id": review_id + 1000, "pull_request_review_id": review_id,
        "body": text, "user": {"login": "chatgpt-codex-connector[bot]"},
        "pull_request_url": "https://api.github.com/repos/Oteryn/Test/pulls/7",
    }


def run_issue(comments: list[dict], repo: Path, final: str, *, fp: str = ISSUE_FP,
              tier: str = "R2",
              comment_edit_histories: dict[int, list[dict]] | None = None,
              reviews: list[dict] | None = None,
              review_comments: list[dict] | None = None) -> dict:
    original = m.fetch_review_source
    m.fetch_review_source = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("missing"))
    try:
        return m.verify_records(
            comments, policy=POLICY, repo_root=repo, tier=tier, fingerprint=fp,
            head=final, repository="Oteryn/Test", pr_number=7, token="x",
            comment_edit_histories=comment_edit_histories or {},
            reviews=reviews or [], review_comments=review_comments or [],
        )
    finally:
        m.fetch_review_source = original


def valid_issue_pair(repo: Path, head: str) -> list[dict]:
    return [issue_comment(10, request_body(head)), codex_result(11, head[:10])]


def test_issue_comment_clean_result_pair_passes() -> None:
    repo, _, final = make_repo()
    found = run_issue(valid_issue_pair(repo, final), repo, final)
    assert found["review_source_kind"] == "issue_comment_result"
    assert found["review_source_commit_id"] == final


def test_issue_comment_wrong_bot_author_fails() -> None:
    repo, _, final = make_repo()
    comments = [issue_comment(10, request_body(final)), codex_result(11, final[:10], login="evil-bot")]
    expect_fail(lambda: run_issue(comments, repo, final))


def test_issue_comment_wrong_repository_fails() -> None:
    repo, _, final = make_repo()
    comments = [issue_comment(10, request_body(final), repository="Oteryn/Other"),
                codex_result(11, final[:10], repository="Oteryn/Other")]
    expect_fail(lambda: run_issue(comments, repo, final))


def test_issue_comment_wrong_pr_fails() -> None:
    repo, _, final = make_repo()
    comments = [issue_comment(10, request_body(final), pr=8), codex_result(11, final[:10], pr=8)]
    expect_fail(lambda: run_issue(comments, repo, final))


def test_issue_comment_stale_reviewed_head_fails() -> None:
    repo, reviewed, final = make_repo(non_neutral_after_review=True)
    comments = [issue_comment(10, request_body(reviewed)), codex_result(11, reviewed[:10])]
    expect_fail(lambda: run_issue(comments, repo, final))


def test_issue_comment_short_sha_wrong_head_fails() -> None:
    repo, reviewed, final = make_repo()
    comments = [issue_comment(10, request_body(final)), codex_result(11, reviewed[:10])]
    expect_fail(lambda: run_issue(comments, repo, final))


def test_issue_comment_ambiguous_short_sha_fails() -> None:
    repo, _, final = make_repo()
    original = m.resolve_reviewed_prefix
    m.resolve_reviewed_prefix = lambda repo_root, prefix: None
    try:
        expect_fail(lambda: run_issue(valid_issue_pair(repo, final), repo, final))
    finally:
        m.resolve_reviewed_prefix = original


def test_issue_comment_wrong_fingerprint_fails() -> None:
    repo, _, final = make_repo()
    comments = [issue_comment(10, request_body(final, "e" * 64)), codex_result(11, final[:10])]
    expect_fail(lambda: run_issue(comments, repo, final))


def test_issue_comment_wrong_tier_fails() -> None:
    repo, _, final = make_repo()
    comments = [issue_comment(10, request_body(final, tier="R1", klass="deep")), codex_result(11, final[:10])]
    expect_fail(lambda: run_issue(comments, repo, final))


def test_issue_comment_wrong_reviewer_class_fails() -> None:
    repo, _, final = make_repo()
    comments = [issue_comment(10, request_body(final, klass="fast")), codex_result(11, final[:10])]
    expect_fail(lambda: run_issue(comments, repo, final))


def test_issue_comment_edited_request_fails() -> None:
    repo, _, final = make_repo()
    request = issue_comment(10, request_body(final), updated_stamp="2026-08-20T10:02:00Z")
    comments = [request, codex_result(11, final[:10], stamp="2026-08-20T10:01:00Z")]
    expect_fail(lambda: run_issue(comments, repo, final))


def test_issue_comment_delayed_older_fingerprint_same_head_fails() -> None:
    repo, _, final = make_repo()
    comments = [
        issue_comment(10, request_body(final, "e" * 64), stamp="2026-08-20T10:00:00Z"),
        issue_comment(11, request_body(final), stamp="2026-08-20T10:01:00Z"),
        codex_result(12, final[:10], stamp="2026-08-20T10:02:00Z"),
    ]
    expect_fail(lambda: run_issue(comments, repo, final))


def test_issue_comment_delayed_fast_result_cannot_satisfy_deep_same_head() -> None:
    repo, _, final = make_repo()
    comments = [
        issue_comment(10, request_body(final, "e" * 64, tier="R1", klass="fast", reviewer="codex_spark"),
                      stamp="2026-08-20T10:00:00Z"),
        issue_comment(11, request_body(final), stamp="2026-08-20T10:01:00Z"),
        codex_result(12, final[:10], stamp="2026-08-20T10:02:00Z"),
    ]
    expect_fail(lambda: run_issue(comments, repo, final))


def test_issue_comment_edited_same_head_request_remains_ambiguous() -> None:
    repo, _, final = make_repo()
    old_request = request_body(final, "e" * 64, tier="R1", klass="fast", reviewer="codex_spark")
    edited = issue_comment(10, old_request, stamp="2026-08-20T10:00:00Z",
                           updated_stamp="2026-08-20T10:00:30Z")
    comments = [
        edited,
        issue_comment(11, request_body(final), stamp="2026-08-20T10:01:00Z"),
        codex_result(12, final[:10], stamp="2026-08-20T10:02:00Z"),
    ]
    histories = edit_history(10, (old_request, "2026-08-20T10:00:00Z"),
                             (old_request, "2026-08-20T10:00:30Z"))
    expect_fail(lambda: run_issue(
        comments, repo, final, comment_edit_histories=histories
    ))


def test_issue_comment_removed_request_body_remains_ambiguous() -> None:
    repo, _, final = make_repo()
    old_request = request_body(final, "e" * 64, tier="R1", klass="fast", reviewer="codex_spark")
    edited = issue_comment(10, "ordinary text after edit", stamp="2026-08-20T10:00:00Z",
                           updated_stamp="2026-08-20T10:00:30Z")
    comments = [
        edited,
        issue_comment(11, request_body(final), stamp="2026-08-20T10:01:00Z"),
        codex_result(12, final[:10], stamp="2026-08-20T10:02:00Z"),
    ]
    histories = edit_history(10, (old_request, "2026-08-20T10:00:00Z"),
                             ("ordinary text after edit", "2026-08-20T10:00:30Z"))
    expect_fail(lambda: run_issue(
        comments, repo, final, comment_edit_histories=histories
    ))


def test_issue_comment_unrelated_edit_history_does_not_poison_pass() -> None:
    repo, _, final = make_repo()
    edited = issue_comment(9, "ordinary edited prose", stamp="2026-08-20T09:00:00Z",
                           updated_stamp="2026-08-20T09:01:00Z")
    comments = [edited, issue_comment(10, request_body(final)), codex_result(11, final[:10])]
    histories = edit_history(9, ("ordinary original prose", "2026-08-20T09:00:00Z"),
                             ("ordinary edited prose", "2026-08-20T09:01:00Z"))
    found = run_issue(comments, repo, final, comment_edit_histories=histories)
    assert found["review_source_kind"] == "issue_comment_result"


def test_issue_comment_missing_edited_history_fails_closed() -> None:
    repo, _, final = make_repo()
    edited = issue_comment(9, "ordinary edited prose", stamp="2026-08-20T09:00:00Z",
                           updated_stamp="2026-08-20T09:01:00Z")
    comments = [edited, issue_comment(10, request_body(final)), codex_result(11, final[:10])]
    expect_fail(lambda: run_issue(comments, repo, final))


def test_issue_comment_request_after_result_fails() -> None:
    repo, _, final = make_repo()
    comments = [codex_result(11, final[:10], stamp="2026-08-20T10:00:00Z"),
                issue_comment(10, request_body(final), stamp="2026-08-20T10:01:00Z")]
    expect_fail(lambda: run_issue(comments, repo, final))


def test_issue_comment_two_competing_matching_requests_fail() -> None:
    repo, _, final = make_repo()
    comments = [issue_comment(10, request_body(final), stamp="2026-08-20T10:00:00Z"),
                issue_comment(12, request_body(final), stamp="2026-08-20T10:01:00Z"),
                codex_result(13, final[:10], stamp="2026-08-20T10:02:00Z")]
    expect_fail(lambda: run_issue(comments, repo, final))


def test_issue_comment_stale_result_followed_by_new_request_fails() -> None:
    repo, _, final = make_repo()
    comments = [
        issue_comment(10, request_body(final), stamp="2026-08-20T10:00:00Z"),
        codex_result(11, final[:10], stamp="2026-08-20T10:01:00Z"),
        issue_comment(12, request_body(final, "e" * 64), stamp="2026-08-20T10:02:00Z"),
    ]
    expect_fail(lambda: run_issue(comments, repo, final))


def test_issue_comment_p1_inline_finding_fails() -> None:
    repo, _, final = make_repo()
    reviews = [codex_review(90, final)]
    inline = [codex_inline(90, "P1 Badge security issue")]
    expect_fail(lambda: run_issue(valid_issue_pair(repo, final), repo, final,
                                  reviews=reviews, review_comments=inline))


def test_issue_comment_bracketed_p1_inline_finding_fails() -> None:
    repo, _, final = make_repo()
    reviews = [codex_review(92, final)]
    inline = [codex_inline(92, "[P1] Security boundary bypass")]
    expect_fail(lambda: run_issue(valid_issue_pair(repo, final), repo, final,
                                  reviews=reviews, review_comments=inline))


def test_issue_comment_standard_badge_p1_inline_finding_fails() -> None:
    repo, _, final = make_repo()
    reviews = [codex_review(93, final)]
    inline = [codex_inline(93, "**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Security boundary bypass**")]
    expect_fail(lambda: run_issue(valid_issue_pair(repo, final), repo, final,
                                  reviews=reviews, review_comments=inline))


def test_issue_comment_p0_inline_finding_fails() -> None:
    repo, _, final = make_repo()
    reviews = [codex_review(91, final)]
    inline = [codex_inline(91, "P0 Critical trust bypass")]
    expect_fail(lambda: run_issue(valid_issue_pair(repo, final), repo, final,
                                  reviews=reviews, review_comments=inline))


def test_maintainer_clean_result_text_fails() -> None:
    repo, _, final = make_repo()
    fake = codex_result(11, final[:10], login="blakinio")
    fake["author_association"] = "OWNER"
    comments = [issue_comment(10, request_body(final)), fake]
    expect_fail(lambda: run_issue(comments, repo, final))


def test_maintainer_structured_pass_fails_without_external_source() -> None:
    repo, _, final = make_repo()
    comments = [attestation(final, ISSUE_FP)]
    expect_fail(lambda: run_issue(comments, repo, final))


def test_issue_comment_cross_pr_replay_fails() -> None:
    repo, _, final = make_repo()
    comments = [issue_comment(10, request_body(final), pr=99), codex_result(11, final[:10], pr=99)]
    expect_fail(lambda: run_issue(comments, repo, final))


def test_issue_comment_cross_repository_replay_fails() -> None:
    repo, _, final = make_repo()
    comments = [issue_comment(10, request_body(final), repository="Elsewhere/Test"),
                codex_result(11, final[:10], repository="Elsewhere/Test")]
    expect_fail(lambda: run_issue(comments, repo, final))


def test_issue_comment_missing_result_source_fails() -> None:
    repo, _, final = make_repo()
    comments = [issue_comment(10, request_body(final))]
    expect_fail(lambda: run_issue(comments, repo, final))


def test_issue_comment_malformed_request_fails() -> None:
    repo, _, final = make_repo()
    malformed = "@codex review\n\n" + m.REQUEST_MARKER + f"\nREVIEWED_HEAD: {final}"
    comments = [issue_comment(10, malformed), codex_result(11, final[:10])]
    expect_fail(lambda: run_issue(comments, repo, final))


def test_issue_comment_malformed_result_fails() -> None:
    repo, _, final = make_repo()
    malformed = "Codex Review: Didn't find any major issues.\n\n**Reviewed commit:** `not-a-sha`"
    comments = [issue_comment(10, request_body(final)), codex_result(11, final[:10], text=malformed)]
    expect_fail(lambda: run_issue(comments, repo, final))


def test_issue_comment_unexpected_result_tail_fails() -> None:
    repo, _, final = make_repo()
    malformed = (
        "Codex Review: Didn't find any major issues.\n\n"
        f"**Reviewed commit:** `{final[:10]}`\n\nuntrusted-shaped trailing prose"
    )
    comments = [issue_comment(10, request_body(final)), codex_result(11, final[:10], text=malformed)]
    expect_fail(lambda: run_issue(comments, repo, final))


def test_issue_comment_duplicate_structured_fields_fail() -> None:
    repo, _, final = make_repo()
    duplicate = request_body(final) + "\nREVIEW_TIER: R2"
    comments = [issue_comment(10, duplicate), codex_result(11, final[:10])]
    expect_fail(lambda: run_issue(comments, repo, final))


def test_issue_comment_post_review_non_neutral_commit_fails() -> None:
    repo, reviewed, final = make_repo(non_neutral_after_review=True)
    comments = [issue_comment(10, request_body(reviewed)), codex_result(11, reviewed[:10])]
    expect_fail(lambda: run_issue(comments, repo, final))


def test_issue_comment_old_fingerprint_result_fails() -> None:
    repo, _, final = make_repo()
    comments = [issue_comment(10, request_body(final, "0" * 64)), codex_result(11, final[:10])]
    expect_fail(lambda: run_issue(comments, repo, final))


def test_issue_comment_different_reviewed_head_fails() -> None:
    repo, reviewed, final = make_repo()
    comments = [issue_comment(10, request_body(final)), codex_result(11, reviewed[:10])]
    expect_fail(lambda: run_issue(comments, repo, final))


def test_issue_comment_untrusted_request_author_fails() -> None:
    repo, _, final = make_repo()
    request = issue_comment(10, request_body(final), association="NONE", login="outsider")
    comments = [request, codex_result(11, final[:10])]
    expect_fail(lambda: run_issue(comments, repo, final))


def test_issue_comment_multiple_trusted_results_fail() -> None:
    repo, _, final = make_repo()
    comments = [
        issue_comment(10, request_body(final), stamp="2026-08-20T10:00:00Z"),
        codex_result(11, final[:10], stamp="2026-08-20T10:01:00Z"),
        codex_result(12, final[:10], stamp="2026-08-20T10:02:00Z"),
    ]
    expect_fail(lambda: run_issue(comments, repo, final))


def test_issue_comment_merge_commit_after_review_fails() -> None:
    repo, reviewed, _ = make_repo()
    git(repo, "reset", "--hard", reviewed)
    git(repo, "checkout", "-b", "side2")
    side = repo / "docs/evidence/side2.md"
    side.parent.mkdir(parents=True, exist_ok=True); side.write_text("side\n", encoding="utf-8")
    git(repo, "add", "."); git(repo, "commit", "-m", "side evidence")
    git(repo, "checkout", "master")
    main_file = repo / "docs/evidence/main2.md"
    main_file.parent.mkdir(parents=True, exist_ok=True); main_file.write_text("main\n", encoding="utf-8")
    git(repo, "add", "."); git(repo, "commit", "-m", "main evidence")
    git(repo, "merge", "--no-ff", "side2", "-m", "merge evidence")
    final = git(repo, "rev-parse", "HEAD")
    comments = [issue_comment(10, request_body(reviewed)), codex_result(11, reviewed[:10])]
    expect_fail(lambda: run_issue(comments, repo, final))


def test_issue_comment_wrong_reviewer_identity_fails() -> None:
    repo, _, final = make_repo()
    comments = [issue_comment(10, request_body(final, reviewer="codex_spark")),
                codex_result(11, final[:10])]
    expect_fail(lambda: run_issue(comments, repo, final))


def test_issue_comment_p1_top_level_bot_finding_fails() -> None:
    repo, _, final = make_repo()
    comments = [issue_comment(10, request_body(final)),
                issue_comment(11, "P1 Security finding", login="chatgpt-codex-connector[bot]",
                              association="NONE", stamp="2026-08-20T10:00:30Z"),
                codex_result(12, final[:10], stamp="2026-08-20T10:01:00Z")]
    expect_fail(lambda: run_issue(comments, repo, final))

def test_fetch_comment_edit_history_binds_server_identity() -> None:
    comment = issue_comment(77, "ordinary edited text", stamp="2026-08-20T10:00:00Z",
                            updated_stamp="2026-08-20T10:01:00Z")
    original = m.fetch_graphql
    m.fetch_graphql = lambda query, variables, token: {
        "node": {
            "databaseId": 77,
            "url": comment["html_url"],
            "body": comment["body"],
            "createdAt": comment["created_at"],
            "updatedAt": comment["updated_at"],
            "includesCreatedEdit": True,
            "issue": {"number": 7, "repository": {"nameWithOwner": "Oteryn/Test"}},
            "userContentEdits": {
                "nodes": [
                    {"diff": comment["body"], "editedAt": "2026-08-20T10:01:00Z",
                     "editor": {"login": "blakinio"}},
                    {"diff": "original text", "editedAt": "2026-08-20T10:00:00Z",
                     "editor": {"login": "blakinio"}},
                ],
                "pageInfo": {"hasNextPage": False},
            },
        }
    }
    try:
        history = m.fetch_comment_edit_history("Oteryn/Test", 7, comment, "x")
        assert {item["body"] for item in history} == {"ordinary edited text", "original text"}
    finally:
        m.fetch_graphql = original


def test_fetch_comment_edit_history_rejects_cross_repository_node() -> None:
    comment = issue_comment(78, "ordinary edited text", stamp="2026-08-20T10:00:00Z",
                            updated_stamp="2026-08-20T10:01:00Z")
    original = m.fetch_graphql
    m.fetch_graphql = lambda query, variables, token: {
        "node": {
            "databaseId": 78, "url": comment["html_url"], "body": comment["body"],
            "createdAt": comment["created_at"], "updatedAt": comment["updated_at"],
            "includesCreatedEdit": True,
            "issue": {"number": 7, "repository": {"nameWithOwner": "Other/Repo"}},
            "userContentEdits": {"nodes": [{"diff": comment["body"],
                "editedAt": "2026-08-20T10:01:00Z", "editor": {"login": "blakinio"}}],
                "pageInfo": {"hasNextPage": False}},
        }
    }
    try:
        expect_fail(lambda: m.fetch_comment_edit_history("Oteryn/Test", 7, comment, "x"))
    finally:
        m.fetch_graphql = original


def test_fetch_comment_edit_history_rejects_truncation() -> None:
    comment = issue_comment(79, "ordinary edited text", stamp="2026-08-20T10:00:00Z",
                            updated_stamp="2026-08-20T10:01:00Z")
    original = m.fetch_graphql
    m.fetch_graphql = lambda query, variables, token: {
        "node": {
            "databaseId": 79, "url": comment["html_url"], "body": comment["body"],
            "createdAt": comment["created_at"], "updatedAt": comment["updated_at"],
            "includesCreatedEdit": True,
            "issue": {"number": 7, "repository": {"nameWithOwner": "Oteryn/Test"}},
            "userContentEdits": {"nodes": [{"diff": comment["body"],
                "editedAt": "2026-08-20T10:01:00Z", "editor": {"login": "blakinio"}}],
                "pageInfo": {"hasNextPage": True}},
        }
    }
    try:
        expect_fail(lambda: m.fetch_comment_edit_history("Oteryn/Test", 7, comment, "x"))
    finally:
        m.fetch_graphql = original


def main() -> int:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print(f"ai review evidence tests PASS: {len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
