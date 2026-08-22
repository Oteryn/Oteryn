#!/usr/bin/env python3
"""Deterministically validate the Oteryn v3.10 terminal audit report contract."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs/governance/audits/OTERYN-ORG-AUDIT-v3.10-FINAL-TERMINAL-REPORT.md"
RECORD = ROOT / "docs/evidence/OTERYN-ORG-AUDIT-v3.10-TERMINAL-REPORT-VALIDATION-20260822.json"
RUNNER_CAPTURE = ROOT / "docs/evidence/OTERYN-ORG-RUNNER-ACL-LIVE-CLOSEOUT-20260822.json"
RUNNER_DIGEST = ROOT / "docs/evidence/OTERYN-ORG-RUNNER-ACL-LIVE-CLOSEOUT-20260822.json.sha256"

REPOS = ["META", "Game", "Platform", "Atlas"]
CLASSES = [
    "root AGENTS", "nested AGENTS/override", "architecture/ADR", "contracts",
    "governance policy", "CI policy", "test strategy", "reusable prompts",
    "one-shot prompts", "task packets", "programmes", "handovers", "agent runbooks",
    "operations runbooks", "recovery/break-glass", "review evidence", "release evidence",
    "migration evidence", "generated docs/indexes", "human reference docs",
    "machine-readable policy companions", "documentation/agent validators",
]
PLACEMENT_QUESTIONS = [
    "Where does a new reusable prompt go?", "Where does a one-shot prompt go while active?",
    "What happens to a one-shot prompt when complete?", "Where does an optional task packet go?",
    "Where does it go when the Issue closes?", "Where does a handover live and when does it expire?",
    "Where does operational/recovery procedure live?", "Where does review/release/migration evidence live?",
    "Where does generated documentation live?", "Which documents belong only in META?",
    "Which remain provider-local?", "Which paths are checked by CI?",
]
BACKLOG_TYPES = ["DOCUMENTATION_IA", "AGENT_INSTRUCTION", "PROMPT_LIFECYCLE", "TASK_LIFECYCLE", "RUNBOOK", "EVIDENCE_GOVERNANCE", "DOCS_CI"]
ALLOWED_PLACEMENT = {"KEEP", "MOVE", "NEW", "GENERATED", "OPTIONAL", "REMOVE_AFTER_MIGRATION", "NOT_NEEDED"}
ALLOWED_H = {"CONFIRMED", "RESOLVED", "CHANGED", "UNKNOWN"}
def table_rows(text: str, marker: str) -> list[list[str]]:
    lines = text.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == marker)
    except StopIteration as exc:
        raise ValueError(f"missing table marker: {marker}") from exc
    rows: list[list[str]] = []
    seen_header = False
    for line in lines[start + 1:]:
        if not line.strip():
            if seen_header and rows:
                break
            continue
        if not line.startswith("|"):
            if seen_header and rows:
                break
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not seen_header:
            seen_header = True
            continue
        if cells and all(re.fullmatch(r":?-+:?", cell or "-") for cell in cells):
            continue
        rows.append(cells)
    return rows


def state_from_rows(rows: list[list[str]], artifact: str) -> tuple[str, list[str]]:
    states = [row[3] for row in rows if len(row) >= 4 and row[1] == artifact]
    if not states:
        return "FAIL", [f"missing lifecycle rows for {artifact}"]
    gaps = sorted({m.group(0) for state in states for m in re.finditer(r"GAP-[A-Z0-9-]+", state)})
    if any(state.startswith("UNKNOWN") for state in states):
        return "UNKNOWN", gaps
    if all(state.startswith("PASS") for state in states):
        return "PASS", []
    return "FAIL", [f"unexpected lifecycle state: {state}" for state in states]


def invariant(state: str, evidence: str, gaps: list[str] | None = None) -> dict:
    result = {"state": state, "evidence": evidence}
    if gaps:
        result["gap_ids"] = gaps
    return result


def sha256(path: Path) -> str:
    # Git normalizes repository text to LF; hash canonical repository bytes.
    data = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()
def build_record() -> dict:
    text = REPORT.read_text(encoding="utf-8")
    lines = text.splitlines()
    errors: list[str] = []

    sections = [int(m.group(1)) for line in lines if (m := re.match(r"^## (\d+)\.", line))]
    if sections != list(range(1, 22)):
        errors.append(f"numbered sections are not exactly 1..21: {sections}")

    matrices: list[str] = []
    in_matrix = False
    for line in lines:
        if line.startswith("# Matrix A0"):
            in_matrix = True
            continue
        if in_matrix and line.startswith("# H1-H14"):
            break
        if in_matrix and (m := re.match(r"^\| (A0|[A-L]) \|", line)):
            matrices.append(m.group(1))
    if matrices != ["A0", *list("ABCDEFGHIJKL")]:
        errors.append(f"matrix ledger mismatch: {matrices}")

    hstates: dict[str, str] = {}
    for line in lines:
        if m := re.match(r"^\| (H(?:[1-9]|1[0-4])) \| .*? \| ([A-Z]+) \|", line):
            hstates[m.group(1)] = m.group(2)
    if list(hstates) != [f"H{i}" for i in range(1, 15)]:
        errors.append(f"H1-H14 ledger incomplete: {list(hstates)}")
    if set(hstates.values()) - ALLOWED_H:
        errors.append(f"invalid H verdicts: {hstates}")

    grows: dict[str, str] = {}
    for line in lines:
        if m := re.match(r"^\| (G(?:[1-9]|1[01])) [^|]+ \| ([^|]+) \|", line):
            grows[m.group(1)] = m.group(2).strip()
    if list(grows) != [f"G{i}" for i in range(1, 12)]:
        errors.append(f"G1-G11 ledger incomplete: {list(grows)}")
    for gate, state in grows.items():
        if state in {"PASS", "FAIL"}:
            continue
        if not re.fullmatch(r"UNKNOWN \(GAP-[^)]+\)", state):
            errors.append(f"invalid terminal state for {gate}: {state}")

    matrix_l = table_rows(text, "| Repository | Artifact class | Current path(s) | Canonical target path / GitHub object | Authority owner | Consumer | Required metadata | Lifecycle / retention | Local copy / override rule | CI / drift enforcement | Migration action | Evidence |")
    by_repo = {repo: [] for repo in REPOS}
    for row in matrix_l:
        if len(row) != 12 or any(not cell for cell in row):
            errors.append(f"invalid Matrix L row: {row}")
            continue
        if row[0] not in by_repo:
            errors.append(f"unexpected Matrix L repository: {row[0]}")
            continue
        by_repo[row[0]].append(row[1])
        if row[1] not in CLASSES:
            errors.append(f"unknown Matrix L class: {row[1]}")
        if "UNKNOWN" in " | ".join(row) and "GAP-" not in " | ".join(row):
            errors.append(f"Matrix L UNKNOWN without GAP-ID: {row}")
    for repo, classes in by_repo.items():
        if classes != CLASSES:
            errors.append(f"Matrix L coverage mismatch for {repo}: {classes}")
    inventory = table_rows(text, "| Repository | Current path/object | Primary class | Normative | Canonical authority | Lifecycle / disposition | Context cost |")
    seen_inventory: set[tuple[str, str]] = set()
    for row in inventory:
        if len(row) != 7 or any(not cell for cell in row):
            errors.append(f"invalid material inventory row: {row}")
            continue
        repo, current, primary, normative, authority, lifecycle, _ = row
        if repo not in REPOS or primary not in CLASSES:
            errors.append(f"invalid inventory repo/class: {row}")
        key = (repo, current)
        if key in seen_inventory:
            errors.append(f"duplicate material inventory path: {key}")
        seen_inventory.add(key)
        if normative not in {"YES", "NO"}:
            errors.append(f"invalid normative flag: {row}")
        if normative == "YES" and authority != repo:
            errors.append(f"normative artifact has non-single/non-owning authority: {row}")
        if "UNKNOWN" in lifecycle and "GAP-" not in lifecycle:
            errors.append(f"inventory lifecycle UNKNOWN without GAP-ID: {row}")

    inventory_classes = {repo: set() for repo in REPOS}
    for row in inventory:
        if len(row) == 7 and row[0] in inventory_classes and row[2] in CLASSES:
            inventory_classes[row[0]].add(row[2])
    for row in matrix_l:
        if len(row) != 12 or row[0] not in inventory_classes:
            continue
        current = row[2]
        if any(token in current for token in ("NOT_NEEDED", "NOT_APPLICABLE", "UNKNOWN")):
            continue
        if row[1] not in inventory_classes[row[0]]:
            errors.append(f"material Matrix L class missing from section 4 inventory: {row[0]}:{row[1]}")

    lifecycle_rows = table_rows(text, "| Repository | Artifact family | Required invariant | Verification state | Lifecycle authority / supersession |")
    prompt_state, prompt_gaps = state_from_rows(lifecycle_rows, "reusable prompts")
    task_state, task_gaps = state_from_rows(lifecycle_rows, "active task packets")
    handover_state, handover_gaps = state_from_rows(lifecycle_rows, "handovers")
    for row in lifecycle_rows:
        if len(row) != 5 or any(not cell for cell in row):
            errors.append(f"invalid lifecycle verification row: {row}")
        if len(row) >= 4 and row[3].startswith("UNKNOWN") and "GAP-" not in row[3]:
            errors.append(f"lifecycle UNKNOWN without GAP-ID: {row}")

    evidence_rows = [row for row in matrix_l if len(row) == 12 and row[1] in {"review evidence", "release evidence", "migration evidence"}]
    evidence_retention_ok = len(evidence_rows) == 12 and all(
        any(token in row[7].lower() for token in ("retain", "append", "historical", "not_needed", "not_applicable"))
        for row in evidence_rows
    )
    if not evidence_retention_ok:
        errors.append("not every evidence class has an explicit retention/disposition rule")

    placement = table_rows(text, "| Placement question | META | Game | Platform | Atlas |")
    if [row[0] for row in placement] != PLACEMENT_QUESTIONS:
        errors.append(f"section-26A placement questions incomplete: {[row[0] for row in placement]}")
    for row in placement:
        if len(row) != 5 or any(not cell for cell in row):
            errors.append(f"invalid placement row: {row}")
            continue
        for answer in row[1:]:
            m = re.match(r"^`?\[([A-Z_]+)\]`?", answer)
            if not m or m.group(1) not in ALLOWED_PLACEMENT:
                errors.append(f"invalid target-tree disposition: {answer}")
    empty_taxonomy_ok = all("[NEW]" not in answer for row in placement for answer in row[1:])
    if not empty_taxonomy_ok:
        errors.append("target tree creates NEW taxonomy without a proven need")
    dispositions = table_rows(text, "| Repository | Current file/path | Primary class | Target / disposition | Authority | Acceptance / evidence |")
    disposition_repos = {repo for row in dispositions if len(row) == 6 for repo in [row[0]]}
    if disposition_repos != set(REPOS):
        errors.append(f"section 15 lacks provider documentation dispositions: {disposition_repos}")
    for row in dispositions:
        if len(row) != 6 or any(not cell for cell in row):
            errors.append(f"invalid section 15 disposition row: {row}")
            continue
        if row[0] not in REPOS or row[2] not in CLASSES:
            errors.append(f"invalid section 15 repo/class: {row}")
        if not re.match(r"^`?\[(KEEP|KEEP/CLEANUP|MOVE|NEW|GENERATED|OPTIONAL|REMOVE_AFTER_MIGRATION|NOT_NEEDED)\]`?", row[3]):
            errors.append(f"invalid section 15 disposition: {row[3]}")

    backlog = table_rows(text, "| Order | Type | CURRENT_PATHS | TARGET_PATHS | AUTHORITY_OWNER | MIGRATION/DISPOSITION | BACKWARD_LINK_OR_REDIRECT_PLAN | ACCEPTANCE_CRITERIA | DETERMINISTIC_VALIDATION | ROLLBACK |")
    backlog_types = [row[1] for row in backlog if len(row) == 10]
    if backlog_types != BACKLOG_TYPES:
        errors.append(f"mandatory documentation backlog mismatch: {backlog_types}")
    for row in backlog:
        if len(row) != 10 or any(not cell for cell in row):
            errors.append(f"invalid documentation backlog row: {row}")

    matrix_access_gaps = sorted({
        m.group(0)
        for row in matrix_l + lifecycle_rows
        for cell in row
        for m in re.finditer(r"GAP-[A-Z0-9-]+", cell)
    })
    backlog_text = "\n".join(" | ".join(row) for row in backlog)
    unmapped_doc_gaps = [gap for gap in matrix_access_gaps if gap not in backlog_text]
    if unmapped_doc_gaps:
        errors.append(f"documentation/agent GAP-IDs missing ordered section 19 remediation: {unmapped_doc_gaps}")

    g11_ok = "G11" in grows and (grows["G11"] == "PASS" or "GAP-" in grows["G11"])
    if not g11_ok:
        errors.append("G11 result missing or lacks explicit GAP-ID")

    actual_runner = sha256(RUNNER_CAPTURE)
    expected_runner = RUNNER_DIGEST.read_text(encoding="utf-8").split()[0]
    if actual_runner != expected_runner:
        errors.append("runner capture digest mismatch")

    invariants = {
        "matrix_l_exists": invariant("PASS" if matrix_l else "FAIL", f"{len(matrix_l)} Matrix L rows"),
        "matrix_l_covers_all_four_repositories": invariant("PASS" if all(by_repo[r] == CLASSES for r in REPOS) else "FAIL", "4 repositories x 22 classes"),
        "material_artifacts_have_primary_class": invariant("PASS" if inventory and not any(e.startswith("invalid material inventory") or e.startswith("duplicate material") for e in errors) else "FAIL", f"{len(inventory)} material path/object families"),
        "normative_artifacts_have_single_authority": invariant("PASS" if inventory and not any("normative artifact" in e for e in errors) else "FAIL", "section 4 normative inventory authority column"),
        "retained_reusable_prompts_have_identity_version_status": invariant(prompt_state, "section 7 lifecycle verification", prompt_gaps),
        "active_task_packets_have_lifecycle_authority": invariant(task_state, "section 7 lifecycle verification", task_gaps),
        "handovers_are_non_authoritative_and_expire": invariant(handover_state, "section 7 lifecycle verification", handover_gaps),
        "evidence_classes_have_retention_disposition": invariant("PASS" if evidence_retention_ok else "FAIL", f"{len(evidence_rows)} repository/evidence-class rows"),
        "target_trees_answer_section_26A": invariant("PASS" if len(placement) == 12 else "FAIL", f"{len(placement)}/12 placement questions"),
        "no_empty_taxonomy_created_for_symmetry": invariant("PASS" if empty_taxonomy_ok else "FAIL", "no [NEW] target-tree entry without proven need"),
        "documentation_agent_access_gaps_are_explicit": invariant("PASS" if matrix_access_gaps else "FAIL", "GAP-IDs parsed from Matrix L/lifecycle ledger", matrix_access_gaps),
        "documentation_agent_gaps_have_ordered_backlog": invariant("PASS" if not unmapped_doc_gaps else "FAIL", "all Matrix L/lifecycle GAP-IDs appear in section 19 remediation backlog"),
        "g11_result_present": invariant("PASS" if g11_ok else "FAIL", grows.get("G11", "missing")),
        "section_15_file_dispositions_present": invariant("PASS" if disposition_repos == set(REPOS) else "FAIL", f"{len(dispositions)} documentation/agent disposition rows"),
        "section_19_required_backlog_categories_present": invariant("PASS" if backlog_types == BACKLOG_TYPES else "FAIL", ", ".join(backlog_types)),
    }
    hard_fail = bool(errors) or any(item["state"] == "FAIL" for item in invariants.values())
    unresolved = sorted({gap for item in invariants.values() for gap in item.get("gap_ids", [])})
    return {
        "schema_version": 2,
        "validator": "tools/governance/validate_v310_terminal_report.py",
        "report": str(REPORT.relative_to(ROOT)).replace("\\", "/"),
        "report_sha256": sha256(REPORT),
        "execution_verdict": "FAIL" if hard_fail else "PASS",
        "programme_verdict": "INCOMPLETE",
        "contract_completeness": "INCOMPLETE" if unresolved else "COMPLETE",
        "numbered_sections": len(sections),
        "matrices": matrices,
        "regression_hypotheses": hstates,
        "final_gates": grows,
        "matrix_l_rows": len(matrix_l),
        "matrix_l_rows_by_repo": {repo: len(by_repo[repo]) for repo in REPOS},
        "material_inventory_rows": len(inventory),
        "section_15_disposition_rows": len(dispositions),
        "section_19_documentation_backlog_types": backlog_types,
        "runner_capture_sha256": actual_runner,
        "mechanical_invariants": invariants,
        "explicit_gap_ids": unresolved,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-record", action="store_true")
    args = parser.parse_args()
    record = build_record()
    if record["execution_verdict"] != "PASS":
        print(json.dumps(record, indent=2, ensure_ascii=False))
        return 1
    rendered = json.dumps(record, indent=2, ensure_ascii=False) + "\n"
    if args.write_record:
        RECORD.write_text(rendered, encoding="utf-8")
        print(f"wrote {RECORD.relative_to(ROOT)}")
    else:
        try:
            stored = json.loads(RECORD.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            raise SystemExit(f"validation record missing/invalid: {exc}") from exc
        if stored != record:
            print("validation record is stale; run with --write-record", file=__import__("sys").stderr)
            print(json.dumps(record, indent=2, ensure_ascii=False))
            return 1
    print(
        "v3.10 terminal report validation PASS: "
        f"21 sections, {len(record['matrices'])} matrices, 14 hypotheses, 11 gates, "
        f"{record['matrix_l_rows']} Matrix L rows; contract remains {record['contract_completeness']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
