#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import subprocess
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

# Exact protected-main commit that first made immutable request anchors available.
# A request created before this commit cannot have targeted a descendant commit
# that did not exist yet. Post-rollout unanchored/malformed requests still fail closed.
REQUEST_ANCHOR_ROLLOUT_COMMIT = "dbed59b9cfab1e8a66ac9e0a5056053718980ce3"
# Compatibility is repository-scoped and declared in the trusted machine-readable policy.
# Repositories without a proven rollout marker retain every request-like comment.

_CORE_PATH = Path(__file__).with_name("verify_ai_review_evidence_core.py")
_spec = importlib.util.spec_from_file_location("verify_ai_review_evidence_core", _CORE_PATH)
if _spec is None or _spec.loader is None:
    raise RuntimeError("cannot load immutable AI review verifier core")
_core = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_core)

_original_verify_records = _core.verify_records
_original_blocking_findings = _core._blocking_findings_for_current_generation
_original_issue_comment_result = _core._verify_issue_comment_result
_original_parse_clean_result = _core.parse_clean_result
_original_fetch_review_source = _core.fetch_review_source
_original_fetch_json = _core.fetch_json
_original_resolve_reviewed_prefix = _core.resolve_reviewed_prefix

_CLEAN_PREFIX = "Codex Review: Didn't find any major issues."
# Do not heuristically classify arbitrary bot prose as celebratory. Compatibility
# is intentionally limited to exact observed Codex clean-result variants.
_ALLOWED_CLEAN_FLAIR = {
    "Swish!", "Hooray!", "Chef's kiss.", "Breezy!", "Nice work!",
    ":rocket:", "More of your lovely PRs please.",
}


