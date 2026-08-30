# Chat-first Persistent Autonomous Execution — Decision Handoff

Status: planning handoff, not policy authority.

Governing lifecycle: `Oteryn/Oteryn#108`.

Related live authority/work: `Oteryn/Oteryn#69`, PR `#71`, `#72`, `#102`, plus provider adoption/issues that must be refreshed before any implementation.

Captured: 2026-08-30.

## Purpose

This document preserves the conclusions reached during an owner/agent review of why some Oteryn autonomous tasks continue for a long time while others stop after roughly 10–25 minutes, how Chat and Work differ operationally and economically, how context limits affect long-running work, and how durable checkpoints should allow a task to survive worker/session boundaries.

It is intentionally a **handoff**, not a canonical execution policy. It must not be used to bypass or silently supersede the current bounded-execution, merge-queue, review, provider or repository policies.

## Owner outcome

The desired user experience is:

- normal autonomous Oteryn work should use regular Chat whenever its currently exposed tools are sufficient;
- Work/Codex should not be mandatory merely because a task is large or high-effort;
- Work/Codex consume a shared agentic-usage/credit pool and therefore should be deliberate escalation paths when their unique capabilities provide material benefit;
- a worker completing one phase, reaching context pressure, checkpointing, rotating, hitting a tool/command timeout, or waiting on CI should not by itself terminate the whole task;
- the owner should normally be interrupted only for verified terminal completion or a genuine owner/safety/policy blocker that cannot progress autonomously;
- durable GitHub/repository state should make the current chat/session disposable.

The target operating principle is:

> **Chat-first, GitHub-native async, Work-by-exception.**

## Verified repository state at capture

At capture time:

- META protected `main`: `563503683b7df31fbb6a37799c9a786023e45544`;
- `ecosystem/agent-execution-routing-policy.json` schema v2 is canonical on META `main`;
- its `preflight_freshness.max_age_seconds` is `900`;
- the `900` seconds are a **GitHub preflight freshness bound**, not a task-runtime, worker-runtime or command-runtime limit;
- META #69 / PR #71 owns bounded autonomous execution / anti-loop semantics and PR #71 is still open;
- META #72 is related execution-stall lifecycle work and must be reconciled rather than ignored;
- META #102 owns merge-queue/review-fingerprint/anti-loop integration and must not be duplicated by this lifecycle;
- Platform already has mature local anti-stall/session controls, including `docs/agents/ANTI_STALL_AND_EXECUTION_BUDGET.md`, `docs/agents/EXECUTION_PROTOCOL.md`, `docs/agents/PROJECT_LANES.json`, `docs/agents/GOVERNANCE_CONTRACT.json` and Control Room tooling;
- Game and Atlas do not yet have an equivalent organization-wide execution-budget contract and their bounded-execution adoption depends on live META state.

Every continuation must refresh these facts. Historical SHA values in this document are provenance only.

## Current Platform budget facts

Platform `docs/agents/ANTI_STALL_AND_EXECUTION_BUDGET.md` currently defines, among other controls:

```yaml
normal_foreground_runtime_minutes: 60
large_foreground_runtime_minutes: 120
no_progress_minutes: 15
max_ci_state_checks_per_exact_head: 2
max_unchanged_external_state_checks: 2
terminal_ci_wait_budget_minutes: 45
terminal_ci_minimum_poll_interval_minutes: 3
max_terminal_ci_state_checks_per_check_generation: 12
max_identical_failure_retries_without_new_hypothesis: 1
max_repair_cycles_per_gate: 3
max_context_reconstruction_attempts: 1
normal_command_timeout_minutes: 20
heavy_command_timeout_minutes: 45
heavy_timeout_requires_reason: true
```

Important interpretation:

- these are **Platform foreground invocation / anti-stall / command budgets**;
- they do not prove that ChatGPT itself has a universal 15, 20, 25, 60 or 120 minute hard limit;
- a 20-minute command timeout plus preflight/analysis/closeout can plausibly produce a visible 20–25 minute foreground run, but this is not proof that every observed 20–25 minute stop has that cause;
- no canonical Oteryn rule was found that says the entire organization task must stop after 10 or 25 minutes;
- Platform's lease/checkpoint/stale timers are ownership/session-management mechanisms, not task-lifetime limits.

