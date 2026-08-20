#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# Exact protected-main commit that first made immutable request anchors available.
# A request created before this commit cannot have targeted a descendant commit
# that did not exist yet. Post-rollout unanchored/malformed requests still fail closed.
REQUEST_ANCHOR_ROLLOUT_COMMIT = "dbed59b9cfab1e8a66ac9e0a5056053718980ce3"

_CORE_PATH = Path(__file__).with_name("verify_ai_review_evidence_core.py")
_spec = importlib.util.spec_from_file_location("verify_ai_review_evidence_core", _CORE_PATH)
if _spec is None or _spec.loader is None:
    raise RuntimeError("cannot load immutable AI review verifier core")
_core = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_core)

_original_issue_comment_result = _core._verify_issue_comment_result
_original_blocking_findings = _core._blocking_findings_for_current_generation


def _request_anchor_rollout_time(repo_root: str | Path) -> datetime | None:
    result = subprocess.run(
        ["git", "show", "-s", "--format=%cI", REQUEST_ANCHOR_ROLLOUT_COMMIT],
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


def _filter_pre_rollout_unstructured_requests(
    comments: list[dict], *, repo_root: str | Path, head: str,
    repository: str, pr_number: int,
) -> list[dict]:
    # Fail closed unless the exact rollout commit is present in this reviewed history.
    if not _core.is_ancestor(repo_root, REQUEST_ANCHOR_ROLLOUT_COMMIT, head):
        return comments
    cutoff = _request_anchor_rollout_time(repo_root)
    if cutoff is None:
        return comments

    filtered: list[dict] = []
    for comment in comments:
        body = str(comment.get("body") or "")
        created = _strict_comment_time(comment)
        is_legacy_pre_rollout = (
            _core._is_request_like(comment)
            and _core._issue_comment_identity(comment, repository, pr_number)
            and _core.REQUEST_MARKER not in body
            and _core.parse_request(body) is None
            and created is not None
            and created < cutoff
        )
        if is_legacy_pre_rollout:
            continue
        filtered.append(comment)
    return filtered


def _compat_issue_comment_result(comments: list[dict], **kwargs) -> dict:
    filtered = _filter_pre_rollout_unstructured_requests(
        comments,
        repo_root=kwargs["repo_root"], head=kwargs["head"],
        repository=kwargs["repository"], pr_number=kwargs["pr_number"],
    )
    return _original_issue_comment_result(filtered, **kwargs)


def _compat_blocking_findings_for_current_generation(*, comments: list[dict], **kwargs) -> bool:
    filtered = _filter_pre_rollout_unstructured_requests(
        comments,
        repo_root=kwargs["repo_root"], head=kwargs["head"],
        repository=kwargs["repository"], pr_number=kwargs["pr_number"],
    )
    return _original_blocking_findings(comments=filtered, **kwargs)


_core._verify_issue_comment_result = _compat_issue_comment_result
_core._blocking_findings_for_current_generation = _compat_blocking_findings_for_current_generation

# Re-export the established verifier API so existing tests/callers remain unchanged.
for _name in dir(_core):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_core, _name)

# Keep compatibility controls visible for regression tests and diagnostics.
globals()["REQUEST_ANCHOR_ROLLOUT_COMMIT"] = REQUEST_ANCHOR_ROLLOUT_COMMIT
globals()["_request_anchor_rollout_time"] = _request_anchor_rollout_time
globals()["_filter_pre_rollout_unstructured_requests"] = _filter_pre_rollout_unstructured_requests


if __name__ == "__main__":
    raise SystemExit(_core.main())
