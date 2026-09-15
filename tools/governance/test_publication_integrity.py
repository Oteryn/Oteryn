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

    def new_bare_remote(self, name: str) -> Path:
        target = self.root / name
        target.mkdir()
        git(target, "init", "--bare", "-q")
        return target

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
            publication.remote_head(self.repo.work, self.repo.push_url, "agent/test"),
            self.repo.candidate,
        )
        listed = git(self.repo.work, "bundle", "list-heads", str(bundle))
        self.assertIn(f"{self.repo.candidate} refs/heads/agent/test", listed)

    def test_colliding_tag_cannot_override_branch_identity_bundle_or_publication(self) -> None:
        git(self.repo.work, "tag", "agent/test", self.repo.intermediate)

        self.assertEqual(
            publication.preflight(
                self.repo.work,
                remote="origin",
                expected_push_url=self.repo.push_url,
                branch="agent/test",
                expected_remote_head=self.repo.base,
                candidate=self.repo.candidate,
            ),
            "NOT_PUBLISHED",
        )

        bundle = self.repo.artifacts / "colliding-tag.bundle"
        result = self.publish(bundle.name)

        self.assertEqual(result.state, "PUBLISHED")
        self.assertEqual(
            publication.remote_head(self.repo.work, self.repo.push_url, "agent/test"),
            self.repo.candidate,
        )
        self.assertEqual(
            git(self.repo.work, "rev-parse", "refs/tags/agent/test"), self.repo.intermediate
        )
        listed = git(self.repo.work, "bundle", "list-heads", str(bundle))
        self.assertIn(f"{self.repo.candidate} refs/heads/agent/test", listed)
        self.assertNotIn("refs/tags/agent/test", listed)

    def test_colliding_tag_does_not_hide_wrong_checked_out_branch(self) -> None:
        git(self.repo.work, "tag", "agent/test", self.repo.intermediate)
        git(self.repo.work, "checkout", "-qb", "agent/other", self.repo.candidate)

        with self.assertRaisesRegex(publication.PublicationError, "checked-out local branch"):
            publication.preflight(
                self.repo.work,
                remote="origin",
                expected_push_url=self.repo.push_url,
                branch="agent/test",
                expected_remote_head=self.repo.base,
                candidate=self.repo.candidate,
            )

        self.assertEqual(
            publication.remote_head(self.repo.work, self.repo.push_url, "agent/test"), self.repo.base
        )

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
        self.assertEqual(
            publication.remote_head(self.repo.work, self.repo.push_url, "agent/test"), other
        )

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

    def test_existing_temporary_bundle_path_is_preserved_and_rejected(self) -> None:
        temporary = self.repo.artifacts / "candidate.bundle.tmp"
        temporary.parent.mkdir(parents=True, exist_ok=True)
        temporary.write_text("keep-me", encoding="utf-8")
        with self.assertRaisesRegex(publication.PublicationError, "temporary path already exists"):
            publication.create_recovery_bundle(
                self.repo.work,
                branch="agent/test",
                expected_remote_head=self.repo.base,
                candidate=self.repo.candidate,
                bundle_path=self.repo.artifacts / "candidate.bundle",
            )
        self.assertEqual(temporary.read_text(encoding="utf-8"), "keep-me")

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
            publication.remote_head(self.repo.work, self.repo.push_url, "agent/test"),
            self.repo.intermediate,
        )

    def test_push_capability_failure_preserves_remote_and_verified_bundle(self) -> None:
        bundle = self.repo.artifacts / "candidate.bundle"
        real_run_git = publication._run_git

        def fail_only_push(cwd: Path, *args: str, check: bool = True):
            if "push" in args:
                return subprocess.CompletedProcess(["git", *args], 1, "", "simulated push denial")
            return real_run_git(cwd, *args, check=check)

        with mock.patch.object(publication, "_run_git", side_effect=fail_only_push):
            with self.assertRaisesRegex(publication.PublicationError, "did not advance"):
                self.publish()

        self.assertEqual(
            publication.remote_head(self.repo.work, self.repo.push_url, "agent/test"), self.repo.base
        )
        self.assertTrue(bundle.is_file())
        listed = git(self.repo.work, "bundle", "list-heads", str(bundle))
        self.assertIn(f"{self.repo.candidate} refs/heads/agent/test", listed)

    def test_distinct_single_push_url_uses_same_endpoint_for_push_and_readback(self) -> None:
        push_remote = self.repo.new_bare_remote("push.git")
        git(
            self.repo.work,
            "push",
            "-q",
            str(push_remote),
            f"{self.repo.base}:refs/heads/agent/test",
        )
        git(self.repo.work, "remote", "set-url", "--push", "origin", str(push_remote))

        result = publication.publish(
            self.repo.work,
            remote="origin",
            expected_push_url=str(push_remote),
            branch="agent/test",
            expected_remote_head=self.repo.base,
            candidate=self.repo.candidate,
            recovery_bundle=self.repo.artifacts / "distinct-push.bundle",
        )

        self.assertEqual(result.state, "PUBLISHED")
        self.assertEqual(
            publication.remote_head(self.repo.work, str(push_remote), "agent/test"),
            self.repo.candidate,
        )
        self.assertEqual(
            publication.remote_head(self.repo.work, self.repo.push_url, "agent/test"), self.repo.base
        )

    def test_multiple_push_urls_fail_closed_before_mutation(self) -> None:
        extra = self.repo.new_bare_remote("extra.git")
        git(self.repo.work, "remote", "set-url", "--add", "--push", "origin", self.repo.push_url)
        git(self.repo.work, "remote", "set-url", "--add", "--push", "origin", str(extra))

        with self.assertRaisesRegex(publication.PublicationError, "exactly one configured push URL"):
            self.publish()

        self.assertEqual(
            publication.remote_head(self.repo.work, self.repo.push_url, "agent/test"), self.repo.base
        )

    def test_chained_push_instead_of_rewrites_fail_closed_before_mutation(self) -> None:
        approved = self.repo.new_bare_remote("approved.git")
        escape = self.repo.new_bare_remote("escape.git")
        git(
            self.repo.work,
            "push",
            "-q",
            str(approved),
            f"{self.repo.base}:refs/heads/agent/test",
        )
        git(self.repo.work, "config", f"url.{approved}.pushInsteadOf", self.repo.push_url)
        git(self.repo.work, "config", f"url.{escape}.pushInsteadOf", str(approved))

        with self.assertRaisesRegex(publication.PublicationError, "URL rewrite rules"):
            publication.publish(
                self.repo.work,
                remote="origin",
                expected_push_url=str(approved),
                branch="agent/test",
                expected_remote_head=self.repo.base,
                candidate=self.repo.candidate,
                recovery_bundle=self.repo.artifacts / "rewrite.bundle",
            )

        git(self.repo.work, "config", "--unset-all", f"url.{approved}.pushInsteadOf")
        git(self.repo.work, "config", "--unset-all", f"url.{escape}.pushInsteadOf")
        self.assertEqual(
            publication.remote_head(self.repo.work, self.repo.push_url, "agent/test"), self.repo.base
        )
        self.assertEqual(
            publication.remote_head(self.repo.work, str(approved), "agent/test"), self.repo.base
        )
        self.assertEqual(
            git(self.repo.work, "ls-remote", "--heads", str(escape), "refs/heads/agent/test"), ""
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

    def test_embedded_url_credentials_are_rejected_without_echoing_them(self) -> None:
        secret_url = "https://user:secret@example.invalid/Oteryn/Oteryn.git"
        with self.assertRaises(publication.PublicationError) as context:
            publication.preflight(
                self.repo.work,
                remote="origin",
                expected_push_url=secret_url,
                branch="agent/test",
                expected_remote_head=self.repo.base,
                candidate=self.repo.candidate,
            )
        self.assertIn("must not embed credentials", str(context.exception))
        self.assertNotIn("secret", str(context.exception))

    def test_nested_remote_helper_credentials_are_rejected_before_git_execution(self) -> None:
        secret_url = "http::https://user:supersecret@example.invalid/Oteryn/Oteryn.git"
        git(self.repo.work, "remote", "set-url", "--push", "origin", secret_url)
        bundle = self.repo.artifacts / "remote-helper.bundle"

        with mock.patch.object(subprocess, "run") as run:
            with self.assertRaises(publication.PublicationError) as context:
                publication.publish(
                    self.repo.work,
                    remote="origin",
                    expected_push_url=secret_url,
                    branch="agent/test",
                    expected_remote_head=self.repo.base,
                    candidate=self.repo.candidate,
                    recovery_bundle=bundle,
                )

        self.assertIn("explicit Git remote-helper syntax", str(context.exception))
        self.assertNotIn("supersecret", str(context.exception))
        run.assert_not_called()
        self.assertFalse(bundle.exists())
        self.assertFalse(bundle.with_name(bundle.name + ".tmp").exists())
        self.assertEqual(
            publication.remote_head(self.repo.work, self.repo.push_url, "agent/test"), self.repo.base
        )

    def test_implicit_remote_helper_scheme_is_rejected_before_execution(self) -> None:
        approved = self.repo.new_bare_remote("approved.git")
        escape = self.repo.new_bare_remote("escape.git")
        for target in (approved, escape):
            git(
                self.repo.work,
                "push",
                "-q",
                str(target),
                f"{self.repo.base}:refs/heads/agent/test",
            )

        marker = self.repo.root / "remote-helper-ran"
        helper_dir = self.repo.root / "helpers"
        helper_dir.mkdir()
        helper = helper_dir / "git-remote-evil"
        helper.write_text(
            "#!/bin/sh\n"
            f"> {marker}\n"
            f"git -C {self.repo.work} push -q {escape} "
            "HEAD:refs/heads/agent/test\n"
            "exit 73\n",
            encoding="utf-8",
        )
        helper.chmod(0o755)
        endpoint = "evil://approved"
        git(self.repo.work, "remote", "set-url", "--push", "origin", endpoint)
        bundle = self.repo.artifacts / "implicit-helper.bundle"

        with mock.patch.dict("os.environ", {"PATH": f"{helper_dir}:{os.environ['PATH']}"}):
            with self.assertRaisesRegex(publication.PublicationError, "native Git push URL scheme"):
                publication.publish(
                    self.repo.work,
                    remote="origin",
                    expected_push_url=endpoint,
                    branch="agent/test",
                    expected_remote_head=self.repo.base,
                    candidate=self.repo.candidate,
                    recovery_bundle=bundle,
                )

        self.assertFalse(marker.exists())
        self.assertFalse(bundle.exists())
        self.assertFalse(bundle.with_name(bundle.name + ".tmp").exists())
        for target in (approved, escape):
            self.assertEqual(
                publication.remote_head(self.repo.work, str(target), "agent/test"), self.repo.base
            )

    def test_native_url_schemes_and_local_paths_remain_supported(self) -> None:
        for scheme in ("ssh", "git", "http", "https", "file"):
            endpoint = f"{scheme}://example.invalid/Oteryn/Oteryn.git"
            self.assertEqual(publication._credential_free_url(endpoint, "test endpoint"), endpoint)
        self.assertEqual(
            publication._credential_free_url(self.repo.push_url, "test endpoint"),
            self.repo.push_url,
        )
        scp_like = "git@example.invalid:Oteryn/Oteryn.git"
        self.assertEqual(publication._credential_free_url(scp_like, "test endpoint"), scp_like)

    def test_mixed_case_native_scheme_is_rejected_before_helper_execution(self) -> None:
        approved = self.repo.new_bare_remote("approved-uppercase.git")
        escape = self.repo.new_bare_remote("escape-uppercase.git")
        for target in (approved, escape):
            git(
                self.repo.work,
                "push",
                "-q",
                str(target),
                f"{self.repo.base}:refs/heads/agent/test",
            )

        marker = self.repo.root / "uppercase-remote-helper-ran"
        helper_dir = self.repo.root / "uppercase-helpers"
        helper_dir.mkdir()
        helper = helper_dir / "git-remote-HTTPS"
        helper.write_text(
            "#!/bin/sh\n"
            f"> {marker}\n"
            f"git -C {self.repo.work} push -q {escape} "
            "HEAD:refs/heads/agent/test\n"
            "exit 73\n",
            encoding="utf-8",
        )
        helper.chmod(0o755)
        endpoint = "HTTPS://approved"
        git(self.repo.work, "remote", "set-url", "--push", "origin", endpoint)
        bundle = self.repo.artifacts / "uppercase-helper.bundle"

        with mock.patch.dict("os.environ", {"PATH": f"{helper_dir}:{os.environ['PATH']}"}):
            with self.assertRaisesRegex(publication.PublicationError, "native Git push URL scheme"):
                publication.publish(
                    self.repo.work,
                    remote="origin",
                    expected_push_url=endpoint,
                    branch="agent/test",
                    expected_remote_head=self.repo.base,
                    candidate=self.repo.candidate,
                    recovery_bundle=bundle,
                )

        self.assertFalse(marker.exists())
        self.assertFalse(bundle.exists())
        self.assertFalse(bundle.with_name(bundle.name + ".tmp").exists())
        for target in (approved, escape):
            self.assertEqual(
                publication.remote_head(self.repo.work, str(target), "agent/test"), self.repo.base
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
