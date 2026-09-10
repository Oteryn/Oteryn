#!/usr/bin/env python3
"""Fail-closed verifier for the frozen Platform routes direct-read candidate."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE_REL = Path("docs/evidence/organization-audit-20260907/r3-platform-routes-direct-candidate.json")
REVIEW_REL = Path("docs/evidence/organization-audit-20260907/coverage-review.tsv")
GROUPS_REL = Path("docs/evidence/organization-audit-20260907/coverage-groups.json")
SOURCE_COMMIT = "de917b3477a1de0667531380de3660e8b2ab59aa"
ROUTES_TREE = "424f8bae6f7b9de1726f7c62c606b3b0baa15b23"
LEDGER_SHA = "73c458b8e1b2a6a5cf02bedbefec8fe3a11d4f883413ef65f6d8dd56952338f9"

PATH_BLOBS = {
    "routes/api.php": "ba7916913c581d88a23cb19a70060d857606f644",
    "routes/console.php": "c5dc5d63ef514d094b1a6019fc41f764883fb265",
    "routes/internal.php": "5fa537392a6f7400f56f8c2b6f55571dad2ebe90",
    "routes/localization.php": "31d474687f8279ef160abd6e1db27753b3a5b99e",
    "routes/web.php": "339e7573b2bc04c7bdd9183cd739c099448d8421",
    "routes/modules/announcements.php": "452bb9ee7b70b03951ab7c2476dd10e437549c2b",
    "routes/modules/character-profile-preferences.php": "cc0ab9c2cfdc574b2924e6554bbfd65f23571840",
    "routes/modules/downloads.php": "62be2bd4f86e45a6273c15508791db9c6530a61f",
    "routes/modules/editorial-media.php": "77d3997723b3881329cfc439268bff98335c9a68",
    "routes/modules/events.php": "31fd0e8ed50b41f99bedc639d562a9fe2cba47f1",
    "routes/modules/game-catalog.php": "bc29adb9c5ebca9fda1a53c663a35b542a3470b9",
    "routes/modules/homepage-templates.php": "bea4353cb2ad2198f17d4840c4eac337a70da94f",
    "routes/modules/marketplace.php": "6ead81fecf5d99eb231413bea98d8bf097fa05b5",
    "routes/modules/payments.php": "77690386865ea9095c427f96ee7a8e6b863f176a",
    "routes/modules/player-companion.php": "797be13e358bf363a9161951551f0c5949d9cd6f",
    "routes/modules/public-game-statistics.php": "a49899694f117acd0a4eba958053dcbccb860754",
    "routes/modules/public-portal.php": "74b581fb449b77fc3985e46b1734f1913b422cc8",
    "routes/modules/support.php": "cacd43464ab0126d4caef0c1a13da1aacdc90122",
    "routes/modules/wiki.php": "f4a16ac017fd075b54904455bc8b6f05af304053",
}
INCLUDED = ["route methods", "route URIs", "route names", "route middleware",
            "permission middleware declarations", "MFA middleware declarations",
            "throttle declarations", "route constraints", "environment gates",
            "module inclusion declarations", "console command declarations",
            "console schedule declarations"]
EXCLUDED = ["controller and service internals", "framework-global middleware behavior",
            "production reachability", "data authorization internals", "UI and product readiness"]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def json_exact(actual, expected, path="root") -> None:
    require(type(actual) is type(expected), f"{path} JSON type drift")
    if isinstance(expected, dict):
        require(list(actual) == list(expected), f"{path} key set/order drift")
        for key in expected:
            json_exact(actual[key], expected[key], f"{path}.{key}")
    elif isinstance(expected, list):
        require(len(actual) == len(expected), f"{path} list length drift")
        for index, (left, right) in enumerate(zip(actual, expected)):
            json_exact(left, right, f"{path}[{index}]")
    else:
        require(actual == expected, f"{path} value drift")


def read_json(path: Path):
    def pairs(items):
        value = {}
        for key, item in items:
            require(key not in value, "duplicate JSON key: " + key)
            value[key] = item
        return value
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs)


def expected_candidate():
    return {
        "schema_version": 1, "id": "platform-routes-direct-candidate-20260910",
        "repository": "platform", "disposition": "DIRECT_CANDIDATE_ONLY_NOT_ADOPTED",
        "coverage_adopted": False, "review_method": "FRESH_FULL_FILE_DIRECT_READ",
        "source": {"repository": "Oteryn/Oteryn-Platform", "commit_sha": SOURCE_COMMIT,
                   "routes_tree_sha": ROUTES_TREE, "regular_file_count": 19,
                   "top_level_file_count": 5, "module_file_count": 14},
        "paths": [{"path": path, "blob_sha": blob} for path, blob in PATH_BLOBS.items()],
        "semantic_boundary": {"included": INCLUDED, "excluded": EXCLUDED},
        "rejected_history": {"claim": "The old Platform audit prose claimed 21 route files.",
                             "claimed_count": 21, "actual_count": 19,
                             "status": "REJECTED_COUNT_MISMATCH",
                             "accepted_as_evidence": False, "used_for_candidate": False},
        "review_result": {"material_new_findings": [],
                          "finding_severities_reviewed": ["P0", "P1", "P2"],
                          "statement": "The fresh direct review of all 19 immutable route files found no new material P0, P1, or P2 within the bounded route-declaration scope.",
                          "existing_provider_findings_closed": False},
        "canonical_accounting_unchanged": {"source_rows": 4325, "direct_paths": 233,
                                           "grouped_paths": 113, "unverified_paths": 3979,
                                           "semantically_classified_paths": 346,
                                           "ledger_sha256": LEDGER_SHA},
        "limitations": [
            "This candidate is proof-phase evidence only and is not an adoption, coverage promotion, readiness, completion, or provider-remediation claim.",
            "Existing provider findings remain open and are not closed by an absence of new findings in this bounded declaration review.",
            "Canonical accounting and path dispositions remain unchanged until a separately authorized adoption phase.",
        ],
    }


def validate_candidate(candidate) -> None:
    json_exact(candidate, expected_candidate())


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-c", "core.hooksPath=/dev/null", *args], cwd=root,
                          check=True, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, timeout=60).stdout.strip()


def validate_source(platform_root: Path) -> None:
    require(git(platform_root, "rev-parse", "HEAD") == SOURCE_COMMIT, "source commit drift")
    tree = git(platform_root, "ls-tree", "HEAD", "routes").split()
    require(len(tree) >= 3 and tree[1] == "tree" and tree[2] == ROUTES_TREE, "routes tree drift")
    rows = git(platform_root, "ls-tree", "-r", "HEAD", "routes").splitlines()
    require(len(rows) == 19, "routes regular-file count drift")
    observed = {}
    for row in rows:
        head, path = row.split("\t", 1)
        mode, kind, blob = head.split()
        require(mode == "100644" and kind == "blob", "non-regular route entry: " + path)
        require(path not in observed, "duplicate source path: " + path)
        observed[path] = blob
    require(observed == PATH_BLOBS, "source route path/blob set drift")


def grouped_prefixes(groups):
    prefixes = set()
    for group in groups["groups"]:
        if group.get("repository") != "platform" or group.get("disposition") != "GROUPED":
            continue
        prefix = group.get("path_prefix")
        require(isinstance(prefix, str) and prefix, "canonical GROUPED prefix drift")
        prefixes.add(prefix)
    return prefixes


def validate_current_accounting(audit_root: Path) -> None:
    with (audit_root / REVIEW_REL).open(encoding="utf-8", newline="") as handle:
        direct_rows = [row for row in csv.DictReader(handle, delimiter="\t")
                       if row["repository"] == "platform" and row["path"] in PATH_BLOBS]
    require(len(direct_rows) == 19, "canonical DIRECT route row count drift")
    require({row["path"]: row["blob_sha"] for row in direct_rows} == PATH_BLOBS,
            "canonical DIRECT route binding drift")
    prefixes = grouped_prefixes(read_json(audit_root / GROUPS_REL))
    overlap = {path for path in PATH_BLOBS if any(path.startswith(prefix) for prefix in prefixes)}
    require(not overlap, "current DIRECT/GROUPED overlap: " + ", ".join(sorted(overlap)))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-root", type=Path, default=ROOT)
    parser.add_argument("--platform-root", type=Path, required=True)
    args = parser.parse_args()
    candidate = read_json(args.audit_root / CANDIDATE_REL)
    validate_candidate(candidate)
    validate_source(args.platform_root)
    validate_current_accounting(args.audit_root)
    print(json.dumps({"result": "PLATFORM_ROUTES_DIRECT_CANDIDATE_VALID_NOT_ADOPTED",
                      "review_method": "FRESH_FULL_FILE_DIRECT_READ", "route_files": 19,
                      "coverage_adopted": False, "canonical_direct_paths": 233,
                      "canonical_grouped_paths": 113, "canonical_unverified_paths": 3979,
                      "canonical_semantically_classified_paths": 346,
                      "canonical_ledger_sha256": LEDGER_SHA,
                      "product_readiness_claimed": False,
                      "audit_completion_claimed": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
