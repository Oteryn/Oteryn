#!/usr/bin/env python3
"""Regression tests for trusted-base review-attestation issuance."""
from __future__ import annotations

import base64
from copy import deepcopy
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import trusted_review_attestation as issuer  # noqa: E402
import test_verify_ai_review_evidence as p2_evidence  # noqa: E402


REPOSITORY = "Oteryn/Oteryn"
REPOSITORY_ID = 1338152366
BASE = "a" * 40
HEAD = "b" * 40
RUN_ID = 100
RUN_ATTEMPT = 2
JOB_ID = 101
CHECK_RUN_ID = 102
CHECK_SUITE_ID = 103
PR_ID = 200


def workflow_run() -> dict:
    return {
        "id": RUN_ID,
        "run_attempt": RUN_ATTEMPT,
        "event": "pull_request_target",
        "head_sha": HEAD,
        "check_suite_id": CHECK_SUITE_ID,
        "repository": {"id": REPOSITORY_ID, "full_name": REPOSITORY},
        "head_repository": {"id": REPOSITORY_ID, "full_name": REPOSITORY, "fork": False},
        "pull_requests": [{
            "id": PR_ID,
            "number": 17,
            "base": {
                "ref": "main", "sha": BASE,
                "repo": {"id": REPOSITORY_ID, "name": "Oteryn", "url": f"https://api.github.com/repos/{REPOSITORY}"},
            },
            "head": {
                "sha": HEAD,
                "repo": {"id": REPOSITORY_ID, "name": "Oteryn", "url": f"https://api.github.com/repos/{REPOSITORY}"},
            },
        }],
    }


def workflow_jobs() -> list[dict]:
    return [{
        "id": JOB_ID,
        "name": "ai-review-gate",
        "run_id": RUN_ID,
        "run_attempt": RUN_ATTEMPT,
        "head_sha": HEAD,
        "check_run_url": f"https://api.github.com/repos/{REPOSITORY}/check-runs/{CHECK_RUN_ID}",
    }]


def check_run() -> dict:
    return {
        "id": CHECK_RUN_ID,
        "name": "ai-review-gate",
        "head_sha": HEAD,
        "check_suite": {"id": CHECK_SUITE_ID},
        "app": {"id": 15368, "slug": "github-actions"},
    }


def check_suite() -> dict:
    return {
        "id": CHECK_SUITE_ID,
        "head_sha": HEAD,
        "repository": {"id": REPOSITORY_ID, "full_name": REPOSITORY},
        "app": {"id": 15368, "slug": "github-actions"},
    }


def certificate() -> dict:
    workflow_uri = f"https://github.com/{REPOSITORY}/.github/workflows/governance-ai-review.yml@refs/heads/main"
    return {
        "subjectAlternativeName": workflow_uri,
        "issuer": "https://token.actions.githubusercontent.com",
        "githubWorkflowTrigger": "pull_request_target",
        "githubWorkflowSHA": BASE,
        "githubWorkflowRepository": REPOSITORY,
        "githubWorkflowRef": "refs/heads/main",
        "buildSignerURI": workflow_uri,
        "buildSignerDigest": BASE,
        "runnerEnvironment": "github-hosted",
        "sourceRepositoryURI": f"https://github.com/{REPOSITORY}",
        "sourceRepositoryDigest": BASE,
        "sourceRepositoryRef": "refs/heads/main",
        "sourceRepositoryIdentifier": str(REPOSITORY_ID),
        "buildConfigURI": workflow_uri,
        "buildConfigDigest": BASE,
        "buildTrigger": "pull_request_target",
        "runInvocationURI": f"https://github.com/{REPOSITORY}/actions/runs/{RUN_ID}/attempts/{RUN_ATTEMPT}",
    }


def verified_attestation_result(payload: bytes, cert: dict | None = None) -> list[dict]:
    return [{"verificationResult": {
        "signature": {"certificate": certificate() if cert is None else cert},
        "statement": {
            "predicateType": issuer.PREDICATE_TYPE,
            "predicate": json.loads(payload),
            "subject": [{"name": "oteryn-trusted-review-envelope.json", "digest": {
                "sha256": hashlib.sha256(payload).hexdigest(),
            }}],
        },
    }}]


def repository() -> dict:
    return {
        "id": REPOSITORY_ID,
        "full_name": REPOSITORY,
        "default_branch": "main",
        "archived": False,
        "disabled": False,
    }


def pull_request() -> dict:
    return {
        "id": PR_ID,
        "number": 17,
        "state": "open",
        "draft": False,
        "base": {
            "ref": "main",
            "sha": BASE,
            "repo": {"id": REPOSITORY_ID, "full_name": REPOSITORY},
        },
        "head": {
            "sha": HEAD,
            "repo": {"id": REPOSITORY_ID, "full_name": REPOSITORY, "fork": False},
        },
    }


def issuer_coordinates() -> dict:
    return {
        "workflow_ref": "Oteryn/Oteryn/.github/workflows/governance-ai-review.yml@refs/heads/main",
        "workflow_sha": "f" * 40,
        "workflow_execution_sha": "f" * 40,
        "workflow_run_id": 100,
        "workflow_run_attempt": 2,
        "workflow_job_id": 101,
        "check_run_id": 102,
        "check_suite_id": 103,
    }


def verified_source() -> dict:
    return {
        "kind": "issue_comment_result", "object_id": 201, "reviewed_head": HEAD,
        "actor_login": "reviewer[bot]", "actor_id": 202,
        "app_slug": "chatgpt-codex-connector", "app_id": None, "body_sha256": "1" * 64,
    }


def follow_up_coordinates() -> dict:
    return {
        "review_outcome": "ACCEPTED_WITH_FOLLOW_UP",
        "p2_review_id": 701,
        "finding_comment_ids": [702],
        "review_thread_ids": ["thread-702"],
        "follow_up_issue_numbers": [114],
    }


def ready_facts() -> dict:
    return issuer.validate_pr_facts(
        repository(), pull_request(), expected_repository=REPOSITORY,
        expected_repository_id=REPOSITORY_ID, expected_pr_id=PR_ID, expected_pr_number=17,
        expected_base=BASE, expected_head=HEAD,
    )


def make_follow_up_envelope(**overrides: object) -> dict:
    values: dict[str, object] = {
        "facts": ready_facts(),
        "classification": {
            "tier": "R2", "review_fingerprint": "c" * 64,
            "reviewer_class": "deep",
        },
        "policy_id": "oteryn-ai-review-risk-v1",
        "policy_sha256": "d" * 64,
        "classifier_revision": "sha256:" + "e" * 64,
        "issuer": issuer_coordinates(),
        "evidence_status": "verified",
        "evidence_sources": [verified_source()],
        "issued_at": "2026-08-30T09:30:00Z",
        **follow_up_coordinates(),
    }
    values.update(overrides)
    return issuer.make_envelope(**values)


