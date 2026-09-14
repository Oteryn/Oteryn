#!/usr/bin/env python3
"""Adversarial tests for the bounded AUDIT186 semantic candidate."""
from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

MODULE_PATH = Path(__file__).with_name("verify_audit186_semantic_01.py")
SPEC = importlib.util.spec_from_file_location("audit186_semantic_01", MODULE_PATH)
assert SPEC and SPEC.loader
verifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verifier)


class Audit186Semantic01Tests(unittest.TestCase):
    def candidate(self):
        return verifier.json_bytes(verifier.CANDIDATE.read_bytes())

    def test_exact_candidate_is_valid(self):
        result = verifier.validate()
        self.assertEqual(result["paths"], 26)
        self.assertEqual(result["proposed_direct"], 26)
        self.assertEqual(result["proposed_grouped"], 0)
        self.assertTrue(result["projection_only"])
        self.assertFalse(result["current_truth_claimed"])

    def test_duplicate_json_key_is_rejected(self):
        with self.assertRaisesRegex(verifier.CandidateError, "duplicate JSON key"):
            verifier.json_bytes(b'{"status":"safe","status":"adopted"}')

    def test_missing_extra_duplicate_and_reordered_paths_are_rejected(self):
        for label, mutate in (
            ("missing", lambda paths: paths.pop()),
            ("extra", lambda paths: paths.append(copy.deepcopy(paths[-1]))),
            ("duplicate", lambda paths: paths.__setitem__(1, copy.deepcopy(paths[0]))),
            ("reordered", lambda paths: paths.reverse()),
        ):
            with self.subTest(label=label):
                doc = self.candidate()
                mutate(doc["family"]["paths"])
                with self.assertRaises(verifier.CandidateError):
                    verifier.validate_document(doc)

    def test_grouped_substitution_is_rejected(self):
        doc = self.candidate()
        doc["family"]["proposed_disposition"] = "GROUPED"
        doc["family"]["grouped_equivalence"]["proposed"] = True
        with self.assertRaisesRegex(verifier.CandidateError, "per-leaf DIRECT"):
            verifier.validate_document(doc)

    def test_per_path_grouped_substitution_is_rejected(self):
        doc = self.candidate()
        doc["family"]["paths"][0]["proposed_disposition"] = "GROUPED"
        with self.assertRaisesRegex(verifier.CandidateError, "non-DIRECT"):
            verifier.validate_document(doc)

    def test_current_truth_overclaim_is_rejected(self):
        for claim in verifier.EXPECTED_CLAIMS:
            with self.subTest(claim=claim):
                doc = self.candidate()
                doc["claims"][claim] = True
                with self.assertRaisesRegex(verifier.CandidateError, "claim drift"):
                    verifier.validate_document(doc)

    def test_adoption_overclaim_is_rejected(self):
        for field in ("adoption_performed", "coverage_adopted"):
            with self.subTest(field=field):
                doc = self.candidate()
                doc[field] = True
                with self.assertRaisesRegex(verifier.CandidateError, "must not claim adoption"):
                    verifier.validate_document(doc)

    def test_projection_must_move_exactly_26_leaves(self):
        doc = self.candidate()
        doc["projection_if_adopted"]["delta"]["direct"] = 25
        with self.assertRaisesRegex(verifier.CandidateError, "accounting drift"):
            verifier.validate_document(doc)

    def test_projection_label_cannot_be_promoted(self):
        doc = self.candidate()
        doc["projection_if_adopted"]["label"] = "ADOPTED"
        with self.assertRaisesRegex(verifier.CandidateError, "accounting drift"):
            verifier.validate_document(doc)

    def test_baseline_coordinate_drift_is_rejected(self):
        doc = self.candidate()
        doc["source_coordinates"]["baseline_head"] = "0" * 40
        with self.assertRaisesRegex(verifier.CandidateError, "coordinate drift"):
            verifier.validate_document(doc)

    def test_current_coordinates_and_canonical_accounting_drift_are_rejected(self):
        mutations = (
            lambda doc: doc["source_coordinates"]["release_observed_current_heads"].__setitem__(
                "atlas", "0" * 40
            ),
            lambda doc: doc["canonical_accounting_before_candidate"].__setitem__(
                "direct", 308
            ),
            lambda doc: doc["projection_if_adopted"]["result"].__setitem__("direct", 334),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                doc = self.candidate()
                mutate(doc)
                with self.assertRaises(verifier.CandidateError):
                    verifier.validate_document(doc)

    def test_semantic_03_overlap_or_readoption_is_rejected(self):
        mutations = (
            lambda doc: doc["canonical_overlap_guard"][
                "later_semantic_03_overlay_paths"
            ].append("meta\tdocs/evidence/repository-audit-2026-09-06/README.md"),
            lambda doc: doc["canonical_overlap_guard"][
                "candidate_historical_family_overlap"
            ].append("docs/evidence/repository-audit-2026-09-06/README.md"),
            lambda doc: doc["canonical_overlap_guard"].__setitem__(
                "candidate_historical_paths_current_disposition", "DIRECT"
            ),
            lambda doc: doc["canonical_overlap_guard"].__setitem__(
                "candidate_historical_paths_current_unverified_count", 25
            ),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                doc = self.candidate()
                mutate(doc)
                with self.assertRaisesRegex(verifier.CandidateError, "overlap/adoption"):
                    verifier.validate_document(doc)

    def test_blob_and_byte_drift_are_rejected(self):
        doc = self.candidate()
        doc["family"]["paths"][0]["blob_sha"] = "0" * 40
        with self.assertRaisesRegex(verifier.CandidateError, "semantic guard digest drift"):
            verifier.validate_document(doc)

    def test_known_manifest_mismatch_cannot_be_silently_repaired(self):
        doc = self.candidate()
        paths = verifier.validate_document(doc)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = verifier.ROOT / verifier.PREFIX
            target = root / verifier.PREFIX
            shutil.copytree(source, target)
            manifest = target / "SHA256SUMS"
            manifest.write_text(
                manifest.read_text().replace(
                    verifier.KNOWN_MANIFEST_MISMATCH["recorded"],
                    verifier.KNOWN_MANIFEST_MISMATCH["actual"],
                )
            )
            with mock.patch.object(verifier, "ROOT", root):
                with self.assertRaisesRegex(verifier.CandidateError, "limitation drift"):
                    verifier.validate_structured_payloads(paths)

    def test_structured_json_duplicate_key_is_rejected(self):
        doc = self.candidate()
        paths = verifier.validate_document(doc)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(verifier.ROOT / verifier.PREFIX, root / verifier.PREFIX)
            json_path = root / verifier.PREFIX / "PUBLICATION-RECEIPT.json"
            json_path.write_text('{"status":"historical","status":"current"}\n')
            with mock.patch.object(verifier, "ROOT", root):
                with self.assertRaisesRegex(verifier.CandidateError, "duplicate JSON key"):
                    verifier.validate_structured_payloads(paths)

    def test_candidate_keeps_claim_surfaces_explicitly_unverified(self):
        doc = self.candidate()
        claims = doc["family"]["intentionally_unverified_claim_surfaces"]
        self.assertEqual(doc["family"]["intentionally_unverified_paths"], [])
        self.assertEqual(len(claims), 3)
        self.assertTrue(any("runtime" in claim for claim in claims))
        self.assertTrue(any("SHA256SUMS" in claim for claim in claims))

    def test_semantic_guards_and_recheck_triggers_are_bound_exactly(self):
        mutations = (
            lambda doc: doc["family"]["paths"][0].__setitem__(
                "semantic_scope",
                "Current runtime truth is accepted; this is not current authority or present-state proof.",
            ),
            lambda doc: doc["family"]["intentionally_unverified_claim_surfaces"].__setitem__(
                0, "Current runtime, security, and CI claims are verified."
            ),
            lambda doc: doc["recheck_triggers"].__setitem__(0, "No meaningful recheck is required."),
            lambda doc: doc.__setitem__("unrecognized_semantic_override", True),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                doc = self.candidate()
                mutate(doc)
                with self.assertRaisesRegex(verifier.CandidateError, "semantic guard digest drift"):
                    verifier.validate_document(doc)

    def test_new_canonical_coverage_review_surface_is_rejected(self):
        doc = self.candidate()
        paths = verifier.validate_document(doc)
        real_git = verifier.git

        def added_coverage_review(*args):
            if args[:3] == ("diff", "--name-only", verifier.BASELINE):
                changed = sorted(
                    verifier.ALLOWED_CHANGED_PATHS
                    | {"docs/evidence/organization-audit-20260907/coverage-review-new.tsv"}
                )
                return ("\n".join(changed) + "\n").encode()
            return real_git(*args)

        with mock.patch.object(verifier, "git", side_effect=added_coverage_review):
            with self.assertRaisesRegex(verifier.CandidateError, "outside exact allowlist"):
                verifier.validate_repository(paths)


if __name__ == "__main__":
    unittest.main()
