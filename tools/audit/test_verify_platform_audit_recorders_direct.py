#!/usr/bin/env python3
from __future__ import annotations

import copy
import unittest

import verify_platform_audit_recorders_direct as v


class AuditRecorderDirectVerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate = v.read_json(v.Path(__file__).resolve().parents[2] / v.CANDIDATE_REL)

    def test_canonical_candidate_shape_passes(self):
        v.validate_candidate_shape(copy.deepcopy(self.candidate))

    def test_source_coordinate_drift_fails_closed(self):
        c = copy.deepcopy(self.candidate)
        c["source"]["commit_sha"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "source coordinates"):
            v.validate_candidate_shape(c)

    def test_path_membership_drift_fails_closed(self):
        c = copy.deepcopy(self.candidate)
        c["paths"] = c["paths"][:1]
        with self.assertRaisesRegex(ValueError, "exactly two"):
            v.validate_candidate_shape(c)

    def test_blob_drift_fails_closed(self):
        c = copy.deepcopy(self.candidate)
        c["paths"][0]["blob_sha"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "path/blob"):
            v.validate_candidate_shape(c)

    def test_premature_adoption_fails_closed(self):
        c = copy.deepcopy(self.candidate)
        c["coverage_adopted"] = True
        with self.assertRaisesRegex(ValueError, "pre-adoption"):
            v.validate_candidate_shape(c)

    def test_projected_count_drift_fails_closed(self):
        c = copy.deepcopy(self.candidate)
        c["projected_accounting"]["direct_paths"] = 224
        with self.assertRaisesRegex(ValueError, "projected accounting"):
            v.validate_candidate_shape(c)

    def test_unearned_qualification_fails_closed(self):
        c = copy.deepcopy(self.candidate)
        c["qualification"]["workflow_run"] = 1
        with self.assertRaisesRegex(ValueError, "unearned qualification"):
            v.validate_candidate_shape(c)

    def test_admin_source_token_tamper_fails_closed(self):
        row = next(r for r in self.candidate["paths"] if r["path"].endswith("AdminAuditRecorder.php"))
        text = "\n".join(row["semantic_assertions"][:-1])
        with self.assertRaisesRegex(ValueError, "semantic oracle"):
            v.validate_source_text(row["path"], text, row)

    def test_security_constant_count_tamper_fails_closed(self):
        row = next(r for r in self.candidate["paths"] if r["path"].endswith("SecurityEventRecorder.php"))
        text = "\n".join(row["semantic_assertions"]) + "\npublic const ONLY_ONE = 'one';\n"
        with self.assertRaisesRegex(ValueError, "constant count"):
            v.validate_source_text(row["path"], text, row)

    def test_direct_overlap_fails_closed(self):
        review = [{"repository": "platform", "path": "app/Audit/AdminAuditRecorder.php"}]
        review.extend({"repository": "meta", "path": f"placeholder/{n}"} for n in range(220))
        summary = {
            "scoped_review_paths": 221,
            "grouped_revalidated_paths": 113,
            "semantically_classified_paths": 334,
            "unverified_semantics_total": 3991,
            "ledger_sha256": self.candidate["baseline_accounting"]["ledger_sha256"],
            "per_repository": {"platform": {"leaves": 2165, "direct_scoped": 156, "grouped": 113, "unverified_semantics": 1896}},
        }
        report = {"scoped_review_paths": 221, "grouped_revalidated_paths": 113, "semantically_classified_paths": 334}
        with self.assertRaisesRegex(ValueError, "already DIRECT"):
            v.validate_pre_adoption_docs(self.candidate, review, summary, report)


if __name__ == "__main__":
    unittest.main()
