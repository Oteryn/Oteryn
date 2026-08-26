# Unified Oteryn World Atlas Convergence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use an isolated task/worktree workflow and execute this plan task-by-task. Parallel workers are allowed only where the dependency/ownership table explicitly permits them.

**Goal:** Evolve Oteryn World Atlas into one reusable product capability: Game-owned authoritative exports feed an Atlas-owned Rust Core and one web product bundle that serves both the public Atlas and a locally embedded native-client Atlas, while the gameplay minimap remains native Rust/wgpu and private live state stays local.

**Architecture:** Game remains canonical World/Content/gameplay authority and publishes explicit versioned public-safe Atlas artifacts. Atlas introduces a strangler-migrated Rust computational core, compiles a reusable web/WASM bundle, and keeps web UI ownership in the browser stack. The Game client embeds a pinned local Atlas bundle through a security-bounded host/bridge while retaining an independent native minimap/HUD.

**Tech Stack:** Rust 2024 in Game; Rust for new Atlas Core; WASM for browser reuse where accepted; existing Atlas JS/HTML/CSS/WebGL/Playwright during migration; existing Game wgpu/native client; immutable provider artifacts/digests; GitHub protected-branch lifecycle.

**Spec:** `docs/architecture/adr/0005-unified-world-atlas-surfaces-and-reuse.md`

**Release contract:** `docs/architecture/WORLD_ATLAS_RELEASE_COMPATIBILITY_CONTRACT.md`

**Risk register:** `docs/architecture/WORLD_ATLAS_RISK_REGISTER.md`

## Global constraints

- `Oteryn-Game` remains canonical World/Content/gameplay-fact authority.
- `Oteryn-Atlas` remains the derived Atlas product and independent release/failure domain.
- Game→Atlas stays provider-owned, explicit, versioned, public-safe and artifact-first.
- META coordinates compatibility and sequencing; it never copies provider schemas or runtime source.
- No direct Atlas dependency on arbitrary Game-internal Rust crates.
- No big-bang rewrite. Every migrated Atlas capability is parity-first and separately reversible.
- Full embedded Atlas content is local/pinned/digest-bound; a remote public Atlas is not a gameplay dependency.
- Native gameplay minimap/HUD remains native and usable when embedded Atlas is unavailable.
- Private/live client state is local-session-only and never becomes a public Atlas publication input.
- The first bridge profile is non-authoritative UI integration only; no movement/combat/use/server-mutation commands.
- Every task resolves fresh protected `main`, instructions, Issues/PRs, branch protection, active path ownership and required checks before mutation.
- Every substantial new or resumed provider task packet must be validated against a freshly obtained GitHub snapshot with the canonical `ecosystem/agent-execution-routing-policy.json` and `tools/governance/agent_execution_routing.py` before local work or mutation is released. The validated packet must truthfully bind execution target/runner, equivalent CI, Remote Desktop disposition, lane ownership, branch/worktree, dependencies, leases/release conditions and integration order; missing or stale routing validation is a fail-closed dispatch blocker.
- Follow ADR 0004: immutable admission SHA, one task/branch/worktree/PR, no restart because `main` moved, late merge-up integration, exact-head proof.
- Shared Cargo/workspace files, shared app composition, shared Atlas FullWorld shell, workflow/CI files, release manifests and final integration are serialized leases.
- Current planning SHAs are provenance only: META `d79df968c1aba98373455399732fc71ab71e6a5d`, Game `2019d501d22614720ef37718e16913d81728e0a2`, Atlas `fc2a952169e15c070b4a2bc66095624d63798435`.
- Planning-time blockers/overlaps must be re-resolved, especially Game #187/#162 and Atlas #179/#162/#170/#185 or their successors.
- `WORLD_ATLAS_RISK_REGISTER.md` is a mandatory execution input, not closeout-only prose. Re-read it at provider design freeze, embedded-host selection, candidate freeze and final cutover. A triggered unresolved Critical risk blocks the dependent decision/cutover; a triggered High risk requires exact mitigation evidence before the dependent decision is accepted. Successful CI alone never closes an architectural/security/performance risk.
- No provider production/live deployment from this META planning lifecycle.

---

## 1. Programme lifecycle and authority map

