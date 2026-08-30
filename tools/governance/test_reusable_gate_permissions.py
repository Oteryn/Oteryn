#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ACTION = ROOT / ".github/actions/ai-review-gate/action.yml"
WORKFLOW = ROOT / ".github/workflows/governance-ai-review.yml"
CONTRACT = ROOT / "docs/governance/AI_REVIEW_REUSABLE_GATE_CONTRACT.md"

REQUIRED = (
    "contents: read",
    "actions: read",
    "checks: read",
    "issues: read",
    "pull-requests: read",
)
FORBIDDEN_PROVIDER_WRITES = (
    "contents: write",
    "actions: write",
    "checks: write",
    "issues: write",
    "pull-requests: write",
    "statuses: write",
)


def main() -> int:
    action = ACTION.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    contract = CONTRACT.read_text(encoding="utf-8")

    token_start = action.find("  github-token:\n")
    outputs_start = action.find("\noutputs:\n", token_start)
    if token_start < 0 or outputs_start < 0:
        raise SystemExit("reusable gate github-token contract block is missing")
    token_block = action[token_start:outputs_start]

    for scope in REQUIRED:
        if scope not in token_block:
            raise SystemExit(f"reusable gate token documentation is missing required scope: {scope}")
        if f"`{scope}`" not in contract:
            raise SystemExit(f"provider wrapper contract is missing required scope: {scope}")
        if f"  {scope}" not in workflow:
            raise SystemExit(f"protected issuer workflow is missing required read permission: {scope}")

    for scope in FORBIDDEN_PROVIDER_WRITES:
        if f"`{scope}`" not in contract:
            raise SystemExit(f"provider wrapper contract must explicitly reject unnecessary permission: {scope}")

    issuer_only = (
        "id-token: write",
        "attestations: write",
        "artifact-metadata: write",
    )
    for scope in issuer_only:
        if f"  {scope}" not in workflow:
            raise SystemExit(f"protected issuer workflow is missing issuer-only permission: {scope}")
        if f"`{scope}`" not in contract:
            raise SystemExit(f"caller contract must distinguish issuer-only permission: {scope}")

    print("Reusable AI review gate permission contract PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
