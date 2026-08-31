#!/usr/bin/env python3
"""Bounded same-head re-evaluation for trusted asynchronous AI review evidence.

The helper never mutates repository contents. It only re-runs the latest failed
attempt-1 trusted AI review workflow for the current exact pull-request candidate
and trusted base coordinates after authenticated review evidence arrives.
"""

from __future__ import annotations

import dataclasses
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable, Protocol

import ai_review_policy
import verify_ai_review_evidence

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REVIEWED_COMMIT_RE = re.compile(
    r"\*\*Reviewed commit:\*\*\s*`([0-9a-f]{10,40})`"
)
MAX_RUN_PAGES = 100
RUNS_PER_PAGE = 100
MAX_GATE_COMPLETION_POLLS = 12
GATE_COMPLETION_POLL_SECONDS = 5.0
NONTERMINAL_RUN_STATUSES = frozenset({"queued", "in_progress", "pending", "requested", "waiting"})
MAX_ACTIVE_EVIDENCE_POLLS = 12
ACTIVE_EVIDENCE_POLL_SECONDS = 5.0
CODEX_SUMMARY_MARKER = "<!-- codex-pull-request-review-summary -->"


class RecheckError(ValueError):
    """Raised for malformed trusted-event or GitHub state."""


class RecheckClient(Protocol):
    def get_pull_request(self, number: int) -> dict[str, Any]: ...
    def list_gate_runs(
        self, head_sha: str, base_sha: str, pr_number: int
    ) -> list[dict[str, Any]]: ...
    def verify_active_review_evidence(
        self, head_sha: str, base_sha: str, pr_number: int
    ) -> bool: ...
    def rerun(self, run_id: int) -> None: ...


@dataclasses.dataclass(frozen=True)
class Result:
    action: str
    reason: str
    run_id: int | None = None
    head_sha: str | None = None
    base_sha: str | None = None

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


def _positive_pr_number(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise RecheckError("pull request number is missing or malformed")
    return value


def _pr_number(pr: dict[str, Any]) -> int:
    if not isinstance(pr, dict):
        raise RecheckError("pull request payload is not an object")
    return _positive_pr_number(pr.get("number"))


def _sha(value: object, field: str) -> str:
    if not isinstance(value, str) or SHA_RE.fullmatch(value) is None:
        raise RecheckError(f"{field} is missing or malformed")
    return value


def _current_coordinates(
    pr: dict[str, Any], repository: str
) -> tuple[str, str]:
    if not isinstance(pr, dict):
        raise RecheckError("pull request payload is not an object")
    head = pr.get("head")
    base = pr.get("base")
    if not isinstance(head, dict) or not isinstance(base, dict):
        raise RecheckError("pull request head/base coordinates are missing")
    head_repo = head.get("repo")
    head_repo_name = head_repo.get("full_name") if isinstance(head_repo, dict) else None
    if head_repo_name != repository:
        raise RecheckError(
            f"cross-repository pull request is not eligible: expected {repository!r}, got {head_repo_name!r}"
        )
    return (
        _sha(head.get("sha"), "pull request current head"),
        _sha(base.get("sha"), "pull request current base"),
    )


def _linked_pr_matches(
    run: dict[str, Any], head_sha: str, base_sha: str, pr_number: int
) -> bool:
    linked = run.get("pull_requests")
    if not isinstance(linked, list) or not all(isinstance(item, dict) for item in linked):
        raise RecheckError("matching workflow run pull_requests is malformed")
    for item in linked:
        if item.get("number") != pr_number:
            continue
        linked_head = item.get("head")
        linked_base = item.get("base")
        if not isinstance(linked_head, dict) or not isinstance(linked_base, dict):
            raise RecheckError("linked pull request head/base coordinates are malformed")
        if linked_head.get("sha") == head_sha and linked_base.get("sha") == base_sha:
            return True
    return False


def _issue_comment_reviewed_prefix(event: dict[str, Any]) -> tuple[str, str | None]:
    comment = event.get("comment")
    body = comment.get("body") if isinstance(comment, dict) else None
    if not isinstance(body, str):
        return "NOOP_NOT_REVIEW_RESULT", None
    matches = REVIEWED_COMMIT_RE.findall(body)
    if not matches:
        if CODEX_SUMMARY_MARKER in body and "**Completed**" in body:
            return "MATCH", None
        return "NOOP_NOT_REVIEW_RESULT", None
    if len(matches) != 1:
        return "NOOP_AMBIGUOUS_REVIEW_RESULT", None
    return "MATCH", matches[0]


def _latest_matching_gate_run(
    runs: list[dict[str, Any]], head_sha: str, base_sha: str, pr_number: int
) -> dict[str, Any] | None:
    """Return the latest exact-PR exact-head exact-base trusted gate run."""

    _sha(head_sha, "head_sha")
    _sha(base_sha, "base_sha")
    _positive_pr_number(pr_number)
    if not isinstance(runs, list) or not all(isinstance(item, dict) for item in runs):
        raise RecheckError("workflow runs must be an object list")

    candidates: list[dict[str, Any]] = []
    for run in runs:
        if run.get("event") != "pull_request_target":
            continue
        # pull_request_target runs execute in trusted base context; candidate identity
        # is carried by the linked PR coordinates, not run-level head_sha.
        if run.get("head_sha") != base_sha:
            continue
        if not _linked_pr_matches(run, head_sha, base_sha, pr_number):
            continue
        run_id = run.get("id")
        if not isinstance(run_id, int) or isinstance(run_id, bool) or run_id < 1:
            raise RecheckError("matching workflow run has invalid id")
        candidates.append(run)
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda item: (str(item.get("created_at") or ""), int(item["id"])),
    )


