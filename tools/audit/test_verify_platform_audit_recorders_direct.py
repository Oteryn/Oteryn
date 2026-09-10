#!/usr/bin/env python3
from __future__ import annotations

import copy
import csv
import io
import json
from pathlib import Path
from unittest import mock
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

    def test_current_lifecycle_is_external_review_metadata_not_pending(self):
        self.assertIn('3eb62ef72c1e13412fa45d5b25d597d112d9ae7d', v.REVIEW_PROVENANCE)
        self.assertIn('Not self-certified evidence', v.REVIEW_PROVENANCE)

    def test_main_emits_current_r6_global_accounting(self):
        output = io.StringIO()
        with mock.patch('sys.argv', ['verify', '--platform-root', '/tmp/platform']), \
             mock.patch.object(v, 'git', return_value=v.CANDIDATE_BLOB), \
             mock.patch.object(v, 'validate_candidate_shape'), \
             mock.patch.object(v, 'validate_adopted_docs'), \
             mock.patch.object(v, 'validate_source'), \
             mock.patch('sys.stdout', output):
            self.assertEqual(v.main(), 0)
        result = json.loads(output.getvalue())
        self.assertEqual(
            {key: result[key] for key in ('current_direct_paths', 'current_grouped_paths', 'current_unverified_paths', 'current_semantically_classified_paths')},
            {'current_direct_paths': 294, 'current_grouped_paths': 113, 'current_unverified_paths': 3918, 'current_semantically_classified_paths': 407},
        )

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

    def test_canonical_recorder_rows_reject_complete_contract_drift(self):
        canonical = ROOT / v.CANONICAL_OVERLAY_REL
        original = canonical.read_text(encoding='utf-8')
        reader = csv.DictReader(io.StringIO(original), delimiter='\t')
        rows = list(reader)

        mutations = []
        for field, value in (
            ('execution_evidence', 'No MariaDB proof; this establishes product readiness.'),
            ('line_ranges', '[[1,1]]'),
        ):
            changed = copy.deepcopy(rows)
            changed[0][field] = value
            mutations.append((list(reader.fieldnames), changed))
        mutations.append((list(reader.fieldnames) + ['unexpected'], [dict(row, unexpected='claim') for row in rows]))
        mutations.append(([field for field in reader.fieldnames if field != 'execution_evidence'], rows))

        for fields, changed in mutations:
            output = io.StringIO(newline='')
            writer = csv.DictWriter(output, fieldnames=fields, delimiter='\t', lineterminator='\n', extrasaction='ignore')
            writer.writeheader(); writer.writerows(changed)
            try:
                canonical.write_text(output.getvalue(), encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'recorder complete current canonical row drift'):
                    v.validate_adopted_docs(copy.deepcopy(self.candidate), ROOT)
            finally:
                canonical.write_text(original, encoding='utf-8')


if __name__ == '__main__':
    unittest.main()
