#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

CANDIDATE = Path('docs/evidence/organization-audit-20260907/r3-platform-marketplace-tests-candidate.json')
GROUPS = Path('docs/evidence/organization-audit-20260907/coverage-groups.json')
SUMMARY = Path('docs/evidence/organization-audit-20260907/coverage-summary.json')
REPORT = Path('docs/evidence/OTERYN-ORGANIZATION-COMPREHENSIVE-AUDIT-20260907.json')
MARKDOWN_REPORT = Path('docs/evidence/OTERYN-ORGANIZATION-COMPREHENSIVE-AUDIT-20260907.md')
INDEX = Path('docs/evidence/organization-audit-20260907/verification-index.json')
EVIDENCE_PATH = 'docs/testing/OTERYN_PLATFORM_REPOSITORY_AUDIT_2026-09-06-CONTINUATION.md'

GROUP_ID = 'PLATFORM-MARKETPLACE-TESTS-HISTORICAL-DIRECT-CARRYFORWARD'
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
ADOPTED = 'QUALIFIED_ADOPTED_AS_GROUPED'
MARKETPLACE_LEDGER_SHA = '25ed5eb371279fbdb16a50263637856a3bc409b775387555efdaa17cebdc3617'
CANONICAL_LEDGER_SHA = '2d823435f76f0c08b118ccb5dc1c9ccf9ef4acc41bffdd447b260e82ea404b0f'
MARKETPLACE_CLOSEOUT = (
    'The exact six-file `tests/Feature/Marketplace/**` GROUPED batch completed fresh independent exact-head review at '
    '`7f53b509791aae6d56637522aee65891e449914c` with no new P0/P1/P2; its two temporary qualifier/ledger workflows '
    'were removed on cleanup head `fbe839699782ad1d6df7a5841162d4a467d60c10`, whose META CI `34341624468` succeeded.'
)
MARKETPLACE_CLOSEOUT_PREDECESSOR = (
    '`DIRECT` is a bounded review with the stated scope, not full approval of the entire file or every dependency.'
)
MARKETPLACE_CLOSEOUT_SUCCESSOR = (
    'Two additional frozen Platform leaves are now adopted as DIRECT bounded full-file reviews:'
)
STALE_MARKETPLACE_GATES = (
    'Post-adoption exact-head proof and fresh independent review are still required.',
    'The remaining gate for this six-path batch is fresh independent exact-head review',
    'temporary qualifier and ledger workflows remain until that review completes',
    'The still-later 49-path Marketplace/Payments/Wallet expansion is new material and therefore requires its own fresh independent exact-head review.',
)

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
PRIMARY = {
    'qualification_head': 'f54e5b0640945d7a5f0a7c471ac81105436214ae', 'workflow_run': 34323945126, 'job': 102376779500,
    'verifier_unit_tests': 10, 'verifier_unit_result': 'PASS',
    'focused_current_tests': {
        'test_files': 6, 'junit_files': 3, 'cases': 17, 'assertions': 179, 'failures': 0, 'errors': 0, 'skipped': 0,
        'junit': [
            {'file': 'ordinary.xml', 'cases': 14, 'assertions': 110, 'failures': 0, 'errors': 0, 'skipped': 0},
            {'file': 'transfer-concurrency.xml', 'cases': 1, 'assertions': 54, 'failures': 0, 'errors': 0, 'skipped': 0},
            {'file': 'transfer.xml', 'cases': 2, 'assertions': 15, 'failures': 0, 'errors': 0, 'skipped': 0},
        ],
    },
    'php': '8.5.10', 'mariadb': '11.8.9', 'composer_validate': 'PASS', 'tracked_source_clean_after_execution': True,
    'outcome': 'QUALIFIED_PRIMARY_NOT_YET_ADOPTED',
}
PRE_ADOPTION = {
    'audit_head': '1999409a1205b7bdb5663a809992b9c44efd8dbb', 'workflow_run': 34329669372, 'job': 102395040735,
    'result': 'PASS', 'verifier_unit_tests': 13, 'focused_current_tests': PRIMARY['focused_current_tests'], 'php': '8.5.10',
    'mariadb': '11.8.9', 'meta_ci_run': 34329669391, 'meta_ci_result': 'SUCCESS',
}
PROJECTED_LEDGER = {
    'projection_head': '1999409a1205b7bdb5663a809992b9c44efd8dbb', 'workflow_run': 34329669431, 'job': 102395041138,
    'artifact': 10095210015, 'source_rows': 4325, 'direct_paths': 221, 'grouped_paths': 113, 'unverified_paths': 3991,
    'new_grouped_paths': sorted(EXPECTED_PATH_BLOBS), 'ledger_sha256': MARKETPLACE_LEDGER_SHA, 'outcome': 'PROJECTED_LEDGER_PASS',
}
POST_ADOPTION = {
    'audit_head': 'c67c1e9d7622612affdd431b2af9fae05d0d11ef', 'workflow_run': 34333058684, 'job': 102405922454,
    'result': 'PASS', 'canonical_group_state': 'MARKETPLACE_TESTS_GROUPED_ADOPTION_PRIMARY_PROOF_REVALIDATED_NOT_PRODUCT_PASS',
    'verifier_unit_tests': 14,
    'focused_current_tests': {
        'test_files': 6, 'junit_files': 3, 'cases': 17, 'assertions': 179, 'failures': 0, 'errors': 0, 'skipped': 0,
        'junit': [
            {'file': 'ordinary.xml', 'cases': 14, 'assertions': 110, 'failures': 0, 'errors': 0, 'skipped': 0},
            {'file': 'transfer-concurrency.xml', 'cases': 1, 'assertions': 54, 'failures': 0, 'errors': 0, 'skipped': 0},
            {'file': 'transfer.xml', 'cases': 2, 'assertions': 15, 'failures': 0, 'errors': 0, 'skipped': 0},
        ],
    },
    'php': '8.5.10', 'mariadb': '11.8.9', 'meta_ci_run': 34333058582, 'meta_ci_result': 'SUCCESS',
    'ledger_reproduction_run': 34333058620, 'ledger_reproduction_job': 102405921741,
    'ledger_reproduction_artifact': 10096546256, 'ledger_sha256': MARKETPLACE_LEDGER_SHA,
    'ledger_counts': {'source_rows': 4325, 'direct_paths': 221, 'grouped_paths': 113, 'unverified_paths': 3991},
}
CANDIDATE_LIMITATIONS = (
    'Adopted only as bounded GROUPED carry-forward after immutable historical direct-read evidence explicitly names all six files, '
    'exact historical/frozen tree/path/blob identity, the exact bound 17-case/179-assertion all-green qualification including both real-MariaDB tests, '
    'and projected-ledger reproduction proving only these six rows transition UNVERIFIED to GROUPED. Fresh independent exact-head review completed at '
    '7f53b509791aae6d56637522aee65891e449914c with no new P0/P1/P2; the temporary qualifier and ledger workflows were removed at cleanup head '
    'fbe839699782ad1d6df7a5841162d4a467d60c10. This does not establish production readiness, complete Marketplace/payment correctness, '
    'later-current-main status, provider remediation, or organization-wide audit completion.'
)
GROUP_SCOPE = (
    'Historical direct-read evidence explicitly names every file in the exact six-file Marketplace test directory; frozen-current carry-forward '
    'is bounded by exact tree/path/blob identity and the bound 17-case/179-assertion all-green qualification including both real-MariaDB tests.'
)
GROUP_LIMITATIONS = (
    'Adopted only as bounded GROUPED carry-forward. Fresh independent exact-head review completed at '
    '7f53b509791aae6d56637522aee65891e449914c with no new P0/P1/P2; the temporary qualifier and ledger workflows were removed at cleanup head '
    'fbe839699782ad1d6df7a5841162d4a467d60c10. This does not establish production readiness, complete Marketplace/payment correctness, '
    'later-current-main status, provider remediation, or organization-wide audit completion.'
)


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def json_exact(left, right) -> bool:
    if type(left) is not type(right): return False
    if isinstance(left, dict): return left.keys() == right.keys() and all(json_exact(left[k], right[k]) for k in left)
    if isinstance(left, list): return len(left) == len(right) and all(json_exact(a, b) for a, b in zip(left, right))
    return left == right


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
        'schema_version': 1, 'candidate_id': GROUP_ID, 'repository': 'Oteryn/Oteryn-Platform', 'state': ADOPTED, 'expected_total': 6,
        'historical_evidence': {
            'publication_commit': EVIDENCE_COMMIT, 'publication_tree': EVIDENCE_TREE, 'evidence_path': EVIDENCE_PATH, 'evidence_blob': EVIDENCE_BLOB,
            'audited_main_sha': HISTORICAL_COMMIT, 'audited_main_tree': HISTORICAL_TREE, 'exact_statement': EXACT_STATEMENT,
            'basis': 'immutable historical evidence explicitly names every file in the six-file Marketplace test directory',
        },
        'current_revalidation': {
            'source_commit': SOURCE_COMMIT, 'source_tree': SOURCE_TREE, 'path_prefix': PREFIX, 'historical_tree': MARKETPLACE_TEST_TREE,
            'current_tree': MARKETPLACE_TEST_TREE, 'path_blobs': EXPECTED_PATH_BLOBS, 'focused_test_files': list(FOCUSED_TEST_FILES),
            'required_checks': list(REQUIRED_CHECKS),
        },
        'coverage_adopted': True, 'limitations': CANDIDATE_LIMITATIONS, 'qualification': PRIMARY,
        'pre_adoption_revalidation': PRE_ADOPTION, 'projected_ledger': PROJECTED_LEDGER, 'post_adoption_revalidation': POST_ADOPTION,
    }


