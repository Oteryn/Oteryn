#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import subprocess
from pathlib import Path, PurePosixPath

DEFAULT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY = DEFAULT_ROOT / "ecosystem/ai-review-policy.json"
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
ACTION_USE = re.compile(r"^\s*uses:\s*([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)?)@([0-9a-f]{40})\s+#\s*v?(\d+)(?:\.\d+)*(?:\s.*)?$")


def load_policy(path: str | Path | None = None) -> dict:
    policy_path = Path(path) if path is not None else DEFAULT_POLICY
    data = json.loads(policy_path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("unsupported ai-review-policy schema_version")
    return data


def matches(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def git(repo_root: str | Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=Path(repo_root), text=True, encoding="utf-8")


def changed_paths(repo_root: str | Path, base: str, head: str) -> list[str]:
    return [p for p in git(repo_root, "diff", "--name-only", f"{base}...{head}").splitlines() if p]


def patch_for(repo_root: str | Path, base: str, head: str, paths: list[str] | None = None) -> str:
    cmd = ["diff", "--no-ext-diff", "--unified=0", f"{base}...{head}"]
    if paths:
        cmd += ["--", *paths]
    return git(repo_root, *cmd)


def changed_content_lines(patch: str) -> list[str]:
    out: list[str] = []
    for line in patch.splitlines():
        if line.startswith(("+++", "---", "@@", "diff --git", "index ")):
            continue
        if line.startswith(("+", "-")):
            out.append(line[1:])
    return out


def json_at(repo_root: str | Path, revision: str, path: str) -> dict | None:
    result = subprocess.run(
        ["git", "show", f"{revision}:{path}"],
        cwd=Path(repo_root),
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        return None
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def semver_triplet(value: object) -> tuple[int, int, int] | None:
    if not isinstance(value, str):
        return None
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", value.strip())
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def composer_dev_patch_only(repo_root: str | Path, base: str, head: str, paths: list[str], policy: dict) -> bool:
    if paths != ["composer.lock"]:
        return False
    before = json_at(repo_root, base, "composer.lock")
    after = json_at(repo_root, head, "composer.lock")
    if before is None or after is None:
        return False
    before_runtime = before.get("packages")
    after_runtime = after.get("packages")
    if before_runtime != after_runtime:
        return False
    before_dev = before.get("packages-dev")
    after_dev = after.get("packages-dev")
    if not isinstance(before_dev, list) or not isinstance(after_dev, list):
        return False
    before_by_name = {item.get("name"): item for item in before_dev if isinstance(item, dict) and isinstance(item.get("name"), str)}
    after_by_name = {item.get("name"): item for item in after_dev if isinstance(item, dict) and isinstance(item.get("name"), str)}
    if set(before_by_name) != set(after_by_name):
        return False
    changed = [name for name in sorted(before_by_name) if before_by_name[name] != after_by_name[name]]
    if len(changed) != 1:
        return False
    package = changed[0]
    if any(marker.casefold() in package.casefold() for marker in policy.get("r2_sensitive_dependency_markers", [])):
        return False
    old_version = semver_triplet(before_by_name[package].get("version"))
    new_version = semver_triplet(after_by_name[package].get("version"))
    if old_version is None or new_version is None:
        return False
    if old_version[:2] != new_version[:2] or new_version[2] <= old_version[2]:
        return False
    before_other = {key: value for key, value in before.items() if key != "packages-dev"}
    after_other = {key: value for key, value in after.items() if key != "packages-dev"}
    return before_other == after_other


def lifecycle_metadata_only(paths: list[str], patch: str) -> bool:
    if len(paths) != 1 or not matches(paths[0], ["docs/agents/tasks/active/**"]):
        return False
    if "new file mode" in patch or "deleted file mode" in patch:
        return False
    lines = [line.strip() for line in changed_content_lines(patch) if line.strip()]
    if not lines:
        return False
    allowed_keys = {
        "status",
        "owner",
        "branch",
        "lifecycle_authority",
        "lifecycle_issue",
        "coordination_origin_branch",
        "coordination_origin_branch_state",
    }
    for line in lines:
        key = line.split(":", 1)[0].strip() if ":" in line else ""
        if key in allowed_keys:
            continue
        if line.startswith("> Lifecycle state, ownership, dependencies and acceptance are authoritative in GitHub Issue #"):
            continue
        return False
    return True


def immutable_action_pin_only(paths: list[str], patch: str) -> bool:
    if not paths or not all(p.startswith(".github/workflows/") and p.endswith((".yml", ".yaml")) for p in paths):
        return False
    lines = [line for line in changed_content_lines(patch) if line.strip()]
    if not lines:
        return False
    matches_: list[re.Match[str]] = []
    for line in lines:
        match = ACTION_USE.match(line)
        if not match:
            return False
        matches_.append(match)
    identities = [match.group(1) for match in matches_]
    majors = [match.group(3) for match in matches_]
    return (
        len(identities) % 2 == 0
        and all(identities[i] == identities[i + 1] for i in range(0, len(identities), 2))
        and all(majors[i] == majors[i + 1] for i in range(0, len(majors), 2))
    )


def classify(paths: list[str], patch: str, policy: dict) -> tuple[str, list[str]]:
    reasons: list[str] = []
    lines = changed_content_lines(patch)
    changed_line_count = len(lines)

    if immutable_action_pin_only(paths, patch) and policy["special_r0_rules"].get("immutable_action_pin_only"):
        return "R0", ["immutable_action_pin_only"]

    if lifecycle_metadata_only(paths, patch) and policy["special_r0_rules"].get("lifecycle_metadata_only"):
        return "R0", ["lifecycle_metadata_only"]

    if paths and all(matches(p, policy["standalone_r0_globs"]) for p in paths):
        return "R0", ["standalone_r0_paths_only"]

    r2_paths = [p for p in paths if matches(p, policy["always_r2_globs"])]
    if r2_paths:
        reasons.append("r2_path:" + ",".join(sorted(r2_paths)))

    prose_extensions = set(policy.get("r0_prose_extensions", []))
    prose_only = bool(paths) and all(PurePosixPath(path).suffix.lower() in prose_extensions for path in paths)
    if not prose_only:
        changed_text = "\n".join(lines).casefold()
        marker_key = "r2_changed_line_markers" if "r2_changed_line_markers" in policy else "r2_added_line_markers"
        markers = [marker for marker in policy[marker_key] if marker.casefold() in changed_text]
        if markers:
            reasons.append("r2_marker:" + ",".join(markers))

    if changed_line_count >= policy["size_thresholds"]["r2_changed_lines"]:
        reasons.append(f"r2_size:{changed_line_count}")

    if reasons:
        return "R2", reasons

    dependency_files = [p for p in paths if matches(p, policy.get("r1_dependency_globs", []))]
    if dependency_files:
        dependency_text = "\n".join(lines).casefold()
        sensitive_dependencies = [
            marker for marker in policy.get("r2_sensitive_dependency_markers", [])
            if marker.casefold() in dependency_text
        ]
        if sensitive_dependencies:
            return "R2", ["security_sensitive_dependency:" + ",".join(sensitive_dependencies)]
        return "R1", ["dependency_manifest_or_lockfile:" + ",".join(sorted(dependency_files))]

    code_extensions = set(policy["r1_code_extensions"])
    code = [p for p in paths if PurePosixPath(p).suffix.lower() in code_extensions]
    if code or changed_line_count >= policy["size_thresholds"]["r1_changed_lines"]:
        return "R1", ["ordinary_code_or_size"]

    return "R0", ["non_sensitive_non_executable_change"]


def blob_at(repo_root: str | Path, revision: str, path: str) -> str:
    result = subprocess.run(
        ["git", "rev-parse", f"{revision}:{path}"],
        cwd=Path(repo_root),
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "ABSENT"


def fingerprint(repo_root: str | Path, base: str, head: str, paths: list[str], policy: dict) -> tuple[str, list[str], list[str]]:
    neutral = [p for p in paths if matches(p, policy["review_neutral_globs"])]
    bearing = [p for p in paths if p not in neutral]
    payload = {
        "base_context_blobs": {path: blob_at(repo_root, base, path) for path in sorted(bearing)},
        "bearing_paths": sorted(bearing),
        "patch": patch_for(repo_root, base, head, sorted(bearing)) if bearing else "",
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return digest, bearing, neutral


def evaluate(base: str, head: str, repo_root: str | Path | None = None, policy_file: str | Path | None = None) -> dict:
    repository = Path(repo_root) if repo_root is not None else DEFAULT_ROOT
    policy = load_policy(policy_file)
    for value, label in ((base, "base"), (head, "head")):
        if not FULL_SHA.fullmatch(value):
            raise ValueError(f"{label} must be a lowercase 40-hex SHA")
    paths = changed_paths(repository, base, head)
    patch = patch_for(repository, base, head)
    if policy.get("special_r0_rules", {}).get("composer_dev_patch_only") and composer_dev_patch_only(repository, base, head, paths, policy):
        tier, reasons = "R0", ["composer_dev_patch_only"]
    else:
        tier, reasons = classify(paths, patch, policy)
    digest, bearing, neutral = fingerprint(repository, base, head, paths, policy)
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
    parser.add_argument("--repo-root", default=str(DEFAULT_ROOT))
    parser.add_argument("--policy-file", default=str(DEFAULT_POLICY))
    args = parser.parse_args()
    print(json.dumps(evaluate(args.base, args.head, args.repo_root, args.policy_file), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
