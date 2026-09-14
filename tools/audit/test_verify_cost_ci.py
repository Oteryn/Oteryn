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

    def test_rejects_sampling_provenance_drift(self) -> None:
        mutations = (
            lambda d: d["sampling"].pop("source_endpoints"),
            lambda d: d["sampling"].update(method="Different method; not filtered by conclusion."),
            lambda d: d["sampling"].update(per_event=3),
        )
        for mutate in mutations:
            data = self.load()
            mutate(data)
            self.expect_rejected(data)

    def test_rejects_missing_event_stratum(self) -> None:
        data = self.load()
        del data["runs"][2]
        self.expect_rejected(data)

    def test_rejects_timing_rewrite(self) -> None:
        data = self.load()
        data["runs"][0]["created_to_start_delay_seconds"] = 0
        self.expect_rejected(data)

    def test_rejects_raw_provenance_drift(self) -> None:
        mutations = (
            lambda d: d["runs"][0].update(head_branch="other-branch"),
            lambda d: d["runs"][0].update(runner_id=999999999),
            lambda d: d["runs"][0].update(job_created_at="2026-09-14T16:00:36Z", job_started_at="2026-09-14T16:00:38Z"),
            lambda d: d["runs"][0].update(run_created_at="2026-09-14T16:00:35Z", run_updated_at="2026-09-14T16:00:51Z"),
        )
        for mutate in mutations:
            data = self.load()
            mutate(data)
            self.expect_rejected(data)

    def test_rejects_retry_rewrite(self) -> None:
        data = self.load()
        data["runs"][0]["run_attempt"] = 2
        self.expect_rejected(data)

    def test_rejects_retry_rate_overclaim(self) -> None:
        data = self.load()
        data["unknown_or_blocked"]["retry_rate"] = "PROVEN: retry rate is zero."
        self.expect_rejected(data)

    def test_rejects_useful_yield_overclaim(self) -> None:
        data = self.load()
        data["unknown_or_blocked"]["useful_verification_yield"] = "PROVEN: useful verification yield is high."
        self.expect_rejected(data)

    def test_rejects_pure_queue_time_promotion(self) -> None:
        data = self.load()
        data["unknown_or_blocked"]["pure_queue_time"] = "PROVEN: pure queue time is 2-3 seconds."
        self.expect_rejected(data)

    def test_rejects_created_to_start_relabelled_as_queue(self) -> None:
        data = self.load()
        value = data["proven"].pop("observed_created_to_start_delay")
        data["proven"]["observed_job_queue"] = value.replace("created-to-start delay", "job queue")
        self.expect_rejected(data)

    def test_rejects_proven_observation_map_drift(self) -> None:
        mutations = (
            lambda d: d["proven"].pop("trigger_stratification"),
            lambda d: d["proven"].pop("sample_outcomes"),
            lambda d: d["proven"].update(observed_execution="PROVEN: execution is always fast."),
        )
        for mutate in mutations:
            data = self.load()
            mutate(data)
            self.expect_rejected(data)

    def test_rejects_recheck_trigger_drift(self) -> None:
        mutations = (
            lambda d: d.pop("recheck_triggers"),
            lambda d: d.update(recheck_triggers=[]),
            lambda d: d["recheck_triggers"].pop(),
        )
        for mutate in mutations:
            data = self.load()
            mutate(data)
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
        data["limitations"] = [item for item in data["limitations"] if "statistically representative" not in item]
        self.expect_rejected(data)


if __name__ == "__main__":
    unittest.main()
