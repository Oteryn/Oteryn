#!/usr/bin/env python3
"""Fail-closed verifier for the bounded COST-CI assurance packet."""
from __future__ import annotations

import argparse
import json
import statistics
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = ROOT / "docs/evidence/organization-audit-20260907/cost-ci-candidate.json"

EXPECTED_BASELINE = {
    "repository": "Oteryn/Oteryn",
    "canonical_audit_pr": 185,
    "canonical_audit_head": "2d877271afa8f177983f3c6147472372adca0ed1",
    "worker_pr": 210,
    "worker_seed_head": "c6b26ebbe04b411658433d9c14bbc32f1a3f941f",
    "programme_pr": 203,
    "programme_head": "82bc113797ecdc70d79aee628d339136b816e15d",
    "dispatch_comment_id": 5668044695,
    "prior_assurance_pr": 206,
    "prior_assurance_frozen_head": "bc3c3339fe2ff39769872d843edf149bd56ff154",
}
EXPECTED_WORKFLOW = {
    "repository": "Oteryn/Oteryn",
    "name": "META CI",
    "workflow_id": 336924336,
    "path": ".github/workflows/ci.yml",
    "protected_main_commit": "d9419b05eb98c81279297563c11fc90e4fe708ac",
    "git_blob": "9a4e944d322b682a1cf61fa0110e69e69c8bb4ba",
    "runner_expression": "ubuntu-latest",
    "explicit_cache_action_present": False,
    "concurrency_group": "meta-ci-${{ github.event.pull_request.number || github.ref }}",
    "cancel_in_progress_pull_request_only": True,
}
EXPECTED_RUN_IDS = {
    "pull_request": [34865871915, 34860587490],
    "merge_group": [34832322263, 34831302624],
    "push": [34832368949, 34831352610],
}
EXPECTED_ROWS = {
    34865871915: ("pull_request", 203, "82bc113797ecdc70d79aee628d339136b816e15d", 104049450869, 2, 12, 16, 5),
    34860587490: ("pull_request", 185, "2d877271afa8f177983f3c6147472372adca0ed1", 104031444663, 3, 10, 22, 6),
    34832322263: ("merge_group", 202, "d9419b05eb98c81279297563c11fc90e4fe708ac", 103938251501, 2, 11, 15, 6),
    34831302624: ("merge_group", 201, "dcb71a131293128bf0a69959d78ae6390a0341fd", 103935028872, 2, 13, 16, 6),
    34832368949: ("push", 202, "d9419b05eb98c81279297563c11fc90e4fe708ac", 103938405941, 2, 12, 15, 5),
    34831352610: ("push", 201, "dcb71a131293128bf0a69959d78ae6390a0341fd", 103935182740, 2, 12, 15, 5),
}
EXPECTED_CLAIMS = {
    "cost_ci_closed": False,
    "cost_savings_claimed": False,
    "queue_health_claimed": False,
    "runner_capacity_claimed": False,
    "cache_efficiency_claimed": False,
    "flake_rate_claimed": False,
    "organization_audit_completion_claimed": False,
}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate(path: Path = CANDIDATE) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    require(data.get("schema_version") == 1 and data.get("obligation") == "COST-CI", "candidate identity")
    require(data.get("disposition") == "HANDOFF_COMPLETE_OBLIGATION_REMAINS_OPEN", "COST-CI must remain open")
    require(data.get("source_observation_cutoff") == "2026-09-14T17:37:30Z", "observation cutoff drift")
    require(data.get("baseline") == EXPECTED_BASELINE, "baseline provenance drift")
    require(data.get("workflow_source") == EXPECTED_WORKFLOW, "workflow source drift")

    sampling = data.get("sampling", {})
    require(sampling.get("event_classes") == ["pull_request", "merge_group", "push"], "event strata")
    require(sampling.get("per_event") == 2 and sampling.get("sample_count") == 6, "sample size")
    require("not filtered by conclusion" in sampling.get("method", ""), "selection must be conclusion-neutral")
    require("not a statistically representative long-term workload sample" in sampling.get("scope", ""), "scope limitation missing")

    runs = data.get("runs", [])
    require(len(runs) == 6, "six sampled runs required")
    actual_by_event: dict[str, list[int]] = {}
    for row in runs:
        run_id = row.get("run_id")
        event = row.get("event")
        actual_by_event.setdefault(event, []).append(run_id)
        require(run_id in EXPECTED_ROWS, "unexpected run id")
        require(row.get("workflow_id") == 336924336, "unexpected workflow id")
        require(row.get("job_name") == "meta-gate", "unexpected job")
        require(row.get("runner_label") == "ubuntu-latest", "runner label drift")
        require(row.get("run_attempt") == 1 and row.get("run_conclusion") == "success", "sample outcome/attempt drift")
        require(row.get("queue_seconds") == int((ts(row["job_started_at"]) - ts(row["job_created_at"])).total_seconds()), "queue timing mismatch")
        require(row.get("execution_seconds") == int((ts(row["job_completed_at"]) - ts(row["job_started_at"])).total_seconds()), "execution timing mismatch")
        require(row.get("run_wall_seconds") == int((ts(row["run_updated_at"]) - ts(row["run_created_at"])).total_seconds()), "run wall timing mismatch")
        expected = EXPECTED_ROWS[run_id]
        actual = (
            event, row.get("pr_number"), row.get("head_sha"), row.get("job_id"),
            row.get("queue_seconds"), row.get("execution_seconds"), row.get("run_wall_seconds"),
            row.get("verification_steps_success"),
        )
        require(actual == expected, f"sample provenance drift: {run_id}")
    require(actual_by_event == EXPECTED_RUN_IDS, "sample identities/order drift")

    queues = [r["queue_seconds"] for r in runs]
    executions = [r["execution_seconds"] for r in runs]
    walls = [r["run_wall_seconds"] for r in runs]
    expected_aggregates = {
        "successful_gate_runs": 6,
        "sampled_run_attempt_one": 6,
        "queue_seconds": {"min": min(queues), "median": statistics.median(queues), "max": max(queues)},
        "execution_seconds": {"min": min(executions), "median": statistics.median(executions), "max": max(executions)},
        "run_wall_seconds": {"min": min(walls), "median": statistics.median(walls), "max": max(walls)},
        "distinct_runner_ids": len({r["runner_id"] for r in runs}),
        "successful_named_verification_steps": sum(r["verification_steps_success"] for r in runs),
    }
    require(data.get("aggregates") == expected_aggregates, "aggregate drift")

    proven = data.get("proven", {})
    require("not fleet capacity" in proven.get("runner_allocation", ""), "capacity overclaim")
    require("does not expose cache hit/miss" in proven.get("workflow_cache_configuration", ""), "cache overclaim")
    require("not proof of defect-detection value or economic efficiency" in proven.get("verification_yield_proxy", ""), "yield overclaim")

    unknown = data.get("unknown_or_blocked", {})
    required_unknown = {"billing_cost", "runner_capacity", "cache_efficiency", "flake_rate", "retry_rate", "cost_savings", "useful_verification_yield"}
    require(set(unknown) == required_unknown, "unknown/blocked surface drift")
    for key in ("billing_cost", "runner_capacity", "cache_efficiency", "flake_rate", "cost_savings"):
        require(unknown[key].startswith("UNKNOWN:"), f"{key} must remain unknown")

    limits = " ".join(data.get("limitations", [])).lower()
    for phrase in (
        "not a statistically representative long-term workload sample",
        "not authoritative billing cost",
        "does not prove that no runner-level",
        "cost-ci remains open",
    ):
        require(phrase in limits, f"missing limitation: {phrase}")

    require(data.get("claims") == EXPECTED_CLAIMS, "closure/efficiency claims must remain false")
    additional = data.get("smallest_additional_observation", {})
    require("billable execution/usage" in additional.get("cohort_cost_cache", ""), "cost recheck input missing")
    require("unfiltered rolling cohort" in additional.get("generalized_efficiency", ""), "generalization recheck input missing")
    return {
        "result": "COST_CI_HANDOFF_VALID_OBLIGATION_OPEN",
        "sampled_runs": len(runs),
        "event_classes": len(EXPECTED_RUN_IDS),
        "successful_named_verification_steps": expected_aggregates["successful_named_verification_steps"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, default=CANDIDATE)
    args = parser.parse_args()
    print(json.dumps(validate(args.candidate), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
