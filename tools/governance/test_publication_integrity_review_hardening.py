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

    def activate_filter(self, driver: str) -> None:
        (self.work / ".gitattributes").write_text(
            f"state.txt filter={driver}\n",
            encoding="utf-8",
        )
        git(self.work, "add", ".gitattributes")
        git(self.work, "commit", "-qm", f"activate {driver} filter")
        self.candidate = git(self.work, "rev-parse", "HEAD")

    def add_nested_candidate(self) -> Path:
        nested = self.work / "nested"
        nested.mkdir()
        (nested / "anchor.txt").write_text("anchor\n", encoding="utf-8")
        git(self.work, "add", "nested/anchor.txt")
        git(self.work, "commit", "-qm", "add nested publication cwd")
        self.candidate = git(self.work, "rev-parse", "HEAD")
        return nested

    def close(self) -> None:
        self.temp.cleanup()


class PublicationReviewHardeningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = Fixture()

    def tearDown(self) -> None:
        self.repo.close()

    def test_replace_ref_cannot_fake_fast_forward_with_clean_same_tree(self) -> None:
        tree = git(self.repo.work, "rev-parse", f"{self.repo.candidate}^{{tree}}")
        orphan = git(self.repo.work, "commit-tree", tree, "-m", "orphan candidate")
        git(self.repo.work, "reset", "--hard", orphan)
        forged = git(
            self.repo.work,
            "commit-tree",
            tree,
            "-p",
            self.repo.base,
            "-m",
            "forged replacement ancestry",
        )
        git(self.repo.work, "replace", orphan, forged)
        self.assertEqual(git(self.repo.work, "status", "--porcelain=v1", "--untracked-files=all"), "")

        with self.assertRaisesRegex(publication.PublicationError, "replacement-history"):
            publication.preflight(
                self.repo.work,
                remote="origin",
                expected_push_url=self.repo.push_url,
                branch="agent/test",
                expected_remote_head=self.repo.base,
                candidate=orphan,
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

    def test_clean_check_disables_repository_fsmonitor_hook(self) -> None:
        escape = self.repo.extra_remote("fsmonitor-escape.git")
        hook_path = self.repo.root / "fsmonitor-hook.sh"
        hook_path.write_text(
            "#!/bin/sh\n"
            f"git -C '{self.repo.work}' push -q '{escape}' HEAD:refs/heads/agent/test\n"
            "exit 73\n",
            encoding="utf-8",
        )
        hook_path.chmod(0o755)
        git(self.repo.work, "config", "core.fsmonitor", str(hook_path))

        result = self.repo.publish("fsmonitor-disabled.bundle")
        self.assertEqual(result.state, "PUBLISHED")
        self.assertEqual(
            publication.remote_head(self.repo.work, self.repo.push_url, "agent/test"),
            self.repo.candidate,
        )
        self.assertEqual(
            git(self.repo.work, "ls-remote", "--heads", str(escape), "refs/heads/agent/test"),
            "",
        )

    def test_clean_check_disables_post_index_change_hook(self) -> None:
        escape = self.repo.extra_remote("index-hook-escape.git")
        hook_path = Path(git(self.repo.work, "rev-parse", "--git-path", "hooks/post-index-change"))
        if not hook_path.is_absolute():
            hook_path = self.repo.work / hook_path
        hook_path.parent.mkdir(parents=True, exist_ok=True)
        hook_path.write_text(
            "#!/bin/sh\n"
            f"git -C '{self.repo.work}' push -q '{escape}' HEAD:refs/heads/agent/test\n"
            "exit 0\n",
            encoding="utf-8",
        )
        hook_path.chmod(0o755)
        (self.repo.work / "state.txt").touch()

        result = self.repo.publish("post-index-disabled.bundle")
        self.assertEqual(result.state, "PUBLISHED")
        self.assertEqual(
            publication.remote_head(self.repo.work, self.repo.push_url, "agent/test"),
            self.repo.candidate,
        )
        self.assertEqual(
            git(self.repo.work, "ls-remote", "--heads", str(escape), "refs/heads/agent/test"),
            "",
        )

    def test_skip_worktree_hidden_change_is_rejected_before_publication(self) -> None:
        git(self.repo.work, "update-index", "--skip-worktree", "state.txt")
        (self.repo.work / "state.txt").write_text("hidden local bytes\n", encoding="utf-8")

        with self.assertRaisesRegex(publication.PublicationError, "skip-worktree/assume-unchanged"):
            self.repo.publish("skip-worktree.bundle")
        self.assertEqual(
            publication.remote_head(self.repo.work, self.repo.push_url, "agent/test"),
            self.repo.base,
        )
        self.assertFalse((self.repo.artifacts / "skip-worktree.bundle").exists())

    def test_assume_unchanged_hidden_change_is_rejected_before_publication(self) -> None:
        git(self.repo.work, "update-index", "--assume-unchanged", "state.txt")
        (self.repo.work / "state.txt").write_text("hidden assumed bytes\n", encoding="utf-8")

        with self.assertRaisesRegex(publication.PublicationError, "skip-worktree/assume-unchanged"):
            self.repo.publish("assume-unchanged.bundle")
        self.assertEqual(
            publication.remote_head(self.repo.work, self.repo.push_url, "agent/test"),
            self.repo.base,
        )
        self.assertFalse((self.repo.artifacts / "assume-unchanged.bundle").exists())

    def test_executable_clean_filter_is_rejected_before_side_publish(self) -> None:
        escape = self.repo.extra_remote("clean-filter-escape.git")
        self.repo.activate_filter("escape")

        filter_path = self.repo.root / "clean-filter.sh"
        filter_path.write_text(
            "#!/bin/sh\n"
            f"git -C '{self.repo.work}' push -q '{escape}' HEAD:refs/heads/agent/test\n"
            "cat\n",
            encoding="utf-8",
        )
        filter_path.chmod(0o755)
        git(self.repo.work, "config", "filter.escape.clean", str(filter_path))
        (self.repo.work / "state.txt").touch()

        with self.assertRaisesRegex(publication.PublicationError, "clean/process filters"):
            self.repo.publish("clean-filter.bundle")
        self.assertEqual(
            publication.remote_head(self.repo.work, self.repo.push_url, "agent/test"),
            self.repo.base,
        )
        self.assertEqual(
            git(self.repo.work, "ls-remote", "--heads", str(escape), "refs/heads/agent/test"),
            "",
        )
        self.assertFalse((self.repo.artifacts / "clean-filter.bundle").exists())

    def test_active_process_filter_configuration_is_rejected_before_publication(self) -> None:
        self.repo.activate_filter("escape")
        git(self.repo.work, "config", "filter.escape.process", "false")
        with self.assertRaisesRegex(publication.PublicationError, "clean/process filters"):
            self.repo.publish("process-filter.bundle")
        self.assertEqual(
            publication.remote_head(self.repo.work, self.repo.push_url, "agent/test"),
            self.repo.base,
        )
        self.assertFalse((self.repo.artifacts / "process-filter.bundle").exists())

    def test_inactive_executable_filter_configuration_does_not_block(self) -> None:
        git(self.repo.work, "config", "filter.unused.clean", "false")
        git(self.repo.work, "config", "filter.unused.process", "false")

        result = self.repo.publish("inactive-filter.bundle")
        self.assertEqual(result.state, "PUBLISHED")
        self.assertEqual(
            publication.remote_head(self.repo.work, self.repo.push_url, "agent/test"),
            self.repo.candidate,
        )

    def test_subdirectory_cwd_rejects_repo_wide_active_filter_before_side_publish(self) -> None:
        nested = self.repo.add_nested_candidate()
        escape = self.repo.extra_remote("subdir-filter-escape.git")
        self.repo.activate_filter("escape")

        filter_path = self.repo.root / "subdir-clean-filter.sh"
        filter_path.write_text(
            "#!/bin/sh\n"
            f"git -C '{self.repo.work}' push -q '{escape}' HEAD:refs/heads/agent/test\n"
            "cat\n",
            encoding="utf-8",
        )
        filter_path.chmod(0o755)
        git(self.repo.work, "config", "filter.escape.clean", str(filter_path))
        (self.repo.work / "state.txt").touch()

        bundle = self.repo.artifacts / "subdir-filter.bundle"
        with self.assertRaisesRegex(publication.PublicationError, "clean/process filters"):
            publication.publish(
                nested,
                remote="origin",
                expected_push_url=self.repo.push_url,
                branch="agent/test",
                expected_remote_head=self.repo.base,
                candidate=self.repo.candidate,
                recovery_bundle=bundle,
            )
        self.assertEqual(
            publication.remote_head(self.repo.work, self.repo.push_url, "agent/test"), self.repo.base
        )
        self.assertEqual(
            git(self.repo.work, "ls-remote", "--heads", str(escape), "refs/heads/agent/test"), ""
        )
        self.assertFalse(bundle.exists())

    def test_subdirectory_cwd_rejects_repo_wide_hidden_index_state(self) -> None:
        nested = self.repo.add_nested_candidate()
        git(self.repo.work, "update-index", "--skip-worktree", "state.txt")
        (self.repo.work / "state.txt").write_text("hidden sibling bytes\n", encoding="utf-8")

        bundle = self.repo.artifacts / "subdir-hidden-index.bundle"
        with self.assertRaisesRegex(publication.PublicationError, "skip-worktree/assume-unchanged"):
            publication.publish(
                nested,
                remote="origin",
                expected_push_url=self.repo.push_url,
                branch="agent/test",
                expected_remote_head=self.repo.base,
                candidate=self.repo.candidate,
                recovery_bundle=bundle,
            )
        self.assertEqual(
            publication.remote_head(self.repo.work, self.repo.push_url, "agent/test"), self.repo.base
        )
        self.assertFalse(bundle.exists())

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

    def _prepare_literal_approved_endpoint(self) -> Path:
        git_dir = Path(git(self.repo.work, "rev-parse", "--git-dir"))
        if not git_dir.is_absolute():
            git_dir = self.repo.work / git_dir
        exclude = git_dir / "info" / "exclude"
        exclude.parent.mkdir(parents=True, exist_ok=True)
        with exclude.open("a", encoding="utf-8") as handle:
            handle.write("approved/\n")

        approved = self.repo.work / "approved"
        approved.mkdir()
        git(approved, "init", "--bare", "-q")
        git(
            self.repo.work,
            "push",
            "-q",
            str(approved),
            f"{self.repo.base}:refs/heads/agent/test",
        )
        git(self.repo.work, "remote", "set-url", "--push", "origin", "approved")
        return approved

    def _assert_legacy_alias_blocked(self, bundle_name: str, approved: Path, escape: Path) -> None:
        bundle = self.repo.artifacts / bundle_name
        with self.assertRaisesRegex(publication.PublicationError, "legacy remote alias"):
            publication.publish(
                self.repo.work,
                remote="origin",
                expected_push_url="approved",
                branch="agent/test",
                expected_remote_head=self.repo.base,
                candidate=self.repo.candidate,
                recovery_bundle=bundle,
            )
        self.assertEqual(
            publication.remote_head(self.repo.work, str(approved), "agent/test"), self.repo.base
        )
        self.assertEqual(
            git(self.repo.work, "ls-remote", "--heads", str(escape), "refs/heads/agent/test"), ""
        )
        self.assertFalse(bundle.exists())
        self.assertFalse(bundle.with_name(bundle.name + ".tmp").exists())

    def test_legacy_remotes_alias_cannot_redirect_approved_endpoint(self) -> None:
        approved = self._prepare_literal_approved_endpoint()
        escape = self.repo.extra_remote("legacy-remotes-escape.git")
        git_dir = Path(git(self.repo.work, "rev-parse", "--git-dir"))
        if not git_dir.is_absolute():
            git_dir = self.repo.work / git_dir
        alias = git_dir / "remotes" / "approved"
        alias.parent.mkdir(parents=True, exist_ok=True)
        alias.write_text(
            f"URL: {escape}\nPush: refs/heads/*:refs/heads/*\n",
            encoding="utf-8",
        )

        self._assert_legacy_alias_blocked("legacy-remotes.bundle", approved, escape)

    def test_legacy_branches_alias_symlink_cannot_redirect_approved_endpoint(self) -> None:
        approved = self._prepare_literal_approved_endpoint()
        escape = self.repo.extra_remote("legacy-branches-escape.git")
        git_dir = Path(git(self.repo.work, "rev-parse", "--git-dir"))
        if not git_dir.is_absolute():
            git_dir = self.repo.work / git_dir
        alias_target = self.repo.root / "legacy-branch-alias.txt"
        alias_target.write_text(f"{escape}#agent/test\n", encoding="utf-8")
        alias = git_dir / "branches" / "approved"
        alias.parent.mkdir(parents=True, exist_ok=True)
        alias.symlink_to(alias_target)

        self._assert_legacy_alias_blocked("legacy-branches.bundle", approved, escape)

    def test_post_push_alias_creation_cannot_supply_success_readback(self) -> None:
        approved = self._prepare_literal_approved_endpoint()
        escape = self.repo.extra_remote("post-push-alias-escape.git")
        git(
            self.repo.work,
            "push",
            "-q",
            str(escape),
            f"{self.repo.candidate}:refs/heads/agent/test",
        )

        hook = approved / "hooks" / "pre-receive"
        hook.write_text(
            "#!/bin/sh\n"
            "unset GIT_DIR GIT_WORK_TREE\n"
            f"git -C '{self.repo.work}' remote add approved '{escape}'\n"
            "exit 73\n",
            encoding="utf-8",
        )
        hook.chmod(0o755)

        bundle = self.repo.artifacts / "post-push-alias.bundle"
        with self.assertRaisesRegex(publication.PublicationError, "ambiguous publication outcome"):
            publication.publish(
                self.repo.work,
                remote="origin",
                expected_push_url="approved",
                branch="agent/test",
                expected_remote_head=self.repo.base,
                candidate=self.repo.candidate,
                recovery_bundle=bundle,
            )

        self.assertEqual(
            publication.remote_head(self.repo.work, str(approved), "agent/test"), self.repo.base
        )
        self.assertEqual(
            publication.remote_head(self.repo.work, str(escape), "agent/test"), self.repo.candidate
        )
        self.assertTrue(bundle.exists())
        self.assertFalse(bundle.with_name(bundle.name + ".tmp").exists())

    def test_post_push_filesystem_symlink_swap_cannot_supply_success_readback(self) -> None:
        approved = self._prepare_literal_approved_endpoint()
        escape = self.repo.extra_remote("post-push-symlink-escape.git")
        git(
            self.repo.work,
            "push",
            "-q",
            str(escape),
            f"{self.repo.candidate}:refs/heads/agent/test",
        )
        original = self.repo.root / "approved-original.git"

        hook = approved / "hooks" / "pre-receive"
        hook.write_text(
            "#!/bin/sh\n"
            "unset GIT_DIR GIT_WORK_TREE\n"
            f"mv '{approved}' '{original}'\n"
            f"ln -s '{escape}' '{approved}'\n"
            "exit 73\n",
            encoding="utf-8",
        )
        hook.chmod(0o755)

        bundle = self.repo.artifacts / "post-push-symlink.bundle"
        with self.assertRaisesRegex(publication.PublicationError, "ambiguous publication outcome"):
            publication.publish(
                self.repo.work,
                remote="origin",
                expected_push_url="approved",
                branch="agent/test",
                expected_remote_head=self.repo.base,
                candidate=self.repo.candidate,
                recovery_bundle=bundle,
            )

        self.assertTrue(approved.is_symlink())
        self.assertEqual(
            publication.remote_head(self.repo.work, str(original), "agent/test"), self.repo.base
        )
        self.assertEqual(
            publication.remote_head(self.repo.work, str(escape), "agent/test"), self.repo.candidate
        )
        self.assertTrue(bundle.exists())
        self.assertFalse(bundle.with_name(bundle.name + ".tmp").exists())

    def test_file_url_authority_cannot_bypass_local_identity_binding(self) -> None:
        approved = self.repo.remote
        endpoint = f"file://ignored-host{approved}"
        git(self.repo.work, "remote", "set-url", "origin", endpoint)
        bundle = self.repo.artifacts / "file-authority.bundle"

        with self.assertRaisesRegex(publication.PublicationError, "file URL authority"):
            publication.publish(
                self.repo.work,
                remote="origin",
                expected_push_url=endpoint,
                branch="agent/test",
                expected_remote_head=self.repo.base,
                candidate=self.repo.candidate,
                recovery_bundle=bundle,
            )

        self.assertEqual(
            publication.remote_head(self.repo.work, str(approved), "agent/test"), self.repo.base
        )
        self.assertFalse(bundle.exists())
        self.assertFalse(bundle.with_name(bundle.name + ".tmp").exists())

    def test_readback_path_replacement_during_ls_remote_is_ambiguous(self) -> None:
        approved = self._prepare_literal_approved_endpoint()
        escape = self.repo.extra_remote("readback-boundary-escape.git")
        git(
            self.repo.work,
            "push",
            "-q",
            str(escape),
            f"{self.repo.candidate}:refs/heads/agent/test",
        )
        original = self.repo.root / "readback-boundary-original.git"
        hook = approved / "hooks" / "pre-receive"
        hook.write_text("#!/bin/sh\nexit 73\n", encoding="utf-8")
        hook.chmod(0o755)
        bundle = self.repo.artifacts / "readback-boundary.bundle"
        real_run_git = publication._run_git
        replaced = False

        def replace_at_readback(cwd: Path, *args: str, **kwargs):
            nonlocal replaced
            if (
                not replaced
                and args
                and args[0] == "ls-remote"
                and any(value.startswith("/proc/self/fd/") for value in args)
            ):
                approved.rename(original)
                approved.symlink_to(escape)
                replaced = True
            return real_run_git(cwd, *args, **kwargs)

        with mock.patch.object(publication, "_run_git", side_effect=replace_at_readback):
            with self.assertRaisesRegex(publication.PublicationError, "ambiguous publication outcome"):
                publication.publish(
                    self.repo.work,
                    remote="origin",
                    expected_push_url="approved",
                    branch="agent/test",
                    expected_remote_head=self.repo.base,
                    candidate=self.repo.candidate,
                    recovery_bundle=bundle,
                )

        self.assertTrue(replaced)
        self.assertEqual(
            publication.remote_head(self.repo.work, str(original), "agent/test"), self.repo.base
        )
        self.assertEqual(
            publication.remote_head(self.repo.work, str(escape), "agent/test"), self.repo.candidate
        )
        self.assertTrue(bundle.exists())
        self.assertFalse(bundle.with_name(bundle.name + ".tmp").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
