# Chat-first Persistent Autonomy Design

**Status:** owner-approved design for `Oteryn/Oteryn#108`; implementation is not canonical until the applicable META and separately authorized provider changes merge to protected `main`.

**Delivery PR:** `Oteryn/Oteryn#110` (supersedes closed unmerged transport PR `#109` with the same original candidate lineage)

**Approved:** 2026-08-30

## Purpose

Define one organization-level continuation model that lets an Oteryn task survive foreground Chat turns, worker/session rotation, context pressure, command timeouts and external waiting without weakening bounded retries, review authority, protected integration or provider ownership.

The target operating principle is:

> **Chat-first, GitHub-native async, Work-by-exception.**

This design is deliberately thin. It does not replace the bounded autonomous execution lifecycle, Merge Queue integration semantics, repository-specific orchestration, or hard platform/tool limits.

## Live authority reconciliation

The following ownership split was verified from GitHub live state before this design was approved.

### META execution and anti-loop authority

- `Oteryn/Oteryn#69` / PR `#71` is the single surviving canonical bounded-autonomous-execution lineage.
- `#72` / PR `#73` is a reconciliation source only. Its stronger still-valid invariants belong in the `#69/#71` survivor rather than in a second canonical implementation.
- The bounded lifecycle owns `RUNNING`, `WAITING_EXTERNAL`, `BLOCKED`, `STALLED`, `READY`, `DONE`, candidate freeze, retry/no-progress budgets, no-op/retrigger prohibition, same-head re-evaluation, material progress/evidence generations and `LOOP_BREAKER_AUDIT`.
- This design must not copy those states or budgets into another lifecycle authority.

### Execution-policy convergence authority

- `Oteryn/Oteryn#104` / PR `#107` owns effort-aware execution-policy convergence, Remote Desktop exact-call binding and provider execution-policy drift detection.
- The owner-approved split for `#108` requires `#107` to remain scoped to `#104` and not become a second bounded-autonomous-execution authority.
- Any bounded-execution code or contract carried by `#107` must be reconciled with the canonical `#69/#71` lineage before protected-main admission. `#108` must not independently fork either branch.

### Merge/integration authority

- `Oteryn/Oteryn#102` / PR `#103` owns candidate-head versus integration-head semantics, review-fingerprint reuse/invalidation, Merge Queue rollout, `merge_group` qualification and protected-main integration-loop removal.
- `#108` may consume those semantics but must not create a second merge, review-fingerprint or branch-freshness authority.

### Provider authority

- Game adoption is tracked by `Oteryn/Oteryn-Game#148` and must follow the eventual canonical META execution contract.
- Platform adoption is tracked by `Oteryn/Oteryn-Platform#1266`; Platform already owns a mature Control Room, checkpoint, session-rotation and anti-stall model.
- Platform `#1009` owns schema-first governance refactoring. `#108` must not create a competing Platform schema or orchestration database.
- Atlas adoption is tracked by `Oteryn/Oteryn-Atlas#176` and must follow the eventual canonical META execution contract.
- META coordination, this design, and provider Issue/PR references do **not** confer product-repository write authority. Game, Platform and Atlas remain read-only from a META task until the owner explicitly authorizes writes to that exact provider repository for the current task. Provider adoption must fail closed before mutation when that authorization is absent.

## Problem statement

Several limits are currently easy to conflate even though they have different meanings:

1. a whole owner-visible task can last across multiple sessions;
2. one Chat/Work/Codex worker session can end or rotate;
3. one command/build/test can time out;
4. external CI/review/dependency observation must be bounded;
5. retries and no-progress loops must be bounded;
6. active model context can become unsafe or inefficient.

When one of these coordinates is incorrectly treated as the lifetime of the whole task, useful work stops prematurely. The opposite failure mode is equally dangerous: treating persistence as permission for unlimited retrying, polling, context growth or background-execution claims.

The organization therefore needs a continuation layer that is orthogonal to the bounded lifecycle.

## Goals

The design must ensure that:

- the owner-visible task does not terminate merely because one worker/session, tool call, local foreground budget or context window ends;
- bounded anti-loop semantics from `#69/#71` remain fully controlling;
- regular Chat is the normal supervising/execution surface when currently exposed tools are sufficient;
- deterministic heavy compute is preferentially delegated to GitHub Actions or repository-approved runners;
- Work/Codex is selected only when its unique persistent, cloud-browser, event-triggered or software-development capabilities materially justify shared agentic usage;
- durable GitHub/repository state is sufficient for a later worker to resume without reconstructing the full prior chat;
- automatic continuation is claimed only when a real configured mechanism exists;
- provider repositories can adopt the organization minimum without losing stronger local controls and only under explicit current-task write authorization for that provider.

