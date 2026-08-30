#!/usr/bin/env python3
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
import re
import types
import urllib.request
from pathlib import Path

_ENTRYPOINT = Path(__file__).resolve()
_COMPAT_PATH = _ENTRYPOINT.with_name("verify_ai_review_evidence_compat_v1.py")
_v1 = types.ModuleType("verify_ai_review_evidence_compat_v1_runtime")
_v1.__file__ = str(_ENTRYPOINT)
_v1.__package__ = None
exec(compile(_COMPAT_PATH.read_bytes(), str(_ENTRYPOINT), "exec"), _v1.__dict__)

for _name in dir(_v1):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_v1, _name)

_CLEAN_PREFIX = "Codex Review: Didn't find any major issues."
_OBSERVED_CLEAN_FLAIRS = {
    "Already looking forward to the next diff.",
    "Another round soon, please!",
    "Keep it up!",
}
_CODEX_SUMMARY_MARKER = "<!-- codex-pull-request-review-summary -->"
_CODEX_SUMMARY_APP = "chatgpt-codex-connector"
_CODEX_SUMMARY_ROW = re.compile(
    r'^\| 📝 \*\*Code Review\*\* \| ✅ \*\*Completed\*\* '
    r'<relative-time datetime="([^"]+)">[^<]*</relative-time> '
    r'\| `([0-9a-f]{7,40})` \| Manual request \|$'
)
_REVIEWED_COMMIT_LINE = re.compile(
    r'^\*\*Reviewed commit:\*\* `([0-9a-f]{7,40})`$', re.MULTILINE
)
_P2_FINDING_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?"
    r"(?:\[P2\]|P2\b|(?:<sub>){1,2}!\[P2 Badge\])"
)
_FINDING_LIKE_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?"
    r"(?:\[P[0-9]+\]|P[0-9]+\b|(?:<sub>){1,2}!\[P[0-9]+ Badge\])"
)
_TRACKED_P2_REPLY_RE = re.compile(r"^Tracked in #([1-9][0-9]*)\.$")
_P2_DISPOSITION_LIKE_RE = re.compile(r"^\s*tracked\s+in\b", re.IGNORECASE)
_TRUSTED_MAINTAINER_ASSOCIATIONS = {"OWNER", "MEMBER", "COLLABORATOR"}
_POSITIVE_DECIMAL_RE = re.compile(r"^[1-9][0-9]*$")


def _compat_parse_clean_result(body: str) -> str | None:
    """Accept only the newly observed exact cosmetic Codex clean-result suffix."""
    exact = _v1._compat_parse_clean_result(body)
    if exact is not None:
        return exact
    text = (body or "").strip()
    lines = text.splitlines()
    if not lines or not lines[0].startswith(f"{_CLEAN_PREFIX} "):
        return None
    flair = lines[0][len(_CLEAN_PREFIX) + 1:]
    if flair not in _OBSERVED_CLEAN_FLAIRS:
        return None
    normalized = "\n".join([_CLEAN_PREFIX, *lines[1:]])
    return _v1._original_parse_clean_result(normalized)


def _compat_fetch_review_source_v2(
    repository: str, pr_number: int, source_url: str, token: str
) -> tuple[str, dict]:
    """Preserve the v1 entrypoint's injectable fetch_json hook for direct calls."""
    saved = _v1.fetch_json
    _v1.fetch_json = globals().get("fetch_json", saved)
    try:
        return _v1._compat_fetch_review_source(repository, pr_number, source_url, token)
    finally:
        _v1.fetch_json = saved


def _compat_verify_records_v2(comments: list[dict], **kwargs) -> dict:
    """Preserve the v1 entrypoint's injectable network/revision hooks."""
    saved = {
        name: getattr(_v1, name)
        for name in ("fetch_review_source", "fetch_json", "resolve_reviewed_prefix")
    }
    for name, fallback in saved.items():
        setattr(_v1, name, globals().get(name, fallback))
    try:
        return _v1._compat_verify_records(comments, **kwargs)
    finally:
        for name, value in saved.items():
            setattr(_v1, name, value)


def _utc_timestamp(raw: object) -> datetime | None:
    if not isinstance(raw, str) or not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _strict_positive_int(raw: object) -> int | None:
    return raw if type(raw) is int and raw > 0 else None


def _strict_graphql_database_id(raw: object) -> int | None:
    if type(raw) is int and raw > 0:
        return raw
    if isinstance(raw, str) and _POSITIVE_DECIMAL_RE.fullmatch(raw):
        return int(raw)
    return None


def _strict_issue_comment_order(comment: dict) -> tuple[datetime, int] | None:
    created_at = _utc_timestamp(comment.get("created_at"))
    comment_id = _strict_positive_int(comment.get("id"))
    if created_at is None or comment_id is None:
        return None
    return created_at, comment_id


def _request_anchor_order(anchor: dict[str, str]) -> tuple[datetime, int]:
    request_at = _utc_timestamp(anchor.get("REQUEST_CREATED_AT"))
    raw_id = anchor.get("REQUEST_COMMENT_ID")
    if request_at is None or not isinstance(raw_id, str) or not _POSITIVE_DECIMAL_RE.fullmatch(raw_id):
        raise RuntimeError("review-evidence envelope request ordering is malformed")
    return request_at, int(raw_id)


