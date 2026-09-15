#!/usr/bin/env python3
"""Fail-closed verifier for the candidate-only AUDIT186-SEMANTIC-04 packet."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = ROOT / "docs/evidence/organization-audit-20260907/audit186-semantic-04-superpowers-plans-candidate.json"
BASELINE = "139eadba0dd86df07e730626ea2ec27310047b8a"
BASELINE_TREE = "57a33ddf71c77dedfe2ce8545e627d61e28f0ee0"
META_SOURCE = "23b21e9b1b2d4b6c3a5cac3d4c7a18747804c090"
META_SOURCE_TREE = "b8ebb8e50bce14a736fa65590ac121655c52fd12"
LEDGER_SHA256 = "d93838bebb6f3690bad3d6182bbc05edd0af8acf8a98d28260e496276b95a22b"
EXPECTED_CANDIDATE_DIGEST = "396873651301781cf34cf9faf9548ea7010b934338e5e45fe717b8cb64aaffa9"
EXPECTED_ADOPTED_META_DIGEST = "227296c7ee9a071da4f6a388164a666716bffb5f1eaab0f2abba5261257c9da5"
PREFIX = "docs/superpowers/plans/"
OVERLAYS = (
    "docs/evidence/organization-audit-20260907/coverage-review.tsv",
    "docs/evidence/organization-audit-20260907/coverage-review-canonical-additions.tsv",
    "docs/evidence/organization-audit-20260907/coverage-review-meta-r4-direct-additions.tsv",
    "docs/evidence/organization-audit-20260907/coverage-review-meta-r5-instruction-efficiency-direct-additions.tsv",
    "docs/evidence/organization-audit-20260907/coverage-review-meta-r6-prompts-direct-additions.tsv",
    "docs/evidence/organization-audit-20260907/coverage-review-meta-current-main-governance-direct-additions.tsv",
    "docs/evidence/organization-audit-20260907/coverage-review-audit186-semantic-03-direct-additions.tsv",
    "docs/evidence/organization-audit-20260907/coverage-review-audit186-semantic-01-historical-direct-additions.tsv",
)
PRIOR_WORKER_PATHS = {
    "docs/agents/workers/AUDIT186-SEMANTIC-01.md",
    "docs/evidence/organization-audit-20260907/audit186-semantic-01-historical-candidate.json",
    "tools/audit/test_verify_audit186_semantic_01.py",
    "tools/audit/verify_audit186_semantic_01.py",
}
NEW_WORKER_PATHS = {
    "docs/evidence/organization-audit-20260907/audit186-semantic-04-superpowers-plans-candidate.json",
    "tools/audit/test_verify_audit186_semantic_04.py",
    "tools/audit/verify_audit186_semantic_04.py",
}
ALLOWED_CHANGED_PATHS = (PRIOR_WORKER_PATHS - {"docs/evidence/organization-audit-20260907/audit186-semantic-01-historical-candidate.json"}) | NEW_WORKER_PATHS
PRIOR_WORKER_HEAD = "b7c8f6f37441b4e80ffb2214fe837105686bf979"
EXPECTED_PROJECTION = {
    "label": "PROJECTION_ONLY",
    "delta": {"direct": 9, "grouped": 0, "unverified": -9, "semantically_classified": 9},
    "result": {"source_leaves": 4361, "direct": 344, "grouped": 113, "unverified": 3904,
               "semantically_classified": 457,
               "meta": {"leaves": 210, "direct": 131, "grouped": 0, "unverified": 79}},
}


class CandidateError(ValueError):
    """Candidate violates a frozen semantic or repository invariant."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CandidateError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def parse_json(raw: bytes) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode(), object_pairs_hook=_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CandidateError(str(exc)) from exc
    if not isinstance(value, dict):
        raise CandidateError("JSON root must be an object")
    return value


def git(*args: str) -> bytes:
    return subprocess.check_output(("git", *args), cwd=ROOT)


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()


