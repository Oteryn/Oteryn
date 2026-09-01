#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import base64
import os
import tempfile
import urllib.error
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("audit_github_readonly.py")
SPEC = importlib.util.spec_from_file_location("audit_github_readonly", MODULE_PATH)
assert SPEC and SPEC.loader
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)

ACTIONS_APP_ID = 15368


class FakeAudit(m.Audit):
    def __init__(self, responses: dict[str, object]) -> None:
        super().__init__("test")
        self.responses = responses
        self.calls: list[str] = []

    def api(self, path: str, *, allow_404: bool = False):
        self.calls.append(path)
        if path in self.responses:
            response = self.responses[path]
            if isinstance(response, BaseException):
                raise response
            return response
        if "?per_page=100&page=" in path:
            base, page = path.rsplit("?per_page=100&page=", 1)
            if page == "1" and base in self.responses:
                return self.responses[base]
            return []
        if path.startswith("/repos/Oteryn/Test/actions/workflows/"):
            return {"id": 1, "state": "active", "path": ".github/workflows/gate.yml"}
        if path.startswith("/repos/Oteryn/Test/contents/.github/workflows/gate.yml"):
            return {"content": base64.b64encode(b"on: [pull_request, pull_request_target]\n").decode("ascii")}
        if allow_404:
            return None
        raise AssertionError(f"unexpected API call: {path}")

    def graphql(self, query: str, variables: dict):
        owner = variables["owner"]
        name = variables["name"]
        number = variables["number"]
        cursor = variables.get("after") or "first"
        path = f"/graphql/repos/{owner}/{name}/pulls/{number}/queue-timeline/{cursor}"
        self.calls.append(path)
        if path not in self.responses:
            return {"repository": {"pullRequest": None}}
        response = self.responses[path]
        if isinstance(response, BaseException):
            raise response
        return response


def check_run(name: str, run_id: int, pr_number: int, *, head_sha: str | None = None) -> dict:
    value = {
        "name": name,
        "app": {"id": ACTIONS_APP_ID},
        "details_url": f"https://github.com/Oteryn/Test/actions/runs/{run_id}/job/{run_id + 1000}",
        "pull_requests": [{"number": pr_number}],
    }
    if head_sha is not None:
        value["head_sha"] = head_sha
    return value


def target_run(main: str, head: str, *, pr_number: int = 7) -> dict:
    repository = {
        "id": 1,
        "name": "Test",
        "url": "https://api.github.com/repos/Oteryn/Test",
    }
    return {
        "event": "pull_request_target",
        "head_sha": head,
        "workflow_id": 1,
        "pull_requests": [{
            "number": pr_number,
            "base": {"ref": "main", "sha": main, "repo": repository},
            "head": {"sha": head, "repo": repository},
        }],
    }


def v2_wanted(repo: str = "Oteryn/Oteryn") -> dict:
    desired = json.loads(m.DESIRED_PATH.read_text(encoding="utf-8"))
    return next(item for item in desired["permanent_repositories"] if item["repository"] == repo)


def lifecycle_comment(
    comment_id: int,
    body: dict,
    *,
    created_at: str = "2026-08-31T10:00:00Z",
    updated_at: str | None = None,
    in_reply_to_id: int | None = None,
) -> dict:
    comment = {
        "id": comment_id,
        "body": json.dumps(body),
        "created_at": created_at,
        "updated_at": created_at if updated_at is None else updated_at,
    }
    if in_reply_to_id is not None:
        comment["in_reply_to_id"] = in_reply_to_id
    return comment


def control_plane_owner_authorization_comment(
    comment_id: int,
    *,
    repository: str,
    pull_request: int,
    material_head_sha: str,
    scope: str,
    login: str = "blakinio",
    actor_type: str = "User",
    created_at: str = "2026-08-31T12:00:00Z",
    updated_at: str | None = None,
) -> dict:
    return {
        "id": comment_id,
        "body": json.dumps({
            "record_type": "CONTROL_PLANE_R2_OWNER_AUTHORIZATION",
            "repository": repository,
            "pull_request": pull_request,
            "material_head_sha": material_head_sha,
            "scope": scope,
            "authorize_integration": True,
        }),
        "created_at": created_at,
        "updated_at": created_at if updated_at is None else updated_at,
        "user": {"login": login, "type": actor_type},
    }


def current_pull_request(repository: str, pull_request: int, head_sha: str) -> dict:
    return {
        "number": pull_request,
        "state": "open",
        "draft": False,
        "head": {"sha": head_sha, "repo": {"full_name": repository}},
        "base": {"ref": "main", "repo": {"full_name": repository}},
    }


def pending_baseline(wanted: dict) -> dict:
    baseline = json.loads(json.dumps(m.core.target_rollout_state(wanted)))
    baseline["required_checks"] = ["legacy-gate"]
    baseline["required_check_sources"] = {"legacy-gate": [ACTIONS_APP_ID]}
    baseline["merge_queue"] = False
    baseline["protection"]["strict_required_status_checks"] = True
    return baseline


def pending_record(wanted: dict, baseline: dict) -> dict:
    return {
        "record_type": "PENDING_BASELINE",
        "repository": wanted["repository"],
        "captured_at": "2026-08-31T09:59:00Z",
        "pre_state_fingerprint": m.core.rollout_state_fingerprint(baseline),
        "pre_state_readback": baseline,
    }


def moving_base_receipt(wanted: dict) -> dict:
    gate = wanted["required_checks"][0]
    return {
        "repository": wanted["repository"],
        "pr_a": 124,
        "a_head": "a" * 40,
        "main_before_b": "b" * 40,
        "pr_b": 125,
        "main_after_b": "c" * 40,
        "base_sha": "c" * 40,
        "a_head_unchanged": "a" * 40,
        "merge_group_sha": "d" * 40,
        "aggregate_gate_run": {
            "context": gate,
            "head_sha": "d" * 40,
            "conclusion": "success",
            "run_id": 77,
        },
        "main_after_a": "e" * 40,
    }


def transition_record(
    wanted: dict,
    baseline: dict,
    *,
    transition_id: str = "meta-v2-cutover-1",
    expires_at: str = "2026-08-31T12:00:00Z",
) -> dict:
    return {
        "record_type": "PRE_TRANSITION",
        "transition_id": transition_id,
        "repository": wanted["repository"],
        "issue_or_pr": "Oteryn/Oteryn#102",
        "expires_at": expires_at,
        "pre_state_fingerprint": m.core.rollout_state_fingerprint(baseline),
        "allowed_deviations": [
            "required_checks",
            "required_check_sources",
            "merge_queue",
            "protection.strict_required_status_checks",
        ],
        "success_condition": {"moving_base_canary": "required"},
        "rollback_condition": {"restore_pre_state": True},
    }


def terminal_record(
    wanted: dict,
    post_state: dict,
    *,
    terminal_status: str,
    transition_id: str = "meta-v2-cutover-1",
    pre_transition_comment_id: int = 2,
) -> dict:
    record = {
        "record_type": "TERMINAL",
        "transition_id": transition_id,
        "pre_transition_comment_id": pre_transition_comment_id,
        "terminal_status": terminal_status,
        "post_state_fingerprint": m.core.rollout_state_fingerprint(post_state),
        "post_state_readback": post_state,
    }
    if terminal_status == "SUCCESS":
        record["moving_base_receipt"] = moving_base_receipt(wanted)
    return record


def direct_moving_base_responses(wanted: dict, receipt: dict) -> dict[str, object]:
    """The direct REST evidence a valid terminal SUCCESS must bind to."""
    repo = wanted["repository"]
    gate = receipt["aggregate_gate_run"]
    gate_name = wanted["required_checks"][0]
    app_id = wanted["required_check_app_id"]
    pr_a = receipt["pr_a"]
    pr_b = receipt["pr_b"]
    return {
        f"/repos/{repo}/pulls/{pr_a}": {
            "number": pr_a,
            "base": {"ref": "main", "repo": {"full_name": repo}},
            "head": {"sha": receipt["a_head"]},
            "merged": True,
            "merged_at": "2026-08-31T11:00:00Z",
            "merge_commit_sha": receipt["main_after_a"],
        },
        f"/repos/{repo}/pulls/{pr_b}": {
            "number": pr_b,
            "base": {"ref": "main", "repo": {"full_name": repo}},
            "head": {"sha": "f" * 40},
            "merged": True,
            "merged_at": "2026-08-31T10:30:00Z",
            "merge_commit_sha": receipt["main_after_b"],
        },
        f"/graphql/repos/{repo}/pulls/{pr_a}/queue-timeline/first": {
            "repository": {
                "pullRequest": {
                    "timelineItems": {
                        "nodes": [
                            {
                                "__typename": "AddedToMergeQueueEvent",
                                "createdAt": "2026-08-31T10:35:00Z",
                            },
                            {
                                "__typename": "MergedEvent",
                                "createdAt": "2026-08-31T11:00:00Z",
                                "commit": {"oid": receipt["main_after_a"]},
                            },
                            {
                                "__typename": "RemovedFromMergeQueueEvent",
                                "createdAt": "2026-08-31T11:00:01Z",
                                "beforeCommit": {"oid": receipt["main_after_a"]},
                            },
                        ],
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                    },
                },
            },
        },
        f"/repos/{repo}/commits/{receipt['a_head']}/check-runs?per_page=100": {
            "check_runs": [{
                "name": gate_name,
                "app": {"id": app_id},
                "head_sha": receipt["a_head"],
                "conclusion": "success",
                "completed_at": "2026-08-31T10:10:00Z",
                "details_url": f"https://github.com/Oteryn/Oteryn/actions/runs/76/job/100",
                "pull_requests": [{"number": pr_a}],
            }],
        },
        f"/repos/{repo}/actions/runs/76": {
            "id": 76,
            "event": "pull_request",
            "head_sha": receipt["a_head"],
            "workflow_id": 1,
        },
        f"/repos/{repo}/actions/workflows/1": {
            "id": 1,
            "state": "active",
            "path": ".github/workflows/gate.yml",
        },
        f"/repos/{repo}/contents/.github/workflows/gate.yml?ref={receipt['a_head']}": {
            "content": base64.b64encode(b"on: [pull_request, pull_request_target]\n").decode("ascii"),
        },
        f"/repos/{repo}/contents/.github/workflows/gate.yml?ref={receipt['main_before_b']}": {
            "content": base64.b64encode(b"on: [pull_request, pull_request_target]\n").decode("ascii"),
        },
        f"/repos/{repo}/contents/.github/workflows/gate.yml?ref={receipt['base_sha']}": {
            "content": base64.b64encode(
                b"on: [pull_request, pull_request_target, merge_group]\n"
            ).decode("ascii"),
        },
        f"/repos/{repo}/contents/.github/workflows/gate.yml?ref={receipt['main_after_a']}": {
            "content": base64.b64encode(
                b"on: [pull_request, pull_request_target, merge_group]\n"
            ).decode("ascii"),
        },
        f"/repos/{repo}/commits/{receipt['main_after_b']}": {
            "sha": receipt["main_after_b"],
            "parents": [{"sha": receipt["main_before_b"]}],
        },
        f"/repos/{repo}/commits/{receipt['main_after_a']}": {
            "sha": receipt["main_after_a"],
            "parents": [{"sha": receipt["main_after_b"]}],
            "committer": {"login": "github-merge-queue[bot]"},
        },
        f"/repos/{repo}/compare/{receipt['main_before_b']}...{receipt['main_after_b']}": {
            "status": "ahead",
        },
        f"/repos/{repo}/actions/runs/{gate['run_id']}": {
            "id": gate["run_id"],
            "event": "merge_group",
            "head_sha": receipt["merge_group_sha"],
            "status": "completed",
            "conclusion": "success",
            "run_started_at": "2026-08-31T10:40:00Z",
            "workflow_id": 1,
        },
        f"/repos/{repo}/commits/{receipt['merge_group_sha']}": {
            "sha": receipt["merge_group_sha"],
            "parents": [
                {"sha": receipt["main_after_b"]},
                {"sha": receipt["a_head"]},
            ],
        },
        f"/repos/{repo}/commits/{receipt['merge_group_sha']}/check-runs?per_page=100": {
            "check_runs": [{
                "name": gate_name,
                "app": {"id": app_id},
                "head_sha": receipt["merge_group_sha"],
                "conclusion": "success",
                "completed_at": "2026-08-31T10:50:00Z",
                "details_url": f"https://github.com/Oteryn/Oteryn/actions/runs/{gate['run_id']}/job/100",
            }],
        },
        f"/repos/{repo}/branches/main": {
            "protected": True,
            "commit": {"sha": receipt["main_after_a"]},
        },
        f"/repos/{repo}/compare/{receipt['main_after_a']}...{receipt['main_after_a']}": {
            "status": "identical",
        },
    }


