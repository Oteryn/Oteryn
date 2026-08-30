# Agent Stall and Retry-Loop Prevention Design

## Status

Proposed organization-wide execution-governance hardening for Issue #72.

## Problem

Autonomous repository agents can spend unbounded time repeating unchanged integration, CI, external-review, or reconciliation actions when completion depends on asynchronous evidence. The failure mode is especially dangerous when the retry action itself mutates the task branch, because a no-op or checkpoint commit changes `task_head_sha`, invalidates exact-head evidence, and restarts the same qualification cycle.

The system must preserve fail-closed exact-head verification while making waiting, stagnation, and bounded retry first-class lifecycle states.

## Goals

1. Distinguish useful execution from passive waiting and true stagnation.
2. Freeze a stable candidate before expensive final qualification.
3. Prevent Git mutations whose only purpose is retriggering checks, reviews, polling, or checkpoint metadata.
4. Represent retry identity deterministically so unchanged failures cannot loop indefinitely.
5. Permit asynchronous evidence to re-evaluate the same exact head without creating a new commit.
6. Keep required checks, authenticated review evidence, exact-head binding, and protected-branch semantics fail-closed.
7. Provide deterministic regression tests for the lifecycle rules.
8. Define a provider-adoption contract for Game, Platform, and Atlas without centralizing provider-specific CI implementation.

## Non-goals

- Repairing or merging PR #62.
- Weakening or bypassing AI review, required CI, branch protection, or exact-head evidence.
- Creating a new organization-wide merge queue.
- Replacing repository-native task records or provider gates with a central mutable service.
- Adding periodic polling when an event-driven transition is available.

## Lifecycle model

Substantial autonomous tasks use the following normalized states:

- `RUNNING`: an active worker is making material progress.
- `READY`: implementation is coherent and may enter final qualification.
- `WAITING_EXTERNAL`: no worker should remain active; completion depends on CI, review evidence, dependency merge, quota, or another external event.
- `BLOCKED`: progress requires a missing permission, owner decision, safety authorization, or unresolved contradiction.
- `STALLED`: the same material failure/progress fingerprint has repeated beyond the allowed retry budget without new evidence.
- `DONE`: terminal completion is verified.

`WAITING_EXTERNAL` is not a failure. `STALLED` is not permission to bypass a gate; it is a durable diagnosis that stops unproductive mutation/retry.

## Candidate freeze

Before final qualification a task records:

- `candidate_frozen: true`
- `candidate_head_sha: <40-hex>`
- `candidate_frozen_at: <timestamp>`

While the candidate is frozen, a worker MUST NOT create a commit solely to:

- retrigger CI;
- retrigger external review;
- refresh a checkpoint;
- force a status recomputation;
- poll for an external event;
- advance a review generation without a material fix.

A frozen candidate may change only for a material reason: a verified finding, semantic conflict, required integration refresh, changed authority, or an implementation/test repair. Any such change unfreezes the prior candidate and establishes a new candidate generation after focused validation.

## Material progress fingerprint

A deterministic progress fingerprint represents the current execution state. It is computed from normalized fields that materially affect the next action, including:

- repository;
- PR number;
- `task_head_sha`;
- `integration_main_sha` when applicable;
- failing/required gate name;
- gate conclusion or waiting reason;
- first material error/finding code;
- unresolved material finding count;
- dependency identity and state when the dependency is the blocker.

Timestamps, run IDs, comment IDs, log ordering, narration text, and other incidental values are excluded.

If two consecutive execution cycles have the same progress fingerprint and the same attempted action, the second cycle consumes the final automatic retry budget for that action. A third identical cycle MUST transition to `WAITING_EXTERNAL` when the condition is externally pending, or `STALLED` when the system has no evidence that waiting alone can change the condition.

## Failure fingerprint and retry budget

A failure fingerprint is a stable subset of the progress fingerprint describing one failed action. Default automatic retry budget:

