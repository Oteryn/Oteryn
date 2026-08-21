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


def test_required_contexts_ignores_active_ruleset_outside_main() -> None:
    audit = FakeAudit({
        "/repos/Oteryn/Test/rulesets": [
            {"id": 1, "enforcement": "active"},
            {"id": 2, "enforcement": "active"},
        ],
        "/repos/Oteryn/Test/rulesets/1": {
            "target": "branch", "enforcement": "active",
            "conditions": {"ref_name": {"include": ["refs/heads/release/*"], "exclude": []}},
            "rules": [{"type": "required_status_checks", "parameters": {"required_status_checks": [{"context": "release-only"}]}}],
        },
        "/repos/Oteryn/Test/rulesets/2": {
            "target": "branch", "enforcement": "active",
            "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
            "rules": [{"type": "required_status_checks", "parameters": {"required_status_checks": [{"context": "main-gate"}]}}],
        },
    })
    assert audit.required_contexts("Oteryn/Test") == {"main-gate"}


def test_current_main_check_run_is_valid_emission_proof() -> None:
    audit = FakeAudit({
        "/repos/Oteryn/Test/branches/main": {"commit": {"sha": "a" * 40}},
        f"/repos/Oteryn/Test/commits/{'a' * 40}/check-runs?per_page=100": {
            "check_runs": [{"name": "gate-a"}, {"name": "gate-b"}],
        },
    })
    assert audit.representative_check_names("Oteryn/Test", {"gate-a", "gate-b"}) >= {"gate-a", "gate-b"}
    assert not any("pulls?" in call for call in audit.calls)


def test_stale_pr_base_does_not_prove_current_required_check() -> None:
    main = "a" * 40
    stale = "b" * 40
    head = "c" * 40
    audit = FakeAudit({
        "/repos/Oteryn/Test/branches/main": {"commit": {"sha": main}},
        f"/repos/Oteryn/Test/commits/{main}/check-runs?per_page=100": {"check_runs": []},
        "/repos/Oteryn/Test/pulls?state=open&base=main&sort=updated&direction=desc&per_page=20": [{
            "head": {"sha": head, "repo": {"full_name": "Oteryn/Test"}},
            "base": {"ref": "main", "sha": stale},
        }],
    })
    assert audit.representative_check_names("Oteryn/Test", {"gate"}) == set()
    assert f"/repos/Oteryn/Test/commits/{head}/check-runs?per_page=100" not in audit.calls


def test_check_names_are_not_union_across_multiple_pr_heads() -> None:
    main = "a" * 40
    head1 = "b" * 40
    head2 = "c" * 40
    audit = FakeAudit({
        "/repos/Oteryn/Test/branches/main": {"commit": {"sha": main}},
        f"/repos/Oteryn/Test/commits/{main}/check-runs?per_page=100": {"check_runs": []},
        "/repos/Oteryn/Test/pulls?state=open&base=main&sort=updated&direction=desc&per_page=20": [
            {"head": {"sha": head1, "repo": {"full_name": "Oteryn/Test"}}, "base": {"ref": "main", "sha": main}},
            {"head": {"sha": head2, "repo": {"full_name": "Oteryn/Test"}}, "base": {"ref": "main", "sha": main}},
        ],
        f"/repos/Oteryn/Test/commits/{head1}/check-runs?per_page=100": {"check_runs": [{"name": "gate-a"}]},
        f"/repos/Oteryn/Test/commits/{head2}/check-runs?per_page=100": {"check_runs": [{"name": "gate-b"}]},
    })
    observed = audit.representative_check_names("Oteryn/Test", {"gate-a", "gate-b"})
    assert not {"gate-a", "gate-b"} <= observed


def test_current_internal_pr_can_prove_required_checks() -> None:
    main = "a" * 40
    head = "b" * 40
    audit = FakeAudit({
        "/repos/Oteryn/Test/branches/main": {"commit": {"sha": main}},
        f"/repos/Oteryn/Test/commits/{main}/check-runs?per_page=100": {"check_runs": []},
        "/repos/Oteryn/Test/pulls?state=open&base=main&sort=updated&direction=desc&per_page=20": [{
            "head": {"sha": head, "repo": {"full_name": "Oteryn/Test"}},
            "base": {"ref": "main", "sha": main},
        }],
        f"/repos/Oteryn/Test/commits/{head}/check-runs?per_page=100": {
            "check_runs": [{"name": "gate-a"}, {"name": "gate-b"}],
        },
    })
    assert audit.representative_check_names("Oteryn/Test", {"gate-a", "gate-b"}) >= {"gate-a", "gate-b"}


def test_game_desired_state_models_gate_transition() -> None:
    desired = json.loads(m.DESIRED_PATH.read_text(encoding="utf-8"))
    game = next(item for item in desired["permanent_repositories"] if item["repository"] == "Oteryn/Oteryn-Game")
    assert game["required_checks"] == ["Merge gate / validate"]
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
