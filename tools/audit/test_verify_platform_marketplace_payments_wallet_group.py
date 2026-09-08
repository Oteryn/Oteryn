#!/usr/bin/env python3
from copy import deepcopy
import json
from pathlib import Path
import unittest

import verify_platform_marketplace_payments_wallet_group as verifier

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = ROOT / verifier.CANDIDATE
GROUPS = ROOT / verifier.GROUPS


class PlatformMarketplacePaymentsWalletCandidateTests(unittest.TestCase):
    def fixture(self):
        return deepcopy(json.loads(CANDIDATE.read_text(encoding='utf-8')))

    def groups_fixture(self):
        return deepcopy(json.loads(GROUPS.read_text(encoding='utf-8')))

    def test_committed_pending_candidate_shape_is_exact(self):
        data = self.fixture()
        verifier.validate_candidate_shape(data)
        verifier.validate_group_absence(self.groups_fixture())
        self.assertEqual(sum(row['expected_count'] for row in data['current_revalidation']['families']), 49)
        self.assertEqual(len(data['current_revalidation']['dependent_blobs']), 23)
        self.assertEqual(len(data['current_revalidation']['focused_test_files']), 13)

    def test_missing_family_fails_closed(self):
        data = self.fixture(); data['current_revalidation']['families'].pop()
        with self.assertRaisesRegex(ValueError, 'family set/order/count/tree bindings must be exact'):
            verifier.validate_candidate_shape(data)

    def test_family_count_or_tree_drift_fails_closed(self):
        data = self.fixture(); data['current_revalidation']['families'][0]['expected_count'] = 20
        with self.assertRaisesRegex(ValueError, 'family set/order/count/tree bindings must be exact'):
            verifier.validate_candidate_shape(data)
        data = self.fixture(); data['current_revalidation']['families'][1]['tree_sha'] = '0' * 40
        with self.assertRaisesRegex(ValueError, 'family set/order/count/tree bindings must be exact'):
            verifier.validate_candidate_shape(data)

    def test_dependency_subset_or_blob_drift_fails_closed(self):
        data = self.fixture(); data['current_revalidation']['dependent_blobs'].pop(verifier.FOCUSED_TEST_FILES[0])
        with self.assertRaisesRegex(ValueError, 'exact 23 bindings'):
            verifier.validate_candidate_shape(data)
        data = self.fixture(); data['current_revalidation']['dependent_blobs']['config/payments.php'] = '0' * 40
        with self.assertRaisesRegex(ValueError, 'dependent blob values must be exact'):
            verifier.validate_candidate_shape(data)

    def test_focused_test_set_reorder_or_subset_fails_closed(self):
        data = self.fixture(); data['current_revalidation']['focused_test_files'].reverse()
        with self.assertRaisesRegex(ValueError, 'focused test set/order'):
            verifier.validate_candidate_shape(data)
        data = self.fixture(); data['current_revalidation']['focused_test_files'].pop()
        with self.assertRaisesRegex(ValueError, 'focused test set/order'):
            verifier.validate_candidate_shape(data)

    def test_source_or_history_coordinate_drift_fails_closed(self):
        data = self.fixture(); data['current_revalidation']['source_commit'] = '0' * 40
        with self.assertRaisesRegex(ValueError, 'frozen source commit'):
            verifier.validate_candidate_shape(data)
        data = self.fixture(); data['historical_evidence']['publication_commit'] = '0' * 40
        with self.assertRaisesRegex(ValueError, 'historical publication commit'):
            verifier.validate_candidate_shape(data)

    def test_historical_statement_drift_fails_closed(self):
        data = self.fixture(); data['historical_evidence']['exact_statement'] += ' changed'
        with self.assertRaisesRegex(ValueError, 'historical direct-read statement'):
            verifier.validate_candidate_shape(data)

    def test_pending_candidate_cannot_preclaim_adoption_or_qualification(self):
        data = self.fixture(); data['coverage_adopted'] = True
        with self.assertRaisesRegex(ValueError, 'pending candidate cannot adopt coverage'):
            verifier.validate_candidate_shape(data)
        data = self.fixture(); data['qualification'] = {'outcome': 'PASS'}
        with self.assertRaisesRegex(ValueError, 'pending candidate must not carry qualification'):
            verifier.validate_candidate_shape(data)

    def test_pending_candidate_rejects_premature_group_records(self):
        groups = self.groups_fixture()
        groups['groups'].append({'id': verifier.EXPECTED_FAMILIES[0][0]})
        with self.assertRaisesRegex(ValueError, 'already has accepted group records'):
            verifier.validate_group_absence(groups)

    def test_bool_total_is_not_integer_49(self):
        data = self.fixture(); data['expected_total'] = True
        with self.assertRaisesRegex(ValueError, 'candidate total'):
            verifier.validate_candidate_shape(data)


if __name__ == '__main__':
    unittest.main()
