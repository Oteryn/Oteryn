#!/usr/bin/env python3
"""Bounded organization-owned native Merge Queue executor.

The Issue comment is only a transport for a coordinator action already authorized
by higher-level repository policy. This executor does not create merge authority.
It re-reads the exact control comment and target state, then performs only the
selected REST merge-async operation with exact-head fencing.
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
import uuid
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Protocol

API_URL = "https://api.github.com"
API_VERSION = "2026-03-10"
EXPECTED_BASE = "main"
MERGE_ACTION = "merge_queue"
CONTROL_REPOSITORY = "Oteryn/Oteryn"
CONTROL_ISSUE = 196
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
CONTROL_COMMAND_RE = re.compile(
    r"^/oteryn-mq-submit "
    r"(Oteryn/(?:Oteryn|Oteryn-Game|Oteryn-Platform|Oteryn-Atlas)) "
    r"([1-9][0-9]*) ([0-9a-f]{40})$"
)
TRUSTED_ASSOCIATIONS = frozenset({"OWNER", "MEMBER"})
TARGET_GATES = {
    "Oteryn/Oteryn": "meta-gate",
    "Oteryn/Oteryn-Game": "game-gate",
    "Oteryn/Oteryn-Platform": "platform-gate",
    "Oteryn/Oteryn-Atlas": "atlas-gate",
}


class ExecutorError(RuntimeError):
    pass


@dataclass(frozen=True)
class Response:
    status: int
    body: Mapping[str, Any]


class Client(Protocol):
    def rest(
        self,
        method: str,
        path: str,
        *,
        body: Mapping[str, Any] | None = None,
        allowed_statuses: tuple[int, ...] = (200,),
    ) -> Response: ...


class GitHubClient:
    def __init__(self, *, token: str | None = None, api_url: str = API_URL) -> None:
        self.token = (token or "").strip()
        self.api_url = api_url.rstrip("/")

    def rest(
        self,
        method: str,
        path: str,
        *,
        body: Mapping[str, Any] | None = None,
        allowed_statuses: tuple[int, ...] = (200,),
    ) -> Response:
        data = None if body is None else json.dumps(body).encode("utf-8")
        headers = {
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "oteryn-governed-merge-queue-executor",
            "X-GitHub-Api-Version": API_VERSION,
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = urllib.request.Request(
            f"{self.api_url}{path}",
            data=data,
            method=method,
            headers=headers,
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as raw_response:
                status = raw_response.status
                raw = raw_response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            status = exc.code
            raw = exc.read().decode("utf-8", errors="replace")
            if status not in allowed_statuses:
                raise ExecutorError(
                    f"GitHub API {method} {path} failed with HTTP {status}"
                ) from exc
        except urllib.error.URLError as exc:
            raise ExecutorError(f"GitHub API {method} {path} transport failure") from exc

        if status not in allowed_statuses:
            raise ExecutorError(
                f"GitHub API {method} {path} returned unexpected HTTP {status}"
            )
        if raw:
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ExecutorError("GitHub API returned invalid JSON") from exc
        else:
            parsed = {}
        if not isinstance(parsed, dict):
            raise ExecutorError("GitHub API returned non-object JSON")
        return Response(status=status, body=parsed)


@dataclass(frozen=True)
class QualifiedTarget:
    repository: str
    pr_number: int
    base: str
    head_sha: str
    required_gate: str
    request_comment_id: int


@dataclass(frozen=True)
class Receipt:
    repository: str
    pr_number: int
    base: str
    expected_head_sha: str
    merge_action: str
    status: str
    server_uuid: str
    executor_sequence: int


class ExecutorSequence:
    def __init__(self) -> None:
        self._value = 0

    def next(self) -> int:
        self._value += 1
        return self._value


def _response_body(response: Response) -> Mapping[str, Any]:
    return response.body


def normalize_inputs(
    repository: str,
    pr_number: int,
    expected_head_sha: str,
    request_comment_id: int,
) -> tuple[str, int, str, int]:
    repository = repository.strip()
    expected_head_sha = expected_head_sha.strip()
    if repository not in TARGET_GATES:
        raise ValueError("repository is not an allowed permanent Oteryn target")
    if isinstance(pr_number, bool) or not isinstance(pr_number, int) or pr_number <= 0:
        raise ValueError("PR number must be a positive integer")
    if not SHA_RE.fullmatch(expected_head_sha):
        raise ValueError(
            "expected head SHA must be exactly 40 lowercase hexadecimal characters"
        )
    if (
        isinstance(request_comment_id, bool)
        or not isinstance(request_comment_id, int)
        or request_comment_id <= 0
    ):
        raise ValueError("request comment id must be a positive integer")
    return repository, pr_number, expected_head_sha, request_comment_id


def verify_control_request(
    read_client: Client,
    *,
    repository: str,
    pr_number: int,
    expected_head_sha: str,
    request_comment_id: int,
) -> None:
    comment = _response_body(
        read_client.rest(
            "GET",
            f"/repos/Oteryn/Oteryn/issues/comments/{request_comment_id}",
        )
    )
    if comment.get("author_association") not in TRUSTED_ASSOCIATIONS:
        raise ValueError("control request actor must be OWNER or MEMBER of META")
    expected_issue_url = (
        f"https://api.github.com/repos/{CONTROL_REPOSITORY}/issues/{CONTROL_ISSUE}"
    )
    if comment.get("issue_url") != expected_issue_url:
        raise ValueError("control request comment is not on the canonical META control issue")
    body = comment.get("body")
    match = CONTROL_COMMAND_RE.fullmatch(body) if isinstance(body, str) else None
    if match is None:
        raise ValueError("control request body does not match the closed command grammar")
    requested_repository, requested_pr, requested_head = match.groups()
    if (
        requested_repository != repository
        or int(requested_pr) != pr_number
        or requested_head != expected_head_sha
    ):
        raise ValueError("live control request does not match workflow-bound target coordinates")


def _validate_target_identity(
    pull: Mapping[str, Any],
    *,
    repository: str,
    expected_head_sha: str,
    require_open_ready: bool,
) -> None:
    if require_open_ready:
        if pull.get("state") != "open" or pull.get("merged") is True:
            raise ValueError("pull request must be open and unmerged")
        if pull.get("draft") is not False:
            raise ValueError("pull request must be ready for review")
    base = pull.get("base")
    if not isinstance(base, dict) or base.get("ref") != EXPECTED_BASE:
        raise ValueError("pull request base must be exactly main")
    head = pull.get("head")
    if not isinstance(head, dict):
        raise ValueError("pull request head metadata is missing")
    if str(head.get("sha") or "").lower() != expected_head_sha:
        raise ValueError("pull request head does not match the qualified exact head")
    head_repo = head.get("repo")
    if not isinstance(head_repo, dict) or head_repo.get("full_name") != repository:
        raise ValueError("pull request must use a same-repository head")


def qualify_target(
    read_client: Client,
    *,
    repository: str,
    pr_number: int,
    expected_head_sha: str,
    request_comment_id: int,
) -> QualifiedTarget:
    repository, pr_number, expected_head_sha, request_comment_id = normalize_inputs(
        repository, pr_number, expected_head_sha, request_comment_id
    )
    verify_control_request(
        read_client,
        repository=repository,
        pr_number=pr_number,
        expected_head_sha=expected_head_sha,
        request_comment_id=request_comment_id,
    )

    owner, name = repository.split("/", 1)
    pull = _response_body(
        read_client.rest("GET", f"/repos/{owner}/{name}/pulls/{pr_number}")
    )
    _validate_target_identity(
        pull,
        repository=repository,
        expected_head_sha=expected_head_sha,
        require_open_ready=True,
    )

    required_gate = TARGET_GATES[repository]
    query = urllib.parse.urlencode(
        {"check_name": required_gate, "filter": "latest", "per_page": "100"}
    )
    checks = _response_body(
        read_client.rest(
            "GET",
            f"/repos/{owner}/{name}/commits/{expected_head_sha}/check-runs?{query}",
        )
    )
    runs = checks.get("check_runs")
    if not isinstance(runs, list) or not runs:
        raise ValueError(f"no exact-head {required_gate} check run was found")
    matching = [
        run
        for run in runs
        if isinstance(run, dict)
        and run.get("name") == required_gate
        and str(run.get("head_sha") or "").lower() == expected_head_sha
        and isinstance(run.get("app"), dict)
        and run["app"].get("slug") == "github-actions"
    ]
    if not matching:
        raise ValueError(
            f"no GitHub-Actions {required_gate} check run matches the exact target head"
        )
    latest = max(matching, key=lambda run: int(run.get("id") or 0))
    if latest.get("status") != "completed" or latest.get("conclusion") != "success":
        raise ValueError(f"latest exact-head {required_gate} must be completed/success")
    return QualifiedTarget(
        repository,
        pr_number,
        EXPECTED_BASE,
        expected_head_sha,
        required_gate,
        request_comment_id,
    )


def _valid_uuid(value: object) -> str:
    if not isinstance(value, str):
        raise ExecutorError("merge-async response is missing a server UUID")
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError) as exc:
        raise ExecutorError("merge-async response UUID is invalid") from exc
    canonical = str(parsed)
    if value.lower() != canonical:
        raise ExecutorError("merge-async response UUID is not canonical")
    return canonical


def _server_fields(
    payload: Mapping[str, Any], *, require_uuid: bool
) -> tuple[str, str, str, str]:
    status = payload.get("status")
    details = payload.get("details")
    if not isinstance(status, str) or not status or not isinstance(details, dict):
        raise ExecutorError("merge-async response is missing status/details")
    server_uuid = _valid_uuid(details.get("uuid")) if require_uuid else ""
    action = str(details.get("merge_action") or "")
    head = str(details.get("expected_head_sha") or "").lower()
    return status, server_uuid, action, head


def _readback(
    read_client: Client,
    mutation_client: Client,
    target: QualifiedTarget,
    *,
    server_uuid: str,
    sequence: ExecutorSequence,
    prior_sequence: int,
) -> Receipt:
    owner, name = target.repository.split("/", 1)
    async_result = _response_body(
        mutation_client.rest(
            "GET",
            f"/repos/{owner}/{name}/pulls/{target.pr_number}/merge-async/{server_uuid}",
        )
    )
    status, readback_uuid, action, head = _server_fields(
        async_result, require_uuid=True
    )
    if readback_uuid != server_uuid:
        raise ExecutorError("merge-async readback UUID differs from accepted request UUID")
    if action != MERGE_ACTION or head != target.head_sha:
        raise ExecutorError("merge-async readback does not bind merge_queue and exact head")

    fresh_pull = _response_body(
        read_client.rest("GET", f"/repos/{owner}/{name}/pulls/{target.pr_number}")
    )
    try:
        _validate_target_identity(
            fresh_pull,
            repository=target.repository,
            expected_head_sha=target.head_sha,
            require_open_ready=False,
        )
    except ValueError as exc:
        raise ExecutorError(f"post-submission target mismatch: {exc}") from exc

    readback_sequence = sequence.next()
    if readback_sequence <= prior_sequence:
        raise ExecutorError("readback sequence must be strictly later than receipt sequence")
    return Receipt(
        target.repository,
        target.pr_number,
        target.base,
        target.head_sha,
        action,
        status,
        readback_uuid,
        readback_sequence,
    )


def submit_merge_queue(
    read_client: Client,
    mutation_client: Client,
    target: QualifiedTarget,
) -> Mapping[str, Any]:
    owner, name = target.repository.split("/", 1)
    sequence = ExecutorSequence()
    response = mutation_client.rest(
        "PUT",
        f"/repos/{owner}/{name}/pulls/{target.pr_number}/merge-async",
        body={"sha": target.head_sha, "merge_action": MERGE_ACTION},
        allowed_statuses=(200, 202, 400, 403, 404, 409, 422),
    )

    if response.status in (400, 422):
        raise ExecutorError(f"REQUEST_REJECTED_HTTP_{response.status}")
    if response.status in (403, 404):
        raise ExecutorError(
            f"BLOCKED_CAPABILITY_UNAVAILABLE: merge-async returned HTTP {response.status}"
        )

    if response.status == 202:
        status, server_uuid, action, head = _server_fields(
            response.body, require_uuid=True
        )
        if action != MERGE_ACTION or head != target.head_sha:
            raise ExecutorError(
                "merge-async acceptance does not bind exact head and merge_queue"
            )
        receipt_sequence = sequence.next()
        receipt = Receipt(
            target.repository,
            target.pr_number,
            target.base,
            target.head_sha,
            action,
            status,
            server_uuid,
            receipt_sequence,
        )
        readback = _readback(
            read_client,
            mutation_client,
            target,
            server_uuid=server_uuid,
            sequence=sequence,
            prior_sequence=receipt_sequence,
        )
        return {
            "result": "REQUEST_ACCEPTED_NON_TERMINAL",
            "request_comment_id": target.request_comment_id,
            "receipt": asdict(receipt),
            "readback": asdict(readback),
        }

    # HTTP 200/409 is reconciliation only: it never fabricates a new acceptance receipt.
    details = response.body.get("details")
    readback: Mapping[str, Any] | None = None
    if isinstance(details, dict) and details.get("uuid") is not None:
        server_uuid = _valid_uuid(details.get("uuid"))
        readback = asdict(
            _readback(
                read_client,
                mutation_client,
                target,
                server_uuid=server_uuid,
                sequence=sequence,
                prior_sequence=0,
            )
        )
    else:
        fresh_pull = _response_body(
            read_client.rest("GET", f"/repos/{owner}/{name}/pulls/{target.pr_number}")
        )
        _validate_target_identity(
            fresh_pull,
            repository=target.repository,
            expected_head_sha=target.head_sha,
            require_open_ready=False,
        )
    return {
        "result": "RECONCILIATION_REQUIRED",
        "request_comment_id": target.request_comment_id,
        "http_status": response.status,
        "accepted": False,
        "receipt": None,
        "readback": readback,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--pr-number", required=True, type=int)
    parser.add_argument("--expected-head-sha", required=True)
    parser.add_argument("--request-comment-id", required=True, type=int)
    args = parser.parse_args()

    mutation_token = os.environ.get("OTERYN_MQ_FINE_GRAINED_PAT", "").strip()
    if not mutation_token:
        print(
            "BLOCKED_CAPABILITY_UNAVAILABLE: OTERYN_MQ_FINE_GRAINED_PAT is not provisioned",
            file=sys.stderr,
        )
        return 2

    try:
        read_client = GitHubClient()
        mutation_client = GitHubClient(token=mutation_token)
        target = qualify_target(
            read_client,
            repository=args.repository,
            pr_number=args.pr_number,
            expected_head_sha=args.expected_head_sha,
            request_comment_id=args.request_comment_id,
        )
        result = submit_merge_queue(read_client, mutation_client, target)
    except (ValueError, ExecutorError) as exc:
        print(f"Merge Queue executor rejected request: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