| Scope | Lifecycle | Authority |
| --- | --- | --- |
| cross-repo architecture/programme | `Oteryn/Oteryn#75` | META coordination only |
| prompt/orchestration pack | `Oteryn/Oteryn#76` | META agent coordination |
| embedded bridge threat model | `Oteryn/Oteryn#77` | cross-product security acceptance envelope |
| cross-surface verification | `Oteryn/Oteryn#78` | composition of immutable provider evidence |
| release/cutover | `Oteryn/Oteryn#79` | cross-repo compatibility tuple/cutover coordination |
| performance/resource evidence | `Oteryn/Oteryn#80` | ecosystem comparison, provider benchmarks remain local |
| architecture packet validation | `Oteryn/Oteryn#81` | META planning packet proof |
| World Atlas Compatibility Record V1 | `Oteryn/Oteryn#84` | dedicated schema/validator/meta-gate mechanism |
| Game producer/client programme | `Oteryn/Oteryn-Game#191` | Game provider implementation |
| Atlas Rust/reuse programme | `Oteryn/Oteryn-Atlas#188` | Atlas provider implementation |

The coordinator may create additional provider child Issues only after a worker domain is dependency-ready and exact ownership is known. Do not create speculative runtime branches just to reserve work. Issue #84 is the sole lifecycle for the dedicated World Atlas compatibility-record mechanism; do not duplicate it.

## 2. Target product decomposition

### Game-owned producer/runtime side

Game owns canonical world/content/gameplay facts, the public Atlas export contract/profile/allowlist, deterministic producer/provenance, native gameplay minimap/HUD, client embedded-host integration, local live-state source/validation, bridge native endpoint and client packaging of an exact Atlas embedded bundle digest.

### Atlas-owned side

Atlas owns validated ingestion, the Rust derived core, spatial/search/query/index products, derived publication, Rust/WASM adapter where selected, existing web product UI/DOM/accessibility, reusable embedded-web bundle construction, embedded-mode bridge endpoint, and public Atlas deployment/release.

### META-owned side

META owns only architecture/sequencing, compatibility identity composition, immutable provider evidence references, the dedicated World Atlas compatibility record mechanism and final compatible release tuple. META does not copy provider schemas/runtime.

## 3. Compatibility identities

The programme preserves independent immutable identities for:

```text
game_atlas_export_profile_version
game_atlas_export_producer_revision
game_atlas_export_artifact_manifest_digest
game_atlas_export_payload_digest_or_root
game_world_content_revision
atlas_core_api_identity
atlas_web_embedded_bundle_version
atlas_web_embedded_bundle_digest
public_atlas_deployed_bundle_version
public_atlas_deployed_bundle_digest
public_atlas_bundle_relation_to_embedded
atlas_bridge_protocol_version
atlas_bridge_capability_profile
game_client_release_identity
public_atlas_release_or_deployment_identity
```

Rules:

- no floating branch/latest alias is a release identity;
- producer version, world revision and produced artifact digest are distinct;
- embedded bundle version and digest are distinct;
- public deployed bundle identity is distinct from client-embedded bundle identity because public Atlas can advance/rollback independently;
- bridge incompatibility disables the bridge/live overlay fail-closed;
- META records combinations, not provider schema copies.

## 4. Stable conceptual interfaces

### 4.1 Game → Atlas public artifact envelope

Must convey producer revision, export profile version, world/content revision, public capabilities, payload manifest, payload digests, provenance and minimum consumer requirements. It contains only Game-selected public-safe facts. Provider evidence must retain an immutable Game export-build/manifest identity proving that the recorded producer revision/profile/world revision produced the exact manifest and payload digests used by Atlas.

### 4.2 Atlas Core surface

Provider design freezes exact types/signatures for deterministic operations equivalent to:

```text
load_verified_public_artifact(...)
query_world(...)
query_spatial(...)
search(...)
resolve_entity(...)
resolve_map_location(...)
route_or_path_product(...)
capability_state(...)
```

Browser/DOM state is not a second authority inside the core.

### 4.3 Embedded bundle manifest

