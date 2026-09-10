#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = Path(__file__).with_name("governed_merge_queue_executor.py")
SPEC = importlib.util.spec_from_file_location("governed_merge_queue_executor", MODULE_PATH)
assert SPEC and SPEC.loader
executor = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = executor
SPEC.loader.exec_module(executor)

REPO = "Oteryn/Oteryn-Game"
PR = 528
HEAD = "97fcf72a2f29a8fc134c97dd3cdaf9237be7c6d3"
REQUEST_COMMENT = 5617345429
SERVER_UUID = "f0a3d092-6c9f-4edd-9d3f-cb9d8865a935"


class FakeClient:
    def __init__(self, responses: dict[tuple[str, str], executor.Response]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, str, Mapping[str, Any] | None]] = []

    def rest(
        self,
        method: str,
        path: str,
        *,
        body: Mapping[str, Any] | None = None,
        allowed_statuses: tuple[int, ...] = (200,),
    ) -> executor.Response:
        self.calls.append((method, path, body))
        response = self.responses.get((method, path))
        if response is None:
            raise AssertionError(f"unexpected request: {method} {path}")
        if response.status not in allowed_statuses:
            raise AssertionError(
                f"fixture status {response.status} not in allowed statuses {allowed_statuses}"
            )
        return response


def control_body(
    repository: str = REPO, pr_number: int = PR, head: str = HEAD
) -> str:
    return f"/oteryn-mq-submit {repository} {pr_number} {head}"


def pull(
    *,
    head: str = HEAD,
    base: str = "main",
    draft: bool = False,
    state: str = "open",
    head_repository: str = REPO,
) -> dict:
    return {
        "state": state,
        "merged": state == "closed",
        "draft": draft,
        "base": {"ref": base},
        "head": {"sha": head, "repo": {"full_name": head_repository}},
    }


def read_responses() -> dict[tuple[str, str], executor.Response]:
    gate_query = "check_name=game-gate&filter=latest&per_page=100"
    return {
        (
            "GET",
            f"/repos/Oteryn/Oteryn/issues/comments/{REQUEST_COMMENT}",
        ): executor.Response(
            200,
            {
                "author_association": "MEMBER",
                "issue_url": "https://api.github.com/repos/Oteryn/Oteryn/issues/196",
                "body": control_body(),
            },
        ),
        (
            "GET",
            f"/repos/Oteryn/Oteryn-Game/pulls/{PR}",
        ): executor.Response(200, pull()),
        (
            "GET",
            f"/repos/Oteryn/Oteryn-Game/commits/{HEAD}/check-runs?{gate_query}",
        ): executor.Response(
            200,
            {
                "check_runs": [
                    {
                        "id": 10,
                        "name": "game-gate",
                        "head_sha": HEAD,
                        "status": "completed",
                        "conclusion": "success",
                        "app": {"slug": "github-actions"},
                    }
                ]
            },
        ),
    }


def qualified(read_client: FakeClient) -> executor.QualifiedTarget:
    return executor.qualify_target(
        read_client,
        repository=REPO,
        pr_number=PR,
        expected_head_sha=HEAD,
        request_comment_id=REQUEST_COMMENT,
    )


def test_allowlist_binds_every_permanent_repository_to_its_gate() -> None:
    assert executor.TARGET_GATES == {
        "Oteryn/Oteryn": "meta-gate",
        "Oteryn/Oteryn-Game": "game-gate",
        "Oteryn/Oteryn-Platform": "platform-gate",
        "Oteryn/Oteryn-Atlas": "atlas-gate",
    }


def test_control_request_is_one_live_exact_transport_record() -> None:
    client = FakeClient(read_responses())
    target = qualified(client)
    assert target.repository == REPO
    assert target.pr_number == PR
    assert target.head_sha == HEAD
    assert target.request_comment_id == REQUEST_COMMENT


