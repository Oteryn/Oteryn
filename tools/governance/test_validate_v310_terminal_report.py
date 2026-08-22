#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

MODULE = Path(__file__).with_name("validate_v310_terminal_report.py")
SPEC = importlib.util.spec_from_file_location("validate_v310_terminal_report", MODULE)
assert SPEC and SPEC.loader
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


def with_report(text: str):
    temp = tempfile.TemporaryDirectory(prefix="oteryn-v310-report-")
    root = Path(temp.name)
    report = root / "report.md"
    report.write_text(text, encoding="utf-8")
    old_root, old_report = m.ROOT, m.REPORT
    m.ROOT, m.REPORT = root, report
    return temp, old_root, old_report


def restore(temp, old_root, old_report) -> None:
    m.ROOT, m.REPORT = old_root, old_report
    temp.cleanup()


def test_current_report_executes_cleanly() -> None:
    record = m.build_record()
    assert record["execution_verdict"] == "PASS"
    assert record["programme_verdict"] == "INCOMPLETE"
    assert record["matrix_l_rows"] == 88
    assert record["section_19_documentation_backlog_types"] == m.BACKLOG_TYPES


def test_missing_docs_ci_backlog_fails() -> None:
    text = m.REPORT.read_text(encoding="utf-8").replace("| 17 | DOCS_CI |", "| 17 | DOCS_CI_MISSING |", 1)
    temp, old_root, old_report = with_report(text)
    try:
        record = m.build_record()
        assert record["execution_verdict"] == "FAIL"
        assert any("mandatory documentation backlog mismatch" in error for error in record["errors"])
    finally:
        restore(temp, old_root, old_report)


def test_missing_material_classification_fails() -> None:
    text = m.REPORT.read_text(encoding="utf-8")
    prefix = "| META | `docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md` | contracts | CROSS_REPO_CONTRACT |"
    text = without_row(text, prefix)
    temp, old_root, old_report = with_report(text)
    try:
        record = m.build_record()
        assert record["execution_verdict"] == "FAIL"
        assert any("META:contracts" in error for error in record["errors"])
    finally:
        restore(temp, old_root, old_report)


def test_report_digest_is_eol_stable() -> None:
    original = m.REPORT.read_bytes().replace(b"\r\n", b"\n")
    temp = tempfile.TemporaryDirectory(prefix="oteryn-v310-eol-")
    try:
        crlf = Path(temp.name) / "report.md"
        crlf.write_bytes(original.replace(b"\n", b"\r\n"))
        canonical = Path(temp.name) / "canonical.md"
        canonical.write_bytes(original)
        assert m.sha256(crlf) == m.sha256(canonical)
    finally:
        temp.cleanup()



def without_row(text: str, prefix: str) -> str:
    matches = [line for line in text.splitlines(keepends=True) if line.startswith(prefix)]
    assert len(matches) == 1, (prefix, len(matches))
    return text.replace(matches[0], "", 1)


def assert_lifecycle_row_required(prefix: str, invariant_name: str) -> None:
    text = without_row(m.REPORT.read_text(encoding="utf-8"), prefix)
    temp, old_root, old_report = with_report(text)
    try:
        record = m.build_record()
        assert record["execution_verdict"] == "FAIL"
        assert record["mechanical_invariants"][invariant_name]["state"] == "FAIL"
    finally:
        restore(temp, old_root, old_report)


def test_missing_game_reusable_prompt_lifecycle_row_fails() -> None:
    assert_lifecycle_row_required("| Game | reusable prompts | stable identity/version/status", "retained_reusable_prompts_have_identity_version_status")


def test_missing_platform_active_task_lifecycle_row_fails() -> None:
    assert_lifecycle_row_required("| Platform | active task packets | explicit lifecycle authority", "active_task_packets_have_lifecycle_authority")


def test_missing_atlas_handover_lifecycle_row_fails() -> None:
    assert_lifecycle_row_required("| Atlas | handovers | explicitly non-authoritative", "handovers_are_non_authoritative_and_expire")


