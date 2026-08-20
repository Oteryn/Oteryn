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


def commit_all(repo: Path, message: str) -> str:
    git(repo, "add", "-A")
    git(repo, "commit", "-m", message)
    return git(repo, "rev-parse", "HEAD")


def commit_index(repo: Path, message: str) -> str:
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
    base = commit_all(repo, "base")
    return repo, base


def assert_risk_bearing(repo: Path, base: str, head: str, path: str, tier: str = "R1") -> None:
    result = m.evaluate(base, head, repo, m.DEFAULT_POLICY)
    assert result["tier"] == tier, result
    assert path in result["risk_bearing_paths"], result
    assert path not in result["review_neutral_paths"], result


def test_executable_mode_is_risk_bearing() -> None:
    repo, base = make_repo()
    git(repo, "update-index", "--chmod=+x", "docs/evidence/run.md")
    head = commit_index(repo, "make evidence executable")
    assert_risk_bearing(repo, base, head, "docs/evidence/run.md")


def test_existing_executable_content_change_is_risk_bearing() -> None:
    repo, _ = make_repo()
    git(repo, "update-index", "--chmod=+x", "docs/evidence/run.md")
    base = commit_index(repo, "make executable base")
    (repo / "docs/evidence/run.md").write_text("changed\n", encoding="utf-8")
    head = commit_all(repo, "change executable content")
    patch = m.patch_for(repo, base, head)
    assert " 100755" in patch
    assert_risk_bearing(repo, base, head, "docs/evidence/run.md")


def test_symlink_mode_is_risk_bearing() -> None:
    repo, base = make_repo()
    path = repo / "docs/evidence/link.md"
    path.symlink_to("../run.md")
    head = commit_all(repo, "add evidence symlink")
    assert_risk_bearing(repo, base, head, "docs/evidence/link.md")


def test_existing_symlink_target_change_is_risk_bearing() -> None:
    repo, _ = make_repo()
    path = repo / "docs/evidence/link.md"
    path.symlink_to("../run.md")
    base = commit_all(repo, "add symlink base")
    path.unlink()
    path.symlink_to("../other.md")
    head = commit_all(repo, "change symlink target")
    patch = m.patch_for(repo, base, head)
    assert " 120000" in patch
    assert_risk_bearing(repo, base, head, "docs/evidence/link.md")


def test_gitlink_mode_is_risk_bearing() -> None:
    repo, base = make_repo()
    git(repo, "update-index", "--add", "--cacheinfo", f"160000,{base},docs/evidence/submodule.md")
    head = commit_index(repo, "add evidence gitlink")
    assert_risk_bearing(repo, base, head, "docs/evidence/submodule.md")


def test_existing_gitlink_target_change_is_risk_bearing() -> None:
    repo, _ = make_repo()
    (repo / "seed.txt").write_text("one\n", encoding="utf-8")
    target_one = commit_all(repo, "target one")
    git(repo, "update-index", "--add", "--cacheinfo", f"160000,{target_one},docs/evidence/submodule.md")
    base = commit_index(repo, "gitlink base")

    (repo / "seed.txt").write_text("two\n", encoding="utf-8")
    git(repo, "add", "seed.txt")
    target_two = commit_index(repo, "target two")
    git(repo, "update-index", "--cacheinfo", f"160000,{target_two},docs/evidence/submodule.md")
    head = commit_index(repo, "change gitlink target")

    patch = m.patch_for(repo, target_two, head, ["docs/evidence/submodule.md"])
    assert " 160000" in patch
    assert_risk_bearing(repo, target_two, head, "docs/evidence/submodule.md")
    assert base != target_two


def test_required_check_contract_is_r2_even_for_prose_only_change() -> None:
    repo, _ = make_repo()
    contract = repo / "docs/ci/CI_CONTRACT.md"
    contract.parent.mkdir(parents=True, exist_ok=True)
    contract.write_text("stable gate\n", encoding="utf-8")
    base = commit_all(repo, "add CI contract")
    contract.write_text("stable gate wording changed\n", encoding="utf-8")
    head = commit_all(repo, "change CI contract prose")
    result = m.evaluate(base, head, repo, m.DEFAULT_POLICY)
    assert result["tier"] == "R2", result
    assert "docs/ci/CI_CONTRACT.md" in result["risk_bearing_paths"], result


