#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = Path(__file__).with_name("verify_meta_current_main_governance_direct_candidate.py")
SPEC = importlib.util.spec_from_file_location("verify_meta_current_main_governance_direct_candidate", MODULE_PATH)
assert SPEC and SPEC.loader
verify = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = verify
SPEC.loader.exec_module(verify)


def document() -> dict:
    _, data = verify._json_bytes(verify.CANDIDATE)
    return data


def expect_invalid(data: dict) -> None:
    try:
        verify.validate_document(data)
    except verify.CandidateError:
        return
    raise AssertionError("invalid candidate mutation was accepted")


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


def main() -> int:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
    print(f"{len(tests)} current-main governance candidate tests PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
