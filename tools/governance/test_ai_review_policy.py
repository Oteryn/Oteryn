#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("ai_review_policy.py")
spec = importlib.util.spec_from_file_location("ai_review_policy", SCRIPT)
assert spec and spec.loader
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
policy = m.load_policy()


def patch(*lines: str) -> str:
    return "\n".join(lines) + "\n"


def test_evidence_is_r0() -> None:
    tier, _ = m.classify(["docs/evidence/run.md"], patch("+result: PASS"), policy)
    assert tier == "R0"


def test_agent_policy_is_r2() -> None:
    tier, _ = m.classify(["AGENTS.md"], patch("+new rule"), policy)
    assert tier == "R2"


def test_workflow_semantic_change_is_r2() -> None:
    tier, _ = m.classify([".github/workflows/ci.yml"], patch("+permissions:", "+  contents: write"), policy)
    assert tier == "R2"


def test_immutable_action_pin_only_is_not_r0() -> None:
    old = "a" * 40
    new = "b" * 40
    p = patch(f"-      uses: actions/checkout@{old} # v7.0.0", f"+      uses: actions/checkout@{new} # v7.0.1")
    assert not m.immutable_action_pin_only([".github/workflows/ci.yml"], p)
    tier, _ = m.classify([".github/workflows/ci.yml"], p, policy)
    assert tier == "R2"


def test_action_major_change_is_not_r0() -> None:
    old = "a" * 40
    new = "b" * 40
    p = patch(
        f"-      uses: actions/upload-artifact@{old} # v4",
        f"+      uses: actions/upload-artifact@{new} # v7.0.1",
    )
    assert not m.immutable_action_pin_only([".github/workflows/ci.yml"], p)
    tier, _ = m.classify([".github/workflows/ci.yml"], p, policy)
    assert tier == "R2"


def test_dependency_lockfile_is_r1() -> None:
    tier, reasons = m.classify(["composer.lock"], patch('-"version": "1.0.0"', '+"version": "1.0.1"'), policy)
    assert tier == "R1"
    assert reasons[0].startswith("dependency_manifest_or_lockfile:")


def test_pin_plus_permission_change_is_not_r0() -> None:
    old = "a" * 40
    new = "b" * 40
    p = patch(
        f"-      uses: actions/checkout@{old}",
        f"+      uses: actions/checkout@{new}",
        "-  contents: read",
        "+  contents: write",
    )
    assert not m.immutable_action_pin_only([".github/workflows/ci.yml"], p)
    tier, _ = m.classify([".github/workflows/ci.yml"], p, policy)
    assert tier == "R2"


def test_ordinary_python_is_r1() -> None:
    tier, _ = m.classify(["src/example.py"], patch("+value = compute()"), policy)
    assert tier == "R1"


def test_sensitive_marker_escalates_to_r2() -> None:
    tier, _ = m.classify(["src/example.py"], patch("+token = rotate_token()"), policy)
    assert tier == "R2"


def test_removed_sensitive_marker_escalates_to_r2() -> None:
    tier, _ = m.classify(["src/example.py"], patch("-require_authorization()", "+continue_request()"), policy)
    assert tier == "R2"


def test_plain_readme_is_r0_but_not_review_neutral() -> None:
    tier, _ = m.classify(["README.md"], patch("+clarify usage"), policy)
    assert tier == "R0"
    assert not m.matches("README.md", policy["review_neutral_globs"])



def test_lifecycle_metadata_only_is_not_r0() -> None:
    p = patch("-status: active", "+status: archived")
    assert not m.lifecycle_metadata_only(["docs/agents/tasks/active/example.md"], p)
    tier, _ = m.classify(["docs/agents/tasks/active/example.md"], p, policy)
    assert tier == "R2"


def test_new_active_task_is_r2() -> None:
    p = patch("+task_id: COORD", "+mode: coordination", "+implementation_authorized: false")
    p = "new file mode 100644\n" + p
    tier, _ = m.classify(["docs/agents/tasks/active/coord.md"], p, policy)
    assert tier == "R2"


def test_architecture_doc_is_r2() -> None:
    tier, _ = m.classify(["docs/architecture/CONTRACT.md"], patch("+consumer authority"), policy)
    assert tier == "R2"


def test_prose_delete_word_does_not_force_r2() -> None:
    tier, _ = m.classify(["README.md"], patch("+Delete the local cache if needed."), policy)
    assert tier == "R0"


