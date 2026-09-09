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
        with self.assertRaisesRegex(ValueError, 'complete audit-recorder candidate'): v.validate_candidate_shape(c)

    def test_path_membership_drift_fails_closed(self):
        c = copy.deepcopy(self.candidate); c['paths'] = c['paths'][:1]
        with self.assertRaisesRegex(ValueError, 'complete audit-recorder candidate'): v.validate_candidate_shape(c)

    def test_blob_drift_fails_closed(self):
        c = copy.deepcopy(self.candidate); c['paths'][0]['blob_sha'] = '0' * 40
        with self.assertRaisesRegex(ValueError, 'complete audit-recorder candidate'): v.validate_candidate_shape(c)

    def test_downclaim_adoption_fails_closed(self):
        c = copy.deepcopy(self.candidate); c['coverage_adopted'] = False
        with self.assertRaisesRegex(ValueError, 'complete audit-recorder candidate'): v.validate_candidate_shape(c)

    def test_adoption_overlay_binding_drift_fails_closed(self):
        c = copy.deepcopy(self.candidate); c['adoption']['direct_overlay_blob_sha'] = '0' * 40
        with self.assertRaisesRegex(ValueError, 'complete audit-recorder candidate'): v.validate_candidate_shape(c)

    def test_projected_digest_drift_fails_closed(self):
        c = copy.deepcopy(self.candidate); c['projected_accounting']['ledger_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'complete audit-recorder candidate'): v.validate_candidate_shape(c)

    def test_primary_qualification_drift_fails_closed(self):
        c = copy.deepcopy(self.candidate); c['qualification']['assertions'] = 88
        with self.assertRaisesRegex(ValueError, 'complete audit-recorder candidate'): v.validate_candidate_shape(c)

    def test_pre_adoption_exact_head_drift_fails_closed(self):
        c = copy.deepcopy(self.candidate); c['pre_adoption_exact_head']['workflow_run'] = 1
        with self.assertRaisesRegex(ValueError, 'complete audit-recorder candidate'): v.validate_candidate_shape(c)

    def test_post_adoption_evidence_drift_fails_closed(self):
        c = copy.deepcopy(self.candidate); c['post_adoption_revalidation']['workflow_run'] = 1
        with self.assertRaisesRegex(ValueError, 'complete audit-recorder candidate'): v.validate_candidate_shape(c)

    def test_complete_evidence_contract_rejects_semantic_and_provenance_drift(self):
        mutations = []
        c = copy.deepcopy(self.candidate); c['paths'][0]['semantic_assertions'].pop(); mutations.append(c)
        c = copy.deepcopy(self.candidate); c['focused_current_tests'][0]['required_text'] = 'weaker_text'; mutations.append(c)
        c = copy.deepcopy(self.candidate); c['qualification']['artifact_sha256'] = '0' * 64; mutations.append(c)
        c = copy.deepcopy(self.candidate); c['qualification']['mariadb_image'] = 'sqlite:latest'; mutations.append(c)
        c = copy.deepcopy(self.candidate); c['qualification']['db_connection'] = 'sqlite'; mutations.append(c)
        c = copy.deepcopy(self.candidate); c['unexpected_claim'] = 'product ready'; mutations.append(c)
        c = copy.deepcopy(self.candidate); c['limitations'].append('This slice establishes full product readiness.'); mutations.append(c)
        for candidate in mutations:
            with self.assertRaisesRegex(ValueError, 'complete audit-recorder candidate'):
                v.validate_candidate_shape(candidate)

    def test_complete_evidence_contract_rejects_nested_extra_keys_and_type_drift(self):
        mutations = []
        c = copy.deepcopy(self.candidate); c['persistence_contract'][0]['unexpected'] = True; mutations.append(c)
        c = copy.deepcopy(self.candidate); c['focused_current_tests'][0]['role'] = 'PROMOTED'; mutations.append(c)
        c = copy.deepcopy(self.candidate); c['initial_projection']['workflow_run'] = True; mutations.append(c)
        c = copy.deepcopy(self.candidate); c['qualification']['status'] = 'SUCCESS'; mutations.append(c)
        for candidate in mutations:
            with self.assertRaisesRegex(ValueError, 'complete audit-recorder candidate'):
                v.validate_candidate_shape(candidate)

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
