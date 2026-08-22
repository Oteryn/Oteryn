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
REQUIRED_RECORD_CHECKS = {
    "report_title",
    "matrix_l",
    "matrix_l_all_required_classes_disposed",
    "all_four_permanent_repositories_disposed",
    "h1_to_h14",
    "g1_to_g11",
    "gate_state_vocabulary_pass_fail_unknown",
    "unknowns_have_gap_ids",
    "report_structure_complete",
    "terminal_verdict_fail_closed",
    "fences_balanced",
    "ends_in_terminal_verdict",
}


def _table_rows(section: str, pattern: str) -> list[str]:
    return [line for line in section.splitlines() if re.match(pattern, line)]


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
    if not text.startswith("# OTERYN-ORG-AUDIT-v3.10 — final terminal audit report\n"):
        raise ValueError("report title is not the required v3.10 terminal title")
    checks = record.get("checks")
    if not isinstance(checks, dict) or set(checks) != REQUIRED_RECORD_CHECKS:
        raise ValueError("report validation record checks are incomplete or unexpected")
    if any(value is not True for value in checks.values()):
        raise ValueError("report validation record may advertise only proven true checks")
    for marker in ("# Matrix L", "### Matrix L required-class completion ledger", "# G1–G11", "# H1–H14", "REPORT_STRUCTURE = COMPLETE", "OTERYN_ORG_AUDIT_V3_10 = INCOMPLETE"):
        if marker not in text:
            raise ValueError(f"required report marker missing: {marker}")
    sections = re.findall(r"^## ([1-9]|1[0-9]|2[01])\. .+$", text, flags=re.MULTILINE)
    if sections != [str(number) for number in range(1, 22)]:
        raise ValueError("report must contain exactly ordered sections 1 through 21")
    fence_count = sum(line.strip() == "```" for line in text.splitlines())
    if fence_count % 2:
        raise ValueError("report Markdown fences are unbalanced")
    if not text.rstrip().endswith("`OTERYN_ORG_AUDIT_V3_10 = INCOMPLETE`"):
        raise ValueError("report must end with the fail-closed terminal verdict")
    for name in REQUIRED_CLASSES:
        if f"| {name} |" not in text:
            raise ValueError(f"Matrix L required class missing: {name}")
    header = "| Required artifact class | META | Game | Platform | Atlas |"
    if header not in text:
        raise ValueError("Matrix L ledger does not cover all permanent repositories")
    ledger_section = text.split("### Matrix L required-class completion ledger", 1)[1].split("## Mechanical completion statement", 1)[0]
    class_rows = [
        row for row in _table_rows(ledger_section, r"\| [^|]+ \|")
        if row.split("|")[1].strip() in REQUIRED_CLASSES
    ]
    if len(class_rows) != len(REQUIRED_CLASSES):
        raise ValueError("Matrix L required-class ledger must contain every required class once")
    for row in class_rows:
        if len(row.split("|")) != 7 or any(not cell.strip() for cell in row.split("|")[1:-1]):
            raise ValueError(f"Matrix L required-class row is incomplete: {row}")
    h_section = text.split("# H1–H14", 1)[1].split("# G1–G11", 1)[0]
    h_rows = _table_rows(h_section, r"\| H(?:[1-9]|1[0-4]) \|")
    if len(h_rows) != 14:
        raise ValueError("H1-H14 ledger must contain exactly 14 rows")
    if {row.split("|")[1].strip() for row in h_rows} != {f"H{number}" for number in range(1, 15)}:
        raise ValueError("H1-H14 ledger has missing or duplicate gate identities")
    gate_section = text.split("# G1–G11", 1)[1].split("# Matrix L", 1)[0]
    rows = _table_rows(gate_section, r"\| G(?:[1-9]|1[01]) \|")
    if len(rows) != 11:
        raise ValueError("G1-G11 ledger must contain exactly 11 rows")
    unknown_gate_rows = 0
    for row in rows:
        state = row.split("|")[3].strip()
        if state.startswith("UNKNOWN (GAP-ID: ") and "V310-" in state:
            unknown_gate_rows += 1
        elif state != "PASS" and state != "FAIL":
            raise ValueError(f"gate row lacks PASS/FAIL/UNKNOWN vocabulary: {row}")
    unknown_cells = re.findall(r"UNKNOWN \(([^)]*)\)", text)
    if not unknown_cells or any("V310-" not in cell for cell in unknown_cells):
        raise ValueError("every UNKNOWN report state must carry a V310 gap identifier")
    return {
        "report_sha256": digest,
        "report_bytes": len(report),
        "matrix_l_required_classes": len(REQUIRED_CLASSES),
        "gate_rows": len(rows),
        "h_rows": len(h_rows),
        "numbered_sections": len(sections),
        "unknown_gate_rows": unknown_gate_rows,
        "validation_checks": len(checks),
    }


if __name__ == "__main__":
    result = validate(Path.cwd())
    print(json.dumps(result, sort_keys=True))