def expect_issuance_failure(fn, message: str) -> None:
    try:
        fn()
    except issuer.IssuanceError:
        return
    raise AssertionError(message)


def expect_review_failure(fn, message: str) -> None:
    try:
        fn()
    except RuntimeError:
        return
    raise AssertionError(message)


def run_valid_p2_review_verifier(*, review_thread: dict | None = None,
                                  tracker_issue: dict | None = None) -> tuple[dict, list[tuple[str, int, str]]]:
    repo, _, final = p2_evidence._v1.core_tests.make_repo()
    current = p2_evidence._v1.core_tests.issue_comment(
        10, p2_evidence._v1.core_tests.request_body(final), stamp="2026-08-20T10:00:00Z",
    )
    summary = p2_evidence._summary_comment(final[:10])
    selected_thread = p2_evidence._p2_thread() if review_thread is None else review_thread
    selected_issue = p2_evidence._tracker_issue() if tracker_issue is None else tracker_issue
    reviews = [
        p2_evidence._v1.core_tests.request_anchor(current, final),
        p2_evidence._p2_review(final, body=p2_evidence._codex_review_envelope(final)),
    ]
    review_comments = [p2_evidence._p2_inline()]
    core = issuer.review_evidence._core
    originals = (
        core.fetch_comments,
        core.fetch_reviews,
        core.fetch_review_comments,
        issuer.review_evidence.fetch_pr_reactions,
        issuer.review_evidence.fetch_review_threads,
        issuer.review_evidence.fetch_review_source,
        issuer.review_evidence.fetch_json,
        issuer.review_evidence._v1.fetch_json,
        issuer.review_evidence._v1._core.fetch_json,
    )
    thread_calls: list[tuple[str, int, str]] = []
    try:
        core.fetch_comments = lambda *_args: [current, summary]
        core.fetch_reviews = lambda *_args: reviews
        core.fetch_review_comments = lambda *_args: review_comments
        issuer.review_evidence.fetch_pr_reactions = lambda *_args: []

        def fetch_threads(repository: str, pr_number: int, token: str) -> list[dict]:
            thread_calls.append((repository, pr_number, token))
            return [selected_thread]

        issuer.review_evidence.fetch_review_threads = fetch_threads
        issuer.review_evidence.fetch_review_source = lambda *_args: ("issue_comment_result", summary)
        issuer.review_evidence.fetch_json = lambda *_args: selected_issue
        issuer.review_evidence._v1.fetch_json = issuer.review_evidence.fetch_json
        issuer.review_evidence._v1._core.fetch_json = issuer.review_evidence.fetch_json
        result = issuer._run_review_verifier(
            repository="Oteryn/Test", pr_number=7, base=BASE, head=final, bare_git_dir=repo,
            policy=p2_evidence._policy(),
            classification={"tier": "R2", "review_fingerprint": "f" * 64}, token="test",
        )
    finally:
        (
            core.fetch_comments,
            core.fetch_reviews,
            core.fetch_review_comments,
            issuer.review_evidence.fetch_pr_reactions,
            issuer.review_evidence.fetch_review_threads,
            issuer.review_evidence.fetch_review_source,
            issuer.review_evidence.fetch_json,
            issuer.review_evidence._v1.fetch_json,
            issuer.review_evidence._v1._core.fetch_json,
        ) = originals
    assert result is not None
    return result, thread_calls


def test_canonical_envelope_bytes_have_recomputable_subject_identity() -> None:
    facts = issuer.validate_pr_facts(
        repository(), pull_request(), expected_repository=REPOSITORY,
        expected_repository_id=REPOSITORY_ID, expected_pr_id=PR_ID, expected_pr_number=17,
        expected_base=BASE, expected_head=HEAD,
    )
    envelope = issuer.make_envelope(
        facts=facts,
        classification={
            "tier": "R2", "review_fingerprint": "c" * 64,
            "reviewer_class": "deep",
        },
        policy_id="oteryn-ai-review-risk-v1",
        policy_sha256="d" * 64,
        classifier_revision="sha256:" + "e" * 64,
        issuer={
            "workflow_ref": "Oteryn/Oteryn/.github/workflows/governance-ai-review.yml@refs/heads/main",
            "workflow_sha": "f" * 40,
            "workflow_execution_sha": "f" * 40,
            "workflow_run_id": 100,
            "workflow_run_attempt": 2,
            "workflow_job_id": 101,
            "check_run_id": 102,
            "check_suite_id": 103,
        },
        evidence_status="verified",
        evidence_sources=[{
            "kind": "pull_request_review", "object_id": 201,
            "reviewed_head": HEAD, "actor_login": "reviewer[bot]", "actor_id": 202,
            "app_slug": "chatgpt-codex-connector", "app_id": None, "body_sha256": "1" * 64,
        }],
        review_outcome="PASS",
        p2_review_id=None,
        finding_comment_ids=None,
        review_thread_ids=None,
        follow_up_issue_numbers=None,
        issued_at="2026-08-30T09:30:00Z",
    )
    payload = issuer.canonical_json_bytes(envelope)
    assert payload == issuer.canonical_json_bytes(json.loads(payload))
    assert issuer.envelope_identifier(payload) == "sha256:" + hashlib.sha256(payload).hexdigest()
    assert envelope["predicate_type"] == issuer.PREDICATE_TYPE
    assert envelope["repository"] == {"id": REPOSITORY_ID, "full_name": REPOSITORY}
    assert envelope["pull_request"]["base"] == {"ref": "main", "sha": BASE}
    assert envelope["pull_request"]["head"] == HEAD
    assert envelope["review"] == {
        "tier": "R2", "fingerprint": "c" * 64, "reviewer_class": "deep",
        "evidence_status": "verified",
    }
    assert envelope["review_outcome"] == "PASS"


def test_canonical_envelope_binds_follow_up_outcome_and_exact_coordinates() -> None:
    envelope = make_follow_up_envelope()
    payload = issuer.canonical_json_bytes(envelope)
    assert payload == issuer.canonical_json_bytes(json.loads(payload))
    assert envelope["review_outcome"] == "ACCEPTED_WITH_FOLLOW_UP"
    assert envelope["p2_review_id"] == 701
    assert envelope["finding_comment_ids"] == [702]
    assert envelope["review_thread_ids"] == ["thread-702"]
    assert envelope["follow_up_issue_numbers"] == [114]


