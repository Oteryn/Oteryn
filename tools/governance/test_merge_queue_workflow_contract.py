#!/usr/bin/env python3
"""Fail-closed contract checks for GitHub-native Merge Queue workflows."""

from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from governance_drift_audit import audit_snapshot


ROOT = Path(__file__).resolve().parents[2]
CI_WORKFLOW = ROOT / ".github/workflows/ci.yml"
DESIRED_STATE = ROOT / "ecosystem/governance-desired-state.json"
ADR_0005 = ROOT / "docs/architecture/adr/0005-solo-maintainer-governance-v2-simplification-reset.md"
MERGE_GROUP_ADAPTER = ROOT / ".github/workflows/merge-group-ai-review-adapter.yml"
CONTINUATION_POLICY = ROOT / "ecosystem/agent-continuation-policy.json"
CONTINUATION_MODULE = ROOT / "tools/governance/agent_continuation_policy.py"
CONTINUATION_TEST = ROOT / "tools/governance/test_agent_continuation_policy.py"
CONTINUATION_CONTRACT = ROOT / "docs/agents/contracts/PERSISTENT_AUTONOMOUS_CONTINUATION_POLICY.md"
AGENTS = ROOT / "AGENTS.md"
ENFORCEMENT_FIELDS = (
    "required_gate",
    "merge_queue",
    "allow_auto_merge",
    "strict_required_status_checks",
    "required_approvals",
    "codeowner_review_required",
    "conversation_resolution",
    "linear_history",
    "force_pushes",
    "deletions",
    "broad_bypass",
)


def _release_record() -> dict:
    return {
        "schema_version": 1, "release_id": "example",
        "components": {
            name: {"repository": f"Oteryn/Oteryn-{name.title()}", "commit_sha": "a" * 40,
                   "evidence": [f"fixture:{name}:exact-head-ci"]}
            for name in ("game", "platform", "atlas")
        },
        "contracts": [{"name": "semantic-export", "version": "1", "provider": "game",
                       "consumer": "atlas", "status": "compatible",
                       "evidence": ["fixture:provider-and-consumer-contract-tests"]}],
    }


def test_release_validation_uses_full_schema_and_admission_rules() -> None:
    from validate_release_manifests import load_validator, validate_manifest
    validator = load_validator(ROOT / "ecosystem/compatibility.schema.json")
    validate_manifest(_release_record(), Path("example.json"), validator)
    mutations = (
        lambda x: x.update(unexpected=True),
        lambda x: x.update(contracts=[]),
        lambda x: x["components"]["game"].update(unexpected=True),
        lambda x: x["components"]["game"].update(commit_sha="a" * 40 + "\n"),
        lambda x: x["components"]["game"].update(repository="Oteryn/other"),
        lambda x: x["components"]["game"].update(evidence=[]),
        lambda x: x["components"]["game"].update(artifact_digests=["sha256:" + "a" * 64] * 2),
        lambda x: x["components"]["game"].update(artifact_digests=["sha256:" + "a" * 64 + "\n"]),
        lambda x: x["contracts"][0].pop("evidence"),
        lambda x: x["contracts"][0].update(evidence=["   "]),
        lambda x: x["contracts"][0].update(status="pending"),
        lambda x: x.update(release_id="different"),
    )
    for mutate in mutations:
        invalid = _release_record()
        mutate(invalid)
        try:
            validate_manifest(invalid, Path("example.json"), validator)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid release was accepted: {invalid}")


def test_release_schema_is_authoritative_and_never_fetches_remote_references() -> None:
    from validate_release_manifests import load_validator, validate_manifest
    schema = json.loads((ROOT / "ecosystem/compatibility.schema.json").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "schema.json"
        changed = copy.deepcopy(schema)
        changed["properties"]["release_id"]["maxLength"] = 2
        path.write_text(json.dumps(changed), encoding="utf-8")
        try:
            validate_manifest(_release_record(), Path("example.json"), load_validator(path))
        except ValueError:
            pass
        else:
            raise AssertionError("the validator ignored a constraint in the supplied schema")
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/governance/validate_release_manifests.py"),
             "--release-dir", str(path)], capture_output=True, text=True, check=False, timeout=30,
        )
        assert result.returncode == 1 and json.loads(result.stdout)["status"] == "INVALID"
        changed = copy.deepcopy(schema)
        changed["$defs"]["component"]["properties"]["commit_sha"] = {"$ref": "https://example.invalid/schema.json"}
        path.write_text(json.dumps(changed), encoding="utf-8")
        try:
            load_validator(path)
        except ValueError as exc:
            assert "reference" in str(exc)
        else:
            raise AssertionError("META must not resolve provider/remote schemas over the network")


