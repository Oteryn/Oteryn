#!/usr/bin/env python3
"""Fail-closed exact-candidate publication helper for Oteryn task branches."""
from __future__ import annotations

import argparse
import errno
import hashlib
import os
import re
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
URL_REWRITE_RE = r"^url\..*\.(insteadof|pushinsteadof)$"
CREDENTIAL_HELPER_RE = r"^credential(\..*)?\.helper$"
REPOSITORY_TRANSPORT_COMMAND_RE = r"^core\.(sshcommand|gitproxy|askpass)$"
ALTERNATE_REFS_COMMAND_RE = r"^core\.alternaterefscommand$"
HTTP_ROUTING_TRUST_RE = (
    r"^http(\..*)?\."
    r"(proxy|curloptresolve|extraheader|sslverify|sslcainfo|sslcapath|"
    r"proxysslverify|proxysslcainfo|proxysslcapath)$"
)
NATIVE_PUSH_URL_SCHEMES = frozenset({"ssh", "git", "http", "https", "file"})


class PublicationError(RuntimeError):
    """Raised when publication cannot proceed or cannot be classified safely."""


@dataclass(frozen=True)
class PublicationResult:
    state: str
    candidate: str
    remote_head: str
    recovery_bundle: str | None = None
    recovery_sha256: str | None = None


@dataclass(frozen=True)
class FilesystemEndpointIdentity:
    resolved_path: str
    device: int
    inode: int
    git_directory_path: str
    git_directory_device: int
    git_directory_inode: int
    common_git_directory_path: str
    common_git_directory_device: int
    common_git_directory_inode: int
    commondir_path: str | None
    commondir_device: int | None
    commondir_inode: int | None


def _run_git(
    cwd: Path, *args: str, check: bool = True, pass_fds: tuple[int, ...] = ()
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        env={**os.environ, "GIT_NO_LAZY_FETCH": "1"},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        pass_fds=pass_fds,
        check=False,
    )
    if check and completed.returncode != 0:
        raise PublicationError(f"git {args[0]} failed with exit code {completed.returncode}")
    return completed


