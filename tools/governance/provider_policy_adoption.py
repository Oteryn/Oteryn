#!/usr/bin/env python3
"""Compatibility entry point for central META provider-overlay validation."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from central_agent_policy import load_policy, validate_provider_overlay

ROOT = Path(__file__).resolve().parents[2]


def validate_provider_agents_text(provider: str, text: str) -> list[str]:
    """Delegate provider AGENTS validation to the single central policy authority."""
    try:
        policy = load_policy(ROOT)
    except (OSError, json.JSONDecodeError, ValueError):
        return ["central META provider policy is unavailable"]
    return validate_provider_overlay(provider, text, policy=policy)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", required=True, help="Exact provider repository coordinate")
    parser.add_argument("--file", required=True, type=Path, help="Provider root AGENTS.md file")
    args = parser.parse_args()
    try:
        text = args.file.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"FAIL {args.provider}: unable to read provider AGENTS file: {exc}")
        return 1
    errors = validate_provider_agents_text(args.provider, text)
    if errors:
        for error in errors:
            print(f"FAIL {args.provider}: {error}")
        return 1
    print(f"PASS {args.provider}: central META provider overlay boundary satisfied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