## Non-goals

This design does not:

- change `#69/#71` retry counts, lifecycle states, candidate-freeze semantics or loop-breaker thresholds;
- change `#102/#103` Merge Queue, review-fingerprint or `merge_group` semantics;
- establish a universal Chat, Work or Codex wall-clock timeout;
- make Work mandatory for high-effort tasks;
- create a second Platform Control Room, checkpoint schema or schema-first governance project;
- grant or infer cross-repository provider write authority;
- authorize production, deployment, secret, credential, data or live-system mutation;
- claim that repository policy can override a hard product/tool limit.

## Core model: six independent coordinates

Every substantial task must reason about these coordinates separately.

### 1. Task lifetime

The task is the owner-visible objective governed by its Issue/task record and applicable repository policy.

By default, task lifetime has no arbitrary organization wall-clock expiration. A task terminates only when the canonical bounded lifecycle reaches a real terminal condition, such as:

- verified `DONE`;
- an owner/permission decision for which no safe autonomous path remains;
- a safety/policy approval requirement;
- terminal `STALLED` after the applicable bounded recovery paths are exhausted and no materially new authorized action exists.

A worker/session ending is not a task terminal state.

### 2. Worker/turn/session lifetime

A worker session is disposable execution capacity. It may finish a coherent phase, hit context pressure, lose an execution surface, rotate or be replaced.

Worker/session completion changes only the worker disposition, not the canonical task lifecycle unless a real bounded-lifecycle condition also changed.

The continuation layer uses worker disposition as an orthogonal attribute, not as a new set of task states:

- `continue_current` — useful authorized work remains and the current worker can safely continue;
- `release_waiting` — the task is `WAITING_EXTERNAL`, `BLOCKED`, `STALLED` or otherwise has no justified active mutating worker;
- `rotate_resumable` — a new worker/session should resume the same task from durable state and a real worker-launching/preserving automatic resume mechanism exists;
- `stop_reinvoke_required` — the current execution cannot continue automatically; durable state is complete and owner re-invocation is required;
- `terminal` — the canonical task lifecycle is terminal.

These values describe worker disposition only. They do not replace `RUNNING`, `WAITING_EXTERNAL`, `BLOCKED`, `STALLED`, `READY` or `DONE`.

### 3. Tool/command timeout

Each long-running command, build, test, network operation or log stream uses an applicable finite timeout when the execution plane supports one.

A command timeout is evidence. It is not automatically task failure or task completion.

The recovery order is:

1. record the first material timeout/failure;
2. inspect the cheapest relevant evidence;
3. isolate with a focused check when possible;
4. change the hypothesis/input/method only when justified;
5. offload genuinely heavy deterministic compute to GitHub Actions or an approved runner when appropriate;
6. continue the same task if useful work remains within the canonical retry/no-progress policy.

Blind replay remains forbidden by `#69/#71`.

### 4. External-wait budget

CI, review, dependency, merge-queue and observation waiting is bounded independently from the task lifetime.

When only external evidence can change the state:

- enter the canonical `WAITING_EXTERNAL` semantics;
- preserve the unchanged candidate;
- release the active mutating worker unless a repository-approved bounded terminal-wait exception applies;
- prefer event-driven/same-head control-plane re-evaluation over polling or Git mutation;
- resume only after a material fact changes or a takeover has a genuinely new authorized action.

### 5. Retry/no-progress budget

Retry and no-progress protection is wholly owned by the canonical bounded-execution policy. The continuation layer never resets or enlarges a consumed retry budget merely because:

- the worker rotated;
- the context was compacted;
- a new Chat turn began;
- the execution surface changed;
- a scheduled/event-triggered continuation fired.

Durable retry counters and generation scopes survive worker replacement.

### 6. Context budget / context pressure

Context pressure is a separate execution coordinate. Exact remaining tokens must not be invented when the runtime does not expose them.

The required response to growing context pressure is:

1. externalize large logs/evidence/artifacts;
2. reduce the active reasoning set to material facts and the next coherent phase;
3. persist a compact durable checkpoint;
4. continue in the same session if reasoning remains safe and efficient;
5. rotate the worker/session when continued reasoning becomes unsafe or inefficient;
6. resume from live GitHub + the compact checkpoint + only the referenced evidence needed for the next phase.

