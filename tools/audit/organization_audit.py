#!/usr/bin/env python3
"""Read-only immutable Git inventory collector. Enumeration is NOT semantic review.

Only public Oteryn repositories in ALLOWED are admitted. Provider code is never
checked out or executed. Optional object transport is a temporary audit artifact,
not META-owned provider source. No credentials, API mutations or remote pushes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
from pathlib import Path
import re
import subprocess
import tempfile
from datetime import datetime, timezone
import zipfile

ALLOWED = frozenset({
    "Oteryn/Oteryn", "Oteryn/Oteryn-Game", "Oteryn/Oteryn-Platform",
    "Oteryn/Oteryn-Atlas", "Oteryn/Oteryn-Platform-Migration-Backup-20260818",
})
SHA = re.compile(r"[0-9a-f]{40}\Z")
IDENTIFIER = re.compile(r"[a-z][a-z0-9_-]{0,63}\Z")
MAX_BLOB = 16 * 1024 * 1024
MAX_OBJECT_BYTES = 256 * 1024 * 1024
MAX_PATHS = 50000
GIT = ["git", "-c", "core.hooksPath=/dev/null", "-c", "credential.helper=",
       "-c", "protocol.file.allow=never", "-c", "protocol.ext.allow=never"]


def git(cwd: Path, *args: str) -> bytes:
    env = {k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "GH_", "GITHUB_"))}
    env.update(GIT_TERMINAL_PROMPT="0", GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL="/dev/null")
    return subprocess.run(GIT + list(args), cwd=cwd, env=env, check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180).stdout


def validate_plan(plan: object) -> list[dict]:
    if not isinstance(plan, dict) or type(plan.get("schema_version")) is not int or plan["schema_version"] != 1:
        raise ValueError("plan schema_version must be 1")
    rows = plan.get("snapshots")
    if not isinstance(rows, list) or not 1 <= len(rows) <= 16:
        raise ValueError("plan must have 1..16 immutable snapshots")
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or row.get("repository") not in ALLOWED:
            raise ValueError("repository is not allowlisted")
        key, sha = row.get("id"), row.get("commit_sha")
        if not isinstance(key, str) or not IDENTIFIER.fullmatch(key) or key in seen:
            raise ValueError("invalid or duplicate snapshot id")
        seen.add(key)
        if not isinstance(sha, str) or not SHA.fullmatch(sha):
            raise ValueError("immutable lowercase 40-character commit SHA required")
        tree = row.get("expected_tree_sha")
        if tree is not None and (not isinstance(tree, str) or not SHA.fullmatch(tree)):
            raise ValueError("invalid expected tree")
        if row.get("role") not in {"audited_source", "historical_evidence", "archive"}:
            raise ValueError("snapshot role is required")
    return rows


def parse_tree(raw: bytes) -> list[dict]:
    if raw and not raw.endswith(b"\0"):
        raise ValueError("incomplete NUL-delimited Git tree")
    entries, seen = [], set()
    for entry in raw.split(b"\0"):
        if not entry:
            continue
        header, path_bytes = entry.split(b"\t", 1)
        mode, kind, oid = header.decode("ascii").split(" ")
        path = path_bytes.decode("utf-8")
        if (not path or path.startswith("/") or "\x00" in path or
                any(part in {"", ".", ".."} for part in path.split("/")) or path in seen):
            raise ValueError("unsafe or duplicate Git path")
        if mode not in {"100644", "100755", "120000", "160000"}:
            raise ValueError("unsupported leaf mode")
        if kind != ("commit" if mode == "160000" else "blob") or not SHA.fullmatch(oid):
            raise ValueError("invalid Git leaf identity")
        seen.add(path)
        entries.append({"path": path, "mode": mode, "type": kind, "object_sha": oid,
                        "disposition": "UNVERIFIED", "evidence_ids": [],
                        "reason": "Enumerated immutable identity; no semantic review inferred."})
    if len(entries) > MAX_PATHS:
        raise ValueError("path limit exceeded")
    return sorted(entries, key=lambda x: x["path"].encode("utf-8"))


def blob_hash(content: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()


def write_bytes_at(directory_fd: int, name: str, raw: bytes) -> None:
    if "/" in name or name in {"", ".", ".."}:
        raise ValueError("unsafe output filename")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(name, flags, 0o600, dir_fd=directory_fd)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(raw)


def write_json_at(directory_fd: int, name: str, value: object) -> None:
    write_bytes_at(directory_fd, name,
                   (json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode())


def create_directory_no_symlinks(path: Path) -> tuple[Path, int]:
    """Create a new directory without following any lexical ancestor symlink."""
    absolute = Path(os.path.abspath(path))
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        try:
            mode = os.lstat(current).st_mode
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(mode):
            raise ValueError("output ancestry must not contain symlinks")
    if os.path.lexists(absolute):
        raise ValueError("output must be a new directory; refusing overwrite or symlink")

    flags = os.O_RDONLY | os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(absolute.anchor, flags)
    try:
        for index, part in enumerate(absolute.parts[1:]):
            final = index == len(absolute.parts[1:]) - 1
            try:
                child = os.open(part, flags, dir_fd=descriptor)
                if final:
                    os.close(child)
                    raise ValueError("output must be a new directory; refusing overwrite or symlink")
            except FileNotFoundError:
                os.mkdir(part, dir_fd=descriptor)
                child = os.open(part, flags, dir_fd=descriptor)
            except OSError as exc:
                raise ValueError("output ancestry must contain only directories, not symlinks") from exc
            os.close(descriptor)
            descriptor = child
    except Exception:
        os.close(descriptor)
        raise
    return absolute, descriptor


def _collect_bound(rows: list[dict], output_fd: int, inventories_fd: int, include_objects: bool) -> dict:
    results, exported, exported_bytes = [], set(), 0
    # Zip entries are object IDs, never provider-controlled filesystem paths.
    archive_handle = None
    if include_objects:
        archive_descriptor = os.open("source-objects.zip", os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                                     getattr(os, "O_NOFOLLOW", 0), 0o600, dir_fd=output_fd)
        archive_handle = os.fdopen(archive_descriptor, "wb")
    archive = zipfile.ZipFile(archive_handle, "w", zipfile.ZIP_DEFLATED) if archive_handle else None
    try:
        with tempfile.TemporaryDirectory(prefix="oteryn-audit-") as tmp:
            repositories = {}
            for row in rows:
                repository, sha, key = row["repository"], row["commit_sha"], row["id"]
                if repository not in repositories:
                    bare = Path(tmp) / repository.split("/")[1]
                    bare.mkdir()
                    git(bare, "init", "--bare", "--quiet")
                    repositories[repository] = bare
                bare = repositories[repository]
                git(bare, "fetch", "--quiet", "--no-tags", "--depth=1",
                    "https://github.com/" + repository + ".git", sha)
                actual = git(bare, "rev-parse", "--verify", sha + "^{commit}").decode().strip()
                tree = git(bare, "rev-parse", sha + "^{tree}").decode().strip()
                if actual != sha or not SHA.fullmatch(tree):
                    raise ValueError("Git identity mismatch")
                if row.get("expected_tree_sha") not in {None, tree}:
                    raise ValueError("expected tree mismatch: " + key)
                entries = parse_tree(git(bare, "ls-tree", "-rz", "--full-tree", sha))
                family_counts = {}
                for entry in entries:
                    family = entry["path"].split("/")[0] if "/" in entry["path"] else "<root>"
                    family_counts[family] = family_counts.get(family, 0) + 1
                    oid = entry["object_sha"]
                    if archive is not None and entry["type"] == "blob" and oid not in exported:
                        size = int(git(bare, "cat-file", "-s", oid).decode().strip())
                        if size > MAX_BLOB or exported_bytes + size > MAX_OBJECT_BYTES:
                            raise ValueError("bounded object transport limit exceeded")
                        data = git(bare, "cat-file", "blob", oid)
                        if len(data) != size or blob_hash(data) != oid:
                            raise ValueError("blob integrity mismatch")
                        archive.writestr(oid, data)
                        exported.add(oid)
                        exported_bytes += len(data)
                inventory = {"schema_version": 1, "snapshot_id": key, "repository": repository,
                             "commit_sha": sha, "tree_sha": tree, "role": row["role"],
                             "leaf_count": len(entries), "family_counts": family_counts,
                             "identity_coverage": "COMPLETE", "semantic_coverage": "NOT_INFERRED",
                             "entries": entries}
                write_json_at(inventories_fd, key + ".json", inventory)
                results.append({k: v for k, v in inventory.items() if k != "entries"})
                print(json.dumps({"snapshot": key, "commit_sha": sha, "tree_sha": tree,
                                  "leaf_count": len(entries), "semantic_coverage": "NOT_INFERRED"}))
    finally:
        if archive is not None:
            archive.close()
        if archive_handle is not None and not archive_handle.closed:
            archive_handle.close()
    summary = {"schema_version": 1, "collected_at": datetime.now(timezone.utc).isoformat(),
               "collector_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "result": "IDENTITY_INVENTORY_COLLECTED_NOT_AUDIT_PASS", "snapshots": results,
               "exported_objects": len(exported), "exported_object_bytes": exported_bytes}
    write_json_at(output_fd, "summary.json", summary)
    names = ["inventories/" + row["snapshot_id"] + ".json" for row in results]
    if include_objects:
        names.append("source-objects.zip")
    names.append("summary.json")
    sums = {}
    for name in sorted(names):
        parent_fd, leaf = (inventories_fd, name.removeprefix("inventories/")) if name.startswith("inventories/") else (output_fd, name)
        descriptor = os.open(leaf, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=parent_fd)
        with os.fdopen(descriptor, "rb") as handle:
            sums[name] = hashlib.sha256(handle.read()).hexdigest()
    write_json_at(output_fd, "SHA256SUMS.json", sums)
    return summary

def collect(plan: dict, output: Path, include_objects: bool = False) -> dict:
    rows = validate_plan(plan)
    _output, output_fd = create_directory_no_symlinks(output)
    inventories_fd = None
    try:
        os.mkdir("inventories", dir_fd=output_fd)
        directory_flags = os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0)
        inventories_fd = os.open("inventories", directory_flags, dir_fd=output_fd)
        return _collect_bound(rows, output_fd, inventories_fd, include_objects)
    finally:
        if inventories_fd is not None:
            os.close(inventories_fd)
        os.close(output_fd)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--include-objects", action="store_true")
    args = parser.parse_args()
    collect(json.loads(args.plan.read_text(encoding="utf-8")), args.output, args.include_objects)


if __name__ == "__main__":
    main()
