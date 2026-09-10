#!/usr/bin/env python3
"""Verify R3 artifact identities and scoped native results offline; never qualify production."""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import statistics
import subprocess
import re
import xml.etree.ElementTree as ET
import zipfile
from collect_ci_cohort import PLAN, measured_interval


SOURCE_SHA = 'de917b3477a1de0667531380de3660e8b2ab59aa'
SOURCE_TREE = 'ffdf2a286d3a39f2344cf2ff53b28e4ef7369a8e'
LEGACY_ROUTES = [
    '/', '/news', '/news/welcome-to-oteryn', '/wiki', '/download', '/login',
    '/register', '/forgot-password', '/recovery-key', '/events', '/support', '/legal/privacy',
]
LEGACY_SIZES = [(390, 844), (820, 1180), (1440, 1000), (1920, 1080)]
LEGACY_FAILED_ROUTES = {'/support', '/legal/privacy'}
LEGACY_CRITERIA = {'http_ok', 'main', 'heading', 'language', 'title', 'no_overflow', 'labels', 'images', 'unique_ids'}
MIGRATION_LINE = re.compile(
    r'^\s{2}([0-9]{4}_[0-9]{2}_[0-9]{2}_[0-9]{6}_[A-Za-z0-9_]+)\s+.*?([0-9]+(?:\.[0-9]+)?)ms\s+DONE\s*$'
)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def json_bytes(raw):
    def pairs(items):
        out = {}
        for key, value in items:
            require(key not in out, 'duplicate JSON key')
            out[key] = value
        return out
    return json.loads(raw, object_pairs_hook=pairs)


def archive_files(file, expected_sha):
    raw = file.read_bytes()
    require(digest(raw) == expected_sha, 'artifact ZIP hash mismatch: ' + file.name)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = archive.infolist()
        names = [e.filename for e in entries]
        require(len(names) == len(set(names)), 'duplicate ZIP path')
        require(sum(e.file_size for e in entries) <= 32_000_000, 'ZIP expanded byte limit')
        require(all(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts and '\\' not in n for n in names), 'unsafe ZIP member')
        files = {e.filename: archive.read(e) for e in entries if not e.is_dir()}
    for name, body in files.items():
        if PurePosixPath(name).name != 'SHA256SUMS.json':
            continue
        parent = PurePosixPath(name).parent
        for member, checksum in json_bytes(body).items():
            path = str(parent / member)
            require(path in files and digest(files[path]) == checksum, 'internal artifact hash mismatch')
    return files


def junit(raw):
    require(b'<!DOCTYPE' not in raw.upper() and b'<!ENTITY' not in raw.upper(), 'XML entities forbidden')
    root = ET.fromstring(raw)
    if root.tag == 'testsuites':
        require(len(root) == 1 and root[0].tag == 'testsuite', 'one aggregate JUnit suite required')
    top = root[0] if root.tag == 'testsuites' else root
    require(top is not None and top.tag == 'testsuite', 'missing JUnit suite')
    cases = list(top.iter('testcase'))
    names = [(c.get('classname'), c.get('name')) for c in cases]
    require(all(all(n) for n in names) and len(names) == len(set(names)), 'duplicate/missing JUnit identity')
    counts = {'tests': len(cases), 'assertions': sum(int(c.get('assertions', '0')) for c in cases),
              'errors': sum(c.find('error') is not None for c in cases),
              'failures': sum(c.find('failure') is not None for c in cases),
              'skipped': sum(c.find('skipped') is not None for c in cases)}
    for key, actual in counts.items():
        require(int(top.get(key, '-1')) == actual, 'JUnit declared/observed mismatch: ' + key)
    require(counts['tests'] > 0 and counts['assertions'] >= 0, 'empty/negative JUnit results')
    require(all(sum(c.find(k) is not None for k in ['error', 'failure', 'skipped']) <= 1 for c in cases), 'contradictory JUnit outcomes')
    require(all(int(c.get('assertions', '0')) >= 0 for c in cases), 'negative per-test assertions')
    counts['executed'] = counts['tests'] - counts['skipped']
    return counts, set(names), {name for name, case in zip(names, cases) if case.find('skipped') is not None}


