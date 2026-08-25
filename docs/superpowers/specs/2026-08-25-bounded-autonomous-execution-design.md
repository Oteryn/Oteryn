# Bounded Autonomous Execution Design

## Status and authority

- Design issue: `Oteryn/Oteryn#69`.
- Admission META head: `b34c94e17c0bcce11ae2caced70295930f27bb34`.
- Scope: permanent Oteryn repositories (`Oteryn/Oteryn`, `Oteryn/Oteryn-Game`, `Oteryn/Oteryn-Platform`, `Oteryn/Oteryn-Atlas`).
- This design governs agent execution/lifecycle only. It does not authorize product/runtime, deployment, production, secret, credential, database, game-state or destructive changes.

## Problem

Oteryn already has strong exact-head validation and a parallel-Git concurrency model, but autonomous workers can still waste time when the current task cannot make local progress. The failure class is broader than one pull request:

1. an asynchronous dependency (CI, external review, another task or provider) is not ready;
2. the worker is instructed to continue until verified completion;
3. no central state says that waiting is a successful terminal state for the current worker session;
4. the worker repeats the same check/action or changes the candidate merely to retrigger a gate;
5. exact-head evidence is invalidated or the same failure is rediscovered;
6. the session loops without material progress.

PR #62 is an incident reference only. The design must prevent the class without special-casing that PR.

## Goals

The organization must make autonomous execution bounded, progress-sensitive and fail-closed:

- explicit `RUNNING`, `WAITING_EXTERNAL`, `BLOCKED`, `STALLED`, `READY`, and `DONE` states;
- one stable candidate head during final qualification unless a material finding/reconciliation requires a real change;
- no no-op/checkpoint/retrigger commit may be used to refresh CI or review evidence;
- deterministic progress and failure fingerprints;
- bounded retry budgets for identical failures, heavy validation and external review invocation;
- no active worker session while the task is only waiting for an external event;
- asynchronous evidence must be able to re-evaluate the same candidate head where the control plane supports it;
- provider-specific CI/test authority remains provider-owned.

## Non-goals

- building a general distributed scheduler;
- centralizing provider CI in META;
- polling external systems indefinitely;
- changing GitHub branch protection or repository security settings;
- replacing existing task records/control rooms;
- weakening exact-head, review or fail-closed requirements.

## Architecture

### 1. Canonical bounded-execution policy

META owns a machine-readable policy at `ecosystem/bounded-autonomous-execution-policy.json` and a human normative contract at `docs/agents/contracts/BOUNDED_AUTONOMOUS_EXECUTION_POLICY.md`.

The machine-readable policy defines the state set, freeze rules, progress-fingerprint fields, retry budgets and allowed transition classes. Provider repositories may be stricter but may not weaken these minimums.

### 2. Deterministic execution guard

`tools/governance/bounded_execution_guard.py` is a pure deterministic helper. It consumes previous/current execution snapshots and returns an action verdict without network access.

A snapshot contains only lifecycle facts required for loop detection:

- `task_id` and `repository`;
- `state` and `phase`;
- exact `task_head_sha`;
- `candidate_frozen`;
- `blocking_dependency`;
- `gate_state`;
- `review_generation`;
- `first_material_failure`;
- retry counters.

The progress fingerprint is SHA-256 over the canonical JSON representation of the policy-selected progress fields. Chat/session text, timestamps and narration are deliberately excluded.

The guard enforces:

- frozen candidate + no material change => mutating/retrigger action denied;
- same progress/failure fingerprint may be retried only within the configured identical-failure budget;
- external dependency with unchanged task head becomes `WAITING_EXTERNAL`, not repeated active work;
- exhausted identical local failure budget becomes `STALLED`;
- `DONE` requires a verified completion flag supplied by the caller; the guard never infers completion from narrative.

### 3. Candidate freeze

A task enters candidate freeze when implementation is coherent and final qualification begins. While frozen:

- Git tree/head must remain unchanged unless a material review finding, failing test, semantic reconciliation, or changed governing authority requires an actual repair;
- no-op commits, metadata-only branch commits, empty commits and commits made only to retrigger CI/review are forbidden;
- task/session checkpoint state must be externalized to the repository task record/control room or other already-authorized durable metadata surface instead of changing the candidate merely to record waiting.

A legitimate repair unfreezes the candidate, records why, changes the head once for the repair, then freezes the new candidate before final qualification resumes.

### 4. Retry budgets

Organization defaults:

- identical unchanged failure cycles: `2`;
- full/heavy validation attempts in one coherent repair cycle: `2`;
- primary external-review invocations for one review fingerprint: `1`;
- automatic same-head AI-review gate rechecks for one result generation: `1`.

