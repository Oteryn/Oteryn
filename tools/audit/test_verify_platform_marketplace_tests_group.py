from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

import verify_platform_marketplace_tests_group as verifier

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = ROOT / verifier.CANDIDATE
GROUPS = ROOT / verifier.GROUPS
SUMMARY = ROOT / verifier.SUMMARY
REPORT = ROOT / verifier.REPORT
INDEX = ROOT / verifier.INDEX

class PlatformMarketplaceTestsAdoptedTests(unittest.TestCase):
    def candidate(self):
        return deepcopy(json.loads(CANDIDATE.read_text(encoding='utf-8')))
    def groups(self):
        return deepcopy(json.loads(GROUPS.read_text(encoding='utf-8')))
    def summary(self):
        return deepcopy(json.loads(SUMMARY.read_text(encoding='utf-8')))
    def report(self):
        return deepcopy(json.loads(REPORT.read_text(encoding='utf-8')))
    def index(self):
        return deepcopy(json.loads(INDEX.read_text(encoding='utf-8')))

    def test_committed_adopted_contract_is_exact(self):
        verifier.validate_candidate_shape(self.candidate())
        verifier.validate_group_state(self.groups())
        verifier.validate_accounting(ROOT)

    def test_candidate_state_or_adoption_drift_fails_closed(self):
        for key, value in (('state','QUALIFIED_PENDING_ADOPTION'),('coverage_adopted',False),('expected_total',True)):
            data=self.candidate(); data[key]=value
            with self.assertRaisesRegex(ValueError,'candidate canonical'):
                verifier.validate_candidate_shape(data)

    def test_candidate_limitations_required_checks_basis_or_extra_key_drift_fails_closed(self):
        mutations=[]
        d=self.candidate(); d['limitations']='product pass'; mutations.append(d)
        d=self.candidate(); d['current_revalidation']['required_checks'].pop(); mutations.append(d)
        d=self.candidate(); d['historical_evidence']['basis']='inferred'; mutations.append(d)
        d=self.candidate(); d['unexpected']='claim'; mutations.append(d)
        for data in mutations:
            with self.assertRaisesRegex(ValueError,'candidate canonical'):
                verifier.validate_candidate_shape(data)

    def test_primary_qualification_coordinate_or_junit_drift_fails_closed(self):
        mutations=[]
        d=self.candidate(); d['qualification']['workflow_run']+=1; mutations.append(d)
        d=self.candidate(); d['qualification']['job']+=1; mutations.append(d)
        d=self.candidate(); d['qualification']['focused_current_tests']['assertions']-=1; mutations.append(d)
        d=self.candidate(); d['qualification']['focused_current_tests']['junit'].reverse(); mutations.append(d)
        for data in mutations:
            with self.assertRaisesRegex(ValueError,'candidate canonical'):
                verifier.validate_candidate_shape(data)

    def test_pre_adoption_proof_drift_fails_closed(self):
        for key, value in (('audit_head','0'*40),('workflow_run',1),('job',1),('verifier_unit_tests',12),('meta_ci_result','FAILURE')):
            d=self.candidate(); d['pre_adoption_revalidation'][key]=value
            with self.assertRaisesRegex(ValueError,'candidate canonical'):
                verifier.validate_candidate_shape(d)

    def test_projected_ledger_digest_count_or_path_drift_fails_closed(self):
        mutations=[]
        d=self.candidate(); d['projected_ledger']['ledger_sha256']='0'*64; mutations.append(d)
        d=self.candidate(); d['projected_ledger']['grouped_paths']=112; mutations.append(d)
        d=self.candidate(); d['projected_ledger']['new_grouped_paths'].pop(); mutations.append(d)
        d=self.candidate(); d['projected_ledger']['new_grouped_paths'].reverse(); mutations.append(d)
        for data in mutations:
            with self.assertRaisesRegex(ValueError,'candidate canonical'):
                verifier.validate_candidate_shape(data)

    def test_post_adoption_preclaim_fails_closed(self):
        d=self.candidate(); d['post_adoption_revalidation']={'result':'PASS'}
        with self.assertRaisesRegex(ValueError,'candidate canonical'):
            verifier.validate_candidate_shape(d)

    def test_group_missing_duplicate_or_scope_drift_fails_closed(self):
        g=self.groups(); g['groups']=[x for x in g['groups'] if x.get('id')!=verifier.GROUP_ID]
        with self.assertRaisesRegex(ValueError,'missing/duplicated'):
            verifier.validate_group_state(g)
        g=self.groups(); row=next(x for x in g['groups'] if x.get('id')==verifier.GROUP_ID); g['groups'].append(deepcopy(row))
        with self.assertRaisesRegex(ValueError,'missing/duplicated'):
            verifier.validate_group_state(g)
        g=self.groups(); row=next(x for x in g['groups'] if x.get('id')==verifier.GROUP_ID); row['scope']+=' changed'
        with self.assertRaisesRegex(ValueError,'canonical group drift'):
            verifier.validate_group_state(g)

    def test_group_evaluation_or_projected_proof_drift_fails_closed(self):
        g=self.groups(); row=next(x for x in g['groups'] if x.get('id')==verifier.GROUP_ID); row['evaluation']['outcome']='ADOPTED_GROUPED_CARRY_FORWARD'
        with self.assertRaisesRegex(ValueError,'canonical group drift'):
            verifier.validate_group_state(g)
        g=self.groups(); row=next(x for x in g['groups'] if x.get('id')==verifier.GROUP_ID); row['evaluation']['projected_ledger']['artifact']+=1
        with self.assertRaisesRegex(ValueError,'canonical group drift'):
            verifier.validate_group_state(g)

    def test_other_group_prefix_overlap_fails_closed(self):
        g=self.groups(); g['groups'].append({'id':'OVERLAP','path_prefix':'tests/Feature/Marketplace/'})
        with self.assertRaisesRegex(ValueError,'overlap'):
            verifier.validate_group_state(g)

    def test_summary_accounting_is_exact(self):
        s=self.summary()
        self.assertEqual(s['ledger_sha256'],verifier.LEDGER_SHA)
        self.assertEqual((s['grouped_revalidated_paths'],s['semantically_classified_paths'],s['unverified_semantics_total']),(113,334,3991))
        self.assertEqual((s['per_repository']['platform']['grouped'],s['per_repository']['platform']['unverified_semantics']),(113,1896))

    def test_report_accounting_and_candidate_binding_are_exact(self):
        r=self.report()
        self.assertEqual(r['revision'],'R3-NATIVE-EVIDENCE-POST-REVIEW-PLATFORM-SEMANTIC-CARRYFORWARD-113')
        self.assertEqual((r['scoped_review_paths'],r['grouped_revalidated_paths'],r['semantically_classified_paths']),(221,113,334))
        self.assertEqual(r['r3_platform_marketplace_tests_candidate'],'organization-audit-20260907/r3-platform-marketplace-tests-candidate.json')

    def test_verification_index_row_is_exact(self):
        i=self.index()
        self.assertTrue(verifier.json_exact(i['r3_platform_marketplace_tests_qualification'],verifier.expected_index_row()))
        i['r3_platform_marketplace_tests_qualification']['projected_ledger_sha256']='0'*64
        self.assertFalse(verifier.json_exact(i['r3_platform_marketplace_tests_qualification'],verifier.expected_index_row()))

    def test_strict_json_types_reject_bool_integer_alias(self):
        self.assertFalse(verifier.json_exact({'x':True},{'x':1}))
        self.assertFalse(verifier.json_exact({'x':0},{'x':False}))

if __name__ == '__main__':
    unittest.main()
