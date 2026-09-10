#!/usr/bin/env python3
"""Fail-closed verifier for frozen Platform Marketplace/Payments/Wallet 49-path carry-forward candidate.

Read-only. Pending state proves immutable historical direct-read evidence, exact historical/current
identity for three families, and the complete dependent test/config binding. It does not adopt
coverage or claim product readiness; frozen-current behavioral tests are a separate required gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

CANDIDATE = Path('docs/evidence/organization-audit-20260907/r3-platform-marketplace-payments-wallet-candidate.json')
GROUPS = Path('docs/evidence/organization-audit-20260907/coverage-groups.json')
INDEX = Path('docs/evidence/organization-audit-20260907/verification-index.json')
SOURCE_COMMIT = 'de917b3477a1de0667531380de3660e8b2ab59aa'
SOURCE_TREE = 'ffdf2a286d3a39f2344cf2ff53b28e4ef7369a8e'
HISTORICAL_COMMIT = '3b2ea1c7392187d5d22488673073dc8f8305a374'
HISTORICAL_TREE = '0f320dd073bc2619307314e380017526d27e5ddb'
APP_TREE = '12f0d06940192719373733ce95fe2171b616b8d3'
EVIDENCE_COMMIT = '3fe7df5330deb9ed38cc17ae1710f0cb4159019b'
EVIDENCE_TREE = 'c6ac8cb7cbff069d7ac7303b3472d992da254774'
EVIDENCE_PATH = 'docs/testing/OTERYN_PLATFORM_REPOSITORY_AUDIT_2026-09-06-CONTINUATION.md'
EVIDENCE_BLOB = '34361414339a5ca57ec5cd13e332ad196aa9e35f'
EXACT_STATEMENT = '**FACT.** A 49-file Marketplace/Payments/Wallet production batch was read directly.'
EXPECTED_FAMILIES = (
    ('PLATFORM-MARKETPLACE-HISTORICAL-DIRECT-CARRYFORWARD', 'app/Marketplace/', 21, 'bb18ad79196ac6e9d91e546662416a031cc0b6ad'),
    ('PLATFORM-PAYMENTS-HISTORICAL-DIRECT-CARRYFORWARD', 'app/Payments/', 24, '903b912ae8e904b4eb52bb987bff670fcea0ed74'),
    ('PLATFORM-WALLET-HISTORICAL-DIRECT-CARRYFORWARD', 'app/Wallet/', 4, '2221b703a2eda060a52d1ea448f791d44bc92d58'),
)
FOCUSED_TEST_FILES = (
    'tests/Feature/Marketplace/CanaryCharacterTransferConcurrencyMariaDbTest.php',
    'tests/Feature/Marketplace/CanaryCharacterTransferMariaDbIntegrationTest.php',
    'tests/Feature/Marketplace/MarketplaceAuctionTerminalRecoveryConcurrencyTest.php',
    'tests/Feature/Marketplace/MarketplaceIdempotencyTest.php',
    'tests/Feature/Marketplace/MarketplaceModuleTest.php',
    'tests/Feature/Marketplace/MarketplaceSettlementRecoveryTest.php',
    'tests/Feature/Payments/PaymentAvailabilityTest.php',
    'tests/Feature/Payments/PaymentEventConcurrencyMariaDbTest.php',
    'tests/Feature/Payments/PaymentEventCoreTest.php',
    'tests/Feature/Payments/PaymentFoundationSurfaceTest.php',
    'tests/Feature/Payments/PaymentPartialRefundConcurrencyMariaDbTest.php',
    'tests/Feature/Payments/PaymentPartialRefundIntegrityTest.php',
    'tests/Unit/Payments/PaymentOrderStateMachineTest.php',
)
NON_TEST_DEPENDENCIES = (
    'bootstrap/app.php',
    'config/database.php',
    'config/marketplace.php',
    'config/payments.php',
    'routes/web.php',
    'routes/modules/marketplace.php',
    'routes/modules/payments.php',
    'composer.json',
    'composer.lock',
    'phpunit.xml',
)
EXPECTED_DEPENDENT_PATHS = frozenset(NON_TEST_DEPENDENCIES + FOCUSED_TEST_FILES)
EXPECTED_DEPENDENT_BLOBS = {
    'bootstrap/app.php': 'daeaa5b91245ab73a9490662cad040e5b5949ce3',
    'config/database.php': '135b780e081eabfba40b123499bdc3536fc6f6e7',
    'config/marketplace.php': '0ed3d3d29827c801f2d72e8aee12b4b23ff0ef75',
    'config/payments.php': '40a13b6d0ebf1cd2eeaeda088458754209ecd3ff',
    'routes/web.php': '339e7573b2bc04c7bdd9183cd739c099448d8421',
    'routes/modules/marketplace.php': '6ead81fecf5d99eb231413bea98d8bf097fa05b5',
    'routes/modules/payments.php': '77690386865ea9095c427f96ee7a8e6b863f176a',
    'composer.json': '6bfd2d8018fb40ce4df9aef11ab715b5210d508d',
    'composer.lock': '9de0c6c04944b771ccd0072ea08f72dc90fff123',
    'phpunit.xml': '5ee5e6c596a08b758922fdc30ba650f5301d7a34',
    'tests/Feature/Marketplace/CanaryCharacterTransferConcurrencyMariaDbTest.php': 'f9b9a17d34003132acf877a9755b998d6cfa5403',
    'tests/Feature/Marketplace/CanaryCharacterTransferMariaDbIntegrationTest.php': '14aa475be873476523eae72775b02acad956c8df',
    'tests/Feature/Marketplace/MarketplaceAuctionTerminalRecoveryConcurrencyTest.php': '41df060eb0b14828e6331aa78e86e6f1a27b5334',
    'tests/Feature/Marketplace/MarketplaceIdempotencyTest.php': 'a3e70ea8019ceaa636afd3c4030c84190c68e077',
    'tests/Feature/Marketplace/MarketplaceModuleTest.php': 'cd545576fba348f5f17e5e527882e8b4c142c6ad',
    'tests/Feature/Marketplace/MarketplaceSettlementRecoveryTest.php': 'e1a8bd57d63a9c86427f0d0140e23147147b6dd2',
    'tests/Feature/Payments/PaymentAvailabilityTest.php': '98c166b7be061979bc721eafe305fbe508cc03f4',
    'tests/Feature/Payments/PaymentEventConcurrencyMariaDbTest.php': '702ae8f13d736947aae28d49dbc351e1a655b61c',
    'tests/Feature/Payments/PaymentEventCoreTest.php': '65aa479ee3ad57ba463d1ec80e0e9e166acd23e4',
    'tests/Feature/Payments/PaymentFoundationSurfaceTest.php': 'b9d81e83e517f068c467fcc4e97d4d0e190154ab',
    'tests/Feature/Payments/PaymentPartialRefundConcurrencyMariaDbTest.php': '66583c63d4714f11d41b5ca25015356409e471cc',
    'tests/Feature/Payments/PaymentPartialRefundIntegrityTest.php': '1dcff12df2d27d5e6d1a875f5e217fa047816bff',
    'tests/Unit/Payments/PaymentOrderStateMachineTest.php': '8481f198ab1961062dda957e28660d76b27ee405',
}

QUALIFIED_PENDING = 'QUALIFIED_PENDING_ADOPTION'
ADOPTED = 'QUALIFIED_ADOPTED_AS_GROUPED'
OUTCOME = 'ADOPTED_GROUPED_CARRY_FORWARD'
PRIMARY_QUALIFICATION = {
    'qualification_head': '13f6933c543db98848450e063e61f8c0dd2fa3d3',
    'workflow_run': 34283717767,
    'job': 102254287765,
    'verifier_unit_tests': 10,
    'verifier_unit_result': 'PASS',
    'focused_current_tests': {
        'test_files': 13,
        'junit_files': 5,
        'cases': 45,
        'assertions': 444,
        'failures': 0,
        'errors': 0,
        'skipped': 0,
        'junit': [
            {'file': 'marketplace-transfer-concurrency.xml', 'cases': 1, 'assertions': 54, 'failures': 0, 'errors': 0, 'skipped': 0},
            {'file': 'marketplace-transfer.xml', 'cases': 2, 'assertions': 15, 'failures': 0, 'errors': 0, 'skipped': 0},
            {'file': 'ordinary.xml', 'cases': 40, 'assertions': 327, 'failures': 0, 'errors': 0, 'skipped': 0},
            {'file': 'payment-event-concurrency.xml', 'cases': 1, 'assertions': 23, 'failures': 0, 'errors': 0, 'skipped': 0},
            {'file': 'payment-refund-concurrency.xml', 'cases': 1, 'assertions': 25, 'failures': 0, 'errors': 0, 'skipped': 0},
        ],
    },
    'php': '8.5.10',
    'mariadb': '11.8.9',
    'composer_validate': 'PASS',
    'tracked_source_clean_after_execution': True,
    'outcome': 'QUALIFIED_PRIMARY_NOT_YET_ADOPTED',
}
POST_ADOPTION = {'audit_head': '5ba21f04dde762a28fdcc04765bfbcfd929ba54a', 'workflow_run': 34285636501, 'job': 102260463521, 'result': 'PASS', 'canonical_group_state': 'MARKETPLACE_PAYMENTS_WALLET_GROUPED_ADOPTION_PRIMARY_PROOF_REVALIDATED_NOT_PRODUCT_PASS', 'verifier_unit_tests': 14, 'focused_current_tests': {'test_files': 13, 'junit_files': 5, 'cases': 45, 'assertions': 444, 'failures': 0, 'errors': 0, 'skipped': 0, 'junit': [{'file': 'marketplace-transfer-concurrency.xml', 'cases': 1, 'assertions': 54, 'failures': 0, 'errors': 0, 'skipped': 0}, {'file': 'marketplace-transfer.xml', 'cases': 2, 'assertions': 15, 'failures': 0, 'errors': 0, 'skipped': 0}, {'file': 'ordinary.xml', 'cases': 40, 'assertions': 327, 'failures': 0, 'errors': 0, 'skipped': 0}, {'file': 'payment-event-concurrency.xml', 'cases': 1, 'assertions': 23, 'failures': 0, 'errors': 0, 'skipped': 0}, {'file': 'payment-refund-concurrency.xml', 'cases': 1, 'assertions': 25, 'failures': 0, 'errors': 0, 'skipped': 0}]}, 'php': '8.5.10', 'mariadb': '11.8.9', 'meta_ci_run': 34285636467, 'meta_ci_result': 'SUCCESS', 'ledger_reproduction_run': 34285636466, 'ledger_reproduction_job': 102260463287, 'ledger_reproduction_artifact': 10079336853, 'ledger_sha256': '742443fbcc7fba9a45e1c71bf4395e3b2fe4ced7ae527a38de6ef2c74cb49406', 'ledger_counts': {'source_rows': 4325, 'direct_paths': 221, 'grouped_paths': 107, 'unverified_paths': 3997}}
GROUP_SCOPE = (
    'Historical direct-read evidence for the documented 49-file Marketplace/Payments/Wallet production batch '
    'is carried forward only for this exact byte-identical family. Adoption is bounded by exact family '
    'path/blob identity, the exact 23-path dependent binding set, and the exact 13-file frozen-current '
    'qualification result of 45 cases / 444 assertions / 0 failures / 0 errors / 0 skips.'
)
GROUP_LIMITATIONS = (
    'Adopted only as bounded GROUPED carry-forward. This does not establish production readiness, '
    'later-current-main status, provider remediation, complete Platform payment/marketplace correctness/security, '
    'or organization-wide audit completion.'
)


CANDIDATE_LIMITATIONS = (
    'Adopted only as bounded GROUPED carry-forward after exact historical/source identity, the exact 23-path '
    'dependent binding set, the exact ordered 13-file frozen-current qualification and bound 45-case/444-assertion '
    'all-green result. This does not establish production readiness, later-current-main status, provider remediation, '
    'complete payment/marketplace correctness/security, or organization-wide audit completion.'
)
CANDIDATE_REQUIRED_CHECKS = (
    'historical audit publication commit/tree and evidence blob match exactly',
    'historical evidence contains the exact 49-file Marketplace/Payments/Wallet direct-read statement exactly once',
    'historical and frozen current app trees are byte-identical',
    'each family tree matches its exact SHA and exact regular-file count on historical and frozen sources',
    'each family has identical historical/current path/blob entries and no changed path under its prefix',
    'the dependent binding map is exactly the required 23 paths and contains all 13 focused test files',
    'fresh frozen-current qualification executes all 13 focused files with zero failures/errors/skips, including four real-MariaDB integration/concurrency files',
)
EXPECTED_INDEX_ROW = {
    'frozen_source_commit': SOURCE_COMMIT,
    'historical_source_commit': HISTORICAL_COMMIT,
    'primary_qualification_head': PRIMARY_QUALIFICATION['qualification_head'],
    'primary_run': PRIMARY_QUALIFICATION['workflow_run'],
    'primary_job': PRIMARY_QUALIFICATION['job'],
    'primary_verifier_unit_tests': PRIMARY_QUALIFICATION['verifier_unit_tests'],
    'exact_family_counts': [21, 24, 4],
    'exact_total_paths': 49,
    'dependent_blob_bindings': 23,
    'focused_test_files': 13,
    'focused_cases': 45,
    'focused_assertions': 444,
    'failures': 0,
    'errors': 0,
    'skips': 0,
    'php': '8.5.10',
    'mariadb': '11.8.9',
    'tracked_source_clean_after_execution': True,
    'hardening_head': '53dc22290da5c952fc76aa4cb7222ad450be6974',
    'hardening_meta_ci_run': 34284712709,
    'hardening_qualification_run': 34284712575,
    'ledger_reproduction_head': 'adc884f64982e71609415ef946d97b445488c3e0',
    'ledger_reproduction_run': 34284837901,
    'ledger_reproduction_artifact': 10079037530,
    'pre_adoption_ledger_sha256': 'b61566ad825adf528b177a5ab4a2ee533680bd948e44a60df6289255c5747459',
    'projected_adopted_ledger_sha256': POST_ADOPTION['ledger_sha256'],
    'qualification': 'BOUNDED_GROUPED_CARRY_FORWARD_NOT_PRODUCT_PASS',
    'post_adoption_head': POST_ADOPTION['audit_head'],
    'post_adoption_run': POST_ADOPTION['workflow_run'],
    'post_adoption_job': POST_ADOPTION['job'],
    'post_adoption_verifier_unit_tests': POST_ADOPTION['verifier_unit_tests'],
    'post_adoption_meta_ci_run': POST_ADOPTION['meta_ci_run'],
    'post_adoption_ledger_run': POST_ADOPTION['ledger_reproduction_run'],
    'post_adoption_ledger_job': POST_ADOPTION['ledger_reproduction_job'],
    'post_adoption_ledger_artifact': POST_ADOPTION['ledger_reproduction_artifact'],
    'post_adoption_ledger_sha256': POST_ADOPTION['ledger_sha256'],
    'post_adoption_grouped_paths': POST_ADOPTION['ledger_counts']['grouped_paths'],
    'post_adoption_unverified_paths': POST_ADOPTION['ledger_counts']['unverified_paths'],
    'post_adoption_result': POST_ADOPTION['canonical_group_state'],
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
        'basis': 'historical direct read of the documented 49-file Marketplace/Payments/Wallet production batch, bounded to this exact family by immutable source enumeration',
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
            'historical 49-file direct-read evidence is bound exactly and this family is its exact enumerated subset',
            'historical and frozen current app trees are byte-identical',
            f'historical and frozen current {prefix} trees contain exactly the same {count} regular-file leaves and blob identities',
            'the dependent binding map is exactly the required 23 paths and contains all 13 focused test files',
            'the exact frozen-current 13-file qualification passes with 45 cases / 444 assertions / 0 failures / 0 errors / 0 skips',
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
            'focused_current_tests': PRIMARY_QUALIFICATION['focused_current_tests'],
            'outcome': OUTCOME,
        },
    }


def expected_candidate(adopted: bool) -> dict:
    expected = {
        'schema_version': 1,
        'candidate_id': 'PLATFORM-MARKETPLACE-PAYMENTS-WALLET-HISTORICAL-DIRECT-CARRYFORWARD',
        'repository': 'Oteryn/Oteryn-Platform',
        'state': ADOPTED if adopted else QUALIFIED_PENDING,
        'expected_total': 49,
        'historical_evidence': {
            'repository': 'Oteryn/Oteryn-Platform',
            'publication_commit': EVIDENCE_COMMIT,
            'publication_tree': EVIDENCE_TREE,
            'evidence_path': EVIDENCE_PATH,
            'evidence_blob': EVIDENCE_BLOB,
            'audited_main_sha': HISTORICAL_COMMIT,
            'audited_main_tree': HISTORICAL_TREE,
            'exact_statement': EXACT_STATEMENT,
            'basis': 'historical direct read of the documented 49-file Marketplace/Payments/Wallet production batch',
        },
        'current_revalidation': {
            'source_commit': SOURCE_COMMIT,
            'source_tree': SOURCE_TREE,
            'historical_app_tree': APP_TREE,
            'current_app_tree': APP_TREE,
            'families': [
                {'id': family_id, 'path_prefix': prefix, 'expected_count': count, 'tree_sha': tree_sha}
                for family_id, prefix, count, tree_sha in EXPECTED_FAMILIES
            ],
            'dependent_blobs': EXPECTED_DEPENDENT_BLOBS,
            'focused_test_files': list(FOCUSED_TEST_FILES),
            'required_checks': list(CANDIDATE_REQUIRED_CHECKS),
        },
        'coverage_adopted': adopted,
        'limitations': CANDIDATE_LIMITATIONS,
        'qualification': PRIMARY_QUALIFICATION,
    }
    if adopted:
        expected['post_adoption_revalidation'] = POST_ADOPTION
    return expected


def validate_verification_index(index_doc: dict) -> None:
    require(type(index_doc.get('schema_version')) is int and index_doc['schema_version'] == 1, 'verification-index schema')
    require(
        json_exact(index_doc.get('r3_platform_marketplace_payments_wallet_qualification'), EXPECTED_INDEX_ROW),
        'Marketplace verification-index record must exactly match bound candidate evidence',
    )


def validate_candidate_shape(candidate) -> bool:
    require(type(candidate.get('schema_version')) is int and candidate['schema_version'] == 1, 'candidate schema')
    require(candidate.get('candidate_id') == 'PLATFORM-MARKETPLACE-PAYMENTS-WALLET-HISTORICAL-DIRECT-CARRYFORWARD', 'candidate id')
    require(candidate.get('repository') == 'Oteryn/Oteryn-Platform', 'candidate repository')
    state = candidate.get('state')
    require(state in {QUALIFIED_PENDING, ADOPTED}, 'candidate state')
    adopted = state == ADOPTED
    require(type(candidate.get('coverage_adopted')) is bool, 'candidate adoption type')
    require(candidate['coverage_adopted'] is adopted, 'candidate adoption/state mismatch')
    require(type(candidate.get('expected_total')) is int and candidate['expected_total'] == 49, 'candidate total')

    hist = candidate.get('historical_evidence') or {}
    require(hist.get('repository') == 'Oteryn/Oteryn-Platform', 'historical repository')
    require(hist.get('publication_commit') == EVIDENCE_COMMIT, 'historical publication commit')
    require(hist.get('publication_tree') == EVIDENCE_TREE, 'historical publication tree')
    require(hist.get('evidence_path') == EVIDENCE_PATH, 'historical evidence path')
    require(hist.get('evidence_blob') == EVIDENCE_BLOB, 'historical evidence blob')
    require(hist.get('audited_main_sha') == HISTORICAL_COMMIT, 'historical source commit')
    require(hist.get('audited_main_tree') == HISTORICAL_TREE, 'historical source tree')
    require(hist.get('exact_statement') == EXACT_STATEMENT, 'historical direct-read statement')

    current = candidate.get('current_revalidation') or {}
    require(current.get('source_commit') == SOURCE_COMMIT, 'frozen source commit')
    require(current.get('source_tree') == SOURCE_TREE, 'frozen source tree')
    require(current.get('historical_app_tree') == APP_TREE and current.get('current_app_tree') == APP_TREE, 'app tree binding')
    rows = current.get('families')
    require(isinstance(rows, list), 'family list')
    specs = tuple((r.get('id'), r.get('path_prefix'), r.get('expected_count'), r.get('tree_sha')) for r in rows)
    require(specs == EXPECTED_FAMILIES, 'family set/order/count/tree bindings must be exact')
    deps = current.get('dependent_blobs')
    require(isinstance(deps, dict), 'dependent blob map')
    require(set(deps) == EXPECTED_DEPENDENT_PATHS and len(deps) == 23, 'dependent path set must be exact 23 bindings')
    require(deps == EXPECTED_DEPENDENT_BLOBS, 'dependent blob bindings must be exact')
    require(tuple(current.get('focused_test_files') or ()) == FOCUSED_TEST_FILES, 'focused test set/order must be exact 13 files')
    require(set(FOCUSED_TEST_FILES).issubset(deps), 'every focused test must be blob-bound')

    qualification = candidate.get('qualification')
    require(isinstance(qualification, dict), 'qualified candidate missing primary qualification')
    require(json_exact(qualification, PRIMARY_QUALIFICATION), 'candidate qualification must equal exact bound run/result')
    if adopted:
        require(json_exact(candidate.get('post_adoption_revalidation'), POST_ADOPTION), 'post-adoption evidence must be bound only after adopted-state requalification')
    else:
        require('post_adoption_revalidation' not in candidate, 'pending adoption candidate cannot carry post-adoption revalidation')
    require(json_exact(candidate, expected_candidate(adopted)), 'candidate canonical evidence fields/key sets drift')
    return adopted


def validate_group_state(candidate: dict, groups_doc: dict, adopted: bool) -> None:
    require(type(groups_doc.get('schema_version')) is int and groups_doc['schema_version'] == 1, 'coverage group schema')
    groups = groups_doc.get('groups')
    require(isinstance(groups, list), 'coverage groups missing')
    ids = {spec[0] for spec in EXPECTED_FAMILIES}
    accepted = [row for row in groups if row.get('id') in ids]
    if adopted:
        require(len(accepted) == 3, 'adopted Marketplace/Payments/Wallet families missing/duplicated canonical groups')
        by_id = {row.get('id'): row for row in accepted}
        require(len(by_id) == 3, 'duplicate adopted Marketplace/Payments/Wallet group id')
        for spec in EXPECTED_FAMILIES:
            require(json_exact(by_id.get(spec[0]), expected_group(candidate, spec)), 'adopted group drift: ' + spec[0])
    else:
        require(accepted == [], 'qualified pending Marketplace/Payments/Wallet candidate already has accepted group records')


def verify(audit_root: Path, platform_root: Path, evidence_root: Path):
    candidate = read_json(audit_root / CANDIDATE)
    adopted = validate_candidate_shape(candidate)
    validate_group_state(candidate, read_json(audit_root / GROUPS), adopted)
    validate_verification_index(read_json(audit_root / INDEX))
    hist = candidate['historical_evidence']
    current = candidate['current_revalidation']

    require(text(platform_root, 'rev-parse', 'HEAD') == SOURCE_COMMIT, 'wrong frozen Platform source')
    require(text(platform_root, 'rev-parse', 'HEAD^{tree}') == SOURCE_TREE, 'wrong frozen Platform tree')
    require(text(platform_root, 'rev-parse', HISTORICAL_COMMIT + '^{tree}') == HISTORICAL_TREE, 'wrong historical Platform source tree')
    require(text(evidence_root, 'rev-parse', 'HEAD') == EVIDENCE_COMMIT, 'wrong Platform audit publication')
    require(text(evidence_root, 'rev-parse', 'HEAD^{tree}') == EVIDENCE_TREE, 'wrong Platform audit publication tree')

    evidence_path = evidence_root / EVIDENCE_PATH
    require(evidence_path.is_file() and not evidence_path.is_symlink(), 'historical evidence path invalid')
    raw = evidence_path.read_bytes()
    require(blob_sha(raw) == EVIDENCE_BLOB, 'historical evidence blob mismatch')
    require(raw.decode('utf-8').count(EXACT_STATEMENT) == 1, 'historical 49-file direct-read statement missing/duplicated')

    require(text(platform_root, 'rev-parse', HISTORICAL_COMMIT + ':app') == APP_TREE, 'historical app tree mismatch')
    require(text(platform_root, 'rev-parse', SOURCE_COMMIT + ':app') == APP_TREE, 'current app tree mismatch')

    total = 0
    family_results = []
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
    require(total == 49, 'qualified family total')

    deps = current['dependent_blobs']
    for path in sorted(EXPECTED_DEPENDENT_PATHS):
        actual = text(platform_root, 'rev-parse', SOURCE_COMMIT + ':' + path)
        require(actual == deps[path], 'frozen-current dependent blob mismatch: ' + path)

    if adopted:
        result = 'MARKETPLACE_PAYMENTS_WALLET_GROUPED_ADOPTION_PRIMARY_PROOF_REVALIDATED_NOT_PRODUCT_PASS'
        next_gate = 'fresh independent exact-head review; retain temporary qualification and ledger evidence until review completes'
    else:
        result = 'MARKETPLACE_PAYMENTS_WALLET_PRIMARY_QUALIFIED_NOT_ADOPTED'
        next_gate = 'reproduce projected ledger digest and atomically adopt three exact GROUPED records or leave all 49 UNVERIFIED'

    return {
        'result': result,
        'candidate_id': candidate['candidate_id'],
        'historical_source': HISTORICAL_COMMIT,
        'current_source': SOURCE_COMMIT,
        'paths': total,
        'families': family_results,
        'dependent_blobs_verified': len(deps),
        'focused_test_files_bound': len(FOCUSED_TEST_FILES),
        'primary_qualification': PRIMARY_QUALIFICATION,
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
