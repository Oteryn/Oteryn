#!/usr/bin/env python3
"""Fail-closed canonical-adoption verifier for frozen Platform app/Announcements/**."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import verify_platform_announcements_direct as pre
import verify_report as vr

ANNOUNCEMENTS_OVERLAY_REL = Path('docs/evidence/organization-audit-20260907/coverage-review-announcements-additions.tsv')
ANNOUNCEMENTS_OVERLAY_BLOB = '7822ad14cb7c9311267fd7bbf52490ca320762e9'
ANNOUNCEMENTS_OVERLAY_SHA256 = '5e9b4832b886cf9049f49be00fa32b76abab5b896e63a1711688c47fb5addcb2'
CANONICAL_LEDGER_SHA = '73c458b8e1b2a6a5cf02bedbefec8fe3a11d4f883413ef65f6d8dd56952338f9'
EXPECTED_LINE_RANGES = {
    'app/Announcements/Actions/SaveAnnouncement.php': '[[1,134]]',
    'app/Announcements/Factories/SiteAnnouncementFactory.php': '[[1,33]]',
    'app/Announcements/Http/AdminAnnouncementController.php': '[[1,105]]',
    'app/Announcements/Http/AnnouncementRequest.php': '[[1,51]]',
    'app/Announcements/Links/AnnouncementActionLink.php': '[[1,49]]',
    'app/Announcements/Models/SiteAnnouncement.php': '[[1,100]]',
    'app/Announcements/Queries/ActiveAnnouncementQuery.php': '[[1,67]]',
    'app/Announcements/Queries/AnnouncementTickerProvider.php': '[[1,40]]',
    'app/Announcements/ViewModels/AnnouncementTicker.php': '[[1,21]]',
    'app/Announcements/ViewModels/AnnouncementTickerState.php': '[[1,10]]',
}
EXECUTION_EVIDENCE_BASE = ('Primary qualification: GitHub Actions run 34380399141, job 102563546379, '
    'artifact 10115614293 (SHA-256 eb577820be531bfbb5451cf8d964ffeb6a78eeb47d06c36c872ab2e04637141f), '
    'MariaDB 11.8.9; AnnouncementsModuleTest 4 cases / 20 assertions / 0 failures / 0 errors / 0 skips. '
    'Projection run 34381252145 proved this path is one of exactly ten UNVERIFIED-to-DIRECT changes; '
    'bounded evidence only.')
EXPECTED_EXECUTION_EVIDENCE = {
    path: EXECUTION_EVIDENCE_BASE + (
        ' The Polish editorial_translations join branch remains a stated execution limitation.'
        if path == 'app/Announcements/Queries/ActiveAnnouncementQuery.php' else '')
    for path in EXPECTED_LINE_RANGES
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(raw)).encode('ascii') + b'\0' + raw).hexdigest()


def read_tsv(path: Path) -> list[dict[str,str]]:
    with path.open(encoding='utf-8',newline='') as handle:
        reader=csv.DictReader(handle,delimiter='\t')
        require(reader.fieldnames is not None and len(reader.fieldnames)==len(set(reader.fieldnames)),'Announcements overlay header drift')
        rows=list(reader)
    require(rows and all(None not in row and None not in row.values() for row in rows),'Announcements overlay row drift')
    return rows


def validate_adopted_docs(candidate: dict, audit_root: Path) -> None:
    pre.validate_candidate_shape(candidate)
    require(candidate['coverage_adopted'] is False,'historical pre-adoption candidate must remain immutable')
    require(candidate['projection']['status']=='PROJECTION_SUCCESS_NOT_ADOPTED','projection provenance drift')
    require(candidate['projection']['projected_ledger_sha256']==CANONICAL_LEDGER_SHA,'projected ledger provenance drift')
    require(candidate['projection']['generated_overlay_sha256']==ANNOUNCEMENTS_OVERLAY_SHA256,'projected overlay provenance drift')

    overlay_path=audit_root/ANNOUNCEMENTS_OVERLAY_REL
    raw=overlay_path.read_bytes()
    require(git_blob_sha(raw)==ANNOUNCEMENTS_OVERLAY_BLOB,'Announcements evidence overlay Git blob drift')
    require(hashlib.sha256(raw).hexdigest()==ANNOUNCEMENTS_OVERLAY_SHA256,'Announcements evidence overlay SHA-256 drift')
    ann_rows=read_tsv(overlay_path)
    require(len(ann_rows)==10,'Announcements evidence overlay must contain exactly ten rows')
    candidate_by_path={row['path']:row for row in candidate['paths']}
    require([row['path'] for row in ann_rows]==list(candidate_by_path),'Announcements overlay path order/set drift')
    for row in ann_rows:
        expected=candidate_by_path[row['path']]
        require(row['repository']=='platform','Announcements overlay repository drift')
        require(row['blob_sha']==expected['blob_sha'],'Announcements overlay blob drift: '+row['path'])
        require(row['depth']==expected['depth'],'Announcements overlay depth drift: '+row['path'])
        require(row['scope']==expected['scope'],'Announcements overlay scope drift: '+row['path'])
        require(row['line_ranges']==EXPECTED_LINE_RANGES[row['path']],'Announcements overlay line-range drift: '+row['path'])
        require('4 cases / 20 assertions / 0 failures / 0 errors / 0 skips' in row['execution_evidence'],'Announcements execution provenance drift: '+row['path'])
        require('whole-product readiness' in row['limitations'] and 'independent score' in row['limitations'],'Announcements limitations drift: '+row['path'])

    report_path=audit_root/'docs/evidence/OTERYN-ORGANIZATION-COMPREHENSIVE-AUDIT-20260907.json'
    report=vr.read_json(report_path)
    require(report.get('revision')=='R3-NATIVE-EVIDENCE-POST-REVIEW-PLATFORM-SEMANTIC-CARRYFORWARD-113-DIRECT-233','report revision drift')
    require(report.get('coverage_review_additions')==vr.DIRECT_ADDITIONS_BINDING,'canonical additions binding drift')
    require(report.get('coverage_review_announcements_additions')==vr.ANNOUNCEMENTS_ADDITIONS_BINDING,'Announcements evidence binding drift')
    require(report.get('r3_platform_announcements_direct_candidate')=='organization-audit-20260907/r3-platform-announcements-direct-candidate.json','Announcements candidate binding drift')
    require(report.get('scoped_review_paths')==233 and report.get('grouped_revalidated_paths')==113 and report.get('semantically_classified_paths')==346,'report accounting drift')

    summary=vr.read_json(audit_root/'docs/evidence/organization-audit-20260907/coverage-summary.json')
    require(summary.get('ledger_sha256')==CANONICAL_LEDGER_SHA,'canonical ledger digest drift')
    require(summary.get('scoped_review_paths')==233 and summary.get('grouped_revalidated_paths')==113 and summary.get('unverified_semantics_total')==3979 and summary.get('semantically_classified_paths')==346,'summary accounting drift')
    require(summary['per_repository']['platform']=={'leaves':2165,'direct_scoped':168,'unverified_semantics':1884,'grouped':113,'not_applicable':0},'Platform summary drift')

    base=report_path.parent/report['evidence_directory']
    review=vr.load_review(base,report)
    require(len(review)==233,'canonical DIRECT count drift')
    canonical={(row['repository'],row['path']):row for row in review}
    for row in ann_rows:
        current=canonical.get(('platform',row['path']))
        require(current is not None,'Announcements path missing from canonical composition: '+row['path'])
        for key in ('blob_sha','depth','scope','line_ranges'):
            require(current[key]==row[key],'Announcements canonical row drift: '+row['path']+': '+key)
        require(current['execution_evidence']==EXPECTED_EXECUTION_EVIDENCE[row['path']],
                'Announcements canonical row drift: '+row['path']+': execution_evidence')


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--audit-root',type=Path,default=Path('.'))
    parser.add_argument('--platform-root',type=Path,required=True)
    args=parser.parse_args()
    candidate=pre.read_json(args.audit_root/pre.CANDIDATE_REL)
    pre.validate_candidate_shape(candidate)
    pre.validate_source(candidate,args.platform_root)
    validate_adopted_docs(candidate,args.audit_root)
    print(json.dumps({
        'result':'ANNOUNCEMENTS_DIRECT_CANONICAL_ADOPTION_VALID_PENDING_POST_PROOF_AND_INDEPENDENT_REVIEW',
        'source_commit':pre.SOURCE_COMMIT,
        'adopted_paths':10,
        'direct_paths':233,
        'grouped_paths':113,
        'unverified_paths':3979,
        'semantically_classified_paths':346,
        'ledger_sha256':CANONICAL_LEDGER_SHA,
        'primary_cases':4,
        'primary_assertions':20,
        'polish_locale_join_directly_executed':False,
        'dedicated_simultaneous_writer_race_executed':False,
        'independent_review_required':True,
        'product_readiness_claimed':False,
        'audit_completion_claimed':False,
    },sort_keys=True))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
