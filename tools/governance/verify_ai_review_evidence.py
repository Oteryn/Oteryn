#!/usr/bin/env python3
from __future__ import annotations

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
_OBSERVED_CLEAN_FLAIR = "Already looking forward to the next diff."


def _compat_parse_clean_result(body: str) -> str | None:
    """Accept only the newly observed exact cosmetic Codex clean-result suffix."""
    exact = _v1._compat_parse_clean_result(body)
    if exact is not None:
        return exact
    text = (body or "").strip()
    lines = text.splitlines()
    if not lines or lines[0] != f"{_CLEAN_PREFIX} {_OBSERVED_CLEAN_FLAIR}":
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
