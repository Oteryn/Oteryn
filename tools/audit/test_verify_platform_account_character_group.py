#!/usr/bin/env python3
from copy import deepcopy
import json
from pathlib import Path
import unittest

import verify_platform_account_character_group as verifier

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = ROOT / verifier.CANDIDATE
GROUPS = ROOT / verifier.GROUPS


class PlatformAccountCharacterCandidateTests(unittest.TestCase):
    def fixture(self):
        return deepcopy(json.loads(CANDIDATE.read_text(encoding='utf-8')))

    def groups_fixture(self):
        return deepcopy(json.loads(GROUPS.read_text(encoding='utf-8')))

    def adopted_fixture(self):
        data = self.fixture()
        data['state'] = verifier.ADOPTED
        data['coverage_adopted'] = True
        data['qualification'] = deepcopy(verifier.PRIMARY_QUALIFICATION)
        return data

    def adopted_groups_fixture(self, candidate):
        groups = self.groups_fixture()
        groups['groups'].extend(verifier.expected_group(candidate, spec) for spec in verifier.EXPECTED_FAMILIES)
        return groups

    def test_committed_pending_candidate_shape_is_exact(self):
        data = self.fixture()
        self.assertFalse(verifier.validate_candidate_shape(data))
        self.assertEqual(sum(row['expected_count'] for row in data['current_revalidation']['families']), 31)
        self.assertEqual(len(data['current_revalidation']['dependent_blobs']), 23)
        self.assertEqual(len(data['current_revalidation']['focused_test_files']), 15)
        verifier.validate_group_state(data, self.groups_fixture(), False)

    def test_exact_primary_qualification_can_be_adopted(self):
        data = self.adopted_fixture()
        self.assertTrue(verifier.validate_candidate_shape(data))
        verifier.validate_group_state(data, self.adopted_groups_fixture(data), True)

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

    def test_pending_candidate_cannot_preclaim_adoption_or_qualification(self):
        data = self.fixture()
        data['coverage_adopted'] = True
        with self.assertRaisesRegex(ValueError, 'adoption/state mismatch'):
            verifier.validate_candidate_shape(data)
        data = self.fixture()
        data['qualification'] = deepcopy(verifier.PRIMARY_QUALIFICATION)
        with self.assertRaisesRegex(ValueError, 'pending candidate must not carry adoption qualification'):
            verifier.validate_candidate_shape(data)

    def test_qualification_run_or_job_drift_fails_closed(self):
        for key in ('workflow_run', 'job'):
            data = self.adopted_fixture()
            data['qualification'][key] += 1
            with self.assertRaisesRegex(ValueError, 'exact bound run/result'):
                verifier.validate_candidate_shape(data)

    def test_qualification_head_drift_fails_closed(self):
        data = self.adopted_fixture()
        data['qualification']['qualification_head'] = '0' * 40
        with self.assertRaisesRegex(ValueError, 'exact bound run/result'):
            verifier.validate_candidate_shape(data)

    def test_qualification_downclaim_or_result_drift_fails_closed(self):
        for key, value in (('cases', 85), ('assertions', 585), ('failures', 1), ('errors', 1), ('skipped', 1)):
            data = self.adopted_fixture()
            data['qualification']['focused_current_tests'][key] = value
            with self.assertRaisesRegex(ValueError, 'exact bound run/result'):
                verifier.validate_candidate_shape(data)

    def test_adopted_group_subset_or_group_evidence_drift_fails_closed(self):
        data = self.adopted_fixture()
        groups = self.adopted_groups_fixture(data)
        groups['groups'].pop()
        with self.assertRaisesRegex(ValueError, 'missing/duplicated canonical groups'):
            verifier.validate_group_state(data, groups, True)

        groups = self.adopted_groups_fixture(data)
        account = next(row for row in groups['groups'] if row.get('id') == verifier.EXPECTED_FAMILIES[0][0])
        account['evaluation']['qualification_run'] += 1
        with self.assertRaisesRegex(ValueError, 'adopted group drift'):
            verifier.validate_group_state(data, groups, True)

    def test_pending_candidate_rejects_premature_group_records(self):
        data = self.fixture()
        groups = self.adopted_groups_fixture(self.adopted_fixture())
        with self.assertRaisesRegex(ValueError, 'pending candidate already present'):
            verifier.validate_group_state(data, groups, False)

    def test_bool_total_is_not_integer_31(self):
        data = self.fixture()
        data['expected_total'] = True
        with self.assertRaisesRegex(ValueError, 'candidate total'):
            verifier.validate_candidate_shape(data)


if __name__ == '__main__':
    unittest.main()
