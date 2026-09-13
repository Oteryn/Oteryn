#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = Path(__file__).with_name("verify_meta_current_main_governance_direct_candidate.py")
SPEC = importlib.util.spec_from_file_location("verify_meta_current_main_governance_direct_candidate", MODULE_PATH)
assert SPEC and SPEC.loader
verify = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = verify
SPEC.loader.exec_module(verify)


def document() -> dict:
    _, data = verify._json_bytes(verify.CANDIDATE, label="candidate JSON")
    return data


def expect_invalid(data: dict) -> None:
    try:
        verify.validate_document(data)
    except verify.CandidateError:
        return
    raise AssertionError("invalid candidate mutation was accepted")


def _fixture() -> tuple[tempfile.TemporaryDirectory[str], Path, Path]:
    temp = tempfile.TemporaryDirectory()
    root = Path(temp.name)
    evidence = root / "organization-audit-20260907"
    shutil.copytree(verify.EVIDENCE_ROOT, evidence)
    report = root / "report.json"
    shutil.copy2(verify.REPORT, report)
    return temp, evidence, report


def _expect_state_invalid(evidence: Path, report: Path) -> None:
    try:
        verify.validate_candidate_only_state(document(), evidence_root=evidence, report_path=report)
    except verify.CandidateError:
        return
    raise AssertionError("invalid candidate-only transition state was accepted")


def test_complete_candidate_validates_against_exact_repository_state() -> None:
    result = verify.validate()
    assert result["result"] == "META_CURRENT_MAIN_GOVERNANCE_DIRECT_CANDIDATE_VALID_NOT_ADOPTED"
    assert result["candidate_paths"] == 19
    assert result["historical_evidence_paths_unverified"] == 26
    assert result["projected_if_adopted"] == verify.EXPECTED_PROJECTION
    assert result["product_readiness_claimed"] is False
    assert result["organization_audit_completion_claimed"] is False


def test_adoption_flags_cannot_self_promote() -> None:
    for key in (
        "coverage_adopted",
        "adoption_performed",
        "product_readiness_claimed",
        "organization_audit_completion_claimed",
    ):
        data = document()
        data[key] = True
        expect_invalid(data)


def test_independent_review_cannot_be_skipped() -> None:
    data = document()
    data["independent_review_required"] = False
    expect_invalid(data)


def test_source_identity_is_exact() -> None:
    data = document()
    data["source"]["commit_sha"] = "a" * 40
    expect_invalid(data)


def test_projection_cannot_drift() -> None:
    data = document()
    data["projection_if_adopted"]["direct"] = 309
    expect_invalid(data)


def test_historical_evidence_cannot_be_promoted_by_candidate() -> None:
    data = document()
    data["historical_evidence_family"]["state"] = "DIRECT"
    expect_invalid(data)


def test_candidate_path_set_rejects_duplicate_or_missing_rows() -> None:
    data = document()
    rows = data["candidate"]["new_active_governance"]
    rows[-1] = copy.deepcopy(rows[0])
    expect_invalid(data)

    data = document()
    data["candidate"]["new_active_governance"].pop()
    expect_invalid(data)


def test_candidate_blob_binding_is_exact() -> None:
    raw = verify.CANDIDATE.read_bytes()
    assert verify.git_blob_sha(raw) == verify.CANDIDATE_BLOB_SHA


def test_all_four_prior_direct_tsvs_are_complete_blob_bound() -> None:
    for name, expected_blob in verify.DIRECT_TSV_BLOBS.items():
        raw = (verify.EVIDENCE_ROOT / name).read_bytes()
        assert verify.git_blob_sha(raw) == expected_blob

        temp, evidence, _ = _fixture()
        try:
            path = evidence / name
            original = path.read_bytes()
            mutated = original.replace(b"SCOPED_SEMANTIC_REVIEW", b"UNSUPPORTED_SCOPE", 1)
            assert mutated != original
            path.write_bytes(mutated)
            try:
                verify._direct_meta_rows(evidence)
            except verify.CandidateError:
                pass
            else:
                raise AssertionError(f"semantic drift in {name} was accepted")
        finally:
            temp.cleanup()


