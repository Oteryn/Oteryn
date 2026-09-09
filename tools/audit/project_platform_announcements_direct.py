#!/usr/bin/env python3
"""Mechanically project the qualified Announcements DIRECT candidate.

This tool is projection-only. It reads an already-reproduced canonical ledger,
requires all ten candidate leaves to remain UNVERIFIED, writes a projected
ledger plus a generated candidate overlay, and never mutates canonical audit
source files.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path

import verify_platform_announcements_direct as candidate_verifier

CANONICAL_SHA = '2d823435f76f0c08b118ccb5dc1c9ccf9ef4acc41bffdd447b260e82ea404b0f'
LEDGER_FIELDS = ['repository_id','commit_sha','tree_sha','path','mode','object_sha','disposition','depth','scope']
OVERLAY_FIELDS = ['repository','path','blob_sha','depth','line_ranges','scope','source_reference','historical_batch','historical_ledger_binding','execution_evidence','limitations']
PRIMARY_EVIDENCE = (
    'Primary qualification: GitHub Actions run 34380399141, job 102563546379, '
    'artifact 10115614293 (SHA-256 eb577820be531bfbb5451cf8d964ffeb6a78eeb47d06c36c872ab2e04637141f), '
    'MariaDB 11.8.9; AnnouncementsModuleTest 4 cases / 20 assertions / 0 failures / 0 errors / 0 skips.'
)
LIMITATIONS = (
    'Bounded frozen-source semantic review plus representative module execution only; '
    'the Polish editorial_translations join branch is not directly executed and no dedicated simultaneous-writer race is proven. '
    'No later Platform state, whole-product readiness, organization-wide audit completion, or independent score is inferred.'
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_ledger(path: Path) -> tuple[bytes, list[dict[str,str]]]:
    raw = path.read_bytes()
    reader = csv.DictReader(io.StringIO(raw.decode('utf-8'), newline=''))
    require(reader.fieldnames == LEDGER_FIELDS, 'canonical ledger header drift')
    rows = list(reader)
    require(len(rows) == 4325, 'canonical ledger row-count drift')
    require(len({(r['repository_id'],r['path']) for r in rows}) == len(rows), 'canonical ledger duplicate path')
    require(hashlib.sha256(raw).hexdigest() == CANONICAL_SHA, 'canonical ledger digest drift')
    require(Counter(r['disposition'] for r in rows) == Counter({'UNVERIFIED':3989,'DIRECT':223,'GROUPED':113}), 'canonical ledger disposition drift')
    return raw, rows


def serialize_ledger(rows: list[dict[str,str]]) -> bytes:
    buf = io.StringIO(newline='')
    writer = csv.DictWriter(buf, fieldnames=LEDGER_FIELDS, lineterminator='\n')
    writer.writeheader(); writer.writerows(rows)
    return buf.getvalue().encode('utf-8')


def project_rows(rows: list[dict[str,str]], candidate: dict) -> tuple[list[dict[str,str]], list[str]]:
    by_path = {row['path']: row for row in candidate['paths']}
    require(len(by_path) == 10, 'candidate path count drift')
    changed=[]; projected=[]
    for original in rows:
        row=dict(original)
        if row['repository_id']=='platform' and row['path'] in by_path:
            spec=by_path[row['path']]
            require(row['commit_sha']==candidate_verifier.SOURCE_COMMIT, 'candidate ledger commit drift: '+row['path'])
            require(row['tree_sha']==candidate_verifier.SOURCE_TREE, 'candidate ledger tree drift: '+row['path'])
            require(row['mode']=='100644', 'candidate ledger mode drift: '+row['path'])
            require(row['object_sha']==spec['blob_sha'], 'candidate ledger blob drift: '+row['path'])
            require(row['disposition']=='UNVERIFIED', 'candidate not UNVERIFIED before projection: '+row['path'])
            require(row['depth']=='IDENTITY_ONLY', 'candidate pre-projection depth drift: '+row['path'])
            row['disposition']='DIRECT'; row['depth']=spec['depth']; row['scope']=spec['scope']; changed.append(row['path'])
        projected.append(row)
    require(changed == list(by_path), 'projected candidate path set/order drift')
    require(len(changed)==10, 'projection must change exactly ten paths')
    return projected, changed


def overlay_bytes(candidate: dict, platform_root: Path) -> bytes:
    buf=io.StringIO(newline=''); writer=csv.DictWriter(buf,fieldnames=OVERLAY_FIELDS,delimiter='\t',lineterminator='\n'); writer.writeheader()
    for row in candidate['paths']:
        source=platform_root/row['path']
        require(source.is_file(), 'candidate source file missing for overlay: '+row['path'])
        line_count=len(source.read_text(encoding='utf-8').splitlines())
        require(line_count>0, 'candidate source file empty: '+row['path'])
        writer.writerow({
            'repository':'platform','path':row['path'],'blob_sha':row['blob_sha'],'depth':row['depth'],
            'line_ranges':json.dumps([[1,line_count]],separators=(',',':')),'scope':row['scope'],
            'source_reference':f'frozen Oteryn/Oteryn-Platform@{candidate_verifier.SOURCE_COMMIT}:{row["path"]}',
            'historical_batch':'none','historical_ledger_binding':'none','execution_evidence':PRIMARY_EVIDENCE,'limitations':LIMITATIONS,
        })
    return buf.getvalue().encode('utf-8')


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--audit-root',type=Path,default=Path('.'))
    parser.add_argument('--platform-root',type=Path,required=True)
    parser.add_argument('--canonical-ledger',type=Path,required=True)
    parser.add_argument('--projected-ledger-output',type=Path,required=True)
    parser.add_argument('--overlay-output',type=Path,required=True)
    args=parser.parse_args()

    candidate=candidate_verifier.read_json(args.audit_root/candidate_verifier.CANDIDATE_REL)
    candidate_verifier.validate_candidate_shape(candidate)
    candidate_verifier.validate_source(candidate,args.platform_root)
    _,rows=read_ledger(args.canonical_ledger)
    projected,changed=project_rows(rows,candidate)
    raw=serialize_ledger(projected)
    counts=Counter(r['disposition'] for r in projected)
    require(len(projected)==4325 and counts==Counter({'UNVERIFIED':3979,'DIRECT':233,'GROUPED':113}), 'projected accounting drift')
    require(sum(1 for r in projected if r['disposition']!='UNVERIFIED')==346, 'projected classified count drift')
    projected_sha=hashlib.sha256(raw).hexdigest()
    args.projected_ledger_output.write_bytes(raw)
    overlay=overlay_bytes(candidate,args.platform_root); args.overlay_output.write_bytes(overlay)
    result={
        'result':'ANNOUNCEMENTS_DIRECT_PROJECTION_VALID_NOT_ADOPTED',
        'canonical_ledger_sha256':CANONICAL_SHA,'projected_ledger_sha256':projected_sha,
        'projected_rows':4325,'projected_direct_paths':233,'projected_grouped_paths':113,
        'projected_unverified_paths':3979,'projected_semantically_classified_paths':346,
        'changed_paths':changed,'changed_path_count':10,'coverage_adopted':False,
        'generated_overlay_sha256':hashlib.sha256(overlay).hexdigest(),
        'product_readiness_claimed':False,'audit_completion_claimed':False,
    }
    print(json.dumps(result,sort_keys=True)); return 0


if __name__=='__main__':
    raise SystemExit(main())
