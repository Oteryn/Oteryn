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
    line = "| META | `docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md`; `docs/ci/CI_CONTRACT.md` | contracts | YES | META | durable while authoritative; update through protected provider process | on-demand/routed |\n"
    assert line in text
    temp, old_root, old_report = with_report(text.replace(line, "", 1))
    try:
        record = m.build_record()
        assert record["execution_verdict"] == "FAIL"
        assert any("META:contracts" in error for error in record["errors"])
    finally:
        restore(temp, old_root, old_report)


def main() -> int:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"v3.10 terminal report validator tests PASS: {len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
