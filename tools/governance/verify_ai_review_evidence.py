#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import subprocess
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

REQUEST_ANCHOR_ROLLOUT_COMMIT = "dbed59b9cfab1e8a66ac9e0a5056053718980ce3"

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
_ALLOWED_CLEAN_FLAIR = {
    "Swish!", "Hooray!", "Chef's kiss.", "Breezy!", "Nice work!", "Bravo.",
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


def _comment_order(comment: dict) -> tuple[datetime, int] | None:
    stamp = _strict_comment_time(comment)
    if stamp is None:
        return None
    try:
        comment_id = int(comment.get("id") or 0)
    except (TypeError, ValueError):
        return None
    if comment_id <= 0:
        return None
    return stamp, comment_id


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


def _identity_valid_request_anchors(
    *, reviews: list[dict], policy: dict, repository: str, pr_number: int,
) -> list[dict[str, str]]:
    """Return all valid same-PR immutable anchors without current-head eligibility filters."""
    anchor_logins = _core._anchor_logins(policy)
    pull_url = f"https://api.github.com/repos/{repository}/pulls/{pr_number}"
    anchors: list[dict[str, str]] = []
    seen_comment_ids: dict[int, dict[str, str]] = {}
    for review in reviews:
        body = str(review.get("body") or "")
        login = str((review.get("user") or {}).get("login", "")).casefold()
        if _core.REQUEST_ANCHOR_MARKER not in body or login not in anchor_logins:
            continue
        anchor = _core.parse_request_anchor(body)
        if anchor is None:
            raise RuntimeError("trusted review-request anchor is malformed")
        dispatch_head = anchor["DISPATCH_HEAD"]
        if (
            review.get("pull_request_url") != pull_url
            or review.get("commit_id") != dispatch_head
            or str(review.get("state") or "").upper() != "COMMENTED"
        ):
            raise RuntimeError("trusted review-request anchor identity is malformed")
        if anchor["REQUEST_VALID"] != "true":
            continue
        if anchor["REQUEST_AUTHOR_ASSOCIATION"] not in _core.TRUSTED_ASSOCIATIONS:
            raise RuntimeError("valid request anchor has an untrusted author association")
        if anchor["REVIEWED_HEAD"] != dispatch_head:
            raise RuntimeError("valid request anchor reviewed head differs from dispatch head")
        request_time = _strict_timestamp(anchor["REQUEST_CREATED_AT"])
        try:
            comment_id = int(anchor["REQUEST_COMMENT_ID"])
        except (TypeError, ValueError):
            raise RuntimeError("valid request anchor comment identity is malformed") from None
        if request_time is None or comment_id <= 0:
            raise RuntimeError("valid request anchor ordering metadata is malformed")
        previous = seen_comment_ids.get(comment_id)
        if previous is not None and previous != anchor:
            raise RuntimeError("request anchor comment identity is ambiguous")
        seen_comment_ids[comment_id] = anchor
        anchors.append(anchor)
    return anchors


def _eligible_anchor_map(
    *, reviews: list[dict], policy: dict, repo_root: str | Path,
    head: str, repository: str, pr_number: int,
) -> dict[int, dict[str, str]]:
    by_comment: dict[int, dict[str, str]] = {}
    for _, anchor in _core._eligible_request_anchors(
        reviews=reviews, policy=policy, repo_root=repo_root, head=head,
        repository=repository, pr_number=pr_number,
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
    return by_comment


def _all_valid_request_anchor_orders(
    *, reviews: list[dict], policy: dict, repository: str, pr_number: int,
) -> list[tuple[datetime, int]]:
    """Validate immutable anchor identity without current-head eligibility filters."""
    orders: list[tuple[datetime, int]] = []
    for anchor in _identity_valid_request_anchors(
        reviews=reviews, policy=policy, repository=repository, pr_number=pr_number,
    ):
        request_time = _strict_timestamp(anchor["REQUEST_CREATED_AT"])
        comment_id = int(anchor["REQUEST_COMMENT_ID"])
        if request_time is None or comment_id <= 0:
            raise RuntimeError("valid request anchor ordering metadata is malformed")
        orders.append((request_time, comment_id))
    return orders


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


def _historical_anchor_trusted_edit_exists(
    comments: list[dict], *, reviews: list[dict], policy: dict,
    repository: str, pr_number: int,
) -> bool:
    """Use historical anchor identity only to add fail-closed edit detection, never PASS authority."""
    anchors = _identity_valid_request_anchors(
        reviews=reviews, policy=policy, repository=repository, pr_number=pr_number,
    )
    trusted_authors = {anchor["REQUEST_AUTHOR"].casefold() for anchor in anchors}
    by_id: dict[int, dict] = {}
    for comment in comments:
        try:
            comment_id = int(comment.get("id") or 0)
        except (TypeError, ValueError):
            continue
        if comment_id > 0:
            by_id[comment_id] = comment

    for anchor in anchors:
        comment = by_id.get(int(anchor["REQUEST_COMMENT_ID"]))
        if comment is not None and not _anchor_matches_comment(anchor, comment):
            return True

    for comment in comments:
        if not _core._issue_comment_identity(comment, repository, pr_number):
            continue
        login = str((comment.get("user") or {}).get("login", "")).casefold()
        if login not in trusted_authors:
            continue
        created_at = str(comment.get("created_at") or "")
        updated_at = str(comment.get("updated_at") or "")
        if created_at and updated_at and updated_at != created_at:
            return True
    return False


def _normalize_anchor_trust(
    comments: list[dict], *, reviews: list[dict], policy: dict,
    repo_root: str | Path, head: str, repository: str, pr_number: int,
) -> list[dict]:
    """Restore association only for an exact current-eligible immutable request anchor."""
    by_comment = _eligible_anchor_map(
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
        if anchor is not None and _anchor_matches_comment(anchor, comment):
            clone["author_association"] = anchor["REQUEST_AUTHOR_ASSOCIATION"]
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
    if rollout_commit is None or not _core.is_ancestor(repo_root, rollout_commit, head):
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
    """Retain trusted blockers from pre-registry and in-flight legacy generations."""
    rollout_commit = _configured_rollout_commit(policy, repository)
    if rollout_commit is None or not _core.is_ancestor(repo_root, rollout_commit, head):
        return False
    cutoff = _request_anchor_rollout_time(repo_root, rollout_commit)
    if cutoff is None:
        return False

    anchor_orders = [
        order for order in _all_valid_request_anchor_orders(
            reviews=reviews, policy=policy, repository=repository, pr_number=pr_number
        )
        if order[0] >= cutoff
    ]
    legacy_window_end: tuple[datetime, int] | None = min(anchor_orders) if anchor_orders else None

    reviewer_ids: set[str] = set()
    for reviewer_class in ("fast", "deep"):
        reviewer_ids.update(policy.get("reviewer_preferences", {}).get(reviewer_class, []))
    trusted_logins: set[str] = set()
    for reviewer_id in reviewer_ids:
        trusted_logins.update(_core._trusted_logins(policy, reviewer_id))
    if not trusted_logins:
        return True

    for comment in comments:
        order = _comment_order(comment)
        login = str((comment.get("user") or {}).get("login", "")).casefold()
        if (
            _core._issue_comment_identity(comment, repository, pr_number)
            and order is not None
            and (legacy_window_end is None or order < legacy_window_end)
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
        comments, reviews=kwargs["reviews"], policy=kwargs["policy"],
        repo_root=kwargs["repo_root"], head=kwargs["head"],
        repository=kwargs["repository"], pr_number=kwargs["pr_number"],
    ):
        return True
    conservative = _conservative_pre_rollout_blocker_comments(
        comments, policy=kwargs["policy"], repo_root=kwargs["repo_root"],
        head=kwargs["head"], repository=kwargs["repository"], pr_number=kwargs["pr_number"],
    )
    return _original_blocking_findings(comments=conservative, **kwargs)


def _compat_issue_comment_result(comments: list[dict], **kwargs) -> dict:
    filtered = _filter_pre_rollout_unstructured_requests(
        comments, policy=kwargs["policy"], repo_root=kwargs["repo_root"],
        head=kwargs["head"], repository=kwargs["repository"], pr_number=kwargs["pr_number"],
    )
    return _original_issue_comment_result(filtered, **kwargs)


def _compat_verify_records(comments: list[dict], **kwargs) -> dict:
    reviews = kwargs.get("reviews") or []
    if _historical_anchor_trusted_edit_exists(
        comments, reviews=reviews, policy=kwargs["policy"],
        repository=kwargs["repository"], pr_number=kwargs["pr_number"],
    ):
        raise RuntimeError("trusted maintainer comment or immutable request anchor was edited")
    normalized = _normalize_anchor_trust(
        comments, reviews=reviews, policy=kwargs["policy"],
        repo_root=kwargs["repo_root"], head=kwargs["head"],
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
