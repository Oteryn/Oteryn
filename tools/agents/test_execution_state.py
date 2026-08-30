from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools.agents.execution_state import validate_checkpoint

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs/agents/EXECUTION_STATE_CONTRACT.json"
SHA = "1" * 40
FP = "a" * 64


def valid_checkpoint(**overrides):
    value = {
        "status": "RUNNING",
        "task_head_sha": SHA,
        "candidate_frozen": False,
        "candidate_head_sha": "",
        "progress_fingerprint": FP,
        "failure_fingerprint": "",
        "identical_cycle_count": 0,
        "retry_count": 0,
        "retry_limit": 1,
        "waiting_for": "",
        "last_material_progress_at": "2026-08-25T16:00:00+00:00",
    }
    value.update(overrides)
    return value


class ExecutionStateContractTests(unittest.TestCase):
    def test_contract_declares_required_durable_fields_and_states(self):
        raw = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(raw["schema_version"], 1)
        self.assertEqual(
            raw["authority"],
            "docs/agents/contracts/BOUNDED_AUTONOMOUS_EXECUTION_POLICY.md",
        )
        self.assertTrue((ROOT / raw["authority"]).is_file())
        self.assertEqual(
            set(raw["durable_fields"]),
            {
                "candidate_frozen",
                "candidate_head_sha",
                "progress_fingerprint",
                "failure_fingerprint",
                "identical_cycle_count",
                "retry_count",
                "retry_limit",
                "waiting_for",
                "last_material_progress_at",
            },
        )
        self.assertEqual(
            set(raw["allowed_statuses"]),
            {"RUNNING", "READY", "WAITING_EXTERNAL", "BLOCKED", "STALLED", "DONE"},
        )
        self.assertTrue(raw["migration"]["legacy_records_readable"])
        self.assertEqual(
            set(raw["migration"]["bounded_fields_required_for"]),
            {"new_substantial_task", "updated_substantial_task"},
        )

    def test_legacy_record_is_readable_when_bounded_fields_not_required(self):
        self.assertEqual(validate_checkpoint({"status": "RUNNING"}, require_bounded_fields=False), [])

    def test_updated_substantial_record_requires_all_bounded_fields(self):
        errors = validate_checkpoint({"status": "RUNNING"}, require_bounded_fields=True)
        self.assertTrue(any("missing bounded fields" in item for item in errors))

    def test_running_cannot_wait_for_external_event(self):
        errors = validate_checkpoint(valid_checkpoint(waiting_for="codex review"), require_bounded_fields=True)
        self.assertIn("RUNNING must not have waiting_for populated", errors)

    def test_waiting_external_requires_waiting_for(self):
        errors = validate_checkpoint(valid_checkpoint(status="WAITING_EXTERNAL"), require_bounded_fields=True)
        self.assertIn("WAITING_EXTERNAL requires waiting_for", errors)

    def test_frozen_candidate_must_match_task_head(self):
        errors = validate_checkpoint(
            valid_checkpoint(candidate_frozen=True, candidate_head_sha="2" * 40),
            require_bounded_fields=True,
        )
        self.assertIn("frozen candidate_head_sha must equal task_head_sha", errors)

    def test_retry_over_limit_cannot_remain_running(self):
        errors = validate_checkpoint(
            valid_checkpoint(retry_count=2, retry_limit=1, identical_cycle_count=2),
            require_bounded_fields=True,
        )
        self.assertIn("retry budget exhausted; status must be STALLED or WAITING_EXTERNAL", errors)

    def test_retry_over_limit_may_be_stalled(self):
        self.assertEqual(
            validate_checkpoint(
                valid_checkpoint(status="STALLED", retry_count=2, retry_limit=1, identical_cycle_count=2),
                require_bounded_fields=True,
            ),
            [],
        )

    def test_valid_waiting_external_checkpoint(self):
        self.assertEqual(
            validate_checkpoint(
                valid_checkpoint(
                    status="WAITING_EXTERNAL",
                    candidate_frozen=True,
                    candidate_head_sha=SHA,
                    waiting_for="authenticated external review evidence",
                    failure_fingerprint="b" * 64,
                    retry_count=0,
                    retry_limit=0,
                ),
                require_bounded_fields=True,
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()