def go_results(raw):
    events = [json_bytes(line) for line in raw.splitlines() if line.strip()]
    terminal = [e for e in events if e.get('Test') and e.get('Action') in {'pass', 'fail', 'skip'}]
    identities = [(e['Package'], e['Test']) for e in terminal]
    require(len(identities) == len(set(identities)), 'duplicate Go terminal event')
    require(all(e['Action'] == 'pass' for e in terminal), 'Go test failed/skipped')
    started = [(e['Package'], e['Test']) for e in events if e.get('Test') and e['Action'] == 'run']
    require(len(started) == len(set(started)), 'duplicate Go start event')
    starts = set(started)
    require(starts == set(identities) and starts, 'incomplete Go test event stream')
    require(not any(e.get('Action') in {'fail', 'skip'} for e in events), 'Go stream includes failure/skip')
    package_starts_list = [(e['Package'], i) for i, e in enumerate(events) if e['Action'] == 'start' and not e.get('Test')]
    package_finishes_list = [(e['Package'], i) for i, e in enumerate(events) if e['Action'] == 'pass' and not e.get('Test')]
    package_starts, package_finishes = dict(package_starts_list), dict(package_finishes_list)
    require(len(package_starts) == len(package_starts_list) and len(package_finishes) == len(package_finishes_list), 'duplicate Go package event')
    require(package_starts.keys() == package_finishes.keys() and package_starts, 'incomplete/failed Go package stream')
    run_positions = {(e['Package'], e['Test']): i for i, e in enumerate(events) if e.get('Test') and e['Action'] == 'run'}
    end_positions = {(e['Package'], e['Test']): i for i, e in enumerate(events) if e.get('Test') and e['Action'] == 'pass'}
    for identity in identities:
        package = identity[0]
        require(package in package_starts, 'unowned Go test package')
        require(package_starts[package] < run_positions[identity] < end_positions[identity] < package_finishes[package], 'Go event order mismatch')
    return {'passed_test_events': len(terminal), 'top_level': sum('/' not in e['Test'] for e in terminal),
            'nested': sum('/' in e['Test'] for e in terminal), 'packages_passed': len(package_finishes), 'failures': 0, 'skips': 0}


def go_coverage(raw):
    lines = raw.decode().splitlines(); require(lines[0].startswith('mode:'), 'Go coverage header')
    covered = total = 0
    seen = set()
    for line in lines[1:]:
        block, statements, count = line.rsplit(' ', 2)
        require(block not in seen, 'duplicate Go coverage block'); seen.add(block)
        n, hits = int(statements), int(count)
        require(n >= 0 and hits >= 0, 'negative coverage')
        total += n; covered += n if hits > 0 else 0
    require(total > 0, 'empty Go coverage')
    return {'statements': total, 'covered_statements': covered, 'percent': round(100 * covered / total, 2)}


def ci_summary(data):
    require(data['qualification'] == 'TIMING_METADATA_ONLY_NOT_PRODUCT_PASS', 'wrong CI metadata scope')
    require({(r['repository'], r['workflow']) for r in data['strata']} == {(repo, workflow) for repo, workflows in PLAN.items() for workflow in workflows} and len(data['strata']) == 7, 'CI stratum scope changed')
    runs = data['runs']; require(len({(r['repository'], r['id']) for r in runs}) == len(runs), 'duplicate CI run')
    summary = {'runs': len(runs), 'jobs': sum(len(r['jobs']) for r in runs),
               'unique_event_candidates': len({(r['repository'], r['event'], r['head_sha']) for r in runs}),
               'run_conclusions': dict(Counter(r['conclusion'] for r in runs)), 'strata': [], 'anomalies': []}
    require(summary['unique_event_candidates'] == data['unique_event_candidates'], 'CI candidate count mismatch')
    for r in runs:
        require(r['repository'] in PLAN and r['path'] in {'.github/workflows/' + w for w in PLAN[r['repository']]}, 'unplanned CI workflow')
        require(len({j['id'] for j in r['jobs']}) == len(r['jobs']), 'duplicate CI job')
        times = []
        for j in r['jobs']:
            anomalies = []
            duration = measured_interval(j['started_at'], j['completed_at'], 'execution', anomalies)
            delay = measured_interval(r['created_at'], j['started_at'], 'start delay', anomalies)
            require(j['execution_seconds'] == duration and j['start_delay_from_run_creation_seconds'] == delay and j['timestamp_anomalies'] == anomalies, 'CI job derived data mismatch')
            times.append(duration)
            if j['timestamp_anomalies']:
                summary['anomalies'].append({'repository': r['repository'], 'run': r['id'], 'job': j['id'], 'conclusion': j['conclusion'], 'started_at': j['started_at'], 'completed_at': j['completed_at'], 'anomalies': j['timestamp_anomalies']})
        observed = sum(t for t in times if t is not None)
        complete = sum(times) if all(t is not None for t in times) else None
        require(r['observed_job_seconds'] == observed and r['latest_attempt_job_seconds'] == complete and r['jobs_with_missing_times'] == sum(t is None for t in times), 'CI run derived total mismatch')
        completions = [j['completed_at'] for j in r['jobs'] if j['completed_at'] is not None]
        anomalies = []
        wall = measured_interval(r['created_at'], max(completions) if completions else None, 'wall', anomalies)
        require(r['wall_from_run_creation_seconds'] == wall and r['timestamp_anomalies'] == anomalies, 'CI wall derived data mismatch')
    for s in data['strata']:
        group = [r for r in runs if r['repository'] == s['repository'] and r['path'] == '.github/workflows/' + s['workflow']]
        require(len(group) == s['selected'], 'CI stratum mismatch')
        jobs = [j for r in group for j in r['jobs']]
        walls = [r['wall_from_run_creation_seconds'] for r in group if r['wall_from_run_creation_seconds'] is not None]
        summary['strata'].append({'repository': s['repository'], 'workflow': s['workflow'], 'runs': len(group), 'jobs': len(jobs),
             'run_conclusions': dict(Counter(r['conclusion'] for r in group)),
             'observed_job_seconds': sum(j['execution_seconds'] for j in jobs if j['execution_seconds'] is not None),
             'job_time_unknown': sum(j['execution_seconds'] is None for j in jobs),
             'skipped_jobs': sum(j['conclusion'] == 'skipped' for j in jobs),
             'wall_observations': len(walls), 'median_wall_seconds': statistics.median(walls) if walls else None})
    summary['limitations'] = 'Newest 12 completed runs per selected workflow; opportunistic, not random. Latest attempt only. Unknown times are not zero. Delays include dependencies. Not all candidate workflows, billed usage, monetary cost, pure queue time, cache yield, token cost or product pass.'
    return summary


