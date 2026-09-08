#!/usr/bin/env python3
"""Revalidate one historical Atlas GROUPED rule against an exact current source checkout.

Read-only. This proves carry-forward eligibility for the generated shard group,
not Atlas product readiness or restored verification.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

GROUP_ID='ATLAS-CREATURE-GAMEPLAY-SHARDS'


def require(ok,message):
    if not ok: raise ValueError(message)


def read_json(path):
    def pairs(items):
        out={}
        for k,v in items:
            require(k not in out,'duplicate JSON key')
            out[k]=v
        return out
    return json.loads(path.read_text(encoding='utf-8'),object_pairs_hook=pairs)


def git(root,*args):
    return subprocess.run(['git','-C',str(root),*args],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=False,timeout=20).stdout


def text(root,*args):
    return git(root,*args).decode().strip()


def blob_sha(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()


def tree_entries(root,ref,prefix):
    raw=git(root,'ls-tree','-rz','--full-tree',ref,'--',prefix)
    rows=[]
    for item in raw.split(b'\0'):
        if not item: continue
        meta,path=item.split(b'\t',1)
        mode,kind,oid=meta.decode().split(' ')
        rows.append((path.decode(),mode,kind,oid))
    return rows


def verify(audit_root:Path,atlas_root:Path,evidence_root:Path):
    group_doc=read_json(audit_root/'docs/evidence/organization-audit-20260907/coverage-groups.json')
    groups=group_doc.get('groups',[])+group_doc.get('rejected_candidates',[])
    selected=[g for g in groups if g['id']==GROUP_ID]
    require(len(selected)==1,'Atlas grouped rule missing/duplicated')
    group=selected[0];hist=group['historical_evidence'];current=group['current_revalidation']
    require(text(atlas_root,'rev-parse','HEAD')==current['source_commit'],'wrong current Atlas commit')
    require(text(atlas_root,'rev-parse','HEAD^{tree}')==current['source_tree'],'wrong current Atlas tree')
    require(text(evidence_root,'rev-parse','HEAD')==hist['publication_commit'],'wrong Atlas audit publication commit')
    rules_path=evidence_root/hist['coverage_rules_path']
    require(not rules_path.is_symlink(),'historical coverage rules symlink refused')
    rules_raw=rules_path.read_bytes()
    require(blob_sha(rules_raw)==hist['coverage_rules_blob'],'historical coverage rules blob mismatch')
    rules=read_json(rules_path)
    require(rules['repository']==hist['repository'] and rules['main_sha']==hist['audited_main_sha'] and rules['root_tree_sha']==hist['audited_main_tree'],'historical coverage source mismatch')
    matches=[r for r in rules['grouped_rules'] if r.get('pattern')==hist['pattern']]
    require(len(matches)==1 and matches[0].get('state')=='GROUPED','historical grouped rule missing')
    require(matches[0].get('count')==group['expected_count']==hist['count'],'historical grouped count mismatch')
    require(matches[0].get('basis')==hist['basis'],'historical grouped basis mismatch')
    prefix=group['path_prefix'];manifest='web/creature-gameplay/manifest.json'
    changed=git(atlas_root,'diff','--name-only',hist['audited_main_sha'],current['source_commit'],'--',prefix,manifest).decode().splitlines()
    require(changed==[],'grouped shard/manifest source changed: '+repr(changed[:10]))
    old=tree_entries(atlas_root,hist['audited_main_sha'],prefix)
    now=tree_entries(atlas_root,current['source_commit'],prefix)
    require(len(now)==group['expected_count'] and len(old)==group['expected_count'],'grouped tree count mismatch')
    require(old==now,'grouped tree identity changed')
    require(all(mode=='100644' and kind=='blob' for _,mode,kind,_ in now),'grouped set contains non-regular leaf')
    for path,expected in current['current_blobs'].items():
        actual=text(atlas_root,'rev-parse',current['source_commit']+':'+path)
        require(actual==expected,'current Atlas dependent blob mismatch: '+path)
    return {
        'result':'GROUPED_REVALIDATION_ELIGIBLE_NOT_PRODUCT_PASS',
        'group_id':group['id'],
        'repository':'Oteryn/Oteryn-Atlas',
        'historical_source':hist['audited_main_sha'],
        'current_source':current['source_commit'],
        'grouped_paths':len(now),
        'changed_group_or_manifest_paths':0,
        'dependent_blobs_verified':len(current['current_blobs']),
        'limitation':group['limitations'],
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--audit-root',type=Path,required=True)
    p.add_argument('--atlas-root',type=Path,required=True)
    p.add_argument('--evidence-root',type=Path,required=True)
    a=p.parse_args();print(json.dumps(verify(a.audit_root.resolve(),a.atlas_root.resolve(),a.evidence_root.resolve()),indent=2))

if __name__=='__main__':main()
