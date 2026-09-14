#!/usr/bin/env python3
"""Fail-closed verifier for the bounded HISTORY-REVALIDATION handoff packet."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = ROOT / "docs/evidence/organization-audit-20260907/history-revalidation-candidate.json"
EXPECTED_BOUNDARIES = [
    {
        "id": "meta", "repository": "Oteryn/Oteryn",
        "historical_commit": "23b21e9b1b2d4b6c3a5cac3d4c7a18747804c090",
        "historical_tree": "b8ebb8e50bce14a736fa65590ac121655c52fd12",
        "current_main_commit": "d9419b05eb98c81279297563c11fc90e4fe708ac",
        "current_main_tree": "cb7e49e772321dbf89fed74e2bc2ac3f28ab37e7",
        "compare_status": "ahead", "ahead_by": 2, "changed_files_reported": 2,
        "compare_file_list_complete": True,
        "compare_path_blob_status_sha256": "039f9e2758bc006149971ccec0e7c7324668af95d65171e1e46e88fc976d3864",
    },
    {
        "id": "game", "repository": "Oteryn/Oteryn-Game",
        "historical_commit": "4d6139083179b8fd8c5d0497b2abf8c2545de599",
        "historical_tree": "49cabfccf7d4876e5bc9276fc5963caa33dab8a5",
        "current_main_commit": "775a09091743af395ecb8f1e440cb9c286bc0dd2",
        "current_main_tree": "bddef2afcb7cf50c5a4c21dfd0c0c8069fbf5936",
        "compare_status": "ahead", "ahead_by": 131, "changed_files_reported": 300,
        "compare_file_list_complete": False,
        "compare_limitation": "GitHub compare returned its 300-file cap; this digest is not a complete changed-path inventory.",
        "compare_path_blob_status_sha256": "e444a9053dac983f0767603fa07037b027e5fb2d6768e6ce777491f2ad34fc93",
    },
    {
        "id": "platform", "repository": "Oteryn/Oteryn-Platform",
        "historical_commit": "de917b3477a1de0667531380de3660e8b2ab59aa",
        "historical_tree": "ffdf2a286d3a39f2344cf2ff53b28e4ef7369a8e",
        "current_main_commit": "84d504c98acc8134eb4c9545711010b74c987974",
        "current_main_tree": "8abbc5e1051710c695205214d4c779291dcfb697",
        "compare_status": "ahead", "ahead_by": 50, "changed_files_reported": 144,
        "compare_file_list_complete": True,
        "compare_path_blob_status_sha256": "050b6effa9d2cf24354602ffe8739eb6394c5f59ad2d2c75000d500b234cc351",
    },
    {
        "id": "atlas", "repository": "Oteryn/Oteryn-Atlas",
        "historical_commit": "f00815858bb5b031c502ad19fb96a05ff66b4d84",
        "historical_tree": "a1009378f8d3950a5ee62fb3ee65041f7d53a1e0",
        "current_main_commit": "be09b84ad96d7e67571a460b55d9546b59bc89a7",
        "current_main_tree": "8666e7ad688ec4ec3063c17e6817843a6e37be55",
        "compare_status": "ahead", "ahead_by": 96, "changed_files_reported": 201,
        "compare_file_list_complete": True,
        "compare_path_blob_status_sha256": "b72b86675870469ac5e8dee1b61e472cb26126544109460374b95f06919554af",
    },
    {
        "id": "migration_archive", "repository": "Oteryn/Oteryn-Platform-Migration-Backup-20260818",
        "historical_commit": "6da4f83ef6a35afbab3332f90d7c7f171d23d235",
        "historical_tree": "dbf8349a21e432df47d1475b8431939bbe94d6e1",
        "current_main_commit": "6da4f83ef6a35afbab3332f90d7c7f171d23d235",
        "current_main_tree": "dbf8349a21e432df47d1475b8431939bbe94d6e1",
        "compare_status": "identical", "ahead_by": 0, "changed_files_reported": 0,
        "compare_file_list_complete": True,
        "compare_path_blob_status_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "repository_archived": True,
    },
]
EXPECTED_CLAIMS = {
    "history_revalidation_closed": False,
    "product_readiness_claimed": False,
    "runtime_readiness_claimed": False,
    "security_remediation_claimed": False,
    "organization_audit_completion_claimed": False,
}
GOVERNED_ASSERTION_KEY_STEMS = (
    "history_revalidation",
    "product_readiness",
    "runtime_readiness",
    "security_remediation",
    "organization_audit",
    "game_compare",
)
EXPECTED_OBSERVED_AT = "2026-09-14T16:23:00Z"
EXPECTED_BASELINE = {
    "repository": "Oteryn/Oteryn",
    "canonical_audit_pr": 185,
    "canonical_audit_head": "2d877271afa8f177983f3c6147472372adca0ed1",
    "worker_pr": 206,
    "worker_seed_head": "c5a410873124adde191514bc86a79ed50583b918",
    "programme_pr": 203,
    "programme_head": "82bc113797ecdc70d79aee628d339136b816e15d",
    "release_comment_id": 5666964258,
}
GAME_CARRY_FORWARD_RULE = (
    "Reject source carry-forward when affected paths, dependent contracts or consumer paths are not exhaustively "
    "compared by blob identity; an API-truncated changed-file list is insufficient."
)
REQUIRED_STATES = {
    "PARTIALLY_REPAIRED", "UNKNOWN_LIVE", "REQUIRES_REVALIDATION",
    "REQUIRES_LIVE_REVALIDATION", "OPEN_QUALIFICATION", "OPEN_INHERITED",
    "REPORTED_OPEN", "OWNER_DECISION_PENDING", "REPORTED_IMPLEMENTED_NOT_REQUALIFIED",
}
EXPECTED_INPUTS = {
    "docs/evidence/organization-audit-20260907/collection-plan.json": ("ad376433710e78591978d4e399e28f8d9eda4b23", "dc67249cc0a20f8e39f6e82c50123938044b4d14ada31926516691511ddca269"),
    "docs/evidence/organization-audit-20260907/r3-native-manifest.json": ("75facd26f0dfa482ad34e2eb410dc32e8ab5ea07", "68518689cd7b9a4b4430f15d4b843757695b73d12b670137f29d8d429d743364"),
    "docs/evidence/organization-audit-20260907/r3-independent-review-corrections.json": ("5a369290e4c438ae1d053cc2cf3511fe03f9ca65", "08b36445baf85ffcbc60896882b7dd9aacb8f250c49d97d65792e9a264954d78"),
    "docs/evidence/organization-audit-20260907/finding-register.tsv": ("0d8a3b61dabb71f75d5ad3bde102ba953eb8d47b", "c5402f1618cfe4cd03d2ad50cd0946ec86f19e834b02128199b31b808cc64e94"),
}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def normalize_key(key: object) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(key).lower()).strip("_")


def reject_duplicate_json_members(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Materialize a JSON object only when every member name is unique."""
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON member: {key}")
        result[key] = value
    return result