def test_follow_up_envelope_rejects_missing_coordinate() -> None:
    for coordinate in (
        "p2_review_id", "finding_comment_ids", "review_thread_ids", "follow_up_issue_numbers",
    ):
        expect_issuance_failure(
            lambda coordinate=coordinate: make_follow_up_envelope(**{coordinate: None}),
            f"follow-up envelope accepted missing {coordinate}",
        )


def test_follow_up_envelope_rejects_duplicate_coordinates() -> None:
    for coordinate, duplicate in (
        ("finding_comment_ids", [702, 702]),
        ("review_thread_ids", ["thread-702", "thread-702"]),
        ("follow_up_issue_numbers", [114, 114]),
    ):
        expect_issuance_failure(
            lambda coordinate=coordinate, duplicate=duplicate: make_follow_up_envelope(
                **{coordinate: duplicate}
            ),
            f"follow-up envelope accepted duplicate {coordinate}",
        )


def test_semantic_claims_reject_follow_up_outcome_or_coordinate_tamper() -> None:
    expected = {
        "policy": {"id": "oteryn-ai-review-risk-v1", "sha256": "d" * 64},
        "classifier": {"revision": "sha256:" + "e" * 64},
        "review": {
            "tier": "R2", "fingerprint": "c" * 64, "reviewer_class": "deep",
            "evidence_status": "verified",
        },
        "review_evidence": [verified_source()],
        **follow_up_coordinates(),
    }
    issuer.validate_semantic_claims(expected, expected)
    for coordinate, replacement in (
        ("review_outcome", "PASS"),
        ("p2_review_id", 999),
        ("finding_comment_ids", [999]),
        ("review_thread_ids", ["thread-999"]),
        ("follow_up_issue_numbers", [999]),
    ):
        candidate = deepcopy(expected)
        candidate[coordinate] = replacement
        expect_issuance_failure(
            lambda candidate=candidate: issuer.validate_semantic_claims(candidate, expected),
            f"semantic claims accepted tampered {coordinate}",
        )


def test_recompute_semantic_claims_preserves_follow_up_outcome_and_coordinates() -> None:
    root = Path(__file__).resolve().parents[2]
    review_match = {
        "reviewed_head": HEAD,
        "review_source_url": "ignored",
        "review_source_kind": "ignored",
        "review_source_commit_id": HEAD,
        **follow_up_coordinates(),
    }
    originals = (
        issuer.risk_policy.load_policy,
        issuer.risk_policy.evaluate,
        issuer._run_review_verifier,
        issuer._material_sources,
    )
    try:
        issuer.risk_policy.load_policy = lambda _path: {"policy_id": "oteryn-ai-review-risk-v1"}
        issuer.risk_policy.evaluate = lambda *_args: {
            "tier": "R2", "review_fingerprint": "c" * 64, "reviewer_class": "deep",
        }
        issuer._run_review_verifier = lambda **_kwargs: review_match
        issuer._material_sources = lambda *_args, **_kwargs: [verified_source()]
        recomputed = issuer.recompute_semantic_claims(
            facts=ready_facts(), repository=REPOSITORY, pr_number=17, base=BASE, head=HEAD,
            bare_git_dir=root, policy_path=root / "ecosystem/ai-review-policy.json",
            classifier_path=root / "tools/governance/ai_review_policy.py", token="test",
        )
    finally:
        (
            issuer.risk_policy.load_policy,
            issuer.risk_policy.evaluate,
            issuer._run_review_verifier,
            issuer._material_sources,
        ) = originals
    assert recomputed["review_outcome"] == "ACCEPTED_WITH_FOLLOW_UP"
    assert recomputed["p2_review_id"] == 701
    assert recomputed["finding_comment_ids"] == [702]
    assert recomputed["review_thread_ids"] == ["thread-702"]
    assert recomputed["follow_up_issue_numbers"] == [114]


def test_run_review_verifier_fetches_lazy_threads_for_valid_p2_follow_up() -> None:
    match, thread_calls = run_valid_p2_review_verifier()
    assert thread_calls == [("Oteryn/Test", 7, "test")]
    assert match["review_outcome"] == "ACCEPTED_WITH_FOLLOW_UP"
    assert match["p2_review_id"] == 701
    assert match["finding_comment_ids"] == [702]
    assert match["review_thread_ids"] == ["thread-702"]
    assert match["follow_up_issue_numbers"] == [114]


def test_run_review_verifier_rejects_unresolved_p2_follow_up() -> None:
    expect_review_failure(
        lambda: run_valid_p2_review_verifier(review_thread=p2_evidence._p2_thread(resolved=False)),
        "review verifier accepted an unresolved P2 follow-up",
    )


def test_run_review_verifier_rejects_closed_p2_follow_up_issue() -> None:
    closed_issue = p2_evidence._tracker_issue()
    closed_issue["state"] = "closed"
    expect_review_failure(
        lambda: run_valid_p2_review_verifier(tracker_issue=closed_issue),
        "review verifier accepted a closed P2 follow-up issue",
    )


def test_run_review_verifier_rejects_cross_repository_p2_follow_up_issue() -> None:
    foreign_issue = p2_evidence._tracker_issue()
    foreign_issue["repository_url"] = "https://api.github.com/repos/Oteryn/Other"
    expect_review_failure(
        lambda: run_valid_p2_review_verifier(tracker_issue=foreign_issue),
        "review verifier accepted a cross-repository P2 follow-up issue",
    )


def test_run_review_verifier_rejects_duplicate_p2_follow_up_disposition() -> None:
    duplicate_thread = p2_evidence._p2_thread()
    duplicate_reply = deepcopy(duplicate_thread["comments"]["nodes"][1])
    duplicate_reply["fullDatabaseId"] = "704"
    duplicate_thread["comments"]["nodes"].append(duplicate_reply)
    expect_review_failure(
        lambda: run_valid_p2_review_verifier(review_thread=duplicate_thread),
        "review verifier accepted duplicate P2 follow-up dispositions",
    )


