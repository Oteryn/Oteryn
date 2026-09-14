from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).with_name("verify_history_revalidation.py")
SPEC = importlib.util.spec_from_file_location("verify_history_revalidation", MODULE)
assert SPEC and SPEC.loader
verify = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify)

class HistoryRevalidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = json.loads(verify.CANDIDATE.read_text(encoding="utf-8"))

    def validate_mutation(self, mutate):
        data = copy.deepcopy(self.base)
        mutate(data)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "candidate.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            return verify.validate(path)

    def test_candidate_is_valid_but_obligation_stays_open(self):
        result = verify.validate()
        self.assertEqual(result["result"], "HISTORY_REVALIDATION_HANDOFF_VALID_OBLIGATION_OPEN")
        self.assertEqual(result["revalidation_findings"], 30)

    def test_current_and_historical_coordinates_cannot_be_conflated(self):
        with self.assertRaisesRegex(ValueError, "moved boundary"):
            self.validate_mutation(lambda d: d["source_boundaries"][1].update(current_main_commit=d["source_boundaries"][1]["historical_commit"]))

    def test_truncated_game_compare_cannot_be_promoted_to_complete(self):
        with self.assertRaisesRegex(ValueError, "Game compare truncation"):
            self.validate_mutation(lambda d: d["source_boundaries"][1].update(compare_file_list_complete=True))

    def test_open_finding_cannot_be_silently_omitted(self):
        with self.assertRaisesRegex(ValueError, "revalidation finding set drift"):
            self.validate_mutation(lambda d: d["claims_requiring_rebind_or_revalidation"]["finding_ids"].pop())

    def test_historical_packet_cannot_claim_closure_or_readiness(self):
        for claim in self.base["claims"]:
            with self.subTest(claim=claim), self.assertRaisesRegex(ValueError, "must all be false"):
                self.validate_mutation(lambda d, claim=claim: d["claims"].update({claim: True}))

    def test_disclosure_and_digest_rejection_rules_are_mandatory(self):
        for phrase in ("digest without retrievable bytes", "public disclosure remains disclosed"):
            with self.subTest(phrase=phrase), self.assertRaisesRegex(ValueError, "stale-evidence rules weakened"):
                self.validate_mutation(lambda d, phrase=phrase: d.update(stale_evidence_rejection_rules=[x.replace(phrase, "weakened") for x in d["stale_evidence_rejection_rules"]]))

if __name__ == "__main__":
    unittest.main()