def source_leaves() -> dict[str, tuple[str, str]]:
    result = {}
    for line in git("ls-tree", "-r", META_SOURCE).decode().splitlines():
        metadata, path = line.split("\t", 1)
        mode, kind, blob = metadata.split()
        if kind != "blob" or path in result:
            raise CandidateError("invalid META source tree")
        result[path] = (mode, blob)
    return result


def baseline_bytes(path: str) -> bytes:
    return git("show", f"{BASELINE}:{path}")


def effective_direct() -> tuple[dict[str, str], list[dict[str, Any]]]:
    direct: dict[str, str] = {}
    evidence = []
    for path in OVERLAYS:
        raw = baseline_bytes(path)
        rows = list(csv.DictReader(io.StringIO(raw.decode()), delimiter="\t"))
        if not rows or any(None in row or None in row.values() for row in rows):
            raise CandidateError(f"invalid canonical coverage table: {path}")
        meta_paths = []
        for row in rows:
            if row["repository"] != "meta":
                continue
            item = row["path"]
            blob = row["blob_sha"]
            if item in direct:
                raise CandidateError(f"duplicate canonical META disposition: {item}")
            direct[item] = blob
            meta_paths.append(item)
        evidence.append({"path": path, "sha256": hashlib.sha256(raw).hexdigest(), "meta_paths": meta_paths})
    return direct, evidence


def validate_document(doc: dict[str, Any]) -> list[dict[str, Any]]:
    canonical = json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    if hashlib.sha256(canonical).hexdigest() != EXPECTED_CANDIDATE_DIGEST:
        raise CandidateError("complete candidate digest drift")
    if doc.get("schema_version") != 1 or doc.get("candidate_id") != "AUDIT186-SEMANTIC-04":
        raise CandidateError("candidate identity drift")
    if doc.get("status") != "PROJECTION_ONLY_NOT_ADOPTED" or doc.get("adoption_performed") is not False or doc.get("coverage_adopted") is not False:
        raise CandidateError("candidate adoption/status drift")
    baseline = doc.get("canonical_baseline", {})
    if baseline != {"commit": BASELINE, "tree": BASELINE_TREE, "ledger_sha256": LEDGER_SHA256,
                    "meta_source_commit": META_SOURCE, "meta_source_tree": META_SOURCE_TREE,
                    "source_leaves": 4361}:
        raise CandidateError("canonical baseline binding drift")
    if doc.get("projection_if_adopted") != EXPECTED_PROJECTION:
        raise CandidateError("projection math drift")
    family = doc.get("family", {})
    paths = family.get("paths")
    if family.get("prefix") != PREFIX or family.get("selected_path_count") != 9 or not isinstance(paths, list) or len(paths) != 9:
        raise CandidateError("frozen family-set drift")
    if family.get("grouped_equivalence", {}).get("proposed") is not False:
        raise CandidateError("GROUPED promotion forbidden")
    if family.get("intentionally_unverified_selected_paths") != []:
        raise CandidateError("selected path disposition drift")
    if any(row.get("proposed_disposition") != "DIRECT" or row.get("review_depth") != "FULL_FILE_SEMANTIC_REVIEW" for row in paths):
        raise CandidateError("disposition/review-depth promotion drift")
    if any("inert provenance" not in row.get("accepted_semantic_scope", "") for row in paths):
        raise CandidateError("semantic-scope overclaim")
    if any(doc.get("claims", {}).values()):
        raise CandidateError("negative current-truth/readiness claims drift")
    return paths


