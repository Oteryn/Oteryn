import copy,csv,io,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import verify_audit186_semantic_01_adopted as v
class Adoption(unittest.TestCase):
 def setUp(self):
  self.c=json.loads((v.BASE/'audit186-semantic-01-historical-candidate.json').read_text()); self.rows=v.parse_overlay((v.BASE/v.verify_report.AUDIT186_SEMANTIC_01_DIRECT_ADDITIONS).read_bytes()); self.s=json.loads((v.BASE/'coverage-summary.json').read_text()); self.i=json.loads((v.BASE/'verification-index.json').read_text())['audit186_semantic_01_historical_direct_adoption']
 def ok(self): v.validate_packet(self.c,self.rows,self.s,self.i)
 def reject(self,fn):
  c,r,s,i=copy.deepcopy((self.c,self.rows,self.s,self.i));fn(c,r,s,i)
  with self.assertRaises(ValueError):v.validate_packet(c,r,s,i)
 def test_valid(self):self.ok()
 def test_wrong_missing_duplicate_path(self):
  for fn in (lambda c,r,s,i:r.pop(),lambda c,r,s,i:r.__setitem__(1,copy.deepcopy(r[0])),lambda c,r,s,i:r[0].update(path='wrong')): self.reject(fn)
 def test_blob_drift(self):self.reject(lambda c,r,s,i:r[0].update(blob_sha='0'*40))
 def test_overlap_or_already_direct_candidate_drift(self):self.reject(lambda c,r,s,i:c['canonical_accounting_before_candidate'].update(direct=310))
 def test_grouped_substitution(self):self.reject(lambda c,r,s,i:r[0].update(depth='GROUPED'))
 def test_scope_current_truth_promotion(self):self.reject(lambda c,r,s,i:r[0].update(scope='current product truth'))
 def test_stale_projection(self):self.reject(lambda c,r,s,i:s.update(scoped_review_paths=334))
 def test_ledger_report_summary_binding(self):
  self.reject(lambda c,r,s,i:s.update(ledger_sha256='0'*64)); self.reject(lambda c,r,s,i:i.update(canonical_ledger_sha256='0'*64)); self.reject(lambda c,r,s,i:i.update(semantic_coverage_complete=True))
 def test_durability_requires_historical_transition_and_current_adoption(self):
  self.reject(lambda c,r,s,i:s.update(durability=s['durability'].replace(v.HISTORICAL_DURABILITY_FRAGMENT,v.FORBIDDEN_STALE_DURABILITY_FRAGMENT)))
  self.reject(lambda c,r,s,i:s.update(durability=s['durability'].replace(v.ADOPTION_DURABILITY_FRAGMENT,'The historical packet is not adopted')))
if __name__=='__main__':unittest.main()
