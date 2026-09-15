#!/usr/bin/env python3
"""Verify the bounded ADMIN/INFRA evidence adoption without closing obligations."""
from __future__ import annotations
import hashlib, json, subprocess
from pathlib import Path
import verify_report

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/evidence/organization-audit-20260907'
WORKER='58574f6057713cfb9c7f0756d5c561df949b52b1'
WORKER_TREE='01fb0b69f25a85ebacf40a7efcbc3a43b101b798'
SOURCE='2f78fafbacc12723516bb7dd00376812c31385ef'
SOURCE_TREE='44c64c60f9e71bde27ff86e7d19c77476cc07ade'
LEDGER='d93838bebb6f3690bad3d6182bbc05edd0af8acf8a98d28260e496276b95a22b'
INDEX_SHA='d64c165d1fb9b871af1b7929b2974e26f08c73a39b1472f30c437065c2743250'
CHECKPOINT_SHA='407a8e3dd0626402b02604eb22de5aff86f07c55f683c5d2033b09f85cf28319'
PACKETS={
 'admin-state-20260914.md':('30b36d0ac7c824a562c098d9c51a4ec751c683ea','17ebeba22a93c7e74ca06cacabca110a385362b75dfa2a0985bb0ba4935b4985','ADMIN-STATE'),
 'infra-state-20260914.md':('95d587a4b96faa45eb5dcf74c2dbcd2f39945f71','a918f4d8360bc0f15c6dd9a2cae2a923a6a2d67d17b013c09b3fa3ef280bcef9','INFRA-STATE'),
}
def require(value,message):
 if not value: raise ValueError(message)
def blob_sha(raw):
 return hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest()
def validate(index,unknowns,packet_raw,checkpoint_raw):
 require(hashlib.sha256(json.dumps(index,sort_keys=True,separators=(',',':')).encode()).hexdigest()==INDEX_SHA,'index record drift')
 require(index['worker_head']==WORKER and index['worker_tree']==WORKER_TREE,'worker identity drift')
 require(index['canonical_source_head']==SOURCE and index['canonical_source_tree']==SOURCE_TREE,'canonical source identity drift')
 require(index['freeze_checkpoint']=='issue-186-comment-5675703518','freeze checkpoint drift')
 require(index['worker_contract_adopted'] is False and index['semantic_accounting_changed'] is False,'authority/accounting drift')
 require(index['residual_obligations_open']==14 and index['canonical_ledger_sha256']==LEDGER,'canonical state drift')
 require(index['admin_state_open_unknown_blocked'] is True and index['infra_state_open_unknown_blocked'] is True,'obligation disposition drift')
 require(all(index[key] is False for key in ('source_or_workflow_evidence_is_live_truth','product_or_runtime_readiness_claimed','production_health_or_slo_claimed','recovery_rpo_rto_claimed','provider_remediation_claimed','audit_completion_or_independent_score_claimed')),'negative-claim boundary drift')
 require(index['verifier_role_required_without_personal_identifier'] is True,'non-personal verifier-role boundary drift')
 by_name={Path(row['path']).name:row for row in index['packets']}
 require(set(by_name)==set(PACKETS) and len(index['packets'])==2,'packet set drift')
 for name,(blob,digest,obligation) in PACKETS.items():
  raw=packet_raw[name];row=by_name[name]
  require(blob_sha(raw)==blob and hashlib.sha256(raw).hexdigest()==digest,'packet byte identity drift')
  require(row=={'path':f'runtime-assurance/{name}','blob_sha':blob,'sha256':digest,'obligation':obligation,'disposition':'UNKNOWN / BLOCKED'},'packet index drift')
 rows={row['id']:row for row in unknowns}
 require(len(rows)==14 and rows['ADMIN-STATE']=={'id':'ADMIN-STATE','missing':'Current organization/admin security settings','reason':'Managed integration does not expose all admin-only configuration.','effect':'No current private reporting/scanning/member/privilege attestation.','owner_route':'Organization owner via META186','closure_condition':'Provide dated nonsecret exported settings and authorized verification; never secret values.'},'ADMIN-STATE changed or closed')
 require(rows['INFRA-STATE']=={'id':'INFRA-STATE','missing':'Private production runtime configuration','reason':'No host exception or production access used.','effect':'No infrastructure health or deployment readiness conclusion.','owner_route':'Provider operations owners','closure_condition':'Authorized read-only configuration/health snapshot with redaction and exact release.'},'INFRA-STATE changed or closed')
 require(hashlib.sha256(checkpoint_raw).hexdigest()==CHECKPOINT_SHA,'checkpoint drift')
def main():
 idx=json.loads((BASE/'verification-index.json').read_bytes())['audit186_runtime_assurance_evidence_adoption']
 unknowns=json.loads((BASE/'unknowns.json').read_bytes())['items']
 packet_raw={name:(BASE/'runtime-assurance'/name).read_bytes() for name in PACKETS}
 validate(idx,unknowns,packet_raw,(BASE/'CHECKPOINT-20260915-RUNTIME-ASSURANCE-ADOPTION.md').read_bytes())
 result=verify_report.validate(ROOT/'docs/evidence/OTERYN-ORGANIZATION-COMPREHENSIVE-AUDIT-20260907.json')
 require(tuple(result[k] for k in ('source_leaves','scoped_review_paths','grouped_revalidated_paths','unverified_semantics','semantically_classified_paths'))==(4361,335,113,3913,448),'accounting changed')
 print(json.dumps({'result':'AUDIT186_RUNTIME_ASSURANCE_EVIDENCE_ADOPTED_OBLIGATIONS_OPEN','admin_state':'UNKNOWN / BLOCKED','infra_state':'UNKNOWN / BLOCKED','residual_obligations_open':14,'ledger_sha256':LEDGER},sort_keys=True))
if __name__=='__main__':main()
