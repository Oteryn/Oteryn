#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import ai_review_policy as risk_policy

MARKER = "<!-- OTERYN_AI_REVIEW_V1 -->"
REQUEST_MARKER = "<!-- OTERYN_AI_REVIEW_REQUEST_V1 -->"
REQUEST_ANCHOR_MARKER = "<!-- OTERYN_AI_REVIEW_REQUEST_ANCHOR_V1 -->"
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
SHORT_SHA = re.compile(r"^[0-9a-f]{7,40}$")
FIELD_RE = re.compile(r"^([A-Z0-9_]+):\s*(.+?)\s*$")
TRUSTED_ASSOCIATIONS = {"OWNER", "MEMBER", "COLLABORATOR"}
SOURCE_URL_RE = re.compile(
    r"^https://github\.com/([^/]+/[^/]+)/pull/([1-9][0-9]*)#pullrequestreview-([1-9][0-9]*)$"
)
REQUEST_FIELDS = {
    "REVIEW_TIER",
    "REVIEW_FINGERPRINT",
    "REVIEWED_HEAD",
    "REVIEWER_CLASS",
    "REVIEWER_ID",
}
REQUEST_ANCHOR_FIELDS = {
    "REQUEST_COMMENT_ID",
    "REQUEST_AUTHOR",
    "REQUEST_AUTHOR_ASSOCIATION",
    "REQUEST_CREATED_AT",
    "REQUEST_BODY_SHA256",
    "REQUEST_VALID",
    "DISPATCH_HEAD",
    "GENERATION_RUN_ID",
}
CLEAN_RESULT_RE = re.compile(
    r"^Codex Review: Didn't find any major issues\."
    r"(?: What shall we delve into next\?)?\s*\n+"
    r"\*\*Reviewed commit:\*\* `([0-9a-f]{7,40})`"
    r"(?:\s*\n+<details>[\s\S]*</details>)?\s*$"
)
BLOCKING_FINDING_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?"
    r"(?:\[(?:P0|P1)\]|(?:P0|P1)\b|(?:<sub>){1,2}!\[(?:P0|P1) Badge\])"
)


def parse_record(body: str) -> dict[str, str] | None:
    if body.count(MARKER) != 1:
        return None
    fields: dict[str, str] = {}
    for line in body.splitlines():
        match = FIELD_RE.match(line.strip())
        if not match:
            continue
        key = match.group(1)
        if key in fields:
            return None
        fields[key] = match.group(2)
    return fields


def parse_request(body: str) -> dict[str, str] | None:
    if body.count(REQUEST_MARKER) != 1:
        return None
    if sum(1 for line in body.splitlines() if line.strip().casefold() == "@codex review") != 1:
        return None
    fields: dict[str, str] = {}
    for line in body.splitlines():
        match = FIELD_RE.match(line.strip())
        if not match:
            continue
        key = match.group(1)
        if key in fields:
            return None
        fields[key] = match.group(2)
    if set(fields) != REQUEST_FIELDS:
        return None
    if fields["REVIEW_TIER"] not in {"R1", "R2"}:
        return None
    if not SHA256.fullmatch(fields["REVIEW_FINGERPRINT"]):
        return None
    if not FULL_SHA.fullmatch(fields["REVIEWED_HEAD"]):
        return None
    if fields["REVIEWER_CLASS"] not in {"fast", "deep"}:
        return None
    if not re.fullmatch(r"[a-z0-9_]+", fields["REVIEWER_ID"]):
        return None
    return fields


def parse_request_anchor(body: str) -> dict[str, str] | None:
    if body.count(REQUEST_ANCHOR_MARKER) != 1:
        return None
    fields: dict[str, str] = {}
    for line in body.splitlines():
        match = FIELD_RE.match(line.strip())
        if not match:
            continue
        key = match.group(1)
        if key in fields:
            return None
        fields[key] = match.group(2)
    valid = fields.get("REQUEST_VALID")
    expected = REQUEST_ANCHOR_FIELDS | (REQUEST_FIELDS if valid == "true" else set())
    if set(fields) != expected or valid not in {"true", "false"}:
        return None
    if not fields["REQUEST_COMMENT_ID"].isdigit():
        return None
    if not re.fullmatch(r"[A-Z_]+", fields["REQUEST_AUTHOR_ASSOCIATION"]):
        return None
    if valid == "true" and fields["REQUEST_AUTHOR_ASSOCIATION"] not in TRUSTED_ASSOCIATIONS:
        return None
    if not SHA256.fullmatch(fields["REQUEST_BODY_SHA256"]):
        return None
    if not FULL_SHA.fullmatch(fields["DISPATCH_HEAD"]):
        return None
    if not fields["GENERATION_RUN_ID"].isdigit():
        return None
    if valid == "true" and parse_request("\n".join([
        "@codex review", REQUEST_MARKER,
        *(f"{key}: {fields[key]}" for key in sorted(REQUEST_FIELDS)),
    ])) is None:
        return None
    return fields


