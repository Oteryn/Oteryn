#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

CANDIDATE = Path('docs/evidence/organization-audit-20260907/r3-platform-marketplace-tests-candidate.json')
GROUPS = Path('docs/evidence/organization-audit-20260907/coverage-groups.json')
EVIDENCE_PATH = 'docs/testing/OTERYN_PLATFORM_REPOSITORY_AUDIT_2026-09-06-CONTINUATION.md'
SOURCE_COMMIT = 'de917b3477a1de0667531380de3660e8b2ab59aa'
SOURCE_TREE = 'ffdf2a286d3a39f2344cf2ff53b28e4ef7369a8e'
HISTORICAL_COMMIT = '3b2ea1c7392187d5d22488673073dc8f8305a374'
HISTORICAL_TREE = '0f320dd073bc2619307314e380017526d27e5ddb'
EVIDENCE_COMMIT = '3fe7df5330deb9ed38cc17ae1710f0cb4159019b'
EVIDENCE_TREE = 'c6ac8cb7cbff069d7ac7303b3472d992da254774'
EVIDENCE_BLOB = '34361414339a5ca57ec5cd13e332ad196aa9e35f'
MARKETPLACE_TEST_TREE = '03f7d3735dee4140bf75960f0e106c3ba3d3b37b'
PREFIX = 'tests/Feature/Marketplace/'
EXACT_STATEMENT = '**FACT.** The following Marketplace tests were read directly during continuation:'
QUALIFIED = 'QUALIFIED_PENDING_ADOPTION'

EXPECTED_PATH_BLOBS = {
    'tests/Feature/Marketplace/CanaryCharacterTransferConcurrencyMariaDbTest.php': 'f9b9a17d34003132acf877a9755b998d6cfa5403',
    'tests/Feature/Marketplace/CanaryCharacterTransferMariaDbIntegrationTest.php': '14aa475be873476523eae72775b02acad956c8df',
    'tests/Feature/Marketplace/MarketplaceAuctionTerminalRecoveryConcurrencyTest.php': '41df060eb0b14828e6331aa78e86e6f1a27b5334',
    'tests/Feature/Marketplace/MarketplaceIdempotencyTest.php': 'a3e70ea8019ceaa636afd3c4030c84190c68e077',
    'tests/Feature/Marketplace/MarketplaceModuleTest.php': 'cd545576fba348f5f17e5e527882e8b4c142c6ad',
    'tests/Feature/Marketplace/MarketplaceSettlementRecoveryTest.php': 'e1a8bd57d63a9c86427f0d0140e23147147b6dd2',
}
FOCUSED_TEST_FILES = (
    'tests/Feature/Marketplace/MarketplaceAuctionTerminalRecoveryConcurrencyTest.php',
    'tests/Feature/Marketplace/MarketplaceIdempotencyTest.php',
    'tests/Feature/Marketplace/MarketplaceModuleTest.php',
    'tests/Feature/Marketplace/MarketplaceSettlementRecoveryTest.php',
    'tests/Feature/Marketplace/CanaryCharacterTransferMariaDbIntegrationTest.php',
    'tests/Feature/Marketplace/CanaryCharacterTransferConcurrencyMariaDbTest.php',
)
REQUIRED_CHECKS = (
    'historical audit publication commit/tree/evidence blob match exactly',
    'historical evidence contains the direct-read statement and all six exact Marketplace test paths',
    'historical and frozen-current Marketplace test directory tree SHAs are identical',
    'both generations contain exactly the same six regular files and exact blob identities',
    'the exact frozen-current six-file qualification is bound to its exact head/run/job and JUnit totals',
    'fresh frozen-current execution repeats all six files with zero failures/errors/skips including both real-MariaDB tests',
)
LIMITATIONS = (
    'Qualified frozen-current carry-forward candidate only. Historical direct-read evidence, byte identity and the bound '
    '17-case/179-assertion all-green qualification do not establish production correctness, complete Marketplace/payment '
    'correctness, later-current-main status, or organization-wide audit completion. No GROUPED coverage is adopted until '
    'projected-ledger reproduction and atomic canonical adoption pass, followed by post-adoption revalidation and '
    'independent exact-head review.'
)
PRIMARY_QUALIFICATION = {
    'qualification_head': 'f54e5b0640945d7a5f0a7c471ac81105436214ae',
    'workflow_run': 34323945126,
    'job': 102376779500,
    'verifier_unit_tests': 10,
    'verifier_unit_result': 'PASS',
    'focused_current_tests': {
        'test_files': 6,
        'junit_files': 3,
        'cases': 17,
        'assertions': 179,
        'failures': 0,
        'errors': 0,
        'skipped': 0,
        'junit': [
            {'file': 'ordinary.xml', 'cases': 14, 'assertions': 110, 'failures': 0, 'errors': 0, 'skipped': 0},
            {'file': 'transfer-concurrency.xml', 'cases': 1, 'assertions': 54, 'failures': 0, 'errors': 0, 'skipped': 0},
            {'file': 'transfer.xml', 'cases': 2, 'assertions': 15, 'failures': 0, 'errors': 0, 'skipped': 0},
        ],
    },
    'php': '8.5.10',
    'mariadb': '11.8.9',
    'composer_validate': 'PASS',
    'tracked_source_clean_after_execution': True,
    'outcome': 'QUALIFIED_PRIMARY_NOT_YET_ADOPTED',
}