## OpenAI product facts verified at capture

These product facts were checked against official OpenAI documentation on 2026-08-30. They are time-sensitive and **must be reverified before becoming policy authority**.

1. Chat is described as the surface for fast conversational assistance and everyday questions.
2. Work is described as an agent for longer, multi-step work and finished deliverables.
3. Work and Codex use the same agentic usage/credit structure when available on the user's plan.
4. Agentic usage depends on model, execution placement, task complexity, context, reasoning, speed and tools; long-running tasks can consume substantially more than short requests.
5. Work cloud-browser tasks can continue after leaving the conversation or closing the computer and pause when input, sign-in or confirmation is required.
6. Scheduled Tasks are a ChatGPT feature. Supported scheduled tasks can use connected apps including GitHub, subject to account/workspace permissions and approvals.
7. Scheduled Tasks cannot run more frequently than once per hour under the currently documented limits and may pause if inactive or if additional action is required.
8. Event-triggered webhook tasks for supported GitHub PR activity are created in Work.
9. The public product documentation checked during this review does **not** publish a simple universal maximum such as `Chat = N minutes` or `Work = N hours`; such a value must not be invented.

References checked at capture:

- `https://help.openai.com/en/articles/20001275`
- `https://help.openai.com/en/articles/11369540/`
- `https://help.openai.com/en/articles/20001280-using-cloud-browser-in-chatgpt`
- `https://help.openai.com/en/articles/10291617`
- `https://help.openai.com/en/articles/11145903-connecting-github-to-chatgpt-deep-research`

## Core architectural conclusion

Oteryn must stop conflating different execution limits. At minimum, model these as independent coordinates:

1. **Task lifetime** — lifetime of the owner-visible objective/programme.
2. **Worker/turn/session lifetime** — lifetime of one active reasoning/execution session.
3. **Tool-call/command timeout** — maximum duration of one invocation, build, test, migration dry-run, log stream or network operation.
4. **External-wait budget** — how long/how often the agent may observe unchanged CI/review/dependency state in one active session.
5. **Retry/no-progress budget** — protection against repeating an unchanged failure/action chain.
6. **Context budget / context pressure** — usable active model context for the current session.

A limit in one coordinate must not silently become a terminal limit in another.

### Desired task-lifetime semantics

By default, an Oteryn task should not terminate merely because a wall-clock interval elapsed. It should terminate only when one of these is truthfully reached:

- verified `DONE`;
- a genuine owner decision/permission is required and no safe autonomous path remains;
- a genuine safety/policy blocker requires owner action;
- a terminal `STALLED`/equivalent condition is reached after the relevant bounded recovery paths are exhausted and no material new hypothesis/action remains.

### Worker/session semantics

A worker/session is disposable. Finishing a coherent phase or reaching a session/context/tool boundary should normally mean:

1. persist durable state;
2. release/rotate the worker when needed;
3. continue the same task from that durable state when an actual continuation path exists.

A worker/session timeout is not automatically a task timeout.

### Tool/command timeout semantics

A normal/heavy command timeout should normally trigger evidence-based recovery:

- inspect the failure/timeout;
- narrow/isolate with a cheaper focused check when possible;
- change the hypothesis/input/method when justified;
- offload genuinely heavy computation to GitHub Actions or the repository-approved runner when appropriate;
- continue the same task if useful authorized progress remains.

A tool timeout alone should not cause `TASK DONE`, and it should not be silently retried without new evidence.

## Chat-first execution

Regular Chat should be the default supervising/execution surface when the currently exposed tools can perform the work safely and completely enough.

`high` effort must **not** imply Work automatically. Effort classification and execution-surface selection are different decisions.

A Chat turn should continue useful authorized work while the platform permits and while doing so does not violate no-progress/retry/waiting policy. A repository-local soft foreground budget should not by itself force an otherwise-progressing Chat turn to end.

