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
SPEC = importlib.util.spec_from_file_location("publication_integrity_submodules", MODULE_PATH)
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

    def publish(self, name: str) -> publication.PublicationResult:
        return publication.publish(
            self.work,
            remote="origin",
            expected_push_url=self.push_url,
            branch="agent/test",
            expected_remote_head=self.base,
            candidate=self.candidate,
            recovery_bundle=self.artifacts / name,
        )

    def new_bare(self, name: str) -> Path:
        path = self.root / name
        path.mkdir()
        git(path, "init", "--bare", "-q")
        return path

    def add_unpushed_submodule_candidate(self) -> tuple[Path, str, str]:
        sub_remote = self.new_bare("submodule.git")
        source = self.root / "sub-source"
        source.mkdir()
        git(source, "init", "-q")
        git(source, "config", "user.name", "Sub")
        git(source, "config", "user.email", "sub@example.com")
        (source / "sub.txt").write_text("base\n", encoding="utf-8")
        git(source, "add", "sub.txt")
        git(source, "commit", "-qm", "sub base")
        sub_base = git(source, "rev-parse", "HEAD")
        git(source, "branch", "-M", "main")
        git(source, "remote", "add", "origin", str(sub_remote))
        git(source, "push", "-q", "-u", "origin", "main")
        git(sub_remote, "symbolic-ref", "HEAD", "refs/heads/main")

        git(
            self.work,
            "-c",
            "protocol.file.allow=always",
            "submodule",
            "add",
            "-q",
            str(sub_remote),
            "sub",
        )
        sub = self.work / "sub"
        git(sub, "config", "user.name", "Sub")
        git(sub, "config", "user.email", "sub@example.com")
        (sub / "sub.txt").write_text("base\nunpushed\n", encoding="utf-8")
        git(sub, "commit", "-qam", "sub unpushed")
        sub_candidate = git(sub, "rev-parse", "HEAD")
        git(self.work, "add", ".gitmodules", "sub")
        git(self.work, "commit", "-qm", "add submodule candidate")
        self.candidate = git(self.work, "rev-parse", "HEAD")
        return sub_remote, sub_base, sub_candidate

    def close(self) -> None:
        self.temp.cleanup()


class PublicationSubmoduleIsolationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = Fixture()

    def tearDown(self) -> None:
        self.repo.close()

    def test_initialized_submodule_is_rejected_before_filter_side_publish(self) -> None:
        sub_remote, _sub_base, _sub_candidate = self.repo.add_unpushed_submodule_candidate()
        escape = self.repo.new_bare("sub-filter-escape.git")
        sub = self.repo.work / "sub"
        (sub / ".gitattributes").write_text("sub.txt filter=escape\n", encoding="utf-8")
        git(sub, "add", ".gitattributes")
        git(sub, "commit", "-qm", "activate escape filter")
        git(self.repo.work, "add", "sub")
        git(self.repo.work, "commit", "-qm", "advance filtered submodule")
        self.repo.candidate = git(self.repo.work, "rev-parse", "HEAD")

        filter_script = self.repo.root / "sub-filter.sh"
        filter_script.write_text(
            "#!/bin/sh\n"
            f"git -C '{sub}' push -q '{escape}' HEAD:refs/heads/main\n"
            "cat\n",
            encoding="utf-8",
        )
        filter_script.chmod(0o755)
        git(sub, "config", "filter.escape.clean", str(filter_script))
        (sub / "sub.txt").touch()

        with self.assertRaisesRegex(publication.PublicationError, "submodule worktrees"):
            self.repo.publish("initialized-submodule.bundle")
        self.assertEqual(
            publication.remote_head(self.repo.work, self.repo.push_url, "agent/test"), self.repo.base
        )
        self.assertEqual(
            git(self.repo.work, "ls-remote", "--heads", str(escape), "refs/heads/main"), ""
        )
        self.assertEqual(git(self.repo.work, "ls-remote", str(sub_remote), "refs/heads/main").split()[0], _sub_base)

    def test_recurse_submodules_config_cannot_publish_after_post_preflight_init(self) -> None:
        sub_remote, sub_base, sub_candidate = self.repo.add_unpushed_submodule_candidate()
        git(self.repo.work, "submodule", "deinit", "-q", "-f", "sub")
        git(self.repo.work, "config", "push.recurseSubmodules", "on-demand")
        real_bundle = publication.create_recovery_bundle

        def bundle_then_initialize(*args, **kwargs):
            result = real_bundle(*args, **kwargs)
            git(
                self.repo.work,
                "-c",
                "protocol.file.allow=always",
                "submodule",
                "update",
                "-q",
                "--init",
                "sub",
            )
            self.assertEqual(git(self.repo.work / "sub", "rev-parse", "HEAD"), sub_candidate)
            return result

        with mock.patch.object(
            publication, "create_recovery_bundle", side_effect=bundle_then_initialize
        ):
            result = self.repo.publish("no-recursive-push.bundle")

        self.assertEqual(result.state, "PUBLISHED")
        remote_sub_head = git(self.repo.work, "ls-remote", str(sub_remote), "refs/heads/main").split()[0]
        self.assertEqual(remote_sub_head, sub_base)
        self.assertNotEqual(remote_sub_head, sub_candidate)

    def test_follow_tags_config_cannot_publish_annotated_tag(self) -> None:
        tag = "publication-side-tag"
        git(self.repo.work, "tag", "-a", tag, "-m", "must not publish", self.repo.candidate)
        git(self.repo.work, "config", "push.followTags", "true")

        result = self.repo.publish("no-follow-tags.bundle")
        self.assertEqual(result.state, "PUBLISHED")
        self.assertEqual(
            git(self.repo.work, "ls-remote", "--tags", self.repo.push_url, f"refs/tags/{tag}"), ""
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
