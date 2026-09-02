# Unified Oteryn World Atlas Convergence Implementation Plan

> Execute task-by-task with isolated branches/worktrees and current repository governance. Parallel work is allowed only where dependency and ownership rules below permit it.

**Goal:** converge Oteryn World Atlas into one reusable product capability: Game-owned authoritative exports feed an Atlas-owned Rust Core and one web product lineage serving both public Atlas and a locally packaged embedded native-client Atlas, while gameplay minimap/HUD stays native Rust/wgpu and private live state stays local.

**Architecture:** Game remains canonical World/Content/gameplay authority and publishes explicit versioned public-safe Atlas artifacts. Atlas introduces a strangler-migrated Rust derived core, bounded WASM adapters where justified, and one web UI/product bundle. The Game client embeds a pinned local Atlas bundle through a security-bounded host/bridge. META coordinates architecture, compatibility and immutable evidence only.

**Canonical spec:** `docs/architecture/adr/0005-unified-world-atlas-surfaces-and-reuse.md`

**Release contract:** `docs/architecture/WORLD_ATLAS_RELEASE_COMPATIBILITY_CONTRACT.md`

**Risk register:** `docs/architecture/WORLD_ATLAS_RISK_REGISTER.md`

## 1. Global invariants

- `Oteryn/Oteryn-Game` is the sole canonical World/Content/gameplay-fact authority.
- `Oteryn/Oteryn-Atlas` is the derived Atlas product and independent release/failure domain.
- Game→Atlas remains provider-owned, explicit, versioned, public-safe and artifact-first.
- META never copies provider schemas/runtime or becomes a second content database.
- Atlas does not depend on arbitrary Game-internal Rust crates.
- No big-bang rewrite: every migrated Atlas capability is parity-first, independently reversible and benchmarked.
- Embedded Atlas content is local/pinned/digest-bound; public Atlas availability is not a gameplay dependency.
- Native gameplay minimap/HUD remains usable when the embedded Atlas host is absent, incompatible, crashed or disabled.
- Private/live client state is local-session-only and never a public Atlas publication input.
- Bridge V1 is non-authoritative UI integration only; no movement/combat/item-use/arbitrary server mutation.
- Every substantial new/resumed task gets a fresh GitHub snapshot and a passing canonical execution-routing packet before work is released.
- One mutating task = one Issue, one branch/worktree, one PR, exact owned paths and immutable `admission_main_sha`.
- Moving `main` is `UPSTREAM_ADVANCED`, not restart authority; integrate late and rerun only invalidated proof.
- Shared Cargo/workspace/toolchain, Game client composition, Atlas FullWorld/shared shell, workflows/CI, META compatibility record and final integration are serialized leases.
- Re-read `WORLD_ATLAS_RISK_REGISTER.md` at provider design freeze, host selection, candidate freeze and final cutover. Triggered unresolved Critical risks block; triggered High risks require explicit mitigation evidence.
- No provider production/live deployment is authorized by this META architecture packet itself.

Planning SHAs are provenance only. All execution resolves live state.

## 2. Lifecycle graph

| Scope | Lifecycle | Owner |
| --- | --- | --- |
| architecture/programme | `Oteryn/Oteryn#75` | META |
| prompt/orchestration pack | `Oteryn/Oteryn#76` | META |
| embedded bridge security | `Oteryn/Oteryn#77` | META composition / provider evidence |
| cross-surface verification | `Oteryn/Oteryn#78` | META composition / provider evidence |
| release/cutover | `Oteryn/Oteryn#79` | META |
| performance/resource evidence | `Oteryn/Oteryn#80` | META composition / provider evidence |
| architecture packet validation | `Oteryn/Oteryn#81` | META |
| World Atlas Compatibility Record V1 | `Oteryn/Oteryn#84` | META mechanism |
| Game programme | `Oteryn/Oteryn-Game#191` | Game |
| Atlas programme | `Oteryn/Oteryn-Atlas#188` | Atlas |

#84 is the single lifecycle for the dedicated World Atlas compatibility schema/validator. Do not duplicate it.

## 3. Immutable provider and artifact identity model

Keep the following stages separate for **each provider**:

```text
provider_pr_head_sha
  -> provider_required_check_set_evidence_ref
  -> complete exact-head provider_required_check_refs[]
  -> accepted exact-head provider_review_evidence_refs[]
  -> immutable provider_merge_evidence_ref
  -> provider_main_or_release_commit_sha
  -> provider_post_merge_evidence_refs[]
```