def test_release_schema_rejects_unused_dangling_references() -> None:
    from validate_release_manifests import load_validator
    original = json.loads((ROOT / "ecosystem/compatibility.schema.json").read_text())
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "schema.json"
        for reference in ({"$ref": "#/$defs/typo"}, {"$dynamicRef": "#missing"}):
            schema = copy.deepcopy(original)
            schema["properties"]["optional_future_field"] = reference
            path.write_text(json.dumps(schema))
            try:
                load_validator(path)
            except ValueError as exc:
                assert "reference" in str(exc)
            else:
                raise AssertionError(f"unused dangling reference was accepted: {reference}")
        schema = copy.deepcopy(original)
        schema["$defs"]["nested"] = {"$id": "urn:example:nested", "$defs": {"local": True},
                                   "properties": {"value": {"$ref": "#/$defs/local"}}}
        path.write_text(json.dumps(schema))
        load_validator(path)  # Valid references retain their resource-local scope.
        schema["$defs"]["nested"]["properties"]["value"]["$ref"] = "#/$defs/component"
        path.write_text(json.dumps(schema))
        try:
            load_validator(path)
        except ValueError:
            pass
        else:
            raise AssertionError("nested resource resolved a reference against the wrong root")


def test_release_cli_rejects_missing_explicit_directory() -> None:
    with tempfile.TemporaryDirectory() as directory:
        command = [sys.executable, str(ROOT / "tools/governance/validate_release_manifests.py")]
        missing = subprocess.run(command + ["--release-dir", str(Path(directory) / "typo")],
                                 capture_output=True, text=True, timeout=30)
        assert missing.returncode == 1 and json.loads(missing.stdout)["status"] == "INVALID"
        empty = subprocess.run(command + ["--release-dir", directory],
                               capture_output=True, text=True, timeout=30)
        assert empty.returncode == 0 and json.loads(empty.stdout)["release_manifests"] == 0
        default = subprocess.run(command, capture_output=True, text=True, timeout=30)
        assert default.returncode == 0  # No committed release directory is permitted.


def _job_body(workflow: str, job_name: str) -> str:
    match = re.search(
        rf"(?ms)^  {re.escape(job_name)}:\n(?P<body>.*?)(?=^  [A-Za-z][^\n]*:\n|\Z)",
        workflow,
    )
    if not match:
        raise AssertionError(f"missing {job_name!r} job")
    return match.group("body")


def _desired_state() -> dict:
    return json.loads(DESIRED_STATE.read_text(encoding="utf-8"))


def _matching_live_state() -> dict:
    desired = _desired_state()
    rows = []
    for expected in desired["permanent_repositories"]:
        rows.append(
            {
                "repository": expected["repository"],
                **{field: expected[field] for field in ENFORCEMENT_FIELDS},
            }
        )
    return {"repositories": rows}


def test_meta_gate_qualifies_pull_requests_and_exact_merge_group_candidates() -> None:
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")

    assert "  pull_request:\n    branches: [main]" in workflow
    assert "  merge_group:\n    types: [checks_requested]" in workflow
    assert workflow.count("\n  meta-gate:\n") == 1
    assert "github.event.merge_group.head_sha || github.event.pull_request.head.sha || github.sha" in workflow
    assert "github.event.merge_group.base_sha || github.event.before || ''" in workflow

    gate = _job_body(workflow, "meta-gate")
    assert "MERGE_GROUP_HEAD_SHA: ${{ github.event.merge_group.head_sha || '' }}" in gate
    assert "MERGE_GROUP_BASE_REF: ${{ github.event.merge_group.base_ref || '' }}" in gate
    assert '[[ "$GITHUB_SHA" == "$MERGE_GROUP_HEAD_SHA" ]]' in gate
    assert '[[ "$MERGE_GROUP_BASE_REF" == "refs/heads/main" ]]' in gate


def test_meta_gate_executes_bounded_execution_guard_regressions() -> None:
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    gate = _job_body(workflow, "meta-gate")

    assert "python3 tools/governance/test_bounded_execution_guard.py" in gate


def test_meta_gate_executes_persistent_continuation_regressions() -> None:
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    gate = _job_body(workflow, "meta-gate")

    assert CONTINUATION_TEST.is_file()
    assert "python3 tools/governance/test_agent_continuation_policy.py" in gate
    assert workflow.count("python3 tools/governance/test_agent_continuation_policy.py") == 1


def test_meta_gate_requires_and_agents_discovers_persistent_continuation_contract() -> None:
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    required_paths = (
        "ecosystem/agent-continuation-policy.json",
        "tools/governance/agent_continuation_policy.py",
        "tools/governance/test_agent_continuation_policy.py",
        "docs/agents/contracts/PERSISTENT_AUTONOMOUS_CONTINUATION_POLICY.md",
    )
    for relative in required_paths:
        assert f"Path('{relative}')" in workflow

    assert CONTINUATION_POLICY.is_file()
    assert CONTINUATION_MODULE.is_file()
    assert CONTINUATION_TEST.is_file()
    assert CONTINUATION_CONTRACT.is_file()

    agents = AGENTS.read_text(encoding="utf-8")
    assert "docs/agents/contracts/PERSISTENT_AUTONOMOUS_CONTINUATION_POLICY.md" in agents
    assert "ecosystem/agent-continuation-policy.json" in agents

    contract = CONTINUATION_CONTRACT.read_text(encoding="utf-8")
    assert "Oteryn/Oteryn#108" in contract
    assert "Oteryn/Oteryn#69" in contract
    assert "STALLED" in contract and "nonterminal" in contract
    assert "CheckpointTransitionAuthority" in contract
    assert "BLOCKED_CAPABILITY_UNAVAILABLE" in contract


