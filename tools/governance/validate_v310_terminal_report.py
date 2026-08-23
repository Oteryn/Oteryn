#!/usr/bin/env python3
"""Deterministically validate the Oteryn v3.10 terminal audit report contract."""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO_STRUCTURE_ROOT = Path(__file__).resolve().parents[2]
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
OPERATIONAL_PRIMARY_CLASSES = {
    "NORMATIVE_AGENT_INSTRUCTION", "GOVERNANCE_POLICY", "MACHINE_READABLE_POLICY",
    "ARCHITECTURE_ADR", "CROSS_REPO_CONTRACT", "PROVIDER_CONTRACT", "CI_POLICY",
    "TEST_STRATEGY", "RUNBOOK_OPERATIONAL", "RUNBOOK_RECOVERY", "PROMPT_REUSABLE",
    "PROMPT_TASK_EXECUTION", "PROMPT_ONE_SHOT", "TASK_PACKET_ACTIVE",
    "TASK_PACKET_ARCHIVED", "PROGRAMME_OBJECT", "HANDOVER_CACHE", "EVIDENCE_REVIEW",
    "EVIDENCE_RELEASE", "EVIDENCE_MIGRATION", "GENERATED_REFERENCE", "HUMAN_REFERENCE",
    "HISTORICAL_ARCHIVE", "OBSOLETE_DELETE", "UNKNOWN",
}

PLACEMENT_QUESTIONS = [
    "Where does a new reusable prompt go?", "Where does a one-shot prompt go while active?",
    "What happens to a one-shot prompt when complete?", "Where does an optional task packet go?",
    "Where does it go when the Issue closes?", "Where does a handover live and when does it expire?",
    "Where does operational/recovery procedure live?", "Where does review/release/migration evidence live?",
    "Where does generated documentation live?", "Which documents belong only in META?",
    "Which remain provider-local?", "Which paths are checked by CI?",
]
BACKLOG_TYPES = ["DOCUMENTATION_IA", "AGENT_INSTRUCTION", "PROMPT_LIFECYCLE", "TASK_LIFECYCLE", "RUNBOOK", "EVIDENCE_GOVERNANCE", "DOCS_CI"]
BACKLOG_REC_IDS = [f"REC-DOCS-{i:03d}" for i in range(1, 8)]
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
    matched = [row for row in rows if len(row) >= 4 and row[1] == artifact]
    repos = [row[0] for row in matched]
    if len(matched) != len(REPOS) or set(repos) != set(REPOS) or len(set(repos)) != len(repos):
        return "FAIL", [f"{artifact} lifecycle rows must cover exactly {REPOS}; got {repos}"]
    states = [row[3] for row in matched]
    gaps = sorted({m.group(0) for state in states for m in re.finditer(r"GAP-[A-Z0-9-]+", state)})
    if any(state.startswith("UNKNOWN") for state in states):
        return "UNKNOWN", gaps
    if all(state.startswith("PASS") for state in states):
        return "PASS", []
    return "FAIL", [f"unexpected lifecycle state: {state}" for state in states]


def parse_selector_spec(cell: str) -> tuple[list[str], list[str]]:
    parts = cell.split(" EXCEPT ")
    if len(parts) > 2:
        raise ValueError("multiple EXCEPT clauses")
    include_text = parts[0]
    exclude_text = parts[1] if len(parts) == 2 else ""
    def parse_side(side: str, required: bool) -> list[str]:
        atoms = [x.strip() for x in re.findall(r"`([^`]+)`", side) if x.strip()]
        residue = re.sub(r"`[^`]+`", "", side).replace(";", "").strip()
        if residue or (required and not atoms):
            raise ValueError(f"unparseable selector side: {side!r}")
        if len(atoms) != len(set(atoms)):
            raise ValueError(f"duplicate selector atom: {side!r}")
        return atoms
    return parse_side(include_text, True), parse_side(exclude_text, False)

def path_pattern_contains(parent: str, child: str) -> bool:
    if parent == child: return True
    if parent.endswith("/**") and child.startswith(parent[:-3]): return True
    if any(ch in parent for ch in "*?[") and not any(ch in child for ch in "*?["):
        return fnmatch.fnmatchcase(child, parent)
    return False