Must identify bundle version/digest, Atlas Core/API identity, supported Game export profiles, supported bridge range, required host capabilities, file/asset digests and security profile. Provider evidence must retain an immutable Atlas build/manifest identity binding the exact accepted Game manifest/payload digests plus Atlas Core/API identity to the exact embedded bundle version/digest.

### 4.4 Local bridge

Handshake semantically binds protocol version, capability profile, client release identity, Atlas bundle identity and world/content revision. Mismatch yields explicit incompatible/degraded state.

Client→Atlas V1 candidates are current player position/floor, route progress, privacy-approved party positions, locale presentation and separately accepted bounded quest context.

Atlas→Client V1 candidates are set/clear waypoint and validated focus coordinate/entity. No direct movement, attack, item use, arbitrary server command, filesystem/process API or credentials.

---

# 5. Execution DAG

```text
META architecture packet merge
        |
        v
Wave 0 read-only discovery (5 parallel scouts)
        |
        v
Wave 1 Game + Atlas provider design freeze
        |
        +-------------------+
        v                   v
Wave 2 Game foundations   Atlas Rust workspace foundation
        |                   |
        |            Wave 3 ingest/spatial/search
        |                   |
        |            Wave 4 WASM/web + bundle
        +---------+---------+
                  v
             Wave 5 client host + bridge
                  v
        Wave 6 security/perf/cross-surface E2E
                  v
        Wave 7 provider cutover + #84 V1 record
                  v
        independent closeout audit
                  v
        Wave 8 later legacy retirement
```

## Concurrency policy

Recommended maximum active reasoning/scout leads: **5**. Recommended mutation: **2–3 disjoint provider lanes**. Programme coordinator, Game/Atlas architecture leads, native host/bridge lead, security lead, final integrator and independent closeout auditor use Extra High reasoning; bounded implementation/parity workers use High unless their provider task requires stricter reasoning.

Root Cargo/workspace/composition/CI, Game client composition, Atlas shared FullWorld shell, META compatibility-record implementation and final release/cutover mutation are serialized leases. Heavy Atlas browser/Molehill qualification follows the current live slot policy.

---

# 6. Wave 0 — read-only discovery

Wave 0 begins only after this packet is canonical on protected META `main`. No provider runtime mutation.

### Task 0A — Game public export inventory

Repo: Game #191. Record exact current public Atlas products/versions, owning contracts/producer paths, public-safe capabilities/gaps, identity/revision fields, fixtures, possible public codec-crate value and active ownership conflicts. Do not invent fields or edit Cargo.

### Task 0B — Atlas Rust migration inventory

Repo: Atlas #188. Inventory relevant generators, `src/browser/**`, `web/**`, publication paths and tests. Classify material components as `KEEP_WEB_UI`, `KEEP_JS_GLUE`, `MIGRATE_RUST_CLI`, `MIGRATE_RUST_CORE`, `MIGRATE_RUST_WASM_CANDIDATE`, `WAIT_FOR_BENCHMARK` or `DO_NOT_MIGRATE`. Record exact parity oracles, interfaces and shared leases.

### Task 0C — native client host feasibility

Repo: Game #191. Identify the client composition boundary and realistic embedded-host candidates. Record local-origin support, navigation controls, CSP/resource controls, JS↔native messaging, crash isolation, packaging, input/focus/accessibility, offline behavior and benchmark/security matrix. Do not select a host from preference alone.

### Task 0D — security/privacy discovery

Lifecycle #77. Threat model malicious/corrupt bundle, XSS, arbitrary navigation, bridge spoof/replay/flood/oversize, privilege escalation, credential leakage, private-state publication/log leakage, stale/incompatible artifacts, host crash/hang/resource exhaustion and dependency compromise.

### Task 0E — verification/performance baseline

Lifecycle #78/#80. Record exact current Atlas and Game verification gates, representative full-world fixtures, cross-surface journey oracles, constrained runner resources and benchmark evidence format.

### Wave 0 gate

Review all five handoffs. Freeze exact contract conflicts, ownership, host candidates, migration priority and decision blockers before provider design mutation.

---

# 7. Wave 1 — provider design freeze

Game and Atlas design lanes may run concurrently because repositories differ.

