#!/usr/bin/env python3
"""Issue a trusted-base, GitHub-attestable review-evidence envelope.

This module deliberately reads candidate revisions only through a bare Git
object store.  It never checks out or executes pull-request controlled code.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any

import ai_review_policy as risk_policy
import verify_ai_review_evidence as review_evidence


PREDICATE_TYPE = "https://oteryn.dev/bounded-execution-evidence/v1"
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
CHECK_RUN_URL = re.compile(
    r"^https://api\.github\.com/repos/([^/]+/[^/]+)/check-runs/([1-9][0-9]*)$"
)
REVIEW_URL = re.compile(
    r"^https://github\.com/([^/]+/[^/]+)/pull/([1-9][0-9]*)#pullrequestreview-([1-9][0-9]*)$"
)
COMMENT_URL = re.compile(
    r"^https://github\.com/([^/]+/[^/]+)/pull/([1-9][0-9]*)#issuecomment-([1-9][0-9]*)$"
)
MAX_PAGES = 1000
WORKFLOW_PATH = ".github/workflows/governance-ai-review.yml"
WORKFLOW_BRANCH_REF = "refs/heads/main"
GITHUB_ACTIONS_APP_ID = 15368
GITHUB_ACTIONS_APP_SLUG = "github-actions"


class IssuanceError(RuntimeError):
    """A non-authoritative, malformed, or ambiguous GitHub fact was observed."""


def canonical_json_bytes(value: dict[str, Any]) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def envelope_identifier(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _require_full_sha(value: object, label: str) -> str:
    if not isinstance(value, str) or FULL_SHA.fullmatch(value) is None:
        raise IssuanceError(f"{label} must be an exact lowercase commit SHA")
    return value


def _require_positive_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise IssuanceError(f"{label} must be a positive integer")
    return value


def _require_bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise IssuanceError(f"{label} must be a boolean")
    return value


def _parse_draft(value: object) -> bool:
    if value == "true":
        return True
    if value == "false":
        return False
    raise IssuanceError("event-bound draft state must be the exact string true or false")


def _require_object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise IssuanceError(f"{label} must be a JSON object")
    return value


def validate_pr_facts(
    repository: dict[str, Any], pull_request: dict[str, Any], *, expected_repository: str,
    expected_repository_id: int, expected_pr_id: int, expected_pr_number: int,
    expected_base: str, expected_head: str,
    expected_draft: bool | None = None,
) -> dict[str, Any]:
    """Validate independently server-fetched repository and PR coordinates."""
    expected_repo_id = _require_positive_int(expected_repository_id, "expected repository id")
    if repository.get("full_name") != expected_repository or repository.get("id") != expected_repo_id:
        raise IssuanceError("server repository identity differs from trusted workflow context")
    if repository.get("archived") is not False or repository.get("disabled") is not False:
        raise IssuanceError("repository is archived or disabled")
    default_branch = repository.get("default_branch")
    if not isinstance(default_branch, str) or not default_branch:
        raise IssuanceError("repository default branch is missing")
    expected_pull_request_id = _require_positive_int(expected_pr_id, "expected PR id")
    if pull_request.get("id") != expected_pull_request_id:
        raise IssuanceError("server pull-request object id differs from trusted workflow context")
    if pull_request.get("number") != _require_positive_int(expected_pr_number, "expected PR number"):
        raise IssuanceError("server pull-request number differs from trusted workflow context")
    if pull_request.get("state") != "open":
        raise IssuanceError("pull request is not open")
    if expected_draft is not None:
        _require_bool(expected_draft, "expected draft state")
    draft = _require_bool(pull_request.get("draft"), "server pull-request draft state")
    if expected_draft is not None and draft != expected_draft:
        raise IssuanceError("server pull-request draft state differs from trusted workflow context")
    base = _require_object(pull_request.get("base"), "pull request base")
    head = _require_object(pull_request.get("head"), "pull request head")
    base_repo = _require_object(base.get("repo"), "pull request base repository")
    head_repo = _require_object(head.get("repo"), "pull request head repository")
    if (
        base.get("ref") != default_branch
        or base.get("sha") != _require_full_sha(expected_base, "expected base")
        or base_repo.get("id") != expected_repo_id
        or base_repo.get("full_name") != expected_repository
    ):
        raise IssuanceError("server pull-request base is not the exact default-branch base")
    if (
        head.get("sha") != _require_full_sha(expected_head, "expected head")
        or head_repo.get("id") != expected_repo_id
        or head_repo.get("full_name") != expected_repository
        or head_repo.get("fork") is not False
    ):
        raise IssuanceError("cross-repository, forked, or inconsistent PR head is rejected")
    return {
        "repository": {"id": expected_repo_id, "full_name": expected_repository},
        "pull_request": {
            "id": expected_pull_request_id,
            "number": expected_pr_number,
            "base": {"ref": default_branch, "sha": expected_base},
            "head": expected_head,
            "draft": draft,
        },
    }


def validate_commit_fact(commit: dict[str, Any], *, expected_sha: str, label: str) -> None:
    if commit.get("sha") != _require_full_sha(expected_sha, label):
        raise IssuanceError(f"server {label} commit identity differs from the PR")


def _validate_run_pr_repository(
    value: object, *, expected_repository: str, expected_repository_id: int, label: str,
) -> None:
    repository = _require_object(value, label)
    if (
        repository.get("id") != expected_repository_id
        or repository.get("name") != expected_repository.rsplit("/", 1)[1]
        or repository.get("url") != f"https://api.github.com/repos/{expected_repository}"
    ):
        raise IssuanceError(f"{label} differs from the expected repository identity")


def _validate_actions_app(value: object, label: str) -> None:
    app = _require_object(value, label)
    if app.get("id") != GITHUB_ACTIONS_APP_ID or app.get("slug") != GITHUB_ACTIONS_APP_SLUG:
        raise IssuanceError(f"{label} is not the GitHub Actions application")


def validate_run_job_facts(
    run: dict[str, Any], jobs: list[dict[str, Any]], *, expected_repository: str,
    expected_repository_id: int, expected_run_id: int, expected_run_attempt: int,
    expected_base: str, expected_head: str, expected_pr_id: int, expected_pr_number: int,
    expected_default_branch: str, expected_job_name: str,
) -> dict[str, int]:
    if run.get("id") != _require_positive_int(expected_run_id, "expected workflow run id"):
        raise IssuanceError("workflow-run identity differs from trusted context")
    if run.get("run_attempt") != _require_positive_int(expected_run_attempt, "expected workflow run attempt"):
        raise IssuanceError("workflow-run attempt differs from trusted context")
    run_repo = _require_object(run.get("repository"), "workflow-run repository")
    if run_repo.get("id") != expected_repository_id or run_repo.get("full_name") != expected_repository:
        raise IssuanceError("workflow-run repository differs from trusted repository")
    head_repository = _require_object(run.get("head_repository"), "workflow-run head repository")
    if (
        head_repository.get("id") != expected_repository_id
        or head_repository.get("full_name") != expected_repository
        or head_repository.get("fork") is not False
    ):
        raise IssuanceError("workflow-run head repository is foreign, forked, or malformed")
    if run.get("event") != "pull_request_target" or run.get("head_sha") != _require_full_sha(expected_head, "expected head"):
        raise IssuanceError("workflow run is not the expected pull_request_target candidate-head run")
    pull_requests = run.get("pull_requests")
    if not isinstance(pull_requests, list) or len(pull_requests) != 1:
        raise IssuanceError("workflow run must bind exactly one pull request")
    run_pull_request = _require_object(pull_requests[0], "workflow-run pull request")
    if run_pull_request.get("id") != _require_positive_int(expected_pr_id, "expected PR id"):
        raise IssuanceError("workflow-run pull request object id differs from trusted context")
    if run_pull_request.get("number") != _require_positive_int(expected_pr_number, "expected PR number"):
        raise IssuanceError("workflow-run pull request number differs from trusted context")
    run_base = _require_object(run_pull_request.get("base"), "workflow-run pull request base")
    run_head = _require_object(run_pull_request.get("head"), "workflow-run pull request head")
    if (
        run_base.get("ref") != expected_default_branch
        or run_base.get("sha") != _require_full_sha(expected_base, "expected base")
        or run_head.get("sha") != _require_full_sha(expected_head, "expected head")
    ):
        raise IssuanceError("workflow-run pull request base/head differs from trusted context")
    _validate_run_pr_repository(
        run_base.get("repo"), expected_repository=expected_repository,
        expected_repository_id=expected_repository_id, label="workflow-run pull-request base repository",
    )
    _validate_run_pr_repository(
        run_head.get("repo"), expected_repository=expected_repository,
        expected_repository_id=expected_repository_id, label="workflow-run pull-request head repository",
    )
    if not isinstance(jobs, list) or any(not isinstance(job, dict) for job in jobs):
        raise IssuanceError("workflow-job list is malformed")
    matches = [job for job in jobs if job.get("name") == expected_job_name]
    if len(matches) != 1:
        raise IssuanceError("workflow job is missing or ambiguous")
    job = matches[0]
    job_id = _require_positive_int(job.get("id"), "workflow job id")
    if (
        job.get("run_id") != expected_run_id
        or job.get("run_attempt") != expected_run_attempt
        or job.get("head_sha") != expected_head
    ):
        raise IssuanceError("workflow job does not bind the expected run attempt and candidate head")
    check_url = job.get("check_run_url")
    match = CHECK_RUN_URL.fullmatch(check_url) if isinstance(check_url, str) else None
    if match is None or match.group(1) != expected_repository:
        raise IssuanceError("workflow job check-run URL is malformed or foreign")
    return {
        "workflow_run_id": expected_run_id,
        "workflow_run_attempt": expected_run_attempt,
        "workflow_job_id": job_id,
        "check_run_id": _require_positive_int(int(match.group(2)), "check run id"),
        "check_suite_id": _require_positive_int(run.get("check_suite_id"), "workflow run check-suite id"),
    }


def validate_check_chain(
    check_run: dict[str, Any], check_suite: dict[str, Any], *, expected_repository: str,
    expected_repository_id: int, expected_head: str, expected_check_run_id: int,
    expected_check_suite_id: int, expected_job_name: str,
) -> None:
    if (
        check_run.get("id") != _require_positive_int(expected_check_run_id, "expected check-run id")
        or check_run.get("name") != expected_job_name
        or check_run.get("head_sha") != _require_full_sha(expected_head, "expected head")
    ):
        raise IssuanceError("check run does not bind the expected job and candidate head")
    _validate_actions_app(check_run.get("app"), "check-run application")
    run_suite = _require_object(check_run.get("check_suite"), "check-run suite")
    if run_suite.get("id") != _require_positive_int(expected_check_suite_id, "expected check-suite id"):
        raise IssuanceError("check run does not belong to the workflow-run check suite")
    if (
        check_suite.get("id") != expected_check_suite_id
        or check_suite.get("head_sha") != expected_head
    ):
        raise IssuanceError("check suite does not bind the expected candidate head")
    suite_repository = _require_object(check_suite.get("repository"), "check-suite repository")
    if suite_repository.get("id") != expected_repository_id or suite_repository.get("full_name") != expected_repository:
        raise IssuanceError("check-suite repository differs from the trusted repository")
    _validate_actions_app(check_suite.get("app"), "check-suite application")


def make_envelope(
    *, facts: dict[str, Any], classification: dict[str, Any], policy_id: str, policy_sha256: str,
    classifier_revision: str, issuer: dict[str, Any], evidence_sources: list[dict[str, Any]],
    evidence_status: str, issued_at: str,
) -> dict[str, Any]:
    tier = classification.get("tier")
    fingerprint = classification.get("review_fingerprint")
    reviewer_class = classification.get("reviewer_class")
    if tier not in {"R0", "R1", "R2"} or not isinstance(fingerprint, str) or SHA256.fullmatch(fingerprint) is None:
        raise IssuanceError("classification is malformed")
    if reviewer_class not in {None, "fast", "deep"}:
        raise IssuanceError("classification reviewer class is malformed")
    if not isinstance(policy_id, str) or not policy_id or SHA256.fullmatch(policy_sha256) is None:
        raise IssuanceError("policy identity is malformed")
    if not isinstance(classifier_revision, str) or not classifier_revision.startswith("sha256:"):
        raise IssuanceError("classifier revision is malformed")
    if SHA256.fullmatch(classifier_revision.removeprefix("sha256:")) is None:
        raise IssuanceError("classifier revision digest is malformed")
    required_issuer = {
        "workflow_ref", "workflow_sha", "workflow_execution_sha", "workflow_run_id",
        "workflow_run_attempt", "workflow_job_id", "check_run_id", "check_suite_id",
    }
    if set(issuer) != required_issuer or not isinstance(issuer["workflow_ref"], str):
        raise IssuanceError("issuer coordinates are malformed")
    _require_full_sha(issuer["workflow_sha"], "issuer workflow SHA")
    _require_full_sha(issuer["workflow_execution_sha"], "issuer workflow execution SHA")
    for key in ("workflow_run_id", "workflow_run_attempt", "workflow_job_id", "check_run_id", "check_suite_id"):
        _require_positive_int(issuer[key], key)
    if not isinstance(issued_at, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", issued_at):
        raise IssuanceError("issued_at is malformed")
    if not isinstance(evidence_sources, list) or any(not isinstance(value, dict) for value in evidence_sources):
        raise IssuanceError("review evidence coordinates are malformed")
    pull_request = _require_object(facts.get("pull_request"), "pull request facts")
    draft = _require_bool(pull_request.get("draft"), "pull request facts draft state")
    expected_evidence_status = (
        "not_required" if tier == "R0" else "deferred" if draft else "verified"
    )
    if evidence_status != expected_evidence_status:
        raise IssuanceError("review evidence status conflicts with the immutable PR state and risk tier")
    if evidence_status == "verified":
        if len(evidence_sources) != 1:
            raise IssuanceError("ready R1/R2 review evidence must contain exactly one source")
        _validate_evidence_source(evidence_sources[0])
    elif evidence_sources:
        raise IssuanceError("deferred or unnecessary review evidence must be source-free")
    return {
        "schema_version": 1,
        "predicate_type": PREDICATE_TYPE,
        "repository": facts["repository"],
        "pull_request": facts["pull_request"],
        "policy": {"id": policy_id, "sha256": policy_sha256},
        "classifier": {"revision": classifier_revision},
        "review": {
            "tier": tier,
            "fingerprint": fingerprint,
            "reviewer_class": reviewer_class,
            "evidence_status": evidence_status,
        },
        "issuer": issuer,
        "review_evidence": evidence_sources,
        "issued_at": issued_at,
    }


def _validate_evidence_source(source: dict[str, Any]) -> None:
    required = {
        "kind", "object_id", "reviewed_head", "actor_login", "actor_id", "app_slug", "app_id",
        "body_sha256",
    }
    if set(source) != required or source.get("kind") not in {"pull_request_review", "issue_comment_result"}:
        raise IssuanceError("review evidence source is malformed")
    _require_positive_int(source.get("object_id"), "review evidence object id")
    _require_full_sha(source.get("reviewed_head"), "review evidence reviewed head")
    if not isinstance(source.get("actor_login"), str) or not source["actor_login"]:
        raise IssuanceError("review evidence actor login is malformed")
    _require_positive_int(source.get("actor_id"), "review evidence actor id")
    if source.get("app_slug") is not None and (
        not isinstance(source["app_slug"], str) or not source["app_slug"]
    ):
        raise IssuanceError("review evidence application slug is malformed")
    if source.get("app_id") is not None:
        _require_positive_int(source["app_id"], "review evidence application id")
    if SHA256.fullmatch(source.get("body_sha256", "")) is None:
        raise IssuanceError("review evidence body digest is malformed")


def _expected_workflow_ref(repository: str) -> str:
    return f"{repository}/{WORKFLOW_PATH}@{WORKFLOW_BRANCH_REF}"


def _expected_workflow_uri(repository: str) -> str:
    return f"https://github.com/{repository}/{WORKFLOW_PATH}@{WORKFLOW_BRANCH_REF}"


def validate_in_job_workflow_context(
    *, repository: str, base: str, workflow_ref: object, workflow_sha: object,
    workflow_execution_sha: object,
) -> None:
    """The only W=T proof available to the running trusted workflow itself."""
    trusted_base = _require_full_sha(base, "base")
    if (
        workflow_ref != _expected_workflow_ref(repository)
        or workflow_sha != trusted_base
        or workflow_execution_sha != trusted_base
    ):
        raise IssuanceError("in-job workflow context is not the exact trusted default-branch source")


def validate_attestation_result(
    result: object, payload: bytes, *, repository: str, repository_id: int, base: str,
    workflow_run_id: int, workflow_run_attempt: int,
) -> None:
    """Require a GitHub-verified statement and certificate to bind trusted W=T."""
    if not isinstance(result, list) or len(result) != 1 or not isinstance(result[0], dict):
        raise IssuanceError("attestation verification result is missing or ambiguous")
    verification = _require_object(result[0].get("verificationResult"), "attestation verification result")
    signature = _require_object(verification.get("signature"), "attestation signature")
    certificate = _require_object(signature.get("certificate"), "attestation signing certificate")
    trusted_base = _require_full_sha(base, "base")
    expected_certificate = {
        "subjectAlternativeName": _expected_workflow_uri(repository),
        "issuer": "https://token.actions.githubusercontent.com",
        "githubWorkflowTrigger": "pull_request_target",
        "githubWorkflowSHA": trusted_base,
        "githubWorkflowRepository": repository,
        "githubWorkflowRef": WORKFLOW_BRANCH_REF,
        "buildSignerURI": _expected_workflow_uri(repository),
        "buildSignerDigest": trusted_base,
        "runnerEnvironment": "github-hosted",
        "sourceRepositoryURI": f"https://github.com/{repository}",
        "sourceRepositoryDigest": trusted_base,
        "sourceRepositoryRef": WORKFLOW_BRANCH_REF,
        "sourceRepositoryIdentifier": str(_require_positive_int(repository_id, "repository id")),
        "buildConfigURI": _expected_workflow_uri(repository),
        "buildConfigDigest": trusted_base,
        "buildTrigger": "pull_request_target",
        "runInvocationURI": (
            f"https://github.com/{repository}/actions/runs/"
            f"{_require_positive_int(workflow_run_id, 'workflow run id')}/attempts/"
            f"{_require_positive_int(workflow_run_attempt, 'workflow run attempt')}"
        ),
    }
    if any(certificate.get(key) != value for key, value in expected_certificate.items()):
        raise IssuanceError("attestation certificate does not bind the exact trusted workflow and run invocation")
    statement = _require_object(verification.get("statement"), "attestation statement")
    if statement.get("predicateType") != PREDICATE_TYPE:
        raise IssuanceError("attestation predicate type differs from the trusted predicate")
    predicate = _require_object(statement.get("predicate"), "attestation predicate")
    if canonical_json_bytes(predicate) != payload:
        raise IssuanceError("attestation predicate does not equal the exact canonical envelope bytes")
    subjects = statement.get("subject")
    if not isinstance(subjects, list) or len(subjects) != 1:
        raise IssuanceError("attestation subject is missing or ambiguous")
    subject = _require_object(subjects[0], "attestation subject")
    digest = _require_object(subject.get("digest"), "attestation subject digest")
    if digest.get("sha256") != hashlib.sha256(payload).hexdigest():
        raise IssuanceError("attestation subject SHA-256 differs from the envelope binding identifier")


def _api_json(url: str, token: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "oteryn-trusted-review-attestation",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            value = json.load(response)
    except Exception as exc:  # API failures are trust failures, never a fallback path.
        raise IssuanceError(f"GitHub API read failed for {url}") from exc
    return _require_object(value, "GitHub API response")


def _api_pages(url: str, token: str, *, list_key: str | None = None) -> list[dict[str, Any]]:
    if list_key is not None and (not isinstance(list_key, str) or not list_key):
        raise IssuanceError("GitHub paginated list key is malformed")
    result: list[dict[str, Any]] = []
    for page in range(1, MAX_PAGES + 1):
        separator = "&" if "?" in url else "?"
        request = urllib.request.Request(
            f"{url}{separator}per_page=100&page={page}",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "oteryn-trusted-review-attestation",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                batch = json.load(response)
        except Exception as exc:
            raise IssuanceError(f"GitHub API paginated read failed for {url}") from exc
        total_count: int | None = None
        if list_key is not None:
            envelope = _require_object(batch, "GitHub paginated response")
            total_count = envelope.get("total_count")
            if isinstance(total_count, bool) or not isinstance(total_count, int) or total_count < 0:
                raise IssuanceError("GitHub paginated response total_count is malformed")
            batch = envelope.get(list_key)
        if (
            not isinstance(batch, list)
            or len(batch) > 100
            or any(not isinstance(item, dict) for item in batch)
        ):
            raise IssuanceError("GitHub paginated response is malformed")
        result.extend(batch)
        if total_count is not None and len(result) > total_count:
            raise IssuanceError("GitHub paginated response exceeds its declared total_count")
        if len(batch) < 100:
            if total_count is not None and len(result) != total_count:
                raise IssuanceError("GitHub paginated response total_count is incomplete or ambiguous")
            return result
    raise IssuanceError("GitHub pagination exceeded the bounded trust limit")


def _direct_source(
    *, repository: str, pr_number: int, source_url: object, source_kind: object,
    reviewed_head: str, token: str,
) -> dict[str, Any]:
    if not isinstance(source_url, str) or not isinstance(source_kind, str):
        raise IssuanceError("review evidence source coordinate is malformed")
    review = REVIEW_URL.fullmatch(source_url)
    comment = COMMENT_URL.fullmatch(source_url)
    if source_kind == "pull_request_review" and review is not None:
        source_repository, source_pr, source_id = review.groups()
        endpoint = f"https://api.github.com/repos/{repository}/pulls/{pr_number}/reviews/{source_id}"
        source = _api_json(endpoint, token)
        object_id = _require_positive_int(source.get("id"), "review source id")
        if source_repository != repository or int(source_pr) != pr_number or object_id != int(source_id):
            raise IssuanceError("review source URL/object identity mismatch")
        if source.get("html_url") != source_url or source.get("commit_id") != reviewed_head:
            raise IssuanceError("review source no longer binds the reviewed head")
    elif source_kind == "issue_comment_result" and comment is not None:
        source_repository, source_pr, source_id = comment.groups()
        endpoint = f"https://api.github.com/repos/{repository}/issues/comments/{source_id}"
        source = _api_json(endpoint, token)
        object_id = _require_positive_int(source.get("id"), "comment source id")
        expected_issue = f"https://api.github.com/repos/{repository}/issues/{pr_number}"
        if (
            source_repository != repository or int(source_pr) != pr_number or object_id != int(source_id)
            or source.get("html_url") != source_url or source.get("issue_url") != expected_issue
        ):
            raise IssuanceError("comment source URL/object identity mismatch")
    else:
        raise IssuanceError("review source kind and URL disagree")
    user = _require_object(source.get("user"), "review source actor")
    actor_login = user.get("login")
    actor_id = user.get("id")
    if not isinstance(actor_login, str) or not actor_login:
        raise IssuanceError("review source actor login is missing")
    app = source.get("performed_via_github_app")
    app_slug = app.get("slug") if isinstance(app, dict) else None
    app_id = app.get("id") if isinstance(app, dict) else None
    if app_slug is not None and not isinstance(app_slug, str):
        raise IssuanceError("review source application slug is malformed")
    if app_id is not None:
        _require_positive_int(app_id, "review source application id")
    body = source.get("body")
    if not isinstance(body, str):
        raise IssuanceError("review source body is malformed")
    return {
        "kind": source_kind,
        "object_id": object_id,
        "reviewed_head": reviewed_head,
        "actor_login": actor_login,
        "actor_id": _require_positive_int(actor_id, "review source actor id"),
        "app_slug": app_slug,
        "app_id": app_id,
        "body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
    }


def _material_sources(match: dict[str, Any], *, repository: str, pr_number: int, token: str) -> list[dict[str, Any]]:
    reviewed_head = _require_full_sha(match.get("reviewed_head"), "reviewed head")
    source = _direct_source(
        repository=repository, pr_number=pr_number, source_url=match.get("review_source_url"),
        source_kind=match.get("review_source_kind"), reviewed_head=reviewed_head, token=token,
    )
    source_commit = match.get("review_source_commit_id")
    if source_commit != reviewed_head:
        raise IssuanceError("review verifier source head differs from independently fetched source")
    return [source]


def _run_review_verifier(
    *, repository: str, pr_number: int, base: str, head: str, bare_git_dir: Path,
    policy: dict[str, Any], classification: dict[str, Any], token: str,
) -> dict[str, Any] | None:
    if classification["tier"] == "R0":
        return None
    policy["_trusted_integration_base_sha"] = base
    core = review_evidence._core
    return review_evidence.verify_records(
        core.fetch_comments(repository, pr_number, token),
        policy=policy,
        repo_root=bare_git_dir,
        tier=classification["tier"],
        fingerprint=classification["review_fingerprint"],
        head=head,
        repository=repository,
        pr_number=pr_number,
        token=token,
        reviews=core.fetch_reviews(repository, pr_number, token),
        review_comments=core.fetch_review_comments(repository, pr_number, token),
        pr_reactions=review_evidence.fetch_pr_reactions(repository, pr_number, token),
    )


def recompute_semantic_claims(
    *, facts: dict[str, Any], repository: str, pr_number: int, base: str, head: str,
    bare_git_dir: Path, policy_path: Path, classifier_path: Path, token: str,
) -> dict[str, Any]:
    """Recompute every candidate-sensitive claim from trusted T and inert T/H objects."""
    try:
        policy_bytes = policy_path.read_bytes()
        classifier_bytes = classifier_path.read_bytes()
        policy = risk_policy.load_policy(policy_path)
        classification = risk_policy.evaluate(base, head, bare_git_dir, policy_path)
    except Exception as exc:
        raise IssuanceError("trusted policy/classifier recomputation failed") from exc
    tier = classification.get("tier")
    fingerprint = classification.get("review_fingerprint")
    reviewer_class = classification.get("reviewer_class")
    if tier not in {"R0", "R1", "R2"} or not isinstance(fingerprint, str) or SHA256.fullmatch(fingerprint) is None:
        raise IssuanceError("trusted classifier result is malformed")
    if reviewer_class not in {None, "fast", "deep"}:
        raise IssuanceError("trusted classifier reviewer class is malformed")
    pull_request = _require_object(facts.get("pull_request"), "pull request facts")
    draft = _require_bool(pull_request.get("draft"), "pull request facts draft state")
    if tier == "R0":
        evidence_status = "not_required"
        evidence_sources: list[dict[str, Any]] = []
    elif draft:
        evidence_status = "deferred"
        evidence_sources = []
    else:
        evidence_status = "verified"
        review_match = _run_review_verifier(
            repository=repository, pr_number=pr_number, base=base, head=head,
            bare_git_dir=bare_git_dir, policy=policy, classification=classification, token=token,
        )
        if review_match is None:
            raise IssuanceError("ready R1/R2 review verification unexpectedly returned no evidence")
        evidence_sources = _material_sources(
            review_match, repository=repository, pr_number=pr_number, token=token,
        )
    return {
        "policy": {
            "id": policy.get("policy_id"),
            "sha256": hashlib.sha256(policy_bytes).hexdigest(),
        },
        "classifier": {"revision": "sha256:" + hashlib.sha256(classifier_bytes).hexdigest()},
        "review": {
            "tier": tier,
            "fingerprint": fingerprint,
            "reviewer_class": reviewer_class,
            "evidence_status": evidence_status,
        },
        "review_evidence": evidence_sources,
    }


def validate_semantic_claims(attested: object, expected: dict[str, Any]) -> None:
    """Do not trust a self-authored predicate when trusted recomputation disagrees."""
    value = _require_object(attested, "attested semantic claims")
    required = {"policy", "classifier", "review", "review_evidence"}
    if set(value) != required or set(expected) != required:
        raise IssuanceError("semantic claim shape is malformed")
    for key in ("policy", "classifier", "review"):
        if value.get(key) != expected[key]:
            raise IssuanceError(f"attested {key} differs from trusted recomputation")
    if value.get("review_evidence") != expected["review_evidence"]:
        raise IssuanceError("attested review evidence differs from trusted recomputation")


def _read_run_facts(
    *, repository: str, repository_id: int, pr_id: int, pr_number: int, base: str, head: str,
    default_branch: str, workflow_run_id: int, workflow_run_attempt: int,
    workflow_job: str, token: str,
) -> dict[str, int]:
    run = _api_json(f"https://api.github.com/repos/{repository}/actions/runs/{workflow_run_id}", token)
    run_facts = validate_run_job_facts(
        run,
        _api_pages(
            f"https://api.github.com/repos/{repository}/actions/runs/{workflow_run_id}/jobs",
            token,
            list_key="jobs",
        ),
        expected_repository=repository, expected_repository_id=repository_id,
        expected_run_id=workflow_run_id, expected_run_attempt=workflow_run_attempt,
        expected_base=base, expected_head=head, expected_pr_id=pr_id, expected_pr_number=pr_number,
        expected_default_branch=default_branch, expected_job_name=workflow_job,
    )
    check_run = _api_json(
        f"https://api.github.com/repos/{repository}/check-runs/{run_facts['check_run_id']}", token,
    )
    check_suite = _api_json(
        f"https://api.github.com/repos/{repository}/check-suites/{run_facts['check_suite_id']}", token,
    )
    validate_check_chain(
        check_run, check_suite, expected_repository=repository, expected_repository_id=repository_id,
        expected_head=head, expected_check_run_id=run_facts["check_run_id"],
        expected_check_suite_id=run_facts["check_suite_id"], expected_job_name=workflow_job,
    )
    return run_facts


def _issue(args: argparse.Namespace) -> int:
    token = args.token
    base = _require_full_sha(args.base, "base")
    head = _require_full_sha(args.head, "head")
    expected_draft = _parse_draft(args.draft)
    repository_id = _require_positive_int(args.repository_id, "repository id")
    repository = _api_json(f"https://api.github.com/repos/{args.repository}", token)
    pull_request = _api_json(f"https://api.github.com/repos/{args.repository}/pulls/{args.pr_number}", token)
    facts = validate_pr_facts(
        repository, pull_request, expected_repository=args.repository,
        expected_repository_id=repository_id, expected_pr_id=args.pr_id, expected_pr_number=args.pr_number,
        expected_base=base, expected_head=head, expected_draft=expected_draft,
    )
    validate_commit_fact(
        _api_json(f"https://api.github.com/repos/{args.repository}/commits/{base}", token),
        expected_sha=base, label="base",
    )
    validate_commit_fact(
        _api_json(f"https://api.github.com/repos/{args.repository}/commits/{head}", token),
        expected_sha=head, label="head",
    )
    validate_in_job_workflow_context(
        repository=args.repository, base=base, workflow_ref=args.workflow_ref,
        workflow_sha=args.workflow_sha, workflow_execution_sha=args.workflow_execution_sha,
    )
    run_facts = _read_run_facts(
        repository=args.repository, repository_id=repository_id, pr_id=args.pr_id, pr_number=args.pr_number,
        base=base, head=head, default_branch=facts["pull_request"]["base"]["ref"],
        workflow_run_id=args.workflow_run_id, workflow_run_attempt=args.workflow_run_attempt,
        workflow_job=args.workflow_job, token=token,
    )
    policy_path = Path(args.policy_file)
    classifier_path = Path(args.classifier_file)
    semantic_claims = recompute_semantic_claims(
        facts=facts, repository=args.repository, pr_number=args.pr_number, base=base, head=head,
        bare_git_dir=Path(args.bare_git_dir), policy_path=policy_path,
        classifier_path=classifier_path, token=token,
    )
    issuer = {
        "workflow_ref": args.workflow_ref,
        "workflow_sha": args.workflow_sha,
        "workflow_execution_sha": args.workflow_execution_sha,
        **run_facts,
    }
    envelope = make_envelope(
        facts=facts,
        classification={
            "tier": semantic_claims["review"]["tier"],
            "review_fingerprint": semantic_claims["review"]["fingerprint"],
            "reviewer_class": semantic_claims["review"]["reviewer_class"],
        },
        policy_id=semantic_claims["policy"]["id"],
        policy_sha256=semantic_claims["policy"]["sha256"],
        classifier_revision=semantic_claims["classifier"]["revision"],
        issuer=issuer,
        evidence_status=semantic_claims["review"]["evidence_status"],
        evidence_sources=semantic_claims["review_evidence"],
        issued_at=datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    )
    payload = canonical_json_bytes(envelope)
    destination = Path(args.output)
    destination.write_bytes(payload)
    identifier = envelope_identifier(payload)
    if args.github_output:
        with Path(args.github_output).open("a", encoding="utf-8") as output:
            output.write(f"tier={semantic_claims['review']['tier']}\n")
            output.write(f"fingerprint={semantic_claims['review']['fingerprint']}\n")
            output.write(f"reviewer-class={semantic_claims['review']['reviewer_class'] or 'none'}\n")
            output.write(f"envelope-path={destination}\n")
            output.write(f"envelope-sha256={identifier}\n")
    print(identifier)
    return 0


def _preflight(args: argparse.Namespace) -> int:
    repository = _api_json(f"https://api.github.com/repos/{args.repository}", args.token)
    pull_request = _api_json(f"https://api.github.com/repos/{args.repository}/pulls/{args.pr_number}", args.token)
    validate_pr_facts(
        repository, pull_request, expected_repository=args.repository,
        expected_repository_id=args.repository_id, expected_pr_id=args.pr_id, expected_pr_number=args.pr_number,
        expected_base=args.base, expected_head=args.head, expected_draft=_parse_draft(args.draft),
    )
    return 0


def _verify(args: argparse.Namespace) -> int:
    payload = Path(args.envelope).read_bytes()
    try:
        envelope = json.loads(payload)
    except Exception as exc:
        raise IssuanceError("envelope is not JSON") from exc
    if not isinstance(envelope, dict) or canonical_json_bytes(envelope) != payload:
        raise IssuanceError("envelope is not exact canonical JSON")
    try:
        attestation_result = json.loads(Path(args.attestation_result).read_text(encoding="utf-8"))
    except Exception as exc:
        raise IssuanceError("GitHub attestation verification output is not JSON") from exc
    repository_id = _require_positive_int(args.repository_id, "repository id")
    expected_draft = _parse_draft(args.draft)
    base = _require_full_sha(args.base, "base")
    head = _require_full_sha(args.head, "head")
    validate_in_job_workflow_context(
        repository=args.repository, base=base, workflow_ref=args.workflow_ref,
        workflow_sha=args.workflow_sha, workflow_execution_sha=args.workflow_execution_sha,
    )
    validate_attestation_result(
        attestation_result, payload, repository=args.repository, repository_id=repository_id,
        base=base, workflow_run_id=args.workflow_run_id,
        workflow_run_attempt=args.workflow_run_attempt,
    )
    if envelope.get("schema_version") != 1 or envelope.get("predicate_type") != PREDICATE_TYPE:
        raise IssuanceError("attested envelope schema or predicate type is invalid")
    repository = _api_json(f"https://api.github.com/repos/{args.repository}", args.token)
    pull_request = _api_json(f"https://api.github.com/repos/{args.repository}/pulls/{args.pr_number}", args.token)
    facts = validate_pr_facts(
        repository, pull_request, expected_repository=args.repository,
        expected_repository_id=repository_id, expected_pr_id=args.pr_id, expected_pr_number=args.pr_number,
        expected_base=base, expected_head=head, expected_draft=expected_draft,
    )
    if envelope.get("repository") != facts["repository"] or envelope.get("pull_request") != facts["pull_request"]:
        raise IssuanceError("attested envelope no longer matches the live PR coordinates")
    run_facts = _read_run_facts(
        repository=args.repository, repository_id=repository_id, pr_id=args.pr_id, pr_number=args.pr_number,
        base=base, head=head, default_branch=facts["pull_request"]["base"]["ref"],
        workflow_run_id=args.workflow_run_id, workflow_run_attempt=args.workflow_run_attempt,
        workflow_job=args.workflow_job, token=args.token,
    )
    issuer = _require_object(envelope.get("issuer"), "envelope issuer")
    expected_issuer = {
        "workflow_ref": args.workflow_ref,
        "workflow_sha": args.workflow_sha,
        "workflow_execution_sha": args.workflow_execution_sha,
        **run_facts,
    }
    if issuer != expected_issuer:
        raise IssuanceError("attested issuer run/job/check coordinates differ from live GitHub facts")
    expected_semantics = recompute_semantic_claims(
        facts=facts, repository=args.repository, pr_number=args.pr_number, base=base, head=head,
        bare_git_dir=Path(args.bare_git_dir), policy_path=Path(args.policy_file),
        classifier_path=Path(args.classifier_file), token=args.token,
    )
    validate_semantic_claims({
        "policy": envelope.get("policy"),
        "classifier": envelope.get("classifier"),
        "review": envelope.get("review"),
        "review_evidence": envelope.get("review_evidence"),
    }, expected_semantics)
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("preflight", "issue", "verify"))
    parser.add_argument("--repository", required=True)
    parser.add_argument("--repository-id", required=True, type=int)
    parser.add_argument("--pr-id", required=True, type=int)
    parser.add_argument("--pr-number", required=True, type=int)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--draft")
    parser.add_argument("--token", required=True)
    parser.add_argument("--workflow-ref")
    parser.add_argument("--workflow-sha")
    parser.add_argument("--workflow-execution-sha")
    parser.add_argument("--workflow-run-id", type=int)
    parser.add_argument("--workflow-run-attempt", type=int)
    parser.add_argument("--workflow-job")
    parser.add_argument("--bare-git-dir")
    parser.add_argument("--policy-file")
    parser.add_argument("--classifier-file")
    parser.add_argument("--output")
    parser.add_argument("--github-output")
    parser.add_argument("--envelope")
    parser.add_argument("--attestation-result")
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        if args.mode == "preflight":
            if args.draft is None:
                raise IssuanceError("preflight command is missing required argument: draft")
            return _preflight(args)
        if args.mode == "verify":
            if (
                not args.envelope or not args.attestation_result or args.workflow_run_id is None
                or args.workflow_run_attempt is None or not args.workflow_job or args.draft is None
                or not args.workflow_ref or not args.workflow_sha or not args.workflow_execution_sha
                or not args.bare_git_dir or not args.policy_file or not args.classifier_file
            ):
                raise IssuanceError("verification command is missing required arguments")
            return _verify(args)
        required = {
            "workflow_ref": args.workflow_ref,
            "workflow_sha": args.workflow_sha,
            "workflow_execution_sha": args.workflow_execution_sha,
            "workflow_run_id": args.workflow_run_id,
            "workflow_run_attempt": args.workflow_run_attempt,
            "workflow_job": args.workflow_job,
            "draft": args.draft,
            "bare_git_dir": args.bare_git_dir,
            "policy_file": args.policy_file,
            "classifier_file": args.classifier_file,
            "output": args.output,
        }
        missing = [name for name, value in required.items() if value is None or value == ""]
        if missing:
            raise IssuanceError(f"issuer command is missing required arguments: {', '.join(missing)}")
        return _issue(args)
    except IssuanceError as exc:
        print(f"trusted review attestation: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
