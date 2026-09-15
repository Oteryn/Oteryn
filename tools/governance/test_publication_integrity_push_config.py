#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

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


class PublicationPushConfigurationTests(unittest.TestCase):
    def test_configured_signed_push_cannot_execute_gpg_side_publish(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            remote = root / "remote.git"
            escape = root / "escape.git"
            work = root / "work"
            artifacts = root / "artifacts"
            remote.mkdir()
            escape.mkdir()
            work.mkdir()
            git(remote, "init", "--bare", "-q")
            git(escape, "init", "--bare", "-q")
            git(remote, "config", "receive.certNonceSeed", "publication-integrity-test")

            git(work, "init", "-q")
            git(work, "config", "user.name", "Test")
            git(work, "config", "user.email", "test@example.com")
            (work / "state.txt").write_text("base\n", encoding="utf-8")
            git(work, "add", "state.txt")
            git(work, "commit", "-qm", "base")
            base = git(work, "rev-parse", "HEAD")
            git(work, "branch", "-M", "agent/test")
            git(work, "remote", "add", "origin", str(remote))
            git(work, "push", "-q", "origin", "agent/test")

            (work / "state.txt").write_text("base\ncandidate\n", encoding="utf-8")
            git(work, "commit", "-qam", "candidate")
            candidate = git(work, "rev-parse", "HEAD")

            malicious_gpg = root / "malicious-gpg.sh"
            malicious_gpg.write_text(
                "#!/bin/sh\n"
                f"git -C '{work}' push -q '{escape}' HEAD:refs/heads/agent/test\n"
                "exit 73\n",
                encoding="utf-8",
            )
            malicious_gpg.chmod(0o755)
            git(work, "config", "push.gpgSign", "true")
            git(work, "config", "gpg.program", str(malicious_gpg))

            result = publication.publish(
                work,
                remote="origin",
                expected_push_url=str(remote),
                branch="agent/test",
                expected_remote_head=base,
                candidate=candidate,
                recovery_bundle=artifacts / "candidate.bundle",
            )

            self.assertEqual(result.state, "PUBLISHED")
            self.assertEqual(
                publication.remote_head(work, str(remote), "agent/test"),
                candidate,
            )
            self.assertEqual(
                git(work, "ls-remote", "--heads", str(escape), "refs/heads/agent/test"),
                "",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
