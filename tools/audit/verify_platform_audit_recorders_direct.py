#!/usr/bin/env python3
"""Fail-closed verifier for the adopted two-file frozen Platform audit-recorder DIRECT slice.

The verifier binds frozen source/persistence/test identities, the exact two-row
DIRECT overlay, canonical accounting and both pre/post-adoption execution proof.
A successful result is bounded audit evidence only, never product readiness.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

CANDIDATE_REL = Path('docs/evidence/organization-audit-20260907/r3-platform-audit-recorders-direct-candidate.json')
REPORT_REL = Path('docs/evidence/OTERYN-ORGANIZATION-COMPREHENSIVE-AUDIT-20260907.json')
SUMMARY_REL = Path('docs/evidence/organization-audit-20260907/coverage-summary.json')
OVERLAY_REL = Path('docs/evidence/organization-audit-20260907/coverage-review-additions.tsv')
SOURCE_COMMIT = 'de917b3477a1de0667531380de3660e8b2ab59aa'
SOURCE_TREE = 'ffdf2a286d3a39f2344cf2ff53b28e4ef7369a8e'
LEDGER_SHA = '2d823435f76f0c08b118ccb5dc1c9ccf9ef4acc41bffdd447b260e82ea404b0f'
OVERLAY_BLOB = '9b5c1afc0d1ac39641077510fb4d6c20222e04d5'
EXPECTED_PATHS = {
    'app/Audit/AdminAuditRecorder.php': '78a757d143036aa4c9c13e40c96a9f1fb66cb6a4',
    'app/Audit/SecurityEventRecorder.php': 'cdf63637dc6902f575abceeaa106525173f08e5f',
}
EXPECTED_PERSISTENCE = {
    'database/migrations/2026_07_20_093300_create_admin_audit_events_table.php': '7ec89faee81a5e6ecd80a741f39e967389838044',
    'database/migrations/2026_07_19_073601_create_identity_security_events_table.php': '783b83a4c735117f4efbbe94f217c603b2a90815',
}
EXPECTED_TESTS = {
    'tests/Feature/Admin/AdminRoleManagementTest.php': '05bcee51c5a7abd3ddc90cb675db74a768429aa1',
    'tests/Feature/Identity/RegistrationTest.php': 'cfb79eeed2ad544166e35724c0ad5cd220c61862',
    'tests/Feature/GameAuth/GameLoginTicketLifecycleTest.php': '1fdf519959d61086f2c32e2415761a4a53369ab4',
}
SHA = re.compile(r'[0-9a-f]{40}\Z')


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_json(path: Path) -> dict:
    def pairs(items):
        out = {}
        for key, value in items:
            require(key not in out, 'duplicate JSON key: ' + key)
            out[key] = value
        return out
    value = json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=pairs)
    require(isinstance(value, dict), 'JSON root must be object')
    return value


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ['git', '-c', 'core.hooksPath=/dev/null', *args], cwd=cwd, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60,
    ).stdout.strip()


def tree_blob(cwd: Path, path: str) -> str:
    raw = git(cwd, 'ls-tree', 'HEAD', '--', path)
    require(raw, 'source path absent: ' + path)
    head, actual_path = raw.split('\t', 1)
    mode, kind, oid = head.split(' ')
    require(actual_path == path and mode == '100644' and kind == 'blob' and SHA.fullmatch(oid), 'invalid tree entry: ' + path)
    return oid


def blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def validate_candidate_shape(c: dict) -> None:
    require(c.get('schema_version') == 1, 'candidate schema')
    require(c.get('id') == 'platform-audit-recorders-direct-20260909', 'candidate id')
    require(c.get('repository') == 'platform', 'candidate repository')
    require(c.get('disposition') == 'DIRECT_ADOPTED_POST_PROOF_COMPLETE_PENDING_INDEPENDENT_REVIEW', 'candidate disposition')
    require(c.get('coverage_adopted') is True, 'candidate must be adopted')
    require(c.get('source') == {'repository': 'Oteryn/Oteryn-Platform', 'commit_sha': SOURCE_COMMIT, 'tree_sha': SOURCE_TREE}, 'source coordinates')

    paths = c.get('paths') or []
    require(isinstance(paths, list) and len(paths) == 2, 'exactly two DIRECT paths required')
    require({row.get('path'): row.get('blob_sha') for row in paths} == EXPECTED_PATHS, 'candidate path/blob set drift')
    for row in paths:
        require(row.get('depth') == 'SCOPED_SEMANTIC_REVIEW', 'candidate depth')
        require(isinstance(row.get('scope'), str) and row['scope'].strip(), 'candidate scope')
        require(row.get('line_ranges') == [], 'full-file review line-range metadata')
        require(isinstance(row.get('semantic_assertions'), list) and row['semantic_assertions'], 'semantic assertions')
    security = next(row for row in paths if row['path'].endswith('SecurityEventRecorder.php'))
    require(security.get('expected_public_event_constants') == 31, 'security constant count oracle')
    require({row.get('path'): row.get('blob_sha') for row in c.get('persistence_contract', [])} == EXPECTED_PERSISTENCE, 'persistence binding drift')
    require({row.get('path'): row.get('blob_sha') for row in c.get('focused_current_tests', [])} == EXPECTED_TESTS, 'focused test binding drift')

    require(c.get('baseline_accounting') == {
        'source_rows': 4325, 'direct_paths': 221, 'grouped_paths': 113, 'unverified_paths': 3991,
        'semantically_classified_paths': 334, 'platform_direct_paths': 156, 'platform_grouped_paths': 113,
        'platform_unverified_paths': 1896, 'ledger_sha256': '25ed5eb371279fbdb16a50263637856a3bc409b775387555efdaa17cebdc3617',
    }, 'baseline accounting drift')
    require(c.get('projected_accounting') == {
        'source_rows': 4325, 'direct_paths': 223, 'grouped_paths': 113, 'unverified_paths': 3989,
        'semantically_classified_paths': 336, 'platform_direct_paths': 158, 'platform_grouped_paths': 113,
        'platform_unverified_paths': 1894, 'ledger_sha256': LEDGER_SHA,
    }, 'projected accounting drift')

    q = c.get('qualification') or {}
    require((q.get('head_sha'), q.get('workflow_run'), q.get('job'), q.get('artifact'), q.get('cases'), q.get('assertions'), q.get('failures'), q.get('errors'), q.get('skipped')) ==
            ('e68726c9590f0ea611871abfbf1bd3238b635c6c', 34347577287, 102452733285, 10102358530, 25, 89, 0, 0, 0), 'primary qualification drift')
    pre = c.get('pre_adoption_exact_head') or {}
    require(pre == {
        'status': 'SUCCESS', 'head_sha': '14b18e00936cbf09884e51bfc4c8eaf121edd715', 'workflow_run': 34348443102,
        'job': 102455526087, 'artifact': 10102677683,
        'artifact_sha256': '0103eca993e0a52d2d9bab834594cb5d63072842bb40f819b34de7d47be7d7a1',
        'meta_ci_run': 34348443175, 'verifier_unit_tests': 12, 'test_files': 3, 'cases': 25, 'assertions': 89,
        'failures': 0, 'errors': 0, 'skipped': 0, 'projected_ledger_sha256': LEDGER_SHA,
    }, 'pre-adoption exact-head evidence drift')
    require(c.get('adoption') == {
        'status': 'ADOPTED_POST_PROOF_COMPLETE_PENDING_INDEPENDENT_REVIEW',
        'direct_overlay_path': str(OVERLAY_REL), 'direct_overlay_blob_sha': OVERLAY_BLOB, 'adopted_paths': 2,
        'source_rows': 4325, 'direct_paths': 223, 'grouped_paths': 113, 'unverified_paths': 3989,
        'semantically_classified_paths': 336, 'ledger_sha256': LEDGER_SHA,
    }, 'adoption state drift')
    require(c.get('post_adoption_revalidation') == {
        'status': 'SUCCESS', 'head_sha': '8d2c412955a283de54c40bec2995a961d2322d9d', 'workflow_run': 34355682587,
        'job': 102479632543, 'artifact': 10105627207,
        'artifact_sha256': 'b0e9f04185f16904dbd6f290e0d559aeb2515512e6bd378a83c5d90524ba7c2e',
        'meta_ci_run': 34355682545, 'verifier_unit_tests': 14, 'cases': 25, 'assertions': 89,
        'ledger_sha256': LEDGER_SHA,
    }, 'post-adoption evidence drift')
    joined = ' '.join(c.get('limitations') or [])
    for phrase in ['not a product or production-readiness PASS', 'not an exhaustive execution', 'fresh independent review of the stable recorder-adoption audit head remains required']:
        require(phrase in joined, 'required limitation missing: ' + phrase)


def validate_source_text(path: str, text: str, row: dict) -> None:
    for token in row['semantic_assertions']:
        require(token in text, f'semantic oracle missing from {path}: {token}')
    if path.endswith('SecurityEventRecorder.php'):
        count = len(re.findall(r'^\s*public const [A-Z0-9_]+\s*=', text, flags=re.MULTILINE))
        require(count == 31, f'security event constant count drift: {count}')


def validate_platform(c: dict, platform_root: Path) -> None:
    require(git(platform_root, 'rev-parse', 'HEAD') == SOURCE_COMMIT, 'Platform HEAD drift')
    require(git(platform_root, 'rev-parse', 'HEAD^{tree}') == SOURCE_TREE, 'Platform tree drift')
    rows = {row['path']: row for row in c['paths']}
    for path, oid in {**EXPECTED_PATHS, **EXPECTED_PERSISTENCE, **EXPECTED_TESTS}.items():
        require(tree_blob(platform_root, path) == oid, 'frozen blob identity drift: ' + path)
    for path, row in rows.items():
        validate_source_text(path, (platform_root / path).read_text(encoding='utf-8'), row)
    admin = (platform_root / 'database/migrations/2026_07_20_093300_create_admin_audit_events_table.php').read_text(encoding='utf-8')
    for token in ["Schema::create('admin_audit_events'", "'actor_identity_id'", "'action', 96", "'target_type', 80", "'target_id', 191", "'metadata'", "'occurred_at'"]:
        require(token in admin, 'admin audit persistence oracle missing: ' + token)
    security = (platform_root / 'database/migrations/2026_07_19_073601_create_identity_security_events_table.php').read_text(encoding='utf-8')
    for token in ["Schema::create('identity_security_events'", "'identity_id'", "'event_type', 100", "'occurred_at'", "['identity_id', 'event_type']"]:
        require(token in security, 'security persistence oracle missing: ' + token)
    for row in c['focused_current_tests']:
        require(row['required_text'] in (platform_root / row['path']).read_text(encoding='utf-8'), 'focused test lost persistence assertion surface: ' + row['path'])


def validate_adopted_docs(c: dict, audit_root: Path) -> None:
    sys.path.insert(0, str((audit_root / 'tools/audit').resolve()))
    import verify_report as vr
    report = vr.read_json(audit_root / REPORT_REL)
    base = (audit_root / REPORT_REL).parent / report['evidence_directory']
    review = vr.load_review(base, report)
    require(len(review) == 223, 'combined DIRECT review count drift')
    by_key = {(row['repository'], row['path']): row for row in review}
    for row in c['paths']:
        actual = by_key.get(('platform', row['path']))
        require(actual is not None, 'adopted DIRECT row missing: ' + row['path'])
        require(actual['blob_sha'] == row['blob_sha'] and actual['depth'] == row['depth'] and actual['scope'] == row['scope'] and actual['line_ranges'] == '[]', 'adopted DIRECT row drift: ' + row['path'])
    overlay = (audit_root / OVERLAY_REL).read_bytes()
    require(blob_sha(overlay) == OVERLAY_BLOB, 'DIRECT overlay blob drift')
    overlay_rows = list(csv.DictReader(overlay.decode('utf-8').splitlines(), delimiter='\t'))
    require(len(overlay_rows) == 2 and {(r['repository'], r['path']) for r in overlay_rows} == {('platform', p) for p in EXPECTED_PATHS}, 'DIRECT overlay membership drift')
    summary = vr.read_json(audit_root / SUMMARY_REL)
    platform = summary['per_repository']['platform']
    require((summary['scoped_review_paths'], summary['grouped_revalidated_paths'], summary['semantically_classified_paths'], summary['unverified_semantics_total']) == (223, 113, 336, 3989), 'summary total drift')
    require((platform['leaves'], platform['direct_scoped'], platform['grouped'], platform['unverified_semantics']) == (2165, 158, 113, 1894), 'Platform summary drift')
    require(summary['ledger_sha256'] == LEDGER_SHA, 'canonical ledger digest drift')
    require(report.get('revision') == 'R3-NATIVE-EVIDENCE-POST-REVIEW-PLATFORM-SEMANTIC-CARRYFORWARD-113-DIRECT-223', 'report revision drift')
    require((report['scoped_review_paths'], report['grouped_revalidated_paths'], report['semantically_classified_paths']) == (223, 113, 336), 'report accounting drift')
    require(report.get('coverage_review_additions') == 'organization-audit-20260907/coverage-review-additions.tsv', 'report overlay binding drift')
    require(report.get('r3_platform_audit_recorders_direct_candidate') == 'organization-audit-20260907/r3-platform-audit-recorders-direct-candidate.json', 'report candidate binding drift')


def run(audit_root: Path, platform_root: Path) -> dict:
    c = read_json(audit_root / CANDIDATE_REL)
    validate_candidate_shape(c)
    validate_adopted_docs(c, audit_root)
    validate_platform(c, platform_root)
    return {
        'result': 'PLATFORM_AUDIT_RECORDERS_DIRECT_POST_PROOF_BOUND_PENDING_INDEPENDENT_REVIEW_NOT_PRODUCT_PASS',
        'source_commit': SOURCE_COMMIT, 'source_tree': SOURCE_TREE, 'paths': 2, 'path_blobs_verified': 2,
        'persistence_bindings_verified': 2, 'focused_test_files_bound': 3, 'security_event_constants_verified': 31,
        'coverage_adopted': True, 'direct_paths': 223, 'grouped_paths': 113, 'unverified_paths': 3989,
        'semantically_classified_paths': 336, 'ledger_sha256': LEDGER_SHA,
        'post_adoption_run': 34355682587, 'post_adoption_job': 102479632543, 'next_gate': 'fresh independent exact-head review',
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit-root', type=Path, required=True)
    parser.add_argument('--platform-root', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.audit_root.resolve(), args.platform_root.resolve()), indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
