#!/usr/bin/env python3
"""Verify R3 artifact identities and scoped native results offline; never qualify production."""
from __future__ import annotations
import argparse
from collections import Counter
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


def verify(manifest_path, archive_dir):
    manifest = json_bytes(manifest_path.read_bytes()); require(manifest['schema_version'] == 1, 'manifest version')
    require(manifest['provider_source_sha'] == 'de917b3477a1de0667531380de3660e8b2ab59aa', 'wrong provider source')
    require(manifest['provider_tree_sha'] == 'ffdf2a286d3a39f2344cf2ff53b28e4ef7369a8e', 'wrong provider tree')
    all_files = {}
    for item in manifest['artifacts']:
        require(Path(item['filename']).name == item['filename'] and '\\' not in item['filename'], 'unsafe artifact filename')
        require(re.fullmatch('[0-9a-f]{64}', item['zip_sha256']) is not None, 'invalid artifact SHA256')
        require(item['name'] not in all_files, 'duplicate artifact name')
        files = archive_files(archive_dir / item['filename'], item['zip_sha256'])
        for name, checksum in item['evidence_files'].items():
            require(name in files and digest(files[name]) == checksum, 'bound evidence file mismatch: ' + name)
        all_files[item['name']] = files
    php, gateway, concurrency, ui = (all_files[n] for n in ['php', 'gateway', 'concurrency', 'public_ui'])
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
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True); parser.add_argument('--archive-dir', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.manifest, args.archive_dir), indent=2))


if __name__ == '__main__': main()
