#!/usr/bin/env python3
"""Fail-closed verifier for the two-file frozen Platform audit-recorder DIRECT candidate.

This verifies source identity, bounded semantic oracles, persistence/test bindings,
pre-adoption non-overlap, and (optionally) a mechanically projected canonical ledger.
It does not execute provider code and never turns DIRECT into product readiness.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
import re
import subprocess
import sys

CANDIDATE_REL = Path("docs/evidence/organization-audit-20260907/r3-platform-audit-recorders-direct-candidate.json")
REVIEW_REL = Path("docs/evidence/organization-audit-20260907/coverage-review.tsv")
SUMMARY_REL = Path("docs/evidence/organization-audit-20260907/coverage-summary.json")
REPORT_REL = Path("docs/evidence/OTERYN-ORGANIZATION-COMPREHENSIVE-AUDIT-20260907.json")
SOURCE_COMMIT = "de917b3477a1de0667531380de3660e8b2ab59aa"
SOURCE_TREE = "ffdf2a286d3a39f2344cf2ff53b28e4ef7369a8e"
EXPECTED_PATHS = {
    "app/Audit/AdminAuditRecorder.php": "78a757d143036aa4c9c13e40c96a9f1fb66cb6a4",
    "app/Audit/SecurityEventRecorder.php": "cdf63637dc6902f575abceeaa106525173f08e5f",
}
EXPECTED_PERSISTENCE = {
    "database/migrations/2026_07_20_093300_create_admin_audit_events_table.php": "7ec89faee81a5e6ecd80a741f39e967389838044",
    "database/migrations/2026_07_19_073601_create_identity_security_events_table.php": "783b83a4c735117f4efbbe94f217c603b2a90815",
}
EXPECTED_TESTS = {
    "tests/Feature/Admin/AdminRoleManagementTest.php": "05bcee51c5a7abd3ddc90cb675db74a768429aa1",
    "tests/Feature/Identity/RegistrationTest.php": "cfb79eeed2ad544166e35724c0ad5cd220c61862",
    "tests/Feature/GameAuth/GameLoginTicketLifecycleTest.php": "1fdf519959d61086f2c32e2415761a4a53369ab4",
}
SHA = re.compile(r"[0-9a-f]{40}\Z")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_json(path: Path) -> dict:
    def pairs(items):
        out = {}
        for key, value in items:
            require(key not in out, "duplicate JSON key: " + key)
            out[key] = value
        return out
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs)
    require(isinstance(value, dict), "JSON root must be object")
    return value


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", *args],
        cwd=cwd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=60,
    ).stdout.strip()


def tree_blob(cwd: Path, path: str) -> str:
    raw = git(cwd, "ls-tree", "HEAD", "--", path)
    require(raw, "source path absent: " + path)
    head, actual_path = raw.split("\t", 1)
    mode, kind, oid = head.split(" ")
    require(actual_path == path and mode == "100644" and kind == "blob" and SHA.fullmatch(oid), "invalid tree entry: " + path)
    return oid


def validate_candidate_shape(c: dict) -> None:
    require(c.get("schema_version") == 1, "candidate schema")
    require(c.get("id") == "platform-audit-recorders-direct-20260909", "candidate id")
    require(c.get("repository") == "platform", "candidate repository")
    require(c.get("disposition") == "DIRECT_CANDIDATE_NOT_ADOPTED", "candidate disposition")
    require(c.get("coverage_adopted") is False, "candidate must remain pre-adoption")
    source = c.get("source") or {}
    require(source.get("repository") == "Oteryn/Oteryn-Platform", "source repository")
    require(source.get("commit_sha") == SOURCE_COMMIT and source.get("tree_sha") == SOURCE_TREE, "source coordinates")

    paths = c.get("paths") or []
    require(isinstance(paths, list) and len(paths) == 2, "exactly two DIRECT candidates required")
    actual = {row.get("path"): row.get("blob_sha") for row in paths}
    require(actual == EXPECTED_PATHS, "candidate path/blob set drift")
    for row in paths:
        require(row.get("depth") == "SCOPED_SEMANTIC_REVIEW", "candidate depth")
        require(isinstance(row.get("scope"), str) and row["scope"].strip(), "candidate scope")
        require(row.get("line_ranges") == [], "this full-file review uses explicit empty bounded line-range metadata")
        tokens = row.get("semantic_assertions")
        require(isinstance(tokens, list) and tokens and all(isinstance(x, str) and x for x in tokens), "semantic assertions")
    security = next(row for row in paths if row["path"].endswith("SecurityEventRecorder.php"))
    require(security.get("expected_public_event_constants") == 31, "security constant count oracle")

    persistence = c.get("persistence_contract") or []
    require({row.get("path"): row.get("blob_sha") for row in persistence} == EXPECTED_PERSISTENCE, "persistence binding drift")
    require(all(row.get("role") == "QUALIFICATION_DEPENDENCY_NOT_PROMOTED_BY_THIS_CANDIDATE" for row in persistence), "persistence role")
    tests = c.get("focused_current_tests") or []
    require({row.get("path"): row.get("blob_sha") for row in tests} == EXPECTED_TESTS, "focused test binding drift")
    require(all(row.get("role") == "REPRESENTATIVE_EXECUTION_DEPENDENCY_NOT_PROMOTED_BY_THIS_CANDIDATE" for row in tests), "test role")

    baseline = c.get("baseline_accounting") or {}
    require(baseline == {
        "source_rows": 4325, "direct_paths": 221, "grouped_paths": 113, "unverified_paths": 3991,
        "semantically_classified_paths": 334, "platform_direct_paths": 156,
        "platform_grouped_paths": 113, "platform_unverified_paths": 1896,
        "ledger_sha256": "25ed5eb371279fbdb16a50263637856a3bc409b775387555efdaa17cebdc3617",
    }, "baseline accounting drift")
    projected = c.get("projected_accounting") or {}
    require(projected == {
        "source_rows": 4325, "direct_paths": 223, "grouped_paths": 113, "unverified_paths": 3989,
        "semantically_classified_paths": 336, "platform_direct_paths": 158,
        "platform_grouped_paths": 113, "platform_unverified_paths": 1894,
        "ledger_sha256": "PENDING_MECHANICAL_REBUILD",
    }, "projected accounting drift")
    qualification = c.get("qualification") or {}
    require(qualification.get("status") == "PENDING_PRIMARY_QUALIFICATION", "qualification must be pending")
    require(qualification.get("workflow_run") is None and qualification.get("job") is None, "unearned qualification identity")
    require(qualification.get("test_files") == 3, "focused test-file count")
    require(all(qualification.get(k) is None for k in ["cases", "assertions", "failures", "errors", "skipped"]), "unearned test totals")
    limits = c.get("limitations") or []
    require(isinstance(limits, list) and len(limits) >= 5, "limitations missing")
    joined = " ".join(limits)
    for phrase in ["not a product or production-readiness PASS", "not an exhaustive execution", "Canonical coverage-review.tsv"]:
        require(phrase in joined, "required limitation missing: " + phrase)


def validate_source_text(path: str, text: str, row: dict) -> None:
    for token in row["semantic_assertions"]:
        require(token in text, f"semantic oracle missing from {path}: {token}")
    if path.endswith("SecurityEventRecorder.php"):
        count = len(re.findall(r"^\s*public const [A-Z0-9_]+\s*=", text, flags=re.MULTILINE))
        require(count == row["expected_public_event_constants"], f"security event constant count drift: {count}")


def validate_platform(c: dict, platform_root: Path) -> None:
    require(git(platform_root, "rev-parse", "HEAD") == SOURCE_COMMIT, "Platform HEAD drift")
    require(git(platform_root, "rev-parse", "HEAD^{tree}") == SOURCE_TREE, "Platform tree drift")
    rows = {row["path"]: row for row in c["paths"]}
    for path, oid in {**EXPECTED_PATHS, **EXPECTED_PERSISTENCE, **EXPECTED_TESTS}.items():
        require(tree_blob(platform_root, path) == oid, "frozen blob identity drift: " + path)
    for path, row in rows.items():
        validate_source_text(path, (platform_root / path).read_text(encoding="utf-8"), row)

    admin_migration = (platform_root / "database/migrations/2026_07_20_093300_create_admin_audit_events_table.php").read_text(encoding="utf-8")
    for token in ["Schema::create('admin_audit_events'", "'actor_identity_id'", "'action', 96", "'target_type', 80", "'target_id', 191", "'metadata'", "'occurred_at'"]:
        require(token in admin_migration, "admin audit persistence oracle missing: " + token)
    security_migration = (platform_root / "database/migrations/2026_07_19_073601_create_identity_security_events_table.php").read_text(encoding="utf-8")
    for token in ["Schema::create('identity_security_events'", "'identity_id'", "'event_type', 100", "'occurred_at'", "['identity_id', 'event_type']"]:
        require(token in security_migration, "security persistence oracle missing: " + token)
    for row in c["focused_current_tests"]:
        text = (platform_root / row["path"]).read_text(encoding="utf-8")
        require(row["required_text"] in text, "focused test lost persistence assertion surface: " + row["path"])


def load_review_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    require(rows, "coverage review empty")
    return rows


def validate_pre_adoption_docs(c: dict, review_rows: list[dict], summary: dict, report: dict) -> None:
    present = {(row.get("repository"), row.get("path")) for row in review_rows}
    for path in EXPECTED_PATHS:
        require(("platform", path) not in present, "candidate already DIRECT before adoption: " + path)
    require(len(review_rows) == 221, "baseline DIRECT row count drift")
    require(report.get("scoped_review_paths") == 221, "report DIRECT baseline drift")
    require(report.get("grouped_revalidated_paths") == 113 and report.get("semantically_classified_paths") == 334, "report grouped/semantic baseline drift")
    require(summary.get("scoped_review_paths") == 221 and summary.get("grouped_revalidated_paths") == 113, "summary baseline coverage drift")
    require(summary.get("semantically_classified_paths") == 334 and summary.get("unverified_semantics_total") == 3991, "summary baseline semantic drift")
    platform = (summary.get("per_repository") or {}).get("platform") or {}
    require(platform.get("leaves") == 2165 and platform.get("direct_scoped") == 156 and platform.get("grouped") == 113 and platform.get("unverified_semantics") == 1896, "Platform baseline accounting drift")
    require(summary.get("ledger_sha256") == c["baseline_accounting"]["ledger_sha256"], "baseline ledger digest drift")


def validate_pre_adoption(c: dict, audit_root: Path) -> None:
    validate_pre_adoption_docs(
        c,
        load_review_rows(audit_root / REVIEW_REL),
        read_json(audit_root / SUMMARY_REL),
        read_json(audit_root / REPORT_REL),
    )


def projected_review_rows(c: dict) -> list[dict]:
    return [
        {
            "repository": "platform",
            "path": row["path"],
            "blob_sha": row["blob_sha"],
            "depth": row["depth"],
            "scope": row["scope"],
            "line_ranges": "[]",
            "execution_evidence": "PLATFORM-AUDIT-RECORDERS-PRIMARY-QUALIFICATION-PENDING-BINDING",
        }
        for row in c["paths"]
    ]


def project_ledger(c: dict, audit_root: Path, inventory_dir: Path) -> dict:
    sys.path.insert(0, str((audit_root / "tools/audit").resolve()))
    import verify_report as vr

    report_path = audit_root / REPORT_REL
    doc = vr.read_json(report_path)
    base = report_path.parent / doc["evidence_directory"]
    review = vr.read_tsv(base / "coverage-review.tsv")
    groups = vr.load_groups(base, doc["repositories"])
    additions = projected_review_rows(c)
    keys = {(row["repository"], row["path"]) for row in review}
    require(all((row["repository"], row["path"]) not in keys for row in additions), "projection overlaps current DIRECT rows")
    raw, grouped_counts = vr.build_ledger(doc, review + additions, groups, inventory_dir)
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8"))))
    counts = Counter(row["disposition"] for row in rows)
    expected = {"DIRECT": 223, "GROUPED": 113, "UNVERIFIED": 3989}
    require(len(rows) == 4325 and dict(counts) == expected, f"projected ledger count drift: rows={len(rows)} counts={dict(counts)}")
    require(grouped_counts.get("platform") == 113, "projected Platform GROUPED drift")
    platform_direct = sum(row["repository_id"] == "platform" and row["disposition"] == "DIRECT" for row in rows)
    platform_unverified = sum(row["repository_id"] == "platform" and row["disposition"] == "UNVERIFIED" for row in rows)
    require(platform_direct == 158 and platform_unverified == 1894, "projected Platform accounting drift")
    return {
        "result": "PLATFORM_AUDIT_RECORDERS_PROJECTED_LEDGER_NOT_ADOPTED_NOT_PRODUCT_PASS",
        "source_rows": len(rows),
        "direct_paths": counts["DIRECT"],
        "grouped_paths": counts["GROUPED"],
        "unverified_paths": counts["UNVERIFIED"],
        "semantically_classified_paths": counts["DIRECT"] + counts["GROUPED"],
        "platform_direct_paths": platform_direct,
        "platform_grouped_paths": grouped_counts["platform"],
        "platform_unverified_paths": platform_unverified,
        "ledger_sha256": hashlib.sha256(raw).hexdigest(),
    }


def run(audit_root: Path, platform_root: Path, inventory_dir: Path | None) -> dict:
    c = read_json(audit_root / CANDIDATE_REL)
    validate_candidate_shape(c)
    validate_pre_adoption(c, audit_root)
    validate_platform(c, platform_root)
    result = {
        "result": "PLATFORM_AUDIT_RECORDERS_DIRECT_CANDIDATE_REVALIDATED_NOT_ADOPTED_NOT_PRODUCT_PASS",
        "source_commit": SOURCE_COMMIT,
        "source_tree": SOURCE_TREE,
        "paths": 2,
        "path_blobs_verified": 2,
        "persistence_bindings_verified": 2,
        "focused_test_files_bound": 3,
        "security_event_constants_verified": 31,
        "coverage_adopted": False,
    }
    if inventory_dir is not None:
        result["projected_ledger"] = project_ledger(c, audit_root, inventory_dir)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-root", type=Path, required=True)
    parser.add_argument("--platform-root", type=Path, required=True)
    parser.add_argument("--inventory-dir", type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.audit_root.resolve(), args.platform_root.resolve(), args.inventory_dir.resolve() if args.inventory_dir else None), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
