# Chat-first Persistent Autonomy Design

**Status:** owner-approved design for `Oteryn/Oteryn#108`; documentation only until merged to protected `main`.

**Operating principle:**

> **Chat-first, GitHub-native async, Work-by-exception.**

## Purpose

Define one small continuation layer that lets an owner-visible Oteryn task survive worker/session boundaries, command timeouts, external waiting and context pressure without creating another task lifecycle, another merge authority or another provider orchestration system.

The continuation layer answers only these questions:

- can the current worker continue safely;
- if not, is there a real mechanism that can resume the same task;
- what durable checkpoint is required to make that resume truthful;
- which execution surface is justified by current capability needs;
- when must the owner be told that automatic continuation is not real.

## Current authority and precedence

Always refresh protected `main` before implementation. Historical Issue, PR and SHA references are locators only.

The current protected-main `AGENTS.md` and ADR 0005 (`docs/architecture/adr/0005-solo-maintainer-governance-v2-simplification-reset.md`) take precedence over older design assumptions.

The authority split is deliberately small:

- `Oteryn/Oteryn#69` and its surviving protected-main implementation own bounded task lifecycle semantics such as `RUNNING`, `WAITING_EXTERNAL`, `BLOCKED`, `STALLED`, `READY`, `DONE`, bounded retries, material progress and candidate freeze. This design references that authority; it does not copy its budgets or state machine.
- `Oteryn/Oteryn#104` / PR `#107` owns effort-aware execution routing, Remote Desktop exact-call/exception controls and provider execution-policy convergence. It must not own a second bounded lifecycle.
- GitHub protected-branch enforcement, the repository aggregate gate and GitHub Merge Queue are the integration authority under ADR 0005. This design must not recreate review fingerprints, AI-review gates, attestation bridges, same-head review-recheck state machines or custom merge proof ledgers.
- `Oteryn/Oteryn#108` owns only persistent continuation semantics defined here.
- Game, Platform and Atlas retain provider implementation authority. META coordination never implies provider write permission.

External AI review is advisory under ADR 0005. It is not a continuation state or merge authority.

## Non-goals

This design does not:

- define a second task lifecycle or retry budget;
- recreate retired `LOOP_BREAKER_AUDIT`, review-fingerprint, R0/R1/R2, `ai-review-gate`, attestation, outbox or custom merge-proof machinery;
- change branch protection, required checks or Merge Queue settings;
- establish a universal Chat, Work or Codex wall-clock timeout;
- make Work/Codex mandatory for high-effort work;
- create a second Platform Control Room/checkpoint schema;
- grant cross-repository write authority;
- authorize production, deployment, secrets, credentials or live-data mutation.

## Six independent execution coordinates

Every substantial continuation decision treats these independently:

1. **task lifetime** — the owner-visible objective;
2. **worker/session lifetime** — one active agent execution;
3. **tool/command timeout** — one command, build, test or network operation;
4. **external wait** — CI, dependency, queue or other externally changing state;
5. **retry/no-progress** — bounded anti-loop state owned by the bounded lifecycle;
6. **context pressure** — whether the current session can still reason safely and economically.

A limit in one coordinate must not silently terminate another. In particular, worker/session end, tool timeout, context rotation and phase completion are not task completion.

## Worker dispositions

Continuation uses an orthogonal worker disposition, never a second task-state enum:

- `continue_current` — current worker can continue useful authorized work;
- `release_waiting` — no justified active mutating worker should remain while an external/control-plane mechanism progresses;
- `rotate_resumable` — another worker execution can really resume from durable state;
- `stop_reinvoke_required` — no automatic worker continuation exists; owner re-invocation is required;
- `terminal` — the bounded lifecycle is independently terminal.

## Resume mechanisms

The closed mechanism set is:

- `same_session`
- `github_native`
- `scheduled_task`
- `work_event_trigger`
- `work_persistent`
- `owner_reinvoke`
- `none_terminal`

Compatibility is fail-closed:

| Worker disposition | Allowed mechanism | Requirement |
| --- | --- | --- |
| `continue_current` | `same_session` | Current worker continues now. |
| `release_waiting` | `github_native` | Repository-native progression can complete **all remaining task work through terminal state** without any later agent-worker action. |
| `release_waiting` | `scheduled_task`, `work_event_trigger`, `work_persistent` | Mechanism is live, authorized, task-bound and has a concrete locator. |
| `rotate_resumable` | `scheduled_task`, `work_event_trigger`, `work_persistent` | A replacement/persistent worker execution is genuinely configured and has a concrete locator. |
| `stop_reinvoke_required` | `owner_reinvoke` | No automatic continuation exists. |
| `terminal` | `none_terminal` | Independent bounded lifecycle is terminal. |

`rotate_resumable` is invalid with `same_session` or `github_native`: neither creates/preserves a replacement agent worker.

`release_waiting + github_native` is intentionally strict. GitHub Actions or Merge Queue may advance repository state, but they do not by themselves create the next Chat worker. If any later agent reasoning/action might still be required, use a worker-capable mechanism or `stop_reinvoke_required`.

## Stable task lineage versus mutable execution context

Durable continuation history is keyed only by immutable lineage identity:

```text
repository
task_id
checkpoint_lineage_token
```

The following are mutable execution coordinates and must not be part of predecessor lookup identity:

```text
task_branch
pr_id
task_head_sha
next_action
```

A branch, PR, head or next action may legitimately change while the same owner-visible task continues. A separate trusted transition authority reconciles the historical checkpoint with fresh GitHub state.