def test_unchanged_protected_source_copy_is_r2_and_source_is_bound() -> None:
    repo, _ = make_repo()
    source = repo / "docs/governance/source.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("protected authority\n", encoding="utf-8")
    base = commit_all(repo, "add protected source")
    destination = repo / "docs/evidence/copied.md"
    destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    head = commit_all(repo, "copy protected source into evidence")
    result = m.evaluate(base, head, repo, m.DEFAULT_POLICY)
    assert result["tier"] == "R2", result
    assert "docs/governance/source.md" in result["changed_paths"], result
    assert "docs/governance/source.md" in result["risk_bearing_paths"], result
    assert "docs/evidence/copied.md" in result["risk_bearing_paths"], result
    assert result["review_neutral_paths"] == [], result


def test_risk_bearing_base_mode_advance_invalidates_fingerprint() -> None:
    repo, _ = make_repo()
    app = repo / "src/app.py"
    app.parent.mkdir(parents=True, exist_ok=True)
    app.write_text("value = 1\n", encoding="utf-8")
    base_one = commit_all(repo, "add risk-bearing app")

    git(repo, "checkout", "-b", "feature")
    app.write_text("value = 2\n", encoding="utf-8")
    head = commit_all(repo, "feature content")

    git(repo, "checkout", "master")
    git(repo, "update-index", "--chmod=+x", "src/app.py")
    base_two = commit_index(repo, "base mode advance")

    first, _, _ = m.fingerprint(repo, base_one, head, ["src/app.py"], m.load_policy())
    changed, _, _ = m.fingerprint(repo, base_two, head, ["src/app.py"], m.load_policy())
    assert first != changed
    assert m.tree_entry_at(repo, base_one, "src/app.py").startswith("100644:blob:")
    assert m.tree_entry_at(repo, base_two, "src/app.py").startswith("100755:blob:")


def test_unicode_risk_bearing_path_has_raw_tree_entry_and_fingerprint() -> None:
    repo, _ = make_repo()
    path = repo / "docs/governance/café.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("authority one\n", encoding="utf-8")
    base = commit_all(repo, "add unicode governance path")
    path.write_text("authority two\n", encoding="utf-8")
    head = commit_all(repo, "edit unicode governance path")
    result = m.evaluate(base, head, repo, m.DEFAULT_POLICY)
    assert result["tier"] == "R2", result
    assert "docs/governance/café.md" in result["risk_bearing_paths"], result
    entry = m.tree_entry_at(repo, base, "docs/governance/café.md")
    assert entry.startswith("100644:blob:"), entry
    assert len(result["review_fingerprint"]) == 64


def test_pathspec_magic_filename_is_literal_and_base_drift_is_bound() -> None:
    repo, _ = make_repo()
    literal = ":(glob)*é.py"
    path = repo / literal
    path.write_text("value = 1\n", encoding="utf-8")
    base_one = commit_all(repo, "add pathspec-magic file")

    git(repo, "checkout", "-b", "feature")
    path.write_text("value = 2\n", encoding="utf-8")
    head = commit_all(repo, "feature edits literal magic path")

    git(repo, "checkout", "master")
    path.write_text("value = 3\n", encoding="utf-8")
    base_two = commit_all(repo, "base advances literal magic path")

    entry_one = m.tree_entry_at(repo, base_one, literal)
    entry_two = m.tree_entry_at(repo, base_two, literal)
    assert entry_one.startswith("100644:blob:"), entry_one
    assert entry_two.startswith("100644:blob:"), entry_two
    assert entry_one != entry_two

    first, _, _ = m.fingerprint(repo, base_one, head, [literal], m.load_policy())
    changed, _, _ = m.fingerprint(repo, base_two, head, [literal], m.load_policy())
    assert first != changed
    assert literal in m.patch_for(repo, base_one, head, [literal])


def main() -> int:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print(f"ai review git metadata tests PASS: {len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
