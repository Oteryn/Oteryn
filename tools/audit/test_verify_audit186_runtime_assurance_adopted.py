import copy,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import verify_audit186_runtime_assurance_adopted as v
class RuntimeAssurance(unittest.TestCase):
 def setUp(self):
  self.i=json.loads((v.BASE/'verification-index.json').read_text())['audit186_runtime_assurance_evidence_adoption'];self.u=json.loads((v.BASE/'unknowns.json').read_text())['items'];self.p={n:(v.BASE/'runtime-assurance'/n).read_bytes() for n in v.PACKETS};self.c=(v.BASE/'CHECKPOINT-20260915-RUNTIME-ASSURANCE-ADOPTION.md').read_bytes()
 def ok(self):v.validate(self.i,self.u,self.p,self.c)
 def reject(self,fn):
  i,u,p,c=copy.deepcopy((self.i,self.u,self.p,self.c));i,u,p,c=fn(i,u,p,c) or (i,u,p,c)
  with self.assertRaises(ValueError):v.validate(i,u,p,c)
 def test_valid(self):self.ok()
 def test_worker_source_or_freeze_drift(self):
  for key in ('worker_head','worker_tree','canonical_source_head','canonical_source_tree','freeze_checkpoint'):self.reject(lambda i,u,p,c,k=key:(i.update({k:'wrong'}),(i,u,p,c))[1])
 def test_packet_missing_or_byte_drift(self):
  self.reject(lambda i,u,p,c:(i,u,{**p,'admin-state-20260914.md':p['admin-state-20260914.md']+b'x'},c))
  self.reject(lambda i,u,p,c:(i.update(packets=i['packets'][:1]),(i,u,p,c))[1])
 def test_dispositions_and_all_obligations_stay_open(self):
  self.reject(lambda i,u,p,c:(i.update(admin_state_open_unknown_blocked=False),(i,u,p,c))[1])
  self.reject(lambda i,u,p,c:(i,[row for row in u if row['id']!='RECOVERY'],p,c))
  self.reject(lambda i,u,p,c:(u[[r['id'] for r in u].index('INFRA-STATE')].update(effect='Production ready'),(i,u,p,c))[1])
 def test_negative_claim_and_accounting_boundaries(self):
  for key in ('source_or_workflow_evidence_is_live_truth','product_or_runtime_readiness_claimed','production_health_or_slo_claimed','recovery_rpo_rto_claimed','provider_remediation_claimed','audit_completion_or_independent_score_claimed'):self.reject(lambda i,u,p,c,k=key:(i.update({k:True}),(i,u,p,c))[1])
  self.reject(lambda i,u,p,c:(i.update(semantic_accounting_changed=True),(i,u,p,c))[1])
 def test_privacy_role_and_checkpoint_bound(self):
  self.reject(lambda i,u,p,c:(i.update(verifier_role_required_without_personal_identifier=False),(i,u,p,c))[1])
  self.reject(lambda i,u,p,c:(i,u,p,c+b'x'))
if __name__=='__main__':unittest.main()