def test_pending_requires_one_unedited_matching_direct_readback_baseline() -> None:
    wanted = v2_wanted()
    baseline = pending_baseline(wanted)
    records = [lifecycle_comment(1, pending_record(wanted, baseline))]
    assert m.core.classify_rollout_state(
        wanted, baseline, records, now="2026-08-31T10:30:00Z"
    ) == "PENDING"

    changed = json.loads(json.dumps(baseline))
    changed["required_checks"] = ["legacy-gate", "unrecorded-gate"]
    changed["required_check_sources"]["unrecorded-gate"] = [ACTIONS_APP_ID]
    assert m.core.classify_rollout_state(
        wanted, changed, records, now="2026-08-31T10:30:00Z"
    ) == "DRIFT"

    rebound = json.loads(json.dumps(baseline))
    rebound["required_check_sources"]["legacy-gate"] = [999]
    assert m.core.classify_rollout_state(
        wanted, rebound, records, now="2026-08-31T10:30:00Z"
    ) == "DRIFT"

    edited = [lifecycle_comment(1, pending_record(wanted, baseline), updated_at="2026-08-31T10:01:00Z")]
    assert m.core.classify_rollout_state(
        wanted, baseline, edited, now="2026-08-31T10:30:00Z"
    ) == "DRIFT"
    duplicate = records + [lifecycle_comment(4, pending_record(wanted, baseline))]
    assert m.core.classify_rollout_state(
        wanted, baseline, duplicate, now="2026-08-31T10:30:00Z"
    ) == "DRIFT"
    assert m.core.classify_rollout_state(
        wanted, baseline, [], now="2026-08-31T10:30:00Z"
    ) == "DRIFT"
    assert m.core.classify_rollout_state(
        wanted, baseline, None, now="2026-08-31T10:30:00Z"
    ) == "UNKNOWN"


def test_pending_duplicate_identified_by_readback_repository_is_drift() -> None:
    wanted = v2_wanted()
    baseline = pending_baseline(wanted)
    valid = lifecycle_comment(1, pending_record(wanted, baseline))

    incomplete = pending_record(wanted, baseline)
    del incomplete["repository"]
    duplicate = lifecycle_comment(2, incomplete, created_at="2026-08-31T10:01:00Z")
    assert m.core.classify_rollout_state(
        wanted, baseline, [valid, duplicate], now="2026-08-31T10:30:00Z"
    ) == "DRIFT"

    other = v2_wanted("Oteryn/Oteryn-Game")
    other_baseline = pending_baseline(other)
    foreign = pending_record(other, other_baseline)
    del foreign["repository"]
    assert m.core.classify_rollout_state(
        wanted,
        baseline,
        [valid, lifecycle_comment(3, foreign, created_at="2026-08-31T10:01:00Z")],
        now="2026-08-31T10:30:00Z",
    ) == "PENDING"


def test_pending_baseline_comment_must_predate_first_pre_transition() -> None:
    wanted = v2_wanted()
    baseline = pending_baseline(wanted)
    target = m.core.target_rollout_state(wanted)
    transition = transition_record(wanted, baseline)
    terminal = terminal_record(wanted, target, terminal_status="SUCCESS")

    late_baseline_records = [
        lifecycle_comment(
            1,
            pending_record(wanted, baseline),
            created_at="2026-08-31T11:05:00Z",
        ),
        lifecycle_comment(2, transition, created_at="2026-08-31T10:05:00Z"),
        lifecycle_comment(3, terminal, created_at="2026-08-31T11:00:00Z"),
    ]
    assert m.core.classify_rollout_state(
        wanted,
        target,
        late_baseline_records,
        now="2026-08-31T13:00:00Z",
        success_receipt_verifier=lambda *_: "SUCCESS",
    ) == "DRIFT"

    valid_records = [
        lifecycle_comment(
            1,
            pending_record(wanted, baseline),
            created_at="2026-08-31T10:00:00Z",
        ),
        lifecycle_comment(2, transition, created_at="2026-08-31T10:05:00Z"),
        lifecycle_comment(3, terminal, created_at="2026-08-31T11:00:00Z"),
    ]
    assert m.core.classify_rollout_state(
        wanted,
        target,
        valid_records,
        now="2026-08-31T13:00:00Z",
        success_receipt_verifier=lambda *_: "SUCCESS",
    ) == "SUCCESS"


def test_auditor_reads_canonical_top_level_lifecycle_comments_before_classification() -> None:
    wanted = v2_wanted()
    baseline = pending_baseline(wanted)
    audit = FakeAudit({
        "/repos/Oteryn/Oteryn/issues/102/comments": [
            lifecycle_comment(1, pending_record(wanted, baseline)),
        ],
    })
    assert audit.classify_rollout_readback(
        wanted, baseline, now="2026-08-31T10:30:00Z"
    ) == "PENDING"
    assert "/repos/Oteryn/Oteryn/issues/102/comments?per_page=100&page=1" in audit.calls


def test_lifecycle_records_for_another_provider_do_not_drift_this_provider() -> None:
    wanted = v2_wanted()
    baseline = pending_baseline(wanted)
    other_wanted = v2_wanted("Oteryn/Oteryn-Game")
    other_baseline = pending_baseline(other_wanted)
    records = [
        lifecycle_comment(1, pending_record(wanted, baseline)),
        lifecycle_comment(10, pending_record(other_wanted, other_baseline)),
        lifecycle_comment(11, transition_record(other_wanted, other_baseline), created_at="2026-08-31T10:05:00Z"),
        lifecycle_comment(
            12,
            terminal_record(
                other_wanted,
                m.core.target_rollout_state(other_wanted),
                terminal_status="SUCCESS",
                pre_transition_comment_id=11,
            ),
            created_at="2026-08-31T11:00:00Z",
        ),
    ]
    assert m.core.classify_rollout_state(
        wanted, baseline, records, now="2026-08-31T13:00:00Z"
    ) == "PENDING"


def test_malformed_lifecycle_evidence_is_scoped_to_its_repository() -> None:
    wanted = v2_wanted()
    baseline = pending_baseline(wanted)
    other_wanted = v2_wanted("Oteryn/Oteryn-Game")
    other_baseline = pending_baseline(other_wanted)
    meta_pending = lifecycle_comment(1, pending_record(wanted, baseline))
    edited_game = lifecycle_comment(
        10,
        pending_record(other_wanted, other_baseline),
        updated_at="2026-08-31T10:01:00Z",
    )
    assert m.core.classify_rollout_state(
        wanted, baseline, [meta_pending, edited_game], now="2026-08-31T10:30:00Z"
    ) == "PENDING"

    edited_meta = lifecycle_comment(
        11,
        pending_record(wanted, baseline),
        updated_at="2026-08-31T10:01:00Z",
    )
    assert m.core.classify_rollout_state(
        wanted, baseline, [meta_pending, edited_meta], now="2026-08-31T10:30:00Z"
    ) == "DRIFT"

    meta_transition = lifecycle_comment(
        12, transition_record(wanted, baseline), created_at="2026-08-31T10:05:00Z"
    )
    malformed_linked_meta = lifecycle_comment(
        13,
        {
            "record_type": "NOT_A_LIFECYCLE_RECORD",
            "transition_id": "meta-v2-cutover-1",
            "pre_transition_comment_id": 12,
        },
        created_at="2026-08-31T10:10:00Z",
    )
    assert m.core.classify_rollout_state(
        wanted,
        baseline,
        [meta_pending, meta_transition, malformed_linked_meta],
        now="2026-08-31T10:30:00Z",
    ) == "DRIFT"


def test_terminal_lifecycle_is_scoped_by_exact_pre_transition_comment_link() -> None:
    wanted = v2_wanted("Oteryn/Oteryn-Game")
    baseline = pending_baseline(wanted)
    other_wanted = v2_wanted()
    other_baseline = pending_baseline(other_wanted)
    shared_transition_id = "shared-cutover"
    meta_pre = transition_record(wanted, baseline, transition_id=shared_transition_id)
    game_pre = transition_record(other_wanted, other_baseline, transition_id=shared_transition_id)
    common_records = [
        lifecycle_comment(1, pending_record(wanted, baseline)),
        lifecycle_comment(10, pending_record(other_wanted, other_baseline)),
        lifecycle_comment(2, meta_pre, created_at="2026-08-31T10:05:00Z"),
        lifecycle_comment(20, game_pre, created_at="2026-08-31T09:00:00Z"),
    ]

    def classify(records: list[dict]) -> str:
        return m.core.classify_rollout_state(
            wanted, baseline, records, now="2026-08-31T11:00:00Z"
        )

    game_terminal = terminal_record(
        other_wanted,
        m.core.target_rollout_state(other_wanted),
        terminal_status="SUCCESS",
        transition_id=shared_transition_id,
        pre_transition_comment_id=20,
    )
    assert classify(common_records + [
        lifecycle_comment(21, game_terminal, created_at="2026-08-31T09:30:00Z"),
    ]) == "TRANSITION"

    assert classify(common_records + [
        lifecycle_comment(
            22, game_terminal, created_at="2026-08-31T09:30:00Z", updated_at="2026-08-31T09:31:00Z",
        ),
    ]) == "DRIFT"

    terminal_shaped_game_record = {
        "record_type": "NOT_A_LIFECYCLE_RECORD",
        "repository": wanted["repository"],
        "transition_id": shared_transition_id,
        "pre_transition_comment_id": 20,
        "terminal_status": "SUCCESS",
    }
    assert classify(common_records + [
        lifecycle_comment(221, terminal_shaped_game_record, created_at="2026-08-31T09:30:00Z"),
    ]) == "DRIFT"

    unlinked_terminal = terminal_record(
        wanted,
        baseline,
        terminal_status="ROLLED_BACK",
        transition_id=shared_transition_id,
        pre_transition_comment_id=999,
    )
    assert classify(common_records + [
        lifecycle_comment(23, unlinked_terminal, created_at="2026-08-31T10:30:00Z"),
    ]) == "DRIFT"

    malformed_meta_terminal = terminal_record(
        wanted,
        baseline,
        terminal_status="ROLLED_BACK",
        transition_id=shared_transition_id,
        pre_transition_comment_id=2,
    )
    assert classify(common_records + [
        lifecycle_comment(
            24,
            malformed_meta_terminal,
            created_at="2026-08-31T10:30:00Z",
            updated_at="2026-08-31T10:31:00Z",
        ),
    ]) == "DRIFT"

    edited_mislinked_meta_terminal = terminal_record(
        wanted,
        baseline,
        terminal_status="ROLLED_BACK",
        transition_id=shared_transition_id,
        pre_transition_comment_id=999,
    )
    assert classify(common_records + [
        lifecycle_comment(
            25,
            edited_mislinked_meta_terminal,
            created_at="2026-08-31T10:30:00Z",
            updated_at="2026-08-31T10:31:00Z",
        ),
    ]) == "DRIFT"