def validate_repository(doc: dict[str, Any], selected: list[dict[str, Any]]) -> None:
    if git("rev-parse", f"{BASELINE}^{{tree}}").decode().strip() != BASELINE_TREE:
        raise CandidateError("canonical baseline tree drift")
    if git("rev-parse", f"{META_SOURCE}^{{tree}}").decode().strip() != META_SOURCE_TREE:
        raise CandidateError("META source tree drift")
    leaves = source_leaves()
    if len(leaves) != 210:
        raise CandidateError("META leaf count drift")
    direct, overlay_evidence = effective_direct()
    if len(direct) != 122:
        raise CandidateError("canonical META DIRECT count drift")
    for path, blob in direct.items():
        if path not in leaves or leaves[path][1] != blob:
            raise CandidateError(f"canonical DIRECT path/blob drift: {path}")
    grouped: set[str] = set()
    unverified = sorted(set(leaves) - set(direct) - grouped)
    if len(unverified) != 88:
        raise CandidateError("frozen META UNVERIFIED count drift")
    freeze = doc["freeze"]
    expected_freeze = [{"path": path, "mode": leaves[path][0], "blob_sha": leaves[path][1]} for path in unverified]
    if freeze.get("unverified_paths") != expected_freeze or freeze.get("overlays") != overlay_evidence:
        raise CandidateError("frozen META set/overlay binding drift")
    adopted_digest = hashlib.sha256("\n".join(f"{p}\t{b}" for p, b in sorted(direct.items())).encode()).hexdigest()
    if freeze.get("adopted_meta_path_blob_digest") != EXPECTED_ADOPTED_META_DIGEST or adopted_digest != EXPECTED_ADOPTED_META_DIGEST:
        raise CandidateError("canonical adopted-set digest drift")
    if freeze.get("direct_or_grouped_overlap") != []:
        raise CandidateError("DIRECT/GROUPED/UNVERIFIED overlap claim drift")
    selected_expected = sorted(path for path in unverified if path.startswith(PREFIX))
    selected_actual = [row.get("path") for row in selected]
    if selected_actual != selected_expected or len(set(selected_actual)) != 9:
        raise CandidateError("selected family path-set drift")
    for row in selected:
        path = row["path"]
        mode, blob = leaves[path]
        raw = (ROOT / path).read_bytes()
        if row.get("mode") != mode or row.get("blob_sha") != blob or git_blob(raw) != blob:
            raise CandidateError(f"selected path/blob drift: {path}")
        if row.get("sha256") != hashlib.sha256(raw).hexdigest() or row.get("bytes") != len(raw):
            raise CandidateError(f"selected byte binding drift: {path}")
    for path in PRIOR_WORKER_PATHS:
        if (ROOT / path).read_bytes() != git("show", f"{PRIOR_WORKER_HEAD}:{path}"):
            raise CandidateError(f"preserved SEMANTIC-01 worker file drift: {path}")
    changed = set(git("diff", "--name-only", BASELINE, "--").decode().splitlines())
    if changed != ALLOWED_CHANGED_PATHS:
        raise CandidateError(f"worker changed-path allowlist mismatch: missing={sorted(ALLOWED_CHANGED_PATHS-changed)}, unexpected={sorted(changed-ALLOWED_CHANGED_PATHS)}")
    summary = parse_json(baseline_bytes("docs/evidence/organization-audit-20260907/coverage-summary.json"))
    expected_counts = {"source_leaf_total": 4361, "scoped_review_paths": 335, "grouped_revalidated_paths": 113,
                       "unverified_semantics_total": 3913, "semantically_classified_paths": 448,
                       "ledger_sha256": LEDGER_SHA256}
    if any(summary.get(k) != v for k, v in expected_counts.items()):
        raise CandidateError("canonical accounting/ledger drift")


def validate() -> dict[str, Any]:
    doc = parse_json(CANDIDATE.read_bytes())
    selected = validate_document(doc)
    validate_repository(doc, selected)
    return {"result": "SEMANTIC_04_DIRECT_CANDIDATE_VALID_NOT_ADOPTED", "baseline": BASELINE,
            "frozen_meta_unverified": 88, "selected": 9, "proposed_direct": 9,
            "proposed_grouped": 0, "projection_only": True, "canonical_mutation": False}


def main() -> int:
    try:
        print(json.dumps(validate(), sort_keys=True))
        return 0
    except (CandidateError, KeyError, OSError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"result": "INVALID", "error": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