def test_security_sensitive_dependency_is_r2() -> None:
    tier, reasons = m.classify(["composer.lock"], patch('+"name": "pragmarx/google2fa"', '+"version": "9.1.0"'), policy)
    assert tier == "R2"
    assert reasons == ["security_sensitive_dependency:google2fa"]



def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()


def _fingerprint_repo() -> tuple[Path, str, str, str, str]:
    repo = Path(tempfile.mkdtemp(prefix="oteryn-ai-fingerprint-"))
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "test")
    (repo / "src").mkdir()
    (repo / "src/app.py").write_text("value = 1\n", encoding="utf-8")
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "base")
    base1 = _git(repo, "rev-parse", "HEAD")
    _git(repo, "checkout", "-b", "feature")
    (repo / "src/app.py").write_text("value = 2\n", encoding="utf-8")
    _git(repo, "commit", "-am", "feature")
    head = _git(repo, "rev-parse", "HEAD")
    _git(repo, "checkout", "master")
    (repo / "README.md").write_text("base moved elsewhere\n", encoding="utf-8")
    _git(repo, "commit", "-am", "unrelated base advance")
    base2 = _git(repo, "rev-parse", "HEAD")
    (repo / "src/app.py").write_text("value = 3\n", encoding="utf-8")
    _git(repo, "commit", "-am", "risk-bearing base advance")
    base3 = _git(repo, "rev-parse", "HEAD")
    return repo, base1, base2, base3, head


def test_unrelated_base_advance_preserves_fingerprint() -> None:
    repo, base1, base2, _, head = _fingerprint_repo()
    first, _, _ = m.fingerprint(repo, base1, head, ["src/app.py"], policy)
    second, _, _ = m.fingerprint(repo, base2, head, ["src/app.py"], policy)
    assert first == second


def test_risk_bearing_base_advance_invalidates_fingerprint() -> None:
    repo, base1, _, base3, head = _fingerprint_repo()
    first, _, _ = m.fingerprint(repo, base1, head, ["src/app.py"], policy)
    changed, _, _ = m.fingerprint(repo, base3, head, ["src/app.py"], policy)
    assert first != changed



def _composer_repo(*, runtime_change: bool = False, sensitive: bool = False, minor_change: bool = False) -> tuple[Path, str, str]:
    repo = Path(tempfile.mkdtemp(prefix="oteryn-composer-risk-"))
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "test")
    package = "vendor/google2fa-test" if sensitive else "phpunit/phpunit"
    before = {
        "_readme": ["generated"],
        "content-hash": "same",
        "packages": [{"name": "runtime/pkg", "version": "1.0.0"}],
        "packages-dev": [{"name": package, "version": "13.3.0", "dist": {"reference": "a"}}],
        "plugin-api-version": "2.6.0",
    }
    after = json.loads(json.dumps(before))
    after["packages-dev"][0]["version"] = "13.4.0" if minor_change else "13.3.1"
    after["packages-dev"][0]["dist"]["reference"] = "b"
    if runtime_change:
        after["packages"][0]["version"] = "1.0.1"
    (repo / "composer.lock").write_text(json.dumps(before, indent=2) + "\n", encoding="utf-8")
    _git(repo, "add", "composer.lock")
    _git(repo, "commit", "-m", "base")
    base = _git(repo, "rev-parse", "HEAD")
    (repo / "composer.lock").write_text(json.dumps(after, indent=2) + "\n", encoding="utf-8")
    _git(repo, "commit", "-am", "bump")
    head = _git(repo, "rev-parse", "HEAD")
    return repo, base, head


def test_composer_dev_patch_only_is_not_r0() -> None:
    repo, base, head = _composer_repo()
    assert not m.composer_dev_patch_only(repo, base, head, ["composer.lock"], policy)
    result = m.evaluate(base, head, repo, m.DEFAULT_POLICY)
    assert result["tier"] == "R1"


def test_composer_runtime_change_is_not_r0() -> None:
    repo, base, head = _composer_repo(runtime_change=True)
    assert not m.composer_dev_patch_only(repo, base, head, ["composer.lock"], policy)


def test_composer_minor_change_is_not_r0() -> None:
    repo, base, head = _composer_repo(minor_change=True)
    assert not m.composer_dev_patch_only(repo, base, head, ["composer.lock"], policy)


def test_composer_sensitive_dev_package_is_not_r0() -> None:
    repo, base, head = _composer_repo(sensitive=True)
    assert not m.composer_dev_patch_only(repo, base, head, ["composer.lock"], policy)