However, repository policy cannot create a new invisible foreground Chat turn after the current response has truly ended. If continued execution requires a later turn, there must be a real continuation mechanism such as a scheduled task, an event-triggered task where supported, a persistent Work/Codex session, repository-native automation, or a subsequent owner invocation.

Therefore, **silent rotation is permitted only when automatic continuation is real**. Otherwise the stop must be reported truthfully rather than allowing the task to die silently.

## Work/Codex-by-exception

Work/Codex should be selected when their unique capabilities materially justify their shared agentic usage, for example:

- persistent cloud/background execution is actually required;
- Work cloud browser is required;
- event-triggered connected-app continuation is required;
- a Codex development workflow materially reduces risk/cost compared with Chat plus repository-native execution;
- persistent/delegated agent execution provides a real benefit that Chat + GitHub automation cannot provide economically.

Do not route to Work/Codex merely because a task is labelled high-effort, contains many files, or may take a long wall-clock time.

## GitHub-native asynchronous execution

Heavy or slow deterministic work should preferentially run on GitHub Actions or repository-approved runners when that execution plane is appropriate.

Examples:

- builds;
- full test suites;
- E2E matrices;
- static analysis;
- deterministic governance validation;
- merge-group qualification.

The agent should reason about the result, not spend scarce agentic runtime merely waiting while the runner computes.

For final integration, Merge Queue/auto-merge/same-head control-plane re-evaluation should remove the need for a foreground worker to chase moving `main`, create no-op commits, or poll unchanged evidence. This must remain compatible with #102 and the canonical review-fingerprint semantics.

## Scheduled continuation

Scheduled Tasks can be considered as an economical periodic monitoring/resume mechanism where supported and where a one-hour minimum cadence is sufficient.

They are not equivalent to a persistent active worker and are not guaranteed to support every action. They remain subject to plan, account, app, approval, activity and permission constraints.

Event-triggered GitHub PR activity is currently a Work capability and therefore belongs in the deliberate escalation tier.

Do not claim scheduled continuation exists unless the task is actually configured and enabled.

## Context-limit conclusions

Context pressure is independent from elapsed wall-clock time.

A session can become context-heavy quickly because active context may include:

- conversation history;
- system/project/repository instructions;
- repository files;
- GitHub/API responses;
- CI logs and artifacts;
- tool outputs;
- review discussions;
- currently relevant evidence and hypotheses.

Do not claim an exact remaining-token count unless the runtime exposes one.

The correct strategy is **minimal active context + durable external state**, not attempting to keep the whole programme in one indefinitely growing chat.

### Context-pressure response

When context pressure grows:

1. externalize large logs/artifacts/evidence;
2. reduce active context to current task identity, material facts and next phase;
3. persist a compact durable checkpoint;
4. continue in the current session if safe;
5. rotate the session when context pressure makes continued reasoning unsafe or inefficient;
6. resume the same task from live GitHub state + checkpoint rather than replaying the full prior chat.

A context limit is not a valid generic blocker if the task can be safely checkpointed and resumed through a real continuation path.

## Durable checkpoint policy direction

A checkpoint is required after **material milestones**, not after every small tool call or file read.

Checkpoint after or before events such as:

- completion of a coherent `investigate`, `design`, `implement`, `validate`, `integrate` or `close` phase;
- a material implementation/fix milestone;
- a materially new validation result;
- before a heavy/long-running/failure-prone operation;
- before external waiting;
- before context/session rotation;
- before releasing worker ownership;
- after a material review finding or blocker changes state.

A useful checkpoint should preserve at least:

```yaml
repository: <owner/repo>
governing_issue: <number>
pull_request: <number or null>
branch: <task branch>
task_head_sha: <exact sha>
phase: <phase>
lifecycle_state: <state>
last_material_progress: <fact>
completed_material_work:
  - <fact>
validation:
  - <exact result/evidence reference>
first_material_failure: <failure or null>
rejected_hypotheses:
  - <when relevant>
retry_budget_state: <when relevant>
context_pressure: <when relevant>
blockers:
  - <real blocker or none>
next_action: <exactly one concrete action>
```

