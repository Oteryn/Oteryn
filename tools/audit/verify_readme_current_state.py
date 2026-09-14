#!/usr/bin/env python3
"""Fail-closed validation for the bounded R3 README current-state contract."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_DIR = Path('.github/workflows')
RETIRED_R7_WORKFLOW = WORKFLOW_DIR / 'organization-audit-meta-current-main-governance-qualification.yml'
EXPECTED_TITLE = '# Organization audit R3 evidence'
EXPECTED_LOCAL_HEADING = '## Local checks'
EXPECTED_EVIDENCE_HEADING = '## Evidence map and durability'
EXPECTED_README_SHA256 = 'fe02bf2edb42e7b42e73016defc0b55753c66738c87672ddf1c77e8289f00e87'
EXPECTED_INTRO = (
    'Governing continuation: META#186, existing PR#185. The main report/JSON owns the scoped opinion; '
    'this is not another approval programme. R3 contains 78 finding records, 23 A–W domains, 14 residual '
    'obligations, 308 DIRECT scoped path reviews and 113 bounded GROUPED Platform paths out of 4361 immutable '
    'leaves. In total, 421 leaves are semantically classified and 3940 retain UNVERIFIED semantics. Full-file, '
    'control-field, translation-range and GROUPED carry-forward evidence are intentionally distinguished.'
)
EXPECTED_REVIEW_CLOSEOUT = (
    'After independent review of `9096edd135d42f31da4824f4c4fb50ee187de2c9`, the verifier was tightened '
    'further. It now parses the original failed browser capture and requires exactly the documented eight '
    '`http_ok` failures, validates the exact 50 migration names against the committed path/blob ledger and bound '
    'successful log, and fails if the raw-archive recount differs semantically from `r3-native-results.json`. '
    'The CI collector now uses exclusive creation for normal and error evidence so an existing file or final-path '
    'symlink cannot be overwritten. `r3-independent-review-corrections.json` records the five review findings and '
    'their bounded corrections. Those five corrections are applied and carried forward in the current audit '
    'lineage; they are not a pending review gate in this README. This historical correction closeout does not '
    'establish organization-wide audit completion, product readiness, provider remediation, or independent 10/10.'
)
EXPECTED_DURABILITY_CLOSEOUT = (
    'The R3 native hosted collector and the completed 31-path batch workflows are absent from the effective tree. '
    'Marketplace/Payments/Wallet qualification, ledger-reproduction and projection workflows and the six-file '
    'Marketplace-test temporary proof workflows were removed after their completed review/cleanup. The '
    'Announcements pre-adoption qualification and projection workflows are removed after their bound successful '
    'runs. The temporary Platform audit-recorder adopted-proof workflow and temporary Platform Announcements '
    'adopted-proof workflow are also absent after their bounded exact-head proof lifecycle. The temporary R7 META '
    'current-main governance qualification workflow was removed after its successful exact-head qualification and '
    'clean independent review; no `organization-audit-*.yml` bounded audit-proof workflows remain in the effective '
    'tree. Historical Actions run/artifact provenance remains external GitHub '
    'Actions metadata; mutable independent-review lifecycle/outcome remains external PR #185 metadata, and PR #185 '
    'remains Draft. No permanent gate, provider writes, deployment, automatic background worker, full semantic '
    'completion, product readiness, or self-awarded score is implied.'
)
STALE_MARKERS = (
    '221 DIRECT scoped path reviews',
    '223 DIRECT scoped path reviews',
    '107 bounded GROUPED Platform paths',
    '3989 retain UNVERIFIED semantics',
    '`3997` leaves retain UNVERIFIED semantics',
    'These remain author remediation until the resulting exact head receives canonical CI and fresh independent re-review.',
    'Temporary Marketplace/Payments/Wallet qualification, ledger-reproduction and projection workflows remain',
    '49-path adoption is rebound and independently reviewed',
    'only the temporary Platform audit-recorder adopted-proof workflow remains',
    'canonical adoption is verified by the temporary Platform Announcements adopted-proof workflow',
    'The current tree retains two bounded audit-proof workflows',
    'The sole retained temporary bounded audit-proof workflow is',
    'it remains pending R7 cleanup',
)
OBLIGATION_TOKEN = re.compile(r'\bobligations?\b', re.IGNORECASE)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def normalize(value: str) -> str:
    return re.sub(r'\s+', ' ', value.strip())


def paragraphs(text: str) -> list[str]:
    return [normalize(part) for part in re.split(r'\n\s*\n', text) if part.strip()]


def validate_text(text: str) -> dict[str, object]:
    require(
        hashlib.sha256(text.encode('utf-8')).hexdigest() == EXPECTED_README_SHA256,
        'README full-document SHA-256 drift',
    )
    items = paragraphs(text)
    require(len(items) >= 4, 'README paragraph structure incomplete')
    require(items[0] == EXPECTED_TITLE, 'README title drift')
    require(items[1] == normalize(EXPECTED_INTRO), 'README current accounting paragraph drift')
    require(OBLIGATION_TOKEN.findall(items[1]) == ['obligations'], 'README canonical obligation claim drift')
    require(
        all(OBLIGATION_TOKEN.search(item) is None for index, item in enumerate(items) if index != 1),
        'README obligation claim must occur only in canonical intro',
    )
    require(items[2] == EXPECTED_LOCAL_HEADING, 'README current accounting slot drift')
    evidence_indexes = [index for index, item in enumerate(items) if item == EXPECTED_EVIDENCE_HEADING]
    require(len(evidence_indexes) == 1, 'README evidence heading missing/duplicated')
    evidence_index = evidence_indexes[0]
    require(evidence_index > 0, 'README evidence heading position invalid')
    require(items[evidence_index - 1] == normalize(EXPECTED_REVIEW_CLOSEOUT), 'README historical review closeout drift')
    require(items[-1] == normalize(EXPECTED_DURABILITY_CLOSEOUT), 'README workflow durability closeout drift')
    for expected, label in (
        (EXPECTED_INTRO, 'current accounting'),
        (EXPECTED_REVIEW_CLOSEOUT, 'historical review closeout'),
        (EXPECTED_DURABILITY_CLOSEOUT, 'workflow durability closeout'),
    ):
        require(items.count(normalize(expected)) == 1, f'README {label} paragraph missing/duplicated')
    compact = normalize(text)
    for marker in STALE_MARKERS:
        require(normalize(marker) not in compact, f'README stale marker present: {marker}')
    return {
        'result': 'README_CURRENT_STATE_VALIDATED_NOT_PRODUCT_PASS',
        'direct_paths': 308,
        'grouped_paths': 113,
        'unverified_paths': 3940,
        'semantically_classified_paths': 421,
        'remaining_bounded_proof_workflows': [],
        'product_readiness_claimed': False,
        'audit_completion_claimed': False,
    }


def validate_terminal_workflow_state(root: Path = ROOT) -> list[str]:
    workflow_dir = root / WORKFLOW_DIR
    require(workflow_dir.is_dir() and not workflow_dir.is_symlink(), 'workflow directory missing or not a regular directory')
    retired = root / RETIRED_R7_WORKFLOW
    require(not retired.exists() and not retired.is_symlink(), 'retired R7 qualification workflow still present')
    remaining = sorted(path.name for path in workflow_dir.glob('organization-audit-*.yml'))
    require(not remaining, f'bounded audit-proof workflow still present: {remaining}')
    return remaining


def validate(text: str, root: Path = ROOT) -> dict[str, object]:
    result = validate_text(text)
    remaining = validate_terminal_workflow_state(root)
    require(result['remaining_bounded_proof_workflows'] == remaining, 'README terminal workflow record drift')
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--readme', type=Path, default=Path('docs/evidence/organization-audit-20260907/README.md'))
    args = parser.parse_args()
    require(args.readme.is_file(), 'README missing')
    readme_bytes = args.readme.read_bytes()
    try:
        readme_text = readme_bytes.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise ValueError('README is not valid UTF-8') from exc
    result = validate(readme_text)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