def _parse_completed_summary(body: str) -> tuple[datetime, str] | None:
    if body.count(_CODEX_SUMMARY_MARKER) != 1 or body.count("## Codex Review Summary") != 1:
        return None
    rows = [line.strip() for line in body.splitlines() if "**Code Review**" in line]
    if len(rows) != 1:
        return None
    match = _CODEX_SUMMARY_ROW.fullmatch(rows[0])
    if match is None:
        return None
    completed = _utc_timestamp(match.group(1))
    if completed is None:
        return None
    return completed, match.group(2)


def _matching_eligible_anchors(
    *, policy: dict, repo_root: str | Path, tier: str, fingerprint: str,
    head: str, repository: str, pr_number: int, reviews: list[dict],
) -> list[tuple[dict, dict[str, str]]]:
    required_class = policy["review_tiers"][tier]["reviewer_class"]
    allowed_classes = {required_class} if required_class == "deep" else {"fast", "deep"}
    matches: list[tuple[dict, dict[str, str]]] = []
    for review, anchor in _v1._core._eligible_request_anchors(
        reviews=reviews,
        policy=policy,
        repo_root=repo_root,
        head=head,
        repository=repository,
        pr_number=pr_number,
    ):
        reviewer_class = anchor.get("REVIEWER_CLASS", "")
        reviewer_id = anchor.get("REVIEWER_ID", "")
        if (
            anchor.get("REQUEST_VALID") == "true"
            and anchor.get("REVIEW_TIER") == tier
            and anchor.get("REVIEW_FINGERPRINT") == fingerprint
            and reviewer_class in allowed_classes
            and _v1._core.reviewer_allowed(policy, reviewer_class, reviewer_id)
        ):
            matches.append((review, anchor))
    return matches


def _eligible_summary_anchor(
    *, policy: dict, repo_root: str | Path, tier: str, fingerprint: str,
    head: str, repository: str, pr_number: int, reviews: list[dict],
) -> tuple[dict, dict[str, str]]:
    matches = _matching_eligible_anchors(
        policy=policy, repo_root=repo_root, tier=tier, fingerprint=fingerprint,
        head=head, repository=repository, pr_number=pr_number, reviews=reviews,
    )
    if len(matches) != 1:
        raise RuntimeError("current Codex summary requires one eligible immutable request anchor")
    return matches[0]


def _envelope_reviewed_heads(
    *, policy: dict, repo_root: str | Path, tier: str, fingerprint: str,
    head: str, repository: str, pr_number: int, reviews: list[dict],
) -> tuple[tuple[str, ...], tuple[datetime, int] | None]:
    """Inspect both current PR head and the sole reusable anchored generation."""
    matches = _matching_eligible_anchors(
        policy=policy, repo_root=repo_root, tier=tier, fingerprint=fingerprint,
        head=head, repository=repository, pr_number=pr_number, reviews=reviews,
    )
    if len(matches) > 1:
        raise RuntimeError("review-evidence envelope has ambiguous eligible immutable request anchors")
    anchored_head = matches[0][1]["REVIEWED_HEAD"] if matches else head
    request_order = _request_anchor_order(matches[0][1]) if matches else None
    return tuple(dict.fromkeys((head, anchored_head))), request_order


def _parse_observed_duplicate_clean_echo(body: str) -> str | None:
    """Return the reviewed prefix only for the complete observed Codex echo envelope."""
    lines = [line.strip() for line in (body or "").splitlines() if line.strip()]
    if len(lines) != 11 or not lines[0].startswith(f"{_CLEAN_PREFIX} "):
        return None
    flair = lines[0][len(_CLEAN_PREFIX) + 1:]
    if flair not in {"Delightful!", ":tada:"}:
        return None
    reviewed = _REVIEWED_COMMIT_LINE.fullmatch(lines[1])
    if reviewed is None:
        return None
    prefix = reviewed.group(1)
    expected = [
        f"{_CLEAN_PREFIX} {flair}",
        f"**Reviewed commit:** `{prefix}`",
        "<details> <summary>ℹ️ About Codex in GitHub</summary>",
        "<br/>",
        "[Your team has set up Codex to review pull requests in this repo]"
        "(https://chatgpt.com/codex/cloud/settings/general). Reviews are triggered when you",
        "- Open a pull request for review",
        "- Mark a draft as ready",
        '- Comment "@codex review".',
        "If Codex has suggestions, it will comment; otherwise it will react with 👍.",
        'Codex can also answer questions or update the PR. Try commenting "@codex address that feedback".',
        "</details>",
    ]
    return prefix if lines == expected else None


