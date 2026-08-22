#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

DISPOSITION = re.compile(r"^[ \t]*Branch-Disposition:[ \t]*(delete|retain)[ \t]*$", re.I | re.M)
ANY_DISPOSITION = re.compile(r"^[ \t]*Branch-Disposition:[ \t]*(.*?)[ \t]*$", re.I | re.M)
REASON = re.compile(r"^[ \t]*Branch-Disposition-Reason:[ \t]*(\S[^\r\n]*)$", re.I | re.M)
ANY_REASON = re.compile(r"^[ \t]*Branch-Disposition-Reason:[ \t]*(.*)$", re.I | re.M)
FULL_SHA = re.compile(r"^[0-9a-fA-F]{40}$")
RESERVED = ("release", "rollback", "recovery", "backup")


class CleanupError(RuntimeError):
    pass


class ApiError(CleanupError):
    pass


def repo_name(value: Any) -> str | None:
    return value.get("full_name") if isinstance(value, dict) and isinstance(value.get("full_name"), str) else None


def parse_disposition(body: str) -> tuple[str | None, str | None]:
    text = body or ""
    all_dispositions = [v.strip() for v in ANY_DISPOSITION.findall(text)]
    all_reasons = [v.strip() for v in ANY_REASON.findall(text)]
    exact = [v.casefold() for v in DISPOSITION.findall(text)]
    reasons = [v.strip() for v in REASON.findall(text)]
    if not all_dispositions and not all_reasons:
        return None, None
    if len(all_dispositions) != 1:
        raise CleanupError("expected exactly one Branch-Disposition marker")
    if len(exact) != 1:
        raise CleanupError(f"invalid Branch-Disposition value: {all_dispositions[0]!r}; expected delete or retain")
    if len(all_reasons) != 1 or len(reasons) != 1 or not reasons[0]:
        raise CleanupError(f"Branch-Disposition: {exact[0]} requires exactly one non-empty Branch-Disposition-Reason")
    return exact[0], reasons[0]


def result(status: str, *, branch=None, number=None, sha=None, reason=None, deleted=False) -> dict[str, Any]:
    return {"result": status, "branch": branch, "pull_request": number, "head_sha": sha, "reason": reason, "deleted": deleted}


def live_pull_matches(pull: Any, repository: str, number: int, branch: str, sha: str) -> bool:
    if not isinstance(pull, dict):
        return False
    head = pull.get("head") if isinstance(pull.get("head"), dict) else {}
    return (
        pull.get("number") == number
        and pull.get("state") == "closed"
        and pull.get("merged") is not True
        and pull.get("merged_at") is None
        and head.get("ref") == branch
        and head.get("sha") == sha
        and repo_name(head.get("repo")) == repository
    )


