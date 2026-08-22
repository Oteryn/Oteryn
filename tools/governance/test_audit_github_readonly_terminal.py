#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import base64
import tempfile
import urllib.error
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
            return {"id": 1, "state": "active", "path": ".github/workflows/gate.yml"}
        if path == "/repos/Oteryn/Test/contents/.github/workflows/gate.yml":
            return {"content": base64.b64encode(b"on: [pull_request, pull_request_target]\n").decode("ascii")}
        if allow_404:
            return None
        raise AssertionError(f"unexpected API call: {path}")


def check_run(name: str, run_id: int, pr_number: int) -> dict:
    return {
        "name": name,
        "app": {"id": ACTIONS_APP_ID},
        "details_url": f"https://github.com/Oteryn/Test/actions/runs/{run_id}/job/{run_id + 1000}",
        "pull_requests": [{"number": pr_number}],
    }


def test_pull_request_target_is_read_from_current_base_commit() -> None:
    main = "a" * 40
    head = "b" * 40
    audit = FakeAudit({
        "/repos/Oteryn/Test/branches/main": {"commit": {"sha": main}},
        f"/repos/Oteryn/Test/commits/{main}/check-runs?per_page=100": {
            "check_runs": [check_run("ai-review-gate", 301, 7)],
        },
        "/repos/Oteryn/Test/actions/runs/301": {
            "event": "pull_request_target", "head_sha": main, "workflow_id": 1,
            "pull_requests": [{"number": 7, "head": {"sha": head}}],
        },
        "/repos/Oteryn/Test/pulls?state=open&base=main&sort=updated&direction=desc&per_page=20": [{
            "number": 7,
            "head": {"sha": head, "repo": {"full_name": "Oteryn/Test"}},
            "base": {"ref": "main"},
        }],
        f"/repos/Oteryn/Test/compare/{main}...{head}": {
            "status": "ahead", "merge_base_commit": {"sha": main},
        },
        f"/repos/Oteryn/Test/commits/{head}/check-runs?per_page=100": {
            "check_runs": [check_run("meta-gate", 302, 7)],
        },
        "/repos/Oteryn/Test/actions/runs/302": {
            "event": "pull_request", "head_sha": head, "workflow_id": 1,
        },
    })
    observed = audit.representative_check_sources(
        "Oteryn/Test", {"meta-gate", "ai-review-gate"}, ACTIONS_APP_ID
    )
    assert m.expected_sources_satisfied(
        observed, {"meta-gate", "ai-review-gate"}, ACTIONS_APP_ID
    )


def test_disabled_pull_request_target_workflow_does_not_prove_gate() -> None:
    main = "a" * 40
    head = "b" * 40
    audit = FakeAudit({
        "/repos/Oteryn/Test/branches/main": {"commit": {"sha": main}},
        f"/repos/Oteryn/Test/commits/{main}/check-runs?per_page=100": {"check_runs": [check_run("ai-review-gate", 307, 7)]},
        "/repos/Oteryn/Test/actions/runs/307": {"event": "pull_request_target", "head_sha": main, "workflow_id": 9, "pull_requests": [{"number": 7, "head": {"sha": head}}]},
        "/repos/Oteryn/Test/actions/workflows/9": {"state": "disabled_manually"},
        "/repos/Oteryn/Test/pulls?state=open&base=main&sort=updated&direction=desc&per_page=20": [{"number": 7, "head": {"sha": head, "repo": {"full_name": "Oteryn/Test"}}, "base": {"ref": "main"}}],
        f"/repos/Oteryn/Test/compare/{main}...{head}": {"status": "ahead", "merge_base_commit": {"sha": main}},
        f"/repos/Oteryn/Test/commits/{head}/check-runs?per_page=100": {"check_runs": [check_run("meta-gate", 308, 7)]},
        "/repos/Oteryn/Test/actions/runs/308": {"event": "pull_request", "head_sha": head, "workflow_id": 1},
    })
    observed = audit.representative_check_sources("Oteryn/Test", {"meta-gate", "ai-review-gate"}, ACTIONS_APP_ID)
    assert not m.expected_sources_satisfied(observed, {"meta-gate", "ai-review-gate"}, ACTIONS_APP_ID)


