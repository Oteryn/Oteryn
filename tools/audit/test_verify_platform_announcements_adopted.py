#!/usr/bin/env python3
"""Regression tests for canonical Announcements DIRECT adoption."""
from pathlib import Path
import copy
import unittest
from unittest.mock import patch

import verify_platform_announcements_adopted as adopted
import verify_platform_announcements_direct as pre

ROOT=Path(__file__).resolve().parents[2]


class AnnouncementsAdoptedVerifierTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate=pre.read_json(ROOT/pre.CANDIDATE_REL)

    def test_current_adopted_docs_pass(self):
        adopted.validate_adopted_docs(copy.deepcopy(self.candidate),ROOT)

    def test_current_lifecycle_is_external_review_metadata_not_pending(self):
        self.assertNotIn('PENDING',adopted.LIFECYCLE_RESULT)
        self.assertIn('3eb62ef72c1e13412fa45d5b25d597d112d9ae7d',adopted.REVIEW_PROVENANCE)
        self.assertIn('Not self-certified evidence',adopted.REVIEW_PROVENANCE)

    def test_historical_candidate_remains_pre_adoption(self):
        self.assertFalse(self.candidate['coverage_adopted'])
        self.assertEqual(self.candidate['projection']['status'],'PROJECTION_SUCCESS_NOT_ADOPTED')
        self.assertEqual(self.candidate['projection']['projected_ledger_sha256'],adopted.ANNOUNCEMENTS_LEDGER_SHA)

    def test_announcements_overlay_blob_is_exact(self):
        raw=(ROOT/adopted.ANNOUNCEMENTS_OVERLAY_REL).read_bytes()
        self.assertEqual(adopted.git_blob_sha(raw),adopted.ANNOUNCEMENTS_OVERLAY_BLOB)
        self.assertEqual(__import__('hashlib').sha256(raw).hexdigest(),adopted.ANNOUNCEMENTS_OVERLAY_SHA256)

    def test_line_range_contract_covers_exact_ten_paths(self):
        self.assertEqual(set(adopted.EXPECTED_LINE_RANGES),{row['path'] for row in self.candidate['paths']})
        self.assertEqual(len(adopted.EXPECTED_LINE_RANGES),10)

    def test_contradictory_canonical_execution_evidence_fails_closed(self):
        canonical=adopted.vr.load_review(
            ROOT/'docs/evidence/organization-audit-20260907',
            adopted.vr.read_json(ROOT/'docs/evidence/OTERYN-ORGANIZATION-COMPREHENSIVE-AUDIT-20260907.json'))
        mutated=copy.deepcopy(canonical)
        target=next(row for row in mutated if row['path'].startswith('app/Announcements/'))
        target['execution_evidence']='Contradictory execution claim.'
        with patch.object(adopted.vr,'load_review',return_value=mutated):
            with self.assertRaisesRegex(ValueError,'execution_evidence'):
                adopted.validate_adopted_docs(copy.deepcopy(self.candidate),ROOT)


if __name__=='__main__':unittest.main()
