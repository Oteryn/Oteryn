#!/usr/bin/env python3
"""Adversarial tests for the bounded R3 README current-state contract."""
from pathlib import Path
import tempfile
import unittest

import verify_readme_current_state as readme_contract

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / 'docs/evidence/organization-audit-20260907/README.md'
CI_WORKFLOW = ROOT / '.github/workflows/ci.yml'

EXPECTED_TERMINAL_GATE_STEP = """      - name: Validate audit terminal state
        shell: bash
        run: |
          set -euo pipefail
          PYTHONDONTWRITEBYTECODE=1 python3 tools/audit/test_verify_readme_current_state.py
          PYTHONDONTWRITEBYTECODE=1 python3 tools/audit/verify_readme_current_state.py"""
EXPECTED_META_GATE_NAME = '    name: meta-gate'


def validate_terminal_gate_step(workflow: str) -> None:
    lines = workflow.splitlines()
    job_markers = [index for index, line in enumerate(lines) if line == '  meta-gate:']
    if len(job_markers) != 1:
        raise ValueError('meta-gate job must exist exactly once')
    job_start = job_markers[0]
    job_end = len(lines)
    for index in range(job_start + 1, len(lines)):
        line = lines[index]
        if line.startswith('  ') and not line.startswith('    ') and line.endswith(':'):
            job_end = index
            break
    job_lines = lines[job_start:job_end]
    job_names = [line for line in job_lines if line.startswith('    name:')]
    if job_names != [EXPECTED_META_GATE_NAME]:
        raise ValueError('meta-gate job must retain the exact required-check display name')
    if any(line.startswith('    if:') for line in job_lines):
        raise ValueError('meta-gate job must not have a disabling condition')
    if any(line.startswith('    continue-on-error:') for line in job_lines):
        raise ValueError('meta-gate job must not suppress job failure')
    step_markers = [index for index, line in enumerate(job_lines) if line == '      - name: Validate audit terminal state']
    if len(step_markers) != 1:
        raise ValueError('terminal-state step must exist exactly once in meta-gate')
    step_start = step_markers[0]
    step_end = len(job_lines)
    for index in range(step_start + 1, len(job_lines)):
        if job_lines[index].startswith('      - '):
            step_end = index
            break
    actual = '\n'.join(job_lines[step_start:step_end]).rstrip()
    if actual != EXPECTED_TERMINAL_GATE_STEP:
        raise ValueError('terminal-state step must be exact executable fail-closed commands')


class ReadmeCurrentStateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current = README.read_text(encoding='utf-8')

    def reject(self, text: str) -> None:
        with self.assertRaises(ValueError):
            readme_contract.validate_text(text)

    def test_current_readme_passes(self):
        result = readme_contract.validate(self.current)
        self.assertEqual(result['result'], 'README_CURRENT_STATE_VALIDATED_NOT_PRODUCT_PASS')
        self.assertEqual(result['direct_paths'], 335)
        self.assertEqual(result['grouped_paths'], 113)
        self.assertEqual(result['unverified_paths'], 3913)
        self.assertEqual(result['semantically_classified_paths'], 448)
        self.assertEqual(
            result['remaining_bounded_proof_workflows'],
            [],
        )
        self.assertFalse(result['product_readiness_claimed'])
        self.assertFalse(result['audit_completion_claimed'])

    def test_required_meta_gate_runs_terminal_state_contract(self):
        validate_terminal_gate_step(CI_WORKFLOW.read_text(encoding='utf-8'))

    def test_required_meta_gate_rejects_non_executable_or_suppressed_commands(self):
        workflow = CI_WORKFLOW.read_text(encoding='utf-8')
        command = '          PYTHONDONTWRITEBYTECODE=1 python3 tools/audit/verify_readme_current_state.py'
        test_command = '          PYTHONDONTWRITEBYTECODE=1 python3 tools/audit/test_verify_readme_current_state.py'
        step_mutations = (
            EXPECTED_TERMINAL_GATE_STEP.replace(command, '          echo PYTHONDONTWRITEBYTECODE=1 python3 tools/audit/verify_readme_current_state.py', 1),
            EXPECTED_TERMINAL_GATE_STEP.replace(command, '          # PYTHONDONTWRITEBYTECODE=1 python3 tools/audit/verify_readme_current_state.py', 1),
            EXPECTED_TERMINAL_GATE_STEP.replace(command, command + ' || true', 1),
            EXPECTED_TERMINAL_GATE_STEP.replace(test_command, test_command + ' || true', 1),
            EXPECTED_TERMINAL_GATE_STEP.replace('        run: |', '        continue-on-error: true\n        run: |', 1),
            EXPECTED_TERMINAL_GATE_STEP.replace('        shell: bash', '        if: false\n        shell: bash', 1),
        )
        for mutated_step in step_mutations:
            with self.subTest(mutated_step=mutated_step):
                mutated_workflow = workflow.replace(EXPECTED_TERMINAL_GATE_STEP, mutated_step, 1)
                self.assertNotEqual(mutated_workflow, workflow)
                with self.assertRaisesRegex(ValueError, 'exact executable fail-closed commands'):
                    validate_terminal_gate_step(mutated_workflow)

    def test_required_meta_gate_rejects_disabled_or_rebound_job(self):
        workflow = CI_WORKFLOW.read_text(encoding='utf-8')
        mutations = (
            workflow.replace('  meta-gate:\n    name: meta-gate', '  meta-gate:\n    if: false\n    name: meta-gate', 1),
            workflow.replace('  meta-gate:\n    name: meta-gate', '  meta-gate:\n    continue-on-error: true\n    name: meta-gate', 1),
            workflow.replace('    name: meta-gate', '    name: disabled-meta-gate', 1),
            workflow.replace(
                '  meta-gate:\n    name: meta-gate',
                '  disabled-gate:\n    name: disabled-meta-gate',
                1,
            ) + '\n  decoy:\n    name: meta-gate\n    runs-on: ubuntu-latest\n    steps: []\n',
        )
        for mutated_workflow in mutations:
            with self.subTest(mutated_workflow=mutated_workflow):
                self.assertNotEqual(mutated_workflow, workflow)
                with self.assertRaises(ValueError):
                    validate_terminal_gate_step(mutated_workflow)

    def test_terminal_workflow_state_rejects_reintroduced_audit_workflow(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            workflow_dir = root / readme_contract.WORKFLOW_DIR
            workflow_dir.mkdir(parents=True)
            self.assertEqual(readme_contract.validate_terminal_workflow_state(root), [])
            retired = root / readme_contract.RETIRED_R7_WORKFLOW
            retired.write_text('name: retired\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'retired R7 qualification workflow still present'):
                readme_contract.validate_terminal_workflow_state(root)
            retired.unlink()
            (workflow_dir / 'organization-audit-unexpected.yml').write_text('name: unexpected\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'bounded audit-proof workflow still present'):
                readme_contract.validate_terminal_workflow_state(root)

    def test_terminal_workflow_state_rejects_yaml_extension(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            workflow_dir = root / readme_contract.WORKFLOW_DIR
            workflow_dir.mkdir(parents=True)
            (workflow_dir / 'organization-audit-unexpected.yaml').write_text(
                'name: unexpected\n', encoding='utf-8'
            )
            with self.assertRaisesRegex(ValueError, 'bounded audit-proof workflow still present'):
                readme_contract.validate_terminal_workflow_state(root)

    def test_validate_rejects_reintroduced_r7_workflow(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            workflow_dir = root / readme_contract.WORKFLOW_DIR
            workflow_dir.mkdir(parents=True)
            retired = root / readme_contract.RETIRED_R7_WORKFLOW
            retired.write_text('name: retired\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'retired R7 qualification workflow still present'):
                readme_contract.validate(self.current, root)

    def test_old_accounting_transition_rejected(self):
        mutated = self.current.replace('335 DIRECT scoped path reviews', '258 DIRECT scoped path reviews', 1)
        mutated = mutated.replace('3918 retain UNVERIFIED semantics', '3954 retain UNVERIFIED semantics', 1)
        self.reject(mutated)

    def test_stale_residual_obligation_count_rejected(self):
        mutated = self.current.replace('14 residual obligations', '15 residual obligations', 1)
        self.reject(mutated)

    def test_spelled_out_stale_obligation_claim_rejected(self):
        mutated = self.current.replace(
            'Full 4325-row CSV',
            'Fifteen residual obligations remain.\n\nFull 4325-row CSV',
            1,
        )
        self.reject(mutated)

    def test_numeric_extra_obligation_claim_rejected(self):
        mutated = self.current.replace(
            'Full 4325-row CSV',
            'There are 15 obligations left.\n\nFull 4325-row CSV',
            1,
        )
        self.reject(mutated)

    def test_html_comment_split_obligation_claim_rejected(self):
        mutated = self.current.replace(
            'Full 4325-row CSV',
            'There are 15 obliga<!-- -->tions left.\n\nFull 4325-row CSV',
            1,
        )
        self.reject(mutated)

    def test_markdown_split_obligation_claim_rejected(self):
        mutated = self.current.replace(
            'Full 4325-row CSV',
            'There are 15 obliga**tions** left.\n\nFull 4325-row CSV',
            1,
        )
        self.reject(mutated)

    def test_unrelated_insertion_rejected(self):
        mutated = self.current.replace(
            'Full 4325-row CSV',
            'Unrelated inserted content.\n\nFull 4325-row CSV',
            1,
        )
        self.reject(mutated)

    def test_duplicate_canonical_obligation_claim_rejected(self):
        mutated = self.current.replace(
            'Full 4325-row CSV',
            '14 residual obligations.\n\nFull 4325-row CSV',
            1,
        )
        self.reject(mutated)

    def test_relocated_canonical_obligation_claim_rejected(self):
        mutated = self.current.replace('14 residual obligations, ', '', 1)
        mutated = mutated.replace(
            'Full 4325-row CSV',
            'There are 14 residual obligations.\n\nFull 4325-row CSV',
            1,
        )
        self.reject(mutated)

    def test_historical_review_pending_wording_rejected(self):
        mutated = self.current.replace(
            'Those five corrections are applied and carried forward in the current audit lineage; they are not a pending review gate in this README.',
            'These remain author remediation until the resulting exact head receives canonical CI and fresh independent re-review.',
            1,
        )
        self.reject(mutated)

    def test_marketplace_workflow_pending_wording_rejected(self):
        mutated = self.current.replace(
            'Marketplace/Payments/Wallet qualification, ledger-reproduction and projection workflows and the six-file Marketplace-test temporary proof workflows were removed after their completed review/cleanup.',
            'Temporary Marketplace/Payments/Wallet qualification, ledger-reproduction and projection workflows remain only while the 49-path adoption is rebound and independently reviewed.',
            1,
        )
        self.reject(mutated)

    def test_announcements_pre_adoption_workflow_wording_rejected(self):
        mutated = self.current.replace(
            'The Announcements pre-adoption qualification and projection workflows are removed after their bound successful runs.',
            'The Announcements pre-adoption qualification and projection workflows remain active.',
            1,
        )
        self.reject(mutated)

    def test_terminal_bounded_proof_workflow_wording_rejected(self):
        mutated = self.current.replace(
            'The temporary R7 META current-main governance qualification workflow was removed after its successful exact-head qualification and clean independent review; no `organization-audit-*.yml` bounded audit-proof workflows remain in the effective tree.',
            'The current tree retains two bounded audit-proof workflows: the Platform audit-recorder adopted-proof workflow and the Platform Announcements adopted-proof workflow.',
            1,
        )
        self.reject(mutated)

    def test_premature_no_bounded_workflow_claim_rejected(self):
        mutated = self.current.replace(
            'The temporary R7 META current-main governance qualification workflow was removed after its successful exact-head qualification and clean independent review; no `organization-audit-*.yml` bounded audit-proof workflows remain in the effective tree.',
            'The current tree retains no bounded audit-proof workflows.',
            1,
        )
        self.reject(mutated)

    def test_product_readiness_append_to_durability_rejected(self):
        mutated = self.current.replace(
            readme_contract.EXPECTED_DURABILITY_CLOSEOUT,
            readme_contract.EXPECTED_DURABILITY_CLOSEOUT + ' This batch establishes full product readiness.',
            1,
        )
        self.reject(mutated)

    def test_adjacent_review_status_paragraph_rejected(self):
        marker = '\n\n## Evidence map and durability'
        mutated = self.current.replace(
            marker,
            '\n\nThis audit is now independently complete and product-ready.' + marker,
            1,
        )
        self.reject(mutated)

    def test_extra_trailing_status_paragraph_rejected(self):
        mutated = self.current.rstrip() + '\n\nOrganization-wide audit completion is established.\n'
        self.reject(mutated)

    def test_truncated_current_accounting_paragraph_rejected(self):
        mutated = self.current.replace(' and 3913 retain UNVERIFIED semantics.', '.', 1)
        self.reject(mutated)


if __name__ == '__main__':
    unittest.main()
