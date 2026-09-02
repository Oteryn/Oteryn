# Persistent Autonomous Continuation Policy

## Authority

This contract implements the persistent-continuation scope of `Oteryn/Oteryn#108`.

It is intentionally subordinate to the canonical bounded execution authority in `Oteryn/Oteryn#69` and its protected-main implementation. The continuation layer MUST NOT define a second bounded state machine, retry budget, progress fingerprint, candidate-freeze rule or terminality rule.

Under the current bounded contract:

- `WAITING_EXTERNAL`, `BLOCKED` and `STALLED` release active worker ownership but remain **nonterminal**;
- only the bounded authority determines terminality;
- currently only `DONE` is terminal;
- `READY` is not released merely because the next step happens outside the current worker.

ADR 0005 protected-branch enforcement, the existing aggregate required gate and GitHub Merge Queue remain integration authority. This contract MUST NOT recreate formal R0/R1/R2 merge authority, review fingerprints, `ai-review-gate`, attestation/outbox machinery, custom merge proofs or `LOOP_BREAKER_AUDIT`.

The machine-readable continuation policy is `ecosystem/agent-continuation-policy.json` and the deterministic validator is `tools/governance/agent_continuation_policy.py`.

## Independent execution coordinates

Continuation decisions keep these coordinates independent:

1. owner-visible task lifetime;
2. worker/session lifetime;
3. tool/command timeout;
4. external waiting;
5. retry/no-progress state owned by the bounded authority;
6. context pressure.

A worker ending, command timing out, external phase completing or context rotating is not task completion.

## Worker dispositions and resume mechanisms

Canonical worker dispositions are:

```text
continue_current
release_waiting
rotate_resumable
stop_reinvoke_required
terminal
```

Canonical resume mechanisms are:

```text
same_session
github_native
scheduled_task
work_event_trigger
work_persistent
owner_reinvoke
none_terminal
```

Every decision consumes current `BoundedLifecycleAuthority` facts:

| Disposition | Mechanism | Bounded requirement | Additional requirement |
| --- | --- | --- | --- |
| `continue_current` | `same_session` | nonreleased + nonterminal | current worker can continue safely |
| `release_waiting` | `github_native` | released + nonterminal | concrete GitHub control-plane locator plus `RemainingWorkAuthority` proof that all remaining work can reach terminal state without later agent-worker action |
| `release_waiting` | `scheduled_task`, `work_event_trigger`, `work_persistent` | released + nonterminal | concrete locator plus trusted proof that the mechanism is live/enabled, authorized, bound to the same stable lineage and bound to the current authoritative `next_action` before ownership is released |
| `rotate_resumable` | `scheduled_task`, `work_event_trigger`, `work_persistent` | nonreleased + nonterminal | same locator/task/action proof plus genuine replacement or persistent worker execution |
| `stop_reinvoke_required` | `owner_reinvoke` | released + nonterminal | no real automatic worker continuation exists |
| `terminal` | `none_terminal` | terminal | bounded authority independently reports terminal state |

Any other pairing fails closed. When the bounded authority is terminal, every nonterminal disposition fails closed. `STALLED` never becomes continuation `terminal` merely because an unchanged retry budget is exhausted.

## Stable lineage

Durable predecessor identity is exactly:

```text
repository
task_id
checkpoint_lineage_token
```

Branch, PR applicability/id, exact head and next action are mutable execution coordinates. They MUST NOT split a normal continuation into a new lineage.

## Checkpoint semantic minimum

Every continuation checkpoint uses the closed machine-validated semantic minimum:

- repository;
- task id;
- checkpoint lineage token;
- task branch;
- explicit PR applicability and PR id when applicable;
- lowercase exact 40-hex task head SHA;
- phase;
- bounded lifecycle state;
- last material progress;
- completed work;
- evidence references;
- opaque bounded continuity reference;
- blockers;
- context-pressure classification;
- worker disposition;
- resume mechanism;
- concrete locator for automatic mechanisms;
- exactly one concrete next action.

The continuation layer stores only a reference to bounded retry/evidence continuity; it does not copy or reset the bounded counters.

A checkpoint is control-plane evidence, not justification for an empty, no-op or retrigger commit.

