#!/usr/bin/env python3
"""Fail-closed pre-adoption verifier for frozen Platform app/Announcements/**.

This proves exact candidate/source identity and binds the completed primary
qualification. It cannot promote coverage: all ten paths remain UNVERIFIED
until a separate projection, adoption, post-adoption proof and independent
review complete.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

CANDIDATE_REL = Path('docs/evidence/organization-audit-20260907/r3-platform-announcements-direct-candidate.json')
CANDIDATE_BLOB = '378b80656470c445a0cae9163d2246615dd039c5'
SOURCE_COMMIT = 'de917b3477a1de0667531380de3660e8b2ab59aa'
SOURCE_TREE = 'ffdf2a286d3a39f2344cf2ff53b28e4ef7369a8e'
BASE_LEDGER_SHA = '2d823435f76f0c08b118ccb5dc1c9ccf9ef4acc41bffdd447b260e82ea404b0f'
SHA = re.compile(r'[0-9a-f]{40}\Z')

EXPECTED_PATH_BLOBS = {
    'app/Announcements/Actions/SaveAnnouncement.php': '63b4c7c6e9da38dbf6b99c51e01fecd922be3866',
    'app/Announcements/Factories/SiteAnnouncementFactory.php': 'bf741e10cd5fca97ae293d170647a5493bb680b4',
    'app/Announcements/Http/AdminAnnouncementController.php': '96b91658faed32cc3207964c0048f9b57e21e3a4',
    'app/Announcements/Http/AnnouncementRequest.php': '8aa14b70116cb6b0afeb715f3772d88d95043e7c',
    'app/Announcements/Links/AnnouncementActionLink.php': '65c3c6608b54d546e41d18aa189cf2c5f0f86d79',
    'app/Announcements/Models/SiteAnnouncement.php': '1895056dc72cd0b3ebcc00d651cf74c743c4ef63',
    'app/Announcements/Queries/ActiveAnnouncementQuery.php': 'ef6551224bc1c8b4c086d4de78d2c36f9b51df5b',
    'app/Announcements/Queries/AnnouncementTickerProvider.php': 'b23de62f34ca34ca8de20832daddeb9421225c15',
    'app/Announcements/ViewModels/AnnouncementTicker.php': '988de28911053d537fa6f227c625834dfcaebd94',
    'app/Announcements/ViewModels/AnnouncementTickerState.php': 'efdc1ec91195071d98a4dfc7b625440afa14a5f2',
}
EXPECTED_DEPENDENCIES = [
    ('database/migrations/2026_07_24_211000_create_site_announcements_table.php', '0572122fee5a7a8cc7c952195668620252e98fd8', "Schema::create('site_announcements'", 'PERSISTENCE_DEPENDENCY_NOT_PROMOTED_BY_THIS_CANDIDATE'),
    ('database/migrations/2026_07_25_090000_create_editorial_translations_table.php', '7823a9f38615add49e4a42d90e840a8377841df5', "Schema::create('editorial_translations'", 'LOCALE_QUERY_DEPENDENCY_NOT_PROMOTED_BY_THIS_CANDIDATE'),
    ('app/Cms/Editorial/EditorialContentType.php', '8e8567d6368b74b73c359d9e82e977acbd7d96f4', "case SiteAnnouncement = 'site_announcement';", 'LOCALE_QUERY_DEPENDENCY_NOT_PROMOTED_BY_THIS_CANDIDATE'),
    ('routes/modules/announcements.php', '452bb9ee7b70b03951ab7c2476dd10e437549c2b', 'admin.permission:portal.announcements.manage', 'ROUTING_DEPENDENCY_NOT_PROMOTED_BY_THIS_CANDIDATE'),
    ('routes/web.php', '339e7573b2bc04c7bdd9183cd739c099448d8421', 'foreach ($moduleRouteFiles as $moduleRouteFile) {', 'ROUTE_MODULE_LOADING_DEPENDENCY_NOT_PROMOTED_BY_THIS_CANDIDATE'),
    ('resources/views/announcements/components/ticker.blade.php', 'b5ca83d179ac5dfeb90678f08f3487d242cae478', 'rel="noopener noreferrer"', 'RENDERING_DEPENDENCY_NOT_PROMOTED_BY_THIS_CANDIDATE'),
    ('app/Audit/AdminAuditRecorder.php', '78a757d143036aa4c9c13e40c96a9f1fb66cb6a4', 'final class AdminAuditRecorder', 'ALREADY_DIRECT_AUDIT_DEPENDENCY_NOT_REPROMOTED'),
]
EXPECTED_TEST_PATH = 'tests/Feature/Announcements/AnnouncementsModuleTest.php'
EXPECTED_TEST_BLOB = 'c99570386714f709e8b509b389a2b84aecff460e'
EXPECTED_TEST_METHODS = [
    'test_active_query_uses_inclusive_start_and_exclusive_end_boundaries',
    'test_ticker_provider_exposes_explicit_state_and_escapes_plain_text_content',
    'test_admin_mutation_requires_exact_permission_audits_and_rejects_unsafe_links',
    'test_stale_edit_fails_with_conflict_and_mfa_is_not_bypassed',
]
EXPECTED_BASELINE = {
    'source_rows': 4325, 'direct_paths': 223, 'grouped_paths': 113,
    'unverified_paths': 3989, 'semantically_classified_paths': 336,
    'platform_direct_paths': 158, 'platform_grouped_paths': 113,
    'platform_unverified_paths': 1894, 'ledger_sha256': BASE_LEDGER_SHA,
}
EXPECTED_QUALIFICATION = {
    'status': 'PRIMARY_QUALIFICATION_SUCCESS', 'mariadb_image': 'mariadb:11.8.9',
    'db_connection': 'mysql', 'db_port': 3306, 'test_files': 1,
    'expected_cases': 4, 'exact_assertions': 20,
    'required_failures': 0, 'required_errors': 0, 'required_skips': 0,
    'primary_audit_head': '0e132f9dc453e5d6784ae5c4c80f2d0330573409',
    'primary_run_id': 34380399141,
    'primary_job_id': 102563546379,
    'primary_artifact_id': 10115614293,
    'primary_artifact_sha256': 'eb577820be531bfbb5451cf8d964ffeb6a78eeb47d06c36c872ab2e04637141f',
}


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
    require(isinstance(value, dict), 'candidate root must be object')
    return value


def canonical_blob(candidate: dict) -> str:
    raw = (json.dumps(candidate, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
    framed = b'blob ' + str(len(raw)).encode('ascii') + b'\0' + raw
    return hashlib.sha1(framed).hexdigest()


def validate_candidate_shape(candidate: dict) -> None:
    # The Git blob pin makes the complete ordered/type-sensitive candidate immutable,
    # while the explicit assertions below document the safety boundary.
    require(canonical_blob(candidate) == CANDIDATE_BLOB, 'candidate complete content drift')
    require(candidate['schema_version'] == 1 and type(candidate['schema_version']) is int, 'schema version drift')
    require(candidate['id'] == 'platform-announcements-direct-candidate-20260909', 'candidate id drift')
    require(candidate['repository'] == 'platform', 'repository drift')
    require(candidate['disposition'] == 'DIRECT_CANDIDATE_PRE_ADOPTION', 'candidate disposition drift')
    require(candidate['coverage_adopted'] is False, 'candidate must remain pre-adoption')
    require(candidate['source'] == {'repository': 'Oteryn/Oteryn-Platform', 'commit_sha': SOURCE_COMMIT, 'tree_sha': SOURCE_TREE}, 'source binding drift')
    require([row['path'] for row in candidate['paths']] == list(EXPECTED_PATH_BLOBS), 'candidate path set/order drift')
    require(len(candidate['paths']) == 10, 'candidate must enumerate exactly ten paths')
    require({row['path']: row['blob_sha'] for row in candidate['paths']} == EXPECTED_PATH_BLOBS, 'candidate path blob drift')
    expected_deps = [
        {'path': path, 'blob_sha': blob, 'required_text': text, 'role': role}
        for path, blob, text, role in EXPECTED_DEPENDENCIES
    ]
    require(candidate['dependency_bindings'] == expected_deps, 'candidate dependency binding drift')
    require(candidate['focused_current_tests'] == [{
        'path': EXPECTED_TEST_PATH,
        'blob_sha': EXPECTED_TEST_BLOB,
        'required_methods': EXPECTED_TEST_METHODS,
        'role': 'FOCUSED_EXECUTION_DEPENDENCY_NOT_PROMOTED_BY_THIS_CANDIDATE',
    }], 'candidate focused test binding drift')
    require(candidate['baseline_accounting'] == EXPECTED_BASELINE, 'candidate baseline accounting drift')
    require(candidate['qualification'] == EXPECTED_QUALIFICATION, 'candidate qualification state/provenance drift')
    require(candidate['projection']['status'] == 'NOT_RUN_NO_CANONICAL_CHANGE', 'candidate projection status drift')
    require(candidate['projection']['adopted_paths'] == 0, 'candidate projection must not adopt paths')
    require(candidate['projection']['candidate_paths'] == 10, 'candidate projection path count drift')
    limitations = candidate['limitations']
    require(len(limitations) == 5, 'candidate limitations drift')
    require('remain UNVERIFIED' in limitations[0], 'pre-adoption limitation missing')
    require('does not directly execute the Polish editorial_translations join branch' in limitations[1], 'locale execution limitation missing')
    require('not a dedicated simultaneous-writer race test' in limitations[2], 'concurrency limitation missing')
    require('do not promote their paths' in limitations[3], 'dependency promotion limitation missing')
    require('whole-product readiness' in limitations[4] and 'organization-wide audit completion' in limitations[4], 'readiness limitation missing')


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ['git', '-c', 'core.hooksPath=/dev/null', *args], cwd=cwd, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60,
    ).stdout.strip()


def tree_blob(cwd: Path, path: str) -> str:
    raw = git(cwd, 'ls-tree', 'HEAD', '--', path)
    require(raw, 'source path absent: ' + path)
    head, actual = raw.split('\t', 1)
    mode, kind, oid = head.split(' ')
    require(actual == path and kind == 'blob' and mode.startswith('100'), 'not regular source blob: ' + path)
    require(bool(SHA.fullmatch(oid)), 'invalid source blob oid: ' + path)
    return oid


def source_text(cwd: Path, path: str) -> str:
    return git(cwd, 'show', 'HEAD:' + path)


def validate_source(candidate: dict, platform_root: Path) -> None:
    require(git(platform_root, 'rev-parse', 'HEAD') == SOURCE_COMMIT, 'frozen Platform commit drift')
    require(git(platform_root, 'rev-parse', 'HEAD^{tree}') == SOURCE_TREE, 'frozen Platform tree drift')
    leaves = [line for line in git(platform_root, 'ls-tree', '-r', '--name-only', 'HEAD', '--', 'app/Announcements').splitlines() if line]
    require(leaves == list(EXPECTED_PATH_BLOBS), 'frozen app/Announcements leaf set/order drift')

    for row in candidate['paths']:
        path = row['path']
        require(tree_blob(platform_root, path) == row['blob_sha'], 'source blob drift: ' + path)
        text = source_text(platform_root, path)
        for assertion in row['semantic_assertions']:
            require(assertion in text, 'source semantic assertion absent: ' + path + ': ' + assertion)

    for dep in candidate['dependency_bindings']:
        path = dep['path']
        require(tree_blob(platform_root, path) == dep['blob_sha'], 'dependency blob drift: ' + path)
        require(dep['required_text'] in source_text(platform_root, path), 'dependency required text absent: ' + path)

    test = candidate['focused_current_tests'][0]
    require(tree_blob(platform_root, test['path']) == test['blob_sha'], 'focused test blob drift')
    text = source_text(platform_root, test['path'])
    for method in test['required_methods']:
        require(('function ' + method + '(') in text, 'focused test method absent: ' + method)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--audit-root', type=Path, default=Path('.'))
    parser.add_argument('--platform-root', type=Path, required=True)
    args = parser.parse_args()
    candidate_path = args.audit_root / CANDIDATE_REL
    candidate = read_json(candidate_path)
    validate_candidate_shape(candidate)
    require(git(args.audit_root, 'rev-parse', 'HEAD:' + str(CANDIDATE_REL)) == CANDIDATE_BLOB, 'tracked candidate blob drift')
    validate_source(candidate, args.platform_root)
    print(json.dumps({
        'result': 'ANNOUNCEMENTS_PRIMARY_QUALIFICATION_BOUND_NOT_ADOPTED',
        'source_commit': SOURCE_COMMIT,
        'candidate_paths': 10,
        'coverage_adopted': False,
        'primary_cases': 4,
        'primary_assertions': 20,
        'primary_run_id': 34380399141,
        'primary_job_id': 102563546379,
        'primary_artifact_id': 10115614293,
        'canonical_direct_paths': 223,
        'canonical_grouped_paths': 113,
        'canonical_unverified_paths': 3989,
        'canonical_semantically_classified_paths': 336,
        'canonical_ledger_sha256': BASE_LEDGER_SHA,
        'next_gate': 'mechanical projection only; canonical coverage must remain unchanged until explicit adoption',
        'product_readiness_claimed': False,
        'audit_completion_claimed': False,
    }, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