def json_exact(left, right) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(json_exact(left[key], right[key]) for key in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(json_exact(a, b) for a, b in zip(left, right))
    return left == right


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def read_json(path: Path) -> dict:
    def pairs(items):
        out = {}
        for key, value in items:
            require(key not in out, f'duplicate JSON key in {path}: {key}')
            out[key] = value
        return out

    data = json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=pairs)
    require(isinstance(data, dict), f'{path} must contain a JSON object')
    return data


def expected_candidate() -> dict:
    return {
        'schema_version': 1,
        'candidate_id': 'PLATFORM-MARKETPLACE-TESTS-HISTORICAL-DIRECT-CARRYFORWARD',
        'repository': 'Oteryn/Oteryn-Platform',
        'state': QUALIFIED,
        'expected_total': 6,
        'historical_evidence': {
            'publication_commit': EVIDENCE_COMMIT,
            'publication_tree': EVIDENCE_TREE,
            'evidence_path': EVIDENCE_PATH,
            'evidence_blob': EVIDENCE_BLOB,
            'audited_main_sha': HISTORICAL_COMMIT,
            'audited_main_tree': HISTORICAL_TREE,
            'exact_statement': EXACT_STATEMENT,
            'basis': 'immutable historical evidence explicitly names every file in the six-file Marketplace test directory',
        },
        'current_revalidation': {
            'source_commit': SOURCE_COMMIT,
            'source_tree': SOURCE_TREE,
            'path_prefix': PREFIX,
            'historical_tree': MARKETPLACE_TEST_TREE,
            'current_tree': MARKETPLACE_TEST_TREE,
            'path_blobs': EXPECTED_PATH_BLOBS,
            'focused_test_files': list(FOCUSED_TEST_FILES),
            'required_checks': list(REQUIRED_CHECKS),
        },
        'coverage_adopted': False,
        'limitations': LIMITATIONS,
        'qualification': PRIMARY_QUALIFICATION,
    }


def validate_candidate_shape(candidate: dict) -> None:
    require(json_exact(candidate, expected_candidate()), 'Marketplace-test candidate canonical evidence fields/key sets drift')


def validate_group_absence(groups_doc: dict) -> None:
    require(type(groups_doc.get('schema_version')) is int and groups_doc['schema_version'] == 1, 'coverage-groups schema')
    groups = groups_doc.get('groups')
    require(isinstance(groups, list), 'coverage-groups groups must be a list')
    for group in groups:
        require(isinstance(group, dict), 'coverage group must be an object')
        require(group.get('id') != 'PLATFORM-MARKETPLACE-TESTS-HISTORICAL-DIRECT-CARRYFORWARD', 'qualified Marketplace-test group already exists')
        prefix = group.get('path_prefix')
        if isinstance(prefix, str):
            require(not any(path.startswith(prefix) for path in EXPECTED_PATH_BLOBS), f'qualified Marketplace tests overlap existing group {group.get("id")}')
        paths = group.get('paths')
        if isinstance(paths, list):
            require(not set(paths).intersection(EXPECTED_PATH_BLOBS), f'qualified Marketplace tests overlap explicit existing group {group.get("id")}')


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ['git', '-C', str(root), *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
    )
    return result.stdout.strip()


