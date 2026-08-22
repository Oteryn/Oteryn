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


def workflow(event: str, head_sha: str) -> dict:
    return {"event": event, "head_sha": head_sha}


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
