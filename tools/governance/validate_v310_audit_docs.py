#!/usr/bin/env python3
"""Fail-closed structural and byte validation for the v3.10 terminal report."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


AUDIT_DIR = Path("docs/governance/audits")
REPORT_NAME = "OTERYN-ORG-AUDIT-v3.10-FINAL-TERMINAL-REPORT.md"
RECORD_NAME = "OTERYN-v3.10-FINAL-TERMINAL-REPORT-VALIDATION.json"
REQUIRED_CLASSES = (
    "root AGENTS", "nested AGENTS/override", "architecture/ADR", "contracts",
    "governance policy", "CI policy", "test strategy", "reusable prompts",
    "one-shot prompts", "task packets", "programmes", "handovers",
    "agent runbooks", "operations runbooks", "recovery/break-glass",
    "review evidence", "release evidence", "migration evidence",
    "generated docs/indexes", "human reference docs",
    "machine-readable policy companions", "documentation/agent validators",
)


def validate(repo_root: Path) -> dict[str, int | str]:
    audit_dir = repo_root / AUDIT_DIR
    report_path = audit_dir / REPORT_NAME
    record_path = audit_dir / RECORD_NAME
    report = report_path.read_bytes()
    record = json.loads(record_path.read_text(encoding="utf-8"))
    digest = hashlib.sha256(report).hexdigest()
    if record.get("artifact") != REPORT_NAME:
        raise ValueError("report validation record has the wrong artifact")
    if record.get("sha256") != digest or record.get("bytes") != len(report):
        raise ValueError("report validation record does not bind the final report bytes")
    text = report.decode("utf-8")
    for marker in ("# Matrix L", "### Matrix L required-class completion ledger", "# G1–G11", "# H1–H14", "REPORT_STRUCTURE = COMPLETE", "OTERYN_ORG_AUDIT_V3_10 = INCOMPLETE"):
        if marker not in text:
            raise ValueError(f"required report marker missing: {marker}")
    for name in REQUIRED_CLASSES:
        if f"| {name} |" not in text:
            raise ValueError(f"Matrix L required class missing: {name}")
    header = "| Required artifact class | META | Game | Platform | Atlas |"
    if header not in text:
        raise ValueError("Matrix L ledger does not cover all permanent repositories")
    gate_section = text.split("# G1–G11", 1)[1].split("# Matrix L", 1)[0]
    rows = [line for line in gate_section.splitlines() if re.match(r"\| G(?:[1-9]|1[01]) \|", line)]
    if len(rows) != 11:
        raise ValueError("G1-G11 ledger must contain exactly 11 rows")
    for row in rows:
        state = row.split("|")[3].strip()
        if state != "PASS" and state != "FAIL" and not state.startswith("UNKNOWN ("):
            raise ValueError(f"gate row lacks PASS/FAIL/UNKNOWN vocabulary: {row}")
    return {"report_sha256": digest, "report_bytes": len(report), "matrix_l_required_classes": len(REQUIRED_CLASSES), "gate_rows": len(rows)}


if __name__ == "__main__":
    result = validate(Path.cwd())
    print(json.dumps(result, sort_keys=True))