def _run_git_input(
    cwd: Path,
    input_text: str,
    *args: str,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        env={**os.environ, "GIT_NO_LAZY_FETCH": "1"},
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and completed.returncode != 0:
        raise PublicationError(f"git {args[0]} failed with exit code {completed.returncode}")
    return completed


def _worktree_root(cwd: Path) -> Path:
    cwd = cwd.resolve()
    result = _run_git(cwd, "rev-parse", "--show-toplevel", check=False)
    if result.returncode != 0 or not result.stdout.rstrip("\r\n"):
        raise PublicationError("publication cwd must be inside a Git worktree")
    return Path(result.stdout.rstrip("\r\n")).resolve()


def _sha(value: str, label: str) -> str:
    value = value.strip().lower()
    if SHA_RE.fullmatch(value) is None:
        raise PublicationError(f"{label} must be a full lowercase 40-character commit SHA")
    return value


def _branch(value: str, cwd: Path) -> str:
    value = value.strip()
    if not value or value.startswith("refs/"):
        raise PublicationError("branch must be an unqualified branch name")
    result = _run_git(cwd, "check-ref-format", "--branch", value, check=False)
    if result.returncode != 0:
        raise PublicationError("branch is not a valid Git branch name")
    return value


def _credential_free_url(value: str, label: str) -> str:
    value = value.strip()
    if not value:
        raise PublicationError(f"{label} must be provided")
    if value.startswith("-") or "\n" in value or "\r" in value or "\x00" in value:
        raise PublicationError(f"{label} is not a safe Git endpoint")
    if "::" in value:
        raise PublicationError(f"{label} must not use explicit Git remote-helper syntax")
    if "://" in value:
        scheme = value.split("://", 1)[0]
        parsed = urlsplit(value)
        if scheme not in NATIVE_PUSH_URL_SCHEMES:
            raise PublicationError(f"{label} must use a supported native Git push URL scheme")
        if parsed.username is not None or parsed.password is not None:
            raise PublicationError(f"{label} must not embed credentials")
        if scheme == "file":
            if parsed.netloc not in ("", "localhost"):
                raise PublicationError(f"{label} must not use an unsupported file URL authority")
            # Git treats literal query/fragment delimiters in file URLs as
            # filesystem-path bytes, whereas urllib parsing separates them.
            # Reject the ambiguous spelling rather than binding and reading a
            # different local repository from the one Git would use.
            if parsed.query or parsed.fragment or "?" in value or "#" in value:
                raise PublicationError(
                    f"{label} must not use query or fragment delimiters in a file URL"
                )
    return value


def _filesystem_endpoint_identity(cwd: Path, endpoint: str) -> FilesystemEndpointIdentity | None:
    endpoint = _credential_free_url(endpoint, "filesystem endpoint")
    if "://" in endpoint:
        parsed = urlsplit(endpoint)
        if parsed.scheme != "file":
            return None
        if parsed.netloc not in ("", "localhost"):
            raise PublicationError(
                "local file publication endpoint must not contain an unsupported authority"
            )
        raw_path = unquote(parsed.path)
        if not raw_path:
            raise PublicationError("local file publication endpoint path is missing")
        path = Path(raw_path)
    else:
        windows_drive = re.match(r"^[A-Za-z]:[\\/]", endpoint) is not None
        scp_like = ":" in endpoint and not endpoint.startswith(("/", "./", "../"))
        if scp_like and not windows_drive:
            return None
        path = Path(endpoint)

    if not path.is_absolute():
        path = cwd / path
    try:
        if path.is_symlink():
            raise PublicationError("local filesystem publication endpoint must not be a symlink")
        resolved = path.resolve(strict=True)
        metadata = resolved.stat()

        # A non-bare repository's worktree is not the object Git opens for
        # ls-remote: Git follows its .git directory (or gitfile). Bind that
        # actual repository object independently so replacing .git cannot
        # redirect readback while leaving the worktree inode unchanged.
        dot_git = resolved / ".git"
        if dot_git.is_symlink():
            raise PublicationError("local filesystem publication Git directory must not be a symlink")
        if dot_git.is_dir():
            git_directory = dot_git.resolve(strict=True)
        elif dot_git.is_file():
            marker = dot_git.read_text(encoding="utf-8").strip()
            if not marker.startswith("gitdir: "):
                raise PublicationError("unable to resolve local filesystem publication Git directory")
            git_directory = Path(marker[8:])
            if not git_directory.is_absolute():
                git_directory = dot_git.parent / git_directory
            git_directory = git_directory.resolve(strict=True)
        else:
            # Bare repositories expose the Git directory at the endpoint.
            git_directory = resolved
        if git_directory.is_symlink() or not git_directory.is_dir():
            raise PublicationError("local filesystem publication Git directory is not stable")
        git_metadata = git_directory.stat()

        # Linked worktrees store refs and objects through an administrative
        # directory's `commondir` indirection.  Pinning only that administrative
        # directory would allow the indirection to be swapped while its inode
        # remains unchanged.  Bind the indirection file and its effective common
        # Git directory as separate filesystem objects.
        commondir = git_directory / "commondir"
        linked_worktree_admin = (git_directory / "gitdir").exists()
        if commondir.is_symlink():
            raise PublicationError("local filesystem publication commondir must not be a symlink")
        if commondir.exists():
            if not commondir.is_file():
                raise PublicationError("local filesystem publication commondir is not stable")
            common_marker = commondir.read_text(encoding="utf-8").strip()
            if not common_marker:
                raise PublicationError("local filesystem publication commondir is missing")
            common_git_directory = Path(common_marker)
            if not common_git_directory.is_absolute():
                common_git_directory = git_directory / common_git_directory
            common_git_directory = common_git_directory.resolve(strict=True)
            if common_git_directory.is_symlink() or not common_git_directory.is_dir():
                raise PublicationError(
                    "local filesystem publication common Git directory is not stable"
                )
            commondir_metadata = commondir.stat()
        elif linked_worktree_admin:
            raise PublicationError("local filesystem publication commondir is missing")
        else:
            common_git_directory = git_directory
            commondir_metadata = None
        common_git_metadata = common_git_directory.stat()
    except PublicationError:
        raise
    except OSError as exc:
        raise PublicationError("unable to bind local filesystem publication endpoint identity") from exc
    return FilesystemEndpointIdentity(
        str(resolved),
        metadata.st_dev,
        metadata.st_ino,
        str(git_directory),
        git_metadata.st_dev,
        git_metadata.st_ino,
        str(common_git_directory),
        common_git_metadata.st_dev,
        common_git_metadata.st_ino,
        str(commondir) if commondir_metadata is not None else None,
        commondir_metadata.st_dev if commondir_metadata is not None else None,
        commondir_metadata.st_ino if commondir_metadata is not None else None,
    )


def _reject_url_rewrites(cwd: Path) -> None:
    result = _run_git(cwd, "config", "--null", "--get-regexp", URL_REWRITE_RE, check=False)
    if result.returncode == 1 and not result.stdout:
        return
    if result.returncode != 0:
        raise PublicationError("unable to verify effective Git URL rewrite configuration")
    if result.stdout:
        raise PublicationError(
            "Git URL rewrite rules are not permitted for exact-candidate publication"
        )


def _scope_has_credential_helpers(cwd: Path, scope: str) -> bool:
    result = _run_git(
        cwd,
        "config",
        scope,
        "--includes",
        "--null",
        "--get-regexp",
        CREDENTIAL_HELPER_RE,
        check=False,
    )
    if result.returncode == 1 and not result.stdout:
        return False
    if result.returncode != 0:
        raise PublicationError(
            "unable to verify repository/worktree Git credential-helper configuration"
        )
    return bool(result.stdout)


def _reject_repository_credential_helpers(cwd: Path) -> None:
    if _scope_has_credential_helpers(cwd, "--local") or _scope_has_credential_helpers(
        cwd, "--worktree"
    ):
        raise PublicationError(
            "repository/worktree Git credential helpers are not permitted for exact-candidate "
            "publication; use an authorized system/global credential path instead"
        )


def _scope_has_transport_commands(cwd: Path, scope: str) -> bool:
    result = _run_git(
        cwd,
        "config",
        scope,
        "--includes",
        "--null",
        "--get-regexp",
        REPOSITORY_TRANSPORT_COMMAND_RE,
        check=False,
    )
    if result.returncode == 1 and not result.stdout:
        return False
    if result.returncode != 0:
        raise PublicationError(
            "unable to verify repository/worktree Git transport-command configuration"
        )
    return bool(result.stdout)


def _reject_repository_transport_commands(cwd: Path) -> None:
    if _scope_has_transport_commands(cwd, "--local") or _scope_has_transport_commands(
        cwd, "--worktree"
    ):
        raise PublicationError(
            "repository/worktree Git transport commands (core.sshCommand/core.gitProxy/core.askPass) "
            "are not permitted for exact-candidate publication; use an authorized system/global "
            "transport path instead"
        )


def _scope_has_alternate_refs_command(cwd: Path, scope: str) -> bool:
    result = _run_git(
        cwd,
        "config",
        scope,
        "--includes",
        "--null",
        "--get-regexp",
        ALTERNATE_REFS_COMMAND_RE,
        check=False,
    )
    if result.returncode == 1 and not result.stdout:
        return False
    if result.returncode != 0:
        raise PublicationError(
            "unable to verify repository/worktree Git alternate-ref command configuration"
        )
    return bool(result.stdout)


def _reject_repository_alternate_refs_commands(cwd: Path) -> None:
    if _scope_has_alternate_refs_command(cwd, "--local") or _scope_has_alternate_refs_command(
        cwd, "--worktree"
    ):
        raise PublicationError(
            "repository/worktree core.alternateRefsCommand is not permitted for "
            "exact-candidate publication"
        )


def _scope_has_http_routing_trust_overrides(cwd: Path, scope: str, remote: str) -> bool:
    result = _run_git(
        cwd, "config", scope, "--includes", "--null", "--get-regexp",
        HTTP_ROUTING_TRUST_RE, check=False,
    )
    if result.returncode not in (0, 1):
        raise PublicationError(
            "unable to verify repository/worktree Git HTTP routing/TLS configuration"
        )
    if result.stdout:
        return True
    result = _run_git(
        cwd, "config", scope, "--includes", "--null", "--get-all",
        f"remote.{remote}.proxy", check=False,
    )
    if result.returncode == 1 and not result.stdout:
        return False
    if result.returncode != 0:
        raise PublicationError(
            "unable to verify repository/worktree selected-remote proxy configuration"
        )
    return bool(result.stdout)


def _reject_repository_http_routing_trust_overrides(cwd: Path, remote: str) -> None:
    if _scope_has_http_routing_trust_overrides(
        cwd, "--local", remote
    ) or _scope_has_http_routing_trust_overrides(cwd, "--worktree", remote):
        raise PublicationError(
            "repository/worktree Git HTTP routing or TLS-trust overrides are not permitted "
            "for exact-candidate publication"
        )


def _active_filter_drivers(cwd: Path, hooks_dir: str) -> set[str]:
    tracked = _run_git(
        cwd,
        "--no-optional-locks",
        "-c",
        "core.fsmonitor=false",
        "-c",
        f"core.hooksPath={hooks_dir}",
        "ls-files",
        "-z",
    ).stdout
    if not tracked:
        return set()

    attrs = _run_git_input(
        cwd,
        tracked,
        "--no-optional-locks",
        "-c",
        "core.fsmonitor=false",
        "-c",
        f"core.hooksPath={hooks_dir}",
        "check-attr",
        "-z",
        "--stdin",
        "--all",
    ).stdout.split("\0")
    if attrs and attrs[-1] == "":
        attrs.pop()
    if len(attrs) % 3 != 0:
        raise PublicationError("unable to parse active Git filter attributes")

    drivers: set[str] = set()
    for index in range(0, len(attrs), 3):
        _path, attribute, value = attrs[index : index + 3]
        if attribute != "filter":
            continue
        if value:
            drivers.add(value)
    return drivers


def _reject_active_executable_filters(cwd: Path, hooks_dir: str) -> None:
    for driver in sorted(_active_filter_drivers(cwd, hooks_dir)):
        for operation in ("clean", "process"):
            result = _run_git(
                cwd,
                "config",
                "--get-all",
                f"filter.{driver}.{operation}",
                check=False,
            )
            if result.returncode == 1 and not result.stdout:
                continue
            if result.returncode != 0:
                raise PublicationError(
                    f"unable to verify active Git filter configuration for {driver!r}"
                )
            if result.stdout:
                raise PublicationError(
                    "active executable Git clean/process filters are not permitted for "
                    "exact-candidate publication"
                )


def _reject_history_overrides(cwd: Path) -> None:
    if os.environ.get("GIT_REPLACE_REF_BASE"):
        raise PublicationError("Git replacement-history overrides are not permitted for publication")

    replace_refs = _run_git(cwd, "for-each-ref", "--format=%(refname)", "refs/replace/").stdout
    if replace_refs.strip():
        raise PublicationError("Git replacement-history overrides are not permitted for publication")

    graft_result = _run_git(cwd, "rev-parse", "--git-path", "info/grafts")
    graft_path = Path(graft_result.stdout.strip())
    if not graft_path.is_absolute():
        graft_path = cwd / graft_path
    try:
        if graft_path.is_file() and graft_path.stat().st_size > 0:
            raise PublicationError("Git graft-history overrides are not permitted for publication")
    except OSError as exc:
        raise PublicationError("unable to verify Git graft-history state") from exc


def _remote_push_endpoint(cwd: Path, value: str, expected_push_url: str) -> str:
    _reject_url_rewrites(cwd)
    _reject_repository_credential_helpers(cwd)
    _reject_repository_transport_commands(cwd)
    _reject_repository_alternate_refs_commands(cwd)
    value = value.strip()
    if not value or value.startswith("-") or any(char.isspace() for char in value):
        raise PublicationError("remote must be an existing Git remote name")
    names = {line.strip() for line in _run_git(cwd, "remote").stdout.splitlines() if line.strip()}
    if value not in names:
        raise PublicationError("remote must be an existing Git remote name")
    _reject_repository_http_routing_trust_overrides(cwd, value)

    expected = _credential_free_url(expected_push_url, "expected push URL")
    configured = [
        _credential_free_url(line, "configured push URL")
        for line in _run_git(cwd, "remote", "get-url", "--push", "--all", value).stdout.splitlines()
        if line.strip()
    ]
    if len(configured) != 1:
        raise PublicationError("remote must resolve to exactly one configured push URL")
    if configured[0] != expected:
        raise PublicationError("configured push URL does not match the approved publication target")
    if expected in names:
        raise PublicationError(
            "approved push URL is ambiguous because it is also a configured Git remote name"
        )
    legacy_alias = _run_git(cwd, "remote", "get-url", "--all", expected, check=False)
    if legacy_alias.returncode == 0:
        raise PublicationError(
            "approved push URL is ambiguous because Git resolves it through a legacy remote alias"
        )
    if legacy_alias.returncode != 2:
        raise PublicationError("unable to verify legacy Git remote alias resolution")
    return configured[0]


def _rev_parse(cwd: Path, revision: str) -> str:
    result = _run_git(cwd, "rev-parse", "--verify", f"{revision}^{{commit}}")
    value = result.stdout.strip().lower()
    return _sha(value, f"resolved revision {revision!r}")


def _current_branch_ref(cwd: Path) -> str:
    result = _run_git(cwd, "symbolic-ref", "--quiet", "HEAD", check=False)
    if result.returncode != 0 or not result.stdout.strip():
        raise PublicationError("publication requires a checked-out local branch, not detached HEAD")
    return result.stdout.strip()


def _is_ancestor(cwd: Path, ancestor: str, descendant: str) -> bool:
    _reject_history_overrides(cwd)
    result = _run_git(
        cwd,
        "--no-replace-objects",
        "merge-base",
        "--is-ancestor",
        ancestor,
        descendant,
        check=False,
    )
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    raise PublicationError("unable to determine candidate ancestry")


def _reject_hidden_index_entries(cwd: Path, hooks_dir: str) -> None:
    result = _run_git(
        cwd,
        "--no-optional-locks",
        "-c",
        "core.fsmonitor=false",
        "-c",
        f"core.hooksPath={hooks_dir}",
        "ls-files",
        "-v",
        "-z",
    )
    for record in result.stdout.split("\0"):
        if not record:
            continue
        tag = record[0]
        if tag == "S" or tag.islower():
            raise PublicationError(
                "publication rejects tracked skip-worktree/assume-unchanged index flags; "
                "clear them before exact-candidate clean-worktree verification"
            )


def _gitlink_paths(cwd: Path, hooks_dir: str) -> list[str]:
    result = _run_git(
        cwd,
        "--no-optional-locks",
        "-c",
        "core.fsmonitor=false",
        "-c",
        f"core.hooksPath={hooks_dir}",
        "ls-files",
        "--stage",
        "-z",
    )
    paths: list[str] = []
    for record in result.stdout.split("\0"):
        if not record:
            continue
        metadata, separator, path = record.partition("\t")
        if not separator:
            raise PublicationError("unable to parse tracked Git index entry")
        mode = metadata.split(" ", 1)[0]
        if mode == "160000":
            paths.append(path)
    return paths


def _reject_present_submodule_worktrees(cwd: Path, hooks_dir: str) -> None:
    for relative in _gitlink_paths(cwd, hooks_dir):
        path = cwd / relative
        try:
            if path.is_symlink() or path.is_file():
                raise PublicationError(
                    "publication requires tracked submodule worktrees to be deinitialized/absent"
                )
            if path.is_dir() and any(path.iterdir()):
                raise PublicationError(
                    "publication requires tracked submodule worktrees to be deinitialized/empty"
                )
        except OSError as exc:
            raise PublicationError("unable to verify tracked submodule worktree state") from exc


def _require_clean_worktree(cwd: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="oteryn-publication-no-hooks-") as hooks_dir:
        _reject_present_submodule_worktrees(cwd, hooks_dir)
        _reject_active_executable_filters(cwd, hooks_dir)
        _reject_hidden_index_entries(cwd, hooks_dir)
        status = _run_git(
            cwd,
            "--no-optional-locks",
            "-c",
            "core.fsmonitor=false",
            "-c",
            f"core.hooksPath={hooks_dir}",
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--ignore-submodules=all",
        ).stdout
    if status.strip():
        raise PublicationError(
            "publication requires a clean isolated worktree so the recovery artifact matches all intended work"
        )


def remote_head(cwd: Path, endpoint: str, branch: str) -> str:
    endpoint = _credential_free_url(endpoint, "readback endpoint")
    cwd = _worktree_root(cwd)
    _reject_url_rewrites(cwd)
    _reject_repository_credential_helpers(cwd)
    _reject_repository_transport_commands(cwd)
    _reject_repository_alternate_refs_commands(cwd)
    branch = _branch(branch, cwd)
    branch_ref = f"refs/heads/{branch}"
    result = _run_git(cwd, "ls-remote", "--heads", endpoint, branch_ref, check=False)
    if result.returncode != 0:
        raise PublicationError("remote head readback is unavailable")
    rows = [line.split() for line in result.stdout.splitlines() if line.strip()]
    rows = [row for row in rows if len(row) == 2 and row[1] == branch_ref]
    if len(rows) != 1:
        raise PublicationError("remote branch is missing or ambiguous")
    return _sha(rows[0][0], "remote head")


def _stable_local_remote_head(
    cwd: Path,
    identity: FilesystemEndpointIdentity,
    branch: str,
    *,
    classify_against: tuple[str, str] | None = None,
    git_descriptor: int | None = None,
    common_descriptor: int | None = None,
) -> str | tuple[str, str]:
    """Read a local endpoint while holding its branch update lock."""
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    owns_descriptors = git_descriptor is None and common_descriptor is None
    if (git_descriptor is None) != (common_descriptor is None):
        raise PublicationError("incomplete stable local publication endpoint handles")
    if owns_descriptors:
        try:
            git_descriptor = os.open(identity.git_directory_path, flags)
            common_descriptor = os.open(identity.common_git_directory_path, flags)
        except OSError as exc:
            if git_descriptor is not None:
                os.close(git_descriptor)
            raise PublicationError("unable to open a stable local publication endpoint") from exc
    assert git_descriptor is not None and common_descriptor is not None
    pinned_packed_descriptor: int | None = None
    pinned_packed_identity: tuple[int, int] | None = None

    def verify_pinned_packed_storage() -> None:
        """Keep the exact packed-ref object authoritative through classification."""
        if pinned_packed_descriptor is None or pinned_packed_identity is None:
            return
        metadata = os.fstat(pinned_packed_descriptor)
        if (metadata.st_dev, metadata.st_ino) != pinned_packed_identity:
            raise PublicationError("packed-refs storage changed during classification")
        verification = os.open(
            "packed-refs",
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=common_descriptor,
        )
        try:
            verify_metadata = os.fstat(verification)
            if (verify_metadata.st_dev, verify_metadata.st_ino) != pinned_packed_identity:
                raise PublicationError("packed-refs storage changed during classification")
        finally:
            os.close(verification)

    try:
        metadata = os.fstat(git_descriptor)
        if (metadata.st_dev, metadata.st_ino) != (
            identity.git_directory_device,
            identity.git_directory_inode,
        ):
            raise PublicationError("approved local filesystem Git directory identity changed")
        common_metadata = os.fstat(common_descriptor)
        if (common_metadata.st_dev, common_metadata.st_ino) != (
            identity.common_git_directory_device,
            identity.common_git_directory_inode,
        ):
            raise PublicationError("approved local filesystem common Git directory identity changed")
        proc_endpoint = f"/proc/self/fd/{common_descriptor}"
        if not Path(proc_endpoint).exists():
            raise PublicationError("stable local filesystem endpoint handles are unavailable")

        branch = _branch(branch, cwd)
        branch_ref = f"refs/heads/{branch}"

        # Directory descriptors pin repository identity, but they do not pin
        # mutable ref contents.  Acquire the same per-ref lock used by Git's
        # files backend and retain it through classification.  A writer using
        # the supported Git mutation path therefore cannot restore a previous
        # value after the last observation but before the decision is made.
        # Fail closed if the ref hierarchy is unavailable, symlinked, or
        # already locked rather than sampling an inherently movable value.
        lock_parent = common_descriptor
        opened_parents: list[int] = []
        opened_parent_identities: list[tuple[int, int]] = []
        lock_name = ""
        lock_descriptor: int | None = None
        try:
            components = branch_ref.split("/")
            for component in components[:-1]:
                try:
                    next_parent = os.open(component, flags, dir_fd=lock_parent)
                except FileNotFoundError:
                    # A packed-only nested branch need not have a corresponding
                    # loose-ref directory hierarchy.  Create each missing
                    # component relative to the already-open, verified parent,
                    # then open it without following symlinks.  This mirrors
                    # Git's loose-ref layout without trusting a path resolved
                    # outside the bound common Git directory.
                    try:
                        os.mkdir(component, 0o777, dir_fd=lock_parent)
                    except FileExistsError:
                        # Another process may have created the component.  The
                        # no-follow open below still decides whether it is safe.
                        pass
                    next_parent = os.open(component, flags, dir_fd=lock_parent)
                opened_parents.append(next_parent)
                parent_metadata = os.fstat(next_parent)
                opened_parent_identities.append(
                    (parent_metadata.st_dev, parent_metadata.st_ino)
                )
                lock_parent = next_parent
            lock_name = components[-1] + ".lock"
            lock_descriptor = os.open(
                lock_name,
                os.O_WRONLY
                | os.O_CREAT
                | os.O_EXCL
                | getattr(os, "O_NOFOLLOW", 0),
                0o600,
                dir_fd=lock_parent,
            )
        except OSError as exc:
            for descriptor in reversed(opened_parents):
                os.close(descriptor)
            raise PublicationError(
                "unable to acquire stable local publication branch lock"
            ) from exc

        def stable_readback() -> str:
            nonlocal pinned_packed_descriptor, pinned_packed_identity
            result = _run_git(
                cwd,
                "ls-remote",
                "--heads",
                proc_endpoint,
                branch_ref,
                check=False,
                pass_fds=(git_descriptor, common_descriptor),
            )
            if result.returncode != 0:
                raise PublicationError("remote head readback is unavailable")
            rows = [line.split() for line in result.stdout.splitlines() if line.strip()]
            rows = [row for row in rows if len(row) == 2 and row[1] == branch_ref]
            if len(rows) != 1:
                raise PublicationError("remote branch is missing or ambiguous")
            ls_remote_head = _sha(rows[0][0], "remote head")

            # Do not re-resolve the ref from the common-directory pathname.
            # The already-open parent descriptors are the authority for loose
            # storage.  When no loose ref exists, pin packed-refs itself and
            # read it through that descriptor.  This prevents a parent
            # directory rename/replacement/restoration around ls-remote from
            # supplying evidence from a replacement loose ref.
            ref_descriptor: int | None = None
            try:
                ref_descriptor = os.open(
                    components[-1],
                    os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=lock_parent,
                )
            except FileNotFoundError:
                pass
            except OSError as exc:
                raise PublicationError(
                    "unable to read pinned local publication branch ref"
                ) from exc

            if ref_descriptor is not None:
                try:
                    metadata = os.fstat(ref_descriptor)
                    if not stat.S_ISREG(metadata.st_mode):
                        raise PublicationError(
                            "local publication branch ref storage is not a regular file"
                        )
                    with os.fdopen(os.dup(ref_descriptor), "rb") as ref_file:
                        value = ref_file.readline(256)
                    if value.startswith(b"ref:"):
                        raise PublicationError(
                            "symbolic local publication target branches are not supported"
                        )
                    pinned_head = _sha(value.decode("ascii").strip(), "remote head")
                except (UnicodeDecodeError, OSError) as exc:
                    raise PublicationError(
                        "unable to read pinned local publication branch ref"
                    ) from exc
                finally:
                    os.close(ref_descriptor)
            else:
                try:
                    pinned_packed_descriptor = os.open(
                        "packed-refs",
                        os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
                        dir_fd=common_descriptor,
                    )
                    packed_metadata = os.fstat(pinned_packed_descriptor)
                    if not stat.S_ISREG(packed_metadata.st_mode):
                        raise PublicationError("packed-refs storage is not a regular file")
                    pinned_packed_identity = (packed_metadata.st_dev, packed_metadata.st_ino)
                    with os.fdopen(
                        os.dup(pinned_packed_descriptor), "r", encoding="ascii"
                    ) as packed:
                        matches = [
                            line.split(" ", 1)[0]
                            for line in packed
                            if not line.startswith(("#", "^"))
                            and line.rstrip("\n").endswith(f" {branch_ref}")
                        ]
                    if len(matches) != 1:
                        raise PublicationError("remote branch is missing or ambiguous")
                    pinned_head = _sha(matches[0], "remote head")

                    verify_pinned_packed_storage()
                except FileNotFoundError as exc:
                    raise PublicationError("remote branch is missing or ambiguous") from exc
                except (UnicodeDecodeError, OSError) as exc:
                    raise PublicationError("unable to read pinned packed-refs storage") from exc

            if pinned_head != ls_remote_head:
                raise PublicationError("local publication branch changed during readback")
            return pinned_head

        def verify_ref_hierarchy() -> None:
            """Prove the named lock still belongs to the bound ref hierarchy."""
            parent = common_descriptor
            verification_descriptors: list[int] = []
            try:
                for component, expected_identity in zip(
                    components[:-1], opened_parent_identities, strict=True
                ):
                    descriptor = os.open(component, flags, dir_fd=parent)
                    verification_descriptors.append(descriptor)
                    metadata = os.fstat(descriptor)
                    if (metadata.st_dev, metadata.st_ino) != expected_identity:
                        raise PublicationError(
                            "local publication branch ref hierarchy changed"
                        )
                    parent = descriptor
            except OSError as exc:
                raise PublicationError(
                    "unable to verify local publication branch ref hierarchy"
                ) from exc
            finally:
                for descriptor in reversed(verification_descriptors):
                    os.close(descriptor)

        try:
            # A symbolic branch delegates its value to another ref. The named
            # lock above does not protect that referent, so reject symbolic
            # publication targets while the named lock is held.
            ref_descriptor: int | None = None
            try:
                ref_descriptor = os.open(
                    components[-1],
                    os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=lock_parent,
                )
            except OSError as exc:
                if exc.errno != errno.ENOENT:
                    raise PublicationError(
                        "unable to verify local publication branch ref storage"
                    ) from exc
            if ref_descriptor is not None:
                try:
                    ref_metadata = os.fstat(ref_descriptor)
                    if not stat.S_ISREG(ref_metadata.st_mode):
                        raise PublicationError(
                            "local publication branch ref storage is not a regular file"
                        )
                    # Git accepts whitespace other than a single space after
                    # the symbolic-ref header (for example ``ref:\t...``).
                    # Reject the syntax marker itself before accepting local
                    # evidence because the named lock does not cover referents.
                    if os.read(ref_descriptor, 4) == b"ref:":
                        raise PublicationError(
                            "symbolic local publication target branches are not supported"
                        )
                finally:
                    os.close(ref_descriptor)

            observed = stable_readback()
            metadata = os.fstat(git_descriptor)
            if (metadata.st_dev, metadata.st_ino) != (
                identity.git_directory_device,
                identity.git_directory_inode,
            ):
                raise PublicationError("approved local filesystem Git directory identity changed")
            common_metadata = os.fstat(common_descriptor)
            if (common_metadata.st_dev, common_metadata.st_ino) != (
                identity.common_git_directory_device,
                identity.common_git_directory_inode,
            ):
                raise PublicationError(
                    "approved local filesystem common Git directory identity changed"
                )
            current = _filesystem_endpoint_identity(cwd, identity.resolved_path)
            if current != identity:
                raise PublicationError("approved local filesystem endpoint identity changed")
            verify_ref_hierarchy()
            if classify_against is None:
                verify_pinned_packed_storage()
                return observed
            expected, candidate = classify_against
            verify_pinned_packed_storage()
            state = classify_remote_state(observed, expected, candidate)
            # Classification callbacks and concurrent filesystem actors must
            # not be able to restore predecessor storage after the last check
            # but before success evidence leaves this protected boundary.
            verify_pinned_packed_storage()
            return observed, state
        finally:
            if pinned_packed_descriptor is not None:
                os.close(pinned_packed_descriptor)
            assert lock_descriptor is not None
            os.close(lock_descriptor)
            try:
                os.unlink(lock_name, dir_fd=lock_parent)
            finally:
                for descriptor in reversed(opened_parents):
                    os.close(descriptor)
    finally:
        if owns_descriptors:
            os.close(common_descriptor)
            os.close(git_descriptor)


def classify_remote_state(remote: str, expected: str, candidate: str) -> str:
    remote = _sha(remote, "remote head")
    expected = _sha(expected, "expected remote head")
    candidate = _sha(candidate, "candidate")
    if remote == candidate:
        return "PUBLISHED"
    if remote == expected:
        return "NOT_PUBLISHED"
    return "REMOTE_HEAD_DRIFT"


def _outside_worktree(cwd: Path, bundle: Path) -> None:
    worktree = Path(_run_git(cwd, "rev-parse", "--show-toplevel").stdout.strip()).resolve()
    target = bundle.resolve()
    try:
        target.relative_to(worktree)
    except ValueError:
        return
    raise PublicationError("recovery bundle must be stored outside the disposable worktree")


def create_recovery_bundle(
    cwd: Path,
    *,
    branch: str,
    expected_remote_head: str,
    candidate: str,
    bundle_path: Path,
) -> tuple[Path, str]:
    cwd = _worktree_root(cwd)
    # Bundle revision walking may enumerate alternate refs by executing this
    # repository-controlled command, so fence it before any recovery work.
    _reject_repository_alternate_refs_commands(cwd)
    branch = _branch(branch, cwd)
    branch_ref = f"refs/heads/{branch}"
    expected_remote_head = _sha(expected_remote_head, "expected remote head")
    candidate = _sha(candidate, "candidate")
    if _rev_parse(cwd, branch_ref) != candidate:
        raise PublicationError("recovery branch does not point to the exact candidate")
    if _rev_parse(cwd, expected_remote_head) != expected_remote_head:
        raise PublicationError("recovery predecessor is not available as a local commit")
    if not _is_ancestor(cwd, expected_remote_head, candidate):
        raise PublicationError("recovery candidate is not a descendant of the expected predecessor")

    _outside_worktree(cwd, bundle_path)
    bundle_path = bundle_path.resolve()
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    if bundle_path.exists():
        raise PublicationError("recovery bundle path already exists")
    temporary = bundle_path.with_name(bundle_path.name + ".tmp")
    if temporary.exists():
        raise PublicationError("recovery temporary path already exists")
    try:
        _run_git(
            cwd,
            "bundle",
            "create",
            str(temporary),
            branch_ref,
            f"^{expected_remote_head}",
        )
        _run_git(cwd, "bundle", "verify", str(temporary))
        heads = _run_git(cwd, "bundle", "list-heads", str(temporary)).stdout.splitlines()
        advertised = {
            parts[1]: parts[0].lower()
            for line in heads
            if len(parts := line.split()) == 2 and SHA_RE.fullmatch(parts[0].lower())
        }
        if advertised.get(branch_ref) != candidate:
            raise PublicationError("recovery bundle does not advertise the exact candidate branch head")
        digest = hashlib.sha256(temporary.read_bytes()).hexdigest()
        temporary.replace(bundle_path)
        return bundle_path, digest
    finally:
        if temporary.exists():
            temporary.unlink()


def preflight(
    cwd: Path,
    *,
    remote: str,
    expected_push_url: str,
    branch: str,
    expected_remote_head: str,
    candidate: str,
) -> str:
    expected_push_url = _credential_free_url(expected_push_url, "expected push URL")
    cwd = _worktree_root(cwd)
    endpoint = _remote_push_endpoint(cwd, remote, expected_push_url)
    branch = _branch(branch, cwd)
    branch_ref = f"refs/heads/{branch}"
    expected_remote_head = _sha(expected_remote_head, "expected remote head")
    candidate = _sha(candidate, "candidate")

    if _current_branch_ref(cwd) != branch_ref:
        raise PublicationError("checked-out local branch does not match the authorized target branch")
    if _rev_parse(cwd, "HEAD") != candidate:
        raise PublicationError("local HEAD does not equal the exact candidate")
    _require_clean_worktree(cwd)
    if _rev_parse(cwd, expected_remote_head) != expected_remote_head:
        raise PublicationError("expected remote predecessor is not available as a local commit")
    if not _is_ancestor(cwd, expected_remote_head, candidate):
        raise PublicationError("candidate is not a fast-forward descendant of the expected remote head")

    endpoint_identity = _filesystem_endpoint_identity(cwd, endpoint)
    if endpoint_identity is None:
        live = remote_head(cwd, endpoint, branch)
        state = classify_remote_state(live, expected_remote_head, candidate)
    else:
        # Local preflight evidence must meet the same identity and content
        # stability standard as post-push reconciliation.
        stable = _stable_local_remote_head(
            cwd,
            endpoint_identity,
            branch,
            classify_against=(expected_remote_head, candidate),
        )
        assert isinstance(stable, tuple)
        live, state = stable
    if state == "REMOTE_HEAD_DRIFT":
        raise PublicationError("remote head moved away from the expected publication fence")
    return state


def publish(
    cwd: Path,
    *,
    remote: str,
    expected_push_url: str,
    branch: str,
    expected_remote_head: str,
    candidate: str,
    recovery_bundle: Path,
) -> PublicationResult:
    expected_push_url = _credential_free_url(expected_push_url, "expected push URL")
    cwd = _worktree_root(cwd)
    branch = _branch(branch, cwd)
    branch_ref = f"refs/heads/{branch}"
    expected_remote_head = _sha(expected_remote_head, "expected remote head")
    candidate = _sha(candidate, "candidate")
    initial_endpoint = _remote_push_endpoint(cwd, remote, expected_push_url)
    initial_identity = _filesystem_endpoint_identity(cwd, initial_endpoint)
    if initial_identity is not None and initial_identity.commondir_path is not None:
        # A descriptor for the per-worktree administrative directory does not
        # bind receive-pack's subsequent read of its mutable commondir file.
        # Until mutation can be expressed against an immutable common-dir
        # binding, linked-worktree local publication targets fail closed.
        raise PublicationError(
            "linked-worktree local publication targets are not supported for mutation"
        )
    state = preflight(
        cwd,
        remote=remote,
        expected_push_url=expected_push_url,
        branch=branch,
        expected_remote_head=expected_remote_head,
        candidate=candidate,
    )
    if state == "PUBLISHED":
        return PublicationResult(state="ALREADY_PUBLISHED", candidate=candidate, remote_head=candidate)

    bundle, bundle_sha256 = create_recovery_bundle(
        cwd,
        branch=branch,
        expected_remote_head=expected_remote_head,
        candidate=candidate,
        bundle_path=recovery_bundle,
    )

    endpoint = _remote_push_endpoint(cwd, remote, expected_push_url)
    endpoint_identity = _filesystem_endpoint_identity(cwd, endpoint)
    git_descriptor: int | None = None
    common_descriptor: int | None = None
    try:
        push_endpoint = endpoint
        push_pass_fds: tuple[int, ...] = ()
        if endpoint_identity is not None:
            flags = (
                os.O_RDONLY
                | getattr(os, "O_DIRECTORY", 0)
                | getattr(os, "O_NOFOLLOW", 0)
            )
            try:
                git_descriptor = os.open(endpoint_identity.git_directory_path, flags)
                common_descriptor = os.open(
                    endpoint_identity.common_git_directory_path, flags
                )
            except OSError as exc:
                if git_descriptor is not None:
                    os.close(git_descriptor)
                    git_descriptor = None
                raise PublicationError(
                    "unable to pin local publication endpoint through mutation"
                ) from exc
            assert git_descriptor is not None and common_descriptor is not None
            git_metadata = os.fstat(git_descriptor)
            common_metadata = os.fstat(common_descriptor)
            if (git_metadata.st_dev, git_metadata.st_ino) != (
                endpoint_identity.git_directory_device,
                endpoint_identity.git_directory_inode,
            ) or (common_metadata.st_dev, common_metadata.st_ino) != (
                endpoint_identity.common_git_directory_device,
                endpoint_identity.common_git_directory_inode,
            ):
                raise PublicationError(
                    "approved local filesystem endpoint identity changed before publication"
                )
            push_endpoint = f"/proc/self/fd/{git_descriptor}"
            if not Path(push_endpoint).exists():
                raise PublicationError(
                    "stable local filesystem endpoint handles are unavailable"
                )
            push_pass_fds = (git_descriptor, common_descriptor)

        push = _run_git(
            cwd,
            "-c",
            "push.pushOption=",
            "push",
            "--no-verify",
            "--porcelain",
            "--recurse-submodules=no",
            "--no-follow-tags",
            "--no-signed",
            f"--force-with-lease={branch_ref}:{expected_remote_head}",
            push_endpoint,
            f"{candidate}:{branch_ref}",
            check=False,
            pass_fds=push_pass_fds,
        )

        readback_endpoint = _remote_push_endpoint(cwd, remote, expected_push_url)
        if readback_endpoint != endpoint:
            raise PublicationError("approved push endpoint changed during publication")
        readback_identity = _filesystem_endpoint_identity(cwd, readback_endpoint)
        if endpoint_identity != readback_identity:
            raise PublicationError("approved local filesystem endpoint identity changed during publication")
        if endpoint_identity is None:
            live = remote_head(cwd, readback_endpoint, branch)
            final_state = classify_remote_state(live, expected_remote_head, candidate)
        else:
            stable = _stable_local_remote_head(
                cwd,
                endpoint_identity,
                branch,
                classify_against=(expected_remote_head, candidate),
                git_descriptor=git_descriptor,
                common_descriptor=common_descriptor,
            )
            assert isinstance(stable, tuple)
            live, final_state = stable
    except PublicationError as exc:
        raise PublicationError(
            f"ambiguous publication outcome; remote readback unavailable; verified recovery bundle={bundle}"
        ) from exc
    finally:
        if common_descriptor is not None:
            os.close(common_descriptor)
        if git_descriptor is not None:
            os.close(git_descriptor)

    if final_state == "PUBLISHED":
        return PublicationResult(
            state="PUBLISHED",
            candidate=candidate,
            remote_head=live,
            recovery_bundle=str(bundle),
            recovery_sha256=bundle_sha256,
        )
    if final_state == "NOT_PUBLISHED":
        raise PublicationError(
            "publication did not advance the remote head; do not retry before diagnosing the exact "
            f"capability failure; verified recovery bundle={bundle}; push_exit={push.returncode}"
        )
    raise PublicationError(
        "remote head changed to a third SHA during publication; stop and reconcile ownership/state; "
        f"verified recovery bundle={bundle}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwd", default=".", help="Git worktree containing the exact candidate")
    parser.add_argument("--remote", default="origin", help="Existing approved Git remote name")
    parser.add_argument(
        "--expected-push-url",
        required=True,
        help="Exact sole approved push URL already configured for the selected remote",
    )
    parser.add_argument("--branch", required=True, help="Unqualified canonical task branch name")
    parser.add_argument("--expected-remote-head", required=True, help="Expected current remote branch SHA")
    parser.add_argument("--candidate", required=True, help="Exact local candidate SHA")
    parser.add_argument("--recovery-bundle", required=True, help="Path outside the disposable worktree")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = publish(
            Path(args.cwd),
            remote=args.remote,
            expected_push_url=args.expected_push_url,
            branch=args.branch,
            expected_remote_head=args.expected_remote_head,
            candidate=args.candidate,
            recovery_bundle=Path(args.recovery_bundle),
        )
    except PublicationError as exc:
        print(f"BLOCKED publication integrity: {exc}")
        return 2
    print(
        f"PASS publication integrity: state={result.state} candidate={result.candidate} "
        f"remote_head={result.remote_head} recovery_bundle={result.recovery_bundle or '-'} "
        f"recovery_sha256={result.recovery_sha256 or '-'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
