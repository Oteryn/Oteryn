#!/usr/bin/env python3
"""Bounded same-head re-evaluation for trusted asynchronous AI review evidence.

The helper never mutates repository contents. It only re-runs the latest failed
attempt-1 trusted AI review workflow for the current exact pull-request head.
"""

from __future__ import annotations

import dataclasses
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Protocol

SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class RecheckError(ValueError):
    """Raised for malformed trusted-event or GitHub state."""


class RecheckClient(Protocol):
    def get_pull_request(self, number: int) -> dict[str, Any]: ...
    def list_gate_runs(self) -> list[dict[str, Any]]: ...
    def rerun(self, run_id: int) -> None: ...


@dataclasses.dataclass(frozen=True)
class Result:
    action: str
    reason: str
    run_id: int | None = None
    head_sha: str | None = None

    def as_dict(self) -> dict[str, object]:
        return dataclasses.asdict(self)


def trusted_reviewer_logins(policy: dict[str, Any]) -> frozenset[str]:
    raw = policy.get("reviewer_source_logins")
    if not isinstance(raw, dict) or not raw:
        raise RecheckError("AI review policy reviewer_source_logins is missing")
    result: set[str] = set()
    for reviewer_id, logins in raw.items():
        if not isinstance(reviewer_id, str) or not reviewer_id:
            raise RecheckError("AI review policy reviewer id is invalid")
        if not isinstance(logins, list) or not all(
            isinstance(item, str) and item for item in logins
        ):
            raise RecheckError(
                f"AI review policy logins for {reviewer_id!r} are invalid"
            )
        result.update(logins)
    if not result:
        raise RecheckError("AI review policy has no trusted reviewer logins")
    return frozenset(result)


def _current_head(pr: dict[str, Any], repository: str) -> str:
    if not isinstance(pr, dict):
        raise RecheckError("pull request payload is not an object")
    head = pr.get("head")
    if not isinstance(head, dict):
        raise RecheckError("pull request head is missing")
    sha = head.get("sha")
    repo = head.get("repo")
    repo_name = repo.get("full_name") if isinstance(repo, dict) else None
    if repo_name != repository:
        raise RecheckError(
            f"cross-repository pull request is not eligible: expected {repository!r}, got {repo_name!r}"
        )
    if not isinstance(sha, str) or SHA_RE.fullmatch(sha) is None:
        raise RecheckError("pull request current head is missing or malformed")
    return sha


def select_rerun_run_id(runs: list[dict[str, Any]], head_sha: str) -> int | None:
    """Select only the latest exact-head failed attempt-1 trusted gate run."""

    if SHA_RE.fullmatch(head_sha) is None:
        raise RecheckError("head_sha must be lowercase 40-hex")
    if not isinstance(runs, list) or not all(isinstance(item, dict) for item in runs):
        raise RecheckError("workflow runs must be an object list")

    candidates: list[dict[str, Any]] = []
    for run in runs:
        if run.get("head_sha") != head_sha or run.get("event") != "pull_request_target":
            continue
        run_id = run.get("id")
        if not isinstance(run_id, int) or run_id < 1:
            raise RecheckError("matching workflow run has invalid id")
        candidates.append(run)
    if not candidates:
        return None

    latest = max(
        candidates,
        key=lambda item: (str(item.get("created_at") or ""), int(item["id"])),
    )
    if latest.get("status") != "completed":
        return None
    if latest.get("conclusion") != "failure":
        return None
    attempt = latest.get("run_attempt")
    if not isinstance(attempt, int) or attempt != 1:
        return None
    return int(latest["id"])


