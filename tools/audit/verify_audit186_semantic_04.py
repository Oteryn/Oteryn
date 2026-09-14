#!/usr/bin/env python3
"""Fail-closed verification for AUDIT186 semantic batch 04."""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BASELINE = "2d877271afa8f177983f3c6147472372adca0ed1"
SOURCE_COMMIT = "23b21e9b1b2d4b6c3a5cac3d4c7a18747804c090"
SOURCE_TREE = "b8ebb8e50bce14a736fa65590ac121655c52fd12"
SELECTED_PATH = "docs/agents/AVAILABLE_TOOLS.md"
SELECTED_BLOB = "2759c93d1e97e4c405c3fbab08b2dbbf0708c7c7"
CANDIDATE = ROOT / "docs/evidence/organization-audit-20260907/audit186-semantic-04-available-tools-candidate.json"
REPORT = ROOT / "docs/evidence/OTERYN-ORGANIZATION-COMPREHENSIVE-AUDIT-20260907.json"
SUMMARY = ROOT / "docs/evidence/organization-audit-20260907/coverage-summary.json"
GROUPS = ROOT / "docs/evidence/organization-audit-20260907/coverage-groups.json"
REPORT_SHA256 = "3f6f6c0e4b7bffac9e240b3e9ccb1ee080be181aff6b29e2d7347107b3313b64"
SUMMARY_SHA256 = "84c30a742abcd3beea3cbedb70f99bdb897f1af082b85c8840ac137a4c3497f8"
GROUPS_SHA256 = "f7d3986b0f9481b683ffc32668057be0b5adac934b82ac9d15800a66f87dc031"
EXPECTED_CANDIDATE_SHA256 = "258ce1a1753c1caaf9524cffc26aa723f51661a987003d8b9968f32ce5433c49"
PR204_PATHS = {
    "docs/evidence/repository-audit-2026-09-06/" + name
    for name in (
        "AUDIT-PROMPT-ORIGINAL.md", "CHANGELOG-R3.md", "COVERAGE-LEDGER.md",
        "OTERYN-REPOSITORY-AUDIT-COMPLETED-R2-20260906.md",
        "OTERYN-REPOSITORY-AUDIT-R4-CURRENT-MAIN-DELTA-CLOSEOUT-20260907.md",
        "PROMPT-COMPLIANCE-MATRIX.md", "PUBLICATION-RECEIPT.json", "README.md",
        "REPRODUCE.md", "SHA256SUMS", "VERIFICATION-SUMMARY.md",
        "evidence/ci-meta-times-1.csv", "evidence/ci-meta-times-2.csv",
        "evidence/ci-meta-times-3.csv", "evidence/ci-recalculation.json",
        "evidence/ci-run-index.json", "evidence/coverage-reconciliation.json",
        "evidence/current-work.json", "evidence/external-references.json",
        "evidence/instruction-sources.json", "evidence/live-governance-readback.json",
        "evidence/native-probe-results.json", "evidence/prior-linux-bounded.log",
        "evidence/prior-native-verification.json", "evidence/revision-provenance.json",
        "evidence/workflow-inventory.json",
    )
}
PR209_PATHS = {"docs/ci/CI_CONTRACT.md"}
PR207_PATHS = {
    "docs/evidence/OTERYN-ORGANIZATION-COMPREHENSIVE-AUDIT-20260907.md",
    "docs/evidence/OTERYN-ORGANIZATION-COMPREHENSIVE-AUDIT-20260907.json",
}
ALLOWED_CHANGED_PATHS = {
    "docs/agents/workers/AUDIT186-SEMANTIC-04.md",
    str(CANDIDATE.relative_to(ROOT)),
    "tools/audit/verify_audit186_semantic_04.py",
    "tools/audit/test_verify_audit186_semantic_04.py",
}


