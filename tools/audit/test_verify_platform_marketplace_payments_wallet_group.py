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

    def adopted_fixture(self):
        data = self.fixture()
        data['state'] = verifier.ADOPTED
        data['coverage_adopted'] = True
        return data

    def adopted_groups_fixture(self, candidate):
        groups = self.groups_fixture()
        groups['groups'].extend(verifier.expected_group(candidate, spec) for spec in verifier.EXPECTED_FAMILIES)
        return groups

    def test_committed_qualified_candidate_shape_is_exact(self):
        data = self.fixture()
        self.assertFalse(verifier.validate_candidate_shape(data))
        verifier.validate_group_state(data, self.groups_fixture(), False)
        self.assertEqual(sum(row['expected_count'] for row in data['current_revalidation']['families']), 49)
        self.assertEqual(len(data['current_revalidation']['dependent_blobs']), 23)
        self.assertEqual(len(data['current_revalidation']['focused_test_files']), 13)
        self.assertEqual(data['qualification']['focused_current_tests']['cases'], 45)
        self.assertEqual(data['qualification']['focused_current_tests']['assertions'], 444)

    def test_exact_primary_qualification_can_be_adopted(self):
        data = self.adopted_fixture()
        self.assertTrue(verifier.validate_candidate_shape(data))
        verifier.validate_group_state(data, self.adopted_groups_fixture(data), True)

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
        with self.assertRaisesRegex(ValueError, 'dependent blob bindings must be exact'):
            verifier.validate_candidate_shape(data)

    def test_focused_test_set_reorder_or_subset_fails_closed(self):
        data = self.fixture(); data['current_revalidation']['focused_test_files'].reverse()
        with self.assertRaisesRegex(ValueError, 'focused test set/order'):
            verifier.validate_candidate_shape(data)
        data = self.fixture(); data['current_revalidation']['focused_test_files'].pop()
        with self.assertRaisesRegex(ValueError, 'focused test set/order'):
            verifier.validate_candidate_shape(data)

    def test_source_history_or_statement_drift_fails_closed(self):
        data = self.fixture(); data['current_revalidation']['source_commit'] = '0' * 40
        with self.assertRaisesRegex(ValueError, 'frozen source commit'):
            verifier.validate_candidate_shape(data)
        data = self.fixture(); data['historical_evidence']['publication_commit'] = '0' * 40
        with self.assertRaisesRegex(ValueError, 'historical publication commit'):
            verifier.validate_candidate_shape(data)
        data = self.fixture(); data['historical_evidence']['exact_statement'] += ' changed'
        with self.assertRaisesRegex(ValueError, 'historical direct-read statement'):
            verifier.validate_candidate_shape(data)

    def test_qualification_head_run_or_job_drift_fails_closed(self):
        for key, value in (
            ('qualification_head', '0' * 40),
            ('workflow_run', verifier.PRIMARY_QUALIFICATION['workflow_run'] + 1),
            ('job', verifier.PRIMARY_QUALIFICATION['job'] + 1),
        ):
            data = self.fixture(); data['qualification'][key] = value
            with self.assertRaisesRegex(ValueError, 'exact bound run/result'):
                verifier.validate_candidate_shape(data)

    def test_qualification_aggregate_downclaim_or_failure_fails_closed(self):
        for key, value in (('cases', 44), ('assertions', 443), ('failures', 1), ('errors', 1), ('skipped', 1)):
            data = self.fixture(); data['qualification']['focused_current_tests'][key] = value
            with self.assertRaisesRegex(ValueError, 'exact bound run/result'):
                verifier.validate_candidate_shape(data)

    def test_qualification_junit_bundle_subset_reorder_or_count_drift_fails_closed(self):
        data = self.fixture(); data['qualification']['focused_current_tests']['junit'].pop()
        with self.assertRaisesRegex(ValueError, 'exact bound run/result'):
            verifier.validate_candidate_shape(data)
        data = self.fixture(); data['qualification']['focused_current_tests']['junit'].reverse()
        with self.assertRaisesRegex(ValueError, 'exact bound run/result'):
            verifier.validate_candidate_shape(data)
        data = self.fixture(); data['qualification']['focused_current_tests']['junit'][0]['assertions'] -= 1
        with self.assertRaisesRegex(ValueError, 'exact bound run/result'):
            verifier.validate_candidate_shape(data)

    def test_adoption_state_and_post_adoption_preclaim_fail_closed(self):
        data = self.fixture(); data['coverage_adopted'] = True
        with self.assertRaisesRegex(ValueError, 'adoption/state mismatch'):
            verifier.validate_candidate_shape(data)
        data = self.fixture(); data['post_adoption_revalidation'] = {'result':'PASS'}
        with self.assertRaisesRegex(ValueError, 'cannot carry post-adoption'):
            verifier.validate_candidate_shape(data)

    def test_group_state_subset_or_evidence_drift_fails_closed(self):
        data = self.adopted_fixture()
        groups = self.adopted_groups_fixture(data)
        groups['groups'].pop()
        with self.assertRaisesRegex(ValueError, 'missing/duplicated canonical groups'):
            verifier.validate_group_state(data, groups, True)
        groups = self.adopted_groups_fixture(data)
        row = next(r for r in groups['groups'] if r.get('id') == verifier.EXPECTED_FAMILIES[0][0])
        row['evaluation']['qualification_run'] += 1
        with self.assertRaisesRegex(ValueError, 'adopted group drift'):
            verifier.validate_group_state(data, groups, True)

    def test_bool_total_is_not_integer_49(self):
        data = self.fixture(); data['expected_total'] = True
        with self.assertRaisesRegex(ValueError, 'candidate total'):
            verifier.validate_candidate_shape(data)


if __name__ == '__main__':
    unittest.main()