def process_event(event: dict[str, Any], repository: str, github: Any, git: Any) -> dict[str, Any]:
    if not isinstance(event, dict) or not isinstance(repository, str) or "/" not in repository:
        raise CleanupError("invalid event or repository identity")
    pull = event.get("pull_request") if isinstance(event.get("pull_request"), dict) else None
    if repo_name(event.get("repository")) != repository or pull is None:
        return result("NOT_APPLICABLE")

    head = pull.get("head") if isinstance(pull.get("head"), dict) else {}
    number, branch, sha = pull.get("number"), head.get("ref"), head.get("sha")
    if not isinstance(number, int) or isinstance(number, bool) or not isinstance(branch, str) or not branch or not isinstance(sha, str) or not FULL_SHA.fullmatch(sha):
        raise CleanupError("closed pull request event has invalid identity fields")

    disposition, reason = parse_disposition(pull.get("body") if isinstance(pull.get("body"), str) else "")
    if disposition is None:
        return result("NOT_APPLICABLE", branch=branch, number=number, sha=sha)
    if disposition == "retain":
        return result("RETAIN", branch=branch, number=number, sha=sha, reason=reason)
    if pull.get("state") != "closed" or pull.get("merged") is True or pull.get("merged_at") is not None or repo_name(head.get("repo")) != repository:
        return result("NOT_APPLICABLE", branch=branch, number=number, sha=sha, reason=reason)
    if any(part in branch.casefold() for part in RESERVED):
        raise CleanupError(f"branch {branch!r} is recovery-sensitive and cannot be auto-deleted")

    repo = github.get_repository()
    if repo_name(repo) != repository:
        raise CleanupError("live repository identity drift")
    if branch == repo.get("default_branch"):
        raise CleanupError(f"refusing to delete default branch {branch!r}")
    live_pull = github.get_pull(number)
    if not live_pull_matches(live_pull, repository, number, branch, sha):
        raise CleanupError("live pull request identity drift")
    live_disposition, live_reason = parse_disposition(
        live_pull.get("body") if isinstance(live_pull.get("body"), str) else ""
    )
    if live_disposition is None:
        return result("NOT_APPLICABLE", branch=branch, number=number, sha=sha)
    if live_disposition == "retain":
        return result("RETAIN", branch=branch, number=number, sha=sha, reason=live_reason)
    reason = live_reason

    current = git.remote_ref_sha(branch)
    if current is None:
        return result("ALREADY_ABSENT", branch=branch, number=number, sha=sha, reason=reason)
    if current != sha:
        raise CleanupError(f"branch head SHA drift: expected {sha}, got {current}")
    if github.get_branch(branch).get("protected") is True:
        raise CleanupError(f"branch {branch!r} is protected")
    if github.get_open_pulls_for_branch(branch):
        raise CleanupError(f"branch {branch!r} still has an open pull request")
    current = git.remote_ref_sha(branch)
    if current != sha:
        raise CleanupError(f"branch head SHA drift before recovery preparation: expected {sha}, got {current}")
    git.prepare_recovery(branch, sha)

    # Destructive authority is mutable until the deletion boundary. Re-read the
    # live pull request after all non-destructive preparation so a late body edit
    # can still revoke or invalidate the delete disposition.
    boundary_pull = github.get_pull(number)
    if not live_pull_matches(boundary_pull, repository, number, branch, sha):
        raise CleanupError("live pull request identity drift at deletion boundary")
    boundary_disposition, boundary_reason = parse_disposition(
        boundary_pull.get("body") if isinstance(boundary_pull.get("body"), str) else ""
    )
    if boundary_disposition is None:
        return result("NOT_APPLICABLE", branch=branch, number=number, sha=sha)
    if boundary_disposition == "retain":
        return result("RETAIN", branch=branch, number=number, sha=sha, reason=boundary_reason)
    reason = boundary_reason

    # The boundary pull revalidation is deliberately the final authority query
    # before the destructive push. Exact branch-SHA drift is enforced atomically
    # by the Git force-with-lease used by delete_with_lease().

    # Once a delete is attempted, every unknown or negative verification result
    # becomes a rollback condition. The recovery object prepared above makes the
    # exact source commit locally available even after the remote ref disappears.
    try:
        git.delete_with_lease(branch, sha)
        if git.remote_ref_sha(branch) is not None:
            raise CleanupError(f"branch {branch!r} still exists after deletion")
        if github.get_open_pulls_for_branch(branch):
            raise CleanupError(f"branch {branch!r} acquired an open pull request during deletion")
    except Exception as failure:
        try:
            git.restore_if_absent(branch, sha)
            restored = git.remote_ref_sha(branch)
            if restored != sha:
                raise CleanupError(
                    f"exact-head rollback verification mismatch: expected {sha}, got {restored or 'absent'}"
                )
        except Exception as rollback_failure:
            raise CleanupError(
                f"terminal delete/verification failed for {branch!r} and exact-head rollback could not be proven: "
                f"{failure}; rollback error: {rollback_failure}"
            ) from failure
        raise CleanupError(
            f"branch {branch!r} exact head was preserved or restored after post-delete verification failed: {failure}"
        ) from failure
    return result("DELETED", branch=branch, number=number, sha=sha, reason=reason, deleted=True)


