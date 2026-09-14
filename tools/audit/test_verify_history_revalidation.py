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
        cls.raw = verify.CANDIDATE.read_text(encoding="utf-8")

    def validate_mutation(self, mutate):
        data = copy.deepcopy(self.base)
        mutate(data)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "candidate.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            return verify.validate(path)

    def validate_raw(self, raw: str):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "candidate.json"
            path.write_text(raw, encoding="utf-8")
            return verify.validate(path)

    def test_candidate_is_valid_but_obligation_stays_open(self):
        result = verify.validate()
        self.assertEqual(result["result"], "HISTORY_REVALIDATION_HANDOFF_VALID_OBLIGATION_OPEN")
        self.assertEqual(result["revalidation_findings"], 30)

    def test_duplicate_top_level_claims_object_is_rejected_before_materialization(self):
        marker = '  "claims": {'
        raw = self.raw.replace(
            marker,
            '  "claims": {"history_revalidation_closed": true},\n' + marker,
            1,
        )
        self.assertNotEqual(raw, self.raw)
        with self.assertRaisesRegex(ValueError, "duplicate JSON member: claims"):
            self.validate_raw(raw)

    def test_duplicate_governed_claim_member_is_rejected_before_materialization(self):
        marker = '    "history_revalidation_closed": false'
        raw = self.raw.replace(
            marker,
            '    "history_revalidation_closed": true,\n' + marker,
            1,
        )
        self.assertNotEqual(raw, self.raw)
        with self.assertRaisesRegex(ValueError, "duplicate JSON member: history_revalidation_closed"):
            self.validate_raw(raw)

    def test_observation_time_is_exactly_bound(self):
        mutations = (
            lambda d: d.pop("observed_at"),
            lambda d: d.update(observed_at="2026-09-14T16:24:00Z"),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate), self.assertRaisesRegex(ValueError, "observation provenance drift"):
                self.validate_mutation(mutate)

    def test_lifecycle_baseline_is_exactly_bound(self):
        mutations = (
            lambda d: d["baseline"].update(canonical_audit_head="0" * 40),
            lambda d: d["baseline"].update(programme_head="0" * 40),
            lambda d: d["baseline"].update(release_comment_id=1),
            lambda d: d["baseline"].pop("canonical_audit_pr"),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate), self.assertRaisesRegex(ValueError, "lifecycle baseline provenance drift"):
                self.validate_mutation(mutate)

    def test_current_and_historical_coordinates_cannot_be_conflated(self):
        with self.assertRaisesRegex(ValueError, "source boundary provenance drift"):
            self.validate_mutation(lambda d: d["source_boundaries"][1].update(current_main_commit=d["source_boundaries"][1]["historical_commit"]))

    def test_each_boundary_coordinate_and_compare_value_is_exactly_bound(self):
        mutations = (
            lambda d: d["source_boundaries"][0].update(historical_tree="0" * 40),
            lambda d: d["source_boundaries"][1].update(compare_path_blob_status_sha256="0" * 64),
            lambda d: d["source_boundaries"][2].update(changed_files_reported=143),
            lambda d: d["source_boundaries"][3].update(ahead_by=95),
            lambda d: d["source_boundaries"][4].pop("compare_path_blob_status_sha256"),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate), self.assertRaisesRegex(ValueError, "source boundary provenance drift"):
                self.validate_mutation(mutate)

    def test_truncated_game_compare_cannot_be_promoted_to_complete(self):
        with self.assertRaisesRegex(ValueError, "Game compare truncation"):
            self.validate_mutation(lambda d: d["source_boundaries"][1].update(compare_file_list_complete=True))

    def test_truncated_game_compare_requires_exact_limitation_and_carry_forward_rule(self):
        mutations = (
            lambda d: d["source_boundaries"][1].update(compare_limitation="GitHub returned 300-file results."),
            lambda d: d.update(stale_evidence_rejection_rules=[x for x in d["stale_evidence_rejection_rules"] if x != verify.GAME_CARRY_FORWARD_RULE]),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate), self.assertRaisesRegex(ValueError, "Game compare truncation"):
                self.validate_mutation(mutate)

    def test_contradictory_game_completeness_prose_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "contradictory positive assertion"):
            self.validate_mutation(lambda d: d["limitations"].append("The Game changed-path inventory is complete."))

    def test_open_finding_cannot_be_silently_omitted(self):
        with self.assertRaisesRegex(ValueError, "revalidation finding set drift"):
            self.validate_mutation(lambda d: d["claims_requiring_rebind_or_revalidation"]["finding_ids"].pop())

    def test_historical_packet_cannot_claim_closure_or_readiness(self):
        for claim in self.base["claims"]:
            with self.subTest(claim=claim), self.assertRaisesRegex(ValueError, "exact keys and all be false"):
                self.validate_mutation(lambda d, claim=claim: d["claims"].update({claim: True}))

    def test_negative_claim_keys_cannot_be_omitted_or_extended(self):
        mutations = (
            lambda d: d["claims"].pop("runtime_readiness_claimed"),
            lambda d: d["claims"].update(unrelated=False),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate), self.assertRaisesRegex(ValueError, "exact keys and all be false"):
                self.validate_mutation(mutate)

    def test_governed_claim_keys_cannot_be_duplicated_outside_claims(self):
        for key in verify.EXPECTED_CLAIMS:
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "governed claim key duplicated outside claims"):
                self.validate_mutation(lambda d, key=key: d.update({key: True}))

    def test_contradictory_positive_readiness_prose_is_rejected(self):
        assertions = (
            "HISTORY-REVALIDATION is closed.",
            "Product readiness is established.",
            "Runtime readiness has been proven.",
            "Security remediation is complete.",
            "The organization-wide audit is complete.",
        )
        for assertion in assertions:
            with self.subTest(assertion=assertion), self.assertRaisesRegex(ValueError, "contradictory positive assertion"):
                self.validate_mutation(lambda d, assertion=assertion: d["limitations"].append(assertion))

    def test_contradictory_machine_readable_assertion_fields_are_rejected(self):
        assertions = (
            ("product_readiness", "established"),
            ("history_revalidation", "closed"),
            ("game_compare", "complete"),
        )
        for key, value in assertions:
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "contradictory positive assertion"):
                self.validate_mutation(lambda d, key=key, value=value: d.update({key: value}))

    def test_boolean_positive_machine_readable_assertion_fields_are_rejected(self):
        for key in ("product_readiness", "history_revalidation", "game_compare"):
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "contradictory positive assertion"):
                self.validate_mutation(lambda d, key=key: d.update({key: True}))

    def test_disclosure_and_digest_rejection_rules_are_mandatory(self):
        for phrase in ("digest without retrievable bytes", "public disclosure remains disclosed"):
            with self.subTest(phrase=phrase), self.assertRaisesRegex(ValueError, "stale-evidence rules weakened"):
                self.validate_mutation(lambda d, phrase=phrase: d.update(stale_evidence_rejection_rules=[x.replace(phrase, "weakened") for x in d["stale_evidence_rejection_rules"]]))

if __name__ == "__main__":
    unittest.main()
