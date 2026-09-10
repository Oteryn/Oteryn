#!/usr/bin/env python3
"""Adversarial tests for the META R6 prompt-family candidate."""
from copy import deepcopy
from pathlib import Path
import csv, json, shutil, tempfile, unittest
import verify_meta_r6_prompts_direct_candidate as v

class MetaR6PromptsCandidateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate = v.expected_candidate()
        cls.temp = tempfile.TemporaryDirectory(prefix='meta-r6-ledger-')
        cls.inventory = v.collect_inventories(v.ROOT, Path(cls.temp.name) / 'audit')
    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()
    def reject_candidate(self, mutation):
        changed = deepcopy(self.candidate); mutation(changed)
        with self.assertRaises(ValueError): v.validate_candidate(changed)
    def copied_evidence(self):
        temp = tempfile.TemporaryDirectory(); root = Path(temp.name)
        shutil.copytree(v.ROOT / 'docs/evidence', root / 'docs/evidence')
        return temp, root
    def test_committed_candidate_source_finding_and_accounting_pass(self):
        v.validate_candidate(deepcopy(self.candidate)); v.validate_source(v.ROOT, self.candidate)
        v.validate_finding(v.ROOT, self.candidate); v.validate_accounting(v.ROOT, self.candidate, self.inventory)
    def test_path_set_blob_source_tree_and_order_fail_closed(self):
        mutations = [lambda c: c['paths'].pop(), lambda c: c['paths'].append(deepcopy(c['paths'][0])), lambda c: c['paths'].append({'path':'extra'}), lambda c: c['paths'][0].update(blob_sha='0'*40), lambda c: c['source'].update(commit='0'*40), lambda c: c['source'].update(subtree_tree='0'*40), lambda c: c['paths'].reverse()]
        for mutation in mutations:
            with self.subTest(mutation=mutation): self.reject_candidate(mutation)
    def test_semantic_rows_authority_classification_and_types_fail_closed(self):
        mutations = [lambda c: c['paths'][0].update(semantic_scope='generic historical plan'), lambda c: c['paths'][0].update(authority_classification='CURRENT_DISPATCH_AUTHORITY'), lambda c: c['paths'][5].update(source_lifecycle_boundary='Historical issue instruction is presently authorized.'), lambda c: c['paths'][0].update(full_file_sha256='0'*64), lambda c: c.update(candidate_path_count='9'), lambda c: c.update(extra_claim=True)]
        for mutation in mutations:
            with self.subTest(mutation=mutation): self.reject_candidate(mutation)
    def test_candidate_tampering_adoption_and_readiness_claims_fail_closed(self):
        mutations = [lambda c: c.update(disposition='DIRECT_ADOPTED'), lambda c: c.update(coverage_delta=9), lambda c: c.update(coverage_adopted=True), lambda c: c.update(adoption_performed=True), lambda c: c.update(currently_canonical_unverified=False), lambda c: c.update(guaranteed_future_adoption=True), lambda c: c.update(product_readiness_claimed=True), lambda c: c.update(audit_completion_claimed=True), lambda c: c.update(live_state_claimed=True)]
        for mutation in mutations:
            with self.subTest(mutation=mutation): self.reject_candidate(mutation)
    def test_excluded_r4_prompts_and_standing_authority_fail_closed(self):
        mutations = [lambda c: c['excluded_already_direct_paths'].pop(), lambda c: c['excluded_already_direct_paths'][0].update(canonical_disposition='UNVERIFIED'), lambda c: c['paths'].append(deepcopy(c['excluded_already_direct_paths'][0])), lambda c: c.update(no_standing_authority_rule='All prompts are current standing authority.'), lambda c: c['paths'][0].update(authority_classification='CURRENT_STANDING_AUTHORITY'), lambda c: c['paths'][1].update(authority_classification='TEMPLATE_REQUIRES_LIVE_AUTHORIZATION')]
        for mutation in mutations:
            with self.subTest(mutation=mutation): self.reject_candidate(mutation)
    def test_temporal_limitations_and_finding_binding_fail_closed(self):
        mutations = [lambda c: c['limitations'].pop(), lambda c: c['dated_main_identity_observation'].update(interpretation='Current live enforcement is proven.'), lambda c: c['finding_bindings'][0].update(state='CLOSED'), lambda c: c['finding_bindings'][0].update(candidate_disposition='RESOLVED'), lambda c: c['finding_bindings'].append(deepcopy(c['finding_bindings'][0]))]
        for mutation in mutations:
            with self.subTest(mutation=mutation): self.reject_candidate(mutation)
    def test_complete_canonical_finding_row_is_bound(self):
        for field in ['repository','scope','evidence','owner_route','closure_condition']:
            temp, root = self.copied_evidence()
            try:
                path = root / v.FINDINGS_REL
                with path.open(encoding='utf-8', newline='') as handle: reader=csv.DictReader(handle,delimiter='\t'); fields=reader.fieldnames; rows=list(reader)
                next(row for row in rows if row['id']=='META-AUD-05')[field] = 'resolved; no further action required'
                with path.open('w',encoding='utf-8',newline='') as handle: writer=csv.DictWriter(handle,fields,delimiter='\t',lineterminator='\n'); writer.writeheader(); writer.writerows(rows)
                with self.assertRaises(ValueError): v.validate_finding(root, self.candidate)
            finally: temp.cleanup()
    def test_direct_or_grouped_overlap_and_unrelated_accounting_drift_fail(self):
        for relative in ['docs/evidence/organization-audit-20260907/coverage-review.tsv','docs/evidence/organization-audit-20260907/coverage-review-meta-r5-instruction-efficiency-direct-additions.tsv']:
            temp, root = self.copied_evidence()
            try:
                path=root/relative
                with path.open(encoding='utf-8',newline='') as handle: reader=csv.DictReader(handle,delimiter='\t'); fields=reader.fieldnames; rows=list(reader)
                row=dict(rows[0]); row.update(repository='meta',path=self.candidate['paths'][0]['path'],blob_sha=self.candidate['paths'][0]['blob_sha']); rows.append(row)
                with path.open('w',encoding='utf-8',newline='') as handle: writer=csv.DictWriter(handle,fields,delimiter='\t',lineterminator='\n');writer.writeheader();writer.writerows(rows)
                with self.assertRaises((ValueError, KeyError)): v.validate_accounting(root,self.candidate,self.inventory)
            finally: temp.cleanup()
    def test_coordinated_summary_and_report_accounting_drift_fails(self):
        temp, root = self.copied_evidence()
        try:
            summary=root/'docs/evidence/organization-audit-20260907/coverage-summary.json'; data=json.loads(summary.read_text()); data['direct_paths']=282; data['unverified_paths']=3930; data['ledger_sha256']='0'*64; summary.write_text(json.dumps(data))
            report=root/v.REPORT_REL; data=json.loads(report.read_text()); data['scoped_review_paths']=282; data['unverified_semantics']=3930; report.write_text(json.dumps(data))
            with self.assertRaises((ValueError, KeyError)): v.validate_accounting(root,self.candidate,self.inventory)
        finally: temp.cleanup()

if __name__ == '__main__': unittest.main()
