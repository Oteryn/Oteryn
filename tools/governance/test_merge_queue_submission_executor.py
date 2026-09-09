#!/usr/bin/env python3
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

REPOSITORY = "Oteryn/Oteryn-Platform"
PR_NUMBER = 1378
HEAD = "a" * 40
OTHER_HEAD = "b" * 40
ATTEMPT_ID = "attempt-20260909-0001"
COMMAND = f"{executor.COMMAND_PREFIX} {ATTEMPT_ID} {REPOSITORY} {PR_NUMBER} {HEAD}"


def queue_identity(**kw):
    d = dict(id="MQ_platform_main_001",
             resourcePath=f"/{REPOSITORY}/queue/main",
             url=f"https://github.com/{REPOSITORY}/queue/main")
    d.update(kw)
    return d


def queue_entry(*, include_pull=False, **kw):
    d = dict(id="MQE_platform_001", position=1, state="QUEUED",
             mergeQueue=queue_identity())
    if include_pull:
        d["pullRequest"] = dict(id="PR_node_1378", number=PR_NUMBER,
                                headRefOid=HEAD, baseRefName="main",
                                repository={"nameWithOwner": REPOSITORY})
    d.update(kw)
    return d


def pull(**kw):
    d = dict(state="open", merged=False, draft=False, node_id="PR_node_1378",
             base={"ref": "main"},
             head={"sha": HEAD, "repo": {"full_name": REPOSITORY}})
    d.update(kw)
    return d


def checks(**kw):
    run = dict(id=101, name="platform-gate", head_sha=HEAD, status="completed",
               conclusion="success", app={"id": executor.GITHUB_ACTIONS_APP_ID})
    run.update(kw)
    return {"check_runs": [run]}


class FakeClient:
    def __init__(self, *, permissions=None, pull_response=None, check_response=None,
                 existing_entry=None, mutation_entry=None, mutation_client_id=ATTEMPT_ID,
                 fail_dequeue=False, mutation_error=None,
                 concurrent_entry_on_mutation_error=None):
        self.permissions = permissions or {
            "Oteryn/Oteryn": "admin",
            REPOSITORY: "write",
        }
        self.pull_response = pull_response if pull_response is not None else pull()
        self.check_response = check_response if check_response is not None else checks()
        self.current_entry = existing_entry
        self.current_head = HEAD
        self.mutation_entry = mutation_entry if mutation_entry is not None else queue_entry(include_pull=True)
        self.mutation_client_id = mutation_client_id
        self.fail_dequeue = fail_dequeue
        self.mutation_error = mutation_error
        self.concurrent_entry_on_mutation_error = concurrent_entry_on_mutation_error
        self.rest_calls = []
        self.graphql_calls = []

    def rest(self, method, path):
        self.rest_calls.append((method, path))
        if "/collaborators/" in path and path.endswith("/permission"):
            parts = path.split("/")
            repo = f"{parts[2]}/{parts[3]}"
            return {"permission": self.permissions.get(repo)}
        if "/pulls/" in path:
            return self.pull_response
        if "/check-runs?" in path:
            return self.check_response
        raise AssertionError(path)

    def graphql(self, query, variables):
        self.graphql_calls.append((query, dict(variables)))
        if query == executor.QUEUE_ENTRY_QUERY:
            base = "main"
            if self.current_entry and self.current_entry.get("pullRequest"):
                base = self.current_entry["pullRequest"].get("baseRefName", "main")
            return {"node": {
                "id": "PR_node_1378", "number": PR_NUMBER, "headRefOid": self.current_head,
                "baseRefName": base, "repository": {"nameWithOwner": REPOSITORY},
                "mergeQueueEntry": self.current_entry,
            }}
        if query == executor.ENQUEUE_MUTATION:
            if self.mutation_error is not None:
                if self.concurrent_entry_on_mutation_error is not None:
                    self.current_entry = self.concurrent_entry_on_mutation_error
                    self.current_head = OTHER_HEAD
                raise executor.SubmissionError(self.mutation_error)
            self.current_entry = self.mutation_entry
            return {"enqueuePullRequest": {
                "clientMutationId": self.mutation_client_id,
                "mergeQueueEntry": self.mutation_entry,
            }}
        if query == executor.DEQUEUE_MUTATION:
            if self.fail_dequeue:
                raise executor.SubmissionError("simulated dequeue failure")
            previous = self.current_entry
            self.current_entry = None
            return {"dequeuePullRequest": {
                "clientMutationId": variables["clientMutationId"],
                "mergeQueueEntry": previous,
            }}
        raise AssertionError("unexpected GraphQL query")


