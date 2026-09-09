from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools' / 'audit'))

import verify_platform_marketplace_tests_group as verifier

CANDIDATE = ROOT / verifier.CANDIDATE
GROUPS = ROOT / verifier.GROUPS


class PlatformMarketplaceTestsCandidateTests(unittest.TestCase):
    def fixture(self):
        return deepcopy(json.loads(CANDIDATE.read_text(encoding='utf-8')))

    def groups_fixture(self):
        return deepcopy(json.loads(GROUPS.read_text(encoding='utf-8')))

    def test_committed_qualified_candidate_shape_and_group_absence_are_exact(self):
        data = self.fixture()
        verifier.validate_candidate_shape(data)
        verifier.validate_group_absence(self.groups_fixture())
        self.assertTrue(verifier.json_exact(data, verifier.expected_candidate()))
        self.assertEqual(data['qualification']['focused_current_tests']['cases'], 17)
        self.assertEqual(data['qualification']['focused_current_tests']['assertions'], 179)

    def test_bool_total_is_not_integer_six(self):
        data = self.fixture()
        data['expected_total'] = True
        with self.assertRaisesRegex(ValueError, 'canonical evidence fields/key sets drift'):
            verifier.validate_candidate_shape(data)

    def test_path_blob_subset_or_value_drift_fails_closed(self):
        data = self.fixture()
        data['current_revalidation']['path_blobs'].pop(next(iter(data['current_revalidation']['path_blobs'])))
        with self.assertRaisesRegex(ValueError, 'canonical evidence fields/key sets drift'):
            verifier.validate_candidate_shape(data)
        data = self.fixture()
        path = next(iter(data['current_revalidation']['path_blobs']))
        data['current_revalidation']['path_blobs'][path] = '0' * 40
        with self.assertRaisesRegex(ValueError, 'canonical evidence fields/key sets drift'):
            verifier.validate_candidate_shape(data)

    def test_focused_test_order_or_subset_drift_fails_closed(self):
        data = self.fixture()
        data['current_revalidation']['focused_test_files'] = list(reversed(data['current_revalidation']['focused_test_files']))
        with self.assertRaisesRegex(ValueError, 'canonical evidence fields/key sets drift'):
            verifier.validate_candidate_shape(data)
        data = self.fixture()
        data['current_revalidation']['focused_test_files'].pop()
        with self.assertRaisesRegex(ValueError, 'canonical evidence fields/key sets drift'):
            verifier.validate_candidate_shape(data)

    def test_historical_statement_basis_or_coordinate_drift_fails_closed(self):
        for key, value in (
            ('exact_statement', 'changed statement'),
            ('basis', 'selected files inferred'),
            ('publication_commit', '0' * 40),
        ):
            data = self.fixture()
            data['historical_evidence'][key] = value
            with self.assertRaisesRegex(ValueError, 'canonical evidence fields/key sets drift'):
                verifier.validate_candidate_shape(data)

    def test_source_tree_or_prefix_drift_fails_closed(self):
        for key, value in (
            ('source_commit', '0' * 40),
            ('source_tree', '0' * 40),
            ('historical_tree', '0' * 40),
            ('current_tree', '0' * 40),
            ('path_prefix', 'tests/Feature/'),
        ):
            data = self.fixture()
            data['current_revalidation'][key] = value
            with self.assertRaisesRegex(ValueError, 'canonical evidence fields/key sets drift'):
                verifier.validate_candidate_shape(data)

    def test_qualified_candidate_cannot_preclaim_adoption(self):
        mutations = []
        data = self.fixture(); data['state'] = 'QUALIFIED_ADOPTED_AS_GROUPED'; mutations.append(data)
        data = self.fixture(); data['coverage_adopted'] = True; mutations.append(data)
        data = self.fixture(); data['post_adoption_revalidation'] = {'result': 'PASS'}; mutations.append(data)
        for data in mutations:
            with self.assertRaisesRegex(ValueError, 'canonical evidence fields/key sets drift'):
                verifier.validate_candidate_shape(data)

    def test_limitations_required_checks_and_unexpected_key_drift_fail_closed(self):
        mutations = []
        data = self.fixture(); data['limitations'] = 'complete product pass'; mutations.append(data)
        data = self.fixture(); data['current_revalidation']['required_checks'].pop(); mutations.append(data)
        data = self.fixture(); data['unexpected_claim'] = 'complete'; mutations.append(data)
        for data in mutations:
            with self.assertRaisesRegex(ValueError, 'canonical evidence fields/key sets drift'):
                verifier.validate_candidate_shape(data)

    def test_qualification_head_run_job_or_unit_result_drift_fails_closed(self):
        mutations = []
        data = self.fixture(); data['qualification']['qualification_head'] = '0' * 40; mutations.append(data)
        data = self.fixture(); data['qualification']['workflow_run'] += 1; mutations.append(data)
        data = self.fixture(); data['qualification']['job'] += 1; mutations.append(data)
        data = self.fixture(); data['qualification']['verifier_unit_tests'] = 9; mutations.append(data)
        data = self.fixture(); data['qualification']['verifier_unit_result'] = 'FAIL'; mutations.append(data)
        for data in mutations:
            with self.assertRaisesRegex(ValueError, 'canonical evidence fields/key sets drift'):
                verifier.validate_candidate_shape(data)

    def test_qualification_aggregate_or_failure_drift_fails_closed(self):
        for key, value in (
            ('cases', 16),
            ('assertions', 178),
            ('failures', 1),
            ('errors', 1),
            ('skipped', 1),
        ):
            data = self.fixture()
            data['qualification']['focused_current_tests'][key] = value
            with self.assertRaisesRegex(ValueError, 'canonical evidence fields/key sets drift'):
                verifier.validate_candidate_shape(data)

    def test_qualification_junit_subset_reorder_or_count_drift_fails_closed(self):
        data = self.fixture()
        data['qualification']['focused_current_tests']['junit'].pop()
        with self.assertRaisesRegex(ValueError, 'canonical evidence fields/key sets drift'):
            verifier.validate_candidate_shape(data)
        data = self.fixture()
        data['qualification']['focused_current_tests']['junit'].reverse()
        with self.assertRaisesRegex(ValueError, 'canonical evidence fields/key sets drift'):
            verifier.validate_candidate_shape(data)
        data = self.fixture()
        data['qualification']['focused_current_tests']['junit'][0]['assertions'] -= 1
        with self.assertRaisesRegex(ValueError, 'canonical evidence fields/key sets drift'):
            verifier.validate_candidate_shape(data)

    def test_existing_group_prefix_overlap_fails_closed(self):
        groups = self.groups_fixture()
        groups['groups'].append({
            'id': 'OVERLAP',
            'path_prefix': 'tests/Feature/Marketplace/',
        })
        with self.assertRaisesRegex(ValueError, 'overlap existing group'):
            verifier.validate_group_absence(groups)

    def test_existing_group_explicit_path_overlap_fails_closed(self):
        groups = self.groups_fixture()
        groups['groups'].append({
            'id': 'OVERLAP-EXPLICIT',
            'paths': [next(iter(verifier.EXPECTED_PATH_BLOBS))],
        })
        with self.assertRaisesRegex(ValueError, 'overlap explicit existing group'):
            verifier.validate_group_absence(groups)


if __name__ == '__main__':
    unittest.main()
