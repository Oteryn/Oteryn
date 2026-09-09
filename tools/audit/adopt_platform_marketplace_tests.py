#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'docs/evidence/organization-audit-20260907'
CANDIDATE = BASE / 'r3-platform-marketplace-tests-candidate.json'
GROUPS = BASE / 'coverage-groups.json'
SUMMARY = BASE / 'coverage-summary.json'
REPORT = ROOT / 'docs/evidence/OTERYN-ORGANIZATION-COMPREHENSIVE-AUDIT-20260907.json'
INDEX = BASE / 'verification-index.json'
MARKDOWN = ROOT / 'docs/evidence/OTERYN-ORGANIZATION-COMPREHENSIVE-AUDIT-20260907.md'

GROUP_ID = 'PLATFORM-MARKETPLACE-TESTS-HISTORICAL-DIRECT-CARRYFORWARD'
SOURCE_COMMIT = 'de917b3477a1de0667531380de3660e8b2ab59aa'
SOURCE_TREE = 'ffdf2a286d3a39f2344cf2ff53b28e4ef7369a8e'
HISTORICAL_COMMIT = '3b2ea1c7392187d5d22488673073dc8f8305a374'
HISTORICAL_TREE = '0f320dd073bc2619307314e380017526d27e5ddb'
EVIDENCE_COMMIT = '3fe7df5330deb9ed38cc17ae1710f0cb4159019b'
EVIDENCE_TREE = 'c6ac8cb7cbff069d7ac7303b3472d992da254774'
EVIDENCE_PATH = 'docs/testing/OTERYN_PLATFORM_REPOSITORY_AUDIT_2026-09-06-CONTINUATION.md'
EVIDENCE_BLOB = '34361414339a5ca57ec5cd13e332ad196aa9e35f'
TREE = '03f7d3735dee4140bf75960f0e106c3ba3d3b37b'
PREFIX = 'tests/Feature/Marketplace/'
STATEMENT = '**FACT.** The following Marketplace tests were read directly during continuation:'
OLD_LEDGER = '742443fbcc7fba9a45e1c71bf4395e3b2fe4ced7ae527a38de6ef2c74cb49406'
NEW_LEDGER = '25ed5eb371279fbdb16a50263637856a3bc409b775387555efdaa17cebdc3617'

PATH_BLOBS = {
    'tests/Feature/Marketplace/CanaryCharacterTransferConcurrencyMariaDbTest.php': 'f9b9a17d34003132acf877a9755b998d6cfa5403',
    'tests/Feature/Marketplace/CanaryCharacterTransferMariaDbIntegrationTest.php': '14aa475be873476523eae72775b02acad956c8df',
    'tests/Feature/Marketplace/MarketplaceAuctionTerminalRecoveryConcurrencyTest.php': '41df060eb0b14828e6331aa78e86e6f1a27b5334',
    'tests/Feature/Marketplace/MarketplaceIdempotencyTest.php': 'a3e70ea8019ceaa636afd3c4030c84190c68e077',
    'tests/Feature/Marketplace/MarketplaceModuleTest.php': 'cd545576fba348f5f17e5e527882e8b4c142c6ad',
    'tests/Feature/Marketplace/MarketplaceSettlementRecoveryTest.php': 'e1a8bd57d63a9c86427f0d0140e23147147b6dd2',
}
FOCUSED = [
    'tests/Feature/Marketplace/MarketplaceAuctionTerminalRecoveryConcurrencyTest.php',
    'tests/Feature/Marketplace/MarketplaceIdempotencyTest.php',
    'tests/Feature/Marketplace/MarketplaceModuleTest.php',
    'tests/Feature/Marketplace/MarketplaceSettlementRecoveryTest.php',
    'tests/Feature/Marketplace/CanaryCharacterTransferMariaDbIntegrationTest.php',
    'tests/Feature/Marketplace/CanaryCharacterTransferConcurrencyMariaDbTest.php',
]
CHECKS = [
    'historical audit publication commit/tree/evidence blob match exactly',
    'historical evidence contains the direct-read statement and all six exact Marketplace test paths',
    'historical and frozen-current Marketplace test directory tree SHAs are identical',
    'both generations contain exactly the same six regular files and exact blob identities',
    'the exact frozen-current six-file qualification is bound to its exact head/run/job and JUnit totals',
    'fresh frozen-current execution repeats all six files with zero failures/errors/skips including both real-MariaDB tests',
]
PRIMARY = {
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
PRE = {
    'audit_head': '1999409a1205b7bdb5663a809992b9c44efd8dbb',
    'workflow_run': 34329669372,
    'job': 102395040735,
    'result': 'PASS',
    'verifier_unit_tests': 13,
    'focused_current_tests': PRIMARY['focused_current_tests'],
    'php': '8.5.10',
    'mariadb': '11.8.9',
    'meta_ci_run': 34329669391,
    'meta_ci_result': 'SUCCESS',
}
PROJECTED = {
    'projection_head': '1999409a1205b7bdb5663a809992b9c44efd8dbb',
    'workflow_run': 34329669431,
    'job': 102395041138,
    'artifact': 10095210015,
    'source_rows': 4325,
    'direct_paths': 221,
    'grouped_paths': 113,
    'unverified_paths': 3991,
    'new_grouped_paths': sorted(PATH_BLOBS),
    'ledger_sha256': NEW_LEDGER,
    'outcome': 'PROJECTED_LEDGER_PASS',
}

def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))

