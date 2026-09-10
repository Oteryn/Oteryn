#!/usr/bin/env python3
"""Adversarial tests for immutable candidate and exact 25-row META adoption."""
from copy import deepcopy
from pathlib import Path
import csv, json, shutil, tempfile, unittest
import verify_meta_r4_direct_candidate as verifier

class MetaR4DirectAdoptionTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.candidate=verifier.expected_candidate(); cls.tmp=tempfile.TemporaryDirectory(prefix='meta-r4-ledger-')
  cls.inventory=verifier.collect_inventories(verifier.ROOT,Path(cls.tmp.name)/'audit')
 @classmethod
 def tearDownClass(cls): cls.tmp.cleanup()
 def reject_candidate(self,fn):
  v=deepcopy(self.candidate);fn(v)
  with self.assertRaises(ValueError):verifier.validate_candidate(v)
 def copied_root(self):
  t=tempfile.TemporaryDirectory(); root=Path(t.name); shutil.copytree(verifier.ROOT/'docs/evidence',root/'docs/evidence'); return t,root
 def mutate_overlay(self,fn):
  t,root=self.copied_root()
  try:
   p=root/verifier.OVERLAY_REL
   with p.open(newline='',encoding='utf-8') as f:r=csv.DictReader(f,delimiter='\t'); fields=r.fieldnames;rows=list(r)
   fn(rows)
   with p.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fields,delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)
   with self.assertRaises(ValueError):verifier.validate_adoption(root,self.candidate)
  finally:t.cleanup()
 def test_committed_adoption_and_rebuilt_ledger_pass(self):
  verifier.validate_candidate(deepcopy(self.candidate));verifier.validate_source(verifier.ROOT,self.candidate)
  verifier.validate_finding(verifier.ROOT,self.candidate);verifier.validate_adoption(verifier.ROOT,self.candidate)
  verifier.validate_accounting(verifier.ROOT,self.candidate,self.inventory)
 def test_candidate_bytes_are_immutable(self):
  raw=(verifier.ROOT/verifier.CANDIDATE_REL).read_bytes();self.assertEqual(verifier.hashlib.sha256(raw).hexdigest(),verifier.CANDIDATE_SHA256)
  self.reject_candidate(lambda c:c['paths'][0].update(semantic_note='mutated'))
 def test_missing_duplicate_and_extra_candidate_path_fail(self):
  self.reject_candidate(lambda c:c['paths'].pop())
  self.reject_candidate(lambda c:c['paths'].append(deepcopy(c['paths'][0])))
  self.reject_candidate(lambda c:c['paths'].append({'path':'extra','blob_sha':'0'*40,'semantic_note':'x'}))
 def test_wrong_candidate_blob_and_temporal_claim_fail(self):
  self.reject_candidate(lambda c:c['paths'][0].update(blob_sha='0'*40))
  self.reject_candidate(lambda c:c['temporal_authority'].update(retired_prompts_dispatchable=True))
  self.reject_candidate(lambda c:c['limitations'].append('product readiness and audit completion established'))
 def test_missing_duplicate_wrong_blob_depth_scope_evidence_and_ranges_fail(self):
  mutations=[lambda r:r.pop(),lambda r:r.append(deepcopy(r[0])),lambda r:r[0].update(blob_sha='0'*40),
   lambda r:r[0].update(depth='FULL_FILE'),lambda r:r[0].update(scope='weakened'),
   lambda r:r[0].update(execution_evidence='product readiness established'),lambda r:r[0].update(line_ranges='[[1,1]]')]
  for fn in mutations:
   with self.subTest(fn=fn):self.mutate_overlay(fn)
 def test_re_adoption_or_unrelated_disposition_mutation_fails(self):
  t,root=self.copied_root()
  try:
   p=root/'docs/evidence/organization-audit-20260907/coverage-review-canonical-additions.tsv'
   with p.open(newline='',encoding='utf-8') as f:r=csv.DictReader(f,delimiter='\t');fields=r.fieldnames;rows=list(r)
   rows.append(verifier.expected_overlay(self.candidate)[0])
   with p.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fields,delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)
   with self.assertRaises(ValueError):verifier.validate_accounting(root,self.candidate,self.inventory)
  finally:t.cleanup()
  t,root=self.copied_root()
  try:
   p=root/'docs/evidence/organization-audit-20260907/coverage-review.tsv'; lines=p.read_text().splitlines();p.write_text('\n'.join(lines[:-1])+'\n')
   with self.assertRaises(ValueError):verifier.validate_accounting(root,self.candidate,self.inventory)
  finally:t.cleanup()
 def test_grouped_overlap_and_stale_counts_digest_fail(self):
  t,root=self.copied_root()
  try:
   p=root/'docs/evidence/organization-audit-20260907/coverage-groups.json';d=json.loads(p.read_text());d['groups'][0]['path_prefix']='.github/';d['groups'][0]['repository']='meta';p.write_text(json.dumps(d))
   with self.assertRaises(ValueError):verifier.validate_accounting(root,self.candidate,self.inventory)
  finally:t.cleanup()
  t,root=self.copied_root()
  try:
   p=root/'docs/evidence/organization-audit-20260907/coverage-summary.json';d=json.loads(p.read_text());d['ledger_sha256']='73c458b8e1b2a6a5cf02bedbefec8fe3a11d4f883413ef65f6d8dd56952338f9';p.write_text(json.dumps(d))
   with self.assertRaises(ValueError):verifier.validate_accounting(root,self.candidate,self.inventory)
  finally:t.cleanup()
 def test_complete_meta_aud_05_row_and_false_closure_fail(self):
  t,root=self.copied_root()
  try:
   p=root/verifier.FINDINGS_REL
   with p.open(newline='',encoding='utf-8') as f:r=csv.DictReader(f,delimiter='\t');fields=r.fieldnames;rows=list(r)
   next(x for x in rows if x['id']=='META-AUD-05')['closure_condition']='CLOSED'
   with p.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fields,delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)
   with self.assertRaises(ValueError):verifier.validate_finding(root,self.candidate)
  finally:t.cleanup()
 def test_index_readiness_and_digest_claims_fail(self):
  t,root=self.copied_root()
  try:
   p=root/verifier.INDEX_REL;d=json.loads(p.read_text());d['r3_meta_r4_direct_adoption']['product_readiness_claimed']=True;p.write_text(json.dumps(d))
   with self.assertRaises(ValueError):verifier.validate_adoption(root,self.candidate)
  finally:t.cleanup()

if __name__=='__main__':unittest.main()
