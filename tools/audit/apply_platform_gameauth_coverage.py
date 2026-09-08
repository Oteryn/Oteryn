#!/usr/bin/env python3
"""One-shot audited reconciliation for Platform routes + GameAuth evidence in PR #185.

Temporary helper. It only edits META audit evidence/docs, rebuilds the complete ledger from immutable
inventories, and fails closed on any unexpected pre-state. Provider repositories are never written.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import verify_report

QUALIFICATION_HEAD = '261c3838cd4806ef29bd9e0e1808049be4bdf809'
QUALIFICATION_RUN = 34225490543
QUALIFICATION_JOB = 102058467962

ROUTES = {
    'routes/api.php': 'ba7916913c581d88a23cb19a70060d857606f644',
    'routes/console.php': 'c5dc5d63ef514d094b1a6019fc41f764883fb265',
    'routes/internal.php': '5fa537392a6f7400f56f8c2b6f55571dad2ebe90',
    'routes/localization.php': '31d474687f8279ef160abd6e1db27753b3a5b99e',
    'routes/modules/announcements.php': '452bb9ee7b70b03951ab7c2476dd10e437549c2b',
    'routes/modules/character-profile-preferences.php': 'cc0ab9c2cfdc574b2924e6554bbfd65f23571840',
    'routes/modules/downloads.php': '62be2bd4f86e45a6273c15508791db9c6530a61f',
    'routes/modules/editorial-media.php': '77d3997723b3881329cfc439268bff98335c9a68',
    'routes/modules/events.php': '31fd0e8ed50b41f99bedc639d562a9fe2cba47f1',
    'routes/modules/game-catalog.php': 'bc29adb9c5ebca9fda1a53c663a35b542a3470b9',
    'routes/modules/homepage-templates.php': 'bea4353cb2ad2198f17d4840c4eac337a70da94f',
    'routes/modules/marketplace.php': '6ead81fecf5d99eb231413bea98d8bf097fa05b5',
    'routes/modules/payments.php': '77690386865ea9095c427f96ee7a8e6b863f176a',
    'routes/modules/player-companion.php': '797be13e358bf363a9161951551f0c5949d9cd6f',
    'routes/modules/public-game-statistics.php': 'a49899694f117acd0a4eba958053dcbccb860754',
    'routes/modules/public-portal.php': '74b581fb449b77fc3985e46b1734f1913b422cc8',
    'routes/modules/support.php': 'cacd43464ab0126d4caef0c1a13da1aacdc90122',
    'routes/modules/wiki.php': 'f4a16ac017fd075b54904455bc8b6f05af304053',
    'routes/web.php': '339e7573b2bc04c7bdd9183cd739c099448d8421',
}


def require(ok, message):
    if not ok:
        raise SystemExit(message)


def load_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def dump_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def read_tsv(path: Path):
    with path.open(encoding='utf-8', newline='') as handle:
        reader = csv.DictReader(handle, delimiter='\t')
        return reader.fieldnames, list(reader)


def write_tsv(path: Path, fields, rows) -> None:
    out = io.StringIO(newline='')
    writer = csv.DictWriter(out, fieldnames=fields, delimiter='\t', lineterminator='\n')
    writer.writeheader(); writer.writerows(rows)
    path.write_text(out.getvalue(), encoding='utf-8')


def replace_once(text: str, old: str, new: str, label: str) -> str:
    require(text.count(old) == 1, f'{label}: expected one replacement target, got {text.count(old)}')
    return text.replace(old, new)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('.'))
    parser.add_argument('--inventory-dir', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve(); inv = args.inventory_dir.resolve()
    ev = root / 'docs/evidence/organization-audit-20260907'
    report_path = root / 'docs/evidence/OTERYN-ORGANIZATION-COMPREHENSIVE-AUDIT-20260907.json'

    # 1. Promote only the 19 frozen-current routes actually read in this continuation.
    review_path = ev / 'coverage-review.tsv'
    fields, rows = read_tsv(review_path)
    require(fields == ['repository','path','blob_sha','depth','scope','line_ranges','execution_evidence'], 'coverage-review header changed')
    require(len(rows) == 202, f'unexpected pre-review count {len(rows)}')
    existing = {(r['repository'], r['path']) for r in rows}
    require(not any(('platform', path) in existing for path in ROUTES), 'route already present in DIRECT ledger')
    scope = ('Frozen Platform de917b3 route declaration and middleware-composition review; all 19 files in the exact routes tree were read. '
             'This does not approve controller/model-binding authorization, framework CSRF implementation, production configuration or runtime behavior.')
    for path, oid in ROUTES.items():
        rows.append({
            'repository': 'platform', 'path': path, 'blob_sha': oid,
            'depth': 'SCOPED_SEMANTIC_REVIEW', 'scope': scope, 'line_ranges': '[]',
            'execution_evidence': 'SOURCE_REVIEW_ONLY; r3-continuation-checkpoint-20260908.json',
        })
    rows.sort(key=lambda row: (row['repository'].encode(), row['path'].encode()))
    write_tsv(review_path, fields, rows)

    # 2. Adopt the exact 27-file GameAuth carry-forward only after the successful hosted qualification.
    candidate_path = ev / 'r3-platform-gameauth-candidate.json'
    candidate = load_json(candidate_path)
    require(candidate['state'] == 'CANDIDATE_PENDING_QUALIFICATION' and candidate['coverage_adopted'] is False, 'GameAuth candidate pre-state changed')
    require(candidate['expected_count'] == 27 and len(candidate['current_revalidation']['current_blobs']) == 23, 'GameAuth candidate binding count changed')
    candidate['state'] = 'QUALIFIED_ADOPTED_AS_GROUPED'
    candidate['coverage_adopted'] = True
    candidate['qualification'] = {
        'qualification_head': QUALIFICATION_HEAD,
        'workflow_run': QUALIFICATION_RUN,
        'job': QUALIFICATION_JOB,
        'verifier_unit_tests': 5,
        'verifier_unit_result': 'PASS',
        'focused_current_tests': {'test_files': 14, 'cases': 61, 'assertions': 565, 'failures': 0, 'errors': 0, 'skipped': 0},
        'php': '8.5.10',
        'composer_validate': 'PASS',
        'tracked_source_clean_after_execution': True,
        'existing_exact_source_concurrency_artifact': 10035749457,
        'outcome': 'ADOPTED_GROUPED_CARRY_FORWARD',
    }
    dump_json(candidate_path, candidate)

    groups_path = ev / 'coverage-groups.json'
    groups = load_json(groups_path)
    require(groups.get('schema_version') == 1 and isinstance(groups.get('groups'), list), 'coverage groups shape')
    require(not any(g.get('id') == candidate['candidate_id'] for g in groups['groups']), 'GameAuth group already adopted')
    group = {
        'id': candidate['candidate_id'],
        'repository': 'platform',
        'disposition': 'GROUPED',
        'path_prefix': candidate['path_prefix'],
        'expected_count': 27,
        'depth': 'GROUPED_REVALIDATED',
        'scope': ('Every app/GameAuth/** leaf was directly read in the immutable historical Platform audit and is byte-identical at frozen de917b3. '
                  'Carry-forward is bounded by exact path/blob identity, 23 frozen dependent config/route/test/toolchain blobs, 61 focused current test cases/565 assertions, '
                  'and separate exact-source concurrency evidence. This is scoped semantic reuse, not product/security readiness.'),
        'limitations': candidate['limitations'],
        'historical_evidence': candidate['historical_evidence'],
        'current_revalidation': candidate['current_revalidation'],
        'evaluation': {
            'qualification_head': QUALIFICATION_HEAD,
            'qualification_run': QUALIFICATION_RUN,
            'qualification_job': QUALIFICATION_JOB,
            'verifier_unit_tests': 5,
            'focused_current_tests': {'cases': 61, 'assertions': 565, 'failures': 0, 'errors': 0, 'skipped': 0},
            'existing_exact_source_concurrency_artifact': 10035749457,
            'outcome': 'ADOPTED_GROUPED_CARRY_FORWARD',
        },
    }
    groups['groups'].append(group)
    dump_json(groups_path, groups)

    # 3. Canonical machine-readable counts.
    summary_path = ev / 'coverage-summary.json'
    summary = load_json(summary_path)
    require(summary['scoped_review_paths'] == 202 and summary['grouped_revalidated_paths'] == 0 and summary['unverified_semantics_total'] == 4123, 'coverage summary pre-state changed')
    summary['per_repository']['platform'].update(direct_scoped=156, grouped=27, unverified_semantics=1982)
    summary['new_scoped_paths_since_r2'] = 156
    summary['scoped_review_paths'] = 221
    summary['grouped_revalidated_paths'] = 27
    summary['semantically_classified_paths'] = 248
    summary['unverified_semantics_total'] = 4077
    summary['durability'] = ('Full CSV accompanies the audit delivery. Committed DIRECT review rows, immutable Git trees, explicit accepted/rejected GROUPED records and verify_report.py reproduce every disposition. '
                             'The 27-file Platform GameAuth group is adopted only through exact historical/source identity plus frozen-current qualification; the rejected 508-file Atlas candidate remains UNVERIFIED.')
    summary['coverage_dimension_note'] = ('DIRECT records bounded current/source review, not universal approval. GROUPED records bounded semantic carry-forward only when historical scope, exact identity and current dependent qualification are all bound. '
                                          'Platform GameAuth contributes 27 GROUPED paths; the Atlas 508-path candidate remains rejected.')
    dump_json(summary_path, summary)

    report = load_json(report_path)
    require(report['scoped_review_paths'] == 202 and report['grouped_revalidated_paths'] == 0, 'report coverage pre-state changed')
    report['revision'] = 'R3-NATIVE-EVIDENCE-POST-REVIEW-PLATFORM-ROUTES-GAMEAUTH-RECONCILIATION'
    report['scoped_review_paths'] = 221
    report['grouped_revalidated_paths'] = 27
    report['semantically_classified_paths'] = 248
    report['r3_platform_gameauth_candidate'] = 'organization-audit-20260907/r3-platform-gameauth-candidate.json'
    report['r3_continuation_checkpoint'] = 'organization-audit-20260907/r3-continuation-checkpoint-20260908.json'
    report['r3_review']['latest_completed_rereview'] = {
        'reviewed_head': 'd72356adccf5600dc2fc2a075f215a6b071a21df',
        'completed_at_utc': '2026-09-08T11:39:15.902085Z',
        'result': 'PASS_NO_NEW_P0_P1_P2',
        'p1': 0,
        'p2': 0,
        'new_material_findings': [],
        'historical_review_threads_resolved_after_readback': 15,
    }
    report['r3_review']['fresh_independent_rereview_required'] = True
    report['r3_review']['fresh_rereview_reason'] = 'Platform routes/GameAuth coverage reconciliation is material evidence added after the clean d72356ad review.'
    dump_json(report_path, report)

    # 4. Residual obligations remain open, but counts must reflect the actual new coverage.
    unknown_path = ev / 'unknowns.json'
    unknowns = load_json(unknown_path)
    semantic = next(item for item in unknowns['items'] if item['id'] == 'SEMANTIC-COVERAGE')
    semantic['reason'] = ('Source bytes available; 221 DIRECT scoped path reviews plus 27 bounded GROUPED GameAuth paths are now bound, not full behavior approval; 4077 paths retain UNVERIFIED. '
                          'The historical Atlas 508-path candidate remains rejected and no automatic import from maintenance N/A or unproven summaries is allowed.')
    independent = next(item for item in unknowns['items'] if item['id'] == 'INDEPENDENT-REVIEW')
    independent['reason'] = ('A clean exact-head review of d72356ad found no new P0/P1/P2 after prior hardening and all 15 historical audit-package review threads were resolved. '
                             'This later Platform routes/GameAuth coverage reconciliation is new material and has not yet received its own fresh independent exact-head review.')
    independent['effect'] = 'No self-awarded 10/10 or final independent acceptance is claimed for the expanded revision.'
    dump_json(unknown_path, unknowns)

    verification_path = ev / 'verification-index.json'
    verification = load_json(verification_path)
    verification['r3_platform_gameauth_qualification'] = {
        'frozen_source_commit': 'de917b3477a1de0667531380de3660e8b2ab59aa',
        'historical_source_commit': '3b2ea1c7392187d5d22488673073dc8f8305a374',
        'qualification_head': QUALIFICATION_HEAD,
        'run': QUALIFICATION_RUN,
        'job': QUALIFICATION_JOB,
        'verifier_unit_tests': 5,
        'exact_gameauth_paths': 27,
        'dependent_blob_bindings': 23,
        'focused_test_files': 14,
        'focused_cases': 61,
        'focused_assertions': 565,
        'failures': 0,
        'errors': 0,
        'skips': 0,
        'tracked_source_clean_after_execution': True,
        'separate_concurrency_artifact': 10035749457,
        'qualification': 'BOUNDED_GROUPED_CARRY_FORWARD_NOT_PRODUCT_PASS',
    }
    dump_json(verification_path, verification)

    # 5. Human-readable counts and explicit semantics.
    readme = ev / 'README.md'; text = readme.read_text(encoding='utf-8')
    old = ('Governing continuation: META#186, existing PR#185. The main report/JSON owns the scoped opinion; this is not another approval programme. '
           'R3 contains 78 finding records, 23 A–W domains, 15 residual obligations and 202 explicit scoped path reviews out of 4325 immutable leaves. `4123` leaves retain UNVERIFIED semantics. Full-file, control-field and translation-range reviews are intentionally distinguished.')
    new = ('Governing continuation: META#186, existing PR#185. The main report/JSON owns the scoped opinion; this is not another approval programme. '
           'R3 contains 78 finding records, 23 A–W domains, 15 residual obligations, 221 DIRECT scoped path reviews and 27 bounded GROUPED GameAuth paths out of 4325 immutable leaves. `4077` leaves retain UNVERIFIED semantics. Full-file, control-field, translation-range and GROUPED carry-forward evidence are intentionally distinguished.')
    text = replace_once(text, old, new, 'README coverage sentence')
    anchor = 'python3 tools/audit/verify_announcement_trigger.py --source-root /path/to/exact-platform-de917b3\n'
    addition = ('python3 tools/audit/verify_platform_gameauth_group.py --audit-root . --platform-root /path/to/exact-platform-de917b3 '
                '--evidence-root /path/to/platform-audit-publication-3fe7df5\n')
    require(anchor in text and addition not in text, 'README GameAuth command anchor')
    text = text.replace(anchor, anchor + addition)
    evidence_anchor = '`r3-atlas-grouped-revalidation.json` records a rejected 508-shard GROUPED carry-forward: immutable shard identity passed, but current consumer impact-routing qualification failed, so all 508 remain UNVERIFIED. '
    evidence_add = ('`r3-platform-gameauth-candidate.json` binds an accepted 27-path Platform GameAuth carry-forward after exact historical/source identity, 23 dependent blob bindings and 61/61 focused frozen-current tests; this remains bounded GROUPED evidence, not product PASS. ')
    require(evidence_anchor in text and evidence_add not in text, 'README evidence anchor')
    text = text.replace(evidence_anchor, evidence_anchor + evidence_add)
    readme.write_text(text, encoding='utf-8')

    md_path = root / 'docs/evidence/OTERYN-ORGANIZATION-COMPREHENSIVE-AUDIT-20260907.md'
    md = md_path.read_text(encoding='utf-8')
    old_table = '''| Source | Tracked leaves | Explicit scoped reviews | Semantics not adopted/established |\n|---|---:|---:|---:|\n| meta | 174 | 20 | 154 |\n| game | 830 | 34 | 796 |\n| platform | 2165 | 137 | 2028 |\n| atlas | 1155 | 10 | 1145 |\n| migration_archive | 1 | 1 | 0 |\n| **Total** | **4325** | **202** | **4123** |'''
    new_table = '''| Source | Tracked leaves | DIRECT scoped | GROUPED revalidated | UNVERIFIED semantics |\n|---|---:|---:|---:|---:|\n| meta | 174 | 20 | 0 | 154 |\n| game | 830 | 34 | 0 | 796 |\n| platform | 2165 | 156 | 27 | 1982 |\n| atlas | 1155 | 10 | 0 | 1145 |\n| migration_archive | 1 | 1 | 0 | 0 |\n| **Total** | **4325** | **221** | **27** | **4077** |'''
    md = replace_once(md, old_table, new_table, 'main report coverage table')
    old_para = ('`DIRECT` is a bounded review with the stated scope, not full approval of the entire file or every dependency. R2 had 65 scoped entries; R3 adds 137 distinct paths and extends some existing scopes. '
                'In particular, R3 reads all 50 Platform migration files and the control fields of all 77 workflow files. It does not claim that every workflow step body was reviewed. All unadopted semantics stay UNVERIFIED; grouping/N/A are not used to inflate coverage. Full CSV is reproducible from immutable inventories, `coverage-review.tsv` and the committed ledger digest.')
    new_para = ('`DIRECT` is a bounded review with the stated scope, not full approval of the entire file or every dependency. R2 had 65 scoped entries; the current revision adds 156 DIRECT paths and extends some existing scopes. '
                'It reads all 50 Platform migration files, control fields of all 77 workflow files and all 19 files in the frozen Platform routes tree. The prior Platform audit statement that there were 21 route files was rejected fail-closed; the frozen tree contains 19 and all 19 were read directly here. '
                'Exactly 27 `app/GameAuth/**` leaves are additionally GROUPED: the earlier audit directly read all 27, the complete path/blob set and whole `app` tree are byte-identical at frozen `de917b3…`, 23 dependent blobs are source-bound, and 61 focused frozen-current cases / 565 assertions passed with zero failures/errors/skips. Separate exact-source concurrency evidence remains distinct. GROUPED is bounded semantic carry-forward, not product/security readiness. The rejected Atlas 508-path candidate remains UNVERIFIED. Full CSV is reproducible from immutable inventories, `coverage-review.tsv`, `coverage-groups.json` and the committed ledger digest.')
    md = replace_once(md, old_para, new_para, 'main report coverage paragraph')
    old_review = ('A later independent re-review of `e242a68a9df73304cbb6ba8bd3cfebbb36a2197b` found one remaining canonical disclosure-label P1 and two strict-JSON-type P2 evidence defects. This revision corrects those items, but the resulting new head still requires fresh independent re-review; author remediation is not independent acceptance.')
    new_review = ('Successive independent review waves exposed and drove correction of the remaining canonical disclosure, strict-JSON-type, output-symlink and rejected-GROUPED evidence defects. A final exact-head re-review of `d72356adccf5600dc2fc2a075f215a6b071a21df` completed with no new P0/P1/P2, after which all 15 historical audit-package review threads were resolved. That resolves those audit-package defects, not provider findings. The Platform routes/GameAuth coverage expansion in this later revision is new material and therefore still requires fresh independent exact-head review.')
    md = replace_once(md, old_review, new_review, 'main report review paragraph')
    md_path.write_text(md, encoding='utf-8')

    # 6. Rebuild the full immutable ledger; only now persist its digest and validate all accounting.
    raw, grouped_counts = verify_report.rebuild_ledger(report_path, inv)
    require(len(raw) > 0 and grouped_counts['platform'] == 27 and sum(grouped_counts.values()) == 27, 'rebuilt grouped counts incorrect')
    digest = hashlib.sha256(raw).hexdigest()
    summary = load_json(summary_path); summary['ledger_sha256'] = digest; dump_json(summary_path, summary)
    result = verify_report.validate(report_path, inv)
    require(result['scoped_review_paths'] == 221, 'validated DIRECT count')
    require(result['grouped_revalidated_paths'] == 27, 'validated GROUPED count')
    require(result['semantically_classified_paths'] == 248, 'validated semantic count')
    require(result['unverified_semantics'] == 4077, 'validated UNVERIFIED count')
    require(result['tree_and_ledger_verified'] is True, 'full tree/ledger validation missing')

    print(json.dumps({'result': 'PLATFORM_ROUTES_GAMEAUTH_RECONCILED_NOT_AUDIT_PASS', 'ledger_sha256': digest, **result}, indent=2))


if __name__ == '__main__':
    main()
