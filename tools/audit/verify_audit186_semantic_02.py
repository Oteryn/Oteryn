#!/usr/bin/env python3
"""Fail closed on the AUDIT186 batch-02 report-pair candidate."""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = ROOT / "docs/evidence/organization-audit-20260907/audit186-semantic-02-report-pair-candidate.json"
BASELINE = "2d877271afa8f177983f3c6147472372adca0ed1"
BASELINE_TREE = "206b56085bbe12f9471be3dcfdbaa48947da7d5d"
PATHS = [
    "docs/evidence/OTERYN-ORGANIZATION-COMPREHENSIVE-AUDIT-20260907.json",
    "docs/evidence/OTERYN-ORGANIZATION-COMPREHENSIVE-AUDIT-20260907.md",
]
PRIOR_PREFIX = "docs/evidence/repository-audit-2026-09-06/"
EXPECTED_DIGEST = "67a8467de878511565ee2e7fd74a223dffbb37e9bf922c41fc11c883badcb179"
EXPECTED_CLAIMS = {
    "current_runtime_truth": False, "current_admin_truth": False,
    "current_product_truth": False, "recursive_reference_verification": False,
    "product_readiness": False, "organization_audit_completion": False,
    "independent_10_of_10": False, "provider_mutation": False,
}
EXPECTED_PROJECTION = {
    "label": "PROJECTION_ONLY",
    "batch_02_delta": {"direct": 2, "grouped": 0, "unverified": -2, "semantically_classified": 2},
    "batch_02_only_result_from_canonical": {"source_leaves": 4361, "direct": 310, "grouped": 113, "unverified": 3938, "semantically_classified": 423, "meta": {"leaves": 210, "direct": 97, "grouped": 0, "unverified": 113}},
    "prior_pr_204_projection_not_adopted": {"direct": 26, "grouped": 0, "unverified": -26, "semantically_classified": 26},
    "sequential_result_if_pr_204_then_batch_02_are_both_later_adopted": {"source_leaves": 4361, "direct": 336, "grouped": 113, "unverified": 3912, "semantically_classified": 449, "meta": {"leaves": 210, "direct": 123, "grouped": 0, "unverified": 87}},
}
ALLOWED_CHANGED_PATHS = {
    "docs/agents/workers/AUDIT186-SEMANTIC-02.md",
    "docs/evidence/organization-audit-20260907/audit186-semantic-02-report-pair-candidate.json",
    "tools/audit/verify_audit186_semantic_02.py",
    "tools/audit/test_verify_audit186_semantic_02.py",
}
CANONICAL_NAMES = {"README.md", "collection-plan.json", "coverage-groups.json", "coverage-summary.json", "unknowns.json", "verification-index.json"}


