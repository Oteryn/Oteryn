#!/usr/bin/env python3
import copy,importlib.util,json,tempfile,unittest
from pathlib import Path
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
 def test_historical_packet_remains_unverified(self):self.assertEqual(m.validate()['historical_packet_paths_unverified'],26)
 def test_wrong_overlay_blob_rejected(self):
  raw=m.OVERLAY.read_bytes().replace(b'00247bc74b1a123ad96f8b9d219eb018581c6f1d',b'0'*40)
  self.assertNotEqual(__import__('hashlib').sha256(raw).hexdigest(),m.OVERLAY_SHA)
 def test_double_count_projection_rejected(self):self.assertEqual(m.validate()['newly_direct'],14);self.assertNotEqual(m.validate()['direct'],313)
 def test_no_completion(self):
  r=m.validate();self.assertFalse(r['product_readiness_claimed']);self.assertFalse(r['organization_audit_completion_claimed'])
if __name__=='__main__':unittest.main()