def test_closed_rollout_transitions_must_not_overlap() -> None:
    wanted = v2_wanted()
    baseline = pending_baseline(wanted)
    target = m.core.target_rollout_state(wanted)
    first = transition_record(wanted, baseline, transition_id="meta-v2-cutover-1")
    second = transition_record(wanted, baseline, transition_id="meta-v2-cutover-2")
    records = [
        lifecycle_comment(1, pending_record(wanted, baseline)),
        lifecycle_comment(2, first, created_at="2026-08-31T10:05:00Z"),
        lifecycle_comment(3, second, created_at="2026-08-31T10:10:00Z"),
        lifecycle_comment(
            4,
            terminal_record(
                wanted,
                baseline,
                terminal_status="ROLLED_BACK",
                transition_id="meta-v2-cutover-1",
                pre_transition_comment_id=2,
            ),
            created_at="2026-08-31T10:30:00Z",
        ),
        lifecycle_comment(
            5,
            terminal_record(
                wanted,
                target,
                terminal_status="SUCCESS",
                transition_id="meta-v2-cutover-2",
                pre_transition_comment_id=3,
            ),
            created_at="2026-08-31T11:00:00Z",
        ),
    ]
    assert m.core.classify_rollout_state(
        wanted,
        target,
        records,
        now="2026-08-31T13:00:00Z",
        success_receipt_verifier=lambda _wanted, _pre, _terminal: "SUCCESS",
    ) == "DRIFT"


def test_malformed_json_lifecycle_evidence_for_current_repository_is_drift() -> None:
    wanted = v2_wanted()
    baseline = pending_baseline(wanted)
    target = m.core.target_rollout_state(wanted)
    transition = transition_record(wanted, baseline)
    records = [
        lifecycle_comment(1, pending_record(wanted, baseline)),
        lifecycle_comment(2, transition, created_at="2026-08-31T10:05:00Z"),
        lifecycle_comment(
            3,
            terminal_record(wanted, target, terminal_status="SUCCESS"),
            created_at="2026-08-31T11:00:00Z",
        ),
        {
            "id": 4,
            "body": (
                '{"record_type":"TERMINAL","repository":"Oteryn/Oteryn",'
                '"transition_id":"meta-v2-cutover-1","pre_transition_comment_id":2'
            ),
            "created_at": "2026-08-31T11:01:00Z",
            "updated_at": "2026-08-31T11:01:00Z",
        },
    ]
    assert m.core.classify_rollout_state(
        wanted,
        target,
        records,
        now="2026-08-31T13:00:00Z",
        success_receipt_verifier=lambda _wanted, _pre, _terminal: "SUCCESS",
    ) == "DRIFT"


def test_schema_invalid_terminal_for_current_repository_cannot_be_ignored() -> None:
    wanted = v2_wanted()
    baseline = pending_baseline(wanted)
    target = m.core.target_rollout_state(wanted)
    records = [
        lifecycle_comment(1, pending_record(wanted, baseline)),
        lifecycle_comment(2, transition_record(wanted, baseline), created_at="2026-08-31T10:05:00Z"),
        lifecycle_comment(
            3, terminal_record(wanted, target, terminal_status="SUCCESS"),
            created_at="2026-08-31T11:00:00Z",
        ),
        lifecycle_comment(4, {"record_type": "TERMINAL", "repository": wanted["repository"]}),
    ]
    assert m.core.classify_rollout_state(
        wanted,
        target,
        records,
        now="2026-08-31T13:00:00Z",
        success_receipt_verifier=lambda _wanted, _pre, _terminal: "SUCCESS",
    ) == "DRIFT"


def test_schema_invalid_pre_and_cross_repository_overlap_cannot_reach_success() -> None:
    wanted = v2_wanted()
    other = v2_wanted("Oteryn/Oteryn-Game")
    baseline = pending_baseline(wanted)
    other_baseline = pending_baseline(other)
    target = m.core.target_rollout_state(wanted)
    valid_pre = transition_record(wanted, baseline)
    valid_terminal = terminal_record(wanted, target, terminal_status="SUCCESS")
    incomplete_duplicate = {"record_type": "PRE_TRANSITION", "transition_id": valid_pre["transition_id"]}
    assert m.core.classify_rollout_state(
        wanted, target,
        [lifecycle_comment(1, pending_record(wanted, baseline)), lifecycle_comment(2, valid_pre, created_at="2026-08-31T10:05:00Z"), lifecycle_comment(3, valid_terminal, created_at="2026-08-31T11:00:00Z"), lifecycle_comment(4, incomplete_duplicate)],
        now="2026-08-31T13:00:00Z", success_receipt_verifier=lambda *_: "SUCCESS",
    ) == "DRIFT"

    other_pre = transition_record(other, other_baseline, transition_id="game-v2-cutover-1")
    other_terminal = terminal_record(other, m.core.target_rollout_state(other), terminal_status="SUCCESS", transition_id="game-v2-cutover-1", pre_transition_comment_id=6)
    assert m.core.classify_rollout_state(
        wanted, target,
        [lifecycle_comment(1, pending_record(wanted, baseline)), lifecycle_comment(2, valid_pre, created_at="2026-08-31T10:05:00Z"), lifecycle_comment(5, pending_record(other, other_baseline)), lifecycle_comment(6, other_pre, created_at="2026-08-31T10:10:00Z"), lifecycle_comment(3, valid_terminal, created_at="2026-08-31T11:00:00Z"), lifecycle_comment(7, other_terminal, created_at="2026-08-31T11:10:00Z")],
        now="2026-08-31T13:00:00Z", success_receipt_verifier=lambda *_: "SUCCESS",
    ) == "DRIFT"


def test_cross_repository_overlap_is_drift_while_transition_is_active() -> None:
    wanted = v2_wanted()
    other = v2_wanted("Oteryn/Oteryn-Game")
    baseline = pending_baseline(wanted)
    other_baseline = pending_baseline(other)
    active = json.loads(json.dumps(baseline))
    active["required_checks"] = ["meta-gate"]
    active["required_check_sources"] = {"meta-gate": [ACTIONS_APP_ID]}
    records = [
        lifecycle_comment(1, pending_record(wanted, baseline)),
        lifecycle_comment(
            2,
            transition_record(wanted, baseline),
            created_at="2026-08-31T10:05:00Z",
        ),
        lifecycle_comment(3, pending_record(other, other_baseline)),
        lifecycle_comment(
            4,
            transition_record(
                other,
                other_baseline,
                transition_id="game-v2-cutover-1",
            ),
            created_at="2026-08-31T10:10:00Z",
        ),
    ]

    assert m.core.classify_rollout_state(
        wanted, active, records, now="2026-08-31T11:00:00Z"
    ) == "DRIFT"


def test_cross_repository_overlap_is_drift_after_rollback() -> None:
    wanted = v2_wanted()
    other = v2_wanted("Oteryn/Oteryn-Game")
    baseline = pending_baseline(wanted)
    other_baseline = pending_baseline(other)
    records = [
        lifecycle_comment(1, pending_record(wanted, baseline)),
        lifecycle_comment(
            2,
            transition_record(wanted, baseline),
            created_at="2026-08-31T10:05:00Z",
        ),
        lifecycle_comment(3, pending_record(other, other_baseline)),
        lifecycle_comment(
            4,
            transition_record(
                other,
                other_baseline,
                transition_id="game-v2-cutover-1",
            ),
            created_at="2026-08-31T10:10:00Z",
        ),
        lifecycle_comment(
            5,
            terminal_record(wanted, baseline, terminal_status="ROLLED_BACK"),
            created_at="2026-08-31T10:30:00Z",
        ),
    ]

    assert m.core.classify_rollout_state(
        wanted, baseline, records, now="2026-08-31T11:00:00Z"
    ) == "DRIFT"


def test_next_provider_requires_prior_provider_success_not_rollback() -> None:
    meta = v2_wanted()
    meta_baseline = pending_baseline(meta)
    game = v2_wanted("Oteryn/Oteryn-Game")
    game_baseline = pending_baseline(game)

    def game_classification(meta_terminal_status: str) -> str:
        meta_post = (
            m.core.target_rollout_state(meta)
            if meta_terminal_status == "SUCCESS"
            else meta_baseline
        )
        records = [
            lifecycle_comment(1, pending_record(meta, meta_baseline)),
            lifecycle_comment(10, pending_record(game, game_baseline)),
            lifecycle_comment(
                2,
                transition_record(meta, meta_baseline),
                created_at="2026-08-31T10:05:00Z",
            ),
            lifecycle_comment(
                3,
                terminal_record(
                    meta,
                    meta_post,
                    terminal_status=meta_terminal_status,
                    pre_transition_comment_id=2,
                ),
                created_at="2026-08-31T10:20:00Z",
            ),
            lifecycle_comment(
                11,
                transition_record(game, game_baseline),
                created_at="2026-08-31T10:30:00Z",
            ),
        ]
        return m.core.classify_rollout_state(
            game, game_baseline, records, now="2026-08-31T10:45:00Z"
        )

    assert game_classification("ROLLED_BACK") == "DRIFT"
    assert game_classification("SUCCESS") == "TRANSITION"


def test_rollout_cannot_start_with_game_before_meta() -> None:
    wanted = v2_wanted("Oteryn/Oteryn-Game")
    baseline = pending_baseline(wanted)
    active = json.loads(json.dumps(baseline))
    active["required_checks"] = ["game-gate"]
    active["required_check_sources"] = {"game-gate": [ACTIONS_APP_ID]}
    records = [
        lifecycle_comment(1, pending_record(wanted, baseline)),
        lifecycle_comment(
            2,
            transition_record(
                wanted,
                baseline,
                transition_id="game-v2-cutover-1",
            ),
            created_at="2026-08-31T10:05:00Z",
        ),
    ]

    assert m.core.classify_rollout_state(
        wanted, active, records, now="2026-08-31T11:00:00Z"
    ) == "DRIFT"


