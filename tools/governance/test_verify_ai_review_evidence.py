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
POLICY = json.loads((Path(__file__).resolve().parents[2] / "ecosystem/ai-review-policy.json").read_text(encoding="utf-8"))


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()


def make_repo() -> tuple[Path, str, str]:
    repo = Path(tempfile.mkdtemp(prefix="oteryn-review-evidence-"))
    git(repo, "init")
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "test")
    (repo / "a.txt").write_text("one\n", encoding="utf-8")
    git(repo, "add", "a.txt")
    git(repo, "commit", "-m", "one")
    first = git(repo, "rev-parse", "HEAD")
    (repo / "a.txt").write_text("two\n", encoding="utf-8")
    git(repo, "commit", "-am", "two")
    second = git(repo, "rev-parse", "HEAD")
    return repo, first, second


def record(head: str, fingerprint: str, *, association: str = "OWNER", reviewer: str = "codex") -> dict:
    body = "\n".join([
        "<!-- OTERYN_AI_REVIEW_V1 -->",
        "REVIEW_TIER: R2",
        f"REVIEW_FINGERPRINT: {fingerprint}",
        f"REVIEWED_HEAD: {head}",
        "REVIEWER_CLASS: deep",
        f"REVIEWER_ID: {reviewer}",
        "RESULT: PASS",
        "REVIEW_SOURCE_URL: https://github.com/Oteryn/Test/pull/7#pullrequestreview-1",
        "FINDINGS: 0",
    ])
    return {"id": 1, "author_association": association, "body": body}


def test_matching_record_passes() -> None:
    repo, reviewed, final = make_repo()
    found = m.verify_records([record(reviewed, "abc")], policy=POLICY, repo_root=repo, tier="R2", fingerprint="abc", head=final, repository="Oteryn/Test", pr_number=7)
    assert found["reviewed_head"] == reviewed


def test_untrusted_author_fails() -> None:
    repo, reviewed, final = make_repo()
    try:
        m.verify_records([record(reviewed, "abc", association="NONE")], policy=POLICY, repo_root=repo, tier="R2", fingerprint="abc", head=final, repository="Oteryn/Test", pr_number=7)
    except RuntimeError:
        return
    raise AssertionError("untrusted review record unexpectedly passed")


def test_deep_reviewer_satisfies_fast_requirement() -> None:
    repo, reviewed, final = make_repo()
    comment = record(reviewed, "abc", reviewer="codex")
    comment["body"] = comment["body"].replace("REVIEW_TIER: R2", "REVIEW_TIER: R1").replace("REVIEWER_CLASS: deep", "REVIEWER_CLASS: deep")
    found = m.verify_records([comment], policy=POLICY, repo_root=repo, tier="R1", fingerprint="abc", head=final, repository="Oteryn/Test", pr_number=7)
    assert found["reviewer_id"] == "codex"


def test_wrong_reviewer_class_fails() -> None:
    repo, reviewed, final = make_repo()
    try:
        m.verify_records([record(reviewed, "abc", reviewer="codex_spark")], policy=POLICY, repo_root=repo, tier="R2", fingerprint="abc", head=final, repository="Oteryn/Test", pr_number=7)
    except RuntimeError:
        return
    raise AssertionError("Spark unexpectedly satisfied deep R2")


def main() -> int:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print(f"ai review evidence tests PASS: {len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
