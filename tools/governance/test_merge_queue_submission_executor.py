#!/usr/bin/env python3
"""Regressions for the protected-default-branch Merge Queue submission executor."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("merge_queue_submission_executor.py")
SPEC = importlib.util.spec_from_file_location("merge_queue_submission_executor", MODULE_PATH)
assert SPEC and SPEC.loader
executor = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = executor
SPEC.loader.exec_module(executor)

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/merge-queue-submission.yml"

ATTEMPT_ID = "attempt-20260909-0001"
REPOSITORY = "Oteryn/Oteryn-Platform"
PR_NUMBER = 1378
HEAD = "a" * 40
OTHER_HEAD = "b" * 40
COMMAND = f"{executor.COMMAND_PREFIX} {ATTEMPT_ID} {REPOSITORY} {PR_NUMBER} {HEAD}"


def queue_identity(**overrides):
    values = {
        "id": "MQ_platform_main_001",
        "resourcePath": "/Oteryn/Oteryn-Platform/queue/main",
        "url": "https://github.com/Oteryn/Oteryn-Platform/queue/main",
    }
    values.update(overrides)
    return values


def queue_entry(*, include_pull=False, **overrides):
    values = {
        "id": "MQE_platform_001",
        "position": 1,
        "state": "QUEUED",
        "mergeQueue": queue_identity(),
    }
    if include_pull:
        values["pullRequest"] = {
            "id": "PR_node_1378",
            "number": PR_NUMBER,
            "headRefOid": HEAD,
            "baseRefName": "main",
            "repository": {"nameWithOwner": REPOSITORY},
        }
    values.update(overrides)
    return values


def pull(**overrides):
    values = {
        "state": "open",
        "merged": False,
        "draft": False,
        "node_id": "PR_node_1378",
        "base": {"ref": "main"},
        "head": {"sha": HEAD, "repo": {"full_name": REPOSITORY}},
    }
    values.update(overrides)
    return values


def checks(**overrides):
    run = {
        "id": 101,
        "name": "platform-gate",
        "head_sha": HEAD,
        "status": "completed",
        "conclusion": "success",
        "app": {"id": executor.GITHUB_ACTIONS_APP_ID},
    }
    run.update(overrides)
    return {"check_runs": [run]}


class FakeClient:
    def __init__(
        self,
        *,
        permission="write",
        pull_response=None,
        check_response=None,
        existing_entry=None,
        mutation_entry=None,
        mutation_client_id=ATTEMPT_ID,
    ):
        self.permission = permission
        self.pull_response = pull_response if pull_response is not None else pull()
        self.check_response = check_response if check_response is not None else checks()
        self.existing_entry = existing_entry
        self.mutation_entry = mutation_entry if mutation_entry is not None else queue_entry(include_pull=True)
        self.mutation_client_id = mutation_client_id
        self.rest_calls = []
        self.graphql_calls = []

    def rest(self, method, path):
        self.rest_calls.append((method, path))
        if "/collaborators/" in path and path.endswith("/permission"):
            return {"permission": self.permission}
        if "/pulls/" in path:
            return self.pull_response
        if "/check-runs?" in path:
            return self.check_response
        raise AssertionError(f"unexpected REST call: {method} {path}")

    def graphql(self, query, variables):
        self.graphql_calls.append((query, dict(variables)))
        if query == executor.QUEUE_ENTRY_QUERY:
            return {
                "node": {
                    "id": "PR_node_1378",
                    "number": PR_NUMBER,
                    "headRefOid": HEAD,
                    "baseRefName": "main",
                    "repository": {"nameWithOwner": REPOSITORY},
                    "mergeQueueEntry": self.existing_entry,
                }
            }
        if query == executor.ENQUEUE_MUTATION:
            return {
                "enqueuePullRequest": {
                    "clientMutationId": self.mutation_client_id,
                    "mergeQueueEntry": self.mutation_entry,
                }
            }
        raise AssertionError("unexpected GraphQL query")


def request():
    return executor.parse_command(COMMAND)


def qualified(client=None):
    current = client or FakeClient()
    return current, executor.qualify_pull_request(current, request())


def assert_submission_error(fn, marker):
    try:
        fn()
    except executor.SubmissionError as exc:
        assert marker in str(exc), (marker, str(exc))
    else:
        raise AssertionError(f"expected SubmissionError containing {marker!r}")


def test_command_parser_is_closed_and_target_allowlisted() -> None:
    parsed = request()
    assert parsed.attempt_id == ATTEMPT_ID
    assert parsed.repository == REPOSITORY
    assert parsed.repository_name == "Oteryn-Platform"
    assert parsed.pr_number == PR_NUMBER
    assert parsed.expected_head_sha == HEAD
    assert parsed.required_gate == "platform-gate"
    for bad in (
        "",
        f"{executor.COMMAND_PREFIX} short {REPOSITORY} {PR_NUMBER} {HEAD}",
        f"{executor.COMMAND_PREFIX} {ATTEMPT_ID} Oteryn/Other {PR_NUMBER} {HEAD}",
        f"{executor.COMMAND_PREFIX} {ATTEMPT_ID} {REPOSITORY} zero {HEAD}",
        f"{executor.COMMAND_PREFIX} {ATTEMPT_ID} {REPOSITORY} 0 {HEAD}",
        f"{executor.COMMAND_PREFIX} {ATTEMPT_ID} {REPOSITORY} {PR_NUMBER} deadbeef",
        f"{executor.COMMAND_PREFIX} {ATTEMPT_ID} {REPOSITORY} {PR_NUMBER} {HEAD} extra",
    ):
        assert_submission_error(lambda bad=bad: executor.parse_command(bad), "")


def test_control_actor_requires_exact_endpoint_and_current_write_permission() -> None:
    client = FakeClient(permission="write")
    assert executor.authorize_actor(
        client,
        actor="blakinio",
        actual_control_repository=executor.CONTROL_REPOSITORY,
        actual_control_issue=executor.CONTROL_ISSUE,
    ) == "write"
    assert client.rest_calls[-1][1].endswith("/repos/Oteryn/Oteryn/collaborators/blakinio/permission")

    for permission in ("read", "triage", "none", None):
        denied = FakeClient(permission=permission)
        assert_submission_error(
            lambda denied=denied: executor.authorize_actor(
                denied,
                actor="reader",
                actual_control_repository=executor.CONTROL_REPOSITORY,
                actual_control_issue=executor.CONTROL_ISSUE,
            ),
            "lacks current write/maintain/admin",
        )
    assert_submission_error(
        lambda: executor.authorize_actor(
            FakeClient(),
            actor="blakinio",
            actual_control_repository="Oteryn/Oteryn-Game",
            actual_control_issue=executor.CONTROL_ISSUE,
        ),
        "canonical control endpoint",
    )
    assert_submission_error(
        lambda: executor.authorize_actor(
            FakeClient(),
            actor="blakinio",
            actual_control_repository=executor.CONTROL_REPOSITORY,
            actual_control_issue=189,
        ),
        "canonical control endpoint",
    )


def test_target_actor_requires_current_target_repository_write_permission() -> None:
    client = FakeClient(permission="maintain")
    assert executor.authorize_target_actor(client, request(), actor="blakinio") == "maintain"
    assert client.rest_calls[-1][1].endswith(
        "/repos/Oteryn/Oteryn-Platform/collaborators/blakinio/permission"
    )
    for permission in ("read", "triage", "none", None):
        denied = FakeClient(permission=permission)
        assert_submission_error(
            lambda denied=denied: executor.authorize_target_actor(
                denied, request(), actor="reader"
            ),
            "target repository Oteryn/Oteryn-Platform",
        )
    for actor in ("", "bad/name", None):
        assert_submission_error(
            lambda actor=actor: executor.authorize_target_actor(
                FakeClient(), request(), actor=actor
            ),
            "invalid comment actor",
        )


def test_pull_qualification_binds_open_ready_same_repo_main_exact_head_and_gate() -> None:
    client, result = qualified()
    assert result.node_id == "PR_node_1378"
    assert result.head_sha == HEAD
    assert result.base_ref == "main"
    assert any("check_name=platform-gate" in path for _, path in client.rest_calls)

    invalid_pulls = (
        (pull(state="closed"), "open and unmerged"),
        (pull(merged=True), "open and unmerged"),
        (pull(draft=True), "non-draft"),
        (pull(base={"ref": "release"}), "base must be exactly main"),
        (pull(head={"sha": OTHER_HEAD, "repo": {"full_name": REPOSITORY}}), "head changed"),
        (pull(head={"sha": HEAD, "repo": {"full_name": "fork/repo"}}), "same-repository"),
        (pull(node_id=""), "node ID is missing"),
    )
    for candidate, marker in invalid_pulls:
        client = FakeClient(pull_response=candidate)
        assert_submission_error(lambda client=client: executor.qualify_pull_request(client, request()), marker)

    invalid_checks = (
        (checks(status="in_progress", conclusion=None), "completed/success"),
        (checks(conclusion="failure"), "completed/success"),
        (checks(head_sha=OTHER_HEAD), "matches the exact expected head"),
        (checks(name="other-gate"), "matches the exact expected head"),
        (checks(app={"id": 1}), "GitHub Actions gate"),
    )
    for candidate, marker in invalid_checks:
        client = FakeClient(check_response=candidate)
        assert_submission_error(lambda client=client: executor.qualify_pull_request(client, request()), marker)


def test_existing_exact_queue_entry_is_idempotent_and_no_mutation_occurs() -> None:
    client = FakeClient(existing_entry=queue_entry())
    pull_result = executor.qualify_pull_request(client, request())
    status, entry = executor.enqueue_pull_request(client, request(), pull_result)
    assert status == "ALREADY_ENQUEUED_EXACT_HEAD"
    assert entry["id"] == "MQE_platform_001"
    assert len(client.graphql_calls) == 1
    assert client.graphql_calls[0][0] == executor.QUEUE_ENTRY_QUERY


def test_enqueue_mutation_uses_expected_head_and_attempt_id_and_binds_response() -> None:
    client = FakeClient(existing_entry=None)
    pull_result = executor.qualify_pull_request(client, request())
    status, entry = executor.enqueue_pull_request(client, request(), pull_result)
    assert status == "ENQUEUED"
    assert entry["id"] == "MQE_platform_001"
    assert len(client.graphql_calls) == 2
    query, variables = client.graphql_calls[1]
    assert query == executor.ENQUEUE_MUTATION
    assert variables == {
        "pullRequestId": "PR_node_1378",
        "expectedHeadOid": HEAD,
        "clientMutationId": ATTEMPT_ID,
    }
    for marker in ("enqueuePullRequest", "expectedHeadOid", "clientMutationId"):
        assert marker in executor.ENQUEUE_MUTATION
    for forbidden in ("enablePullRequestAutoMerge", "mergePullRequest", "direct_merge"):
        assert forbidden not in executor.ENQUEUE_MUTATION


def test_queue_and_mutation_response_identity_fail_closed() -> None:
    bad_queues = (
        queue_identity(resourcePath="/Oteryn/Oteryn-Platform/queue/release"),
        queue_identity(url="https://github.com/Oteryn/Oteryn-Game/queue/main"),
        queue_identity(id=""),
    )
    for bad_queue in bad_queues:
        client = FakeClient(existing_entry=queue_entry(mergeQueue=bad_queue))
        pull_result = executor.qualify_pull_request(client, request())
        assert_submission_error(
            lambda client=client, pull_result=pull_result: executor.enqueue_pull_request(
                client, request(), pull_result
            ),
            "merge queue",
        )

    wrong_pull_entry = queue_entry(include_pull=True)
    wrong_pull_entry["pullRequest"] = {**wrong_pull_entry["pullRequest"], "headRefOid": OTHER_HEAD}
    client = FakeClient(existing_entry=None, mutation_entry=wrong_pull_entry)
    pull_result = executor.qualify_pull_request(client, request())
    assert_submission_error(
        lambda: executor.enqueue_pull_request(client, request(), pull_result),
        "pull request identity",
    )

    client = FakeClient(existing_entry=None, mutation_client_id="other-attempt")
    pull_result = executor.qualify_pull_request(client, request())
    assert_submission_error(
        lambda: executor.enqueue_pull_request(client, request(), pull_result),
        "clientMutationId mismatch",
    )


def test_receipt_contains_only_exact_submission_coordinates() -> None:
    assert executor.receipt(request(), status="ENQUEUED", entry=queue_entry()) == {
        "schema": "OTERYN_MQ_SUBMISSION_V1",
        "status": "ENQUEUED",
        "attempt_id": ATTEMPT_ID,
        "repository": REPOSITORY,
        "pr_number": PR_NUMBER,
        "base_ref": "main",
        "expected_head_sha": HEAD,
        "required_gate": "platform-gate",
        "merge_queue_entry_id": "MQE_platform_001",
        "merge_queue_entry_position": 1,
        "merge_queue_entry_state": "QUEUED",
        "merge_queue_id": "MQ_platform_main_001",
        "merge_queue_resource_path": "/Oteryn/Oteryn-Platform/queue/main",
        "merge_queue_url": "https://github.com/Oteryn/Oteryn-Platform/queue/main",
    }


def test_workflow_is_protected_comment_triggered_least_privilege_and_exact_target_scoped() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    for marker in (
        "issue_comment:",
        "types: [created]",
        "github.event.issue.number == 190",
        "!github.event.issue.pull_request",
        "github.event.comment.author_association",
        "startsWith(github.event.comment.body, '/oteryn-mq-submit ')",
        "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
        "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97",
        "actions/create-github-app-token@bcd2ba49218906704ab6c1aa796996da409d3eb1",
        "owner: Oteryn",
        "repositories: ${{ steps.parse.outputs.repository_name }}",
        "permission-checks: read",
        "permission-pull-requests: read",
        "permission-merge-queues: write",
        "CONTROL_GITHUB_TOKEN: ${{ github.token }}",
        "MQ_GITHUB_TOKEN: ${{ steps.app-token.outputs.token }}",
        "COMMENT_ACTOR: ${{ github.event.comment.user.login }}",
        "--actor \"$COMMENT_ACTOR\"",
        "OTERYN_MQ_APP_CLIENT_ID",
        "OTERYN_MQ_APP_PRIVATE_KEY",
    ):
        assert marker in text, marker
    assert text.index("Authorize current control-endpoint actor") < text.index(
        "Mint target-repository Merge Queue App token"
    )
    assert text.index("Parse exact submission command") < text.index(
        "Mint target-repository Merge Queue App token"
    )
    for forbidden in (
        "enablePullRequestAutoMerge",
        "merge-async",
        "direct_merge",
        "merge_pull_request",
        "contents: write",
        "pull-requests: write",
        "workflow_dispatch:",
    ):
        assert forbidden not in text, forbidden


def test_executor_has_no_direct_merge_or_generic_auto_merge_operation() -> None:
    text = MODULE_PATH.read_text(encoding="utf-8")
    assert "enqueuePullRequest" in text
    assert "expectedHeadOid" in text
    assert "authorize_target_actor" in text
    for forbidden in (
        "enablePullRequestAutoMerge",
        "mergePullRequest(input",
        "/merge-async",
        "direct_merge",
    ):
        assert forbidden not in text, forbidden


def main() -> int:
    failures = []
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            failures.append((name, exc))
    if failures:
        for name, exc in failures:
            print(f"FAIL {name}: {exc}")
        return 1
    print(f"PASS {len(tests)} protected Merge Queue executor regressions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