def parse_clean_result(body: str) -> str | None:
    match = CLEAN_RESULT_RE.fullmatch((body or "").strip())
    return match.group(1) if match else None


def _created_at(value: dict) -> tuple[datetime, int]:
    raw = str(value.get("created_at") or "")
    try:
        stamp = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        stamp = datetime.min.replace(tzinfo=timezone.utc)
    try:
        object_id = int(value.get("id") or 0)
    except (TypeError, ValueError):
        object_id = 0
    return stamp, object_id


def _is_request_like(comment: dict) -> bool:
    if comment.get("author_association") not in TRUSTED_ASSOCIATIONS:
        return False
    return any(
        line.strip().casefold() == "@codex review"
        for line in str(comment.get("body") or "").splitlines()
    )


def _is_result_like(comment: dict) -> bool:
    body = str(comment.get("body") or "")
    return body.lstrip().startswith("Codex Review:") or "**Reviewed commit:**" in body


def _issue_comment_identity(comment: dict, repository: str, pr_number: int) -> bool:
    expected_issue = f"https://api.github.com/repos/{repository}/issues/{pr_number}"
    expected_html = f"https://github.com/{repository}/pull/{pr_number}#issuecomment-"
    return (
        comment.get("issue_url") == expected_issue
        and str(comment.get("html_url") or "").startswith(expected_html)
        and str(comment.get("html_url") or "")[len(expected_html):].isdigit()
    )


