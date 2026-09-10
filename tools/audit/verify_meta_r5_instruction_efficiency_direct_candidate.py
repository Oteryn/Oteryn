#!/usr/bin/env python3
"""Fail-closed verifier for the META R5 instruction-efficiency DIRECT candidate."""
from __future__ import annotations
import argparse, contextlib, csv, hashlib, io, json, subprocess, tempfile
from pathlib import Path
import organization_audit
import verify_report

ROOT=Path(__file__).resolve().parents[2]
CANDIDATE_REL=Path('docs/evidence/organization-audit-20260907/r3-meta-r5-instruction-efficiency-direct-candidate.json')
CANDIDATE_SHA256='a6ff7425e1a1d338bd02c769cc930109bf28c03db39b896c2ceb90233234eef3'
REPORT_REL=Path('docs/evidence/OTERYN-ORGANIZATION-COMPREHENSIVE-AUDIT-20260907.json')
PLAN_REL=Path('docs/evidence/organization-audit-20260907/collection-plan.json')
OVERLAY_REL=Path('docs/evidence/organization-audit-20260907/coverage-review-meta-r5-instruction-efficiency-direct-additions.tsv')
INDEX_REL=Path('docs/evidence/organization-audit-20260907/verification-index.json')
OVERLAY_SHA256='929b2afdb37263181ea116a4c9616ce25f58e12c26f04d12dd8ed6dd2a60d4ad'
FINDINGS_REL=Path('docs/evidence/organization-audit-20260907/finding-register.tsv')
SOURCE='1a01c5b3e08666a82245b1cac78da3736c65e785'
SOURCE_TREE='f084e824ec5e14d5909c9750d906d91d51425fd5'
SUBTREE='docs/agents/evals/r5-instruction-efficiency'
SUBTREE_TREE='58673e86047adc98c4612c3bedf78f6d47175139'
LIVE_MAIN='3b39e0be05aef008f1bd442821daefa898a201dd'
LEDGER_SHA='27654f5f724d9857912e69fd036712dd00d63882ebf8e9c1411c26c66eaeef41'
INVENTORY_IDS={'meta','game','platform','atlas','migration_archive'}
EXPECTED_BLOBS={
'docs/agents/evals/r5-instruction-efficiency/README.md':'0dd93bcbecd1a9595fba40c7bb1d992149e0904b','docs/agents/evals/r5-instruction-efficiency/REVIEWER.md':'766a94df34cda5dae852069e3eca584e7d02ded1','docs/agents/evals/r5-instruction-efficiency/TRIAL_PROTOCOL.md':'1a02b16b60dad93b0b671c049f76797e1c781df8','docs/agents/evals/r5-instruction-efficiency/arms/A1A.md':'b79ca465001e90b6862949c189898b94417adafa','docs/agents/evals/r5-instruction-efficiency/arms/A1B.md':'ff83774f63e2cb91afd49a8c599b6582adc1547f','docs/agents/evals/r5-instruction-efficiency/arms/A2A.md':'7c850c28dda5078f339d6a3327c4cefd179ac3f9','docs/agents/evals/r5-instruction-efficiency/arms/A2B.md':'939a7405a5205e840bce5ff1c1f3a6007e6f8bae','docs/agents/evals/r5-instruction-efficiency/arms/A3A.md':'d505f584824b0351c1c30a4346c7f93da844ae94','docs/agents/evals/r5-instruction-efficiency/arms/A3B.md':'2cd0537490ae9e197fa083f8d325a0f984dd02a9','docs/agents/evals/r5-instruction-efficiency/arms/G1A.md':'d9ea039388ce77367ffb4121c87ed411e9ca3a76','docs/agents/evals/r5-instruction-efficiency/arms/G1B.md':'838185a82d62ae799d7d9fa343148cf1e2222a74','docs/agents/evals/r5-instruction-efficiency/arms/G2A.md':'3c3ce298d2fcf32cc7a93f8a656623ba2b89e83d','docs/agents/evals/r5-instruction-efficiency/arms/G2B.md':'41163138c1a98b85c488f5288375b43fd807e9ef','docs/agents/evals/r5-instruction-efficiency/arms/G3A.md':'a2f3ae8105237f1b7662a093d73e875cd0eeb130','docs/agents/evals/r5-instruction-efficiency/arms/G3B.md':'a42642e3357e947217717c443d333c7a968db6aa','docs/agents/evals/r5-instruction-efficiency/arms/G4A.md':'8590bfcfab4adf0b3969758715abea431b197821','docs/agents/evals/r5-instruction-efficiency/arms/G4B.md':'d9329424c2437e573394b48d5b54b6ae47ffd4c8','docs/agents/evals/r5-instruction-efficiency/arms/P1A.md':'921dfc5f8120a74e3daac7b9e19a503cabc811b7','docs/agents/evals/r5-instruction-efficiency/arms/P1B.md':'43729e1943a66ebdc19b1237cc3d2bf6dc49674e','docs/agents/evals/r5-instruction-efficiency/arms/P2A.md':'3d28f721f890e2ed9998454ff819f88cd4ee16f6','docs/agents/evals/r5-instruction-efficiency/arms/P2B.md':'93564ee5af28f2e6180cea564fb1274335d885a8','docs/agents/evals/r5-instruction-efficiency/arms/P3A.md':'9e60d298fd1bd88fa985d3817be20598baf5d239','docs/agents/evals/r5-instruction-efficiency/arms/P3B.md':'dfc51c039d64b0250a5dcf7a744c694302e2f812','docs/agents/evals/r5-instruction-efficiency/arms/P4A.md':'fda70c648364b3764ace60fdb99891672a56a39b','docs/agents/evals/r5-instruction-efficiency/arms/P4B.md':'3a30e77652f54a8cf61f12866f52501e64443ffc'}
EXPECTED_META_AUD_05={'id':'META-AUD-05','priority':'P2','repository':'meta','state':'PARTIALLY_REPAIRED','scope':'governance','title':'Historical authority and merge-up conflict','evidence':'META-153 | Current access policy separates MQ candidate refresh from source-head churn. Historical/open PR authority liveness is not exhaustively revalidated.','owner_route':'Oteryn/Oteryn#153; evidence continuation #186','closure_condition':'Classify remaining operative-looking documents/PRs against current v3 authority without deleting historical evidence.'}