def test_draft_risk_review_is_explicitly_deferred_and_source_free() -> None:
    draft = pull_request()
    draft["draft"] = True
    facts = issuer.validate_pr_facts(
        repository(), draft, expected_repository=REPOSITORY,
        expected_repository_id=REPOSITORY_ID, expected_pr_id=PR_ID, expected_pr_number=17,
        expected_base=BASE, expected_head=HEAD, expected_draft=True,
    )
    envelope = issuer.make_envelope(
        facts=facts,
        classification={
            "tier": "R2", "review_fingerprint": "c" * 64,
            "reviewer_class": "deep",
        },
        policy_id="oteryn-ai-review-risk-v1",
        policy_sha256="d" * 64,
        classifier_revision="sha256:" + "e" * 64,
        issuer={
            "workflow_ref": "Oteryn/Oteryn/.github/workflows/governance-ai-review.yml@refs/heads/main",
            "workflow_sha": "f" * 40,
            "workflow_execution_sha": "f" * 40,
            "workflow_run_id": 100,
            "workflow_run_attempt": 2,
            "workflow_job_id": 101,
            "check_run_id": 102,
            "check_suite_id": 103,
        },
        evidence_status="deferred",
        evidence_sources=[],
        review_outcome=None,
        p2_review_id=None,
        finding_comment_ids=None,
        review_thread_ids=None,
        follow_up_issue_numbers=None,
        issued_at="2026-08-30T09:30:00Z",
    )
    assert envelope["review"]["evidence_status"] == "deferred"
    assert envelope["review_evidence"] == []
    try:
        issuer.make_envelope(
            facts=facts,
            classification={
                "tier": "R2", "review_fingerprint": "c" * 64,
                "reviewer_class": "deep",
            },
            policy_id="oteryn-ai-review-risk-v1",
            policy_sha256="d" * 64,
            classifier_revision="sha256:" + "e" * 64,
            issuer={
                "workflow_ref": "Oteryn/Oteryn/.github/workflows/governance-ai-review.yml@refs/heads/main",
                "workflow_sha": "f" * 40,
                "workflow_execution_sha": "f" * 40,
                "workflow_run_id": 100,
                "workflow_run_attempt": 2,
                "workflow_job_id": 101,
                "check_run_id": 102,
                "check_suite_id": 103,
            },
            evidence_status="verified",
            evidence_sources=[],
            review_outcome=None,
            p2_review_id=None,
            finding_comment_ids=None,
            review_thread_ids=None,
            follow_up_issue_numbers=None,
            issued_at="2026-08-30T09:30:00Z",
        )
    except issuer.IssuanceError:
        pass
    else:
        raise AssertionError("draft R2 envelope was permitted to require review evidence")


def test_verified_attestation_result_must_bind_the_exact_canonical_envelope() -> None:
    payload = issuer.canonical_json_bytes({"schema_version": 1, "value": "trusted"})
    result = verified_attestation_result(payload)
    issuer.validate_attestation_result(
        result, payload, repository=REPOSITORY, repository_id=REPOSITORY_ID,
        base=BASE, workflow_run_id=RUN_ID, workflow_run_attempt=RUN_ATTEMPT,
    )
    result[0]["verificationResult"]["statement"]["subject"][0]["digest"]["sha256"] = "0" * 64
    try:
        issuer.validate_attestation_result(
            result, payload, repository=REPOSITORY, repository_id=REPOSITORY_ID,
            base=BASE, workflow_run_id=RUN_ID, workflow_run_attempt=RUN_ATTEMPT,
        )
    except issuer.IssuanceError:
        pass
    else:
        raise AssertionError("attestation with a mismatched subject digest was accepted")


def test_attestation_certificate_must_bind_trusted_workflow_source_and_invocation() -> None:
    payload = issuer.canonical_json_bytes({"schema_version": 1, "value": "trusted"})
    issuer.validate_attestation_result(
        verified_attestation_result(payload), payload,
        repository=REPOSITORY, repository_id=REPOSITORY_ID, base=BASE,
        workflow_run_id=RUN_ID, workflow_run_attempt=RUN_ATTEMPT,
    )
    for field, original in certificate().items():
        tampered = certificate()
        tampered[field] = HEAD if original == BASE else f"tampered:{field}"
        try:
            issuer.validate_attestation_result(
                verified_attestation_result(payload, tampered), payload,
                repository=REPOSITORY, repository_id=REPOSITORY_ID, base=BASE,
                workflow_run_id=RUN_ID, workflow_run_attempt=RUN_ATTEMPT,
            )
        except issuer.IssuanceError:
            pass
        else:
            raise AssertionError(f"certificate tamper for {field} was accepted")


def test_in_job_context_is_the_only_workflow_provenance_w_equals_t_proof() -> None:
    trusted_ref = f"{REPOSITORY}/.github/workflows/governance-ai-review.yml@refs/heads/main"
    issuer.validate_in_job_workflow_context(
        repository=REPOSITORY, base=BASE, workflow_ref=trusted_ref,
        workflow_sha=BASE, workflow_execution_sha=BASE,
    )
    for key, value in {
        "workflow_ref": trusted_ref.replace("main", "feature"),
        "workflow_sha": HEAD,
        "workflow_execution_sha": HEAD,
    }.items():
        context = {
            "repository": REPOSITORY, "base": BASE, "workflow_ref": trusted_ref,
            "workflow_sha": BASE, "workflow_execution_sha": BASE,
        }
        context[key] = value
        try:
            issuer.validate_in_job_workflow_context(**context)
        except issuer.IssuanceError:
            pass
        else:
            raise AssertionError(f"untrusted in-job {key} was accepted")


def test_foreign_or_mismatched_pr_facts_fail_closed() -> None:
    for mutate in (
        lambda value: value["head"]["repo"].update({"id": 9, "full_name": "other/fork", "fork": True}),
        lambda value: value.update({"id": 9}),
        lambda value: value["base"].update({"ref": "release"}),
        lambda value: value.update({"state": "closed"}),
        lambda value: value["head"].update({"sha": "c" * 40}),
    ):
        candidate = pull_request()
        mutate(candidate)
        try:
            issuer.validate_pr_facts(
                repository(), candidate, expected_repository=REPOSITORY,
                expected_repository_id=REPOSITORY_ID, expected_pr_id=PR_ID, expected_pr_number=17,
                expected_base=BASE, expected_head=HEAD,
            )
        except issuer.IssuanceError:
            pass
        else:
            raise AssertionError("untrusted or inconsistent pull-request facts were accepted")


def test_server_draft_state_must_match_the_event_bound_draft_input() -> None:
    draft = pull_request()
    draft["draft"] = True
    try:
        issuer.validate_pr_facts(
            repository(), draft, expected_repository=REPOSITORY,
            expected_repository_id=REPOSITORY_ID, expected_pr_id=PR_ID, expected_pr_number=17,
            expected_base=BASE, expected_head=HEAD, expected_draft=False,
        )
    except issuer.IssuanceError:
        pass
    else:
        raise AssertionError("server Draft state differing from the event input was accepted")


