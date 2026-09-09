#!/usr/bin/env python3
"""Validate this audit's accounting, not the truth of arbitrary source assertions.

No network or repository writes. Optional immutable inventories reconstruct the
Git trees and reproduce the complete per-leaf CSV. DIRECT, GROUPED and
UNVERIFIED are distinct dispositions; GROUPED is accepted only through an
explicit fail-closed evidence rule. A successful result never becomes
product/audit-semantic PASS.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import os
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
DIRECT_ADDITIONS = 'coverage-review-canonical-additions.tsv'
DIRECT_ADDITIONS_BINDING = 'organization-audit-20260907/coverage-review-canonical-additions.tsv'
RECORDER_ADDITIONS_BINDING = 'organization-audit-20260907/coverage-review-additions.tsv'
ANNOUNCEMENTS_ADDITIONS_BINDING = 'organization-audit-20260907/coverage-review-announcements-additions.tsv'


def write_new_file_no_symlinks(path: Path, raw: bytes) -> None:
    """Create one file exclusively without following its final or ancestor symlinks."""
    absolute=Path(os.path.abspath(path));parent=absolute.parent
    flags=os.O_RDONLY|os.O_DIRECTORY
    if hasattr(os,'O_NOFOLLOW'): flags|=os.O_NOFOLLOW
    descriptor=os.open(parent.anchor,flags)
    try:
        for part in parent.parts[1:]:
            try: child=os.open(part,flags,dir_fd=descriptor)
            except OSError as exc: raise ValueError('ledger output ancestry must contain only directories, not symlinks') from exc
            os.close(descriptor);descriptor=child
        file_flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL
        if hasattr(os,'O_NOFOLLOW'): file_flags|=os.O_NOFOLLOW
        try: output=os.open(absolute.name,file_flags,0o666,dir_fd=descriptor)
        except OSError as exc: raise ValueError('refusing ledger overwrite or symlink') from exc
        try:
            with os.fdopen(output,'wb') as handle:
                handle.write(raw)
        except Exception:
            try: os.unlink(absolute.name,dir_fd=descriptor)
            except OSError: pass
            raise
    finally: os.close(descriptor)
SEMANTIC_COVERAGE_UNKNOWN = {
    'id': 'SEMANTIC-COVERAGE',
    'missing': '3979 source leaves retain UNVERIFIED semantics; 346 of 4325 leaves are semantically classified',
    'reason': 'Source bytes are available; 233 DIRECT scoped path reviews are bound (the prior 221 plus two app/Audit recorder paths plus ten app/Announcements/** paths), and 113 bounded GROUPED Platform paths are bound (27 GameAuth + 31 Accounts/CanaryIntegration/CharacterProfiles/Characters + 49 Marketplace/Payments/Wallet + 6 Marketplace tests). The ten Announcements DIRECT paths are frozen-source bounded reviews qualified by real MariaDB 11.8.9 with 4 cases / 20 assertions and a mechanical projection proving exactly those ten rows transition UNVERIFIED to DIRECT; the Polish editorial_translations join branch and a dedicated simultaneous-writer race remain explicit execution limits. This is bounded semantic accounting, not full behavior, product, or audit approval; 3979 paths retain UNVERIFIED. The rejected Atlas 508-path candidate remains UNVERIFIED, and no automatic import from maintenance N/A or unproven summaries is allowed.',
    'effect': 'Original exhaustive completeness cannot be claimed from 346 semantically classified leaves out of 4325.',
    'owner_route': 'META186 plus provider audit owners',
    'closure_condition': 'Import exact historical disposition ledgers with bounded validity, review changed/uncovered authored families, and retain justified grouping/N/A.',
}
INDEPENDENT_REVIEW_UNKNOWN = {
    'id': 'INDEPENDENT-REVIEW',
    'missing': 'Independent review lifecycle/outcome for the adopted Platform audit-recorder and Announcements DIRECT slices',
    'reason': 'Independent review and cleanup are complete for the 49-path Marketplace/Payments/Wallet GROUPED expansion and the six-file Marketplace-test GROUPED batch. The current stable audit lineage additionally adopts two app/Audit recorder paths and ten app/Announcements/** paths as bounded DIRECT reviews. Their independent-review lifecycle and outcome are external mutable PR #185 metadata and are not self-certified by this evidence object.',
    'effect': 'No whole-audit or product-readiness conclusion and no self-awarded independent 10/10 are claimed from these twelve post-Marketplace DIRECT paths.',
    'owner_route': 'PR185 reviewer',
    'closure_condition': 'PR #185 review metadata records the independent exact-head disposition for the recorder and Announcements DIRECT slices; this evidence object remains a durable pre-review snapshot and does not itself close unrelated product/operations obligations.',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def json_exact(left, right):
    """Compare JSON values recursively without Python's bool/int equivalence."""
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(json_exact(left[key], right[key]) for key in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(json_exact(a, b) for a, b in zip(left, right))
    return left == right


def read_json(path):
    def pairs(items):
        result={}
        for key,value in items:
            require(key not in result,'duplicate JSON key')
            result[key]=value
        return result
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=pairs)


