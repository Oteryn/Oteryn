#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("publication_integrity.py")
SPEC = importlib.util.spec_from_file_location("publication_integrity_review", MODULE_PATH)
assert SPEC and SPEC.loader
publication = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = publication
SPEC.loader.exec_module(publication)


def git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {result.stderr}")
    return result.stdout.strip()


class Fixture:
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
        (self.work / "state.txt").write_text("base\ncandidate\n", encoding="utf-8")
        git(self.work, "commit", "-qam", "candidate")
        self.candidate = git(self.work, "rev-parse", "HEAD")

    @property
    def push_url(self) -> str:
        return str(self.remote)

    def extra_remote(self, name: str) -> Path:
        target = self.root / name
        target.mkdir()
        git(target, "init", "--bare", "-q")
        return target

    def publish(self, name: str = "candidate.bundle") -> publication.PublicationResult:
        return publication.publish(
            self.work,
            remote="origin",
            expected_push_url=self.push_url,
            branch="agent/test",
            expected_remote_head=self.base,
            candidate=self.candidate,
            recovery_bundle=self.artifacts / name,
        )

    def close(self) -> None:
        self.temp.cleanup()


class PublicationReviewHardeningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = Fixture()

    def tearDown(self) -> None:
        self.repo.close()

    def test_replace_ref_is_rejected_before_ancestry_can_be_trusted(self) -> None:
        git(self.repo.work, "replace", self.repo.candidate, self.repo.base)
        with self.assertRaisesRegex(publication.PublicationError, "replacement-history"):
            publication.preflight(
                self.repo.work,
                remote="origin",
                expected_push_url=self.repo.push_url,
                branch="agent/test",
                expected_remote_head=self.repo.base,
                candidate=self.repo.candidate,
            )
        self.assertEqual(
            publication.remote_head(self.repo.work, self.repo.push_url, "agent/test"),
            self.repo.base,
        )

    def test_graft_metadata_is_rejected(self) -> None:
        graft_path = Path(git(self.repo.work, "rev-parse", "--git-path", "info/grafts"))
        if not graft_path.is_absolute():
            graft_path = self.repo.work / graft_path
        graft_path.parent.mkdir(parents=True, exist_ok=True)
        graft_path.write_text(f"{self.repo.candidate} {self.repo.base}\n", encoding="utf-8")
        with self.assertRaisesRegex(publication.PublicationError, "graft-history"):
            publication.preflight(
                self.repo.work,
                remote="origin",
                expected_push_url=self.repo.push_url,
                branch="agent/test",
                expected_remote_head=self.repo.base,
                candidate=self.repo.candidate,
            )

    def test_guarded_push_bypasses_pre_push_hook(self) -> None:
        hook_path = Path(git(self.repo.work, "rev-parse", "--git-path", "hooks/pre-push"))
        if not hook_path.is_absolute():
            hook_path = self.repo.work / hook_path
        hook_path.parent.mkdir(parents=True, exist_ok=True)
        hook_path.write_text("#!/bin/sh\nexit 73\n", encoding="utf-8")
        hook_path.chmod(0o755)

        result = self.repo.publish("no-hook.bundle")
        self.assertEqual(result.state, "PUBLISHED")
        self.assertEqual(
            publication.remote_head(self.repo.work, self.repo.push_url, "agent/test"),
            self.repo.candidate,
        )

    def test_push_url_that_is_also_remote_name_fails_closed(self) -> None:
        alternate = self.repo.extra_remote("alternate.git")
        git(self.repo.work, "remote", "add", "approved", str(alternate))
        git(self.repo.work, "remote", "set-url", "--push", "origin", "approved")

        with self.assertRaisesRegex(publication.PublicationError, "also a configured Git remote name"):
            publication.preflight(
                self.repo.work,
                remote="origin",
                expected_push_url="approved",
                branch="agent/test",
                expected_remote_head=self.repo.base,
                candidate=self.repo.candidate,
            )

        self.assertEqual(
            publication.remote_head(self.repo.work, self.repo.push_url, "agent/test"),
            self.repo.base,
        )
        self.assertEqual(
            git(self.repo.work, "ls-remote", "--heads", str(alternate), "refs/heads/agent/test"),
            "",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