def request():
    return executor.parse_command(COMMAND)


def assert_error(fn, marker):
    try:
        fn()
    except executor.SubmissionError as exc:
        assert marker in str(exc), (marker, str(exc))
    else:
        raise AssertionError(f"expected error containing {marker!r}")


def test_exact_target_authorization_is_comment_bound():
    client = FakeClient()
    auth = executor.authorize_target_submission(
        client, request(), actor="blakinio", actual_control_issue=190,
        control_comment_id=12345, control_owner_actor="blakinio")
    assert auth.repository == REPOSITORY
    assert auth.pr_number == PR_NUMBER
    assert auth.expected_head_sha == HEAD
    assert auth.control_comment_id == 12345
    assert auth.permission == "write"
    assert executor._authorization_matches_request(auth, request())

    moved = request().__class__(request().attempt_id, request().repository,
                                request().repository_name, request().pr_number,
                                OTHER_HEAD, request().required_gate)
    assert not executor._authorization_matches_request(auth, moved)


def test_meta_control_plane_requires_owner_admin_decision():
    meta_request = executor.parse_command(
        f"{executor.COMMAND_PREFIX} {ATTEMPT_ID} Oteryn/Oteryn 188 {HEAD}"
    )
    client = FakeClient(permissions={"Oteryn/Oteryn": "admin"})
    auth = executor.authorize_target_submission(
        client, meta_request, actor="blakinio", actual_control_issue=190,
        control_comment_id=99, control_owner_actor="blakinio")
    assert auth.owner_decision is True

    assert_error(lambda: executor.authorize_target_submission(
        FakeClient(permissions={"Oteryn/Oteryn": "write"}), meta_request,
        actor="blakinio", actual_control_issue=190, control_comment_id=99,
        control_owner_actor="blakinio"), "requires the control endpoint owner")
    assert_error(lambda: executor.authorize_target_submission(
        client, meta_request, actor="other", actual_control_issue=190,
        control_comment_id=99, control_owner_actor="blakinio"),
        "requires the control endpoint owner")


def test_qualification_is_exact_head_main_and_gate():
    client = FakeClient()
    q = executor.qualify_pull_request(client, request())
    assert q.head_sha == HEAD and q.base_ref == "main"
    for candidate, marker in (
        (pull(base={"ref": "release"}), "base must be exactly main"),
        (pull(draft=True), "non-draft"),
        (pull(head={"sha": OTHER_HEAD, "repo": {"full_name": REPOSITORY}}), "head changed"),
    ):
        assert_error(lambda candidate=candidate: executor.qualify_pull_request(
            FakeClient(pull_response=candidate), request()), marker)


def test_enqueue_success_requires_fresh_same_entry_readback():
    client = FakeClient()
    q = executor.qualify_pull_request(client, request())
    status, entry = executor.enqueue_pull_request(client, request(), q)
    assert status == "ENQUEUED"
    assert entry["id"] == "MQE_platform_001"
    assert any(qry == executor.ENQUEUE_MUTATION for qry, _ in client.graphql_calls)
    assert not any(qry == executor.DEQUEUE_MUTATION for qry, _ in client.graphql_calls)