A long conversation is not by itself a reason to split the task into multiple tasks.

## Executor-selection model

Effort classification and execution-surface selection are independent decisions.

### Chat-first

Use regular Chat as the primary supervising/execution surface when the tools actually exposed in the current session can safely perform the work.

A task being `high` effort, multi-file or long-lived does not by itself justify Work/Codex.

Chat should continue useful authorized work in the current turn while the platform permits it and the bounded lifecycle still has real progress available. It must not voluntarily terminate the whole task merely because one local phase, command or soft foreground budget ended.

### GitHub-native async

Use GitHub Actions or repository-approved runners for deterministic work whose main cost is compute or waiting rather than reasoning, including:

- full builds;
- complete test suites;
- E2E matrices;
- static analysis;
- deterministic governance validation;
- merge-group qualification;
- other repository-owned exact-head checks.

The supervising worker consumes the resulting evidence; it does not stay active merely to watch compute.

### Work/Codex-by-exception

Escalate to Work/Codex only when a capability that is materially useful to the task is unavailable or materially inferior through Chat + repository-native execution, for example:

- persistent cloud/background execution is actually required;
- Work cloud browser is required;
- an event-triggered connected-app continuation is required;
- a Codex software-development workflow materially reduces implementation/test risk or cost;
- delegated persistent agent execution provides a real benefit that GitHub-native async plus Chat supervision cannot economically provide.

The decision must record the capability reason, not merely `high effort`.

## Resume mechanisms and truthfulness

A worker may claim automatic continuation only when a real mechanism is configured and observable.

The organization recognizes these continuation mechanism classes:

- `same_session` — the current worker continues immediately; it does not launch or preserve a replacement worker;
- `github_native` — GitHub Actions, Merge Queue or another repository-native event progresses the control plane without an active worker; it does not by itself launch a replacement agent worker;
- `scheduled_task` — an enabled ChatGPT scheduled/monitoring task will perform the configured later check/action and therefore can launch a later worker execution;
- `work_event_trigger` — an enabled Work event-triggered task will respond to a supported connected-app event and therefore can launch a later worker execution;
- `work_persistent` — an active Work cloud task or other supported persistent Work execution continues independently and preserves worker execution;
- `owner_reinvoke` — no automatic mechanism exists; a future owner invocation is required;
- `none_terminal` — the canonical task lifecycle is terminal.

Disposition/mechanism compatibility is fail-closed:

| Worker disposition | Allowed resume mechanism(s) | Meaning |
| --- | --- | --- |
| `continue_current` | `same_session` | The current worker continues now; no rotation is claimed. |
| `release_waiting` | `github_native`, `scheduled_task`, `work_event_trigger`, `work_persistent` | The active mutating worker is released while an external/control-plane or worker-capable mechanism remains active. `github_native` alone is valid only when repository-native progression can complete **all remaining task work through a canonical terminal state** without any later agent worker action. If any later worker action may be required, `github_native` alone is invalid; use a worker-launching/preserving mechanism or `stop_reinvoke_required`. |
| `rotate_resumable` | `scheduled_task`, `work_event_trigger`, `work_persistent` | A replacement/persistent worker execution is actually configured; a concrete locator is mandatory. |
| `stop_reinvoke_required` | `owner_reinvoke` | No automatic worker continuation exists; owner re-invocation is required and must be reported truthfully. |
| `terminal` | `none_terminal` | The canonical task lifecycle is terminal. |

`rotate_resumable` is invalid with `same_session` because no rotation occurs, and invalid with `github_native` because repository-native control-plane progress alone does not launch a replacement agent worker. It is also invalid with `owner_reinvoke` or `none_terminal`.

A checkpoint that records `rotate_resumable` must identify one of `scheduled_task`, `work_event_trigger` or `work_persistent` and include the concrete task/workflow/trigger locator required to re-establish it.

For `release_waiting`, every worker-capable automatic mechanism (`scheduled_task`, `work_event_trigger`, or `work_persistent`) likewise requires a non-empty concrete locator that identifies the configured continuation. `github_native` requires a concrete workflow/queue/control-plane locator plus **authoritative whole-task remaining-work proof before the checkpoint is accepted and before the worker releases** that no later agent worker action remains anywhere in the task. That proof must be re-evaluated against fresh trusted state at resumption; it cannot be deferred until after release.