def test_active_transition_expires_and_late_terminal_records_stay_drift() -> None:
    wanted = v2_wanted()
    baseline = pending_baseline(wanted)
    transition = transition_record(wanted, baseline)
    active = json.loads(json.dumps(baseline))
    active["required_checks"] = ["meta-gate"]
    active["required_check_sources"] = {"meta-gate": [ACTIONS_APP_ID]}
    records = [
        lifecycle_comment(1, pending_record(wanted, baseline)),
        lifecycle_comment(2, transition, created_at="2026-08-31T10:05:00Z"),
    ]
    assert m.core.classify_rollout_state(
        wanted, active, records, now="2026-08-31T11:00:00Z"
    ) == "TRANSITION"
    assert m.core.classify_rollout_state(
        wanted, active, records, now="2026-08-31T12:01:00Z"
    ) == "DRIFT"

    late_rollback = terminal_record(wanted, baseline, terminal_status="ROLLED_BACK")
    records.append(lifecycle_comment(3, late_rollback, created_at="2026-08-31T12:01:00Z"))
    assert m.core.classify_rollout_state(
        wanted, baseline, records, now="2026-08-31T12:02:00Z"
    ) == "DRIFT"


def test_transition_records_must_be_unique_unedited_and_top_level() -> None:
    wanted = v2_wanted()
    baseline = pending_baseline(wanted)
    active = json.loads(json.dumps(baseline))
    active["required_checks"] = ["meta-gate"]
    active["required_check_sources"] = {"meta-gate": [ACTIONS_APP_ID]}
    transition = transition_record(wanted, baseline)
    pending = lifecycle_comment(1, pending_record(wanted, baseline))
    valid = lifecycle_comment(2, transition, created_at="2026-08-31T10:05:00Z")
    assert m.core.classify_rollout_state(
        wanted, active, [pending, valid], now="2026-08-31T11:00:00Z"
    ) == "TRANSITION"

    edited = lifecycle_comment(
        2,
        transition,
        created_at="2026-08-31T10:05:00Z",
        updated_at="2026-08-31T10:06:00Z",
    )
    assert m.core.classify_rollout_state(
        wanted, active, [pending, edited], now="2026-08-31T11:00:00Z"
    ) == "DRIFT"
    nested = lifecycle_comment(
        2,
        transition,
        created_at="2026-08-31T10:05:00Z",
        in_reply_to_id=99,
    )
    assert m.core.classify_rollout_state(
        wanted, active, [pending, nested], now="2026-08-31T11:00:00Z"
    ) == "DRIFT"
    duplicate = lifecycle_comment(4, transition, created_at="2026-08-31T10:06:00Z")
    assert m.core.classify_rollout_state(
        wanted, active, [pending, valid, duplicate], now="2026-08-31T11:00:00Z"
    ) == "DRIFT"


def test_terminal_success_requires_complete_moving_base_receipt_and_target_readback() -> None:
    wanted = v2_wanted()
    baseline = pending_baseline(wanted)
    target = m.core.target_rollout_state(wanted)
    transition = transition_record(wanted, baseline)
    terminal = terminal_record(wanted, target, terminal_status="SUCCESS")
    records = [
        lifecycle_comment(1, pending_record(wanted, baseline)),
        lifecycle_comment(2, transition, created_at="2026-08-31T10:05:00Z"),
        lifecycle_comment(3, terminal, created_at="2026-08-31T11:00:00Z"),
    ]
    assert transition["success_condition"] == {"moving_base_canary": "required"}
    assert "moving_base_receipt" not in transition["success_condition"]
    assert m.core.classify_rollout_state(
        wanted, target, records, now="2026-08-31T13:00:00Z"
    ) == "UNKNOWN"

    incomplete = json.loads(json.dumps(terminal))
    del incomplete["moving_base_receipt"]["main_after_a"]
    invalid_records = [records[0], records[1], lifecycle_comment(3, incomplete, created_at="2026-08-31T11:00:00Z")]
    assert m.core.classify_rollout_state(
        wanted, target, invalid_records, now="2026-08-31T13:00:00Z"
    ) == "DRIFT"

    preloaded = json.loads(json.dumps(transition))
    preloaded["success_condition"]["moving_base_receipt"] = moving_base_receipt(wanted)
    assert m.core.classify_rollout_state(
        wanted,
        target,
        [records[0], lifecycle_comment(2, preloaded, created_at="2026-08-31T10:05:00Z"), records[2]],
        now="2026-08-31T13:00:00Z",
    ) == "DRIFT"

    mislinked = terminal_record(
        wanted, target, terminal_status="SUCCESS", pre_transition_comment_id=99
    )
    assert m.core.classify_rollout_state(
        wanted,
        target,
        [records[0], records[1], lifecycle_comment(3, mislinked, created_at="2026-08-31T11:00:00Z")],
        now="2026-08-31T13:00:00Z",
    ) == "DRIFT"

    body_timestamp = terminal_record(wanted, target, terminal_status="SUCCESS")
    body_timestamp["closed_at"] = "2026-08-31T11:00:00Z"
    assert m.core.classify_rollout_state(
        wanted,
        target,
        [records[0], records[1], lifecycle_comment(3, body_timestamp, created_at="2026-08-31T11:00:00Z")],
        now="2026-08-31T13:00:00Z",
    ) == "DRIFT"


def test_auditor_binds_success_to_direct_github_moving_base_evidence() -> None:
    wanted = v2_wanted()
    baseline = pending_baseline(wanted)
    target = m.core.target_rollout_state(wanted)
    transition = transition_record(wanted, baseline)
    terminal = terminal_record(wanted, target, terminal_status="SUCCESS")
    receipt = terminal["moving_base_receipt"]
    comments = [
        lifecycle_comment(1, pending_record(wanted, baseline)),
        lifecycle_comment(2, transition, created_at="2026-08-31T10:05:00Z"),
        lifecycle_comment(3, terminal, created_at="2026-08-31T11:00:00Z"),
    ]
    responses = {
        "/repos/Oteryn/Oteryn/issues/102/comments": comments,
        **direct_moving_base_responses(wanted, receipt),
    }
    audit = FakeAudit(responses)
    assert audit.classify_rollout_readback(
        wanted, target, now="2026-08-31T13:00:00Z"
    ) == "SUCCESS"
    assert f"/repos/{wanted['repository']}/pulls/{receipt['pr_a']}" in audit.calls
    assert f"/repos/{wanted['repository']}/actions/runs/{receipt['aggregate_gate_run']['run_id']}" in audit.calls
    assert f"/repos/{wanted['repository']}/commits/{receipt['main_after_a']}" in audit.calls
    assert f"/repos/{wanted['repository']}/commits/{receipt['merge_group_sha']}" in audit.calls


def test_dequeued_candidate_then_direct_admin_merge_is_drift() -> None:
    wanted = v2_wanted()
    baseline = pending_baseline(wanted)
    target = m.core.target_rollout_state(wanted)
    transition = transition_record(wanted, baseline)
    terminal = terminal_record(wanted, target, terminal_status="SUCCESS")
    receipt = terminal["moving_base_receipt"]
    comments = [
        lifecycle_comment(1, pending_record(wanted, baseline)),
        lifecycle_comment(2, transition, created_at="2026-08-31T10:05:00Z"),
        lifecycle_comment(3, terminal, created_at="2026-08-31T11:00:00Z"),
    ]
    responses = {
        "/repos/Oteryn/Oteryn/issues/102/comments": comments,
        **direct_moving_base_responses(wanted, receipt),
    }
    timeline = responses[
        f"/graphql/repos/{wanted['repository']}/pulls/{receipt['pr_a']}/queue-timeline/first"
    ]["repository"]["pullRequest"]["timelineItems"]["nodes"]
    timeline[1:1] = [{
        "__typename": "RemovedFromMergeQueueEvent",
        "createdAt": "2026-08-31T10:55:00Z",
        "beforeCommit": {"oid": receipt["merge_group_sha"]},
    }]

    assert FakeAudit(responses).classify_rollout_readback(
        wanted, target, now="2026-08-31T13:00:00Z"
    ) == "DRIFT"


def test_moving_base_success_requires_queue_bot_final_integration() -> None:
    """A completed merge-group run cannot substitute for queue integration."""
    wanted = v2_wanted()
    baseline = pending_baseline(wanted)
    target = m.core.target_rollout_state(wanted)
    transition = transition_record(wanted, baseline)
    terminal = terminal_record(wanted, target, terminal_status="SUCCESS")
    receipt = terminal["moving_base_receipt"]
    comments = [
        lifecycle_comment(1, pending_record(wanted, baseline)),
        lifecycle_comment(2, transition, created_at="2026-08-31T10:05:00Z"),
        lifecycle_comment(3, terminal, created_at="2026-08-31T11:00:00Z"),
    ]
    commit_path = f"/repos/{wanted['repository']}/commits/{receipt['main_after_a']}"

    def classification_with(committer: object) -> str:
        responses = {
            "/repos/Oteryn/Oteryn/issues/102/comments": comments,
            **direct_moving_base_responses(wanted, receipt),
        }
        responses[commit_path]["committer"] = committer
        return FakeAudit(responses).classify_rollout_readback(
            wanted, target, now="2026-08-31T13:00:00Z"
        )

    assert classification_with({"login": "github-merge-queue[bot]"}) == "SUCCESS"
    assert classification_with({"login": "admin"}) == "DRIFT"
    assert classification_with({}) == "DRIFT"
    assert classification_with("malformed") == "DRIFT"


def test_merge_group_success_from_disabled_workflow_is_drift() -> None:
    wanted = v2_wanted()
    baseline = pending_baseline(wanted)
    target = m.core.target_rollout_state(wanted)
    transition = transition_record(wanted, baseline)
    terminal = terminal_record(wanted, target, terminal_status="SUCCESS")
    receipt = terminal["moving_base_receipt"]
    comments = [
        lifecycle_comment(1, pending_record(wanted, baseline)),
        lifecycle_comment(2, transition, created_at="2026-08-31T10:05:00Z"),
        lifecycle_comment(3, terminal, created_at="2026-08-31T11:00:00Z"),
    ]
    responses = {
        "/repos/Oteryn/Oteryn/issues/102/comments": comments,
        **direct_moving_base_responses(wanted, receipt),
        f"/repos/{wanted['repository']}/actions/workflows/2": {
            "id": 2,
            "state": "disabled_manually",
            "path": ".github/workflows/merge-group-gate.yml",
        },
    }
    responses[
        f"/repos/{wanted['repository']}/actions/runs/{receipt['aggregate_gate_run']['run_id']}"
    ]["workflow_id"] = 2

    assert FakeAudit(responses).classify_rollout_readback(
        wanted, target, now="2026-08-31T13:00:00Z"
    ) == "DRIFT"


def test_merge_group_trigger_must_remain_on_current_protected_main() -> None:
    wanted = v2_wanted()
    baseline = pending_baseline(wanted)
    target = m.core.target_rollout_state(wanted)
    transition = transition_record(wanted, baseline)
    terminal = terminal_record(wanted, target, terminal_status="SUCCESS")
    receipt = terminal["moving_base_receipt"]
    comments = [
        lifecycle_comment(1, pending_record(wanted, baseline)),
        lifecycle_comment(2, transition, created_at="2026-08-31T10:05:00Z"),
        lifecycle_comment(3, terminal, created_at="2026-08-31T11:00:00Z"),
    ]
    responses = {
        "/repos/Oteryn/Oteryn/issues/102/comments": comments,
        **direct_moving_base_responses(wanted, receipt),
    }
    responses[
        f"/repos/{wanted['repository']}/contents/.github/workflows/gate.yml"
        f"?ref={receipt['main_after_a']}"
    ] = {
        "content": base64.b64encode(b"on: [pull_request, pull_request_target]\n").decode(
            "ascii"
        ),
    }

    assert FakeAudit(responses).classify_rollout_readback(
        wanted, target, now="2026-08-31T13:00:00Z"
    ) == "DRIFT"


