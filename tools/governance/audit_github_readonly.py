#!/usr/bin/env python3
"""Compatibility entrypoint for the read-only Oteryn governance drift audit.

The preserved core contains the validated v3.10 audit implementation. This
entrypoint carries only the terminal interoperability fixes that require
candidate-bound pull_request_target evidence and fail-closed transport handling.
"""
from __future__ import annotations

import importlib.util
import urllib.error
from pathlib import Path

_CORE_PATH = Path(__file__).with_name("audit_github_readonly_core.py")
_SPEC = importlib.util.spec_from_file_location("audit_github_readonly_core", _CORE_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"cannot load governance audit core: {_CORE_PATH}")
core = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(core)

# Public compatibility surface used by tests and callers.
DESIRED_PATH = core.DESIRED_PATH
urllib = core.urllib
ruleset_applies_to_branch = core.ruleset_applies_to_branch
expected_sources_satisfied = core.expected_sources_satisfied
expected_checks = core.expected_checks
expected_check_app_id = core.expected_check_app_id
merge_sources = core.merge_sources


class Audit(core.Audit):
    """Terminal fail-closed fixes over the preserved validated core."""

    def api(self, path: str, *, allow_404: bool = False):
        try:
            return super().api(path, allow_404=allow_404)
        except urllib.error.URLError as exc:
            raise RuntimeError(f"GET {path} -> transport unavailable: {exc.reason}") from exc

    def representative_check_sources(
        self,
        repo: str,
        expected: set[str],
        expected_app_id: int,
    ) -> dict[str, set[int | None]]:
        """Prove required-gate emission from one current internal PR.

        Both pull_request and pull_request_target check suites are attached to
        the PR candidate head. The pull_request_target workflow definition is
        still resolved from protected main, and each run must remain bound to
        the same PR number. Manual/scheduled runs are never accepted.
        """
        branch = self.api(f"/repos/{repo}/branches/main") or {}
        main_sha = ((branch.get("commit") or {}).get("sha") or "").strip()
        if not main_sha:
            return {}

        def score(candidate: dict[str, set[int | None]]) -> int:
            return sum(candidate.get(context) == {expected_app_id} for context in expected)

        best: dict[str, set[int | None]] = {}
        pulls = self.api(
            f"/repos/{repo}/pulls?state=open&base=main&sort=updated&direction=desc&per_page=20"
        ) or []
        for pr in pulls:
            head = pr.get("head", {})
            base = pr.get("base", {})
            head_repo = (head.get("repo") or {}).get("full_name")
            pr_number = pr.get("number")
            if head_repo != repo or base.get("ref") != "main" or not isinstance(pr_number, int):
                continue
            sha = head.get("sha")
            if not sha:
                continue
            comparison = self.api(f"/repos/{repo}/compare/{main_sha}...{sha}") or {}
            merge_base = (comparison.get("merge_base_commit") or {}).get("sha")
            if comparison.get("status") not in {"ahead", "identical"} or merge_base != main_sha:
                continue

            head_runs = self.api(f"/repos/{repo}/commits/{sha}/check-runs?per_page=100") or {}
            pr_sources = self._protected_flow_sources(
                repo,
                head_runs,
                event="pull_request",
                allowed_head_shas={sha},
                workflow_ref=sha,
                pr_number=pr_number,
            )
            target_sources: dict[str, set[int | None]] = {}
            expected_repo_url = f"https://api.github.com/repos/{repo}"
            expected_repo_name = repo.rsplit("/", 1)[1]
            for check_run in head_runs.get("check_runs", []):
                if check_run.get("head_sha") != sha:
                    continue
                check_prs = check_run.get("pull_requests")
                if (
                    not isinstance(check_prs, list)
                    or len(check_prs) != 1
                    or not isinstance(check_prs[0], dict)
                    or check_prs[0].get("number") != pr_number
                ):
                    continue
                workflow = self._workflow_run(repo, check_run)
                if (
                    not workflow
                    or workflow.get("event") != "pull_request_target"
                    or workflow.get("head_sha") != sha
                ):
                    continue
                definition = self._workflow_definition(repo, workflow)
                if not definition or definition.get("state") != "active":
                    continue
                if not self._workflow_event_unfiltered(
                    repo, definition, "pull_request_target", ref=main_sha
                ):
                    continue
                run_prs = workflow.get("pull_requests")
                if not isinstance(run_prs, list) or len(run_prs) != 1:
                    continue
                run_pr = run_prs[0]
                if not isinstance(run_pr, dict) or run_pr.get("number") != pr_number:
                    continue
                run_base = run_pr.get("base")
                run_head = run_pr.get("head")
                if not isinstance(run_base, dict) or not isinstance(run_head, dict):
                    continue
                if (
                    run_base.get("ref") != "main"
                    or run_base.get("sha") != main_sha
                    or run_head.get("sha") != sha
                ):
                    continue
                repositories = (run_base.get("repo"), run_head.get("repo"))
                if any(
                    not isinstance(identity, dict)
                    or not isinstance(identity.get("id"), int)
                    or identity.get("id") <= 0
                    or identity.get("url") != expected_repo_url
                    or identity.get("name") != expected_repo_name
                    for identity in repositories
                ):
                    continue
                if repositories[0].get("id") != repositories[1].get("id"):
                    continue
                self._add_source(
                    target_sources,
                    check_run.get("name"),
                    (check_run.get("app") or {}).get("id"),
                )
            sources = merge_sources(pr_sources, target_sources)
            if expected_sources_satisfied(sources, expected, expected_app_id):
                return sources
            if score(sources) > score(best):
                best = sources
        return best


# core.main resolves Audit at runtime; preserve the CLI while using the fixed class.
core.Audit = Audit


def main() -> int:
    return core.main()


if __name__ == "__main__":
    raise SystemExit(main())