Truthfulness has two different verification boundaries. **Before release/checkpoint**, an automatic continuation mechanism must be live and bound to the trusted task plus the checkpoint's current `next_action`. **At automatic resumption**, the control plane authenticates the actual trigger/completion event against that immutable historical mechanism, locator, task identity and historical action before reconciling its result to fresh GitHub/task state. A one-shot scheduled/Work/GitHub-native mechanism may legitimately be completed or consumed after firing and therefore need not remain live or bind to the freshly advanced action. **Manual `owner_reinvoke` is different:** no automatic trigger or locator exists, so the new invocation must instead be authenticated as an owner-authorized re-entry bound to the exact historical task/lineage/action. It must never fabricate automatic-event evidence. If a resumed worker claims another future automatic continuation, the successor checkpoint must freshly verify that new claim as live and bound to the successor action.

`release_waiting + github_native` is invalid whenever any later agent worker action remains in the task after the GitHub-native event. In that case the checkpoint must identify a worker-launching/preserving continuation mechanism instead, or use `stop_reinvoke_required` if none exists.

If no worker-launching/preserving automatic mechanism exists when replacement worker action will be required, use `stop_reinvoke_required`. Never imply that regular Chat or GitHub-native control-plane progress will silently create a new foreground worker turn after the current response ends.

## Immutable lineage identity versus mutable execution context

Continuation history MUST be keyed by an immutable lineage identity containing only repository, governing task/Issue identity and an opaque checkpoint-lineage token. Branch, PR identity, exact head SHA and `next_action` are **mutable execution coordinates** and MUST NOT be part of the predecessor/no-predecessor lookup key. A released task may legitimately resume after any of those mutable coordinates advance; the same immutable lineage key must still resolve the same durable predecessor, after which a separate transition authority reconciles historical coordinates to fresh control-plane state. Changing an immutable lineage-key field is a different lineage and fails closed rather than being treated as ordinary progress.

## Durable checkpoint semantic minimum

The organization defines a semantic minimum, not one universal provider file format.

Before worker release, external waiting, context rotation or any other continuation boundary, durable state must make the next safe action reconstructible from GitHub/repository state without replaying the whole chat.

The checkpoint semantics are:

- repository identity;
- governing Issue/task identity;
- PR identity when applicable;
- task branch;
- exact task-head SHA;
- current coherent phase;
- canonical bounded-lifecycle state;
- last material progress;
- completed material work relevant to continuation;
- current validation/evidence references;
- first material failure when applicable;
- rejected hypotheses when material;
- canonical retry/evidence-generation state when applicable;
- context-pressure classification when applicable;
- blockers;
- worker disposition;
- continuation mechanism class and concrete locator when applicable;
- exactly one concrete `next_action`.

The provider may store these semantics in an existing task/checkpoint/control-plane format. The organization contract must not force Platform to create a second checkpoint schema.

### Checkpoint storage

Checkpointing is a control-plane action, not a reason to mutate a frozen technical candidate.

When `candidate_frozen=true`:

- do not create empty/no-op/checkpoint/retrigger commits;
- use an authorized Issue/task/control-plane metadata surface for waiting/session state unless a tracked-file update is itself materially required by repository policy;
- preserve exact technical-head evidence.

## User-notification semantics

Owner-facing communication should be low-noise and truthful.

Do not interrupt solely because of:

- coherent phase completion;
- ordinary durable checkpoint creation;
- a recoverable command timeout;
- bounded retry progression;
- context compaction;
- worker/session rotation when a real automatic continuation path exists;
- ordinary lease renewal/release;
- unchanged external waiting already represented by an active automatic mechanism.

Notify the owner when:

- the task is verified `DONE`;
- a concrete owner decision or permission is required, including missing cross-repository write authorization before a provider mutation;
- a safety/protected/irreversible approval is required;
- terminal `STALLED` is reached after bounded recovery;
- execution is stopping and no real automatic continuation mechanism exists, so `owner_reinvoke` is required.

## Relationship to Merge Queue and review fingerprints

The continuation layer consumes `#102/#103` rather than duplicating it.

When Merge Queue is canonical for a repository:

- the active mutating worker may release while GitHub owns the merge-group integration attempt only when either no later agent worker action remains anywhere in the task, or a worker-launching/preserving continuation mechanism is separately configured and represented by the checkpoint; GitHub-native queue progression alone must not strand post-merge readback/closeout work;
- queue rebuilds after trusted-main movement are GitHub-native continuation, not a reason to mutate the PR branch;
- external review reuse/invalidation remains a review-fingerprint decision, not a continuation-layer decision;
- a changed risk-bearing fingerprint still requires the review behavior defined by the canonical review policy.