def test_moving_base_canary_events_must_fit_the_current_transition_window() -> None:
    wanted = v2_wanted()
    baseline = pending_baseline(wanted)
    target = m.core.target_rollout_state(wanted)

    def classification_with(pre_created_at: str, terminal_created_at: str) -> str:
        transition = transition_record(wanted, baseline)
        terminal = terminal_record(wanted, target, terminal_status="SUCCESS")
        receipt = terminal["moving_base_receipt"]
        comments = [
            lifecycle_comment(1, pending_record(wanted, baseline)),
            lifecycle_comment(2, transition, created_at=pre_created_at),
            lifecycle_comment(3, terminal, created_at=terminal_created_at),
        ]
        responses = {
            "/repos/Oteryn/Oteryn/issues/102/comments": comments,
            **direct_moving_base_responses(wanted, receipt),
        }
        return FakeAudit(responses).classify_rollout_readback(
            wanted, target, now="2026-08-31T13:00:00Z"
        )

    assert classification_with(
        "2026-08-31T10:05:00Z", "2026-08-31T11:00:00Z"
    ) == "SUCCESS"
    assert classification_with(
        "2026-08-31T10:05:00Z", "2026-08-31T10:55:00Z"
    ) == "DRIFT"
    assert classification_with(
        "2026-08-31T11:05:00Z", "2026-08-31T11:30:00Z"
    ) == "DRIFT"


def test_moving_base_receipt_requires_exact_queue_base_parent() -> None:
    wanted = v2_wanted()
    baseline = pending_baseline(wanted)
    target = m.core.target_rollout_state(wanted)

    def classification_with(parents: list[dict]) -> str:
        transition = transition_record(wanted, baseline)
        terminal = terminal_record(wanted, target, terminal_status="SUCCESS")
        receipt = terminal["moving_base_receipt"]
        comments = [
            lifecycle_comment(1, pending_record(wanted, baseline)),
            lifecycle_comment(2, transition, created_at="2026-08-31T10:05:00Z"),
            lifecycle_comment(3, terminal, created_at="2026-08-31T11:00:00Z"),
        ]
        responses = {
            "/repos/Oteryn/Oteryn/issues/102/comments": comments,
            **direct_moving_base_responses(wanted, receipt),
        }
        responses[f"/repos/{wanted['repository']}/commits/{receipt['merge_group_sha']}"]["parents"] = parents
        return FakeAudit(responses).classify_rollout_readback(
            wanted, target, now="2026-08-31T13:00:00Z"
        )

    receipt = moving_base_receipt(wanted)
    assert classification_with([
        {"sha": receipt["base_sha"]},
        {"sha": receipt["a_head"]},
    ]) == "SUCCESS"
    assert classification_with([
        {"sha": receipt["a_head"]},
        {"sha": receipt["base_sha"]},
    ]) == "DRIFT"

    wrong_base = transition_record(wanted, baseline)
    wrong_base_terminal = terminal_record(wanted, target, terminal_status="SUCCESS")
    wrong_base_terminal["moving_base_receipt"]["base_sha"] = "f" * 40
    wrong_base_records = [
        lifecycle_comment(1, pending_record(wanted, baseline)),
        lifecycle_comment(2, wrong_base, created_at="2026-08-31T10:05:00Z"),
        lifecycle_comment(3, wrong_base_terminal, created_at="2026-08-31T11:00:00Z"),
    ]
    assert m.core.classify_rollout_state(
        wanted, target, wrong_base_records, now="2026-08-31T13:00:00Z"
    ) == "DRIFT"


def test_auditor_rejects_each_forged_or_mismatched_success_receipt_binding() -> None:
    wanted = v2_wanted()
    baseline = pending_baseline(wanted)
    target = m.core.target_rollout_state(wanted)
    transition = transition_record(wanted, baseline)
    terminal = terminal_record(wanted, target, terminal_status="SUCCESS")
    receipt = terminal["moving_base_receipt"]
    comments = [
        lifecycle_comment(1, pending_record(wanted, baseline)),
        lifecycle_comment(2, transition, created_at="2026-08-31T10:05:00Z"),
        lifecycle_comment(3, terminal, created_at="2026-08-31T11:00:00Z"),
    ]

    def result_with(mutator) -> str:
        responses = {
            "/repos/Oteryn/Oteryn/issues/102/comments": comments,
            **direct_moving_base_responses(wanted, receipt),
        }
        mutator(responses)
        return FakeAudit(responses).classify_rollout_readback(
            wanted, target, now="2026-08-31T13:00:00Z"
        )

    repo = wanted["repository"]
    gate = receipt["aggregate_gate_run"]
    assert result_with(lambda responses: responses.__setitem__(
        f"/repos/{repo}/pulls/{receipt['pr_a']}",
        {**responses[f"/repos/{repo}/pulls/{receipt['pr_a']}"], "head": {"sha": "0" * 40}},
    )) == "DRIFT"
    assert result_with(lambda responses: responses[f"/repos/{repo}/commits/{receipt['a_head']}/check-runs?per_page=100"]["check_runs"][0].update(
        {"head_sha": "0" * 40}
    )) == "DRIFT"
    assert result_with(lambda responses: responses[f"/repos/{repo}/commits/{receipt['a_head']}/check-runs?per_page=100"]["check_runs"][0].update(
        {"completed_at": "2026-08-31T10:45:00Z"}
    )) == "DRIFT"
    assert result_with(lambda responses: responses["/repos/Oteryn/Oteryn/actions/runs/76"].update(
        {"event": "workflow_dispatch"}
    )) == "DRIFT"
    assert result_with(lambda responses: responses[f"/repos/{repo}/pulls/{receipt['pr_b']}"].update(
        {"merge_commit_sha": "0" * 40}
    )) == "DRIFT"
    assert result_with(lambda responses: responses[f"/repos/{repo}/commits/{receipt['main_after_b']}"].update(
        {"parents": [{"sha": "0" * 40}]}
    )) == "DRIFT"
    assert result_with(lambda responses: responses[f"/repos/{repo}/commits/{receipt['main_after_a']}"].update(
        {"parents": [{"sha": "0" * 40}]}
    )) == "DRIFT"
    assert result_with(lambda responses: responses[f"/repos/{repo}/compare/{receipt['main_before_b']}...{receipt['main_after_b']}"].update(
        {"status": "diverged"}
    )) == "DRIFT"
    assert result_with(lambda responses: responses[f"/repos/{repo}/actions/runs/{gate['run_id']}"].update(
        {"event": "pull_request"}
    )) == "DRIFT"
    assert result_with(lambda responses: responses[f"/repos/{repo}/actions/runs/{gate['run_id']}"].update(
        {"head_sha": "0" * 40}
    )) == "DRIFT"
    assert result_with(lambda responses: responses[f"/repos/{repo}/actions/runs/{gate['run_id']}"].update(
        {"conclusion": "failure"}
    )) == "DRIFT"
    assert result_with(lambda responses: responses[f"/repos/{repo}/actions/runs/{gate['run_id']}"].update(
        {"run_started_at": "2026-08-31T10:00:00Z"}
    )) == "DRIFT"
    assert result_with(lambda responses: responses[f"/repos/{repo}/commits/{receipt['merge_group_sha']}"].update(
        {"parents": [{"sha": receipt["a_head"]}]}
    )) == "DRIFT"
    assert result_with(lambda responses: responses[
        f"/repos/{repo}/commits/{receipt['merge_group_sha']}/check-runs?per_page=100"
    ]["check_runs"][0].update({"app": {"id": 1}})) == "DRIFT"
    assert result_with(lambda responses: responses[
        f"/repos/{repo}/commits/{receipt['merge_group_sha']}/check-runs?per_page=100"
    ]["check_runs"][0].update({"name": "forged-gate"})) == "DRIFT"
    assert result_with(lambda responses: responses[
        f"/repos/{repo}/commits/{receipt['merge_group_sha']}/check-runs?per_page=100"
    ]["check_runs"][0].update({"head_sha": "0" * 40})) == "DRIFT"
    assert result_with(lambda responses: responses[
        f"/repos/{repo}/commits/{receipt['merge_group_sha']}/check-runs?per_page=100"
    ]["check_runs"][0].update({"conclusion": "failure"})) == "DRIFT"
    assert result_with(lambda responses: responses[
        f"/repos/{repo}/commits/{receipt['merge_group_sha']}/check-runs?per_page=100"
    ]["check_runs"][0].update({"completed_at": "2026-08-31T11:10:00Z"})) == "DRIFT"
    assert result_with(lambda responses: responses[f"/repos/{repo}/branches/main"].update(
        {"protected": False}
    )) == "DRIFT"

    def not_integrated(responses: dict[str, object]) -> None:
        main_head = "f" * 40
        responses[f"/repos/{repo}/branches/main"]["commit"] = {"sha": main_head}
        responses[f"/repos/{repo}/compare/{receipt['main_after_a']}...{main_head}"] = {
            "status": "behind",
            "merge_base_commit": {"sha": "0" * 40},
        }

    assert result_with(not_integrated) == "DRIFT"

    assert result_with(lambda responses: responses.__setitem__(
        f"/repos/{repo}/pulls/{receipt['pr_a']}", []
    )) == "DRIFT"

    same_pr_terminal = json.loads(json.dumps(terminal))
    same_pr_terminal["moving_base_receipt"]["pr_b"] = receipt["pr_a"]
    same_comments = [comments[0], comments[1], lifecycle_comment(3, same_pr_terminal, created_at="2026-08-31T11:00:00Z")]
    assert FakeAudit({
        "/repos/Oteryn/Oteryn/issues/102/comments": same_comments,
        **direct_moving_base_responses(wanted, receipt),
    }).classify_rollout_readback(wanted, target, now="2026-08-31T13:00:00Z") == "DRIFT"


