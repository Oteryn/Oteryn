#!/usr/bin/env python3
"""Adversarial tests for the Announcements pre-adoption candidate verifier."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

import verify_platform_announcements_direct as verifier

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = ROOT / verifier.CANDIDATE_REL


class AnnouncementsDirectCandidateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current = verifier.read_json(CANDIDATE)

    def reject(self, candidate: dict) -> None:
        with self.assertRaises(ValueError):
            verifier.validate_candidate_shape(candidate)

    def test_current_candidate_shape_passes(self):
        verifier.validate_candidate_shape(deepcopy(self.current))

    def test_coverage_cannot_be_adopted_during_primary_candidate_stage(self):
        mutated = deepcopy(self.current)
        mutated['coverage_adopted'] = True
        self.reject(mutated)

    def test_exact_ten_path_enumeration_is_required(self):
        mutated = deepcopy(self.current)
        mutated['paths'].pop()
        self.reject(mutated)

    def test_extra_path_is_rejected(self):
        mutated = deepcopy(self.current)
        mutated['paths'].append(deepcopy(mutated['paths'][0]))
        mutated['paths'][-1]['path'] = 'app/Announcements/Unexpected.php'
        self.reject(mutated)

    def test_path_blob_drift_is_rejected(self):
        mutated = deepcopy(self.current)
        mutated['paths'][0]['blob_sha'] = '0' * 40
        self.reject(mutated)

    def test_path_semantic_assertion_drift_is_rejected(self):
        mutated = deepcopy(self.current)
        mutated['paths'][0]['semantic_assertions'][0] = 'final class DifferentAnnouncement'
        self.reject(mutated)

    def test_dependency_binding_drift_is_rejected(self):
        mutated = deepcopy(self.current)
        mutated['dependency_bindings'][0]['required_text'] = 'Schema::create(\'different_table\''
        self.reject(mutated)

    def test_focused_test_method_drift_is_rejected(self):
        mutated = deepcopy(self.current)
        mutated['focused_current_tests'][0]['required_methods'][0] = 'test_missing_method'
        self.reject(mutated)

    def test_stale_baseline_accounting_is_rejected(self):
        mutated = deepcopy(self.current)
        mutated['baseline_accounting']['direct_paths'] = 221
        mutated['baseline_accounting']['unverified_paths'] = 3991
        self.reject(mutated)

    def test_baseline_ledger_digest_drift_is_rejected(self):
        mutated = deepcopy(self.current)
        mutated['baseline_accounting']['ledger_sha256'] = '0' * 64
        self.reject(mutated)

    def test_primary_backend_and_case_contract_are_exact(self):
        mutated = deepcopy(self.current)
        mutated['qualification']['mariadb_image'] = 'mariadb:latest'
        mutated['qualification']['expected_cases'] = 3
        self.reject(mutated)

    def test_primary_failure_requirement_cannot_be_relaxed(self):
        mutated = deepcopy(self.current)
        mutated['qualification']['required_failures'] = 1
        self.reject(mutated)

    def test_projection_cannot_claim_adoption(self):
        mutated = deepcopy(self.current)
        mutated['projection']['status'] = 'ADOPTED'
        mutated['projection']['adopted_paths'] = 10
        self.reject(mutated)

    def test_polish_locale_execution_limitation_is_required(self):
        mutated = deepcopy(self.current)
        mutated['limitations'][1] = 'All locale branches are fully executed.'
        self.reject(mutated)

    def test_simultaneous_writer_limitation_is_required(self):
        mutated = deepcopy(self.current)
        mutated['limitations'][2] = 'Concurrency is exhaustively proven.'
        self.reject(mutated)

    def test_product_or_whole_audit_pass_cannot_be_appended(self):
        mutated = deepcopy(self.current)
        mutated['limitations'].append('The product and organization audit are fully ready.')
        self.reject(mutated)

    def test_unexpected_top_level_key_is_rejected(self):
        mutated = deepcopy(self.current)
        mutated['review_passed'] = True
        self.reject(mutated)

    def test_type_drift_is_rejected(self):
        mutated = deepcopy(self.current)
        mutated['schema_version'] = True
        self.reject(mutated)

    def test_duplicate_json_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'candidate.json'
            path.write_text('{"schema_version":1,"schema_version":1}\n', encoding='utf-8')
            with self.assertRaises(ValueError):
                verifier.read_json(path)


if __name__ == '__main__':
    unittest.main()