Changing an immutable lineage field creates a different lineage and fails closed rather than being interpreted as progress.

## Durable checkpoint semantic minimum

The organization standard is semantic, not one universal file/database format. Providers may map it into an existing control-plane/checkpoint system.

A release/rotation checkpoint must make the next safe action reconstructible without replaying the whole chat. It contains at least:

- repository;
- task id and checkpoint lineage token;
- task branch;
- PR applicability and PR id when applicable;
- exact task-head SHA;
- coherent phase;
- bounded lifecycle state obtained from the bounded authority;
- last material progress and relevant completed work;
- validation/evidence references;
- bounded retry/evidence continuity reference without redefining its schema;
- blockers;
- context-pressure classification when relevant;
- worker disposition;
- resume mechanism;
- concrete mechanism locator when required;
- exactly one concrete `next_action`.

Checkpoint state belongs in an authorized durable task/control-plane surface. A checkpoint is never justification for an empty/no-op/retrigger commit.

## Checkpoint-write trust boundary

When writing a checkpoint:

1. obtain independently authenticated trusted task identity from the current control plane;
2. resolve the latest durable predecessor by the immutable lineage key;
3. if a predecessor exists, require the bounded authority to verify retry/evidence continuity rather than reimplementing its counters here;
4. if no continuation predecessor exists, require authoritative proof that none exists and verify that the first continuation checkpoint matches the already-consumed current bounded state;
5. require mutable coordinates in the proposed checkpoint to match current trusted task context;
6. require the disposition/mechanism pair to be valid;
7. for an automatic future worker mechanism, verify current liveness, authorization, task binding and locator before release;
8. for `release_waiting + github_native`, require authoritative proof that no later agent worker action remains anywhere in the task.

Unknown, unavailable or contradictory authority fails closed.

## Resume-read trust boundary

Historical checkpoints must not be rewritten to look current.

On resume:

1. resolve the latest historical checkpoint by immutable lineage key;
2. verify its durable integrity;
3. authenticate the real resumption event against the historical mechanism, locator, task and historical next action;
4. for `owner_reinvoke`, authenticate the owner-authorized re-entry instead of inventing automatic-event evidence;
5. fetch fresh GitHub/task state independently;
6. require a trusted transition authority to reconcile the historical mutable coordinates with the fresh task context;
7. require the bounded lifecycle authority to confirm current lifecycle and retry/evidence continuity;
8. only then choose the next worker disposition/action.

A consumed one-shot mechanism need not still be live after it has fired. If the new checkpoint claims another future automatic continuation, that new mechanism must be freshly verified.

## Execution-surface selection

Execution effort and execution surface are separate decisions.

### Chat

Default supervising/execution surface when currently available tools can perform the work safely. High effort alone never requires Work.

### GitHub-native

Prefer GitHub Actions or repository-approved runners for deterministic compute and waiting: builds, full tests, static analysis, E2E and merge-group qualification. The worker consumes evidence rather than staying active to watch compute.

### Work

Use only when a material capability requires it, such as supported cloud-browser use, event-triggered connected-app continuation or genuine persistent cloud execution.

### Codex

Use when a software-development repository loop materially improves implementation/testing compared with Chat plus GitHub-native execution.

If a required capability is unavailable or unauthorized and no safe alternative surface exists, fail closed as `BLOCKED_CAPABILITY_UNAVAILABLE`.

## Context pressure

Use **minimal active context + durable external state**.

When context pressure grows:

1. externalize large logs/evidence;
2. keep only material facts and the next coherent phase active;
3. write a durable checkpoint when crossing a continuation boundary;
4. continue in the same session if safe;
5. rotate only if a real resumable mechanism exists;
6. otherwise report `stop_reinvoke_required` truthfully.

Do not invent exact remaining token counts when the runtime does not expose them.

## User notification

Normally do not interrupt solely for a phase completion, ordinary checkpoint, recoverable command timeout, context compaction or a real automatic worker rotation.

Notify the owner when:

- the task is independently verified `DONE`;
- a concrete owner/permission/safety decision is required;
- bounded recovery reaches terminal `STALLED` with no materially new safe action;
- automatic continuation is unavailable and owner re-invocation is genuinely required.

Never imply background continuation when no mechanism exists.

## Provider adoption boundary

Game, Platform and Atlas are read-only from a META task unless the owner explicitly authorizes writes to the exact provider repository for the current adoption task.

Provider adoption must:

- preserve stronger provider-local safety/session controls;
- reference the organization continuation semantics without creating a competing bounded lifecycle;
- let Platform map the semantic minimum into its existing Control Room/checkpoint model;
- fail closed before mutation when exact provider authorization is absent.

Programme closeout may count a provider as intentionally excluded only through an explicit durable owner scope/defer decision. Missing authorization by itself is not an implicit defer.

## Acceptance criteria

The design is satisfied only when:

- the continuation machine policy references rather than duplicates bounded lifecycle authority;
- the six coordinates remain independent;
- stable lineage identity is separated from mutable branch/PR/head/action context;
- invalid disposition/mechanism combinations fail closed;
- automatic resume claims are verified both at release and at resumption;
- `github_native` cannot masquerade as a replacement agent worker;
- bounded retry/evidence state survives worker/session/context changes;
- execution-surface selection is capability-driven;
- CI deterministically executes the continuation regression suite;
- no retired ADR0005 review/proof/merge machinery is recreated;
- provider writes remain explicitly authorization-gated;
- final completion is based on live protected-main/provider evidence, not narrative.