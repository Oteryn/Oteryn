import copy
import unittest
from collect_ci_cohort import elapsed, select_runs, job_metrics, ReadOnlyAPI, PLAN, collect


def run(n=1, **kw):
    result = {'id': n, 'head_sha': 'a' * 40, 'path': '.github/workflows/ci.yml', 'status': 'completed', 'event': 'pull_request',
              'conclusion': 'success', 'run_attempt': 1, 'created_at': '2026-09-08T00:00:00Z', 'run_started_at': '2026-09-08T00:00:02Z', 'updated_at': '2026-09-08T00:01:00Z'}
    return dict(result, **kw)


def job(**kw):
    return dict({'id': 2, 'run_id': 1, 'run_attempt': 1, 'name': 'test', 'status': 'completed', 'conclusion': 'success',
                 'started_at': '2026-09-08T00:00:10Z', 'completed_at': '2026-09-08T00:00:40Z'}, **kw)


class Tests(unittest.TestCase):
    def test_intervals_are_not_confused(self):
        j = job_metrics(job(), run()); self.assertEqual(j['execution_seconds'], 30); self.assertEqual(j['start_delay_from_run_creation_seconds'], 10)

    def test_missing_is_not_zero(self):
        self.assertIsNone(job_metrics(job(started_at=None, completed_at=None, conclusion='skipped'), run())['execution_seconds'])

    def test_wrong_time_order(self):
        with self.assertRaises(ValueError): elapsed('2026-09-08T00:01:00Z', '2026-09-08T00:00:00Z')

    def test_timezone_required(self):
        with self.assertRaises(ValueError): elapsed('2026-09-08T00:00:00', '2026-09-08T00:01:00')

    def test_latest_completed_only(self):
        rows = [run(1), run(2, status='in_progress'), run(3, event='workflow_dispatch'), run(4, path='.github/workflows/other.yml')]
        self.assertEqual([r['id'] for r in select_runs(rows, 'ci.yml')], [1])

    def test_failure_not_filtered_to_success(self):
        self.assertEqual(select_runs([run(conclusion='failure')], 'ci.yml')[0]['conclusion'], 'failure')

    def test_closed_sample_budget(self):
        self.assertEqual(len(select_runs([run(n) for n in range(1, 30)], 'ci.yml')), 12)
        for value in [0, 13, True]:
            with self.assertRaises(ValueError): select_runs([], 'ci.yml', value)

    def test_duplicate_run(self):
        with self.assertRaises(ValueError): select_runs([run(), run()], 'ci.yml')

    def test_bad_run_sha(self):
        with self.assertRaises(ValueError): select_runs([run(head_sha='main')], 'ci.yml')

    def test_wrong_run_or_attempt(self):
        for changes in [{'run_id': 3}, {'run_attempt': 2}, {'status': 'in_progress'}]:
            with self.assertRaises(ValueError): job_metrics(job(**changes), run())

    def test_credentials_required_without_network(self):
        with self.assertRaises(ValueError): ReadOnlyAPI(None)

    def test_admin_and_foreign_endpoints_denied_before_network(self):
        api = ReadOnlyAPI('test-only')
        for repo, suffix in [('foreign/repo', '/git/ref/heads/main'), ('Oteryn/Oteryn', '/secrets'), ('Oteryn/Oteryn', '/actions/runs/2/cancel'), ('Oteryn/Oteryn', '/../../orgs')]:
            with self.assertRaises(ValueError): api.get(repo, suffix)
        self.assertEqual(api.count, 0)

    def test_sanitized_collection_is_explicitly_incomplete_when_fewer_runs_exist(self):
        class Fake:
            count = 0
            def get(self, repo, suffix):
                self.count += 1
                if suffix.startswith('/git/'): return {'object': {'sha': 'a' * 40}}
                if '/workflows/' in suffix: return {'workflow_runs': []}
                raise AssertionError('unexpected endpoint')
        result = collect(Fake())
        self.assertEqual(result['runs'], []); self.assertEqual(len(result['strata']), 7)
        self.assertEqual(result['pricing'], 'NOT_MEASURED'); self.assertEqual(result['unique_event_candidates'], 0)

    def test_all_plan_coordinates_are_closed(self):
        self.assertEqual(len(PLAN), 4); self.assertEqual(sum(map(len, PLAN.values())), 7)


if __name__ == '__main__': unittest.main()
