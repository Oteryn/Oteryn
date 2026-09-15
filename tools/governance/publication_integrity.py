#!/usr/bin/env python3
"""Fail-closed exact-candidate publication helper for Oteryn task branches."""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
URL_REWRITE_RE = r"^url\..*\.(insteadof|pushinsteadof)$"
CREDENTIAL_HELPER_RE = r"^credential(\..*)?\.helper$"
REPOSITORY_TRANSPORT_COMMAND_RE = r"^core\.(sshcommand|gitproxy|askpass)$"


class PublicationError(RuntimeError):
    """Raised when publication cannot proceed or cannot be classified safely."""


@dataclass(frozen=True)
class PublicationResult:
    state: str
    candidate: str
    remote_head: str
    recovery_bundle: str | None = None
    recovery_sha256: str | None = None


def _run_git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
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
    if "://" in value:
        parsed = urlsplit(value)
        if parsed.username is not None or parsed.password is not None:
            raise PublicationError(f"{label} must not embed credentials")
    return value


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
        "filter",
    ).stdout.split("\0")
    if attrs and attrs[-1] == "":
        attrs.pop()
    if len(attrs) % 3 != 0:
        raise PublicationError("unable to parse active Git filter attributes")

    drivers: set[str] = set()
    for index in range(0, len(attrs), 3):
        _path, attribute, value = attrs[index : index + 3]
        if attribute != "filter":
            raise PublicationError("unexpected Git attribute response while checking filters")
        if value not in {"", "unspecified", "unset"}:
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
    value = value.strip()
    if not value or value.startswith("-") or any(char.isspace() for char in value):
        raise PublicationError("remote must be an existing Git remote name")
    names = {line.strip() for line in _run_git(cwd, "remote").stdout.splitlines() if line.strip()}
    if value not in names:
        raise PublicationError("remote must be an existing Git remote name")

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
    return configured[0]


def _rev_parse(cwd: Path, revision: str) -> str:
    result = _run_git(cwd, "rev-parse", "--verify", f"{revision}^{{commit}}")
    value = result.stdout.strip().lower()
    return _sha(value, f"resolved revision {revision!r}")


def _current_branch(cwd: Path) -> str:
    result = _run_git(cwd, "symbolic-ref", "--quiet", "--short", "HEAD", check=False)
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
    cwd = _worktree_root(cwd)
    _reject_url_rewrites(cwd)
    _reject_repository_credential_helpers(cwd)
    _reject_repository_transport_commands(cwd)
    endpoint = _credential_free_url(endpoint, "readback endpoint")
    ref = f"refs/heads/{branch}"
    result = _run_git(cwd, "ls-remote", "--heads", endpoint, ref, check=False)
    if result.returncode != 0:
        raise PublicationError("remote head readback is unavailable")
    rows = [line.split() for line in result.stdout.splitlines() if line.strip()]
    rows = [row for row in rows if len(row) == 2 and row[1] == ref]
    if len(rows) != 1:
        raise PublicationError("remote branch is missing or ambiguous")
    return _sha(rows[0][0], "remote head")


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
    branch = _branch(branch, cwd)
    expected_remote_head = _sha(expected_remote_head, "expected remote head")
    candidate = _sha(candidate, "candidate")
    if _rev_parse(cwd, branch) != candidate:
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
        _run_git(cwd, "bundle", "create", str(temporary), branch, f"^{expected_remote_head}")
        _run_git(cwd, "bundle", "verify", str(temporary))
        heads = _run_git(cwd, "bundle", "list-heads", str(temporary)).stdout.splitlines()
        advertised = {
            parts[1]: parts[0].lower()
            for line in heads
            if len(parts := line.split()) == 2 and SHA_RE.fullmatch(parts[0].lower())
        }
        ref = f"refs/heads/{branch}"
        if advertised.get(ref) != candidate:
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
    cwd = _worktree_root(cwd)
    endpoint = _remote_push_endpoint(cwd, remote, expected_push_url)
    branch = _branch(branch, cwd)
    expected_remote_head = _sha(expected_remote_head, "expected remote head")
    candidate = _sha(candidate, "candidate")

    if _current_branch(cwd) != branch:
        raise PublicationError("checked-out local branch does not match the authorized target branch")
    if _rev_parse(cwd, "HEAD") != candidate:
        raise PublicationError("local HEAD does not equal the exact candidate")
    _require_clean_worktree(cwd)
    if _rev_parse(cwd, expected_remote_head) != expected_remote_head:
        raise PublicationError("expected remote predecessor is not available as a local commit")
    if not _is_ancestor(cwd, expected_remote_head, candidate):
        raise PublicationError("candidate is not a fast-forward descendant of the expected remote head")

    live = remote_head(cwd, endpoint, branch)
    state = classify_remote_state(live, expected_remote_head, candidate)
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
    cwd = _worktree_root(cwd)
    expected_remote_head = _sha(expected_remote_head, "expected remote head")
    candidate = _sha(candidate, "candidate")
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
    ref = f"refs/heads/{branch}"
    push = _run_git(
        cwd,
        "push",
        "--no-verify",
        "--porcelain",
        "--recurse-submodules=no",
        "--no-follow-tags",
        "--no-signed",
        f"--force-with-lease={ref}:{expected_remote_head}",
        endpoint,
        f"{candidate}:{ref}",
        check=False,
    )

    try:
        live = remote_head(cwd, endpoint, branch)
    except PublicationError as exc:
        raise PublicationError(
            f"ambiguous publication outcome; remote readback unavailable; verified recovery bundle={bundle}"
        ) from exc

    final_state = classify_remote_state(live, expected_remote_head, candidate)
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
