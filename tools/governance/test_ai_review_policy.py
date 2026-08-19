#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
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


def test_immutable_action_pin_only_is_r0() -> None:
    old = "a" * 40
    new = "b" * 40
    p = patch(
        f"-      uses: actions/checkout@{old} # v7.0.0",
        f"+      uses: actions/checkout@{new} # v7.0.1",
    )
    assert m.immutable_action_pin_only([".github/workflows/ci.yml"], p)
    tier, reasons = m.classify([".github/workflows/ci.yml"], p, policy)
    assert tier == "R0"
    assert reasons == ["immutable_action_pin_only"]


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


def main() -> int:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print(f"ai review policy tests PASS: {len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