## `checkpoint_write` trust boundary

Before persisting a new checkpoint:

1. resolve an independently trusted current `TrustedTaskIdentity`;
2. validate the proposed checkpoint against the closed semantic minimum;
3. require stable lineage equality with the trusted task;
4. require mutable branch/PR/head/next-action coordinates to match current trusted state;
5. require checkpoint lifecycle to match current `BoundedLifecycleAuthority` state;
6. resolve the latest predecessor using only the stable lineage key;
7. for the first continuation checkpoint, accept missing predecessor only when `CheckpointLineageAuthority` independently proves none exists and the bounded authority confirms the proposed checkpoint matches already-consumed current retry/evidence state;
8. for successor checkpoints, delegate retry/evidence continuity to the bounded authority;
9. enforce the bounded ownership/terminality predicate for the disposition;
10. verify required automatic resume locator/task/current-action evidence before releasing or rotating a worker;
11. for `release_waiting + github_native`, additionally require `RemainingWorkAuthority` proof that no later agent worker is required.

Unknown, unavailable or contradictory authority fails closed.

## `resume_read` trust boundary

A durable checkpoint is historical evidence. It MUST NOT be rewritten to look current.

Resume proceeds in this order:

1. resolve and authenticate the exact latest historical checkpoint for the stable lineage;
2. validate its historical semantic shape and disposition/mechanism against its historical bounded state;
3. authenticate the actual historical resume cause against the historical task/action:
   - automatic mechanisms authenticate the historical trigger/completion event and locator;
   - `owner_reinvoke` authenticates the current owner-authorized re-entry instead of fabricating an automatic event;
4. resolve fresh trusted GitHub/control-plane task state and fresh bounded lifecycle/ownership/terminality;
5. require `CheckpointTransitionAuthority` to prove every historical-to-fresh change in branch, PR applicability/id, head, next action, lifecycle and disposition semantics;
6. require the bounded authority to confirm retry/evidence continuity;
7. only after transition proof apply current bounded predicates to fresh state or a successor `checkpoint_write`.

A historical `WAITING_EXTERNAL + release_waiting` checkpoint may therefore reconcile to fresh `READY` or terminal `DONE` when the transition authority proves the advance. A consumed one-shot trigger need not remain live after authenticated firing; any successor checkpoint claiming future automatic continuation must freshly verify its new mechanism.

## Execution capability authority

Execution-surface selection uses a trusted current `ExecutionCapabilityAuthority`, not caller-supplied availability/authorization booleans.

The trusted capability snapshot must bind the required capability to supported compatible surfaces, current availability/authorization where applicable, current evidence references and whether all safe compatible fallbacks were actually evaluated.

Surface choices remain capability-driven:

- Chat for current Chat-safe work;
- GitHub-native execution for deterministic repository compute/waiting;
- Work only for a material Work-compatible capability such as event-triggered connected-app or persistent cloud execution;
- Codex for the software-development repository loop when current capability evidence supports it.

`BLOCKED_CAPABILITY_UNAVAILABLE` is valid only when trusted evidence proves the safe compatible fallback set is exhausted. Otherwise the decision fails closed as incomplete capability evaluation rather than inventing a blocker or unusable surface.

## Provider boundary

META continuation authority does not authorize product repository writes.

`Oteryn/Oteryn-Game`, `Oteryn/Oteryn-Platform` and `Oteryn/Oteryn-Atlas` remain read-only from a META task unless the owner explicitly authorizes the exact provider repository and current adoption task. Missing authorization is not an implicit defer.

A provider defer/exclusion counts toward final programme closeout only through the canonical GitHub-authoritative `OTERYN_PROVIDER_SCOPE_DECISION_V1` evidence defined by the protected-main #108 design, including exact provider/current-task binding, current owner/admin authority and supersession readback.

## Validation and integration

Changes to this continuation layer use strict RED → GREEN TDD and are executed by the existing required `meta-gate`. No second required status is introduced.

Completion requires exact-head tests/checks, full diff/review-thread inspection, normal protected-branch/Merge Queue integration and protected-main readback. External AI review remains advisory under ADR 0005 and is not merge authority.