def test_pull_request_target_for_other_pr_does_not_prove_gate() -> None:
    main = "a" * 40
    head = "b" * 40
    audit = FakeAudit({
        "/repos/Oteryn/Test/branches/main": {"commit": {"sha": main}},
        f"/repos/Oteryn/Test/commits/{main}/check-runs?per_page=100": {
            "check_runs": [check_run("ai-review-gate", 303, 99)],
        },
        "/repos/Oteryn/Test/actions/runs/303": {
            "event": "pull_request_target", "head_sha": main, "workflow_id": 1,
            "pull_requests": [{"number": 99, "head": {"sha": "c" * 40}}],
        },
        "/repos/Oteryn/Test/pulls?state=open&base=main&sort=updated&direction=desc&per_page=20": [{
            "number": 7,
            "head": {"sha": head, "repo": {"full_name": "Oteryn/Test"}},
            "base": {"ref": "main"},
        }],
        f"/repos/Oteryn/Test/compare/{main}...{head}": {
            "status": "ahead", "merge_base_commit": {"sha": main},
        },
        f"/repos/Oteryn/Test/commits/{head}/check-runs?per_page=100": {
            "check_runs": [check_run("meta-gate", 304, 7)],
        },
        "/repos/Oteryn/Test/actions/runs/304": {
            "event": "pull_request", "head_sha": head, "workflow_id": 1,
        },
    })
    observed = audit.representative_check_sources(
        "Oteryn/Test", {"meta-gate", "ai-review-gate"}, ACTIONS_APP_ID
    )
    assert not m.expected_sources_satisfied(
        observed, {"meta-gate", "ai-review-gate"}, ACTIONS_APP_ID
    )



def test_stale_pull_request_target_generation_does_not_prove_current_head() -> None:
    main = "a" * 40
    old_head = "b" * 40
    head = "c" * 40
    audit = FakeAudit({
        "/repos/Oteryn/Test/branches/main": {"commit": {"sha": main}},
        f"/repos/Oteryn/Test/commits/{main}/check-runs?per_page=100": {
            "check_runs": [check_run("ai-review-gate", 305, 7)],
        },
        "/repos/Oteryn/Test/actions/runs/305": {
            "event": "pull_request_target", "head_sha": main, "workflow_id": 1,
            "pull_requests": [{"number": 7, "head": {"sha": old_head}}],
        },
        "/repos/Oteryn/Test/pulls?state=open&base=main&sort=updated&direction=desc&per_page=20": [{
            "number": 7,
            "head": {"sha": head, "repo": {"full_name": "Oteryn/Test"}},
            "base": {"ref": "main"},
        }],
        f"/repos/Oteryn/Test/compare/{main}...{head}": {
            "status": "ahead", "merge_base_commit": {"sha": main},
        },
        f"/repos/Oteryn/Test/commits/{head}/check-runs?per_page=100": {
            "check_runs": [check_run("meta-gate", 306, 7)],
        },
        "/repos/Oteryn/Test/actions/runs/306": {
            "event": "pull_request", "head_sha": head, "workflow_id": 1,
        },
    })
    observed = audit.representative_check_sources(
        "Oteryn/Test", {"meta-gate", "ai-review-gate"}, ACTIONS_APP_ID
    )
    assert not m.expected_sources_satisfied(
        observed, {"meta-gate", "ai-review-gate"}, ACTIONS_APP_ID
    )


def test_desired_state_requires_complete_merge_and_security_contract() -> None:
    data = json.loads(m.DESIRED_PATH.read_text(encoding="utf-8"))
    original_path = m.core.DESIRED_PATH
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "desired.json"
        broken = json.loads(json.dumps(data))
        del broken["permanent_repositories"][0]["squash_only"]
        path.write_text(json.dumps(broken), encoding="utf-8")
        m.core.DESIRED_PATH = path
        try:
            m.core.load_desired()
        except SystemExit as exc:
            assert "squash_only" in str(exc)
        else:
            raise AssertionError("missing squash_only must fail closed")

        broken = json.loads(json.dumps(data))
        del broken["permanent_repositories"][0]["security"]["push_protection"]
        path.write_text(json.dumps(broken), encoding="utf-8")
        try:
            m.core.load_desired()
        except SystemExit as exc:
            assert "security contract" in str(exc)
        else:
            raise AssertionError("incomplete security object must fail closed")
        finally:
            m.core.DESIRED_PATH = original_path

def test_desired_state_requires_terminal_administrative_identity() -> None:
    data = json.loads(m.DESIRED_PATH.read_text(encoding="utf-8"))
    original_path = m.core.DESIRED_PATH
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "desired.json"
        for broken in (
            {**data, "administrative_repositories": []},
            json.loads(json.dumps(data)),
        ):
            if broken["administrative_repositories"]:
                broken["administrative_repositories"][0]["repository_id"] = 1
            path.write_text(json.dumps(broken), encoding="utf-8")
            m.core.DESIRED_PATH = path
            try:
                try:
                    m.core.load_desired()
                except SystemExit as exc:
                    assert "administrative repository" in str(exc)
                else:
                    raise AssertionError("missing or wrong administrative identity must fail closed")
            finally:
                m.core.DESIRED_PATH = original_path