def legacy_failure_signature(raw, source_sha):
    """Validate the original captured failure exactly, without trusting its recorded green/failed summary."""
    report = json_bytes(raw)
    require(report.get('source_sha') == source_sha, 'wrong original UI source')
    require(report.get('playwright') == '1.62.1' and isinstance(report.get('browser'), str) and report['browser'], 'wrong original UI toolchain')
    cases = report.get('cases')
    require(isinstance(cases, list) and len(cases) == 48, 'original UI matrix incomplete')
    expected_matrix = {(route, width, height) for width, height in LEGACY_SIZES for route in LEGACY_ROUTES}
    actual_matrix = {(r.get('route'), r.get('width'), r.get('height')) for r in cases}
    require(len(actual_matrix) == 48 and actual_matrix == expected_matrix, 'original UI matrix identity mismatch')
    expected_failed = {(route, width, 'http_ok') for width, _ in LEGACY_SIZES for route in LEGACY_FAILED_ROUTES}
    stored_failed = report.get('failed_criteria')
    require(isinstance(stored_failed, list), 'original UI failed_criteria missing')
    actual_failed = {(r.get('route'), r.get('width'), r.get('criterion')) for r in stored_failed}
    require(len(stored_failed) == 8 and len(actual_failed) == 8 and actual_failed == expected_failed, 'original UI failure signature mismatch')
    for row in cases:
        criteria = row.get('criteria')
        require(isinstance(criteria, dict) and set(criteria) == LEGACY_CRITERIA, 'original UI criterion shape changed')
        false_keys = {k for k, value in criteria.items() if value is not True}
        if row['route'] in LEGACY_FAILED_ROUTES:
            require(row.get('status') == 404 and false_keys == {'http_ok'}, 'original editorial failure mismatch')
        else:
            require(row.get('status') == 200 and not false_keys, 'unexpected original UI failure')
        require(not row.get('error') and row.get('observed_errors') == [], 'original UI browser error present')
    no_js = report.get('no_javascript')
    require(no_js == {'route': '/login', 'status': 200, 'email_visible': True, 'password_visible': True}, 'original no-JS control mismatch')
    return {'failed_criteria': 8, 'mode': 'PARSED_ORIGINAL_CAPTURE_NOT_NEW_BROWSER_EXECUTION'}


