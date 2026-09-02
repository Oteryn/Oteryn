# OTERYN-CHAT-FIRST-AUTONOMY-CONTINUATION

## Alias

`OTERYN-CHAT-FIRST-AUTONOMY-CONTINUATION`

## Coordinator prompt

Continue `Oteryn/Oteryn#108` autonomously as the supervising coordinator.

### Source of truth

GitHub live state is authoritative for repository, Issue/PR, branch/head, checks, reviews, Merge Queue and protected-main facts.

Before every material mutation or integration decision, refresh at least:

- current protected `main` and `AGENTS.md`;
- ADR 0005 and any newer superseding governance authority;
- `#108` and its current delivery/implementation PRs;
- bounded execution authority from `#69` and its surviving protected-main implementation;
- `#104/#107` routing/RDC/provider-convergence state;
- current provider adoption state where relevant.

Historical SHAs and statuses in handoffs/docs are locators only.

### Precedence

Follow current protected-main `AGENTS.md` and ADR 0005.

Do **not** recreate retired governance machinery such as formal R0/R1/R2 merge states, review fingerprints, `ai-review-gate`, attestation bridges, durable dispatch/outbox systems, custom merge-proof ledgers or `LOOP_BREAKER_AUDIT` unless a newer protected-main authority explicitly reintroduces one.

GitHub protected-branch enforcement, the repository aggregate gate and GitHub Merge Queue own integration freshness/enforcement.

Under the current bounded contract, `WAITING_EXTERNAL`, `BLOCKED` and `STALLED` release worker ownership but remain nonterminal. Only the bounded authority determines terminality, and currently only `DONE` is terminal.

### Objective

Implement the smallest organization continuation layer that preserves one owner-visible task across worker/session/tool/wait/context boundaries without weakening the existing bounded lifecycle.

Operating principle:

> **Chat-first, GitHub-native async, Work-by-exception.**

### Six independent coordinates

Keep these separate:

1. task lifetime;
2. worker/session lifetime;
3. tool/command timeout;
4. external waiting;
5. retry/no-progress state;
6. context pressure.

A worker/session ending, command timeout, context rotation or phase completion is not task completion.

Retry/no-progress state remains owned by the bounded lifecycle and must never reset merely because a worker/session/surface changes.

### Worker disposition and resume truthfulness

Use only:

```text
continue_current
release_waiting
rotate_resumable
stop_reinvoke_required
terminal
```

Resume mechanisms are:

```text
same_session
github_native
scheduled_task
work_event_trigger
work_persistent
owner_reinvoke
none_terminal
```

Fail closed on invalid pairs.

The continuation layer must consume `BoundedLifecycleAuthority` ownership-release and terminality facts rather than infer them from its own disposition/mechanism pair:

- `continue_current + same_session` requires authoritative **nonreleased + nonterminal** bounded state;
- `release_waiting` with `github_native`, `scheduled_task`, `work_event_trigger` or `work_persistent` requires authoritative **released + nonterminal** bounded state, in addition to the mechanism-specific proof below;
- `rotate_resumable` requires authoritative **nonreleased + nonterminal** bounded state plus a genuine replacement/persistent worker mechanism;
- `stop_reinvoke_required + owner_reinvoke` requires authoritative **released + nonterminal** bounded state;
- `terminal + none_terminal` requires authoritative bounded terminality.

When the bounded authority reports terminal state — currently `DONE` — reject every nonterminal disposition. `READY` is not released merely because the next step is external; require a real bounded transition/classification to a released nonterminal state before persisting `release_waiting`.

For `release_waiting + scheduled_task|work_event_trigger|work_persistent`, require a concrete non-empty locator and trusted `ResumeMechanismVerifier` evidence **before releasing ownership** that the mechanism is live/enabled, authorized, bound to the same stable task lineage, and bound to the current authoritative `next_action`. Missing, stale, disabled, paused, inaccessible, cross-task or action-mismatched proof fails closed rather than releasing the worker.

`rotate_resumable` is valid only with `scheduled_task`, `work_event_trigger` or `work_persistent` plus a concrete verified locator that satisfies the same live/authorized/task/action binding and genuinely launches or preserves replacement worker execution.

`github_native` does not create a replacement Chat worker. `release_waiting + github_native` requires a concrete GitHub control-plane locator and is valid only when an authoritative `RemainingWorkAuthority` check proves that all remaining work through terminal state can complete without later agent-worker action.

If another worker will be needed and no worker-launching/preserving automatic mechanism exists, use `stop_reinvoke_required`; do not imply background continuation.

`STALLED` is released bounded-retry exhaustion, not terminal completion. Never map `STALLED` to the continuation `terminal` disposition unless a newer bounded authority explicitly changes canonical terminality.

### Stable lineage and resume reconciliation

Durable predecessor lookup must use only immutable lineage identity:

```text
repository
task_id
checkpoint_lineage_token
```

Branch, PR, exact head and next action are mutable execution coordinates. Do not use them to split normal continuation into a new lineage.

For `checkpoint_write`, current snapshot lifecycle/disposition and mutable coordinates must match the current trusted task context and current `BoundedLifecycleAuthority` before persistence/release.

For `resume_read`, keep the durable checkpoint immutable and treat its branch/PR/head/action/lifecycle/disposition as authenticated **historical evidence**, not as values that must already equal fresh state. Follow this order:

