#!/usr/bin/env python3
from __future__ import annotations

import copy
from pathlib import Path
import unittest

import verify_platform_audit_recorders_direct as v

ROOT = Path(__file__).resolve().parents[2]


class AuditRecorderDirectVerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate = v.read_json(ROOT / v.CANDIDATE_REL)

    def test_canonical_candidate_shape_passes(self):
        v.validate_candidate_shape(copy.deepcopy(self.candidate))

    def test_committed_adopted_docs_pass(self):
        v.validate_adopted_docs(copy.deepcopy(self.candidate), ROOT)

    def test_source_coordinate_drift_fails_closed(self):
        c = copy.deepcopy(self.candidate); c['source']['commit_sha'] = '0' * 40
        with self.assertRaisesRegex(ValueError, 'source coordinates'): v.validate_candidate_shape(c)

    def test_path_membership_drift_fails_closed(self):
        c = copy.deepcopy(self.candidate); c['paths'] = c['paths'][:1]
        with self.assertRaisesRegex(ValueError, 'exactly two'): v.validate_candidate_shape(c)

    def test_blob_drift_fails_closed(self):
        c = copy.deepcopy(self.candidate); c['paths'][0]['blob_sha'] = '0' * 40
        with self.assertRaisesRegex(ValueError, 'path/blob'): v.validate_candidate_shape(c)

    def test_downclaim_adoption_fails_closed(self):
        c = copy.deepcopy(self.candidate); c['coverage_adopted'] = False
        with self.assertRaisesRegex(ValueError, 'must be adopted'): v.validate_candidate_shape(c)

    def test_adoption_overlay_binding_drift_fails_closed(self):
        c = copy.deepcopy(self.candidate); c['adoption']['direct_overlay_blob_sha'] = '0' * 40
        with self.assertRaisesRegex(ValueError, 'adoption state'): v.validate_candidate_shape(c)

    def test_projected_digest_drift_fails_closed(self):
        c = copy.deepcopy(self.candidate); c['projected_accounting']['ledger_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'projected accounting'): v.validate_candidate_shape(c)

    def test_primary_qualification_drift_fails_closed(self):
        c = copy.deepcopy(self.candidate); c['qualification']['assertions'] = 88
        with self.assertRaisesRegex(ValueError, 'primary qualification'): v.validate_candidate_shape(c)

    def test_pre_adoption_exact_head_drift_fails_closed(self):
        c = copy.deepcopy(self.candidate); c['pre_adoption_exact_head']['workflow_run'] = 1
        with self.assertRaisesRegex(ValueError, 'pre-adoption exact-head'): v.validate_candidate_shape(c)

    def test_post_adoption_evidence_drift_fails_closed(self):
        c = copy.deepcopy(self.candidate); c['post_adoption_revalidation']['workflow_run'] = 1
        with self.assertRaisesRegex(ValueError, 'post-adoption evidence'): v.validate_candidate_shape(c)

    def test_admin_source_token_tamper_fails_closed(self):
        row = next(r for r in self.candidate['paths'] if r['path'].endswith('AdminAuditRecorder.php'))
        text = '\n'.join(row['semantic_assertions'][:-1])
        with self.assertRaisesRegex(ValueError, 'semantic oracle'): v.validate_source_text(row['path'], text, row)

    def test_security_constant_count_tamper_fails_closed(self):
        row = next(r for r in self.candidate['paths'] if r['path'].endswith('SecurityEventRecorder.php'))
        text = '\n'.join(row['semantic_assertions']) + "\npublic const ONLY_ONE = 'one';\n"
        with self.assertRaisesRegex(ValueError, 'constant count'): v.validate_source_text(row['path'], text, row)

    def test_overlay_blob_hash_is_exact(self):
        self.assertEqual(v.blob_sha((ROOT / v.OVERLAY_REL).read_bytes()), v.OVERLAY_BLOB)


if __name__ == '__main__':
    unittest.main()
