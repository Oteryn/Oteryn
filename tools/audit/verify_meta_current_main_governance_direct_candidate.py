#!/usr/bin/env python3
"""Verify the adopted R7 META current-main governance source review."""
from __future__ import annotations
import csv, hashlib, importlib.util, io, json, subprocess, tempfile
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[2]; E=ROOT/'docs/evidence/organization-audit-20260907'
CANDIDATE=E/'r7-meta-current-main-governance-direct-candidate.json'; OVERLAY=E/'coverage-review-meta-current-main-governance-direct-additions.tsv'
CANDIDATE_BLOB='6a3e98ad65f52015a43a84e39a8940f64b31dc65'; OVERLAY_SHA='8c9064552ea9592d7c5b51852333add3f58cdb4963f4316c2dd6bcbd21b44e16'; LEDGER_SHA='bf51139f97683659f752a54e643c1d342791476d64a0f78237b5c5d3ba3a310a'
R7_LEDGER_SHA='8520e472698d3592fcc95d5b093a631d9ae936256affcbf2d1418fa8b7448f94'
SOURCE='23b21e9b1b2d4b6c3a5cac3d4c7a18747804c090'; TREE='b8ebb8e50bce14a736fa65590ac121655c52fd12'; HIST='docs/evidence/repository-audit-2026-09-06/'
BASE_REVIEW_BLOB='9f24e951b7012d6bdbfafb19c8f2470c22a01467'
FIELDS=('repository','path','blob_sha','depth','scope','line_ranges','execution_evidence')
REFRESH_EXECUTION_EVIDENCE='BOUNDED_FULL_FILE_SOURCE_REVIEW_REFRESH; source semantics/exercised assertions only; no live provider, admin, runtime, operational-capability, readiness, or completion inference'
EXPECTED_R7_ADOPTION_INDEX={
 'state':'ADOPTED_BOUNDED_SOURCE_SEMANTICS_NOT_PRODUCT_PASS',
 'candidate':'r7-meta-current-main-governance-direct-candidate.json','candidate_git_blob':CANDIDATE_BLOB,
 'adoption_overlay':'coverage-review-meta-current-main-governance-direct-additions.tsv','adoption_overlay_sha256':OVERLAY_SHA,
 'source_commit':SOURCE,'source_tree':TREE,'path_count':14,'refreshed_existing_direct_paths':5,
 'depth':'SCOPED_SEMANTIC_REVIEW','line_ranges':[],'ledger_sha256':R7_LEDGER_SHA,
 'counts':{'source_leaves':4361,'direct':308,'grouped':113,'unverified':3940,'semantically_classified':421},
 'meta':{'leaves':210,'direct':95,'grouped':0,'unverified':115},
 'historical_packet_paths_remaining_unverified':26,'meta_aud_05':'P2_PARTIALLY_REPAIRED',
 'product_readiness_claimed':False,'organization_audit_completion_claimed':False,
 'live_operational_capability_claimed':False,
}
class CandidateError(ValueError): pass
def blob(raw:bytes)->str:return hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest()
def pairs(ps):
 d={}
 for k,v in ps:
  if k in d: raise CandidateError(f'duplicate JSON key: {k}')
  d[k]=v
 return d
def json_bytes(raw:bytes):
 try:d=json.loads(raw.decode('utf-8'),object_pairs_hook=pairs)
 except (UnicodeDecodeError,json.JSONDecodeError) as e:raise CandidateError(str(e)) from e
 if not isinstance(d,dict):raise CandidateError('JSON root must be object')
 return d
def tsv_bytes(raw:bytes):
 try:r=csv.DictReader(io.StringIO(raw.decode('utf-8')),delimiter='\t',strict=True)
 except UnicodeDecodeError as e:raise CandidateError('TSV UTF-8 drift') from e
 if tuple(r.fieldnames or ())!=FIELDS:raise CandidateError('TSV header drift')
 rows=list(r)
 if any(None in x or set(x)!=set(FIELDS) for x in rows):raise CandidateError('TSV row shape drift')
 return rows
def load_candidate():
 raw=CANDIDATE.read_bytes()
 if blob(raw)!=CANDIDATE_BLOB:raise CandidateError('immutable reviewed candidate blob drift')
 return json_bytes(raw)
def load_base_review_raw():
 raw=(E/'coverage-review.tsv').read_bytes()
 if blob(raw)!=BASE_REVIEW_BLOB:raise CandidateError('canonical coverage-review.tsv blob drift')
 return raw
def validate_base_review_unchanged(initial:bytes):
 current=(E/'coverage-review.tsv').read_bytes()
 if current!=initial or blob(current)!=BASE_REVIEW_BLOB:raise CandidateError('canonical coverage-review.tsv changed during verification')
def json_exact(actual,expected):
 return json.dumps(actual,sort_keys=True,separators=(',',':'))==json.dumps(expected,sort_keys=True,separators=(',',':'))
def validate_adoption_index(index):
 if not json_exact(index.get('r7_meta_current_main_governance_direct_adoption'),EXPECTED_R7_ADOPTION_INDEX):
  raise CandidateError('R7 adoption index drift')
def report_module(base_review_raw:bytes):
 p=ROOT/'tools/audit/verify_report.py'; spec=importlib.util.spec_from_file_location('r7_report',p);m=importlib.util.module_from_spec(spec);assert spec.loader;spec.loader.exec_module(m)
 canonical=E/'coverage-review.tsv'; frozen=tuple(tsv_bytes(base_review_raw)); read_tsv=m.read_tsv
 def frozen_read_tsv(path):
  if Path(path)==canonical:return [dict(row) for row in frozen]
  return read_tsv(path)
 m.read_tsv=frozen_read_tsv
 return m