def process_event(
    event_name: str,
    event: dict[str, Any],
    repository: str,
    policy: dict[str, Any],
    client: RecheckClient,
) -> Result:
    """Process one trusted reviewer result event with a bounded same-head rerun."""

    if repository.count("/") != 1:
        raise RecheckError("repository must use owner/name form")
    if not isinstance(event, dict):
        raise RecheckError("event payload must be an object")

    sender = event.get("sender")
    actor = sender.get("login") if isinstance(sender, dict) else None
    if not isinstance(actor, str) or actor not in trusted_reviewer_logins(policy):
        return Result(
            "NOOP_UNTRUSTED_ACTOR",
            "event actor is not a configured trusted reviewer",
        )

    if event_name == "pull_request_review":
        pr = event.get("pull_request")
        if not isinstance(pr, dict):
            raise RecheckError("pull_request_review event is missing pull_request")
        head_sha = _current_head(pr, repository)
        review = event.get("review")
        review_commit = review.get("commit_id") if isinstance(review, dict) else None
        if not isinstance(review_commit, str) or SHA_RE.fullmatch(review_commit) is None:
            raise RecheckError("pull request review commit_id is missing or malformed")
        if review_commit != head_sha:
            return Result(
                "NOOP_STALE_REVIEW",
                "review result is bound to an older pull-request head",
                head_sha=head_sha,
            )
    elif event_name == "issue_comment":
        issue = event.get("issue")
        if not isinstance(issue, dict) or not isinstance(
            issue.get("pull_request"), dict
        ):
            return Result(
                "NOOP_NOT_PULL_REQUEST",
                "trusted reviewer comment is not on a pull request",
            )
        number = issue.get("number")
        if not isinstance(number, int) or number < 1:
            raise RecheckError("issue_comment pull request number is invalid")
        pr = client.get_pull_request(number)
        head_sha = _current_head(pr, repository)
    else:
        raise RecheckError(f"unsupported event name: {event_name!r}")

    run_id = select_rerun_run_id(client.list_gate_runs(), head_sha)
    if run_id is None:
        return Result(
            "NOOP_NO_ELIGIBLE_RUN",
            "no exact-head completed failed attempt-1 AI review gate run is eligible",
            head_sha=head_sha,
        )

    client.rerun(run_id)
    return Result(
        "RERUN",
        "trusted reviewer result triggered one bounded same-head gate re-evaluation",
        run_id=run_id,
        head_sha=head_sha,
    )


class GitHubClient:
    def __init__(
        self,
        repository: str,
        token: str,
        *,
        api_url: str = "https://api.github.com",
        workflow: str = "governance-ai-review.yml",
        timeout: float = 30.0,
    ) -> None:
        if repository.count("/") != 1:
            raise RecheckError("repository must use owner/name form")
        if not token:
            raise RecheckError("GitHub token is required")
        self.repository = repository
        self.token = token
        self.api_url = api_url.rstrip("/")
        self.workflow = workflow
        self.timeout = timeout

    def _request(self, path: str, *, method: str = "GET") -> Any:
        request = urllib.request.Request(
            f"{self.api_url}{path}",
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "oteryn-ai-review-recheck/1",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raise RecheckError(
                f"GitHub API {method} {path} returned HTTP {exc.code}"
            ) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise RecheckError(f"GitHub API {method} {path} failed") from exc
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RecheckError(
                f"GitHub API {method} {path} returned invalid JSON"
            ) from exc

    def get_pull_request(self, number: int) -> dict[str, Any]:
        payload = self._request(f"/repos/{self.repository}/pulls/{number}")
        if not isinstance(payload, dict):
            raise RecheckError("GitHub pull request response is malformed")
        return payload

    def list_gate_runs(self) -> list[dict[str, Any]]:
        workflow = urllib.parse.quote(self.workflow, safe="")
        payload = self._request(
            f"/repos/{self.repository}/actions/workflows/{workflow}/runs"
            "?event=pull_request_target&per_page=100"
        )
        runs = payload.get("workflow_runs") if isinstance(payload, dict) else None
        if not isinstance(runs, list) or not all(isinstance(item, dict) for item in runs):
            raise RecheckError("GitHub workflow-run response is malformed")
        if len(runs) >= 100:
            raise RecheckError(
                "AI review workflow returned 100 runs; exact-head selection is ambiguous"
            )
        return runs

    def rerun(self, run_id: int) -> None:
        payload = self._request(
            f"/repos/{self.repository}/actions/runs/{run_id}/rerun",
            method="POST",
        )
        if payload is not None:
            raise RecheckError(
                "GitHub rerun endpoint returned unexpected response body"
            )


def main() -> int:
    event_path = os.environ.get("GITHUB_EVENT_PATH", "")
    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    token = os.environ.get("GITHUB_TOKEN", "")
    policy_path = os.environ.get(
        "OTERYN_AI_REVIEW_POLICY", "ecosystem/ai-review-policy.json"
    )

    if not event_path:
        raise RecheckError("GITHUB_EVENT_PATH is required")
    event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    policy = json.loads(Path(policy_path).read_text(encoding="utf-8"))
    if not isinstance(event, dict) or not isinstance(policy, dict):
        raise RecheckError("event and policy must be JSON objects")

    result = process_event(
        event_name,
        event,
        repository,
        policy,
        GitHubClient(repository, token),
    )
    print(json.dumps(result.as_dict(), sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RecheckError, json.JSONDecodeError, OSError) as exc:
        print(f"ai-review-recheck: {exc}", file=sys.stderr)
        raise SystemExit(2)
