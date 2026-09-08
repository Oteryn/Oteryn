#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess
import tempfile
import unittest

import verify_platform_gameauth_group as gameauth


def run(root: Path, *args: str) -> str:
    return subprocess.run(
        ['git', '-C', str(root), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ).stdout.strip()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


class PlatformGameAuthGroupTests(unittest.TestCase):
    def make_repo(self, root: Path) -> None:
        subprocess.run(['git', 'init', '-q', str(root)], check=True)
        run(root, 'config', 'user.name', 'Audit fixture')
        run(root, 'config', 'user.email', 'audit@example.invalid')
        run(root, 'config', 'commit.gpgsign', 'false')

    def fixture(self, base: Path):
        platform = base / 'platform'
        evidence = base / 'evidence'
        audit = base / 'audit'
        self.make_repo(platform)

        prefix_files = ['app/GameAuth/A.php'] + [
            f'app/GameAuth/Nested/F{index:02d}.php' for index in range(26)
        ]
        self.assertEqual(len(prefix_files), 27)
        for path in prefix_files:
            write(platform / path, '<?php\n')
        deps = {
            'bootstrap/app.php': 'bootstrap\n',
            'config/game-auth.php': 'gameauth\n',
            'config/auth.php': 'auth\n',
            'config/database.php': 'db\n',
            'routes/api.php': 'api\n',
            'routes/internal.php': 'internal\n',
            'tests/Feature/GameAuth': None,
            'tests/Unit/Http/Middleware/PreventSensitiveGameAuthResponseCachingTest.php': 'unit\n',
            'composer.json': '{}\n',
            'composer.lock': '{}\n',
            'phpunit.xml': '<phpunit/>\n',
        }
        focused = []
        for index in range(14):
            path = f'tests/Feature/GameAuth/F{index}.php'
            focused.append(path)
            write(platform / path, '<?php\n')
        for path, content in deps.items():
            if content is not None:
                write(platform / path, content)
        run(platform, 'add', '.')
        run(platform, 'commit', '-qm', 'historical')
        historical = run(platform, 'rev-parse', 'HEAD')
        historical_tree = run(platform, 'rev-parse', 'HEAD^{tree}')
        app_tree = run(platform, 'rev-parse', 'HEAD:app')
        group_tree = run(platform, 'rev-parse', 'HEAD:app/GameAuth')

        write(platform / 'docs/only.md', 'later\n')
        run(platform, 'add', '.')
        run(platform, 'commit', '-qm', 'current')
        current = run(platform, 'rev-parse', 'HEAD')
        current_tree = run(platform, 'rev-parse', 'HEAD^{tree}')

        self.make_repo(evidence)
        statement = '**FACT.** All 27 files in the inspected `app/GameAuth/**` batch were read directly.'
        evidence_rel = Path('docs/testing/audit.md')
        write(evidence / evidence_rel, statement + '\n')
        run(evidence, 'add', '.')
        run(evidence, 'commit', '-qm', 'evidence')
        publication = run(evidence, 'rev-parse', 'HEAD')
        publication_tree = run(evidence, 'rev-parse', 'HEAD^{tree}')
        evidence_blob = run(evidence, 'rev-parse', 'HEAD:' + evidence_rel.as_posix())

        dep_blobs = {path: run(platform, 'rev-parse', current + ':' + path) for path in deps}
        candidate = {
            'schema_version': 1,
            'candidate_id': 'fixture',
            'repository': 'Oteryn/Oteryn-Platform',
            'state': gameauth.PENDING,
            'path_prefix': 'app/GameAuth/',
            'expected_count': 27,
            'historical_evidence': {
                'publication_commit': publication,
                'publication_tree': publication_tree,
                'coverage_rules_path': evidence_rel.as_posix(),
                'coverage_rules_blob': evidence_blob,
                'audited_main_sha': historical,
                'audited_main_tree': historical_tree,
                'exact_statement': statement,
                'pattern': 'app/GameAuth/**',
                'count': 27,
                'basis': 'fixture direct read',
            },
            'current_revalidation': {
                'source_commit': current,
                'source_tree': current_tree,
                'historical_app_tree': app_tree,
                'current_app_tree': app_tree,
                'gameauth_tree': group_tree,
                'changed_paths_under_group_prefix': 0,
                'historical_to_current_compare_status': 'ahead',
                'current_blobs': dep_blobs,
                'required_checks': ['fixture'],
                'focused_test_files': focused,
            },
            'coverage_adopted': False,
            'limitations': 'fixture',
        }
        candidate_path = audit / gameauth.CANDIDATE
        write(candidate_path, json.dumps(candidate))
        write(audit / gameauth.GROUPS, json.dumps({'schema_version': 1, 'groups': [], 'rejected_candidates': []}))
        return platform, evidence, audit, candidate_path, historical, current

    def adopt(self, audit: Path, candidate_path: Path):
        candidate = json.loads(candidate_path.read_text())
        candidate['state'] = gameauth.ADOPTED
        candidate['coverage_adopted'] = True
        candidate_path.write_text(json.dumps(candidate))
        group = {
            'id': candidate['candidate_id'],
            'repository': 'platform',
            'disposition': 'GROUPED',
            'path_prefix': candidate['path_prefix'],
            'expected_count': candidate['expected_count'],
            'depth': 'GROUPED_REVALIDATED',
            'scope': 'fixture group',
            'limitations': 'fixture limitation',
            'historical_evidence': candidate['historical_evidence'],
            'current_revalidation': candidate['current_revalidation'],
            'evaluation': {
                'qualification_run': 1,
                'qualification_job': 2,
                'focused_current_tests': {'cases': 3, 'assertions': 4, 'failures': 0, 'errors': 0, 'skipped': 0},
                'outcome': gameauth.OUTCOME,
            },
        }
        write(audit / gameauth.GROUPS, json.dumps({'schema_version': 1, 'groups': [group], 'rejected_candidates': []}))

    def test_exact_identity_candidate_passes_without_adopting_coverage(self):
        with tempfile.TemporaryDirectory(prefix='gameauth-group-') as td:
            platform, evidence, audit, _, _, _ = self.fixture(Path(td))
            result = gameauth.verify(audit, platform, evidence)
            self.assertEqual(result['paths'], 27)
            self.assertTrue(result['path_blob_identity'])
            self.assertFalse(result['coverage_adopted'])

    def test_adopted_state_requires_and_revalidates_matching_group(self):
        with tempfile.TemporaryDirectory(prefix='gameauth-group-') as td:
            platform, evidence, audit, candidate_path, _, _ = self.fixture(Path(td))
            self.adopt(audit, candidate_path)
            result = gameauth.verify(audit, platform, evidence)
            self.assertEqual(result['result'], 'GAMEAUTH_GROUPED_ADOPTION_REVALIDATED_NOT_PRODUCT_PASS')
            self.assertTrue(result['coverage_adopted'])

    def test_adopted_state_rejects_group_evidence_drift(self):
        with tempfile.TemporaryDirectory(prefix='gameauth-group-') as td:
            platform, evidence, audit, candidate_path, _, _ = self.fixture(Path(td))
            self.adopt(audit, candidate_path)
            doc = json.loads((audit / gameauth.GROUPS).read_text())
            doc['groups'][0]['current_revalidation']['current_app_tree'] = '0' * 40
            write(audit / gameauth.GROUPS, json.dumps(doc))
            with self.assertRaisesRegex(ValueError, 'current evidence drift'):
                gameauth.verify(audit, platform, evidence)

    def test_group_source_change_fails_closed(self):
        with tempfile.TemporaryDirectory(prefix='gameauth-group-') as td:
            platform, evidence, audit, candidate_path, _, _ = self.fixture(Path(td))
            write(platform / 'app/GameAuth/A.php', '<?php // changed\n')
            run(platform, 'add', '.')
            run(platform, 'commit', '-qm', 'bad')
            data = json.loads(candidate_path.read_text())
            current = run(platform, 'rev-parse', 'HEAD')
            data['current_revalidation']['source_commit'] = current
            data['current_revalidation']['source_tree'] = run(platform, 'rev-parse', 'HEAD^{tree}')
            data['current_revalidation']['current_app_tree'] = run(platform, 'rev-parse', 'HEAD:app')
            data['current_revalidation']['gameauth_tree'] = run(platform, 'rev-parse', 'HEAD:app/GameAuth')
            for path in data['current_revalidation']['current_blobs']:
                data['current_revalidation']['current_blobs'][path] = run(platform, 'rev-parse', current + ':' + path)
            candidate_path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, 'app tree changed|GameAuth tree changed|GameAuth path/blob identity changed|GameAuth diff not empty'):
                gameauth.verify(audit, platform, evidence)

    def test_missing_historical_statement_fails_closed(self):
        with tempfile.TemporaryDirectory(prefix='gameauth-group-') as td:
            platform, evidence, audit, candidate_path, _, _ = self.fixture(Path(td))
            data = json.loads(candidate_path.read_text())
            data['historical_evidence']['exact_statement'] = 'not present'
            candidate_path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, 'direct-read statement'):
                gameauth.verify(audit, platform, evidence)

    def test_dependent_blob_drift_fails_closed(self):
        with tempfile.TemporaryDirectory(prefix='gameauth-group-') as td:
            platform, evidence, audit, candidate_path, _, _ = self.fixture(Path(td))
            data = json.loads(candidate_path.read_text())
            data['current_revalidation']['current_blobs']['config/auth.php'] = '0' * 40
            candidate_path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, 'dependent blob mismatch'):
                gameauth.verify(audit, platform, evidence)

    def test_candidate_cannot_preclaim_adoption(self):
        with tempfile.TemporaryDirectory(prefix='gameauth-group-') as td:
            platform, evidence, audit, candidate_path, _, _ = self.fixture(Path(td))
            data = json.loads(candidate_path.read_text())
            data['coverage_adopted'] = True
            candidate_path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, 'adoption/state mismatch'):
                gameauth.verify(audit, platform, evidence)


if __name__ == '__main__':
    unittest.main()
