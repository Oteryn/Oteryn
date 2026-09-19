#!/usr/bin/env python3
"""Verify canonical adoption of the immutable HISTORY-REVALIDATION packet."""
from __future__ import annotations
import hashlib, json, subprocess
from pathlib import Path
import verify_report

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/evidence/organization-audit-20260907'
PACKET=BASE/'history-revalidation-candidate.json'
CHECKPOINT=BASE/'CHECKPOINT-20260915-HISTORY-REVALIDATION-ADOPTION.md'
PACKET_SHA='73fd0205395af9647a2ca669bcce9e60841daa69d0f390e99b21413546870bf2'
PACKET_BLOB='f8ded1a4a392e7378090c2cfe02585478a4bcc08'
CHECKPOINT_SHA='a2eebaedde5adcaf9f6d09bbbf310b735a44e3c742a8aaa58742225f985af2bc'
SOURCE_COMMITS={'meta':'d9419b05eb98c81279297563c11fc90e4fe708ac','game':'775a09091743af395ecb8f1e440cb9c286bc0dd2','platform':'84d504c98acc8134eb4c9545711010b74c987974','atlas':'0d22a8d4378e66441502482ce715e226d487248e'}
COUNTS={'source_leaves':4361,'direct':335,'grouped':113,'unverified':3913,'semantically_classified':448}
LEDGER='d93838bebb6f3690bad3d6182bbc05edd0af8acf8a98d28260e496276b95a22b'

def require(ok,msg):
    if not ok: raise ValueError(msg)
def blob(raw):
    header=f'blob {len(raw)}\0'.encode(); return hashlib.sha1(header+raw).hexdigest()
def load_json_bytes(path):
    raw=path.read_bytes(); seen=[]
    def hook(pairs):
        d={}
        for k,v in pairs:
            require(k not in d,f'duplicate JSON key: {k}'); d[k]=v
        return d
    try: data=json.loads(raw.decode('utf-8'),object_pairs_hook=hook)
    except UnicodeDecodeError as e: raise ValueError('invalid UTF-8') from e
    require(type(data) is dict,'packet root must be object'); return raw,data

def validate(root=ROOT):
    base=root/'docs/evidence/organization-audit-20260907'
    raw,p=load_json_bytes(base/PACKET.name)
    require(hashlib.sha256(raw).hexdigest()==PACKET_SHA,'packet SHA drift')
    require(blob(raw)==PACKET_BLOB,'packet Git blob drift')
    require(p['obligation']=='HISTORY-REVALIDATION' and p['disposition']=='HANDOFF_COMPLETE_OBLIGATION_REMAINS_OPEN','packet open disposition drift')
    boundaries={x['id']:x for x in p['source_boundaries']}
    require({k:boundaries[k]['current_main_commit'] for k in SOURCE_COMMITS}==SOURCE_COMMITS,'source observation drift')
    require(boundaries['game']['compare_file_list_complete'] is False and boundaries['game']['changed_files_reported']==300,'Game truncation limitation drift')
    require(p['claims']=={'history_revalidation_closed':False,'product_readiness_claimed':False,'runtime_readiness_claimed':False,'security_remediation_claimed':False,'organization_audit_completion_claimed':False},'negative claims drift')
    cp=(base/CHECKPOINT.name).read_bytes(); require(hashlib.sha256(cp).hexdigest()==CHECKPOINT_SHA,'checkpoint drift')
    report_path=root/'docs/evidence/OTERYN-ORGANIZATION-COMPREHENSIVE-AUDIT-20260907.json'
    result=verify_report.validate(report_path)
    report=verify_report.read_json(report_path); index=verify_report.read_json(base/'verification-index.json')
    require(report.get('history_revalidation_packet')=='organization-audit-20260907/history-revalidation-candidate.json','report packet pointer drift')
    require(report.get('history_revalidation_adoption_checkpoint')=='organization-audit-20260907/CHECKPOINT-20260915-HISTORY-REVALIDATION-ADOPTION.md','report checkpoint pointer drift')
    record=index.get('audit186_history_revalidation_evidence_adoption'); require(type(record) is dict,'adoption index missing')
    require(record['worker_pull_request']==206 and record['worker_head']=='58a73b77b945b97011fa01ac8bda1732a8a4e6dd' and record['issue_freeze_checkpoint']==5671120887,'worker provenance drift')
    require(record['packet_git_blob']==PACKET_BLOB and record['packet_sha256']==PACKET_SHA,'packet identity binding drift')
    require(record['source_observation_commits']==SOURCE_COMMITS,'index source observations drift')
    require(record['history_revalidation_open'] is True and record['game_compare_complete'] is False,'open/Game limitation drift')
    for key in ('current_truth_claimed','product_readiness_claimed','runtime_readiness_claimed','security_remediation_claimed','audit_completion_claimed'):
        require(record[key] is False,f'{key} drift')
    require(record['canonical_counts']==COUNTS and record['canonical_ledger_sha256']==LEDGER,'canonical accounting drift')
    unknowns=verify_report.read_json(base/'unknowns.json')['items']; require(len(unknowns)==14 and any(x['id']=='HISTORY-REVALIDATION' for x in unknowns),'HISTORY/all-open obligation drift')
    return {'result':'AUDIT186_HISTORY_REVALIDATION_EVIDENCE_ADOPTED_OBLIGATION_OPEN','history_revalidation_open':True,'game_compare_complete':False,'canonical_counts':COUNTS,'canonical_ledger_sha256':LEDGER,'residual_obligations_open':14,'report_result':result['result']}
if __name__=='__main__': print(json.dumps(validate(),sort_keys=True))
