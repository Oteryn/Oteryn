#!/usr/bin/env python3
"""Fail-closed verifier for the preserved two-path Platform audit-recorder DIRECT slice.

The recorder candidate and its original two-row overlay are immutable historical
adoption evidence. Current global accounting may advance through a separate
canonical composition overlay; that must not rewrite the recorder evidence.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess

import verify_report as vr

CANDIDATE_REL = Path('docs/evidence/organization-audit-20260907/r3-platform-audit-recorders-direct-candidate.json')
CANDIDATE_BLOB = 'ca73bad56417157136b4284e8b31fe7f29829d07'
CANDIDATE_SEMANTIC_SHA256 = '16ef44948f3490d1fcd05065fed89fbdba3d9334c28cd73c741a0d41f280d0f6'
OVERLAY_REL = Path('docs/evidence/organization-audit-20260907/coverage-review-additions.tsv')
OVERLAY_BLOB = '9b5c1afc0d1ac39641077510fb4d6c20222e04d5'
CANONICAL_OVERLAY_REL = Path('docs/evidence/organization-audit-20260907/coverage-review-canonical-additions.tsv')
SOURCE_COMMIT = 'de917b3477a1de0667531380de3660e8b2ab59aa'
SOURCE_TREE = 'ffdf2a286d3a39f2344cf2ff53b28e4ef7369a8e'
CURRENT_LEDGER_SHA = 'ff5c6621a78c14fc17802ecf01b4ef815867ccab95acce90c490973946d6279b'
REVIEW_PROVENANCE = 'External mutable PR #185 metadata: reviewed implementation 3eb62ef72c1e13412fa45d5b25d597d112d9ae7d; review comment 5609072309. Not self-certified evidence.'
SHA = re.compile(r'[0-9a-f]{40}\Z')
OVERLAY_HEADER = (
    'repository', 'path', 'blob_sha', 'depth', 'scope', 'line_ranges',
    'execution_evidence',
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(raw)).encode('ascii') + b'\0' + raw).hexdigest()


def parse_json_bytes(raw: bytes) -> dict:
    def pairs(items):
        out={}
        for key,value in items:
            require(key not in out,'duplicate JSON key')
            out[key]=value
        return out
    try:
        text=raw.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise ValueError('invalid UTF-8 JSON') from exc
    value=json.loads(text,object_pairs_hook=pairs)
    require(isinstance(value,dict),'JSON root must be an object')
    return value


def read_json(path: Path) -> dict:
    return parse_json_bytes(path.read_bytes())


def expected_candidate(root: Path) -> dict:
    """Load the candidate once and bind the parsed semantics to its Git blob."""
    raw=(root/CANDIDATE_REL).read_bytes()
    require(blob_sha(raw)==CANDIDATE_BLOB,'audit-recorder candidate working-tree blob drift')
    require(git(root,'rev-parse','HEAD:'+str(CANDIDATE_REL))==CANDIDATE_BLOB,'tracked audit-recorder candidate blob drift')
    return parse_json_bytes(raw)


def validate_candidate_shape(candidate: dict) -> None:
    semantic_bytes=json.dumps(candidate,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')
    require(hashlib.sha256(semantic_bytes).hexdigest()==CANDIDATE_SEMANTIC_SHA256,'complete audit-recorder candidate content drift')
    require(candidate.get('coverage_adopted') is True,'complete audit-recorder candidate adoption drift')
    require(candidate.get('source')=={'repository':'Oteryn/Oteryn-Platform','commit_sha':SOURCE_COMMIT,'tree_sha':SOURCE_TREE},'complete audit-recorder candidate source drift')
    require(candidate.get('adoption',{}).get('direct_overlay_path')==str(OVERLAY_REL),'complete audit-recorder candidate overlay path drift')
    require(candidate.get('adoption',{}).get('direct_overlay_blob_sha')==OVERLAY_BLOB,'complete audit-recorder candidate overlay blob drift')


def validate_source_text(path: str, text: str, row: dict) -> None:
    for token in row['semantic_assertions']:
        require(token in text,'semantic oracle drift: '+path)
    if path.endswith('SecurityEventRecorder.php'):
        constants=re.findall(r'^\s*public const [A-Z0-9_]+\s*=',text,re.MULTILINE)
        require(len(constants)==row['expected_public_event_constants'],'security event constant count drift')


def git(cwd: Path,*args: str) -> str:
    return subprocess.run(['git','-c','core.hooksPath=/dev/null',*args],cwd=cwd,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=60).stdout.strip()


def tree_blob(cwd: Path,path: str) -> str:
    raw=git(cwd,'ls-tree','HEAD','--',path)
    require(raw,'source path absent: '+path)
    head,actual=raw.split('\t',1);mode,kind,oid=head.split(' ')
    require(actual==path and kind=='blob' and mode.startswith('100'),'not regular source blob: '+path)
    require(bool(SHA.fullmatch(oid)),'invalid source blob: '+path)
    return oid


def parse_tsv_bytes(raw: bytes) -> list[dict[str,str]]:
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise ValueError('invalid UTF-8 TSV') from exc
    try:
        rows = list(csv.reader(io.StringIO(text, newline=''), delimiter='\t', strict=True))
    except csv.Error as exc:
        raise ValueError('malformed TSV') from exc
    require(bool(rows), 'recorder overlay header missing')
    require(tuple(rows[0]) == OVERLAY_HEADER, 'recorder overlay header drift')
    parsed = []
    for row in rows[1:]:
        require(len(row) == len(OVERLAY_HEADER), 'recorder overlay column count drift')
        parsed.append(dict(zip(OVERLAY_HEADER, row, strict=True)))
    return parsed


def read_tsv(path: Path) -> list[dict[str,str]]:
    return parse_tsv_bytes(path.read_bytes())


def validate_adopted_docs(candidate: dict, audit_root: Path) -> None:
    validate_candidate_shape(candidate)
    old_overlay=audit_root/OVERLAY_REL
    require(old_overlay.is_file(),'recorder overlay missing')
    raw=old_overlay.read_bytes()
    require(blob_sha(raw)==OVERLAY_BLOB,'recorder overlay blob drift')
    old_rows=parse_tsv_bytes(raw)
    require(len(old_rows)==2,'recorder overlay row count drift')
    expected_paths={row['path'] for row in candidate['paths']}
    require({row['path'] for row in old_rows}==expected_paths,'recorder overlay membership drift')
    require(len(old_rows)==len({row['path'] for row in old_rows}),'recorder overlay duplicate path')

    report_path=audit_root/'docs/evidence/OTERYN-ORGANIZATION-COMPREHENSIVE-AUDIT-20260907.json'
    report=vr.read_json(report_path)
    require(report.get('revision')=='R3-NATIVE-EVIDENCE-POST-REVIEW-PLATFORM-SEMANTIC-CARRYFORWARD-113-DIRECT-294','current report revision drift')
    require(report.get('coverage_review_additions')==vr.DIRECT_ADDITIONS_BINDING,'current canonical overlay binding drift')
    require(report.get('coverage_review_recorder_additions')==str(OVERLAY_REL).removeprefix('docs/evidence/'),'recorder evidence binding drift')
    require(report.get('scoped_review_paths')==294 and report.get('grouped_revalidated_paths')==113 and report.get('semantically_classified_paths')==407,'current report accounting drift')
    summary=vr.read_json(audit_root/'docs/evidence/organization-audit-20260907/coverage-summary.json')
    require(summary.get('ledger_sha256')==CURRENT_LEDGER_SHA,'current ledger digest drift')
    require(summary.get('scoped_review_paths')==294 and summary.get('grouped_revalidated_paths')==113 and summary.get('unverified_semantics_total')==3918 and summary.get('semantically_classified_paths')==407,'current summary accounting drift')
    platform=summary['per_repository']['platform']
    require(platform=={'leaves':2165,'direct_scoped':168,'unverified_semantics':1884,'grouped':113,'not_applicable':0},'current Platform accounting drift')

    base=report_path.parent/report['evidence_directory']
    review=vr.load_review(base,report)
    require(len(review)==294,'current composed DIRECT count drift')
    by_path={(row['repository'],row['path']):row for row in review}
    old_by_path={(row['repository'],row['path']):row for row in old_rows}
    for key, expected in old_by_path.items():
        current=by_path.get(key)
        require(current is not None,'recorder missing from current canonical composition: '+key[1])
        require(vr.json_exact(current,expected),'recorder complete current canonical row drift: '+key[1])


def validate_source(candidate: dict, platform_root: Path) -> None:
    require(git(platform_root,'rev-parse','HEAD')==SOURCE_COMMIT,'frozen Platform commit drift')
    require(git(platform_root,'rev-parse','HEAD^{tree}')==SOURCE_TREE,'frozen Platform tree drift')
    for row in candidate['paths']:
        require(tree_blob(platform_root,row['path'])==row['blob_sha'],'recorder source blob drift: '+row['path'])
        validate_source_text(row['path'],git(platform_root,'show','HEAD:'+row['path']),row)
    for dep in candidate['persistence_contract']:
        require(tree_blob(platform_root,dep['path'])==dep['blob_sha'],'recorder persistence blob drift: '+dep['path'])
    for test in candidate['focused_current_tests']:
        require(tree_blob(platform_root,test['path'])==test['blob_sha'],'recorder focused-test blob drift: '+test['path'])
        require(test['required_text'] in git(platform_root,'show','HEAD:'+test['path']),'recorder focused-test oracle drift: '+test['path'])


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--audit-root',type=Path,default=Path('.'))
    parser.add_argument('--platform-root',type=Path,required=True)
    args=parser.parse_args()
    candidate=expected_candidate(args.audit_root)
    validate_adopted_docs(candidate,args.audit_root)
    validate_source(candidate,args.platform_root)
    print(json.dumps({
        'result':'AUDIT_RECORDERS_DIRECT_EVIDENCE_PRESERVED_IN_CURRENT_CANONICAL_COMPOSITION',
        'recorder_paths':2,
        'current_direct_paths':294,
        'current_grouped_paths':113,
        'current_unverified_paths':3918,
        'current_semantically_classified_paths':407,
        'current_ledger_sha256':CURRENT_LEDGER_SHA,
        'independent_review_required':False,
        'review_provenance':REVIEW_PROVENANCE,
        'product_readiness_claimed':False,
        'audit_completion_claimed':False,
    },sort_keys=True))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