def _same_generation_clean_echoes(
    comments: list[dict], *, summary: dict, trusted_logins: set[str],
    repo_root: str | Path, reviewed_head: str, request_at: datetime,
    reaction_at: datetime, repository: str, pr_number: int,
) -> list[dict]:
    """Find at most one redundant clean-result echo superseded by summary+reaction."""
    echoes: list[dict] = []
    for comment in comments:
        if comment is summary:
            continue
        login = str((comment.get("user") or {}).get("login", "")).casefold()
        app_slug = str((comment.get("performed_via_github_app") or {}).get("slug", ""))
        if (
            login not in trusted_logins
            or app_slug != _CODEX_SUMMARY_APP
            or not _v1._core._issue_comment_identity(comment, repository, pr_number)
        ):
            continue
        created_at = _utc_timestamp(comment.get("created_at"))
        updated_at = _utc_timestamp(comment.get("updated_at"))
        if created_at is None or updated_at is None or updated_at != created_at:
            continue
        if not (request_at < created_at <= reaction_at):
            continue
        body = str(comment.get("body") or "")
        if _FINDING_LIKE_RE.search(body):
            raise RuntimeError("Codex finding exists in the same-generation clean echo")
        prefix = _parse_observed_duplicate_clean_echo(body)
        if prefix is None:
            continue
        resolved = _v1._core.resolve_reviewed_prefix(repo_root, prefix)
        if resolved != reviewed_head:
            continue
        echoes.append(comment)
    if len(echoes) > 1:
        raise RuntimeError("same-generation Codex clean echo is ambiguous")
    return echoes


def _fetch_graphql(query: str, variables: dict[str, object], token: str) -> dict:
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode("utf-8"),
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "oteryn-ai-review-gate",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        value = json.load(response)
    if not isinstance(value, dict) or value.get("errors") or not isinstance(value.get("data"), dict):
        raise RuntimeError("GitHub GraphQL review-thread response is malformed")
    return value["data"]


def fetch_review_threads(repository: str, pr_number: int, token: str) -> list[dict]:
    """Fetch complete review-thread state; a truncated nested connection fails closed."""
    if not re.fullmatch(r"[^/\s]+/[^/\s]+", repository) or pr_number <= 0:
        raise RuntimeError("review-thread request identity is malformed")
    owner, name = repository.split("/", 1)
    query = """
query($owner: String!, $name: String!, $number: Int!, $after: String) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      reviewThreads(first: 100, after: $after) {
        nodes {
          id
          isResolved
          comments(first: 100) {
            nodes {
              fullDatabaseId
              body
              author { login }
              authorAssociation
              createdAt
              lastEditedAt
            }
            pageInfo { hasNextPage }
          }
        }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
"""
    threads: list[dict] = []
    after: str | None = None
    while True:
        data = _fetch_graphql(
            query, {"owner": owner, "name": name, "number": pr_number, "after": after}, token
        )
        pull_request = ((data.get("repository") or {}).get("pullRequest"))
        connection = (pull_request or {}).get("reviewThreads") if isinstance(pull_request, dict) else None
        if not isinstance(connection, dict):
            raise RuntimeError("GitHub review-thread connection is malformed")
        nodes = connection.get("nodes")
        page_info = connection.get("pageInfo")
        if not isinstance(nodes, list) or any(not isinstance(node, dict) for node in nodes):
            raise RuntimeError("GitHub review-thread nodes are malformed")
        if not isinstance(page_info, dict) or type(page_info.get("hasNextPage")) is not bool:
            raise RuntimeError("GitHub review-thread pagination is malformed")
        for thread in nodes:
            comments = thread.get("comments")
            comment_page = comments.get("pageInfo") if isinstance(comments, dict) else None
            if not isinstance(comment_page, dict) or comment_page.get("hasNextPage") is not False:
                raise RuntimeError("GitHub review-thread comments are truncated or malformed")
        threads.extend(nodes)
        if page_info["hasNextPage"] is False:
            return threads
        cursor = page_info.get("endCursor")
        if not isinstance(cursor, str) or not cursor:
            raise RuntimeError("GitHub review-thread cursor is malformed")
        after = cursor


def _thread_comment_map(review_threads: object) -> dict[int, tuple[dict, list[dict]]]:
    if not isinstance(review_threads, list) or any(not isinstance(thread, dict) for thread in review_threads):
        raise RuntimeError("review-thread evidence is missing or malformed")
    by_comment: dict[int, tuple[dict, list[dict]]] = {}
    for thread in review_threads:
        thread_id = thread.get("id")
        comments = thread.get("comments")
        nodes = comments.get("nodes") if isinstance(comments, dict) else None
        page_info = comments.get("pageInfo") if isinstance(comments, dict) else None
        if (
            not isinstance(thread_id, str)
            or not thread_id
            or type(thread.get("isResolved")) is not bool
            or not isinstance(nodes, list)
            or any(not isinstance(node, dict) for node in nodes)
            or not isinstance(page_info, dict)
            or page_info.get("hasNextPage") is not False
        ):
            raise RuntimeError("review-thread evidence is malformed or truncated")
        for node in nodes:
            comment_id = _strict_graphql_database_id(node.get("fullDatabaseId"))
            if comment_id is None or comment_id in by_comment:
                raise RuntimeError("review-thread comment identity is malformed or ambiguous")
            by_comment[comment_id] = (thread, nodes)
    return by_comment


