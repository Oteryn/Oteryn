#!/usr/bin/env python3
from __future__ import annotations

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
_BENIGN_CLEAN_FLAIR_RE = re.compile(r"^[A-Za-z][A-Za-z0-9' ,.!?-]{0,95}$")
_CONTRADICTORY_CLEAN_FLAIR_RE = re.compile(
    r"(?i)\b(?:p0|p1|p2|issue|issues|finding|findings|problem|problems|bug|bugs|"
    r"risk|risks|security|vulnerab(?:ility|ilities)|however|but|except|warning|"
    r"warnings|concern|concerns|must|should|need|needs|fix|fixes|fail|fails|"
    r"failing|error|errors|broken|breaks|not|mostly|major|flaw|flaws|remain|remains)\b"
)


def _compat_parse_clean_result(body: str) -> str | None:
    """Accept bounded cosmetic Codex flair without weakening clean-result semantics.

    The authenticated, immutable Codex result must still begin with the canonical
    clean assertion and retain the exact Reviewed commit shape. Known historical
    variants remain handled by v1; previously unseen suffixes are accepted only as
    bounded plain-text flair and fail closed on finding/problem language.
    """
    exact = _v1._compat_parse_clean_result(body)
    if exact is not None:
        return exact
    text = (body or "").strip()
    lines = text.splitlines()
    if not lines or not lines[0].startswith(_CLEAN_PREFIX + " "):
        return None
    flair = lines[0][len(_CLEAN_PREFIX) + 1:]
    if (
        not _BENIGN_CLEAN_FLAIR_RE.fullmatch(flair)
        or _CONTRADICTORY_CLEAN_FLAIR_RE.search(flair)
    ):
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


_v1._core.parse_clean_result = _compat_parse_clean_result
_v1._core.verify_records = _compat_verify_records_v2
globals()["_core"] = _v1._core
globals()["_compat_parse_clean_result"] = _compat_parse_clean_result
globals()["_compat_fetch_review_source_v2"] = _compat_fetch_review_source_v2
globals()["_compat_verify_records_v2"] = _compat_verify_records_v2
globals()["fetch_review_source"] = _compat_fetch_review_source_v2
globals()["verify_records"] = _compat_verify_records_v2


if __name__ == "__main__":
    raise SystemExit(_v1._core.main())