def test_prior_direct_blob_drift_is_rejected() -> None:
    temp, evidence, report = _fixture()
    try:
        path = evidence / "coverage-review.tsv"
        raw = path.read_bytes()
        old = b"ee7d5dee4b7aafb2601a25fbbe5d789ab4627687"
        assert old in raw
        path.write_bytes(raw.replace(old, b"a" * 40, 1))
        _expect_state_invalid(evidence, report)
    finally:
        temp.cleanup()


def test_candidate_only_rejects_verification_index_adoption_record() -> None:
    temp, evidence, report = _fixture()
    try:
        path = evidence / "verification-index.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["r7_meta_current_main_governance_direct_adoption"] = {"status": "ADOPTED"}
        path.write_text(json.dumps(data), encoding="utf-8")
        _expect_state_invalid(evidence, report)
    finally:
        temp.cleanup()


def test_candidate_only_rejects_report_adoption_pointer() -> None:
    temp, evidence, report = _fixture()
    try:
        data = json.loads(report.read_text(encoding="utf-8"))
        data["coverage_review_meta_current_main_governance_direct_adoption"] = "wrong.tsv"
        report.write_text(json.dumps(data), encoding="utf-8")
        _expect_state_invalid(evidence, report)
    finally:
        temp.cleanup()


def test_candidate_only_rejects_rows_in_existing_additions_tsv() -> None:
    temp, evidence, report = _fixture()
    try:
        path = evidence / "coverage-review-canonical-additions.tsv"
        row = document()["candidate"]["previous_unverified_modified"][0]
        with path.open("a", encoding="utf-8", newline="") as handle:
            handle.write(
                "meta\t"
                + row["path"]
                + "\t"
                + row["blob_sha"]
                + "\tSCOPED_SEMANTIC_REVIEW\tR7 illicit adoption\t[]\tNOT_EXECUTED\n"
            )
        _expect_state_invalid(evidence, report)
    finally:
        temp.cleanup()


def test_candidate_only_rejects_implicit_refresh_of_prior_direct_row() -> None:
    temp, evidence, report = _fixture()
    try:
        path = evidence / "coverage-review-canonical-additions.tsv"
        row = document()["candidate"]["previous_direct_modified"][0]
        with path.open("a", encoding="utf-8", newline="") as handle:
            handle.write(
                "meta\t"
                + row["path"]
                + "\t"
                + row["blob_sha"]
                + "\tSCOPED_SEMANTIC_REVIEW\tR7 illicit refresh\t[]\tNOT_EXECUTED\n"
            )
        _expect_state_invalid(evidence, report)
    finally:
        temp.cleanup()


def test_candidate_only_rejects_grouped_classification() -> None:
    temp, evidence, report = _fixture()
    try:
        path = evidence / "coverage-groups.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["r7_injected_path"] = document()["candidate"]["new_active_governance"][0]["path"]
        path.write_text(json.dumps(data), encoding="utf-8")
        _expect_state_invalid(evidence, report)
    finally:
        temp.cleanup()


def test_candidate_only_rejects_summary_or_source_cut_transition() -> None:
    temp, evidence, report = _fixture()
    try:
        summary_path = evidence / "coverage-summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        summary["scoped_review_paths"] = 308
        summary_path.write_text(json.dumps(summary), encoding="utf-8")
        _expect_state_invalid(evidence, report)
    finally:
        temp.cleanup()

    temp, evidence, report = _fixture()
    try:
        plan_path = evidence / "collection-plan.json"
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        meta = next(row for row in plan["snapshots"] if row["id"] == "meta")
        meta["commit_sha"] = verify.SOURCE_COMMIT
        meta["expected_tree_sha"] = verify.SOURCE_TREE
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        _expect_state_invalid(evidence, report)
    finally:
        temp.cleanup()


def test_qualification_workflow_watches_all_transition_dependencies() -> None:
    workflow = (
        ROOT / ".github/workflows/organization-audit-meta-current-main-governance-qualification.yml"
    ).read_text(encoding="utf-8")
    for marker in (
        "coverage-review*.tsv",
        "coverage-groups.json",
        "coverage-summary.json",
        "verification-index.json",
        "collection-plan.json",
        "OTERYN-ORGANIZATION-COMPREHENSIVE-AUDIT-20260907.json",
    ):
        assert marker in workflow


def main() -> int:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
    print(f"{len(tests)} current-main governance candidate tests PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
