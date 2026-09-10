#!/usr/bin/env python3
"""Adversarial tests for the immutable META R5 candidate."""
from copy import deepcopy
from pathlib import Path
import csv,json,shutil,tempfile,unittest
import verify_meta_r5_instruction_efficiency_direct_candidate as v

class MetaR5CandidateTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.c=v.expected_candidate(); cls.tmp=tempfile.TemporaryDirectory(prefix='r5-ledger-'); cls.inventory=v.collect_inventories(v.ROOT,Path(cls.tmp.name)/'audit')
 @classmethod
 def tearDownClass(cls): cls.tmp.cleanup()
 def reject(self,fn):
  x=deepcopy(self.c); fn(x)
  with self.assertRaises(ValueError): v.validate_candidate(x)
 def copied(self):
  t=tempfile.TemporaryDirectory(); root=Path(t.name); shutil.copytree(v.ROOT/'docs/evidence',root/'docs/evidence'); return t,root
 def test_committed_candidate_source_finding_and_accounting_pass(self):
  v.validate_candidate(deepcopy(self.c)); v.validate_source(v.ROOT,self.c); v.validate_finding(v.ROOT); v.validate_adoption(v.ROOT,self.c); v.validate_accounting(v.ROOT,self.c,self.inventory)
 def test_missing_extra_duplicate_wrong_blob_tree_and_ref_fail(self):
  for fn in [lambda c:c['paths'].pop(),lambda c:c['paths'].append(deepcopy(c['paths'][0])),lambda c:c['paths'].append({'x':'y'}),lambda c:c['paths'][0].update(blob_sha='0'*40),lambda c:c['source'].update(subtree_tree='0'*40),lambda c:c['source'].update(commit='0'*40)]:
   with self.subTest(fn=fn): self.reject(fn)
 def test_semantic_note_generic_mutation_and_type_key_drift_fail(self):
  for fn in [lambda c:c['paths'][0].update(semantic_note='generic source note'),lambda c:c['paths'][3].update(semantic_note='mutated'),lambda c:c['paths'][0].update(full_file_sha256='0'*64),lambda c:c['paths'][0].update(object_type='tree'),lambda c:c.update(candidate_path_count='25'),lambda c:c.update(extra_claim=True)]:
   with self.subTest(fn=fn): self.reject(fn)
 def test_adoption_coverage_and_false_claims_fail(self):
  for fn in [lambda c:c.update(disposition='DIRECT_ADOPTED'),lambda c:c.update(coverage_delta=25),lambda c:c.update(adoption_performed=True),lambda c:c.update(currently_canonical_unverified=False),lambda c:c.update(product_readiness_claimed=True),lambda c:c.update(runtime_attested=True),lambda c:c['limitations'].append('universal B superiority and cost saving established')]:
   with self.subTest(fn=fn): self.reject(fn)
 def test_every_r5q_limitation_is_exact_bound(self):
  for key in list(self.c['r5q_results_limitations']):
   with self.subTest(key=key): self.reject(lambda c,k=key:c['r5q_results_limitations'].pop(k))
  for key in ['worker_configuration_discrepancy','runtime_model_effort_attestation','isolation_attestation','tokens_api_wall_clock','inference_boundary']:
   with self.subTest(key=key): self.reject(lambda c,k=key:c['r5q_results_limitations'].__setitem__(k,'weakened'))
 def test_result_findings_cannot_be_promoted_to_source_findings(self):
  self.reject(lambda c:c['finding_disposition']['new_source_findings'].append('G3B'))
  self.reject(lambda c:c['finding_disposition'].update(result_findings_not_promoted_to_source_findings=[]))
 def mutate_overlay(self,fn):
  t,root=self.copied()
  try:
   p=root/v.OVERLAY_REL
   with p.open(encoding='utf-8',newline='') as f:r=csv.DictReader(f,delimiter='\t');fields=r.fieldnames;rows=list(r)
   fn(rows)
   with p.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fields,delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)
   with self.assertRaises(ValueError):v.validate_adoption(root,self.c)
  finally:t.cleanup()
 def test_adoption_overlay_complete_rows_fail_closed(self):
  mutations=[lambda r:r.pop(),lambda r:r.append(deepcopy(r[0])),lambda r:r[0].update(blob_sha='0'*40),lambda r:r[0].update(depth='LINE_RANGE_REVIEW'),lambda r:r[0].update(scope='generic'),lambda r:r[0].update(line_ranges='[[1,1]]'),lambda r:r[0].update(execution_evidence='Runtime model, isolation, cost and product readiness proven.'),lambda r:r[0].update(path='docs/evidence/OTERYN-R5Q-RESULTS.md')]
  for fn in mutations:
   with self.subTest(fn=fn):self.mutate_overlay(fn)
 def test_adoption_index_provenance_and_counts_fail_closed(self):
  for key,value in [('candidate_path','wrong.json'),('adoption_overlay','wrong.tsv'),('canonical_ledger_sha256','0'*64),('runtime_attested',True)]:
   t,root=self.copied()
   try:
    p=root/v.INDEX_REL;d=json.loads(p.read_text());d['r3_meta_r5_instruction_efficiency_direct_adoption'][key]=value;p.write_text(json.dumps(d))
    with self.assertRaises(ValueError):v.validate_adoption(root,self.c)
   finally:t.cleanup()
 def test_direct_or_grouped_overlap_fails(self):
  for rel in ['docs/evidence/organization-audit-20260907/coverage-review.tsv','docs/evidence/organization-audit-20260907/coverage-review-meta-r4-direct-additions.tsv']:
   t,root=self.copied()
   try:
    p=root/rel
    with p.open(encoding='utf-8',newline='') as f: r=csv.DictReader(f,delimiter='\t'); fields=r.fieldnames; rows=list(r)
    row=dict(rows[0]); row.update(repository='meta',path=self.c['paths'][0]['path'],blob_sha=self.c['paths'][0]['blob_sha']); rows.append(row)
    with p.open('w',encoding='utf-8',newline='') as f: w=csv.DictWriter(f,fields,delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)
    with self.assertRaises(ValueError): v.validate_accounting(root,self.c,self.inventory)
   finally:t.cleanup()
 def test_coordinated_stale_accounting_and_digest_mutation_fails(self):
  t,root=self.copied()
  try:
   summary=root/'docs/evidence/organization-audit-20260907/coverage-summary.json'; d=json.loads(summary.read_text()); d['direct_paths']=257; d['unverified_paths']=3955; d['ledger_sha256']='0'*64; summary.write_text(json.dumps(d))
   report=root/v.REPORT_REL; d=json.loads(report.read_text()); d['scoped_review_paths']=257; d['semantically_classified_paths']=370; report.write_text(json.dumps(d))
   with self.assertRaises((ValueError,KeyError)): v.validate_accounting(root,self.c,self.inventory)
  finally:t.cleanup()
 def test_meta_aud_05_complete_row_is_inherited(self):
  t,root=self.copied()
  try:
   p=root/v.FINDINGS_REL
   with p.open(encoding='utf-8',newline='') as f:r=csv.DictReader(f,delimiter='\t');fields=r.fieldnames;rows=list(r)
   next(x for x in rows if x['id']=='META-AUD-05')['closure_condition']='resolved; no further action required'
   with p.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fields,delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)
   with self.assertRaises(ValueError):v.validate_finding(root)
  finally:t.cleanup()
if __name__=='__main__': unittest.main()
