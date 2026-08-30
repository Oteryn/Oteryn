#!/usr/bin/env python3
"""Regression tests for trusted-base review-attestation issuance."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import trusted_review_attestation as issuer  # noqa: E402


REPOSITORY = "Oteryn/Oteryn"
REPOSITORY_ID = 1338152366
BASE = "a" * 40
HEAD = "b" * 40


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
        expected_repository_id=REPOSITORY_ID, expected_pr_number=17,
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
            "workflow_run_id": 100,
            "workflow_job_id": 101,
            "check_run_id": 102,
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
        expected_repository_id=REPOSITORY_ID, expected_pr_number=17,
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
            "workflow_run_id": 100,
            "workflow_job_id": 101,
            "check_run_id": 102,
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
                "workflow_run_id": 100,
                "workflow_job_id": 101,
                "check_run_id": 102,
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
    statement = {
        "predicateType": issuer.PREDICATE_TYPE,
        "predicate": json.loads(payload),
        "subject": [{"name": "oteryn-trusted-review-envelope.json", "digest": {
            "sha256": hashlib.sha256(payload).hexdigest(),
        }}],
    }
    issuer.validate_attestation_result(
        [{"verificationResult": {"statement": statement}}], payload,
    )
    statement["subject"][0]["digest"]["sha256"] = "0" * 64
    try:
        issuer.validate_attestation_result(
            [{"verificationResult": {"statement": statement}}], payload,
        )
    except issuer.IssuanceError:
        pass
    else:
        raise AssertionError("attestation with a mismatched subject digest was accepted")


def test_foreign_or_mismatched_pr_facts_fail_closed() -> None:
    for mutate in (
        lambda value: value["head"]["repo"].update({"id": 9, "full_name": "other/fork", "fork": True}),
        lambda value: value["base"].update({"ref": "release"}),
        lambda value: value.update({"state": "closed"}),
        lambda value: value["head"].update({"sha": "c" * 40}),
    ):
        candidate = pull_request()
        mutate(candidate)
        try:
            issuer.validate_pr_facts(
                repository(), candidate, expected_repository=REPOSITORY,
                expected_repository_id=REPOSITORY_ID, expected_pr_number=17,
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
            expected_repository_id=REPOSITORY_ID, expected_pr_number=17,
            expected_base=BASE, expected_head=HEAD, expected_draft=False,
        )
    except issuer.IssuanceError:
        pass
    else:
        raise AssertionError("server Draft state differing from the event input was accepted")


def test_workflow_job_and_check_coordinates_are_unique_and_typed() -> None:
    run = {
        "id": 100,
        "event": "pull_request_target",
        "head_sha": BASE,
        "repository": {"id": REPOSITORY_ID, "full_name": REPOSITORY},
    }
    jobs = [{
        "id": 101,
        "name": "ai-review-gate",
        "check_run_url": f"https://api.github.com/repos/{REPOSITORY}/check-runs/102",
    }]
    result = issuer.validate_run_job_facts(
        run, jobs, expected_repository=REPOSITORY, expected_repository_id=REPOSITORY_ID,
        expected_run_id=100, expected_base=BASE, expected_job_name="ai-review-gate",
    )
    assert result == {"workflow_run_id": 100, "workflow_job_id": 101, "check_run_id": 102}
    try:
        issuer.validate_run_job_facts(
            run, [*jobs, dict(jobs[0])], expected_repository=REPOSITORY,
            expected_repository_id=REPOSITORY_ID, expected_run_id=100,
            expected_base=BASE, expected_job_name="ai-review-gate",
        )
    except issuer.IssuanceError:
        pass
    else:
        raise AssertionError("ambiguous job identity was accepted")


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
        "contents: read", "issues: read", "pull-requests: read", "actions: read",
        "id-token: write", "attestations: write", "artifact-metadata: write",
    ):
        assert permission in workflow
    assert "subject-path:" in workflow
    assert issuer.PREDICATE_TYPE in workflow
    assert "gh attestation verify" in workflow
    assert "--deny-self-hosted-runners" in workflow
    assert "trusted_review_attestation.py verify" in workflow
    assert "candidate.git" in action
    assert "git init --bare" in action
    assert "uses: ./trusted/.github/actions/ai-review-gate" in workflow
    assert "repo-root:" not in action


def main() -> int:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print(f"trusted review attestation tests PASS: {len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
