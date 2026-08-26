# Unified Oteryn World Atlas — Programme Index

Lifecycle: `Oteryn/Oteryn#75`.

Architecture admission authority is the protected-merged pull request that carries this exact packet. Superseded unmerged recovery pull requests carry no architecture-admission authority.

Status: proposed until the architecture packet is protected-merged to META `main`. Provider runtime implementation must not start from this branch.

## Canonical packet after merge

1. Programme manifest / admission index:
   - `docs/architecture/WORLD_ATLAS_PROGRAMME_INDEX.md`
2. Architecture decision:
   - `docs/architecture/adr/0005-unified-world-atlas-surfaces-and-reuse.md`
3. Executable implementation DAG:
   - `docs/superpowers/plans/2026-08-26-unified-world-atlas-convergence.md`
4. Cross-repository risk register:
   - `docs/architecture/WORLD_ATLAS_RISK_REGISTER.md`
5. Release compatibility / cutover evidence contract:
   - `docs/architecture/WORLD_ATLAS_RELEASE_COMPATIBILITY_CONTRACT.md`
6. Autonomous programme coordinator:
   - `docs/agents/prompts/OTERYN-WORLD-ATLAS-PROGRAMME-COORDINATOR.md`
7. Parallel role prompt pack:
   - `docs/agents/prompts/OTERYN-WORLD-ATLAS-PARALLEL-AGENT-SUITE.md`
8. Independent terminal auditor:
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

The accepted exact head SHA must be the same candidate covered by successful required `meta-gate` and `ai-review-gate` checks and accepted R2/deep review evidence before protected squash merge. A merge SHA, Issue narration, floating branch, stale/raw review, failing/missing trusted verifier, or admin/bypass path cannot substitute for those exact-head admission identities. After merge, the complete eight-path manifest above must be readable from the exact protected-main squash-merge SHA before provider runtime execution treats this architecture as canonical.

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

## Terminal evidence model

`WORLD_ATLAS_RELEASE_COMPATIBILITY_CONTRACT.md` is canonical for the exact release tuple. It requires, separately for Game and Atlas:

```text
provider_pr_head_sha
provider_required_check_set_evidence_ref
complete provider_required_check_refs[]
provider_review_evidence_refs[]
provider_merge_evidence_ref
provider_main_or_release_commit_sha
provider_post_merge_evidence_refs[]
```

Checks/review bind the exact pre-squash provider PR head. Merge evidence binds that head to the exact resulting protected-main/release SHA. A non-empty subset of required checks is insufficient.

The same contract requires authorized Game/Atlas build-source commit SHAs tied to final provider revisions, immutable Game export-build and Atlas bundle-build chains, exact client/bundle/bridge handshake evidence, exact public deployment/bundle evidence, and a `qualification_candidate_evidence_manifest_ref` binding security/performance/E2E/rollback evidence to the exact released candidate. Stale candidate evidence is not terminal evidence.

The current generic META release schema is not the terminal World Atlas record format. Issue #84 owns the dedicated mechanism. Before Wave 7 Task 7E can complete, protected META `main` must contain:

- `ecosystem/world-atlas/compatibility.schema.json`;
- `ecosystem/world-atlas/releases/<release_id>.json`;
- `tools/governance/validate_world_atlas_compatibility.py`;
- `meta-gate` integration with deterministic positive/negative tests.

If absent, cutover is `WAITING_EXTERNAL`, not an invitation to encode the tuple in opaque generic fields.

## Optional manual Wave 0 parallel scouts

The five Wave-0 roles may run concurrently, but provider read-only does not mean lifecycle-free. Every independently launched scout is a META evidence-only worker with a fresh META child Issue, dedicated branch/worktree and PR/task head, exactly one disjoint `docs/evidence/world-atlas/wave0/<role>.md` report path or recorded equivalent, and a normal PR-backed execution-routing packet validated against fresh GitHub state. It may mutate only that META evidence report; Game/Atlas/provider/runtime/config/Cargo/workflow/shared-shell/production surfaces remain read-only. There is no PR-less scout route.

Roles:

- `OTERYN-WORLD-ATLAS-GAME-CONTRACT-SCOUT` — Extra High
- `OTERYN-WORLD-ATLAS-ATLAS-MIGRATION-SCOUT` — Extra High
- `OTERYN-WORLD-ATLAS-CLIENT-HOST-SCOUT` — Extra High
- `OTERYN-WORLD-ATLAS-SECURITY-SCOUT` — Extra High
- `OTERYN-WORLD-ATLAS-VERIFICATION-PERF-SCOUT` — Extra High

## Qualification evidence lane

`OTERYN-WORLD-ATLAS-QUALIFICATION-LEAD` is provider-read-only over frozen candidates but gets a real META qualification-evidence Issue/branch/worktree/PR/task head, one qualification report path and normal PR-backed routing validation. Provider test/evidence-code changes require separate provider child tasks. WA-6Q must produce an immutable qualification candidate manifest binding accepted evidence to the exact candidate/released tuple. There is no PR-less WA-6Q route.

## Allocation-gated mutating leads

These must not mutate provider code until the coordinator records fresh provider child Issue, `admission_main_sha`, branch/worktree, exact path ownership and passing routing validation:

- `OTERYN-WORLD-ATLAS-GAME-PROVIDER-LEAD`
- `OTERYN-WORLD-ATLAS-ATLAS-CORE-LEAD`
- `OTERYN-WORLD-ATLAS-WEB-EMBEDDED-LEAD`
- `OTERYN-WORLD-ATLAS-CLIENT-INTEGRATION-LEAD`
- `OTERYN-WORLD-ATLAS-FINAL-INTEGRATION-LEAD`

Normal mutating concurrency is 2–3 disjoint lanes. Root Cargo/workspace, client composition, Atlas shared FullWorld shell, workflow/CI and release-manifest surfaces are serialized leases.

## Terminal verification entry point

After provider implementation/cutover and the canonical V1 compatibility record are complete, run:

`OTERYN-WORLD-ATLAS-CLOSEOUT-AUDITOR`

Recommended reasoning effort: **Extra High**.

The closeout auditor is itself substantial and therefore uses a real PR-backed META closeout-evidence lifecycle: fresh child Issue under #75/#81, dedicated branch/worktree + PR/task head, exactly one `docs/evidence/world-atlas/closeout/<release-id-or-candidate>.md` report path or recorded equivalent, and normal routing validation against fresh GitHub state. Provider/META product/config state remains read-only from the auditor. There is no PR-less closeout route.

Only a `DONE` verdict backed by the canonical closeout report and its immutable META evidence, plus the exact provider/compatibility evidence required above, permits the coordinator to report terminal programme completion.