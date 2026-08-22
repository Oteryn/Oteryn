#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("audit_github_readonly.py")
SPEC = importlib.util.spec_from_file_location("audit_github_readonly", MODULE_PATH)
assert SPEC and SPEC.loader
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)

ACTIONS_APP_ID = 15368


class FakeAudit(m.Audit):
    def __init__(self, responses: dict[str, object]) -> None:
        super().__init__("test")
        self.responses = responses
        self.calls: list[str] = []

    def api(self, path: str, *, allow_404: bool = False):
        self.calls.append(path)
        if path in self.responses:
            return self.responses[path]
        if path.startswith("/repos/Oteryn/Test/actions/workflows/"):
            return {"state": "active"}
        if allow_404:
            return None
        raise AssertionError(f"unexpected API call: {path}")


def check_run(name: str, run_id: int, *, app_id: int = ACTIONS_APP_ID, pr_number: int | None = None) -> dict:
    pull_requests = [] if pr_number is None else [{"number": pr_number}]
    return {
        "name": name,
        "app": {"id": app_id},
        "details_url": f"https://github.com/Oteryn/Test/actions/runs/{run_id}/job/{run_id + 1000}",
        "pull_requests": pull_requests,
    }


def workflow(event: str, head_sha: str, workflow_id: int = 1) -> dict:
    return {"event": event, "head_sha": head_sha, "workflow_id": workflow_id}


