#!/usr/bin/env python3
"""Fail-closed verifier for the frozen Platform 31-file account/Canary/profile/character carry-forward candidate.

Read-only. Pending state proves immutable historical direct-read evidence, exact historical/current source
identity for four families, and the complete dependent test/config binding. It does not adopt coverage or
claim product readiness; frozen-current behavioral tests are a separate required qualification step.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

CANDIDATE = Path('docs/evidence/organization-audit-20260907/r3-platform-account-character-candidate.json')
SOURCE_COMMIT = 'de917b3477a1de0667531380de3660e8b2ab59aa'
SOURCE_TREE = 'ffdf2a286d3a39f2344cf2ff53b28e4ef7369a8e'
HISTORICAL_COMMIT = '3b2ea1c7392187d5d22488673073dc8f8305a374'
HISTORICAL_TREE = '0f320dd073bc2619307314e380017526d27e5ddb'
APP_TREE = '12f0d06940192719373733ce95fe2171b616b8d3'
EVIDENCE_COMMIT = '3fe7df5330deb9ed38cc17ae1710f0cb4159019b'
EVIDENCE_TREE = 'c6ac8cb7cbff069d7ac7303b3472d992da254774'
EVIDENCE_PATH = 'docs/testing/OTERYN_PLATFORM_REPOSITORY_AUDIT_2026-09-06-CONTINUATION.md'
EVIDENCE_BLOB = '34361414339a5ca57ec5cd13e332ad196aa9e35f'
EXPECTED_FAMILIES = (
    ('PLATFORM-ACCOUNTS-HISTORICAL-DIRECT-CARRYFORWARD', 'app/Accounts/', 7, '7505ff7d6836c667e0354622616ba2673e1ff9f2'),
    ('PLATFORM-CANARY-INTEGRATION-HISTORICAL-DIRECT-CARRYFORWARD', 'app/CanaryIntegration/', 8, 'f37ac5641d49dbc7f419c69ffc0ae852af655baa'),
    ('PLATFORM-CHARACTER-PROFILES-HISTORICAL-DIRECT-CARRYFORWARD', 'app/CharacterProfiles/', 4, '677b67618fa5155c8e0e33b1baed097c8afce8e3'),
    ('PLATFORM-CHARACTERS-HISTORICAL-DIRECT-CARRYFORWARD', 'app/Characters/', 12, 'cee6097116aea56865cfa54406c0be150e1f3f97'),
)
EXACT_SCOPE_LINES = (
    '**FACT.** A 31-file batch was read covering:',
    '- `app/Accounts/**`;',
    '- `app/CanaryIntegration/**` relevant to account provisioning, character creation, character transfer, database privilege verification and runtime Redis reads;',
    '- `app/CharacterProfiles/**`;',
    '- `app/Characters/**`.',
)
FOCUSED_TEST_FILES = (
    'tests/Feature/Accounts/AccountOverviewTest.php',
    'tests/Feature/Accounts/CanaryProvisioningMariaDbIntegrationTest.php',
    'tests/Feature/Accounts/ProvisionCanaryAccountTest.php',
    'tests/Feature/CharacterProfiles/CharacterProfilePreferenceTest.php',
    'tests/Feature/CharacterProfiles/Concurrency/CharacterProfilePreferenceConcurrencyTest.php',
    'tests/Feature/Characters/CanaryCharacterCreateMariaDbIntegrationTest.php',
    'tests/Feature/Characters/CharacterCreationTest.php',
    'tests/Unit/CanaryIntegration/CanaryCharacterCreateDatabasePrivilegeVerifierTest.php',
    'tests/Unit/CanaryIntegration/CanaryCharacterTransferDatabasePrivilegeVerifierTest.php',
    'tests/Unit/CanaryIntegration/CanaryDatabasePrivilegeVerifierTest.php',
    'tests/Unit/CanaryIntegration/CanaryProvisioningDatabasePrivilegeVerifierTest.php',
    'tests/Unit/CanaryIntegration/CanaryRuntimeRedisReaderTest.php',
    'tests/Unit/Characters/CharacterNamePolicyTest.php',
    'tests/Feature/Marketplace/CanaryCharacterTransferConcurrencyMariaDbTest.php',
    'tests/Feature/Marketplace/CanaryCharacterTransferMariaDbIntegrationTest.php',
)
NON_TEST_DEPENDENCIES = (
    'bootstrap/app.php',
    'config/database.php',
    'config/marketplace.php',
    'routes/web.php',
    'routes/modules/marketplace.php',
    'composer.json',
    'composer.lock',
    'phpunit.xml',
)
EXPECTED_DEPENDENT_PATHS = frozenset(NON_TEST_DEPENDENCIES + FOCUSED_TEST_FILES)


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


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
        ['git', '-C', str(root), *args], check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30,
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


def validate_candidate_shape(candidate) -> None:
    require(type(candidate.get('schema_version')) is int and candidate['schema_version'] == 1, 'candidate schema')
    require(candidate.get('candidate_id') == 'PLATFORM-ACCOUNT-CHARACTER-HISTORICAL-DIRECT-CARRYFORWARD', 'candidate id')
    require(candidate.get('repository') == 'Oteryn/Oteryn-Platform', 'candidate repository')
    require(candidate.get('state') == 'CANDIDATE_PENDING_QUALIFICATION', 'candidate state')
    require(candidate.get('coverage_adopted') is False, 'pending candidate cannot adopt coverage')
    require(type(candidate.get('expected_total')) is int and candidate['expected_total'] == 31, 'candidate total')

    hist = candidate.get('historical_evidence') or {}
    require(hist.get('repository') == 'Oteryn/Oteryn-Platform', 'historical repository')
    require(hist.get('publication_commit') == EVIDENCE_COMMIT, 'historical publication commit')
    require(hist.get('publication_tree') == EVIDENCE_TREE, 'historical publication tree')
    require(hist.get('evidence_path') == EVIDENCE_PATH, 'historical evidence path')
    require(hist.get('evidence_blob') == EVIDENCE_BLOB, 'historical evidence blob')
    require(hist.get('audited_main_sha') == HISTORICAL_COMMIT, 'historical source commit')
    require(hist.get('audited_main_tree') == HISTORICAL_TREE, 'historical source tree')
    require(tuple(hist.get('exact_scope_lines') or ()) == EXACT_SCOPE_LINES, 'historical scope line set/order')

    current = candidate.get('current_revalidation') or {}
    require(current.get('source_commit') == SOURCE_COMMIT, 'frozen source commit')
    require(current.get('source_tree') == SOURCE_TREE, 'frozen source tree')
    require(current.get('historical_app_tree') == APP_TREE and current.get('current_app_tree') == APP_TREE, 'app tree binding')
    family_rows = current.get('families')
    require(isinstance(family_rows, list), 'family list')
    actual_specs = tuple((row.get('id'), row.get('path_prefix'), row.get('expected_count'), row.get('tree_sha')) for row in family_rows)
    require(actual_specs == EXPECTED_FAMILIES, 'family set/order/count/tree bindings must be exact')

    deps = current.get('dependent_blobs')
    require(isinstance(deps, dict), 'dependent blob map')
    require(set(deps) == EXPECTED_DEPENDENT_PATHS and len(deps) == 23, 'dependent path set must be exact 23 bindings')
    require(tuple(current.get('focused_test_files') or ()) == FOCUSED_TEST_FILES, 'focused test set/order must be exact 15 files')
    require(set(FOCUSED_TEST_FILES).issubset(deps), 'every focused test must be blob-bound')


def verify(audit_root: Path, platform_root: Path, evidence_root: Path):
    candidate = read_json(audit_root / CANDIDATE)
    validate_candidate_shape(candidate)
    hist = candidate['historical_evidence']; current = candidate['current_revalidation']

    require(text(platform_root, 'rev-parse', 'HEAD') == SOURCE_COMMIT, 'wrong frozen Platform source')
    require(text(platform_root, 'rev-parse', 'HEAD^{tree}') == SOURCE_TREE, 'wrong frozen Platform tree')
    require(text(platform_root, 'rev-parse', HISTORICAL_COMMIT + '^{tree}') == HISTORICAL_TREE, 'wrong historical Platform source tree')
    require(text(evidence_root, 'rev-parse', 'HEAD') == EVIDENCE_COMMIT, 'wrong Platform audit publication')
    require(text(evidence_root, 'rev-parse', 'HEAD^{tree}') == EVIDENCE_TREE, 'wrong Platform audit publication tree')

    evidence_path = evidence_root / EVIDENCE_PATH
    require(evidence_path.is_file() and not evidence_path.is_symlink(), 'historical evidence path invalid')
    raw = evidence_path.read_bytes()
    require(blob_sha(raw) == EVIDENCE_BLOB, 'historical evidence blob mismatch')
    historical_text = raw.decode('utf-8')
    for line in EXACT_SCOPE_LINES:
        require(historical_text.count(line) == 1, 'historical 31-file scope line missing/duplicated: ' + line)

    require(text(platform_root, 'rev-parse', HISTORICAL_COMMIT + ':app') == APP_TREE, 'historical app tree mismatch')
    require(text(platform_root, 'rev-parse', SOURCE_COMMIT + ':app') == APP_TREE, 'current app tree mismatch')

    total = 0; family_results = []
    for family_id, prefix, count, tree_sha in EXPECTED_FAMILIES:
        path = prefix.rstrip('/')
        require(text(platform_root, 'rev-parse', HISTORICAL_COMMIT + ':' + path) == tree_sha, 'historical family tree mismatch: ' + prefix)
        require(text(platform_root, 'rev-parse', SOURCE_COMMIT + ':' + path) == tree_sha, 'current family tree mismatch: ' + prefix)
        old = recursive_entries(platform_root, HISTORICAL_COMMIT, prefix)
        now = recursive_entries(platform_root, SOURCE_COMMIT, prefix)
        require(len(old) == len(now) == count, 'family leaf count mismatch: ' + prefix)
        require(old == now, 'family path/blob identity changed: ' + prefix)
        require(all(mode == '100644' and kind == 'blob' for _, mode, kind, _ in now), 'family contains non-regular leaf: ' + prefix)
        changed = git(platform_root, 'diff', '--name-only', HISTORICAL_COMMIT, SOURCE_COMMIT, '--', prefix).decode().splitlines()
        require(changed == [], 'family diff not empty: ' + prefix)
        total += len(now)
        family_results.append({'id': family_id, 'path_prefix': prefix, 'paths': len(now), 'tree_sha': tree_sha})
    require(total == 31, 'qualified family total')

    deps = current['dependent_blobs']
    for path in sorted(EXPECTED_DEPENDENT_PATHS):
        expected = deps[path]
        require(isinstance(expected, str) and len(expected) == 40, 'dependent SHA shape: ' + path)
        actual = text(platform_root, 'rev-parse', SOURCE_COMMIT + ':' + path)
        require(actual == expected, 'frozen-current dependent blob mismatch: ' + path)

    return {
        'result': 'ACCOUNT_CHARACTER_IDENTITY_AND_HISTORICAL_DIRECT_EVIDENCE_REVALIDATED_TESTS_STILL_REQUIRED',
        'candidate_id': candidate['candidate_id'],
        'historical_source': HISTORICAL_COMMIT,
        'current_source': SOURCE_COMMIT,
        'paths': total,
        'families': family_results,
        'dependent_blobs_verified': len(deps),
        'focused_test_files_bound': len(FOCUSED_TEST_FILES),
        'coverage_adopted': False,
        'next_gate': 'frozen-current 15-file behavioral qualification including MariaDB concurrency/integration must pass before any GROUPED adoption',
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit-root', type=Path, required=True)
    parser.add_argument('--platform-root', type=Path, required=True)
    parser.add_argument('--evidence-root', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.audit_root.resolve(), args.platform_root.resolve(), args.evidence_root.resolve()), indent=2))


if __name__ == '__main__':
    main()
