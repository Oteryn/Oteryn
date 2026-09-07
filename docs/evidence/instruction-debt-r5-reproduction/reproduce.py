#!/usr/bin/env python3
"""Read-only R5 reproducibility replacement; not the unrecovered original pack.

Pass downloaded immutable provider sources. No network, repository writes, CI
claims or provider runtime execution. Only selected snapshot functions run.
"""
from __future__ import annotations
import argparse
import ast
import dataclasses
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import types

SOURCES = {
    "platform": ("Oteryn/Oteryn-Platform", "3b2ea1c7392187d5d22488673073dc8f8305a374",
                 "tools/agents/task_issue_liveness.py", "1634a776976d231b10e8d322c49a2a1ed087eb6b"),
    "atlas": ("Oteryn/Oteryn-Atlas", "51623c7dab2346cee39cd51e3caa845bf4b65426",
              "tools/maintenance/verify-maintenance-diff.mjs", "714fb73fe08b7c741d606c6e5a8ecdf33a3adf10"),
}

def verified_source(path: Path, key: str) -> str:
    raw = path.read_bytes()
    actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if actual != SOURCES[key][3]:
        raise ValueError(f"{key}: immutable source blob mismatch: {actual}")
    return raw.decode("utf-8")

def liveness_cases(source: str) -> list[dict]:
    tree = ast.parse(source)
    names = {"Policy", "Finding", "TaskResult", "evaluate_tasks"}
    selected = [n for n in tree.body if isinstance(n, (ast.ClassDef, ast.FunctionDef)) and n.name in names]
    if {n.name for n in selected} != names:
        raise ValueError("required snapshot definitions absent")
    module = types.ModuleType("r5_isolated_liveness")
    sys.modules[module.__name__] = module
    module.__dict__.update(dataclasses=dataclasses, Path=Path)
    body = [ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), *selected]
    exec(compile(ast.fix_missing_locations(ast.Module(body=body, type_ignores=[])), "verified-snapshot", "exec"), module.__dict__)
    policy = module.Policy(1, "governing_issue", frozenset({"open"}), 1)
    results = []
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        cases = [("L01", "missing", True, 0), ("L02", "regular-file", True, 0),
                 ("L03", "empty-directory", True, 0), ("L04", "readme-only", True, 0),
                 ("L05", "stub-error", False, 1), ("L06", "stub-valid", True, 1)]
        for identifier, kind, expected_valid, expected_tasks in cases:
            active = root / identifier
            if kind == "regular-file":
                active.write_text("not a directory", encoding="utf-8")
            elif kind != "missing":
                active.mkdir()
                if kind == "readme-only":
                    (active / "README.md").write_text("context", encoding="utf-8")
                elif kind.startswith("stub-"):
                    (active / "task.md").write_text("stub", encoding="utf-8")
            def evaluate_task(path: Path, **kwargs):
                findings = (module.Finding("error", "PROBE", "controlled stub"),) if kind == "stub-error" else ()
                return module.TaskResult("probe", path.name, "fixture#1", not findings, "open", findings)
            module.evaluate_task = evaluate_task
            observed = module.evaluate_tasks(active, repository=SOURCES["platform"][0], client=None, policy=policy)
            row = {"case": identifier, "fixture": kind, "live_valid": observed["live_valid"],
                   "task_count": len(observed["tasks"]), "errors": observed["errors"]}
            row["matches_reported_behavior"] = row["live_valid"] == expected_valid and row["task_count"] == expected_tasks
            results.append(row)
    return results

def atlas_cases(source: str) -> list[dict]:
    # Fixed, blob-verified source delimiters; execute no CLI or process/git logic.
    selected = source.split("function allowedNormal(change){", 1)[1].split("\nfunction verifyNormal(", 1)[0]
    function = "function allowedNormal(change){" + selected
    archive = source.split("const ARCHIVE_ROOT=", 1)[1].split(";", 1)[0]
    cases = [
        ("A01", {"status":"M", "path":"AGENTS.md"}, True),
        ("A02", {"status":"A", "path":"docs/agents/META_AGENT_POLICY_BINDING.json"}, True),
        ("A03", {"status":"A", "path":".codex/agents/auditor.toml"}, False),
        ("A04", {"status":"A", "path":".agents/skills/review/SKILL.md"}, False),
        ("A05", {"status":"R", "oldPath":"docs/agents/tasks/active/a.md", "path":"docs/agents/tasks/archive/a.md"}, "error"),
        ("A06", {"status":"M", "path":"tools/maintenance/verify-maintenance-diff.mjs"}, "error"),
        ("A07", {"status":"M", "path":"src/runtime.ts"}, False),
    ]
    program = "const ARCHIVE_ROOT=" + archive + ";\nfunction fail(message){throw new TypeError(message);}\n" + function
    program += "\nconst cases=" + json.dumps(cases) + ";\n"
    program += "console.log(JSON.stringify(cases.map(([id,change,expected])=>{let observed;try{observed=allowedNormal(change)}catch(error){observed='error'}return {case:id,change,observed,matches_reported_behavior:observed===expected}})));"
    result = subprocess.run(["node", "-e", program], capture_output=True, text=True, check=True)
    return json.loads(result.stdout)

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform-source", required=True, type=Path)
    parser.add_argument("--atlas-source", required=True, type=Path)
    args = parser.parse_args()
    results = liveness_cases(verified_source(args.platform_source, "platform")) + atlas_cases(verified_source(args.atlas_source, "atlas"))
    report = {"schema_version":1, "kind":"new reproducibility replacement; original pack not authenticated",
              "scope":"isolated functions on historical immutable snapshots; not current provider runtime/CI",
              "python":platform.python_version(),
              "node":subprocess.run(["node", "--version"], capture_output=True, text=True, check=True).stdout.strip(),
              "sources":{key:dict(zip(("repository", "commit", "path", "blob"), value)) for key,value in SOURCES.items()},
              "results":results, "matches":sum(row["matches_reported_behavior"] for row in results)}
    print(json.dumps(report, indent=2))
    return 0 if report["matches"] == len(results) else 1

if __name__ == "__main__":
    raise SystemExit(main())