def test_action_added_only_is_not_r0() -> None:
    patch="""diff --git a/.github/workflows/ci.yml b/.github/workflows/ci.yml
@@ -0,0 +1,2 @@
+      uses: actions/checkout@1111111111111111111111111111111111111111 # v4
+      uses: actions/checkout@2222222222222222222222222222222222222222 # v4
"""
    assert not m.immutable_action_pin_only(['.github/workflows/ci.yml'],patch)

def test_action_deleted_only_is_not_r0() -> None:
    patch="""diff --git a/.github/workflows/ci.yml b/.github/workflows/ci.yml
@@ -1,2 +0,0 @@
-      uses: actions/checkout@1111111111111111111111111111111111111111 # v4
-      uses: actions/checkout@2222222222222222222222222222222222222222 # v4
"""
    assert not m.immutable_action_pin_only(['.github/workflows/ci.yml'],patch)

def test_unknown_executable_paths_fail_closed_to_r1() -> None:
    for path in ['Dockerfile','Makefile','CMakeLists.txt','scripts/a.ps1','scripts/a.bat','scripts/a.cmd','scripts/a.lua','config/tool.toml']:
        tier,_=m.classify([path],f'diff --git a/{path} b/{path}\n@@ -0,0 +1 @@\n+echo hi\n',m.load_policy())
        assert tier != 'R0',path

def test_lifecycle_value_injection_is_not_r0() -> None:
    patch="""diff --git a/docs/agents/tasks/active/x.md b/docs/agents/tasks/active/x.md
@@ -1 +1 @@
-owner: agent
+owner: agent; execute-dangerous-command
"""
    assert not m.lifecycle_metadata_only(['docs/agents/tasks/active/x.md'],patch)

def test_lifecycle_objective_change_is_not_r0() -> None:
    patch="""diff --git a/docs/agents/tasks/active/x.md b/docs/agents/tasks/active/x.md
@@ -4 +4 @@
-Objective: read only
+Objective: mutate production
"""
    assert not m.lifecycle_metadata_only(['docs/agents/tasks/active/x.md'],patch)

def test_composer_behavior_metadata_change_is_not_r0() -> None:
    repo,base,head=_composer_repo()
    after=json.loads(_git(repo,'show',f'{head}:composer.lock'))
    after['packages-dev'][0]['autoload']={'psr-4':{'Injected\\\\':'src/'}}
    (repo/'composer.lock').write_text(json.dumps(after,indent=2)+'\n',encoding='utf-8')
    _git(repo,'commit','-am','metadata')
    newer=_git(repo,'rev-parse','HEAD')
    assert not m.composer_dev_patch_only(repo,base,newer,['composer.lock'],policy)

def test_composite_action_binds_untrusted_inputs_to_github_context() -> None:
    action=(Path(__file__).resolve().parents[2]/'.github/actions/ai-review-gate/action.yml').read_text(encoding='utf-8')
    assert 'Bind caller inputs to immutable GitHub PR context' in action
    for token in ['github.event.pull_request.base.sha','github.event.pull_request.head.sha','github.event.pull_request.draft','github.repository','github.event.pull_request.number']:
        assert token in action
    assert "caller inputs do not match trusted GitHub PR context" in action
    assert 'steps.bind.outputs.head' in action and 'steps.bind.outputs.repository' in action and 'steps.bind.outputs.pr' in action


def test_root_agents_override_is_r2() -> None:
    tier, _ = m.classify(["AGENTS.override.md"], patch("+mode: autonomous"), policy)
    assert tier == "R2"


def test_human_review_policy_is_r2() -> None:
    tier, _ = m.classify(["docs/governance/AI_REVIEW_POLICY.md"], patch("+change review semantics"), policy)
    assert tier == "R2"


def test_core_enforcement_and_codeowners_are_r2() -> None:
    paths = [
        ".github/actions/ai-review-gate/action.yml",
        "tools/governance/verify_ai_review_evidence.py",
        "CODEOWNERS",
        "docs/CODEOWNERS",
        ".github/CODEOWNERS",
    ]
    for path in paths:
        tier, _ = m.classify([path], patch("+benign-looking change"), policy)
        assert tier == "R2", path


