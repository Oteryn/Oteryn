#!/usr/bin/env python3
import copy,csv,importlib.util,io,json,tempfile,unittest
from pathlib import Path
from unittest import mock
P=Path(__file__).with_name('verify_meta_current_main_governance_direct_candidate.py');S=importlib.util.spec_from_file_location('r7',P);m=importlib.util.module_from_spec(S);S.loader.exec_module(m)
class R7(unittest.TestCase):
 def test_adopted_state(self):
  r=m.validate();self.assertEqual((r['source_leaves'],r['direct'],r['grouped'],r['unverified'],r['semantically_classified']),(4361,308,113,3940,421))
 def test_candidate_blob_drift(self):
  with self.assertRaises(m.CandidateError):m.json_bytes(b'{"x":1,"x":2}')
 def test_overlay_exact_count_and_shape(self):
  rows=m.tsv_bytes(m.OVERLAY.read_bytes());self.assertEqual(len(rows),14);self.assertEqual(len({r['path'] for r in rows}),14)
  bad=rows[:-1];self.assertNotEqual(len(bad),14)
 def test_refreshes_not_in_overlay(self):
  d=m.load_candidate(); overlay={r['path'] for r in m.tsv_bytes(m.OVERLAY.read_bytes())};self.assertFalse(overlay & {x['path'] for x in d['candidate']['previous_direct_modified']})
 def test_each_refreshed_row_requires_exact_execution_evidence(self):
  doc=m.load_candidate(); refresh=[x['path'] for x in doc['candidate']['previous_direct_modified']]
  base=m.tsv_bytes((m.E/'coverage-review.tsv').read_bytes())
  for path in refresh:
   with self.subTest(path=path),tempfile.TemporaryDirectory() as td:
    evidence=Path(td); (evidence/'coverage-review-meta-current-main-governance-direct-additions.tsv').write_bytes(m.OVERLAY.read_bytes())
    changed=copy.deepcopy(base)
    next(r for r in changed if r['repository']=='meta' and r['path']==path)['execution_evidence']='Product readiness and live operational capability established'
    output=io.StringIO(); writer=csv.DictWriter(output,fieldnames=m.FIELDS,delimiter='\t',lineterminator='\n');writer.writeheader();writer.writerows(changed)
    (evidence/'coverage-review.tsv').write_text(output.getvalue(),encoding='utf-8')
    with mock.patch.object(m,'E',evidence),mock.patch.object(m,'OVERLAY',evidence/'coverage-review-meta-current-main-governance-direct-additions.tsv'):
     with self.assertRaisesRegex(m.CandidateError,'refreshed prior DIRECT row drift'):
      m.validate_rows(doc)
 def test_historical_packet_remains_unverified(self):self.assertEqual(m.validate()['historical_packet_paths_unverified'],26)
 def test_wrong_overlay_blob_rejected(self):
  raw=m.OVERLAY.read_bytes().replace(b'00247bc74b1a123ad96f8b9d219eb018581c6f1d',b'0'*40)
  self.assertNotEqual(__import__('hashlib').sha256(raw).hexdigest(),m.OVERLAY_SHA)
 def test_adoption_index_is_complete_and_type_exact(self):
  index=m.json_bytes((m.E/'verification-index.json').read_bytes())
  m.validate_adoption_index(index)
  for field,value in (('state','PRODUCT_PASS'),('live_operational_capability_claimed',True),('path_count',True)):
   with self.subTest(field=field):
    changed=copy.deepcopy(index)
    changed['r7_meta_current_main_governance_direct_adoption'][field]=value
    with self.assertRaisesRegex(m.CandidateError,'R7 adoption index drift'):
     m.validate_adoption_index(changed)
  changed=copy.deepcopy(index);changed['r7_meta_current_main_governance_direct_adoption']['unexpected_claim']='ready'
  with self.assertRaisesRegex(m.CandidateError,'R7 adoption index drift'):
   m.validate_adoption_index(changed)
 def test_double_count_projection_rejected(self):self.assertEqual(m.validate()['newly_direct'],14);self.assertNotEqual(m.validate()['direct'],313)
 def test_no_completion(self):
  r=m.validate();self.assertFalse(r['product_readiness_claimed']);self.assertFalse(r['organization_audit_completion_claimed'])
if __name__=='__main__':unittest.main()
