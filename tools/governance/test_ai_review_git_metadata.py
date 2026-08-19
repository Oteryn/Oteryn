#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("ai_review_policy.py")
spec = importlib.util.spec_from_file_location("ai_review_policy", SCRIPT)
assert spec and spec.loader
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()


def make_repo() -> tuple[Path, str]:
    repo = Path(tempfile.mkdtemp(prefix="oteryn-git-metadata-risk-"))
    git(repo, "init")
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "test")
    evidence = repo / "docs/evidence/run.md"
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text("ok\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "base")
    return repo, git(repo, "rev-parse", "HEAD")


def test_executable_mode_is_risk_bearing() -> None:
    repo, base = make_repo()
    git(repo, "update-index", "--chmod=+x", "docs/evidence/run.md")
    git(repo, "commit", "-m", "make evidence executable")
    head = git(repo, "rev-parse", "HEAD")
    result = m.evaluate(base, head, repo, m.DEFAULT_POLICY)
    assert result["tier"] == "R1"
    assert "docs/evidence/run.md" in result["risk_bearing_paths"]
    assert "docs/evidence/run.md" not in result["review_neutral_paths"]


def test_symlink_mode_is_risk_bearing() -> None:
    repo, base = make_repo()
    path = repo / "docs/evidence/link.md"
    path.symlink_to("../run.md")
    git(repo, "add", "docs/evidence/link.md")
    git(repo, "commit", "-m", "add evidence symlink")
    head = git(repo, "rev-parse", "HEAD")
    result = m.evaluate(base, head, repo, m.DEFAULT_POLICY)
    assert result["tier"] == "R1"
    assert "docs/evidence/link.md" in result["risk_bearing_paths"]
    assert "docs/evidence/link.md" not in result["review_neutral_paths"]


def test_gitlink_mode_is_risk_bearing() -> None:
    repo, base = make_repo()
    git(repo, "update-index", "--add", "--cacheinfo", f"160000,{base},docs/evidence/submodule.md")
    git(repo, "commit", "-m", "add evidence gitlink")
    head = git(repo, "rev-parse", "HEAD")
    result = m.evaluate(base, head, repo, m.DEFAULT_POLICY)
    assert result["tier"] == "R1"
    assert "docs/evidence/submodule.md" in result["risk_bearing_paths"]
    assert "docs/evidence/submodule.md" not in result["review_neutral_paths"]


def main() -> int:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print(f"ai review git metadata tests PASS: {len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