def expected_group() -> dict:
    return {
        'id': GROUP_ID, 'repository': 'platform', 'disposition': 'GROUPED', 'path_prefix': PREFIX, 'expected_count': 6,
        'depth': 'GROUPED_REVALIDATED', 'scope': GROUP_SCOPE, 'limitations': GROUP_LIMITATIONS,
        'historical_evidence': {
            'repository': 'Oteryn/Oteryn-Platform', 'publication_commit': EVIDENCE_COMMIT, 'publication_tree': EVIDENCE_TREE,
            'coverage_rules_path': EVIDENCE_PATH, 'coverage_rules_blob': EVIDENCE_BLOB, 'audited_main_sha': HISTORICAL_COMMIT,
            'audited_main_tree': HISTORICAL_TREE, 'exact_statement': EXACT_STATEMENT, 'pattern': PREFIX + '**', 'count': 6,
            'basis': 'immutable historical evidence explicitly names every file in the six-file Marketplace test directory',
        },
        'current_revalidation': {
            'source_commit': SOURCE_COMMIT, 'source_tree': SOURCE_TREE, 'family_tree': MARKETPLACE_TEST_TREE,
            'changed_paths_under_group_prefix': 0, 'historical_to_current_compare_status': 'ahead',
            'current_blobs': EXPECTED_PATH_BLOBS, 'required_checks': list(REQUIRED_CHECKS), 'focused_test_files': list(FOCUSED_TEST_FILES),
        },
        'evaluation': {
            'qualification_head': PRIMARY['qualification_head'], 'qualification_run': PRIMARY['workflow_run'], 'qualification_job': PRIMARY['job'],
            'verifier_unit_tests': PRIMARY['verifier_unit_tests'], 'focused_current_tests': PRIMARY['focused_current_tests'],
            'pre_adoption_revalidation': PRE_ADOPTION, 'projected_ledger': PROJECTED_LEDGER,
            'post_adoption_revalidation': POST_ADOPTION, 'outcome': 'ADOPTED_GROUPED_CARRY_FORWARD',
        },
    }


