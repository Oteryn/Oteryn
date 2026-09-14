#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path
from unittest import mock

PATH = Path(__file__).with_name("verify_audit186_semantic_historical_provenance.py")
SPEC = importlib.util.spec_from_file_location("audit186_semantic", PATH)
assert SPEC and SPEC.loader
verifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verifier)


class HistoricalProvenanceCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.leaves = verifier.baseline_leaves()
        cls.doc = verifier.load_json(verifier.CANDIDATE.read_bytes())

    def assert_invalid(self, changed: dict, message: str) -> None:
        with self.assertRaisesRegex(verifier.CandidateError, message):
            verifier.validate_document(changed, self.leaves)

    def test_exact_candidate_is_valid_but_not_adopted(self) -> None:
        result = verifier.validate()
        self.assertEqual(result["path_count"], 26)
        self.assertTrue(result["projection_only"])
        self.assertFalse(result["coverage_adopted"])
        self.assertFalse(result["current_truth_revalidated"])

    def test_duplicate_json_key_is_rejected(self) -> None:
        with self.assertRaisesRegex(verifier.CandidateError, "duplicate JSON key"):
            verifier.load_json(b'{"status":"x","status":"y"}')

    def test_missing_extra_reordered_and_duplicate_paths_are_rejected(self) -> None:
        mutations = []
        missing = copy.deepcopy(self.doc); missing["family"]["paths"].pop(); mutations.append(missing)
        extra = copy.deepcopy(self.doc); extra["family"]["paths"].append(copy.deepcopy(extra["family"]["paths"][0])); mutations.append(extra)
        reordered = copy.deepcopy(self.doc); reordered["family"]["paths"][0:2] = reversed(reordered["family"]["paths"][0:2]); mutations.append(reordered)
        duplicate = copy.deepcopy(self.doc); duplicate["family"]["paths"][1] = copy.deepcopy(duplicate["family"]["paths"][0]); mutations.append(duplicate)
        for changed in mutations:
            with self.subTest(kind=len(changed["family"]["paths"])):
                self.assert_invalid(changed, "path")

    def test_blob_drift_is_rejected(self) -> None:
        changed = copy.deepcopy(self.doc)
        changed["family"]["paths"][0]["blob_sha"] = "0" * 40
        self.assert_invalid(changed, "blob identity")

    def test_grouped_substitution_is_rejected(self) -> None:
        changed = copy.deepcopy(self.doc)
        changed["family"]["proposed_disposition"] = "GROUPED"
        changed["family"]["grouped_proposed"] = True
        self.assert_invalid(changed, "DIRECT, not GROUPED")

    def test_adoption_and_readiness_overclaims_are_rejected(self) -> None:
        changed = copy.deepcopy(self.doc); changed["coverage_adopted"] = True
        self.assert_invalid(changed, "must not claim adoption")
        changed = copy.deepcopy(self.doc); changed["family"]["limitations"] = ["Product readiness established"]
        self.assert_invalid(changed, "non-claim boundary")

    def test_projection_must_be_exact_and_type_strict(self) -> None:
        for field, value in (("label", "ADOPTED"), ("direct", 335), ("source_leaves", True)):
            changed = copy.deepcopy(self.doc); changed["projection_if_adopted"][field] = value
            with self.subTest(field=field):
                self.assert_invalid(changed, "accounting drift")

    def test_inert_envelope_loss_is_rejected(self) -> None:
        with mock.patch.object(Path, "read_text", return_value="historical package"):
            with self.assertRaisesRegex(verifier.CandidateError, "inert/non-authority envelope"):
                verifier.validate()

    def test_canonical_surface_mutation_is_rejected(self) -> None:
        with mock.patch.object(verifier, "changed_paths", return_value=["docs/evidence/organization-audit-20260907/coverage-summary.json"]):
            with self.assertRaisesRegex(verifier.CandidateError, "canonical accounting surface"):
                verifier.validate()


if __name__ == "__main__":
    unittest.main()