class CandidateError(ValueError):
    """The candidate cannot safely be handed off."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CandidateError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(), object_pairs_hook=_pairs)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CandidateError(str(exc)) from exc
    if not isinstance(value, dict):
        raise CandidateError(f"JSON object required: {path}")
    return value


def git(*args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=ROOT, text=True).strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def direct_paths() -> set[tuple[str, str]]:
    result: set[tuple[str, str]] = set()
    directory = ROOT / "docs/evidence/organization-audit-20260907"
    for path in sorted(directory.glob("coverage-review*.tsv")):
        with path.open(newline="") as stream:
            for row in csv.DictReader(stream, delimiter="\t"):
                result.add((row["repository"], row["path"]))
    return result


def validate_document(doc: dict[str, Any]) -> None:
    canonical = json.dumps(doc, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
    if hashlib.sha256(canonical).hexdigest() != EXPECTED_CANDIDATE_SHA256:
        raise CandidateError("immutable candidate digest drift")


def validate_prior_packet_exclusions(path: str = SELECTED_PATH) -> None:
    if len(PR204_PATHS) != 26:
        raise CandidateError("PR #204 exclusion set drift")
    if path in PR204_PATHS or path in PR207_PATHS or path in PR209_PATHS:
        raise CandidateError("selected leaf overlaps frozen/rejected prior packet")


def validate_repository() -> dict[str, Any]:
    if sha256(REPORT) != REPORT_SHA256 or sha256(SUMMARY) != SUMMARY_SHA256 or sha256(GROUPS) != GROUPS_SHA256:
        raise CandidateError("canonical inventory/accounting identity drift or source rebaseline")
    report, summary, groups = load_json(REPORT), load_json(SUMMARY), load_json(GROUPS)
    repositories = report.get("repositories")
    expected_counts = {"meta": 210, "game": 830, "platform": 2165, "atlas": 1155, "migration_archive": 1}
    if not isinstance(repositories, dict) or {k: repositories.get(k, {}).get("leaf_count") for k in expected_counts} != expected_counts:
        raise CandidateError("canonical repository leaf counts drift")
    if sum(expected_counts.values()) != 4361 or summary.get("source_leaf_total") != 4361:
        raise CandidateError("canonical 4,361-leaf population not proven")
    meta = repositories["meta"]
    if (meta.get("commit_sha"), meta.get("tree_sha")) != (SOURCE_COMMIT, SOURCE_TREE):
        raise CandidateError("canonical META source coordinate drift")
    if git("rev-parse", f"{SOURCE_COMMIT}^{{tree}}") != SOURCE_TREE:
        raise CandidateError("canonical META source tree unavailable or mismatched")
    entries = git("ls-tree", "-r", SOURCE_COMMIT).splitlines()
    if len(entries) != 210:
        raise CandidateError("canonical META inventory leaf count drift")
    selected = [line for line in entries if line.endswith("\t" + SELECTED_PATH)]
    if len(selected) != 1 or selected[0].split()[2] != SELECTED_BLOB:
        raise CandidateError("selected path/blob absent from canonical source inventory")
    if ("meta", SELECTED_PATH) in direct_paths():
        raise CandidateError("selected leaf is already DIRECT")
    adopted_groups = groups.get("groups")
    if not isinstance(adopted_groups, list):
        raise CandidateError("canonical GROUPED surface invalid")
    if any(g.get("repository") == "meta" and SELECTED_PATH.startswith(g.get("path_prefix", "")) for g in adopted_groups):
        raise CandidateError("selected leaf is already GROUPED")
    validate_prior_packet_exclusions()
    changed = set(git("diff", "--name-only", BASELINE, "--").splitlines())
    unexpected = sorted(changed - ALLOWED_CHANGED_PATHS)
    if unexpected:
        raise CandidateError(f"worker changed path outside exact allowlist: {unexpected[0]}")
    raw = (ROOT / SELECTED_PATH).read_bytes()
    if git("hash-object", SELECTED_PATH) != SELECTED_BLOB or hashlib.sha256(raw).hexdigest() != "00c746e8b2375b3ce03b477802d93018404af32764f048b41521551c9cbd0473":
        raise CandidateError("selected working-tree bytes drift")
    return {"meta_inventory_leaves": len(entries), "canonical_population": sum(expected_counts.values())}


def validate() -> dict[str, Any]:
    validate_document(load_json(CANDIDATE))
    proof = validate_repository()
    return {
        "result": "META_AVAILABLE_TOOLS_DIRECT_CANDIDATE_VALID_NOT_ADOPTED",
        "selected_paths": 1,
        "canonical_disposition": "UNVERIFIED",
        "proposed_direct": 1,
        "projection_only": True,
        "canonical_accounting_mutated": False,
        **proof,
    }


def main() -> int:
    try:
        print(json.dumps(validate(), sort_keys=True))
        return 0
    except (CandidateError, KeyError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"result": "INVALID", "error": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