def _trusted_review_body_is_nonfinding(body: str, reviewed_head: str) -> bool:
    lines = [line.strip() for line in (body or "").splitlines() if line.strip()]
    if len(lines) != 12 or lines[0] != "### 💡 Codex Review":
        return False
    reviewed = _REVIEWED_COMMIT_LINE.fullmatch(lines[2])
    if reviewed is None or not reviewed_head.startswith(reviewed.group(1)):
        return False
    return lines == [
        "### 💡 Codex Review",
        "Here are some automated review suggestions for this pull request.",
        lines[2],
        "<details> <summary>ℹ️ About Codex in GitHub</summary>",
        "<br/>",
        "[Your team has set up Codex to review pull requests in this repo]"
        "(https://chatgpt.com/codex/cloud/settings/general). Reviews are triggered when you",
        "- Open a pull request for review",
        "- Mark a draft as ready",
        '- Comment "@codex review".',
        "If Codex has suggestions, it will comment; otherwise it will react with 👍.",
        'Codex can also answer questions or update the PR. Try commenting "@codex address that feedback".',
        "</details>",
    ]


def _open_same_repository_issue(
    *, issue_number: int, repository: str, token: str, tracker_issues: dict[int, dict] | None,
) -> dict:
    if tracker_issues is None:
        issue = _v1._core.fetch_json(
            f"https://api.github.com/repos/{repository}/issues/{issue_number}", token
        )
    else:
        issue = tracker_issues.get(issue_number)
    expected_repository_url = f"https://api.github.com/repos/{repository}"
    expected_issue_url = f"{expected_repository_url}/issues/{issue_number}"
    if (
        not isinstance(issue, dict)
        or issue.get("number") != issue_number
        or issue.get("state") != "open"
        or issue.get("repository_url") != expected_repository_url
        or issue.get("url") != expected_issue_url
        or ("pull_request" in issue and issue.get("pull_request") is not None)
    ):
        raise RuntimeError("P2 follow-up tracker is not an open same-repository issue")
    return issue


def _p2_follow_up_config(policy: dict) -> tuple[str, set[str]]:
    config = policy.get("p2_follow_up")
    if not isinstance(config, dict):
        raise RuntimeError("P2 follow-up policy is missing or malformed")
    associations = config.get("trusted_maintainer_associations")
    if (
        config.get("outcome") != "ACCEPTED_WITH_FOLLOW_UP"
        or config.get("thread_must_be_resolved") is not True
        or config.get("tracker_reply_format") != "Tracked in #<issue>."
        or config.get("tracker_must_be_open_same_repository_issue") is not True
        or not isinstance(associations, list)
        or set(associations) != _TRUSTED_MAINTAINER_ASSOCIATIONS
        or len(associations) != len(_TRUSTED_MAINTAINER_ASSOCIATIONS)
    ):
        raise RuntimeError("P2 follow-up policy is missing or malformed")
    return config["outcome"], set(associations)


def _reject_unenveloped_current_head_findings(
    *, reviews: list[dict], review_comments: list[dict], policy: dict,
    comments: list[dict], reviewed_head: str, repository: str, pr_number: int,
    request_order: tuple[datetime, int] | None = None,
) -> None:
    """Fail closed before legacy evidence can bypass current trusted review findings."""
    trusted_logins = {
        str(login).casefold()
        for values in policy.get("reviewer_source_logins", {}).values()
        for login in values
    }
    pull_url = f"https://api.github.com/repos/{repository}/pulls/{pr_number}"
    current_review_ids: set[int] = set()
    trusted_review_ids: set[int] = set()
    for review in reviews:
        if (
            str((review.get("user") or {}).get("login", "")).casefold() not in trusted_logins
            or review.get("pull_request_url") != pull_url
        ):
            continue
        commit_id = review.get("commit_id")
        if not isinstance(commit_id, str) or _v1._core.FULL_SHA.fullmatch(commit_id) is None:
            raise RuntimeError("trusted review commit identity is malformed")
        review_id = _strict_positive_int(review.get("id"))
        if review_id is not None:
            trusted_review_ids.add(review_id)
        if commit_id != reviewed_head:
            continue
        review_body = str(review.get("body") or "")
        if review.get("state") not in {"COMMENTED", "APPROVED"}:
            raise RuntimeError("trusted current-head review has an escalated or unknown state")
        if _P2_FINDING_RE.search(review_body):
            raise RuntimeError("current-head P2 finding requires the accepted Codex summary and follow-up envelope")
        if review_body and not _trusted_review_body_is_nonfinding(review_body, reviewed_head):
            raise RuntimeError("trusted current-head review body is unclassified")
        if review_id is not None:
            current_review_ids.add(review_id)
    for comment in review_comments:
        if (
            str((comment.get("user") or {}).get("login", "")).casefold() not in trusted_logins
            or comment.get("pull_request_url") != pull_url
        ):
            continue
        body = str(comment.get("body") or "")
        review_id = _strict_positive_int(comment.get("pull_request_review_id"))
        is_p2 = _P2_FINDING_RE.search(body) is not None
        if review_id is None or review_id not in current_review_ids:
            if review_id in trusted_review_ids:
                continue
            if body:
                raise RuntimeError("trusted inline finding has no exact known parent review")
            continue
        if is_p2:
            raise RuntimeError("current-head P2 finding requires the accepted Codex summary and follow-up envelope")
        raise RuntimeError("trusted current-generation inline finding is unclassified")
    for comment in comments:
        if (
            str((comment.get("user") or {}).get("login", "")).casefold() not in trusted_logins
            or not _v1._core._issue_comment_identity(comment, repository, pr_number)
        ):
            continue
        body = str(comment.get("body") or "")
        if _P2_FINDING_RE.search(body):
            raise RuntimeError("trusted P2 finding must use the accepted inline follow-up envelope")
        if request_order is not None and _FINDING_LIKE_RE.search(body):
            comment_order = _strict_issue_comment_order(comment)
            if comment_order is None or comment_order > request_order:
                raise RuntimeError("trusted post-request finding is outside the P2 inline envelope")


