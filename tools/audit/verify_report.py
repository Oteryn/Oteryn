#!/usr/bin/env python3
"""Validate this audit's accounting, not the truth of arbitrary source assertions.

No network or repository writes. Optional immutable inventories reconstruct the
Git trees and reproduce the complete per-leaf CSV. DIRECT, GROUPED and
UNVERIFIED are distinct dispositions; GROUPED is accepted only through an
explicit fail-closed evidence rule. A successful result never becomes
product/audit-semantic PASS.
"""
from __future__ import annotations
import argparse
import ctypes
import csv
import errno
import hashlib
import io
import json
import os
from pathlib import Path
import re

SHA = re.compile(r'[0-9a-f]{40}\Z')
COVERAGE_GROUPS_BLOB_SHA = 'b3313b4a0831b9fcc528665dca25bdccdb9dab59'
FINDING_REGISTER_SHA256 = 'c5402f1618cfe4cd03d2ad50cd0946ec86f19e834b02128199b31b808cc64e94'
DOMAIN_MATRIX_SHA256 = '34e46372880cbb932b2ed26d89cf71448d360fecd0a90f562ee693698ca10ac4'
FINDING_REGISTER_FIELDS = ('id', 'priority', 'repository', 'state', 'scope', 'title',
                           'evidence', 'owner_route', 'closure_condition')
DOMAIN_MATRIX_FIELDS = ('domain', 'name', 'acceptance_criterion', 'method_and_evidence',
                        'opinion', 'remaining_limit', 'references')
STATES = {'SOURCE_REPAIRED_TESTED','PARTIALLY_REPAIRED','RETIRED_SOURCE','SOURCE_REPAIRED',
          'UNKNOWN_LIVE','REQUIRES_REVALIDATION','REQUIRES_LIVE_REVALIDATION',
          'SOURCE_REPAIRED_RECORDED_CI','OPEN_QUALIFICATION','HISTORICAL_NOTE','CONFIRMED_SOURCE',
          'OPEN_INHERITED','REPRODUCED','UNVERIFIED_HYPOTHESIS','REGRESSION_VERIFIED',
          'REPORTED_CLOSED','LIVE_RECORD_RECONCILED','REPORTED_IMPLEMENTED_NOT_REQUALIFIED',
          'REPORTED_OPEN','OWNER_DECISION_PENDING','HISTORICAL_TERMINAL','REPORTED_OPEN_CANDIDATE'}
