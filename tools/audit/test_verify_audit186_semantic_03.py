#!/usr/bin/env python3
"""Adversarial tests for AUDIT186 semantic batch 03."""
from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path
from unittest import mock

MODULE = Path(__file__).with_name("verify_audit186_semantic_03.py")
SPEC = importlib.util.spec_from_file_location("audit186_semantic_03", MODULE)
assert SPEC and SPEC.loader
verifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verifier)


class Audit186Semantic03Tests(unittest.TestCase):
    def test_exact_candidate_and_canonical_membership_are_valid(self):
        result = verifier.validate()
        self.assertEqual(result["selected_paths"], 1)
        self.assertEqual(result["canonical_population"], 4361)
        self.assertEqual(result["meta_inventory_leaves"], 210)
        self.assertEqual(result["canonical_disposition"], "UNVERIFIED")
        self.assertTrue(result["projection_only"])

    def test_duplicate_json_key_is_rejected(self):
        with self.assertRaisesRegex(verifier.CandidateError, "duplicate JSON key"):
            verifier._pairs([("status", "safe"), ("status", "adopted")])

    def test_any_candidate_semantic_drift_is_rejected(self):
        doc = verifier.load_json(verifier.CANDIDATE)
        mutations = (
            lambda d: d["family"]["paths"][0].__setitem__("canonical_disposition", "DIRECT"),
            lambda d: d["projection_if_adopted"].__setitem__("label", "ADOPTED"),
            lambda d: d["claims"].__setitem__("current_protection_truth", True),
            lambda d: d["excluded_scope"].__setitem__("source_rebaseline_performed", True),
            lambda d: d.__setitem__("unknown_override", True),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                changed = copy.deepcopy(doc)
                mutate(changed)
                with self.assertRaisesRegex(verifier.CandidateError, "candidate digest drift"):
                    verifier.validate_document(changed)

    def test_wrong_or_absent_selected_blob_is_rejected(self):
        real_git = verifier.git
        def altered(*args):
            value = real_git(*args)
            if args[:2] == ("ls-tree", "-r"):
                return value.replace(verifier.SELECTED_BLOB, "0" * 40)
            return value
        with mock.patch.object(verifier, "git", side_effect=altered):
            with self.assertRaisesRegex(verifier.CandidateError, "absent from canonical source inventory"):
                verifier.validate_repository()

    def test_already_direct_is_rejected(self):
        with mock.patch.object(verifier, "direct_paths", return_value={("meta", verifier.SELECTED_PATH)}):
            with self.assertRaisesRegex(verifier.CandidateError, "already DIRECT"):
                verifier.validate_repository()

    def test_already_grouped_is_rejected(self):
        real_load = verifier.load_json
        def load(path):
            data = real_load(path)
            if path == verifier.GROUPS:
                data["groups"].append({"repository": "meta", "path_prefix": "docs/ci/"})
            return data
        with mock.patch.object(verifier, "load_json", side_effect=load):
            with self.assertRaisesRegex(verifier.CandidateError, "already GROUPED"):
                verifier.validate_repository()

    def test_pr204_and_pr207_overlap_is_rejected(self):
        for exclusion in (verifier.PR204_PATHS, verifier.PR207_PATHS):
            with self.subTest(exclusion=id(exclusion)):
                with self.assertRaisesRegex(verifier.CandidateError, "overlaps frozen/rejected"):
                    verifier.validate_prior_packet_exclusions(next(iter(exclusion)))

    def test_population_or_source_rebaseline_is_rejected(self):
        for path, expected in ((verifier.REPORT, verifier.REPORT_SHA256), (verifier.SUMMARY, verifier.SUMMARY_SHA256)):
            with self.subTest(path=path):
                def digest(candidate, *, target=path, original=expected):
                    return "0" * 64 if candidate == target else verifier.hashlib.sha256(candidate.read_bytes()).hexdigest()
                with mock.patch.object(verifier, "sha256", side_effect=digest):
                    with self.assertRaisesRegex(verifier.CandidateError, "identity drift or source rebaseline"):
                        verifier.validate_repository()

    def test_out_of_scope_change_is_rejected(self):
        real_git = verifier.git
        def changed(*args):
            if args[:3] == ("diff", "--name-only", verifier.BASELINE):
                return "docs/evidence/organization-audit-20260907/coverage-review-new.tsv"
            return real_git(*args)
        with mock.patch.object(verifier, "git", side_effect=changed):
            with self.assertRaisesRegex(verifier.CandidateError, "outside exact allowlist"):
                verifier.validate_repository()


if __name__ == "__main__":
    unittest.main()