class GitHubClient:
    def __init__(self, repository: str, token: str, api_url="https://api.github.com") -> None:
        self.repository, self.token, self.api_url = repository, token, api_url.rstrip("/")

    def get(self, path: str) -> Any:
        request = urllib.request.Request(
            f"{self.api_url}{path}",
            headers={"Accept": "application/vnd.github+json", "Authorization": f"Bearer {self.token}", "User-Agent": "oteryn-terminal-branch-cleanup/1", "X-GitHub-Api-Version": "2022-11-28"},
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise ApiError(f"GitHub API GET {path} returned {exc.code}: {body[:300]}") from exc

    def get_repository(self):
        return self.get(f"/repos/{self.repository}")

    def get_pull(self, number: int):
        return self.get(f"/repos/{self.repository}/pulls/{number}")

    def get_branch(self, branch: str):
        return self.get(f"/repos/{self.repository}/branches/{urllib.parse.quote(branch, safe='')}")

    def get_open_pulls_for_branch(self, branch: str):
        owner = self.repository.split("/", 1)[0]
        query = urllib.parse.urlencode({"state": "open", "head": f"{owner}:{branch}", "per_page": 100})
        value = self.get(f"/repos/{self.repository}/pulls?{query}")
        if not isinstance(value, list):
            raise ApiError("open pull request response is not an array")
        return value


def repo_from_remote(value: str) -> str | None:
    value = value.strip()
    if value.startswith("git@github.com:"):
        path = value[len("git@github.com:"):]
    else:
        parsed = urllib.parse.urlsplit(value)
        if parsed.scheme not in {"https", "ssh"} or (parsed.hostname or "").casefold() != "github.com" or parsed.password is not None:
            return None
        path = parsed.path.lstrip("/")
    path = path[:-4] if path.endswith(".git") else path
    parts = path.split("/")
    return "/".join(parts) if len(parts) == 2 and all(parts) else None


class GitTransport:
    def __init__(self, repository: str, root=".", remote="origin") -> None:
        self.repository, self.root, self.remote = repository, Path(root).resolve(), remote
        if not remote or remote.startswith("-") or any(c.isspace() for c in remote):
            raise CleanupError("git remote must be a non-option token without whitespace")
        probe = self.run(["git", "remote", "get-url", "--push", remote])
        remote_repo = repo_from_remote(probe.stdout.strip()) if probe.returncode == 0 else None
        if remote_repo is None or remote_repo.casefold() != repository.casefold():
            raise CleanupError(f"git remote identity mismatch: expected {repository}, got {remote_repo or 'unsupported remote'}")

    def run(self, command: list[str]):
        try:
            return subprocess.run(command, cwd=self.root, capture_output=True, text=True, timeout=60, check=False)
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            raise CleanupError("git command failed to execute") from exc

    def remote_ref_sha(self, branch: str) -> str | None:
        ref = f"refs/heads/{branch}"
        out = self.run(["git", "ls-remote", "--refs", self.remote, ref])
        if out.returncode != 0:
            raise CleanupError(f"remote ref lookup failed for {branch}")
        rows = [line.split() for line in out.stdout.splitlines() if line.strip()]
        if not rows:
            return None
        if len(rows) != 1 or len(rows[0]) != 2 or rows[0][1] != ref or not FULL_SHA.fullmatch(rows[0][0]):
            raise CleanupError(f"unexpected remote ref data for {branch}")
        return rows[0][0]

    def prepare_recovery(self, branch: str, expected_sha: str) -> None:
        recovery_ref = f"refs/oteryn-terminal-recovery/{expected_sha}"
        source_ref = f"refs/heads/{branch}"
        out = self.run([
            "git", "fetch", "--no-tags", "--depth=1", self.remote,
            f"{source_ref}:{recovery_ref}",
        ])
        if out.returncode != 0:
            raise CleanupError(f"failed to prepare recovery object for {branch}")
        probe = self.run(["git", "rev-parse", "--verify", recovery_ref])
        if probe.returncode != 0 or probe.stdout.strip() != expected_sha:
            raise CleanupError(f"recovery object mismatch for {branch}")

    def restore_if_absent(self, branch: str, expected_sha: str) -> None:
        ref = f"refs/heads/{branch}"
        out = self.run([
            "git", "push", "--porcelain", f"--force-with-lease={ref}:",
            self.remote, f"{expected_sha}:{ref}",
        ])
        if out.returncode == 0:
            return
        current = self.remote_ref_sha(branch)
        if current == expected_sha:
            return
        raise CleanupError(
            f"exact-head restoration was rejected for {branch}; current {current or 'absent'}"
        )

    def delete_with_lease(self, branch: str, expected_sha: str) -> None:
        ref = f"refs/heads/{branch}"
        out = self.run(["git", "push", "--porcelain", f"--force-with-lease={ref}:{expected_sha}", self.remote, f":{ref}"])
        if out.returncode != 0:
            current = self.remote_ref_sha(branch)
            if current != expected_sha:
                raise CleanupError(f"leased delete rejected for {branch}: expected {expected_sha}, current {current or 'absent'}")
            raise CleanupError(f"leased delete push was rejected for {branch}")


def write_json(path: str, value: dict[str, Any]) -> None:
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_cli(argv=None, *, github=None, git=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--root", default=".")
    parser.add_argument("--remote", default="origin")
    args = parser.parse_args(argv)
    try:
        event = json.loads(Path(args.event).read_text(encoding="utf-8"))
        if github is None:
            token = os.environ.get("GITHUB_TOKEN", "")
            if not token:
                raise CleanupError("GITHUB_TOKEN is required")
            github = GitHubClient(args.repository, token)
        git = git or GitTransport(args.repository, args.root, args.remote)
        payload = process_event(event, args.repository, github, git)
        write_json(args.output, payload)
        print(json.dumps(payload, sort_keys=True))
        return 0
    except (CleanupError, json.JSONDecodeError, OSError) as exc:
        payload = {"result": "BLOCKED", "deleted": False, "error": str(exc)}
        write_json(args.output, payload)
        print(json.dumps(payload, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(run_cli())