def test_readable_malformed_nested_direct_success_evidence_is_drift() -> None:
    """A decoded-but-wrong REST shape is evidence mismatch, never unreadability."""
    wanted = v2_wanted()
    baseline = pending_baseline(wanted)
    target = m.core.target_rollout_state(wanted)
    transition = transition_record(wanted, baseline)
    terminal = terminal_record(wanted, target, terminal_status="SUCCESS")
    receipt = terminal["moving_base_receipt"]
    comments = [
        lifecycle_comment(1, pending_record(wanted, baseline)),
        lifecycle_comment(2, transition, created_at="2026-08-31T10:05:00Z"),
        lifecycle_comment(3, terminal, created_at="2026-08-31T11:00:00Z"),
    ]
    repo = wanted["repository"]

    def result_with(mutator) -> str:
        responses = {
            "/repos/Oteryn/Oteryn/issues/102/comments": comments,
            **direct_moving_base_responses(wanted, receipt),
        }
        mutator(responses)
        try:
            return FakeAudit(responses).classify_rollout_readback(
                wanted, target, now="2026-08-31T13:00:00Z"
            )
        except (TypeError, AttributeError) as error:
            return f"CRASH:{type(error).__name__}"

    def malformed_integrated_base(responses: dict[str, object]) -> None:
        main_head = "f" * 40
        responses[f"/repos/{repo}/branches/main"]["commit"] = {"sha": main_head}
        responses[f"/repos/{repo}/compare/{receipt['main_after_a']}...{main_head}"] = {
            "status": "ahead",
            "merge_base_commit": "malformed",
        }

    malformed_payloads = (
        (
            "main-after-b parents",
            lambda responses: responses[f"/repos/{repo}/commits/{receipt['main_after_b']}"].update(
                {"parents": None}
            ),
        ),
        (
            "main-after-a parents",
            lambda responses: responses[f"/repos/{repo}/commits/{receipt['main_after_a']}"].update(
                {"parents": "malformed"}
            ),
        ),
        (
            "pull base",
            lambda responses: responses[f"/repos/{repo}/pulls/{receipt['pr_a']}"].update(
                {"base": "malformed"}
            ),
        ),
        (
            "pull base repository",
            lambda responses: responses[f"/repos/{repo}/pulls/{receipt['pr_a']}"]["base"].update(
                {"repo": "malformed"}
            ),
        ),
        (
            "pull head",
            lambda responses: responses[f"/repos/{repo}/pulls/{receipt['pr_a']}"].update(
                {"head": "malformed"}
            ),
        ),
        (
            "check app",
            lambda responses: responses[
                f"/repos/{repo}/commits/{receipt['a_head']}/check-runs?per_page=100"
            ]["check_runs"][0].update({"app": "malformed"}),
        ),
        (
            "check pull requests",
            lambda responses: responses[
                f"/repos/{repo}/commits/{receipt['a_head']}/check-runs?per_page=100"
            ]["check_runs"][0].update({"pull_requests": None}),
        ),
        (
            "protected branch commit",
            lambda responses: responses[f"/repos/{repo}/branches/main"].update(
                {"commit": "malformed"}
            ),
        ),
        ("integration merge base", malformed_integrated_base),
    )

    for label, mutator in malformed_payloads:
        result = result_with(mutator)
        assert result == "DRIFT", f"{label}: {result}"


def test_readable_missing_direct_success_evidence_is_drift_and_never_a_target() -> None:
    wanted = v2_wanted()
    baseline = pending_baseline(wanted)
    target = m.core.target_rollout_state(wanted)
    transition = transition_record(wanted, baseline)
    terminal = terminal_record(wanted, target, terminal_status="SUCCESS")
    comments = [
        lifecycle_comment(1, pending_record(wanted, baseline)),
        lifecycle_comment(2, transition, created_at="2026-08-31T10:05:00Z"),
        lifecycle_comment(3, terminal, created_at="2026-08-31T11:00:00Z"),
    ]
    receipt = terminal["moving_base_receipt"]
    audit = FakeAudit({
        "/repos/Oteryn/Oteryn/issues/102/comments": comments,
        **{path: None for path in direct_moving_base_responses(wanted, receipt)},
    })
    classification = audit.classify_rollout_readback(wanted, target, now="2026-08-31T13:00:00Z")
    assert classification == "DRIFT"
    assert m.core.effective_rollout_state(classification) != "TARGET"


def test_unreadable_direct_success_evidence_is_unknown() -> None:
    wanted = v2_wanted()
    baseline = pending_baseline(wanted)
    target = m.core.target_rollout_state(wanted)
    transition = transition_record(wanted, baseline)
    terminal = terminal_record(wanted, target, terminal_status="SUCCESS")
    receipt = terminal["moving_base_receipt"]
    comments = [
        lifecycle_comment(1, pending_record(wanted, baseline)),
        lifecycle_comment(2, transition, created_at="2026-08-31T10:05:00Z"),
        lifecycle_comment(3, terminal, created_at="2026-08-31T11:00:00Z"),
    ]
    for failure in (RuntimeError("transport unavailable"), ValueError("decode failure")):
        responses = {
            "/repos/Oteryn/Oteryn/issues/102/comments": comments,
            **direct_moving_base_responses(wanted, receipt),
            f"/repos/{wanted['repository']}/pulls/{receipt['pr_a']}": failure,
        }
        assert FakeAudit(responses).classify_rollout_readback(
            wanted, target, now="2026-08-31T13:00:00Z"
        ) == "UNKNOWN"


def test_valid_rollback_is_non_target_and_terminal_closeout_rejects_it() -> None:
    wanted = v2_wanted()
    baseline = pending_baseline(wanted)
    records = [
        lifecycle_comment(1, pending_record(wanted, baseline)),
        lifecycle_comment(2, transition_record(wanted, baseline), created_at="2026-08-31T10:05:00Z"),
        lifecycle_comment(3, terminal_record(wanted, baseline, terminal_status="ROLLED_BACK"), created_at="2026-08-31T11:00:00Z"),
    ]
    assert m.core.classify_rollout_state(
        wanted, baseline, records, now="2026-08-31T13:00:00Z"
    ) == "ROLLED_BACK"
    assert not m.core.terminal_v2_closeout_permitted({
        "Oteryn/Oteryn": "SUCCESS",
        "Oteryn/Oteryn-Game": "SUCCESS",
        "Oteryn/Oteryn-Platform": "SUCCESS",
        "Oteryn/Oteryn-Atlas": "ROLLED_BACK",
    })
    assert not m.core.terminal_v2_closeout_permitted({
        "Oteryn/Oteryn": "SUCCESS",
        "Oteryn/Oteryn-Game": "SUCCESS",
        "Oteryn/Oteryn-Platform": "SUCCESS",
        "Oteryn/Oteryn-Atlas": "PENDING",
    })
    assert m.core.effective_rollout_state("SUCCESS") == "TARGET"
    assert m.core.effective_rollout_state("ROLLED_BACK") == "ROLLED_BACK"


def test_multiple_valid_rollback_receipts_use_the_latest_terminal_state() -> None:
    wanted = v2_wanted()
    baseline = pending_baseline(wanted)
    first = transition_record(wanted, baseline, transition_id="meta-v2-cutover-1")
    second = transition_record(wanted, baseline, transition_id="meta-v2-cutover-2")
    records = [
        lifecycle_comment(1, pending_record(wanted, baseline)),
        lifecycle_comment(2, first, created_at="2026-08-31T10:05:00Z"),
        lifecycle_comment(
            3,
            terminal_record(
                wanted, baseline, terminal_status="ROLLED_BACK", transition_id="meta-v2-cutover-1",
            ),
            created_at="2026-08-31T10:30:00Z",
        ),
        lifecycle_comment(4, second, created_at="2026-08-31T10:35:00Z"),
        lifecycle_comment(
            5,
            terminal_record(
                wanted,
                baseline,
                terminal_status="ROLLED_BACK",
                transition_id="meta-v2-cutover-2",
                pre_transition_comment_id=4,
            ),
            created_at="2026-08-31T11:00:00Z",
        ),
    ]
    assert m.core.classify_rollout_state(
        wanted, baseline, records, now="2026-08-31T13:00:00Z"
    ) == "ROLLED_BACK"


def test_latest_rollback_does_not_reverify_stale_success_evidence() -> None:
    wanted = v2_wanted()
    baseline = pending_baseline(wanted)
    target = m.core.target_rollout_state(wanted)
    first = transition_record(wanted, baseline, transition_id="meta-v2-cutover-success")
    second = transition_record(wanted, baseline, transition_id="meta-v2-cutover-rollback")
    records = [
        lifecycle_comment(1, pending_record(wanted, baseline)),
        lifecycle_comment(2, first, created_at="2026-08-31T10:05:00Z"),
        lifecycle_comment(
            3,
            terminal_record(
                wanted,
                target,
                terminal_status="SUCCESS",
                transition_id="meta-v2-cutover-success",
            ),
            created_at="2026-08-31T10:30:00Z",
        ),
        lifecycle_comment(4, second, created_at="2026-08-31T10:35:00Z"),
        lifecycle_comment(
            5,
            terminal_record(
                wanted,
                baseline,
                terminal_status="ROLLED_BACK",
                transition_id="meta-v2-cutover-rollback",
                pre_transition_comment_id=4,
            ),
            created_at="2026-08-31T11:00:00Z",
        ),
    ]
    verification_calls: list[int] = []

    def unavailable_stale_success(_wanted: dict, _pre: dict, terminal: dict) -> str:
        verification_calls.append(terminal["id"])
        return "UNKNOWN"

    assert m.core.classify_rollout_state(
        wanted,
        baseline,
        records,
        now="2026-08-31T13:00:00Z",
        success_receipt_verifier=unavailable_stale_success,
    ) == "ROLLED_BACK"
    assert verification_calls == []


def test_control_plane_classifier_conservatively_covers_authority_and_gate_implementation() -> None:
    for path in (
        ".github/workflows/meta-gate.yml",
        ".github/actions/meta-gate/action.yml",
        "AGENTS.md",
        "docs/architecture/adr/0002-organization-governance-operating-model.md",
        "docs/ci/CI_CONTRACT.md",
        "docs/governance/AI_REVIEW_POLICY.md",
        "docs/recovery/organization-recovery-contract.md",
        "docs/migration/active-cutover-contract.md",
        "ecosystem/governance-desired-state.json",
        "ecosystem/ai-review-policy.json",
        "ecosystem/agent-execution-routing-policy.json",
        "tools/governance/audit_github_readonly_core.py",
    ):
        assert m.core.is_control_plane_r2([path]), path
    assert not m.core.is_control_plane_r2(["docs/evidence/2026-08-31-historical-snapshot.md"])


def test_control_plane_owner_authorization_is_directly_verified_against_current_pr_and_role() -> None:
    repository = "Oteryn/Oteryn"
    pull_request = 124
    material_head_sha = "a" * 40
    scope = "META Task 1 V2 authority integration"
    comment = control_plane_owner_authorization_comment(
        77,
        repository=repository,
        pull_request=pull_request,
        material_head_sha=material_head_sha,
        scope=scope,
    )
    audit = FakeAudit({
        f"/repos/{repository}/pulls/{pull_request}": current_pull_request(
            repository, pull_request, material_head_sha
        ),
        f"/repos/{repository}/issues/{pull_request}/comments": [comment],
        f"/repos/{repository}/collaborators/blakinio/permission": {
            "permission": "admin", "user": {"login": "blakinio", "type": "User"},
        },
    })
    evidence = audit.control_plane_owner_authorization(
        repository, pull_request, material_head_sha, scope
    )
    assert evidence == {
        "status": "VERIFIED",
        "comment_id": 77,
        "author_login": "blakinio",
        "actor_type": "User",
        "owner_role": "admin",
        "repository": repository,
        "pull_request": pull_request,
        "material_head_sha": material_head_sha,
        "scope": scope,
        "authorize_integration": True,
    }
    assert audit.control_plane_integration_permitted(
        [".github/actions/meta-gate/action.yml"],
        repository=repository,
        pull_request=pull_request,
        material_head_sha=material_head_sha,
        scope=scope,
        candidate_ci_passed=True,
        independent_deep_review=True,
        merge_queue_required=False,
        merge_queue_validated=False,
    )


