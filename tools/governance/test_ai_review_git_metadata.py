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


def commit(repo: Path, message: str) -> str:
    git(repo, "add", "-A")
    git(repo, "commit", "-m", message)
    return git(repo, "rev-parse", "HEAD")


def make_repo() -> tuple[Path, str]:
    repo = Path(tempfile.mkdtemp(prefix="oteryn-git-metadata-risk-"))
    git(repo, "init")
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "test")
    evidence = repo / "docs/evidence/run.md"
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text("ok\n", encoding="utf-8")
    base = commit(repo, "base")
    return repo, base


def assert_risk_bearing(repo: Path, base: str, head: str, path: str, tier: str = "R1") -> None:
    result = m.evaluate(base, head, repo, m.DEFAULT_POLICY)
    assert result["tier"] == tier, result
    assert path in result["risk_bearing_paths"], result
    assert path not in result["review_neutral_paths"], result


def test_executable_mode_is_risk_bearing() -> None:
    repo, base = make_repo()
    git(repo, "update-index", "--chmod=+x", "docs/evidence/run.md")
    head = commit(repo, "make evidence executable")
    assert_risk_bearing(repo, base, head, "docs/evidence/run.md")


def test_existing_executable_content_change_is_risk_bearing() -> None:
    repo, _ = make_repo()
    git(repo, "update-index", "--chmod=+x", "docs/evidence/run.md")
    base = commit(repo, "make executable base")
    (repo / "docs/evidence/run.md").write_text("changed\n", encoding="utf-8")
    head = commit(repo, "change executable content")
    patch = m.patch_for(repo, base, head)
    assert " 100755" in patch
    assert_risk_bearing(repo, base, head, "docs/evidence/run.md")


def test_symlink_mode_is_risk_bearing() -> None:
    repo, base = make_repo()
    path = repo / "docs/evidence/link.md"
    path.symlink_to("../run.md")
    head = commit(repo, "add evidence symlink")
    assert_risk_bearing(repo, base, head, "docs/evidence/link.md")


def test_existing_symlink_target_change_is_risk_bearing() -> None:
    repo, _ = make_repo()
    path = repo / "docs/evidence/link.md"
    path.symlink_to("../run.md")
    base = commit(repo, "add symlink base")
    path.unlink()
    path.symlink_to("../other.md")
    head = commit(repo, "change symlink target")
    patch = m.patch_for(repo, base, head)
    assert " 120000" in patch
    assert_risk_bearing(repo, base, head, "docs/evidence/link.md")


def test_gitlink_mode_is_risk_bearing() -> None:
    repo, base = make_repo()
    git(repo, "update-index", "--add", "--cacheinfo", f"160000,{base},docs/evidence/submodule.md")
    head = commit(repo, "add evidence gitlink")
    assert_risk_bearing(repo, base, head, "docs/evidence/submodule.md")


def test_existing_gitlink_target_change_is_risk_bearing() -> None:
    repo, first = make_repo()
    (repo / "seed.txt").write_text("one\n", encoding="utf-8")
    target_one = commit(repo, "target one")
    git(repo, "update-index", "--add", "--cacheinfo", f"160000,{target_one},docs/evidence/submodule.md")
    base = commit(repo, "gitlink base")
    (repo / "seed.txt").write_text("two\n", encoding="utf-8")
    target_two = commit(repo, "target two")
    git(repo, "update-index", "--cacheinfo", f"160000,{target_two},docs/evidence/submodule.md")
    head = commit(repo, "change gitlink target")
    patch = m.patch_for(repo, base, head, ["docs/evidence/submodule.md"])
    assert " 160000" in patch
    assert_risk_bearing(repo, base, head, "docs/evidence/submodule.md")
    assert first != target_two


def test_required_check_contract_is_r2_even_for_prose_only_change() -> None:
    repo, _ = make_repo()
    contract = repo / "docs/ci/CI_CONTRACT.md"
    contract.parent.mkdir(parents=True, exist_ok=True)
    contract.write_text("stable gate\n", encoding="utf-8")
    base = commit(repo, "add CI contract")
    contract.write_text("stable gate wording changed\n", encoding="utf-8")
    head = commit(repo, "change CI contract prose")
    result = m.evaluate(base, head, repo, m.DEFAULT_POLICY)
    assert result["tier"] == "R2", result
    assert "docs/ci/CI_CONTRACT.md" in result["risk_bearing_paths"], result


def main() -> int:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print(f"ai review git metadata tests PASS: {len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
