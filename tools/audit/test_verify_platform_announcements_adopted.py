#!/usr/bin/env python3
"""Regression tests for canonical Announcements DIRECT adoption."""
from pathlib import Path
import copy
import unittest

import verify_platform_announcements_adopted as adopted
import verify_platform_announcements_direct as pre

ROOT=Path(__file__).resolve().parents[2]


class AnnouncementsAdoptedVerifierTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate=pre.read_json(ROOT/pre.CANDIDATE_REL)

    def test_current_adopted_docs_pass(self):
        adopted.validate_adopted_docs(copy.deepcopy(self.candidate),ROOT)

    def test_historical_candidate_remains_pre_adoption(self):
        self.assertFalse(self.candidate['coverage_adopted'])
        self.assertEqual(self.candidate['projection']['status'],'PROJECTION_SUCCESS_NOT_ADOPTED')
        self.assertEqual(self.candidate['projection']['projected_ledger_sha256'],adopted.CANONICAL_LEDGER_SHA)

    def test_announcements_overlay_blob_is_exact(self):
        raw=(ROOT/adopted.ANNOUNCEMENTS_OVERLAY_REL).read_bytes()
        self.assertEqual(adopted.git_blob_sha(raw),adopted.ANNOUNCEMENTS_OVERLAY_BLOB)
        self.assertEqual(__import__('hashlib').sha256(raw).hexdigest(),adopted.ANNOUNCEMENTS_OVERLAY_SHA256)

    def test_line_range_contract_covers_exact_ten_paths(self):
        self.assertEqual(set(adopted.EXPECTED_LINE_RANGES),{row['path'] for row in self.candidate['paths']})
        self.assertEqual(len(adopted.EXPECTED_LINE_RANGES),10)


if __name__=='__main__':unittest.main()
