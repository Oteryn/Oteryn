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
    expected_repository_id: int, expected_pr_number: int, expected_base: str, expected_head: str,
    expected_draft: bool | None = None,
) -> dict[str, Any]:
    """Validate independently server-fetched repository and PR coordinates."""
    expected_id = _require_positive_int(expected_repository_id, "expected repository id")
    if repository.get("full_name") != expected_repository or repository.get("id") != expected_id:
        raise IssuanceError("server repository identity differs from trusted workflow context")
    if repository.get("archived") is not False or repository.get("disabled") is not False:
        raise IssuanceError("repository is archived or disabled")
    default_branch = repository.get("default_branch")
    if not isinstance(default_branch, str) or not default_branch:
        raise IssuanceError("repository default branch is missing")
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
        or base_repo.get("id") != expected_id
        or base_repo.get("full_name") != expected_repository
    ):
        raise IssuanceError("server pull-request base is not the exact default-branch base")
    if (
        head.get("sha") != _require_full_sha(expected_head, "expected head")
        or head_repo.get("id") != expected_id
        or head_repo.get("full_name") != expected_repository
        or head_repo.get("fork") is not False
    ):
        raise IssuanceError("cross-repository, forked, or inconsistent PR head is rejected")
    return {
        "repository": {"id": expected_id, "full_name": expected_repository},
        "pull_request": {
            "number": expected_pr_number,
            "base": {"ref": default_branch, "sha": expected_base},
            "head": expected_head,
            "draft": draft,
        },
    }


def validate_commit_fact(commit: dict[str, Any], *, expected_sha: str, label: str) -> None:
    if commit.get("sha") != _require_full_sha(expected_sha, label):
        raise IssuanceError(f"server {label} commit identity differs from the PR")


def validate_run_job_facts(
    run: dict[str, Any], jobs: list[dict[str, Any]], *, expected_repository: str,
    expected_repository_id: int, expected_run_id: int, expected_base: str, expected_job_name: str,
) -> dict[str, int]:
    if run.get("id") != _require_positive_int(expected_run_id, "expected workflow run id"):
        raise IssuanceError("workflow-run identity differs from trusted context")
    run_repo = _require_object(run.get("repository"), "workflow-run repository")
    if run_repo.get("id") != expected_repository_id or run_repo.get("full_name") != expected_repository:
        raise IssuanceError("workflow-run repository differs from trusted repository")
    if run.get("event") != "pull_request_target" or run.get("head_sha") != expected_base:
        raise IssuanceError("workflow run is not the expected trusted-base pull_request_target run")
    if not isinstance(jobs, list) or any(not isinstance(job, dict) for job in jobs):
        raise IssuanceError("workflow-job list is malformed")
    matches = [job for job in jobs if job.get("name") == expected_job_name]
    if len(matches) != 1:
        raise IssuanceError("workflow job is missing or ambiguous")
    job = matches[0]
    job_id = _require_positive_int(job.get("id"), "workflow job id")
    check_url = job.get("check_run_url")
    match = CHECK_RUN_URL.fullmatch(check_url) if isinstance(check_url, str) else None
    if match is None or match.group(1) != expected_repository:
        raise IssuanceError("workflow job check-run URL is malformed or foreign")
    return {
        "workflow_run_id": expected_run_id,
        "workflow_job_id": job_id,
        "check_run_id": _require_positive_int(int(match.group(2)), "check run id"),
    }


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
    required_issuer = {"workflow_ref", "workflow_sha", "workflow_run_id", "workflow_job_id", "check_run_id"}
    if set(issuer) != required_issuer or not isinstance(issuer["workflow_ref"], str):
        raise IssuanceError("issuer coordinates are malformed")
    _require_full_sha(issuer["workflow_sha"], "issuer workflow SHA")
    for key in ("workflow_run_id", "workflow_job_id", "check_run_id"):
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


def validate_attestation_result(result: object, payload: bytes) -> None:
    """Require the GitHub CLI's verified statement to bind these exact bytes."""
    if not isinstance(result, list) or len(result) != 1 or not isinstance(result[0], dict):
        raise IssuanceError("attestation verification result is missing or ambiguous")
    verification = _require_object(result[0].get("verificationResult"), "attestation verification result")
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


