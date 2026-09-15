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

    def clean_filter_side_publish_script(self, name: str) -> Path:
        script = self.root / name
        script.write_text(
            "#!/bin/sh\n"
            f"git -C '{self.work}' push -q '{self.escape}' HEAD:refs/heads/agent/test\n"
            "cat\n",
            encoding="utf-8",
        )
        script.chmod(0o755)
        return script

    def activate_filter(self, driver: str) -> None:
        (self.work / ".gitattributes").write_text(
            f"state.txt filter={driver}\n",
            encoding="utf-8",
        )
        git(self.work, "add", ".gitattributes")
        git(self.work, "commit", "-qm", f"activate {driver} filter")
        self.candidate = git(self.work, "rev-parse", "HEAD")

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

    def assert_blocked_without_publication(self, pattern: str, bundle_name: str) -> None:
        bundle = self.repo.artifacts / bundle_name
        with self.assertRaisesRegex(publication.PublicationError, pattern):
            self.repo.publish(bundle_name)
        self.assertEqual(self.repo.raw_remote_head(), self.repo.base)
        self.assertEqual(self.repo.raw_escape_head(), "")
        self.assertFalse(bundle.exists())

    def assert_reserved_filter_driver_blocked(self, driver: str) -> None:
        self.repo.activate_filter(driver)
        filter_script = self.repo.clean_filter_side_publish_script(f"filter-{driver}.sh")
        git(self.repo.work, "config", f"filter.{driver}.clean", str(filter_script))
        (self.repo.work / "state.txt").touch()
        self.assert_blocked_without_publication(
            "clean/process filters",
            f"filter-{driver}.bundle",
        )

    def test_local_http_routing_and_tls_overrides_are_rejected(self) -> None:
        cases = (
            ("http.proxy", "http://user:supersecret@proxy.invalid", "proxy"),
            ("http.https://example.invalid/.curloptResolve", "example.invalid:443:127.0.0.1", "resolve"),
            ("http.sslVerify", "false", "verify"),
            ("http.sslCAInfo", str(self.repo.root / "untrusted-ca.pem"), "ca"),
            ("http.extraHeader", "Host: evil.invalid", "header"),
            ("remote.origin.proxy", "http://proxy.invalid", "remote-proxy"),
        )
        for key, value, name in cases:
            with self.subTest(key=key):
                git(self.repo.work, "config", "--local", key, value)
                try:
                    bundle = self.repo.artifacts / f"http-{name}.bundle"
                    with self.assertRaisesRegex(publication.PublicationError, "HTTP routing or TLS-trust") as raised:
                        self.repo.publish(bundle.name)
                    self.assertNotIn("supersecret", str(raised.exception))
                    self.assertEqual(self.repo.raw_remote_head(), self.repo.base)
                    self.assertEqual(self.repo.raw_escape_head(), "")
                    self.assertFalse(bundle.exists())
                    self.assertFalse(bundle.with_name(bundle.name + ".tmp").exists())
                finally:
                    git(self.repo.work, "config", "--local", "--unset-all", key)

    def test_included_and_worktree_http_overrides_are_rejected(self) -> None:
        included = self.repo.root / "repo-http.cfg"
        included.write_text("[http]\n\textraHeader = Host: evil.invalid\n", encoding="utf-8")
        git(self.repo.work, "config", "--local", "include.path", str(included))
        self.assert_blocked_without_publication("HTTP routing or TLS-trust", "included-http.bundle")
        git(self.repo.work, "config", "--local", "--unset-all", "include.path")

        git(self.repo.work, "config", "extensions.worktreeConfig", "true")
        git(self.repo.work, "config", "--worktree", "http.sslCAPath", str(self.repo.root))
        self.assert_blocked_without_publication("HTTP routing or TLS-trust", "worktree-http.bundle")

    def test_system_and_global_http_configuration_is_not_rejected(self) -> None:
        system_config = self.repo.root / "trusted-system.cfg"
        global_config = self.repo.root / "trusted-global-http.cfg"
        system_config.write_text("[http]\n\tproxy = http://system-proxy.invalid\n", encoding="utf-8")
        global_config.write_text("[http]\n\tsslVerify = false\n", encoding="utf-8")
        with mock.patch.dict(
            os.environ,
            {"GIT_CONFIG_SYSTEM": str(system_config), "GIT_CONFIG_GLOBAL": str(global_config)},
            clear=False,
        ):
            result = self.repo.publish("global-system-http.bundle")
        self.assertEqual(result.state, "PUBLISHED")
        self.assertEqual(self.repo.raw_remote_head(), self.repo.candidate)

    def test_configured_signed_push_cannot_execute_gpg_side_publish(self) -> None:
        git(self.repo.remote, "config", "receive.certNonceSeed", "publication-integrity-test")
        malicious_gpg = self.repo.malicious_script("malicious-gpg.sh")
        git(self.repo.work, "config", "push.gpgSign", "true")
        git(self.repo.work, "config", "gpg.program", str(malicious_gpg))

        result = self.repo.publish("signed-push.bundle")

        self.assertEqual(result.state, "PUBLISHED")
        self.assertEqual(self.repo.raw_remote_head(), self.repo.candidate)
        self.assertEqual(self.repo.raw_escape_head(), "")

    def test_configured_push_options_are_cleared_on_guarded_push(self) -> None:
        git(self.repo.remote, "config", "receive.advertisePushOptions", "true")
        observed = self.repo.root / "observed-push-option-count.txt"
        hook = self.repo.remote / "hooks" / "pre-receive"
        hook.write_text(
            "#!/bin/sh\n"
            f"printf '%s\\n' \"${{GIT_PUSH_OPTION_COUNT:-0}}\" > '{observed}'\n"
            "cat >/dev/null\n",
            encoding="utf-8",
        )
        hook.chmod(0o755)
        git(self.repo.work, "config", "--local", "push.pushOption", "deploy=production")

        result = self.repo.publish("push-options-cleared.bundle")

        self.assertEqual(result.state, "PUBLISHED")
        self.assertEqual(observed.read_text(encoding="utf-8").strip(), "0")
        self.assertEqual(self.repo.raw_remote_head(), self.repo.candidate)

    def test_partial_clone_missing_recovery_object_cannot_lazy_fetch_promisor(self) -> None:
        recovery_only = self.repo.work / "recovery-only.txt"
        recovery_only.write_text("candidate-history-only\n", encoding="utf-8")
        git(self.repo.work, "add", "recovery-only.txt")
        git(self.repo.work, "commit", "-qm", "add recovery-only blob")
        missing_blob = git(self.repo.work, "rev-parse", "HEAD:recovery-only.txt")

        recovery_only.unlink()
        (self.repo.work / "state.txt").write_text(
            "base\ncandidate\nfinal\n",
            encoding="utf-8",
        )
        git(self.repo.work, "add", "-A")
        git(self.repo.work, "commit", "-qm", "final candidate without recovery-only file")
        self.repo.candidate = git(self.repo.work, "rev-parse", "HEAD")

        marker = self.repo.root / "promisor-transport-invoked.txt"
        promisor_script = self.repo.root / "promisor-transport.sh"
        promisor_script.write_text(
            "#!/bin/sh\n"
            f"printf 'invoked\\n' > '{marker}'\n"
            "exit 73\n",
            encoding="utf-8",
        )
        promisor_script.chmod(0o755)

        git(self.repo.work, "config", "core.repositoryformatversion", "1")
        git(self.repo.work, "config", "extensions.partialClone", "promisor")
        git(self.repo.work, "remote", "add", "promisor", f"ext::{promisor_script}")
        git(self.repo.work, "config", "remote.promisor.promisor", "true")
        git(self.repo.work, "config", "remote.promisor.partialCloneFilter", "blob:none")
        git(self.repo.work, "config", "protocol.ext.allow", "always")

        object_path = self.repo.work / ".git" / "objects" / missing_blob[:2] / missing_blob[2:]
        self.assertTrue(object_path.is_file())
        object_path.unlink()

        probe_env = os.environ.copy()
        probe_env.pop("GIT_NO_LAZY_FETCH", None)
        probe = subprocess.run(
            ["git", "cat-file", "-e", missing_blob],
            cwd=self.repo.work,
            env=probe_env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertNotEqual(probe.returncode, 0)
        self.assertTrue(marker.is_file(), "control must prove the promisor transport is executable")
        marker.unlink()

        bundle = self.repo.artifacts / "partial-clone.bundle"
        with self.assertRaises(publication.PublicationError):
            self.repo.publish(bundle.name)

        self.assertFalse(marker.exists(), "publisher must not execute the promisor transport")
        self.assertEqual(self.repo.raw_remote_head(), self.repo.base)
        self.assertEqual(self.repo.raw_escape_head(), "")
        self.assertFalse(bundle.exists())
        self.assertFalse(bundle.with_name(bundle.name + ".tmp").exists())

    def test_local_include_alternate_refs_command_is_rejected_before_bundle(self) -> None:
        alternates = self.repo.work / ".git" / "objects" / "info" / "alternates"
        alternates.write_text(f"{self.repo.remote / 'objects'}\n", encoding="utf-8")

        marker = self.repo.root / "alternate-refs-command-invoked.txt"
        command = self.repo.root / "alternate-refs-command.sh"
        command.write_text(
            "#!/bin/sh\n"
            f"printf 'invoked\\n' > '{marker}'\n"
            f"git -C '{self.repo.work}' push -q '{self.repo.escape}' "
            "HEAD:refs/heads/agent/test\n"
            f"printf '%s\\n' '{self.repo.base}'\n",
            encoding="utf-8",
        )
        command.chmod(0o755)
        included = self.repo.root / "repo-alternate-refs.cfg"
        included.write_text(
            "[core]\n"
            f"\talternateRefsCommand = {command}\n",
            encoding="utf-8",
        )
        git(self.repo.work, "config", "--local", "include.path", str(included))

        bundle = self.repo.artifacts / "alternate-refs-command.bundle"
        with self.assertRaisesRegex(publication.PublicationError, "alternateRefsCommand"):
            self.repo.publish(bundle.name)

        self.assertFalse(marker.exists(), "publisher must not execute alternateRefsCommand")
        self.assertEqual(self.repo.raw_remote_head(), self.repo.base)
        self.assertEqual(self.repo.raw_escape_head(), "")
        self.assertFalse(bundle.exists())
        self.assertFalse(bundle.with_name(bundle.name + ".tmp").exists())

    def test_reserved_unspecified_filter_driver_is_rejected_before_side_publish(self) -> None:
        self.assert_reserved_filter_driver_blocked("unspecified")

    def test_reserved_unset_filter_driver_is_rejected_before_side_publish(self) -> None:
        self.assert_reserved_filter_driver_blocked("unset")

    def test_local_shell_credential_helper_is_rejected_before_readback(self) -> None:
        helper = self.repo.malicious_script("credential-helper.sh")
        git(self.repo.work, "config", "--local", "credential.helper", f"!{helper}")
        self.assert_blocked_without_publication("credential helpers", "local-helper.bundle")

    def test_local_include_credential_helper_is_rejected_before_readback(self) -> None:
        helper = self.repo.malicious_script("included-credential-helper.sh")
        included = self.repo.root / "repo-credential.cfg"
        included.write_text(
            "[credential]\n"
            f"\thelper = !{helper}\n",
            encoding="utf-8",
        )
        git(self.repo.work, "config", "--local", "include.path", str(included))
        self.assert_blocked_without_publication("credential helpers", "included-helper.bundle")

    def test_worktree_credential_helper_is_rejected_before_readback(self) -> None:
        helper = self.repo.malicious_script("worktree-credential-helper.sh")
        git(self.repo.work, "config", "extensions.worktreeConfig", "true")
        git(self.repo.work, "config", "--worktree", "credential.helper", f"!{helper}")
        self.assert_blocked_without_publication("credential helpers", "worktree-helper.bundle")

    def test_global_credential_helper_configuration_is_not_rejected(self) -> None:
        global_config = self.repo.root / "trusted-global.cfg"
        global_config.write_text("[credential]\n\thelper = false\n", encoding="utf-8")
        with mock.patch.dict(os.environ, {"GIT_CONFIG_GLOBAL": str(global_config)}, clear=False):
            result = self.repo.publish("global-helper.bundle")

        self.assertEqual(result.state, "PUBLISHED")
        self.assertEqual(self.repo.raw_remote_head(), self.repo.candidate)
        self.assertEqual(self.repo.raw_escape_head(), "")

    def test_local_ssh_command_is_rejected_before_readback(self) -> None:
        command = self.repo.malicious_script("local-ssh-command.sh")
        git(self.repo.work, "config", "--local", "core.sshCommand", str(command))
        self.assert_blocked_without_publication("transport commands", "local-ssh.bundle")

    def test_local_include_ssh_command_is_rejected_before_readback(self) -> None:
        command = self.repo.malicious_script("included-ssh-command.sh")
        included = self.repo.root / "repo-transport.cfg"
        included.write_text(
            "[core]\n"
            f"\tsshCommand = {command}\n",
            encoding="utf-8",
        )
        git(self.repo.work, "config", "--local", "include.path", str(included))
        self.assert_blocked_without_publication("transport commands", "included-ssh.bundle")

    def test_worktree_ssh_command_is_rejected_before_readback(self) -> None:
        command = self.repo.malicious_script("worktree-ssh-command.sh")
        git(self.repo.work, "config", "extensions.worktreeConfig", "true")
        git(self.repo.work, "config", "--worktree", "core.sshCommand", str(command))
        self.assert_blocked_without_publication("transport commands", "worktree-ssh.bundle")

    def test_local_git_proxy_is_rejected_before_readback(self) -> None:
        command = self.repo.malicious_script("local-git-proxy.sh")
        git(self.repo.work, "config", "--local", "core.gitProxy", str(command))
        self.assert_blocked_without_publication("transport commands", "local-git-proxy.bundle")

    def test_local_askpass_is_rejected_before_readback(self) -> None:
        command = self.repo.malicious_script("local-askpass.sh")
        git(self.repo.work, "config", "--local", "core.askPass", str(command))
        self.assert_blocked_without_publication("transport commands", "local-askpass.bundle")

    def test_global_transport_command_configuration_is_not_rejected(self) -> None:
        global_config = self.repo.root / "trusted-global-transport.cfg"
        global_config.write_text(
            "[core]\n"
            "\tsshCommand = false\n"
            "\tgitProxy = none\n"
            "\taskPass = false\n",
            encoding="utf-8",
        )
        with mock.patch.dict(os.environ, {"GIT_CONFIG_GLOBAL": str(global_config)}, clear=False):
            result = self.repo.publish("global-transport.bundle")

        self.assertEqual(result.state, "PUBLISHED")
        self.assertEqual(self.repo.raw_remote_head(), self.repo.candidate)
        self.assertEqual(self.repo.raw_escape_head(), "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