def entries(doc):return [x for k in ('previous_direct_modified','previous_unverified_modified','new_active_governance') for x in doc['candidate'][k]]
def validate_rows(doc,base_raw=None):
 raw=OVERLAY.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=OVERLAY_SHA:raise CandidateError('R7 overlay SHA drift')
 rows=tsv_bytes(raw); expected=doc['candidate']['previous_unverified_modified']+doc['candidate']['new_active_governance']
 if len(rows)!=14 or [r['path'] for r in rows]!=[x['path'] for x in expected]:raise CandidateError('R7 overlay exact 14-row path set drift')
 scopes=doc['candidate']['semantic_scope']
 allowed=set(scopes.values())
 for r,x in zip(rows,expected):
  if r['repository']!='meta' or r['blob_sha']!=x['blob_sha'] or r['depth']!='SCOPED_SEMANTIC_REVIEW' or r['line_ranges']!='[]' or r['scope'] not in allowed:raise CandidateError(f'R7 overlay row drift: {x["path"]}')
  if not r['execution_evidence'] or any(word in r['execution_evidence'].casefold() for word in ('product readiness established','live operational capability proven')):raise CandidateError('R7 execution evidence overclaim')
 if base_raw is None:base_raw=load_base_review_raw()
 base=tsv_bytes(base_raw); refresh=doc['candidate']['previous_direct_modified']
 br={r['path']:r for r in base if r['repository']=='meta'}
 if set(x['path'] for x in refresh)&set(r['path'] for r in rows):raise CandidateError('refreshed DIRECT row duplicated in overlay')
 for x in refresh:
  r=br.get(x['path'])
  if not r or r['blob_sha']!=x['blob_sha'] or r['depth']!='SCOPED_SEMANTIC_REVIEW' or r['line_ranges']!='[]' or r['scope'] not in allowed or r['execution_evidence']!=REFRESH_EXECUTION_EVIDENCE:raise CandidateError(f'refreshed prior DIRECT row drift: {x["path"]}')
 return rows
def validate():
 doc=load_candidate()
 if doc['source']!={'repository':'Oteryn/Oteryn','commit_sha':SOURCE,'tree_sha':TREE}:raise CandidateError('candidate source drift')
 base_raw=load_base_review_raw()
 rows=validate_rows(doc,base_raw); vr=report_module(base_raw); report=ROOT/'docs/evidence/OTERYN-ORGANIZATION-COMPREHENSIVE-AUDIT-20260907.json'
 with tempfile.TemporaryDirectory() as td:
  out=Path(td)/'inv'; import contextlib
  spec=importlib.util.spec_from_file_location('r7_collect',ROOT/'tools/audit/organization_audit.py');co=importlib.util.module_from_spec(spec);assert spec.loader;spec.loader.exec_module(co)
  with contextlib.redirect_stdout(io.StringIO()):co.collect(json.loads((E/'collection-plan.json').read_text()),out,False)
  result=vr.validate(report,out/'inventories'); raw,groups=vr.rebuild_ledger(report,out/'inventories')
 if hashlib.sha256(raw).hexdigest()!=LEDGER_SHA:raise CandidateError('authoritative R7 ledger digest drift')
 expected=(4361,309,113,3939,422)
 got=(result['source_leaves'],result['scoped_review_paths'],result['grouped_revalidated_paths'],result['unverified_semantics'],result['semantically_classified_paths'])
 if got!=expected:raise CandidateError('R7 accounting drift')
 ledger=list(csv.DictReader(io.StringIO(raw.decode())))
 by={(r['repository_id'],r['path']):r for r in ledger}
 for x in entries(doc):
  r=by.get(('meta',x['path']))
  if not r or r['disposition']!='DIRECT' or r['object_sha']!=x['blob_sha']:raise CandidateError('R7 candidate disposition/blob drift')
 hist=[r for r in ledger if r['repository_id']=='meta' and r['path'].startswith(HIST)]
 if len(hist)!=26 or any(r['disposition']!='UNVERIFIED' for r in hist):raise CandidateError('historical packet leaves must remain exactly 26 UNVERIFIED')
 validate_adoption_index(json_bytes((E/'verification-index.json').read_bytes()))
 rep=json_bytes(report.read_bytes())
 if rep.get('audit_completion')!='NOT_ESTABLISHED; source inventory complete, semantic scope and independent acceptance remain partial' or rep.get('production_readiness_claimed') is not False:raise CandidateError('R7 completion/readiness drift')
 validate_base_review_unchanged(base_raw)
 return {'result':'META_CURRENT_MAIN_GOVERNANCE_DIRECT_ADOPTION_VALID_NOT_PRODUCT_PASS','source_leaves':4361,'direct':309,'grouped':113,'unverified':3939,'semantically_classified':422,'meta':{'leaves':210,'direct':96,'grouped':0,'unverified':114},'ledger_sha256':LEDGER_SHA,'refreshed_existing_direct':5,'newly_direct':14,'historical_packet_paths_unverified':26,'residual_obligations':14,'meta_aud_05':'P2_PARTIALLY_REPAIRED','product_readiness_claimed':False,'organization_audit_completion_claimed':False}
def main():
 try:print(json.dumps(validate(),sort_keys=True));return 0
 except (CandidateError,ValueError,OSError,subprocess.CalledProcessError) as e:print(json.dumps({'result':'INVALID','error':str(e)},sort_keys=True));return 1
if __name__=='__main__':raise SystemExit(main())