DEFAULT_REASON = 'Identity enumerated; this continuation does not assert a complete semantic review of this leaf. Historical/source oracles may provide narrower evidence in the finding register.'
DIRECT_ADDITIONS = 'coverage-review-canonical-additions.tsv'
META_R4_DIRECT_ADDITIONS = 'coverage-review-meta-r4-direct-additions.tsv'
META_R5_DIRECT_ADDITIONS = 'coverage-review-meta-r5-instruction-efficiency-direct-additions.tsv'
META_R6_DIRECT_ADDITIONS = 'coverage-review-meta-r6-prompts-direct-additions.tsv'
META_R7_DIRECT_ADDITIONS = 'coverage-review-meta-current-main-governance-direct-additions.tsv'
AUDIT186_SEMANTIC_03_DIRECT_ADDITIONS = 'coverage-review-audit186-semantic-03-direct-additions.tsv'
DIRECT_ADDITIONS_BINDING = 'organization-audit-20260907/coverage-review-canonical-additions.tsv'
RECORDER_ADDITIONS_BINDING = 'organization-audit-20260907/coverage-review-additions.tsv'
ANNOUNCEMENTS_ADDITIONS_BINDING = 'organization-audit-20260907/coverage-review-announcements-additions.tsv'
META_R4_DIRECT_ADDITIONS_BINDING = 'organization-audit-20260907/coverage-review-meta-r4-direct-additions.tsv'
META_R5_DIRECT_ADDITIONS_BINDING = 'organization-audit-20260907/coverage-review-meta-r5-instruction-efficiency-direct-additions.tsv'
META_R5_CANDIDATE_BINDING = 'organization-audit-20260907/r3-meta-r5-instruction-efficiency-direct-candidate.json'
META_R6_DIRECT_ADDITIONS_BINDING = 'organization-audit-20260907/coverage-review-meta-r6-prompts-direct-additions.tsv'
META_R6_CANDIDATE_BINDING = 'organization-audit-20260907/r3-meta-r6-prompts-direct-candidate.json'
META_R7_DIRECT_ADDITIONS_BINDING = 'organization-audit-20260907/coverage-review-meta-current-main-governance-direct-additions.tsv'
AUDIT186_SEMANTIC_03_DIRECT_ADDITIONS_BINDING = 'organization-audit-20260907/coverage-review-audit186-semantic-03-direct-additions.tsv'
AUDIT186_SEMANTIC_03_CANDIDATE_SHA256 = '4f9eb30d596da45a95f8cadf37dfee4ae4bb89a2846683098021574613d9676c'
AUDIT186_SEMANTIC_03_OVERLAY_SHA256 = '76881b1eace7559a9d84b060c82ccf9bf86ae5627e670535a7680ccb32285de5'
VERIFICATION_RESULTS_SHA256 = '221f0fed6cc79c2fc3fcab5945d075fb98d6cdd319d746700207b7237b3181b1'
VERIFICATION_RESULT_KEYS = ('id', 'source_commit', 'command', 'exit_code', 'log_sha256')
VERIFICATION_RESULT_IDS = (
    'atlas-focused-node', 'atlas-output-safety', 'game-semantic-dispatch',
    'meta-central_agent_policy.py', 'meta-test_agent_continuation_policy.py',
    'meta-test_agent_continuation_review_repairs.py', 'meta-test_agent_execution_routing.py',
    'meta-test_bounded_execution_guard.py', 'meta-test_central_agent_policy.py',
    'meta-test_merge_queue_workflow_contract.py', 'meta-test_remote_desktop_action_gate.py',
    'meta-validate_release_manifests.py', 'platform-test_classify_changes',
    'platform-test_required_test_gate',
)
EXPECTED_UNRESOLVED_IDS = {
    'SEMANTIC-COVERAGE', 'HISTORY-REVALIDATION', 'ADMIN-STATE', 'INFRA-STATE', 'RECOVERY',
    'COST-CI', 'COST-AGENTS', 'SUPPLY-CHAIN', 'NATIVE-G1', 'UI-343', 'PORTABILITY',
    'LIVE-TELEMETRY', 'PRIVACY-RIGHTS', 'PLATFORM-H02',
}
SECTION_7_HEADING = '## 7. Remaining obligations and closure conditions'
SECTION_8_HEADING = '## 8. Reproduction, retention and integration boundary'
EXPECTED_RESIDUAL_OBLIGATIONS_PARAGRAPH = (
    'All 23 A–W domains have a criterion, method, evidence, opinion and limitation in `domain-matrix.tsv`. '
    'FOURTEEN material residual obligations retain explicit owner routes and measurable closure conditions in '
    '`unknowns.json`: `SEMANTIC-COVERAGE`, `HISTORY-REVALIDATION`, `ADMIN-STATE`, `INFRA-STATE`, `RECOVERY`, '
    '`COST-CI`, `COST-AGENTS`, `SUPPLY-CHAIN`, `NATIVE-G1`, `UI-343`, `PORTABILITY`, `LIVE-TELEMETRY`, '
    '`PRIVACY-RIGHTS`, and `PLATFORM-H02`.'
)
EXPECTED_SECTION_7_PARAGRAPHS = (
    SECTION_7_HEADING,
    EXPECTED_RESIDUAL_OBLIGATIONS_PARAGRAPH,
    (
        'These are not all access failures. Source bytes and native hosted execution are available. '
        'Missing semantic review must be completed or validly imported, not labelled inaccessible. '
        'Maintenance does not turn suspended authored code into tested code. No host/deploy action is '
        'authorized merely because a tool exists.'
    ),
    (
        'Professional completion requires every material scoped obligation to receive a defensible disposition '
        'and independent review of the stable candidate. It does not require fixing every discovered product '
        'defect inside this META audit. Conversely, an unreviewed source area cannot be called audited merely '
        'because its remediation has an owner.'
    ),
)
SECTION_1_HEADING = '## 1. Source identity and actual coverage'
SECTION_2_HEADING = '## 2. Native evidence actually acquired and rechecked'
EXPECTED_SECTION_1_SHA256 = 'f0b6c1bc73952275d56d8e9a675b5d25d6b4da46762bd14353442869c19d59cf'
EXPECTED_REPORT_MARKDOWN_SHA256 = '87a20b8d4f8dc107a41672db18415391e3998b2302a25d6300736b4726bc13c8'
CURRENT_COVERAGE_TABLE_HEADER = '| Source | Tracked leaves | DIRECT scoped | GROUPED revalidated | UNVERIFIED semantics |'
CURRENT_R5_ADOPTION_PARAGRAPH = (
    'Exactly 25 META source files under `docs/agents/evals/r5-instruction-efficiency/**` are now separately '
    'adopted as DIRECT `SCOPED_SEMANTIC_REVIEW` rows through '
    '`coverage-review-meta-r5-instruction-efficiency-direct-additions.tsv`, from immutable reviewed candidate '
    '`r3-meta-r5-instruction-efficiency-direct-candidate.json` (SHA-256 '
    '`a6ff7425e1a1d338bd02c769cc930109bf28c03db39b896c2ceb90233234eef3`). Each row records bounded '
    'full-file source semantics with empty line ranges. This adoption does not re-adopt the already-DIRECT '
    '`OTERYN-R5Q-RESULTS.md` evidence and does not attest runtime model/effort, fresh isolation, answer '
    'correctness or safety, A/B superiority, provider permission, measured cost, live state, or product '
    'readiness. The dated protected-main identity `3b39e0be05aef008f1bd442821daefa898a201dd` is source '
    'identity carry-forward only. `META-AUD-05` remains P2 / `PARTIALLY_REPAIRED`, and all 14 residual '
    'obligations remain open. The R5 adoption ledger was '
    '`27654f5f724d9857912e69fd036712dd00d63882ebf8e9c1411c26c66eaeef41`.'
)
CURRENT_R6_ADOPTION_PARAGRAPH = (
    'Exactly 11 META prompt files under `docs/agents/prompts/**` are now separately adopted as DIRECT '
    '`SCOPED_SEMANTIC_REVIEW` rows through `coverage-review-meta-r6-prompts-direct-additions.tsv`, from '
    'immutable reviewed candidate `r3-meta-r6-prompts-direct-candidate.json` (SHA-256 '
    '`62b7f49af1434667f9ed293c896bc7f9b285cb8652883f00915607f0ce65381a`). The two rollout prompts '
    'already counted by R4 are excluded and not re-adopted. Prompt text is source evidence, not standing '
    'authority; retired/history packets remain non-dispatchable and templates require fresh live authorization. '
    'No provider/runtime/admin/security/production/recovery/readiness/completion result is attested. The dated '
    'protected-main identity `3b39e0be05aef008f1bd442821daefa898a201dd` is source identity carry-forward '
    'only. `META-AUD-05` remains P2 / `PARTIALLY_REPAIRED`, all 14 residual obligations remain open, and the '
    'current canonical ledger is `ff5c6621a78c14fc17802ecf01b4ef815867ccab95acce90c490973946d6279b`.'
)
CURRENT_R7_ADOPTION_PARAGRAPH = 'Exactly five already-DIRECT META governance rows are refreshed in place and exactly fourteen previously UNVERIFIED/new governance paths are separately adopted as DIRECT `SCOPED_SEMANTIC_REVIEW` rows through `coverage-review-meta-current-main-governance-direct-additions.tsv`, from immutable reviewed R7 candidate `r7-meta-current-main-governance-direct-candidate.json` at Git blob `6a3e98ad65f52015a43a84e39a8940f64b31dc65`. This is a +14 DIRECT transition, not +19. META alone is rebaselined to protected main `23b21e9b1b2d4b6c3a5cac3d4c7a18747804c090` / tree `b8ebb8e50bce14a736fa65590ac121655c52fd12`; the other four pinned sources remain unchanged. The historical program record is provenance only, tests attest exercised deterministic assertions only, and source existence does not prove live executor, capability-routing, Merge Queue, provider/runtime/admin state, readiness, or completion. All 26 current leaves under `docs/evidence/repository-audit-2026-09-06/**` remain UNVERIFIED. All 14 residual obligations remain open, `META-AUD-05` remains P2 / `PARTIALLY_REPAIRED`, and the current canonical ledger is `8520e472698d3592fcc95d5b093a631d9ae936256affcbf2d1418fa8b7448f94`.'
CURRENT_SEMANTIC_03_ADOPTION_PARAGRAPH = 'Exactly one additional canonical META leaf, `docs/ci/CI_CONTRACT.md` at source cut `23b21e9b1b2d4b6c3a5cac3d4c7a18747804c090` / blob `3c6d36cd58cd81f332382db7f2eda78261788caa`, is adopted as DIRECT `SCOPED_SEMANTIC_REVIEW` through `coverage-review-audit186-semantic-03-direct-additions.tsv` from frozen worker PR #209 head `9ad2942ba0dedb5b94e437c32b85161c6c59885a`. Its scope is the frozen CI contract’s declared META validation, gate, runner, provider-ownership and protection/integration intent; it does not attest current workflow bytes, live rulesets/protection, actual check execution, provider CI, runtime, readiness or audit completion. PR #204 is not adopted by this transition, PR #207 remains void, all 14 residual obligations remain open, and the current canonical ledger is `bf51139f97683659f752a54e643c1d342791476d64a0f78237b5c5d3ba3a310a`.'
CURRENT_HISTORY_ANNOTATION = (
    'The following paragraph is retained verbatim as the bounded **pre-Announcements Marketplace closeout '
    'snapshot** required by the Marketplace durability contract. Within that paragraph, “the current revision” '
    'and its 223-path ledger refer to that historical pre-Announcements audit state, not to the present canonical '
    '309-path state shown above and bound below.'
)
EXPECTED_PRE_ANNOUNCEMENTS_MARKETPLACE_SNAPSHOT = (
    '`DIRECT` is a bounded review with the stated scope, not full approval of the entire file or every '
    'dependency. R2 had 65 scoped entries; the current revision adds 158 DIRECT paths and extends some '
    'existing scopes. It reads all 50 Platform migration files, control fields of all 77 workflow files and '
    'all 19 files in the frozen Platform routes tree. The prior Platform audit statement that there were 21 '
    'route files was rejected fail-closed; the frozen tree contains 19 and all 19 were read directly here. '
    'Exactly 113 Platform leaves are additionally GROUPED. GameAuth contributes 27 paths after exact '
    'historical/source identity, 23 dependent bindings and 61 focused cases / 565 assertions. Four '
    'account/Canary/profile/character families contribute 31 paths after exact 23 dependent bindings and an '
    'ordered 15-file qualification producing 86 cases / 586 assertions. Three Marketplace/Payments/Wallet '
    'families contribute 49 paths — `app/Marketplace/**` (21), `app/Payments/**` (24), `app/Wallet/**` (4) — '
    'after exact historical direct-read evidence, byte-identical family trees, exact 23 dependent bindings '
    'and an ordered 13-file PHP 8.5.10/MariaDB 11.8.9 qualification producing 45 cases / 444 assertions / 0 '
    'failures / 0 errors / 0 skips, including four real-MariaDB integration/concurrency files. The exact '
    'six-file `tests/Feature/Marketplace/**` directory contributes a further 6 GROUPED paths after immutable '
    'historical evidence explicitly names every file, exact byte identity, a bound 17-case / 179-assertion '
    'all-green qualification including both real-MariaDB tests, and projected-ledger reproduction proving '
    'only those six rows transition from UNVERIFIED to GROUPED. GROUPED is bounded semantic carry-forward, '
    'not product/security readiness. The rejected Atlas 508-path candidate remains UNVERIFIED. Full CSV is '
    'reproducible from immutable inventories, the base `coverage-review.tsv`, the exact two-row '
    '`coverage-review-additions.tsv` overlay, `coverage-groups.json` and ledger SHA-256 '
    '`2d823435f76f0c08b118ccb5dc1c9ccf9ef4acc41bffdd447b260e82ea404b0f`.'
)
_LIBC = ctypes.CDLL(None, use_errno=True)
_AT_EMPTY_PATH = 0x1000


def write_new_file_no_symlinks(path: Path, raw: bytes) -> None:
    """Create one file exclusively without following its final or ancestor symlinks."""
    absolute=Path(os.path.abspath(path));parent=absolute.parent
    flags=os.O_RDONLY|os.O_DIRECTORY
    if hasattr(os,'O_NOFOLLOW'): flags|=os.O_NOFOLLOW
    descriptor=os.open(parent.anchor,flags)
    try:
        for part in parent.parts[1:]:
            try: child=os.open(part,flags,dir_fd=descriptor)
            except OSError as exc: raise ValueError('ledger output ancestry must contain only directories, not symlinks') from exc
            os.close(descriptor);descriptor=child
        tmpfile=getattr(os,'O_TMPFILE',0)
        if not tmpfile: raise ValueError('O_TMPFILE is required for ownership-safe ledger output')
        try:
            output=os.open('.',os.O_RDWR|tmpfile,0o666,dir_fd=descriptor)
            with os.fdopen(output,'wb') as handle:
                handle.write(raw)
                handle.flush();os.fsync(handle.fileno())
                linkat=getattr(_LIBC,'linkat',None)
                if linkat is None: raise OSError(errno.ENOSYS,'linkat is required for ownership-safe ledger output')
                result=linkat(ctypes.c_int(handle.fileno()),ctypes.c_char_p(b''),ctypes.c_int(descriptor),ctypes.c_char_p(os.fsencode(absolute.name)),ctypes.c_int(_AT_EMPTY_PATH))
                if result != 0:
                    error=ctypes.get_errno();raise OSError(error,os.strerror(error),absolute.name)
        except OSError as exc: raise ValueError('refusing ledger overwrite or symlink') from exc
    finally: os.close(descriptor)