Before either provider design is accepted as frozen, re-read `WORLD_ATLAS_RISK_REGISTER.md` against the exact design evidence. Record immutable dispositions for every triggered High/Critical risk. Any triggered unresolved Critical risk blocks provider design freeze; a triggered High risk requires exact mitigation evidence before acceptance.

### Task 1A — Game producer + client design

Create provider-owned design/plan under Game #191. Define exact export identities/gaps, client host adapter, native minimap independence, bridge API/capability profile, packaging of exact embedded bundle digest, failure behavior, dependency direction, tests and shared Cargo/client composition leases. Reconcile the live Game coordinator and any durability/client ownership blocker first.

### Task 1B — Atlas Rust Core + reusable bundle design

Create provider-owned design/plan under Atlas #188. Define Rust workspace/crates, pure-core dependency direction, Game export consumer boundary, legacy parity seams, Core/WASM APIs, embedded bundle manifest, bridge web endpoint, Production UI Shell integration, rollback/capability flags, tests and shared FullWorld/workflow leases. Reconcile live #179/#162/#170/#185 successors first.

### Task 1C — security profile freeze

Under #77 define trusted origin, network/navigation/CSP policy, native capability allowlist, message framing/version/size/rate validation, privacy/retention, crash/restart behavior, supply-chain policy and negative tests. Reject any host that cannot meet the profile.

---

# 8. Wave 2 — foundations

### Task 2A — Atlas Rust workspace/core foundation

Serialized Atlas root workspace/dependency/CI lease. Deliver toolchain/workspace policy, pure core/model crates, deterministic errors, bounded resource-limit surface, Rust unit/property tests and CI/lint/security checks without cutting over production capabilities.

### Task 2B — Game export gap implementation

Run only when Wave 0/1 proves a concrete gap. Deliver Game-owned profile/schema evolution, deterministic producer changes, compatibility/negative tests, immutable export-build/manifest evidence binding producer/profile/world inputs to exact output digests, and exact fixture/publication evidence. If no gap, record `NO_CHANGE_REQUIRED`; no cosmetic branch.

### Task 2C — embedded host prototype

Prototype realistic host candidates in isolated Game paths and measure local content, navigation isolation, startup, RSS/CPU/GPU, input/focus, crash/hang isolation, offline operation, packaging and dependency/license security. Before selecting/promoting a host, re-read `WORLD_ATLAS_RISK_REGISTER.md`, record exact triggered-risk dispositions, block selection on any triggered unresolved Critical risk and require exact mitigation evidence for every triggered High risk affecting host acceptance. Select only a host satisfying the frozen security/product criteria.

---

# 9. Wave 3 — Atlas Core capability lanes

After root workspace/core interfaces are canonical, up to three disjoint Atlas lanes may run concurrently:

### Task 3A — verified ingestion/compiler/index parity

RED→GREEN tests for accepted Game input, malformed/oversized/incompatible rejection, deterministic repeated build, logical/byte parity where promised, provenance/digest continuity and wall-time/RSS/output benchmark. Keep legacy generator as rollback/shadow comparator.

### Task 3B — spatial/query core

Test coordinates/floors/bounds, overflow rejection, deterministic ordering, current-oracle parity, property invariants and large-world performance. No DOM/WebGL edits.

### Task 3C — search/intelligence core

Test stable normalization/results, public authority preservation, truthful missing/partial capabilities, parity with accepted search journeys and resource performance. Never invent canonical gameplay facts.

Each lane merges through normal Atlas protected lifecycle; workers never share one writable integration branch.

---

# 10. Wave 4 — Web/WASM and reusable bundle

### Task 4A — WASM adapter

Expose stable Core behavior through bounded serialization/error mapping. Keep browser DOM/accessibility in web technology and collect startup/payload/runtime evidence.

### Task 4B — capability-level shadow/cutover

For every migrated capability compare current and Rust/WASM paths on the same fixtures/actions, promote failures to regressions, cut over only after parity/performance/browser proof and retain rollback until separate removal gate.

### Task 4C — web/embedded bundle V1

Produce deterministic local static bundle with manifest, exact Core/export/bridge identities, file digests, public/embedded modes without codebase duplication, default-deny embedded remote navigation and a bridge endpoint disabled in public mode. Retain immutable build/manifest evidence proving the exact accepted Game export digests and exact Atlas Core/API identity that produced the exact embedded bundle version/digest.

