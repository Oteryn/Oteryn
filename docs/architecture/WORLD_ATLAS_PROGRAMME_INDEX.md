# Unified Oteryn World Atlas — Programme Index

Lifecycle: `Oteryn/Oteryn#75`.

Architecture admission authority is the protected-merged pull request that carries this exact packet. Superseded unmerged recovery pull requests carry no architecture-admission authority.

Status: proposed until the architecture packet is protected-merged to META `main`. Provider runtime implementation must not start from this branch.

## Canonical packet after merge

1. Architecture decision:
   - `docs/architecture/adr/0005-unified-world-atlas-surfaces-and-reuse.md`
2. Executable implementation DAG:
   - `docs/superpowers/plans/2026-08-26-unified-world-atlas-convergence.md`
3. Cross-repository risk register:
   - `docs/architecture/WORLD_ATLAS_RISK_REGISTER.md`
4. Release compatibility / cutover evidence contract:
   - `docs/architecture/WORLD_ATLAS_RELEASE_COMPATIBILITY_CONTRACT.md`
5. Autonomous programme coordinator:
   - `docs/agents/prompts/OTERYN-WORLD-ATLAS-PROGRAMME-COORDINATOR.md`
6. Parallel role prompt pack:
   - `docs/agents/prompts/OTERYN-WORLD-ATLAS-PARALLEL-AGENT-SUITE.md`
7. Independent terminal auditor:
   - `docs/agents/prompts/OTERYN-WORLD-ATLAS-CLOSEOUT-AUDITOR.md`

### Architecture-packet admission evidence

The packet becomes canonical only through the normal protected META pull-request lifecycle. Terminal architecture evidence must independently identify:

```text
meta_architecture_pr_number
meta_architecture_pr_head_sha
meta_architecture_pr_required_check_refs
meta_architecture_pr_review_evidence_refs
meta_architecture_pr_squash_merge_sha
protected_main_packet_readback_ref
```

The accepted exact head SHA must be the same candidate covered by the required `meta-gate` and accepted R2/deep review evidence before protected squash merge. A merge SHA, Issue narration, floating branch, stale review or admin/bypass path cannot substitute for those exact-head admission identities. After merge, ADR 0005, the executable plan and coordinator/auditor packet must be readable from the exact protected-main squash-merge SHA before provider runtime execution treats this architecture as canonical.

## Lifecycle graph

- META parent architecture/programme: `Oteryn/Oteryn#75`
- META prompt pack: `Oteryn/Oteryn#76`
- META embedded bridge security: `Oteryn/Oteryn#77`
- META cross-surface verification: `Oteryn/Oteryn#78`
- META release/cutover: `Oteryn/Oteryn#79`
- META performance/resource evidence: `Oteryn/Oteryn#80`
- META architecture-packet validation: `Oteryn/Oteryn#81`
- META World Atlas Compatibility Record V1 implementation: `Oteryn/Oteryn#84`
- Game provider programme: `Oteryn/Oteryn-Game#191`
- Atlas provider programme: `Oteryn/Oteryn-Atlas#188`

Accidental META Issue #82 is closed `not_planned` and carries no programme authority.

## Default execution entry point

After this packet is canonical on protected META `main`, the normal owner invocation is:

`OTERYN-WORLD-ATLAS-PROGRAMME-COORDINATOR`

Recommended reasoning effort: **Extra High**.

The coordinator resolves current GitHub state, ownership and dependencies before releasing provider work. Do not manually start mutating worker roles merely because this planning packet exists.

For release/cutover, `WORLD_ATLAS_RELEASE_COMPATIBILITY_CONTRACT.md` is the canonical exact tuple/evidence contract. Its required produced Game export artifact digests and protected-main META compatibility-record evidence refine the shorthand Wave 7 tuple in the implementation plan and may not be omitted.

The current generic META release schema is not the terminal World Atlas record format. Issue #84 owns the required dedicated implementation. Before Wave 7 Task 7E can complete, protected META `main` must contain:

- `ecosystem/world-atlas/compatibility.schema.json`;
- `ecosystem/world-atlas/releases/<release_id>.json` for each final record;
- `tools/governance/validate_world_atlas_compatibility.py`;
- integration of that validator into `meta-gate` with deterministic negative/positive tests.

If that mechanism is absent, cutover is `WAITING_EXTERNAL`, not an invitation to encode the tuple in opaque generic fields.

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

Only the auditor's `DONE` verdict backed by exact provider evidence and the canonical validated protected-main World Atlas compatibility record permits the programme coordinator to report terminal completion.