def test_pull_request_target_run_job_and_check_chain_bind_candidate_head() -> None:
    run = workflow_run()
    jobs = workflow_jobs()
    result = issuer.validate_run_job_facts(
        run, jobs, expected_repository=REPOSITORY, expected_repository_id=REPOSITORY_ID,
        expected_run_id=RUN_ID, expected_run_attempt=RUN_ATTEMPT, expected_base=BASE,
        expected_head=HEAD, expected_pr_id=PR_ID, expected_pr_number=17, expected_default_branch="main",
        expected_job_name="ai-review-gate",
    )
    assert result == {
        "workflow_run_id": RUN_ID,
        "workflow_run_attempt": RUN_ATTEMPT,
        "workflow_job_id": JOB_ID,
        "check_run_id": CHECK_RUN_ID,
        "check_suite_id": CHECK_SUITE_ID,
    }
    issuer.validate_check_chain(
        check_run(), check_suite(), expected_repository=REPOSITORY,
        expected_repository_id=REPOSITORY_ID, expected_head=HEAD,
        expected_check_run_id=CHECK_RUN_ID, expected_check_suite_id=CHECK_SUITE_ID,
        expected_job_name="ai-review-gate",
    )
    mutations = (
        lambda value: value.update({"head_sha": BASE}),
        lambda value: value.update({"run_attempt": 9}),
        lambda value: value.update({"pull_requests": []}),
        lambda value: value.update({"pull_requests": [value["pull_requests"][0], deepcopy(value["pull_requests"][0])]}),
        lambda value: value["pull_requests"][0].update({"id": 9}),
        lambda value: value["pull_requests"][0]["base"].update({"sha": HEAD}),
        lambda value: value["pull_requests"][0]["head"]["repo"].update({"id": 9}),
        lambda value: value["head_repository"].update({"fork": True}),
    )
    for mutate in mutations:
        candidate = workflow_run()
        mutate(candidate)
        try:
            issuer.validate_run_job_facts(
                candidate, jobs, expected_repository=REPOSITORY,
                expected_repository_id=REPOSITORY_ID, expected_run_id=RUN_ID,
                expected_run_attempt=RUN_ATTEMPT, expected_base=BASE,
                expected_head=HEAD, expected_pr_id=PR_ID, expected_pr_number=17, expected_default_branch="main",
                expected_job_name="ai-review-gate",
            )
        except issuer.IssuanceError:
            pass
        else:
            raise AssertionError("malformed PTR run-to-PR binding was accepted")
    for mutate in (
        lambda value: value.update({"head_sha": BASE}),
        lambda value: value["app"].update({"id": 1}),
        lambda value: value["check_suite"].update({"id": 999}),
    ):
        candidate = check_run()
        mutate(candidate)
        try:
            issuer.validate_check_chain(
                candidate, check_suite(), expected_repository=REPOSITORY,
                expected_repository_id=REPOSITORY_ID, expected_head=HEAD,
                expected_check_run_id=CHECK_RUN_ID, expected_check_suite_id=CHECK_SUITE_ID,
                expected_job_name="ai-review-gate",
            )
        except issuer.IssuanceError:
            pass
        else:
            raise AssertionError("malformed job/check chain was accepted")
    for mutate in (
        lambda value: value[0].update({"run_id": 9}),
        lambda value: value[0].update({"run_attempt": 9}),
        lambda value: value[0].update({"head_sha": BASE}),
        lambda value: value[0].update({"check_run_url": "https://api.github.com/repos/other/repo/check-runs/102"}),
    ):
        candidate = workflow_jobs()
        mutate(candidate)
        try:
            issuer.validate_run_job_facts(
                run, candidate, expected_repository=REPOSITORY,
                expected_repository_id=REPOSITORY_ID, expected_run_id=RUN_ID,
                expected_run_attempt=RUN_ATTEMPT, expected_base=BASE,
                expected_head=HEAD, expected_pr_id=PR_ID, expected_pr_number=17, expected_default_branch="main",
                expected_job_name="ai-review-gate",
            )
        except issuer.IssuanceError:
            pass
        else:
            raise AssertionError("malformed workflow job chain was accepted")
    for mutate in (
        lambda value: value.update({"head_sha": BASE}),
        lambda value: value["app"].update({"slug": "other"}),
        lambda value: value["repository"].update({"id": 9}),
    ):
        candidate = check_suite()
        mutate(candidate)
        try:
            issuer.validate_check_chain(
                check_run(), candidate, expected_repository=REPOSITORY,
                expected_repository_id=REPOSITORY_ID, expected_head=HEAD,
                expected_check_run_id=CHECK_RUN_ID, expected_check_suite_id=CHECK_SUITE_ID,
                expected_job_name="ai-review-gate",
            )
        except issuer.IssuanceError:
            pass
        else:
            raise AssertionError("malformed check-suite chain was accepted")
    try:
        issuer.validate_run_job_facts(
            run, [*jobs, deepcopy(jobs[0])], expected_repository=REPOSITORY,
            expected_repository_id=REPOSITORY_ID, expected_run_id=RUN_ID,
            expected_run_attempt=RUN_ATTEMPT, expected_base=BASE,
            expected_head=HEAD, expected_pr_id=PR_ID, expected_pr_number=17, expected_default_branch="main",
            expected_job_name="ai-review-gate",
        )
    except issuer.IssuanceError:
        pass
    else:
        raise AssertionError("ambiguous job identity was accepted")


def test_read_run_facts_extracts_bounded_actions_jobs_envelope_and_rejects_count_ambiguity() -> None:
    """A GitHub Actions jobs envelope is authoritative only when its bounded count agrees."""
    root_url = f"https://api.github.com/repos/{REPOSITORY}/actions/runs/{RUN_ID}"
    jobs_url = f"{root_url}/jobs?per_page=100&page=1"
    responses = {
        root_url: workflow_run(),
        jobs_url: {"total_count": 1, "jobs": workflow_jobs()},
        f"https://api.github.com/repos/{REPOSITORY}/check-runs/{CHECK_RUN_ID}": check_run(),
        f"https://api.github.com/repos/{REPOSITORY}/check-suites/{CHECK_SUITE_ID}": check_suite(),
    }

    class Response:
        def __init__(self, value: object) -> None:
            self.value = value

        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self, *_args: object) -> str:
            return json.dumps(self.value)

    original_urlopen = issuer.urllib.request.urlopen
    calls: list[str] = []

    def urlopen(request: object, *, timeout: int) -> Response:
        url = request.full_url
        calls.append(url)
        return Response(responses[url])

    try:
        issuer.urllib.request.urlopen = urlopen
        facts = issuer._read_run_facts(
            repository=REPOSITORY, repository_id=REPOSITORY_ID, pr_id=PR_ID, pr_number=17,
            base=BASE, head=HEAD, default_branch="main", workflow_run_id=RUN_ID,
            workflow_run_attempt=RUN_ATTEMPT, workflow_job="ai-review-gate", token="test",
        )
        assert facts == {
            "workflow_run_id": RUN_ID, "workflow_run_attempt": RUN_ATTEMPT,
            "workflow_job_id": JOB_ID, "check_run_id": CHECK_RUN_ID,
            "check_suite_id": CHECK_SUITE_ID,
        }
        assert calls == [
            root_url, jobs_url,
            f"https://api.github.com/repos/{REPOSITORY}/check-runs/{CHECK_RUN_ID}",
            f"https://api.github.com/repos/{REPOSITORY}/check-suites/{CHECK_SUITE_ID}",
        ]
        responses[jobs_url] = {"total_count": 2, "jobs": workflow_jobs()}
        try:
            issuer._read_run_facts(
                repository=REPOSITORY, repository_id=REPOSITORY_ID, pr_id=PR_ID, pr_number=17,
                base=BASE, head=HEAD, default_branch="main", workflow_run_id=RUN_ID,
                workflow_run_attempt=RUN_ATTEMPT, workflow_job="ai-review-gate", token="test",
            )
        except issuer.IssuanceError:
            pass
        else:
            raise AssertionError("jobs envelope with an ambiguous total_count was accepted")
    finally:
        issuer.urllib.request.urlopen = original_urlopen


