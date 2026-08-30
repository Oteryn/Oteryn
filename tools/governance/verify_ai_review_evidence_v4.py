#!/usr/bin/env python3
"""Event-safe compatibility layer for authenticated AI review evidence.

The preserved verifier remains fail-closed authority for request anchors,
findings, P2 follow-up, ancestry and fingerprints. This layer adds one narrowly
scoped completion signal: after the trusted Codex summary reaches Completed, a
unique exact-head trusted non-finding review submission may stand in for the
later cosmetic PR thumbs-up reaction. This removes the webhook race without
weakening finding validation.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import verify_ai_review_evidence as legacy


def _event_safe_reactions(comments: list[dict], kwargs: dict) -> list[dict]:
    reactions = kwargs.get("pr_reactions")
    if not isinstance(reactions, list):
        return reactions
    policy = kwargs["policy"]
    repo_root = kwargs["repo_root"]
    tier = kwargs["tier"]
    fingerprint = kwargs["fingerprint"]
    head = kwargs["head"]
    repository = kwargs["repository"]
    pr_number = kwargs["pr_number"]
    reviews = kwargs.get("reviews") or []

    summary_candidates = [
        comment for comment in comments
        if legacy._CODEX_SUMMARY_MARKER in str(comment.get("body") or "")
    ]
    if len(summary_candidates) != 1:
        return reactions

    try:
        _, anchor = legacy._eligible_summary_anchor(
            policy=policy,
            repo_root=repo_root,
            tier=tier,
            fingerprint=fingerprint,
            head=head,
            repository=repository,
            pr_number=pr_number,
            reviews=reviews,
        )
        trusted_logins = legacy._v1._core._trusted_logins(policy, anchor["REVIEWER_ID"])
        summary = summary_candidates[0]
        summary_login = str((summary.get("user") or {}).get("login", "")).casefold()
        if (
            not trusted_logins
            or summary_login not in trusted_logins
            or str((summary.get("performed_via_github_app") or {}).get("slug", ""))
            != legacy._CODEX_SUMMARY_APP
            or not legacy._v1._core._issue_comment_identity(summary, repository, pr_number)
        ):
            return reactions
        body = str(summary.get("body") or "")
        if legacy._FINDING_LIKE_RE.search(body):
            return reactions
        parsed = legacy._parse_completed_summary(body)
        if parsed is None:
            return reactions
        completed_at, prefix = parsed
        reviewed_head = anchor["REVIEWED_HEAD"]
        if legacy._v1._core.resolve_reviewed_prefix(repo_root, prefix) != reviewed_head:
            return reactions
        request_at = legacy._request_anchor_order(anchor)[0]
        summary_updated_at = legacy._utc_timestamp(summary.get("updated_at"))
        if (
            completed_at <= request_at
            or summary_updated_at is None
            or summary_updated_at < completed_at
        ):
            return reactions
    except (KeyError, RuntimeError, TypeError, ValueError):
        return reactions

    matching_actual = []
    for reaction in reactions:
        reaction_at = legacy._utc_timestamp(reaction.get("created_at"))
        reaction_login = str((reaction.get("user") or {}).get("login", "")).casefold()
        if (
            reaction.get("content") == "+1"
            and reaction_login in trusted_logins
            and reaction_at is not None
            and reaction_at >= completed_at
            and reaction_at > request_at
        ):
            matching_actual.append(reaction)
    if matching_actual:
        return reactions

    pull_url = f"https://api.github.com/repos/{repository}/pulls/{pr_number}"
    clean_reviews: list[dict] = []
    for review in reviews:
        login = str((review.get("user") or {}).get("login", "")).casefold()
        if login not in trusted_logins or review.get("pull_request_url") != pull_url:
            continue
        if review.get("commit_id") != reviewed_head or review.get("state") != "COMMENTED":
            continue
        if legacy._strict_positive_int(review.get("id")) is None:
            continue
        submitted_at = legacy._utc_timestamp(review.get("submitted_at"))
        review_body = str(review.get("body") or "")
        if (
            submitted_at is None
            or not (request_at < submitted_at <= completed_at)
            or not review_body
            or not legacy._trusted_review_body_is_nonfinding(review_body, reviewed_head)
        ):
            continue
        clean_reviews.append(review)
    if len(clean_reviews) != 1:
        return reactions

    synthetic = {
        "content": "+1",
        "created_at": summary_updated_at.isoformat().replace("+00:00", "Z"),
        "user": {"login": summary_login},
        "_oteryn_event_safe_completion": True,
    }
    return [*reactions, synthetic]


def verify_records(comments: list[dict], **kwargs) -> dict:
    forwarded = dict(kwargs)
    if "pr_reactions" in forwarded:
        forwarded["pr_reactions"] = _event_safe_reactions(comments, forwarded)
    return legacy.verify_records(comments, **forwarded)


def main() -> int:
    parser = legacy.argparse.ArgumentParser()
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
    if not legacy._v1._core.FULL_SHA.fullmatch(args.base):
        raise SystemExit("base must be a lowercase 40-hex SHA")
    policy["_trusted_integration_base_sha"] = args.base
    match = verify_records(
        legacy._v1._core.fetch_comments(args.repository, args.pr_number, args.token),
        policy=policy,
        repo_root=args.repo_root,
        tier=args.tier,
        fingerprint=args.fingerprint,
        head=args.head,
        repository=args.repository,
        pr_number=args.pr_number,
        token=args.token,
        reviews=legacy._v1._core.fetch_reviews(args.repository, args.pr_number, args.token),
        review_comments=legacy._v1._core.fetch_review_comments(args.repository, args.pr_number, args.token),
        review_threads=lambda: legacy.fetch_review_threads(args.repository, args.pr_number, args.token),
        pr_reactions=legacy.fetch_pr_reactions(args.repository, args.pr_number, args.token),
    )
    print(json.dumps(match, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
