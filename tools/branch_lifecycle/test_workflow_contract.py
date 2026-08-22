from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class WorkflowContractTests(unittest.TestCase):
    def test_composite_action_is_fail_closed_and_uses_action_path(self):
        path = ROOT / '.github' / 'actions' / 'terminal-branch-cleanup' / 'action.yml'
        text = path.read_text(encoding='utf-8')
        self.assertIn('using: composite', text)
        self.assertIn('GITHUB_ACTION_PATH', text)
        self.assertIn('GITHUB_TOKEN: ${{ inputs.token }}', text)
        self.assertIn('--event "$GITHUB_EVENT_PATH"', text)
        self.assertIn('--repository "$GITHUB_REPOSITORY"', text)
        self.assertIn('--root "$GITHUB_WORKSPACE"', text)
        self.assertIn('exit "$status"', text)

    def test_meta_close_event_workflow_uses_trusted_main_and_write_is_job_scoped(self):
        path = ROOT / '.github' / 'workflows' / 'terminal-branch-lifecycle.yml'
        text = path.read_text(encoding='utf-8')
        self.assertIn('pull_request_target:', text)
        self.assertIn('types: [closed]', text)
        self.assertIn('contents: read', text)
        self.assertIn('contents: write', text)
        self.assertIn('github.event.pull_request.merged == false', text)
        self.assertIn('github.event.pull_request.head.repo.full_name == github.repository', text)
        self.assertIn('ref: main', text)
        self.assertIn('uses: ./.github/actions/terminal-branch-cleanup', text)
        self.assertIn('token: ${{ github.token }}', text)

    def test_branch_lifecycle_ci_runs_unit_and_workflow_contract_tests(self):
        path = ROOT / '.github' / 'workflows' / 'terminal-branch-lifecycle-ci.yml'
        text = path.read_text(encoding='utf-8')
        self.assertIn('pull_request:', text)
        self.assertIn('permissions:\n  contents: read', text)
        self.assertIn('python3 tools/branch_lifecycle/test_closed_pr_cleanup.py', text)
        self.assertIn('python3 tools/branch_lifecycle/test_workflow_contract.py', text)
        self.assertIn('py_compile', text)


if __name__ == '__main__':
    unittest.main()
