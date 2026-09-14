#!/usr/bin/env python3
"""Verify the AUDIT186 semantic worker's historical-provenance candidate."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = (
    ROOT
    / "docs/evidence/organization-audit-20260907/"
    "audit186-semantic-01-historical-candidate.json"
)
PREFIX = "docs/evidence/repository-audit-2026-09-06/"
BASELINE = "2d877271afa8f177983f3c6147472372adca0ed1"
BASELINE_TREE = "206b56085bbe12f9471be3dcfdbaa48947da7d5d"
FAMILY_TREE = "1609dfc49cc95b174a8efd0ccf8e342c22dd2173"
KNOWN_MANIFEST_MISMATCH = {
    "path": "OTERYN-REPOSITORY-AUDIT-R4-CURRENT-MAIN-DELTA-CLOSEOUT-20260907.md",
    "recorded": "93009d656cdf715eeed8cea8b949d37225f9c0a14fb9bb5eb61d821754ad4768",
    "actual": "2c7e6bad09327ba4adfe2bfac1409437b23f48858e0a3e42d4f08aac1b7997f3",
}
EXPECTED_CLAIMS = {
    "current_runtime_truth": False,
    "current_admin_truth": False,
    "current_product_truth": False,
    "live_operational_capability": False,
    "product_readiness": False,
    "organization_audit_completion": False,
    "package_wide_digest_integrity": False,
    "provider_mutation": False,
}
EXPECTED_PROJECTION = {
    "label": "PROJECTION_ONLY",
    "delta": {"direct": 26, "grouped": 0, "unverified": -26, "semantically_classified": 26},
    "result": {
        "source_leaves": 4361,
        "direct": 334,
        "grouped": 113,
        "unverified": 3914,
        "semantically_classified": 447,
        "meta": {"leaves": 210, "direct": 121, "grouped": 0, "unverified": 89},
    },
}
EXPECTED_CANDIDATE_DIGEST = "97b20b6d7c0aee80eab487bc59c7662acd1851bd86cb6a9643d9a007fd007b4b"
ALLOWED_CHANGED_PATHS = {
    "docs/agents/workers/AUDIT186-SEMANTIC-01.md",
    "docs/evidence/organization-audit-20260907/audit186-semantic-01-historical-candidate.json",
    "tools/audit/test_verify_audit186_semantic_01.py",
    "tools/audit/verify_audit186_semantic_01.py",
}
CANONICAL_PATHS = (
    "docs/evidence/OTERYN-ORGANIZATION-COMPREHENSIVE-AUDIT-20260907.md",
    "docs/evidence/OTERYN-ORGANIZATION-COMPREHENSIVE-AUDIT-20260907.json",
    "docs/evidence/organization-audit-20260907/README.md",
    "docs/evidence/organization-audit-20260907/collection-plan.json",
    "docs/evidence/organization-audit-20260907/coverage-groups.json",
    "docs/evidence/organization-audit-20260907/coverage-summary.json",
    "docs/evidence/organization-audit-20260907/unknowns.json",
    "docs/evidence/organization-audit-20260907/verification-index.json",
)


class CandidateError(ValueError):
    """The bounded candidate is not safe to hand off."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CandidateError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def json_bytes(raw: bytes) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CandidateError(str(exc)) from exc
    if not isinstance(value, dict):
        raise CandidateError("JSON root must be an object")
    return value


def git(*args: str) -> bytes:
    return subprocess.check_output(("git", *args), cwd=ROOT)


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()


def baseline_family() -> list[tuple[str, str]]:
    lines = git("ls-tree", "-r", BASELINE, PREFIX).decode().splitlines()
    result: list[tuple[str, str]] = []
    for line in lines:
        metadata, path = line.split("\t", 1)
        mode, kind, blob = metadata.split()
        if mode != "100644" or kind != "blob":
            raise CandidateError(f"unexpected family tree entry: {line}")
        result.append((path, blob))
    return result