def expected_index_row() -> dict:
    return {
        'frozen_source_commit': SOURCE_COMMIT, 'historical_source_commit': HISTORICAL_COMMIT, 'family_tree': MARKETPLACE_TEST_TREE,
        'exact_total_paths': 6, 'path_blob_bindings': 6, 'focused_test_files': 6, 'primary_qualification_head': PRIMARY['qualification_head'],
        'primary_run': PRIMARY['workflow_run'], 'primary_job': PRIMARY['job'], 'primary_verifier_unit_tests': PRIMARY['verifier_unit_tests'],
        'focused_cases': 17, 'focused_assertions': 179, 'failures': 0, 'errors': 0, 'skips': 0, 'php': '8.5.10', 'mariadb': '11.8.9',
        'qualification_binding_head': 'b8f7aba0ed08813203f64ae56cac5ef7f857af93', 'qualification_binding_run': 34329383462,
        'qualification_binding_job': 102394131869, 'qualification_binding_verifier_unit_tests': 13,
        'pre_adoption_head': PRE_ADOPTION['audit_head'], 'pre_adoption_run': PRE_ADOPTION['workflow_run'], 'pre_adoption_job': PRE_ADOPTION['job'],
        'pre_adoption_meta_ci_run': PRE_ADOPTION['meta_ci_run'], 'projected_ledger_run': PROJECTED_LEDGER['workflow_run'],
        'projected_ledger_job': PROJECTED_LEDGER['job'], 'projected_ledger_artifact': PROJECTED_LEDGER['artifact'],
        'projected_ledger_sha256': MARKETPLACE_LEDGER_SHA, 'projected_grouped_paths': 113, 'projected_unverified_paths': 3991,
        'qualification': 'BOUNDED_GROUPED_CARRY_FORWARD_NOT_PRODUCT_PASS', 'post_adoption_head': POST_ADOPTION['audit_head'],
        'post_adoption_run': POST_ADOPTION['workflow_run'], 'post_adoption_job': POST_ADOPTION['job'],
        'post_adoption_verifier_unit_tests': POST_ADOPTION['verifier_unit_tests'], 'post_adoption_meta_ci_run': POST_ADOPTION['meta_ci_run'],
        'post_adoption_ledger_run': POST_ADOPTION['ledger_reproduction_run'], 'post_adoption_ledger_job': POST_ADOPTION['ledger_reproduction_job'],
        'post_adoption_ledger_artifact': POST_ADOPTION['ledger_reproduction_artifact'], 'post_adoption_ledger_sha256': POST_ADOPTION['ledger_sha256'],
        'post_adoption_grouped_paths': POST_ADOPTION['ledger_counts']['grouped_paths'],
        'post_adoption_unverified_paths': POST_ADOPTION['ledger_counts']['unverified_paths'], 'post_adoption_result': POST_ADOPTION['canonical_group_state'],
    }


