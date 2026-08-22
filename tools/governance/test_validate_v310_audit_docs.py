#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = Path(__file__).with_name("validate_v310_audit_docs.py")
SPEC = importlib.util.spec_from_file_location("validate_v310_audit_docs", SCRIPT)
assert SPEC and SPEC.loader
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


def test_terminal_report_validation_binds_bytes_and_required_v310_ledgers() -> None:
    """Fails if any advertised terminal-report structural control drifts."""
    result = m.validate(ROOT)
    assert result["matrix_l_required_classes"] == 22
    assert result["gate_rows"] == 11
    assert result["h_rows"] == 14
    assert result["numbered_sections"] == 21
    assert result["unknown_gate_rows"] == 8
    assert result["validation_checks"] == 12


if __name__ == "__main__":
    test_terminal_report_validation_binds_bytes_and_required_v310_ledgers()
    print("v3.10 audit-document validator tests PASS: 1")
