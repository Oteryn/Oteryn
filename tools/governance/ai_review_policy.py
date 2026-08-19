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


def load_policy(path: str | Path | None = None) -> dict:
    policy_path = Path(path) if path is not None else DEFAULT_POLICY
    data = json.loads(policy_path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("unsupported ai-review-policy schema_version")
    return data


def matches(path: str, patterns: list[str]) -> bool:
    for pattern in patterns:
        if fnmatch.fnmatchcase(path, pattern):
            return True
        if pattern.startswith("**/") and fnmatch.fnmatchcase(path, pattern[3:]):
            return True
    return False


def git(repo_root: str | Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=Path(repo_root), text=True, encoding="utf-8")


def changed_paths(repo_root: str | Path, base: str, head: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-status", "-z", "-M", "-C", f"{base}...{head}"],
        cwd=Path(repo_root), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("git diff --name-status failed")
    fields = result.stdout.split(b"\0")
    if fields and fields[-1] == b"":
        fields.pop()
    paths: set[str] = set()
    index = 0
    while index < len(fields):
        status = fields[index].decode("ascii", errors="strict")
        index += 1
        count = 2 if status.startswith(("R", "C")) else 1
        if index + count > len(fields):
            raise RuntimeError("malformed NUL-delimited git name-status output")
        names = [value.decode("utf-8", errors="surrogateescape") for value in fields[index:index + count]]
        paths.update(names)
        index += count
    return sorted(paths)


def patch_for(repo_root: str | Path, base: str, head: str, paths: list[str] | None = None) -> str:
    cmd = ["diff", "--no-ext-diff", "--unified=0", f"{base}...{head}"]
    if paths:
        cmd += ["--", *paths]
    return git(repo_root, *cmd)


def changed_content_lines(patch: str) -> list[str]:
    return [line[1:] for _, line in changed_signed_lines(patch)]


def changed_signed_lines(patch: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for line in patch.splitlines():
        if line.startswith(("+++", "---", "@@", "diff --git", "index ")):
            continue
        if line.startswith(("+", "-")):
            out.append((line[0], line))
    return out


def composer_dev_patch_only(*args, **kwargs) -> bool:
    # Disabled fail-closed: this optimization may not bypass review until a stronger proof exists.
    return False


def lifecycle_metadata_only(*args, **kwargs) -> bool:
    # Disabled fail-closed: this optimization may not bypass review until a stronger proof exists.
    return False


def immutable_action_pin_only(*args, **kwargs) -> bool:
    # Disabled fail-closed: this optimization may not bypass review until a stronger proof exists.
    return False


def executable_or_config_path(path: str, policy: dict) -> bool:
    p=PurePosixPath(path); name=p.name.casefold(); suffix=p.suffix.casefold()
    return suffix in set(policy.get("r1_code_extensions",[])) or suffix in set(policy.get("r1_config_extensions",[])) or name in {x.casefold() for x in policy.get("r1_executable_filenames",[])}


def safe_r0_path(path: str, patterns: list[str], policy: dict) -> bool:
    if not matches(path, patterns):
        return False
    if matches(path, policy.get("always_r2_globs", [])):
        return False
    if matches(path, policy.get("r1_dependency_globs", [])):
        return False
    if executable_or_config_path(path, policy):
        return False
    return PurePosixPath(path).suffix.casefold() in set(policy.get("r0_safe_data_extensions", []))


def git_metadata_risk(patch: str) -> bool:
    # Executable, symlink and gitlink/submodule modes must never be review-neutral safe data.
    risky_modes = ("100755", "120000", "160000")
    for line in patch.splitlines():
        if line.startswith(("old mode ", "new mode ", "new file mode ", "deleted file mode ")):
            if any(mode in line for mode in risky_modes):
                return True
    return False


def classify(paths: list[str], patch: str, policy: dict) -> tuple[str, list[str]]:
    reasons: list[str] = []
    lines = changed_content_lines(patch)
    changed_line_count = len(lines)

    r2_paths = [p for p in paths if matches(p, policy["always_r2_globs"])]
    if r2_paths:
        reasons.append("r2_path:" + ",".join(sorted(r2_paths)))

    prose_extensions = set(policy.get("r0_prose_extensions", []))
    prose_only = bool(paths) and all(PurePosixPath(path).suffix.lower() in prose_extensions for path in paths)
    if not prose_only:
        changed_text = "\n".join(lines).casefold()
        markers = [marker for marker in policy["r2_changed_line_markers"] if marker.casefold() in changed_text]
        if markers:
            reasons.append("r2_marker:" + ",".join(markers))
    if changed_line_count >= policy["size_thresholds"]["r2_changed_lines"]:
        reasons.append(f"r2_size:{changed_line_count}")
    if reasons:
        return "R2", reasons

    dependency_files = [p for p in paths if matches(p, policy.get("r1_dependency_globs", []))]
    if dependency_files:
        dependency_text = "\n".join(lines).casefold()
        sensitive = [m for m in policy.get("r2_sensitive_dependency_markers", []) if m.casefold() in dependency_text]
        if sensitive:
            return "R2", ["security_sensitive_dependency:" + ",".join(sensitive)]
        return "R1", ["dependency_manifest_or_lockfile:" + ",".join(sorted(dependency_files))]

    if git_metadata_risk(patch):
        return "R1", ["executable_or_symlink_mode_change"]

    executable = [p for p in paths if executable_or_config_path(p, policy)]
    if executable or changed_line_count >= policy["size_thresholds"]["r1_changed_lines"]:
        return "R1", ["ordinary_code_config_or_size"]
    if paths and all(safe_r0_path(p, policy["standalone_r0_globs"], policy) for p in paths):
        return "R0", ["standalone_r0_safe_data_only"]
    if any(PurePosixPath(p).suffix.casefold() not in prose_extensions for p in paths):
        return "R1", ["unknown_non_prose_path"]
    return "R0", ["non_sensitive_prose_change"]


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
    neutral: list[str] = []
    for path in paths:
        if not safe_r0_path(path, policy["review_neutral_globs"], policy):
            continue
        # Path-only extension checks are insufficient for Git type/mode changes. Bind
        # executable, symlink and gitlink metadata changes into the reviewed fingerprint.
        if git_metadata_risk(patch_for(repo_root, base, head, [path])):
            continue
        neutral.append(path)
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