Rules:

- `provider_required_check_set_evidence_ref` is an immutable snapshot of the applicable final PR/base protection/ruleset state and enumerates the **complete** expected required-check set.
- Recorded provider check refs must cover that complete set. A non-empty subset is insufficient.
- Pre-squash checks/review bind to the exact provider PR head, never merely to the resulting squash/main SHA.
- Immutable merge evidence binds that exact head to the exact resulting protected-main/release SHA.
- The reviewed head alone does not prove the merge result; the resulting main SHA alone does not prove which head passed checks/review.

The final record also preserves authorized artifact-build source identities:

```text
game_atlas_export_build_source_commit_sha
atlas_embedded_bundle_build_source_commit_sha
```

Each build source must equal the corresponding final provider PR head or resulting main/release SHA. Build evidence from unrelated/stale revisions is invalid unless a later accepted contract explicitly introduces another authorized derivation mode.

Additional required chain-of-custody:

- Game build source + producer revision + profile/version + world/content revision → Game export-build evidence → exact manifest/payload digests.
- Exact Game digests → Atlas accepted digests + Atlas build source + Core identity → Atlas bundle-build evidence → exact embedded bundle version/digest.
- Game client pins the exact embedded bundle digest.
- Exact client + bundle + supported bridge range/profile + world identity → bridge handshake evidence → selected protocol/profile.
- Public deployment identity → exact public deployed bundle version/digest.
- `qualification_candidate_evidence_manifest_ref` binds qualification evidence to the exact candidate/released tuple; stale-candidate evidence cannot carry forward.

## 4. Stable conceptual interfaces

### 4.1 Game → Atlas artifact

Must carry producer revision, export profile version, world/content revision, public capabilities, payload manifest/digests, provenance and minimum consumer requirements. Only Game-selected public-safe facts are allowed.

### 4.2 Atlas Core

Provider design freezes bounded deterministic operations for verified artifact ingestion, world/spatial queries, search/intelligence, entity/location resolution, routing/path products and capability-state reporting. DOM/browser state is not a second authority.

### 4.3 Embedded bundle

Manifest identifies exact bundle version/digest, Atlas Core/API identity, supported Game export profiles, supported bridge range/profile, required host capabilities and file/asset digests.

### 4.4 Local bridge

Handshake binds protocol, capability profile, exact Game client identity, exact pinned Atlas bundle and world/content compatibility identity. Mismatch disables bridge/live overlay fail-closed.

Candidate V1 client→Atlas state: player position/floor, route progress, privacy-approved party positions, locale and separately accepted bounded quest context. Candidate Atlas→client intents: validated set/clear waypoint and focus coordinate/entity only.

## 5. Execution DAG

```text
canonical META architecture packet
        |
        v
Wave 0: five provider-read-only / META evidence-only scouts
        |
        v
Wave 1: Game + Atlas provider design freeze
        |
        +-------------------+
        v                   v
Wave 2 Game foundations   Atlas Rust foundation
        |                   |
        |            Wave 3 Atlas Core lanes
        |                   |
        |            Wave 4 WASM/web + bundle
        +---------+---------+
                  v
Wave 5 native host + bridge
                  v
Wave 6 routed qualification evidence + provider qualification
                  v
Wave 7 provider integration/cutover + #84 V1 record
                  v
routed independent closeout evidence
                  v
Wave 8 legacy retirement
```

Normal maximum reasoning/evidence lanes: 5. Normal mutating provider lanes: 2–3 disjoint lanes.

## 6. Wave 0 — provider-read-only / META evidence-only discovery

Wave 0 starts only after the architecture packet is canonical on protected META `main`.

Each independently launched WA-0A..WA-0E gets a fresh META child Issue under #75, dedicated META branch/worktree and PR/task head, exactly one disjoint `docs/evidence/world-atlas/wave0/<role>.md` report path or recorded equivalent, and normal PR-backed routing validation against fresh GitHub state. Only that report is writable. Game/Atlas/provider runtime/config/Cargo/workflow/shared-shell/production paths remain read-only. There is no PR-less Wave-0 route.