def test_desired_state_requires_complete_administrative_contract() -> None:
    data = json.loads(m.DESIRED_PATH.read_text(encoding="utf-8"))
    original_path = m.core.DESIRED_PATH
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "desired.json"
        for field in ("classification", "terminal_state", "archived", "retention_authority"):
            broken = json.loads(json.dumps(data))
            del broken["administrative_repositories"][0][field]
            path.write_text(json.dumps(broken), encoding="utf-8")
            m.core.DESIRED_PATH = path
            try:
                try:
                    m.core.load_desired()
                except SystemExit as exc:
                    assert "administrative repository" in str(exc)
                else:
                    raise AssertionError(f"missing {field} must fail closed")
            finally:
                m.core.DESIRED_PATH = original_path


def test_desired_state_requires_strict_protection_contract() -> None:
    data = json.loads(m.DESIRED_PATH.read_text(encoding="utf-8"))
    original_path = m.core.DESIRED_PATH
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "desired.json"
        for mutate in (
            lambda item: item["protection"].pop("broad_bypass"),
            lambda item: item["protection"].pop("pull_requests"),
            lambda item: item["protection"].__setitem__("pull_requests", False),
            lambda item: item["protection"].__setitem__("force_pushes", True),
        ):
            broken = json.loads(json.dumps(data))
            mutate(broken["permanent_repositories"][0])
            path.write_text(json.dumps(broken), encoding="utf-8")
            m.core.DESIRED_PATH = path
            try:
                try:
                    m.core.load_desired()
                except SystemExit as exc:
                    assert "protection contract" in str(exc)
                else:
                    raise AssertionError("weakened protection contract must fail closed")
            finally:
                m.core.DESIRED_PATH = original_path


def test_desired_state_requires_complete_coordinate_policy() -> None:
    data = json.loads(m.DESIRED_PATH.read_text(encoding="utf-8"))
    original_path = m.core.DESIRED_PATH
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "desired.json"
        broken = json.loads(json.dumps(data))
        del broken["mutable_coordinate_policy"]["forbidden"]
        path.write_text(json.dumps(broken), encoding="utf-8")
        m.core.DESIRED_PATH = path
        try:
            try:
                m.core.load_desired()
            except SystemExit as exc:
                assert "mutable_coordinate_policy" in str(exc)
            else:
                raise AssertionError("missing coordinate policy must fail closed")
        finally:
            m.core.DESIRED_PATH = original_path

def test_desired_state_requires_codeowners_coverage_contract() -> None:
    data = json.loads(m.DESIRED_PATH.read_text(encoding="utf-8"))
    original_path = m.core.DESIRED_PATH
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "desired.json"
        broken = json.loads(json.dumps(data))
        del broken["permanent_repositories"][0]["codeowners_required_paths"]
        path.write_text(json.dumps(broken), encoding="utf-8")
        m.core.DESIRED_PATH = path
        try:
            try:
                m.core.load_desired()
            except SystemExit as exc:
                assert "codeowners_required_paths" in str(exc)
            else:
                raise AssertionError("missing CODEOWNERS coverage contract must fail closed")
        finally:
            m.core.DESIRED_PATH = original_path


def test_desired_state_requires_retention_release_contract() -> None:
    data = json.loads(m.DESIRED_PATH.read_text(encoding="utf-8"))
    original_path = m.core.DESIRED_PATH
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "desired.json"
        for broken in (json.loads(json.dumps(data)), json.loads(json.dumps(data))):
            if "retention_release" in broken["administrative_repositories"][0]:
                if broken is not None and broken["administrative_repositories"][0]["retention_release"]["assets"]:
                    if len(broken["administrative_repositories"][0]["retention_release"]["assets"]) == 6:
                        broken["administrative_repositories"][0]["retention_release"]["assets"].pop(next(iter(broken["administrative_repositories"][0]["retention_release"]["assets"])))
                    else:
                        del broken["administrative_repositories"][0]["retention_release"]
            path.write_text(json.dumps(broken), encoding="utf-8")
            m.core.DESIRED_PATH = path
            try:
                try:
                    m.core.load_desired()
                except SystemExit as exc:
                    assert "retention" in str(exc)
                else:
                    raise AssertionError("weakened retention release contract must fail closed")
            finally:
                m.core.DESIRED_PATH = original_path


def test_transport_failure_becomes_runtime_unknown_signal() -> None:
    original = m.urllib.request.urlopen

    def fail(*args, **kwargs):
        raise urllib.error.URLError("dns unavailable")

    m.urllib.request.urlopen = fail
    try:
        audit = m.Audit("test")
        try:
            audit.api("/repos/Oteryn/Test")
        except RuntimeError as exc:
            assert "transport unavailable" in str(exc)
        else:
            raise AssertionError("transport failure must be wrapped as RuntimeError")
    finally:
        m.urllib.request.urlopen = original


def main() -> int:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print(f"governance terminal live-audit tests PASS: {len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
