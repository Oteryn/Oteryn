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
    """Fails if report bytes, Matrix L, or G1-G11 fail-closed vocabulary drift."""
    result = m.validate(ROOT)
    assert result["report_sha256"] == "35702cd1775f19517f825aa72ad6243e6d430a5f63a36cd107cc04e499ed5db4"
    assert result["report_bytes"] == 40362
    assert result["matrix_l_required_classes"] == 22
    assert result["gate_rows"] == 11


if __name__ == "__main__":
    test_terminal_report_validation_binds_bytes_and_required_v310_ledgers()
    print("v3.10 audit-document validator tests PASS: 1")