def wildcard_literal_prefix(pattern: str) -> str:
    positions = [pattern.find(ch) for ch in "*?[" if ch in pattern]
    return pattern[:min(positions)] if positions else pattern

def wildcard_patterns_may_overlap(left: str, right: str) -> bool:
    if not any(ch in left for ch in "*?[") or not any(ch in right for ch in "*?["):
        return False
    lp = wildcard_literal_prefix(left)
    rp = wildcard_literal_prefix(right)
    return lp.startswith(rp) or rp.startswith(lp)

def selector_specs_overlap(left, right):
    left_in, left_ex = left; right_in, right_ex = right
    for a in left_in:
        for b in right_in:
            if path_pattern_contains(a,b): narrower=b
            elif path_pattern_contains(b,a): narrower=a
            elif wildcard_patterns_may_overlap(a,b):
                # Fail closed when two wildcard sets share a compatible literal prefix
                # and disjointness cannot be proven structurally.
                return a,b
            else: continue
            if any(path_pattern_contains(ex,narrower) for ex in left_ex): continue
            if any(path_pattern_contains(ex,narrower) for ex in right_ex): continue
            return a,b
    return None


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
    inventory = table_rows(text, "| Repository | Current path/object | Artifact family | Primary operational class | Authority owner | Canonical repository | Canonical target path/object | Purpose | Consumers | Normative | Mutable state allowed | Local copy allowed | Override/precedence rule | Required metadata | Lifecycle | Retention/expiry | Supersession/archive rule | CI/drift enforcement | Migration action | Evidence ID | Context cost |")
    inventory_families = {repo: set() for repo in REPOS}
    selector_records = {repo: [] for repo in REPOS}
    for row in inventory:
        if len(row) != 21 or any(not cell for cell in row):
            errors.append(f"invalid material inventory row: {row}")
            continue
        repo,current,family,primary,authority,canonical_repo,canonical_target,purpose,consumers,normative,mutable_state,local_copy,override_rule,required_metadata,lifecycle,retention,supersession,ci_enforcement,migration_action,evidence_id,context_cost = row
        if repo not in REPOS:
            errors.append(f"invalid inventory repository: {row}")
            continue
        if family not in CLASSES:
            errors.append(f"invalid inventory artifact family: {repo}:{family}")
        else:
            inventory_families[repo].add(family)
        if primary not in OPERATIONAL_PRIMARY_CLASSES:
            errors.append(f"invalid operational primary class: {repo}:{current}:{primary}")
        if canonical_repo not in REPOS:
            errors.append(f"invalid canonical repository: {repo}:{current}:{canonical_repo}")
        for name,value in (("Normative",normative),("Mutable state allowed",mutable_state),("Local copy allowed",local_copy)):
            if value not in {"YES","NO"}:
                errors.append(f"invalid {name} flag: {repo}:{current}:{value}")
        if normative == "YES" and authority != repo:
            errors.append(f"normative artifact has non-single/non-owning authority: {row}")
        if primary == "UNKNOWN" and "GAP-" not in " | ".join(row):
            errors.append(f"UNKNOWN primary class lacks GAP-ID: {repo}:{current}")
        if "UNKNOWN" in lifecycle and "GAP-" not in lifecycle:
            errors.append(f"inventory lifecycle UNKNOWN without GAP-ID: {row}")
        try:
            spec=parse_selector_spec(current)
        except ValueError as exc:
            errors.append(f"unparseable CURRENT_PATH selector: {repo}:{current}: {exc}")
            continue
        for prior_spec,prior_primary,prior_current in selector_records[repo]:
            overlap=selector_specs_overlap(prior_spec,spec)
            if not overlap:
                continue
            a,b=overlap
            if prior_primary != primary:
                errors.append(f"material artifact has multiple primary classes: {repo}:{prior_current} ({prior_primary}) <> {current} ({primary}); overlap={a}::{b}")
            else:
                errors.append(f"material artifact appears in multiple primary records: {repo}:{prior_current} <> {current} ({primary}); overlap={a}::{b}")
        selector_records[repo].append((spec,primary,current))

    for row in matrix_l:
        if len(row) != 12 or row[0] not in inventory_families:
            continue
        current=row[2]
        if any(token in current for token in ("NOT_NEEDED","NOT_APPLICABLE","UNKNOWN")):
            continue
        if row[1] not in inventory_families[row[0]]:
            errors.append(f"material Matrix L class missing from section 4 inventory: {row[0]}:{row[1]}")

    required_meta_github = sorted(
        str(path.relative_to(REPO_STRUCTURE_ROOT)).replace("\\", "/")
        for path in [
            *list((REPO_STRUCTURE_ROOT / ".github/workflows").glob("*.yml")),
            *list((REPO_STRUCTURE_ROOT / ".github/workflows").glob("*.yaml")),
            *list((REPO_STRUCTURE_ROOT / ".github/actions").rglob("action.yml")),
            *list((REPO_STRUCTURE_ROOT / ".github/actions").rglob("action.yaml")),
        ]
        if path.is_file()
    )
    meta_specs = [spec for spec, _primary, _current in selector_records["META"]]
    missing_meta_github = []
    for path in required_meta_github:
        covered = any(
            any(path_pattern_contains(include, path) for include in includes)
            and not any(path_pattern_contains(exclude, path) for exclude in excludes)
            for includes, excludes in meta_specs
        )
        if not covered:
            missing_meta_github.append(path)
    if missing_meta_github:
        errors.append(f"material META .github governance surface missing from section 4 inventory: {missing_meta_github}")

    material_roots = (
        ".github/", "docs/agents/", "docs/architecture/", "docs/ci/", "docs/testing/",
        "docs/release/", "docs/recovery/", "docs/governance/", "docs/evidence/",
        "ecosystem/", "tools/governance/",
    )
    material_root_files = {"AGENTS.md", "README.md", "CONTRIBUTING.md", "SECURITY.md"}
    try:
        tracked_raw = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=REPO_STRUCTURE_ROOT,
            check=True,
            capture_output=True,
        ).stdout
        tracked = tracked_raw.decode("utf-8").split("\0")
    except (subprocess.CalledProcessError, UnicodeDecodeError, OSError) as exc:
        errors.append(f"unable to enumerate tracked META material surface: {exc}")
        tracked = []
    meta_material = sorted(
        path for path in tracked
        if path and (path in material_root_files or path.startswith(material_roots))
    )
    def spec_covers_path(spec, path: str) -> bool:
        includes, excludes = spec
        normalized_includes = [item.lstrip("/") for item in includes]
        normalized_excludes = [item.lstrip("/") for item in excludes]
        return (
            any(path_pattern_contains(include, path) for include in normalized_includes)
            and not any(path_pattern_contains(exclude, path) for exclude in normalized_excludes)
        )
    missing_meta_material = [
        path for path in meta_material if not any(spec_covers_path(spec, path) for spec in meta_specs)
    ]
    if missing_meta_material:
        errors.append(f"tracked META material surface missing from section 4 inventory: {missing_meta_material}")

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
    dispositions = table_rows(text, "| Repository | Current file/path | Primary operational class | Target / disposition | Authority | Acceptance / evidence |")
    disposition_repos = {repo for row in dispositions if len(row) == 6 for repo in [row[0]]}
    if disposition_repos != set(REPOS):
        errors.append(f"section 15 lacks provider documentation dispositions: {disposition_repos}")
    disposition_keys: list[tuple[str, str, str]] = []
    for row in dispositions:
        if len(row) != 6 or any(not cell for cell in row):
            errors.append(f"invalid section 15 disposition row: {row}")
            continue
        if row[0] not in REPOS or row[2] not in OPERATIONAL_PRIMARY_CLASSES:
            errors.append(f"invalid section 15 repo/operational-class: {row}")
        disposition_keys.append((row[0], row[1], row[2]))
        if not re.match(r"^`?\[(KEEP|KEEP/CLEANUP|MOVE|NEW|GENERATED|OPTIONAL|REMOVE_AFTER_MIGRATION|NOT_NEEDED)\]`?", row[3]):
            errors.append(f"invalid section 15 disposition: {row[3]}")
    inventory_keys = [(row[0], row[1], row[3]) for row in inventory if len(row) == 21]
    missing_dispositions = sorted(set(inventory_keys) - set(disposition_keys))
    extra_dispositions = sorted(set(disposition_keys) - set(inventory_keys))
    duplicate_dispositions = len(disposition_keys) != len(set(disposition_keys))
    if missing_dispositions or extra_dispositions or duplicate_dispositions:
        errors.append(f"section 15 inventory mapping mismatch: missing={missing_dispositions}, extra={extra_dispositions}, duplicates={duplicate_dispositions}")

    backlog = table_rows(text, "| Order | REC_ID | Type | CURRENT_PATHS | TARGET_PATHS | AUTHORITY_OWNER | MIGRATION/DISPOSITION | BACKWARD_LINK_OR_REDIRECT_PLAN | ACCEPTANCE_CRITERIA | DETERMINISTIC_VALIDATION | ROLLBACK |")
    backlog_ids = [row[1] for row in backlog if len(row) == 11]
    backlog_types = [row[2] for row in backlog if len(row) == 11]
    if backlog_ids != BACKLOG_REC_IDS:
        errors.append(f"mandatory recommendation REC_ID mismatch: {backlog_ids}")
    if backlog_types != BACKLOG_TYPES:
        errors.append(f"mandatory documentation backlog mismatch: {backlog_types}")
    for row in backlog:
        if len(row) != 11 or any(not cell for cell in row):
            errors.append(f"invalid documentation backlog row: {row}")

    quality_rows = table_rows(text, "| REC_ID | WHY | AUTHORITY_OWNER | CANONICAL_LOCATION_OR_GITHUB_SETTING | CONSUMER | ENFORCEMENT | DRIFT_PREVENTION | MIGRATION_IMPACT | TRADE_OFF | ARTIFACT_CLASS | CURRENT_PATHS | TARGET_PATH | LIFECYCLE_RETENTION | DUPLICATION_OVERRIDE_RULE | DETERMINISTIC_VALIDATION |")
    quality_ids = [row[0] for row in quality_rows if len(row) == 15]
    if quality_ids != BACKLOG_REC_IDS:
        errors.append(f"recommendation quality REC_ID mismatch: {quality_ids}")
    for row in quality_rows:
        if len(row) != 15 or any(not cell for cell in row):
            errors.append(f"invalid recommendation quality row: {row}")

    baseline_match = re.search(r"META_LIVE_TREE_BASELINE = ([0-9a-f]{40})", text)
    meta_baseline = baseline_match.group(1) if baseline_match else ""
    meta_baseline_short = meta_baseline[:8] if meta_baseline else ""
    baseline_ancestor_ok = False
    if not meta_baseline:
        errors.append("META live-tree baseline marker missing")
    else:
        try:
            baseline_ancestor_ok = subprocess.run(
                ["git", "merge-base", "--is-ancestor", meta_baseline, "HEAD"],
                cwd=REPO_STRUCTURE_ROOT, check=False, capture_output=True
            ).returncode == 0
        except OSError as exc:
            errors.append(f"unable to verify META live-tree baseline ancestry: {exc}")
        if not baseline_ancestor_ok:
            errors.append(f"META live-tree baseline is not an ancestor of HEAD: {meta_baseline}")
    stale_meta_inventory_evidence = [row for row in inventory if len(row) == 21 and row[0] == "META" and "live tree" in row[19] and meta_baseline_short not in row[19]]
    stale_meta_matrix_evidence = [row for row in matrix_l if len(row) == 12 and row[0] == "META" and "live tree" in row[11] and meta_baseline_short not in row[11]]
    if stale_meta_inventory_evidence or stale_meta_matrix_evidence:
        errors.append(f"META inventory evidence not bound to baseline {meta_baseline_short}: inventory={stale_meta_inventory_evidence}, matrix={stale_meta_matrix_evidence}")

    matrix_access_gaps = sorted({
        m.group(0)
        for row in matrix_l + lifecycle_rows + inventory
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
        "material_artifacts_have_primary_class": invariant(
            "PASS" if inventory and not any(
                token in e for e in errors for token in (
                    "invalid material inventory", "invalid operational primary class", "multiple primary classes",
                    "multiple primary records", "unparseable CURRENT_PATH selector", "UNKNOWN primary class lacks GAP-ID",
                )
            ) else "FAIL",
            f"{len(inventory)} material artifact records using section-10A operational taxonomy",
        ),
        "normative_artifacts_have_single_authority": invariant("PASS" if inventory and not any("normative artifact" in e for e in errors) else "FAIL", "section 4 normative inventory authority column"),
        "meta_github_governance_surface_inventory": invariant(
            "PASS" if not missing_meta_github else "FAIL",
            f"{len(required_meta_github) - len(missing_meta_github)}/{len(required_meta_github)} META workflow/action files covered by section 4",
        ),
        "meta_material_surface_inventory": invariant(
            "PASS" if not missing_meta_material else "FAIL",
            f"{len(meta_material) - len(missing_meta_material)}/{len(meta_material)} tracked META material files covered by section 4",
        ),
        "retained_reusable_prompts_have_identity_version_status": invariant(prompt_state, "section 7 lifecycle verification", prompt_gaps),
        "active_task_packets_have_lifecycle_authority": invariant(task_state, "section 7 lifecycle verification", task_gaps),
        "handovers_are_non_authoritative_and_expire": invariant(handover_state, "section 7 lifecycle verification", handover_gaps),
        "evidence_classes_have_retention_disposition": invariant("PASS" if evidence_retention_ok else "FAIL", f"{len(evidence_rows)} repository/evidence-class rows"),
        "target_trees_answer_section_26A": invariant("PASS" if len(placement) == 12 else "FAIL", f"{len(placement)}/12 placement questions"),
        "no_empty_taxonomy_created_for_symmetry": invariant("PASS" if empty_taxonomy_ok else "FAIL", "no [NEW] target-tree entry without proven need"),
        "documentation_agent_access_gaps_are_explicit": invariant("PASS" if matrix_access_gaps else "FAIL", "GAP-IDs parsed from Matrix L/lifecycle ledger", matrix_access_gaps),
        "documentation_agent_gaps_have_ordered_backlog": invariant("PASS" if not unmapped_doc_gaps else "FAIL", "all Matrix L/lifecycle GAP-IDs appear in section 19 remediation backlog"),
        "g11_result_present": invariant("PASS" if g11_ok else "FAIL", grows.get("G11", "missing")),
        "section_15_file_dispositions_present": invariant(
            "PASS" if disposition_repos == set(REPOS) and not missing_dispositions and not extra_dispositions and not duplicate_dispositions else "FAIL",
            f"{len(set(disposition_keys))}/{len(set(inventory_keys))} section-4 material families mapped exactly once",
        ),
        "section_19_required_backlog_categories_present": invariant("PASS" if backlog_types == BACKLOG_TYPES else "FAIL", ", ".join(backlog_types)),
        "section_19_recommendation_quality_records_present": invariant("PASS" if backlog_ids == BACKLOG_REC_IDS and quality_ids == BACKLOG_REC_IDS and not any("recommendation quality" in e or "REC_ID mismatch" in e for e in errors) else "FAIL", f"{len(quality_rows)}/7 section-32A quality records mapped 1:1"),
        "meta_inventory_bound_to_reconciled_baseline": invariant("PASS" if meta_baseline and baseline_ancestor_ok and not stale_meta_inventory_evidence and not stale_meta_matrix_evidence else "FAIL", meta_baseline or "missing"),
    }
    hard_fail = bool(errors) or any(item["state"] == "FAIL" for item in invariants.values())
    unresolved = sorted({gap for item in invariants.values() for gap in item.get("gap_ids", [])})
    return {
        "schema_version": 4,
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
        "operational_primary_classes": sorted({row[3] for row in inventory if len(row) == 21}),
        "section_15_disposition_rows": len(dispositions),
        "section_19_documentation_backlog_types": backlog_types,
        "section_19_recommendation_ids": backlog_ids,
        "section_19_recommendation_quality_rows": len(quality_rows),
        "meta_live_tree_baseline": meta_baseline,
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
