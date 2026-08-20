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
    """Recover server-proven request trust when REST hides private org membership.

    The issue-comment webhook records the authoritative association in an immutable
    github-actions review anchor. Public/repository-scoped REST can later expose the
    same organization member as CONTRIBUTOR. Only an exact anchor/comment match may
    restore the request's association. Other comments by that already anchored author
    are treated as trusted only for the core's fail-closed edit/blocker checks.
    """
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
    """Treat legacy request syntax as trusted only for blocker discovery.

    This can only make the gate fail more often: it never supplies current PASS
    authority or request identity.
    """
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
        if (
            _request_command_present(body)
            and _core._issue_comment_identity(comment, repository, pr_number)
            and created is not None
            and created < cutoff
        ):
            clone["author_association"] = "COLLABORATOR"
        normalized.append(clone)
    return normalized


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


def _compat_blocking_findings(*, comments: list[dict], **kwargs) -> bool:
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
    return _original_verify_records(normalized, **kwargs)


_core.parse_clean_result = _compat_parse_clean_result
_core._blocking_findings_for_current_generation = _compat_blocking_findings
_core._verify_issue_comment_result = _compat_issue_comment_result
_core.verify_records = _compat_verify_records

# Re-export the established verifier API so existing tests/callers remain unchanged.
for _name in dir(_core):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_core, _name)

# Keep compatibility controls visible for regression tests and diagnostics.
globals()["REQUEST_ANCHOR_ROLLOUT_COMMIT"] = REQUEST_ANCHOR_ROLLOUT_COMMIT
globals()["_configured_rollout_commit"] = _configured_rollout_commit
globals()["_request_anchor_rollout_time"] = _request_anchor_rollout_time
globals()["_normalize_anchor_trust"] = _normalize_anchor_trust
globals()["_filter_pre_rollout_unstructured_requests"] = _filter_pre_rollout_unstructured_requests
globals()["_compat_parse_clean_result"] = _compat_parse_clean_result


if __name__ == "__main__":
    raise SystemExit(_core.main())
