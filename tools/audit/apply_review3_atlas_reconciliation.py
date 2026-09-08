#!/usr/bin/env python3
"""One-shot branch reconciliation for PR #185. Temporary; no network/provider writes."""
from pathlib import Path
import csv
import io
import json

ROOT=Path(__file__).resolve().parents[2]
EV=ROOT/'docs/evidence/organization-audit-20260907'


def require(ok,message):
    if not ok:
        raise SystemExit(message)


def replace_once(path:Path,old:str,new:str,label:str):
    text=path.read_text(encoding='utf-8')
    require(text.count(old)==1,f'{label}: expected one exact replacement, found {text.count(old)}')
    path.write_text(text.replace(old,new),encoding='utf-8')


def main():
    coverage=EV/'coverage-review.tsv'
    text=coverage.read_text(encoding='utf-8')
    old='PLATFORM-H02 (restricted owner evidence)'
    new='PLATFORM-H02 (mechanism publicly disclosed; details intentionally not repeated)'
    require(text.count(old)==9,f'expected exactly 9 stale PLATFORM-H02 labels, found {text.count(old)}')
    coverage.write_text(text.replace(old,new),encoding='utf-8')

    p=ROOT/'tools/audit/verify_r3_evidence.py'
    replace_once(p,"""def require_committed_results(summary, raw):
    committed = json_bytes(raw)
    require(summary == committed, 'recount differs from committed r3-native-results.json')
    return committed
""","""def strict_json_equal(left, right):
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(strict_json_equal(left[key], right[key]) for key in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(strict_json_equal(a, b) for a, b in zip(left, right))
    return left == right


def require_committed_results(summary, raw):
    committed = json_bytes(raw)
    require(strict_json_equal(summary, committed), 'recount differs from committed r3-native-results.json')
    return committed
""",'strict native JSON equality')

    p=ROOT/'tools/audit/test_verify_r3_evidence.py'
    text=p.read_text(encoding='utf-8')
    marker="\n\nif __name__ == '__main__': unittest.main()"
    addition="""

    def test_committed_results_reject_bool_int_type_drift(self):
        with self.assertRaises(ValueError):
            require_committed_results({'missing_editorial_text_checked': True}, b'{\"missing_editorial_text_checked\":1}')
        with self.assertRaises(ValueError):
            require_committed_results({'schema_version': 1}, b'{\"schema_version\":true}')
"""
    require('test_committed_results_reject_bool_int_type_drift' not in text,'native JSON type test already present')
    require(marker in text,'native test insertion marker missing')
    p.write_text(text.replace(marker,addition+marker),encoding='utf-8')

    p=ROOT/'tools/audit/verify_announcement_trigger.py'
    replace_once(p,"""def require_committed_result(generated, raw):
    committed=json_bytes(raw)
    require(generated==committed,'generated F17 trigger evidence differs from committed r3-trigger-evidence.json')
    return committed
""","""def strict_json_equal(left, right):
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(strict_json_equal(left[key], right[key]) for key in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(strict_json_equal(a, b) for a, b in zip(left, right))
    return left == right


def require_committed_result(generated, raw):
    committed=json_bytes(raw)
    require(strict_json_equal(generated,committed),'generated F17 trigger evidence differs from committed r3-trigger-evidence.json')
    return committed
""",'strict trigger JSON equality')

    p=ROOT/'tools/audit/test_verify_announcement_trigger.py'
    text=p.read_text(encoding='utf-8')
    marker="\nif __name__=='__main__':unittest.main()\n"
    addition="""
    def test_committed_map_rejects_bool_int_type_drift(self):
        from verify_announcement_trigger import require_committed_result
        with self.assertRaises(ValueError):
            require_committed_result({'selected': False}, b'{\"selected\":0}')
        with self.assertRaises(ValueError):
            require_committed_result({'schema_version': 1}, b'{\"schema_version\":true}')
"""
    require('test_committed_map_rejects_bool_int_type_drift' not in text,'trigger JSON type test already present')
    require(marker in text,'trigger test insertion marker missing')
    p.write_text(text.replace(marker,'\n'+addition+marker),encoding='utf-8')

    groups_path=EV/'coverage-groups.json'
    groups=json.loads(groups_path.read_text(encoding='utf-8'))
    require(len(groups.get('groups',[]))==1 and groups['groups'][0].get('id')=='ATLAS-CREATURE-GAMEPLAY-SHARDS','expected one Atlas grouped candidate before rejection')
    candidate=groups['groups'][0]
    candidate['disposition']='REVALIDATION_FAILED_NOT_ADOPTED'
    candidate['depth']='GROUPED_REVALIDATION_CANDIDATE_REJECTED'
    candidate['evaluation']={
        'qualification_run':34218265762,
        'qualification_job':102035087439,
        'audit_python_tests_passed':103,
        'audit_node_tests_passed':37,
        'identity_revalidation':'PASS_508_EXACT_SHARDS_MANIFEST_UNCHANGED_AND_5_DEPENDENT_BLOBS_BOUND',
        'focused_current_consumer_tests':{'passed':4,'failed':1},
        'failing_test':'gameplay impact routing executes both functional fixture and bounded source-contract coverage',
        'failure_location':'tests/verification/qualification-gameplay-contract.test.mjs:77',
        'failure_reason':'gameplay runtime requires a dedicated impact rule',
        'outcome':'REJECTED_NOT_COUNTED_AS_GROUPED'
    }
    groups['groups']=[]
    groups['rejected_candidates']=[candidate]
    groups_path.write_text(json.dumps(groups,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

    summary_path=EV/'coverage-summary.json'
    summary=json.loads(summary_path.read_text(encoding='utf-8'))
    summary['per_repository']['atlas'].update(direct_scoped=10,grouped=0,not_applicable=0,unverified_semantics=1145)
    summary['ledger_sha256']='72547eec47bb8b5d64688ba0597947708d5ebc524a54acfce267deb47597e7c1'
    summary.pop('ledger_sha256_status',None)
    summary.update(scoped_review_paths=202,grouped_revalidated_paths=0,semantically_classified_paths=202,unverified_semantics_total=4123,rejected_group_candidates=1)
    summary['durability']='Full CSV accompanies the audit delivery. Committed DIRECT review rows, immutable Git trees and verify_report.py reproduce every disposition. A rejected GROUPED candidate is evidence of a failed carry-forward attempt and is not counted as semantic coverage.'
    summary['coverage_dimension_note']='DIRECT records an explicit bounded review scope, not universal approval. The attempted 508-path Atlas GROUPED carry-forward was rejected after current consumer impact-routing qualification failed; those leaves remain UNVERIFIED.'
    summary_path.write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

    report_path=ROOT/'docs/evidence/OTERYN-ORGANIZATION-COMPREHENSIVE-AUDIT-20260907.json'
    report=json.loads(report_path.read_text(encoding='utf-8'))
    report.update(revision='R3-NATIVE-EVIDENCE-SCOPED-REVIEW-POST-INDEPENDENT-HARDENING-ATLAS-GROUP-REJECTED',reconciled_register_rows=78,additional_followup_ids=4,scoped_review_paths=202,grouped_revalidated_paths=0,semantically_classified_paths=202,rejected_group_candidates=1,atlas_grouped_revalidation='organization-audit-20260907/r3-atlas-grouped-revalidation.json')
    report['r3_review']['latest_completed_rereview']={'reviewed_head':'e242a68a9df73304cbb6ba8bd3cfebbb36a2197b','completed_at_utc':'2026-09-08T10:54:10Z','result':'CHANGES_REQUIRED','p1':1,'p2':2,'new_material_findings':['coverage ledger disclosure labels','native-result strict JSON type equality','trigger-map strict JSON type equality']}
    report['r3_review']['fresh_independent_rereview_required']=True
    report_path.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

    rejected={'schema_version':1,'candidate_id':'ATLAS-CREATURE-GAMEPLAY-SHARDS','source_commit':'f00815858bb5b031c502ad19fb96a05ff66b4d84','historical_source':'5ea38a62fe1af8b8068adcb84350e9644905943c','qualification_run':34218265762,'qualification_job':102035087439,'identity_carry_forward':{'result':'PASS','grouped_candidate_paths':508,'changed_group_or_manifest_paths':0,'dependent_blobs_verified':5},'focused_current_consumer_tests':{'passed':4,'failed':1,'failing_test':'gameplay impact routing executes both functional fixture and bounded source-contract coverage','location':'tests/verification/qualification-gameplay-contract.test.mjs:77','assertion':'gameplay runtime requires a dedicated impact rule'},'audit_tool_tests':{'python_passed':103,'node_passed':37},'decision':'GROUPED_CARRY_FORWARD_REJECTED_AND_508_PATHS_REMAIN_UNVERIFIED','reason':'Historical grouped identity remained stable, but a current dependent impact-routing contract test failed. Historical consumer-based GROUPED assurance therefore cannot be carried forward to this source cut.','limitations':'No provider repair, restored Atlas verification, product runtime failure, or later-main regression is inferred. This is exact evidence about the pinned f008 source cut.'}
    (EV/'r3-atlas-grouped-revalidation.json').write_text(json.dumps(rejected,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

    findings=EV/'finding-register.tsv'
    ft=findings.read_text(encoding='utf-8')
    require('\nATLAS-F17\t' not in ft,'ATLAS-F17 already exists')
    row=['ATLAS-F17','P2','atlas','CONFIRMED_SOURCE','source_snapshot','Gameplay profile runtime lacks its expected dedicated impact-routing rule','R3 Atlas grouped qualification run34218265762/job102035087439 on exact f008: 508 shard identities plus manifest carry-forward check passed and five dependent blobs were bound; focused current consumer/runtime tests then passed4/5 and failed the existing qualification test at tests/verification/qualification-gameplay-contract.test.mjs:77 because no dedicated impact rule exists for src/browser/creature-gameplay-profiles.mjs. No provider mutation or product runtime failure is inferred.','Oteryn/Oteryn-Atlas#376; Oteryn/Oteryn-Atlas#315','On a protected later source, the existing qualification test passes with an exact impact rule selecting the gameplay profile runtime required groups; preserve minimal data-capability routing and do not infer restored product verification.']
    require(not any('\t' in x or '\n' in x for x in row),'unsafe finding field')
    findings.write_text(ft.rstrip('\n')+'\n'+'\t'.join(row)+'\n',encoding='utf-8')

    dm=EV/'domain-matrix.tsv'
    rows=list(csv.DictReader(io.StringIO(dm.read_text(encoding='utf-8')),delimiter='\t'))
    require(len(rows)==23,'domain row count changed')
    l=[r for r in rows if r['domain']=='L'];require(len(l)==1,'domain L missing');l=l[0]
    require('ATLAS-F17' not in l['references'],'ATLAS-F17 already bound to domain L')
    l['method_and_evidence']+='; exact Atlas f008 gameplay impact-routing qualification test fails because the dedicated profile-runtime impact rule is absent'
    l['references']+=';ATLAS-F17'
    out=io.StringIO(newline='');w=csv.DictWriter(out,fieldnames=['domain','name','acceptance_criterion','method_and_evidence','opinion','remaining_limit','references'],delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows);dm.write_text(out.getvalue(),encoding='utf-8')

    readme=EV/'README.md'
    replace_once(readme,'R3 contains 77 finding records, 23 A–W domains, 15 residual obligations and 202 explicit scoped path reviews out of 4325 immutable leaves.','R3 contains 78 finding records, 23 A–W domains, 15 residual obligations and 202 explicit scoped path reviews out of 4325 immutable leaves.','README finding count')
    rt=readme.read_text(encoding='utf-8');anchor='`r3-native-manifest.json` binds six public native archives;';note='`r3-atlas-grouped-revalidation.json` records a rejected 508-shard GROUPED carry-forward: immutable shard identity passed, but current consumer impact-routing qualification failed, so all 508 remain UNVERIFIED. '
    require(anchor in rt,'README evidence anchor missing');readme.write_text(rt.replace(anchor,note+anchor,1),encoding='utf-8')

    md=ROOT/'docs/evidence/OTERYN-ORGANIZATION-COMPREHENSIVE-AUDIT-20260907.md'
    replace_once(md,'`finding-register.tsv` accounts individually for **77 records**: 74 historical source IDs plus three explicit follow-ups/additions.','`finding-register.tsv` accounts individually for **78 records**: 74 historical source IDs plus four explicit follow-ups/additions.','main report finding count')
    mt=md.read_text(encoding='utf-8');anchor='**PLATFORM-H02 security handling correction:**';atlas_note='**ATLAS-F17 (P2):** on the pinned Atlas `f008158…` source, the existing gameplay impact-routing qualification test fails because `src/browser/creature-gameplay-profiles.mjs` has no dedicated impact rule. A proposed carry-forward of the historical 508 generated gameplay shards passed exact shard/manifest identity checks but was therefore rejected; those 508 leaves remain UNVERIFIED. This is not a claim about later Atlas main, restored verification or a runtime gameplay incident.\n\n';require(anchor in mt,'main report security anchor missing');mt=mt.replace(anchor,atlas_note+anchor,1)
    anchor='The correction pass does five things:';review_note='A later independent re-review of `e242a68a9df73304cbb6ba8bd3cfebbb36a2197b` found one remaining canonical disclosure-label P1 and two strict-JSON-type P2 evidence defects. This revision corrects those items, but the resulting new head still requires fresh independent re-review; author remediation is not independent acceptance.\n\n';require(anchor in mt,'main report review anchor missing');md.write_text(mt.replace(anchor,review_note+anchor,1),encoding='utf-8')

    vi=EV/'verification-index.json';v=json.loads(vi.read_text(encoding='utf-8'));v['r3_sensitive_material']='Two characterization scripts are absent from the final effective diff; mechanism details present in public ancestor history/Actions artifacts are treated as disclosed. Current audit text does not repeat mechanism details; historical artifact deletion/expiry, private-advisory submission and remediation are not established.';vi.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

    corrections=EV/'r3-independent-review-corrections.json';c=json.loads(corrections.read_text(encoding='utf-8'));c['status']='AUTHOR_REMEDIATION_ACTIVE_AFTER_REREVIEW3';c['latest_rereview']={'reviewed_head':'e242a68a9df73304cbb6ba8bd3cfebbb36a2197b','completed_at_utc':'2026-09-08T10:54:10Z','result':'CHANGES_REQUIRED','findings':[{'thread_id':'PRRT_kwDOT8KVrs6gNOM7','priority':'P1','subject':'Canonical coverage ledger disclosure labels'},{'thread_id':'PRRT_kwDOT8KVrs6gNONA','priority':'P2','subject':'Native result strict JSON types'},{'thread_id':'PRRT_kwDOT8KVrs6gNOND','priority':'P2','subject':'Trigger evidence strict JSON types'}]};c['validation']['limits']='Author remediation remains non-independent. A fresh review is required after the exact corrected head is stable.';corrections.write_text(json.dumps(c,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

    p=ROOT/'tools/audit/test_verify_report.py';tt=p.read_text(encoding='utf-8')
    for old,new in [("self.assertEqual(result['findings'],77)","self.assertEqual(result['findings'],78)"),("self.assertEqual(result['grouped_revalidated_paths'],508)","self.assertEqual(result['grouped_revalidated_paths'],0)"),("self.assertEqual(result['semantically_classified_paths'],710)","self.assertEqual(result['semantically_classified_paths'],202)"),("self.assertEqual(result['unverified_semantics'],3615)","self.assertEqual(result['unverified_semantics'],4123)")]:
        require(tt.count(old)==1,'test_verify_report expected-count shape changed: '+old);tt=tt.replace(old,new)
    start=tt.find('    def test_grouped_count_cannot_be_hidden');end=tt.find('    def test_reproduction_called_pass_rejected');require(start>=0 and end>start,'group-test replacement markers missing')
    replacement="""    def test_rejected_group_is_not_promoted_by_summary(self):
        self.mutate(self.base/'coverage-summary.json',lambda d:d['per_repository']['atlas'].update(grouped=508,unverified_semantics=637))
        self.reject()

    def test_rejected_candidate_is_preserved_but_not_counted(self):
        data=audit.read_json(self.base/'coverage-groups.json')
        self.assertEqual(data['groups'],[])
        self.assertEqual(len(data['rejected_candidates']),1)
        self.assertEqual(data['rejected_candidates'][0]['evaluation']['outcome'],'REJECTED_NOT_COUNTED_AS_GROUPED')

"""
    p.write_text(tt[:start]+replacement+tt[end:],encoding='utf-8')

    p=ROOT/'tools/audit/verify_report.py';vt=p.read_text(encoding='utf-8')
    replace_once(p,"""    groups=doc.get('groups')
    require(isinstance(groups,list),'coverage groups missing')
    unique(groups,lambda row:row.get('id'),'coverage group id')
    prefixes=[]
""","""    groups=doc.get('groups')
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
""",'verify_report rejected candidate validation')

    p=ROOT/'tools/audit/verify_atlas_group.py';at=p.read_text(encoding='utf-8')
    old="groups=read_json(audit_root/'docs/evidence/organization-audit-20260907/coverage-groups.json')['groups']\n    selected=[g for g in groups if g['id']==GROUP_ID]"
    new="group_doc=read_json(audit_root/'docs/evidence/organization-audit-20260907/coverage-groups.json')\n    groups=group_doc.get('groups',[])+group_doc.get('rejected_candidates',[])\n    selected=[g for g in groups if g['id']==GROUP_ID]"
    require(at.count(old)==1,'verify_atlas_group selection shape changed');p.write_text(at.replace(old,new),encoding='utf-8')

    print(json.dumps({'result':'RECONCILIATION_PREPARED_NOT_COMMITTED','findings':78,'direct_scoped':202,'grouped_adopted':0,'unverified':4123,'atlas_group_candidate':'REJECTED','review3_type_checks':'STRICT'},indent=2))


if __name__=='__main__':
    main()
