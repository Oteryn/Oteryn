#!/usr/bin/env python3
"""Fail-closed revalidation for the Platform app/GameAuth historical direct-read candidate.

Read-only. This tool proves exact historical evidence identity, byte-identical source carry-forward,
and frozen-current dependent contract identity. It does not by itself adopt GROUPED coverage; focused
current tests are a separate required qualification step.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

CANDIDATE = Path('docs/evidence/organization-audit-20260907/r3-platform-gameauth-candidate.json')


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
        ['git', '-C', str(root), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
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


def verify(audit_root: Path, platform_root: Path, evidence_root: Path):
    candidate = read_json(audit_root / CANDIDATE)
    require(candidate.get('schema_version') == 1, 'candidate schema')
    require(candidate.get('state') == 'CANDIDATE_PENDING_QUALIFICATION', 'candidate state')
    require(candidate.get('coverage_adopted') is False, 'candidate must not already claim adoption')
    require(candidate.get('repository') == 'Oteryn/Oteryn-Platform', 'candidate repository')
    require(candidate.get('path_prefix') == 'app/GameAuth/', 'candidate prefix')
    require(type(candidate.get('expected_count')) is int and candidate['expected_count'] == 27, 'candidate count')

    hist = candidate['historical_evidence']
    current = candidate['current_revalidation']

    require(text(platform_root, 'rev-parse', 'HEAD') == current['source_commit'], 'wrong frozen Platform source')
    require(text(platform_root, 'rev-parse', 'HEAD^{tree}') == current['source_tree'], 'wrong frozen Platform tree')
    require(text(evidence_root, 'rev-parse', 'HEAD') == hist['publication_commit'], 'wrong Platform audit publication commit')
    require(text(evidence_root, 'rev-parse', 'HEAD^{tree}') == hist['publication_tree'], 'wrong Platform audit publication tree')
    require(text(platform_root, 'rev-parse', hist['audited_main_sha'] + '^{tree}') == hist['audited_main_tree'], 'wrong historical Platform source tree')

    evidence_path = evidence_root / hist['coverage_rules_path']
    require(evidence_path.is_file() and not evidence_path.is_symlink(), 'historical evidence path invalid')
    evidence_raw = evidence_path.read_bytes()
    require(blob_sha(evidence_raw) == hist['coverage_rules_blob'], 'historical evidence blob mismatch')
    statement = hist['exact_statement']
    require(evidence_raw.decode('utf-8').count(statement) == 1, 'historical all-27 direct-read statement missing/duplicated')
    require(hist['pattern'] == candidate['path_prefix'] + '**' and hist['count'] == candidate['expected_count'], 'historical scope mismatch')

    historical_app = text(platform_root, 'rev-parse', hist['audited_main_sha'] + ':app')
    current_app = text(platform_root, 'rev-parse', current['source_commit'] + ':app')
    require(historical_app == current['historical_app_tree'], 'historical app tree mismatch')
    require(current_app == current['current_app_tree'], 'current app tree mismatch')
    require(historical_app == current_app, 'app tree changed across carry-forward interval')

    historical_group_tree = text(platform_root, 'rev-parse', hist['audited_main_sha'] + ':app/GameAuth')
    current_group_tree = text(platform_root, 'rev-parse', current['source_commit'] + ':app/GameAuth')
    require(current_group_tree == current['gameauth_tree'], 'current GameAuth tree mismatch')
    require(historical_group_tree == current_group_tree, 'GameAuth tree changed across carry-forward interval')

    old = recursive_entries(platform_root, hist['audited_main_sha'], candidate['path_prefix'])
    now = recursive_entries(platform_root, current['source_commit'], candidate['path_prefix'])
    require(len(old) == len(now) == candidate['expected_count'], 'GameAuth leaf count mismatch')
    require(old == now, 'GameAuth path/blob identity changed')
    require(all(mode == '100644' and kind == 'blob' for _, mode, kind, _ in now), 'GameAuth group contains non-regular leaf')

    changed = git(
        platform_root,
        'diff', '--name-only', hist['audited_main_sha'], current['source_commit'], '--', candidate['path_prefix'],
    ).decode().splitlines()
    require(changed == [], 'GameAuth diff not empty: ' + repr(changed[:10]))
    require(current.get('changed_paths_under_group_prefix') == 0, 'candidate changed-path declaration')

    for path, expected in current['current_blobs'].items():
        actual = text(platform_root, 'rev-parse', current['source_commit'] + ':' + path)
        require(actual == expected, 'frozen-current dependent blob mismatch: ' + path)

    tests = current.get('focused_test_files')
    require(isinstance(tests, list) and len(tests) == len(set(tests)) == 14, 'focused test set must contain 14 unique paths')
    for path in tests:
        require(text(platform_root, 'rev-parse', current['source_commit'] + ':' + path), 'focused test missing: ' + path)

    return {
        'result': 'GAMEAUTH_IDENTITY_AND_HISTORICAL_DIRECT_EVIDENCE_REVALIDATED_TESTS_STILL_REQUIRED',
        'candidate_id': candidate['candidate_id'],
        'historical_source': hist['audited_main_sha'],
        'current_source': current['source_commit'],
        'paths': len(now),
        'path_blob_identity': True,
        'historical_direct_read_statement_bound': True,
        'dependent_blobs_verified': len(current['current_blobs']),
        'focused_test_files_bound': len(tests),
        'coverage_adopted': False,
        'next_gate': 'focused frozen-current tests must pass before GROUPED adoption',
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit-root', type=Path, required=True)
    parser.add_argument('--platform-root', type=Path, required=True)
    parser.add_argument('--evidence-root', type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.audit_root.resolve(), args.platform_root.resolve(), args.evidence_root.resolve())
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