def select_rerun_run_id(
    runs: list[dict[str, Any]], head_sha: str, base_sha: str, pr_number: int
) -> int | None:
    """Select the latest failed attempt-1 gate for exact PR/head/base coordinates."""

    latest = _latest_matching_gate_run(runs, head_sha, base_sha, pr_number)
    if latest is None:
        return None
    if latest.get("status") != "completed":
        return None
    if latest.get("conclusion") != "failure":
        return None
    attempt = latest.get("run_attempt")
    if not isinstance(attempt, int) or isinstance(attempt, bool) or attempt != 1:
        return None
    return int(latest["id"])


def _live_pr(
    client: RecheckClient, number: int, repository: str
) -> tuple[dict[str, Any], str, str]:
    pr = client.get_pull_request(number)
    if _pr_number(pr) != number:
        raise RecheckError("pull request identity mismatch")
    if pr.get("state") not in (None, "open"):
        raise RecheckError("pull request is no longer open")
    head_sha, base_sha = _current_coordinates(pr, repository)
    base = pr.get("base") or {}
    base_repo = base.get("repo") or {}
    base_ref = base.get("ref")
    default_branch = base_repo.get("default_branch")
    if not isinstance(base_ref, str) or not base_ref or not isinstance(default_branch, str) or not default_branch:
        raise RecheckError("pull request base/default branch authority is missing")
    if base_ref != default_branch:
        raise RecheckError("pull request no longer targets the repository default branch")
    return pr, head_sha, base_sha