- deterministic transient transport/API failure: 2 attempts total;
- same exact CI/test failure without a code/config change: 1 retry after focused diagnosis;
- same external-review evidence absence for a frozen head: 0 mutating retries; transition directly to `WAITING_EXTERNAL` after the request is validly dispatched;
- same dependency-not-ready state: 0 active-worker retries; transition directly to `WAITING_EXTERNAL`;
- same merge-race/current-base requirement: 1 integration refresh per distinct `integration_main_sha`.

Repository-local policy may be stricter but may not permit unbounded retries.

## No-op mutation prohibition

A commit is invalid when its only purpose is changing Git identity to cause external systems to run again and it has no material repository-content or required integration effect. This includes empty commits and semantic no-op edits/checkpoint churn used as a trigger.

Durable execution state belongs in the task record/control-room state. Updating that state must not require changing the qualified product/governance candidate unless the task record itself is an explicitly risk-bearing deliverable.

## Event-driven same-head re-evaluation

Asynchronous evidence pipelines must support re-evaluating a stable candidate without changing `task_head_sha`.

For META AI review:

1. `pull_request_target` classification/check may initially report the exact head as waiting/failing closed because external evidence is absent.
2. The trusted request/evidence registry remains authoritative and candidate code remains inert.
3. When trusted review evidence for the exact requested head is recorded, a trusted default-branch workflow dispatches or invokes a same-head verification workflow.
4. The re-evaluation verifies that the PR is still open, the live PR head still equals the evidence-bound head, the trusted base identity is current for that PR event, and the evidence matches the required tier/fingerprint.
5. No candidate commit is created.

Any evidence for an older head remains superseded exactly as today.

## Deterministic execution guard

META owns a small pure-Python guard library/CLI that evaluates a JSON lifecycle snapshot and returns one of:

- `CONTINUE`
- `WAIT`
- `STALL`
- `BLOCK`
- `DONE`

The guard is intentionally independent of GitHub network access so its decision logic is unit-testable. Repository workflows or agent tooling can populate the snapshot from live GitHub state.

Minimum snapshot fields:

- schema version;
- task/repository/PR identity;
- task head;
- candidate freeze state;
- current action;
- waiting reason or failure code;
- previous progress fingerprint;
- repeated identical cycle count;
- retry count and retry limit;
- whether an external event can change the condition without a repository mutation;
- whether a material repository change occurred since the prior cycle.

## Provider adoption

META owns the normative lifecycle semantics and deterministic guard contract. Provider repositories adopt a thin bootstrap rule:

- no active worker remains attached to a `WAITING_EXTERNAL` task;
- no no-op/retrigger commit is permitted;
- final candidates are frozen before expensive qualification;
- unchanged failure/progress fingerprints obey bounded retry limits;
- provider-specific CI and merge gates remain provider-owned and fail-closed.

Platform's existing resilient execution protocol is treated as a compatible prior implementation and should be aligned, not replaced.

## Verification

Required deterministic tests include:

1. missing external review on a frozen head => `WAIT`, no mutating retry;
2. same failure fingerprint repeated past budget => `STALL`;
3. changed head or material fix resets the relevant retry generation;
4. dependency pending => `WAIT` immediately;
5. distinct integration-main SHA allows one new integration refresh;
6. no-op retrigger intent is rejected;
7. terminal verified state => `DONE`;
8. same-head external evidence re-evaluation verifies live head equality before accepting evidence;
9. stale evidence for an older head remains rejected.

## Rollout

1. Merge META design, contract, deterministic guard, workflow hardening, and tests.
2. Verify META same-head review-evidence re-evaluation on a dedicated test PR or deterministic fixture without weakening branch protection.
3. Add thin adoption text/tests to Game, Platform, and Atlas in separate provider PRs.
4. Close Issue #72 only after META is merged and provider adoption is either merged or explicitly tracked by linked provider issues with no claim of organization-wide completion.