def test_control_request_wrong_issue_body_actor_or_coordinates_fail_closed() -> None:
    comment_key = ("GET", f"/repos/Oteryn/Oteryn/issues/comments/{REQUEST_COMMENT}")
    mutations = (
        ("issue_url", "https://api.github.com/repos/Oteryn/Oteryn/issues/999"),
        ("body", control_body(head="a" * 40)),
        ("body", control_body() + "\n"),
        ("author_association", "COLLABORATOR"),
        ("author_association", "CONTRIBUTOR"),
    )
    for field, value in mutations:
        responses = read_responses()
        body = dict(responses[comment_key].body)
        body[field] = value
        responses[comment_key] = executor.Response(200, body)
        try:
            qualified(FakeClient(responses))
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid control request field {field} was accepted")


def test_target_must_be_open_ready_main_same_repo_and_exact_head() -> None:
    mutations = (
        {"draft": True},
        {"base": "other"},
        {"head": "a" * 40},
        {"state": "closed"},
        {"head_repository": "someone/fork"},
    )
    for mutation in mutations:
        responses = read_responses()
        key = ("GET", f"/repos/Oteryn/Oteryn-Game/pulls/{PR}")
        responses[key] = executor.Response(200, pull(**mutation))
        try:
            qualified(FakeClient(responses))
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid target mutation was accepted: {mutation}")


def test_latest_exact_head_provider_gate_must_be_success() -> None:
    responses = read_responses()
    query = "check_name=game-gate&filter=latest&per_page=100"
    key = ("GET", f"/repos/Oteryn/Oteryn-Game/commits/{HEAD}/check-runs?{query}")
    responses[key] = executor.Response(
        200,
        {
            "check_runs": [
                {
                    "id": 11,
                    "name": "game-gate",
                    "head_sha": HEAD,
                    "status": "completed",
                    "conclusion": "failure",
                    "app": {"slug": "github-actions"},
                }
            ]
        },
    )
    try:
        qualified(FakeClient(responses))
    except ValueError as exc:
        assert "completed/success" in str(exc)
    else:
        raise AssertionError("failed source-head gate was accepted")


def test_exact_head_gate_must_come_from_github_actions() -> None:
    responses = read_responses()
    query = "check_name=game-gate&filter=latest&per_page=100"
    key = ("GET", f"/repos/Oteryn/Oteryn-Game/commits/{HEAD}/check-runs?{query}")
    spoofed = dict(responses[key].body["check_runs"][0])
    spoofed["app"] = {"slug": "untrusted-app"}
    responses[key] = executor.Response(200, {"check_runs": [spoofed]})
    try:
        qualified(FakeClient(responses))
    except ValueError as exc:
        assert "GitHub-Actions" in str(exc)
    else:
        raise AssertionError("spoofed non-GitHub-Actions gate was accepted")


def test_202_uses_only_exact_merge_async_request_and_causal_uuid_readback() -> None:
    read_client = FakeClient(read_responses())
    target = qualified(read_client)
    mutation_client = FakeClient(
        {
            (
                "PUT",
                f"/repos/Oteryn/Oteryn-Game/pulls/{PR}/merge-async",
            ): executor.Response(
                202,
                {
                    "status": "accepted",
                    "details": {
                        "uuid": SERVER_UUID,
                        "merge_action": "merge_queue",
                        "expected_head_sha": HEAD,
                    },
                },
            ),
            (
                "GET",
                f"/repos/Oteryn/Oteryn-Game/pulls/{PR}/merge-async/{SERVER_UUID}",
            ): executor.Response(
                200,
                {
                    "status": "enqueued",
                    "details": {
                        "uuid": SERVER_UUID,
                        "merge_action": "merge_queue",
                        "expected_head_sha": HEAD,
                    },
                },
            ),
        }
    )

    result = executor.submit_merge_queue(read_client, mutation_client, target)

    assert result["result"] == "REQUEST_ACCEPTED_NON_TERMINAL"
    assert result["request_comment_id"] == REQUEST_COMMENT
    assert result["receipt"]["server_uuid"] == SERVER_UUID
    assert result["receipt"]["executor_sequence"] == 1
    assert result["readback"]["server_uuid"] == SERVER_UUID
    assert result["readback"]["executor_sequence"] == 2
    put_calls = [call for call in mutation_client.calls if call[0] == "PUT"]
    assert put_calls == [
        (
            "PUT",
            f"/repos/Oteryn/Oteryn-Game/pulls/{PR}/merge-async",
            {"sha": HEAD, "merge_action": "merge_queue"},
        )
    ]


