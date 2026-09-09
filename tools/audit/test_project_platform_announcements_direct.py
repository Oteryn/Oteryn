#!/usr/bin/env python3
"""Adversarial tests for the Announcements projection-only transform."""
from copy import deepcopy
from pathlib import Path
import unittest

import project_platform_announcements_direct as projector
import verify_platform_announcements_direct as candidate_verifier

ROOT=Path(__file__).resolve().parents[2]


class AnnouncementsProjectionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate=candidate_verifier.read_json(ROOT/candidate_verifier.CANDIDATE_REL)
        candidate_verifier.validate_candidate_shape(cls.candidate)

    def rows(self):
        rows=[]
        for spec in self.candidate['paths']:
            rows.append({
                'repository_id':'platform','commit_sha':candidate_verifier.SOURCE_COMMIT,
                'tree_sha':candidate_verifier.SOURCE_TREE,'path':spec['path'],'mode':'100644',
                'object_sha':spec['blob_sha'],'disposition':'UNVERIFIED','depth':'IDENTITY_ONLY',
                'scope':'identity-only pre-projection marker',
            })
        return rows

    def test_exact_ten_paths_project_unverified_to_direct(self):
        projected,changed=projector.project_rows(self.rows(),self.candidate)
        self.assertEqual(changed,[row['path'] for row in self.candidate['paths']])
        self.assertEqual(len(projected),10)
        self.assertTrue(all(row['disposition']=='DIRECT' for row in projected))
        self.assertEqual([row['depth'] for row in projected],[row['depth'] for row in self.candidate['paths']])
        self.assertEqual([row['scope'] for row in projected],[row['scope'] for row in self.candidate['paths']])

    def test_already_direct_candidate_fails_closed(self):
        rows=self.rows(); rows[0]['disposition']='DIRECT'
        with self.assertRaises(ValueError): projector.project_rows(rows,self.candidate)

    def test_grouped_candidate_fails_closed(self):
        rows=self.rows(); rows[0]['disposition']='GROUPED'
        with self.assertRaises(ValueError): projector.project_rows(rows,self.candidate)

    def test_missing_candidate_path_fails_closed(self):
        rows=self.rows()[:-1]
        with self.assertRaises(ValueError): projector.project_rows(rows,self.candidate)

    def test_candidate_blob_drift_fails_closed(self):
        rows=self.rows(); rows[2]['object_sha']='0'*40
        with self.assertRaises(ValueError): projector.project_rows(rows,self.candidate)

    def test_candidate_commit_drift_fails_closed(self):
        rows=self.rows(); rows[3]['commit_sha']='0'*40
        with self.assertRaises(ValueError): projector.project_rows(rows,self.candidate)

    def test_candidate_tree_drift_fails_closed(self):
        rows=self.rows(); rows[4]['tree_sha']='0'*40
        with self.assertRaises(ValueError): projector.project_rows(rows,self.candidate)

    def test_non_regular_candidate_fails_closed(self):
        rows=self.rows(); rows[5]['mode']='120000'
        with self.assertRaises(ValueError): projector.project_rows(rows,self.candidate)

    def test_noncandidate_row_is_byte_semantically_unchanged(self):
        rows=self.rows(); sentinel={
            'repository_id':'meta','commit_sha':'1'*40,'tree_sha':'2'*40,'path':'sentinel.txt','mode':'100644',
            'object_sha':'3'*40,'disposition':'UNVERIFIED','depth':'IDENTITY_ONLY','scope':'sentinel scope',
        }; rows.append(deepcopy(sentinel))
        projected,_=projector.project_rows(rows,self.candidate)
        self.assertEqual(projected[-1],sentinel)

    def test_projection_does_not_mutate_candidate(self):
        candidate=deepcopy(self.candidate); before=deepcopy(candidate)
        projector.project_rows(self.rows(),candidate)
        self.assertEqual(candidate,before)
        self.assertFalse(candidate['coverage_adopted'])
        self.assertEqual(candidate['projection']['status'],'PROJECTION_SUCCESS_NOT_ADOPTED')
        self.assertEqual(candidate['projection']['adopted_paths'],0)


if __name__=='__main__': unittest.main()