def write(path: Path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

def require(ok: bool, message: str):
    if not ok:
        raise SystemExit(message)

def replace_once(text: str, old: str, new: str, label: str) -> str:
    require(text.count(old) == 1, f'{label} anchor count={text.count(old)}')
    return text.replace(old, new, 1)

sys.path.insert(0, str(ROOT / 'tools/audit'))
import verify_platform_marketplace_tests_group as pre
candidate = pre.read_json(pre.CANDIDATE)
groups_doc = pre.read_json(pre.GROUPS)
pre.validate_candidate_shape(candidate)
pre.validate_group_absence(groups_doc)
require(candidate['coverage_adopted'] is False, 'candidate already adopted')
require(candidate['qualification'] == PRIMARY, 'primary qualification drift')

candidate['state'] = 'QUALIFIED_ADOPTED_AS_GROUPED_PENDING_POST_ADOPTION_REVALIDATION'
candidate['coverage_adopted'] = True
candidate['limitations'] = (
    'Adopted only as bounded GROUPED carry-forward after immutable historical direct-read evidence explicitly names all six files, '
    'exact historical/frozen tree/path/blob identity, the exact bound 17-case/179-assertion all-green qualification including both real-MariaDB tests, '
    'and projected-ledger reproduction proving only these six rows transition UNVERIFIED to GROUPED. This does not establish production readiness, '
    'complete Marketplace/payment correctness, later-current-main status, provider remediation, or organization-wide audit completion. '
    'Post-adoption exact-head qualifier/ledger/META proof and fresh independent review are still required.'
)
candidate['pre_adoption_revalidation'] = PRE
candidate['projected_ledger'] = PROJECTED
write(CANDIDATE, candidate)

group = {
    'id': GROUP_ID,
    'repository': 'platform',
    'disposition': 'GROUPED',
    'path_prefix': PREFIX,
    'expected_count': 6,
    'depth': 'GROUPED_REVALIDATED',
    'scope': (
        'Historical direct-read evidence explicitly names every file in the exact six-file Marketplace test directory; frozen-current carry-forward '
        'is bounded by exact tree/path/blob identity, the bound 17-case/179-assertion all-green qualification including both real-MariaDB tests, '
        'and exact projected-ledger reproduction.'
    ),
    'limitations': (
        'Adopted only as bounded GROUPED carry-forward. This does not establish production readiness, complete Marketplace/payment correctness, '
        'later-current-main status, provider remediation, or organization-wide audit completion. Post-adoption exact-head proof and fresh independent review remain required.'
    ),
    'historical_evidence': {
        'repository': 'Oteryn/Oteryn-Platform',
        'publication_commit': EVIDENCE_COMMIT,
        'publication_tree': EVIDENCE_TREE,
        'coverage_rules_path': EVIDENCE_PATH,
        'coverage_rules_blob': EVIDENCE_BLOB,
        'audited_main_sha': HISTORICAL_COMMIT,
        'audited_main_tree': HISTORICAL_TREE,
        'exact_statement': STATEMENT,
        'pattern': PREFIX + '**',
        'count': 6,
        'basis': 'immutable historical evidence explicitly names every file in the six-file Marketplace test directory',
    },
    'current_revalidation': {
        'source_commit': SOURCE_COMMIT,
        'source_tree': SOURCE_TREE,
        'family_tree': TREE,
        'changed_paths_under_group_prefix': 0,
        'historical_to_current_compare_status': 'ahead',
        'current_blobs': PATH_BLOBS,
        'required_checks': CHECKS,
        'focused_test_files': FOCUSED,
    },
    'evaluation': {
        'qualification_head': PRIMARY['qualification_head'],
        'qualification_run': PRIMARY['workflow_run'],
        'qualification_job': PRIMARY['job'],
        'verifier_unit_tests': PRIMARY['verifier_unit_tests'],
        'focused_current_tests': PRIMARY['focused_current_tests'],
        'pre_adoption_revalidation': PRE,
        'projected_ledger': PROJECTED,
        'outcome': 'ADOPTED_GROUPED_CARRY_FORWARD_PENDING_POST_ADOPTION_REVALIDATION',
    },
}
require(not any(g.get('id') == GROUP_ID for g in groups_doc['groups']), 'group already exists')
groups_doc['groups'].append(group)
write(GROUPS, groups_doc)

summary = load(SUMMARY)
p = summary['per_repository']['platform']
require(summary['ledger_sha256'] == OLD_LEDGER, 'pre-adoption summary digest drift')
require((p['direct_scoped'], p['grouped'], p['unverified_semantics']) == (156, 107, 1902), 'pre-adoption platform summary drift')
require((summary['grouped_revalidated_paths'], summary['semantically_classified_paths'], summary['unverified_semantics_total']) == (107, 328, 3997), 'pre-adoption summary totals drift')
p['grouped'] = 113
p['unverified_semantics'] = 1896
summary['ledger_sha256'] = NEW_LEDGER
summary['grouped_revalidated_paths'] = 113
summary['semantically_classified_paths'] = 334
summary['unverified_semantics_total'] = 3991
summary['durability'] = (
    'Full CSV accompanies the audit delivery. Committed DIRECT review rows, immutable Git trees, explicit accepted/rejected GROUPED records and verify_report.py reproduce every disposition. '
    'Platform GameAuth contributes 27 GROUPED paths; Accounts/CanaryIntegration/CharacterProfiles/Characters contribute 31; Marketplace/Payments/Wallet production code contributes 49; '
    'the exact six-file Marketplace test directory contributes 6; the rejected 508-file Atlas candidate remains UNVERIFIED.'
)
summary['coverage_dimension_note'] = (
    'DIRECT records bounded current/source review, not universal approval. GROUPED records bounded semantic carry-forward only when historical scope, exact identity and current dependent qualification are all bound. '
    'Platform contributes 113 GROUPED paths: GameAuth 27, account/Canary/profile/character 31, Marketplace/Payments/Wallet production code 49, and the exact six-file Marketplace test directory 6. '
    'The Atlas 508-path candidate remains rejected.'
)
write(SUMMARY, summary)

report = load(REPORT)
require(report['revision'] == 'R3-NATIVE-EVIDENCE-POST-REVIEW-PLATFORM-SEMANTIC-CARRYFORWARD-107', 'pre-adoption report revision drift')
require((report['scoped_review_paths'], report['grouped_revalidated_paths'], report['semantically_classified_paths']) == (221, 107, 328), 'pre-adoption report counts drift')
report['revision'] = 'R3-NATIVE-EVIDENCE-POST-REVIEW-PLATFORM-SEMANTIC-CARRYFORWARD-113'
report['grouped_revalidated_paths'] = 113
report['semantically_classified_paths'] = 334
report['r3_platform_marketplace_tests_candidate'] = 'organization-audit-20260907/r3-platform-marketplace-tests-candidate.json'
report['r3_review']['fresh_rereview_reason'] = (
    'The exact six-file Platform Marketplace test GROUPED expansion is new material after the clean d34f3ac Marketplace/Payments/Wallet production-code re-review; '
    'fresh independent exact-head review is required after post-adoption qualifier/ledger/META proof is bound.'
)
write(REPORT, report)

index = load(INDEX)
require('r3_platform_marketplace_tests_qualification' not in index, 'Marketplace-tests verification-index row already exists')
index['r3_platform_marketplace_tests_qualification'] = {
    'frozen_source_commit': SOURCE_COMMIT,
    'historical_source_commit': HISTORICAL_COMMIT,
    'family_tree': TREE,
    'exact_total_paths': 6,
    'path_blob_bindings': 6,
    'focused_test_files': 6,
    'primary_qualification_head': PRIMARY['qualification_head'],
    'primary_run': PRIMARY['workflow_run'],
    'primary_job': PRIMARY['job'],
    'primary_verifier_unit_tests': PRIMARY['verifier_unit_tests'],
    'focused_cases': 17,
    'focused_assertions': 179,
    'failures': 0,
    'errors': 0,
    'skips': 0,
    'php': '8.5.10',
    'mariadb': '11.8.9',
    'qualification_binding_head': 'b8f7aba0ed08813203f64ae56cac5ef7f857af93',
    'qualification_binding_run': 34329383462,
    'qualification_binding_job': 102394131869,
    'qualification_binding_verifier_unit_tests': 13,
    'pre_adoption_head': PRE['audit_head'],
    'pre_adoption_run': PRE['workflow_run'],
    'pre_adoption_job': PRE['job'],
    'pre_adoption_meta_ci_run': PRE['meta_ci_run'],
    'projected_ledger_run': PROJECTED['workflow_run'],
    'projected_ledger_job': PROJECTED['job'],
    'projected_ledger_artifact': PROJECTED['artifact'],
    'projected_ledger_sha256': NEW_LEDGER,
    'projected_grouped_paths': 113,
    'projected_unverified_paths': 3991,
    'qualification': 'BOUNDED_GROUPED_CARRY_FORWARD_NOT_PRODUCT_PASS',
    'post_adoption_status': 'PENDING',
}
write(INDEX, index)

md = MARKDOWN.read_text(encoding='utf-8')
md = replace_once(md, '| platform | 2165 | 156 | 107 | 1902 |', '| platform | 2165 | 156 | 113 | 1896 |', 'platform table')
md = replace_once(md, '| **Total** | **4325** | **221** | **107** | **3997** |', '| **Total** | **4325** | **221** | **113** | **3991** |', 'total table')
old_para = (
    'Exactly 107 Platform leaves are additionally GROUPED. GameAuth contributes 27 paths after exact historical/source identity, 23 dependent bindings and 61 focused cases / 565 assertions. '
    'Four account/Canary/profile/character families contribute 31 paths after exact 23 dependent bindings and an ordered 15-file qualification producing 86 cases / 586 assertions. '
    'Three Marketplace/Payments/Wallet families contribute 49 paths — `app/Marketplace/**` (21), `app/Payments/**` (24), `app/Wallet/**` (4) — after exact historical direct-read evidence, '
    'byte-identical family trees, exact 23 dependent bindings and an ordered 13-file PHP 8.5.10/MariaDB 11.8.9 qualification producing 45 cases / 444 assertions / 0 failures / 0 errors / 0 skips, '
    'including four real-MariaDB integration/concurrency files. GROUPED is bounded semantic carry-forward, not product/security readiness. The rejected Atlas 508-path candidate remains UNVERIFIED. '
    'Full CSV is reproducible from immutable inventories, `coverage-review.tsv`, `coverage-groups.json` and ledger SHA-256 `742443fbcc7fba9a45e1c71bf4395e3b2fe4ced7ae527a38de6ef2c74cb49406`.'
)
new_para = (
    'Exactly 113 Platform leaves are additionally GROUPED. GameAuth contributes 27 paths after exact historical/source identity, 23 dependent bindings and 61 focused cases / 565 assertions. '
    'Four account/Canary/profile/character families contribute 31 paths after exact 23 dependent bindings and an ordered 15-file qualification producing 86 cases / 586 assertions. '
    'Three Marketplace/Payments/Wallet families contribute 49 paths — `app/Marketplace/**` (21), `app/Payments/**` (24), `app/Wallet/**` (4) — after exact historical direct-read evidence, '
    'byte-identical family trees, exact 23 dependent bindings and an ordered 13-file PHP 8.5.10/MariaDB 11.8.9 qualification producing 45 cases / 444 assertions / 0 failures / 0 errors / 0 skips, '
    'including four real-MariaDB integration/concurrency files. The exact six-file `tests/Feature/Marketplace/**` directory contributes a further 6 GROUPED paths after immutable historical evidence '
    'explicitly names every file, exact byte identity, a bound 17-case / 179-assertion all-green qualification including both real-MariaDB tests, and projected-ledger reproduction proving only those six rows transition '
    'from UNVERIFIED to GROUPED. Post-adoption exact-head proof and fresh independent review are still required. GROUPED is bounded semantic carry-forward, not product/security readiness. '
    'The rejected Atlas 508-path candidate remains UNVERIFIED. Full CSV is reproducible from immutable inventories, `coverage-review.tsv`, `coverage-groups.json` and ledger SHA-256 '
    '`25ed5eb371279fbdb16a50263637856a3bc409b775387555efdaa17cebdc3617`.'
)
md = replace_once(md, old_para, new_para, 'coverage paragraph')
MARKDOWN.write_text(md, encoding='utf-8')

print(json.dumps({
    'result': 'MARKETPLACE_TESTS_CANONICAL_ADOPTION_MUTATION_READY',
    'grouped_paths': 113,
    'unverified_paths': 3991,
    'ledger_sha256': NEW_LEDGER,
    'mutated_files': [str(p.relative_to(ROOT)) for p in (CANDIDATE, GROUPS, SUMMARY, REPORT, INDEX, MARKDOWN)],
}, sort_keys=True))
