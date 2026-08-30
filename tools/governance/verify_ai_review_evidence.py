#!/usr/bin/env python3
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
import re
import types
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


def _eligible_summary_anchor(
    *, policy: dict, repo_root: str | Path, tier: str, fingerprint: str,
    head: str, repository: str, pr_number: int, reviews: list[dict],
) -> tuple[dict, dict[str, str]]:
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
    if len(matches) != 1:
        raise RuntimeError("current Codex summary requires one eligible immutable request anchor")
    return matches[0]


def _parse_observed_duplicate_clean_echo(body: str) -> str | None:
    """Return the reviewed prefix only for the complete observed Codex echo envelope."""
    lines = [line.strip() for line in (body or "").splitlines() if line.strip()]
    if len(lines) != 11 or lines[0] != f"{_CLEAN_PREFIX} Delightful!":
        return None
    reviewed = _REVIEWED_COMMIT_LINE.fullmatch(lines[1])
    if reviewed is None:
        return None
    prefix = reviewed.group(1)
    expected = [
        f"{_CLEAN_PREFIX} Delightful!",
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
        if _v1._core.BLOCKING_FINDING_RE.search(body):
            raise RuntimeError("P0/P1 Codex finding exists in the same-generation clean echo")
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


def _normalize_current_codex_summary(
    comments: list[dict], *, pr_reactions: list[dict], policy: dict,
    repo_root: str | Path, tier: str, fingerprint: str, head: str,
    repository: str, pr_number: int, reviews: list[dict],
) -> list[dict]:
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
        return comments
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
    if _v1._core.BLOCKING_FINDING_RE.search(summary_body):
        raise RuntimeError("P0/P1 Codex finding exists in the review summary")
    parsed_summary = _parse_completed_summary(summary_body)
    if parsed_summary is None:
        raise RuntimeError("trusted Codex review summary is not the accepted completed shape")
    completed_at, prefix = parsed_summary
    reviewed_head = anchor["REVIEWED_HEAD"]
    resolved = _v1._core.resolve_reviewed_prefix(repo_root, prefix)
    if resolved is None or resolved != reviewed_head:
        raise RuntimeError("Codex summary reviewed-commit prefix does not match the request anchor")

    request_at = _utc_timestamp(anchor.get("REQUEST_CREATED_AT"))
    summary_updated_at = _utc_timestamp(summary.get("updated_at"))
    if request_at is None or completed_at <= request_at:
        raise RuntimeError("Codex summary completion does not follow the current request")
    if summary_updated_at is None or summary_updated_at < completed_at:
        raise RuntimeError("Codex summary update timestamp precedes completion")

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
    if len(matching_reactions) != 1:
        raise RuntimeError("current Codex summary requires exactly one trusted post-completion PR reaction")
    reaction_at_raw = str(matching_reactions[0].get("created_at") or "")
    reaction_at = _utc_timestamp(reaction_at_raw)
    if reaction_at is None:
        raise RuntimeError("trusted Codex reaction timestamp is malformed")

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
    ]


def _compat_verify_records_v3(comments: list[dict], **kwargs) -> dict:
    """Adapt the current Codex summary/reaction envelope into the preserved verifier."""
    pr_reactions = kwargs.pop("pr_reactions", None)
    if pr_reactions is not None:
        if not isinstance(pr_reactions, list) or any(not isinstance(item, dict) for item in pr_reactions):
            raise RuntimeError("pull request reactions response is malformed")
        comments = _normalize_current_codex_summary(
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
        )
    return _compat_verify_records_v2(comments, **kwargs)


def fetch_pr_reactions(repository: str, pr_number: int, token: str) -> list[dict]:
    return _v1._core._fetch_paginated(
        f"https://api.github.com/repos/{repository}/issues/{pr_number}/reactions", token
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
    policy["_trusted_integration_base_sha"] = args.base
    match = verify_records(
        _v1._core.fetch_comments(args.repository, args.pr_number, args.token),
        policy=policy,
        repo_root=args.repo_root,
        tier=args.tier,
        fingerprint=args.fingerprint,
        head=args.head,
        repository=args.repository,
        pr_number=args.pr_number,
        token=args.token,
        reviews=_v1._core.fetch_reviews(args.repository, args.pr_number, args.token),
        review_comments=_v1._core.fetch_review_comments(args.repository, args.pr_number, args.token),
        pr_reactions=fetch_pr_reactions(args.repository, args.pr_number, args.token),
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