def test_recomputed_semantic_claims_reject_every_single_claim_tamper() -> None:
    source = {
        "kind": "pull_request_review", "object_id": 201, "reviewed_head": BASE,
        "actor_login": "reviewer[bot]", "actor_id": 202,
        "app_slug": "chatgpt-codex-connector", "app_id": None, "body_sha256": "1" * 64,
    }
    expected = {
        "policy": {"id": "oteryn-ai-review-risk-v1", "sha256": "d" * 64},
        "classifier": {"revision": "sha256:" + "e" * 64},
        "review": {
            "tier": "R2", "fingerprint": "c" * 64, "reviewer_class": "deep",
            "evidence_status": "verified",
        },
        "review_evidence": [source],
        "review_outcome": "PASS",
    }
    issuer.validate_semantic_claims(expected, expected)
    tampered_claims = {
        "policy.id": "another-policy",
        "policy.sha256": "0" * 64,
        "classifier.revision": "sha256:" + "0" * 64,
        "review.tier": "R1",
        "review.fingerprint": "0" * 64,
        "review.reviewer_class": "fast",
        "review.evidence_status": "deferred",
        "review_evidence": [],
    }
    for path, value in tampered_claims.items():
        candidate = deepcopy(expected)
        target = candidate
        keys = path.split(".")
        for key in keys[:-1]:
            target = target[key]
        target[keys[-1]] = value
        try:
            issuer.validate_semantic_claims(candidate, expected)
        except issuer.IssuanceError:
            pass
        else:
            raise AssertionError(f"attested semantic claim {path} was not recomputed and compared")
    stale_source = deepcopy(expected)
    stale_source["review_evidence"][0]["body_sha256"] = "0" * 64
    try:
        issuer.validate_semantic_claims(stale_source, expected)
    except issuer.IssuanceError:
        pass
    else:
        raise AssertionError("stale normalized review source was accepted")


def test_semantic_recompute_accepts_policy_authorized_clean_merge_up_source() -> None:
    root = Path(__file__).resolve().parents[2]
    facts = issuer.validate_pr_facts(
        repository(), pull_request(), expected_repository=REPOSITORY,
        expected_repository_id=REPOSITORY_ID, expected_pr_id=PR_ID, expected_pr_number=17,
        expected_base=BASE, expected_head=HEAD,
    )
    source = {
        "kind": "pull_request_review", "object_id": 201, "reviewed_head": BASE,
        "actor_login": "reviewer[bot]", "actor_id": 202,
        "app_slug": "chatgpt-codex-connector", "app_id": None, "body_sha256": "1" * 64,
    }
    originals = (
        issuer.risk_policy.load_policy, issuer.risk_policy.evaluate,
        issuer._run_review_verifier, issuer._material_sources,
    )
    try:
        issuer.risk_policy.load_policy = lambda _path: {"policy_id": "oteryn-ai-review-risk-v1"}
        issuer.risk_policy.evaluate = lambda *_args: {
            "tier": "R2", "review_fingerprint": "c" * 64, "reviewer_class": "deep",
        }
        issuer._run_review_verifier = lambda **kwargs: {
            "reviewed_head": BASE, "review_source_url": "ignored", "review_source_kind": "ignored",
            "review_source_commit_id": BASE,
        }
        issuer._material_sources = lambda *_args, **_kwargs: [source]
        recomputed = issuer.recompute_semantic_claims(
            facts=facts, repository=REPOSITORY, pr_number=17, base=BASE, head=HEAD,
            bare_git_dir=root, policy_path=root / "ecosystem/ai-review-policy.json",
            classifier_path=root / "tools/governance/ai_review_policy.py", token="test",
        )
    finally:
        (
            issuer.risk_policy.load_policy, issuer.risk_policy.evaluate,
            issuer._run_review_verifier, issuer._material_sources,
        ) = originals
    assert recomputed["review_evidence"] == [source]
    assert recomputed["review_evidence"][0]["reviewed_head"] == BASE
    assert recomputed["review_outcome"] == "PASS"
    assert BASE != HEAD


def test_semantic_claims_fail_closed_on_r0_draft_and_ready_source_cardinality() -> None:
    source = {
        "kind": "pull_request_review", "object_id": 201, "reviewed_head": HEAD,
        "actor_login": "reviewer[bot]", "actor_id": 202,
        "app_slug": "chatgpt-codex-connector", "app_id": None, "body_sha256": "1" * 64,
    }
    for review, expected_sources, tampered_sources, outcome in (
        ({"tier": "R0", "fingerprint": "c" * 64, "reviewer_class": None, "evidence_status": "not_required"}, [], [source], None),
        ({"tier": "R1", "fingerprint": "c" * 64, "reviewer_class": "fast", "evidence_status": "deferred"}, [], [source], None),
        ({"tier": "R2", "fingerprint": "c" * 64, "reviewer_class": "deep", "evidence_status": "verified"}, [source], [], "PASS"),
    ):
        expected = {
            "policy": {"id": "oteryn-ai-review-risk-v1", "sha256": "d" * 64},
            "classifier": {"revision": "sha256:" + "e" * 64},
            "review": review,
            "review_evidence": expected_sources,
        }
        if outcome is not None:
            expected["review_outcome"] = outcome
        candidate = deepcopy(expected)
        candidate["review_evidence"] = tampered_sources
        try:
            issuer.validate_semantic_claims(candidate, expected)
        except issuer.IssuanceError:
            pass
        else:
            raise AssertionError("semantic source cardinality did not fail closed")