SEMANTIC_COVERAGE_UNKNOWN = {'id': 'SEMANTIC-COVERAGE',
 'missing': '3939 source leaves retain UNVERIFIED semantics; 422 of 4361 leaves are semantically '
            'classified',
 'reason': 'Source bytes are available; 309 DIRECT scoped path reviews are bound (the prior 294, '
           'with five already-DIRECT META governance rows refreshed in place and exactly fourteen '
           'previously UNVERIFIED/new governance rows adopted through the R7 overlay; the five '
           'refreshes are not re-counted), and 113 bounded GROUPED Platform paths remain bound. '
           'META is rebaselined to 210 leaves at protected main '
           '23b21e9b1b2d4b6c3a5cac3d4c7a18747804c090; the other four source coordinates remain '
           'pinned. The 26 historical repository-audit packet leaves remain UNVERIFIED. R7 '
           'evidence is bounded source semantics and exercised deterministic assertions only; it '
           'does not prove live executor/capability/Merge Queue operation, provider/runtime/admin '
           'state, readiness, or completion. The frozen PR #209 CI-contract leaf adds one bounded '
           'META DIRECT source review; PR #204 remains unadopted and PR #207 remains void.',
 'effect': 'Original exhaustive completeness cannot be claimed from 422 semantically classified '
           'leaves out of 4361.',
 'owner_route': 'META186 plus provider audit owners',
 'closure_condition': 'Import exact historical disposition ledgers with bounded validity, review '
                      'changed/uncovered authored families, and retain justified grouping/N/A.'}
EXPECTED_AUDIT_COMPLETION = 'NOT_ESTABLISHED; source inventory complete, semantic scope and independent acceptance remain partial'
EXPECTED_REPORT_SEMANTIC_COVERAGE = 'PARTIAL_EXPLICIT_NOT_ALL_LINE'
EXPECTED_FINDING_STATES_SHA256 = '741b78d1abc5553fc745916b47fccf13e7617a37d5f20666cfcef0713ded0ee4'
EXPECTED_META_AUD_05 = {
    'id': 'META-AUD-05',
    'priority': 'P2',
    'repository': 'meta',
    'state': 'PARTIALLY_REPAIRED',
    'scope': 'governance',
    'title': 'Historical authority and merge-up conflict',
    'evidence': 'META-153 | Current access policy separates MQ candidate refresh from source-head churn. Historical/open PR authority liveness is not exhaustively revalidated.',
    'owner_route': 'Oteryn/Oteryn#153; evidence continuation #186',
    'closure_condition': 'Classify remaining operative-looking documents/PRs against current v3 authority without deleting historical evidence.',
}
META_R4_CANDIDATE_BINDING = 'organization-audit-20260907/r3-meta-r4-direct-candidate.json'
EXPECTED_COVERAGE_SUMMARY = {'schema_version': 1,
 'source_leaf_total': 4361,
 'active_repository_leaf_total': 4360,
 'per_repository': {'meta': {'leaves': 210,
                             'direct_scoped': 96,
                             'unverified_semantics': 114,
                             'grouped': 0,
                             'not_applicable': 0},
                    'game': {'leaves': 830,
                             'direct_scoped': 34,
                             'unverified_semantics': 796,
                             'grouped': 0,
                             'not_applicable': 0},
                    'platform': {'leaves': 2165,
                                 'direct_scoped': 168,
                                 'unverified_semantics': 1884,
                                 'grouped': 113,
                                 'not_applicable': 0},
                    'atlas': {'leaves': 1155,
                              'direct_scoped': 10,
                              'unverified_semantics': 1145,
                              'grouped': 0,
                              'not_applicable': 0},
                    'migration_archive': {'leaves': 1,
                                          'direct_scoped': 1,
                                          'unverified_semantics': 0,
                                          'grouped': 0,
                                          'not_applicable': 0}},
 'ledger_sha256': 'bf51139f97683659f752a54e643c1d342791476d64a0f78237b5c5d3ba3a310a',
 'identity_coverage': 'COMPLETE_FOR_PINNED_FIVE_REPOSITORIES',
 'semantic_coverage': 'PARTIAL_EXPLICIT',
 'unclassified_paths': 0,
 'semantic_completion_claimed': False,
 'durability': 'Full CSV accompanies the audit delivery. Committed DIRECT review rows plus the '
               'fail-closed coverage-review-canonical-additions.tsv composition overlay, immutable '
               'Git trees, explicit accepted/rejected GROUPED records and verify_report.py '
               'reproduce every disposition. The canonical additions overlay composes the '
               'separately preserved two-row audit-recorder overlay and the exact ten-row '
               'Announcements overlay. Platform GameAuth contributes 27 GROUPED paths; '
               'Accounts/CanaryIntegration/CharacterProfiles/Characters contribute 31; '
               'Marketplace/Payments/Wallet production code contributes 49; the exact six-file '
               'Marketplace test directory contributes 6. Two frozen Platform app/Audit recorder '
               'implementations and ten frozen app/Announcements implementations are adopted as '
               'bounded DIRECT review rows. The Announcements slice is qualified by real MariaDB '
               '11.8.9 with 4 cases / 20 assertions and a mechanical projection proving exactly '
               'ten UNVERIFIED-to-DIRECT transitions; the Polish editorial_translations join '
               'branch and a dedicated simultaneous-writer race remain explicit execution limits. '
               'The rejected 508-file Atlas candidate remains UNVERIFIED. The immutable reviewed '
               '25-path META R4 candidate is adopted exactly once through '
               'coverage-review-meta-r4-direct-additions.tsv; its source-specific overlay '
               'preserves exact path/blob/scope evidence and does not imply runtime, admin, '
               'provider, or readiness proof. The immutable reviewed 25-path META R5 '
               'instruction-efficiency candidate is separately adopted exactly once through '
               'coverage-review-meta-r5-instruction-efficiency-direct-additions.tsv; the '
               'source-row evidence does not attest runtime model/effort, isolation, answer '
               'quality/safety, A/B superiority, provider permission, cost, or readiness, and the '
               'already-DIRECT R5Q Results row remains separate. The immutable reviewed 11-path '
               'META R6 prompt-family candidate is separately adopted exactly once through '
               'coverage-review-meta-r6-prompts-direct-additions.tsv; prompt text remains source '
               'evidence rather than standing authority, retired/history packets remain '
               'non-dispatchable, templates require fresh live authorization, and no '
               'provider/runtime/admin/security/production/recovery/readiness/completion result is '
               'attested. R7 rebaselines only META to protected main '
               '23b21e9b1b2d4b6c3a5cac3d4c7a18747804c090 and refreshes five existing DIRECT rows '
               'in place while adopting exactly fourteen newly DIRECT current-main governance rows '
               'through coverage-review-meta-current-main-governance-direct-additions.tsv. The 26 '
               'historical repository-audit packet leaves remain UNVERIFIED; source existence and '
               'deterministic tests do not prove live operational capability, provider/runtime '
               'state, readiness, or completion. The clean, frozen PR #209 one-leaf CI-contract '
               'packet is adopted exactly once through '
               'coverage-review-audit186-semantic-03-direct-additions.tsv; it records bounded '
               'source-contract semantics only and does not attest current workflows, live '
               'protection, provider CI, runtime, readiness, or completion.',
 'new_scoped_paths_since_r2': 244,
 'scoped_review_paths': 309,
 'grouped_revalidated_paths': 113,
 'semantically_classified_paths': 422,
 'unverified_semantics_total': 3939,
 'coverage_dimension_note': 'DIRECT records bounded source review, not universal approval. The 309 '
                            'DIRECT paths comprise the prior 308 plus exactly one canonical META '
                            'CI-contract leaf adopted from frozen worker PR #209; META contributes '
                            '96 DIRECT of 210 leaves. The 26 historical repository-audit packet '
                            'leaves remain UNVERIFIED. Platform contributes 168 DIRECT and 113 '
                            'GROUPED paths; all provider counts are unchanged.',
 'rejected_group_candidates': 1}