def tree_entries(root: Path, commit: str) -> dict[str, tuple[str, str]]:
    raw = subprocess.run(
        ['git', '-C', str(root), 'ls-tree', '-r', '-z', '--full-tree', commit, '--', PREFIX],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
    ).stdout
    entries: dict[str, tuple[str, str]] = {}
    for item in raw.split(b'\0'):
        if not item:
            continue
        meta, path_bytes = item.split(b'\t', 1)
        mode, kind, sha = meta.decode().split()
        path = path_bytes.decode()
        require(kind == 'blob' and mode == '100644', f'unexpected Marketplace test entry mode/type for {path}: {mode} {kind}')
        entries[path] = (mode, sha)
    return entries


def verify(audit_root: Path, platform_root: Path, evidence_root: Path) -> dict:
    candidate = read_json(audit_root / CANDIDATE)
    validate_candidate_shape(candidate)
    validate_group_absence(read_json(audit_root / GROUPS))

    require(git(platform_root, 'rev-parse', 'HEAD') == SOURCE_COMMIT, 'frozen Platform HEAD drift')
    require(git(platform_root, 'rev-parse', 'HEAD^{tree}') == SOURCE_TREE, 'frozen Platform tree drift')
    require(git(platform_root, 'rev-parse', f'{HISTORICAL_COMMIT}^{{tree}}') == HISTORICAL_TREE, 'historical Platform tree drift')
    require(git(platform_root, 'rev-parse', f'{HISTORICAL_COMMIT}:tests/Feature/Marketplace') == MARKETPLACE_TEST_TREE, 'historical Marketplace-test tree drift')
    require(git(platform_root, 'rev-parse', f'{SOURCE_COMMIT}:tests/Feature/Marketplace') == MARKETPLACE_TEST_TREE, 'frozen Marketplace-test tree drift')

    historical_entries = tree_entries(platform_root, HISTORICAL_COMMIT)
    current_entries = tree_entries(platform_root, SOURCE_COMMIT)
    expected_entries = {path: ('100644', sha) for path, sha in EXPECTED_PATH_BLOBS.items()}
    require(json_exact(historical_entries, expected_entries), 'historical Marketplace-test path/blob set drift')
    require(json_exact(current_entries, expected_entries), 'frozen Marketplace-test path/blob set drift')
    require(json_exact(historical_entries, current_entries), 'Marketplace-test historical/current identity drift')

    require(git(evidence_root, 'rev-parse', 'HEAD') == EVIDENCE_COMMIT, 'historical evidence HEAD drift')
    require(git(evidence_root, 'rev-parse', 'HEAD^{tree}') == EVIDENCE_TREE, 'historical evidence tree drift')
    require(git(evidence_root, 'rev-parse', f'HEAD:{EVIDENCE_PATH}') == EVIDENCE_BLOB, 'historical evidence blob drift')
    evidence_text = (evidence_root / EVIDENCE_PATH).read_text(encoding='utf-8')
    require(evidence_text.count(EXACT_STATEMENT) == 1, 'historical Marketplace-test direct-read statement missing/duplicated')
    for path in EXPECTED_PATH_BLOBS:
        require(evidence_text.count(f'`{path}`') == 1, f'historical evidence missing/duplicates exact Marketplace test path: {path}')

    return {
        'result': 'MARKETPLACE_TESTS_PRIMARY_QUALIFIED_NOT_ADOPTED',
        'candidate_id': candidate['candidate_id'],
        'historical_source': HISTORICAL_COMMIT,
        'current_source': SOURCE_COMMIT,
        'path_prefix': PREFIX,
        'tree_sha': MARKETPLACE_TEST_TREE,
        'paths': 6,
        'path_blobs_verified': 6,
        'focused_test_files_bound': 6,
        'primary_qualification': PRIMARY_QUALIFICATION,
        'coverage_adopted': False,
        'next_gate': 'reproduce projected 4,325-row ledger with exactly six additional GROUPED paths, then atomically adopt or reject the batch',
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--audit-root', type=Path, default=Path('.'))
    parser.add_argument('--platform-root', type=Path, required=True)
    parser.add_argument('--evidence-root', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.audit_root.resolve(), args.platform_root.resolve(), args.evidence_root.resolve()), indent=2))


if __name__ == '__main__':
    main()