def git_blob(path: Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], cwd=ROOT, text=True).strip()


def assertion_strings(value: object, path: tuple[str, ...] = ()):
    """Yield prose and normalized field/value assertions from outside ``claims``."""
    if isinstance(value, str):
        yield value.lower()
    elif isinstance(value, dict):
        for key, item in value.items():
            normalized_key = normalize_key(key)
            next_path = (*path, normalized_key)
            if isinstance(item, (str, bool, int, float)):
                yield f"{' '.join(next_path)} {str(item).lower()}"
            yield from assertion_strings(item, next_path)
    elif isinstance(value, list):
        for item in value:
            yield from assertion_strings(item, path)


def duplicated_governed_claim_keys(value: object) -> set[str]:
    """Return canonical claim keys found anywhere outside the canonical claims object."""
    found: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if key in EXPECTED_CLAIMS:
                found.add(key)
            found.update(duplicated_governed_claim_keys(item))
    elif isinstance(value, list):
        for item in value:
            found.update(duplicated_governed_claim_keys(item))
    return found


def unexpected_governed_assertion_keys(value: object, path: tuple[str, ...] = ()) -> set[str]:
    """Reject machine-readable assertion fields whose complete normalized key path shadows governed claims."""
    found: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = normalize_key(key)
            next_path = (*path, normalized)
            joined_path = "_".join(part for part in next_path if part)
            if any(stem in joined_path for stem in GOVERNED_ASSERTION_KEY_STEMS):
                found.add(".".join(str(part) for part in next_path))
            found.update(unexpected_governed_assertion_keys(item, next_path))
    elif isinstance(value, list):
        for item in value:
            found.update(unexpected_governed_assertion_keys(item, path))
    return found


