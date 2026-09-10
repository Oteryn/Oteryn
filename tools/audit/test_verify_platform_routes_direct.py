#!/usr/bin/env python3
"""Adversarial tests for the frozen Platform routes candidate."""
from copy import deepcopy
from pathlib import Path
import unittest

import verify_platform_routes_direct as verifier


class PlatformRoutesCandidateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate = verifier.read_json(verifier.ROOT / verifier.CANDIDATE_REL)

    def reject(self, mutate):
        candidate = deepcopy(self.candidate)
        mutate(candidate)
        with self.assertRaises(ValueError):
            verifier.validate_candidate(candidate)

    def test_committed_candidate_passes(self):
        verifier.validate_candidate(deepcopy(self.candidate))
        verifier.validate_current_accounting(verifier.ROOT)

    def test_direct_grouped_overlap_detection_is_exact(self):
        groups = {"groups": [{"repository": "platform", "disposition": "GROUPED",
                              "path_prefix": "routes/"}]}
        prefixes = verifier.grouped_prefixes(groups)
        self.assertTrue(any(path.startswith(prefix) for path in verifier.PATH_BLOBS for prefix in prefixes))

    def test_missing_duplicate_and_extra_paths_fail(self):
        self.reject(lambda c: c["paths"].pop())
        self.reject(lambda c: c["paths"].append(deepcopy(c["paths"][0])))
        self.reject(lambda c: c["paths"].append({"path": "routes/extra.php", "blob_sha": "0" * 40}))

    def test_path_blob_and_tree_drift_fail(self):
        self.reject(lambda c: c["paths"][0].update(blob_sha="0" * 40))
        self.reject(lambda c: c["source"].update(routes_tree_sha="0" * 40))
        self.reject(lambda c: c["source"].update(commit_sha="0" * 40))

    def test_rejected_21_claim_cannot_be_accepted_or_used(self):
        self.reject(lambda c: c["rejected_history"].update(accepted_as_evidence=True))
        self.reject(lambda c: c["rejected_history"].update(used_for_candidate=True))
        self.reject(lambda c: c["source"].update(regular_file_count=21))

    def test_semantic_scope_cannot_be_weakened(self):
        self.reject(lambda c: c["semantic_boundary"]["included"].pop())
        self.reject(lambda c: c["semantic_boundary"]["excluded"].pop())
        self.reject(lambda c: c["semantic_boundary"]["excluded"].remove("production reachability"))

    def test_candidate_cannot_claim_adoption(self):
        self.reject(lambda c: c.update(coverage_adopted=True))
        self.reject(lambda c: c.update(disposition="DIRECT_ADOPTED"))

    def test_readiness_completion_and_finding_closure_fail(self):
        self.reject(lambda c: c["limitations"].append("This establishes product readiness."))
        self.reject(lambda c: c["review_result"].update(existing_provider_findings_closed=True))
        self.reject(lambda c: c.update(audit_complete=True))

    def test_accounting_drift_fails(self):
        self.reject(lambda c: c["canonical_accounting_unchanged"].update(direct_paths=252))
        self.reject(lambda c: c["canonical_accounting_unchanged"].update(ledger_sha256="0" * 64))

    def test_type_and_extra_key_drift_fail(self):
        self.reject(lambda c: c.update(schema_version=True))
        self.reject(lambda c: c["source"].update(readiness=False))


if __name__ == "__main__":
    unittest.main()
