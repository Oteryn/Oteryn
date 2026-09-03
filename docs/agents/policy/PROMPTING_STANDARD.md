# Oteryn Prompting Standard

Policy: `OTERYN_ORGANIZATION_AGENT_POLICY@3.0.0`

Write prompts as **task-specific deltas** on top of the current governing repository instructions and immutable META policy binding. Do not restate the agent operating system in every prompt.

A substantial prompt may contain these fields when they materially change execution:

1. `ROLE / OUTCOME` — bounded role and one observable target.
2. `AUTHORITY / SCOPE DELTA` — exact writable scope and task-specific prohibited effects.
3. `LIVE LOCATORS` — Issue/task/PR/branch identifiers needed to refresh current truth.
4. `DOMAIN CONSTRAINTS / DEPENDENCIES` — product/domain invariants and prerequisites unique to this work.
5. `ACCEPTANCE / VALIDATION DELTA` — observable evidence required specifically for this task.
6. `STOP / HANDOFF DELTA` — genuine owner/safety/authority blockers and durable next state.

Omit a section when it has no task-specific content.

## Inherited policy

Do not copy global GitHub-first, moving-main, branch/worktree, concurrency, Remote Desktop, AI-review, retry/continuation, merge or generic closeout policy into task prompts. Resolve those rules through the provider's immutable META binding and current repository instructions.

A task prompt may narrow authority or name a task-specific risk trigger. It must not create a broader permission, a second merge authority, a local Remote Desktop controller, a local Codex controller or a parallelism requirement that conflicts with META.

## Live state and authority

Use identifiers as locators, not frozen truth. Refresh material live state before relying on it for mutation or integration. Do not ask the owner for facts that an authorized live-state read can resolve.

Prompt aliases and reusable prompt lifecycle entries grant discoverability, not write authority. Mutation still requires the current task/repository allocation or explicit owner authorization required by the governing repository.

## Outcome-first instructions

Prefer one observable objective and success criteria over a detailed step-by-step procedure. Prescribe steps only when order is itself a correctness/safety invariant or when evaluation has shown that the model otherwise fails materially.

Keep domain constraints that are easy to violate and costly to rediscover. Remove generic reminders already supplied by higher authority or deterministic enforcement.

## Parallelism

Do not make multi-agent execution mandatory by template. Use one worker when it is sufficient. Use parallel analysis or implementation only when independent workstreams have clear ownership boundaries and measurable value.

## Handoffs

A handoff is state, not policy. Keep only durable coordinates, completed/remaining material work, evidence, blocker/disposition and one next safe action. Never paste the global policy bundle into a handoff.