EXPECTED_UNKNOWNS = [{'id': 'SEMANTIC-COVERAGE',
  'missing': '3939 source leaves retain UNVERIFIED semantics; 422 of 4361 leaves are semantically '
             'classified',
  'reason': 'Source bytes are available; 309 DIRECT scoped path reviews are bound (the prior 294, '
            'with five already-DIRECT META governance rows refreshed in place and exactly fourteen '
            'previously UNVERIFIED/new governance rows adopted through the R7 overlay; the five '
            'refreshes are not re-counted), and 113 bounded GROUPED Platform paths remain bound. '
            'META is rebaselined to 210 leaves at protected main '
            '23b21e9b1b2d4b6c3a5cac3d4c7a18747804c090; the other four source coordinates remain '
            'pinned. The 26 historical repository-audit packet leaves remain UNVERIFIED. R7 '
            'evidence is bounded source semantics and exercised deterministic assertions only; it '
            'does not prove live executor/capability/Merge Queue operation, provider/runtime/admin '
            'state, readiness, or completion. The frozen PR #209 CI-contract leaf adds one bounded '
            'META DIRECT source review; PR #204 remains unadopted and PR #207 remains void.',
  'effect': 'Original exhaustive completeness cannot be claimed from 422 semantically classified '
            'leaves out of 4361.',
  'owner_route': 'META186 plus provider audit owners',
  'closure_condition': 'Import exact historical disposition ledgers with bounded validity, review '
                       'changed/uncovered authored families, and retain justified grouping/N/A.'},
 {'id': 'HISTORY-REVALIDATION',
  'missing': 'Current outcome of explicitly unverified historical findings',
  'reason': 'Source changed, live PR/ref state not read or runtime condition unexecuted.',
  'effect': '77 individual records are accounted, not77 proven current outcomes; later metadata '
            'reconciliation is separate from source/regression qualification.',
  'owner_route': 'META153/Game364/Platform451/Atlas315',
  'closure_condition': 'Resolve each REQUIRES/UNKNOWN/OPEN_INHERITED row with exact '
                       'source/runtime/live evidence.'},
 {'id': 'ADMIN-STATE',
  'missing': 'Current organization/admin security settings',
  'reason': 'Managed integration does not expose all admin-only configuration.',
  'effect': 'No current private reporting/scanning/member/privilege attestation.',
  'owner_route': 'Organization owner via META186',
  'closure_condition': 'Provide dated nonsecret exported settings and authorized verification; '
                       'never secret values.'},
 {'id': 'INFRA-STATE',
  'missing': 'Private production runtime configuration',
  'reason': 'No host exception or production access used.',
  'effect': 'No infrastructure health or deployment readiness conclusion.',
  'owner_route': 'Provider operations owners',
  'closure_condition': 'Authorized read-only configuration/health snapshot with redaction and '
                       'exact release.'},
 {'id': 'RECOVERY',
  'missing': 'Current release/data restore/rollback',
  'reason': 'All50 Platform migration up paths ran on the synthetic SQLite UI fixture and up/down '
            'source was read; current-data upgrade/down/restore and measured RPO/RTO remain '
            'unexecuted.',
  'effect': 'RPO/RTO and live data recovery not qualified.',
  'owner_route': 'META59/60 and provider operations',
  'closure_condition': 'Isolated approved current-release/data restore with measured RPO/RTO, '
                       'smoke, rollback and cleanup.'},
 {'id': 'COST-CI',
  'missing': 'Representative complete candidate cost/latency/cache/retry and billed-usage evidence',
  'reason': 'R3 acquires84 completed runs/418 jobs across seven newest12-run strata;16 anomalous '
            'job times remain unknown. No random/full candidate cohort or earlier-attempt/billing '
            'history.',
  'effect': 'Measured observations exist, but no organization savings, flake rate or pure '
            'queue-time claim follows.',
  'owner_route': 'Provider CI programmes',
  'closure_condition': 'Collect representative recent PR/MQ/push cohort, sample criteria and '
                       'timestamps; measure queue/run/capacity/cache/retry/yield before changes.'},
 {'id': 'COST-AGENTS',
  'missing': 'Actual token/API/wall-clock cost',
  'reason': 'R5Q explicitly labels these NOT_MEASURED.',
  'effect': 'Fewer Markdown reads do not prove token/billing savings.',
  'owner_route': 'META instruction optimization owner',
  'closure_condition': 'Instrument supported execution telemetry, stratify task classes and '
                       'compare cost/quality/safety without claiming an enforced model default.'},
 {'id': 'SUPPLY-CHAIN',
  'missing': 'Fresh CVE/SBOM/history/provenance assessment',
  'reason': 'Locked Platform Composer audit at recorded execution returned0 advisories/0 '
            'abandoned; remaining ecosystems, full SBOM/provenance/secret-history and freshness '
            'are not established.',
  'effect': 'Lockfiles and Dependabot do not establish clean supply chain.',
  'owner_route': 'Provider security owners',
  'closure_condition': 'Authorized advisory/SBOM/provenance scans with '
                       'source/lock/time/scope/exclusion and triage; keep sensitive findings '
                       'private.'},
 {'id': 'NATIVE-G1',
  'missing': 'Game native durable user journey',
  'reason': 'No actual native/durable G1 user journey was executed in this audit continuation; '
            'provider programme state must be read separately rather than inferred from component '
            'CI.',
  'effect': 'Component/source tests cannot establish actual gameplay composition.',
  'owner_route': 'Game364/162',
  'closure_condition': 'Real producer/native command -> logical owner -> durable effect -> visible '
                       'projection through reconnect/restart with no duplicate effect/rollback.'},
 {'id': 'UI-343',
  'missing': 'Initialized Atlas product/UI acceptance',
  'reason': 'Platform public fixture now has48 scoped cases/eight author-reviewed screenshots. '
            'This does not supply initialized Atlas world/renderer or native Game acceptance; '
            'Atlas maintenance authority remains separate.',
  'effect': 'No full product UX, renderer synchronization or accessibility PASS.',
  'owner_route': 'Atlas343/344; maintenance315',
  'closure_condition': 'Qualified minimum-data browser environment, pinned Playwright, real '
                       'journeys/screenshots/keyboard/accessibility checks and independent '
                       'acceptance.'},
 {'id': 'PORTABILITY',
  'missing': 'Complete supported OS/runtime matrix',
  'reason': 'R3 adds supported PHP8.5 and Go Gateway execution on isolated hosted Linux, plus '
            'prior Python/Node. Complete Windows/GPU/native-Game and production-supported matrix '
            'not executed.',
  'effect': 'No current Windows/GPU/full supported runtime qualification.',
  'owner_route': 'Provider build owners',
  'closure_condition': 'Execute bounded required native/OS matrix with exact source/toolchain '
                       'identities.'},
 {'id': 'LIVE-TELEMETRY',
  'missing': 'Production SLO/alerts and failure yield',
  'reason': 'No current telemetry queried.',
  'effect': 'No measured availability, alert correctness or failure recovery conclusion.',
  'owner_route': 'Provider operations',
  'closure_condition': 'Read dated sanitized metrics, exercise approved isolated alert delivery '
                       'and map critical journeys to observable conditions.'},
 {'id': 'PRIVACY-RIGHTS',
  'missing': 'Complete data/asset rights and privacy posture',
  'reason': 'Root license inventory and repository statements are not complete rights/privacy '
            'assessments.',
  'effect': 'No legal compliance or third-party-data clearance conclusion.',
  'owner_route': 'Owner plus provider data/security owners',
  'closure_condition': 'Document intended META/Atlas terms, asset provenance/usage terms, data '
                       'inventory/retention/consent boundaries and appropriate expert review.'},
 {'id': 'PLATFORM-H02',
  'missing': 'Security maintainer disposition for the already-disclosed characterization and '
             'current-generation regression/remediation',
  'reason': 'Controlled source-pinned characterization exists. Independent review established that '
            'mechanism details were present in public ancestor commits and public Actions '
            'artifacts, so that material must be treated as disclosed. The current report '
            'intentionally does not repeat the mechanism. Artifact deletion/expiry, current live '
            'reachability, private-advisory submission and remediation are not established.',
  'effect': 'Cannot claim confidentiality restoration, private advisory submission, current '
            'exploitability status or completed security remediation.',
  'owner_route': 'Platform451 via the private reporting process in Oteryn/Oteryn-Platform '
                 'SECURITY.md',
  'closure_condition': 'Platform security maintainer assesses severity/reachability on relevant '
                       'current source through the private reporting route, binds a deterministic '
                       'regression and disposition/remediation evidence, and separately verifies '
                       'any artifact deletion/expiry before claiming historical material is no '
                       'longer downloadable.'}]
