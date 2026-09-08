#!/usr/bin/env python3
"""Read-only bounded GitHub CI timing sample; no logs, billing or runner identities.

The newest 12 completed runs per named workflow are an opportunistic, path-stratified
sample, not a random organization census. Job time is latest-attempt execution time,
not billed time. Start delay includes dependency/setup waiting and is not queue time.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import threading
from urllib.error import HTTPError
from urllib.request import Request, build_opener, HTTPRedirectHandler

PLAN = {
    'Oteryn/Oteryn': ['ci.yml'],
    'Oteryn/Oteryn-Platform': ['ci.yml'],
    'Oteryn/Oteryn-Game': ['merge-gate.yml', 'merge-group-gate.yml', 'rust.yml'],
    'Oteryn/Oteryn-Atlas': ['merge-group-gate.yml', 'merge-authority-audit.yml'],
}
SHA = re.compile(r'[0-9a-f]{40}\Z')
EVENTS = {'pull_request', 'pull_request_target', 'merge_group', 'push'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def timestamp(value):
    require(isinstance(value, str), 'missing timestamp')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(parsed.tzinfo is not None, 'timezone required')
    return parsed


def elapsed(start, finish):
    if start is None or finish is None:
        return None
    seconds = (timestamp(finish) - timestamp(start)).total_seconds()
    require(seconds >= 0, 'negative interval')
    return seconds


def measured_interval(start, finish, label, anomalies):
    try:
        value = elapsed(start, finish)
        if value is None:
            anomalies.append(label + ': missing timestamp')
        return value
    except (ValueError, TypeError) as exc:
        anomalies.append(label + ': ' + str(exc)[:160])
        return None


def select_runs(rows, workflow, limit=12):
    require(type(limit) is int and 1 <= limit <= 12, 'sample limit')
    selected, seen = [], set()
    for row in sorted(rows, key=lambda r: (r['created_at'], r['id']), reverse=True):
        if row['status'] != 'completed' or row['event'] not in EVENTS:
            continue
        if row['path'] != '.github/workflows/' + workflow:
            continue
        require(type(row['id']) is int and row['id'] > 0 and SHA.fullmatch(row['head_sha']), 'invalid run identity')
        require(row['id'] not in seen, 'duplicate run id')
        seen.add(row['id'])
        selected.append({key: row.get(key) for key in ('id', 'head_sha', 'path', 'event', 'status', 'conclusion', 'run_attempt', 'created_at', 'run_started_at', 'updated_at')})
        if len(selected) == limit:
            break
    return selected


def job_metrics(job, run):
    require(type(job['id']) is int and job['id'] > 0 and job['run_id'] == run['id'], 'job/run identity mismatch')
    require(job['status'] == 'completed', 'nonterminal job in completed sample')
    if job.get('run_attempt') is not None:
        require(job['run_attempt'] == run['run_attempt'], 'job attempt mismatch')
    start, finish = job.get('started_at'), job.get('completed_at')
    anomalies = []
    duration = measured_interval(start, finish, 'execution', anomalies)
    delay = measured_interval(run['created_at'], start, 'start delay', anomalies)
    return {'id': job['id'], 'name': job['name'], 'conclusion': job.get('conclusion'),
            'started_at': start, 'completed_at': finish, 'execution_seconds': duration,
            'start_delay_from_run_creation_seconds': delay, 'timestamp_anomalies': anomalies}


def prepare_output_parent(path: Path) -> Path:
    """Create only lexical, non-symlink output ancestry and return an absolute path.

    The nearest existing ancestor and every created directory must resolve to the
    same lexical path. This rejects both direct ancestor symlinks and deeper
    paths that are already underneath a symlinked ancestor before any evidence
    file is created.
    """
    absolute = Path(os.path.abspath(path))
    parent = absolute.parent
    cursor = parent
    missing = []
    while not os.path.lexists(cursor):
        missing.append(cursor)
        require(cursor.parent != cursor, 'output parent resolution failed')
        cursor = cursor.parent
    require(not cursor.is_symlink(), 'output ancestor symlink refused')
    require(cursor.resolve(strict=True) == cursor, 'output ancestor symlink refused')
    for directory in reversed(missing):
        directory.mkdir()
        require(not directory.is_symlink(), 'output ancestor symlink refused')
        require(directory.resolve(strict=True) == directory, 'output ancestor symlink refused')
    require(parent.resolve(strict=True) == parent, 'output ancestor symlink refused')
    return absolute


def write_new(path: Path, raw: bytes) -> None:
    """Create one evidence file exclusively; never overwrite or follow symlinks."""
    path = prepare_output_parent(path)
    if path.is_symlink():
        raise FileExistsError(str(path))
    with path.open('xb') as handle:
        handle.write(raw)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('redirect refused; credential may not leave the exact API endpoint')


class ReadOnlyAPI:
    def __init__(self, token):
        require(bool(token), 'ephemeral read token required')
        self.token, self.count, self.lock = token, 0, threading.Lock()

    def get(self, repository, suffix):
        require(repository in PLAN and suffix.startswith('/') and '..' not in PurePosixPath(suffix).parts, 'endpoint scope')
        require(re.fullmatch(r'/git/ref/heads/main|/actions/workflows/[a-z-]+\.yml/runs\?per_page=100&page=[12]|/actions/runs/[0-9]+/attempts/[1-9][0-9]*/jobs\?per_page=100&page=[12]', suffix), 'endpoint not allowlisted')
        with self.lock:
            self.count += 1
            require(self.count <= 200, 'bounded API budget exceeded')
        request = Request('https://api.github.com/repos/' + repository + suffix,
                          headers={'Authorization': 'Bearer ' + self.token, 'Accept': 'application/vnd.github+json', 'User-Agent': 'Oteryn-audit-185-read-only'}, method='GET')
        try:
            with build_opener(NoRedirect()).open(request, timeout=25) as response:
                raw = response.read(8_000_001)
                require(len(raw) <= 8_000_000, 'response too large')
                return json.loads(raw)
        except HTTPError as exc:
            raise ValueError(f'GitHub HTTP {exc.code} for bounded metadata endpoint') from None


def collect(api):
    rows, collection = [], {'main_reads': {}, 'strata': []}
    for repository, workflows in PLAN.items():
        sha = api.get(repository, '/git/ref/heads/main')['object']['sha']
        require(SHA.fullmatch(sha), 'invalid main identity')
        collection['main_reads'][repository] = sha
        for workflow in workflows:
            raw, pages = [], 0
            for page in (1, 2):
                response = api.get(repository, f'/actions/workflows/{workflow}/runs?per_page=100&page={page}')
                raw.extend(response['workflow_runs']); pages += 1
                if len(select_runs(raw, workflow)) >= 12 or len(response['workflow_runs']) < 100:
                    break
            selected = select_runs(raw, workflow)
            collection['strata'].append({'repository': repository, 'workflow': workflow, 'pages_read': pages, 'requested': 12, 'selected': len(selected)})
            rows.extend(dict(r, repository=repository) for r in selected)

    def attach(run):
        require(type(run['run_attempt']) is int and run['run_attempt'] > 0, 'run attempt required')
        jobs, total = [], None
        for page in (1, 2):
            data = api.get(run['repository'], f"/actions/runs/{run['id']}/attempts/{run['run_attempt']}/jobs?per_page=100&page={page}")
            if total is None:
                total = data['total_count']
            require(total == data['total_count'], 'job total changed during acquisition')
            jobs.extend(data['jobs'])
            if len(jobs) >= total:
                break
        require(len(jobs) == total and len({j['id'] for j in jobs}) == len(jobs), 'incomplete/duplicate job pagination')
        result = dict(run, jobs=[job_metrics(job, run) for job in jobs])
        times = [j['execution_seconds'] for j in result['jobs']]
        result['latest_attempt_job_seconds'] = sum(times) if all(t is not None for t in times) else None
        result['observed_job_seconds'] = sum(t for t in times if t is not None)
        result['jobs_with_missing_times'] = sum(t is None for t in times)
        completions = [j['completed_at'] for j in result['jobs'] if j['completed_at'] is not None]
        result['timestamp_anomalies'] = []
        result['wall_from_run_creation_seconds'] = measured_interval(run['created_at'], max(completions) if completions else None, 'wall', result['timestamp_anomalies'])
        return result

    with ThreadPoolExecutor(max_workers=4) as pool:
        completed = list(pool.map(attach, rows))
    collection.update(schema_version=1, collected_at_utc=datetime.now(timezone.utc).isoformat(),
                      method='Newest 12 completed PR/PR-target/MQ/push runs per seven named workflow strata; at most two listing/job pages; latest attempt only.',
                      sampling_bias='Opportunistic workflow-stratified sample; not random, not complete organization spend and not all runs of each candidate.',
                      pricing='NOT_MEASURED', cache_yield='NOT_MEASURED', pure_queue_time='NOT_MEASURED',
                      prior_attempt_cost='NOT_MEASURED', token_cost='NOT_MEASURED',
                      api_calls=api.count, runs=completed,
                      unique_event_candidates=len({(r['repository'], r['event'], r['head_sha']) for r in completed}),
                      qualification='TIMING_METADATA_ONLY_NOT_PRODUCT_PASS')
    return collection


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(os.environ.get('OTERYN_AUDIT185_CI_COHORT') == '1', 'explicit bounded metadata collection consent required')
    output = prepare_output_parent(args.output)
    require(not os.path.lexists(output), 'refusing output overwrite')
    try:
        result = collect(ReadOnlyAPI(os.environ.get('GH_TOKEN')))
    except Exception as exc:
        diagnostic = {'collection_failed': True, 'error_type': type(exc).__name__, 'message': str(exc)[:300], 'qualification': 'NO_COMPLETE_COHORT'}
        diagnostic_path = output.parent / 'collection-error.json'
        try:
            write_new(diagnostic_path, (json.dumps(diagnostic, indent=2) + '\n').encode())
        except FileExistsError:
            raise RuntimeError('collection failed; existing collection-error.json preserved without overwrite') from exc
        raise
    raw = (json.dumps(result, indent=2) + '\n').encode()
    write_new(output, raw)
    print(json.dumps({'runs': len(result['runs']), 'unique_event_candidates': result['unique_event_candidates'], 'api_calls': result['api_calls'], 'sha256': hashlib.sha256(raw).hexdigest()}))


if __name__ == '__main__':
    main()