def _api_pages(url: str, token: str) -> list[dict[str, Any]]:
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
        if not isinstance(batch, list) or any(not isinstance(item, dict) for item in batch):
            raise IssuanceError("GitHub paginated response is malformed")
        result.extend(batch)
        if len(batch) < 100:
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


def _expected_workflow_ref(repository: str) -> str:
    return f"{repository}/.github/workflows/governance-ai-review.yml@refs/heads/main"


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
        expected_repository_id=repository_id, expected_pr_number=args.pr_number,
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
    run = _api_json(f"https://api.github.com/repos/{args.repository}/actions/runs/{args.workflow_run_id}", token)
    run_facts = validate_run_job_facts(
        run,
        _api_pages(f"https://api.github.com/repos/{args.repository}/actions/runs/{args.workflow_run_id}/jobs", token),
        expected_repository=args.repository, expected_repository_id=repository_id,
        expected_run_id=args.workflow_run_id, expected_base=base, expected_job_name=args.workflow_job,
    )
    if args.workflow_ref != _expected_workflow_ref(args.repository) or args.workflow_sha != base:
        raise IssuanceError("issuer workflow is not the exact trusted default-branch workflow source")
    policy_path = Path(args.policy_file)
    classifier_path = Path(args.classifier_file)
    policy = risk_policy.load_policy(policy_path)
    classification = risk_policy.evaluate(base, head, args.bare_git_dir, policy_path)
    if classification["tier"] == "R0":
        evidence_status = "not_required"
        evidence_sources: list[dict[str, Any]] = []
    elif facts["pull_request"]["draft"]:
        evidence_status = "deferred"
        evidence_sources = []
    else:
        evidence_status = "verified"
        review_match = _run_review_verifier(
            repository=args.repository, pr_number=args.pr_number, base=base, head=head,
            bare_git_dir=Path(args.bare_git_dir), policy=policy, classification=classification, token=token,
        )
        if review_match is None:
            raise IssuanceError("ready R1/R2 review verification unexpectedly returned no evidence")
        evidence_sources = _material_sources(
            review_match, repository=args.repository, pr_number=args.pr_number, token=token,
        )
    issuer = {
        "workflow_ref": args.workflow_ref,
        "workflow_sha": args.workflow_sha,
        **run_facts,
    }
    envelope = make_envelope(
        facts=facts,
        classification=classification,
        policy_id=policy["policy_id"],
        policy_sha256=hashlib.sha256(policy_path.read_bytes()).hexdigest(),
        classifier_revision="sha256:" + hashlib.sha256(classifier_path.read_bytes()).hexdigest(),
        issuer=issuer,
        evidence_status=evidence_status,
        evidence_sources=evidence_sources,
        issued_at=datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    )
    payload = canonical_json_bytes(envelope)
    destination = Path(args.output)
    destination.write_bytes(payload)
    identifier = envelope_identifier(payload)
    if args.github_output:
        with Path(args.github_output).open("a", encoding="utf-8") as output:
            output.write(f"tier={classification['tier']}\n")
            output.write(f"fingerprint={classification['review_fingerprint']}\n")
            output.write(f"reviewer-class={classification['reviewer_class'] or 'none'}\n")
            output.write(f"envelope-path={destination}\n")
            output.write(f"envelope-sha256={identifier}\n")
    print(identifier)
    return 0


def _preflight(args: argparse.Namespace) -> int:
    repository = _api_json(f"https://api.github.com/repos/{args.repository}", args.token)
    pull_request = _api_json(f"https://api.github.com/repos/{args.repository}/pulls/{args.pr_number}", args.token)
    validate_pr_facts(
        repository, pull_request, expected_repository=args.repository,
        expected_repository_id=args.repository_id, expected_pr_number=args.pr_number,
        expected_base=args.base, expected_head=args.head, expected_draft=_parse_draft(args.draft),
    )
    return 0