1. authenticate the historical checkpoint/digest and validate its closed semantic-minimum shape without rewriting it to look current;
2. authenticate the actual historical resume cause against the historical task/action: automatic mechanisms verify the historical trigger/completion event and locator binding; `owner_reinvoke` instead verifies the current owner-authorized re-entry bound to the exact historical lineage/action;
3. resolve a fresh trusted GitHub/control-plane task context and fresh current bounded lifecycle/ownership/terminality;
4. require `CheckpointTransitionAuthority` to prove every legitimate historical-to-fresh change in branch, PR applicability/ID, head, next action, lifecycle and disposition semantics before using the fresh state;
5. only after that transition proof apply the current `BoundedLifecycleAuthority` disposition predicates to the **fresh** state or any successor `checkpoint_write`.

A historical `WAITING_EXTERNAL + release_waiting` checkpoint may therefore reconcile to fresh `READY` or terminal `DONE` when the trusted transition authority proves the advance; never reject that solely because historical lifecycle differs from fresh lifecycle, and never rewrite authenticated history to manufacture equality. A consumed one-shot trigger need not remain live after it has been authenticated as the cause of the resume; fresh liveness is required again only if a successor checkpoint claims future automatic continuation.

### Checkpoints

Checkpoint after material milestones or before release/wait/rotation, not after every tool call.

A checkpoint must make one concrete next safe action reconstructible from durable state. It must include the semantic minimum from the canonical #108 design, reference current bounded lifecycle/retry evidence and must not create a competing bounded counter schema.

Checkpoint state is not justification for an empty/no-op/retrigger commit.

### Execution surface

- Prefer Chat when current tools safely cover the task.
- Prefer GitHub Actions/approved runners for deterministic compute and waiting.
- Use Work only for a material Work-only capability.
- Use Codex when its repository development loop materially improves safety/cost.
- High effort alone never requires Work/Codex.

Do not select a surface or report a capability blocker from stale handoffs or caller-supplied booleans. Resolve a trusted current-session capability snapshot from actual exposed tools/connectors, supported operation schemas, observable repository authentication/permission, surface compatibility/availability/authorization and safe fallback discovery.

If no safe authorized compatible surface exists for a required capability, fail closed as `BLOCKED_CAPABILITY_UNAVAILABLE` **only after** trusted current evidence proves the safe fallback set exhausted.

Remote Desktop/Desktop Commander remains subject to the exact current protected-main exception policy. Availability is not authorization.

### Parallelism

Use the smallest useful number of lanes.

- one writer per branch/lane;
- never allow overlapping writers on shared policy/workflow/schema;
- parallelize independent provider repositories or read-only review when beneficial;
- refresh live heads before integrating any lane.

### Provider authority

META authority does not grant Game/Platform/Atlas writes.

Before mutating a provider repository, require explicit owner authorization naming that exact repository and the current adoption task. Without it, perform only read-only preflight and record the permission blocker.

Final programme closeout requires every provider either protected-main adopted or covered by a currently verified GitHub-authoritative scope-decision record. A defer/exclusion counts only when canonical `#108` (or an explicitly named successor Issue) contains an `OTERYN_PROVIDER_SCOPE_DECISION_V1` comment naming the exact provider repository, exact current adoption task, `DEFER|EXCLUDE`, non-empty reason, META main SHA and provider main SHA. Re-read the exact comment at closeout, verify the author currently has sufficient repository-admin/owner authority, confirm provider/task binding and reject a record superseded by a later owner decision. Missing write authorization, generic handoffs or unknown permission are not implicit defer.

### Validation discipline

For code/policy changes use strict TDD:

1. write the focused failing regression;
2. prove hosted/authorized RED;
3. implement the smallest fix;
4. prove focused GREEN;
5. run the full applicable regression suite;
6. inspect exact final diff and required exact-head checks;
7. inspect all review threads/comments;
8. integrate only through current protected-branch/Merge Queue rules;
9. read back protected main before claiming completion.

Ensure CI itself is contract-tested so a regression test cannot silently exist without being executed by the required aggregate gate.

External AI review is advisory under ADR 0005. Use it only when current repository guidance says its value justifies the cost; never recreate it as merge authority.

### Owner communication

Do not interrupt for ordinary progress, checkpoints, recoverable failures or real automatic rotation.

Notify only for:

- verified terminal completion;
- a concrete owner/permission/safety decision;
- bounded recovery reaching `STALLED` when no verified automatic mechanism can wait for a material progress-fingerprint change and resume; `STALLED` remains nonterminal;
- truthful owner re-invocation requirement because no automatic continuation exists;
- an unavoidable tool capability gap that blocks the required protected integration operation after all safe alternatives are exhausted.

### Dependency order

Continue the live critical path rather than restarting design:

1. bounded execution survivor canonical on protected main;
2. reconcile `#107` to routing/RDC/provider convergence only;
3. terminalize the design packet;
4. create a **fresh branch from then-current protected main** for canonical `#108` implementation;
5. implement the thin continuation policy + contract + CI/tests;
6. provider adoption only where separately authorized;
7. protected-main/provider readback and terminal closeout.

Do not stop at preparation, a PR, a canary or a green branch when a safe authorized next step remains.