def read_tsv(path):
    require(path.is_file(), 'missing TSV: '+path.name)
    with path.open(encoding='utf-8', newline='') as handle:
        reader=csv.DictReader(handle, delimiter='\t')
        require(reader.fieldnames and len(reader.fieldnames)==len(set(reader.fieldnames)), 'duplicate/absent TSV header')
        rows=list(reader)
    require(rows and all(None not in row and None not in row.values() for row in rows), 'invalid TSV: '+path.name)
    return rows


def unique(rows, key, label):
    values=[key(row) for row in rows]
    require(len(values)==len(set(values)), 'duplicate '+label)


def load_review(base: Path, doc: dict):
    review=read_tsv(base/'coverage-review.tsv')
    additions_binding=doc.get('coverage_review_additions')
    if additions_binding is not None:
        require(additions_binding==DIRECT_ADDITIONS_BINDING,'coverage review additions binding drift')
        additions=read_tsv(base/DIRECT_ADDITIONS)
        require(additions,'coverage review additions empty')
        review=review+additions
    unique(review,lambda r:(r['repository'],r['path']),'review path')
    return review


def safe_relative(path):
    parts=path.split('/')
    return bool(parts) and not path.startswith('/') and '\\' not in path and all(p not in {'','.', '..'} for p in parts)


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
        for name,value in sorted(node.items(),key=lambda kv:(kv[0]+('/' if isinstance(kv[1],dict) else '')).encode('utf-8')):
            mode,oid=('40000',digest(value)) if isinstance(value,dict) else value
            data.extend(mode.encode()+b' '+name.encode('utf-8')+b'\0'+bytes.fromhex(oid))
        return hashlib.sha1(b'tree '+str(len(data)).encode()+b'\0'+data).hexdigest()
    return digest(root)


