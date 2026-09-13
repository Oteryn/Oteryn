#!/usr/bin/env python3
"""Verify the current-main META governance DIRECT candidate without adopting it."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_ROOT = ROOT / "docs/evidence/organization-audit-20260907"
CANDIDATE = EVIDENCE_ROOT / "r7-meta-current-main-governance-direct-candidate.json"
CANDIDATE_BLOB_SHA = "6a3e98ad65f52015a43a84e39a8940f64b31dc65"
REPORT = ROOT / "docs/evidence/OTERYN-ORGANIZATION-COMPREHENSIVE-AUDIT-20260907.json"
VERIFICATION_INDEX = EVIDENCE_ROOT / "verification-index.json"
COVERAGE_GROUPS = EVIDENCE_ROOT / "coverage-groups.json"
COVERAGE_SUMMARY = EVIDENCE_ROOT / "coverage-summary.json"
COLLECTION_PLAN = EVIDENCE_ROOT / "collection-plan.json"
OLD_COMMIT = "1a01c5b3e08666a82245b1cac78da3736c65e785"
OLD_TREE = "f084e824ec5e14d5909c9750d906d91d51425fd5"
SOURCE_COMMIT = "23b21e9b1b2d4b6c3a5cac3d4c7a18747804c090"
SOURCE_TREE = "b8ebb8e50bce14a736fa65590ac121655c52fd12"
HISTORICAL_PREFIX = "docs/evidence/repository-audit-2026-09-06/"
OVERLAY_NAME = "coverage-review-meta-current-main-governance-direct-additions.tsv"
OVERLAY = EVIDENCE_ROOT / OVERLAY_NAME
DIRECT_TSV_BLOBS = {
    "coverage-review.tsv": "d7bb404e0ca001149f1dd33ebd8515e7a50f2542",
    "coverage-review-meta-r4-direct-additions.tsv": "77fc7c4c2a6f11a076dd4a32408163d997c29c26",
    "coverage-review-meta-r5-instruction-efficiency-direct-additions.tsv": "a4d203bf1e15d4beb0b33cd9be3c57cb52bf2a60",
    "coverage-review-meta-r6-prompts-direct-additions.tsv": "5818fbfb0b2b36cb534985712ed8d9f6504b7d8e",
}
EXPECTED_TSV_FIELDS = (
    "repository",
    "path",
    "blob_sha",
    "depth",
    "scope",
    "line_ranges",
    "execution_evidence",
)
EXPECTED_OLD_SUMMARY = {
    "source_leaf_total": 4325,
    "active_repository_leaf_total": 4324,
    "ledger_sha256": "ff5c6621a78c14fc17802ecf01b4ef815867ccab95acce90c490973946d6279b",
    "scoped_review_paths": 294,
    "grouped_revalidated_paths": 113,
    "semantically_classified_paths": 407,
    "unverified_semantics_total": 3918,
}
EXPECTED_PROJECTION = {
    "source_archive_leaves": 4361,
    "direct": 308,
    "grouped": 113,
    "unverified": 3940,
    "semantically_classified": 421,
    "meta": {"leaves": 210, "direct": 95, "grouped": 0, "unverified": 115},
}
EXPECTED_VALIDATION = {
    "meta_ci_run": 34787598536,
    "meta_gate_job": 103805804171,
    "status": "SUCCESS",
    "integration_capability_tests": 19,
    "governed_executor_tests": 22,
    "native_merge_queue_regressions": 11,
    "central_agent_policy": "PASS",
}
EXPECTED_IDENTITY = {
    "workflow_run": 34787598530,
    "job": 103805803939,
    "result_sha256": "bb592edba0090a218b7c979791be495f59698112544c3768e4884c35e84ef5ea",
    "meta_leaf_count": 210,
    "organization_source_archive_leaf_count": 4361,
    "added": 36,
    "modified": 9,
    "removed": 0,
}


class CandidateError(ValueError):
    pass


def _pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CandidateError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _json_bytes(path: Path, *, label: str = "JSON") -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    try:
        data = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs_hook)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CandidateError(f"{label} invalid: {exc}") from exc
    if not isinstance(data, dict):
        raise CandidateError(f"{label} root must be an object")
    return raw, data


def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()


def _run(*args: str) -> bytes:
    return subprocess.check_output(("git",) + args, cwd=ROOT)


def _ls_tree(commit: str) -> tuple[str, dict[str, tuple[str, str]]]:
    tree = _run("show", "-s", "--format=%T", commit).decode().strip()
    rows: dict[str, tuple[str, str]] = {}
    raw = _run("ls-tree", "-r", "-z", "--full-tree", commit)
    for record in raw.split(b"\0"):
        if not record:
            continue
        meta, path = record.split(b"\t", 1)
        mode, kind, sha = meta.decode().split()
        if mode in {"100644", "100755", "120000", "160000"}:
            rows[path.decode("utf-8")] = (mode, sha)
    return tree, rows


def _tsv_rows(path: Path, *, expected_blob_sha: str | None = None) -> list[dict[str, str]]:
    raw = path.read_bytes()
    if expected_blob_sha is not None and git_blob_sha(raw) != expected_blob_sha:
        raise CandidateError(f"prior DIRECT TSV blob drift: {path.name}")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CandidateError(f"TSV is not UTF-8: {path.name}") from exc
    reader = csv.DictReader(text.splitlines(), delimiter="\t")
    if tuple(reader.fieldnames or ()) != EXPECTED_TSV_FIELDS:
        raise CandidateError(f"TSV header drift: {path.name}")
    rows = list(reader)
    if not all(set(row) == set(EXPECTED_TSV_FIELDS) for row in rows):
        raise CandidateError(f"TSV row shape drift: {path.name}")
    return rows


def _direct_meta_rows(evidence_root: Path = EVIDENCE_ROOT) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for name, expected_blob in DIRECT_TSV_BLOBS.items():
        for row in _tsv_rows(evidence_root / name, expected_blob_sha=expected_blob):
            if row.get("repository") != "meta":
                continue
            path = row["path"]
            if path in result:
                raise CandidateError(f"duplicate R6 META DIRECT path: {path}")
            result[path] = row
    if len(result) != 81:
        raise CandidateError(f"expected 81 R6 META DIRECT rows, got {len(result)}")
    return result


def _entries(candidate: dict[str, Any], key: str) -> list[dict[str, str]]:
    block = candidate.get("candidate")
    if not isinstance(block, dict):
        raise CandidateError("candidate block missing")
    rows = block.get(key)
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise CandidateError(f"{key} must be a list of objects")
    normalized: list[dict[str, str]] = []
    for row in rows:
        if set(row) != {"path", "blob_sha"}:
            raise CandidateError(f"{key} row keys drift")
        path, sha = row["path"], row["blob_sha"]
        if (
            not isinstance(path, str)
            or not path
            or not isinstance(sha, str)
            or len(sha) != 40
            or any(char not in "0123456789abcdef" for char in sha)
        ):
            raise CandidateError(f"{key} row invalid")
        normalized.append({"path": path, "blob_sha": sha})
    return normalized


def validate_document(doc: dict[str, Any]) -> None:
    for key in (
        "coverage_adopted",
        "adoption_performed",
        "product_readiness_claimed",
        "organization_audit_completion_claimed",
    ):
        if doc.get(key) is not False:
            raise CandidateError(f"{key} must remain false")
    if doc.get("independent_review_required") is not True:
        raise CandidateError("independent review must remain required")
    if doc.get("schema_version") != 1 or doc.get("status") != "DIRECT_CANDIDATE_ONLY_NOT_ADOPTED":
        raise CandidateError("candidate status/schema drift")
    if doc.get("source") != {
        "repository": "Oteryn/Oteryn",
        "commit_sha": SOURCE_COMMIT,
        "tree_sha": SOURCE_TREE,
    }:
        raise CandidateError("source identity drift")
    if doc.get("identity_rebaseline") != EXPECTED_IDENTITY:
        raise CandidateError("identity rebaseline drift")
    if doc.get("exact_head_validation") != EXPECTED_VALIDATION:
        raise CandidateError("exact-head validation drift")
    if doc.get("projection_if_adopted") != EXPECTED_PROJECTION:
        raise CandidateError("projection drift")
    historical = doc.get("historical_evidence_family")
    if historical != {
        "prefix": HISTORICAL_PREFIX,
        "path_count": 26,
        "state": "UNVERIFIED",
        "reason": "tracked current-tree identity but historical package assertions are not automatically current live authority",
    }:
        raise CandidateError("historical evidence family drift")
    block = doc.get("candidate")
    if not isinstance(block, dict) or block.get("path_count") != 19 or block.get("proposed_state") != "DIRECT":
        raise CandidateError("candidate path count/state drift")
    scopes = block.get("semantic_scope")
    if (
        not isinstance(scopes, dict)
        or set(scopes)
        != {
            "human_and_machine_policy",
            "merge_queue",
            "capability_routing",
            "executor",
            "tests",
            "program_record",
        }
        or not all(isinstance(value, str) and value.strip() for value in scopes.values())
    ):
        raise CandidateError("semantic scope drift")
    limitations = doc.get("limitations")
    if (
        not isinstance(limitations, list)
        or len(limitations) != 3
        or not all(isinstance(value, str) and value.strip() for value in limitations)
    ):
        raise CandidateError("limitations drift")
    combined = (
        _entries(doc, "previous_direct_modified")
        + _entries(doc, "previous_unverified_modified")
        + _entries(doc, "new_active_governance")
    )
    paths = [row["path"] for row in combined]
    if len(paths) != 19 or len(set(paths)) != 19:
        raise CandidateError("candidate path set must contain exactly 19 unique paths")


def _has_r7_adoption_marker(value: object) -> bool:
    if isinstance(value, dict):
        return any(_has_r7_adoption_marker(key) or _has_r7_adoption_marker(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_has_r7_adoption_marker(item) for item in value)
    if not isinstance(value, str):
        return False
    normalized = value.casefold().replace("-", "_")
    return (
        ("r7" in normalized and "adopt" in normalized)
        or ("current_main_governance" in normalized and "adopt" in normalized)
        or ("meta_current_main_governance" in normalized and "coverage_review" in normalized)
    )


def _validate_old_summary(summary: dict[str, Any]) -> None:
    for key, expected in EXPECTED_OLD_SUMMARY.items():
        if summary.get(key) != expected:
            raise CandidateError(f"candidate-only coverage summary drift: {key}")
    meta = summary.get("per_repository", {}).get("meta") if isinstance(summary.get("per_repository"), dict) else None
    if meta != {
        "leaves": 174,
        "direct_scoped": 81,
        "unverified_semantics": 93,
        "grouped": 0,
        "not_applicable": 0,
    }:
        raise CandidateError("candidate-only META summary must remain on R6 source/accounting")
    if summary.get("semantic_coverage") != "PARTIAL_EXPLICIT" or summary.get("semantic_completion_claimed") is not False:
        raise CandidateError("candidate-only semantic completion state drift")


def _validate_old_collection_plan(plan: dict[str, Any]) -> None:
    snapshots = plan.get("snapshots")
    if not isinstance(snapshots, list):
        raise CandidateError("collection plan snapshots missing")
    meta_rows = [row for row in snapshots if isinstance(row, dict) and row.get("id") == "meta"]
    if len(meta_rows) != 1 or meta_rows[0] != {
        "id": "meta",
        "repository": "Oteryn/Oteryn",
        "commit_sha": OLD_COMMIT,
        "expected_tree_sha": OLD_TREE,
        "role": "audited_source",
    }:
        raise CandidateError("candidate-only collection plan must retain pinned R6 META source")


def validate_candidate_only_state(
    doc: dict[str, Any],
    *,
    evidence_root: Path = EVIDENCE_ROOT,
    report_path: Path = REPORT,
) -> None:
    if (evidence_root / OVERLAY_NAME).exists() or (evidence_root / OVERLAY_NAME).is_symlink():
        raise CandidateError("candidate-only state cannot coexist with R7 adoption overlay")

    prior_direct = _direct_meta_rows(evidence_root)
    prior_direct_candidate = {row["path"]: row["blob_sha"] for row in _entries(doc, "previous_direct_modified")}
    new_direct_paths = {
        row["path"]
        for row in _entries(doc, "previous_unverified_modified") + _entries(doc, "new_active_governance")
    }

    for path in sorted(evidence_root.glob("coverage-review*.tsv")):
        rows = _tsv_rows(path)
        for row in rows:
            if row.get("repository") != "meta":
                continue
            candidate_path = row.get("path")
            if candidate_path in new_direct_paths:
                raise CandidateError(f"candidate-only state contains R7 DIRECT adoption row in {path.name}: {candidate_path}")
            current_blob = prior_direct_candidate.get(candidate_path or "")
            if current_blob is not None and row.get("blob_sha") == current_blob:
                raise CandidateError(f"candidate-only state contains implicit R7 DIRECT blob refresh in {path.name}: {candidate_path}")

    for candidate_path in prior_direct_candidate:
        if candidate_path not in prior_direct:
            raise CandidateError(f"prior DIRECT row disappeared: {candidate_path}")

    _, groups = _json_bytes(evidence_root / "coverage-groups.json", label="coverage groups")
    serialized_groups = json.dumps(groups, sort_keys=True)
    all_candidate_paths = {
        row["path"]
        for key in ("previous_direct_modified", "previous_unverified_modified", "new_active_governance")
        for row in _entries(doc, key)
    }
    if any(path in serialized_groups for path in all_candidate_paths):
        raise CandidateError("candidate-only state cannot coexist with R7 GROUPED classification")

    _, report = _json_bytes(report_path, label="canonical report")
    meta_report = report.get("repositories", {}).get("meta") if isinstance(report.get("repositories"), dict) else None
    if meta_report != {
        "repository": "Oteryn/Oteryn",
        "commit_sha": OLD_COMMIT,
        "tree_sha": OLD_TREE,
        "leaf_count": 174,
    }:
        raise CandidateError("candidate-only canonical report must retain R6 META source identity")
    if (
        report.get("scoped_review_paths") != 294
        or report.get("grouped_revalidated_paths") != 113
        or report.get("semantically_classified_paths") != 407
    ):
        raise CandidateError("candidate-only canonical report accounting drift")
    if _has_r7_adoption_marker(report):
        raise CandidateError("candidate-only canonical report contains R7 adoption representation")

    _, index = _json_bytes(evidence_root / "verification-index.json", label="verification index")
    if _has_r7_adoption_marker(index):
        raise CandidateError("candidate-only verification index contains R7 adoption representation")

    _, summary = _json_bytes(evidence_root / "coverage-summary.json", label="coverage summary")
    _validate_old_summary(summary)

    _, plan = _json_bytes(evidence_root / "collection-plan.json", label="collection plan")
    _validate_old_collection_plan(plan)


def validate_repository(doc: dict[str, Any]) -> None:
    old_tree, old_rows = _ls_tree(OLD_COMMIT)
    current_tree, current_rows = _ls_tree(SOURCE_COMMIT)
    if old_tree != OLD_TREE or current_tree != SOURCE_TREE:
        raise CandidateError("source tree identity mismatch")

    direct = _direct_meta_rows()
    direct_rows = _entries(doc, "previous_direct_modified")
    old_unverified_rows = _entries(doc, "previous_unverified_modified")
    new_rows = _entries(doc, "new_active_governance")
    if len(direct_rows) != 5 or len(old_unverified_rows) != 4 or len(new_rows) != 10:
        raise CandidateError("candidate family counts drift")
    for row in direct_rows:
        if row["path"] not in direct:
            raise CandidateError(f"previous DIRECT state not proven: {row['path']}")
    for row in old_unverified_rows:
        if row["path"] in direct:
            raise CandidateError(f"previous UNVERIFIED state contradicts DIRECT ledger: {row['path']}")
    for row in new_rows:
        if row["path"] in old_rows:
            raise CandidateError(f"new path already existed in old source: {row['path']}")

    all_candidate = {
        row["path"]: row["blob_sha"]
        for row in direct_rows + old_unverified_rows + new_rows
    }
    for path, expected_sha in all_candidate.items():
        actual = current_rows.get(path)
        if actual is None or actual[1] != expected_sha:
            raise CandidateError(f"current source blob mismatch: {path}")

    changed = _run("diff", "--name-status", "--no-renames", OLD_COMMIT, SOURCE_COMMIT).decode().splitlines()
    added = {line.split("\t", 1)[1] for line in changed if line.startswith("A\t")}
    modified = {line.split("\t", 1)[1] for line in changed if line.startswith("M\t")}
    removed = {line.split("\t", 1)[1] for line in changed if line.startswith("D\t")}
    if (len(added), len(modified), len(removed)) != (36, 9, 0):
        raise CandidateError("source delta counts drift")
    candidate_modified = {row["path"] for row in direct_rows + old_unverified_rows}
    candidate_added = {row["path"] for row in new_rows}
    historical_added = {path for path in added if path.startswith(HISTORICAL_PREFIX)}
    if modified != candidate_modified or candidate_added != (added - historical_added):
        raise CandidateError("candidate does not partition active current-main delta exactly")
    if len(historical_added) != 26:
        raise CandidateError("historical evidence family must contain exactly 26 added paths")

    validate_candidate_only_state(doc)


def validate() -> dict[str, Any]:
    raw, doc = _json_bytes(CANDIDATE, label="candidate JSON")
    if git_blob_sha(raw) != CANDIDATE_BLOB_SHA:
        raise CandidateError("candidate complete-file blob SHA drift")
    validate_document(doc)
    validate_repository(doc)
    return {
        "result": "META_CURRENT_MAIN_GOVERNANCE_DIRECT_CANDIDATE_VALID_NOT_ADOPTED",
        "candidate_paths": 19,
        "historical_evidence_paths_unverified": 26,
        "projected_if_adopted": EXPECTED_PROJECTION,
        "product_readiness_claimed": False,
        "organization_audit_completion_claimed": False,
    }


def main() -> int:
    try:
        print(json.dumps(validate(), sort_keys=True))
    except (CandidateError, OSError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"result": "INVALID", "error": str(exc)}, sort_keys=True))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