def test_control_plane_owner_authorization_fails_closed_for_edited_bot_stale_or_non_owner_evidence() -> None:
    repository = "Oteryn/Oteryn"
    pull_request = 124
    material_head_sha = "a" * 40
    scope = "META Task 1 V2 authority integration"

    def result_for(comment: dict, permission: object, current_head: str = material_head_sha) -> dict:
        return FakeAudit({
            f"/repos/{repository}/pulls/{pull_request}": current_pull_request(
                repository, pull_request, current_head
            ),
            f"/repos/{repository}/issues/{pull_request}/comments": [comment],
            f"/repos/{repository}/collaborators/blakinio/permission": permission,
        }).control_plane_owner_authorization(repository, pull_request, material_head_sha, scope)

    valid = control_plane_owner_authorization_comment(
        77,
        repository=repository,
        pull_request=pull_request,
        material_head_sha=material_head_sha,
        scope=scope,
    )
    admin = {"permission": "admin", "user": {"login": "blakinio", "type": "User"}}
    edited_duplicate = {**valid, "id": 78, "updated_at": "2026-08-31T12:01:00Z"}
    assert FakeAudit({
        f"/repos/{repository}/pulls/{pull_request}": current_pull_request(
            repository, pull_request, material_head_sha
        ),
        f"/repos/{repository}/issues/{pull_request}/comments": [valid, edited_duplicate],
        f"/repos/{repository}/collaborators/blakinio/permission": admin,
    }).control_plane_owner_authorization(repository, pull_request, material_head_sha, scope)["status"] == "UNKNOWN"
    malformed_duplicate = {
        **valid,
        "id": 79,
        "body": (
            '{"record_type":"CONTROL_PLANE_R2_OWNER_AUTHORIZATION",'
            f'"repository":"{repository}","pull_request":{pull_request},'
            f'"material_head_sha":"{material_head_sha}","scope":"{scope}",'
            '"authorize_integration":'
        ),
    }
    assert FakeAudit({
        f"/repos/{repository}/pulls/{pull_request}": current_pull_request(
            repository, pull_request, material_head_sha
        ),
        f"/repos/{repository}/issues/{pull_request}/comments": [valid, malformed_duplicate],
        f"/repos/{repository}/collaborators/blakinio/permission": admin,
    }).control_plane_owner_authorization(repository, pull_request, material_head_sha, scope)["status"] == "UNKNOWN"
    assert result_for({**valid, "updated_at": "2026-08-31T12:01:00Z"}, admin)["status"] == "UNKNOWN"
    bot = json.loads(json.dumps(valid))
    bot["user"]["type"] = "Bot"
    assert result_for(bot, admin)["status"] == "UNKNOWN"
    assert result_for(valid, {"permission": "write"})["status"] == "UNKNOWN"
    assert result_for(valid, admin, current_head="b" * 40)["status"] == "UNKNOWN"
    draft = current_pull_request(repository, pull_request, material_head_sha)
    draft["draft"] = True
    assert FakeAudit({
        f"/repos/{repository}/pulls/{pull_request}": draft,
        f"/repos/{repository}/issues/{pull_request}/comments": [valid],
        f"/repos/{repository}/collaborators/blakinio/permission": admin,
    }).control_plane_owner_authorization(repository, pull_request, material_head_sha, scope)["status"] == "UNKNOWN"


def test_control_plane_candidate_cannot_self_authorize_from_candidate_ci() -> None:
    repository = "Oteryn/Oteryn"
    pull_request = 124
    material_head_sha = "a" * 40
    scope = "META Task 1 V2 authority integration"
    unauthorised = FakeAudit({
        f"/repos/{repository}/pulls/{pull_request}": current_pull_request(
            repository, pull_request, material_head_sha
        ),
        f"/repos/{repository}/issues/{pull_request}/comments": [],
    })
    assert not unauthorised.control_plane_integration_permitted(
        [".github/workflows/ci.yml"],
        repository=repository,
        pull_request=pull_request,
        material_head_sha=material_head_sha,
        scope=scope,
        candidate_ci_passed=True,
        independent_deep_review=True,
        merge_queue_required=False,
        merge_queue_validated=False,
    )


def test_control_plane_owner_authorization_cli_reads_direct_evidence() -> None:
    repository = "Oteryn/Oteryn"
    pull_request = 124
    material_head_sha = "a" * 40
    scope = "META Task 1 V2 authority integration"
    responses = {
        f"/repos/{repository}/pulls/{pull_request}": current_pull_request(
            repository, pull_request, material_head_sha
        ),
        f"/repos/{repository}/issues/{pull_request}/comments": [
            control_plane_owner_authorization_comment(
                77,
                repository=repository,
                pull_request=pull_request,
                material_head_sha=material_head_sha,
                scope=scope,
            ),
        ],
        f"/repos/{repository}/collaborators/blakinio/permission": {
            "permission": "admin", "user": {"login": "blakinio", "type": "User"},
        },
    }
    original_audit = m.core.Audit
    original_load_desired = m.core.load_desired
    original_argv = m.core.sys.argv
    original_token = os.environ.get("GH_TOKEN")
    m.core.Audit = lambda token: FakeAudit(responses)
    m.core.load_desired = lambda: (_ for _ in ()).throw(
        AssertionError("owner-authorization readback must not load candidate desired state")
    )
    m.core.sys.argv = [
        "audit_github_readonly.py",
        "--verify-control-plane-owner-authorization",
        "--repository", repository,
        "--pull-request", str(pull_request),
        "--material-head-sha", material_head_sha,
        "--control-plane-scope", scope,
    ]
    os.environ["GH_TOKEN"] = "test"
    try:
        assert m.main() == 0
    finally:
        m.core.Audit = original_audit
        m.core.load_desired = original_load_desired
        m.core.sys.argv = original_argv
        if original_token is None:
            del os.environ["GH_TOKEN"]
        else:
            os.environ["GH_TOKEN"] = original_token


def test_pull_request_target_is_read_from_current_candidate_commit() -> None:
    main = "a" * 40
    head = "b" * 40
    audit = FakeAudit({
        "/repos/Oteryn/Test/branches/main": {"commit": {"sha": main}},
        "/repos/Oteryn/Test/actions/runs/301": target_run(main, head),
        "/repos/Oteryn/Test/pulls?state=open&base=main&sort=updated&direction=desc&per_page=20": [{
            "number": 7,
            "head": {"sha": head, "repo": {"full_name": "Oteryn/Test"}},
            "base": {"ref": "main"},
        }],
        f"/repos/Oteryn/Test/compare/{main}...{head}": {
            "status": "ahead", "merge_base_commit": {"sha": main},
        },
        f"/repos/Oteryn/Test/commits/{head}/check-runs?per_page=100": {
            "check_runs": [
                check_run("meta-gate", 302, 7),
                check_run("ai-review-gate", 301, 7, head_sha=head),
            ],
        },
        "/repos/Oteryn/Test/actions/runs/302": {
            "event": "pull_request", "head_sha": head, "workflow_id": 1,
        },
    })
    observed = audit.representative_check_sources(
        "Oteryn/Test", {"meta-gate", "ai-review-gate"}, ACTIONS_APP_ID
    )
    assert m.expected_sources_satisfied(
        observed, {"meta-gate", "ai-review-gate"}, ACTIONS_APP_ID
    )


def test_pull_request_workflow_is_read_from_candidate_head() -> None:
    main = "a" * 40
    head = "b" * 40
    audit = FakeAudit({
        "/repos/Oteryn/Test/branches/main": {"commit": {"sha": main}},
        f"/repos/Oteryn/Test/commits/{main}/check-runs?per_page=100": {"check_runs": []},
        "/repos/Oteryn/Test/pulls?state=open&base=main&sort=updated&direction=desc&per_page=20": [{
            "number": 7,
            "head": {"sha": head, "repo": {"full_name": "Oteryn/Test"}},
            "base": {"ref": "main"},
        }],
        f"/repos/Oteryn/Test/compare/{main}...{head}": {
            "status": "ahead", "merge_base_commit": {"sha": main},
        },
        f"/repos/Oteryn/Test/commits/{head}/check-runs?per_page=100": {
            "check_runs": [check_run("gate", 309, 7)],
        },
        "/repos/Oteryn/Test/actions/runs/309": {
            "event": "pull_request", "head_sha": head, "workflow_id": 1,
        },
        f"/repos/Oteryn/Test/contents/.github/workflows/gate.yml?ref={head}": {
            "content": base64.b64encode(b"on:\n  pull_request:\n    paths: [src/**]\n").decode("ascii"),
        },
    })
    assert audit.representative_check_sources("Oteryn/Test", {"gate"}, ACTIONS_APP_ID) == {}
    assert f"/repos/Oteryn/Test/contents/.github/workflows/gate.yml?ref={head}" in audit.calls


def test_disabled_pull_request_target_workflow_does_not_prove_gate() -> None:
    main = "a" * 40
    head = "b" * 40
    audit = FakeAudit({
        "/repos/Oteryn/Test/branches/main": {"commit": {"sha": main}},
        "/repos/Oteryn/Test/actions/runs/307": {
            **target_run(main, head),
            "workflow_id": 9,
        },
        "/repos/Oteryn/Test/actions/workflows/9": {"state": "disabled_manually"},
        "/repos/Oteryn/Test/pulls?state=open&base=main&sort=updated&direction=desc&per_page=20": [{"number": 7, "head": {"sha": head, "repo": {"full_name": "Oteryn/Test"}}, "base": {"ref": "main"}}],
        f"/repos/Oteryn/Test/compare/{main}...{head}": {"status": "ahead", "merge_base_commit": {"sha": main}},
        f"/repos/Oteryn/Test/commits/{head}/check-runs?per_page=100": {"check_runs": [
            check_run("meta-gate", 308, 7),
            check_run("ai-review-gate", 307, 7, head_sha=head),
        ]},
        "/repos/Oteryn/Test/actions/runs/308": {"event": "pull_request", "head_sha": head, "workflow_id": 1},
    })
    observed = audit.representative_check_sources("Oteryn/Test", {"meta-gate", "ai-review-gate"}, ACTIONS_APP_ID)
    assert not m.expected_sources_satisfied(observed, {"meta-gate", "ai-review-gate"}, ACTIONS_APP_ID)


def test_pull_request_target_for_other_pr_does_not_prove_gate() -> None:
    main = "a" * 40
    head = "b" * 40
    audit = FakeAudit({
        "/repos/Oteryn/Test/branches/main": {"commit": {"sha": main}},
        "/repos/Oteryn/Test/actions/runs/303": target_run(main, head, pr_number=99),
        "/repos/Oteryn/Test/pulls?state=open&base=main&sort=updated&direction=desc&per_page=20": [{
            "number": 7,
            "head": {"sha": head, "repo": {"full_name": "Oteryn/Test"}},
            "base": {"ref": "main"},
        }],
        f"/repos/Oteryn/Test/compare/{main}...{head}": {
            "status": "ahead", "merge_base_commit": {"sha": main},
        },
        f"/repos/Oteryn/Test/commits/{head}/check-runs?per_page=100": {
            "check_runs": [
                check_run("meta-gate", 304, 7),
                check_run("ai-review-gate", 303, 7, head_sha=head),
            ],
        },
        "/repos/Oteryn/Test/actions/runs/304": {
            "event": "pull_request", "head_sha": head, "workflow_id": 1,
        },
    })
    observed = audit.representative_check_sources(
        "Oteryn/Test", {"meta-gate", "ai-review-gate"}, ACTIONS_APP_ID
    )
    assert not m.expected_sources_satisfied(
        observed, {"meta-gate", "ai-review-gate"}, ACTIONS_APP_ID
    )