def validate_document(doc: dict[str, Any]) -> list[dict[str, Any]]:
    if doc.get("schema_version") != 1:
        raise CandidateError("schema version drift")
    if doc.get("status") != "DIRECT_CANDIDATE_ONLY_NOT_ADOPTED":
        raise CandidateError("candidate status drift")
    if doc.get("adoption_performed") is not False or doc.get("coverage_adopted") is not False:
        raise CandidateError("candidate must not claim adoption")
    if doc.get("claims") != EXPECTED_CLAIMS:
        raise CandidateError("current/readiness/completion/provider claim drift")
    if doc.get("projection_if_adopted") != EXPECTED_PROJECTION:
        raise CandidateError("PROJECTION_ONLY accounting drift")

    source = doc.get("source_coordinates")
    if not isinstance(source, dict) or (
        source.get("repository"), source.get("baseline_head"), source.get("baseline_tree"), source.get("family_tree")
    ) != ("Oteryn/Oteryn", BASELINE, BASELINE_TREE, FAMILY_TREE):
        raise CandidateError("baseline/source coordinate drift")

    family = doc.get("family")
    if not isinstance(family, dict):
        raise CandidateError("family must be an object")
    if family.get("prefix") != PREFIX or family.get("path_count") != 26:
        raise CandidateError("family prefix/count drift")
    if family.get("proposed_disposition") != "DIRECT":
        raise CandidateError("family must remain a per-leaf DIRECT proposal")
    grouped = family.get("grouped_equivalence")
    if not isinstance(grouped, dict) or grouped.get("proposed") is not False or grouped.get("result") != "NOT_APPLICABLE":
        raise CandidateError("GROUPED equivalence must remain explicitly not proposed")
    if family.get("intentionally_unverified_paths") != []:
        raise CandidateError("all 26 paths must be dispositioned; claim surfaces remain separately unverified")
    unverified_claims = family.get("intentionally_unverified_claim_surfaces")
    if not isinstance(unverified_claims, list) or len(unverified_claims) != 3:
        raise CandidateError("intentionally UNVERIFIED claim surfaces drift")

    paths = family.get("paths")
    if not isinstance(paths, list) or len(paths) != 26 or not all(isinstance(item, dict) for item in paths):
        raise CandidateError("candidate must contain exactly 26 path records")
    actual_paths = [item.get("path") for item in paths]
    if len(set(actual_paths)) != 26 or actual_paths != sorted(actual_paths):
        raise CandidateError("candidate paths must be unique and ordered")
    for item in paths:
        if item.get("proposed_disposition") != "DIRECT":
            raise CandidateError(f"non-DIRECT path disposition: {item.get('path')}")
        if item.get("review_depth") != "FULL_FILE_HISTORICAL_PROVENANCE_REVIEW":
            raise CandidateError(f"review-depth drift: {item.get('path')}")
        scope = item.get("semantic_scope")
        if not isinstance(scope, str) or "not current authority or present-state proof" not in scope:
            raise CandidateError(f"historical-only scope missing: {item.get('path')}")
        if not isinstance(item.get("payload_role"), str) or not item["payload_role"]:
            raise CandidateError(f"payload role missing: {item.get('path')}")
    if not isinstance(doc.get("recheck_triggers"), list) or len(doc["recheck_triggers"]) != 6:
        raise CandidateError("exact recheck triggers drift")
    canonical = json.dumps(
        doc, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    if hashlib.sha256(canonical).hexdigest() != EXPECTED_CANDIDATE_DIGEST:
        raise CandidateError("immutable candidate semantic guard digest drift")
    return paths


def validate_structured_payloads(paths: list[dict[str, Any]]) -> None:
    manifest: dict[str, str] = {}
    for item in paths:
        relative = item["path"][len(PREFIX) :]
        raw = (ROOT / item["path"]).read_bytes()
        if relative.endswith(".json"):
            json_bytes(raw)
        elif relative.endswith(".csv"):
            try:
                rows = list(csv.reader(io.StringIO(raw.decode("utf-8")), strict=True))
            except (UnicodeDecodeError, csv.Error) as exc:
                raise CandidateError(f"unreadable CSV: {relative}") from exc
            if len(rows) < 2 or any(len(row) != len(rows[0]) for row in rows):
                raise CandidateError(f"invalid CSV shape: {relative}")
        elif relative == "SHA256SUMS":
            for line in raw.decode("utf-8").splitlines():
                digest, name = line.split("  ", 1)
                if len(digest) != 64 or name in manifest:
                    raise CandidateError("invalid SHA256SUMS entry")
                manifest[name] = digest

    mismatches = []
    for name, recorded in manifest.items():
        actual = hashlib.sha256((ROOT / PREFIX / name).read_bytes()).hexdigest()
        if actual != recorded:
            mismatches.append({"path": name, "recorded": recorded, "actual": actual})
    if mismatches != [KNOWN_MANIFEST_MISMATCH]:
        raise CandidateError("known SHA256SUMS limitation drift")


def validate_repository(paths: list[dict[str, Any]]) -> None:
    if git("rev-parse", f"{BASELINE}^{{tree}}").decode().strip() != BASELINE_TREE:
        raise CandidateError("baseline tree identity drift")
    if git("rev-parse", f"{BASELINE}:{PREFIX.rstrip('/')}").decode().strip() != FAMILY_TREE:
        raise CandidateError("family tree identity drift")
    expected = baseline_family()
    candidate = [(item["path"], item["blob_sha"]) for item in paths]
    if candidate != expected:
        raise CandidateError("exact baseline path/blob set drift")
    for item in paths:
        raw = (ROOT / item["path"]).read_bytes()
        if git_blob(raw) != item["blob_sha"] or hashlib.sha256(raw).hexdigest() != item["sha256"]:
            raise CandidateError(f"working-tree byte identity drift: {item['path']}")
        if len(raw) != item["bytes"]:
            raise CandidateError(f"working-tree size drift: {item['path']}")
    for path in CANONICAL_PATHS:
        if (ROOT / path).read_bytes() != git("show", f"{BASELINE}:{path}"):
            raise CandidateError(f"canonical audit surface mutated: {path}")
    changed_paths = set(git("diff", "--name-only", BASELINE, "--").decode().splitlines())
    unexpected_paths = sorted(changed_paths - ALLOWED_CHANGED_PATHS)
    if unexpected_paths:
        raise CandidateError(f"worker changed path outside exact allowlist: {unexpected_paths[0]}")
    review_paths = git("ls-tree", "-r", "--name-only", BASELINE, "docs/evidence/organization-audit-20260907").decode().splitlines()
    for path in review_paths:
        if Path(path).name.startswith("coverage-review") and (ROOT / path).read_bytes() != git("show", f"{BASELINE}:{path}"):
            raise CandidateError(f"canonical coverage review mutated: {path}")
    validate_structured_payloads(paths)


def validate() -> dict[str, Any]:
    doc = json_bytes(CANDIDATE.read_bytes())
    paths = validate_document(doc)
    validate_repository(paths)
    return {
        "result": "HISTORICAL_PROVENANCE_DIRECT_CANDIDATE_VALID_NOT_ADOPTED",
        "baseline": BASELINE,
        "paths": 26,
        "proposed_direct": 26,
        "proposed_grouped": 0,
        "projection_only": True,
        "current_truth_claimed": False,
        "canonical_accounting_mutated": False,
        "known_manifest_mismatches": 1,
    }


def main() -> int:
    try:
        print(json.dumps(validate(), sort_keys=True))
        return 0
    except (CandidateError, KeyError, OSError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"result": "INVALID", "error": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