def migration_execution(log_raw, migration_review_raw, coverage_review_raw, manifest):
    """Bind the successful synthetic up log to the exact 50 source paths/blobs."""
    review = json_bytes(migration_review_raw)
    require(review.get('schema_version') == 1 and review.get('repository') == 'Oteryn/Oteryn-Platform', 'migration review identity')
    require(review.get('source_sha') == manifest['provider_source_sha'], 'migration source mismatch')
    require(review.get('execution_log_sha256') == digest(log_raw), 'migration log digest mismatch')
    public_ui = next((item for item in manifest['artifacts'] if item.get('name') == 'public_ui'), None)
    require(public_ui is not None and review.get('execution_artifact_id') == public_ui.get('artifact_id'), 'migration artifact binding mismatch')
    path_set = review.get('path_set')
    require(isinstance(path_set, dict) and path_set.get('ledger') == 'coverage-review.tsv', 'migration ledger binding')
    text = coverage_review_raw.decode('utf-8')
    rows = list(csv.DictReader(io.StringIO(text), delimiter='\t'))
    require(rows and set(rows[0]) == {'repository', 'path', 'blob_sha', 'depth', 'scope', 'line_ranges', 'execution_evidence'}, 'coverage ledger columns changed')
    selected = [
        row for row in rows
        if row['repository'] == path_set.get('repository')
        and row['path'].startswith(path_set.get('exact_prefix', ''))
        and row['path'].endswith(path_set.get('exact_suffix', ''))
    ]
    require(len(selected) == review.get('count') == 50, 'migration path count mismatch')
    pairs = sorted((row['path'], row['blob_sha']) for row in selected)
    pair_bytes = ''.join(f'{path}\t{sha}\n' for path, sha in pairs).encode()
    require(digest(pair_bytes) == path_set.get('sha256_of_path_and_blob_tsv'), 'migration path/blob digest mismatch')
    expected_names = {Path(path).stem for path, _ in pairs}
    observed = []
    for line in log_raw.decode('utf-8').splitlines():
        match = MIGRATION_LINE.match(line)
        if match:
            observed.append(match.group(1))
    require(len(observed) == 50 and len(set(observed)) == 50, 'migration execution count/duplicate mismatch')
    require(set(observed) == expected_names, 'migration execution names do not equal the source ledger')
    require(review.get('up_execution') == 'All50 migration names occur in the bound successful log; synthetic SQLite only', 'migration review execution claim changed')
    require(review.get('down_execution') == 'NOT_EXECUTED', 'migration down execution must remain unclaimed')
    return {'migrations': 50, 'mode': 'SYNTHETIC_SQLITE_UP_ONLY'}


