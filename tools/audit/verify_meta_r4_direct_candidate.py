#!/usr/bin/env python3
"""Fail-closed verifier for the 25-path META R4-correlated DIRECT candidate."""
from __future__ import annotations
import argparse, contextlib, csv, hashlib, io, json, subprocess, tempfile
from pathlib import Path
import organization_audit
import verify_report

ROOT=Path(__file__).resolve().parents[2]
CANDIDATE_REL=Path('docs/evidence/organization-audit-20260907/r3-meta-r4-direct-candidate.json')
CANDIDATE_SHA256='aeb3eaf325aef8c989209d1c9104c8d7a890b25eef2b3bb1ea014ffd079aab39'
REPORT_REL=Path('docs/evidence/OTERYN-ORGANIZATION-COMPREHENSIVE-AUDIT-20260907.json')
PLAN_REL=Path('docs/evidence/organization-audit-20260907/collection-plan.json')
FINDINGS_REL=Path('docs/evidence/organization-audit-20260907/finding-register.tsv')
SOURCE='1a01c5b3e08666a82245b1cac78da3736c65e785'; SOURCE_TREE='f084e824ec5e14d5909c9750d906d91d51425fd5'
LEDGER_SHA='73c458b8e1b2a6a5cf02bedbefec8fe3a11d4f883413ef65f6d8dd56952338f9'
INVENTORY_IDS={'meta','game','platform','atlas','migration_archive'}


def require(value,message):
    if not value: raise ValueError(message)

def json_exact(actual,expected,path='root'):
    require(type(actual) is type(expected),f'{path} JSON type drift')
    if isinstance(expected,dict):
        require(list(actual)==list(expected),f'{path} key set/order drift')
        for k in expected: json_exact(actual[k],expected[k],f'{path}.{k}')
    elif isinstance(expected,list):
        require(len(actual)==len(expected),f'{path} list length drift')
        for i,(a,e) in enumerate(zip(actual,expected)): json_exact(a,e,f'{path}[{i}]')
    else: require(actual==expected,f'{path} value drift')

def read_json(path):
    def pairs(items):
        out={}
        for k,v in items: require(k not in out,'duplicate JSON key: '+k); out[k]=v
        return out
    return json.loads(path.read_text(encoding='utf-8'),object_pairs_hook=pairs)

def expected_candidate():
    raw=(ROOT/CANDIDATE_REL).read_bytes(); require(hashlib.sha256(raw).hexdigest()==CANDIDATE_SHA256,'candidate complete-file SHA drift')
    return read_json(ROOT/CANDIDATE_REL)

def validate_candidate(candidate, expected=None): json_exact(candidate,expected or expected_candidate())

def git(root,*args):
    return subprocess.run(['git','-c','core.hooksPath=/dev/null',*args],cwd=root,check=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60).stdout.strip()

def validate_source(root,candidate):
    require(git(root,'rev-parse',SOURCE+'^{tree}')==SOURCE_TREE,'source tree drift')
    observed={}
    for row in candidate['paths']:
        spec=f"{SOURCE}:{row['path']}"
        require(git(root,'cat-file','-t',spec)=='blob','source path is not a blob: '+row['path'])
        observed[row['path']]=git(root,'rev-parse',spec)
        # A complete direct read, not metadata alone.
        subprocess.run(['git','cat-file','blob',observed[row['path']]],cwd=root,check=True,stdout=subprocess.PIPE,timeout=60)
    require(observed=={r['path']:r['blob_sha'] for r in candidate['paths']},'source path/blob set drift')
    h=candidate['historical_r4_provenance']
    require(git(root,'rev-parse',h['audited_source_commit']+'^{tree}')==h['audited_source_tree'],'historical R4 audited source/tree drift')
    require(git(root,'rev-parse',h['publication_merge_commit']+':'+h['coverage_ledger_path'])==h['coverage_ledger_publication_blob'],'historical R4 ledger publication drift')
    require(git(root,'rev-parse',h['publication_merge_commit']+':'+h['closeout_path'])==h['closeout_publication_blob'],'historical R4 closeout publication drift')

def collect_inventories(root,output):
    plan=read_json(root/PLAN_REL); plan['snapshots']=[x for x in plan['snapshots'] if x['id'] in INVENTORY_IDS]
    require({x['id'] for x in plan['snapshots']}==INVENTORY_IDS,'inventory snapshot set drift')
    with contextlib.redirect_stdout(io.StringIO()): organization_audit.collect(plan,output)
    return output/'inventories'

def validate_finding(root,candidate):
    with (root/FINDINGS_REL).open(encoding='utf-8',newline='') as f: rows=list(csv.DictReader(f,delimiter='\t'))
    found=[r for r in rows if r['id']=='META-AUD-05']
    require(len(found)==1,'META-AUD-05 missing or duplicated')
    row=found[0]; c=candidate['reconfirmed_finding']
    require((row['priority'],row['state'],row['title'])==(c['severity'],c['status'],c['title']),'META-AUD-05 canonical state drift')

def validate_accounting(root,candidate,inventory_dir=None):
    temporary=None
    if inventory_dir is None:
        temporary=tempfile.TemporaryDirectory(prefix='oteryn-meta-r4-inventory-'); inventory_dir=collect_inventories(root,Path(temporary.name)/'audit')
    try:
        result=verify_report.validate(root/REPORT_REL,inventory_dir=inventory_dir)
        ledger,grouped=verify_report.rebuild_ledger(root/REPORT_REL,inventory_dir)
    finally:
        if temporary: temporary.cleanup()
    require(result.get('tree_and_ledger_verified') is True,'canonical ledger was not rebuilt')
    require(hashlib.sha256(ledger).hexdigest()==LEDGER_SHA,'canonical ledger SHA drift')
    expected={'source_leaves':4325,'scoped_review_paths':233,'grouped_revalidated_paths':113,'unverified_semantics':3979,'semantically_classified_paths':346}
    for k,v in expected.items(): require(type(result.get(k)) is int and result[k]==v,'canonical accounting drift: '+k)
    rows=list(csv.DictReader(io.StringIO(ledger.decode('utf-8'))))
    wanted={r['path'] for r in candidate['paths']}
    selected=[r for r in rows if r.get('repository_id')=='meta' and r.get('path') in wanted]
    require(len(selected)==25 and {r['path'] for r in selected}==wanted,'candidate ledger identity set drift')
    require(all(r.get('disposition')=='UNVERIFIED' for r in selected),'candidate path is not currently UNVERIFIED')
    require(sum(grouped.values())==113,'canonical GROUPED count drift')

def main():
    p=argparse.ArgumentParser(); p.add_argument('--audit-root',type=Path,default=ROOT); a=p.parse_args()
    raw=(a.audit_root/CANDIDATE_REL).read_bytes(); require(hashlib.sha256(raw).hexdigest()==CANDIDATE_SHA256,'candidate complete-file SHA drift'); candidate=read_json(a.audit_root/CANDIDATE_REL); validate_candidate(candidate); validate_source(a.audit_root,candidate); validate_finding(a.audit_root,candidate); validate_accounting(a.audit_root,candidate)
    print(json.dumps({'result':'META_R4_DIRECT_CANDIDATE_VALID_NOT_ADOPTED','candidate_paths':25,'coverage_adopted':False,'current_disposition':'UNVERIFIED','source_rows':4325,'direct_paths':233,'grouped_paths':113,'unverified_paths':3979,'semantically_classified_paths':346,'ledger_sha256':LEDGER_SHA,'meta_aud_05_status':'PARTIALLY_REPAIRED','product_readiness_claimed':False,'audit_completion_claimed':False,'live_state_claimed':False},sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