def _accepted_p2_follow_up(
    *, comments: list[dict], reviews: list[dict], review_comments: list[dict], review_threads: object,
    tracker_issues: dict[int, dict] | None, policy: dict, trusted_logins: set[str],
    reviewed_head: str, repository: str, pr_number: int, request_at: datetime,
    request_order: tuple[datetime, int], completed_at: datetime, token: str,
) -> dict | None:
    """Validate resolved exact-head P2 findings with durable same-repo issue tracking."""
    outcome, trusted_maintainer_associations = _p2_follow_up_config(policy)
    pull_url = f"https://api.github.com/repos/{repository}/pulls/{pr_number}"
    candidates: dict[int, datetime] = {}
    trusted_reviews: dict[int, dict] = {}
    current_review_ids: set[int] = set()
    for review in reviews:
        login = str((review.get("user") or {}).get("login", "")).casefold()
        if (
            login not in trusted_logins
            or review.get("pull_request_url") != pull_url
        ):
            continue
        review_id = _strict_positive_int(review.get("id"))
        if review_id is None:
            raise RuntimeError("trusted P2 review identity is malformed")
        if review_id in trusted_reviews:
            raise RuntimeError("trusted P2 review identity is ambiguous")
        trusted_reviews[review_id] = review
        commit_id = review.get("commit_id")
        if not isinstance(commit_id, str) or _v1._core.FULL_SHA.fullmatch(commit_id) is None:
            raise RuntimeError("trusted P2 review commit identity is malformed")
        if commit_id != reviewed_head:
            continue
        current_review_ids.add(review_id)
        review_body = str(review.get("body") or "")
        review_state = review.get("state")
        if review_state == "APPROVED":
            if _P2_FINDING_RE.search(review_body):
                raise RuntimeError("trusted P2 finding must be an inline root comment")
            if review_body and not _trusted_review_body_is_nonfinding(review_body, reviewed_head):
                raise RuntimeError("trusted current-head approved review body is unclassified")
            continue
        if review_state != "COMMENTED":
            raise RuntimeError("trusted current-head review has an escalated or unknown state")
        if _P2_FINDING_RE.search(review_body):
            raise RuntimeError("trusted P2 finding must be an inline root comment")
        if review_body and not _trusted_review_body_is_nonfinding(review_body, reviewed_head):
            raise RuntimeError("trusted current-head review body is unclassified")
        submitted_at = _utc_timestamp(review.get("submitted_at"))
        if submitted_at is None:
            raise RuntimeError("trusted P2 review timestamp is malformed")
        if request_at < submitted_at <= completed_at:
            if review_id in candidates:
                raise RuntimeError("trusted P2 review identity is ambiguous")
            candidates[review_id] = submitted_at

    candidate_review_id = next(iter(candidates)) if len(candidates) == 1 else None
    review_at = candidates.get(candidate_review_id) if candidate_review_id is not None else None
    p2_comments: list[dict] = []
    p2_comment_ids: set[int] = set()
    for comment in review_comments:
        login = str((comment.get("user") or {}).get("login", "")).casefold()
        if login not in trusted_logins or comment.get("pull_request_url") != pull_url:
            continue
        review_id = _strict_positive_int(comment.get("pull_request_review_id"))
        if review_id is None:
            if str(comment.get("body") or ""):
                raise RuntimeError("trusted inline finding identity is malformed")
            continue
        parent_review = trusted_reviews.get(review_id)
        if parent_review is None:
            body = str(comment.get("body") or "")
            if body:
                raise RuntimeError("trusted inline finding parent review is missing")
            continue
        if review_id not in current_review_ids:
            continue
        created_at = _utc_timestamp(comment.get("created_at"))
        updated_at = _utc_timestamp(comment.get("updated_at"))
        if (
            created_at is None
            or updated_at is None
            or updated_at < created_at
            or not (request_at < created_at <= completed_at)
        ):
            raise RuntimeError("trusted P2 inline finding metadata is malformed")
        if comment.get("in_reply_to_id") is not None:
            raise RuntimeError("trusted current-generation inline finding is not a root comment")
        if not _P2_FINDING_RE.search(str(comment.get("body") or "")):
            raise RuntimeError("trusted current-generation inline finding is unclassified")
        if review_id != candidate_review_id:
            raise RuntimeError("trusted P2 inline finding is outside the exact review generation")
        comment_id = _strict_positive_int(comment.get("id"))
        if comment_id is None or comment_id in p2_comment_ids:
            raise RuntimeError("trusted P2 inline finding identity is malformed")
        p2_comment_ids.add(comment_id)
        p2_comments.append(comment)

    for comment in comments:
        if (
            str((comment.get("user") or {}).get("login", "")).casefold() not in trusted_logins
            or not _v1._core._issue_comment_identity(comment, repository, pr_number)
            or not _FINDING_LIKE_RE.search(str(comment.get("body") or ""))
        ):
            continue
        comment_order = _strict_issue_comment_order(comment)
        if comment_order is None:
            raise RuntimeError("trusted finding issue-comment ordering is malformed")
        if comment_order > request_order:
            raise RuntimeError("trusted finding must be an accepted P2 inline root comment")

    if not p2_comments:
        return None
    if review_at is None:
        raise RuntimeError("trusted P2 review generation is missing or ambiguous")
    if callable(review_threads):
        review_threads = review_threads()

    thread_by_comment = _thread_comment_map(review_threads)
    thread_ids: set[str] = set()
    issue_numbers: set[int] = set()
    finding_ids: list[int] = []
    accepted_at = review_at
    for comment in p2_comments:
        comment_id = _strict_positive_int(comment.get("id"))
        if comment_id is None:
            raise RuntimeError("trusted P2 inline finding identity is malformed")
        thread_entry = thread_by_comment.get(comment_id)
        if thread_entry is None:
            raise RuntimeError("P2 inline finding has no exact review thread")
        thread, nodes = thread_entry
        if thread.get("isResolved") is not True:
            raise RuntimeError("P2 review thread is unresolved")
        root = next(
            (node for node in nodes if _strict_graphql_database_id(node.get("fullDatabaseId")) == comment_id),
            None,
        )
        if not isinstance(root, dict) or (
            root.get("body") != comment.get("body")
            or str((root.get("author") or {}).get("login", "")).casefold()
            != str((comment.get("user") or {}).get("login", "")).casefold()
            or root.get("createdAt") != comment.get("created_at")
            or root.get("lastEditedAt") is not None
        ):
            raise RuntimeError("P2 review-thread root identity is malformed or edited")
        root_at = _utc_timestamp(root.get("createdAt"))
        if root_at is None:
            raise RuntimeError("P2 review-thread root timestamp is malformed")

        trusted_replies: list[tuple[dict, datetime, re.Match[str]]] = []
        for node in nodes:
            if node is root:
                continue
            body = str(node.get("body") or "")
            if _FINDING_LIKE_RE.search(body):
                raise RuntimeError("P2 review thread contains an intermediate finding")
            tracker = _TRACKED_P2_REPLY_RE.fullmatch(body)
            if tracker is None:
                if _P2_DISPOSITION_LIKE_RE.search(body):
                    raise RuntimeError("P2 follow-up disposition is malformed")
                continue
            association = str(node.get("authorAssociation") or "")
            reply_at = _utc_timestamp(node.get("createdAt"))
            if (
                association not in trusted_maintainer_associations
                or node.get("lastEditedAt") is not None
                or reply_at is None
                or reply_at <= root_at
                or not str((node.get("author") or {}).get("login", "")).strip()
            ):
                raise RuntimeError("P2 follow-up disposition is malformed or edited")
            trusted_replies.append((node, reply_at, tracker))
        if len(trusted_replies) != 1:
            raise RuntimeError("P2 follow-up requires exactly one trusted maintainer disposition")
        _, disposition_at, tracker = trusted_replies[0]
        issue_number = int(tracker.group(1))
        _open_same_repository_issue(
            issue_number=issue_number, repository=repository, token=token,
            tracker_issues=tracker_issues,
        )
        thread_id = str(thread["id"])
        thread_ids.add(thread_id)
        issue_numbers.add(issue_number)
        finding_ids.append(comment_id)
        accepted_at = max(accepted_at, disposition_at)

    return {
        "review_outcome": outcome,
        "accepted_at": accepted_at,
        "p2_review_id": candidate_review_id,
        "finding_comment_ids": sorted(finding_ids),
        "review_thread_ids": sorted(thread_ids),
        "follow_up_issue_numbers": sorted(issue_numbers),
    }


