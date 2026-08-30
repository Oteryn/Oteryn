#!/usr/bin/env python3
"""Regression tests for trusted-base review-attestation issuance."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import trusted_review_attestation as issuer  # noqa: E402


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
    assert BASE != HEAD


def test_semantic_claims_fail_closed_on_r0_draft_and_ready_source_cardinality() -> None:
    source = {
        "kind": "pull_request_review", "object_id": 201, "reviewed_head": HEAD,
        "actor_login": "reviewer[bot]", "actor_id": 202,
        "app_slug": "chatgpt-codex-connector", "app_id": None, "body_sha256": "1" * 64,
    }
    for review, expected_sources, tampered_sources in (
        ({"tier": "R0", "fingerprint": "c" * 64, "reviewer_class": None, "evidence_status": "not_required"}, [], [source]),
        ({"tier": "R1", "fingerprint": "c" * 64, "reviewer_class": "fast", "evidence_status": "deferred"}, [], [source]),
        ({"tier": "R2", "fingerprint": "c" * 64, "reviewer_class": "deep", "evidence_status": "verified"}, [source], []),
    ):
        expected = {
            "policy": {"id": "oteryn-ai-review-risk-v1", "sha256": "d" * 64},
            "classifier": {"revision": "sha256:" + "e" * 64},
            "review": review,
            "review_evidence": expected_sources,
        }
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
