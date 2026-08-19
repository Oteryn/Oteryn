#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import urllib.request
from pathlib import Path

MARKER = "<!-- OTERYN_AI_REVIEW_V1 -->"
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
FIELD_RE = re.compile(r"^([A-Z0-9_]+):\s*(.+?)\s*$")
TRUSTED_ASSOCIATIONS = {"OWNER", "MEMBER", "COLLABORATOR"}


def parse_record(body: str) -> dict[str, str] | None:
    if MARKER not in body:
        return None
    fields: dict[str, str] = {}
    for line in body.splitlines():
        match = FIELD_RE.match(line.strip())
        if match:
            fields[match.group(1)] = match.group(2)
    return fields


def is_ancestor(repo_root: str | Path, older: str, newer: str) -> bool:
    if not FULL_SHA.fullmatch(older) or not FULL_SHA.fullmatch(newer):
        return False
    result = subprocess.run(["git", "merge-base", "--is-ancestor", older, newer], cwd=Path(repo_root), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    return result.returncode == 0


def reviewer_allowed(policy: dict, reviewer_class: str, reviewer_id: str) -> bool:
    allowed = set(policy["reviewer_preferences"][reviewer_class])
    if reviewer_class == "fast":
        allowed.update(policy["reviewer_preferences"].get("deep", []))
    return reviewer_id in allowed


def verify_records(comments: list[dict], *, policy: dict, repo_root: str | Path, tier: str, fingerprint: str, head: str, repository: str, pr_number: int) -> dict:
    required_class = policy["review_tiers"][tier]["reviewer_class"]
    prefix = f"https://github.com/{repository}/pull/{pr_number}"
    for comment in reversed(comments):
        if comment.get("author_association") not in TRUSTED_ASSOCIATIONS:
            continue
        record = parse_record(comment.get("body") or "")
        if not record:
            continue
        reviewed_head = record.get("REVIEWED_HEAD", "")
        if record.get("RESULT") != "PASS":
            continue
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
        source = record.get("REVIEW_SOURCE_URL", "")
        if not source.startswith(prefix):
            continue
        return {"comment_id": comment.get("id"), "reviewed_head": reviewed_head, "reviewer_id": reviewer_id, "review_source_url": source}
    raise RuntimeError("no trusted PASS AI review record matches this tier/fingerprint/head ancestry")


def fetch_comments(repository: str, pr_number: int, token: str) -> list[dict]:
    comments: list[dict] = []
    page = 1
    while True:
        url = f"https://api.github.com/repos/{repository}/issues/{pr_number}/comments?per_page=100&page={page}"
        request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "Authorization": f"Bearer {token}", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "oteryn-ai-review-gate"})
        with urllib.request.urlopen(request, timeout=30) as response:
            batch = json.load(response)
        comments.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return comments


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--pr-number", required=True, type=int)
    parser.add_argument("--tier", required=True, choices=("R1", "R2"))
    parser.add_argument("--fingerprint", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--policy-file", required=True)
    parser.add_argument("--token", required=True)
    args = parser.parse_args()
    policy = json.loads(Path(args.policy_file).read_text(encoding="utf-8"))
    match = verify_records(fetch_comments(args.repository, args.pr_number, args.token), policy=policy, repo_root=args.repo_root, tier=args.tier, fingerprint=args.fingerprint, head=args.head, repository=args.repository, pr_number=args.pr_number)
    print(json.dumps(match, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