def require(v,m):
 if not v: raise ValueError(m)
def json_exact(a,e,p='root'):
 require(type(a) is type(e),p+' JSON type drift')
 if isinstance(e,dict):
  require(list(a)==list(e),p+' key set/order drift')
  for k in e: json_exact(a[k],e[k],p+'.'+k)
 elif isinstance(e,list):
  require(len(a)==len(e),p+' list length drift')
  for i,(x,y) in enumerate(zip(a,e)): json_exact(x,y,f'{p}[{i}]')
 else: require(a==e,p+' value drift')
def read_json(path):
 def pairs(items):
  d={}
  for k,v in items: require(k not in d,'duplicate JSON key: '+k); d[k]=v
  return d
 return json.loads(path.read_text(encoding='utf-8'),object_pairs_hook=pairs)
def expected_candidate(root=ROOT):
 raw=(root/CANDIDATE_REL).read_bytes(); require(hashlib.sha256(raw).hexdigest()==CANDIDATE_SHA256,'candidate complete-file SHA drift'); return read_json(root/CANDIDATE_REL)
def validate_candidate(candidate,expected=None): json_exact(candidate,expected or expected_candidate())
def git(root,*args): return subprocess.run(['git','-c','core.hooksPath=/dev/null',*args],cwd=root,check=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60).stdout.strip()
def validate_source(root,c):
 require(git(root,'rev-parse',SOURCE+'^{tree}')==SOURCE_TREE,'source tree drift')
 require(git(root,'rev-parse',SOURCE+':'+SUBTREE)==SUBTREE_TREE,'source subtree tree drift')
 require(git(root,'rev-parse',LIVE_MAIN+'^{commit}')==LIVE_MAIN,'current-main identity unavailable')
 observed={}; hashes={}
 for row in c['paths']:
  p=row['path']; spec=SOURCE+':'+p
  require(git(root,'cat-file','-t',spec)=='blob','source object type drift: '+p)
  blob=git(root,'rev-parse',spec); data=subprocess.run(['git','cat-file','blob',blob],cwd=root,check=True,stdout=subprocess.PIPE,timeout=60).stdout
  observed[p]=blob; hashes[p]=hashlib.sha256(data).hexdigest()
  require(git(root,'rev-parse',LIVE_MAIN+':'+p)==blob,'current-main source identity drift: '+p)
 require(observed==EXPECTED_BLOBS,'exact source path/blob set drift')
 require(hashes=={r['path']:r['full_file_sha256'] for r in c['paths']},'full-file SHA-256 contract drift')
 require(all(r['object_type']=='blob' for r in c['paths']),'object type contract drift')
def validate_finding(root):
 with (root/FINDINGS_REL).open(encoding='utf-8',newline='') as f: rows=list(csv.DictReader(f,delimiter='\t'))
 found=[r for r in rows if r['id']=='META-AUD-05']; require(len(found)==1,'META-AUD-05 missing or duplicated'); json_exact(found[0],EXPECTED_META_AUD_05,'META-AUD-05')
def collect_inventories(root,out):
 plan=read_json(root/PLAN_REL); plan['snapshots']=[x for x in plan['snapshots'] if x['id'] in INVENTORY_IDS]; require({x['id'] for x in plan['snapshots']}==INVENTORY_IDS,'inventory set drift')
 with contextlib.redirect_stdout(io.StringIO()): organization_audit.collect(plan,out)
 return out/'inventories'
def expected_overlay(c):
 evidence=('Exact source file received bounded full-file semantic review at immutable META source cut '+SOURCE+' and was separately adopted after clean candidate review of 334d6b9f0a856b9ad11ddd22b39f358249a61d44. This is source-semantic evidence only; runtime model/effort, fresh isolation, answer correctness or safety, A/B superiority, provider permission, cost, and product readiness are not attested.')
 return [{'repository':'meta','path':r['path'],'blob_sha':r['blob_sha'],'depth':'SCOPED_SEMANTIC_REVIEW','scope':r['semantic_note'],'line_ranges':'[]','execution_evidence':evidence} for r in c['paths']]
