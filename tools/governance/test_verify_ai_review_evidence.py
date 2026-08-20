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


def run_verify(comment: dict, src: dict, repo: Path, final: str, *, tier="R2", fp="abc"):
    original = m.fetch_review_source
    m.fetch_review_source = lambda repository, pr_number, source_url, token: ("pull_request_review", src)
    try:
        return m.verify_records([comment], policy=POLICY, repo_root=repo, tier=tier, fingerprint=fp,
                                head=final, repository="Oteryn/Test", pr_number=7, token="x")
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

def main() -> int:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print(f"ai review evidence tests PASS: {len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
