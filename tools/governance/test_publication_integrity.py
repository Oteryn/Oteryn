#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

MODULE_PATH = Path(__file__).with_name("publication_integrity.py")
SPEC = importlib.util.spec_from_file_location("publication_integrity", MODULE_PATH)
assert SPEC and SPEC.loader
publication = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = publication
SPEC.loader.exec_module(publication)


def git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
    )
    if result.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {result.stderr}")
    return result.stdout.strip()


class RepoFixture:
    def __init__(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.remote = self.root / "remote.git"
        self.work = self.root / "work"
        self.artifacts = self.root / "artifacts"
        self.remote.mkdir()
        self.work.mkdir()
        git(self.remote, "init", "--bare", "-q")
        git(self.work, "init", "-q")
        git(self.work, "config", "user.name", "Test")
        git(self.work, "config", "user.email", "test@example.com")
        (self.work / "state.txt").write_text("base\n", encoding="utf-8")
        git(self.work, "add", "state.txt")
        git(self.work, "commit", "-qm", "base")
        self.base = git(self.work, "rev-parse", "HEAD")
        git(self.work, "branch", "-M", "agent/test")
        git(self.work, "remote", "add", "origin", str(self.remote))
        git(self.work, "push", "-q", "origin", "agent/test")

        (self.work / "state.txt").write_text("base\nintermediate\n", encoding="utf-8")
        git(self.work, "commit", "-qam", "intermediate")
        self.intermediate = git(self.work, "rev-parse", "HEAD")
        (self.work / "state.txt").write_text("base\nintermediate\ncandidate\n", encoding="utf-8")
        git(self.work, "commit", "-qam", "candidate")
        self.candidate = git(self.work, "rev-parse", "HEAD")

    @property
    def push_url(self) -> str:
        return str(self.remote)

    def close(self) -> None:
        self.temp.cleanup()


class PublicationIntegrityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = RepoFixture()

    def tearDown(self) -> None:
        self.repo.close()

    def publish(self, bundle_name: str = "candidate.bundle") -> publication.PublicationResult:
        return publication.publish(
            self.repo.work,
            remote="origin",
            expected_push_url=self.repo.push_url,
            branch="agent/test",
            expected_remote_head=self.repo.base,
            candidate=self.repo.candidate,
            recovery_bundle=self.repo.artifacts / bundle_name,
        )

    def test_exact_candidate_fast_forward_publishes_and_bundles(self) -> None:
        bundle = self.repo.artifacts / "candidate.bundle"
        result = self.publish()
        self.assertEqual(result.state, "PUBLISHED")
        self.assertEqual(result.remote_head, self.repo.candidate)
        self.assertTrue(bundle.is_file())
        self.assertRegex(result.recovery_sha256 or "", r"^[0-9a-f]{64}$")
        self.assertEqual(
            publication.remote_head(self.repo.work, "origin", "agent/test"), self.repo.candidate
        )
        listed = git(self.repo.work, "bundle", "list-heads", str(bundle))
        self.assertIn(f"{self.repo.candidate} refs/heads/agent/test", listed)

    def test_remote_head_drift_fails_before_publication(self) -> None:
        git(self.repo.work, "checkout", "-qb", "other", self.repo.base)
        (self.repo.work / "other.txt").write_text("other\n", encoding="utf-8")
        git(self.repo.work, "add", "other.txt")
        git(self.repo.work, "commit", "-qm", "other")
        other = git(self.repo.work, "rev-parse", "HEAD")
        git(self.repo.work, "push", "-q", "origin", f"{other}:refs/heads/agent/test")
        git(self.repo.work, "checkout", "-q", "agent/test")

        with self.assertRaisesRegex(publication.PublicationError, "remote head moved"):
            self.publish()
        self.assertEqual(publication.remote_head(self.repo.work, "origin", "agent/test"), other)

    def test_non_descendant_candidate_is_rejected(self) -> None:
        git(self.repo.work, "checkout", "--orphan", "agent/unrelated")
        for path in self.repo.work.iterdir():
            if path.name == ".git":
                continue
            if path.is_file():
                path.unlink()
        (self.repo.work / "unrelated.txt").write_text("unrelated\n", encoding="utf-8")
        git(self.repo.work, "add", "-A")
        git(self.repo.work, "commit", "-qm", "unrelated")
        unrelated = git(self.repo.work, "rev-parse", "HEAD")
        git(self.repo.work, "branch", "-M", "agent/test")

        with self.assertRaisesRegex(publication.PublicationError, "not a fast-forward descendant"):
            publication.preflight(
                self.repo.work,
                remote="origin",
                expected_push_url=self.repo.push_url,
                branch="agent/test",
                expected_remote_head=self.repo.base,
                candidate=unrelated,
            )

    def test_bundle_must_live_outside_disposable_worktree(self) -> None:
        with self.assertRaisesRegex(publication.PublicationError, "outside the disposable worktree"):
            publication.create_recovery_bundle(
                self.repo.work,
                branch="agent/test",
                expected_remote_head=self.repo.base,
                candidate=self.repo.candidate,
                bundle_path=self.repo.work / "candidate.bundle",
            )

    def test_ambiguous_outcome_classification_is_readback_driven(self) -> None:
        self.assertEqual(
            publication.classify_remote_state(self.repo.candidate, self.repo.base, self.repo.candidate),
            "PUBLISHED",
        )
        self.assertEqual(
            publication.classify_remote_state(self.repo.base, self.repo.base, self.repo.candidate),
            "NOT_PUBLISHED",
        )
        third = "f" * 40
        self.assertEqual(
            publication.classify_remote_state(third, self.repo.base, self.repo.candidate),
            "REMOTE_HEAD_DRIFT",
        )

    def test_exact_candidate_already_published_is_idempotent(self) -> None:
        git(
            self.repo.work,
            "push",
            "-q",
            "origin",
            f"{self.repo.candidate}:refs/heads/agent/test",
        )
        result = self.publish("unused.bundle")
        self.assertEqual(result.state, "ALREADY_PUBLISHED")
        self.assertIsNone(result.recovery_bundle)

    def test_expected_head_lease_rejects_race_even_when_new_tip_is_candidate_ancestor(self) -> None:
        real_bundle = publication.create_recovery_bundle

        def create_bundle_then_move_remote(*args, **kwargs):
            result = real_bundle(*args, **kwargs)
            git(
                self.repo.work,
                "push",
                "-q",
                "origin",
                f"{self.repo.intermediate}:refs/heads/agent/test",
            )
            return result

        with mock.patch.object(
            publication, "create_recovery_bundle", side_effect=create_bundle_then_move_remote
        ):
            with self.assertRaisesRegex(publication.PublicationError, "third SHA"):
                self.publish()

        self.assertEqual(
            publication.remote_head(self.repo.work, "origin", "agent/test"), self.repo.intermediate
        )

    def test_push_url_mismatch_fails_closed(self) -> None:
        with self.assertRaisesRegex(publication.PublicationError, "approved publication target"):
            publication.preflight(
                self.repo.work,
                remote="origin",
                expected_push_url="/not/the/approved/remote.git",
                branch="agent/test",
                expected_remote_head=self.repo.base,
                candidate=self.repo.candidate,
            )

    def test_option_like_remote_name_is_rejected(self) -> None:
        with self.assertRaisesRegex(publication.PublicationError, "existing Git remote name"):
            publication.preflight(
                self.repo.work,
                remote="--upload-pack=evil",
                expected_push_url=self.repo.push_url,
                branch="agent/test",
                expected_remote_head=self.repo.base,
                candidate=self.repo.candidate,
            )

    def test_dirty_worktree_is_rejected_before_publication(self) -> None:
        (self.repo.work / "unpublished.txt").write_text("not in candidate\n", encoding="utf-8")
        with self.assertRaisesRegex(publication.PublicationError, "clean isolated worktree"):
            self.publish()


if __name__ == "__main__":
    unittest.main(verbosity=2)