def load_groups(base, repo):
    doc=read_json(base/'coverage-groups.json')
    require(type(doc.get('schema_version')) is int and doc['schema_version']==1,'coverage group schema')
    groups=doc.get('groups')
    require(isinstance(groups,list),'coverage groups missing')
    rejected=doc.get('rejected_candidates',[])
    require(isinstance(rejected,list),'rejected coverage candidates invalid')
    unique(groups+rejected,lambda row:row.get('id'),'coverage group/candidate id')
    for row in rejected:
        require(row.get('repository') in repo,'rejected coverage repository')
        require(row.get('disposition')=='REVALIDATION_FAILED_NOT_ADOPTED','rejected coverage disposition')
        require(type(row.get('expected_count')) is int and row['expected_count']>0,'rejected coverage count')
        evaluation=row.get('evaluation') or {}
        require(evaluation.get('outcome')=='REJECTED_NOT_COUNTED_AS_GROUPED','rejected coverage outcome')
        require(type(evaluation.get('qualification_run')) is int and type(evaluation.get('qualification_job')) is int,'rejected coverage execution identity')
        tests=evaluation.get('focused_current_consumer_tests') or {}
        require(type(tests.get('passed')) is int and type(tests.get('failed')) is int and tests.get('failed',0)>0,'rejected coverage failure evidence')
    prefixes=[]
    for row in groups:
        require(row.get('repository') in repo,'coverage group repository')
        require(row.get('disposition')=='GROUPED','coverage group disposition')
        prefix=row.get('path_prefix')
        require(isinstance(prefix,str) and prefix.endswith('/') and safe_relative(prefix[:-1]) and '*' not in prefix,'unsafe coverage group prefix')
        require(type(row.get('expected_count')) is int and row['expected_count']>0,'coverage group count')
        require(row.get('depth')=='GROUPED_REVALIDATED','coverage group depth')
        require(isinstance(row.get('scope'),str) and row['scope'].strip(),'coverage group scope')
        require(isinstance(row.get('limitations'),str) and row['limitations'].strip(),'coverage group limitations')
        hist=row.get('historical_evidence') or {}
        require(hist.get('repository')==repo[row['repository']]['repository'],'coverage historical repository')
        for key in ['publication_commit','coverage_rules_blob','audited_main_sha','audited_main_tree']:
            require(isinstance(hist.get(key),str) and SHA.fullmatch(hist[key]),'coverage historical identity')
        require(hist.get('pattern')==prefix+'**' and hist.get('count')==row['expected_count'],'coverage historical rule mismatch')
        require(isinstance(hist.get('coverage_rules_path'),str) and safe_relative(hist['coverage_rules_path']),'coverage historical path')
        require(isinstance(hist.get('basis'),str) and hist['basis'].strip(),'coverage historical basis')
        current=row.get('current_revalidation') or {}
        source=repo[row['repository']]
        require(current.get('source_commit')==source['commit_sha'] and current.get('source_tree')==source['tree_sha'],'coverage current source mismatch')
        require(current.get('changed_paths_under_group_prefix')==0,'coverage group changed-path carry-forward forbidden')
        require(current.get('historical_to_current_compare_status') in {'ahead','identical'},'coverage compare state')
        blobs=current.get('current_blobs')
        require(isinstance(blobs,dict) and blobs,'coverage current blobs missing')
        for path,oid in blobs.items():
            require(safe_relative(path) and isinstance(oid,str) and SHA.fullmatch(oid),'coverage current blob binding')
        checks=current.get('required_checks')
        require(isinstance(checks,list) and checks and all(isinstance(x,str) and x.strip() for x in checks),'coverage required checks')
        for other_repo,other_prefix in prefixes:
            if other_repo==row['repository']:
                require(not (prefix.startswith(other_prefix) or other_prefix.startswith(prefix)),'overlapping coverage group prefixes')
        prefixes.append((row['repository'],prefix))
    return groups


def build_ledger(doc, review, groups, inventory_dir):
    repo=doc['repositories']
    data=[]
    mapping={(r['repository'],r['path']):r for r in review}
    grouped_counts={key:0 for key in repo}
    for key in sorted(repo):
        inv=read_json(inventory_dir/(key+'.json'));r=repo[key]
        require(inv['commit_sha']==r['commit_sha'] and inv['tree_sha']==r['tree_sha'],'inventory coordinate mismatch')
        require(len(inv['entries'])==r['leaf_count'] and tree_sha(inv['entries'])==r['tree_sha'],'inventory tree/count mismatch')
        paths={x['path'] for x in inv['entries']}
        require(all(path in paths for rep,path in mapping if rep==key),'review path absent')
        grouped={}
        for group in [g for g in groups if g['repository']==key]:
            matched=[x for x in inv['entries'] if x['path'].startswith(group['path_prefix'])]
            require(len(matched)==group['expected_count'],'coverage group inventory count mismatch')
            for x in matched:
                require(x['mode']=='100644','coverage group contains non-regular leaf')
                require((key,x['path']) not in mapping,'DIRECT/GROUPED overlap')
                require(x['path'] not in grouped,'GROUPED/GROUPED overlap')
                grouped[x['path']]=group
            grouped_counts[key]+=len(matched)
        for x in sorted(inv['entries'],key=lambda x:x['path'].encode('utf-8')):
            reviewed=mapping.get((key,x['path']))
            require(reviewed is None or reviewed['blob_sha']==x['object_sha'],'review blob mismatch')
            group=grouped.get(x['path'])
            if reviewed:
                disposition='DIRECT';depth=reviewed['depth'];scope=reviewed['scope']
            elif group:
                disposition='GROUPED';depth=group['depth'];scope=group['scope']
            else:
                disposition='UNVERIFIED';depth='IDENTITY_ONLY';scope=DEFAULT_REASON
            data.append({'repository_id':key,'commit_sha':r['commit_sha'],'tree_sha':r['tree_sha'],'path':x['path'],'mode':x['mode'],'object_sha':x['object_sha'],'disposition':disposition,'depth':depth,'scope':scope})
    buf=io.StringIO(newline='');w=csv.DictWriter(buf,fieldnames=list(data[0]),lineterminator='\n');w.writeheader();w.writerows(data)
    return buf.getvalue().encode('utf-8'),grouped_counts