def test_trusted_workflow_has_no_candidate_checkout_and_verifies_issued_attestation() -> None:
    root = Path(__file__).resolve().parents[2]
    workflow = (root / ".github/workflows/governance-ai-review.yml").read_text(encoding="utf-8")
    action = (root / ".github/actions/ai-review-gate/action.yml").read_text(encoding="utf-8")
    assert "pull_request_target:" in workflow
    assert "path: trusted" in workflow
    assert "path: candidate" not in workflow
    assert "Checkout candidate" not in workflow
    assert workflow.count("actions/checkout@") == 1
    assert "actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6" in workflow
    for permission in (
        "contents: read", "issues: read", "pull-requests: read", "actions: read", "checks: read",
        "id-token: write", "attestations: write", "artifact-metadata: write",
    ):
        assert permission in workflow
    assert "subject-path:" in workflow
    assert issuer.PREDICATE_TYPE in workflow
    assert "gh attestation verify" in workflow
    assert "--deny-self-hosted-runners" in workflow
    assert "--source-ref refs/heads/main" in workflow
    assert "--source-digest \"$BASE_SHA\"" in workflow
    assert "trusted_review_attestation.py verify" in workflow
    assert "candidate.git" in action
    assert "git init --bare" in action
    assert "uses: ./trusted/.github/actions/ai-review-gate" in workflow
    assert "repo-root:" not in action
    assert "pr-id: ${{ github.event.pull_request.id }}" in workflow
    assert "INPUT_PR_ID: ${{ inputs.pr-id }}" in action
    assert "WORKFLOW_EXECUTION_SHA: ${{ github.sha }}" in action
    assert "WORKFLOW_RUN_ATTEMPT: ${{ github.run_attempt }}" in action


def test_action_passes_runtime_github_output_to_the_issuer() -> None:
    """The issuer must receive the runner output file, not an unavailable expression context."""
    action = (Path(__file__).resolve().parents[2] / ".github/actions/ai-review-gate/action.yml").read_text(encoding="utf-8")
    issue_step = re.search(
        r"(?ms)^    - id: issue\n(?P<body>.*?)(?=^    - id:|\Z)", action,
    )
    assert issue_step is not None
    assert '--github-output "$GITHUB_OUTPUT"' in issue_step.group("body")
    assert "GITHUB_OUTPUT_PATH:" not in issue_step.group("body")
    assert "${{ github.output }}" not in issue_step.group("body")


def _candidate_fetch_run() -> str:
    action = (Path(__file__).resolve().parents[2] / ".github/actions/ai-review-gate/action.yml").read_text(encoding="utf-8")
    step = re.search(
        r"(?ms)^    - name: Fetch candidate as inert bare Git objects\n(?P<body>.*?)(?=^    - (?:id:|name:)|\Z)",
        action,
    )
    assert step is not None
    run = re.search(r"(?ms)^      run: \|\n(?P<script>(?:        .*\n?)*)\Z", step.group("body"))
    assert run is not None
    return textwrap.dedent(run.group("script"))


def _run_candidate_fetch_with_fake_git(
    *, fail_fetch: bool = False, reject_config_env: bool = False, require_auth: bool = True,
) -> tuple[subprocess.CompletedProcess[str], str, str, list[str], str, bool]:
    """Execute the actual action shell body against fake Git without recording a secret."""
    secret = "token-for-inert-fetch-test"
    derived = base64.b64encode(f"x-access-token:{secret}".encode("utf-8")).decode("ascii")
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        bin_dir = root / "bin"
        bin_dir.mkdir()
        argv_log = root / "git-argv.log"
        event_log = root / "git-events.log"
        lfs_log = root / "git-lfs.log"
        fake_git = bin_dir / "git"
        fake_git.write_text(
            """#!/usr/bin/env bash
set -euo pipefail
printf '%s\\n' '---' >> "$FAKE_GIT_ARGV_LOG"
printf '%s\\n' "$@" >> "$FAKE_GIT_ARGV_LOG"
is_fetch=0
has_config_env=0
for arg in "$@"; do
  [[ "$arg" == fetch ]] && is_fetch=1
  [[ "$arg" == lfs ]] && touch "$FAKE_GIT_LFS_LOG"
  [[ "$arg" == --config-env=http.https://github.com/.extraheader=OTERYN_GIT_AUTH_HEADER ]] && has_config_env=1
done
if [[ "$is_fetch" -eq 1 ]]; then
  if [[ "${FAKE_GIT_REQUIRE_AUTH:-0}" -eq 1 ]]; then
    [[ -n "${OTERYN_GIT_AUTH_HEADER:-}" ]] || exit 41
    [[ "$has_config_env" -eq 1 ]] || exit 42
    [[ "${GIT_TERMINAL_PROMPT:-}" == 0 ]] || exit 43
    [[ "${GIT_CONFIG_NOSYSTEM:-}" == 1 ]] || exit 44
    [[ "${GIT_CONFIG_GLOBAL:-}" == /dev/null ]] || exit 45
    [[ "${GIT_LFS_SKIP_SMUDGE:-}" == 1 ]] || exit 46
  fi
  printf '%s\\n' 'fetch:auth-present' >> "$FAKE_GIT_EVENT_LOG"
  [[ "${FAKE_GIT_REJECT_CONFIG_ENV:-0}" -eq 1 && "$has_config_env" -eq 1 ]] && exit 77
  [[ "${FAKE_GIT_FAIL_FETCH:-0}" -eq 1 ]] && exit 78
else
  [[ -z "${OTERYN_GIT_AUTH_HEADER:-}" ]] || exit 79
  printf '%s\\n' 'nonfetch:auth-absent' >> "$FAKE_GIT_EVENT_LOG"
fi
if [[ "${1:-}" == init && "${2:-}" == --bare ]]; then
  mkdir -p "$3"
fi
""",
            encoding="utf-8",
        )
        fake_git.chmod(0o755)
        fake_lfs = bin_dir / "git-lfs"
        fake_lfs.write_text('#!/usr/bin/env bash\ntouch "$FAKE_GIT_LFS_LOG"\nexit 99\n', encoding="utf-8")
        fake_lfs.chmod(0o755)
        env = dict(os.environ)
        env.update({
            "PATH": f"{bin_dir}:{env['PATH']}",
            "GH_TOKEN": secret,
            "REPOSITORY": REPOSITORY,
            "BASE_SHA": BASE,
            "HEAD_SHA": HEAD,
            "RUNNER_TEMP": str(root),
            "FAKE_GIT_ARGV_LOG": str(argv_log),
            "FAKE_GIT_EVENT_LOG": str(event_log),
            "FAKE_GIT_LFS_LOG": str(lfs_log),
            "FAKE_GIT_FAIL_FETCH": "1" if fail_fetch else "0",
            "FAKE_GIT_REJECT_CONFIG_ENV": "1" if reject_config_env else "0",
            "FAKE_GIT_REQUIRE_AUTH": "1" if require_auth else "0",
        })
        completed = subprocess.run(
            ["bash", "-c", _candidate_fetch_run()], cwd=root, env=env,
            text=True, capture_output=True, check=False,
        )
        contents = [path.read_text(encoding="utf-8") for path in root.rglob("*") if path.is_file()]
        return (
            completed, argv_log.read_text(encoding="utf-8"), event_log.read_text(encoding="utf-8"),
            contents, derived, lfs_log.exists(),
        )