def validate_candidate_shape(candidate: dict) -> None:
    require(json_exact(candidate, expected_candidate()), 'Marketplace-test adopted candidate canonical evidence fields/key sets drift')


def validate_group_state(groups_doc: dict) -> None:
    require(type(groups_doc.get('schema_version')) is int and groups_doc['schema_version'] == 1, 'coverage-groups schema')
    groups = groups_doc.get('groups')
    require(isinstance(groups, list), 'coverage-groups groups must be a list')
    rows = [g for g in groups if isinstance(g, dict) and g.get('id') == GROUP_ID]
    require(len(rows) == 1, 'Marketplace-test canonical group missing/duplicated')
    require(json_exact(rows[0], expected_group()), 'Marketplace-test canonical group drift')
    target_paths = set(EXPECTED_PATH_BLOBS)
    for group in groups:
        if group is rows[0] or not isinstance(group, dict): continue
        prefix = group.get('path_prefix')
        if isinstance(prefix, str): require(not any(path.startswith(prefix) for path in target_paths), f'Marketplace-test overlap with group {group.get("id")}')
        paths = group.get('paths')
        if isinstance(paths, list): require(not target_paths.intersection(paths), f'Marketplace-test explicit overlap with group {group.get("id")}')


def validate_companion_report_text(text: str) -> None:
    paragraphs = [paragraph.replace('\n', ' ').strip() for paragraph in text.split('\n\n')]
    closeout_paragraphs = [paragraph for paragraph in paragraphs if MARKETPLACE_CLOSEOUT in paragraph]
    require(closeout_paragraphs == [MARKETPLACE_CLOSEOUT],
            'Marketplace-test companion Markdown complete closeout paragraph missing/duplicated/drifted')
    predecessor_indexes = [i for i, paragraph in enumerate(paragraphs)
                           if paragraph.startswith(MARKETPLACE_CLOSEOUT_PREDECESSOR)]
    successor_indexes = [i for i, paragraph in enumerate(paragraphs)
                         if paragraph.startswith(MARKETPLACE_CLOSEOUT_SUCCESSOR)]
    closeout_index = paragraphs.index(MARKETPLACE_CLOSEOUT)
    require(predecessor_indexes == [closeout_index - 1] and successor_indexes == [closeout_index + 1],
            'Marketplace-test companion Markdown bounded closeout slot has inserted/missing/drifted paragraphs')
    for stale in STALE_MARKETPLACE_GATES:
        require(stale not in text, 'Marketplace-test companion Markdown retains stale review/workflow gate')


def validate_accounting(audit_root: Path) -> None:
    validate_companion_report_text((audit_root / MARKDOWN_REPORT).read_text(encoding='utf-8'))
    summary = read_json(audit_root / SUMMARY); platform = summary['per_repository']['platform']
    require((platform['leaves'], platform['direct_scoped'], platform['grouped'], platform['unverified_semantics']) == (2165, 158, 113, 1894), 'Marketplace-test summary platform accounting drift')
    require(summary.get('ledger_sha256') == CANONICAL_LEDGER_SHA, 'Marketplace-test current canonical ledger digest drift')
    require((summary.get('grouped_revalidated_paths'), summary.get('semantically_classified_paths'), summary.get('unverified_semantics_total')) == (113, 336, 3989), 'Marketplace-test summary totals drift')
    report = read_json(audit_root / REPORT)
    require(report.get('revision') == 'R3-NATIVE-EVIDENCE-POST-REVIEW-PLATFORM-SEMANTIC-CARRYFORWARD-113-DIRECT-223', 'Marketplace-test report revision drift')
    require((report.get('scoped_review_paths'), report.get('grouped_revalidated_paths'), report.get('semantically_classified_paths')) == (223, 113, 336), 'Marketplace-test report accounting drift')
    require(report.get('r3_platform_marketplace_tests_candidate') == 'organization-audit-20260907/r3-platform-marketplace-tests-candidate.json', 'Marketplace-test report candidate binding drift')
    index = read_json(audit_root / INDEX)
    require(json_exact(index.get('r3_platform_marketplace_tests_qualification'), expected_index_row()), 'Marketplace-test verification-index row drift')