def _source_url_from_coordinate(repository: str, pr_number: int, source: dict[str, Any]) -> str:
    kind = source.get("kind")
    object_id = _require_positive_int(source.get("object_id"), "review evidence object id")
    if kind == "pull_request_review":
        return f"https://github.com/{repository}/pull/{pr_number}#pullrequestreview-{object_id}"
    if kind == "issue_comment_result":
        return f"https://github.com/{repository}/pull/{pr_number}#issuecomment-{object_id}"
    raise IssuanceError("review evidence source kind is unsupported")


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
    validate_attestation_result(attestation_result, payload)
    repository_id = _require_positive_int(args.repository_id, "repository id")
    expected_draft = _parse_draft(args.draft)
    repository = _api_json(f"https://api.github.com/repos/{args.repository}", args.token)
    pull_request = _api_json(f"https://api.github.com/repos/{args.repository}/pulls/{args.pr_number}", args.token)
    facts = validate_pr_facts(
        repository, pull_request, expected_repository=args.repository,
        expected_repository_id=repository_id, expected_pr_number=args.pr_number,
        expected_base=args.base, expected_head=args.head, expected_draft=expected_draft,
    )
    if envelope.get("repository") != facts["repository"] or envelope.get("pull_request") != facts["pull_request"]:
        raise IssuanceError("attested envelope no longer matches the live PR coordinates")
    run = _api_json(f"https://api.github.com/repos/{args.repository}/actions/runs/{args.workflow_run_id}", args.token)
    run_facts = validate_run_job_facts(
        run,
        _api_pages(f"https://api.github.com/repos/{args.repository}/actions/runs/{args.workflow_run_id}/jobs", args.token),
        expected_repository=args.repository, expected_repository_id=repository_id,
        expected_run_id=args.workflow_run_id, expected_base=args.base, expected_job_name=args.workflow_job,
    )
    issuer = _require_object(envelope.get("issuer"), "envelope issuer")
    if (
        issuer.get("workflow_ref") != _expected_workflow_ref(args.repository)
        or issuer.get("workflow_sha") != args.base
        or any(issuer.get(key) != value for key, value in run_facts.items())
    ):
        raise IssuanceError("attested issuer run/job/check coordinates differ from live GitHub facts")
    review = _require_object(envelope.get("review"), "envelope review")
    sources = envelope.get("review_evidence")
    if review.get("tier") == "R0":
        if review.get("evidence_status") != "not_required" or sources != []:
            raise IssuanceError("R0 envelope review-evidence state is malformed")
    elif review.get("tier") in {"R1", "R2"}:
        expected_status = "deferred" if facts["pull_request"]["draft"] else "verified"
        if review.get("evidence_status") != expected_status:
            raise IssuanceError("R1/R2 envelope review-evidence state conflicts with the live Draft state")
        if expected_status == "deferred":
            if sources != []:
                raise IssuanceError("Draft R1/R2 envelope unexpectedly carries external review evidence")
        else:
            if not isinstance(sources, list) or len(sources) != 1 or not isinstance(sources[0], dict):
                raise IssuanceError("external-review envelope source is missing or ambiguous")
            source = sources[0]
            _validate_evidence_source(source)
            rechecked = _direct_source(
                repository=args.repository, pr_number=args.pr_number,
                source_url=_source_url_from_coordinate(args.repository, args.pr_number, source),
                source_kind=source.get("kind"),
                reviewed_head=_require_full_sha(source.get("reviewed_head"), "review evidence reviewed head"),
                token=args.token,
            )
            if rechecked != source:
                raise IssuanceError("live review source differs from the attested immutable coordinate")
    else:
        raise IssuanceError("attested review tier is invalid")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("preflight", "issue", "verify"))
    parser.add_argument("--repository", required=True)
    parser.add_argument("--repository-id", required=True, type=int)
    parser.add_argument("--pr-number", required=True, type=int)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--draft")
    parser.add_argument("--token", required=True)
    parser.add_argument("--workflow-ref")
    parser.add_argument("--workflow-sha")
    parser.add_argument("--workflow-run-id", type=int)
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
                or not args.workflow_job or args.draft is None
            ):
                raise IssuanceError("verification command is missing required arguments")
            return _verify(args)
        required = {
            "workflow_ref": args.workflow_ref,
            "workflow_sha": args.workflow_sha,
            "workflow_run_id": args.workflow_run_id,
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