When Merge Queue is not yet canonical, the existing repository integration policy remains controlling until the staged `#102` rollout proves and enables the replacement.

## Provider adoption model

Provider adoption is a separate write-authority boundary. Protected META policy being canonical is necessary but never sufficient authorization to mutate a product repository. Before any provider write, the executing task must hold explicit owner authorization naming that provider repository for the current task. Provider Issues, PRs, dependency links, manifests or META coordination text are evidence/routing only and cannot confer that authority.

### META

META owns the organization continuation semantics and deterministic validator. The new contract references canonical bounded-execution and merge-integration authorities rather than copying them.

### Game

After canonical META dependencies are protected-main verified **and** the owner explicitly authorizes `Oteryn/Oteryn-Game` writes for the current adoption task, Game may adopt the organization continuation minimum by reference in its root/agent-governance surfaces. The adoption must remove stale claims that a worker/session stop automatically terminates the task and must preserve Game-specific review/merge/security rules.

Existing provider PRs that depend on the superseded `#72/#73` lineage must be reconciled rather than independently merged. Without current-task Game write authorization, only read-only preflight/reconciliation analysis is permitted.

### Platform

After canonical META dependencies are protected-main verified **and** the owner explicitly authorizes `Oteryn/Oteryn-Platform` writes for the current adoption task, Platform maps the organization minimum into its existing model. Without that authorization, only read-only preflight/reconciliation analysis is permitted.

Platform keeps its existing `EXECUTION_PROTOCOL.md`, `ANTI_STALL_AND_EXECUTION_BUDGET.md`, `PROJECT_LANES.json`, `GOVERNANCE_CONTRACT.json` and Control Room.

Organization semantics map as follows:

- organization task lifetime -> existing Platform task record lifetime;
- worker/session lifetime -> existing Platform session/rotation semantics;
- external waiting -> existing `waiting` task state / `WAITING` invocation result plus the canonical organization `WAITING_EXTERNAL` meaning;
- context pressure -> existing Platform context-pressure assessment and same-task rotation;
- checkpoint minimum -> existing Platform checkpoint fields plus additive continuation semantics where missing;
- provider foreground/runtime/command budgets -> remain local worker/invocation limits and must not become the lifetime of the whole organization task.

Broader schema-first restructuring remains owned by Platform `#1009`.

### Atlas

After canonical META dependencies are protected-main verified **and** the owner explicitly authorizes `Oteryn/Oteryn-Atlas` writes for the current adoption task, Atlas may adopt the organization continuation minimum through its provider-owned governance/test-execution surfaces. Without that authorization, only read-only preflight/reconciliation analysis is permitted. The adoption must not weaken Atlas exact-head, provenance, hosted-E2E or specialist-capability gates.

## Deterministic validation and drift strategy

The META implementation should provide a versioned machine policy and validator that can prove at least these invariants:

1. task lifetime is distinct from worker/session, command, wait, retry and context coordinates;
2. a worker/session timeout, command timeout or context rotation alone cannot produce task `DONE`;
3. worker disposition and resume mechanism obey the fail-closed compatibility matrix;
4. `rotate_resumable` is allowed only with `scheduled_task`, `work_event_trigger` or `work_persistent` plus a concrete locator; `same_session` and `github_native` cannot qualify it;
5. `release_waiting + github_native` is allowed only when no later agent worker action remains anywhere in the task after GitHub-native progression;
6. `release_waiting` paired with `scheduled_task`, `work_event_trigger`, or `work_persistent` requires a non-empty concrete locator; `github_native` also requires a concrete control-plane locator;
7. `owner_reinvoke` cannot be presented as automatic continuation;
8. continuation history is resolved only by the immutable repository/task/lineage key; mutable branch/PR/head/next-action advances never change predecessor selection, and continuation does not reset canonical retry/no-progress counters: a first continuation checkpoint with no continuation predecessor must still match the canonical bounded authority's current retry/evidence state, while every successor checkpoint write resolves the latest trusted predecessor and delegates retry/evidence continuity validation to that same authority;
9. frozen candidates cannot use checkpoint/retrigger commits as a continuation mechanism;
10. Work selection requires a capability reason rather than effort alone;
11. provider mapping may be stricter but cannot weaken organization task-lifetime truthfulness or bounded-execution safety;
12. provider write adoption cannot be inferred from META policy/Issue/PR references and must be separately authorized for the current task;
13. the continuation contract does not redefine bounded lifecycle states or Merge Queue/review-fingerprint semantics.