---

# 11. Wave 5 — native client integration

Starts after host acceptance and immutable Atlas bundle candidate.

### Task 5A — Game host production adapter

Load only the pinned local embedded bundle, expose open/close/degraded UI, clean resources, contain failure to Atlas capability and keep gameplay/native minimap usable.

### Task 5B — Game local bridge endpoint

Implement version/capability handshake, allowlisted events/intents, source/size/rate validation, mismatch/reconnect behavior, privacy-safe diagnostics, no credentials and no gameplay/server mutation commands.

### Task 5C — Atlas embedded-mode bridge endpoint

Keep local state ephemeral, validate intents/messages, perform no public publication writes and keep bridge code unavailable in public mode.

### Task 5D — native minimap/waypoint interop

Integrate only narrow local UX semantics such as a validated Atlas waypoint; native minimap remains native Rust/wgpu.

---

# 12. Wave 6 — qualification

Before the candidate freeze is accepted as qualification authority, re-read `WORLD_ATLAS_RISK_REGISTER.md` against the exact candidate heads/artifact digests and current evidence. Record immutable dispositions for every triggered High/Critical risk. A triggered unresolved Critical risk blocks candidate-freeze acceptance; a triggered High risk requires exact mitigation evidence. CI success alone is not risk closure.

Freeze exact candidate heads/artifact digests before expensive qualification. Code/config changes require a new freeze and reapplication of the risk checkpoint.

### Task 6A — security

Lifecycle #77. Prove trusted local origin, default-deny navigation/network, CSP/resource restrictions, bridge validation/limits/allowlist, forbidden command rejection, no secret exposure, no private-state publication leakage, malicious bundle handling, host isolation and dependency posture. Independent reviewer required.

### Task 6B — performance/resources

Lifecycle #80. Record exact machine/profile and compare current/Rust generators, selected JS/WASM hot paths, bundle startup/payload, embedded host RSS/CPU/GPU/input, large-world paths and native minimap unaffected baseline.

### Task 6C — cross-surface E2E

Lifecycle #78. On compatible immutable world/export evidence prove same public entity facts/location/floor/camera semantics, route/waypoint where supported, embedded local state only in client mode, public no-private-state behavior, host failure/minimap independence and negative bridge/export/bundle cases.

---

# 13. Wave 7 — release compatibility and cutover

**Lifecycle:** META #79 + #84 + `docs/architecture/WORLD_ATLAS_RELEASE_COMPATIBILITY_CONTRACT.md`.

Before Task 7A or terminal compatibility-record creation, execute the final-cutover risk checkpoint: re-read `WORLD_ATLAS_RISK_REGISTER.md`, record immutable dispositions for every triggered High/Critical risk, and stop cutover while any triggered unresolved Critical risk remains. Triggered High risks require exact mitigation evidence before the dependent cutover decision; successful checks alone do not close them.

### Task 7A — freeze pre-cutover candidate identities

This is a **candidate-only freeze**, not the terminal compatibility tuple. Freeze only identities and evidence that already exist before provider merge/deployment:

```text
Game export profile/version + producer revision
Game world/content revision
Game export-build/manifest evidence binding those inputs to exact produced manifest/payload digests
Game produced export manifest digest + payload digest/root
Atlas Core/API identity
Atlas accepted Game manifest/payload digests
Atlas embedded-bundle build/manifest evidence binding accepted digests + Core identity to exact bundle
embedded bundle version + digest
bridge protocol/profile
Game client candidate identity + pinned embedded bundle digest
separate Game/Atlas provider required-check refs
separate Game/Atlas provider review-evidence refs
security/performance/cross-surface/rollback evidence refs available at candidate freeze
```

Do **not** freeze `public_atlas_deployed_bundle_version`, `public_atlas_deployed_bundle_digest`, `public_atlas_release_or_deployment_identity`, final `public_atlas_bundle_relation_to_embedded`, or immutable public deployment-to-bundle evidence in Task 7A. Those terminal identities do not exist until the merged-main public deployment/live acceptance in Task 7C. Any earlier deployment values are historical evidence only and must not be carried forward as the final tuple.

No candidate identity contains a floating ref.