class CandidateError(ValueError):
    """The bounded candidate is unsafe for lead handoff."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CandidateError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def json_bytes(raw: bytes) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode(), object_pairs_hook=_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CandidateError(str(exc)) from exc
    if not isinstance(value, dict):
        raise CandidateError("JSON root must be an object")
    return value


def git(*args: str) -> bytes:
    return subprocess.check_output(("git", *args), cwd=ROOT)


def validate_document(doc: dict[str, Any]) -> list[dict[str, Any]]:
    if doc.get("schema_version") != 1 or doc.get("status") != "DIRECT_CANDIDATE_ONLY_NOT_ADOPTED":
        raise CandidateError("candidate status/schema drift")
    if doc.get("adoption_performed") is not False or doc.get("coverage_adopted") is not False:
        raise CandidateError("candidate must not claim adoption")
    if doc.get("claims") != EXPECTED_CLAIMS:
        raise CandidateError("current/readiness/completion/provider claim drift")
    if doc.get("projection_if_adopted") != EXPECTED_PROJECTION:
        raise CandidateError("isolated PROJECTION_ONLY accounting drift")
    source = doc.get("source_coordinates", {})
    if (source.get("repository"), source.get("baseline_head"), source.get("baseline_tree")) != ("Oteryn/Oteryn", BASELINE, BASELINE_TREE):
        raise CandidateError("baseline/source coordinate drift")
    family = doc.get("family", {})
    paths = family.get("paths")
    if family.get("path_count") != 2 or not isinstance(paths, list) or len(paths) != 2:
        raise CandidateError("family must contain exactly two leaves")
    if [item.get("path") for item in paths] != PATHS or len({item.get("path") for item in paths}) != 2:
        raise CandidateError("exact ordered path set drift")
    if family.get("proposed_disposition") != "DIRECT" or family.get("grouped_equivalence", {}).get("proposed") is not False:
        raise CandidateError("family must remain per-leaf DIRECT, never GROUPED")
    if family.get("intentionally_unverified_paths") != [] or len(family.get("intentionally_unverified_claim_surfaces", [])) != 3:
        raise CandidateError("explicit UNVERIFIED boundary drift")
    for item in paths:
        if item.get("proposed_disposition") != "DIRECT" or item.get("review_depth") != "FULL_FILE_BOUNDED_REPORT_SEMANTIC_REVIEW":
            raise CandidateError("per-leaf disposition/review-depth drift")
    if len(doc.get("recheck_triggers", [])) != 6:
        raise CandidateError("recheck trigger drift")
    canonical = json.dumps(doc, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
    if hashlib.sha256(canonical).hexdigest() != EXPECTED_DIGEST:
        raise CandidateError("immutable candidate semantic guard digest drift")
    return paths


def validate_report_contract() -> None:
    machine = json_bytes((ROOT / PATHS[0]).read_bytes())
    prose = (ROOT / PATHS[1]).read_text()
    if machine.get("report_id") != "OTERYN-ORGANIZATION-COMPREHENSIVE-AUDIT-20260907" or machine.get("status") != "QUALIFIED_AUDIT_WITH_EXPLICIT_OPEN_SCOPE":
        raise CandidateError("machine report identity/opinion drift")
    expected_counts = {"meta": 210, "game": 830, "platform": 2165, "atlas": 1155, "migration_archive": 1}
    if {key: value.get("leaf_count") for key, value in machine.get("repositories", {}).items()} != expected_counts:
        raise CandidateError("machine report source-count drift")
    if (machine.get("scoped_review_paths"), machine.get("grouped_revalidated_paths"), machine.get("semantically_classified_paths"), machine.get("unresolved_unknowns")) != (308, 113, 421, 14):
        raise CandidateError("machine report accounting/obligation drift")
    if machine.get("production_readiness_claimed") is not False or "NOT CLAIMED" not in prose or "NOT ESTABLISHED" not in prose:
        raise CandidateError("negative readiness/completion boundary drift")
    for text in ("| **Total** | **4361** | **308** | **113** | **3940** |", "FOURTEEN material residual obligations"):
        if text not in prose:
            raise CandidateError("prose accounting/obligation drift")


def validate_repository(paths: list[dict[str, Any]]) -> None:
    if git("rev-parse", f"{BASELINE}^{{tree}}").decode().strip() != BASELINE_TREE:
        raise CandidateError("baseline tree identity drift")
    for item in paths:
        raw = (ROOT / item["path"]).read_bytes()
        expected = git("show", f"{BASELINE}:{item['path']}")
        if raw != expected or git("rev-parse", f"{BASELINE}:{item['path']}").decode().strip() != item["blob_sha"]:
            raise CandidateError(f"baseline/blob identity drift: {item['path']}")
        if hashlib.sha256(raw).hexdigest() != item["sha256"] or len(raw) != item["bytes"]:
            raise CandidateError(f"working-tree digest/size drift: {item['path']}")
    prior = set(git("ls-tree", "-r", "--name-only", BASELINE, PRIOR_PREFIX).decode().splitlines())
    if set(PATHS) & prior or len(prior) != 26:
        raise CandidateError("PR #204 exclusion set drift")
    changed = set(git("diff", "--name-only", BASELINE, "--").decode().splitlines())
    unexpected = sorted(changed - ALLOWED_CHANGED_PATHS)
    if unexpected:
        raise CandidateError(f"worker changed path outside exact allowlist: {unexpected[0]}")
    directory = ROOT / "docs/evidence/organization-audit-20260907"
    for path in git("ls-tree", "-r", "--name-only", BASELINE, str(directory.relative_to(ROOT))).decode().splitlines():
        name = Path(path).name
        if name.startswith("coverage-review") or name in CANONICAL_NAMES:
            if (ROOT / path).read_bytes() != git("show", f"{BASELINE}:{path}"):
                raise CandidateError(f"canonical accounting surface mutated: {path}")
    validate_report_contract()


def validate() -> dict[str, Any]:
    paths = validate_document(json_bytes(CANDIDATE.read_bytes()))
    validate_repository(paths)
    return {"result": "REPORT_PAIR_DIRECT_CANDIDATE_VALID_NOT_ADOPTED", "baseline": BASELINE, "paths": 2, "proposed_direct": 2, "proposed_grouped": 0, "projection_only": True, "prior_pr_204_projection_separate": True, "canonical_accounting_mutated": False}


def main() -> int:
    try:
        print(json.dumps(validate(), sort_keys=True))
        return 0
    except (CandidateError, KeyError, OSError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"result": "INVALID", "error": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
