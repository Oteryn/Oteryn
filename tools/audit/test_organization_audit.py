#!/usr/bin/env python3
"""Offline positive/negative controls for the bounded audit collector."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import organization_audit as audit


class CollectorTest(unittest.TestCase):
    def setUp(self):
        self.plan = {"schema_version": 1, "snapshots": [{"id": "meta", "repository": "Oteryn/Oteryn",
                     "commit_sha": "a" * 40, "role": "audited_source"}]}

    def test_valid_plan(self):
        self.assertEqual(len(audit.validate_plan(self.plan)), 1)

    def test_boolean_schema_rejected(self):
        self.plan["schema_version"] = True
        with self.assertRaises(ValueError): audit.validate_plan(self.plan)

    def test_untrusted_repo_rejected(self):
        self.plan["snapshots"][0]["repository"] = "other/repo"
        with self.assertRaises(ValueError): audit.validate_plan(self.plan)

    def test_moving_ref_rejected(self):
        self.plan["snapshots"][0]["commit_sha"] = "main"
        with self.assertRaises(ValueError): audit.validate_plan(self.plan)

    def test_duplicate_snapshot_rejected(self):
        self.plan["snapshots"] *= 2
        with self.assertRaises(ValueError): audit.validate_plan(self.plan)

    def test_path_in_identifier_rejected(self):
        self.plan["snapshots"][0]["id"] = "../outside"
        with self.assertRaises(ValueError): audit.validate_plan(self.plan)

    def test_bad_tree_rejected(self):
        self.plan["snapshots"][0]["expected_tree_sha"] = "master"
        with self.assertRaises(ValueError): audit.validate_plan(self.plan)

    def test_empty_plan_rejected(self):
        self.plan["snapshots"] = []
        with self.assertRaises(ValueError): audit.validate_plan(self.plan)

    def row(self, path="a.txt", mode="100644", kind="blob"):
        return (f"{mode} {kind} {'b' * 40}\t{path}\0").encode()

    def test_nul_tree_preserves_unusual_filename(self):
        rows = audit.parse_tree(self.row("docs/a\nb\t c.md"))
        self.assertEqual(rows[0]["path"], "docs/a\nb\t c.md")
        self.assertEqual(rows[0]["disposition"], "UNVERIFIED")
        self.assertEqual(rows[0]["evidence_ids"], [])

    def test_incomplete_tree_rejected(self):
        with self.assertRaises(ValueError): audit.parse_tree(self.row()[:-1])

    def test_duplicate_path_rejected(self):
        with self.assertRaises(ValueError): audit.parse_tree(self.row() * 2)

    def test_traversal_rejected(self):
        with self.assertRaises(ValueError): audit.parse_tree(self.row("../bad"))

    def test_symlink_and_submodule_not_followed(self):
        rows = audit.parse_tree(self.row("link", "120000") + self.row("module", "160000", "commit"))
        self.assertEqual([r["type"] for r in rows], ["blob", "commit"])
        self.assertTrue(all(r["disposition"] == "UNVERIFIED" for r in rows))

    def test_unknown_mode_rejected(self):
        with self.assertRaises(ValueError): audit.parse_tree(self.row(mode="040000"))

    def test_blob_hash(self):
        self.assertEqual(audit.blob_hash(b"test content\n"), "d670460b4b4aece5915caf5c68d12f560a9fe3e4")

    def test_existing_output_rejected_without_network(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(audit, "git") as git:
            with self.assertRaises(ValueError): audit.collect(self.plan, Path(tmp))
            git.assert_not_called()

    def test_symlinked_output_ancestor_rejected_without_network_or_write(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(audit, "git") as git:
            root=Path(tmp); provider=root/'provider'; provider.mkdir()
            (root/'provider-link').symlink_to(provider, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink"):
                audit.collect(self.plan, root/'provider-link'/'deep'/'out')
            self.assertFalse((provider/'deep').exists())
            git.assert_not_called()

    def test_dangling_deep_output_ancestor_rejected_without_network(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(audit, "git") as git:
            root=Path(tmp); (root/'dangling').symlink_to(root/'missing')
            with self.assertRaisesRegex(ValueError, "symlink"):
                audit.collect(self.plan, root/'dangling'/'deep'/'out')
            self.assertFalse((root/'missing').exists())
            git.assert_not_called()

    def test_wrong_tree_aborts(self):
        self.plan["snapshots"][0]["expected_tree_sha"] = "c" * 40
        with tempfile.TemporaryDirectory() as tmp, patch.object(audit, "git", side_effect=[b"", b"", b"a"*40+b"\n", b"d"*40+b"\n"]):
            with self.assertRaisesRegex(ValueError, "expected tree mismatch"):
                audit.collect(self.plan, Path(tmp)/"out")
            self.assertFalse((Path(tmp)/"out"/"summary.json").exists())

    def test_success_does_not_claim_semantic_review(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(audit, "git", side_effect=[b"", b"", b"a"*40+b"\n", b"d"*40+b"\n", self.row()]):
            result = audit.collect(self.plan, Path(tmp)/"out")
            self.assertEqual(result["snapshots"][0]["leaf_count"], 1)
            self.assertEqual(result["snapshots"][0]["semantic_coverage"], "NOT_INFERRED")
            inventory = json.loads((Path(tmp)/"out/inventories/meta.json").read_text())
            self.assertEqual(inventory["entries"][0]["disposition"], "UNVERIFIED")


if __name__ == "__main__":
    unittest.main()