After provider adoption, organization live-state drift audit should check the protected-main provider contracts for stale incompatible wording and the expected META policy reference/version without attempting to parse arbitrary prose as the primary authority.

## OpenAI product capability basis

Product facts are time-sensitive and must be reverified before future policy changes depend on them.

Verified from official OpenAI documentation on 2026-08-30:

- Chat is described as the fast conversational assistance surface; Work is intended for longer, multi-step work and finished deliverables.
- Work follows the same usage structure as Codex; Codex, Work and other eligible agentic features can draw from the same agentic usage/credit pool when available on the user's plan.
- Work cloud-browser tasks can continue after the user leaves the conversation or closes the device, pausing when input, sign-in or confirmation is required.
- Eligible paid plans can schedule recurring tasks up to once per hour; monitoring tasks can check for changes and notify on relevant updates.
- Event-triggered tasks run in Work and can respond to supported GitHub pull-request activity in an authorized `github.com` repository for eligible plans/workspaces.

References:

- `https://help.openai.com/en/articles/20001275`
- `https://help.openai.com/en/articles/11369540/`
- `https://help.openai.com/en/articles/20001280-using-cloud-browser-in-chatgpt`
- `https://help.openai.com/en/articles/10291617`
- `https://help.openai.com/en/articles/11145903-connecting-github-to-chatgpt-deep-research`

No universal public wall-clock maximum such as `Chat = N minutes` or `Work = N hours` is part of this design.

## Rollout order

1. Persist the owner-approved authority split on the relevant META lifecycle threads.
2. Preserve `#69/#71` as the sole bounded-execution lineage and reconcile any overlapping bounded-execution material carried by `#107` without losing `#104`'s routing/RDC/provider-drift work.
3. Complete and protected-main verify canonical bounded-execution authority before provider continuation adoption treats those semantics as stable.
4. Implement the thin META continuation contract and deterministic tests without importing Merge Queue or provider-specific orchestration.
5. Reconcile `#102/#103` integration semantics by reference; do not make `#108` a merge authority.
6. For each provider independently, obtain explicit owner authorization naming that provider repository for the current adoption task; only then adopt the continuation minimum through the provider-owned branch/PR. Platform maps into its existing Control Room/checkpoint model.
7. Add provider/live-state drift validation after protected provider adoption exists.
8. Close `#108` only after protected-main META/provider readback proves the organization contract is consistently adopted or the Issue's final scope is explicitly reduced by owner decision.

## Acceptance criteria

This programme is complete when all of the following are true for the **final owner-approved scope**:

- `#69/#71` remains the sole bounded-autonomous-execution authority;
- `#107` does not establish a competing bounded lifecycle;
- `#102/#103` remains the sole merge-integration/review-fingerprint authority;
- META has one thin, versioned continuation contract covering task/session/tool/wait/retry/context separation and execution-surface/resume semantics;
- deterministic tests reject false automatic-resume claims, including `rotate_resumable` paired with `same_session` or `github_native`, `release_waiting + github_native` when later worker action remains, missing/empty locators for configured waiting continuations, and local-limit-as-task-limit behavior;
- for each provider that remains **IN_SCOPE**, Game/Atlas consume the META minimum without product/runtime changes and only under explicit current-task provider write authorization, while Platform maps the minimum into its existing Control Room/checkpoint system without a second orchestration schema and only under explicit current-task provider write authorization;
- for each provider explicitly **OUT_OF_SCOPE** by durable owner scope-reduction/defer decision, that decision is recorded exactly and no provider adoption or mutation is claimed as completed;
- every originally enumerated provider is therefore accounted for as either protected-main adopted while IN_SCOPE or explicitly deferred/excluded by owner decision;
- provider-specific foreground/command budgets remain worker/invocation limits rather than whole-task lifetime limits;
- Work/Codex is selected by capability need, not effort label alone;
- no-op/retrigger commits remain forbidden;
- user notification is limited to terminal completion, real decision/approval blockers (including missing provider write authority), terminal stall, or truthful re-invocation requirement;
- protected-main readback and applicable deterministic/provider gates confirm the final scoped state.