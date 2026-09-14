from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.audit.verify_cost_ci import validate

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs/evidence/organization-audit-20260907/cost-ci-candidate.json"


class CostCiVerifierTests(unittest.TestCase):
    def load(self) -> dict:
        return json.loads(SOURCE.read_text(encoding="utf-8"))

    def expect_rejected(self, data: dict) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "candidate.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                validate(path)

    def test_valid_packet(self) -> None:
        result = validate(SOURCE)
        self.assertEqual(result["result"], "COST_CI_HANDOFF_VALID_OBLIGATION_OPEN")

    def test_rejects_missing_event_stratum(self) -> None:
        data = self.load()
        del data["runs"][2]
        self.expect_rejected(data)

    def test_rejects_timing_rewrite(self) -> None:
        data = self.load()
        data["runs"][0]["queue_seconds"] = 0
        self.expect_rejected(data)

    def test_rejects_retry_rewrite(self) -> None:
        data = self.load()
        data["runs"][0]["run_attempt"] = 2
        self.expect_rejected(data)

    def test_rejects_capacity_claim(self) -> None:
        data = self.load()
        data["claims"]["runner_capacity_claimed"] = True
        self.expect_rejected(data)

    def test_rejects_cost_closure(self) -> None:
        data = self.load()
        data["claims"]["cost_ci_closed"] = True
        self.expect_rejected(data)

    def test_rejects_removed_long_term_limitation(self) -> None:
        data = self.load()
        data["limitations"] = [
            item for item in data["limitations"] if "statistically representative" not in item
        ]
        self.expect_rejected(data)


if __name__ == "__main__":
    unittest.main()