def git(root: Path, *args: str) -> str:
    return subprocess.run(['git', '-C', str(root), *args], check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30).stdout.strip()


def tree_entries(root: Path, commit: str) -> dict[str, tuple[str, str]]:
    raw = subprocess.run(['git', '-C', str(root), 'ls-tree', '-r', '-z', '--full-tree', commit, '--', PREFIX], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30).stdout
    entries = {}
    for item in raw.split(b'\0'):
        if not item: continue
        meta, path_bytes = item.split(b'\t', 1); mode, kind, sha = meta.decode().split(); path = path_bytes.decode()
        require(kind == 'blob' and mode == '100644', f'unexpected Marketplace test entry {path}: {mode} {kind}')
        entries[path] = (mode, sha)
    return entries


def verify(audit_root: Path, platform_root: Path, evidence_root: Path) -> dict:
    candidate = read_json(audit_root / CANDIDATE)
    validate_candidate_shape(candidate); validate_group_state(read_json(audit_root / GROUPS)); validate_accounting(audit_root)
    require(git(platform_root, 'rev-parse', 'HEAD') == SOURCE_COMMIT, 'frozen Platform HEAD drift')
    require(git(platform_root, 'rev-parse', 'HEAD^{tree}') == SOURCE_TREE, 'frozen Platform tree drift')
    require(git(platform_root, 'rev-parse', f'{HISTORICAL_COMMIT}^{{tree}}') == HISTORICAL_TREE, 'historical Platform tree drift')
    require(git(platform_root, 'rev-parse', f'{HISTORICAL_COMMIT}:tests/Feature/Marketplace') == MARKETPLACE_TEST_TREE, 'historical Marketplace-test tree drift')
    require(git(platform_root, 'rev-parse', f'{SOURCE_COMMIT}:tests/Feature/Marketplace') == MARKETPLACE_TEST_TREE, 'frozen Marketplace-test tree drift')
    expected_entries = {path: ('100644', sha) for path, sha in EXPECTED_PATH_BLOBS.items()}
    historical_entries = tree_entries(platform_root, HISTORICAL_COMMIT); current_entries = tree_entries(platform_root, SOURCE_COMMIT)
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
        'result': 'MARKETPLACE_TESTS_GROUPED_ADOPTION_REVIEWED_AND_CLEANED_NOT_PRODUCT_PASS', 'candidate_id': GROUP_ID,
        'historical_source': HISTORICAL_COMMIT, 'current_source': SOURCE_COMMIT, 'path_prefix': PREFIX, 'tree_sha': MARKETPLACE_TEST_TREE,
        'paths': 6, 'path_blobs_verified': 6, 'focused_test_files_bound': 6, 'primary_qualification': PRIMARY,
        'pre_adoption_revalidation': PRE_ADOPTION, 'projected_ledger': PROJECTED_LEDGER, 'post_adoption_revalidation': POST_ADOPTION,
        'coverage_adopted': True, 'marketplace_batch_ledger_sha256': MARKETPLACE_LEDGER_SHA,
        'current_canonical_ledger_sha256': CANONICAL_LEDGER_SHA,
        'independent_review_head': '7f53b509791aae6d56637522aee65891e449914c',
        'cleanup_head': 'fbe839699782ad1d6df7a5841162d4a467d60c10', 'next_gate': 'NONE_FOR_MARKETPLACE_TEST_BATCH',
    }


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument('--audit-root', type=Path, default=Path('.'))
    parser.add_argument('--platform-root', type=Path, required=True); parser.add_argument('--evidence-root', type=Path, required=True)
    args = parser.parse_args(); print(json.dumps(verify(args.audit_root.resolve(), args.platform_root.resolve(), args.evidence_root.resolve()), indent=2))


if __name__ == '__main__':
    main()