def is_ancestor(repo_root: str | Path, older: str, newer: str) -> bool:
    if not FULL_SHA.fullmatch(older) or not FULL_SHA.fullmatch(newer):
        return False
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", older, newer],
        cwd=Path(repo_root),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def resolve_reviewed_prefix(repo_root: str | Path, prefix: str) -> str | None:
    if not SHORT_SHA.fullmatch(prefix):
        return None
    result = subprocess.run(
        ["git", "rev-parse", "--verify", f"{prefix}^{{commit}}"],
        cwd=Path(repo_root),
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        return None
    resolved = result.stdout.strip()
    if not FULL_SHA.fullmatch(resolved) or not resolved.startswith(prefix):
        return None
    return resolved


def reviewer_allowed(policy: dict, reviewer_class: str, reviewer_id: str) -> bool:
    allowed = set(policy["reviewer_preferences"][reviewer_class])
    if reviewer_class == "fast":
        allowed.update(policy["reviewer_preferences"].get("deep", []))
    return reviewer_id in allowed


def _git_lines(repo_root: str | Path, *args: str) -> list[str]:
    result = subprocess.run(
        ["git", *args], cwd=Path(repo_root), text=True, encoding="utf-8",
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git command failed: {' '.join(args)}")
    return [line for line in result.stdout.splitlines() if line]


def post_review_commits_are_neutral(
    repo_root: str | Path, reviewed_head: str, head: str, policy: dict,
    *, _merge_reuse_consumed: bool = False,
) -> bool:
    try:
        if reviewed_head == head:
            return True
        head_parents = _git_lines(repo_root, "show", "-s", "--format=%P", head)
        parents = head_parents[0].split() if len(head_parents) == 1 else []
        trusted_base = str(policy.get("_trusted_integration_base_sha") or "")
        merge_reuse_enabled = bool(policy.get("activation", {}).get("allow_clean_trusted_base_merge_reuse"))
        if (
            merge_reuse_enabled and not _merge_reuse_consumed
            and len(parents) == 2 and trusted_base and parents[1] == trusted_base
        ):
            if not is_ancestor(repo_root, reviewed_head, parents[0]):
                return False
            merged_tree = _git_lines(repo_root, "show", "-s", "--format=%T", head)
            merge_tree = subprocess.run(
                ["git", "merge-tree", "--write-tree", parents[0], parents[1]],
                cwd=Path(repo_root), text=True, encoding="utf-8",
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
            )
            expected_tree = merge_tree.stdout.splitlines()[0].strip() if merge_tree.stdout else ""
            if merge_tree.returncode != 0 or merged_tree != [expected_tree]:
                return False
            return post_review_commits_are_neutral(
                repo_root, reviewed_head, parents[0], policy, _merge_reuse_consumed=True
            )
        commits = _git_lines(repo_root, "rev-list", "--reverse", f"{reviewed_head}..{head}")
        for commit in commits:
            parents = _git_lines(repo_root, "show", "-s", "--format=%P", commit)
            parent_shas = parents[0].split() if len(parents) == 1 else []
            if len(parent_shas) != 1:
                return False
            parent = parent_shas[0]
            paths = risk_policy.changed_paths(repo_root, parent, commit)
            patch = risk_policy.patch_for(repo_root, parent, commit)
            commit_tier, _ = risk_policy.classify(paths, patch, policy)
            if commit_tier != "R0":
                return False
            if any(
                not risk_policy.safe_r0_path(path, policy["review_neutral_globs"], policy)
                for path in paths
            ):
                return False
    except (RuntimeError, subprocess.SubprocessError):
        return False
    return True


def fetch_json(url: str, token: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "oteryn-ai-review-gate",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        value = json.load(response)
    if not isinstance(value, dict):
        raise RuntimeError("review source response is not an object")
    return value


def _fetch_paginated(url: str, token: str) -> list[dict]:
    values: list[dict] = []
    page = 1
    while True:
        separator = "&" if "?" in url else "?"
        request = urllib.request.Request(
            f"{url}{separator}per_page=100&page={page}",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "oteryn-ai-review-gate",
            },
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            batch = json.load(response)
        if not isinstance(batch, list) or any(not isinstance(item, dict) for item in batch):
            raise RuntimeError("GitHub list response is malformed")
        values.extend(batch)
        if len(batch) < 100:
            return values
        page += 1


def fetch_review_source(
    repository: str, pr_number: int, source_url: str, token: str
) -> tuple[str, dict]:
    match = SOURCE_URL_RE.fullmatch(source_url)
    if not match or match.group(1) != repository or int(match.group(2)) != pr_number:
        raise RuntimeError("review source URL is not an exact PR review on this pull request")
    review_id = int(match.group(3))
    obj = fetch_json(
        f"https://api.github.com/repos/{repository}/pulls/{pr_number}/reviews/{review_id}", token
    )
    if obj.get("html_url") != source_url:
        raise RuntimeError("pull-request-review source identity mismatch")
    expected_pr = f"https://api.github.com/repos/{repository}/pulls/{pr_number}"
    if obj.get("pull_request_url") != expected_pr:
        raise RuntimeError("pull-request-review PR identity mismatch")
    return "pull_request_review", obj


def source_attests(
    source: dict, *, reviewed_head: str, tier: str, fingerprint: str,
    reviewer_class: str, reviewer_id: str
) -> bool:
    record = parse_record(source.get("body") or "")
    if not record:
        return False
    return (
        record.get("RESULT") == "PASS"
        and record.get("FINDINGS") == "0"
        and record.get("REVIEWED_HEAD") == reviewed_head
        and record.get("REVIEW_TIER") == tier
        and record.get("REVIEW_FINGERPRINT") == fingerprint
        and record.get("REVIEWER_CLASS") == reviewer_class
        and record.get("REVIEWER_ID") == reviewer_id
    )


def _trusted_logins(policy: dict, reviewer_id: str) -> set[str]:
    return {
        value.casefold()
        for value in policy.get("reviewer_source_logins", {}).get(reviewer_id, [])
    }


def _anchor_logins(policy: dict) -> set[str]:
    return {
        str(value).casefold()
        for value in policy.get("review_request_anchor_logins", [])
    }


def _eligible_request_anchors(
    *, reviews: list[dict], policy: dict, repo_root: str | Path,
    head: str, repository: str, pr_number: int
) -> list[tuple[dict, dict[str, str]]]:
    anchor_logins = _anchor_logins(policy)
    pull_url = f"https://api.github.com/repos/{repository}/pulls/{pr_number}"
    anchors: list[tuple[dict, dict[str, str]]] = []
    for review in reviews:
        body = str(review.get("body") or "")
        login = str((review.get("user") or {}).get("login", "")).casefold()
        if REQUEST_ANCHOR_MARKER not in body or login not in anchor_logins:
            continue
        anchor = parse_request_anchor(body)
        if anchor is None:
            raise RuntimeError("trusted review-request anchor is malformed")
        dispatch_head = anchor["DISPATCH_HEAD"]
        if (
            review.get("pull_request_url") != pull_url
            or review.get("commit_id") != dispatch_head
            or str(review.get("state") or "").upper() != "COMMENTED"
        ):
            raise RuntimeError("trusted review-request anchor identity is malformed")
        if not is_ancestor(repo_root, dispatch_head, head):
            continue
        if not post_review_commits_are_neutral(repo_root, dispatch_head, head, policy):
            continue
        anchors.append((review, anchor))
    return anchors


def _validate_anchor_generation(
    *, reviews: list[dict], policy: dict, repo_root: str | Path,
    head: str, repository: str, pr_number: int
) -> list[tuple[dict, dict[str, str]]]:
    anchors = _eligible_request_anchors(
        reviews=reviews,
        policy=policy,
        repo_root=repo_root,
        head=head,
        repository=repository,
        pr_number=pr_number,
    )
    by_head: dict[str, list[tuple[dict, dict[str, str]]]] = {}
    for item in anchors:
        by_head.setdefault(item[1]["DISPATCH_HEAD"], []).append(item)
    for items in by_head.values():
        if len(items) != 1 or items[0][1]["REQUEST_VALID"] != "true":
            raise RuntimeError("immutable Codex request-anchor generation is missing, invalid, or ambiguous")
    return anchors


def _blocking_findings_exist(
    *, reviews: list[dict], review_comments: list[dict], repository: str,
    pr_number: int, reviewed_head: str, trusted_logins: set[str]
) -> bool:
    pull_url = f"https://api.github.com/repos/{repository}/pulls/{pr_number}"
    matching_reviews: set[int] = set()
    for review in reviews:
        login = str((review.get("user") or {}).get("login", "")).casefold()
        if (
            login in trusted_logins
            and review.get("commit_id") == reviewed_head
            and review.get("pull_request_url") == pull_url
        ):
            try:
                matching_reviews.add(int(review.get("id")))
            except (TypeError, ValueError):
                return True
            if BLOCKING_FINDING_RE.search(str(review.get("body") or "")):
                return True
    for comment in review_comments:
        login = str((comment.get("user") or {}).get("login", "")).casefold()
        if login not in trusted_logins or comment.get("pull_request_url") != pull_url:
            continue
        try:
            review_id = int(comment.get("pull_request_review_id"))
        except (TypeError, ValueError):
            continue
        if review_id in matching_reviews and BLOCKING_FINDING_RE.search(str(comment.get("body") or "")):
            return True
    return False


def _blocking_findings_for_current_generation(
    *, comments: list[dict], reviews: list[dict], review_comments: list[dict], policy: dict,
    repo_root: str | Path, tier: str, head: str, repository: str, pr_number: int
) -> bool:
    reviewer_ids: set[str] = set()
    for reviewer_class in ("fast", "deep"):
        reviewer_ids.update(policy.get("reviewer_preferences", {}).get(reviewer_class, []))
    trusted_logins: set[str] = set()
    for reviewer_id in reviewer_ids:
        trusted_logins.update(_trusted_logins(policy, reviewer_id))
    if not trusted_logins:
        return True

    eligible_requests: list[tuple[dict, set[str]]] = []
    for request_comment in comments:
        if not _is_request_like(request_comment):
            continue
        if not _issue_comment_identity(request_comment, repository, pr_number):
            continue
        if not request_comment.get("created_at"):
            continue
        if request_comment.get("updated_at") != request_comment.get("created_at"):
            eligible_requests.append((request_comment, trusted_logins))
            continue
        parsed = parse_request(str(request_comment.get("body") or ""))
        if parsed is None or not reviewer_allowed(
            policy, parsed["REVIEWER_CLASS"], parsed["REVIEWER_ID"]
        ):
            eligible_requests.append((request_comment, trusted_logins))
            continue
        reviewed_head = parsed["REVIEWED_HEAD"]
        if not is_ancestor(repo_root, reviewed_head, head):
            continue
        if not post_review_commits_are_neutral(repo_root, reviewed_head, head, policy):
            continue
        request_logins = _trusted_logins(policy, parsed["REVIEWER_ID"])
        if request_logins:
            eligible_requests.append((request_comment, request_logins))

    for _, anchor in _eligible_request_anchors(
        reviews=reviews,
        policy=policy,
        repo_root=repo_root,
        head=head,
        repository=repository,
        pr_number=pr_number,
    ):
        if anchor["REQUEST_VALID"] != "true":
            continue
        request_logins = _trusted_logins(policy, anchor["REVIEWER_ID"])
        if request_logins:
            eligible_requests.append(({
                "created_at": anchor["REQUEST_CREATED_AT"],
                "id": anchor["REQUEST_COMMENT_ID"],
            }, request_logins))

    latest_request = max(eligible_requests, key=lambda item: _created_at(item[0]), default=None)
    for comment in comments:
        if not _issue_comment_identity(comment, repository, pr_number):
            continue
        if not BLOCKING_FINDING_RE.search(str(comment.get("body") or "")):
            continue
        login = str((comment.get("user") or {}).get("login", "")).casefold()
        if (
            latest_request is not None
            and login in latest_request[1]
            and _created_at(comment) > _created_at(latest_request[0])
        ):
            return True

    pull_url = f"https://api.github.com/repos/{repository}/pulls/{pr_number}"
    has_valid_exact_head_generation = any(
        anchor["REQUEST_VALID"] == "true"
        and anchor["DISPATCH_HEAD"] == head
        and anchor["REVIEWED_HEAD"] == head
        and anchor["REVIEW_TIER"] == tier
        and reviewer_allowed(policy, anchor["REVIEWER_CLASS"], anchor["REVIEWER_ID"])
        for _, anchor in _eligible_request_anchors(
            reviews=reviews,
            policy=policy,
            repo_root=repo_root,
            head=head,
            repository=repository,
            pr_number=pr_number,
        )
    )
    has_exact_head_review = has_valid_exact_head_generation and any(
        str((review.get("user") or {}).get("login", "")).casefold() in trusted_logins
        and review.get("pull_request_url") == pull_url
        and review.get("commit_id") == head
        for review in reviews
    )
    eligible_review_ids: set[int] = set()
    for review in reviews:
        login = str((review.get("user") or {}).get("login", "")).casefold()
        reviewed_head = str(review.get("commit_id") or "")
        if login not in trusted_logins or review.get("pull_request_url") != pull_url:
            continue
        if not FULL_SHA.fullmatch(reviewed_head):
            continue
        if has_exact_head_review and reviewed_head != head:
            continue
        if not is_ancestor(repo_root, reviewed_head, head):
            continue
        if not post_review_commits_are_neutral(repo_root, reviewed_head, head, policy):
            continue
        try:
            review_id = int(review.get("id"))
        except (TypeError, ValueError):
            return True
        eligible_review_ids.add(review_id)
        if BLOCKING_FINDING_RE.search(str(review.get("body") or "")):
            return True

    for comment in review_comments:
        login = str((comment.get("user") or {}).get("login", "")).casefold()
        if login not in trusted_logins or comment.get("pull_request_url") != pull_url:
            continue
        try:
            review_id = int(comment.get("pull_request_review_id"))
        except (TypeError, ValueError):
            continue
        if review_id in eligible_review_ids and BLOCKING_FINDING_RE.search(str(comment.get("body") or "")):
            return True
    return False


def _verify_issue_comment_result(
    comments: list[dict], *, reviews: list[dict], review_comments: list[dict],
    policy: dict, repo_root: str | Path, tier: str, fingerprint: str, head: str,
    repository: str, pr_number: int
) -> dict:
    required_class = policy["review_tiers"][tier]["reviewer_class"]
    request_like = sorted((c for c in comments if _is_request_like(c)), key=_created_at)
    if not request_like:
        raise RuntimeError("no Codex review request is present")

    latest_request_comment = request_like[-1]
    if not _issue_comment_identity(latest_request_comment, repository, pr_number):
        raise RuntimeError("latest Codex request does not belong to this repository and PR")
    request = parse_request(str(latest_request_comment.get("body") or ""))
    if request is None:
        raise RuntimeError("latest Codex request is not one exact structured request")
    if (
        not latest_request_comment.get("created_at")
        or latest_request_comment.get("updated_at") != latest_request_comment.get("created_at")
    ):
        raise RuntimeError("latest Codex request was edited after creation")

    matching_requests: list[tuple[dict, dict[str, str]]] = []
    for comment in request_like:
        if not _issue_comment_identity(comment, repository, pr_number):
            continue
        parsed = parse_request(str(comment.get("body") or ""))
        if parsed is None:
            continue
        if not comment.get("created_at") or comment.get("updated_at") != comment.get("created_at"):
            continue
        request_class = parsed["REVIEWER_CLASS"]
        allowed_classes = {required_class} if required_class == "deep" else {"fast", "deep"}
        if (
            parsed["REVIEW_TIER"] == tier
            and parsed["REVIEW_FINGERPRINT"] == fingerprint
            and request_class in allowed_classes
            and reviewer_allowed(policy, request_class, parsed["REVIEWER_ID"])
            and is_ancestor(repo_root, parsed["REVIEWED_HEAD"], head)
            and post_review_commits_are_neutral(repo_root, parsed["REVIEWED_HEAD"], head, policy)
        ):
            matching_requests.append((comment, parsed))
    if len(matching_requests) != 1:
        raise RuntimeError("Codex request/result generation is missing or ambiguous")
    request_comment, request = matching_requests[0]
    if request_comment.get("id") != latest_request_comment.get("id"):
        raise RuntimeError("a newer Codex request supersedes the matching generation")

    reviewer_id = request["REVIEWER_ID"]
    request_class = request["REVIEWER_CLASS"]
    reviewed_head = request["REVIEWED_HEAD"]
    trusted_logins = _trusted_logins(policy, reviewer_id)
    if not trusted_logins:
        raise RuntimeError("reviewer has no configured trusted source login")
    if "issue_comment_result" not in policy.get("reviewer_source_kinds", {}).get(reviewer_id, []):
        raise RuntimeError("issue-comment result source is not enabled for reviewer")
    anchors = [
        item for item in _eligible_request_anchors(
            reviews=reviews,
            policy=policy,
            repo_root=repo_root,
            head=head,
            repository=repository,
            pr_number=pr_number,
        )
        if item[1]["DISPATCH_HEAD"] == reviewed_head
    ]
    if len(anchors) != 1:
        raise RuntimeError("one immutable trusted request anchor is required")
    anchor_review, anchor = anchors[0]
    request_login = str((request_comment.get("user") or {}).get("login", ""))
    request_body = str(request_comment.get("body") or "")
    if (
        anchor["REQUEST_VALID"] != "true"
        or anchor["REQUEST_COMMENT_ID"] != str(request_comment.get("id"))
        or anchor["REQUEST_AUTHOR"] != request_login
        or anchor["REQUEST_AUTHOR_ASSOCIATION"] != request_comment.get("author_association")
        or anchor["REQUEST_CREATED_AT"] != request_comment.get("created_at")
        or anchor["REQUEST_BODY_SHA256"] != hashlib.sha256(request_body.encode("utf-8")).hexdigest()
        or any(anchor[key] != request[key] for key in REQUEST_FIELDS)
    ):
        raise RuntimeError("trusted request anchor does not match the exact request comment")
    for other_comment in request_like:
        if other_comment.get("id") == request_comment.get("id"):
            continue
        if not _issue_comment_identity(other_comment, repository, pr_number):
            continue
        if (
            not other_comment.get("created_at")
            or other_comment.get("updated_at") != other_comment.get("created_at")
        ):
            raise RuntimeError("another Codex request has ambiguous immutable metadata")
        other = parse_request(str(other_comment.get("body") or ""))
        if other is None:
            raise RuntimeError("another Codex request is malformed and makes the generation ambiguous")
        if other["REVIEWED_HEAD"] != reviewed_head:
            continue
        if not reviewer_allowed(policy, other["REVIEWER_CLASS"], other["REVIEWER_ID"]):
            continue
        if trusted_logins & _trusted_logins(policy, other["REVIEWER_ID"]):
            raise RuntimeError("same-head Codex requests share an ambiguous trusted source identity")
    if any(
        _created_at(comment) > _created_at(request_comment)
        and str((comment.get("user") or {}).get("login", "")).casefold() in trusted_logins
        and BLOCKING_FINDING_RE.search(str(comment.get("body") or ""))
        for comment in comments
    ):
        raise RuntimeError("P0/P1 Codex finding exists in the issue-comment generation")

    result_like = [
        comment for comment in comments
        if _created_at(comment) > _created_at(request_comment) and _is_result_like(comment)
    ]
    trusted_results = [
        comment for comment in result_like
        if str((comment.get("user") or {}).get("login", "")).casefold() in trusted_logins
    ]
    if len(trusted_results) != 1:
        raise RuntimeError("trusted Codex result is missing or ambiguous")
    result = trusted_results[0]
    if not _issue_comment_identity(result, repository, pr_number):
        raise RuntimeError("Codex result does not belong to this repository and PR")
    if _created_at(result) <= _created_at(request_comment):
        raise RuntimeError("Codex result does not follow its request")
    prefix = parse_clean_result(str(result.get("body") or ""))
    if prefix is None:
        raise RuntimeError("Codex result is not the accepted clean-result shape")
    resolved = resolve_reviewed_prefix(repo_root, prefix)
    if resolved is None or resolved != reviewed_head:
        raise RuntimeError("Codex reviewed-commit prefix does not uniquely match the requested head")
    if _blocking_findings_exist(
        reviews=reviews,
        review_comments=review_comments,
        repository=repository,
        pr_number=pr_number,
        reviewed_head=reviewed_head,
        trusted_logins=trusted_logins,
    ):
        raise RuntimeError("P0/P1 Codex finding exists for the reviewed generation")

    return {
        "review_request_id": request_comment.get("id"),
        "review_request_url": request_comment.get("html_url"),
        "review_request_anchor_id": anchor_review.get("id"),
        "review_request_anchor_url": anchor_review.get("html_url"),
        "reviewed_head": reviewed_head,
        "reviewer_id": reviewer_id,
        "review_source_url": result.get("html_url"),
        "review_source_author": str((result.get("user") or {}).get("login", "")).casefold(),
        "review_source_kind": "issue_comment_result",
        "review_source_commit_id": resolved,
    }


def _verify_legacy_records(
    comments: list[dict], *, policy: dict, repo_root: str | Path, tier: str,
    fingerprint: str, head: str, repository: str, pr_number: int, token: str
) -> dict:
    required_class = policy["review_tiers"][tier]["reviewer_class"]
    for comment in reversed(comments):
        if comment.get("author_association") not in TRUSTED_ASSOCIATIONS:
            continue
        record = parse_record(comment.get("body") or "")
        if not record or record.get("RESULT") != "PASS":
            continue
        reviewed_head = record.get("REVIEWED_HEAD", "")
        if record.get("REVIEW_TIER") != tier or record.get("REVIEW_FINGERPRINT") != fingerprint:
            continue
        record_class = record.get("REVIEWER_CLASS", "")
        allowed_classes = {required_class} if required_class == "deep" else {"fast", "deep"}
        if record_class not in allowed_classes:
            continue
        reviewer_id = record.get("REVIEWER_ID", "")
        if not reviewer_allowed(policy, record_class, reviewer_id):
            continue
        if not is_ancestor(repo_root, reviewed_head, head):
            continue
        if not post_review_commits_are_neutral(repo_root, reviewed_head, head, policy):
            continue
        source_url = record.get("REVIEW_SOURCE_URL", "")
        try:
            source_kind, source = fetch_review_source(repository, pr_number, source_url, token)
        except Exception:
            continue
        source_login = str((source.get("user") or {}).get("login", "")).casefold()
        attestor_login = str((comment.get("user") or {}).get("login", "")).casefold()
        trusted = _trusted_logins(policy, reviewer_id)
        if not source_login or source_login == attestor_login or source_login not in trusted:
            continue
        if source_kind not in policy.get("reviewer_source_kinds", {}).get(reviewer_id, []):
            continue
        if source.get("commit_id") != reviewed_head:
            continue
        if str(source.get("state", "")).upper() not in {"APPROVED", "COMMENTED"}:
            continue
        if not source_attests(
            source,
            reviewed_head=reviewed_head,
            tier=tier,
            fingerprint=fingerprint,
            reviewer_class=record_class,
            reviewer_id=reviewer_id,
        ):
            continue
        return {
            "comment_id": comment.get("id"),
            "reviewed_head": reviewed_head,
            "reviewer_id": reviewer_id,
            "review_source_url": source_url,
            "review_source_author": source_login,
            "review_source_kind": source_kind,
            "review_source_commit_id": source.get("commit_id"),
        }
    raise RuntimeError("no authenticated legacy external PASS review matches")


def verify_records(
    comments: list[dict], *, policy: dict, repo_root: str | Path, tier: str,
    fingerprint: str, head: str, repository: str, pr_number: int, token: str,
    reviews: list[dict] | None = None, review_comments: list[dict] | None = None
) -> dict:
    if tier not in {"R1", "R2"} or not FULL_SHA.fullmatch(head):
        raise RuntimeError("invalid gate identity")
    trusted_reviewer_logins: set[str] = set()
    for reviewer_logins in policy.get("reviewer_source_logins", {}).values():
        trusted_reviewer_logins.update(str(login).casefold() for login in reviewer_logins)
    for comment in comments:
        login = str((comment.get("user") or {}).get("login", "")).casefold()
        if (
            comment.get("author_association") not in TRUSTED_ASSOCIATIONS
            and login not in trusted_reviewer_logins
        ):
            continue
        created_at = str(comment.get("created_at") or "")
        updated_at = str(comment.get("updated_at") or "")
        if not created_at or not updated_at:
            raise RuntimeError("trusted PR comment edit metadata is missing")
        if updated_at != created_at:
            raise RuntimeError("edited trusted PR comments invalidate external review evidence")
    for comment in review_comments or []:
        login = str((comment.get("user") or {}).get("login", "")).casefold()
        if login not in trusted_reviewer_logins:
            continue
        created_at = str(comment.get("created_at") or "")
        updated_at = str(comment.get("updated_at") or "")
        if not created_at or not updated_at:
            raise RuntimeError("trusted inline review comment edit metadata is missing")
        if updated_at != created_at:
            raise RuntimeError("edited trusted inline review comments invalidate external review evidence")
    request_anchors = _validate_anchor_generation(
        reviews=reviews or [],
        policy=policy,
        repo_root=repo_root,
        head=head,
        repository=repository,
        pr_number=pr_number,
    )
    if _blocking_findings_for_current_generation(
        comments=comments,
        reviews=reviews or [],
        review_comments=review_comments or [],
        policy=policy,
        repo_root=repo_root,
        tier=tier,
        head=head,
        repository=repository,
        pr_number=pr_number,
    ):
        raise RuntimeError("P0/P1 Codex finding blocks every review-evidence envelope")
    errors: list[str] = []
    try:
        return _verify_issue_comment_result(
            comments,
            reviews=reviews or [],
            review_comments=review_comments or [],
            policy=policy,
            repo_root=repo_root,
            tier=tier,
            fingerprint=fingerprint,
            head=head,
            repository=repository,
            pr_number=pr_number,
        )
    except RuntimeError as exc:
        errors.append(str(exc))
    if request_anchors:
        raise RuntimeError(
            "an immutable issue-comment review generation exists and cannot fall back to legacy evidence: "
            + "; ".join(errors)
        )
    try:
        return _verify_legacy_records(
            comments,
            policy=policy,
            repo_root=repo_root,
            tier=tier,
            fingerprint=fingerprint,
            head=head,
            repository=repository,
            pr_number=pr_number,
            token=token,
        )
    except RuntimeError as exc:
        errors.append(str(exc))
    raise RuntimeError(
        "no authenticated external PASS review matches tier/fingerprint/head and neutral post-review history: "
        + "; ".join(errors)
    )


def fetch_comments(repository: str, pr_number: int, token: str) -> list[dict]:
    return _fetch_paginated(
        f"https://api.github.com/repos/{repository}/issues/{pr_number}/comments", token
    )


def fetch_reviews(repository: str, pr_number: int, token: str) -> list[dict]:
    return _fetch_paginated(
        f"https://api.github.com/repos/{repository}/pulls/{pr_number}/reviews", token
    )


def fetch_review_comments(repository: str, pr_number: int, token: str) -> list[dict]:
    return _fetch_paginated(
        f"https://api.github.com/repos/{repository}/pulls/{pr_number}/comments", token
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
    if not FULL_SHA.fullmatch(args.base):
        raise SystemExit("base must be a lowercase 40-hex SHA")
    policy["_trusted_integration_base_sha"] = args.base
    match = verify_records(
        fetch_comments(args.repository, args.pr_number, args.token),
        policy=policy,
        repo_root=args.repo_root,
        tier=args.tier,
        fingerprint=args.fingerprint,
        head=args.head,
        repository=args.repository,
        pr_number=args.pr_number,
        token=args.token,
        reviews=fetch_reviews(args.repository, args.pr_number, args.token),
        review_comments=fetch_review_comments(args.repository, args.pr_number, args.token),
    )
    print(json.dumps(match, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
