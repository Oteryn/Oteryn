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
MARKDOWN_REPORT = ROOT / verifier.MARKDOWN_REPORT
INDEX = ROOT / verifier.INDEX


class PlatformMarketplaceTestsAdoptedTests(unittest.TestCase):
    def candidate(self): return deepcopy(json.loads(CANDIDATE.read_text(encoding='utf-8')))
    def groups(self): return deepcopy(json.loads(GROUPS.read_text(encoding='utf-8')))
    def summary(self): return deepcopy(json.loads(SUMMARY.read_text(encoding='utf-8')))
    def report(self): return deepcopy(json.loads(REPORT.read_text(encoding='utf-8')))
    def index(self): return deepcopy(json.loads(INDEX.read_text(encoding='utf-8')))

    def test_committed_adopted_contract_is_exact(self):
        verifier.validate_candidate_shape(self.candidate())
        verifier.validate_group_state(self.groups())
        verifier.validate_accounting(ROOT)

    def test_candidate_state_or_adoption_drift_fails_closed(self):
        for key, value in (('state', 'QUALIFIED_PENDING_ADOPTION'), ('coverage_adopted', False), ('expected_total', True)):
            data = self.candidate(); data[key] = value
            with self.assertRaisesRegex(ValueError, 'candidate canonical'): verifier.validate_candidate_shape(data)

    def test_candidate_limitations_required_checks_basis_or_extra_key_drift_fails_closed(self):
        mutations = []
        d = self.candidate(); d['limitations'] = 'product pass'; mutations.append(d)
        d = self.candidate(); d['current_revalidation']['required_checks'].pop(); mutations.append(d)
        d = self.candidate(); d['historical_evidence']['basis'] = 'inferred'; mutations.append(d)
        d = self.candidate(); d['unexpected'] = 'claim'; mutations.append(d)
        for data in mutations:
            with self.assertRaisesRegex(ValueError, 'candidate canonical'): verifier.validate_candidate_shape(data)

    def test_primary_qualification_coordinate_or_junit_drift_fails_closed(self):
        mutations = []
        d = self.candidate(); d['qualification']['workflow_run'] += 1; mutations.append(d)
        d = self.candidate(); d['qualification']['job'] += 1; mutations.append(d)
        d = self.candidate(); d['qualification']['focused_current_tests']['assertions'] -= 1; mutations.append(d)
        d = self.candidate(); d['qualification']['focused_current_tests']['junit'].reverse(); mutations.append(d)
        for data in mutations:
            with self.assertRaisesRegex(ValueError, 'candidate canonical'): verifier.validate_candidate_shape(data)

    def test_pre_adoption_proof_drift_fails_closed(self):
        for key, value in (('audit_head', '0' * 40), ('workflow_run', 1), ('job', 1), ('verifier_unit_tests', 12), ('meta_ci_result', 'FAILURE')):
            d = self.candidate(); d['pre_adoption_revalidation'][key] = value
            with self.assertRaisesRegex(ValueError, 'candidate canonical'): verifier.validate_candidate_shape(d)

    def test_historical_projected_ledger_digest_count_or_path_drift_fails_closed(self):
        mutations = []
        d = self.candidate(); d['projected_ledger']['ledger_sha256'] = '0' * 64; mutations.append(d)
        d = self.candidate(); d['projected_ledger']['grouped_paths'] = 112; mutations.append(d)
        d = self.candidate(); d['projected_ledger']['new_grouped_paths'].pop(); mutations.append(d)
        d = self.candidate(); d['projected_ledger']['new_grouped_paths'].reverse(); mutations.append(d)
        for data in mutations:
            with self.assertRaisesRegex(ValueError, 'candidate canonical'): verifier.validate_candidate_shape(data)

    def test_post_adoption_evidence_drift_fails_closed(self):
        for key, value in (('audit_head', '0' * 40), ('workflow_run', 1), ('job', 1), ('verifier_unit_tests', 13), ('meta_ci_result', 'FAILURE'), ('ledger_reproduction_artifact', 1), ('ledger_sha256', '0' * 64)):
            d = self.candidate(); d['post_adoption_revalidation'][key] = value
            with self.assertRaisesRegex(ValueError, 'candidate canonical'): verifier.validate_candidate_shape(d)
        d = self.candidate(); d['post_adoption_revalidation']['ledger_counts']['grouped_paths'] = 112
        with self.assertRaisesRegex(ValueError, 'candidate canonical'): verifier.validate_candidate_shape(d)

    def test_group_missing_duplicate_or_scope_drift_fails_closed(self):
        g = self.groups(); g['groups'] = [x for x in g['groups'] if x.get('id') != verifier.GROUP_ID]
        with self.assertRaisesRegex(ValueError, 'missing/duplicated'): verifier.validate_group_state(g)
        g = self.groups(); row = next(x for x in g['groups'] if x.get('id') == verifier.GROUP_ID); g['groups'].append(deepcopy(row))
        with self.assertRaisesRegex(ValueError, 'missing/duplicated'): verifier.validate_group_state(g)
        g = self.groups(); row = next(x for x in g['groups'] if x.get('id') == verifier.GROUP_ID); row['scope'] += ' changed'
        with self.assertRaisesRegex(ValueError, 'canonical group drift'): verifier.validate_group_state(g)

    def test_group_evaluation_or_projected_proof_drift_fails_closed(self):
        g = self.groups(); row = next(x for x in g['groups'] if x.get('id') == verifier.GROUP_ID); row['evaluation']['outcome'] = 'BROKEN'
        with self.assertRaisesRegex(ValueError, 'canonical group drift'): verifier.validate_group_state(g)
        g = self.groups(); row = next(x for x in g['groups'] if x.get('id') == verifier.GROUP_ID); row['evaluation']['projected_ledger']['artifact'] += 1
        with self.assertRaisesRegex(ValueError, 'canonical group drift'): verifier.validate_group_state(g)
        g = self.groups(); row = next(x for x in g['groups'] if x.get('id') == verifier.GROUP_ID); row['evaluation']['post_adoption_revalidation']['workflow_run'] += 1
        with self.assertRaisesRegex(ValueError, 'canonical group drift'): verifier.validate_group_state(g)

    def test_other_group_prefix_overlap_fails_closed(self):
        g = self.groups(); g['groups'].append({'id': 'OVERLAP', 'path_prefix': 'tests/Feature/Marketplace/'})
        with self.assertRaisesRegex(ValueError, 'overlap'): verifier.validate_group_state(g)

    def test_summary_accounting_is_current_and_exact(self):
        s = self.summary(); p = s['per_repository']['platform']
        self.assertEqual(s['ledger_sha256'], verifier.CANONICAL_LEDGER_SHA)
        self.assertEqual((s['scoped_review_paths'], s['grouped_revalidated_paths'], s['semantically_classified_paths'], s['unverified_semantics_total']), (233, 113, 346, 3979))
        self.assertEqual((p['direct_scoped'], p['grouped'], p['unverified_semantics']), (168, 113, 1884))

    def test_report_accounting_and_candidate_binding_are_current_and_exact(self):
        r = self.report()
        self.assertEqual(r['revision'], 'R3-NATIVE-EVIDENCE-POST-REVIEW-PLATFORM-SEMANTIC-CARRYFORWARD-113-DIRECT-233')
        self.assertEqual((r['scoped_review_paths'], r['grouped_revalidated_paths'], r['semantically_classified_paths']), (233, 113, 346))
        self.assertEqual(r['r3_platform_marketplace_tests_candidate'], 'organization-audit-20260907/r3-platform-marketplace-tests-candidate.json')

    def test_companion_markdown_closeout_is_exact_and_fail_closed(self):
        text = MARKDOWN_REPORT.read_text(encoding='utf-8')
        verifier.validate_companion_report_text(text)
        adjacent_claims = (
            'This batch establishes full product readiness.',
            'This batch is still awaiting independent review.',
            'Arbitrary equivalent Marketplace batch status text.',
        )
        mutations = [
            text.replace(verifier.MARKETPLACE_CLOSEOUT, 'The Marketplace batch still needs review.', 1),
            text.replace(verifier.MARKETPLACE_CLOSEOUT, verifier.MARKETPLACE_CLOSEOUT + ' This batch establishes production readiness.', 1),
            text.replace(verifier.MARKETPLACE_CLOSEOUT, verifier.MARKETPLACE_CLOSEOUT + ' This batch establishes full product readiness.', 1),
            text.replace(verifier.MARKETPLACE_CLOSEOUT, verifier.MARKETPLACE_CLOSEOUT + ' This batch is still awaiting independent review.', 1),
            text.replace(verifier.MARKETPLACE_CLOSEOUT, verifier.MARKETPLACE_CLOSEOUT + ' Arbitrary contradictory closeout.', 1),
            text + '\n\n' + verifier.MARKETPLACE_CLOSEOUT + '\n',
        ]
        for claim in adjacent_claims:
            mutations.extend((
                text.replace(verifier.MARKETPLACE_CLOSEOUT, verifier.MARKETPLACE_CLOSEOUT + '\n\n' + claim, 1),
                text.replace(verifier.MARKETPLACE_CLOSEOUT, claim + '\n\n' + verifier.MARKETPLACE_CLOSEOUT, 1),
            ))
        for stale in verifier.STALE_MARKETPLACE_GATES:
            mutations.append(text + '\n\n' + stale + '\n')
        contradictory_claims = (
            'This Marketplace batch establishes full product readiness.',
            'This Marketplace batch is still awaiting independent review.',
        )
        neighbor_mutations = []
        for neighbor in (verifier.MARKETPLACE_CLOSEOUT_PREDECESSOR,
                         verifier.MARKETPLACE_CLOSEOUT_SUCCESSOR):
            neighbor_mutations.extend((neighbor, neighbor + ' ' + claim) for claim in contradictory_claims)
            neighbor_mutations.extend((neighbor, claim) for claim in contradictory_claims)
            neighbor_mutations.extend(((neighbor, neighbor[:-1]), (neighbor, '')))
        mutations.extend(text.replace(original, replacement, 1)
                         for original, replacement in neighbor_mutations)
        for mutated in mutations:
            with self.assertRaisesRegex(ValueError, 'companion Markdown'): verifier.validate_companion_report_text(mutated)

    def test_companion_markdown_allows_unrelated_prose_outside_closeout_slot(self):
        text = MARKDOWN_REPORT.read_text(encoding='utf-8')
        mutated = text.replace('## 8. Reproduction, retention and integration boundary',
                               'An unrelated retention note remains permitted here.\n\n## 8. Reproduction, retention and integration boundary', 1)
        verifier.validate_companion_report_text(mutated)

    def test_verification_index_row_preserves_historical_batch_digest(self):
        i = self.index(); row = i['r3_platform_marketplace_tests_qualification']
        self.assertTrue(verifier.json_exact(row, verifier.expected_index_row()))
        self.assertEqual(row['projected_ledger_sha256'], verifier.MARKETPLACE_LEDGER_SHA)
        self.assertEqual(row['post_adoption_ledger_sha256'], verifier.MARKETPLACE_LEDGER_SHA)
        i['r3_platform_marketplace_tests_qualification']['projected_ledger_sha256'] = '0' * 64
        self.assertFalse(verifier.json_exact(i['r3_platform_marketplace_tests_qualification'], verifier.expected_index_row()))

    def test_strict_json_types_reject_bool_integer_alias(self):
        self.assertFalse(verifier.json_exact({'x': True}, {'x': 1}))
        self.assertFalse(verifier.json_exact({'x': 0}, {'x': False}))


if __name__ == '__main__':
    unittest.main()
