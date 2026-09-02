# Chat-first Persistent Autonomous Execution — Decision Handoff

Status: provenance and continuation handoff only; not policy authority.

Governing continuation task: `Oteryn/Oteryn#108`.

## Owner decision

The target operating principle is:

> **Chat-first, GitHub-native async, Work-by-exception.**

The objective is not to make one foreground agent run forever. The objective is to let one owner-visible task survive worker/session/tool/context boundaries truthfully and safely.

## Current precedence

Every continuation must refresh GitHub live state. Historical SHAs, PR states and product facts in earlier discussions are provenance only.

Protected-main `AGENTS.md` and ADR 0005 now supersede older assumptions that depended on formal R0/R1/R2 review classes, review fingerprints, `ai-review-gate`, attestation/outbox machinery, custom merge-proof ledgers or a second same-head review lifecycle. Do not reintroduce those mechanisms through this programme.

Current authority boundaries are:

- `#69` and its surviving protected-main implementation: minimum bounded task lifecycle, material progress, bounded retries and candidate freeze;
- `#104/#107`: effort-aware execution routing, Remote Desktop exception/exact-call controls and provider execution-policy convergence;
- GitHub protected branch + one aggregate required gate + GitHub Merge Queue: integration enforcement under ADR 0005;
- `#108`: persistent continuation only;
- Game/Platform/Atlas: provider-owned implementation, writable only with explicit owner authorization for that exact provider and current task.

Under the current bounded contract, `WAITING_EXTERNAL`, `BLOCKED` and `STALLED` release active worker ownership but remain nonterminal. Only the bounded authority determines terminality, and currently only `DONE` is terminal.

## Problem being solved

Oteryn must not conflate:

1. whole task lifetime;
2. worker/session lifetime;
3. one command/tool timeout;
4. external waiting;
5. retry/no-progress protection;
6. context pressure.

A worker ending, command timing out, context rotating or one phase finishing must not by itself mark the whole task complete or failed.

## Continuation model

Worker dispositions:

- `continue_current`
- `release_waiting`
- `rotate_resumable`
- `stop_reinvoke_required`
- `terminal`

Resume mechanisms:

- `same_session`
- `github_native`
- `scheduled_task`
- `work_event_trigger`
- `work_persistent`
- `owner_reinvoke`
- `none_terminal`

`rotate_resumable` requires a real worker-launching/preserving mechanism: `scheduled_task`, `work_event_trigger` or `work_persistent`, with a concrete locator.

`github_native` can advance Actions/Merge Queue/control-plane state but does not itself create a replacement Chat worker. `release_waiting + github_native` is valid only when authoritative remaining-work evidence proves that no later agent-worker action will be required before terminal completion.

If a replacement worker will be needed and no real automatic mechanism exists, record `stop_reinvoke_required` and report that truthfully.

`STALLED` never maps to continuation `terminal` merely because the unchanged retry budget was exhausted. It may resume only after the bounded authority accepts a material progress-fingerprint change.

## Durable lineage

Stable continuation lineage is keyed by:

```text
repository
task_id
checkpoint_lineage_token
```

Branch, PR, exact head and next action are mutable execution coordinates. They must not be used to create a new lineage merely because normal task progress advanced them.

A durable checkpoint must preserve enough trusted state to reconstruct exactly one next safe action without replaying the full chat. It must include the semantic minimum required by the canonical #108 design and delegate bounded retry/evidence continuity to the bounded lifecycle authority rather than defining a competing counter schema.

Checkpointing is control-plane state, not justification for a no-op/retrigger commit.

## Execution surface

- use Chat when current tools are sufficient;
- use GitHub Actions/approved runners for deterministic compute and waiting;
- use Work only for a material Work-only capability such as supported persistent/event-triggered/cloud-browser execution;
- use Codex when its software-development loop materially reduces implementation/testing cost or risk;
- do not route to Work/Codex merely because effort is high.

Surface decisions must use trusted **current-session** capability evidence: exposed tool/connector registration, supported operation schemas, observable repository permissions/authentication, surface compatibility/availability/authorization and evaluation of safe fallbacks. Stale handoffs or caller-supplied booleans are not capability authority.

If no authorized compatible surface can perform a required capability, fail closed only after trusted evidence proves safe fallbacks are exhausted. Do not report `BLOCKED_CAPABILITY_UNAVAILABLE` while a safe authorized fallback remains untested.

## Context handling

Prefer:

> minimal active context + durable GitHub/repository state

Externalize large evidence, compact to material facts, checkpoint at material continuation boundaries, and rotate only when the successor execution is real. Do not invent exact context/token limits that the runtime does not expose.

## Owner communication

Keep owner-facing noise low. Notify for:

- verified terminal completion;
- a real owner/permission/safety decision;
- bounded recovery reaching `STALLED` only when no verified automatic mechanism can wait for a material progress-fingerprint change and resume; `STALLED` remains nonterminal;
- truthful owner re-invocation requirement when automatic continuation is unavailable.

Do not claim background work when none is configured.

## Provider boundary

META design/issues/PRs never confer Game, Platform or Atlas write authority. Before provider mutation, require explicit owner authorization naming the exact repository and current adoption task. Without it, read-only preflight is allowed and mutation fails closed.

Programme closeout needs each provider either adopted on protected main or covered by a fail-closed GitHub-authoritative scope decision. A defer/exclusion counts only when canonical `Oteryn/Oteryn#108` (or its explicitly named successor Issue) contains an `OTERYN_PROVIDER_SCOPE_DECISION_V1` comment naming the exact provider repository, exact current adoption task, `DEFER|EXCLUDE`, non-empty reason, META main SHA and provider main SHA. Closeout must re-read the exact comment, verify the author currently has sufficient repository-admin/owner authority, confirm exact provider/task binding and that no later owner decision supersedes it. Missing authorization, generic handoffs or unverifiable permission are not implicit defer.

## Continuation order

Refresh live state and continue the smallest remaining delta. The intended dependency order is:

1. make the surviving bounded contract canonical on protected main;
2. reconcile `#107` so it retains only routing/RDC/provider-convergence ownership;
3. terminalize this design packet;
4. create a fresh implementation branch from then-current protected main for `#108`;
5. implement the thin continuation policy with RED → GREEN → exact-head CI;
6. perform provider adoption only where separately authorized;
7. close only after protected-main/provider readback proves the scoped programme terminal.

Do not restart already-completed design work and do not recreate ADR0005-retired governance machinery.