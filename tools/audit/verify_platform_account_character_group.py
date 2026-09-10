#!/usr/bin/env python3
"""Fail-closed verifier for the frozen Platform 31-file account/Canary/profile/character carry-forward candidate.

Read-only. The tool verifies immutable historical direct-read evidence, exact historical/current source
identity for four families, the complete dependent test/config binding, and—if adoption is claimed—the
exact qualification record plus four canonical GROUPED records. It does not claim product readiness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

CANDIDATE = Path('docs/evidence/organization-audit-20260907/r3-platform-account-character-candidate.json')
GROUPS = Path('docs/evidence/organization-audit-20260907/coverage-groups.json')
SOURCE_COMMIT = 'de917b3477a1de0667531380de3660e8b2ab59aa'
SOURCE_TREE = 'ffdf2a286d3a39f2344cf2ff53b28e4ef7369a8e'
HISTORICAL_COMMIT = '3b2ea1c7392187d5d22488673073dc8f8305a374'
HISTORICAL_TREE = '0f320dd073bc2619307314e380017526d27e5ddb'
APP_TREE = '12f0d06940192719373733ce95fe2171b616b8d3'
EVIDENCE_COMMIT = '3fe7df5330deb9ed38cc17ae1710f0cb4159019b'
EVIDENCE_TREE = 'c6ac8cb7cbff069d7ac7303b3472d992da254774'
EVIDENCE_PATH = 'docs/testing/OTERYN_PLATFORM_REPOSITORY_AUDIT_2026-09-06-CONTINUATION.md'
EVIDENCE_BLOB = '34361414339a5ca57ec5cd13e332ad196aa9e35f'
PENDING = 'CANDIDATE_PENDING_QUALIFICATION'
ADOPTED = 'QUALIFIED_ADOPTED_AS_GROUPED'
OUTCOME = 'ADOPTED_GROUPED_CARRY_FORWARD'
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
FOCUSED_RESULT = {
    'cases': 86,
    'assertions': 586,
    'failures': 0,
    'errors': 0,
    'skipped': 0,
}
PRIMARY_QUALIFICATION = {
    'qualification_head': 'a55ed0c005b581dd91042a3da40678f8ff04acb6',
    'workflow_run': 34230659158,
    'job': 102075660945,
    'verifier_unit_tests': 8,
    'verifier_unit_result': 'PASS',
    'focused_current_tests': {
        'test_files': 15,
        **FOCUSED_RESULT,
    },
    'php': '8.5.10',
    'mariadb': '11.8.9',
    'composer_validate': 'PASS',
    'tracked_source_clean_after_execution': True,
    'outcome': OUTCOME,
}
POST_ADOPTION = {'audit_head': '3b05f71a331da8c06fd0f5d6a0557590004ce5c5', 'workflow_run': 34281059173, 'job': 102245648440, 'result': 'PASS', 'canonical_group_state': 'ACCOUNT_CHARACTER_GROUPED_ADOPTION_REVALIDATED_NOT_PRODUCT_PASS', 'verifier_unit_tests': 16, 'focused_current_tests': {'test_files': 15, 'cases': 86, 'assertions': 586, 'failures': 0, 'errors': 0, 'skipped': 0}, 'php': '8.5.10', 'mariadb': '11.8.9', 'meta_ci_run': 34281059174, 'meta_ci_result': 'SUCCESS', 'ledger_reproduction_run': 34281059142, 'ledger_reproduction_artifact': 10077605747, 'ledger_sha256': 'b61566ad825adf528b177a5ab4a2ee533680bd948e44a60df6289255c5747459'}
GROUP_SCOPE = (
    'Historical direct-read evidence for the documented 31-file account/Canary/profile/character batch '
    'is carried forward only for this exact byte-identical family. Adoption is bounded by exact family '
    'path/blob identity, the exact 23-path dependent binding set, and the exact 15-file frozen-current '
    'qualification result of 86 cases / 586 assertions / 0 failures / 0 errors / 0 skips.'
)
GROUP_LIMITATIONS = (
    'Adopted only as bounded GROUPED carry-forward. This does not establish production readiness, '
    'later-current-main status, provider remediation, full Platform security/correctness, or organization-wide audit completion.'
)


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


def expected_historical_group(prefix: str, count: int) -> dict:
    return {
        'repository': 'Oteryn/Oteryn-Platform',
        'publication_commit': EVIDENCE_COMMIT,
        'publication_tree': EVIDENCE_TREE,
        'coverage_rules_path': EVIDENCE_PATH,
        'coverage_rules_blob': EVIDENCE_BLOB,
        'audited_main_sha': HISTORICAL_COMMIT,
        'audited_main_tree': HISTORICAL_TREE,
        'pattern': prefix + '**',
        'count': count,
        'basis': 'historical direct read of the documented 31-file account/Canary/profile/character batch, bounded to this exact family by immutable source enumeration',
    }


def expected_current_group(current: dict, prefix: str, count: int, tree_sha: str) -> dict:
    return {
        'source_commit': SOURCE_COMMIT,
        'source_tree': SOURCE_TREE,
        'historical_app_tree': APP_TREE,
        'current_app_tree': APP_TREE,
        'family_tree': tree_sha,
        'changed_paths_under_group_prefix': 0,
        'historical_to_current_compare_status': 'ahead',
        'current_blobs': current['dependent_blobs'],
        'required_checks': [
            'historical 31-file direct-read evidence is bound exactly and this family is its exact enumerated subset',
            'historical and frozen current app trees are byte-identical',
            f'historical and frozen current {prefix} trees contain exactly the same {count} regular-file leaves and blob identities',
            'the dependent binding map is exactly the required 23 paths and contains all 15 focused test files',
            'the exact frozen-current 15-file qualification passes with 86 cases / 586 assertions / 0 failures / 0 errors / 0 skips',
        ],
        'focused_test_files': list(FOCUSED_TEST_FILES),
    }


def expected_group(candidate: dict, spec: tuple[str, str, int, str]) -> dict:
    family_id, prefix, count, tree_sha = spec
    return {
        'id': family_id,
        'repository': 'platform',
        'disposition': 'GROUPED',
        'path_prefix': prefix,
        'expected_count': count,
        'depth': 'GROUPED_REVALIDATED',
        'scope': GROUP_SCOPE,
        'limitations': GROUP_LIMITATIONS,
        'historical_evidence': expected_historical_group(prefix, count),
        'current_revalidation': expected_current_group(candidate['current_revalidation'], prefix, count, tree_sha),
        'evaluation': {
            'qualification_head': PRIMARY_QUALIFICATION['qualification_head'],
            'qualification_run': PRIMARY_QUALIFICATION['workflow_run'],
            'qualification_job': PRIMARY_QUALIFICATION['job'],
            'verifier_unit_tests': PRIMARY_QUALIFICATION['verifier_unit_tests'],
            'focused_current_tests': FOCUSED_RESULT,
            'outcome': OUTCOME,
        },
    }


def validate_candidate_shape(candidate) -> bool:
    require(type(candidate.get('schema_version')) is int and candidate['schema_version'] == 1, 'candidate schema')
    require(candidate.get('candidate_id') == 'PLATFORM-ACCOUNT-CHARACTER-HISTORICAL-DIRECT-CARRYFORWARD', 'candidate id')
    require(candidate.get('repository') == 'Oteryn/Oteryn-Platform', 'candidate repository')
    state = candidate.get('state')
    require(state in {PENDING, ADOPTED}, 'candidate state')
    adopted = state == ADOPTED
    require(type(candidate.get('coverage_adopted')) is bool, 'candidate adoption type')
    require(candidate['coverage_adopted'] is adopted, 'candidate adoption/state mismatch')
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

    if adopted:
        qualification = candidate.get('qualification')
        require(isinstance(qualification, dict), 'adopted candidate qualification missing')
        require(json_exact(qualification, PRIMARY_QUALIFICATION), 'candidate qualification must equal exact bound run/result')
        require(json_exact(candidate.get('post_adoption_revalidation'), POST_ADOPTION), 'candidate post-adoption revalidation must equal exact bound run/result')
    else:
        require('qualification' not in candidate, 'pending candidate must not carry adoption qualification')
        require('post_adoption_revalidation' not in candidate, 'pending candidate must not carry post-adoption revalidation')
    return adopted


def validate_group_state(candidate: dict, groups_doc: dict, adopted: bool) -> None:
    require(type(groups_doc.get('schema_version')) is int and groups_doc['schema_version'] == 1, 'coverage group schema')
    groups = groups_doc.get('groups')
    require(isinstance(groups, list), 'coverage groups missing')
    ids = {spec[0] for spec in EXPECTED_FAMILIES}
    accepted = [row for row in groups if row.get('id') in ids]
    if adopted:
        require(len(accepted) == 4, 'adopted account/character families missing/duplicated canonical groups')
        by_id = {row.get('id'): row for row in accepted}
        require(len(by_id) == 4, 'duplicate adopted account/character group id')
        for spec in EXPECTED_FAMILIES:
            expected = expected_group(candidate, spec)
            require(json_exact(by_id.get(spec[0]), expected), 'adopted group drift: ' + spec[0])
    else:
        require(accepted == [], 'pending candidate already present in accepted groups')


def verify(audit_root: Path, platform_root: Path, evidence_root: Path):
    candidate = read_json(audit_root / CANDIDATE)
    adopted = validate_candidate_shape(candidate)
    groups_doc = read_json(audit_root / GROUPS)
    validate_group_state(candidate, groups_doc, adopted)
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

    if adopted:
        result = 'ACCOUNT_CHARACTER_GROUPED_ADOPTION_REVALIDATED_NOT_PRODUCT_PASS'
        next_gate = 'fresh independent exact-head review; retain temporary qualification evidence until review completes'
    else:
        result = 'ACCOUNT_CHARACTER_IDENTITY_AND_HISTORICAL_DIRECT_EVIDENCE_REVALIDATED_TESTS_STILL_REQUIRED'
        next_gate = 'exact frozen-current 15-file behavioral qualification must be bound before GROUPED adoption'

    return {
        'result': result,
        'candidate_id': candidate['candidate_id'],
        'historical_source': HISTORICAL_COMMIT,
        'current_source': SOURCE_COMMIT,
        'paths': total,
        'families': family_results,
        'dependent_blobs_verified': len(deps),
        'focused_test_files_bound': len(FOCUSED_TEST_FILES),
        'coverage_adopted': adopted,
        'next_gate': next_gate,
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
