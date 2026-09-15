#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

MODULE_PATH = Path(__file__).with_name("publication_integrity.py")
SPEC = importlib.util.spec_from_file_location("publication_integrity_push_config", MODULE_PATH)
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
        self.escape = self.root / "escape.git"
        self.work = self.root / "work"
        self.artifacts = self.root / "artifacts"
        self.remote.mkdir()
        self.escape.mkdir()
        self.work.mkdir()
        git(self.remote, "init", "--bare", "-q")
        git(self.escape, "init", "--bare", "-q")
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

    def malicious_script(self, name: str) -> Path:
        script = self.root / name
        script.write_text(
            "#!/bin/sh\n"
            f"git -C '{self.work}' push -q '{self.escape}' HEAD:refs/heads/agent/test\n"
            "exit 73\n",
            encoding="utf-8",
        )
        script.chmod(0o755)
        return script

    def publish(self, bundle_name: str) -> publication.PublicationResult:
        return publication.publish(
            self.work,
            remote="origin",
            expected_push_url=str(self.remote),
            branch="agent/test",
            expected_remote_head=self.base,
            candidate=self.candidate,
            recovery_bundle=self.artifacts / bundle_name,
        )

    def raw_remote_head(self) -> str:
        return git(self.work, "ls-remote", "--heads", str(self.remote), "refs/heads/agent/test").split()[0]

    def raw_escape_head(self) -> str:
        output = git(self.work, "ls-remote", "--heads", str(self.escape), "refs/heads/agent/test")
        return output.split()[0] if output else ""

    def close(self) -> None:
        self.temp.cleanup()


class PublicationPushConfigurationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = Fixture()

    def tearDown(self) -> None:
        self.repo.close()

    def assert_credential_helper_blocked(self, bundle_name: str) -> None:
        bundle = self.repo.artifacts / bundle_name
        with self.assertRaisesRegex(publication.PublicationError, "credential helpers"):
            self.repo.publish(bundle_name)
        self.assertEqual(self.repo.raw_remote_head(), self.repo.base)
        self.assertEqual(self.repo.raw_escape_head(), "")
        self.assertFalse(bundle.exists())

    def test_configured_signed_push_cannot_execute_gpg_side_publish(self) -> None:
        git(self.repo.remote, "config", "receive.certNonceSeed", "publication-integrity-test")
        malicious_gpg = self.repo.malicious_script("malicious-gpg.sh")
        git(self.repo.work, "config", "push.gpgSign", "true")
        git(self.repo.work, "config", "gpg.program", str(malicious_gpg))

        result = self.repo.publish("signed-push.bundle")

        self.assertEqual(result.state, "PUBLISHED")
        self.assertEqual(self.repo.raw_remote_head(), self.repo.candidate)
        self.assertEqual(self.repo.raw_escape_head(), "")

    def test_local_shell_credential_helper_is_rejected_before_readback(self) -> None:
        helper = self.repo.malicious_script("credential-helper.sh")
        git(self.repo.work, "config", "--local", "credential.helper", f"!{helper}")
        self.assert_credential_helper_blocked("local-helper.bundle")

    def test_local_include_credential_helper_is_rejected_before_readback(self) -> None:
        helper = self.repo.malicious_script("included-credential-helper.sh")
        included = self.repo.root / "repo-credential.cfg"
        included.write_text(
            "[credential]\n"
            f"\thelper = !{helper}\n",
            encoding="utf-8",
        )
        git(self.repo.work, "config", "--local", "include.path", str(included))
        self.assert_credential_helper_blocked("included-helper.bundle")

    def test_worktree_credential_helper_is_rejected_before_readback(self) -> None:
        helper = self.repo.malicious_script("worktree-credential-helper.sh")
        git(self.repo.work, "config", "extensions.worktreeConfig", "true")
        git(self.repo.work, "config", "--worktree", "credential.helper", f"!{helper}")
        self.assert_credential_helper_blocked("worktree-helper.bundle")

    def test_global_credential_helper_configuration_is_not_rejected(self) -> None:
        global_config = self.repo.root / "trusted-global.cfg"
        global_config.write_text("[credential]\n\thelper = false\n", encoding="utf-8")
        with mock.patch.dict(os.environ, {"GIT_CONFIG_GLOBAL": str(global_config)}, clear=False):
            result = self.repo.publish("global-helper.bundle")

        self.assertEqual(result.state, "PUBLISHED")
        self.assertEqual(self.repo.raw_remote_head(), self.repo.candidate)
        self.assertEqual(self.repo.raw_escape_head(), "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
