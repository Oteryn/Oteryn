#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import subprocess
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "ecosystem/ai-review-policy.json"
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
ACTION_USE = re.compile(r"^\s*uses:\s*([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)?)@([0-9a-f]{40})(?:\s+#.*)?$")


def load_policy() -> dict:
    data = json.loads(POLICY.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("unsupported ai-review-policy schema_version")
    return data


def matches(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True, encoding="utf-8")


def changed_paths(base: str, head: str) -> list[str]:
    return [p for p in git("diff", "--name-only", f"{base}...{head}").splitlines() if p]


def patch_for(base: str, head: str, paths: list[str] | None = None) -> str:
    cmd = ["diff", "--no-ext-diff", "--unified=0", f"{base}...{head}"]
    if paths:
        cmd += ["--", *paths]
    return git(*cmd)


def changed_content_lines(patch: str) -> list[str]:
    out: list[str] = []
    for line in patch.splitlines():
        if line.startswith(("+++", "---", "@@", "diff --git", "index ")):
            continue
        if line.startswith(("+", "-")):
            out.append(line[1:])
    return out


def added_content_lines(patch: str) -> list[str]:
    return [line[1:] for line in patch.splitlines() if line.startswith("+") and not line.startswith("+++")]


def immutable_action_pin_only(paths: list[str], patch: str) -> bool:
    if not paths or not all(p.startswith(".github/workflows/") and p.endswith((".yml", ".yaml")) for p in paths):
        return False
    lines = [line for line in changed_content_lines(patch) if line.strip()]
    if not lines:
        return False
    matches_: list[re.Match[str]] = []
    for line in lines:
        m = ACTION_USE.match(line)
        if not m:
            return False
        matches_.append(m)
    identities = [m.group(1) for m in matches_]
    return len(identities) % 2 == 0 and all(identities[i] == identities[i + 1] for i in range(0, len(identities), 2))


def classify(paths: list[str], patch: str, policy: dict) -> tuple[str, list[str]]:
    reasons: list[str] = []
    lines = changed_content_lines(patch)
    changed_line_count = len(lines)

    if immutable_action_pin_only(paths, patch) and policy["special_r0_rules"].get("immutable_action_pin_only"):
        return "R0", ["immutable_action_pin_only"]

    if paths and all(matches(p, policy["standalone_r0_globs"]) for p in paths):
        return "R0", ["standalone_r0_paths_only"]

    r2_paths = [p for p in paths if matches(p, policy["always_r2_globs"])]
    if r2_paths:
        reasons.append("r2_path:" + ",".join(sorted(r2_paths)))

    additions = "\n".join(added_content_lines(patch)).casefold()
    markers = [m for m in policy["r2_added_line_markers"] if m.casefold() in additions]
    if markers:
        reasons.append("r2_marker:" + ",".join(markers))

    if changed_line_count >= policy["size_thresholds"]["r2_changed_lines"]:
        reasons.append(f"r2_size:{changed_line_count}")

    if reasons:
        return "R2", reasons

    code = [p for p in paths if PurePosixPath(p).suffix.lower() in set(policy["r1_code_extensions"])]
    if code or changed_line_count >= policy["size_thresholds"]["r1_changed_lines"]:
        return "R1", ["ordinary_code_or_size"]

    return "R0", ["non_sensitive_non_executable_change"]


def fingerprint(base: str, head: str, paths: list[str], policy: dict) -> tuple[str, list[str], list[str]]:
    neutral = [p for p in paths if matches(p, policy["review_neutral_globs"])]
    bearing = [p for p in paths if p not in neutral]
    payload = {
        "base": base,
        "bearing_paths": sorted(bearing),
        "patch": patch_for(base, head, sorted(bearing)) if bearing else "",
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return digest, bearing, neutral


def evaluate(base: str, head: str) -> dict:
    policy = load_policy()
    for value, label in ((base, "base"), (head, "head")):
        if not FULL_SHA.fullmatch(value):
            raise ValueError(f"{label} must be a lowercase 40-hex SHA")
    paths = changed_paths(base, head)
    patch = patch_for(base, head)
    tier, reasons = classify(paths, patch, policy)
    digest, bearing, neutral = fingerprint(base, head, paths, policy)
    return {
        "schema_version": 1,
        "policy_id": policy["policy_id"],
        "base": base,
        "head": head,
        "tier": tier,
        "external_review": policy["review_tiers"][tier]["external_review"],
        "reviewer_class": policy["review_tiers"][tier]["reviewer_class"],
        "review_fingerprint": digest,
        "changed_paths": paths,
        "risk_bearing_paths": bearing,
        "review_neutral_paths": neutral,
        "reasons": reasons,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    args = parser.parse_args()
    print(json.dumps(evaluate(args.base, args.head), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