def process_event(
    event_name: str,
    event: dict[str, Any],
    repository: str,
    policy: dict[str, Any],
    client: RecheckClient,
    *,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> Result:
    """Process one trusted reviewer result event with a bounded same-head rerun."""

    if repository.count("/") != 1:
        raise RecheckError("repository must use owner/name form")
    if not isinstance(event, dict):
        raise RecheckError("event payload must be an object")

    sender = event.get("sender")
    actor = sender.get("login") if isinstance(sender, dict) else None
    comment = event.get("comment") if event_name == "issue_comment" else None
    marker = policy.get("p2_follow_up", {}).get("evidence_wakeup_marker")
    maintainer_wakeup = (
        isinstance(comment, dict)
        and isinstance(marker, str)
        and comment.get("body") == marker
        and comment.get("author_association")
        in set(policy.get("p2_follow_up", {}).get("trusted_maintainer_associations", []))
    )
    if (not isinstance(actor, str) or actor not in trusted_reviewer_logins(policy)) and not maintainer_wakeup:
        return Result(
            "NOOP_UNTRUSTED_ACTOR",
            "event actor is not a configured trusted reviewer",
        )

    reviewed_prefix: str | None = None
    review_commit: str | None = None
    if event_name == "pull_request_review":
        event_pr = event.get("pull_request")
        if not isinstance(event_pr, dict):
            raise RecheckError("pull_request_review event is missing pull_request")
        pr_number = _pr_number(event_pr)
        review = event.get("review")
        review_commit = review.get("commit_id") if isinstance(review, dict) else None
        review_commit = _sha(review_commit, "pull request review commit_id")
    elif event_name == "issue_comment":
        issue = event.get("issue")
        if not isinstance(issue, dict) or not isinstance(issue.get("pull_request"), dict):
            return Result(
                "NOOP_NOT_PULL_REQUEST",
                "trusted reviewer comment is not on a pull request",
            )
        match_state, reviewed_prefix = ("MATCH", None) if maintainer_wakeup else _issue_comment_reviewed_prefix(event)
        if match_state == "NOOP_NOT_REVIEW_RESULT":
            return Result(
                match_state,
                "trusted reviewer comment has no unambiguous reviewed-commit result",
            )
        if match_state == "NOOP_AMBIGUOUS_REVIEW_RESULT":
            return Result(
                match_state,
                "trusted reviewer comment contains multiple reviewed-commit identities",
            )
        pr_number = _positive_pr_number(issue.get("number"))
    else:
        raise RecheckError(f"unsupported event name: {event_name!r}")

    _, head_sha, base_sha = _live_pr(client, pr_number, repository)
    if review_commit is not None and review_commit != head_sha:
        return Result(
            "NOOP_STALE_REVIEW",
            "review result is bound to an older pull-request head",
            head_sha=head_sha,
            base_sha=base_sha,
        )
    if reviewed_prefix is not None and not head_sha.startswith(reviewed_prefix):
        return Result(
            "NOOP_STALE_REVIEW",
            "review result is bound to an older pull-request head",
            head_sha=head_sha,
            base_sha=base_sha,
        )

    run_id: int | None = None
    for poll_index in range(MAX_GATE_COMPLETION_POLLS):
        runs = client.list_gate_runs(head_sha, base_sha, pr_number)
        run_id = select_rerun_run_id(runs, head_sha, base_sha, pr_number)
        if run_id is not None:
            break

        latest = _latest_matching_gate_run(runs, head_sha, base_sha, pr_number)
        if latest is None:
            return Result(
                "NOOP_NO_ELIGIBLE_RUN",
                "no exact-PR exact-head exact-base AI review gate run is eligible",
                head_sha=head_sha,
                base_sha=base_sha,
            )
        attempt = latest.get("run_attempt")
        status = latest.get("status")
        if (
            not isinstance(attempt, int)
            or isinstance(attempt, bool)
            or attempt != 1
            or status not in NONTERMINAL_RUN_STATUSES
        ):
            return Result(
                "NOOP_NO_ELIGIBLE_RUN",
                "latest exact-PR exact-head exact-base gate is not a failed or pending attempt-1 run",
                head_sha=head_sha,
                base_sha=base_sha,
            )
        if poll_index == MAX_GATE_COMPLETION_POLLS - 1:
            return Result(
                "NOOP_GATE_STILL_RUNNING",
                "matching attempt-1 AI review gate remained nonterminal through the bounded completion wait",
                run_id=int(latest["id"]),
                head_sha=head_sha,
                base_sha=base_sha,
            )
        sleep_fn(GATE_COMPLETION_POLL_SECONDS)

    assert run_id is not None

    active_evidence = False
    for evidence_poll_index in range(MAX_ACTIVE_EVIDENCE_POLLS):
        if client.verify_active_review_evidence(head_sha, base_sha, pr_number):
            active_evidence = True
            break
        if evidence_poll_index == MAX_ACTIVE_EVIDENCE_POLLS - 1:
            break
        sleep_fn(ACTIVE_EVIDENCE_POLL_SECONDS)
    if not active_evidence:
        return Result(
            "NOOP_UNVERIFIED_REVIEW_GENERATION",
            "active exact-tier exact-fingerprint review evidence was not verified within the bounded wakeup window",
            run_id=run_id,
            head_sha=head_sha,
            base_sha=base_sha,
        )

    # Race guard immediately before mutation of workflow state.
    _, fresh_head_sha, fresh_base_sha = _live_pr(client, pr_number, repository)
    if fresh_head_sha != head_sha or fresh_base_sha != base_sha:
        return Result(
            "NOOP_PR_MOVED",
            "pull-request head/base changed before same-head recheck",
            head_sha=fresh_head_sha,
            base_sha=fresh_base_sha,
        )

    client.rerun(run_id)
    return Result(
        "RERUN",
        "trusted reviewer result triggered one bounded exact-PR same-head gate re-evaluation",
        run_id=run_id,
        head_sha=head_sha,
        base_sha=base_sha,
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
        candidate_root: str | Path | None = None,
        policy_path: str | Path = "ecosystem/ai-review-policy.json",
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
        self.candidate_root = Path(candidate_root) if candidate_root is not None else None
        self.policy_path = Path(policy_path)

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

    def list_gate_runs(
        self, head_sha: str, base_sha: str, pr_number: int
    ) -> list[dict[str, Any]]:
        _sha(head_sha, "head_sha")
        _sha(base_sha, "base_sha")
        _positive_pr_number(pr_number)
        workflow = urllib.parse.quote(self.workflow, safe="")
        collected: list[dict[str, Any]] = []
        for page in range(1, MAX_RUN_PAGES + 1):
            query = urllib.parse.urlencode(
                {
                    "event": "pull_request_target",
                    "per_page": str(RUNS_PER_PAGE),
                    "page": str(page),
                }
            )
            payload = self._request(
                f"/repos/{self.repository}/actions/workflows/{workflow}/runs?{query}"
            )
            runs = payload.get("workflow_runs") if isinstance(payload, dict) else None
            if not isinstance(runs, list) or not all(isinstance(item, dict) for item in runs):
                raise RecheckError("GitHub workflow-run response is malformed")
            collected.extend(runs)
            if len(runs) < RUNS_PER_PAGE:
                return collected
        raise RecheckError(
            f"trusted gate history exceeds bounded {MAX_RUN_PAGES * RUNS_PER_PAGE}-run scan"
        )

    def verify_active_review_evidence(
        self, head_sha: str, base_sha: str, pr_number: int
    ) -> bool:
        if self.candidate_root is None:
            raise RecheckError("OTERYN_CANDIDATE_ROOT is required for active review verification")
        if not self.candidate_root.is_dir():
            raise RecheckError("candidate inert checkout is unavailable")
        try:
            classification = ai_review_policy.evaluate(
                base_sha,
                head_sha,
                self.candidate_root,
                self.policy_path,
            )
            if (
                classification.get("tier") not in {"R1", "R2"}
                or classification.get("external_review") != "required"
            ):
                return False
            policy = json.loads(self.policy_path.read_text(encoding="utf-8"))
            verify_ai_review_evidence.verify_live_review_evidence(
                repository=self.repository,
                pr_number=pr_number,
                token=self.token,
                policy=policy,
                repo_root=self.candidate_root,
                tier=classification["tier"],
                fingerprint=classification["review_fingerprint"],
                head=head_sha,
                base=base_sha,
            )
            return True
        except (RuntimeError, ValueError, OSError, json.JSONDecodeError):
            return False

    def rerun(self, run_id: int) -> None:
        if not isinstance(run_id, int) or isinstance(run_id, bool) or run_id < 1:
            raise RecheckError("run_id must be a positive integer")
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
    candidate_root = os.environ.get("OTERYN_CANDIDATE_ROOT", "")

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
        GitHubClient(
            repository,
            token,
            candidate_root=candidate_root or None,
            policy_path=policy_path,
        ),
    )
    print(json.dumps(result.as_dict(), sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RecheckError, json.JSONDecodeError, OSError) as exc:
        print(f"ai-review-recheck: {exc}", file=sys.stderr)
        raise SystemExit(2)