R3_REVIEW = {
    'reviewed_head': '9096edd135d42f31da4824f4c4fb50ee187de2c9',
    'result': 'CHANGES_REQUIRED',
    'p1': 4,
    'p2': 1,
    'author_remediation': 'PUBLISHED_AND_SUBSEQUENTLY_HARDENED',
    'fresh_independent_rereview_required': False,
    'latest_repair_rereview_requested_head': '3eb62ef72c1e13412fa45d5b25d597d112d9ae7d',
    'security_disclosure_state': 'PUBLIC_ANCESTOR_HISTORY_AND_ARTIFACTS_TREATED_AS_DISCLOSED; current report does not repeat mechanism details; deletion/expiry not established',
    'latest_completed_rereview': {
        'reviewed_head': '3eb62ef72c1e13412fa45d5b25d597d112d9ae7d',
        'result': 'PASS_NO_NEW_P0_P1_P2',
        'review_summary': 'Completed for 3eb62ef',
        'review_comment_id': 5609072309,
        'review_comment': "Codex Review: Didn't find any major issues",
        'provenance': 'Observed external mutable GitHub PR #185 metadata; not author-generated audit evidence.',
        'p1': 0,
        'p2': 0,
        'new_material_findings': [],
    },
    'fresh_rereview_reason': 'SATISFIED_BY_EXTERNAL_PR_METADATA: fresh independent exact-head review completed cleanly on reviewed implementation 3eb62ef72c1e13412fa45d5b25d597d112d9ae7d (comment 5609072309). Later terminal cleanup head 12d6ee2f76f3ed23ee6a5d78131f2f64eaa2c97d removes only the two bounded proof workflows and records remaining_bounded_proof_workflows=[]; post-cleanup META CI run 34408192898/job 102656129082 succeeded and terminal read-only verifier comment 5609155461 reported 10/10 current-state tests PASS. These are external mutable lifecycle facts, not author evidence, whole-audit PASS, independent 10/10, or product readiness.',
    'reviewed_implementation_head': '3eb62ef72c1e13412fa45d5b25d597d112d9ae7d',
    'terminal_cleanup': {
        'head': '12d6ee2f76f3ed23ee6a5d78131f2f64eaa2c97d',
        'remaining_bounded_proof_workflows': [],
        'meta_ci_run_id': 34408192898,
        'meta_ci_job_id': 102656129082,
        'meta_ci_result': 'SUCCESS',
        'terminal_verifier_comment_id': 5609155461,
        'terminal_verifier_tests': '10/10 PASS',
        'provenance': 'Observed external mutable GitHub PR #185 metadata and read-only verifier output; not author-generated audit evidence.',
    },
}
def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_verification_results(results):
    require(type(results) is list, 'verification results must be a list')
    require(
        len(results) == len(VERIFICATION_RESULT_IDS)
        and tuple(row.get('id') for row in results if type(row) is dict) == VERIFICATION_RESULT_IDS,
        'verification result identity/order drift',
    )
    for row in results:
        require(type(row) is dict and tuple(row) == VERIFICATION_RESULT_KEYS,
                'verification result key/order drift')
        require(type(row['exit_code']) is int and row['exit_code'] == 0,
                'verification result did not succeed')
    encoded=json.dumps(results,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')
    require(hashlib.sha256(encoded).hexdigest()==VERIFICATION_RESULTS_SHA256,
            'verification result content drift')


def json_exact(left, right):
    """Compare JSON values recursively without Python's bool/int equivalence."""
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(json_exact(left[key], right[key]) for key in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(json_exact(a, b) for a, b in zip(left, right))
    return left == right


def validate_residual_obligations_paragraph(text: str) -> None:
    require(text.count(SECTION_7_HEADING) == 1, 'section 7 heading missing/duplicated')
    require(text.count(SECTION_8_HEADING) == 1, 'section 8 heading missing/duplicated')
    start = text.index(SECTION_7_HEADING)
    end = text.index(SECTION_8_HEADING, start)
    section = text[start:end]
    paragraphs = tuple(
        re.sub(r'\s+', ' ', part.strip())
        for part in re.split(r'\n\s*\n', section)
        if part.strip()
    )
    expected = tuple(re.sub(r'\s+', ' ', part) for part in EXPECTED_SECTION_7_PARAGRAPHS)
    require(paragraphs == expected, 'section 7 paragraph sequence drift')


def _current_coverage_table() -> tuple[str, ...]:
    per_repository = EXPECTED_COVERAGE_SUMMARY['per_repository']
    rows = [CURRENT_COVERAGE_TABLE_HEADER, '|---|---:|---:|---:|---:|']
    for repository in ('meta', 'game', 'platform', 'atlas', 'migration_archive'):
        values = per_repository[repository]
        rows.append(f"| {repository} | {values['leaves']} | {values['direct_scoped']} | {values['grouped']} | {values['unverified_semantics']} |")
    rows.append(
        f"| **Total** | **{EXPECTED_COVERAGE_SUMMARY['source_leaf_total']}** | "
        f"**{EXPECTED_COVERAGE_SUMMARY['scoped_review_paths']}** | "
        f"**{EXPECTED_COVERAGE_SUMMARY['grouped_revalidated_paths']}** | "
        f"**{EXPECTED_COVERAGE_SUMMARY['unverified_semantics_total']}** |"
    )
    return tuple(rows)


def validate_current_coverage_section(text: str) -> None:
    """Bind the current §1 table/adoption/history slot while leaving scoped history intact."""
    require(text.count(SECTION_1_HEADING) == 1 and text.count(SECTION_2_HEADING) == 1,
            'report section 1 boundary drift')
    section = text.split(SECTION_1_HEADING, 1)[1].split(SECTION_2_HEADING, 1)[0]
    lines = section.splitlines()
    require(lines.count(CURRENT_COVERAGE_TABLE_HEADER) == 1,
            'current coverage table missing or duplicated')
    start = lines.index(CURRENT_COVERAGE_TABLE_HEADER)
    table = _current_coverage_table()
    require(tuple(lines[start:start + len(table)]) == table, 'current coverage table drift')
    remainder = '\n'.join(lines[start + len(table):]).strip()
    paragraphs = tuple(re.sub(r'\s+', ' ', part.strip())
                       for part in re.split(r'\n\s*\n', remainder) if part.strip())
    require(len(paragraphs) >= 6, 'current coverage status slot incomplete')
    require(paragraphs[0] == CURRENT_R5_ADOPTION_PARAGRAPH, 'current R5 adoption paragraph drift')
    require(paragraphs[1] == CURRENT_R6_ADOPTION_PARAGRAPH, 'current R6 adoption paragraph drift')
    require(paragraphs[2] == CURRENT_R7_ADOPTION_PARAGRAPH, 'current R7 adoption paragraph drift')
    require(paragraphs[3] == CURRENT_SEMANTIC_03_ADOPTION_PARAGRAPH, 'current Semantic 03 adoption paragraph drift')
    require(paragraphs[4] == CURRENT_HISTORY_ANNOTATION, 'current history annotation drift')
    require(paragraphs[5] == EXPECTED_PRE_ANNOUNCEMENTS_MARKETPLACE_SNAPSHOT,
            'historical snapshot is missing, reordered, or drifted')
    require(section.count(CURRENT_R5_ADOPTION_PARAGRAPH) == 1,
            'current R5 adoption paragraph missing or duplicated')
    require(section.count(CURRENT_R7_ADOPTION_PARAGRAPH) == 1,
            'current R7 adoption paragraph missing or duplicated')
    require(section.count(CURRENT_HISTORY_ANNOTATION) == 1,
            'current history annotation missing or duplicated')
    require(section.count(CURRENT_R6_ADOPTION_PARAGRAPH) == 1,
            'current R6 adoption paragraph missing or duplicated')


def validate_complete_source_identity_section(text: str) -> None:
    """Bind every UTF-8 byte in §1, including prose after the readable status slot."""
    require(text.count(SECTION_1_HEADING) == 1, 'section 1 heading missing/duplicated')
    require(text.count(SECTION_2_HEADING) == 1, 'section 2 heading missing/duplicated')
    start = text.index(SECTION_1_HEADING)
    end = text.index(SECTION_2_HEADING)
    require(start < end, 'report section 1 boundary ordering drift')
    digest = hashlib.sha256(text[start:end].encode('utf-8')).hexdigest()
    require(digest == EXPECTED_SECTION_1_SHA256, 'complete report section 1 byte contract drift')


def load_authenticated_report_markdown(report_path: Path) -> str:
    """Read, authenticate, and decode the companion Markdown exactly once."""
    companion = report_path.with_suffix('.md')
    require(companion.is_file(), 'companion report missing')
    raw = companion.read_bytes()
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise ValueError('companion report must be valid UTF-8') from exc
    require(hashlib.sha256(raw).hexdigest() == EXPECTED_REPORT_MARKDOWN_SHA256,
            'complete companion report byte contract drift')
    return text


def parse_json_bytes(raw: bytes):
    def pairs(items):
        result={}
        for key,value in items:
            require(key not in result,'duplicate JSON key')
            result[key]=value
        return result
    try:
        text=raw.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise ValueError('JSON must be valid UTF-8') from exc
    return json.loads(text, object_pairs_hook=pairs)


def read_json(path):
    return parse_json_bytes(path.read_bytes())


def git_blob_sha(raw: bytes) -> str:
    header=b'blob '+str(len(raw)).encode('ascii')+b'\0'
    return hashlib.sha1(header+raw).hexdigest()


def read_tsv(path):
    require(path.is_file(), 'missing TSV: '+path.name)
    with path.open(encoding='utf-8', newline='') as handle:
        reader=csv.DictReader(handle, delimiter='\t')
        require(reader.fieldnames and len(reader.fieldnames)==len(set(reader.fieldnames)), 'duplicate/absent TSV header')
        rows=list(reader)
    require(rows and all(None not in row and None not in row.values() for row in rows), 'invalid TSV: '+path.name)
    return rows


def parse_tsv_bytes(raw: bytes, expected_fields: tuple[str, ...], label: str):
    """Parse the same complete TSV snapshot whose bytes were authenticated."""
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise ValueError(label + ' must be valid UTF-8') from exc
    reader = csv.DictReader(io.StringIO(text, newline=''), delimiter='\t')
    require(tuple(reader.fieldnames or ()) == expected_fields, label + ' header drift')
    rows = list(reader)
    require(rows and all(None not in row and None not in row.values() for row in rows),
            'invalid ' + label)
    return rows


def load_authenticated_tsv(path: Path, expected_sha256: str,
                           expected_fields: tuple[str, ...], label: str):
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == expected_sha256,
            label + ' canonical snapshot drift')
    return parse_tsv_bytes(raw, expected_fields, label)


def validate_finding_report_boundary(findings, confirmed_p0):
    require(type(confirmed_p0) is int, 'confirmed P0 count must be an integer')
    scoped_p0 = sum(row['priority'] == 'P0' for row in findings)
    require(scoped_p0 == confirmed_p0, 'confirmed scoped P0 count mismatch')


def validate_domain_report_boundary(domains, report_all_pass):
    require(type(report_all_pass) is bool, 'audit domain all-pass flag must be Boolean')
    matrix_all_pass = all(
        row['opinion'] == 'PASS' and row['remaining_limit'] == 'NONE'
        for row in domains
    )
    require(report_all_pass == matrix_all_pass, 'audit domain all-pass boundary mismatch')


def unique(rows, key, label):
    values=[key(row) for row in rows]
    require(len(values)==len(set(values)), 'duplicate '+label)


def load_review(base: Path, doc: dict):
    review=read_tsv(base/'coverage-review.tsv')
    additions_binding=doc.get('coverage_review_additions')
    if additions_binding is not None:
        require(additions_binding==DIRECT_ADDITIONS_BINDING,'coverage review additions binding drift')
        additions=read_tsv(base/DIRECT_ADDITIONS)
        require(additions,'coverage review additions empty')
        review=review+additions
    meta_binding=doc.get('coverage_review_meta_r4_direct_additions')
    if meta_binding is not None:
        require(meta_binding==META_R4_DIRECT_ADDITIONS_BINDING,'META R4 direct additions binding drift')
        meta_additions=read_tsv(base/META_R4_DIRECT_ADDITIONS)
        require(len(meta_additions)==25,'META R4 direct additions must contain exactly 25 rows')
        review=review+meta_additions
    r5_binding=doc.get('coverage_review_meta_r5_instruction_efficiency_direct_additions')
    if r5_binding is not None:
        require(r5_binding==META_R5_DIRECT_ADDITIONS_BINDING,'META R5 direct additions binding drift')
        r5_additions=read_tsv(base/META_R5_DIRECT_ADDITIONS)
        require(len(r5_additions)==25,'META R5 direct additions must contain exactly 25 rows')
        review=review+r5_additions
    r6_binding=doc.get('coverage_review_meta_r6_prompts_direct_additions')
    if r6_binding is not None:
        require(r6_binding==META_R6_DIRECT_ADDITIONS_BINDING,'META R6 direct additions binding drift')
        r6_additions=read_tsv(base/META_R6_DIRECT_ADDITIONS)
        require(len(r6_additions)==11,'META R6 direct additions must contain exactly 11 rows')
        review=review+r6_additions
    r7_binding=doc.get('coverage_review_meta_current_main_governance_direct_additions')
    if r7_binding is not None:
        require(r7_binding==META_R7_DIRECT_ADDITIONS_BINDING,'META R7 direct additions binding drift')
        r7_additions=read_tsv(base/META_R7_DIRECT_ADDITIONS)
        require(len(r7_additions)==14,'META R7 direct additions must contain exactly 14 rows')
        review=review+r7_additions
    semantic_03_binding=doc.get('coverage_review_audit186_semantic_03_direct_additions')
    if semantic_03_binding is not None:
        require(semantic_03_binding==AUDIT186_SEMANTIC_03_DIRECT_ADDITIONS_BINDING,'AUDIT186 Semantic 03 additions binding drift')
        semantic_03_additions=read_tsv(base/AUDIT186_SEMANTIC_03_DIRECT_ADDITIONS)
        require(len(semantic_03_additions)==1,'AUDIT186 Semantic 03 additions must contain exactly one row')
        expected_semantic_03={'repository':'meta','path':'docs/ci/CI_CONTRACT.md','blob_sha':'3c6d36cd58cd81f332382db7f2eda78261788caa','depth':'SCOPED_SEMANTIC_REVIEW','scope':'The full frozen leaf was reviewed as the declared META CI contract: META-only validation scope, stable meta-gate intent, GitHub-hosted runner intent, provider CI ownership boundaries, and documented protection/integration intent.','line_ranges':'[]','execution_evidence':'BOUNDED_FULL_FILE_SOURCE_REVIEW_ADOPTED_FROM_PR_209_HEAD_9ad2942ba0dedb5b94e437c32b85161c6c59885a_AFTER_CLEAN_INDEPENDENT_REVIEW; source contract semantics only; no current workflow, live ruleset/protection, check execution, provider CI, runtime, readiness, or audit-completion attestation'}
        require(semantic_03_additions[0]==expected_semantic_03,'AUDIT186 Semantic 03 canonical row drift')
        review=review+semantic_03_additions
    unique(review,lambda r:(r['repository'],r['path']),'review path')
    return review


def safe_relative(path):
    parts=path.split('/')
    return bool(parts) and not path.startswith('/') and '\\' not in path and all(p not in {'','.', '..'} for p in parts)


def tree_sha(entries):
    root={}
    for row in entries:
        parts=row['path'].split('/')
        require(parts and all(p not in {'','.', '..'} for p in parts), 'unsafe path')
        require(SHA.fullmatch(row['object_sha']) is not None, 'invalid object SHA')
        require(row['mode'] in {'100644','100755','120000','160000'}, 'unsupported mode')
        node=root
        for part in parts[:-1]:
            node=node.setdefault(part,{})
            require(isinstance(node,dict), 'file/directory conflict')
        require(parts[-1] not in node,'duplicate inventory path')
        node[parts[-1]]=(row['mode'],row['object_sha'])
    def digest(node):
        data=bytearray()
        for name,value in sorted(node.items(),key=lambda kv:(kv[0]+('/' if isinstance(kv[1],dict) else '')).encode('utf-8')):
            mode,oid=('40000',digest(value)) if isinstance(value,dict) else value
            data.extend(mode.encode()+b' '+name.encode('utf-8')+b'\0'+bytes.fromhex(oid))
        return hashlib.sha1(b'tree '+str(len(data)).encode()+b'\0'+data).hexdigest()
    return digest(root)


def load_groups(base, repo):
    path=base/'coverage-groups.json'
    raw=path.read_bytes()
    require(git_blob_sha(raw)==COVERAGE_GROUPS_BLOB_SHA,
            'coverage groups canonical blob drift')
    doc=parse_json_bytes(raw)
    require(type(doc.get('schema_version')) is int and doc['schema_version']==1,'coverage group schema')
    groups=doc.get('groups')
    require(isinstance(groups,list),'coverage groups missing')
    rejected=doc.get('rejected_candidates',[])
    require(isinstance(rejected,list),'rejected coverage candidates invalid')
    unique(groups+rejected,lambda row:row.get('id'),'coverage group/candidate id')
    for row in rejected:
        require(row.get('repository') in repo,'rejected coverage repository')
        require(row.get('disposition')=='REVALIDATION_FAILED_NOT_ADOPTED','rejected coverage disposition')
        require(type(row.get('expected_count')) is int and row['expected_count']>0,'rejected coverage count')
        evaluation=row.get('evaluation') or {}
        require(evaluation.get('outcome')=='REJECTED_NOT_COUNTED_AS_GROUPED','rejected coverage outcome')
        require(type(evaluation.get('qualification_run')) is int and type(evaluation.get('qualification_job')) is int,'rejected coverage execution identity')
        tests=evaluation.get('focused_current_consumer_tests') or {}
        require(type(tests.get('passed')) is int and type(tests.get('failed')) is int and tests.get('failed',0)>0,'rejected coverage failure evidence')
    prefixes=[]
    for row in groups:
        require(row.get('repository') in repo,'coverage group repository')
        require(row.get('disposition')=='GROUPED','coverage group disposition')
        prefix=row.get('path_prefix')
        require(isinstance(prefix,str) and prefix.endswith('/') and safe_relative(prefix[:-1]) and '*' not in prefix,'unsafe coverage group prefix')
        require(type(row.get('expected_count')) is int and row['expected_count']>0,'coverage group count')
        require(row.get('depth')=='GROUPED_REVALIDATED','coverage group depth')
        require(isinstance(row.get('scope'),str) and row['scope'].strip(),'coverage group scope')
        require(isinstance(row.get('limitations'),str) and row['limitations'].strip(),'coverage group limitations')
        hist=row.get('historical_evidence') or {}
        require(hist.get('repository')==repo[row['repository']]['repository'],'coverage historical repository')
        for key in ['publication_commit','coverage_rules_blob','audited_main_sha','audited_main_tree']:
            require(isinstance(hist.get(key),str) and SHA.fullmatch(hist[key]),'coverage historical identity')
        require(hist.get('pattern')==prefix+'**' and hist.get('count')==row['expected_count'],'coverage historical rule mismatch')
        require(isinstance(hist.get('coverage_rules_path'),str) and safe_relative(hist['coverage_rules_path']),'coverage historical path')
        require(isinstance(hist.get('basis'),str) and hist['basis'].strip(),'coverage historical basis')
        current=row.get('current_revalidation') or {}
        source=repo[row['repository']]
        require(current.get('source_commit')==source['commit_sha'] and current.get('source_tree')==source['tree_sha'],'coverage current source mismatch')
        require(current.get('changed_paths_under_group_prefix')==0,'coverage group changed-path carry-forward forbidden')
        require(current.get('historical_to_current_compare_status') in {'ahead','identical'},'coverage compare state')
        blobs=current.get('current_blobs')
        require(isinstance(blobs,dict) and blobs,'coverage current blobs missing')
        for path,oid in blobs.items():
            require(safe_relative(path) and isinstance(oid,str) and SHA.fullmatch(oid),'coverage current blob binding')
        checks=current.get('required_checks')
        require(isinstance(checks,list) and checks and all(isinstance(x,str) and x.strip() for x in checks),'coverage required checks')
        for other_repo,other_prefix in prefixes:
            if other_repo==row['repository']:
                require(not (prefix.startswith(other_prefix) or other_prefix.startswith(prefix)),'overlapping coverage group prefixes')
        prefixes.append((row['repository'],prefix))
    return groups


def build_ledger(doc, review, groups, inventory_dir):
    repo=doc['repositories']
    data=[]
    mapping={(r['repository'],r['path']):r for r in review}
    grouped_counts={key:0 for key in repo}
    for key in sorted(repo):
        inv=read_json(inventory_dir/(key+'.json'));r=repo[key]
        require(inv['commit_sha']==r['commit_sha'] and inv['tree_sha']==r['tree_sha'],'inventory coordinate mismatch')
        require(len(inv['entries'])==r['leaf_count'] and tree_sha(inv['entries'])==r['tree_sha'],'inventory tree/count mismatch')
        inventory_by_path={x['path']:x for x in inv['entries']}
        paths=set(inventory_by_path)
        require(all(path in paths for rep,path in mapping if rep==key),'review path absent')
        grouped={}
        for group in [g for g in groups if g['repository']==key]:
            for path, oid in group['current_revalidation']['current_blobs'].items():
                current_entry=inventory_by_path.get(path)
                require(current_entry is not None,'coverage current blob path absent from inventory')
                require(current_entry['mode']=='100644','coverage current blob is not a regular source leaf')
                require(current_entry['object_sha']==oid,'coverage current blob OID mismatch')
            matched=[x for x in inv['entries'] if x['path'].startswith(group['path_prefix'])]
            require(len(matched)==group['expected_count'],'coverage group inventory count mismatch')
            for x in matched:
                require(x['mode']=='100644','coverage group contains non-regular leaf')
                require((key,x['path']) not in mapping,'DIRECT/GROUPED overlap')
                require(x['path'] not in grouped,'GROUPED/GROUPED overlap')
                grouped[x['path']]=group
            grouped_counts[key]+=len(matched)
        for x in sorted(inv['entries'],key=lambda x:x['path'].encode('utf-8')):
            reviewed=mapping.get((key,x['path']))
            require(reviewed is None or reviewed['blob_sha']==x['object_sha'],'review blob mismatch')
            group=grouped.get(x['path'])
            if reviewed:
                disposition='DIRECT';depth=reviewed['depth'];scope=reviewed['scope']
            elif group:
                disposition='GROUPED';depth=group['depth'];scope=group['scope']
            else:
                disposition='UNVERIFIED';depth='IDENTITY_ONLY';scope=DEFAULT_REASON
            data.append({'repository_id':key,'commit_sha':r['commit_sha'],'tree_sha':r['tree_sha'],'path':x['path'],'mode':x['mode'],'object_sha':x['object_sha'],'disposition':disposition,'depth':depth,'scope':scope})
    buf=io.StringIO(newline='');w=csv.DictWriter(buf,fieldnames=list(data[0]),lineterminator='\n');w.writeheader();w.writerows(data)
    return buf.getvalue().encode('utf-8'),grouped_counts


def rebuild_ledger(report_path: Path, inventory_dir: Path):
    doc=read_json(report_path)
    repo=doc['repositories']
    require(set(repo)=={'meta','game','platform','atlas','migration_archive'},'repository scope')
    base=report_path.parent/doc['evidence_directory']
    review=load_review(base,doc)
    groups=load_groups(base,repo)
    for row in review:
        for group in groups:
            require(not (row['repository']==group['repository'] and row['path'].startswith(group['path_prefix'])),'DIRECT/GROUPED overlap')
    return build_ledger(doc,review,groups,inventory_dir)


def validate(report_path: Path, inventory_dir: Path|None=None, ledger_output: Path|None=None):
    doc=read_json(report_path)
    require(type(doc.get('schema_version')) is int and doc['schema_version']==2,'schema_version')
    require(doc['production_readiness_claimed'] is False,'production claim forbidden')
    require(doc.get('semantic_coverage') == EXPECTED_REPORT_SEMANTIC_COVERAGE,
            'report semantic coverage status drift')
    require(doc['independent_score'] is None,'independent score not established')
    require(doc['severity_counts_exhaustive'] is False,'exhaustive severity claim unsupported')
    require(doc['status']=='QUALIFIED_AUDIT_WITH_EXPLICIT_OPEN_SCOPE','unsupported completion status')
    require(doc.get('audit_completion') == EXPECTED_AUDIT_COMPLETION,'audit completion boundary drift')
    repo=doc['repositories']
    require(set(repo)=={'meta','game','platform','atlas','migration_archive'},'repository scope')
    for v in repo.values():
        require(SHA.fullmatch(v['commit_sha']) and SHA.fullmatch(v['tree_sha']),'invalid source identity')
        require(type(v['leaf_count']) is int and v['leaf_count']>0,'invalid leaf count')
    require(doc['evidence_directory']=='organization-audit-20260907','invalid evidence directory')
    require(doc.get('coverage_review_additions')==DIRECT_ADDITIONS_BINDING,'canonical direct additions binding drift')
    require(doc.get('coverage_review_recorder_additions')==RECORDER_ADDITIONS_BINDING,'recorder additions evidence binding drift')
    require(doc.get('coverage_review_announcements_additions')==ANNOUNCEMENTS_ADDITIONS_BINDING,'Announcements additions evidence binding drift')
    require(doc.get('coverage_review_meta_r4_direct_additions')==META_R4_DIRECT_ADDITIONS_BINDING,'META R4 additions evidence binding drift')
    require(doc.get('r3_meta_r4_direct_candidate')==META_R4_CANDIDATE_BINDING,'META R4 candidate provenance binding drift')
    require(doc.get('r3_meta_r4_direct_adoption_overlay')==META_R4_DIRECT_ADDITIONS_BINDING,'META R4 adoption overlay provenance binding drift')
    require(doc.get('coverage_review_meta_r5_instruction_efficiency_direct_additions')==META_R5_DIRECT_ADDITIONS_BINDING,'META R5 additions evidence binding drift')
    require(doc.get('r3_meta_r5_instruction_efficiency_direct_candidate')==META_R5_CANDIDATE_BINDING,'META R5 candidate provenance binding drift')
    require(doc.get('r3_meta_r5_instruction_efficiency_direct_adoption_overlay')==META_R5_DIRECT_ADDITIONS_BINDING,'META R5 adoption overlay provenance binding drift')
    require(doc.get('coverage_review_meta_r6_prompts_direct_additions')==META_R6_DIRECT_ADDITIONS_BINDING,'META R6 additions evidence binding drift')
    require(doc.get('r3_meta_r6_prompts_direct_candidate')==META_R6_CANDIDATE_BINDING,'META R6 candidate provenance binding drift')
    require(doc.get('r3_meta_r6_prompts_direct_adoption_overlay')==META_R6_DIRECT_ADDITIONS_BINDING,'META R6 adoption overlay provenance binding drift')
    require(doc.get('coverage_review_meta_current_main_governance_direct_additions')==META_R7_DIRECT_ADDITIONS_BINDING,'META R7 additions evidence binding drift')
    require(doc.get('coverage_review_audit186_semantic_03_direct_additions')==AUDIT186_SEMANTIC_03_DIRECT_ADDITIONS_BINDING,'AUDIT186 Semantic 03 additions evidence binding drift')
    require(doc.get('audit186_semantic_03_candidate')=='organization-audit-20260907/audit186-semantic-03-ci-contract-candidate.json','AUDIT186 Semantic 03 candidate binding drift')
    require(doc.get('r7_meta_current_main_governance_direct_candidate')=='organization-audit-20260907/r7-meta-current-main-governance-direct-candidate.json','META R7 candidate provenance binding drift')
    require(doc.get('r7_meta_current_main_governance_direct_adoption_overlay')==META_R7_DIRECT_ADDITIONS_BINDING,'META R7 adoption overlay provenance binding drift')
    require(json_exact(doc.get('r3_review'),R3_REVIEW),'R3 review lifecycle drift')
    base=report_path.parent/doc['evidence_directory']
    findings=load_authenticated_tsv(base/'finding-register.tsv', FINDING_REGISTER_SHA256,
                                    FINDING_REGISTER_FIELDS, 'finding register')
    unique(findings,lambda r:r['id'],'finding id')
    require(len(findings)==doc['reconciled_register_rows'],'finding count mismatch')
    for row in findings:
        require(row['state'] in STATES,'unknown finding state')
        require(row['repository'] in repo,'unknown finding repository')
        require(row['priority'] in {'P0','P1','P2','P3','NOTE','UNRATED'},'invalid priority')
        require(all(row[k].strip() for k in ['title','evidence','owner_route','closure_condition']),'missing finding evidence/closure')
    finding_states={row['id']:row['state'] for row in findings}
    finding_states_raw=json.dumps(finding_states,sort_keys=True,separators=(',',':')).encode('utf-8')
    require(hashlib.sha256(finding_states_raw).hexdigest()==EXPECTED_FINDING_STATES_SHA256,
            'canonical finding state transition drift')
    meta_aud_05=[row for row in findings if row['id']=='META-AUD-05']
    require(len(meta_aud_05)==1 and json_exact(meta_aud_05[0],EXPECTED_META_AUD_05),
            'META-AUD-05 canonical finding drift')
    validate_finding_report_boundary(findings, doc.get('confirmed_p0_in_scoped_review'))
    p1=[r['id'] for r in findings if r['priority']=='P1' and r['scope']=='source_snapshot' and r['state'] in {'CONFIRMED_SOURCE','REPRODUCED'}]
    require(p1==doc['known_source_snapshot_p1_ids'] and len(p1)==doc['known_source_snapshot_p1_count'],'source-snapshot P1 mismatch')
    domains=load_authenticated_tsv(base/'domain-matrix.tsv', DOMAIN_MATRIX_SHA256,
                                   DOMAIN_MATRIX_FIELDS, 'domain matrix')
    unique(domains,lambda r:r['domain'],'domain')
    require({r['domain'] for r in domains}==set('ABCDEFGHIJKLMNOPQRSTUVW'),'A-W matrix incomplete')
    require(len(domains)==doc['audit_domains_accounted'],'domain count')
    require(all(all(r[k].strip() for k in ['acceptance_criterion','method_and_evidence','opinion','remaining_limit','references']) for r in domains),'empty domain evidence')
    validate_domain_report_boundary(domains, doc.get('audit_domains_all_pass'))
    unknowns=read_json(base/'unknowns.json')['items'];unique(unknowns,lambda r:r['id'],'unknown id')
    require(type(doc.get('unresolved_unknowns')) is int and doc['unresolved_unknowns']==14,'report unresolved unknown count must be exactly 14')
    require(len(unknowns)==14,'unresolved unknown count must be exactly 14')
    require({row.get('id') for row in unknowns}==EXPECTED_UNRESOLVED_IDS,'unresolved unknown ID set drift')
    require(json_exact(unknowns,EXPECTED_UNKNOWNS),'unresolved unknown register drift')
    report_markdown = load_authenticated_report_markdown(report_path)
    validate_complete_source_identity_section(report_markdown)
    validate_current_coverage_section(report_markdown)
    validate_residual_obligations_paragraph(report_markdown)
    semantic_coverage=[row for row in unknowns if row.get('id')=='SEMANTIC-COVERAGE']
    require(len(semantic_coverage)==1,'semantic-coverage unknown missing')
    require(json_exact(semantic_coverage[0],SEMANTIC_COVERAGE_UNKNOWN),'semantic-coverage unknown drift')
    independent=[row for row in unknowns if row.get('id')=='INDEPENDENT-REVIEW']
    require(not independent,'resolved independent-review unknown was reintroduced')
    review=load_review(base,doc)
    for row in review:
        require(row['repository'] in repo and SHA.fullmatch(row['blob_sha']),'invalid review source')
        require(row['depth']=='SCOPED_SEMANTIC_REVIEW' and row['scope'].strip(),'unsupported review depth')
        ranges=json.loads(row['line_ranges'])
        require(isinstance(ranges,list) and all(isinstance(x,list) and len(x)==2 and all(type(n)is int for n in x) and 1<=x[0]<=x[1] for x in ranges),'invalid source range')
    require(doc['scoped_review_paths']==len(review),'report scoped review count mismatch')
    groups=load_groups(base,repo)
    grouped_total=sum(g['expected_count'] for g in groups)
    require(doc.get('grouped_revalidated_paths')==grouped_total,'report grouped coverage count mismatch')
    require(doc.get('semantically_classified_paths')==len(review)+grouped_total,'report semantic classification count mismatch')
    for row in review:
        require(not any(row['repository']==g['repository'] and row['path'].startswith(g['path_prefix']) for g in groups),'DIRECT/GROUPED overlap')
    coverage=read_json(base/'coverage-summary.json')
    require(json_exact(coverage,EXPECTED_COVERAGE_SUMMARY),'coverage summary contract drift')
    require(coverage['semantic_completion_claimed'] is False,'unsupported semantic completion')
    require(coverage['source_leaf_total']==sum(r['leaf_count'] for r in repo.values()),'leaf total mismatch')
    require(coverage.get('scoped_review_paths')==len(review),'coverage direct count mismatch')
    require(coverage.get('grouped_revalidated_paths')==grouped_total,'coverage grouped count mismatch')
    require(coverage.get('semantically_classified_paths')==len(review)+grouped_total,'coverage semantic count mismatch')
    for key,r in repo.items():
        c=coverage['per_repository'][key]
        direct=sum(row['repository']==key for row in review)
        grouped=sum(g['expected_count'] for g in groups if g['repository']==key)
        require(c['leaves']==r['leaf_count'] and c['direct_scoped']==direct and c['grouped']==grouped,'review/group count mismatch')
        require(c['not_applicable']==0,'unexpected N/A reclassification')
        require(c['unverified_semantics']==c['leaves']-direct-grouped,'hidden coverage reclassification')
    require(coverage.get('unverified_semantics_total')==sum(c['unverified_semantics'] for c in coverage['per_repository'].values()),'unverified total mismatch')
    workflows=read_tsv(base/'workflow-inventory.tsv');unique(workflows,lambda r:(r['repository'],r['path']),'workflow')
    require(len(workflows)==doc['workflow_census']['total_workflows'],'workflow count')
    require(sum(int(r['job_count']) for r in workflows)==doc['workflow_census']['total_declared_jobs'],'job count')
    for key in ['meta','game','platform','atlas']:
        subset=[r for r in workflows if r['repository']==key];c=doc['workflow_census'][key]
        require(len(subset)==c['workflows'] and sum(int(r['job_count']) for r in subset)==c['jobs'],'repository workflow/job count')
    require(hashlib.sha256((base/'audit186-semantic-03-ci-contract-candidate.json').read_bytes()).hexdigest()==AUDIT186_SEMANTIC_03_CANDIDATE_SHA256,'AUDIT186 Semantic 03 candidate digest drift')
    require(hashlib.sha256((base/AUDIT186_SEMANTIC_03_DIRECT_ADDITIONS).read_bytes()).hexdigest()==AUDIT186_SEMANTIC_03_OVERLAY_SHA256,'AUDIT186 Semantic 03 overlay digest drift')
    proof=read_json(base/'verification-index.json')
    require(json_exact(proof.get('audit186_semantic_03_ci_contract_direct_adoption'), {'state': 'ADOPTED_BOUNDED_SOURCE_SEMANTICS_NOT_PRODUCT_PASS',
 'worker_pull_request': 209,
 'worker_head': '9ad2942ba0dedb5b94e437c32b85161c6c59885a',
 'candidate': 'audit186-semantic-03-ci-contract-candidate.json',
 'candidate_sha256': '4f9eb30d596da45a95f8cadf37dfee4ae4bb89a2846683098021574613d9676c',
 'adoption_overlay': 'coverage-review-audit186-semantic-03-direct-additions.tsv',
 'adoption_overlay_sha256': '76881b1eace7559a9d84b060c82ccf9bf86ae5627e670535a7680ccb32285de5',
 'source_commit': '23b21e9b1b2d4b6c3a5cac3d4c7a18747804c090',
 'source_tree': 'b8ebb8e50bce14a736fa65590ac121655c52fd12',
 'path': 'docs/ci/CI_CONTRACT.md',
 'blob_sha': '3c6d36cd58cd81f332382db7f2eda78261788caa',
 'depth': 'SCOPED_SEMANTIC_REVIEW',
 'coverage_delta': {'direct': 1, 'unverified': -1, 'semantically_classified': 1},
 'canonical_counts': {'source_leaves': 4361,
                      'direct': 309,
                      'grouped': 113,
                      'unverified': 3939,
                      'semantically_classified': 422},
 'meta_counts': {'source_leaves': 210, 'direct': 96, 'unverified': 114},
 'pr_204_adopted': False,
 'pr_207_included': False,
 'residual_obligations': 14,
 'product_readiness_claimed': False,
 'runtime_or_provider_claimed': False,
 'audit_completion_claimed': False}),'AUDIT186 Semantic 03 adoption index drift')
    require(proof['routing_product_verdict']=='FAIL_FOR_TWO_CASES' and proof['routing_false_negatives']==2,'reproduction misrepresented as product PASS')
    validate_verification_results(proof.get('results'))
    for c in proof['results']:
        require(c['source_commit'] in ({r['commit_sha'] for r in repo.values()} | {'1a01c5b3e08666a82245b1cac78da3736c65e785'}),'unbound execution source')
        require(len(c['log_sha256'])==64,'invalid check record')
    if inventory_dir is not None:
        raw,grouped_counts=build_ledger(doc,review,groups,inventory_dir)
        require(grouped_counts=={key:coverage['per_repository'][key]['grouped'] for key in repo},'inventory grouped count mismatch')
        expected=coverage.get('ledger_sha256')
        require(isinstance(expected,str) and re.fullmatch(r'[0-9a-f]{64}',expected),'ledger digest not finalized')
        require(hashlib.sha256(raw).hexdigest()==expected,'ledger digest mismatch')
        if ledger_output is not None:
            write_new_file_no_symlinks(ledger_output,raw)
    elif ledger_output is not None:
        raise ValueError('inventories required for ledger output')
    return {'result':'ACCOUNTING_VALID_NOT_SEMANTIC_PASS','findings':len(findings),'domains':len(domains),'source_leaves':coverage['source_leaf_total'],'source_snapshot_p1':len(p1),'scoped_review_paths':len(review),'grouped_revalidated_paths':grouped_total,'semantically_classified_paths':len(review)+grouped_total,'unverified_semantics':coverage['unverified_semantics_total'],'tree_and_ledger_verified':inventory_dir is not None,'semantic_coverage':doc['semantic_coverage']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--inventory-dir',type=Path)
    parser.add_argument('--ledger-output',type=Path)
    parser.add_argument('--rebuild-ledger-digest',action='store_true')
    args=parser.parse_args()
    if args.rebuild_ledger_digest:
        require(args.inventory_dir is not None,'inventories required for ledger rebuild')
        raw,counts=rebuild_ledger(args.report,args.inventory_dir)
        print(json.dumps({'result':'LEDGER_REBUILD_NOT_AUDIT_PASS','sha256':hashlib.sha256(raw).hexdigest(),'rows':sum(read_json(args.inventory_dir/(key+'.json'))['entries'].__len__() for key in ['meta','game','platform','atlas','migration_archive']),'grouped_by_repository':counts},indent=2))
        return
    print(json.dumps(validate(args.report,args.inventory_dir,args.ledger_output),indent=2))

if __name__=='__main__':main()