def test_stale_pull_request_target_generation_does_not_prove_current_head() -> None:
    main = "a" * 40
    old_head = "b" * 40
    head = "c" * 40
    audit = FakeAudit({
        "/repos/Oteryn/Test/branches/main": {"commit": {"sha": main}},
        "/repos/Oteryn/Test/actions/runs/305": target_run(main, old_head),
        "/repos/Oteryn/Test/pulls?state=open&base=main&sort=updated&direction=desc&per_page=20": [{
            "number": 7,
            "head": {"sha": head, "repo": {"full_name": "Oteryn/Test"}},
            "base": {"ref": "main"},
        }],
        f"/repos/Oteryn/Test/compare/{main}...{head}": {
            "status": "ahead", "merge_base_commit": {"sha": main},
        },
        f"/repos/Oteryn/Test/commits/{head}/check-runs?per_page=100": {
            "check_runs": [
                check_run("meta-gate", 306, 7),
                check_run("ai-review-gate", 305, 7, head_sha=head),
            ],
        },
        "/repos/Oteryn/Test/actions/runs/306": {
            "event": "pull_request", "head_sha": head, "workflow_id": 1,
        },
    })
    observed = audit.representative_check_sources(
        "Oteryn/Test", {"meta-gate", "ai-review-gate"}, ACTIONS_APP_ID
    )
    assert not m.expected_sources_satisfied(
        observed, {"meta-gate", "ai-review-gate"}, ACTIONS_APP_ID
    )


def test_stale_pull_request_target_base_does_not_prove_current_pr() -> None:
    main = "a" * 40
    head = "b" * 40
    stale_base = "c" * 40
    run = target_run(main, head)
    run["pull_requests"][0]["base"]["sha"] = stale_base
    audit = FakeAudit({
        "/repos/Oteryn/Test/branches/main": {"commit": {"sha": main}},
        "/repos/Oteryn/Test/actions/runs/311": run,
        "/repos/Oteryn/Test/pulls?state=open&base=main&sort=updated&direction=desc&per_page=20": [{
            "number": 7,
            "head": {"sha": head, "repo": {"full_name": "Oteryn/Test"}},
            "base": {"ref": "main"},
        }],
        f"/repos/Oteryn/Test/compare/{main}...{head}": {
            "status": "ahead", "merge_base_commit": {"sha": main},
        },
        f"/repos/Oteryn/Test/commits/{head}/check-runs?per_page=100": {"check_runs": [
            check_run("meta-gate", 312, 7),
            check_run("ai-review-gate", 311, 7, head_sha=head),
        ]},
        "/repos/Oteryn/Test/actions/runs/312": {
            "event": "pull_request", "head_sha": head, "workflow_id": 1,
        },
    })
    observed = audit.representative_check_sources(
        "Oteryn/Test", {"meta-gate", "ai-review-gate"}, ACTIONS_APP_ID
    )
    assert not m.expected_sources_satisfied(
        observed, {"meta-gate", "ai-review-gate"}, ACTIONS_APP_ID
    )


def test_stale_target_check_run_head_does_not_prove_current_pr() -> None:
    main = "a" * 40
    head = "b" * 40
    old_head = "c" * 40
    audit = FakeAudit({
        "/repos/Oteryn/Test/branches/main": {"commit": {"sha": main}},
        "/repos/Oteryn/Test/actions/runs/313": target_run(main, head),
        "/repos/Oteryn/Test/pulls?state=open&base=main&sort=updated&direction=desc&per_page=20": [{
            "number": 7,
            "head": {"sha": head, "repo": {"full_name": "Oteryn/Test"}},
            "base": {"ref": "main"},
        }],
        f"/repos/Oteryn/Test/compare/{main}...{head}": {
            "status": "ahead", "merge_base_commit": {"sha": main},
        },
        f"/repos/Oteryn/Test/commits/{head}/check-runs?per_page=100": {"check_runs": [
            check_run("meta-gate", 314, 7),
            check_run("ai-review-gate", 313, 7, head_sha=old_head),
        ]},
        "/repos/Oteryn/Test/actions/runs/314": {
            "event": "pull_request", "head_sha": head, "workflow_id": 1,
        },
    })
    observed = audit.representative_check_sources(
        "Oteryn/Test", {"meta-gate", "ai-review-gate"}, ACTIONS_APP_ID
    )
    assert not m.expected_sources_satisfied(
        observed, {"meta-gate", "ai-review-gate"}, ACTIONS_APP_ID
    )


def test_desired_state_requires_complete_merge_and_security_contract() -> None:
    data = json.loads(m.DESIRED_PATH.read_text(encoding="utf-8"))
    original_path = m.core.DESIRED_PATH
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "desired.json"
        broken = json.loads(json.dumps(data))
        del broken["permanent_repositories"][0]["squash_only"]
        path.write_text(json.dumps(broken), encoding="utf-8")
        m.core.DESIRED_PATH = path
        try:
            m.core.load_desired()
        except SystemExit as exc:
            assert "squash_only" in str(exc)
        else:
            raise AssertionError("missing squash_only must fail closed")

        broken = json.loads(json.dumps(data))
        del broken["permanent_repositories"][0]["security"]["push_protection"]
        path.write_text(json.dumps(broken), encoding="utf-8")
        try:
            m.core.load_desired()
        except SystemExit as exc:
            assert "security contract" in str(exc)
        else:
            raise AssertionError("incomplete security object must fail closed")
        finally:
            m.core.DESIRED_PATH = original_path

def test_desired_state_requires_terminal_administrative_identity() -> None:
    data = json.loads(m.DESIRED_PATH.read_text(encoding="utf-8"))
    original_path = m.core.DESIRED_PATH
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "desired.json"
        for broken in (
            {**data, "administrative_repositories": []},
            json.loads(json.dumps(data)),
        ):
            if broken["administrative_repositories"]:
                broken["administrative_repositories"][0]["repository_id"] = 1
            path.write_text(json.dumps(broken), encoding="utf-8")
            m.core.DESIRED_PATH = path
            try:
                try:
                    m.core.load_desired()
                except SystemExit as exc:
                    assert "administrative repository" in str(exc)
                else:
                    raise AssertionError("missing or wrong administrative identity must fail closed")
            finally:
                m.core.DESIRED_PATH = original_path


def test_desired_state_requires_complete_administrative_contract() -> None:
    data = json.loads(m.DESIRED_PATH.read_text(encoding="utf-8"))
    original_path = m.core.DESIRED_PATH
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "desired.json"
        for field in ("classification", "terminal_state", "archived", "retention_authority"):
            broken = json.loads(json.dumps(data))
            del broken["administrative_repositories"][0][field]
            path.write_text(json.dumps(broken), encoding="utf-8")
            m.core.DESIRED_PATH = path
            try:
                try:
                    m.core.load_desired()
                except SystemExit as exc:
                    assert "administrative repository" in str(exc)
                else:
                    raise AssertionError(f"missing {field} must fail closed")
            finally:
                m.core.DESIRED_PATH = original_path


def test_desired_state_requires_strict_protection_contract() -> None:
    data = json.loads(m.DESIRED_PATH.read_text(encoding="utf-8"))
    original_path = m.core.DESIRED_PATH
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "desired.json"
        for mutate in (
            lambda item: item["protection"].pop("broad_bypass"),
            lambda item: item["protection"].pop("pull_requests"),
            lambda item: item["protection"].__setitem__("pull_requests", False),
            lambda item: item["protection"].__setitem__("force_pushes", True),
        ):
            broken = json.loads(json.dumps(data))
            mutate(broken["permanent_repositories"][0])
            path.write_text(json.dumps(broken), encoding="utf-8")
            m.core.DESIRED_PATH = path
            try:
                try:
                    m.core.load_desired()
                except SystemExit as exc:
                    assert "protection contract" in str(exc)
                else:
                    raise AssertionError("weakened protection contract must fail closed")
            finally:
                m.core.DESIRED_PATH = original_path


def test_desired_state_requires_complete_coordinate_policy() -> None:
    data = json.loads(m.DESIRED_PATH.read_text(encoding="utf-8"))
    original_path = m.core.DESIRED_PATH
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "desired.json"
        broken = json.loads(json.dumps(data))
        del broken["mutable_coordinate_policy"]["forbidden"]
        path.write_text(json.dumps(broken), encoding="utf-8")
        m.core.DESIRED_PATH = path
        try:
            try:
                m.core.load_desired()
            except SystemExit as exc:
                assert "mutable_coordinate_policy" in str(exc)
            else:
                raise AssertionError("missing coordinate policy must fail closed")
        finally:
            m.core.DESIRED_PATH = original_path

def test_desired_state_requires_codeowners_coverage_contract() -> None:
    data = json.loads(m.DESIRED_PATH.read_text(encoding="utf-8"))
    original_path = m.core.DESIRED_PATH
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "desired.json"
        broken = json.loads(json.dumps(data))
        del broken["permanent_repositories"][0]["codeowners_required_paths"]
        path.write_text(json.dumps(broken), encoding="utf-8")
        m.core.DESIRED_PATH = path
        try:
            try:
                m.core.load_desired()
            except SystemExit as exc:
                assert "codeowners_required_paths" in str(exc)
            else:
                raise AssertionError("missing CODEOWNERS coverage contract must fail closed")
        finally:
            m.core.DESIRED_PATH = original_path


def test_desired_state_requires_retention_release_contract() -> None:
    data = json.loads(m.DESIRED_PATH.read_text(encoding="utf-8"))
    original_path = m.core.DESIRED_PATH
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "desired.json"
        for broken in (json.loads(json.dumps(data)), json.loads(json.dumps(data))):
            if "retention_release" in broken["administrative_repositories"][0]:
                if broken is not None and broken["administrative_repositories"][0]["retention_release"]["assets"]:
                    if len(broken["administrative_repositories"][0]["retention_release"]["assets"]) == 6:
                        broken["administrative_repositories"][0]["retention_release"]["assets"].pop(next(iter(broken["administrative_repositories"][0]["retention_release"]["assets"])))
                    else:
                        del broken["administrative_repositories"][0]["retention_release"]
            path.write_text(json.dumps(broken), encoding="utf-8")
            m.core.DESIRED_PATH = path
            try:
                try:
                    m.core.load_desired()
                except SystemExit as exc:
                    assert "retention" in str(exc)
                else:
                    raise AssertionError("weakened retention release contract must fail closed")
            finally:
                m.core.DESIRED_PATH = original_path


def test_transport_failure_becomes_runtime_unknown_signal() -> None:
    original = m.urllib.request.urlopen

    def fail(*args, **kwargs):
        raise urllib.error.URLError("dns unavailable")

    m.urllib.request.urlopen = fail
    try:
        audit = m.Audit("test")
        try:
            audit.api("/repos/Oteryn/Test")
        except RuntimeError as exc:
            assert "transport unavailable" in str(exc)
        else:
            raise AssertionError("transport failure must be wrapped as RuntimeError")
    finally:
        m.urllib.request.urlopen = original


def test_graphql_transport_failure_becomes_runtime_unknown_signal() -> None:
    original = m.urllib.request.urlopen

    def fail(*args, **kwargs):
        raise urllib.error.URLError("dns unavailable")

    m.urllib.request.urlopen = fail
    try:
        audit = m.Audit("test")
        try:
            audit.graphql("query { viewer { login } }", {})
        except RuntimeError as exc:
            assert "transport unavailable" in str(exc)
        else:
            raise AssertionError("GraphQL transport failure must be wrapped as RuntimeError")
    finally:
        m.urllib.request.urlopen = original


def main() -> int:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print(f"governance terminal live-audit tests PASS: {len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
