#!/usr/bin/env python3
"""Adversarial tests for AUDIT186-SEMANTIC-04."""
from __future__ import annotations

import copy
import importlib.util
import unittest
from unittest import mock
from pathlib import Path

MODULE = Path(__file__).with_name("verify_audit186_semantic_04.py")
SPEC = importlib.util.spec_from_file_location("audit186_semantic_04", MODULE)
assert SPEC and SPEC.loader
verifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verifier)


class Semantic04Tests(unittest.TestCase):
    def candidate(self):
        return verifier.parse_json(verifier.CANDIDATE.read_bytes())

    def assert_document_rejected(self, mutate):
        doc = self.candidate()
        mutate(doc)
        with self.assertRaises(verifier.CandidateError):
            verifier.validate_document(doc)

    def test_exact_candidate_passes(self):
        result = verifier.validate()
        self.assertEqual(result["frozen_meta_unverified"], 88)
        self.assertEqual(result["selected"], 9)
        self.assertEqual(result["proposed_direct"], 9)
        self.assertTrue(result["projection_only"])

    def test_duplicate_json_key_rejected(self):
        with self.assertRaisesRegex(verifier.CandidateError, "duplicate JSON key"):
            verifier.parse_json(b'{"status":"candidate","status":"adopted"}')

    def test_unknown_field_rejected_by_complete_digest(self):
        self.assert_document_rejected(lambda d: d.__setitem__("semantic_override", True))

    def test_path_blob_and_family_set_drift_rejected(self):
        mutations = (
            lambda d: d["family"]["paths"].pop(),
            lambda d: d["family"]["paths"].append(copy.deepcopy(d["family"]["paths"][0])),
            lambda d: d["family"]["paths"].reverse(),
            lambda d: d["family"]["paths"][0].__setitem__("blob_sha", "0" * 40),
            lambda d: d["freeze"]["unverified_paths"].pop(),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                self.assert_document_rejected(mutate)

    def test_disposition_and_grouped_promotion_rejected(self):
        mutations = (
            lambda d: d["family"]["paths"][0].__setitem__("proposed_disposition", "GROUPED"),
            lambda d: d["family"]["grouped_equivalence"].__setitem__("proposed", True),
            lambda d: d.__setitem__("status", "ADOPTED"),
            lambda d: d.__setitem__("coverage_adopted", True),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate): self.assert_document_rejected(mutate)

    def test_semantic_scope_and_negative_claim_overclaim_rejected(self):
        mutations = (
            lambda d: d["family"]["paths"][0].__setitem__("accepted_semantic_scope", "Current policy is authoritative."),
            lambda d: d["claims"].__setitem__("current_policy_or_authority", True),
            lambda d: d["claims"].__setitem__("readiness_or_completion", True),
            lambda d: d["recheck_triggers"].clear(),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate): self.assert_document_rejected(mutate)

    def test_baseline_ledger_overlay_and_projection_drift_rejected(self):
        mutations = (
            lambda d: d["canonical_baseline"].__setitem__("commit", "0" * 40),
            lambda d: d["canonical_baseline"].__setitem__("ledger_sha256", "0" * 64),
            lambda d: d["freeze"]["overlays"].pop(),
            lambda d: d["freeze"].__setitem__("adopted_meta_path_blob_digest", "0" * 64),
            lambda d: d["projection_if_adopted"]["result"].__setitem__("direct", 345),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate): self.assert_document_rejected(mutate)

    def test_changed_path_extra_and_missing_rejected(self):
        doc = self.candidate(); selected = verifier.validate_document(doc); real_git = verifier.git
        cases = (
            verifier.ALLOWED_CHANGED_PATHS | {"docs/evidence/organization-audit-20260907/coverage-review-evil.tsv"},
            verifier.ALLOWED_CHANGED_PATHS - {"tools/audit/test_verify_audit186_semantic_04.py"},
            verifier.ALLOWED_CHANGED_PATHS - {"docs/evidence/organization-audit-20260907/audit186-semantic-04-superpowers-plans-candidate.json"},
        )
        for changed in cases:
            def fake_git(*args, changed=changed):
                if args[:3] == ("diff", "--name-only", verifier.BASELINE):
                    return ("\n".join(sorted(changed)) + "\n").encode()
                return real_git(*args)
            with self.subTest(changed=changed), mock.patch.object(verifier, "git", side_effect=fake_git):
                with self.assertRaisesRegex(verifier.CandidateError, "allowlist mismatch"):
                    verifier.validate_repository(doc, selected)

    def test_prior_worker_file_drift_rejected(self):
        doc = self.candidate(); selected = verifier.validate_document(doc); real_git = verifier.git
        target = sorted(verifier.PRIOR_WORKER_PATHS)[0]
        def fake_git(*args):
            if args == ("show", f"{verifier.PRIOR_WORKER_HEAD}:{target}"):
                return b"drift"
            return real_git(*args)
        with mock.patch.object(verifier, "git", side_effect=fake_git):
            with self.assertRaisesRegex(verifier.CandidateError, "preserved SEMANTIC-01"):
                verifier.validate_repository(doc, selected)


if __name__ == "__main__":
    unittest.main()