def _request_anchor_rollout_time(
    repo_root: str | Path, rollout_commit: str = REQUEST_ANCHOR_ROLLOUT_COMMIT,
) -> datetime | None:
    result = subprocess.run(
        ["git", "show", "-s", "--format=%cI", rollout_commit],
        cwd=Path(repo_root), text=True, encoding="utf-8",
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    if result.returncode != 0:
        return None
    try:
        stamp = datetime.fromisoformat(result.stdout.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if stamp.tzinfo is None:
        return None
    return stamp.astimezone(timezone.utc)


def _strict_comment_time(comment: dict) -> datetime | None:
    raw = str(comment.get("created_at") or "")
    try:
        stamp = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if stamp.tzinfo is None:
        return None
    return stamp.astimezone(timezone.utc)


def _strict_timestamp(raw: str) -> datetime | None:
    try:
        stamp = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None
    if stamp.tzinfo is None:
        return None
    return stamp.astimezone(timezone.utc)


def _request_command_present(body: str) -> bool:
    return any(line.strip().casefold() == "@codex review" for line in body.splitlines())


def _configured_rollout_commit(policy: dict, repository: str) -> str | None:
    rollouts = policy.get("request_anchor_rollouts")
    if not isinstance(rollouts, dict):
        return None
    value = rollouts.get(repository)
    if not isinstance(value, str) or _core.FULL_SHA.fullmatch(value) is None:
        return None
    return value


def _eligible_anchor_map(
    *, reviews: list[dict], policy: dict, repo_root: str | Path,
    head: str, repository: str, pr_number: int,
) -> tuple[dict[int, dict[str, str]], dict[str, str]]:
    by_comment: dict[int, dict[str, str]] = {}
    trusted_authors: dict[str, str] = {}
    for _, anchor in _core._eligible_request_anchors(
        reviews=reviews,
        policy=policy,
        repo_root=repo_root,
        head=head,
        repository=repository,
        pr_number=pr_number,
    ):
        if anchor["REQUEST_VALID"] != "true":
            continue
        association = anchor["REQUEST_AUTHOR_ASSOCIATION"]
        if association not in _core.TRUSTED_ASSOCIATIONS:
            raise RuntimeError("valid request anchor has an untrusted author association")
        comment_id = int(anchor["REQUEST_COMMENT_ID"])
        if comment_id in by_comment and by_comment[comment_id] != anchor:
            raise RuntimeError("request anchor comment identity is ambiguous")
        by_comment[comment_id] = anchor
        author = anchor["REQUEST_AUTHOR"].casefold()
        trusted_authors.setdefault(author, association)
    return by_comment, trusted_authors


def _anchor_matches_comment(anchor: dict[str, str], comment: dict) -> bool:
    body = str(comment.get("body") or "")
    login = str((comment.get("user") or {}).get("login", ""))
    created_at = str(comment.get("created_at") or "")
    parsed = _core.parse_request(body)
    return (
        parsed is not None
        and str(comment.get("id") or "") == anchor["REQUEST_COMMENT_ID"]
        and login == anchor["REQUEST_AUTHOR"]
        and created_at == anchor["REQUEST_CREATED_AT"]
        and str(comment.get("updated_at") or "") == created_at
        and hashlib.sha256(body.encode("utf-8")).hexdigest() == anchor["REQUEST_BODY_SHA256"]
        and all(anchor[key] == parsed[key] for key in _core.REQUEST_FIELDS)
    )


def _normalize_anchor_trust(
    comments: list[dict], *, reviews: list[dict], policy: dict,
    repo_root: str | Path, head: str, repository: str, pr_number: int,
) -> list[dict]:
    """Recover server-proven request trust when REST hides private org membership."""
    by_comment, trusted_authors = _eligible_anchor_map(
        reviews=reviews, policy=policy, repo_root=repo_root, head=head,
        repository=repository, pr_number=pr_number,
    )
    normalized: list[dict] = []
    for comment in comments:
        clone = deepcopy(comment)
        try:
            comment_id = int(comment.get("id") or 0)
        except (TypeError, ValueError):
            comment_id = 0
        anchor = by_comment.get(comment_id)
        if anchor is not None:
            if _anchor_matches_comment(anchor, comment):
                clone["author_association"] = anchor["REQUEST_AUTHOR_ASSOCIATION"]
            normalized.append(clone)
            continue

        login = str((comment.get("user") or {}).get("login", "")).casefold()
        if login in trusted_authors:
            # Conservative only: this can add edit/blocking failures but cannot create
            # a valid current request because current request identity still needs its
            # own exact immutable anchor.
            clone["author_association"] = trusted_authors[login]
        normalized.append(clone)
    return normalized


def _pre_rollout_request_candidate(
    comment: dict, *, cutoff: datetime, repository: str, pr_number: int,
) -> bool:
    body = str(comment.get("body") or "")
    created = _strict_comment_time(comment)
    return (
        _request_command_present(body)
        and _core._issue_comment_identity(comment, repository, pr_number)
        and _core.REQUEST_MARKER not in body
        and _core.parse_request(body) is None
        and created is not None
        and created < cutoff
    )


def _filter_pre_rollout_unstructured_requests(
    comments: list[dict], *, policy: dict, repo_root: str | Path, head: str,
    repository: str, pr_number: int,
) -> list[dict]:
    rollout_commit = _configured_rollout_commit(policy, repository)
    if rollout_commit is None:
        return comments
    if not _core.is_ancestor(repo_root, rollout_commit, head):
        return comments
    cutoff = _request_anchor_rollout_time(repo_root, rollout_commit)
    if cutoff is None:
        return comments

    return [
        comment for comment in comments
        if not _pre_rollout_request_candidate(
            comment, cutoff=cutoff, repository=repository, pr_number=pr_number
        )
    ]


def _conservative_pre_rollout_blocker_comments(
    comments: list[dict], *, policy: dict, repo_root: str | Path, head: str,
    repository: str, pr_number: int,
) -> list[dict]:
    """Preserve observable legacy request history only for blocker discovery."""
    rollout_commit = _configured_rollout_commit(policy, repository)
    if rollout_commit is None or not _core.is_ancestor(repo_root, rollout_commit, head):
        return comments
    cutoff = _request_anchor_rollout_time(repo_root, rollout_commit)
    if cutoff is None:
        return comments

    normalized: list[dict] = []
    for comment in comments:
        clone = deepcopy(comment)
        body = str(comment.get("body") or "")
        created = _strict_comment_time(comment)
        same_pr = _core._issue_comment_identity(comment, repository, pr_number)
        edited = (
            bool(comment.get("created_at"))
            and bool(comment.get("updated_at"))
            and comment.get("updated_at") != comment.get("created_at")
        )
        if same_pr and created is not None and created < cutoff and (
            _request_command_present(body) or edited
        ):
            clone["author_association"] = "COLLABORATOR"
            if edited and not _request_command_present(body):
                clone["body"] = "@codex review\n\nlegacy pre-rollout edited request candidate"
        normalized.append(clone)
    return normalized


def _legacy_trusted_blocking_finding_exists(
    comments: list[dict], *, reviews: list[dict], policy: dict,
    repo_root: str | Path, head: str, repository: str, pr_number: int,
) -> bool:
    """Fail closed on surviving legacy P0/P1 even if its request was deleted.

    A request launched before registry rollout can complete asynchronously after the
    rollout commit. The first valid immutable post-rollout request anchor is therefore
    the deterministic upper boundary of the legacy in-flight window. A trusted P0/P1
    before that boundary remains blocking even if its initiating request disappeared
    from REST. This path only adds FAIL; it never creates review identity or PASS.
    """
    rollout_commit = _configured_rollout_commit(policy, repository)
    if rollout_commit is None or not _core.is_ancestor(repo_root, rollout_commit, head):
        return False
    cutoff = _request_anchor_rollout_time(repo_root, rollout_commit)
    if cutoff is None:
        return False

    post_rollout_anchor_times: list[datetime] = []
    for _, anchor in _core._eligible_request_anchors(
        reviews=reviews,
        policy=policy,
        repo_root=repo_root,
        head=head,
        repository=repository,
        pr_number=pr_number,
    ):
        if anchor["REQUEST_VALID"] != "true":
            continue
        request_time = _strict_timestamp(anchor["REQUEST_CREATED_AT"])
        if request_time is not None and request_time >= cutoff:
            post_rollout_anchor_times.append(request_time)
    legacy_window_end = min(post_rollout_anchor_times) if post_rollout_anchor_times else cutoff

    reviewer_ids: set[str] = set()
    for reviewer_class in ("fast", "deep"):
        reviewer_ids.update(policy.get("reviewer_preferences", {}).get(reviewer_class, []))
    trusted_logins: set[str] = set()
    for reviewer_id in reviewer_ids:
        trusted_logins.update(_core._trusted_logins(policy, reviewer_id))
    if not trusted_logins:
        return True

    for comment in comments:
        created = _strict_comment_time(comment)
        login = str((comment.get("user") or {}).get("login", "")).casefold()
        if (
            _core._issue_comment_identity(comment, repository, pr_number)
            and created is not None
            and created < legacy_window_end
            and login in trusted_logins
            and _core.BLOCKING_FINDING_RE.search(str(comment.get("body") or ""))
        ):
            return True
    return False


def _compat_parse_clean_result(body: str) -> str | None:
    exact = _original_parse_clean_result(body)
    if exact is not None:
        return exact

    text = (body or "").strip()
    lines = text.splitlines()
    if not lines or not lines[0].startswith(_CLEAN_PREFIX + " "):
        return None

    flair = lines[0][len(_CLEAN_PREFIX) + 1:]
    if flair not in _ALLOWED_CLEAN_FLAIR:
        return None

    normalized = "\n".join([_CLEAN_PREFIX, *lines[1:]])
    return _original_parse_clean_result(normalized)


def _compat_fetch_review_source(
    repository: str, pr_number: int, source_url: str, token: str
) -> tuple[str, dict]:
    saved = _core.fetch_json
    _core.fetch_json = globals().get("fetch_json", _original_fetch_json)
    try:
        return _original_fetch_review_source(repository, pr_number, source_url, token)
    finally:
        _core.fetch_json = saved


def _compat_blocking_findings(*, comments: list[dict], **kwargs) -> bool:
    if _legacy_trusted_blocking_finding_exists(
        comments,
        reviews=kwargs["reviews"],
        policy=kwargs["policy"], repo_root=kwargs["repo_root"], head=kwargs["head"],
        repository=kwargs["repository"], pr_number=kwargs["pr_number"],
    ):
        return True
    conservative = _conservative_pre_rollout_blocker_comments(
        comments,
        policy=kwargs["policy"], repo_root=kwargs["repo_root"], head=kwargs["head"],
        repository=kwargs["repository"], pr_number=kwargs["pr_number"],
    )
    return _original_blocking_findings(comments=conservative, **kwargs)


def _compat_issue_comment_result(comments: list[dict], **kwargs) -> dict:
    filtered = _filter_pre_rollout_unstructured_requests(
        comments,
        policy=kwargs["policy"], repo_root=kwargs["repo_root"], head=kwargs["head"],
        repository=kwargs["repository"], pr_number=kwargs["pr_number"],
    )
    return _original_issue_comment_result(filtered, **kwargs)


def _compat_verify_records(comments: list[dict], **kwargs) -> dict:
    normalized = _normalize_anchor_trust(
        comments,
        reviews=kwargs.get("reviews") or [],
        policy=kwargs["policy"], repo_root=kwargs["repo_root"], head=kwargs["head"],
        repository=kwargs["repository"], pr_number=kwargs["pr_number"],
    )
    saved_source = _core.fetch_review_source
    saved_json = _core.fetch_json
    saved_resolve = _core.resolve_reviewed_prefix
    _core.fetch_review_source = globals().get("fetch_review_source", _compat_fetch_review_source)
    _core.fetch_json = globals().get("fetch_json", _original_fetch_json)
    _core.resolve_reviewed_prefix = globals().get(
        "resolve_reviewed_prefix", _original_resolve_reviewed_prefix
    )
    try:
        return _original_verify_records(normalized, **kwargs)
    finally:
        _core.fetch_review_source = saved_source
        _core.fetch_json = saved_json
        _core.resolve_reviewed_prefix = saved_resolve


_core.parse_clean_result = _compat_parse_clean_result
_core._blocking_findings_for_current_generation = _compat_blocking_findings
_core._verify_issue_comment_result = _compat_issue_comment_result
_core.verify_records = _compat_verify_records

for _name in dir(_core):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_core, _name)

globals()["REQUEST_ANCHOR_ROLLOUT_COMMIT"] = REQUEST_ANCHOR_ROLLOUT_COMMIT
globals()["_configured_rollout_commit"] = _configured_rollout_commit
globals()["_request_anchor_rollout_time"] = _request_anchor_rollout_time
globals()["_normalize_anchor_trust"] = _normalize_anchor_trust
globals()["_filter_pre_rollout_unstructured_requests"] = _filter_pre_rollout_unstructured_requests
globals()["_legacy_trusted_blocking_finding_exists"] = _legacy_trusted_blocking_finding_exists
globals()["_compat_parse_clean_result"] = _compat_parse_clean_result
globals()["fetch_json"] = _original_fetch_json
globals()["fetch_review_source"] = _compat_fetch_review_source
globals()["resolve_reviewed_prefix"] = _original_resolve_reviewed_prefix


if __name__ == "__main__":
    raise SystemExit(_core.main())