def test_executable_content_in_r0_globs_is_not_r0_or_neutral() -> None:
    for path in ["docs/evidence/payload.sh", "docs/generated/tool.py", "docs/agents/tasks/archive/run.ps1", "artifacts/checksums/config.yml"]:
        tier, _ = m.classify([path], patch("+echo hi"), policy)
        assert tier != "R0", path
        assert not m.safe_r0_path(path, policy["review_neutral_globs"], policy), path


def _rename_repo(source: str, destination: str) -> tuple[Path, str, str]:
    repo = Path(tempfile.mkdtemp(prefix="oteryn-rename-risk-"))
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "test")
    src = repo / source
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text("name: trusted\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "base")
    base = _git(repo, "rev-parse", "HEAD")
    dst = repo / destination
    dst.parent.mkdir(parents=True, exist_ok=True)
    _git(repo, "mv", source, destination)
    _git(repo, "commit", "-m", "rename")
    head = _git(repo, "rev-parse", "HEAD")
    return repo, base, head


def test_protected_source_rename_stays_r2_and_risk_bearing() -> None:
    cases = [
        (".github/workflows/ci.yml", "docs/evidence/ci.md"),
        ("AGENTS.md", "README.md"),
    ]
    for source, destination in cases:
        repo, base, head = _rename_repo(source, destination)
        result = m.evaluate(base, head, repo, m.DEFAULT_POLICY)
        assert source in result["changed_paths"]
        assert destination in result["changed_paths"]
        assert source in result["risk_bearing_paths"]
        assert result["tier"] == "R2"


def test_r0_optimizations_with_unproven_semantics_are_disabled() -> None:
    flags = policy["special_r0_rules"]
    for key in ["immutable_action_pin_only", "lifecycle_metadata_only", "composer_dev_patch_only"]:
        assert flags[key] is False


def test_trusted_base_workflow_never_executes_candidate_code() -> None:
    root = Path(__file__).resolve().parents[2]
    workflow = (root / ".github/workflows/governance-ai-review.yml").read_text(encoding="utf-8")
    action = (root / ".github/actions/ai-review-gate/action.yml").read_text(encoding="utf-8")
    assert "pull_request_target:" in workflow
    assert "ref: ${{ github.event.pull_request.base.sha }}" in workflow
    assert "path: trusted" in workflow
    assert "ref: ${{ github.event.pull_request.head.sha }}" in workflow
    assert "path: candidate" in workflow
    assert workflow.count("persist-credentials: false") == 2
    assert "uses: ./trusted/.github/actions/ai-review-gate" in workflow
    assert "repo-root: candidate" in workflow
    assert "repo-root:" in action and "CANDIDATE_ROOT" in action
    assert "requires trusted pull_request_target context" in action


def test_external_source_kind_is_server_bound_pr_review_only() -> None:
    for reviewer in ("codex", "codex_spark"):
        assert policy["reviewer_source_kinds"][reviewer] == ["pull_request_review"]


def test_leading_double_star_patterns_also_cover_repository_root() -> None:
    for path in ["auth/config.txt", "security/policy.txt", "migrations/001.sql", "deploy/run.txt"]:
        tier, _ = m.classify([path], patch("+benign-looking change"), policy)
        assert tier == "R2", path


def test_nested_dependency_manifests_are_classified_and_sensitive_escalates() -> None:
    tier, _ = m.classify(["services/api/composer.lock"], patch('+"name": "vendor/plain"'), policy)
    assert tier == "R1"
    tier, _ = m.classify(["services/api/composer.lock"], patch('+"name": "pragmarx/google2fa"'), policy)
    assert tier == "R2"


def test_always_r2_file_inside_evidence_is_never_r0_or_neutral() -> None:
    path = "docs/evidence/AGENTS.md"
    tier, _ = m.classify([path], patch("+new agent authority"), policy)
    assert tier == "R2"
    assert not m.safe_r0_path(path, policy["review_neutral_globs"], policy)


def test_executable_or_symlink_mode_change_is_not_r0() -> None:
    executable_patch = "old mode 100644\nnew mode 100755\n"
    tier, reasons = m.classify(["docs/evidence/run.md"], executable_patch, policy)
    assert tier == "R1"
    assert reasons == ["executable_or_symlink_mode_change"]
    symlink_patch = "new file mode 120000\n+../outside\n"
    tier, reasons = m.classify(["docs/evidence/link.md"], symlink_patch, policy)
    assert tier == "R1"
    assert reasons == ["executable_or_symlink_mode_change"]

def main() -> int:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print(f"ai review policy tests PASS: {len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
