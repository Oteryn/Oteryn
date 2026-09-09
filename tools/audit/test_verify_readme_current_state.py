#!/usr/bin/env python3
"""Adversarial tests for the bounded R3 README current-state contract."""
from pathlib import Path
import unittest

import verify_readme_current_state as readme_contract

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / 'docs/evidence/organization-audit-20260907/README.md'


class ReadmeCurrentStateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current = README.read_text(encoding='utf-8')

    def reject(self, text: str) -> None:
        with self.assertRaises(ValueError):
            readme_contract.validate_text(text)

    def test_current_readme_passes(self):
        result = readme_contract.validate_text(self.current)
        self.assertEqual(result['result'], 'README_CURRENT_STATE_VALIDATED_NOT_PRODUCT_PASS')
        self.assertEqual(result['direct_paths'], 223)
        self.assertEqual(result['grouped_paths'], 113)
        self.assertEqual(result['unverified_paths'], 3989)
        self.assertEqual(result['semantically_classified_paths'], 336)
        self.assertFalse(result['product_readiness_claimed'])
        self.assertFalse(result['audit_completion_claimed'])

    def test_old_accounting_transition_rejected(self):
        mutated = self.current.replace('223 DIRECT scoped path reviews', '221 DIRECT scoped path reviews', 1)
        mutated = mutated.replace('113 bounded GROUPED Platform paths', '107 bounded GROUPED Platform paths', 1)
        mutated = mutated.replace('3989 retain UNVERIFIED semantics', '3997 retain UNVERIFIED semantics', 1)
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
        mutated = self.current.replace(' and 3989 retain UNVERIFIED semantics.', '.', 1)
        self.reject(mutated)


if __name__ == '__main__':
    unittest.main()
