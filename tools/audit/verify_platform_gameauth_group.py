#!/usr/bin/env python3
"""Fail-closed revalidation for the Platform app/GameAuth historical direct-read carry-forward.

Read-only. The tool verifies exact historical evidence identity, byte-identical source carry-forward,
the complete frozen-current dependent contract set, and—after adoption—the exact qualification records
that justified GROUPED coverage. It does not claim Platform or organization product readiness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

CANDIDATE = Path('docs/evidence/organization-audit-20260907/r3-platform-gameauth-candidate.json')
GROUPS = Path('docs/evidence/organization-audit-20260907/coverage-groups.json')
PENDING = 'CANDIDATE_PENDING_QUALIFICATION'
ADOPTED = 'QUALIFIED_ADOPTED_AS_GROUPED'
OUTCOME = 'ADOPTED_GROUPED_CARRY_FORWARD'

FOCUSED_TEST_FILES = (
    'tests/Feature/GameAuth/EnsureGameWorldCommandTest.php',
    'tests/Feature/GameAuth/GameAuthRevocationTest.php',
    'tests/Feature/GameAuth/GameLoginContextApiTest.php',
    'tests/Feature/GameAuth/GameLoginTicketApiTest.php',
    'tests/Feature/GameAuth/GameLoginTicketLifecycleTest.php',
    'tests/Feature/GameAuth/GameLoginTicketRedeemApiTest.php',
    'tests/Feature/GameAuth/NativeProtocolIdentityMigrationTest.php',
    'tests/Feature/GameAuth/OAuth/NativeOAuthClientManagerTest.php',
    'tests/Feature/GameAuth/OAuth/NativeOAuthGrantPolicyTest.php',
    'tests/Feature/GameAuth/OAuth/NativeOAuthPkceTest.php',
    'tests/Feature/GameAuth/OAuth/NativeOAuthRevocationGenerationTest.php',
    'tests/Feature/GameAuth/OAuth/PublicClientPkcePolicyTest.php',
    'tests/Feature/GameAuth/WorldRegistryTest.php',
    'tests/Unit/Http/Middleware/PreventSensitiveGameAuthResponseCachingTest.php',
)
NON_TEST_DEPENDENCIES = (
    'bootstrap/app.php',
    'config/game-auth.php',
    'config/auth.php',
    'config/database.php',
    'routes/api.php',
    'routes/internal.php',
    'composer.json',
    'composer.lock',
    'phpunit.xml',
)
EXPECTED_DEPENDENT_PATHS = frozenset(NON_TEST_DEPENDENCIES + FOCUSED_TEST_FILES)
PRIMARY_QUALIFICATION = {
    'qualification_head': '261c3838cd4806ef29bd9e0e1808049be4bdf809',
    'workflow_run': 34225490543,
    'job': 102058467962,
    'verifier_unit_tests': 5,
    'verifier_unit_result': 'PASS',
    'focused_current_tests': {
        'test_files': 14,
        'cases': 61,
        'assertions': 565,
        'failures': 0,
        'errors': 0,
        'skipped': 0,
    },
    'php': '8.5.10',
    'composer_validate': 'PASS',
    'tracked_source_clean_after_execution': True,
    'existing_exact_source_concurrency_artifact': 10035749457,
    'outcome': OUTCOME,
}
POST_ADOPTION = {
    'audit_head': '34c037154d1861ab0f1995ce4dc3ee9a36ebbb65',
    'workflow_run': 34227110039,
    'job': 102063808556,
    'result': 'PASS',
    'canonical_group_state': 'GAMEAUTH_GROUPED_ADOPTION_REVALIDATED_NOT_PRODUCT_PASS',
    'focused_current_tests': {
        'cases': 61,
        'assertions': 565,
        'failures': 0,
        'errors': 0,
        'skipped': 0,
    },
    'meta_ci_run': 34227109946,
    'meta_ci_result': 'SUCCESS',
}
GROUP_FOCUSED_RESULT = {
    'cases': 61,
    'assertions': 565,
    'failures': 0,
    'errors': 0,
    'skipped': 0,
}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def json_exact(left, right) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(json_exact(left[key], right[key]) for key in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(json_exact(a, b) for a, b in zip(left, right))
    return left == right


def read_json(path: Path):
    def pairs(items):
        out = {}
        for key, value in items:
            require(key not in out, 'duplicate JSON key')
            out[key] = value
        return out
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=pairs)


def git(root: Path, *args: str) -> bytes:
    return subprocess.run(
        ['git', '-C', str(root), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
    ).stdout


def text(root: Path, *args: str) -> str:
    return git(root, *args).decode().strip()


def blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def recursive_entries(root: Path, ref: str, prefix: str):
    raw = git(root, 'ls-tree', '-rz', '--full-tree', '-r', ref, '--', prefix)
    rows = []
    for item in raw.split(b'\0'):
        if not item:
            continue
        meta, path = item.split(b'\t', 1)
        mode, kind, oid = meta.decode().split(' ')
        rows.append((path.decode(), mode, kind, oid))
    return rows


def verify(audit_root: Path, platform_root: Path, evidence_root: Path):
    candidate = read_json(audit_root / CANDIDATE)
    require(type(candidate.get('schema_version')) is int and candidate['schema_version'] == 1, 'candidate schema')
    state = candidate.get('state')
    require(state in {PENDING, ADOPTED}, 'candidate state')
    adopted = state == ADOPTED
    require(type(candidate.get('coverage_adopted')) is bool, 'candidate adoption type')
    require(candidate['coverage_adopted'] is adopted, 'candidate adoption/state mismatch')
    require(candidate.get('repository') == 'Oteryn/Oteryn-Platform', 'candidate repository')
    require(candidate.get('path_prefix') == 'app/GameAuth/', 'candidate prefix')
    require(type(candidate.get('expected_count')) is int and candidate['expected_count'] == 27, 'candidate count')

    hist = candidate['historical_evidence']
    current = candidate['current_revalidation']
    require(hist.get('repository') == 'Oteryn/Oteryn-Platform', 'historical repository')

    require(text(platform_root, 'rev-parse', 'HEAD') == current['source_commit'], 'wrong frozen Platform source')
    require(text(platform_root, 'rev-parse', 'HEAD^{tree}') == current['source_tree'], 'wrong frozen Platform tree')
    require(text(evidence_root, 'rev-parse', 'HEAD') == hist['publication_commit'], 'wrong Platform audit publication commit')
    require(text(evidence_root, 'rev-parse', 'HEAD^{tree}') == hist['publication_tree'], 'wrong Platform audit publication tree')
    require(text(platform_root, 'rev-parse', hist['audited_main_sha'] + '^{tree}') == hist['audited_main_tree'], 'wrong historical Platform source tree')

    evidence_path = evidence_root / hist['coverage_rules_path']
    require(evidence_path.is_file() and not evidence_path.is_symlink(), 'historical evidence path invalid')
    evidence_raw = evidence_path.read_bytes()
    require(blob_sha(evidence_raw) == hist['coverage_rules_blob'], 'historical evidence blob mismatch')
    statement = hist['exact_statement']
    require(evidence_raw.decode('utf-8').count(statement) == 1, 'historical all-27 direct-read statement missing/duplicated')
    require(hist['pattern'] == candidate['path_prefix'] + '**' and hist['count'] == candidate['expected_count'], 'historical scope mismatch')

    historical_app = text(platform_root, 'rev-parse', hist['audited_main_sha'] + ':app')
    current_app = text(platform_root, 'rev-parse', current['source_commit'] + ':app')
    require(historical_app == current['historical_app_tree'], 'historical app tree mismatch')
    require(current_app == current['current_app_tree'], 'current app tree mismatch')
    require(historical_app == current_app, 'app tree changed across carry-forward interval')

    historical_group_tree = text(platform_root, 'rev-parse', hist['audited_main_sha'] + ':app/GameAuth')
    current_group_tree = text(platform_root, 'rev-parse', current['source_commit'] + ':app/GameAuth')
    require(current_group_tree == current['gameauth_tree'], 'current GameAuth tree mismatch')
    require(historical_group_tree == current_group_tree, 'GameAuth tree changed across carry-forward interval')

    old = recursive_entries(platform_root, hist['audited_main_sha'], candidate['path_prefix'])
    now = recursive_entries(platform_root, current['source_commit'], candidate['path_prefix'])
    require(len(old) == len(now) == candidate['expected_count'], 'GameAuth leaf count mismatch')
    require(old == now, 'GameAuth path/blob identity changed')
    require(all(mode == '100644' and kind == 'blob' for _, mode, kind, _ in now), 'GameAuth group contains non-regular leaf')

    changed = git(
        platform_root,
        'diff', '--name-only', hist['audited_main_sha'], current['source_commit'], '--', candidate['path_prefix'],
    ).decode().splitlines()
    require(changed == [], 'GameAuth diff not empty: ' + repr(changed[:10]))
    require(type(current.get('changed_paths_under_group_prefix')) is int and current['changed_paths_under_group_prefix'] == 0, 'candidate changed-path declaration')

    current_blobs = current.get('current_blobs')
    require(isinstance(current_blobs, dict), 'current dependent blob map')
    require(set(current_blobs) == EXPECTED_DEPENDENT_PATHS, 'current dependent blob path set must be exact 23 bindings')
    require(len(current_blobs) == 23, 'current dependent blob count must be 23')
    for path in sorted(EXPECTED_DEPENDENT_PATHS):
        expected = current_blobs[path]
        require(isinstance(expected, str) and len(expected) == 40, 'dependent blob SHA shape: ' + path)
        actual = text(platform_root, 'rev-parse', current['source_commit'] + ':' + path)
        require(actual == expected, 'frozen-current dependent blob mismatch: ' + path)

    tests = current.get('focused_test_files')
    require(isinstance(tests, list) and tuple(tests) == FOCUSED_TEST_FILES, 'focused test set/order must match exact 14-file qualification')
    require(set(tests).issubset(current_blobs), 'every focused test must be blob-bound')

    groups_doc = read_json(audit_root / GROUPS)
    accepted = [row for row in groups_doc.get('groups', []) if row.get('id') == candidate['candidate_id']]
    if adopted:
        qualification = candidate.get('qualification')
        require(isinstance(qualification, dict), 'adopted candidate qualification missing')
        qualification_without_post = dict(qualification)
        post = qualification_without_post.pop('post_adoption_revalidation', None)
        require(json_exact(qualification_without_post, PRIMARY_QUALIFICATION), 'candidate primary qualification must equal exact bound run/result')
        require(json_exact(post, POST_ADOPTION), 'candidate post-adoption qualification must equal exact bound run/result')

        require(len(accepted) == 1, 'adopted candidate missing/duplicated canonical group')
        group = accepted[0]
        require(group.get('repository') == 'platform', 'adopted group repository')
        require(group.get('disposition') == 'GROUPED', 'adopted group disposition')
        require(group.get('depth') == 'GROUPED_REVALIDATED', 'adopted group depth')
        require(group.get('path_prefix') == candidate['path_prefix'], 'adopted group prefix')
        require(group.get('expected_count') == candidate['expected_count'], 'adopted group count')
        require(json_exact(group.get('historical_evidence'), hist), 'adopted group historical evidence drift')
        require(json_exact(group.get('current_revalidation'), current), 'adopted group current evidence drift')

        evaluation = group.get('evaluation')
        require(isinstance(evaluation, dict), 'adopted group evaluation missing')
        require(evaluation.get('qualification_head') == PRIMARY_QUALIFICATION['qualification_head'], 'adopted qualification head')
        require(type(evaluation.get('qualification_run')) is int and evaluation['qualification_run'] == PRIMARY_QUALIFICATION['workflow_run'], 'adopted qualification run')
        require(type(evaluation.get('qualification_job')) is int and evaluation['qualification_job'] == PRIMARY_QUALIFICATION['job'], 'adopted qualification job')
        require(type(evaluation.get('verifier_unit_tests')) is int and evaluation['verifier_unit_tests'] == 5, 'adopted verifier unit count')
        require(json_exact(evaluation.get('focused_current_tests'), GROUP_FOCUSED_RESULT), 'adopted focused result must be exact 61/565 all-green')
        require(type(evaluation.get('existing_exact_source_concurrency_artifact')) is int and evaluation['existing_exact_source_concurrency_artifact'] == 10035749457, 'adopted concurrency artifact')
        require(evaluation.get('outcome') == OUTCOME, 'adopted group outcome')
        require(json_exact(evaluation.get('post_adoption_revalidation'), POST_ADOPTION), 'adopted post-revalidation must equal exact bound run/result')
        result = 'GAMEAUTH_GROUPED_ADOPTION_REVALIDATED_NOT_PRODUCT_PASS'
        next_gate = 'retain bounded GROUPED evidence; broader Platform and organization assurance remains open'
    else:
        require(accepted == [], 'pending candidate already present in accepted groups')
        require('qualification' not in candidate, 'pending candidate must not carry adoption qualification')
        result = 'GAMEAUTH_IDENTITY_AND_HISTORICAL_DIRECT_EVIDENCE_REVALIDATED_TESTS_STILL_REQUIRED'
        next_gate = 'focused frozen-current tests must pass before GROUPED adoption'

    return {
        'result': result,
        'candidate_id': candidate['candidate_id'],
        'historical_source': hist['audited_main_sha'],
        'current_source': current['source_commit'],
        'paths': len(now),
        'path_blob_identity': True,
        'historical_direct_read_statement_bound': True,
        'dependent_blobs_verified': len(current_blobs),
        'focused_test_files_bound': len(tests),
        'coverage_adopted': adopted,
        'next_gate': next_gate,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit-root', type=Path, required=True)
    parser.add_argument('--platform-root', type=Path, required=True)
    parser.add_argument('--evidence-root', type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.audit_root.resolve(), args.platform_root.resolve(), args.evidence_root.resolve())
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
