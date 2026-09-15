#!/usr/bin/env python3
"""Fail-closed exact-candidate publication helper for Oteryn task branches."""
from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

SHA_RE = re.compile(r"^[0-9a-f]{40}$")


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


def _remote(cwd: Path, value: str, expected_push_url: str) -> str:
    value = value.strip()
    if not value or value.startswith("-") or any(char.isspace() for char in value):
        raise PublicationError("remote must be an existing Git remote name")
    names = {line.strip() for line in _run_git(cwd, "remote").stdout.splitlines() if line.strip()}
    if value not in names:
        raise PublicationError("remote must be an existing Git remote name")
    expected_push_url = expected_push_url.strip()
    if not expected_push_url:
        raise PublicationError("expected push URL must be provided")
    actual = _run_git(cwd, "remote", "get-url", "--push", value).stdout.strip()
    if actual != expected_push_url:
        raise PublicationError("configured push URL does not match the approved publication target")
    return value


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
    result = _run_git(cwd, "merge-base", "--is-ancestor", ancestor, descendant, check=False)
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    raise PublicationError("unable to determine candidate ancestry")


def _require_clean_worktree(cwd: Path) -> None:
    status = _run_git(cwd, "status", "--porcelain=v1", "--untracked-files=all").stdout
    if status.strip():
        raise PublicationError(
            "publication requires a clean isolated worktree so the recovery artifact matches all intended work"
        )


def remote_head(cwd: Path, remote: str, branch: str) -> str:
    ref = f"refs/heads/{branch}"
    result = _run_git(cwd, "ls-remote", "--heads", remote, ref, check=False)
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
    _outside_worktree(cwd, bundle_path)
    bundle_path = bundle_path.resolve()
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    if bundle_path.exists():
        raise PublicationError("recovery bundle path already exists")
    temporary = bundle_path.with_name(bundle_path.name + ".tmp")
    if temporary.exists():
        temporary.unlink()
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
    cwd = cwd.resolve()
    remote = _remote(cwd, remote, expected_push_url)
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

    live = remote_head(cwd, remote, branch)
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
    cwd = cwd.resolve()
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

    # Re-validate the configured push target after bundle creation. The explicit
    # expected-old-value lease atomically fences the ref at mutation time, while
    # the ancestry check above independently guarantees the update is fast-forward.
    # The lease is therefore compare-and-swap protection, not permission to
    # publish a non-fast-forward history rewrite.
    remote = _remote(cwd, remote, expected_push_url)
    ref = f"refs/heads/{branch}"
    push = _run_git(
        cwd,
        "push",
        "--porcelain",
        f"--force-with-lease={ref}:{expected_remote_head}",
        remote,
        f"{candidate}:{ref}",
        check=False,
    )

    try:
        live = remote_head(cwd, remote, branch)
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
        help="Exact approved push URL already configured for the selected remote",
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
