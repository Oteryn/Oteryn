#!/usr/bin/env python3
"""Validate this audit's accounting, not the truth of arbitrary source assertions.

No network or repository writes. Optional immutable inventories reconstruct the
Git trees and reproduce the complete per-leaf CSV; all unmatched leaves remain
UNVERIFIED. A successful result never becomes product/audit-semantic PASS.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re

SHA = re.compile(r'[0-9a-f]{40}\Z')
STATES = {'SOURCE_REPAIRED_TESTED','PARTIALLY_REPAIRED','RETIRED_SOURCE','SOURCE_REPAIRED',
          'UNKNOWN_LIVE','REQUIRES_REVALIDATION','REQUIRES_LIVE_REVALIDATION',
          'SOURCE_REPAIRED_RECORDED_CI','OPEN_QUALIFICATION','HISTORICAL_NOTE','CONFIRMED_SOURCE',
          'OPEN_INHERITED','REPRODUCED','UNVERIFIED_HYPOTHESIS','REGRESSION_VERIFIED',
          'REPORTED_CLOSED','LIVE_RECORD_RECONCILED','REPORTED_IMPLEMENTED_NOT_REQUALIFIED',
          'REPORTED_OPEN','OWNER_DECISION_PENDING','HISTORICAL_TERMINAL','REPORTED_OPEN_CANDIDATE'}
DEFAULT_REASON = 'Identity enumerated; this continuation does not assert a complete semantic review of this leaf. Historical/source oracles may provide narrower evidence in the finding register.'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    def pairs(items):
        result={}
        for key,value in items:
            require(key not in result,'duplicate JSON key')
            result[key]=value
        return result
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=pairs)


def read_tsv(path):
    with path.open(encoding='utf-8', newline='') as handle:
        reader=csv.DictReader(handle, delimiter='\t')
        require(reader.fieldnames and len(reader.fieldnames)==len(set(reader.fieldnames)), 'duplicate/absent TSV header')
        rows=list(reader)
    require(rows and all(None not in row and None not in row.values() for row in rows), 'invalid TSV: '+path.name)
    return rows


def unique(rows, key, label):
    values = [key(row) for row in rows]
    require(len(values)==len(set(values)), 'duplicate '+label)


def tree_sha(entries):
    root={}
    for row in entries:
        parts=row['path'].split('/')
        require(parts and all(p not in {'','.', '..'} for p in parts), 'unsafe path')
        require(SHA.fullmatch(row['object_sha']) is not None, 'invalid object SHA')
        require(row['mode'] in {'100644','100755','120000','160000'}, 'unsupported mode')
        node=root
        for part in parts[:-1]:
            node=node.setdefault(part,{})
            require(isinstance(node,dict), 'file/directory conflict')
        require(parts[-1] not in node,'duplicate inventory path')
        node[parts[-1]]=(row['mode'],row['object_sha'])
    def digest(node):
        data=bytearray()
        for name, value in sorted(node.items(),key=lambda kv:(kv[0]+('/' if isinstance(kv[1],dict) else '')).encode('utf-8')):
            mode,oid=('40000',digest(value)) if isinstance(value,dict) else value
            data.extend(mode.encode()+b' '+name.encode('utf-8')+b'\0'+bytes.fromhex(oid))
        return hashlib.sha1(b'tree '+str(len(data)).encode()+b'\0'+data).hexdigest()
    return digest(root)


def validate(report_path: Path, inventory_dir: Path|None=None, ledger_output: Path|None=None):
    doc=read_json(report_path)
    require(type(doc.get('schema_version')) is int and doc['schema_version']==2,'schema_version')
    require(doc['production_readiness_claimed'] is False,'production claim forbidden')
    require(doc['independent_score'] is None,'independent score not established')
    require(doc['severity_counts_exhaustive'] is False,'exhaustive severity claim unsupported')
    require(doc['status']=='QUALIFIED_AUDIT_WITH_EXPLICIT_OPEN_SCOPE','unsupported completion status')
    repo=doc['repositories']
    require(set(repo)=={'meta','game','platform','atlas','migration_archive'},'repository scope')
    for v in repo.values():
        require(SHA.fullmatch(v['commit_sha']) and SHA.fullmatch(v['tree_sha']),'invalid source identity')
        require(type(v['leaf_count']) is int and v['leaf_count']>0,'invalid leaf count')
    require(doc['evidence_directory']=='organization-audit-20260907','invalid evidence directory')
    base=report_path.parent/doc['evidence_directory']
    findings=read_tsv(base/'finding-register.tsv'); unique(findings,lambda r:r['id'],'finding id')
    require(len(findings)==doc['reconciled_register_rows'],'finding count mismatch')
    for row in findings:
        require(row['state'] in STATES,'unknown finding state')
        require(row['repository'] in repo,'unknown finding repository')
        require(row['priority'] in {'P0','P1','P2','P3','NOTE','UNRATED'},'invalid priority')
        require(all(row[k].strip() for k in ['title','evidence','owner_route','closure_condition']),'missing finding evidence/closure')
    p1=[r['id']for r in findings if r['priority']=='P1'and r['scope']=='current_main'and r['state']in {'CONFIRMED_SOURCE','REPRODUCED'}]
    require(p1==doc['known_current_main_p1_ids'] and len(p1)==doc['known_current_main_p1_count'],'current-main P1 mismatch')
    domains=read_tsv(base/'domain-matrix.tsv');unique(domains,lambda r:r['domain'],'domain')
    require({r['domain']for r in domains}==set('ABCDEFGHIJKLMNOPQRSTUVW'),'A-W matrix incomplete')
    require(len(domains)==doc['audit_domains_accounted'],'domain count')
    require(all(all(r[k].strip() for k in ['acceptance_criterion','method_and_evidence','opinion','remaining_limit','references']) for r in domains),'empty domain evidence')
    unknowns=read_json(base/'unknowns.json')['items'];unique(unknowns,lambda r:r['id'],'unknown id')
    require(len(unknowns)==doc['unresolved_unknowns'],'unknown count')
    review=read_tsv(base/'coverage-review.tsv');unique(review,lambda r:(r['repository'],r['path']),'review path')
    for row in review:
        require(row['repository']in repo and SHA.fullmatch(row['blob_sha']),'invalid review source')
        require(row['depth']=='SCOPED_SEMANTIC_REVIEW' and row['scope'].strip(),'unsupported review depth')
        ranges=json.loads(row['line_ranges'])
        require(isinstance(ranges,list) and all(isinstance(x,list)and len(x)==2 and all(type(n)is int for n in x)and 1<=x[0]<=x[1] for x in ranges),'invalid source range')
    coverage=read_json(base/'coverage-summary.json')
    require(coverage['semantic_completion_claimed'] is False,'unsupported semantic completion')
    require(coverage['source_leaf_total']==sum(r['leaf_count']for r in repo.values()),'leaf total mismatch')
    for key,r in repo.items():
        c=coverage['per_repository'][key]
        n=sum(row['repository']==key for row in review)
        require(c['leaves']==r['leaf_count'] and c['direct_scoped']==n,'review count mismatch')
        require(c['unverified_semantics']==c['leaves']-n and c['grouped']==0 and c['not_applicable']==0,'hidden coverage reclassification')
    workflows=read_tsv(base/'workflow-inventory.tsv');unique(workflows,lambda r:(r['repository'],r['path']),'workflow')
    require(len(workflows)==doc['workflow_census']['total_workflows'],'workflow count')
    require(sum(int(r['job_count'])for r in workflows)==doc['workflow_census']['total_declared_jobs'],'job count')
    for key in ['meta','game','platform','atlas']:
        subset=[r for r in workflows if r['repository']==key];c=doc['workflow_census'][key]
        require(len(subset)==c['workflows']and sum(int(r['job_count'])for r in subset)==c['jobs'],'repository workflow/job count')
    proof=read_json(base/'verification-index.json')
    require(proof['routing_product_verdict']=='FAIL_FOR_TWO_CASES' and proof['routing_false_negatives']==2,'reproduction misrepresented as product PASS')
    for c in proof['results']:
        require(c['source_commit'] in {r['commit_sha']for r in repo.values()},'unbound execution source')
        require(type(c['exit_code'])is int and len(c['log_sha256'])==64,'invalid check record')
    if inventory_dir is not None:
        data=[]; mapping={(r['repository'],r['path']):r for r in review}
        for key in sorted(repo):
            inv=read_json(inventory_dir/(key+'.json'));r=repo[key]
            require(inv['commit_sha']==r['commit_sha']and inv['tree_sha']==r['tree_sha'],'inventory coordinate mismatch')
            require(len(inv['entries'])==r['leaf_count']and tree_sha(inv['entries'])==r['tree_sha'],'inventory tree/count mismatch')
            paths={x['path']for x in inv['entries']}
            require(all(path in paths for rep,path in mapping if rep==key),'review path absent')
            for x in sorted(inv['entries'],key=lambda x:x['path'].encode('utf-8')):
                reviewed=mapping.get((key,x['path']))
                require(reviewed is None or reviewed['blob_sha']==x['object_sha'],'review blob mismatch')
                data.append({'repository_id':key,'commit_sha':r['commit_sha'],'tree_sha':r['tree_sha'],'path':x['path'],'mode':x['mode'],'object_sha':x['object_sha'],'disposition':'DIRECT'if reviewed else'UNVERIFIED','depth':reviewed['depth']if reviewed else'IDENTITY_ONLY','scope':reviewed['scope']if reviewed else DEFAULT_REASON})
        buf=io.StringIO(newline='');w=csv.DictWriter(buf,fieldnames=list(data[0]),lineterminator='\n');w.writeheader();w.writerows(data)
        raw=buf.getvalue().encode('utf-8')
        require(hashlib.sha256(raw).hexdigest()==coverage['ledger_sha256'],'ledger digest mismatch')
        if ledger_output is not None:
            require(not ledger_output.exists(),'refusing ledger overwrite');ledger_output.write_bytes(raw)
    elif ledger_output is not None:
        raise ValueError('inventories required for ledger output')
    return {'result':'ACCOUNTING_VALID_NOT_SEMANTIC_PASS','findings':len(findings),'domains':len(domains),'source_leaves':coverage['source_leaf_total'],'current_main_p1':len(p1),'scoped_review_paths':len(review),'tree_and_ledger_verified':inventory_dir is not None,'semantic_coverage':doc['semantic_coverage']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--inventory-dir',type=Path)
    parser.add_argument('--ledger-output',type=Path)
    args=parser.parse_args()
    print(json.dumps(validate(args.report,args.inventory_dir,args.ledger_output),indent=2))

if __name__=='__main__':main()