### Task 7B — provider final integration

Each provider independently refreshes current protected `main`, merge-ups normally, reviews the complete diff, reruns invalidated exact-head tests, obtains required review, protected-squash-merges and verifies resulting main/post-merge checks.

### Task 7C — public Atlas cutover

Atlas follows its normal merged-main deployment/live acceptance. Record exact deployed revision, exact deployed public bundle version/digest, immutable evidence binding the deployment to that digest, the declared relation to the client-embedded bundle and rollback artifact. If the public deployment intentionally uses a different but compatible bundle, prove compatibility using provider evidence defined by the release contract.

### Task 7D — native client candidate acceptance

Game runs provider-owned native-client acceptance against the exact embedded bundle digest. Prove offline/local startup, bridge behavior and native minimap fallback.

### Task 7E — terminal tuple refreeze + dedicated META World Atlas Compatibility Record V1

1. Refresh/reconcile existing lifecycle `Oteryn/Oteryn#84`; do not create a duplicate compatibility schema/validator task.
2. Require #84 to have protected-merged the dedicated mechanism:
   - `ecosystem/world-atlas/compatibility.schema.json`;
   - `tools/governance/validate_world_atlas_compatibility.py`;
   - deterministic positive/negative validator regressions;
   - integration into stable `meta-gate`.
3. If that mechanism is not canonical, return `WAITING_EXTERNAL: WORLD_ATLAS_COMPATIBILITY_RECORD_MECHANISM_NOT_CANONICAL` for Task 7E while other dependency-ready work may continue.
4. **After Tasks 7B–7D are complete, perform a mandatory terminal refreeze** that supersedes Task 7A for release authority. It must bind the exact final provider main/release identities; immutable Game export-build evidence; exact produced and Atlas-accepted Game manifest/payload digests; Atlas Core/API identity; immutable Atlas embedded-bundle build evidence; exact embedded bundle version/digest; exact public deployment identity; exact public deployed bundle version/digest; immutable deployment-to-bundle evidence; final `SAME_BUNDLE` or `COMPATIBLE_INDEPENDENT` relation; Game client identity/pinned embedded digest; separate Game/Atlas provider required-check refs; and separate Game/Atlas provider review-evidence refs.
5. Create the final record only at `ecosystem/world-atlas/releases/<release_id>.json` from that terminal refreeze using the separately typed identities required by the release contract. Generic `ecosystem/releases/*.json`, Issue comments, Markdown tables or opaque fields are not substitutes.
6. Validate exact cross-links: Game producer/profile/world inputs == Game export-build evidence == produced Game manifest/payload digests; produced Game export == Atlas accepted export; Atlas accepted export + Core identity == Atlas embedded-bundle build evidence == embedded bundle; Game client pinned digest == embedded bundle digest; and public deployment identity is bound to its exact public deployed bundle under the declared `SAME_BUNDLE` or `COMPATIBLE_INDEPENDENT` mode.
7. Deliver the final record through a dedicated META PR with exact head, current required checks/review and `meta-gate` validation.
8. Protected-squash-merge the record, read it back from the exact merge SHA and require post-merge `meta-gate` success on that exact protected-main SHA.

Task 7E is not complete merely because #79 contains a candidate tuple or a compatibility PR exists. A terminal refreeze after public deployment/live acceptance is mandatory.

---

# 14. Wave 8 — legacy path retirement

Legacy Python/JS computational paths are not removed during first Rust implementation unless their exact removal gate is already satisfied. Separate Atlas cleanup PRs require the Rust path to be accepted default, parity/browser/live acceptance, documented rollback, zero active consumers, acceptable performance/security evidence and bounded diff review.

---

# 15. Rollback matrix

| Failure | Rollback/fallback |
| --- | --- |
| Rust compiler/index regression | capability-level previous accepted generator until removal gate |
| WASM adapter failure | retained compatible JS/current path for that capability |
| public Atlas deployment regression | Atlas deployment rollback to prior exact accepted public bundle/deployment pair |
| embedded Atlas bundle incompatible/corrupt | disable panel or repin prior compatible bundle in a new client candidate; native minimap remains |
| bridge mismatch/failure | disable live overlay/native intents; no guessed compatibility |
| embedded host crash/hang | tear down/disable host; gameplay/native minimap remains |
| private-state leak | fail release, disable bridge profile, sanitize evidence/logging, security requalification |
| Game export incompatibility | Atlas rejects/marks unavailable; no legacy-runtime truth fallback |
| bad META compatibility record | keep prior canonical record; do not report DONE until corrected record is reviewed, merged and post-merge validated |