def _normalize_current_codex_summary(
    comments: list[dict], *, pr_reactions: list[dict], policy: dict,
    repo_root: str | Path, tier: str, fingerprint: str, head: str,
    repository: str, pr_number: int, reviews: list[dict], review_comments: list[dict],
    review_threads: object, tracker_issues: dict[int, dict] | None, token: str,
) -> tuple[list[dict], dict | None]:
    configured_logins = {
        str(login).casefold()
        for values in policy.get("reviewer_source_logins", {}).values()
        for login in values
    }
    summary_candidates = [
        comment for comment in comments
        if _CODEX_SUMMARY_MARKER in str(comment.get("body") or "")
        and str((comment.get("user") or {}).get("login", "")).casefold() in configured_logins
    ]
    if not summary_candidates:
        reviewed_heads, request_order = _envelope_reviewed_heads(
            policy=policy, repo_root=repo_root, tier=tier, fingerprint=fingerprint,
            head=head, repository=repository, pr_number=pr_number, reviews=reviews,
        )
        for reviewed_head in reviewed_heads:
            _reject_unenveloped_current_head_findings(
                reviews=reviews, review_comments=review_comments, policy=policy,
                comments=comments, reviewed_head=reviewed_head,
                repository=repository, pr_number=pr_number, request_order=request_order,
            )
        return comments, None
    if len(summary_candidates) != 1:
        raise RuntimeError("trusted Codex review summary is ambiguous")

    _, anchor = _eligible_summary_anchor(
        policy=policy,
        repo_root=repo_root,
        tier=tier,
        fingerprint=fingerprint,
        head=head,
        repository=repository,
        pr_number=pr_number,
        reviews=reviews,
    )
    reviewer_id = anchor["REVIEWER_ID"]
    trusted_logins = _v1._core._trusted_logins(policy, reviewer_id)
    if not trusted_logins:
        raise RuntimeError("reviewer has no configured trusted source login")

    summary = summary_candidates[0]
    summary_login = str((summary.get("user") or {}).get("login", "")).casefold()
    app_slug = str((summary.get("performed_via_github_app") or {}).get("slug", ""))
    if (
        summary_login not in trusted_logins
        or app_slug != _CODEX_SUMMARY_APP
        or not _v1._core._issue_comment_identity(summary, repository, pr_number)
    ):
        raise RuntimeError("trusted Codex review summary identity is invalid")

    summary_body = str(summary.get("body") or "")
    if _FINDING_LIKE_RE.search(summary_body):
        raise RuntimeError("Codex finding exists in the review summary")
    parsed_summary = _parse_completed_summary(summary_body)
    if parsed_summary is None:
        raise RuntimeError("trusted Codex review summary is not the accepted completed shape")
    completed_at, prefix = parsed_summary
    reviewed_head = anchor["REVIEWED_HEAD"]
    resolved = _v1._core.resolve_reviewed_prefix(repo_root, prefix)
    if resolved is None or resolved != reviewed_head:
        raise RuntimeError("Codex summary reviewed-commit prefix does not match the request anchor")

    request_order = _request_anchor_order(anchor)
    request_at = request_order[0]
    summary_updated_at = _utc_timestamp(summary.get("updated_at"))
    if completed_at <= request_at:
        raise RuntimeError("Codex summary completion does not follow the current request")
    if summary_updated_at is None or summary_updated_at < completed_at:
        raise RuntimeError("Codex summary update timestamp precedes completion")
    if head != reviewed_head:
        _reject_unenveloped_current_head_findings(
            reviews=reviews, review_comments=review_comments, policy=policy,
            comments=comments, reviewed_head=head, repository=repository, pr_number=pr_number,
            request_order=request_order,
        )

    matching_reactions: list[dict] = []
    for reaction in pr_reactions:
        reaction_at = _utc_timestamp(reaction.get("created_at"))
        reaction_login = str((reaction.get("user") or {}).get("login", "")).casefold()
        if (
            reaction.get("content") == "+1"
            and reaction_login in trusted_logins
            and reaction_at is not None
            and reaction_at >= completed_at
            and reaction_at > request_at
        ):
            matching_reactions.append(reaction)
    if len(matching_reactions) > 1:
        raise RuntimeError("current Codex summary has ambiguous trusted post-completion PR reactions")
    p2_follow_up = _accepted_p2_follow_up(
        comments=comments, reviews=reviews, review_comments=review_comments, review_threads=review_threads,
        tracker_issues=tracker_issues, policy=policy,
        trusted_logins=trusted_logins,
        reviewed_head=reviewed_head,
        repository=repository,
        pr_number=pr_number,
        request_at=request_at,
        request_order=request_order,
        completed_at=completed_at,
        token=token,
    )
    if len(matching_reactions) == 1:
        reaction_at_raw = str(matching_reactions[0].get("created_at") or "")
        reaction_at = _utc_timestamp(reaction_at_raw)
        if reaction_at is None:
            raise RuntimeError("trusted Codex reaction timestamp is malformed")
        if p2_follow_up is not None:
            reaction_at_raw = max(reaction_at, p2_follow_up["accepted_at"]).isoformat().replace(
                "+00:00", "Z"
            )
        redundant_echoes = _same_generation_clean_echoes(
            comments,
            summary=summary,
            trusted_logins=trusted_logins,
            repo_root=repo_root,
            reviewed_head=reviewed_head,
            request_at=request_at,
            reaction_at=reaction_at,
            repository=repository,
            pr_number=pr_number,
        )
    else:
        if p2_follow_up is None:
            raise RuntimeError(
                "current Codex summary requires one trusted post-completion PR reaction "
                "or resolved P2 follow-up evidence"
            )
        reaction_at_raw = p2_follow_up["accepted_at"].isoformat().replace("+00:00", "Z")
        redundant_echoes = []

    synthetic = deepcopy(summary)
    synthetic["body"] = (
        f"{_CLEAN_PREFIX}\n\n"
        f"**Reviewed commit:** `{prefix}`"
    )
    synthetic["created_at"] = reaction_at_raw
    synthetic["updated_at"] = reaction_at_raw

    redundant_ids = {id(comment) for comment in redundant_echoes}
    return [
        synthetic if comment is summary else comment
        for comment in comments
        if id(comment) not in redundant_ids
    ], p2_follow_up