def test_ruleset_scope_only_accepts_main_applicable_rulesets() -> None:
    base = {"target": "branch", "enforcement": "active"}
    assert m.ruleset_applies_to_branch(
        {**base, "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}}},
        branch="main", default_branch="main",
    )
    assert not m.ruleset_applies_to_branch(
        {**base, "conditions": {"ref_name": {"include": ["refs/heads/release/*"], "exclude": []}}},
        branch="main", default_branch="main",
    )
    assert not m.ruleset_applies_to_branch(
        {**base, "conditions": {"ref_name": {"include": ["~ALL"], "exclude": ["refs/heads/main"]}}},
        branch="main", default_branch="main",
    )
    assert not m.ruleset_applies_to_branch(
        {**base, "conditions": {"ref_name": {"include": ["~ALL"], "exclude": []}}, "enforcement": "disabled"},
        branch="main", default_branch="main",
    )


def test_required_context_sources_ignore_other_branches_and_keep_app_identity() -> None:
    audit = FakeAudit({
        "/repos/Oteryn/Test/rulesets": [
            {"id": 1, "enforcement": "active"},
            {"id": 2, "enforcement": "active"},
        ],
        "/repos/Oteryn/Test/rulesets/1": {
            "target": "branch", "enforcement": "active",
            "conditions": {"ref_name": {"include": ["refs/heads/release/*"], "exclude": []}},
            "rules": [{"type": "required_status_checks", "parameters": {"required_status_checks": [
                {"context": "release-only", "integration_id": 999},
            ]}}],
        },
        "/repos/Oteryn/Test/rulesets/2": {
            "target": "branch", "enforcement": "active",
            "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
            "rules": [{"type": "required_status_checks", "parameters": {"required_status_checks": [
                {"context": "main-gate", "integration_id": ACTIONS_APP_ID},
            ]}}],
        },
    })
    assert audit.required_context_sources("Oteryn/Test") == {"main-gate": {ACTIONS_APP_ID}}


def test_required_context_sources_reject_wrong_or_unbound_app() -> None:
    audit = FakeAudit({
        "/repos/Oteryn/Test/rulesets": [{"id": 1, "enforcement": "active"}],
        "/repos/Oteryn/Test/rulesets/1": {
            "target": "branch", "enforcement": "active",
            "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
            "rules": [{"type": "required_status_checks", "parameters": {"required_status_checks": [
                {"context": "gate", "integration_id": 999},
            ]}}],
        },
        "/repos/Oteryn/Test/branches/main/protection/required_status_checks": {
            "contexts": ["gate"],
            "checks": [{"context": "gate", "app_id": ACTIONS_APP_ID}],
        },
    })
    sources = audit.required_context_sources("Oteryn/Test")
    assert sources["gate"] == {999, ACTIONS_APP_ID}
    assert not m.expected_sources_satisfied(sources, {"gate"}, ACTIONS_APP_ID)


def test_current_main_push_is_valid_emission_proof() -> None:
    main = "a" * 40
    audit = FakeAudit({
        "/repos/Oteryn/Test/branches/main": {"commit": {"sha": main}},
        f"/repos/Oteryn/Test/commits/{main}/check-runs?per_page=100": {
            "check_runs": [check_run("gate-a", 101), check_run("gate-b", 102)],
        },
        "/repos/Oteryn/Test/actions/runs/101": workflow("push", main),
        "/repos/Oteryn/Test/actions/runs/102": workflow("push", main),
    })
    observed = audit.representative_check_sources("Oteryn/Test", {"gate-a", "gate-b"}, ACTIONS_APP_ID)
    assert m.expected_sources_satisfied(observed, {"gate-a", "gate-b"}, ACTIONS_APP_ID)
    assert not any("pulls?" in call for call in audit.calls)


def test_workflow_dispatch_on_main_does_not_prove_protected_emission() -> None:
    main = "a" * 40
    audit = FakeAudit({
        "/repos/Oteryn/Test/branches/main": {"commit": {"sha": main}},
        f"/repos/Oteryn/Test/commits/{main}/check-runs?per_page=100": {
            "check_runs": [check_run("gate", 103)],
        },
        "/repos/Oteryn/Test/actions/runs/103": workflow("workflow_dispatch", main),
        "/repos/Oteryn/Test/pulls?state=open&base=main&sort=updated&direction=desc&per_page=20": [],
    })
    assert audit.representative_check_sources("Oteryn/Test", {"gate"}, ACTIONS_APP_ID) == {}


def test_same_name_from_wrong_app_does_not_prove_emission() -> None:
    main = "a" * 40
    audit = FakeAudit({
        "/repos/Oteryn/Test/branches/main": {"commit": {"sha": main}},
        f"/repos/Oteryn/Test/commits/{main}/check-runs?per_page=100": {
            "check_runs": [check_run("gate", 104, app_id=999)],
        },
        "/repos/Oteryn/Test/actions/runs/104": workflow("push", main),
        "/repos/Oteryn/Test/pulls?state=open&base=main&sort=updated&direction=desc&per_page=20": [],
    })
    observed = audit.representative_check_sources("Oteryn/Test", {"gate"}, ACTIONS_APP_ID)
    assert observed == {"gate": {999}}
    assert not m.expected_sources_satisfied(observed, {"gate"}, ACTIONS_APP_ID)


def test_pr_payload_base_sha_does_not_replace_head_ancestry_proof() -> None:
    main = "a" * 40
    head = "b" * 40
    audit = FakeAudit({
        "/repos/Oteryn/Test/branches/main": {"commit": {"sha": main}},
        f"/repos/Oteryn/Test/commits/{main}/check-runs?per_page=100": {"check_runs": []},
        "/repos/Oteryn/Test/pulls?state=open&base=main&sort=updated&direction=desc&per_page=20": [{
            "number": 7,
            "head": {"sha": head, "repo": {"full_name": "Oteryn/Test"}},
            "base": {"ref": "main", "sha": main},
        }],
        f"/repos/Oteryn/Test/compare/{main}...{head}": {
            "status": "diverged",
            "merge_base_commit": {"sha": "c" * 40},
        },
    })
    assert audit.representative_check_sources("Oteryn/Test", {"gate"}, ACTIONS_APP_ID) == {}
    assert f"/repos/Oteryn/Test/commits/{head}/check-runs?per_page=100" not in audit.calls


def test_current_internal_pr_requires_pull_request_event_and_association() -> None:
    main = "a" * 40
    head = "b" * 40
    audit = FakeAudit({
        "/repos/Oteryn/Test/branches/main": {"commit": {"sha": main}},
        f"/repos/Oteryn/Test/commits/{main}/check-runs?per_page=100": {"check_runs": []},
        "/repos/Oteryn/Test/pulls?state=open&base=main&sort=updated&direction=desc&per_page=20": [{
            "number": 7,
            "head": {"sha": head, "repo": {"full_name": "Oteryn/Test"}},
            "base": {"ref": "main"},
        }],
        f"/repos/Oteryn/Test/compare/{main}...{head}": {"status": "ahead", "merge_base_commit": {"sha": main}},
        f"/repos/Oteryn/Test/commits/{head}/check-runs?per_page=100": {
            "check_runs": [check_run("gate-a", 201, pr_number=7), check_run("gate-b", 202, pr_number=7)],
        },
        "/repos/Oteryn/Test/actions/runs/201": workflow("pull_request", head),
        "/repos/Oteryn/Test/actions/runs/202": workflow("pull_request", head),
    })
    observed = audit.representative_check_sources("Oteryn/Test", {"gate-a", "gate-b"}, ACTIONS_APP_ID)
    assert m.expected_sources_satisfied(observed, {"gate-a", "gate-b"}, ACTIONS_APP_ID)


def test_scheduled_pr_head_check_does_not_prove_pr_emission() -> None:
    main = "a" * 40
    head = "b" * 40
    audit = FakeAudit({
        "/repos/Oteryn/Test/branches/main": {"commit": {"sha": main}},
        f"/repos/Oteryn/Test/commits/{main}/check-runs?per_page=100": {"check_runs": []},
        "/repos/Oteryn/Test/pulls?state=open&base=main&sort=updated&direction=desc&per_page=20": [{
            "number": 7,
            "head": {"sha": head, "repo": {"full_name": "Oteryn/Test"}},
            "base": {"ref": "main"},
        }],
        f"/repos/Oteryn/Test/compare/{main}...{head}": {"status": "ahead", "merge_base_commit": {"sha": main}},
        f"/repos/Oteryn/Test/commits/{head}/check-runs?per_page=100": {
            "check_runs": [check_run("gate", 203, pr_number=7)],
        },
        "/repos/Oteryn/Test/actions/runs/203": workflow("schedule", head),
    })
    assert audit.representative_check_sources("Oteryn/Test", {"gate"}, ACTIONS_APP_ID) == {}


def test_check_names_are_not_union_across_multiple_pr_heads() -> None:
    main = "a" * 40
    head1 = "b" * 40
    head2 = "c" * 40
    audit = FakeAudit({
        "/repos/Oteryn/Test/branches/main": {"commit": {"sha": main}},
        f"/repos/Oteryn/Test/commits/{main}/check-runs?per_page=100": {"check_runs": []},
        "/repos/Oteryn/Test/pulls?state=open&base=main&sort=updated&direction=desc&per_page=20": [
            {"number": 7, "head": {"sha": head1, "repo": {"full_name": "Oteryn/Test"}}, "base": {"ref": "main"}},
            {"number": 8, "head": {"sha": head2, "repo": {"full_name": "Oteryn/Test"}}, "base": {"ref": "main"}},
        ],
        f"/repos/Oteryn/Test/compare/{main}...{head1}": {"status": "ahead", "merge_base_commit": {"sha": main}},
        f"/repos/Oteryn/Test/compare/{main}...{head2}": {"status": "ahead", "merge_base_commit": {"sha": main}},
        f"/repos/Oteryn/Test/commits/{head1}/check-runs?per_page=100": {"check_runs": [check_run("gate-a", 204, pr_number=7)]},
        f"/repos/Oteryn/Test/commits/{head2}/check-runs?per_page=100": {"check_runs": [check_run("gate-b", 205, pr_number=8)]},
        "/repos/Oteryn/Test/actions/runs/204": workflow("pull_request", head1),
        "/repos/Oteryn/Test/actions/runs/205": workflow("pull_request", head2),
    })
    observed = audit.representative_check_sources("Oteryn/Test", {"gate-a", "gate-b"}, ACTIONS_APP_ID)
    assert not m.expected_sources_satisfied(observed, {"gate-a", "gate-b"}, ACTIONS_APP_ID)


def test_dependabot_security_updates_treat_200_json_as_enabled() -> None:
    audit = FakeAudit({
        "/repos/Oteryn/Test/automated-security-fixes": {"enabled": True, "paused": False},
    })
    assert audit.dependabot_security_updates_enabled("Oteryn/Test")

def test_dependabot_security_updates_treat_204_as_enabled() -> None:
    repo = "Oteryn/Test"
    audit = FakeAudit({f"/repos/{repo}/automated-security-fixes": {"_http_status": 204}})
    assert audit.dependabot_security_updates_enabled(repo)
    assert audit.calls == [f"/repos/{repo}/automated-security-fixes"]


def test_dependabot_security_updates_treat_404_as_disabled() -> None:
    repo = "Oteryn/Test"
    audit = FakeAudit({})
    assert not audit.dependabot_security_updates_enabled(repo)
    assert audit.calls == [f"/repos/{repo}/automated-security-fixes"]


def test_required_context_contract_rejects_undeclared_contexts() -> None:
    stable = {"required_checks": ["gate"], "gate_mode": "stable"}
    assert m.core.required_contexts_match(stable, {"gate"})
    assert not m.core.required_contexts_match(stable, {"gate", "stale"})
    transition = {"required_checks": ["old-gate"], "gate_mode": "transition", "target_gate": "new-gate"}
    assert m.core.required_contexts_match(transition, {"old-gate"})
    assert m.core.required_contexts_match(transition, {"old-gate", "new-gate"})
    assert not m.core.required_contexts_match(transition, {"old-gate", "stale"})


def test_ruleset_protection_controls_require_no_bypass_force_or_delete() -> None:
    detail = {
        "target": "branch", "enforcement": "active", "bypass_actors": [],
        "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
        "rules": [{"type": "deletion"}, {"type": "non_fast_forward"}, {"type": "pull_request"}],
    }
    audit = FakeAudit({
        "/repos/Oteryn/Test/rulesets": [{"id": 1, "enforcement": "active"}],
        "/repos/Oteryn/Test/rulesets/1": detail,
    })
    assert audit.main_protection_controls("Oteryn/Test") == {
        "pull_requests": True, "force_pushes": False, "deletions": False, "broad_bypass": False,
    }
    detail["bypass_actors"] = [{"actor_id": 1}]
    assert audit.main_protection_controls("Oteryn/Test")["broad_bypass"] is True
    no_pr_detail = dict(detail)
    no_pr_detail["bypass_actors"] = []
    no_pr_detail["rules"] = [{"type": "deletion"}, {"type": "non_fast_forward"}]
    no_pr = FakeAudit({
        "/repos/Oteryn/Test/rulesets": [{"id": 1, "enforcement": "active"}],
        "/repos/Oteryn/Test/rulesets/1": no_pr_detail,
    })
    assert no_pr.main_protection_controls("Oteryn/Test")["pull_requests"] is False


def test_classic_protection_controls_detect_admin_bypass() -> None:
    clean = FakeAudit({
        "/repos/Oteryn/Test/rulesets": [],
        "/repos/Oteryn/Test/branches/main/protection": {
            "allow_force_pushes": {"enabled": False},
            "allow_deletions": {"enabled": False},
            "enforce_admins": {"enabled": True},
            "required_pull_request_reviews": {},
        },
    })
    assert clean.main_protection_controls("Oteryn/Test") == {
        "pull_requests": True, "force_pushes": False, "deletions": False, "broad_bypass": False,
    }
    bypass = FakeAudit({
        "/repos/Oteryn/Test/rulesets": [],
        "/repos/Oteryn/Test/branches/main/protection": {
            "allow_force_pushes": {"enabled": False},
            "allow_deletions": {"enabled": False},
            "enforce_admins": {"enabled": False},
            "required_pull_request_reviews": {},
        },
    })
    assert bypass.main_protection_controls("Oteryn/Test")["broad_bypass"] is True
    allowance = FakeAudit({
        "/repos/Oteryn/Test/rulesets": [],
        "/repos/Oteryn/Test/branches/main/protection": {
            "allow_force_pushes": {"enabled": False},
            "allow_deletions": {"enabled": False},
            "enforce_admins": {"enabled": True},
            "required_pull_request_reviews": {
                "bypass_pull_request_allowances": {"users": [{"login": "bypass-user"}], "teams": [], "apps": []},
            },
        },
    })
    assert allowance.main_protection_controls("Oteryn/Test")["broad_bypass"] is True
    no_pr = FakeAudit({
        "/repos/Oteryn/Test/rulesets": [],
        "/repos/Oteryn/Test/branches/main/protection": {
            "allow_force_pushes": {"enabled": False},
            "allow_deletions": {"enabled": False},
            "enforce_admins": {"enabled": True},
        },
    })
    assert no_pr.main_protection_controls("Oteryn/Test")["pull_requests"] is False


def test_private_vulnerability_reporting_status() -> None:
    repo = "Oteryn/Test"
    enabled = FakeAudit({f"/repos/{repo}/private-vulnerability-reporting": {"enabled": True}})
    disabled = FakeAudit({f"/repos/{repo}/private-vulnerability-reporting": {"enabled": False}})
    assert enabled.private_vulnerability_reporting_enabled(repo)
    assert not disabled.private_vulnerability_reporting_enabled(repo)


def test_actions_permissions_must_be_enabled() -> None:
    assert m.core.actions_permissions_enabled({"enabled": True})
    assert not m.core.actions_permissions_enabled({"enabled": False})
    assert not m.core.actions_permissions_enabled({})


def test_github_actions_dependency_updates_require_structured_entry() -> None:
    repo = "Oteryn/Test"
    good = """version: 2
updates:
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
"""
    outside = """version: 2
package-ecosystem: github-actions
updates: []
"""
    missing_directory = """version: 2
updates:
  - package-ecosystem: github-actions
    schedule:
      interval: weekly
"""
    missing_schedule = """version: 2
updates:
  - package-ecosystem: github-actions
    directory: /
"""
    interval_outside_schedule = """version: 2
updates:
  - package-ecosystem: github-actions
    directory: /
    schedule:
    groups:
      fake:
        interval: weekly
"""
    fields_aligned_with_dash = """version: 2
updates:
  - package-ecosystem: github-actions
  directory: /
  schedule:
    interval: weekly
"""
    wrapped_item = """version: 2
updates:
  wrapper:
    - package-ecosystem: github-actions
      directory: /
      schedule:
        interval: weekly
"""
    duplicate_schedule = """version: 2
updates:
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
    schedule: {}
"""
    encode = lambda text: m.core.base64.b64encode(text.encode("utf-8")).decode("ascii")
    reordered = """version: 2
updates:
  - directory: /
    package-ecosystem: github-actions
    schedule:
      interval: weekly
"""
    for valid in (good, reordered):
        enabled = FakeAudit({f"/repos/{repo}/contents/.github/dependabot.yml": {"content": encode(valid)}})
        assert enabled.github_actions_dependency_updates_configured(repo)
    for invalid in (outside, missing_directory, missing_schedule, interval_outside_schedule, fields_aligned_with_dash, wrapped_item, duplicate_schedule):
        audit = FakeAudit({f"/repos/{repo}/contents/.github/dependabot.yml": {"content": encode(invalid)}})
        assert not audit.github_actions_dependency_updates_configured(repo)


def test_codeowners_requires_clean_errors_and_critical_coverage() -> None:
    repo = "Oteryn/Test"
    encode = lambda text: m.core.base64.b64encode(text.encode("utf-8")).decode("ascii")
    text = """/.github/workflows/ @owner
/SECURITY.md @owner
/contracts/ @owner
"""
    paths = [".github/workflows/ci.yml", "SECURITY.md", "contracts/api.md"]
    good = FakeAudit({
        f"/repos/{repo}/contents/.github/CODEOWNERS": {"content": encode(text)},
        f"/repos/{repo}/codeowners/errors": {"errors": []},
    })
    assert good.codeowners_baseline_valid(repo, paths)
    malformed = FakeAudit({
        f"/repos/{repo}/contents/.github/CODEOWNERS": {"content": encode(text)},
        f"/repos/{repo}/codeowners/errors": {"errors": [{"line": 1}]},
    })
    assert not malformed.codeowners_baseline_valid(repo, paths)
    assert not m.core.codeowners_text_covers_paths("/.github/workflows/ @owner\n", paths)
    assert not m.core.codeowners_pattern_covers("/.github/*", ".github/workflows/ci.yml")
    assert m.core.codeowners_pattern_covers("/.github/**", ".github/workflows/ci.yml")


def test_workflow_supply_chain_requires_permissions_and_full_sha_pins() -> None:
    secure = """name: test
permissions:
  contents: read
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@0123456789abcdef0123456789abcdef01234567
      - uses: docker://ghcr.io/example/action@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
      - uses: ./local-action
"""
    assert m.core.workflow_text_secure(secure)
    assert not m.core.workflow_text_secure(secure.replace("0123456789abcdef0123456789abcdef01234567", "v4"))
    quoted_mutable = secure.replace(
        "- uses: actions/checkout@0123456789abcdef0123456789abcdef01234567",
        '- "uses": actions/checkout@v4',
    )
    assert not m.core.workflow_text_secure(quoted_mutable)
    escaped_mutable = secure.replace(
        "- uses: actions/checkout@0123456789abcdef0123456789abcdef01234567",
        '- "u\\u0073es": actions/checkout@v4',
    )
    assert not m.core.workflow_text_secure(escaped_mutable)
    flow_mutable = secure.replace(
        "- uses: actions/checkout@0123456789abcdef0123456789abcdef01234567",
        "- {uses: actions/checkout@v4}",
    )
    assert not m.core.workflow_text_secure(flow_mutable)
    flow_write_all = secure.replace(
        "runs-on: ubuntu-latest",
        "runs-on: ubuntu-latest\n    policy: {permissions: write-all}",
    )
    assert not m.core.workflow_text_secure(flow_write_all)
    write_scopes = sorted(m.core.WRITE_CAPABLE_TOKEN_SCOPES)
    block_write_wide = secure.replace(
        "  contents: read",
        "\n".join(f"  {scope}: write" for scope in write_scopes),
    )
    assert not m.core.workflow_text_secure(block_write_wide)
    flow_write_wide = secure.replace(
        "permissions:\n  contents: read",
        "permissions: {" + ", ".join(f"{scope}: write" for scope in write_scopes) + "}",
    )
    assert not m.core.workflow_text_secure(flow_write_wide)
    bounded_write = secure.replace("contents: read", "contents: write")
    assert m.core.workflow_text_secure(bounded_write)
    anchored_write_wide = block_write_wide.replace("permissions:", "permissions: &wide", 1)
    assert not m.core.workflow_text_secure(anchored_write_wide)
    quoted_write_all = secure.replace("permissions:\n  contents: read", '"permissions": write-all')
    assert not m.core.workflow_text_secure(quoted_write_all)
    assert not m.core.workflow_text_secure(
        secure.replace(
            "docker://ghcr.io/example/action@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "docker://ghcr.io/example/action:latest",
        )
    )
    assert not m.core.workflow_text_secure(secure.replace("permissions:\n  contents: read", "permissions: write-all"))
    assert not m.core.workflow_text_secure(secure.replace("permissions:\n  contents: read\n", ""))


def test_disabled_required_gate_workflow_does_not_prove_emission() -> None:
    main = "a" * 40
    audit = FakeAudit({
        "/repos/Oteryn/Test/branches/main": {"commit": {"sha": main}},
        f"/repos/Oteryn/Test/commits/{main}/check-runs?per_page=100": {"check_runs": [check_run("gate", 301)]},
        "/repos/Oteryn/Test/actions/runs/301": workflow("push", main, workflow_id=9),
        "/repos/Oteryn/Test/actions/workflows/9": {"state": "disabled_manually"},
        "/repos/Oteryn/Test/pulls?state=open&base=main&sort=updated&direction=desc&per_page=20": [],
    })
    assert audit.representative_check_sources("Oteryn/Test", {"gate"}, ACTIONS_APP_ID) == {}


def test_dependabot_duplicate_top_level_keys_fail_closed() -> None:
    duplicate_updates = """version: 2
updates:
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
updates: []
"""
    duplicate_version = duplicate_updates.replace("updates: []", "version: 2")
    assert not m.core.dependabot_github_actions_entry_valid(duplicate_updates)
    assert not m.core.dependabot_github_actions_entry_valid(duplicate_version)


def test_retained_release_requires_all_pinned_asset_identities() -> None:
    repo = "Oteryn/Test"
    wanted = {"tag": "cut", "assets": {"bundle": {"size": 10, "digest": "sha256:" + "a" * 64}}}
    release = {"tag_name": "cut", "assets": [{"name": "bundle", "size": 10, "digest": "sha256:" + "a" * 64}]}
    good = FakeAudit({f"/repos/{repo}/releases/tags/cut": release})
    assert good.retained_release_valid(repo, wanted)
    missing = FakeAudit({f"/repos/{repo}/releases/tags/cut": {"tag_name": "cut", "assets": []}})
    assert not missing.retained_release_valid(repo, wanted)


def test_administrative_repo_live_coordinate_is_pinned() -> None:
    repo = "Oteryn/Test"
    retention = {"tag": "cut", "assets": {"bundle": {"size": 10, "digest": "sha256:" + "a" * 64}}}
    release = {"tag_name": "cut", "assets": [{"name": "bundle", "size": 10, "digest": "sha256:" + "a" * 64}]}
    audit = FakeAudit({
        f"/repos/{repo}": {"full_name": "Oteryn/Renamed", "id": 123, "archived": True},
        f"/repos/{repo}/releases/tags/cut": release,
    })
    audit.audit_administrative_repo({"repository": repo, "repository_id": 123, "archived": True, "retention_release": retention})
    assert audit.errors == [f"{repo}: administrative coordinate drift"]

def search_path(repo: str, needle: str, page: int) -> str:
    q = m.urllib.parse.quote_plus(f'"{needle}" repo:{repo}')
    return f"/search/code?q={q}&per_page=100&page={page}"


def test_coordinate_scan_ignores_policy_manifest_but_flags_mutable_use() -> None:
    repo = "Oteryn/Test"
    needle = "blakinio/Oteryn-Platform"
    audit = FakeAudit({
        search_path(repo, needle, 1): {
            "total_count": 2,
            "incomplete_results": False,
            "items": [
                {"path": "ecosystem/governance-desired-state.json"},
                {"path": "README.md"},
            ],
        }
    })
    audit.coordinate_scan({
        "permanent_repositories": [{"repository": repo}],
        "mutable_coordinate_policy": {"forbidden": [needle], "historical_reference_only": []},
    })
    assert audit.errors == [f"{repo}: stale mutable coordinate {needle} in README.md"]


def test_coordinate_scan_rejects_incomplete_results() -> None:
    repo = "Oteryn/Test"
    needle = "legacy"
    audit = FakeAudit({
        search_path(repo, needle, 1): {"total_count": 1, "incomplete_results": True, "items": []},
    })
    try:
        audit._search_all_code(repo, needle)
    except RuntimeError as exc:
        assert "incomplete" in str(exc)
    else:
        raise AssertionError("incomplete code search must fail closed")


def test_coordinate_scan_paginates_before_passing() -> None:
    repo = "Oteryn/Test"
    needle = "legacy"
    page1 = [{"path": f"docs/evidence/archive-{i}.md"} for i in range(100)]
    page2 = [{"path": "README.md"}]
    audit = FakeAudit({
        search_path(repo, needle, 1): {"total_count": 101, "incomplete_results": False, "items": page1},
        search_path(repo, needle, 2): {"total_count": 101, "incomplete_results": False, "items": page2},
    })
    audit.coordinate_scan({
        "permanent_repositories": [{"repository": repo}],
        "mutable_coordinate_policy": {"forbidden": [needle], "historical_reference_only": []},
    })
    assert audit.errors == [f"{repo}: stale mutable coordinate {needle} in README.md"]
    assert search_path(repo, needle, 2) in audit.calls


def test_coordinate_scan_rejects_results_above_github_cap() -> None:
    repo = "Oteryn/Test"
    needle = "legacy"
    audit = FakeAudit({
        search_path(repo, needle, 1): {"total_count": 1001, "incomplete_results": False, "items": []},
    })
    try:
        audit._search_all_code(repo, needle)
    except RuntimeError as exc:
        assert "1000-result" in str(exc)
    else:
        raise AssertionError("search above GitHub completeness cap must fail closed")


def test_desired_state_binds_all_required_checks_to_github_actions_app() -> None:
    desired = json.loads(m.DESIRED_PATH.read_text(encoding="utf-8"))
    assert {item["required_check_app_id"] for item in desired["permanent_repositories"]} == {ACTIONS_APP_ID}


def test_game_desired_state_models_gate_transition() -> None:
    desired = json.loads(m.DESIRED_PATH.read_text(encoding="utf-8"))
    game = next(item for item in desired["permanent_repositories"] if item["repository"] == "Oteryn/Oteryn-Game")
    assert game["required_checks"] == ["Merge gate / validate"]
    assert game["required_check_app_id"] == ACTIONS_APP_ID
    assert game["gate_mode"] == "transition"
    assert game["target_gate"] == "game-gate"


def main() -> int:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print(f"governance live-audit regression tests PASS: {len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