def strict_json_equal(left, right):
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(strict_json_equal(left[key], right[key]) for key in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(strict_json_equal(a, b) for a, b in zip(left, right))
    return left == right


def require_committed_results(summary, raw):
    committed = json_bytes(raw)
    require(strict_json_equal(summary, committed), 'recount differs from committed r3-native-results.json')
    return committed


def verify(manifest_path, archive_dir):
    manifest = json_bytes(manifest_path.read_bytes()); require(manifest['schema_version'] == 1, 'manifest version')
    require(manifest['provider_source_sha'] == SOURCE_SHA, 'wrong provider source')
    require(manifest['provider_tree_sha'] == SOURCE_TREE, 'wrong provider tree')
    all_files = {}
    for item in manifest['artifacts']:
        require(Path(item['filename']).name == item['filename'] and '\\' not in item['filename'], 'unsafe artifact filename')
        require(re.fullmatch('[0-9a-f]{64}', item['zip_sha256']) is not None, 'invalid artifact SHA256')
        require(item['name'] not in all_files, 'duplicate artifact name')
        files = archive_files(archive_dir / item['filename'], item['zip_sha256'])
        for name, checksum in item['evidence_files'].items():
            require(name in files and digest(files[name]) == checksum, 'bound evidence file mismatch: ' + name)
        all_files[item['name']] = files
    required_artifacts = {'php', 'gateway', 'concurrency', 'public_ui_original', 'public_ui', 'ci_metadata'}
    require(set(all_files) == required_artifacts, 'artifact set changed')
    php, gateway, concurrency, ui_original, ui = (all_files[n] for n in ['php', 'gateway', 'concurrency', 'public_ui_original', 'public_ui'])

    legacy_failure_signature(ui_original['browser/result.json'], manifest['provider_source_sha'])
    legacy_reassessment = subprocess.run(
        ['node', str(Path(__file__).with_name('verify-public-surface-evidence.mjs')), '--legacy'],
        input=ui_original['browser/result.json'], capture_output=True, timeout=15, check=False)
    require(legacy_reassessment.returncode == 0, 'original browser capture does not pass the explicit legacy replay oracle')
    legacy_check = json_bytes(legacy_reassessment.stdout)
    require(legacy_check.get('verdict') == 'PASS_SCOPED_PUBLIC_FIXTURE'
            and legacy_check.get('mode') == 'REPLAY_OF_CAPTURED_OBSERVATIONS_NOT_NEW_BROWSER_EXECUTION'
            and not legacy_check.get('errors'), 'legacy browser replay mode/signature mismatch')

    evidence_dir = manifest_path.parent
    migration_execution(
        ui['migrations.log'],
        (evidence_dir / 'r3-migration-review.json').read_bytes(),
        (evidence_dir / 'coverage-review.tsv').read_bytes(),
        manifest,
    )

    experiment = json_bytes(php['experiment.json'])
    require(experiment['source_sha'] == manifest['provider_source_sha'] and experiment['baseline_exit'] == 0 and experiment['empty_env_control_exit'] == 0, 'wrong PHP source or nonzero execution')
    baseline, names, skipped = junit(php['no-env.junit.xml'])
    control, control_names, control_skipped = junit(php['empty-env.junit.xml'])
    require((baseline, names, skipped) == (control, control_names, control_skipped), 'empty-env control changed tested identities/results')
    extra, extra_names, extra_skipped = junit(concurrency['junit.xml'])
    require(skipped == extra_names and not extra_skipped and not extra['errors'] and not extra['failures'], 'concurrency run does not close the exact skipped identity set')
    require(not baseline['errors'] and not baseline['failures'], 'PHP errors/failures')
    require(b'<!DOCTYPE' not in php['empty-env.clover.xml'].upper() and b'<!ENTITY' not in php['empty-env.clover.xml'].upper(), 'Clover entities forbidden')
    coverage = ET.fromstring(php['empty-env.clover.xml']).find('project/metrics')
    require(coverage is not None, 'missing Clover project metrics')
    metrics = {k: int(v) for k, v in coverage.attrib.items()}
    require(metrics['statements'] > 0 and 0 <= metrics['coveredstatements'] <= metrics['statements'], 'impossible Clover coverage')
    report = json_bytes(ui['browser/result.json'])
    require(report['schema_version'] == 2 and report['source_sha'] == manifest['provider_source_sha'] and report['source_tree'] == manifest['provider_tree_sha'], 'wrong UI source')
    require(report['assessment']['verdict'] == 'PASS_SCOPED_PUBLIC_FIXTURE' and not report['assessment']['errors'], 'UI capture reported failure')
    require(len(report['cases']) == 48 and len({(r['route'], r['width'], r['height']) for r in report['cases']}) == 48, 'UI matrix incomplete')
    require(all(r['criteria'] and all(v is True for v in r['criteria'].values()) for r in report['cases']), 'UI recorded criterion failure')
    reassessment = subprocess.run(['node', str(Path(__file__).with_name('verify-public-surface-evidence.mjs'))],
                                 input=ui['browser/result.json'], capture_output=True, timeout=15, check=False)
    require(reassessment.returncode == 0, 'raw DOM observation reassessment failed')
    browser_check = json_bytes(reassessment.stdout)
    require(browser_check['verdict'] == 'PASS_SCOPED_PUBLIC_FIXTURE' and not browser_check['errors'], 'UI raw observations fail')
    advisories = json_bytes(php['composer-audit.json'])
    require(advisories['advisories'] == [] and advisories['abandoned'] == [], 'Composer audit contains findings')
    summary = {'schema_version': 1, 'source_sha': manifest['provider_source_sha'], 'php_baseline': baseline, 'php_empty_env_control': control,
         'separate_concurrency': extra, 'distinct_php_identities_across_profiles': len(names | extra_names),
         'php_coverage': metrics, 'php_statement_percent': round(100 * metrics['coveredstatements'] / metrics['statements'], 2),
         'php_branch_coverage': 'NOT_MEASURED', 'composer_advisories_at_execution': 0,
         'gateway': go_results(gateway['tests.jsonl']), 'gateway_coverage': go_coverage(gateway['coverage.out']),
         'ui_reassessment': browser_check, 'ui_cases': len(report['cases']), 'ui_expected_404_cases': sum(r['status'] == 404 for r in report['cases']),
         'ci': ci_summary(json_bytes(all_files['ci_metadata']['cohort.json'])),
         'limitations': 'Across-profile identity closure is not one all-green full integration run. Browser anonymous English fixture only. No production, full accessibility, native Game/Rust, deployment, DR or independent semantic qualification.'}

    require_committed_results(summary, (evidence_dir / 'r3-native-results.json').read_bytes())
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True); parser.add_argument('--archive-dir', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.manifest, args.archive_dir), indent=2))


if __name__ == '__main__': main()