def _compat_verify_records_v3(comments: list[dict], **kwargs) -> dict:
    """Adapt the current Codex summary/reaction envelope into the preserved verifier."""
    pr_reactions = kwargs.pop("pr_reactions", None)
    review_threads = kwargs.pop("review_threads", None)
    tracker_issues = kwargs.pop("tracker_issues", None)
    accepted_follow_up: dict | None = None
    if pr_reactions is None:
        reviewed_heads, request_order = _envelope_reviewed_heads(
            policy=kwargs["policy"], repo_root=kwargs["repo_root"], tier=kwargs["tier"],
            fingerprint=kwargs["fingerprint"], head=kwargs["head"],
            repository=kwargs["repository"], pr_number=kwargs["pr_number"],
            reviews=kwargs.get("reviews") or [],
        )
        for reviewed_head in reviewed_heads:
            _reject_unenveloped_current_head_findings(
                reviews=kwargs.get("reviews") or [], review_comments=kwargs.get("review_comments") or [],
                policy=kwargs["policy"], comments=comments, reviewed_head=reviewed_head,
                repository=kwargs["repository"], pr_number=kwargs["pr_number"],
                request_order=request_order,
            )
    else:
        if not isinstance(pr_reactions, list) or any(not isinstance(item, dict) for item in pr_reactions):
            raise RuntimeError("pull request reactions response is malformed")
        comments, accepted_follow_up = _normalize_current_codex_summary(
            comments,
            pr_reactions=pr_reactions,
            policy=kwargs["policy"],
            repo_root=kwargs["repo_root"],
            tier=kwargs["tier"],
            fingerprint=kwargs["fingerprint"],
            head=kwargs["head"],
            repository=kwargs["repository"],
            pr_number=kwargs["pr_number"],
            reviews=kwargs.get("reviews") or [],
            review_comments=kwargs.get("review_comments") or [],
            review_threads=review_threads,
            tracker_issues=tracker_issues,
            token=kwargs["token"],
        )
    if accepted_follow_up is not None:
        accepted_finding_ids = set(accepted_follow_up["finding_comment_ids"])
        kwargs["review_comments"] = [
            {**comment, "updated_at": comment.get("created_at")}
            if _strict_positive_int(comment.get("id")) in accepted_finding_ids
            else comment
            for comment in kwargs.get("review_comments") or []
        ]
    result = _compat_verify_records_v2(comments, **kwargs)
    if accepted_follow_up is not None:
        result = dict(result)
        result.update({
            "review_outcome": accepted_follow_up["review_outcome"],
            "p2_review_id": accepted_follow_up["p2_review_id"],
            "finding_comment_ids": accepted_follow_up["finding_comment_ids"],
            "review_thread_ids": accepted_follow_up["review_thread_ids"],
            "follow_up_issue_numbers": accepted_follow_up["follow_up_issue_numbers"],
        })
    return result


