#!/usr/bin/env python3
"""Regression tests for v3.10 organization recovery evidence validation."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from validate_v310_organization_recovery import validate  # noqa: E402

EVIDENCE = ROOT / "docs/evidence/OTERYN-V310-ORGANIZATION-RECOVERY-CLOSEOUT-20260824.json"


class RecoveryEvidenceValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_real_artifact_validates(self) -> None:
        validate(copy.deepcopy(self.data))

    def test_pass_requires_restore_evidence(self) -> None:
        data = copy.deepcopy(self.data)
        gap = data["recovery_gaps"]["GAP-RECOVERY-003"]
        gap["status"] = "PASS"
        gap["generation_evidence"] = ["inventory generated"]
        gap.pop("owner_decisions_required", None)
        with self.assertRaisesRegex(ValueError, "restore/reconstruction evidence"):
            validate(data)

    def test_blocked_requires_owner_decision(self) -> None:
        data = copy.deepcopy(self.data)
        gap = data["recovery_gaps"]["GAP-RECOVERY-005"]
        gap["owner_decisions_required"] = []
        with self.assertRaisesRegex(ValueError, "BLOCKED requires owner decisions"):
            validate(data)

    def test_unknown_requires_reason(self) -> None:
        data = copy.deepcopy(self.data)
        gap = data["recovery_gaps"]["GAP-RECOVERY-003"]
        gap["status"] = "UNKNOWN"
        gap.pop("owner_decisions_required", None)
        gap["unknown_reason"] = ""
        with self.assertRaisesRegex(ValueError, "UNKNOWN requires unknown_reason"):
            validate(data)

    def test_non_pass_cannot_be_merge_eligible(self) -> None:
        data = copy.deepcopy(self.data)
        data["merge_eligible"] = True
        with self.assertRaisesRegex(ValueError, "must not be merge eligible"):
            validate(data)

    def test_sensitive_key_is_rejected(self) -> None:
        data = copy.deepcopy(self.data)
        forbidden_key = "secret" + "_value"
        data["observations"]["unsafe"] = {forbidden_key: "placeholder"}
        with self.assertRaisesRegex(ValueError, "sensitive key forbidden"):
            validate(data)


if __name__ == "__main__":
    unittest.main()