def test_missing_section15_material_disposition_fails() -> None:
    text = m.REPORT.read_text(encoding="utf-8")
    prefix = "| META | `docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md` | CROSS_REPO_CONTRACT |"
    text = without_row(text, prefix)
    temp, old_root, old_report = with_report(text)
    try:
        record = m.build_record()
        assert record["execution_verdict"] == "FAIL"
        assert record["mechanical_invariants"]["section_15_file_dispositions_present"]["state"] == "FAIL"
    finally:
        restore(temp, old_root, old_report)


def test_grouped_inventory_path_overlap_fails() -> None:
    text = m.REPORT.read_text(encoding="utf-8")
    old = "| META | `docs/architecture/adr/**` | architecture/ADR | ARCHITECTURE_ADR |"
    new_prefix = "| META | `/AGENTS.md`; `docs/architecture/adr/**` | architecture/ADR | ARCHITECTURE_ADR |"
    assert old in text
    text = text.replace(old, new_prefix, 1)
    temp, old_root, old_report = with_report(text)
    try:
        record = m.build_record()
        assert record["execution_verdict"] == "FAIL"
        assert any("multiple primary classes" in error for error in record["errors"])
    finally:
        restore(temp, old_root, old_report)


def test_section4_uses_contract_operational_primary_classes() -> None:
    record = m.build_record()
    assert record["execution_verdict"] == "PASS"
    assert set(record["operational_primary_classes"]) <= m.OPERATIONAL_PRIMARY_CLASSES
    assert "root AGENTS" not in record["operational_primary_classes"]


def test_unquoted_inventory_selector_fails() -> None:
    text = m.REPORT.read_text(encoding="utf-8")
    inv = "| META | `/AGENTS.md` | root AGENTS | NORMATIVE_AGENT_INSTRUCTION |"
    disp = "| META | `/AGENTS.md` | NORMATIVE_AGENT_INSTRUCTION |"
    assert inv in text and disp in text
    text = text.replace(inv, "| META | /AGENTS.md | root AGENTS | NORMATIVE_AGENT_INSTRUCTION |", 1)
    text = text.replace(disp, "| META | /AGENTS.md | NORMATIVE_AGENT_INSTRUCTION |", 1)
    temp, old_root, old_report = with_report(text)
    try:
        record = m.build_record()
        assert record["execution_verdict"] == "FAIL"
        assert any("unparseable CURRENT_PATH selector" in error for error in record["errors"])
    finally:
        restore(temp, old_root, old_report)


def test_meta_github_governance_surface_is_inventory_covered() -> None:
    record = m.build_record()
    assert record["mechanical_invariants"]["meta_github_governance_surface_inventory"]["state"] == "PASS"


def test_wildcard_pair_possible_intersection_fails_closed() -> None:
    text = m.REPORT.read_text(encoding="utf-8")
    gov = "`docs/agents/OWNER_FUNDED_AI_POLICY.md`; `docs/agents/PROMPTING_STANDARD.md`; `docs/agents/PROMPT_EVAL_STANDARD.md`; `docs/agents/PROMPTING_HANDOVER.md`"
    machine = "`.github/repository-policy.json`; `docs/agents/GOVERNANCE_CONTRACT.json`; `docs/agents/PROJECT_LANES.json`"
    assert text.count(gov) >= 2 and text.count(machine) >= 2
    text = text.replace(gov, "`docs/agents/*POLICY*.md`", 2)
    text = text.replace(machine, "`docs/agents/*AI*.md`", 2)
    temp, old_root, old_report = with_report(text)
    try:
        record = m.build_record()
        assert record["execution_verdict"] == "FAIL"
        assert any("multiple primary classes" in error for error in record["errors"])
    finally:
        restore(temp, old_root, old_report)


def test_meta_material_surface_is_inventory_covered() -> None:
    record = m.build_record()
    assert record["mechanical_invariants"]["meta_material_surface_inventory"]["state"] == "PASS"


def main() -> int:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"v3.10 terminal report validator tests PASS: {len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