def rebuild_ledger(report_path: Path, inventory_dir: Path):
    doc=read_json(report_path)
    repo=doc['repositories']
    require(set(repo)=={'meta','game','platform','atlas','migration_archive'},'repository scope')
    base=report_path.parent/doc['evidence_directory']
    review=load_review(base,doc)
    groups=load_groups(base,repo)
    for row in review:
        for group in groups:
            require(not (row['repository']==group['repository'] and row['path'].startswith(group['path_prefix'])),'DIRECT/GROUPED overlap')
    return build_ledger(doc,review,groups,inventory_dir)


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
    require(doc.get('coverage_review_additions')==DIRECT_ADDITIONS_BINDING,'canonical direct additions binding drift')
    require(doc.get('coverage_review_recorder_additions')==RECORDER_ADDITIONS_BINDING,'recorder additions evidence binding drift')
    require(doc.get('coverage_review_announcements_additions')==ANNOUNCEMENTS_ADDITIONS_BINDING,'Announcements additions evidence binding drift')
    base=report_path.parent/doc['evidence_directory']
    findings=read_tsv(base/'finding-register.tsv');unique(findings,lambda r:r['id'],'finding id')
    require(len(findings)==doc['reconciled_register_rows'],'finding count mismatch')
    for row in findings:
        require(row['state'] in STATES,'unknown finding state')
        require(row['repository'] in repo,'unknown finding repository')
        require(row['priority'] in {'P0','P1','P2','P3','NOTE','UNRATED'},'invalid priority')
        require(all(row[k].strip() for k in ['title','evidence','owner_route','closure_condition']),'missing finding evidence/closure')
    p1=[r['id'] for r in findings if r['priority']=='P1' and r['scope']=='source_snapshot' and r['state'] in {'CONFIRMED_SOURCE','REPRODUCED'}]
    require(p1==doc['known_source_snapshot_p1_ids'] and len(p1)==doc['known_source_snapshot_p1_count'],'source-snapshot P1 mismatch')
    domains=read_tsv(base/'domain-matrix.tsv');unique(domains,lambda r:r['domain'],'domain')
    require({r['domain'] for r in domains}==set('ABCDEFGHIJKLMNOPQRSTUVW'),'A-W matrix incomplete')
    require(len(domains)==doc['audit_domains_accounted'],'domain count')
    require(all(all(r[k].strip() for k in ['acceptance_criterion','method_and_evidence','opinion','remaining_limit','references']) for r in domains),'empty domain evidence')
    unknowns=read_json(base/'unknowns.json')['items'];unique(unknowns,lambda r:r['id'],'unknown id')
    require(len(unknowns)==doc['unresolved_unknowns'],'unknown count')
    semantic_coverage=[row for row in unknowns if row.get('id')=='SEMANTIC-COVERAGE']
    require(len(semantic_coverage)==1,'semantic-coverage unknown missing')
    require(json_exact(semantic_coverage[0],SEMANTIC_COVERAGE_UNKNOWN),'semantic-coverage unknown drift')
    independent=[row for row in unknowns if row.get('id')=='INDEPENDENT-REVIEW']
    require(len(independent)==1,'independent-review unknown missing')
    require(json_exact(independent[0],INDEPENDENT_REVIEW_UNKNOWN),'independent-review unknown drift')
    review=load_review(base,doc)
    for row in review:
        require(row['repository'] in repo and SHA.fullmatch(row['blob_sha']),'invalid review source')
        require(row['depth']=='SCOPED_SEMANTIC_REVIEW' and row['scope'].strip(),'unsupported review depth')
        ranges=json.loads(row['line_ranges'])
        require(isinstance(ranges,list) and all(isinstance(x,list) and len(x)==2 and all(type(n)is int for n in x) and 1<=x[0]<=x[1] for x in ranges),'invalid source range')
    require(doc['scoped_review_paths']==len(review),'report scoped review count mismatch')
    groups=load_groups(base,repo)
    grouped_total=sum(g['expected_count'] for g in groups)
    require(doc.get('grouped_revalidated_paths')==grouped_total,'report grouped coverage count mismatch')
    require(doc.get('semantically_classified_paths')==len(review)+grouped_total,'report semantic classification count mismatch')
    for row in review:
        require(not any(row['repository']==g['repository'] and row['path'].startswith(g['path_prefix']) for g in groups),'DIRECT/GROUPED overlap')
    coverage=read_json(base/'coverage-summary.json')
    require(coverage['semantic_completion_claimed'] is False,'unsupported semantic completion')
    require(coverage['source_leaf_total']==sum(r['leaf_count'] for r in repo.values()),'leaf total mismatch')
    require(coverage.get('scoped_review_paths')==len(review),'coverage direct count mismatch')
    require(coverage.get('grouped_revalidated_paths')==grouped_total,'coverage grouped count mismatch')
    require(coverage.get('semantically_classified_paths')==len(review)+grouped_total,'coverage semantic count mismatch')
    for key,r in repo.items():
        c=coverage['per_repository'][key]
        direct=sum(row['repository']==key for row in review)
        grouped=sum(g['expected_count'] for g in groups if g['repository']==key)
        require(c['leaves']==r['leaf_count'] and c['direct_scoped']==direct and c['grouped']==grouped,'review/group count mismatch')
        require(c['not_applicable']==0,'unexpected N/A reclassification')
        require(c['unverified_semantics']==c['leaves']-direct-grouped,'hidden coverage reclassification')
    require(coverage.get('unverified_semantics_total')==sum(c['unverified_semantics'] for c in coverage['per_repository'].values()),'unverified total mismatch')
    workflows=read_tsv(base/'workflow-inventory.tsv');unique(workflows,lambda r:(r['repository'],r['path']),'workflow')
    require(len(workflows)==doc['workflow_census']['total_workflows'],'workflow count')
    require(sum(int(r['job_count']) for r in workflows)==doc['workflow_census']['total_declared_jobs'],'job count')
    for key in ['meta','game','platform','atlas']:
        subset=[r for r in workflows if r['repository']==key];c=doc['workflow_census'][key]
        require(len(subset)==c['workflows'] and sum(int(r['job_count']) for r in subset)==c['jobs'],'repository workflow/job count')
    proof=read_json(base/'verification-index.json')
    require(proof['routing_product_verdict']=='FAIL_FOR_TWO_CASES' and proof['routing_false_negatives']==2,'reproduction misrepresented as product PASS')
    for c in proof['results']:
        require(c['source_commit'] in {r['commit_sha'] for r in repo.values()},'unbound execution source')
        require(type(c['exit_code']) is int and len(c['log_sha256'])==64,'invalid check record')
    if inventory_dir is not None:
        raw,grouped_counts=build_ledger(doc,review,groups,inventory_dir)
        require(grouped_counts=={key:coverage['per_repository'][key]['grouped'] for key in repo},'inventory grouped count mismatch')
        expected=coverage.get('ledger_sha256')
        require(isinstance(expected,str) and re.fullmatch(r'[0-9a-f]{64}',expected),'ledger digest not finalized')
        require(hashlib.sha256(raw).hexdigest()==expected,'ledger digest mismatch')
        if ledger_output is not None:
            write_new_file_no_symlinks(ledger_output,raw)
    elif ledger_output is not None:
        raise ValueError('inventories required for ledger output')
    return {'result':'ACCOUNTING_VALID_NOT_SEMANTIC_PASS','findings':len(findings),'domains':len(domains),'source_leaves':coverage['source_leaf_total'],'source_snapshot_p1':len(p1),'scoped_review_paths':len(review),'grouped_revalidated_paths':grouped_total,'semantically_classified_paths':len(review)+grouped_total,'unverified_semantics':coverage['unverified_semantics_total'],'tree_and_ledger_verified':inventory_dir is not None,'semantic_coverage':doc['semantic_coverage']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--inventory-dir',type=Path)
    parser.add_argument('--ledger-output',type=Path)
    parser.add_argument('--rebuild-ledger-digest',action='store_true')
    args=parser.parse_args()
    if args.rebuild_ledger_digest:
        require(args.inventory_dir is not None,'inventories required for ledger rebuild')
        raw,counts=rebuild_ledger(args.report,args.inventory_dir)
        print(json.dumps({'result':'LEDGER_REBUILD_NOT_AUDIT_PASS','sha256':hashlib.sha256(raw).hexdigest(),'rows':sum(read_json(args.inventory_dir/(key+'.json'))['entries'].__len__() for key in ['meta','game','platform','atlas','migration_archive']),'grouped_by_repository':counts},indent=2))
        return
    print(json.dumps(validate(args.report,args.inventory_dir,args.ledger_output),indent=2))

if __name__=='__main__':main()
