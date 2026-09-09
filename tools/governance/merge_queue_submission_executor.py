#!/usr/bin/env python3
"""Protected-default-branch executor for exact-head Merge Queue submission.

The executor accepts one authenticated control comment, binds authorization to the
exact requested repository/PR/base/head, qualifies the exact candidate, and performs
only GraphQL enqueuePullRequest(expectedHeadOid=...). If an enqueue result cannot be
verified, cleanup is limited to the exact queue entry attributable to this attempt;
concurrent/new-head entries are never dequeued. It has no direct-merge or generic
auto-merge path.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping, Protocol

CONTROL_REPOSITORY = "Oteryn/Oteryn"
CONTROL_ISSUE = 190
COMMAND_PREFIX = "/oteryn-mq-submit"
API_VERSION = "2026-03-10"
GITHUB_ACTIONS_APP_ID = 15368
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
ATTEMPT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{15,127}$")
ALLOWED_TARGETS = {
    "Oteryn/Oteryn": "meta-gate",
    "Oteryn/Oteryn-Game": "game-gate",
    "Oteryn/Oteryn-Platform": "platform-gate",
    "Oteryn/Oteryn-Atlas": "atlas-gate",
}
ALLOWED_PERMISSIONS = {"write", "maintain", "admin"}


class SubmissionError(RuntimeError):
    pass


class Client(Protocol):
    def rest(self, method: str, path: str) -> Mapping[str, Any]: ...
    def graphql(self, query: str, variables: Mapping[str, Any]) -> Mapping[str, Any]: ...


class GitHubClient:
    def __init__(self, token: str, api_url: str = "https://api.github.com") -> None:
        if not token.strip():
            raise SubmissionError("GitHub token is required")
        self.token = token.strip()
        self.api_url = api_url.rstrip("/")

    def _request(
        self, url: str, *, method: str, body: Mapping[str, Any] | None = None
    ) -> Mapping[str, Any]:
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "User-Agent": "oteryn-merge-queue-submission",
                "X-GitHub-Api-Version": API_VERSION,
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise SubmissionError(
                f"GitHub API {method} {url} failed with HTTP {exc.code}: {detail}"
            ) from exc
        except urllib.error.URLError as exc:
            raise SubmissionError(f"GitHub API {method} {url} failed: {exc.reason}") from exc

        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SubmissionError(f"GitHub API returned invalid JSON for {method} {url}") from exc
        if not isinstance(parsed, dict):
            raise SubmissionError(f"GitHub API returned non-object JSON for {method} {url}")
        return parsed

    def rest(self, method: str, path: str) -> Mapping[str, Any]:
        return self._request(f"{self.api_url}{path}", method=method)

    def graphql(self, query: str, variables: Mapping[str, Any]) -> Mapping[str, Any]:
        response = self._request(
            f"{self.api_url}/graphql",
            method="POST",
            body={"query": query, "variables": dict(variables)},
        )
        errors = response.get("errors")
        if errors:
            raise SubmissionError(
                f"GitHub GraphQL returned errors: {json.dumps(errors, sort_keys=True)}"
            )
        data = response.get("data")
        if not isinstance(data, dict):
            raise SubmissionError("GitHub GraphQL response is missing object data")
        return data


@dataclass(frozen=True)
class SubmissionRequest:
    attempt_id: str
    repository: str
    repository_name: str
    pr_number: int
    expected_head_sha: str
    required_gate: str


@dataclass(frozen=True)
class TargetAuthorization:
    source: str
    actor: str
    control_issue: int
    control_comment_id: int
    repository: str
    pr_number: int
    base_ref: str
    expected_head_sha: str
    permission: str
    owner_decision: bool


@dataclass(frozen=True)
class QualifiedPullRequest:
    node_id: str
    number: int
    head_sha: str
    base_ref: str


def parse_command(command: object) -> SubmissionRequest:
    if not isinstance(command, str):
        raise SubmissionError("command must be a string")
    parts = command.strip().split()
    if len(parts) != 5 or parts[0] != COMMAND_PREFIX:
        raise SubmissionError(
            f"command must be: {COMMAND_PREFIX} <attempt_id> <owner/repo> <pr_number> <exact_head_sha>"
        )
    _, attempt_id, repository, raw_pr_number, expected_head_sha = parts
    if not ATTEMPT_RE.fullmatch(attempt_id):
        raise SubmissionError("attempt_id has invalid syntax")
    required_gate = ALLOWED_TARGETS.get(repository)
    if required_gate is None:
        raise SubmissionError("target repository is not in the permanent Oteryn allowlist")
    try:
        pr_number = int(raw_pr_number)
    except ValueError as exc:
        raise SubmissionError("PR number must be an integer") from exc
    if pr_number <= 0:
        raise SubmissionError("PR number must be positive")
    expected_head_sha = expected_head_sha.lower()
    if not SHA_RE.fullmatch(expected_head_sha):
        raise SubmissionError(
            "expected head must be a full 40-character lowercase hexadecimal SHA"
        )
    return SubmissionRequest(
        attempt_id=attempt_id,
        repository=repository,
        repository_name=repository.split("/", 1)[1],
        pr_number=pr_number,
        expected_head_sha=expected_head_sha,
        required_gate=required_gate,
    )


def _validated_actor(actor: object) -> str:
    if not isinstance(actor, str) or not actor or "/" in actor:
        raise SubmissionError("invalid comment actor")
    return actor


def _require_repository_permission(
    client: Client, *, repository: str, actor: object, purpose: str
) -> str:
    actor_name = _validated_actor(actor)
    owner, name = repository.split("/", 1)
    encoded_actor = urllib.parse.quote(actor_name, safe="")
    response = client.rest(
        "GET", f"/repos/{owner}/{name}/collaborators/{encoded_actor}/permission"
    )
    permission = response.get("permission")
    if permission not in ALLOWED_PERMISSIONS:
        raise SubmissionError(
            f"comment actor lacks current write/maintain/admin permission on {purpose}"
        )
    return str(permission)


def authorize_actor(
    client: Client,
    *,
    actor: object,
    actual_control_repository: object,
    actual_control_issue: object,
) -> str:
    if actual_control_repository != CONTROL_REPOSITORY or actual_control_issue != CONTROL_ISSUE:
        raise SubmissionError(
            "submission command did not originate from the canonical control endpoint"
        )
    return _require_repository_permission(
        client, repository=CONTROL_REPOSITORY, actor=actor, purpose="META"
    )


def authorize_target_submission(
    client: Client,
    request: SubmissionRequest,
    *,
    actor: object,
    actual_control_issue: object,
    control_comment_id: object,
    control_owner_actor: object,
) -> TargetAuthorization:
    """Bind one authenticated control comment to one exact target candidate."""

    actor_name = _validated_actor(actor)
    if actual_control_issue != CONTROL_ISSUE:
        raise SubmissionError("target authorization is not bound to the canonical control Issue")
    if not isinstance(control_comment_id, int) or isinstance(control_comment_id, bool) or control_comment_id <= 0:
        raise SubmissionError("control comment ID must be a positive integer")

    permission = _require_repository_permission(
        client,
        repository=request.repository,
        actor=actor_name,
        purpose=f"target repository {request.repository}",
    )

    owner_decision = False
    if request.repository == CONTROL_REPOSITORY:
        if not isinstance(control_owner_actor, str) or not control_owner_actor:
            raise SubmissionError("control endpoint owner identity is missing")
        if actor_name != control_owner_actor or permission != "admin":
            raise SubmissionError(
                "META control-plane submission requires the control endpoint owner with current admin permission"
            )
        owner_decision = True

    return TargetAuthorization(
        source="authenticated_control_comment",
        actor=actor_name,
        control_issue=CONTROL_ISSUE,
        control_comment_id=control_comment_id,
        repository=request.repository,
        pr_number=request.pr_number,
        base_ref="main",
        expected_head_sha=request.expected_head_sha,
        permission=permission,
        owner_decision=owner_decision,
    )


def _authorization_matches_request(
    authorization: TargetAuthorization, request: SubmissionRequest
) -> bool:
    return (
        authorization.source == "authenticated_control_comment"
        and authorization.control_issue == CONTROL_ISSUE
        and authorization.repository == request.repository
        and authorization.pr_number == request.pr_number
        and authorization.base_ref == "main"
        and authorization.expected_head_sha == request.expected_head_sha
        and authorization.permission in ALLOWED_PERMISSIONS
        and (
            request.repository != CONTROL_REPOSITORY
            or (authorization.owner_decision and authorization.permission == "admin")
        )
    )


def qualify_pull_request(client: Client, request: SubmissionRequest) -> QualifiedPullRequest:
    owner, name = request.repository.split("/", 1)
    pull = client.rest("GET", f"/repos/{owner}/{name}/pulls/{request.pr_number}")
    if pull.get("state") != "open" or pull.get("merged") is True:
        raise SubmissionError("target pull request must be open and unmerged")
    if pull.get("draft") is not False:
        raise SubmissionError("target pull request must be non-draft")

    base = pull.get("base")
    if not isinstance(base, dict) or base.get("ref") != "main":
        raise SubmissionError("target pull request base must be exactly main")

    head = pull.get("head")
    if not isinstance(head, dict):
        raise SubmissionError("target pull request head metadata is missing")
    actual_head = str(head.get("sha") or "").lower()
    if actual_head != request.expected_head_sha:
        raise SubmissionError(
            f"target pull request head changed: expected {request.expected_head_sha}, "
            f"found {actual_head or 'UNKNOWN'}"
        )
    head_repo = head.get("repo")
    if not isinstance(head_repo, dict) or head_repo.get("full_name") != request.repository:
        raise SubmissionError("target pull request must use a same-repository head")

    node_id = pull.get("node_id")
    if not isinstance(node_id, str) or not node_id:
        raise SubmissionError("target pull request GraphQL node ID is missing")

    params = urllib.parse.urlencode(
        {"check_name": request.required_gate, "filter": "latest", "per_page": "100"}
    )
    checks = client.rest(
        "GET",
        f"/repos/{owner}/{name}/commits/{request.expected_head_sha}/check-runs?{params}",
    )
    raw_runs = checks.get("check_runs")
    if not isinstance(raw_runs, list) or not raw_runs:
        raise SubmissionError(f"no exact-head {request.required_gate} check run was found")
    matching = [
        run for run in raw_runs
        if isinstance(run, dict)
        and run.get("name") == request.required_gate
        and str(run.get("head_sha") or "").lower() == request.expected_head_sha
    ]
    if not matching:
        raise SubmissionError(
            f"no {request.required_gate} check run matches the exact expected head"
        )
    latest = max(matching, key=lambda run: int(run.get("id") or 0))
    app = latest.get("app")
    if not isinstance(app, dict) or app.get("id") != GITHUB_ACTIONS_APP_ID:
        raise SubmissionError(
            f"latest exact-head {request.required_gate} is not the GitHub Actions gate"
        )
    if latest.get("status") != "completed" or latest.get("conclusion") != "success":
        raise SubmissionError(
            f"latest exact-head {request.required_gate} must be completed/success, found "
            f"{latest.get('status')}/{latest.get('conclusion')}"
        )

    return QualifiedPullRequest(
        node_id=node_id,
        number=request.pr_number,
        head_sha=request.expected_head_sha,
        base_ref="main",
    )


QUEUE_ENTRY_QUERY = """
query QueueEntry($pullRequestId: ID!) {
  node(id: $pullRequestId) {
    ... on PullRequest {
      id
      number
      headRefOid
      baseRefName
      repository { nameWithOwner }
      mergeQueueEntry {
        id
        position
        state
        mergeQueue { id resourcePath url }
      }
    }
  }
}
""".strip()

ENQUEUE_MUTATION = """
mutation EnqueuePullRequest(
  $pullRequestId: ID!,
  $expectedHeadOid: GitObjectID!,
  $clientMutationId: String!
) {
  enqueuePullRequest(input: {
    pullRequestId: $pullRequestId,
    expectedHeadOid: $expectedHeadOid,
    clientMutationId: $clientMutationId
  }) {
    clientMutationId
    mergeQueueEntry {
      id
      position
      state
      mergeQueue { id resourcePath url }
      pullRequest {
        id
        number
        headRefOid
        baseRefName
        repository { nameWithOwner }
      }
    }
  }
}
""".strip()

DEQUEUE_MUTATION = """
mutation DequeuePullRequest($pullRequestId: ID!, $clientMutationId: String!) {
  dequeuePullRequest(input: {
    id: $pullRequestId,
    clientMutationId: $clientMutationId
  }) {
    clientMutationId
    mergeQueueEntry {
      id
      position
      state
      mergeQueue { id resourcePath url }
    }
  }
}
""".strip()


def _validate_queue_identity(request: SubmissionRequest, queue: object) -> Mapping[str, Any]:
    if not isinstance(queue, dict):
        raise SubmissionError("merge queue identity is missing")
    expected_resource_path = f"/{request.repository}/queue/main"
    expected_url = f"https://github.com/{request.repository}/queue/main"
    if queue.get("resourcePath") != expected_resource_path or queue.get("url") != expected_url:
        raise SubmissionError("merge queue identity does not match the exact target main queue")
    queue_id = queue.get("id")
    if not isinstance(queue_id, str) or not queue_id:
        raise SubmissionError("merge queue ID is missing")
    return queue


def _normalize_entry(
    request: SubmissionRequest,
    entry: object,
    *,
    require_pull_request: bool,
) -> Mapping[str, Any]:
    if not isinstance(entry, dict):
        raise SubmissionError("merge queue entry is missing")
    if not isinstance(entry.get("id"), str) or not entry["id"]:
        raise SubmissionError("merge queue entry ID is missing")
    position = entry.get("position")
    if not isinstance(position, int) or isinstance(position, bool) or position < 0:
        raise SubmissionError("merge queue entry position is invalid")
    if not isinstance(entry.get("state"), str) or not entry["state"]:
        raise SubmissionError("merge queue entry state is missing")
    _validate_queue_identity(request, entry.get("mergeQueue"))

    if require_pull_request:
        pull = entry.get("pullRequest")
        if not isinstance(pull, dict):
            raise SubmissionError("enqueue response is missing pull request identity")
        repository = pull.get("repository")
        if (
            not isinstance(repository, dict)
            or repository.get("nameWithOwner") != request.repository
            or pull.get("number") != request.pr_number
            or str(pull.get("headRefOid") or "").lower() != request.expected_head_sha
            or pull.get("baseRefName") != "main"
        ):
            raise SubmissionError(
                "enqueue response pull request identity does not match the exact target"
            )
    return entry


def _query_queue_node(client: Client, pull_node_id: str) -> Mapping[str, Any]:
    data = client.graphql(QUEUE_ENTRY_QUERY, {"pullRequestId": pull_node_id})
    node = data.get("node")
    if not isinstance(node, dict):
        raise SubmissionError("queue-entry query did not return a pull request")
    return node


def get_existing_queue_entry(
    client: Client, request: SubmissionRequest, pull: QualifiedPullRequest
) -> Mapping[str, Any] | None:
    node = _query_queue_node(client, pull.node_id)
    repository = node.get("repository")
    if (
        node.get("id") != pull.node_id
        or node.get("number") != request.pr_number
        or str(node.get("headRefOid") or "").lower() != request.expected_head_sha
        or node.get("baseRefName") != "main"
        or not isinstance(repository, dict)
        or repository.get("nameWithOwner") != request.repository
    ):
        raise SubmissionError(
            "queue-entry query target identity does not match the exact request"
        )
    entry = node.get("mergeQueueEntry")
    if entry is None:
        return None
    return _normalize_entry(request, entry, require_pull_request=False)


def _entry_id(entry: object) -> str | None:
    if not isinstance(entry, dict):
        return None
    value = entry.get("id")
    return value if isinstance(value, str) and value else None


def _reconcile_after_indeterminate_enqueue(
    client: Client,
    *,
    request: SubmissionRequest,
    pull_node_id: str,
    attempt_id: str,
    attributable_entry_id: str | None,
    original_error: Exception,
) -> None:
    """Remove only an exact queue entry attributable to this failed attempt."""

    try:
        node = _query_queue_node(client, pull_node_id)
        current_entry = node.get("mergeQueueEntry")
        current_entry_id = _entry_id(current_entry)
        current_head = str(node.get("headRefOid") or "").lower()

        should_dequeue = (
            attributable_entry_id is not None
            and current_entry_id == attributable_entry_id
            and current_head == request.expected_head_sha
        )
        if should_dequeue:
            response = client.graphql(
                DEQUEUE_MUTATION,
                {
                    "pullRequestId": pull_node_id,
                    "clientMutationId": f"{attempt_id}:reconcile",
                },
            )
            payload = response.get("dequeuePullRequest")
            if not isinstance(payload, dict):
                raise SubmissionError("dequeuePullRequest response payload is missing")
            if payload.get("clientMutationId") != f"{attempt_id}:reconcile":
                raise SubmissionError("dequeuePullRequest response clientMutationId mismatch")

            after = _query_queue_node(client, pull_node_id)
            if _entry_id(after.get("mergeQueueEntry")) == attributable_entry_id:
                raise SubmissionError("attributable queue entry still exists after reconciliation")

    except Exception as reconciliation_error:
        raise SubmissionError(
            "enqueue result was not safely verifiable and attributable-entry reconciliation failed: "
            f"{reconciliation_error}; original error: {original_error}"
        ) from reconciliation_error

    if attributable_entry_id is None:
        cleanup = "no queue entry was attributable to this attempt; concurrent entries were left untouched"
    elif current_head != request.expected_head_sha:
        cleanup = "target head moved; current queue entry was left untouched"
    elif current_entry_id != attributable_entry_id:
        cleanup = "current queue entry is not the entry returned for this attempt and was left untouched"
    else:
        cleanup = "the exact attributable queue entry was reconciled/dequeued"

    raise SubmissionError(
        f"enqueue result was not safely verifiable; {cleanup}: {original_error}"
    ) from original_error


def enqueue_pull_request(
    client: Client,
    request: SubmissionRequest,
    pull: QualifiedPullRequest,
) -> tuple[str, Mapping[str, Any]]:
    existing = get_existing_queue_entry(client, request, pull)
    if existing is not None:
        return "ALREADY_ENQUEUED_EXACT_HEAD", existing

    attributable_entry_id: str | None = None
    try:
        data = client.graphql(
            ENQUEUE_MUTATION,
            {
                "pullRequestId": pull.node_id,
                "expectedHeadOid": request.expected_head_sha,
                "clientMutationId": request.attempt_id,
            },
        )
        payload = data.get("enqueuePullRequest")
        if not isinstance(payload, dict):
            raise SubmissionError("enqueuePullRequest response payload is missing")
        if payload.get("clientMutationId") != request.attempt_id:
            raise SubmissionError("enqueuePullRequest response clientMutationId mismatch")

        attributable_entry_id = _entry_id(payload.get("mergeQueueEntry"))
        if attributable_entry_id is None:
            raise SubmissionError("enqueuePullRequest response queue entry ID is missing")

        response_entry = _normalize_entry(
            request, payload.get("mergeQueueEntry"), require_pull_request=True
        )
        live_entry = get_existing_queue_entry(client, request, pull)
        if live_entry is None:
            raise SubmissionError("fresh post-enqueue read found no queue entry")
        if live_entry.get("id") != response_entry.get("id"):
            raise SubmissionError("fresh post-enqueue queue entry differs from mutation receipt")
        return "ENQUEUED", live_entry
    except SubmissionError as exc:
        _reconcile_after_indeterminate_enqueue(
            client,
            request=request,
            pull_node_id=pull.node_id,
            attempt_id=request.attempt_id,
            attributable_entry_id=attributable_entry_id,
            original_error=exc,
        )
        raise AssertionError("unreachable")


def receipt(
    request: SubmissionRequest,
    authorization: TargetAuthorization,
    *,
    status: str,
    entry: Mapping[str, Any],
) -> Mapping[str, Any]:
    if not _authorization_matches_request(authorization, request):
        raise SubmissionError("target authorization no longer matches the exact submission request")
    queue = entry["mergeQueue"]
    return {
        "schema": "OTERYN_MQ_SUBMISSION_V1",
        "status": status,
        "attempt_id": request.attempt_id,
        "authorization_source": authorization.source,
        "authorization_actor": authorization.actor,
        "authorization_comment_id": authorization.control_comment_id,
        "authorization_permission": authorization.permission,
        "owner_decision": authorization.owner_decision,
        "repository": request.repository,
        "pr_number": request.pr_number,
        "base_ref": "main",
        "expected_head_sha": request.expected_head_sha,
        "required_gate": request.required_gate,
        "merge_queue_entry_id": entry["id"],
        "merge_queue_entry_position": entry["position"],
        "merge_queue_entry_state": entry["state"],
        "merge_queue_id": queue["id"],
        "merge_queue_resource_path": queue["resourcePath"],
        "merge_queue_url": queue["url"],
    }


def write_github_outputs(request: SubmissionRequest, path: str) -> None:
    if not path:
        raise SubmissionError("github-output path is required")
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(f"repository={request.repository}\n")
        handle.write(f"repository_name={request.repository_name}\n")
        handle.write(f"pr_number={request.pr_number}\n")
        handle.write(f"expected_head_sha={request.expected_head_sha}\n")
        handle.write(f"attempt_id={request.attempt_id}\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fail-closed Oteryn Merge Queue submission executor"
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    parse = subparsers.add_parser("parse")
    parse.add_argument("--command", required=True)
    parse.add_argument("--github-output", required=True)

    authorize = subparsers.add_parser("authorize")
    authorize.add_argument("--actor", required=True)
    authorize.add_argument("--control-repository", required=True)
    authorize.add_argument("--control-issue", required=True, type=int)

    execute = subparsers.add_parser("execute")
    execute.add_argument("--command", required=True)
    execute.add_argument("--actor", required=True)
    execute.add_argument("--control-issue", required=True, type=int)
    execute.add_argument("--control-comment-id", required=True, type=int)
    execute.add_argument("--control-owner", required=True)
    execute.add_argument("--receipt-path", required=True)

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.mode == "parse":
            request = parse_command(args.command)
            write_github_outputs(request, args.github_output)
            return 0

        if args.mode == "authorize":
            token = os.environ.get("CONTROL_GITHUB_TOKEN", "")
            client = GitHubClient(
                token, os.environ.get("GITHUB_API_URL", "https://api.github.com")
            )
            permission = authorize_actor(
                client,
                actor=args.actor,
                actual_control_repository=args.control_repository,
                actual_control_issue=args.control_issue,
            )
            print(json.dumps({"authorized": True, "permission": permission}, sort_keys=True))
            return 0

        request = parse_command(args.command)
        target_token = os.environ.get("MQ_GITHUB_TOKEN", "")
        client = GitHubClient(
            target_token, os.environ.get("GITHUB_API_URL", "https://api.github.com")
        )
        authorization = authorize_target_submission(
            client,
            request,
            actor=args.actor,
            actual_control_issue=args.control_issue,
            control_comment_id=args.control_comment_id,
            control_owner_actor=args.control_owner,
        )
        if not _authorization_matches_request(authorization, request):
            raise SubmissionError(
                "authenticated target authorization does not match the exact submission request"
            )

        pull = qualify_pull_request(client, request)
        status, entry = enqueue_pull_request(client, request, pull)
        result = receipt(request, authorization, status=status, entry=entry)
        with open(args.receipt_path, "w", encoding="utf-8") as handle:
            json.dump(result, handle, sort_keys=True)
            handle.write("\n")
        print(json.dumps(result, sort_keys=True))
        return 0
    except (SubmissionError, OSError, ValueError) as exc:
        print(f"Merge Queue submission rejected: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())