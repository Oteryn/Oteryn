import json, shutil, tempfile, unittest
from pathlib import Path
import verify_audit186_history_revalidation_adopted as audit

ROOT=Path(__file__).resolve().parents[2]
class TestHistoryAdoption(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory(); self.addCleanup(self.t.cleanup); self.root=Path(self.t.name)
  evidence=self.root/'docs/evidence'; base=evidence/'organization-audit-20260907'; base.mkdir(parents=True)
  for name in ('OTERYN-ORGANIZATION-COMPREHENSIVE-AUDIT-20260907.json','OTERYN-ORGANIZATION-COMPREHENSIVE-AUDIT-20260907.md'):
   shutil.copy2(ROOT/'docs/evidence'/name,evidence/name)
  names=('finding-register.tsv','domain-matrix.tsv','unknowns.json','coverage-review.tsv','coverage-review-canonical-additions.tsv','coverage-review-meta-r4-direct-additions.tsv','coverage-review-meta-r5-instruction-efficiency-direct-additions.tsv','coverage-review-meta-r6-prompts-direct-additions.tsv','coverage-review-meta-current-main-governance-direct-additions.tsv','coverage-review-audit186-semantic-03-direct-additions.tsv','audit186-semantic-03-ci-contract-candidate.json','coverage-review-audit186-semantic-01-historical-direct-additions.tsv','audit186-semantic-01-historical-candidate.json','coverage-summary.json','coverage-groups.json','workflow-inventory.tsv','verification-index.json','CHECKPOINT-20260915-RUNTIME-ASSURANCE-ADOPTION.md','history-revalidation-candidate.json','CHECKPOINT-20260915-HISTORY-REVALIDATION-ADOPTION.md')
  for name in names: shutil.copy2(ROOT/'docs/evidence/organization-audit-20260907'/name,base/name)
  shutil.copytree(ROOT/'docs/evidence/organization-audit-20260907/runtime-assurance',base/'runtime-assurance')
 def valid(self): return audit.validate(self.root)
 def mutate_json(self,path,fn):
  d=json.loads(path.read_text()); fn(d); path.write_text(json.dumps(d,indent=2)+'\n')
 def reject(self):
  with self.assertRaises((ValueError,KeyError)): self.valid()
 def test_current_passes_open(self): self.assertTrue(self.valid()['history_revalidation_open'])
 def test_packet_byte_drift_rejected(self):
  p=self.root/'docs/evidence/organization-audit-20260907/history-revalidation-candidate.json'; p.write_bytes(p.read_bytes()+b' '); self.reject()
 def test_game_completeness_promotion_rejected(self):
  p=self.root/'docs/evidence/organization-audit-20260907/history-revalidation-candidate.json'; self.mutate_json(p,lambda d:d['source_boundaries'][1].update(compare_file_list_complete=True)); self.reject()
 def test_negative_claim_promotion_rejected(self):
  p=self.root/'docs/evidence/organization-audit-20260907/history-revalidation-candidate.json'; self.mutate_json(p,lambda d:d['claims'].update(history_revalidation_closed=True)); self.reject()
 def test_index_provenance_drift_rejected(self):
  p=self.root/'docs/evidence/organization-audit-20260907/verification-index.json'; self.mutate_json(p,lambda d:d['audit186_history_revalidation_evidence_adoption'].update(worker_head='0'*40)); self.reject()
 def test_index_accounting_drift_rejected(self):
  p=self.root/'docs/evidence/organization-audit-20260907/verification-index.json'; self.mutate_json(p,lambda d:d['audit186_history_revalidation_evidence_adoption']['canonical_counts'].update(direct=336)); self.reject()
 def test_history_obligation_removal_rejected(self):
  p=self.root/'docs/evidence/organization-audit-20260907/unknowns.json'; self.mutate_json(p,lambda d:d.update(items=[x for x in d['items'] if x['id']!='HISTORY-REVALIDATION'])); self.reject()
 def test_checkpoint_readiness_drift_rejected(self):
  p=self.root/'docs/evidence/organization-audit-20260907/CHECKPOINT-20260915-HISTORY-REVALIDATION-ADOPTION.md'; p.write_text(p.read_text()+'Product ready.\n'); self.reject()
if __name__=='__main__': unittest.main()
