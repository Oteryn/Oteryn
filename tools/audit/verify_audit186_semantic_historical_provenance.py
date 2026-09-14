#!/usr/bin/env python3
"""Verify the candidate-only AUDIT186 historical-provenance semantic packet."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = ROOT / "docs/evidence/organization-audit-20260907/audit186-semantic-historical-provenance-candidate.json"
PACKAGE = ROOT / "docs/evidence/repository-audit-2026-09-06"
BASELINE = "2d877271afa8f177983f3c6147472372adca0ed1"
BASELINE_TREE = "206b56085bbe12f9471be3dcfdbaa48947da7d5d"
PREFIX = "docs/evidence/repository-audit-2026-09-06/"
CANDIDATE_BLOB = "88bef6a313ae90bd195d97f61df65f0e00b2b82d"
INERT_SENTENCE = "This directory is inert audit evidence, not an agent policy, skill, permission grant or implementation plan to execute automatically."
FORBIDDEN_CHANGED_PREFIXES = (
    "docs/evidence/OTERYN-ORGANIZATION-COMPREHENSIVE-AUDIT-20260907.",
    "docs/evidence/organization-audit-20260907/README.md",
    "docs/evidence/organization-audit-20260907/coverage-review",
    "docs/evidence/organization-audit-20260907/coverage-groups",
    "docs/evidence/organization-audit-20260907/coverage-summary",
    "docs/evidence/organization-audit-20260907/unknowns",
    "docs/evidence/organization-audit-20260907/verification-index",
    "docs/evidence/organization-audit-20260907/collection-plan",
)


class CandidateError(ValueError):
    pass


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()


def unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CandidateError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(raw: bytes) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CandidateError(str(exc)) from exc
    if not isinstance(value, dict):
        raise CandidateError("candidate root must be an object")
    return value


def baseline_leaves() -> list[dict[str, str]]:
    output = subprocess.check_output(
        ["git", "ls-tree", "-r", BASELINE, PREFIX], cwd=ROOT, text=True
    )
    leaves = []
    for line in output.splitlines():
        metadata, path = line.split("\t", 1)
        mode, kind, blob_sha = metadata.split()
        if kind != "blob":
            raise CandidateError(f"non-blob historical leaf: {path}")
        leaves.append({"path": path, "mode": mode, "blob_sha": blob_sha})
    return leaves


def validate_document(doc: dict[str, Any], leaves: list[dict[str, str]]) -> None:
    if doc.get("schema_version") != 1 or type(doc.get("schema_version")) is not int:
        raise CandidateError("schema version drift")
    if doc.get("status") != "DIRECT_CANDIDATE_ONLY_NOT_ADOPTED":
        raise CandidateError("candidate-only status drift")
    if doc.get("adoption_performed") is not False or doc.get("coverage_adopted") is not False:
        raise CandidateError("candidate must not claim adoption")
    baseline = doc.get("baseline")
    if not isinstance(baseline, dict) or baseline.get("commit_sha") != BASELINE or baseline.get("tree_sha") != BASELINE_TREE:
        raise CandidateError("baseline identity drift")
    family = doc.get("family")
    if not isinstance(family, dict) or family.get("prefix") != PREFIX or family.get("path_count") != 26:
        raise CandidateError("family boundary/count drift")
    if family.get("proposed_disposition") != "DIRECT" or family.get("grouped_proposed") is not False:
        raise CandidateError("family must remain per-leaf DIRECT, not GROUPED")
    expected = [{"path": leaf["path"], "blob_sha": leaf["blob_sha"]} for leaf in leaves]
    paths = family.get("paths")
    if not isinstance(paths, list) or len(paths) != 26:
        raise CandidateError("candidate exact path set drift")
    actual = []
    for row in paths:
        if not isinstance(row, dict):
            raise CandidateError("candidate path row must be an object")
        actual.append({"path": row.get("path"), "blob_sha": row.get("blob_sha")})
        if row.get("proposed_disposition") != "DIRECT" or row.get("depth") != "SCOPED_SEMANTIC_REVIEW":
            raise CandidateError("per-leaf disposition/depth drift")
        scope = row.get("scope")
        if not isinstance(scope, str) or "not revalidated as current truth" not in scope:
            raise CandidateError("per-leaf current-truth limitation missing")
    if actual != expected or len({row["path"] for row in actual}) != 26:
        raise CandidateError("candidate path order/blob identity drift")
    grouped = doc.get("grouped_equivalence")
    if not isinstance(grouped, dict) or grouped.get("applicable") is not False or "heterogeneous" not in grouped.get("reason", ""):
        raise CandidateError("GROUPED non-equivalence proof drift")
    projection = doc.get("projection_if_adopted")
    expected_projection = {
        "label": "PROJECTION_ONLY", "source_leaves": 4361, "direct": 334,
        "grouped": 113, "unverified": 3914, "semantically_classified": 447,
        "meta": {"leaves": 210, "direct": 121, "grouped": 0, "unverified": 89},
        "delta": {"direct": 26, "grouped": 0, "unverified": -26, "semantically_classified": 26},
    }
    if projection != expected_projection:
        raise CandidateError("PROJECTION_ONLY accounting drift")
    limits = " ".join(family.get("limitations", []))
    required = ("No historical factual assertion", "No runtime", "non-dispatchable", "not approval")
    if not all(token in limits for token in required):
        raise CandidateError("historical/current non-claim boundary drift")
    intentionally = doc.get("intentionally_unverified")
    if not isinstance(intentionally, dict) or intentionally.get("within_family") != []:
        raise CandidateError("within-family disposition drift")
    if "remain unverified as current truth" not in intentionally.get("payload_claims", ""):
        raise CandidateError("payload current-truth UNVERIFIED boundary missing")
    triggers = intentionally.get("recheck_triggers")
    if not isinstance(triggers, list) or len(triggers) != 5:
        raise CandidateError("exact recheck triggers drift")


def changed_paths() -> list[str]:
    output = subprocess.check_output(["git", "diff", "--name-only", BASELINE], cwd=ROOT, text=True)
    return [line for line in output.splitlines() if line]


def validate() -> dict[str, Any]:
    raw = CANDIDATE.read_bytes()
    if git_blob(raw) != CANDIDATE_BLOB:
        raise CandidateError("immutable candidate blob drift")
    if subprocess.check_output(["git", "rev-parse", f"{BASELINE}^{{tree}}"], cwd=ROOT, text=True).strip() != BASELINE_TREE:
        raise CandidateError("baseline tree drift")
    leaves = baseline_leaves()
    if len(leaves) != 26:
        raise CandidateError("baseline family must contain exactly 26 leaves")
    for leaf in leaves:
        path = ROOT / leaf["path"]
        if not path.is_file() or git_blob(path.read_bytes()) != leaf["blob_sha"] or leaf["mode"] != "100644":
            raise CandidateError(f"working historical leaf identity drift: {leaf['path']}")
    if INERT_SENTENCE not in (PACKAGE / "README.md").read_text(encoding="utf-8"):
        raise CandidateError("package inert/non-authority envelope missing")
    doc = load_json(raw)
    validate_document(doc, leaves)
    changed = changed_paths()
    forbidden = [path for path in changed if any(path.startswith(prefix) for prefix in FORBIDDEN_CHANGED_PREFIXES)]
    if forbidden:
        raise CandidateError(f"canonical accounting surface changed: {forbidden[0]}")
    return {
        "result": "HISTORICAL_PROVENANCE_DIRECT_CANDIDATE_VALID_NOT_ADOPTED",
        "baseline": BASELINE, "path_count": 26, "proposed_direct": 26,
        "projected_direct": 334, "projected_grouped": 113,
        "projected_unverified": 3914, "projection_only": True,
        "current_truth_revalidated": False, "coverage_adopted": False,
    }


def main() -> int:
    try:
        print(json.dumps(validate(), sort_keys=True))
        return 0
    except (CandidateError, OSError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"result": "INVALID", "error": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