def validate(path: Path = CANDIDATE) -> dict:
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw, object_pairs_hook=reject_duplicate_json_members)
    require(data.get("schema_version") == 1 and data.get("obligation") == "HISTORY-REVALIDATION", "candidate identity")
    require(data.get("disposition") == "HANDOFF_COMPLETE_OBLIGATION_REMAINS_OPEN", "obligation must remain open")
    require(data.get("observed_at") == EXPECTED_OBSERVED_AT, "observation provenance drift")
    require(data.get("baseline") == EXPECTED_BASELINE, "lifecycle baseline provenance drift")
    boundaries = data.get("source_boundaries", [])
    require([x.get("id") for x in boundaries] == [x["id"] for x in EXPECTED_BOUNDARIES], "source boundary set/order")
    game = boundaries[1]
    stale_rules = data.get("stale_evidence_rejection_rules", [])
    require(
        game.get("compare_file_list_complete") is False
        and game.get("compare_limitation") == EXPECTED_BOUNDARIES[1]["compare_limitation"]
        and GAME_CARRY_FORWARD_RULE in stale_rules,
        "Game compare truncation must fail closed",
    )
    require(boundaries == EXPECTED_BOUNDARIES, "source boundary provenance drift")

    canonical_inputs = data.get("provenance", {}).get("canonical_inputs", [])
    require(isinstance(canonical_inputs, list), "canonical input manifest must be a list")
    require(len(canonical_inputs) == len(EXPECTED_INPUTS), "canonical input manifest cardinality drift")
    paths = [item.get("path") for item in canonical_inputs if isinstance(item, dict)]
    require(len(paths) == len(canonical_inputs) and len(set(paths)) == len(paths), "duplicate canonical input entry")
    inputs = {item["path"]: (item.get("git_blob"), item.get("sha256")) for item in canonical_inputs}
    require(inputs == EXPECTED_INPUTS, "canonical input manifest drift")
    for rel, expected in EXPECTED_INPUTS.items():
        raw_input = (ROOT / rel).read_bytes()
        require((git_blob(ROOT / rel), hashlib.sha256(raw_input).hexdigest()) == expected, f"canonical input bytes drift: {rel}")

    with (ROOT / "docs/evidence/organization-audit-20260907/finding-register.tsv").open(encoding="utf-8") as stream:
        register = list(csv.DictReader(stream, delimiter="\t"))
    expected_ids = {r["id"] for r in register if r["state"] in REQUIRED_STATES}
    actual_ids = set(data.get("claims_requiring_rebind_or_revalidation", {}).get("finding_ids", []))
    require(actual_ids == expected_ids, "revalidation finding set drift")
    claims = data.get("claims", {})
    require(claims == EXPECTED_CLAIMS, "readiness/closure claims must have exact keys and all be false")
    outside_claims = {key: value for key, value in data.items() if key != "claims"}
    require(not duplicated_governed_claim_keys(outside_claims), "governed claim key duplicated outside claims")
    unexpected = unexpected_governed_assertion_keys(outside_claims)
    require(not unexpected, f"unexpected governed assertion key path: {sorted(unexpected)[0] if unexpected else ''}")
    prose = "\n".join(assertion_strings(outside_claims))
    contradictory = (
        r"history[- ]revalidation (?:is |has been )?closed",
        r"(?:product|runtime) readiness (?:is |has been )?(?:claimed|established|proven)",
        r"security remediation (?:is |has been )?(?:claimed|complete|established|proven)",
        r"organization(?:-wide)? audit (?:is |has been )?(?:complete|completed|closed)",
        r"game compare (?:is |was )?(?:complete|exhaustive)",
        r"game (?:file|changed-path|path)(?: list| inventory)? (?:is |was )?(?:complete|exhaustive)",
        r"(?:history revalidation|product readiness|runtime readiness|security remediation|organization(?: wide)? audit(?: completion)?|game compare) true\b",
    )
    require(not any(re.search(pattern, prose) for pattern in contradictory), "contradictory positive assertion")
    stale = " ".join(stale_rules).lower()
    require("digest without retrievable bytes" in stale and "public disclosure remains disclosed" in stale, "stale-evidence rules weakened")
    limits = " ".join(data.get("limitations", [])).lower()
    require("does not close history-revalidation" in limits and "no provider code execution" in limits, "limitations weakened")
    return {"result": "HISTORY_REVALIDATION_HANDOFF_VALID_OBLIGATION_OPEN", "revalidation_findings": len(actual_ids), "source_boundaries": len(boundaries)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, default=CANDIDATE)
    args = parser.parse_args()
    print(json.dumps(validate(args.candidate), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