def validate_adoption(root,c):
 raw=(root/OVERLAY_REL).read_bytes(); require(hashlib.sha256(raw).hexdigest()==OVERLAY_SHA256,'R5 overlay SHA drift')
 rows=list(csv.DictReader(io.StringIO(raw.decode()),delimiter='\t')); json_exact(rows,expected_overlay(c),'R5 overlay')
 require(len(rows)==25 and len({(r['repository'],r['path']) for r in rows})==25,'R5 overlay path count/duplicate drift')
 idx=read_json(root/INDEX_REL)['r3_meta_r5_instruction_efficiency_direct_adoption']
 expected={'candidate_path':CANDIDATE_REL.name,'candidate_sha256':CANDIDATE_SHA256,'adoption_overlay':OVERLAY_REL.name,'adoption_overlay_sha256':OVERLAY_SHA256,'source_commit':SOURCE,'source_tree':SOURCE_TREE,'subtree_tree':SUBTREE_TREE,'live_main_identity_commit':LIVE_MAIN,'path_count':25,'depth':'SCOPED_SEMANTIC_REVIEW','line_ranges':[],'canonical_ledger_sha256':LEDGER_SHA,'canonical_counts':{'source_rows':4325,'direct_paths':283,'grouped_paths':113,'unverified_paths':3929,'semantically_classified_paths':396},'meta_counts':{'direct_paths':70,'unverified_paths':104,'source_rows':174},'results_row_readopted':False,'meta_aud_05_status':'PARTIALLY_REPAIRED','product_readiness_claimed':False,'audit_completion_claimed':False,'runtime_attested':False}
 json_exact(idx,expected,'R5 adoption index')

def validate_accounting(root,c,inventory_dir=None):
 tmp=None
 if inventory_dir is None: tmp=tempfile.TemporaryDirectory(prefix='meta-r5-'); inventory_dir=collect_inventories(root,Path(tmp.name)/'audit')
 try: result=verify_report.validate(root/REPORT_REL,inventory_dir=inventory_dir); ledger,grouped=verify_report.rebuild_ledger(root/REPORT_REL,inventory_dir)
 finally:
  if tmp: tmp.cleanup()
 require(result.get('tree_and_ledger_verified') is True,'authoritative ledger not rebuilt')
 require(hashlib.sha256(ledger).hexdigest()==LEDGER_SHA,'canonical ledger SHA drift')
 expected={'source_leaves':4325,'scoped_review_paths':283,'grouped_revalidated_paths':113,'unverified_semantics':3929,'semantically_classified_paths':396}
 for k,v in expected.items(): require(type(result.get(k)) is int and result[k]==v,'canonical accounting drift: '+k)
 rows=list(csv.DictReader(io.StringIO(ledger.decode()))); wanted=set(EXPECTED_BLOBS)
 selected=[r for r in rows if r['repository_id']=='meta' and r['path'] in wanted]
 require(len(selected)==25 and {r['path'] for r in selected}==wanted,'candidate ledger path set drift')
 require(all(r['disposition']=='DIRECT' and r['depth']=='SCOPED_SEMANTIC_REVIEW' for r in selected),'R5 source path not exactly adopted DIRECT')
 require(all(r['scope']==next(x['semantic_note'] for x in c['paths'] if x['path']==r['path']) for r in selected),'R5 adopted scope drift')
 require(not any(r['disposition']=='GROUPED' for r in selected),'candidate GROUPED overlap')
 require(not any(r['path']=='docs/evidence/OTERYN-R5Q-RESULTS.md' for r in selected),'R5 Results row re-adopted')
 require(sum(grouped.values())==113,'GROUPED accounting drift')
 return result

def main():
 p=argparse.ArgumentParser(); p.add_argument('--audit-root',type=Path,default=ROOT); a=p.parse_args(); c=expected_candidate(a.audit_root); validate_candidate(c,c); validate_source(a.audit_root,c); validate_finding(a.audit_root); validate_adoption(a.audit_root,c); validate_accounting(a.audit_root,c)
 print(json.dumps({'result':'META_R5_INSTRUCTION_EFFICIENCY_DIRECT_ADOPTION_VALID_NOT_PRODUCT_PASS','candidate_paths':25,'coverage_delta':25,'coverage_adopted':True,'adoption_performed':True,'current_disposition':'DIRECT','eligible_adoption_depth':'SCOPED_SEMANTIC_REVIEW','source_rows':4325,'direct_paths':283,'grouped_paths':113,'unverified_paths':3929,'semantically_classified_paths':396,'ledger_sha256':LEDGER_SHA,'meta_aud_05_status':'PARTIALLY_REPAIRED','residual_obligations':14,'product_readiness_claimed':False,'audit_completion_claimed':False,'runtime_attested':False,'live_state_claimed':False},sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