The exact schema must be designed against current META and provider contracts; the example above is a direction, not canonical structure.

### Checkpoint is not a no-op commit

Do not create an empty/no-op/checkpoint/retrigger commit merely to store waiting state or wake CI/review.

If the technical candidate is frozen, persist waiting/session state in an authorized Issue/task/control-plane metadata surface unless a tracked-file update is itself materially necessary and valid under the governing policy.

## User-notification direction

The desired owner-facing behavior is low-noise:

Normally **do not interrupt solely because of**:

- phase completion;
- ordinary checkpoint creation;
- session/worker rotation when an automatic continuation path actually exists;
- context compaction/rotation when continuation is real;
- a recoverable tool/command timeout;
- ordinary bounded retry progression;
- internal lease renewal/release.

Notify the owner for:

- verified `DONE`;
- `BLOCKED_OWNER` / equivalent owner decision or permission;
- `SAFETY_APPROVAL_REQUIRED` / equivalent protected or irreversible action requiring confirmation;
- terminal stalled state after bounded recovery is exhausted;
- a stop that cannot be automatically resumed and therefore requires owner re-invocation.

Do not claim or imply background continuation when no such continuation exists.

## Expected organization-level design work

The next design should decide how to encode, without duplicating existing authorities:

- task lifetime vs worker/session/tool/wait/retry/context budgets;
- Chat-first executor selection and Work/Codex escalation criteria;
- context-pressure compaction/rotation semantics;
- durable checkpoint schema and storage surfaces;
- silent vs user-visible stop/rotation semantics;
- resume mechanisms and truthful capability checks;
- GitHub Actions / Merge Queue / same-head re-evaluation integration;
- provider override rules (providers may tighten safety/validation but should not accidentally turn a local session budget into task termination);
- drift validation across META/Game/Platform/Atlas;
- migration of Platform's existing mature anti-stall controls without creating a second competing orchestration schema;
- adoption in Game and Atlas after META authority is canonical.

## Required reconciliation before implementation

Before modifying any canonical policy, the next coordinator must refresh and reconcile:

- META #69 and PR #71;
- META #72;
- META #102 and its current PR/rollout state;
- current META protected `main` and execution-routing policy;
- Game bounded-execution adoption state;
- Platform bounded-execution adoption state and the existing Control Room/schema-first work;
- Atlas bounded-execution adoption state;
- any newer policy/PR that now owns execution budgets, context rotation, checkpointing, scheduled continuation or merge queue.

Do not restart or duplicate already completed work.

## Evidence classification

### FACT

- Platform currently has explicit invocation/command/no-progress/CI-wait budgets.
- META current main at capture contains a 900-second preflight freshness bound.
- PR #71 is open at capture and proposes bounded autonomous execution semantics.
- Work/Codex currently share an agentic usage/credit structure according to official OpenAI documentation.
- Scheduled Tasks currently support connected apps including GitHub when available and have a documented minimum one-hour recurrence interval.
- Event-triggered GitHub PR tasks are currently created in Work.

### INFERENCE

- Some observed 20–25 minute Oteryn stops may be explained by Platform's 20-minute normal command timeout plus surrounding work, but a concrete run must be inspected before attributing causality.
- A Chat-first + GitHub-native-async architecture is likely more economical for this owner than making Work the mandatory supervisor for every long task.

### UNKNOWN

- A universal internal hard wall-clock maximum for a regular Chat turn. Public documentation checked during this review does not provide one.
- Exact usable Chat/Work context-window behavior for every product/model configuration unless the product/runtime explicitly exposes it.
- Whether a future product change will alter Scheduled Tasks, Work/Codex billing, event triggers or context behavior.

## Next action

Use the continuation prompt `docs/agents/prompts/OTERYN-CHAT-FIRST-AUTONOMY-CONTINUATION.md`, refresh all live authority, and produce a non-duplicative organization-level design before implementing any policy change.