---

# 16. Definition of Done

The programme is not `DONE` until immutable evidence proves all of the following:

- ADR 0005 and this programme packet are canonical on protected META main.
- Required Game #191 and Atlas #188 children are terminal or evidence-backed `NO_CHANGE_REQUIRED`.
- Game remains sole canonical world/content/gameplay authority.
- Atlas Rust Core is real, tested and owns accepted derived capabilities without arbitrary Game-internal dependencies.
- Migrated capabilities have parity, bounded resource and rollback evidence.
- Public and embedded Atlas use the accepted shared Core/bundle architecture.
- Native client opens a locally packaged Atlas without remote dependency; native minimap remains independent.
- Bridge is versioned/default-deny/security-qualified and private state remains local-only.
- Cross-surface user and failure journeys pass.
- Exact performance/resource evidence exists for migrated paths and selected host.
- Every substantial provider task packet that required routing validation has fresh, passing execution-routing evidence before local work/mutation.
- Provider exact-head/protected-main checks and reviews are green, with separate immutable Game and Atlas required-check and review evidence.
- Every triggered risk has the disposition/evidence required by `WORLD_ATLAS_RISK_REGISTER.md`, with no unresolved cutover-blocking risk.
- Immutable Game export-build evidence binds the recorded producer/profile/world revision to the exact produced manifest/payload digests.
- Immutable Atlas embedded-bundle build evidence binds the exact accepted Game digests and Atlas Core/API identity to the exact embedded bundle version/digest.
- Public Atlas live acceptance binds the named public deployment to its exact deployed bundle version/digest.
- Native client acceptance binds the client identity to its exact embedded bundle digest.
- When public and embedded bundles differ, their relation is explicitly `COMPATIBLE_INDEPENDENT` with immutable compatibility evidence; otherwise it is `SAME_BUNDLE` with digest equality.
- #84 dedicated V1 schema/validator/meta-gate mechanism is canonical.
- Final World Atlas compatibility record is created only from the mandatory post-deployment terminal refreeze, preserves Game export-build evidence, Atlas embedded-bundle build evidence, separate Game/Atlas required-check and review evidence, is exact-head reviewed/gated, protected-squash-merged, read back and post-merge `meta-gate` validated.
- A fresh independent `OTERYN-WORLD-ATLAS-CLOSEOUT-AUDITOR` returns `FINAL_VERDICT: DONE` with complete immutable evidence.
- Legacy paths are retained or removed truthfully according to their own removal gates.
- No unresolved security, authority, provenance or compatibility conflict is hidden as PASS.

# 17. Coordinator completion report

The final coordinator returns:

- parent/child Issue numbers and terminal states;
- META architecture merge SHA;
- exact Game and Atlas final main SHAs;
- exact provider PRs/merge SHAs;
- separate immutable Game and Atlas provider exact-head required-check refs and review evidence refs;
- Game export profile/version, producer revision, world/content revision, exact produced manifest/payload digests and immutable Game export-build evidence ref;
- Atlas Core/API identity, exact accepted Game manifest/payload digests, exact embedded bundle version/digest and immutable Atlas embedded-bundle build evidence ref;
- exact public deployed bundle version/digest and relation to embedded;
- immutable public deployment-to-bundle evidence;
- bridge protocol/profile;
- Game client identity pinning the embedded bundle;
- public Atlas deployment identity;
- execution-routing validation refs for substantial provider lanes;
- #84 schema/validator paths and final compatibility record path/PR/head/merge/post-merge-gate refs;
- verification/security/performance evidence references;
- rollback evidence;
- risk-register disposition evidence;
- deliberately retained legacy paths and reasons;
- independent closeout auditor verdict;
- final verdict `DONE`, `WAITING_EXTERNAL`, `BLOCKED`, or `STALLED` with exact material reason.