def fetch_pr_reactions(repository: str, pr_number: int, token: str) -> list[dict]:
    return _v1._core._fetch_paginated(
        f"https://api.github.com/repos/{repository}/issues/{pr_number}/reactions", token
    )


def verify_live_review_evidence(
    *,
    repository: str,
    pr_number: int,
    token: str,
    policy: dict,
    repo_root: str | Path,
    tier: str,
    fingerprint: str,
    head: str,
    base: str,
) -> dict:
    """Verify the same live evidence envelope used by the required AI gate."""

    trusted_policy = deepcopy(policy)
    trusted_policy["_trusted_integration_base_sha"] = base
    return verify_records(
        _v1._core.fetch_comments(repository, pr_number, token),
        policy=trusted_policy,
        repo_root=repo_root,
        tier=tier,
        fingerprint=fingerprint,
        head=head,
        repository=repository,
        pr_number=pr_number,
        token=token,
        reviews=_v1._core.fetch_reviews(repository, pr_number, token),
        review_comments=_v1._core.fetch_review_comments(repository, pr_number, token),
        review_threads=fetch_review_threads(repository, pr_number, token),
        pr_reactions=fetch_pr_reactions(repository, pr_number, token),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--pr-number", required=True, type=int)
    parser.add_argument("--tier", required=True, choices=("R1", "R2"))
    parser.add_argument("--fingerprint", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--policy-file", required=True)
    parser.add_argument("--token", required=True)
    args = parser.parse_args()
    policy = json.loads(Path(args.policy_file).read_text(encoding="utf-8"))
    if not _v1._core.FULL_SHA.fullmatch(args.base):
        raise SystemExit("base must be a lowercase 40-hex SHA")
    match = verify_live_review_evidence(
        repository=args.repository,
        pr_number=args.pr_number,
        token=args.token,
        policy=policy,
        repo_root=args.repo_root,
        tier=args.tier,
        fingerprint=args.fingerprint,
        head=args.head,
        base=args.base,
    )
    print(json.dumps(match, sort_keys=True))
    return 0


_v1._core.parse_clean_result = _compat_parse_clean_result
_v1._core.verify_records = _compat_verify_records_v3
globals()["_core"] = _v1._core
globals()["_compat_parse_clean_result"] = _compat_parse_clean_result
globals()["_compat_fetch_review_source_v2"] = _compat_fetch_review_source_v2
globals()["_compat_verify_records_v2"] = _compat_verify_records_v2
globals()["_compat_verify_records_v3"] = _compat_verify_records_v3
globals()["fetch_review_source"] = _compat_fetch_review_source_v2
globals()["fetch_pr_reactions"] = fetch_pr_reactions
globals()["verify_records"] = _compat_verify_records_v3


if __name__ == "__main__":
    raise SystemExit(main())
