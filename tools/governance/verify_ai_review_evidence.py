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
_original_parse_clean_result = _core.parse_clean_result

_CLEAN_PREFIX = "Codex Review: Didn't find any major issues."
# Do not heuristically classify arbitrary bot prose as celebratory. Compatibility
# is intentionally limited to exact observed Codex clean-result variants.
_ALLOWED_CLEAN_FLAIR = {"Swish!", "Hooray!", "Chef's kiss."}


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


def _compat_parse_clean_result(body: str) -> str | None:
    # Preserve every already accepted exact shape first.
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

    # Strip only the exact allowlisted compatibility token. The preserved strict
    # parser still owns every other part of the result envelope.
    normalized = "\n".join([_CLEAN_PREFIX, *lines[1:]])
    return _original_parse_clean_result(normalized)


def _compat_issue_comment_result(comments: list[dict], **kwargs) -> dict:
    # Migration compatibility is intentionally limited to request-generation
    # ambiguity. The global blocker scan must retain the complete historical
    # request set so later trusted P0/P1 findings can never be detached/erased.
    filtered = _filter_pre_rollout_unstructured_requests(
        comments,
        repo_root=kwargs["repo_root"], head=kwargs["head"],
        repository=kwargs["repository"], pr_number=kwargs["pr_number"],
    )
    return _original_issue_comment_result(filtered, **kwargs)


_core.parse_clean_result = _compat_parse_clean_result
_core._verify_issue_comment_result = _compat_issue_comment_result
# Deliberately do NOT wrap/replace _blocking_findings_for_current_generation.
# The preserved fail-closed core sees all historical requests and findings.

# Re-export the established verifier API so existing tests/callers remain unchanged.
for _name in dir(_core):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_core, _name)

# Keep compatibility controls visible for regression tests and diagnostics.
globals()["REQUEST_ANCHOR_ROLLOUT_COMMIT"] = REQUEST_ANCHOR_ROLLOUT_COMMIT
globals()["_request_anchor_rollout_time"] = _request_anchor_rollout_time
globals()["_filter_pre_rollout_unstructured_requests"] = _filter_pre_rollout_unstructured_requests
globals()["_compat_parse_clean_result"] = _compat_parse_clean_result


if __name__ == "__main__":
    raise SystemExit(_core.main())