def test_202_rejects_wrong_uuid_bound_head_or_action() -> None:
    for details in (
        {"uuid": "not-a-uuid", "merge_action": "merge_queue", "expected_head_sha": HEAD},
        {"uuid": SERVER_UUID, "merge_action": "default", "expected_head_sha": HEAD},
        {"uuid": SERVER_UUID, "merge_action": "merge_queue", "expected_head_sha": "a" * 40},
    ):
        read_client = FakeClient(read_responses())
        target = qualified(read_client)
        mutation_client = FakeClient(
            {
                (
                    "PUT",
                    f"/repos/Oteryn/Oteryn-Game/pulls/{PR}/merge-async",
                ): executor.Response(202, {"status": "accepted", "details": details})
            }
        )
        try:
            executor.submit_merge_queue(read_client, mutation_client, target)
        except executor.ExecutorError:
            pass
        else:
            raise AssertionError(f"invalid acceptance was accepted: {details}")


def test_200_and_409_never_fabricate_a_fresh_acceptance_receipt() -> None:
    for status in (200, 409):
        read_client = FakeClient(read_responses())
        target = qualified(read_client)
        mutation_client = FakeClient(
            {
                (
                    "PUT",
                    f"/repos/Oteryn/Oteryn-Game/pulls/{PR}/merge-async",
                ): executor.Response(status, {"status": "existing", "details": {}})
            }
        )
        result = executor.submit_merge_queue(read_client, mutation_client, target)
        assert result["result"] == "RECONCILIATION_REQUIRED"
        assert result["request_comment_id"] == REQUEST_COMMENT
        assert result["accepted"] is False
        assert result["receipt"] is None


def test_403_and_404_are_precise_capability_blockers() -> None:
    for status in (403, 404):
        read_client = FakeClient(read_responses())
        target = qualified(read_client)
        mutation_client = FakeClient(
            {
                (
                    "PUT",
                    f"/repos/Oteryn/Oteryn-Game/pulls/{PR}/merge-async",
                ): executor.Response(status, {"message": "unavailable"})
            }
        )
        try:
            executor.submit_merge_queue(read_client, mutation_client, target)
        except executor.ExecutorError as exc:
            assert "BLOCKED_CAPABILITY_UNAVAILABLE" in str(exc)
        else:
            raise AssertionError(f"HTTP {status} was not classified as capability blocker")


def test_invalid_inputs_fail_before_any_target_mutation() -> None:
    for values in (
        ("Other/Repo", PR, HEAD, REQUEST_COMMENT),
        (REPO, 0, HEAD, REQUEST_COMMENT),
        (REPO, PR, "A" * 40, REQUEST_COMMENT),
        (REPO, PR, HEAD, 0),
    ):
        try:
            executor.normalize_inputs(*values)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid input was accepted: {values}")


def test_workflow_is_narrow_read_only_and_has_no_forbidden_merge_fallback() -> None:
    workflow = (
        ROOT / ".github/workflows/governed-merge-queue-executor.yml"
    ).read_text(encoding="utf-8")
    assert "issue_comment:" in workflow
    assert "pull_request:" not in workflow
    assert "CONTROL_ISSUE: '196'" in workflow
    assert "REQUEST_COMMENT_ID: ${{ github.event.comment.id }}" in workflow
    assert "OTERYN_MQ_FINE_GRAINED_PAT: ${{ secrets.OTERYN_MQ_FINE_GRAINED_PAT }}" in workflow
    assert "python3 tools/governance/governed_merge_queue_executor.py" in workflow
    assert "merge_pull_request" not in workflow
    assert "enablePullRequestAutoMerge" not in workflow
    assert "enqueuePullRequest" not in workflow
    assert "GITHUB_TOKEN" not in workflow
    assert "contents: read" in workflow
    assert "issues: read" in workflow
    assert "pull-requests: read" in workflow
    assert '{"OWNER", "MEMBER"}' in workflow
    assert "COLLABORATOR" not in workflow


def main() -> int:
    tests = [
        value
        for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    for test in tests:
        test()
    print(f"{len(tests)} governed Merge Queue executor tests PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
