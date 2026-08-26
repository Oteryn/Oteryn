# Unified Oteryn World Atlas — Programme Index

Lifecycle: `Oteryn/Oteryn#75`.

Status: proposed until the architecture packet is protected-merged to META `main`. Provider runtime implementation must not start from this branch.

## Canonical packet after merge

1. Architecture decision:
   - `docs/architecture/adr/0005-unified-world-atlas-surfaces-and-reuse.md`
2. Executable implementation DAG:
   - `docs/superpowers/plans/2026-08-26-unified-world-atlas-convergence.md`
3. Cross-repository risk register:
   - `docs/architecture/WORLD_ATLAS_RISK_REGISTER.md`
4. Autonomous programme coordinator:
   - `docs/agents/prompts/OTERYN-WORLD-ATLAS-PROGRAMME-COORDINATOR.md`
5. Parallel role prompt pack:
   - `docs/agents/prompts/OTERYN-WORLD-ATLAS-PARALLEL-AGENT-SUITE.md`
6. Independent terminal auditor:
   - `docs/agents/prompts/OTERYN-WORLD-ATLAS-CLOSEOUT-AUDITOR.md`

## Lifecycle graph

- META parent architecture/programme: `Oteryn/Oteryn#75`
- META prompt pack: `Oteryn/Oteryn#76`
- META embedded bridge security: `Oteryn/Oteryn#77`
- META cross-surface verification: `Oteryn/Oteryn#78`
- META release/cutover: `Oteryn/Oteryn#79`
- META performance/resource evidence: `Oteryn/Oteryn#80`
- META architecture-packet validation: `Oteryn/Oteryn#81`
- Game provider programme: `Oteryn/Oteryn-Game#191`
- Atlas provider programme: `Oteryn/Oteryn-Atlas#188`

Accidental META Issue #82 is closed `not_planned` and carries no programme authority.

## Default execution entry point

After this packet is canonical on protected META `main`, the normal owner invocation is:

`OTERYN-WORLD-ATLAS-PROGRAMME-COORDINATOR`

Recommended reasoning effort: **Extra High**.

The coordinator resolves current GitHub state, ownership and dependencies before releasing provider work. Do not manually start mutating worker roles merely because this planning packet exists.

## Optional manual Wave 0 parallel scouts

If the owner chooses separate chats instead of an agent-capable coordinator, these five roles are intentionally read-only and may run concurrently after the packet is canonical:

- `OTERYN-WORLD-ATLAS-GAME-CONTRACT-SCOUT` — Extra High
- `OTERYN-WORLD-ATLAS-ATLAS-MIGRATION-SCOUT` — Extra High
- `OTERYN-WORLD-ATLAS-CLIENT-HOST-SCOUT` — Extra High
- `OTERYN-WORLD-ATLAS-SECURITY-SCOUT` — Extra High
- `OTERYN-WORLD-ATLAS-VERIFICATION-PERF-SCOUT` — Extra High

Their exact prompts and return formats are in the parallel-agent suite.

## Allocation-gated later leads

These must not mutate until the coordinator records a fresh provider child Issue, `admission_main_sha`, branch/worktree and exact path ownership:

- `OTERYN-WORLD-ATLAS-GAME-PROVIDER-LEAD`
- `OTERYN-WORLD-ATLAS-ATLAS-CORE-LEAD`
- `OTERYN-WORLD-ATLAS-WEB-EMBEDDED-LEAD`
- `OTERYN-WORLD-ATLAS-CLIENT-INTEGRATION-LEAD`
- `OTERYN-WORLD-ATLAS-QUALIFICATION-LEAD`
- `OTERYN-WORLD-ATLAS-FINAL-INTEGRATION-LEAD`

Normal mutating concurrency is 2–3 disjoint lanes. Root Cargo/workspace, client composition, Atlas shared FullWorld shell, workflow/CI and release-manifest surfaces are serialized leases.

## Terminal verification entry point

After provider implementation/cutover claims completion, run independently:

`OTERYN-WORLD-ATLAS-CLOSEOUT-AUDITOR`

Recommended reasoning effort: **Extra High**.

Only the auditor's `DONE` verdict backed by exact provider evidence permits the programme coordinator to report terminal completion.
