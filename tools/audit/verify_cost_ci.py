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
EXPECTED_RUNS = [
    {
        "event": "pull_request", "run_id": 34865871915, "workflow_id": 336924336, "pr_number": 203,
        "head_sha": "82bc113797ecdc70d79aee628d339136b816e15d", "head_branch": "docs/20260914-audit186-parallel-execution",
        "run_created_at": "2026-09-14T16:00:36Z", "run_updated_at": "2026-09-14T16:00:52Z", "run_attempt": 1, "run_conclusion": "success",
        "job_id": 104049450869, "job_name": "meta-gate", "job_created_at": "2026-09-14T16:00:37Z", "job_started_at": "2026-09-14T16:00:39Z", "job_completed_at": "2026-09-14T16:00:51Z",
        "runner_label": "ubuntu-latest", "runner_id": 1000080667, "verification_steps_success": 5,
        "created_to_start_delay_seconds": 2, "execution_seconds": 12, "run_wall_seconds": 16,
    },
    {
        "event": "pull_request", "run_id": 34860587490, "workflow_id": 336924336, "pr_number": 185,
        "head_sha": "2d877271afa8f177983f3c6147472372adca0ed1", "head_branch": "docs/20260907-org-comprehensive-audit",
        "run_created_at": "2026-09-14T15:12:03Z", "run_updated_at": "2026-09-14T15:12:25Z", "run_attempt": 1, "run_conclusion": "success",
        "job_id": 104031444663, "job_name": "meta-gate", "job_created_at": "2026-09-14T15:12:04Z", "job_started_at": "2026-09-14T15:12:07Z", "job_completed_at": "2026-09-14T15:12:17Z",
        "runner_label": "ubuntu-latest", "runner_id": 1000080596, "verification_steps_success": 6,
        "created_to_start_delay_seconds": 3, "execution_seconds": 10, "run_wall_seconds": 22,
    },
    {
        "event": "merge_group", "run_id": 34832322263, "workflow_id": 336924336, "pr_number": 202,
        "head_sha": "d9419b05eb98c81279297563c11fc90e4fe708ac", "head_branch": "gh-readonly-queue/main/pr-202-dcb71a131293128bf0a69959d78ae6390a0341fd",
        "run_created_at": "2026-09-14T10:16:08Z", "run_updated_at": "2026-09-14T10:16:23Z", "run_attempt": 1, "run_conclusion": "success",
        "job_id": 103938251501, "job_name": "meta-gate", "job_created_at": "2026-09-14T10:16:09Z", "job_started_at": "2026-09-14T10:16:11Z", "job_completed_at": "2026-09-14T10:16:22Z",
        "runner_label": "ubuntu-latest", "runner_id": 1000080178, "verification_steps_success": 6,
        "created_to_start_delay_seconds": 2, "execution_seconds": 11, "run_wall_seconds": 15,
    },
    {
        "event": "merge_group", "run_id": 34831302624, "workflow_id": 336924336, "pr_number": 201,
        "head_sha": "dcb71a131293128bf0a69959d78ae6390a0341fd", "head_branch": "gh-readonly-queue/main/pr-201-23b21e9b1b2d4b6c3a5cac3d4c7a18747804c090",
        "run_created_at": "2026-09-14T10:04:42Z", "run_updated_at": "2026-09-14T10:04:58Z", "run_attempt": 1, "run_conclusion": "success",
        "job_id": 103935028872, "job_name": "meta-gate", "job_created_at": "2026-09-14T10:04:43Z", "job_started_at": "2026-09-14T10:04:45Z", "job_completed_at": "2026-09-14T10:04:58Z",
        "runner_label": "ubuntu-latest", "runner_id": 1000080165, "verification_steps_success": 6,
        "created_to_start_delay_seconds": 2, "execution_seconds": 13, "run_wall_seconds": 16,
    },
    {
        "event": "push", "run_id": 34832368949, "workflow_id": 336924336, "pr_number": 202,
        "head_sha": "d9419b05eb98c81279297563c11fc90e4fe708ac", "head_branch": "main",
        "run_created_at": "2026-09-14T10:16:43Z", "run_updated_at": "2026-09-14T10:16:58Z", "run_attempt": 1, "run_conclusion": "success",
        "job_id": 103938405941, "job_name": "meta-gate", "job_created_at": "2026-09-14T10:16:43Z", "job_started_at": "2026-09-14T10:16:45Z", "job_completed_at": "2026-09-14T10:16:57Z",
        "runner_label": "ubuntu-latest", "runner_id": 1000080179, "verification_steps_success": 5,
        "created_to_start_delay_seconds": 2, "execution_seconds": 12, "run_wall_seconds": 15,
    },
    {
        "event": "push", "run_id": 34831352610, "workflow_id": 336924336, "pr_number": 201,
        "head_sha": "dcb71a131293128bf0a69959d78ae6390a0341fd", "head_branch": "main",
        "run_created_at": "2026-09-14T10:05:16Z", "run_updated_at": "2026-09-14T10:05:31Z", "run_attempt": 1, "run_conclusion": "success",
        "job_id": 103935182740, "job_name": "meta-gate", "job_created_at": "2026-09-14T10:05:16Z", "job_started_at": "2026-09-14T10:05:18Z", "job_completed_at": "2026-09-14T10:05:30Z",
        "runner_label": "ubuntu-latest", "runner_id": 1000080166, "verification_steps_success": 5,
        "created_to_start_delay_seconds": 2, "execution_seconds": 12, "run_wall_seconds": 15,
    },
]
EXPECTED_RUN_IDS = {
    "pull_request": [34865871915, 34860587490],
    "merge_group": [34832322263, 34831302624],
    "push": [34832368949, 34831352610],
}
EXPECTED_UNKNOWN = {
    "billing_cost": "UNKNOWN: collected run/job metadata does not include authoritative billed minutes, spend or marginal cost.",
    "runner_capacity": "UNKNOWN: short created-to-start delays and distinct runner IDs do not expose available fleet capacity, saturation or concurrency headroom.",
    "cache_efficiency": "UNKNOWN: no authoritative cache hit/miss, transferred-byte or cache-time telemetry was collected.",
    "flake_rate": "UNKNOWN: six recent successful runs are too small and too short a window to establish a long-term flake rate.",
    "retry_rate": "UNKNOWN beyond the sampled run IDs: each sampled run is attempt 1, but this cohort does not establish organization-wide retry frequency.",
    "cost_savings": "UNKNOWN: no baseline-vs-current billable usage or spend dataset is available.",
    "useful_verification_yield": "PARTIAL: named successful validation steps are observable, but prevented defects, redundant work and value per billed minute are not.",
    "pure_queue_time": "UNKNOWN: job created-to-start delay does not identify when the job became runnable or when a runner was assigned, so pure queue time is not measured.",
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
    require(runs == EXPECTED_RUNS, "sample raw provenance drift")
    actual_by_event: dict[str, list[int]] = {}
    for row in runs:
        run_id = row["run_id"]
        event = row["event"]
        actual_by_event.setdefault(event, []).append(run_id)
        require(row["created_to_start_delay_seconds"] == int((ts(row["job_started_at"]) - ts(row["job_created_at"])).total_seconds()), "created-to-start timing mismatch")
        require(row["execution_seconds"] == int((ts(row["job_completed_at"]) - ts(row["job_started_at"])).total_seconds()), "execution timing mismatch")
        require(row["run_wall_seconds"] == int((ts(row["run_updated_at"]) - ts(row["run_created_at"])).total_seconds()), "run wall timing mismatch")
    require(actual_by_event == EXPECTED_RUN_IDS, "sample identities/order drift")

    delays = [r["created_to_start_delay_seconds"] for r in runs]
    executions = [r["execution_seconds"] for r in runs]
    walls = [r["run_wall_seconds"] for r in runs]
    expected_aggregates = {
        "successful_gate_runs": 6,
        "sampled_run_attempt_one": 6,
        "created_to_start_delay_seconds": {"min": min(delays), "median": statistics.median(delays), "max": max(delays)},
        "execution_seconds": {"min": min(executions), "median": statistics.median(executions), "max": max(executions)},
        "run_wall_seconds": {"min": min(walls), "median": statistics.median(walls), "max": max(walls)},
        "distinct_runner_ids": len({r["runner_id"] for r in runs}),
        "successful_named_verification_steps": sum(r["verification_steps_success"] for r in runs),
    }
    require(data.get("aggregates") == expected_aggregates, "aggregate drift")

    proven = data.get("proven", {})
    require("observed_job_queue" not in proven, "created-to-start delay must not be labelled as queue time")
    delay_claim = proven.get("observed_created_to_start_delay", "")
    require("created-to-start delay" in delay_claim and "not pure queue time" in delay_claim, "created-to-start delay semantics drift")
    require("not fleet capacity" in proven.get("runner_allocation", ""), "capacity overclaim")
    require("does not expose cache hit/miss" in proven.get("workflow_cache_configuration", ""), "cache overclaim")
    require("not proof of defect-detection value or economic efficiency" in proven.get("verification_yield_proxy", ""), "yield overclaim")

    require(data.get("unknown_or_blocked") == EXPECTED_UNKNOWN, "unknown/blocked surface drift")

    limits = " ".join(data.get("limitations", [])).lower()
    for phrase in (
        "not a statistically representative long-term workload sample",
        "not authoritative billing cost",
        "not pure queue time",
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
