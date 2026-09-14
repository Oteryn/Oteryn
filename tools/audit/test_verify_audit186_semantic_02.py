#!/usr/bin/env python3
"""Adversarial tests for AUDIT186 semantic batch 02."""
from __future__ import annotations

import copy
import importlib.util
import unittest
from unittest import mock
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("verify_audit186_semantic_02.py")
SPEC = importlib.util.spec_from_file_location("audit186_semantic_02", MODULE_PATH)
assert SPEC and SPEC.loader
verifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verifier)


class Audit186Semantic02Tests(unittest.TestCase):
    def candidate(self):
        return verifier.json_bytes(verifier.CANDIDATE.read_bytes())

    def test_exact_candidate_is_valid(self):
        result = verifier.validate()
        self.assertEqual((result["paths"], result["proposed_direct"]), (2, 2))
        self.assertTrue(result["projection_only"])
        self.assertTrue(result["prior_pr_204_projection_separate"])

    def test_duplicate_json_key_is_rejected(self):
        with self.assertRaisesRegex(verifier.CandidateError, "duplicate JSON key"):
            verifier.json_bytes(b'{"status":"candidate","status":"adopted"}')

    def test_path_set_attacks_are_rejected(self):
        for label, mutate in (
            ("missing", lambda p: p.pop()),
            ("extra", lambda p: p.append(copy.deepcopy(p[-1]))),
            ("duplicate", lambda p: p.__setitem__(1, copy.deepcopy(p[0]))),
            ("reordered", lambda p: p.reverse()),
        ):
            with self.subTest(label=label):
                doc = self.candidate(); mutate(doc["family"]["paths"])
                with self.assertRaises(verifier.CandidateError): verifier.validate_document(doc)

    def test_grouped_substitution_is_rejected(self):
        doc = self.candidate(); doc["family"]["proposed_disposition"] = "GROUPED"
        with self.assertRaisesRegex(verifier.CandidateError, "DIRECT"): verifier.validate_document(doc)

    def test_adoption_and_truth_overclaims_are_rejected(self):
        for field in ("adoption_performed", "coverage_adopted"):
            doc = self.candidate(); doc[field] = True
            with self.assertRaisesRegex(verifier.CandidateError, "must not claim adoption"): verifier.validate_document(doc)
        for claim in verifier.EXPECTED_CLAIMS:
            doc = self.candidate(); doc["claims"][claim] = True
            with self.assertRaisesRegex(verifier.CandidateError, "claim drift"): verifier.validate_document(doc)

    def test_projection_isolated_from_pr204(self):
        mutations = (
            lambda d: d["projection_if_adopted"]["batch_02_delta"].__setitem__("direct", 28),
            lambda d: d["projection_if_adopted"]["prior_pr_204_projection_not_adopted"].__setitem__("direct", 0),
            lambda d: d["projection_if_adopted"].__setitem__("label", "ADOPTED"),
        )
        for mutate in mutations:
            doc = self.candidate(); mutate(doc)
            with self.assertRaisesRegex(verifier.CandidateError, "accounting drift"): verifier.validate_document(doc)

    def test_blob_and_semantic_guard_drift_are_rejected(self):
        for mutate in (
            lambda d: d["family"]["paths"][0].__setitem__("blob_sha", "0" * 40),
            lambda d: d["review"]["limitations"].clear(),
            lambda d: d["recheck_triggers"].clear(),
            lambda d: d.__setitem__("unrecognized_override", True),
        ):
            doc = self.candidate(); mutate(doc)
            with self.assertRaises(verifier.CandidateError): verifier.validate_document(doc)

    def test_machine_report_duplicate_key_is_rejected(self):
        real_read = Path.read_bytes
        def read_bytes(path):
            if path == verifier.ROOT / verifier.PATHS[0]: return b'{"status":"qualified","status":"complete"}'
            return real_read(path)
        with mock.patch.object(Path, "read_bytes", read_bytes):
            with self.assertRaisesRegex(verifier.CandidateError, "duplicate JSON key"): verifier.validate_report_contract()

    def test_report_accounting_or_negative_boundary_drift_is_rejected(self):
        machine = verifier.json_bytes((verifier.ROOT / verifier.PATHS[0]).read_bytes())
        machine["scoped_review_paths"] = 309
        with mock.patch.object(verifier, "json_bytes", return_value=machine):
            with self.assertRaisesRegex(verifier.CandidateError, "accounting/obligation drift"): verifier.validate_report_contract()

    def test_new_canonical_surface_change_is_rejected(self):
        paths = verifier.validate_document(self.candidate())
        real_git = verifier.git
        def changed(*args):
            if args[:3] == ("diff", "--name-only", verifier.BASELINE):
                return ("\n".join(sorted(verifier.ALLOWED_CHANGED_PATHS | {"docs/evidence/organization-audit-20260907/coverage-summary.json"})) + "\n").encode()
            return real_git(*args)
        with mock.patch.object(verifier, "git", side_effect=changed):
            with self.assertRaisesRegex(verifier.CandidateError, "outside exact allowlist"): verifier.validate_repository(paths)

    def test_prior_26_leaf_exclusion_is_fail_closed(self):
        paths = verifier.validate_document(self.candidate())
        real_git = verifier.git
        def shortened(*args):
            result = real_git(*args)
            if args[:4] == ("ls-tree", "-r", "--name-only", verifier.BASELINE) and args[-1] == verifier.PRIOR_PREFIX:
                return b""
            return result
        with mock.patch.object(verifier, "git", side_effect=shortened):
            with self.assertRaisesRegex(verifier.CandidateError, "exclusion set drift"): verifier.validate_repository(paths)


if __name__ == "__main__":
    unittest.main()
