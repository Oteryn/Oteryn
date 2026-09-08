#!/usr/bin/env python3
from copy import deepcopy
import json
from pathlib import Path
import unittest

import verify_platform_account_character_group as verifier

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = ROOT / verifier.CANDIDATE


class PlatformAccountCharacterCandidateTests(unittest.TestCase):
    def fixture(self):
        return deepcopy(json.loads(CANDIDATE.read_text(encoding='utf-8')))

    def test_committed_pending_candidate_shape_is_exact(self):
        data = self.fixture()
        verifier.validate_candidate_shape(data)
        self.assertEqual(sum(row['expected_count'] for row in data['current_revalidation']['families']), 31)
        self.assertEqual(len(data['current_revalidation']['dependent_blobs']), 23)
        self.assertEqual(len(data['current_revalidation']['focused_test_files']), 15)

    def test_missing_family_fails_closed(self):
        data = self.fixture()
        data['current_revalidation']['families'].pop()
        with self.assertRaisesRegex(ValueError, 'family set/order/count/tree bindings must be exact'):
            verifier.validate_candidate_shape(data)

    def test_family_count_or_tree_drift_fails_closed(self):
        data = self.fixture()
        data['current_revalidation']['families'][0]['expected_count'] = 6
        with self.assertRaisesRegex(ValueError, 'family set/order/count/tree bindings must be exact'):
            verifier.validate_candidate_shape(data)
        data = self.fixture()
        data['current_revalidation']['families'][0]['tree_sha'] = '0' * 40
        with self.assertRaisesRegex(ValueError, 'family set/order/count/tree bindings must be exact'):
            verifier.validate_candidate_shape(data)

    def test_missing_dependency_fails_closed(self):
        data = self.fixture()
        data['current_revalidation']['dependent_blobs'].pop(verifier.FOCUSED_TEST_FILES[0])
        with self.assertRaisesRegex(ValueError, 'exact 23 bindings'):
            verifier.validate_candidate_shape(data)

    def test_focused_test_set_reorder_or_subset_fails_closed(self):
        data = self.fixture()
        data['current_revalidation']['focused_test_files'].reverse()
        with self.assertRaisesRegex(ValueError, 'focused test set/order'):
            verifier.validate_candidate_shape(data)
        data = self.fixture()
        data['current_revalidation']['focused_test_files'].pop()
        with self.assertRaisesRegex(ValueError, 'focused test set/order'):
            verifier.validate_candidate_shape(data)

    def test_source_or_history_coordinate_drift_fails_closed(self):
        data = self.fixture()
        data['current_revalidation']['source_commit'] = '0' * 40
        with self.assertRaisesRegex(ValueError, 'frozen source commit'):
            verifier.validate_candidate_shape(data)
        data = self.fixture()
        data['historical_evidence']['publication_commit'] = '0' * 40
        with self.assertRaisesRegex(ValueError, 'historical publication commit'):
            verifier.validate_candidate_shape(data)

    def test_pending_candidate_cannot_preclaim_adoption(self):
        data = self.fixture()
        data['coverage_adopted'] = True
        with self.assertRaisesRegex(ValueError, 'cannot adopt coverage'):
            verifier.validate_candidate_shape(data)

    def test_bool_total_is_not_integer_31(self):
        data = self.fixture()
        data['expected_total'] = True
        with self.assertRaisesRegex(ValueError, 'candidate total'):
            verifier.validate_candidate_shape(data)


if __name__ == '__main__':
    unittest.main()