The budget is not a success probability mechanism. Exhaustion changes lifecycle state; it never authorizes bypassing a required gate.

### 5. Same-head asynchronous AI evidence recheck

META adds `.github/workflows/governance-ai-review-recheck.yml` plus `tools/governance/ai_review_recheck.py`.

The workflow listens only for external-review result events (`pull_request_review: submitted` and trusted reviewer-bot `issue_comment: created`). It does not check out or execute candidate code.

The helper:

1. reads the trusted default-branch AI review policy;
2. requires the event actor to be one of the configured trusted reviewer source logins;
3. resolves the PR and exact current PR head through GitHub API;
4. for pull-request-review events, requires the review commit to equal the current PR head;
5. locates the latest `governance-ai-review.yml` run for that exact head;
6. re-runs it only when it is completed/failed and still on run attempt `1`;
7. performs at most one automatic same-head re-evaluation for that evidence generation.

The re-run preserves the original trusted `pull_request_target` context. The evidence verifier remains authoritative; the recheck helper cannot manufacture PASS evidence.

### 6. Event and safety invariants

The recheck workflow receives `actions: write`, `contents: read`, `issues: read`, and `pull-requests: read` only. It does not receive `contents: write` and cannot mutate branches.

Untrusted comments/reviews, stale review commits, cross-repository PRs, malformed API responses, missing exact-head failed runs, already-retried runs, and already-green/in-progress runs result in a no-op or fail-closed error. They never change repository content.

### 7. Provider adoption

Provider rollout is deliberately thin and sequenced behind the canonical META merge:

- Game issue: `Oteryn/Oteryn-Game#148`;
- Platform issue: `Oteryn/Oteryn-Platform#1266`;
- Atlas issue: `Oteryn/Oteryn-Atlas#176`.

Game and Atlas adopt the state/freeze/no-progress minimum in bootstrap-visible agent instructions after current overlapping root-instruction work is terminal.

Platform already has `WAITING`, `STALE`, session rotation and heavy-validation budgeting in `docs/agents/EXECUTION_PROTOCOL.md`/Control Room. Its follow-up should extend those existing mechanisms with `candidate_frozen`, progress/failure fingerprints and retry-budget exhaustion rather than creating a second control room.

No provider branch is mutated concurrently with an already-active worker that owns the same root instruction surface.

## Lifecycle

Normal successful flow:

`RUNNING -> READY -> candidate freeze -> final deterministic qualification -> WAITING_EXTERNAL (when needed) -> same-head re-evaluation -> READY -> merge -> DONE`

Material repair flow:

`WAITING_EXTERNAL/READY -> material finding -> RUNNING (unfreeze with reason) -> repair -> new exact head -> candidate freeze -> qualification`

No-progress flow:

`RUNNING -> identical failure #1 -> focused repair/recheck -> identical failure #2 -> STALLED`

External wait flow:

`RUNNING/READY -> external dependency not ready -> WAITING_EXTERNAL -> end worker session`

`WAITING_EXTERNAL` is not `BLOCKED`: no owner decision is implied. `BLOCKED` is reserved for a missing permission, policy decision, unsafe/irreversible choice, contradictory authority, or dependency that cannot progress autonomously. `STALLED` means the permitted local retry budget was exhausted without a changed progress fingerprint.

## Testing

TDD is mandatory for both Python helpers.

Execution-guard tests must prove at minimum:

- progress fingerprint ignores timestamps/narration;
- changed material gate/head/failure state changes the fingerprint;
- frozen candidate denies no-op/retrigger mutation;
- external unchanged dependency yields `WAITING_EXTERNAL`;
- second identical local failure exhausts the default budget and yields `STALLED`;
- verified completion is required for `DONE`.

AI recheck tests must prove at minimum:

- untrusted actor cannot trigger a rerun;
- trusted result bound to the current exact head selects the failed attempt-1 run;
- stale review commit is rejected;
- successful/in-progress/already-retried runs are not rerun;
- cross-repository or malformed PR identity fails closed.

META CI runs both deterministic suites. The final PR still requires existing `meta-gate` and `ai-review-gate` on the exact final head.

## Completion criteria

META is complete only when:

- the normative and machine-readable policies agree;
- deterministic tests pass from a clean exact candidate tree;
- `meta-gate` and `ai-review-gate` pass on the exact final head;
- full diff/review state is inspected;
- the PR is squash-merged and protected `main` is verified.

Organization-wide rollout is complete only after Game, Platform and Atlas provider issues are independently merged and verified. A waiting provider is reported as waiting, not falsely counted as complete.