def test_legacy_ai_merge_group_adapter_is_retired() -> None:
    assert not MERGE_GROUP_ADAPTER.exists()


def test_ci_has_one_external_gate_only() -> None:
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    assert "\n  ai-review-gate:\n" not in workflow
    assert "ai_review_policy.py" not in workflow
    assert "trusted_review_attestation.py" not in workflow
    assert "verify_ai_review_evidence.py" not in workflow


def test_adr0005_keeps_auto_merge_subordinate_to_merge_queue() -> None:
    text = ADR_0005.read_text(encoding="utf-8")

    assert "repository auto-merge is enabled" in text
    assert "does not bypass GitHub Merge Queue" in text


def test_desired_state_requires_auto_merge_for_every_permanent_repo() -> None:
    desired = _desired_state()
    rows = desired["permanent_repositories"]

    assert len(rows) == 4
    assert all(row.get("allow_auto_merge") is True for row in rows)


def test_drift_audit_accepts_exact_target_snapshot() -> None:
    report = audit_snapshot(_desired_state(), _matching_live_state())

    assert report["status"] == "TARGET"
    assert [row["status"] for row in report["repositories"]] == ["TARGET"] * 4
    assert all(not row["drift"] and not row["unknown"] for row in report["repositories"])


def test_drift_audit_reports_known_mismatch_as_drift() -> None:
    live = _matching_live_state()
    platform = next(row for row in live["repositories"] if row["repository"] == "Oteryn/Oteryn-Platform")
    platform["strict_required_status_checks"] = True

    report = audit_snapshot(_desired_state(), live)
    row = next(item for item in report["repositories"] if item["repository"] == "Oteryn/Oteryn-Platform")

    assert report["status"] == "DRIFT"
    assert row["status"] == "DRIFT"
    assert row["drift"] == [
        {
            "field": "strict_required_status_checks",
            "expected": False,
            "actual": True,
        }
    ]


def test_drift_audit_reports_auto_merge_mismatch_as_drift() -> None:
    live = _matching_live_state()
    meta = next(row for row in live["repositories"] if row["repository"] == "Oteryn/Oteryn")
    meta["allow_auto_merge"] = False

    report = audit_snapshot(_desired_state(), live)
    row = next(item for item in report["repositories"] if item["repository"] == "Oteryn/Oteryn")

    assert report["status"] == "DRIFT"
    assert row["status"] == "DRIFT"
    assert row["drift"] == [
        {
            "field": "allow_auto_merge",
            "expected": True,
            "actual": False,
        }
    ]


def test_drift_audit_preserves_unobservable_field_as_unknown() -> None:
    live = _matching_live_state()
    platform = next(row for row in live["repositories"] if row["repository"] == "Oteryn/Oteryn-Platform")
    del platform["broad_bypass"]

    report = audit_snapshot(_desired_state(), live)
    row = next(item for item in report["repositories"] if item["repository"] == "Oteryn/Oteryn-Platform")

    assert report["status"] == "UNKNOWN"
    assert row["status"] == "UNKNOWN"
    assert row["drift"] == []
    assert row["unknown"] == ["broad_bypass"]


def test_drift_audit_rejects_duplicate_repository_snapshot() -> None:
    live = _matching_live_state()
    live["repositories"].append(dict(live["repositories"][0]))

    try:
        audit_snapshot(_desired_state(), live)
    except ValueError as exc:
        assert "duplicate" in str(exc).lower()
    else:
        raise AssertionError("duplicate live repository snapshot must fail closed")


if __name__ == "__main__":
    test_release_schema_rejects_unused_dangling_references()
    test_release_cli_rejects_missing_explicit_directory()
    test_release_validation_uses_full_schema_and_admission_rules()
    test_release_schema_is_authoritative_and_never_fetches_remote_references()
    test_meta_gate_qualifies_pull_requests_and_exact_merge_group_candidates()
    test_meta_gate_executes_bounded_execution_guard_regressions()
    test_meta_gate_executes_persistent_continuation_regressions()
    test_meta_gate_requires_and_agents_discovers_persistent_continuation_contract()
    test_legacy_ai_merge_group_adapter_is_retired()
    test_ci_has_one_external_gate_only()
    test_adr0005_keeps_auto_merge_subordinate_to_merge_queue()
    test_desired_state_requires_auto_merge_for_every_permanent_repo()
    test_drift_audit_accepts_exact_target_snapshot()
    test_drift_audit_reports_known_mismatch_as_drift()
    test_drift_audit_reports_auto_merge_mismatch_as_drift()
    test_drift_audit_preserves_unobservable_field_as_unknown()
    test_drift_audit_rejects_duplicate_repository_snapshot()
    print("merge queue workflow contract PASS")
