#!/usr/bin/env python3
"""Adversarial tests for the Announcements projection-only transform."""
from copy import deepcopy
import errno
from pathlib import Path
import tempfile
import unittest
from unittest import mock

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

    def test_outputs_are_created_exclusively(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); ledger=root/'projected.csv'; overlay=root/'overlay.tsv'
            projector.write_outputs_exclusive(ledger,b'ledger',overlay,b'overlay')
            self.assertEqual(ledger.read_bytes(),b'ledger')
            self.assertEqual(overlay.read_bytes(),b'overlay')

    def test_existing_and_final_symlink_destinations_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); existing=root/'existing'; existing.write_bytes(b'preserve')
            other=root/'other'; dangling=root/'dangling'; dangling.symlink_to(root/'missing')
            for bad in (existing,dangling):
                with self.assertRaises((FileExistsError, ValueError)):
                    projector.write_outputs_exclusive(bad,b'ledger',other,b'overlay')
                self.assertEqual(existing.read_bytes(),b'preserve')
                self.assertFalse(other.exists())
            with self.assertRaises(FileExistsError):
                projector.write_outputs_exclusive(other,b'ledger',existing,b'overlay')
            self.assertFalse(other.exists()); self.assertEqual(existing.read_bytes(),b'preserve')

    def test_symlinked_ancestor_destinations_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); target=root/'target'; target.mkdir(); link=root/'link'; link.symlink_to(target, target_is_directory=True)
            with self.assertRaises(OSError):
                projector.write_outputs_exclusive(link/'projected',b'ledger',root/'overlay',b'overlay')
            self.assertFalse((target/'projected').exists()); self.assertFalse((root/'overlay').exists())
            dangling=root/'dangling-parent'; dangling.symlink_to(root/'missing-parent', target_is_directory=True)
            with self.assertRaises(OSError):
                projector.write_outputs_exclusive(root/'projected',b'ledger',dangling/'deeper'/'overlay',b'overlay')
            self.assertFalse((root/'projected').exists()); self.assertFalse((root/'missing-parent').exists())

    def test_output_aliases_are_rejected_without_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); input_path=root/'canonical.csv'; input_path.write_bytes(b'input')
            candidate_path=root/'candidate.json'; candidate_path.write_bytes(b'candidate')
            for first, second in ((root/'same',root/'same'),(input_path,root/'overlay'),(root/'ledger',candidate_path)):
                with self.assertRaisesRegex(ValueError,'alias'):
                    projector.write_outputs_exclusive(first,b'ledger',second,b'overlay',(input_path,candidate_path))
            self.assertEqual(input_path.read_bytes(),b'input'); self.assertEqual(candidate_path.read_bytes(),b'candidate')

    def test_second_output_failure_rolls_back_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); first=root/'first'; second=root/'second'
            real=projector._exclusive_create
            calls=0
            def fail_second(path):
                nonlocal calls
                calls += 1
                if calls == 2: raise OSError('simulated second create failure')
                return real(path)
            with mock.patch.object(projector,'_exclusive_create',side_effect=fail_second):
                with self.assertRaisesRegex(OSError,'simulated'):
                    projector.write_outputs_exclusive(first,b'ledger',second,b'overlay')
            self.assertFalse(first.exists()); self.assertFalse(second.exists())

    def test_second_output_write_failure_removes_both_new_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); first=root/'first'; second=root/'second'
            with mock.patch.object(projector.os,'fsync',side_effect=[None,OSError('simulated write failure')]):
                with self.assertRaisesRegex(OSError,'simulated'):
                    projector.write_outputs_exclusive(first,b'ledger',second,b'overlay')
            self.assertFalse(first.exists()); self.assertFalse(second.exists())

    def test_rollback_preserves_replacement_of_first_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); first=root/'first'; renamed=root/'renamed'; second=root/'second'
            calls=0
            def replace_first_then_fail(_fd):
                nonlocal calls
                calls += 1
                if calls == 2:
                    first.rename(renamed)
                    first.write_bytes(b'unrelated replacement')
                    raise OSError('simulated write failure after replacement')
            with mock.patch.object(projector.os,'fsync',side_effect=replace_first_then_fail):
                with self.assertRaisesRegex(OSError,'simulated write failure after replacement'):
                    projector.write_outputs_exclusive(first,b'ledger',second,b'overlay')
            self.assertEqual(first.read_bytes(),b'unrelated replacement')
            self.assertEqual(renamed.read_bytes(),b'ledger')
            self.assertFalse(second.exists())

    def test_rollback_atomically_captures_replacement_before_ownership_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); first=root/'first'; renamed=root/'renamed'; second=root/'second'
            real_rename=projector._rename_noreplace
            attacked=False
            def replace_immediately_before_capture(old_name,new_name,parent_fd):
                nonlocal attacked
                if old_name == 'first' and not attacked:
                    attacked=True
                    first.rename(renamed)
                    first.write_bytes(b'unrelated replacement')
                return real_rename(old_name,new_name,parent_fd)
            with mock.patch.object(projector.os,'fsync',side_effect=[None,OSError('simulated second fsync failure')]), \
                 mock.patch.object(projector,'_rename_noreplace',side_effect=replace_immediately_before_capture):
                with self.assertRaisesRegex(OSError,'simulated second fsync failure'):
                    projector.write_outputs_exclusive(first,b'ledger',second,b'overlay')
            self.assertTrue(attacked)
            self.assertEqual(first.read_bytes(),b'unrelated replacement')
            self.assertEqual(renamed.read_bytes(),b'ledger')
            self.assertFalse(second.exists())

    def test_ownership_check_interception_cannot_replace_captured_pathname(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); first=root/'first'; second=root/'second'
            real_stat=projector.os.stat
            attacked=False
            def replace_active_name_after_check(path,*args,**kwargs):
                nonlocal attacked
                observed=real_stat(path,*args,**kwargs)
                if isinstance(path,str) and path.startswith('.first.rollback-') and not attacked:
                    attacked=True
                    # The tool-owned inode has already been atomically captured
                    # under ``path``.  Reusing the published name now must not
                    # expose these unrelated bytes to the subsequent unlink.
                    first.write_bytes(b'unrelated replacement')
                return observed
            with mock.patch.object(projector.os,'fsync',side_effect=[None,OSError('simulated second fsync failure')]), \
                 mock.patch.object(projector.os,'stat',side_effect=replace_active_name_after_check):
                with self.assertRaisesRegex(OSError,'simulated second fsync failure'):
                    projector.write_outputs_exclusive(first,b'ledger',second,b'overlay')
            self.assertTrue(attacked)
            self.assertEqual(first.read_bytes(),b'unrelated replacement')
            self.assertFalse(second.exists())
            self.assertEqual(list(root.glob('.first.rollback-*')),[])

    def test_quarantine_name_collision_is_retried(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); first=root/'first'; second=root/'second'
            real_rename=projector._rename_noreplace
            collisions=0
            def collide_once(old_name,new_name,parent_fd):
                nonlocal collisions
                if old_name == 'first' and collisions == 0:
                    collisions += 1
                    raise FileExistsError(errno.EEXIST,'collision')
                return real_rename(old_name,new_name,parent_fd)
            with mock.patch.object(projector.os,'fsync',side_effect=[None,OSError('simulated second fsync failure')]), \
                 mock.patch.object(projector,'_rename_noreplace',side_effect=collide_once):
                with self.assertRaisesRegex(OSError,'simulated second fsync failure'):
                    projector.write_outputs_exclusive(first,b'ledger',second,b'overlay')
            self.assertEqual(collisions,1)
            self.assertFalse(first.exists()); self.assertFalse(second.exists())


if __name__=='__main__': unittest.main()
