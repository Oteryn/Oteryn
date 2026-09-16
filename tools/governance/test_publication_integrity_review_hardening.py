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

    def test_mutation_binding_rejects_endpoint_swapped_to_linked_worktree(self) -> None:
        approved = self.repo.remote
        original = self.repo.root / "approved-original.git"
        common = self.repo.root / "linked-common"
        git(self.repo.root, "clone", "-q", str(approved), str(common))
        escape = self.repo.extra_remote("mutation-linked-escape.git")
        git(
            self.repo.work,
            "push",
            "-q",
            str(escape),
            f"{self.repo.base}:refs/heads/agent/test",
        )
        bundle = self.repo.artifacts / "mutation-linked-swap.bundle"
        real_create_bundle = publication.create_recovery_bundle
        real_run_git = publication._run_git
        push_reached = False

        def swap_after_bundle(*args, **kwargs):
            result = real_create_bundle(*args, **kwargs)
            approved.rename(original)
            git(
                common,
                "worktree",
                "add",
                "--detach",
                str(approved),
                self.repo.base,
            )
            return result

        def observe_push(cwd: Path, *args: str, **kwargs):
            nonlocal push_reached
            if "push" in args:
                push_reached = True
            return real_run_git(cwd, *args, **kwargs)

        with (
            mock.patch.object(
                publication, "create_recovery_bundle", side_effect=swap_after_bundle
            ),
            mock.patch.object(publication, "_run_git", side_effect=observe_push),
        ):
            with self.assertRaisesRegex(
                publication.PublicationError,
                "linked-worktree local publication targets are not supported",
            ):
                self.repo.publish("mutation-linked-swap.bundle")

        self.assertFalse(push_reached)
        self.assertEqual(git(original, "rev-parse", "refs/heads/agent/test"), self.repo.base)
        self.assertEqual(git(escape, "rev-parse", "refs/heads/agent/test"), self.repo.base)
        self.assertTrue(bundle.exists())

    def test_preflight_rejects_replacement_endpoint_candidate_evidence(self) -> None:
        approved = self.repo.remote
        original = self.repo.root / "preflight-approved-original.git"
        replacement = self.repo.root / "preflight-replacement.git"
        git(self.repo.root, "clone", "-q", "--bare", str(approved), str(replacement))
        git(
            self.repo.work,
            "push",
            "-q",
            str(replacement),
            f"{self.repo.candidate}:refs/heads/agent/test",
        )
        bundle = self.repo.artifacts / "preflight-endpoint-swap.bundle"
        real_endpoint = publication._remote_push_endpoint
        endpoint_resolutions = 0
        swapped = False

        def swap_only_for_preflight(*args, **kwargs):
            nonlocal endpoint_resolutions, swapped
            endpoint_resolutions += 1
            if endpoint_resolutions == 2:
                approved.rename(original)
                replacement.rename(approved)
                swapped = True
            return real_endpoint(*args, **kwargs)

        try:
            with mock.patch.object(
                publication, "_remote_push_endpoint", side_effect=swap_only_for_preflight
            ):
                with self.assertRaisesRegex(
                    publication.PublicationError,
                    "endpoint identity changed before preflight readback",
                ):
                    self.repo.publish("preflight-endpoint-swap.bundle")
        finally:
            if swapped:
                approved.rename(replacement)
                original.rename(approved)

        self.assertTrue(swapped)
        self.assertEqual(git(approved, "rev-parse", "refs/heads/agent/test"), self.repo.base)
        self.assertEqual(
            git(replacement, "rev-parse", "refs/heads/agent/test"), self.repo.candidate
        )
        self.assertFalse(bundle.exists())
        self.assertFalse(bundle.with_name(bundle.name + ".tmp").exists())

    def test_loose_ref_in_place_restore_during_classification_is_rejected(self) -> None:
        approved = self.repo.root / "loose-in-place.git"
        git(self.repo.root, "clone", "-q", "--bare", str(self.repo.remote), str(approved))
        git(approved, "fetch", "-q", str(self.repo.work), self.repo.candidate)
        git(self.repo.work, "remote", "set-url", "origin", str(approved))
        loose_ref = approved / "refs" / "heads" / "agent" / "test"
        loose_ref.parent.mkdir(parents=True, exist_ok=True)
        loose_ref.write_text(f"{self.repo.base}\n", encoding="ascii")
        self.assertTrue(loose_ref.is_file())
        predecessor_contents = loose_ref.read_bytes()
        candidate_contents = f"{self.repo.candidate}\n".encode("ascii")
        original_inode = loose_ref.stat().st_ino
        real_run_git = publication._run_git
        real_classify = publication.classify_remote_state
        candidate_exposed = False

        def expose_candidate_in_place(cwd: Path, *args: str, **kwargs):
            nonlocal candidate_exposed
            if (
                not candidate_exposed
                and args
                and args[0] == "ls-remote"
                and "/proc/self/fd/" in args[-2]
            ):
                candidate_exposed = True
                loose_ref.write_bytes(candidate_contents)
                self.assertEqual(loose_ref.stat().st_ino, original_inode)
            return real_run_git(cwd, *args, **kwargs)

        def restore_predecessor_in_place(remote: str, expected: str, candidate: str) -> str:
            loose_ref.write_bytes(predecessor_contents)
            self.assertEqual(loose_ref.stat().st_ino, original_inode)
            return real_classify(remote, expected, candidate)

        with (
            mock.patch.object(publication, "_run_git", side_effect=expose_candidate_in_place),
            mock.patch.object(
                publication,
                "classify_remote_state",
                side_effect=restore_predecessor_in_place,
            ),
        ):
            with self.assertRaisesRegex(
                publication.PublicationError,
                "loose-ref contents changed during classification",
            ):
                publication.preflight(
                    self.repo.work,
                    remote="origin",
                    expected_push_url=str(approved),
                    branch="agent/test",
                    expected_remote_head=self.repo.base,
                    candidate=self.repo.candidate,
                )

        self.assertTrue(candidate_exposed)
        self.assertEqual(loose_ref.stat().st_ino, original_inode)
        self.assertEqual(git(approved, "rev-parse", "refs/heads/agent/test"), self.repo.base)

    def test_packed_refs_in_place_restore_during_classification_is_rejected(self) -> None:
        approved = self.repo.root / "packed-in-place.git"
        git(self.repo.root, "clone", "-q", "--bare", str(self.repo.remote), str(approved))
        git(approved, "fetch", "-q", str(self.repo.work), self.repo.candidate)
        git(approved, "pack-refs", "--all", "--prune")
        git(self.repo.work, "remote", "set-url", "origin", str(approved))
        packed = approved / "packed-refs"
        predecessor_contents = packed.read_bytes()
        candidate_contents = predecessor_contents.replace(
            self.repo.base.encode("ascii"), self.repo.candidate.encode("ascii")
        )
        self.assertNotEqual(predecessor_contents, candidate_contents)
        original_inode = packed.stat().st_ino
        real_run_git = publication._run_git
        real_classify = publication.classify_remote_state
        candidate_exposed = False

        def expose_candidate_in_place(cwd: Path, *args: str, **kwargs):
            nonlocal candidate_exposed
            if (
                not candidate_exposed
                and args
                and args[0] == "ls-remote"
                and "/proc/self/fd/" in args[-2]
            ):
                candidate_exposed = True
                packed.write_bytes(candidate_contents)
                self.assertEqual(packed.stat().st_ino, original_inode)
            return real_run_git(cwd, *args, **kwargs)

        def restore_predecessor_in_place(remote: str, expected: str, candidate: str) -> str:
            packed.write_bytes(predecessor_contents)
            self.assertEqual(packed.stat().st_ino, original_inode)
            return real_classify(remote, expected, candidate)

        with (
            mock.patch.object(
                publication, "_run_git", side_effect=expose_candidate_in_place
            ),
            mock.patch.object(
                publication,
                "classify_remote_state",
                side_effect=restore_predecessor_in_place,
            ),
        ):
            with self.assertRaisesRegex(
                publication.PublicationError,
                "packed-refs contents changed during classification",
            ):
                publication.preflight(
                    self.repo.work,
                    remote="origin",
                    expected_push_url=str(approved),
                    branch="agent/test",
                    expected_remote_head=self.repo.base,
                    candidate=self.repo.candidate,
                )

        self.assertTrue(candidate_exposed)
        self.assertEqual(packed.stat().st_ino, original_inode)
        self.assertEqual(git(approved, "rev-parse", "refs/heads/agent/test"), self.repo.base)

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

    def test_file_url_query_and_fragment_cannot_rebind_local_evidence(self) -> None:
        for delimiter, suffix in (("?", "route"), ("#", "fragment")):
            with self.subTest(delimiter=delimiter):
                literal = self.repo.extra_remote(f"literal-{suffix}.git{delimiter}{suffix}")
                stripped = self.repo.extra_remote(f"literal-{suffix}.git")
                git(
                    self.repo.work,
                    "push",
                    "-q",
                    str(literal),
                    f"{self.repo.base}:refs/heads/agent/test",
                )
                git(
                    self.repo.work,
                    "push",
                    "-q",
                    str(stripped),
                    f"{self.repo.candidate}:refs/heads/agent/test",
                )
                endpoint = f"file://{literal}"
                git(self.repo.work, "remote", "set-url", "--push", "origin", endpoint)
                bundle = self.repo.artifacts / f"file-{suffix}.bundle"

                with self.assertRaisesRegex(
                    publication.PublicationError, "query or fragment delimiters"
                ):
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
                    publication.remote_head(self.repo.work, str(literal), "agent/test"),
                    self.repo.base,
                )
                self.assertEqual(
                    publication.remote_head(self.repo.work, str(stripped), "agent/test"),
                    self.repo.candidate,
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
        push_seen = False

        def replace_at_readback(cwd: Path, *args: str, **kwargs):
            nonlocal replaced, push_seen
            if "push" in args:
                push_seen = True
            if (
                push_seen
                and not replaced
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

    def test_nonbare_git_directory_replacement_cannot_supply_success_readback(self) -> None:
        approved = self.repo.root / "approved-worktree"
        git(self.repo.root, "clone", "-q", str(self.repo.remote), str(approved))
        git(approved, "checkout", "-q", "agent/test")
        git(self.repo.work, "remote", "set-url", "origin", str(approved))

        escape = self.repo.extra_remote("git-directory-escape.git")
        git(
            self.repo.work,
            "push",
            "-q",
            str(escape),
            f"{self.repo.candidate}:refs/heads/agent/test",
        )
        original_git_directory = self.repo.root / "approved-original.git"
        bundle = self.repo.artifacts / "git-directory-boundary.bundle"
        real_run_git = publication._run_git
        replaced = False
        push_seen = False

        def replace_git_directory_at_readback(cwd: Path, *args: str, **kwargs):
            nonlocal replaced, push_seen
            if "push" in args:
                push_seen = True
            if (
                push_seen
                and not replaced
                and args
                and args[0] == "ls-remote"
                and any(value.startswith("/proc/self/fd/") for value in args)
            ):
                (approved / ".git").rename(original_git_directory)
                (approved / ".git").symlink_to(escape)
                replaced = True
            return real_run_git(cwd, *args, **kwargs)

        with mock.patch.object(publication, "_run_git", side_effect=replace_git_directory_at_readback):
            with self.assertRaisesRegex(publication.PublicationError, "ambiguous publication outcome"):
                publication.publish(
                    self.repo.work,
                    remote="origin",
                    expected_push_url=str(approved),
                    branch="agent/test",
                    expected_remote_head=self.repo.base,
                    candidate=self.repo.candidate,
                    recovery_bundle=bundle,
                )

        self.assertTrue(replaced)
        self.assertTrue((approved / ".git").is_symlink())
        self.assertEqual(
            publication.remote_head(self.repo.work, str(original_git_directory), "agent/test"),
            self.repo.base,
        )
        self.assertEqual(
            publication.remote_head(self.repo.work, str(escape), "agent/test"), self.repo.candidate
        )
        self.assertTrue(bundle.exists())
        self.assertFalse(bundle.with_name(bundle.name + ".tmp").exists())

    def test_linked_worktree_commondir_swap_cannot_supply_success_readback(self) -> None:
        primary = self.repo.root / "approved-primary"
        approved = self.repo.root / "approved-linked"
        git(self.repo.root, "clone", "-q", "--no-checkout", str(self.repo.remote), str(primary))
        git(primary, "worktree", "add", "-q", "-b", "agent/test", str(approved), "origin/agent/test")
        git(self.repo.work, "remote", "set-url", "origin", str(approved))

        escape = self.repo.extra_remote("commondir-escape.git")
        git(
            self.repo.work,
            "push",
            "-q",
            str(escape),
            f"{self.repo.candidate}:refs/heads/agent/test",
        )
        gitfile = (approved / ".git").read_text(encoding="utf-8").strip()
        self.assertTrue(gitfile.startswith("gitdir: "))
        admin = Path(gitfile[8:])
        if not admin.is_absolute():
            admin = approved / admin
        admin = admin.resolve()
        commondir = admin / "commondir"
        common = (admin / commondir.read_text(encoding="utf-8").strip()).resolve()
        bundle = self.repo.artifacts / "linked-worktree-commondir.bundle"
        real_run_git = publication._run_git
        replaced = False
        push_seen = False

        def replace_commondir_at_readback(cwd: Path, *args: str, **kwargs):
            nonlocal replaced, push_seen
            if "push" in args:
                push_seen = True
            if (
                push_seen
                and not replaced
                and args
                and args[0] == "ls-remote"
                and any(value.startswith("/proc/self/fd/") for value in args)
            ):
                commondir.write_text(f"{escape}\n", encoding="utf-8")
                replaced = True
            return real_run_git(cwd, *args, **kwargs)

        with mock.patch.object(publication, "_run_git", side_effect=replace_commondir_at_readback):
            with self.assertRaisesRegex(
                publication.PublicationError,
                "linked-worktree local publication targets are not supported",
            ):
                publication.publish(
                    self.repo.work,
                    remote="origin",
                    expected_push_url=str(approved),
                    branch="agent/test",
                    expected_remote_head=self.repo.base,
                    candidate=self.repo.candidate,
                    recovery_bundle=bundle,
                )

        self.assertFalse(replaced)
        self.assertEqual(
            publication.remote_head(self.repo.work, str(common), "agent/test"), self.repo.base
        )
        self.assertEqual(
            publication.remote_head(self.repo.work, str(escape), "agent/test"), self.repo.candidate
        )
        self.assertFalse(bundle.exists())
        self.assertFalse(bundle.with_name(bundle.name + ".tmp").exists())

    def test_transient_ref_swap_during_stable_readback_is_blocked_by_ref_lock(self) -> None:
        approved = self._prepare_literal_approved_endpoint()
        hook = approved / "hooks" / "pre-receive"
        hook.write_text("#!/bin/sh\nexit 73\n", encoding="utf-8")
        hook.chmod(0o755)

        # Seed the candidate object without advancing the approved branch.
        git(approved, "fetch", "-q", str(self.repo.work), self.repo.candidate)
        bundle = self.repo.artifacts / "transient-ref-readback.bundle"
        real_run_git = publication._run_git
        swap_blocked = False
        push_seen = False

        def transient_ref_swap(cwd: Path, *args: str, **kwargs):
            nonlocal swap_blocked, push_seen
            if "push" in args:
                push_seen = True
            stable_readback = (
                push_seen
                and args
                and args[0] == "ls-remote"
                and any(value.startswith("/proc/self/fd/") for value in args)
            )
            if stable_readback and not swap_blocked:
                attempted = subprocess.run(
                    ["git", "update-ref", "refs/heads/agent/test", self.repo.candidate],
                    cwd=approved,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False,
                )
                swap_blocked = attempted.returncode != 0
            return real_run_git(cwd, *args, **kwargs)

        with mock.patch.object(publication, "_run_git", side_effect=transient_ref_swap):
            with self.assertRaisesRegex(publication.PublicationError, "publication did not advance"):
                publication.publish(
                    self.repo.work,
                    remote="origin",
                    expected_push_url="approved",
                    branch="agent/test",
                    expected_remote_head=self.repo.base,
                    candidate=self.repo.candidate,
                    recovery_bundle=bundle,
                )

        self.assertTrue(swap_blocked)
        self.assertEqual(
            publication.remote_head(self.repo.work, str(approved), "agent/test"), self.repo.base
        )
        self.assertTrue(bundle.exists())
        self.assertFalse(bundle.with_name(bundle.name + ".tmp").exists())

    def test_final_preflight_restoration_cannot_precede_classification(self) -> None:
        approved = self._prepare_literal_approved_endpoint()
        git(approved, "fetch", "-q", str(self.repo.work), self.repo.candidate)
        git(approved, "update-ref", "refs/heads/agent/test", self.repo.candidate)
        restoration_returncode = 0
        real_classify = publication.classify_remote_state

        def restore_at_classification(remote: str, expected: str, candidate: str) -> str:
            nonlocal restoration_returncode
            attempted = subprocess.run(
                ["git", "update-ref", "refs/heads/agent/test", self.repo.base],
                cwd=approved,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            restoration_returncode = attempted.returncode
            self.assertNotEqual(restoration_returncode, 0)
            self.assertEqual(
                publication.remote_head(self.repo.work, str(approved), "agent/test"),
                self.repo.candidate,
            )
            return real_classify(remote, expected, candidate)

        with mock.patch.object(
            publication, "classify_remote_state", side_effect=restore_at_classification
        ):
            state = publication.preflight(
                self.repo.work,
                remote="origin",
                expected_push_url="approved",
                branch="agent/test",
                expected_remote_head=self.repo.base,
                candidate=self.repo.candidate,
            )

        self.assertEqual(state, "PUBLISHED")
        self.assertNotEqual(restoration_returncode, 0)
        git(approved, "update-ref", "refs/heads/agent/test", self.repo.base)
        self.assertEqual(
            publication.remote_head(self.repo.work, str(approved), "agent/test"), self.repo.base
        )

    def test_symbolic_local_target_is_rejected_while_named_lock_is_held(self) -> None:
        approved = self._prepare_literal_approved_endpoint()
        git(approved, "fetch", "-q", str(self.repo.work), self.repo.candidate)
        git(approved, "update-ref", "refs/heads/underlying", self.repo.candidate)
        symbolic_ref = approved / "refs" / "heads" / "agent" / "test"
        symbolic_ref.write_bytes(b"ref:\trefs/heads/underlying\n")
        self.assertEqual(
            git(approved, "symbolic-ref", "refs/heads/agent/test"),
            "refs/heads/underlying",
        )
        bundle = self.repo.artifacts / "symbolic-target.bundle"
        real_open = publication.os.open
        referent_move_returncode: int | None = None

        def move_referent_after_named_lock(path, flags, *args, **kwargs):
            nonlocal referent_move_returncode
            descriptor = real_open(path, flags, *args, **kwargs)
            if path == "test.lock" and flags & publication.os.O_EXCL:
                attempted = subprocess.run(
                    ["git", "update-ref", "refs/heads/underlying", self.repo.base],
                    cwd=approved,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False,
                )
                referent_move_returncode = attempted.returncode
            return descriptor

        with mock.patch.object(publication.os, "open", side_effect=move_referent_after_named_lock):
            with self.assertRaisesRegex(
                publication.PublicationError,
                "symbolic local publication target branches are not supported",
            ):
                publication.publish(
                    self.repo.work,
                    remote="origin",
                    expected_push_url="approved",
                    branch="agent/test",
                    expected_remote_head=self.repo.base,
                    candidate=self.repo.candidate,
                    recovery_bundle=bundle,
                )

        # The named lock does not block a supported writer from moving its
        # referent, so rejection must occur before local evidence is accepted.
        self.assertEqual(referent_move_returncode, 0)
        self.assertEqual(git(approved, "rev-parse", "refs/heads/underlying"), self.repo.base)
        self.assertFalse((approved / "refs" / "heads" / "agent" / "test.lock").exists())
        self.assertFalse(bundle.exists())
        self.assertFalse(bundle.with_name(bundle.name + ".tmp").exists())

    def test_packed_only_nested_branch_creates_safe_lock_hierarchy(self) -> None:
        approved = self.repo.root / "packed-approved.git"
        git(self.repo.root, "clone", "-q", "--bare", str(self.repo.remote), str(approved))
        git(approved, "pack-refs", "--all", "--prune")
        nested_parent = approved / "refs" / "heads" / "agent"
        self.assertFalse(nested_parent.exists())
        self.assertEqual(
            git(approved, "rev-parse", "refs/heads/agent/test"), self.repo.base
        )
        git(self.repo.work, "remote", "set-url", "origin", str(approved))

        state = publication.preflight(
            self.repo.work,
            remote="origin",
            expected_push_url=str(approved),
            branch="agent/test",
            expected_remote_head=self.repo.base,
            candidate=self.repo.candidate,
        )
        self.assertEqual(state, "NOT_PUBLISHED")
        self.assertTrue(nested_parent.is_dir())

        bundle = self.repo.artifacts / "packed-only.bundle"
        result = publication.publish(
            self.repo.work,
            remote="origin",
            expected_push_url=str(approved),
            branch="agent/test",
            expected_remote_head=self.repo.base,
            candidate=self.repo.candidate,
            recovery_bundle=bundle,
        )
        self.assertEqual(result.state, "PUBLISHED")
        self.assertEqual(
            publication.remote_head(self.repo.work, str(approved), "agent/test"),
            self.repo.candidate,
        )
        self.assertTrue(bundle.exists())

    def test_packed_only_branch_rejects_symlinked_lock_hierarchy(self) -> None:
        approved = self.repo.root / "packed-symlink-approved.git"
        git(self.repo.root, "clone", "-q", "--bare", str(self.repo.remote), str(approved))
        git(approved, "pack-refs", "--all", "--prune")
        heads = approved / "refs" / "heads"
        heads.mkdir(parents=True, exist_ok=True)
        redirected = self.repo.root / "redirected-ref-hierarchy"
        redirected.mkdir()
        (heads / "agent").symlink_to(redirected, target_is_directory=True)
        git(self.repo.work, "remote", "set-url", "origin", str(approved))
        bundle = self.repo.artifacts / "packed-symlink.bundle"

        with self.assertRaisesRegex(
            publication.PublicationError,
            "unable to acquire stable local publication branch lock",
        ):
            publication.publish(
                self.repo.work,
                remote="origin",
                expected_push_url=str(approved),
                branch="agent/test",
                expected_remote_head=self.repo.base,
                candidate=self.repo.candidate,
                recovery_bundle=bundle,
            )

        self.assertFalse((redirected / "test.lock").exists())
        self.assertEqual(
            publication.remote_head(self.repo.work, str(approved), "agent/test"),
            self.repo.base,
        )
        self.assertFalse(bundle.exists())
        self.assertFalse(bundle.with_name(bundle.name + ".tmp").exists())

    def test_packed_only_ref_hierarchy_swap_cannot_supply_success_evidence(self) -> None:
        approved = self.repo.root / "packed-hierarchy-race.git"
        git(self.repo.root, "clone", "-q", "--bare", str(self.repo.remote), str(approved))
        git(approved, "fetch", "-q", str(self.repo.work), self.repo.candidate)
        git(approved, "pack-refs", "--all", "--prune")
        git(self.repo.work, "remote", "set-url", "origin", str(approved))
        real_run_git = publication._run_git
        swapped = False

        def swap_parent_only_during_ls_remote(cwd: Path, *args: str, **kwargs):
            nonlocal swapped
            if not swapped and args and args[0] == "ls-remote" and "/proc/self/fd/" in args[-2]:
                swapped = True
                heads = approved / "refs" / "heads"
                original = approved / "refs" / "heads.original"
                heads.rename(original)
                replacement = heads / "agent"
                replacement.mkdir(parents=True)
                (replacement / "test").write_text(self.repo.candidate + "\n", encoding="ascii")
                try:
                    return real_run_git(cwd, *args, **kwargs)
                finally:
                    for child in replacement.iterdir():
                        child.unlink()
                    replacement.rmdir()
                    heads.rmdir()
                    original.rename(heads)
            return real_run_git(cwd, *args, **kwargs)

        with mock.patch.object(
            publication, "_run_git", side_effect=swap_parent_only_during_ls_remote
        ):
            with self.assertRaisesRegex(
                publication.PublicationError,
                "local publication branch changed during readback",
            ):
                publication.preflight(
                    self.repo.work,
                    remote="origin",
                    expected_push_url=str(approved),
                    branch="agent/test",
                    expected_remote_head=self.repo.base,
                    candidate=self.repo.candidate,
                )

        self.assertTrue(swapped)
        self.assertEqual(git(approved, "rev-parse", "refs/heads/agent/test"), self.repo.base)

    def test_local_endpoint_swap_during_push_cannot_redirect_mutation(self) -> None:
        approved = self._prepare_literal_approved_endpoint()
        escape = self.repo.extra_remote("push-endpoint-escape.git")
        git(
            self.repo.work,
            "push",
            "-q",
            str(escape),
            f"{self.repo.base}:refs/heads/agent/test",
        )
        moved = self.repo.work / "approved.original"
        bundle = self.repo.artifacts / "push-endpoint-race.bundle"
        real_run_git = publication._run_git
        swapped = False

        def swap_endpoint_only_during_push(cwd: Path, *args: str, **kwargs):
            nonlocal swapped
            if not swapped and "push" in args:
                swapped = True
                approved.rename(moved)
                approved.symlink_to(escape, target_is_directory=True)
                try:
                    return real_run_git(cwd, *args, **kwargs)
                finally:
                    approved.unlink()
                    moved.rename(approved)
            return real_run_git(cwd, *args, **kwargs)

        with mock.patch.object(publication, "_run_git", side_effect=swap_endpoint_only_during_push):
            result = publication.publish(
                self.repo.work,
                remote="origin",
                expected_push_url="approved",
                branch="agent/test",
                expected_remote_head=self.repo.base,
                candidate=self.repo.candidate,
                recovery_bundle=bundle,
            )

        self.assertTrue(swapped)
        self.assertEqual(result.state, "PUBLISHED")
        self.assertEqual(git(approved, "rev-parse", "refs/heads/agent/test"), self.repo.candidate)
        self.assertEqual(git(escape, "rev-parse", "refs/heads/agent/test"), self.repo.base)
        self.assertTrue(bundle.exists())

    def test_linked_worktree_commondir_cannot_redirect_guarded_push(self) -> None:
        approved = self.repo.root / "linked-push"
        git(
            self.repo.remote,
            "worktree",
            "add",
            "--detach",
            str(approved),
            "refs/heads/agent/test",
        )
        escape = self.repo.extra_remote("linked-push-escape.git")
        git(
            self.repo.work,
            "push",
            "-q",
            str(escape),
            f"{self.repo.base}:refs/heads/agent/test",
        )
        git(self.repo.work, "remote", "set-url", "origin", str(approved))
        bundle = self.repo.artifacts / "linked-push-commondir.bundle"
        real_run_git = publication._run_git
        push_reached = False

        def rewrite_commondir_only_during_push(cwd: Path, *args: str, **kwargs):
            nonlocal push_reached
            if "push" in args:
                push_reached = True
                gitfile = approved / ".git"
                admin = Path(gitfile.read_text(encoding="utf-8").strip()[8:])
                commondir = admin / "commondir"
                original = commondir.read_text(encoding="utf-8")
                commondir.write_text(f"{escape}\n", encoding="utf-8")
                try:
                    return real_run_git(cwd, *args, **kwargs)
                finally:
                    commondir.write_text(original, encoding="utf-8")
            return real_run_git(cwd, *args, **kwargs)

        with mock.patch.object(publication, "_run_git", side_effect=rewrite_commondir_only_during_push):
            with self.assertRaisesRegex(
                publication.PublicationError,
                "linked-worktree local publication targets are not supported",
            ):
                publication.publish(
                    self.repo.work,
                    remote="origin",
                    expected_push_url=str(approved),
                    branch="agent/test",
                    expected_remote_head=self.repo.base,
                    candidate=self.repo.candidate,
                    recovery_bundle=bundle,
                )

        self.assertFalse(push_reached)
        self.assertEqual(
            git(self.repo.remote, "rev-parse", "refs/heads/agent/test"), self.repo.base
        )
        self.assertEqual(git(escape, "rev-parse", "refs/heads/agent/test"), self.repo.base)
        self.assertFalse(bundle.exists())

    def test_packed_refs_remains_pinned_through_classification(self) -> None:
        approved = self.repo.root / "packed-classification.git"
        git(self.repo.root, "clone", "-q", "--bare", str(self.repo.remote), str(approved))
        git(approved, "fetch", "-q", str(self.repo.work), self.repo.candidate)
        git(approved, "pack-refs", "--all", "--prune")
        git(self.repo.work, "remote", "set-url", "origin", str(approved))
        packed = approved / "packed-refs"
        predecessor_storage = packed.with_name("packed-refs.predecessor")
        real_run_git = publication._run_git
        real_classify = publication.classify_remote_state
        replacement_installed = False

        def candidate_storage_during_readback(cwd: Path, *args: str, **kwargs):
            nonlocal replacement_installed
            if (
                not replacement_installed
                and args
                and args[0] == "ls-remote"
                and "/proc/self/fd/" in args[-2]
            ):
                replacement_installed = True
                packed.rename(predecessor_storage)
                packed.write_text(
                    f"# pack-refs with: peeled fully-peeled sorted\n"
                    f"{self.repo.candidate} refs/heads/agent/test\n",
                    encoding="ascii",
                )
            return real_run_git(cwd, *args, **kwargs)

        def restore_storage_at_classification(remote: str, expected: str, candidate: str) -> str:
            packed.unlink()
            predecessor_storage.rename(packed)
            return real_classify(remote, expected, candidate)

        try:
            with (
                mock.patch.object(
                    publication, "_run_git", side_effect=candidate_storage_during_readback
                ),
                mock.patch.object(
                    publication,
                    "classify_remote_state",
                    side_effect=restore_storage_at_classification,
                ),
            ):
                with self.assertRaisesRegex(
                    publication.PublicationError,
                    "packed-refs storage changed during classification",
                ):
                    publication.preflight(
                        self.repo.work,
                        remote="origin",
                        expected_push_url=str(approved),
                        branch="agent/test",
                        expected_remote_head=self.repo.base,
                        candidate=self.repo.candidate,
                    )
        finally:
            if predecessor_storage.exists():
                if packed.exists():
                    packed.unlink()
                predecessor_storage.rename(packed)

        self.assertTrue(replacement_installed)
        self.assertEqual(git(approved, "rev-parse", "refs/heads/agent/test"), self.repo.base)

    def test_final_post_push_restoration_cannot_precede_classification(self) -> None:
        approved = self._prepare_literal_approved_endpoint()
        git(approved, "fetch", "-q", str(self.repo.work), self.repo.candidate)
        bundle = self.repo.artifacts / "post-push-final-classification.bundle"
        real_run_git = publication._run_git
        real_classify = publication.classify_remote_state
        restoration_returncode = 0

        def rejected_push_with_candidate_visible(cwd: Path, *args: str, **kwargs):
            if "push" in args:
                git(approved, "update-ref", "refs/heads/agent/test", self.repo.candidate)
                return subprocess.CompletedProcess(["git", *args], 73, "", "rejected")
            return real_run_git(cwd, *args, **kwargs)

        def restore_at_classification(remote: str, expected: str, candidate: str) -> str:
            nonlocal restoration_returncode
            attempted = subprocess.run(
                ["git", "update-ref", "refs/heads/agent/test", self.repo.base],
                cwd=approved,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            restoration_returncode = attempted.returncode
            self.assertNotEqual(restoration_returncode, 0)
            return real_classify(remote, expected, candidate)

        with (
            mock.patch.object(
                publication, "_run_git", side_effect=rejected_push_with_candidate_visible
            ),
            mock.patch.object(
                publication, "classify_remote_state", side_effect=restore_at_classification
            ),
        ):
            result = publication.publish(
                self.repo.work,
                remote="origin",
                expected_push_url="approved",
                branch="agent/test",
                expected_remote_head=self.repo.base,
                candidate=self.repo.candidate,
                recovery_bundle=bundle,
            )

        self.assertEqual(result.state, "PUBLISHED")
        self.assertNotEqual(restoration_returncode, 0)
        git(approved, "update-ref", "refs/heads/agent/test", self.repo.base)
        self.assertEqual(
            publication.remote_head(self.repo.work, str(approved), "agent/test"), self.repo.base
        )
        self.assertTrue(bundle.exists())
        self.assertFalse(bundle.with_name(bundle.name + ".tmp").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
