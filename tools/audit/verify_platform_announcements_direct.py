#!/usr/bin/env python3
"""Fail-closed pre-adoption verifier for frozen Platform app/Announcements/**.

This verifier proves only candidate identity/source semantics and qualification
prerequisites. It MUST NOT promote coverage: all ten paths remain UNVERIFIED
until a separate projection, adoption, post-adoption proof and independent
review complete.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess

CANDIDATE_REL = Path('docs/evidence/organization-audit-20260907/r3-platform-announcements-direct-candidate.json')
SOURCE_COMMIT = 'de917b3477a1de0667531380de3660e8b2ab59aa'
SOURCE_TREE = 'ffdf2a286d3a39f2344cf2ff53b28e4ef7369a8e'
BASE_LEDGER_SHA = '2d823435f76f0c08b118ccb5dc1c9ccf9ef4acc41bffdd447b260e82ea404b0f'
SHA = re.compile(r'[0-9a-f]{40}\Z')

EXPECTED_TOP_KEYS = {
    'schema_version', 'id', 'repository', 'disposition', 'coverage_adopted',
    'source', 'paths', 'dependency_bindings', 'focused_current_tests',
    'baseline_accounting', 'qualification', 'projection', 'limitations',
}
EXPECTED_PATHS = {
    'app/Announcements/Actions/SaveAnnouncement.php': {
        'blob_sha': '63b4c7c6e9da38dbf6b99c51e01fecd922be3866',
        'scope': 'Full-file bounded review of announcement persistence, optimistic-lock conflict handling, action-link normalization and minimal admin-audit metadata.',
        'assertions': [
            'final class SaveAnnouncement',
            'return DB::transaction(function () use (',
            '->lockForUpdate()',
            "throw new DomainException('This announcement changed after the form was opened. Reload it before saving.');",
            "'portal.announcement_created'", "'portal.announcement_updated'",
            "'has_action' => $current->action_url !== null",
            "'lock_version' => $current->lock_version",
        ],
    },
    'app/Announcements/Factories/SiteAnnouncementFactory.php': {
        'blob_sha': 'bf741e10cd5fca97ae293d170647a5493bb680b4',
        'scope': 'Full-file bounded review of deterministic model factory defaults used by focused qualification.',
        'assertions': [
            'final class SiteAnnouncementFactory extends Factory',
            "'publication_state' => SiteAnnouncement::STATE_PUBLISHED",
            "'lock_version' => 1",
        ],
    },
    'app/Announcements/Http/AdminAnnouncementController.php': {
        'blob_sha': '96b91658faed32cc3207964c0048f9b57e21e3a4',
        'scope': 'Full-file bounded review of admin CRUD handoff, authenticated identity checks, UTC parsing and stale-edit HTTP 409 mapping.',
        'assertions': [
            'final class AdminAnnouncementController',
            'abort_unless($identity instanceof Identity, 403);',
            'throw new ConflictHttpException($exception->getMessage(), $exception);',
            "$request->integer('lock_version')",
        ],
    },
    'app/Announcements/Http/AnnouncementRequest.php': {
        'blob_sha': '8aa14b70116cb6b0afeb715f3772d88d95043e7c',
        'scope': 'Full-file bounded review of input length/state/time/link/lock-version validation; authorization itself is delegated to route middleware.',
        'assertions': [
            'final class AnnouncementRequest extends FormRequest',
            "'title' => ['required', 'string', 'max:200']",
            "'body' => ['required', 'string', 'max:10000']",
            'AnnouncementActionLink::normalize(is_string($value) ? $value : null);',
            "? ['required', 'integer', 'min:1']",
        ],
    },
    'app/Announcements/Links/AnnouncementActionLink.php': {
        'blob_sha': '65c3c6608b54d546e41d18aa189cf2c5f0f86d79',
        'scope': 'Full-file bounded review of internal-path and external-HTTPS action-link normalization boundaries.',
        'assertions': [
            'final class AnnouncementActionLink', 'strlen($link) > 2048',
            "str_starts_with($link, '//') || str_contains($link, '\\\\')",
            "($parts['scheme'] ?? null) !== 'https'", "isset($parts['user'])",
            "isset($parts['pass'])", "$parts['port'] !== 443",
        ],
    },
    'app/Announcements/Models/SiteAnnouncement.php': {
        'blob_sha': '1895056dc72cd0b3ebcc00d651cf74c743c4ef63',
        'scope': 'Full-file bounded review of announcement states, mass-assignable persistence fields, factory binding and typed casts.',
        'assertions': [
            'final class SiteAnnouncement extends Model',
            "public const SEVERITY_MAINTENANCE = 'maintenance';",
            "public const STATE_PUBLISHED = 'published';", "'lock_version',",
            "'lock_version' => 'integer'",
        ],
    },
    'app/Announcements/Queries/ActiveAnnouncementQuery.php': {
        'blob_sha': 'ef6551224bc1c8b4c086d4de78d2c36f9b51df5b',
        'scope': 'Full-file bounded review of active-time/publication filtering, bounded limit, deterministic ordering and Polish editorial-translation freshness join.',
        'assertions': [
            'final class ActiveAnnouncementQuery', 'if ($limit < 1 || $limit > 10)',
            "->where('site_announcements.starts_at', '<=', $readTime)",
            "->orWhere('site_announcements.ends_at', '>', $readTime);",
            "if (app()->getLocale() === 'pl')",
            "->whereColumn($alias.'.source_updated_at', '>=', 'site_announcements.updated_at');",
        ],
    },
    'app/Announcements/Queries/AnnouncementTickerProvider.php': {
        'blob_sha': 'b23de62f34ca34ca8de20832daddeb9421225c15',
        'scope': 'Full-file bounded review of AVAILABLE/EMPTY/UNAVAILABLE state mapping and ticker rendering handoff.',
        'assertions': [
            'final class AnnouncementTickerProvider', 'catch (Throwable)',
            'AnnouncementTickerState::UNAVAILABLE', 'AnnouncementTickerState::EMPTY',
            'AnnouncementTickerState::AVAILABLE', "view('announcements.components.ticker'",
        ],
    },
    'app/Announcements/ViewModels/AnnouncementTicker.php': {
        'blob_sha': '988de28911053d537fa6f227c625834dfcaebd94',
        'scope': 'Full-file bounded review of immutable ticker state/items transport.',
        'assertions': [
            'final readonly class AnnouncementTicker',
            'public AnnouncementTickerState $state', '$this->items = $items;',
        ],
    },
    'app/Announcements/ViewModels/AnnouncementTickerState.php': {
        'blob_sha': 'efdc1ec91195071d98a4dfc7b625440afa14a5f2',
        'scope': 'Full-file bounded review of the exact three ticker availability states.',
        'assertions': [
            'enum AnnouncementTickerState: string', "case AVAILABLE = 'AVAILABLE';",
            "case EMPTY = 'EMPTY';", "case UNAVAILABLE = 'UNAVAILABLE';",
        ],
    },
}
EXPECTED_DEPENDENCIES = [
    ('database/migrations/2026_07_24_211000_create_site_announcements_table.php', '0572122fee5a7a8cc7c952195668620252e98fd8', "Schema::create('site_announcements'", 'PERSISTENCE_DEPENDENCY_NOT_PROMOTED_BY_THIS_CANDIDATE'),
    ('database/migrations/2026_07_25_090000_create_editorial_translations_table.php', '7823a9f38615add49e4a42d90e840a8377841df5', "Schema::create('editorial_translations'", 'LOCALE_QUERY_DEPENDENCY_NOT_PROMOTED_BY_THIS_CANDIDATE'),
    ('app/Cms/Editorial/EditorialContentType.php', '8e8567d6368b74b73c359d9e82e977acbd7d96f4', "case SiteAnnouncement = 'site_announcement';", 'LOCALE_QUERY_DEPENDENCY_NOT_PROMOTED_BY_THIS_CANDIDATE'),
    ('routes/modules/announcements.php', '452bb9ee7b70b03951ab7c2476dd10e437549c2b', 'admin.permission:portal.announcements.manage', 'ROUTING_DEPENDENCY_NOT_PROMOTED_BY_THIS_CANDIDATE'),
    ('routes/web.php', '339e7573b2bc04c7bdd9183cd739c099448d8421', 'foreach ($modules as $module) {', 'ROUTE_MODULE_LOADING_DEPENDENCY_NOT_PROMOTED_BY_THIS_CANDIDATE'),
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
    'status': 'PENDING_PRIMARY_EXECUTION', 'mariadb_image': 'mariadb:11.8.9',
    'db_connection': 'mysql', 'db_port': 3306, 'test_files': 1,
    'expected_cases': 4, 'exact_assertions': 'TO_BE_BOUND_FROM_PRIMARY_RUN',
    'required_failures': 0, 'required_errors': 0, 'required_skips': 0,
}
EXPECTED_PROJECTION = {
    'status': 'NOT_RUN_NO_CANONICAL_CHANGE', 'adopted_paths': 0, 'candidate_paths': 10,
    'expected_delta_if_later_adopted': {
        'direct_paths': 10, 'grouped_paths': 0, 'unverified_paths': -10,
        'semantically_classified_paths': 10,
    },
    'expected_accounting_if_later_adopted': {
        'source_rows': 4325, 'direct_paths': 233, 'grouped_paths': 113,
        'unverified_paths': 3979, 'semantically_classified_paths': 346,
        'platform_direct_paths': 168, 'platform_grouped_paths': 113,
        'platform_unverified_paths': 1884,
    },
}
EXPECTED_LIMITATIONS = [
    'This file is a pre-adoption DIRECT candidate only; all 10 app/Announcements/** paths remain UNVERIFIED in canonical accounting until a separate projection, adoption, post-adoption proof and independent review complete.',
    'The focused AnnouncementsModuleTest executes four representative module cases but does not directly execute the Polish editorial_translations join branch in ActiveAnnouncementQuery.',
    'The focused test proves sequential stale-edit conflict handling on the requested database backend; it is not a dedicated simultaneous-writer race test.',
    'Dependency bindings are qualification context only and do not promote their paths.',
    'No later Platform main, deployment state, whole-product readiness, organization-wide audit completion, or independent score is inferred.',
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def json_exact(left, right) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(json_exact(left[key], right[key]) for key in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(json_exact(a, b) for a, b in zip(left, right))
    return left == right


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
    require(bool(SHA.fullmatch(oid)), 'invalid blob oid: ' + path)
    return oid


def source_text(cwd: Path, path: str) -> str:
    return git(cwd, 'show', 'HEAD:' + path)


def validate_candidate_shape(candidate: dict) -> None:
    require(set(candidate) == EXPECTED_TOP_KEYS, 'candidate top-level keys drift')
    require(type(candidate.get('schema_version')) is int and candidate['schema_version'] == 1, 'schema version drift')
    require(candidate['id'] == 'platform-announcements-direct-candidate-20260909', 'candidate id drift')
    require(candidate['repository'] == 'platform', 'repository drift')
    require(candidate['disposition'] == 'DIRECT_CANDIDATE_PRE_ADOPTION', 'candidate disposition drift')
    require(candidate['coverage_adopted'] is False, 'candidate must remain pre-adoption')
    require(json_exact(candidate['source'], {
        'repository': 'Oteryn/Oteryn-Platform', 'commit_sha': SOURCE_COMMIT, 'tree_sha': SOURCE_TREE,
    }), 'candidate source binding drift')

    rows = candidate['paths']
    require(isinstance(rows, list) and len(rows) == 10, 'candidate must enumerate exactly 10 paths')
    require([row.get('path') for row in rows] == list(EXPECTED_PATHS), 'candidate path order/set drift')
    for row in rows:
        expected = EXPECTED_PATHS[row['path']]
        require(set(row) == {'path', 'blob_sha', 'depth', 'scope', 'semantic_assertions'}, 'candidate path key drift: ' + row['path'])
        require(row['blob_sha'] == expected['blob_sha'], 'candidate path blob drift: ' + row['path'])
        require(row['depth'] == 'SCOPED_SEMANTIC_REVIEW', 'candidate depth drift: ' + row['path'])
        require(row['scope'] == expected['scope'], 'candidate scope drift: ' + row['path'])
        require(json_exact(row['semantic_assertions'], expected['assertions']), 'candidate assertions drift: ' + row['path'])

    expected_deps = [
        {'path': path, 'blob_sha': blob, 'required_text': text, 'role': role}
        for path, blob, text, role in EXPECTED_DEPENDENCIES
    ]
    require(json_exact(candidate['dependency_bindings'], expected_deps), 'candidate dependency binding drift')
    expected_tests = [{
        'path': EXPECTED_TEST_PATH, 'blob_sha': EXPECTED_TEST_BLOB,
        'required_methods': EXPECTED_TEST_METHODS,
        'role': 'FOCUSED_EXECUTION_DEPENDENCY_NOT_PROMOTED_BY_THIS_CANDIDATE',
    }]
    require(json_exact(candidate['focused_current_tests'], expected_tests), 'candidate focused test binding drift')
    require(json_exact(candidate['baseline_accounting'], EXPECTED_BASELINE), 'candidate baseline accounting drift')
    require(json_exact(candidate['qualification'], EXPECTED_QUALIFICATION), 'candidate qualification state drift')
    require(json_exact(candidate['projection'], EXPECTED_PROJECTION), 'candidate projection state drift')
    require(json_exact(candidate['limitations'], EXPECTED_LIMITATIONS), 'candidate limitations drift')


def validate_source(candidate: dict, platform_root: Path) -> None:
    require(git(platform_root, 'rev-parse', 'HEAD') == SOURCE_COMMIT, 'frozen Platform commit drift')
    require(git(platform_root, 'rev-parse', 'HEAD^{tree}') == SOURCE_TREE, 'frozen Platform tree drift')

    ls = git(platform_root, 'ls-tree', '-r', '--name-only', 'HEAD', '--', 'app/Announcements')
    exact = [line for line in ls.splitlines() if line]
    require(exact == list(EXPECTED_PATHS), 'frozen app/Announcements leaf set/order drift')

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
    candidate = read_json(args.audit_root / CANDIDATE_REL)
    validate_candidate_shape(candidate)
    validate_source(candidate, args.platform_root)
    result = {
        'result': 'ANNOUNCEMENTS_DIRECT_CANDIDATE_QUALIFIED_FOR_PRIMARY_EXECUTION_NOT_ADOPTED',
        'source_commit': SOURCE_COMMIT,
        'candidate_paths': 10,
        'coverage_adopted': False,
        'canonical_direct_paths': 223,
        'canonical_grouped_paths': 113,
        'canonical_unverified_paths': 3989,
        'canonical_semantically_classified_paths': 336,
        'canonical_ledger_sha256': BASE_LEDGER_SHA,
        'next_gate': 'real MariaDB primary qualification; canonical coverage must remain unchanged',
        'product_readiness_claimed': False,
        'audit_completion_claimed': False,
    }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