- **0A Game contract scout:** inventory public Atlas contracts/profiles, deterministic producer/provenance, world/content identities, fixtures, gaps, optional public Rust codec value and active ownership conflicts.
- **0B Atlas migration scout:** trace `tools/**`, `src/browser/**`, `web/**`, publication/tests; classify keep/migrate/benchmark-gated paths, parity oracles, interfaces and shared leases.
- **0C Client-host scout:** compare composition boundary and viable embedded hosts across local origin, navigation/CSP/resources, JS↔native bridge, crash isolation, packaging, accessibility/input, offline, licensing and benchmark plan.
- **0D Security scout:** threat-model bundle/XSS/navigation/bridge spoof/flood/privilege/credentials/private-state/stale-artifact/host/supply-chain failures.
- **0E Verification/performance scout:** map provider gates, representative fixtures, cross-surface journeys, heavy-runner constraints and benchmark format.

Wave-0 gate: review all five META evidence PR handoffs before provider design mutation.

## 7. Wave 1 — provider design freeze

Game and Atlas designs may run concurrently. Execute design risk checkpoint before acceptance.

- **1A Game:** freeze export gaps/identities, embedded-host adapter, native minimap independence, bridge endpoint/profile, bundle pinning, failure behavior, tests and serialized Cargo/client-composition leases.
- **1B Atlas:** freeze Rust workspace/crates, pure-core dependency direction, Game artifact consumer boundary, parity seams, Core/WASM APIs, embedded bundle manifest, bridge endpoint, Production UI Shell integration, rollback flags, tests and FullWorld/workflow leases.
- **1C Security:** freeze trusted origin, network/navigation/CSP, capability allowlist, message framing/version/size/rate, privacy/retention, crash behavior, supply-chain policy and negative tests.

## 8. Wave 2 — foundations

- **2A Atlas Rust foundation:** serialized root lease for workspace/core/model, deterministic bounded errors/resources, unit/property tests and CI/lint/security checks. No production cutover yet.
- **2B Game export gaps:** only for proven gaps. Deliver provider-owned contract/producer changes, permanent tests, fixtures and Game export-build evidence. If no gap, record `NO_CHANGE_REQUIRED`.
- **2C Host prototype:** isolated Game paths; measure local content, navigation isolation, startup, RSS/CPU/GPU, input/focus, crash/hang isolation, offline, packaging and dependency security. Execute host-selection risk checkpoint before promotion.

## 9. Wave 3 — Atlas Core lanes

After foundation/API canonicalization, release up to three disjoint Atlas lanes: verified ingestion/compiler/index parity, spatial/query core, and search/intelligence core. Every lane uses RED→GREEN permanent tests, accepted oracle/parity, deterministic results, bounded resources, benchmark evidence and rollback/shadow path. Shared shell/CI edits require serialized leases.

## 10. Wave 4 — Web/WASM + reusable bundle

Expose reusable core behavior through bounded WASM only where justified; keep DOM/accessibility/UI in web technology; cut over capability-by-capability with parity and rollback; produce one deterministic public/embedded bundle lineage; keep public mode bridge-free and embedded mode local/default-deny. Preserve immutable Atlas build evidence linking authorized Atlas build source + exact accepted Game digests + Core identity → exact embedded bundle version/digest.

## 11. Wave 5 — native client integration

Requires accepted host, immutable embedded bundle candidate and frozen bridge/security profile. Production host loads only pinned local bundle and contains failures; native bridge validates handshake/source/size/rate/capabilities and exposes no gameplay mutation/credentials; embedded endpoint keeps local state ephemeral; native minimap remains independent; produce immutable bridge handshake/compatibility evidence.

## 12. Wave 6 — qualification

Freeze exact provider candidate PR heads, authorized build source SHAs, artifact digests, client/bundle/bridge identities and execute candidate risk checkpoint.

### 12.1 WA-6Q routed qualification-evidence lifecycle

`OTERYN-WORLD-ATLAS-QUALIFICATION-LEAD` is provider-read-only over frozen candidates but not lifecycle-free. Each qualification cycle gets:

- fresh META qualification-evidence child Issue under #78/#80;
- dedicated META branch/worktree and PR/task head;
- exactly one `docs/evidence/world-atlas/qualification/<candidate-or-role>.md` report path or recorded equivalent;
- normal PR-backed routing validation against fresh GitHub state;
- write authority only to that META report.

Provider candidate code/config remains read-only for WA-6Q. Provider test/evidence code changes require a separate provider child Issue/branch/worktree/PR/routing packet, invalidate affected evidence and return the candidate to integration. There is no PR-less WA-6Q route.

### 12.2 Qualification candidate manifest

WA-6Q must preserve immutable `qualification_candidate_evidence_manifest_ref` binding the qualification generation and all accepted security/performance/E2E/rollback refs to the exact candidate identities applicable to that proof:

- Game provider PR head;
- Game authorized export build source SHA, export profile/producer/world revision and exact digests;
- Atlas provider PR head;
- Atlas authorized bundle build source SHA, Core identity and exact embedded bundle;
- exact client identity + bundle pin;
- exact bridge protocol/profile + handshake identity;
- for post-deployment/live evidence, exact public deployment + public bundle identity.

Every evidence ref must resolve directly to those same exact identities or be explicitly bound by this manifest. Product/config/provider-head/artifact/bundle/client/bridge/deployment changes invalidate stale qualification evidence.

### 12.3 Qualification proof

- #77 security: origin/navigation/CSP, bridge limits/allowlist, secret/private-state protections, malicious input/host/dependency failures.
- #80 performance: exact machine/profile, Rust migration comparisons, WASM/bundle startup, host RSS/CPU/GPU/input and native minimap baseline.
- #78 cross-surface E2E: compatible public facts/location/floor/camera/routing, embedded-only local state, public no-private-state, host failure/minimap independence and negative bundle/export/bridge cases.

## 13. Wave 7 — provider integration, cutover and V1 record

Execute final-cutover risk checkpoint first.

### 7A Candidate evidence freeze

Freeze only identities that already exist: provider PR heads, required-check-set snapshots, complete exact-head check/review refs, authorized build source SHAs, Game export chain, Atlas bundle-build chain, client/bundle, bridge handshake, qualification candidate manifest and accepted security/performance/E2E/rollback refs. Do not invent resulting squash/main SHAs or terminal public deployment identities.

### 7B Provider final integration

For **each provider independently**:

1. refresh protected `main`, merge-up if needed and rerun invalidated exact-head proof;
2. freeze exact **pre-squash provider PR head SHA**;
3. freeze immutable `provider_required_check_set_evidence_ref` from the applicable protection/ruleset state and enumerate the complete expected required-check set;
4. preserve required-check refs covering that entire set and accepted review refs resolving to the exact PR head;
5. protected-squash-merge;
6. record exact resulting protected `main`/release SHA;
7. record immutable merge evidence proving `provider_pr_head_sha -> provider_main_or_release_commit_sha`;
8. run required post-merge/live evidence against the resulting SHA.

A non-empty subset of required checks is insufficient. Checks/reviews bound only to post-squash SHA are invalid. A reviewed PR head without merge binding does not prove the protected-main result. Old/stale/wrong-stage/wrong-result/cross-provider evidence is blocking.

### 7C Artifact source binding

- `game_atlas_export_build_source_commit_sha` must equal the final Game provider PR head or resulting Game main/release SHA. Game build evidence binds that exact source + producer/profile/world inputs → exact manifest/payload digests.
- `atlas_embedded_bundle_build_source_commit_sha` must equal the final Atlas provider PR head or resulting Atlas main/release SHA. Atlas build evidence binds that exact source + accepted Game digests + Core identity → exact embedded bundle version/digest.
- Artifacts from unrelated/stale source revisions are blocking.

### 7D Public Atlas cutover and native client acceptance

Atlas performs merged-main deployment/live acceptance and records exact deployment identity, deployed public bundle/version/digest, deployment→bundle evidence, rollback artifact and declared relation. Game acceptance runs against exact embedded bundle and bridge tuple. Update/extend qualification manifest/evidence as required so post-deployment/live proof binds to exact released public deployment/bundle identity; stale pre-deployment evidence alone is insufficient.

### 7E Terminal refreeze + dedicated META V1 record

1. Refresh/reconcile #84; do not duplicate it.
2. Require canonical #84 schema/validator/regressions and `meta-gate` integration.
3. If absent, return `WAITING_EXTERNAL: WORLD_ATLAS_COMPATIBILITY_RECORD_MECHANISM_NOT_CANONICAL`.
4. Terminally refreeze, separately for Game and Atlas: PR head, required-check-set snapshot, complete required-check refs, exact-head review refs, resulting main/release SHA, immutable head→result merge evidence and post-merge/live evidence.
5. Refreeze authorized build source SHAs and exact Game export, Atlas embedded-bundle, client pin, bridge handshake, qualification candidate manifest/evidence and public deployment chains.
6. Create only `ecosystem/world-atlas/releases/<release_id>.json` under #84 schema.
7. Validate all cross-links including complete check-set coverage, authorized build sources and exact candidate-bound qualification evidence.
8. Deliver through dedicated META PR with exact-head checks/review.
9. Protected-squash-merge, read exact record path from exact merge SHA, and require post-merge `meta-gate` on that SHA.

