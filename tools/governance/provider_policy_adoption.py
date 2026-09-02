#!/usr/bin/env python3
"""Deterministically validate provider adoption of META execution-routing authority."""
from __future__ import annotations

import argparse
from pathlib import Path
import re

_HISTORICAL_POLICY_PIN = re.compile(
    r"Oteryn/Oteryn@[0-9a-fA-F]{40}:ecosystem/agent-execution-routing-policy\.json",
    re.IGNORECASE,
)
_PARALLEL_FIRST = re.compile(r"\bparallel[-_]first\b", re.IGNORECASE)
_SERIAL_EXCEPTION = re.compile(
    r"\bserial\s+(?:work|execution)\s+requires?\s+(?:an?\s+)?(?:explicit|recorded)\s+(?:reason|exception)\b",
    re.IGNORECASE,
)


def validate_provider_agents_text(provider: str, text: str) -> list[str]:
    """Return deterministic adoption errors for one provider root AGENTS document."""
    if not isinstance(provider, str) or not provider.strip():
        return ["provider name is invalid"]
    if not isinstance(text, str) or not text.strip():
        return [f"{provider}: provider AGENTS text is empty"]

    errors: list[str] = []
    if _HISTORICAL_POLICY_PIN.search(text):
        errors.append("historical META execution-policy pin is forbidden")
    if _PARALLEL_FIRST.search(text) or _SERIAL_EXCEPTION.search(text):
        errors.append("parallel-first execution wording is forbidden")

    lowered = text.lower()
    has_meta_policy = (
        "oteryn/oteryn" in lowered
        and "ecosystem/agent-execution-routing-policy.json" in lowered
        and "current protected" in lowered
    )
    if not has_meta_policy:
        errors.append("current protected META execution-policy authority is required")
    if "single_agent" not in text:
        errors.append("provider execution policy must name single_agent")
    if "parallel_when_beneficial" not in text:
        errors.append("provider execution policy must name parallel_when_beneficial")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", required=True, help="Provider label used in diagnostics")
    parser.add_argument("--file", required=True, type=Path, help="Provider root AGENTS.md file")
    args = parser.parse_args()
    text = args.file.read_text(encoding="utf-8")
    errors = validate_provider_agents_text(args.provider, text)
    if errors:
        for error in errors:
            print(f"FAIL {args.provider}: {error}")
        return 1
    print(f"PASS {args.provider}: current effort-aware META execution policy adopted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