def test_candidate_fetch_uses_ephemeral_git_config_without_secret_argv_or_persistence() -> None:
    """A fetch must send Basic auth only through config-env and leave no token material behind."""
    completed, argv, events, contents, derived, lfs_invoked = _run_candidate_fetch_with_fake_git()
    assert completed.returncode == 0, completed.stderr
    action = (Path(__file__).resolve().parents[2] / ".github/actions/ai-review-gate/action.yml").read_text(encoding="utf-8")
    assert re.search(
        r"(?ms)^    - name: Fetch candidate as inert bare Git objects\n.*?^        GH_TOKEN: \$\{\{ inputs\.github-token \}\}",
        action,
    )
    assert "--config-env=http.https://github.com/.extraheader=OTERYN_GIT_AUTH_HEADER" in argv
    assert "credential.helper=" in argv
    assert "http.sslVerify=true" in argv
    assert "http.followRedirects=false" in argv
    assert "protocol.allow=never" in argv
    assert "protocol.https.allow=always" in argv
    assert "--no-recurse-submodules" in argv
    assert f"https://github.com/{REPOSITORY}.git" in argv
    assert f"http://github.com/{REPOSITORY}.git" not in argv
    assert "fetch:auth-present" in events
    assert events.count("nonfetch:auth-absent") >= 3
    assert "token-for-inert-fetch-test" not in argv
    assert derived not in argv
    assert f"Authorization: Basic {derived}" not in argv
    assert all("token-for-inert-fetch-test" not in value for value in contents)
    assert all(derived not in value for value in contents)
    assert all(f"Authorization: Basic {derived}" not in value for value in contents)
    assert not lfs_invoked


def test_candidate_fetch_fails_closed_when_config_env_is_unsupported() -> None:
    """Git implementations that reject config-env must not fall back to a helper or URL token."""
    completed, argv, events, contents, derived, _lfs_invoked = _run_candidate_fetch_with_fake_git(
        reject_config_env=True, require_auth=False,
    )
    assert completed.returncode != 0
    assert "--config-env=http.https://github.com/.extraheader=OTERYN_GIT_AUTH_HEADER" in argv
    assert "fetch:auth-present" in events
    assert all("token-for-inert-fetch-test" not in value for value in contents)
    assert all(derived not in value for value in contents)


def test_candidate_fetch_failure_leaves_no_secret_material_and_has_exit_cleanup() -> None:
    """Both fetch failure and shell exit keep the token/header out of persistent state."""
    completed, argv, events, contents, derived, _lfs_invoked = _run_candidate_fetch_with_fake_git(fail_fetch=True)
    assert completed.returncode != 0
    assert "fetch:auth-present" in events
    assert "token-for-inert-fetch-test" not in argv
    assert derived not in argv
    assert all("token-for-inert-fetch-test" not in value for value in contents)
    assert all(derived not in value for value in contents)
    fetch = _candidate_fetch_run()
    assert "set +x" in fetch
    assert "cleanup() {" in fetch
    assert "unset GH_TOKEN OTERYN_GIT_AUTH_HEADER auth_b64" in fetch
    assert "trap cleanup EXIT" in fetch
    assert "unset OTERYN_GIT_AUTH_HEADER" in fetch


def test_ai_review_gate_job_identity_is_static_and_rejects_renamed_or_matrix_rest_jobs() -> None:
    """The job name passed as github.job has one static REST identity; P2 defer never widens it."""
    workflow = (Path(__file__).resolve().parents[2] / ".github/workflows/governance-ai-review.yml").read_text(encoding="utf-8")
    action = (Path(__file__).resolve().parents[2] / ".github/actions/ai-review-gate/action.yml").read_text(encoding="utf-8")
    assert workflow.count("\n  ai-review-gate:\n") == 1
    job = re.search(r"(?ms)^  ai-review-gate:\n(?P<body>.*?)(?=^  [a-zA-Z][^\n]*:\n|\Z)", workflow)
    assert job is not None
    assert re.search(r"^    name: ai-review-gate$", job.group("body"), flags=re.MULTILINE)
    assert "strategy:" not in job.group("body")
    assert "matrix" not in job.group("body")
    assert "WORKFLOW_JOB: ${{ github.job }}" in action
    for name in ("renamed-ai-review-gate", "ai-review-gate (ubuntu-latest)", "${{ matrix.job }}"):
        jobs = workflow_jobs()
        jobs[0]["name"] = name
        try:
            issuer.validate_run_job_facts(
                workflow_run(), jobs, expected_repository=REPOSITORY, expected_repository_id=REPOSITORY_ID,
                expected_run_id=RUN_ID, expected_run_attempt=RUN_ATTEMPT, expected_base=BASE,
                expected_head=HEAD, expected_pr_id=PR_ID, expected_pr_number=17,
                expected_default_branch="main", expected_job_name="ai-review-gate",
            )
        except issuer.IssuanceError:
            pass
        else:
            raise AssertionError(f"non-static REST job name {name!r} was accepted")


def test_meta_gate_runs_trusted_attestation_regression_on_every_invocation() -> None:
    """Removal of the attestation suite from the required meta-gate must fail closed."""
    ci_workflow = (Path(__file__).resolve().parents[2] / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    step = re.search(
        r"(?ms)^      - name: Validate AI review risk policy\n(?P<body>.*?)(?=^      - name:|\Z)",
        ci_workflow,
    )
    assert step is not None
    assert "\n        if:" not in step.group("body")
    assert "python3 tools/governance/test_trusted_review_attestation.py" in step.group("body")


def main() -> int:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print(f"trusted review attestation tests PASS: {len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