def test_base_or_queue_race_is_reconciled_by_dequeue():
    bad = queue_entry(include_pull=True)
    bad["pullRequest"] = {**bad["pullRequest"], "baseRefName": "release"}
    bad["mergeQueue"] = {
        "id": "MQ_release_001",
        "resourcePath": f"/{REPOSITORY}/queue/release",
        "url": f"https://github.com/{REPOSITORY}/queue/release",
    }
    client = FakeClient(mutation_entry=bad)
    q = executor.qualify_pull_request(client, request())
    assert_error(lambda: executor.enqueue_pull_request(client, request(), q),
                 "reconciled/dequeued")
    assert client.current_entry is None
    assert any(qry == executor.DEQUEUE_MUTATION for qry, _ in client.graphql_calls)


def test_failed_enqueue_preserves_concurrent_new_head_entry():
    concurrent = queue_entry(include_pull=True, id="MQE_new_head_002")
    concurrent["pullRequest"] = {
        **concurrent["pullRequest"],
        "headRefOid": OTHER_HEAD,
    }
    client = FakeClient(
        mutation_error="expectedHeadOid mismatch after concurrent push",
        concurrent_entry_on_mutation_error=concurrent,
    )
    q = executor.qualify_pull_request(client, request())
    assert_error(lambda: executor.enqueue_pull_request(client, request(), q),
                 "concurrent entries were left untouched")
    assert client.current_entry is concurrent
    assert client.current_head == OTHER_HEAD
    assert not any(qry == executor.DEQUEUE_MUTATION for qry, _ in client.graphql_calls)


def test_failed_reconciliation_is_material_failure():
    bad = queue_entry(include_pull=True)
    bad["pullRequest"] = {**bad["pullRequest"], "baseRefName": "release"}
    client = FakeClient(mutation_entry=bad, fail_dequeue=True)
    q = executor.qualify_pull_request(client, request())
    assert_error(lambda: executor.enqueue_pull_request(client, request(), q),
                 "reconciliation failed")


def test_receipt_preserves_authorization_and_queue_identity():
    client = FakeClient()
    auth = executor.authorize_target_submission(
        client, request(), actor="blakinio", actual_control_issue=190,
        control_comment_id=12345, control_owner_actor="blakinio")
    result = executor.receipt(request(), auth, status="ENQUEUED", entry=queue_entry())
    assert result["authorization_comment_id"] == 12345
    assert result["authorization_actor"] == "blakinio"
    assert result["merge_queue_id"] == "MQ_platform_main_001"
    assert result["merge_queue_resource_path"] == f"/{REPOSITORY}/queue/main"


def test_no_direct_merge_or_generic_auto_merge_operation():
    text = MODULE_PATH.read_text(encoding="utf-8")
    assert "enqueuePullRequest" in text
    assert "expectedHeadOid" in text
    assert "dequeuePullRequest" in text
    for forbidden in ("enablePullRequestAutoMerge", "mergePullRequest(input",
                      "/merge-async", "direct_merge"):
        assert forbidden not in text, forbidden


def test_workflow_binds_exact_comment_and_target_authorization():
    workflow = (Path(__file__).resolve().parents[2] / ".github/workflows/merge-queue-submission.yml")
    if not workflow.exists():
        return
    text = workflow.read_text(encoding="utf-8")
    for marker in (
        "github.event.issue.number == 190",
        "github.event.comment.id",
        "github.event.issue.user.login",
        "--control-comment-id",
        "--control-owner",
        "permission-checks: read",
        "permission-pull-requests: read",
        "permission-merge-queues: write",
        "authorization comment",
        "queue id",
    ):
        assert marker in text, marker
    for forbidden in (
        "enablePullRequestAutoMerge",
        "merge_pull_request",
        "direct_merge",
        "workflow_dispatch:",
        "contents: write",
        "pull-requests: write",
    ):
        assert forbidden not in text, forbidden


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for t in tests:
        t()
    print(f"PASS {len(tests)} protected Merge Queue executor regressions")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())