Issue narration, generic releases, Draft/unmerged PRs or Markdown tuples are not terminal records.

## 14. Routed independent closeout

After the canonical V1 record and provider terminal evidence exist, run `OTERYN-WORLD-ATLAS-CLOSEOUT-AUDITOR` through a real META closeout-evidence lifecycle:

- fresh META closeout-evidence child Issue under #75/#81 for the exact release/candidate;
- dedicated META branch/worktree and PR/task head;
- exactly one `docs/evidence/world-atlas/closeout/<release-id-or-candidate>.md` report path or recorded equivalent;
- normal PR-backed routing validation;
- provider/META product/config state read-only from the auditor;
- only the closeout report writable.

If closeout finds defects, return `NOT_DONE` and create separate owning tasks. Do not repair from the auditor branch. Preserve the closeout report PR/head/check/review/merge/readback evidence required by current META policy before its `DONE` can authorize programme completion. There is no PR-less closeout route.

## 15. Wave 8 — legacy retirement

Open separate bounded Atlas removal lifecycles only after the new default has parity/browser/live acceptance, rollback evidence, acceptable performance/security and zero active consumers. No opportunistic cleanup.

## 16. Rollback matrix

| Failure | Response |
| --- | --- |
| Rust compiler/index regression | restore previous accepted capability path until removal gate |
| WASM failure | use retained compatible current path for that capability |
| public deployment regression | Atlas rollback to prior exact deployment/bundle pair |
| embedded bundle incompatible/corrupt | disable panel or repin prior compatible bundle in a new client candidate; native minimap stays |
| bridge mismatch/failure | disable bridge/live overlay; do not guess compatibility |
| embedded host crash/hang | tear down/disable host; gameplay/native minimap stays |
| private-state leak | fail release, disable bridge profile, sanitize evidence/logging, requalify security |
| Game export incompatible | Atlas rejects/marks unavailable; no legacy-runtime truth fallback |
| bad META compatibility record | retain prior canonical record; do not report DONE |

## 17. Definition of Done

Programme completion requires immutable proof that:

- architecture packet is canonical on protected META main;
- Game/Atlas child work is terminal or evidence-backed `NO_CHANGE_REQUIRED`;
- authority boundary remains intact;
- Atlas Rust Core is real, tested, parity-qualified and rollback-capable;
- public and embedded Atlas use the accepted shared Core/bundle architecture;
- embedded Atlas works locally/offline and native minimap remains independent;
- bridge is versioned/default-deny/security-qualified and private state remains local;
- performance/cross-surface/security proof exists;
- substantial routing evidence is valid, including Wave-0, WA-6Q and closeout PR-backed META evidence lanes;
- each provider has immutable complete required-check-set snapshot + complete exact-head checks/review on pre-squash PR head + merge binding to exact resulting main/release SHA + post-merge/live evidence;
- Game/Atlas build source SHAs are authorized final provider revisions and exact export/bundle chains are proven;
- bridge/client/public deployment chains are exact;
- qualification evidence is bound to the exact released candidate, not a prior candidate generation;
- no triggered cutover-blocking risk remains unresolved;
- #84 V1 mechanism is canonical;
- final compatibility record is exact-head reviewed/gated, protected-squash-merged, exact-record read back and post-merge validated;
- fresh independent closeout is produced through its routed META closeout-evidence lifecycle and returns `FINAL_VERDICT: DONE` with immutable report evidence;
- retained/removed legacy paths are truthful.

## 18. Coordinator completion report

Return exact:

- META/Game/Atlas protected SHAs and implementation PR/merge identities;
- each provider PR head, required-check-set snapshot, complete required-check/review refs, resulting main/release SHA, merge evidence and post-merge/live evidence;
- Game/Atlas authorized build source SHAs and build/artifact evidence;
- public deployment/bundle/relation evidence;
- bridge protocol/profile/handshake + client identity;
- qualification candidate manifest and security/performance/E2E/rollback evidence;
- Wave-0, WA-6Q and closeout META evidence Issue/PR/report/routing identities;
- #84 schema/validator/final-record PR/head/merge/readback/post-merge-gate refs;
- risk evidence;
- retained legacy paths/reasons;
- independent closeout verdict;
- final `DONE|WAITING_EXTERNAL|BLOCKED|STALLED` with exact reason.