# Bounded Autonomous Execution and No-Progress Policy

Status: active contract when merged to protected `main`.

## Purpose

Autonomous execution must distinguish productive work from passive external waiting and repeated no-progress cycles. This contract prevents agents from keeping expensive workers alive, manufacturing no-op commits, or retrying the same failure indefinitely when no material state has changed.

## Lifecycle states

Substantial autonomous tasks use these normalized states when applicable:

- `RUNNING`: an active worker is making material progress;
- `READY`: the coherent implementation may enter final qualification;
- `WAITING_EXTERNAL`: no active worker should remain attached because CI, authenticated review evidence, another dependency, quota or another external event must change before useful execution can continue;
- `BLOCKED`: progress requires a missing permission, owner decision, safety authorization or contradictory authority resolution;
- `STALLED`: the same material state exceeded its bounded retry budget without new evidence;
- `DONE`: terminal completion is verified.

`WAITING_EXTERNAL` is a valid autonomous outcome and is not a false stop. When no authorized repository mutation can improve the current state, the worker MUST persist the waiting reason and next event, release ownership/lease where the repository uses one, and end or release the active session rather than poll, narrate, or mutate merely to provoke another check.

`WAITING_EXTERNAL` and `STALLED` never satisfy merge readiness or completion.

## Candidate freeze

Before expensive final qualification, an agent SHOULD record `candidate_frozen: true` and the exact `candidate_head_sha`. While `candidate_frozen` is true, the branch MUST NOT be changed solely to retrigger CI, external review, status calculation, polling or checkpoint publication.

A candidate may change only for a material reason such as a verified finding, semantic conflict, required integration refresh, changed authority, or an implementation/test repair. The resulting new head starts a new qualification generation and invalidates only evidence that is head-bound or otherwise materially affected.

## Material progress and failure identity

For repeated execution cycles, agents and repository tooling SHOULD compute or record a stable `progress_fingerprint` from material state: repository/PR identity, `task_head_sha`, `integration_main_sha` when applicable, current action, required/failing gate, waiting reason, first material error/finding and dependency state. Incidental values such as timestamps, run IDs, comment IDs, narration and log ordering MUST NOT manufacture progress.

A `failure_fingerprint` identifies the current failed action using the same stable material coordinates. If the same `progress_fingerprint` and action recur without material repository/evidence change, retries are bounded.

The organization defaults are:

- external evidence absent for a frozen candidate: zero mutating retries after a valid request is dispatched; transition to `WAITING_EXTERNAL`;
- dependency not ready: zero active-worker retries; transition to `WAITING_EXTERNAL`;
- identical CI/test failure: one retry only after focused diagnosis; a further identical cycle becomes `STALLED` unless new evidence changes the fingerprint;
- transient transport/API failure: at most two attempts total before durable waiting/blocker classification;
- integration refresh: at most one refresh per distinct `integration_main_sha`.

Repository-local rules may be stricter but MUST NOT authorize unbounded retries.

## No-op and retrigger mutation prohibition

A no-op/retrigger commit is forbidden. Agents MUST NOT create an empty commit, semantic no-op edit, checkpoint-only churn, or unrelated documentation mutation whose only purpose is to change Git identity so CI, review, mergeability or another external system runs again.

Qualification must be re-evaluated on the same exact head when the external evidence system supports it. If same-head re-evaluation is unavailable, classify the precise limitation as `WAITING_EXTERNAL` or `BLOCKED`; do not manufacture a new candidate.

Durable execution/checkpoint state SHOULD live outside the qualified candidate diff when the repository provides a task record/control-room mechanism. Updating agent bookkeeping does not justify invalidating otherwise-current exact-head evidence.

## Durable checkpoint contract

The machine-readable durable checkpoint contract is `docs/agents/EXECUTION_STATE_CONTRACT.json`. In repositories that persist task/checkpoint records, every new or materially updated substantial task record after this policy is active MUST emit the bounded execution fields defined there. Legacy records remain readable until they are materially updated.

Repository-local schemas may add stricter fields or transitions but MUST NOT weaken the central `RUNNING`/`WAITING_EXTERNAL`/`STALLED`, candidate-freeze, retry-exhaustion or no-op prohibition invariants.

## Interaction with other execution policy

This contract complements, and does not replace, `AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md`, `ecosystem/agent-execution-routing-policy.json`, repository protection, exact-head checks, independent review requirements, safety boundaries, or the non-destructive moving-main reconciliation rules.

A worker that reaches `WAITING_EXTERNAL` must not misreport the task as `DONE`; a worker that reaches `STALLED` must report the stable failure identity and the smallest new evidence or decision capable of changing material state.