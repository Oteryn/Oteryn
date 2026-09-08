import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from collect_ci_cohort import PLAN, job_metrics
from verify_r3_evidence import (
    archive_files, digest, json_bytes, junit, go_results, go_coverage, ci_summary,
    legacy_failure_signature, migration_execution, require_committed_results,
)


def xml(extra='', declared=1):
    return f'<testsuites><testsuite tests="{declared}" assertions="2" errors="0" failures="0" skipped="0"><testcase classname="C" name="n" assertions="2">{extra}</testcase></testsuite></testsuites>'.encode()


class Tests(unittest.TestCase):
    def test_junit_recounts_actual_cases(self):
        self.assertEqual(junit(xml())[0]['executed'], 1)

    def test_junit_rejects_inflated_declared_total(self):
        with self.assertRaises(ValueError): junit(xml(declared=10))

    def test_junit_cannot_hide_skip(self):
        with self.assertRaises(ValueError): junit(xml('<skipped/>'))

    def test_junit_cannot_hide_failure(self):
        with self.assertRaises(ValueError): junit(xml('<failure/>'))

    def test_junit_rejects_xml_entity(self):
        with self.assertRaises(ValueError): junit(b'<!DOCTYPE x>'+xml())

    def test_junit_rejects_unaccounted_second_suite(self):
        raw = xml().replace(b'</testsuites>', b'<testsuite tests="1"/></testsuites>')
        with self.assertRaises(ValueError): junit(raw)

    def test_junit_rejects_duplicate_identity(self):
        raw = xml(declared=2).replace(b'assertions="2" errors', b'assertions="4" errors').replace(b'</testsuite>', b'<testcase classname="C" name="n" assertions="2"/></testsuite>')
        with self.assertRaises(ValueError): junit(raw)

    def test_junit_rejects_empty_success(self):
        with self.assertRaises(ValueError): junit(b'<testsuite tests="0" assertions="0" errors="0" failures="0" skipped="0"/>')

    def test_empty_coverage_is_not_100_percent(self):
        with self.assertRaises(ValueError): go_coverage(b'mode: atomic\n')

    def test_json_duplicate_key_is_not_last_wins(self):
        with self.assertRaises(ValueError): json_bytes(b'{"x":1,"x":2}')

    def test_go_distinguishes_parent_and_subtest(self):
        rows = [{'Action': 'start', 'Package': 'p'}]
        for name in ['TestA', 'TestA/sub']:
            rows += [{'Action': a, 'Package': 'p', 'Test': name} for a in ['run', 'pass']]
        rows += [{'Action': 'pass', 'Package': 'p'}]
        result = go_results(('\n'.join(json.dumps(x) for x in rows)).encode())
        self.assertEqual((result['top_level'], result['nested'], result['passed_test_events']), (1, 1, 2))
        rows.pop()
        with self.assertRaises(ValueError): go_results(('\n'.join(json.dumps(x) for x in rows)).encode())

    def go_stream(self, events):
        return ('\n'.join(json.dumps(e) for e in events)).encode()

    def test_go_rejects_unowned_test_package(self):
        events = [{'Action': 'start', 'Package': 'p'},
                  {'Action': 'run', 'Package': 'orphan', 'Test': 'TestA'},
                  {'Action': 'pass', 'Package': 'orphan', 'Test': 'TestA'},
                  {'Action': 'pass', 'Package': 'p'}]
        with self.assertRaises(ValueError): go_results(self.go_stream(events))

    def test_go_rejects_terminal_before_start(self):
        events = [{'Action': 'start', 'Package': 'p'},
                  {'Action': 'pass', 'Package': 'p', 'Test': 'TestA'},
                  {'Action': 'run', 'Package': 'p', 'Test': 'TestA'},
                  {'Action': 'pass', 'Package': 'p'}]
        with self.assertRaises(ValueError): go_results(self.go_stream(events))

    def test_go_rejects_duplicate_package_start(self):
        events = [{'Action': 'start', 'Package': 'p'}, {'Action': 'start', 'Package': 'p'},
                  {'Action': 'run', 'Package': 'p', 'Test': 'TestA'},
                  {'Action': 'pass', 'Package': 'p', 'Test': 'TestA'},
                  {'Action': 'pass', 'Package': 'p'}]
        with self.assertRaises(ValueError): go_results(self.go_stream(events))

    def test_go_rejects_duplicate_test_start(self):
        events = [{'Action': 'start', 'Package': 'p'},
                  {'Action': 'run', 'Package': 'p', 'Test': 'TestA'},
                  {'Action': 'run', 'Package': 'p', 'Test': 'TestA'},
                  {'Action': 'pass', 'Package': 'p', 'Test': 'TestA'},
                  {'Action': 'pass', 'Package': 'p'}]
        with self.assertRaises(ValueError): go_results(self.go_stream(events))

    def test_junit_negative_case_assertions_cannot_cancel_out(self):
        raw = b'<testsuite tests="2" assertions="2" errors="0" failures="0" skipped="0"><testcase classname="C" name="a" assertions="-1"/><testcase classname="C" name="b" assertions="3"/></testsuite>'
        with self.assertRaises(ValueError): junit(raw)

    def test_go_cannot_convert_skips_to_passes(self):
        with self.assertRaises(ValueError): go_results(b'{"Action":"skip","Package":"p","Test":"TestA"}')

    def test_go_coverage_counts_statements_not_blocks(self):
        self.assertEqual(go_coverage(b'mode: atomic\np.go:1.1,2.1 3 1\np.go:3.1,4.1 1 0\n')['percent'], 75.0)

    def test_zip_requires_expected_digest_and_safe_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/'test.zip'
            with zipfile.ZipFile(file,'w') as archive: archive.writestr('ok.txt',b'ok')
            self.assertEqual(archive_files(file,digest(file.read_bytes()))['ok.txt'],b'ok')
            with self.assertRaises(ValueError): archive_files(file,'0'*64)
            with zipfile.ZipFile(file,'w') as archive: archive.writestr('../escape',b'bad')
            with self.assertRaises(ValueError): archive_files(file,digest(file.read_bytes()))

    def cohort(self):
        r = {'repository': 'Oteryn/Oteryn', 'path': '.github/workflows/ci.yml', 'id': 1, 'head_sha': 'a'*40, 'event': 'pull_request', 'run_attempt': 1, 'conclusion': 'success', 'created_at': '2026-09-08T00:00:00Z'}
        j = {'id': 2, 'run_id': 1, 'name': 'test', 'status': 'completed', 'conclusion': 'success', 'started_at': '2026-09-08T00:00:10Z', 'completed_at': '2026-09-08T00:00:40Z'}
        r.update(jobs=[job_metrics(j,r)], observed_job_seconds=30.0, latest_attempt_job_seconds=30.0, jobs_with_missing_times=0, wall_from_run_creation_seconds=40.0, timestamp_anomalies=[])
        return {'qualification': 'TIMING_METADATA_ONLY_NOT_PRODUCT_PASS', 'unique_event_candidates': 1, 'runs': [r], 'strata': [{'repository': repo, 'workflow': w, 'selected': int(repo == r['repository'] and w == 'ci.yml')} for repo, ws in PLAN.items() for w in ws]}

    def test_ci_recomputes_times_from_native_timestamps(self):
        result = ci_summary(self.cohort()); self.assertEqual(result['strata'][0]['observed_job_seconds'], 30.0)

    def test_ci_rejects_invented_duration(self):
        d = self.cohort(); d['runs'][0]['jobs'][0]['execution_seconds'] = 0
        with self.assertRaises(ValueError): ci_summary(d)

    def test_ci_rejects_invented_total(self):
        d = self.cohort(); d['runs'][0]['observed_job_seconds'] = 31
        with self.assertRaises(ValueError): ci_summary(d)

    def test_ci_rejects_hidden_workflow_stratum(self):
        d = self.cohort(); d['strata'].pop()
        with self.assertRaises(ValueError): ci_summary(d)

    def test_internal_manifest_is_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/'test.zip'
            with zipfile.ZipFile(file,'w') as archive:
                archive.writestr('scope/value',b'ok');archive.writestr('scope/SHA256SUMS.json',json.dumps({'value':'0'*64}))
            with self.assertRaises(ValueError): archive_files(file,digest(file.read_bytes()))

    def legacy_fixture(self):
        routes = ['/', '/news', '/news/welcome-to-oteryn', '/wiki', '/download', '/login',
                  '/register', '/forgot-password', '/recovery-key', '/events', '/support', '/legal/privacy']
        sizes = [(390,844),(820,1180),(1440,1000),(1920,1080)]
        cases=[]; failed=[]
        for width,height in sizes:
            for route in routes:
                is_failed = route in {'/support','/legal/privacy'}
                criteria={k: True for k in ['http_ok','main','heading','language','title','no_overflow','labels','images','unique_ids']}
                if is_failed:
                    criteria['http_ok']=False
                    failed.append({'route':route,'width':width,'criterion':'http_ok'})
                cases.append({'route':route,'width':width,'height':height,'status':404 if is_failed else 200,
                              'criteria':criteria,'observed_errors':[]})
        return {'source_sha':'de917b3477a1de0667531380de3660e8b2ab59aa','playwright':'1.62.1','browser':'test',
                'cases':cases,'failed_criteria':failed,
                'no_javascript':{'route':'/login','status':200,'email_visible':True,'password_visible':True}}

    def test_original_browser_failure_signature_is_exact(self):
        result = legacy_failure_signature(json.dumps(self.legacy_fixture()).encode(), 'de917b3477a1de0667531380de3660e8b2ab59aa')
        self.assertEqual(result['failed_criteria'], 8)

    def test_original_browser_failure_rejects_hidden_ninth_failure(self):
        report=self.legacy_fixture()
        report['cases'][0]['criteria']['main']=False
        with self.assertRaises(ValueError):
            legacy_failure_signature(json.dumps(report).encode(), 'de917b3477a1de0667531380de3660e8b2ab59aa')

    def test_migration_log_binds_exact_path_set(self):
        rows=[]
        log=[]
        for i in range(50):
            name=f'2026_07_19_{i:06d}_migration_{i}'
            path=f'database/migrations/{name}.php'
            sha=f'{i:040x}'[-40:]
            rows.append((path,sha,name))
            log.append(f'  {name} .... 1.00ms DONE')
        pair_bytes=''.join(f'{p}\t{s}\n' for p,s,_ in sorted(rows)).encode()
        ledger='repository\tpath\tblob_sha\tdepth\tscope\tline_ranges\texecution_evidence\n'
        ledger+=''.join(f'platform\t{p}\t{s}\tSCOPED_SEMANTIC_REVIEW\tR3-DB\t[]\tSOURCE_REVIEW_ONLY\n' for p,s,_ in rows)
        log_raw=('\n'.join(log)+'\n').encode()
        review={'schema_version':1,'repository':'Oteryn/Oteryn-Platform','source_sha':'de917b3477a1de0667531380de3660e8b2ab59aa',
                'execution_artifact_id':7,'execution_log_sha256':digest(log_raw),'count':50,
                'path_set':{'ledger':'coverage-review.tsv','repository':'platform','exact_prefix':'database/migrations/','exact_suffix':'.php',
                            'sha256_of_path_and_blob_tsv':digest(pair_bytes)},
                'up_execution':'All50 migration names occur in the bound successful log; synthetic SQLite only','down_execution':'NOT_EXECUTED'}
        manifest={'provider_source_sha':'de917b3477a1de0667531380de3660e8b2ab59aa','artifacts':[{'name':'public_ui','artifact_id':7}]}
        self.assertEqual(migration_execution(log_raw,json.dumps(review).encode(),ledger.encode(),manifest)['migrations'],50)
        with self.assertRaises(ValueError):
            migration_execution(log_raw.replace(b'migration_49',b'migration_X'),json.dumps(review).encode(),ledger.encode(),manifest)

    def test_committed_results_drift_fails_closed(self):
        summary={'a':1,'nested':{'x':2}}
        self.assertEqual(require_committed_results(summary,json.dumps(summary).encode()),summary)
        with self.assertRaises(ValueError):
            require_committed_results(summary,b'{"a":1,"nested":{"x":3}}')


if __name__ == '__main__': unittest.main()
