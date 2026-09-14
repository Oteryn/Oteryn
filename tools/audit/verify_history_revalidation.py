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
SHA40 = re.compile(r"^[0-9a-f]{40}$")
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

def git_blob(path: Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], cwd=ROOT, text=True).strip()

def validate(path: Path = CANDIDATE) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    require(data.get("schema_version") == 1 and data.get("obligation") == "HISTORY-REVALIDATION", "candidate identity")
    require(data.get("disposition") == "HANDOFF_COMPLETE_OBLIGATION_REMAINS_OPEN", "obligation must remain open")
    boundaries = data.get("source_boundaries", [])
    require([x.get("id") for x in boundaries] == ["meta", "game", "platform", "atlas", "migration_archive"], "source boundary set/order")
    for item in boundaries:
        for field in ("historical_commit", "historical_tree", "current_main_commit", "current_main_tree"):
            require(isinstance(item.get(field), str) and SHA40.fullmatch(item[field]) is not None, f"{item.get('id')} {field}")
        if item["id"] != "migration_archive":
            require(item["historical_commit"] != item["current_main_commit"] and item["compare_status"] == "ahead" and item["ahead_by"] > 0, f"{item['id']} moved boundary")
    game = next(x for x in boundaries if x["id"] == "game")
    require(game.get("compare_file_list_complete") is False and "300-file" in game.get("compare_limitation", ""), "Game compare truncation must fail closed")
    inputs = {x["path"]: (x["git_blob"], x["sha256"]) for x in data.get("provenance", {}).get("canonical_inputs", [])}
    require(inputs == EXPECTED_INPUTS, "canonical input manifest drift")
    for rel, expected in EXPECTED_INPUTS.items():
        raw = (ROOT / rel).read_bytes()
        require((git_blob(ROOT / rel), hashlib.sha256(raw).hexdigest()) == expected, f"canonical input bytes drift: {rel}")
    with (ROOT / "docs/evidence/organization-audit-20260907/finding-register.tsv").open(encoding="utf-8") as stream:
        register = list(csv.DictReader(stream, delimiter="\t"))
    expected_ids = {r["id"] for r in register if r["state"] in REQUIRED_STATES}
    actual_ids = set(data.get("claims_requiring_rebind_or_revalidation", {}).get("finding_ids", []))
    require(actual_ids == expected_ids, "revalidation finding set drift")
    claims = data.get("claims", {})
    require(claims and all(value is False for value in claims.values()), "readiness/closure claims must all be false")
    stale = " ".join(data.get("stale_evidence_rejection_rules", [])).lower()
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
