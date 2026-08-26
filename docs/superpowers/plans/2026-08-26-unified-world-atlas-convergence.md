# Unified Oteryn World Atlas Convergence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use an isolated task/worktree workflow and execute this plan task-by-task. Parallel workers are allowed only where the dependency/ownership table explicitly permits them.

**Goal:** Evolve Oteryn World Atlas into one reusable product capability: Game-owned authoritative exports feed an Atlas-owned Rust Core and one web product bundle that serves both the public Atlas and a locally embedded native-client Atlas, while the gameplay minimap remains native Rust/wgpu and private live state stays local.

**Architecture:** Game remains canonical World/Content/gameplay authority and publishes explicit versioned public-safe Atlas artifacts. Atlas introduces a strangler-migrated Rust computational core, compiles a reusable web/WASM bundle, and keeps web UI ownership in the browser stack. The Game client embeds a pinned local Atlas bundle through a security-bounded host/bridge while retaining an independent native minimap/HUD.

**Tech Stack:** Rust 2024 in Game; Rust for new Atlas Core; WASM for browser reuse where accepted; existing Atlas JS/HTML/CSS/WebGL/Playwright during migration; existing Game wgpu/native client; immutable provider artifacts/digests; GitHub protected-branch lifecycle.

**Spec:** `docs/architecture/adr/0005-unified-world-atlas-surfaces-and-reuse.md`

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
- Follow ADR 0004: immutable admission SHA, one task/branch/worktree/PR, no restart because `main` moved, late merge-up integration, exact-head proof.
- Shared Cargo/workspace files, shared app composition, shared Atlas FullWorld shell, workflow/CI files, release manifests and final integration are serialized leases.
- Current planning SHAs are provenance only: META `d79df968c1aba98373455399732fc71ab71e6a5d`, Game `2019d501d22614720ef37718e16913d81728e0a2`, Atlas `fc2a952169e15c070b4a2bc66095624d63798435`.
- Planning-time blockers/overlaps must be re-resolved, especially Game #187/#162 and Atlas #179/#162/#170/#185.
- No provider production/live deployment from this META plan.

---

## 1. Programme lifecycle and authority map

### Parent and provider lifecycles

| Scope | Lifecycle | Authority |
| --- | --- | --- |
| cross-repo architecture/programme | `Oteryn/Oteryn#75` | META coordination only |
| prompt/orchestration pack | `Oteryn/Oteryn#76` | META agent coordination |
| embedded bridge threat model | `Oteryn/Oteryn#77` | cross-product security acceptance envelope |
| cross-surface verification | `Oteryn/Oteryn#78` | composition of immutable provider evidence |
| release/cutover | `Oteryn/Oteryn#79` | cross-repo compatibility tuple/cutover coordination |
| performance/resource evidence | `Oteryn/Oteryn#80` | ecosystem comparison, provider benchmarks remain local |
| architecture packet validation | `Oteryn/Oteryn#81` | META planning packet proof |
| Game producer/client programme | `Oteryn/Oteryn-Game#191` | Game provider implementation |
| Atlas Rust/reuse programme | `Oteryn/Oteryn-Atlas#188` | Atlas provider implementation |

The coordinator may create additional provider child Issues only after a worker domain is dependency-ready and exact ownership is known. Do not create speculative runtime branches just to reserve work.

## 2. Target product decomposition

### Game-owned producer/runtime side

Game owns:

- canonical world/content and gameplay facts;
- public Atlas export contract/profile/allowlist;
- deterministic producer and provenance;
- native gameplay minimap/HUD;
- client embedded-host integration;
- local live-state source and validation;
- bridge native endpoint and client-side command validation;
- client packaging of an exact Atlas bundle identity.

### Atlas-owned side

Atlas owns:

- validated consumer ingestion;
- Rust derived core;
- Atlas spatial/search/query/index products;
- derived publication;
- Rust/WASM adapter where selected;
- existing web product UI/DOM/accessibility;
- Atlas embedded-web bundle construction;
- browser/embedded-mode Atlas endpoint for the bridge;
- public Atlas deployment/release.

### META-owned side

META owns only:

- ADR and sequencing;
- cross-repo compatibility identity composition;
- immutable provider evidence references;
- final compatible release tuple;
- cross-repo agent orchestration policy.

## 3. Compatibility identities to establish

Provider child plans must define exact field/schema representation, but the programme must preserve independent identities for:

```text
game_atlas_export_profile_version
game_world_content_revision
atlas_core_api_version
atlas_web_embedded_bundle_version
atlas_web_embedded_bundle_digest
atlas_bridge_protocol_version
atlas_bridge_capability_profile
game_client_release_identity
public_atlas_release_identity
```

Rules:

- no floating branch is a release identity;
- a producer schema/version is not the same identity as a world/content revision;
- an Atlas bundle version is not the same identity as its exact digest;
- bridge incompatibility disables the bridge/live overlay fail-closed;
- static embedded Atlas may remain usable only when its own bundle/export compatibility is valid;
- META records combinations but not provider schema copies.

## 4. Stable conceptual interfaces

These are cross-lane conceptual contracts. Provider specs may choose wire syntax and exact Rust/JS type names, but must preserve semantics.

### 4.1 Game → Atlas public artifact envelope

Must convey:

```text
producer_revision
export_profile_version
world_content_revision
public_capabilities
payload_manifest
payload_digests
provenance
minimum_consumer_requirements
```

It contains only public-safe facts selected by Game.

### 4.2 Atlas Core surface

The core exposes deterministic derived operations equivalent to:

```text
load_verified_public_artifact(...)
query_world(...)
query_spatial(...)
search(...)
resolve_entity(...)
resolve_map_location(...)
route_or_path_product(...)   # only where Atlas owns the derived product
capability_state(...)
```

Exact APIs are frozen by the Atlas provider spec before implementation. Browser/UI state is not stored as an ad-hoc second authority inside the core.

### 4.3 Embedded bundle manifest

Must identify:

```text
bundle_version
bundle_digest/source_revision
atlas_core_api_identity
supported_export_profiles
supported_bridge_protocol_range
required_host_capabilities
asset/file digests
security profile
```

### 4.4 Local bridge handshake

Semantically:

```text
HostHello {
  protocol_version,
  capability_profile,
  client_release_identity,
  atlas_bundle_identity,
  world_content_revision
}

AtlasHello {
  protocol_version,
  requested_capabilities,
  atlas_bundle_identity
}
```

A mismatch returns an explicit incompatible/degraded state; it never guesses.

### 4.5 Client → Atlas event profile v1

Allowlist candidates, each separately capability-gated:

```text
player_position
current_floor
route_progress
party_positions       # only after privacy/product acceptance
locale_presentation
bounded_quest_context # only after separate acceptance
```

### 4.6 Atlas → Client command profile v1

Allowlist candidates:

```text
set_waypoint
clear_waypoint
focus_coordinate
focus_entity_reference
```

No direct movement, attack, item use, arbitrary server command, filesystem/process API or credential access is allowed.

---

# 5. Execution DAG

```text
META ADR/plan merge
        │
        ▼
WAVE 0 read-only parallel discovery
 A Game contract   B Atlas inventory   C Client host   D Security   E Verification
        │                 │                 │              │             │
        └────────────┬────┴────────────┬────┴───────┬──────┴─────────────┘
                     ▼                 ▼            ▼
             Game provider spec   Atlas Core spec  Security/test freeze
                     │                 │            │
                     └───────┬─────────┴─────┬──────┘
                             ▼               ▼
                    Game export/client   Atlas Rust workspace
                       foundations         foundation
                             │               │
                             │        ┌──────┼──────────┐
                             │        ▼      ▼          ▼
                             │      ingest  spatial   search/query
                             │        └──────┼──────────┘
                             │               ▼
                             │          WASM/web adapter
                             │               │
                             ▼               ▼
                     client host spike   embedded bundle v1
                             │               │
                             └───────┬───────┘
                                     ▼
                              local bridge v1
                                     │
                                     ▼
                           client embedded integration
                                     │
                          ┌──────────┼──────────┐
                          ▼          ▼          ▼
                       security   perf       cross-surface E2E
                          └──────────┼──────────┘
                                     ▼
                             compatibility/cutover
                                     │
                                     ▼
                         later legacy-path removal
```

## Concurrency policy

### Reasoning lanes

Recommended maximum active reasoning leads: **5**.

Recommended effort:

| Role | Effort |
| --- | --- |
| programme coordinator | Extra High |
| Game contract/producer lead | Extra High |
| Atlas Core architecture lead | Extra High |
| native client host/bridge lead | Extra High |
| security lead | Extra High |
| verification/performance lead | Extra High for design, High for bounded implementation |
| bounded crate implementation workers | High |
| deterministic fixture/parity workers | High |
| final cross-repo integrator | Extra High |
| independent closeout auditor | Extra High |

### Mutating lanes

Normal limit: **2–3 provider-mutating workers concurrently**, only on disjoint paths/branches. More requires explicit live proof of disjoint ownership and no shared constrained runner/resource.

Read-only scouts/reviewers may run concurrently without a branch.

Within a provider repo, root Cargo/workspace/composition/CI leases are serial. Cross-repository Game and Atlas work may run concurrently when their provider-local leases are disjoint and no contract dependency is unresolved.

Heavy Atlas real-browser/Molehill qualification must obey the current live slot policy; this plan does not invent parallel heavy capacity.

---

# 6. Wave 0 — read-only discovery and interface evidence

Wave 0 may begin only after ADR 0005 and this plan are canonical on protected META `main`. Workers do not mutate provider runtime.

## Task 0A — Game public export compatibility inventory

**Repo:** `Oteryn/Oteryn-Game`

**Lifecycle:** umbrella #191; coordinator creates a bounded child Issue if needed.

**Read:** current Game architecture/contracts/export producer, current Atlas-export related Issues/PRs, current client workspace/dependency map.

**Produce handoff:**

- exact current public Atlas export products and versions;
- exact owning files/contracts;
- which Atlas-required facts are already public-safe versus missing;
- whether a dedicated provider-owned public Rust codec crate has concrete value or should remain artifact/schema-only;
- incompatibility/versioning risks;
- recommended minimal Game changes, if any;
- exact active path ownership conflicts.

**Do not:** edit Cargo/workspace, invent new schema fields or implement Atlas derived logic.

**Exit:** self-contained evidence packet sufficient for the Game provider design task.

## Task 0B — Atlas Rust migration inventory

**Repo:** `Oteryn/Oteryn-Atlas`

**Read:** current `tools/**`, `src/browser/**`, `web/**`, tests, publication path, verification docs and active PR ownership.

**Produce handoff:** classify each meaningful computational component as:

```text
KEEP_WEB_UI
KEEP_JS_GLUE
MIGRATE_RUST_CLI
MIGRATE_RUST_CORE
MIGRATE_RUST_WASM_CANDIDATE
WAIT_FOR_BENCHMARK
DO_NOT_MIGRATE
```

For each migration candidate record:

- current exact file(s);
- input/output contract;
- current tests/fixtures;
- determinism requirement;
- performance/resource profile if known;
- overlap with active work;
- proposed Atlas crate ownership.

**Exit:** no unclassified high-impact generator/index/search/spatial path relevant to the programme.

## Task 0C — native client embedded-host feasibility inventory

**Repo:** `Oteryn/Oteryn-Game`

**Read:** current client runtime, renderer/windowing boundaries, packaging, security assumptions and supported platform profile.

**Produce handoff:**

- exact client surface where full Atlas could be hosted without coupling gameplay renderer to browser state;
- realistic embedded-host candidates available to the supported platform;
- required dependencies/package footprint;
- local-asset/custom-origin capabilities;
- crash/hang isolation options;
- input/focus/accessibility implications;
- offline behavior;
- required client composition leases;
- prototype acceptance matrix.

**Do not select a host from familiarity alone.** Selection is evidence-gated.

## Task 0D — security/privacy threat model discovery

**Lifecycle:** META #77 with provider read-only inspection.

**Produce:** assets, trust boundaries, abuse cases, default-deny bridge capabilities, private-state handling, CSP/origin/navigation requirements, supply-chain risks and negative-test requirements.

Threats must include at least:

- malicious/compromised embedded bundle;
- XSS/script injection in Atlas data/UI;
- arbitrary navigation/origin confusion;
- bridge message spoof/replay/flood/oversize;
- privilege escalation from web surface to native APIs;
- credential/session leakage;
- private live-state publication/log leakage;
- stale/incompatible bundle/export;
- host crash/hang/resource exhaustion;
- dependency/update compromise.

## Task 0E — verification/performance baseline inventory

**Lifecycle:** META #78/#80 with provider test ownership preserved.

**Produce:**

- exact current Atlas deterministic/browser/E2E/performance gates;
- exact current Game Rust/native-client test gates;
- representative full-world fixtures suitable for parity benchmarking;
- cross-surface user-journey oracle set;
- current constrained runner resources/serialization needs;
- benchmark collection format and sanitization rules.

### Wave 0 integration gate

The coordinator reviews all five handoffs and records:

- contract conflicts;
- unresolved provider ownership;
- exact recommended spec interfaces;
- host candidates worth prototyping;
- migration priority;
- risks requiring owner/security decision.

No runtime implementation begins until the affected provider spec is merged or explicitly accepted under provider governance.

---

# 7. Wave 1 — provider design/spec freeze

Two provider design lanes may run concurrently because they live in different repositories.

## Task 1A — Game producer + native-client integration design

**Repo:** `Oteryn/Oteryn-Game`

**Preferred design path:** `docs/architecture/WORLD_ATLAS_GAME_PRODUCER_AND_CLIENT_BOUNDARY.md`

**Preferred implementation plan path:** `docs/superpowers/plans/2026-08-26-world-atlas-game-integration.md`

**Must define:**

- exact existing/new Game-owned public export contract identities;
- minimum producer changes and compatibility policy;
- exact client host adapter boundary;
- native minimap independence invariant;
- local bridge native endpoint API and capability profile;
- client packaging model for an exact Atlas bundle digest;
- failure/degraded behavior;
- dependency direction and crate candidates;
- TDD/negative/native integration tests;
- shared Cargo/client-composition lease points;
- exact implementation child Issues and branch order.

**Hard gate:** must reconcile current Game coordinator/durability/client allocations before mutation. If shared client paths are not available, design may merge but runtime child lanes remain `WAITING_EXTERNAL`.

## Task 1B — Atlas Rust Core + reusable bundle design

**Repo:** `Oteryn/Oteryn-Atlas`

**Preferred design path:** `docs/superpowers/specs/2026-08-26-atlas-rust-core-and-embedded-bundle-design.md`

**Preferred implementation plan path:** `docs/superpowers/plans/2026-08-26-atlas-rust-core-and-embedded-bundle.md`

**Must define:**

- exact Rust workspace/crate layout;
- dependency rules that keep core platform-neutral;
- exact Game public export consumer boundary;
- legacy Python/JS parity seams;
- core API types/signatures;
- WASM adapter API and JS compatibility wrapper;
- embedded bundle manifest/build layout;
- embedded-mode bridge web endpoint;
- public web shell integration without replacing Production UI Shell V1;
- feature/capability flags and rollback seams;
- Rust/Node/browser tests and performance gates;
- exact shared FullWorld/workflow leases and implementation child Issues.

**Hard gate:** reconcile current #179/#162/#170/Production UI Shell shared-path ownership before any runtime/UI branch.

## Task 1C — security profile freeze

**Lifecycle:** META #77 plus provider-local security specs/tests.

Before host/bridge implementation, accept a bridge/security profile containing:

- trusted embedded origin model;
- navigation/network policy;
- CSP/resource policy;
- native capability allowlist;
- message framing/versioning/validation/size/rate limits;
- privacy/state retention policy;
- crash/restart behavior;
- supply-chain/update policy;
- required negative tests.

If the selected host cannot satisfy the profile, reject the host rather than weakening the profile silently.

---

# 8. Wave 2 — foundations

Game and Atlas foundation work may run in parallel after their provider specs are accepted and live ownership permits it.

## Task 2A — Atlas Rust workspace/core foundation

**Repo:** Atlas

**Serialized lease:** root workspace/dependency/toolchain/CI introduction.

**Deliver:**

- accepted Rust toolchain/workspace policy;
- pure core/model crate(s);
- deterministic error/result model;
- resource-limit configuration surface;
- Rust unit/property tests;
- CI/lint/security dependency checks integrated without weakening existing JS/Python/browser gates;
- no production capability cutover yet.

**RED/GREEN principle:** first failing contract test demonstrates the minimal core interface is absent; foundation then makes it pass.

**Exit:** later independent Atlas crate lanes can build/test without editing root workspace configuration.

## Task 2B — Game export/contract gap implementation

**Repo:** Game

Run only when Wave 0/1 proves a concrete gap. If current public export is sufficient, record `NO_CHANGE_REQUIRED` with exact evidence and do not create a no-op implementation branch.

**Deliver when required:**

- provider-owned schema/profile evolution;
- deterministic exporter changes;
- compatibility/negative tests;
- exact fixture/publication evidence for Atlas consumers;
- no Atlas-derived search/index logic.

## Task 2C — client host prototype foundation

**Repo:** Game

Prototype realistic host candidates on isolated branches/fixtures, not in production client composition first.

Measure:

- local static content loading;
- navigation/origin restriction;
- startup latency;
- idle/active RSS;
- GPU/process footprint;
- keyboard/mouse/focus behavior;
- crash/hang isolation;
- offline operation;
- packaging/runtime availability;
- dependency/license/security posture.

**Exit decision:** select one host only if it satisfies mandatory security and product criteria. Otherwise record `HOST_NOT_ACCEPTED` and return to architecture rather than forcing embedded delivery.

---

# 9. Wave 3 — Atlas Core capability lanes

After Task 2A freezes root workspace and shared core interfaces, Atlas may run up to three disjoint implementation lanes concurrently. Each lane owns separate crates/tests and must not edit shared web shell/CI files.

## Task 3A — verified ingestion + compiler/index parity

**Target responsibility:** migrate representative high-value Python generation/index work into Rust CLI/core.

**Tests:**

- accepted Game fixture parses/validates;
- malformed/oversized/incompatible inputs fail closed;
- deterministic repeated build;
- canonical logical output parity with current accepted generator;
- provenance/digest continuity;
- benchmark wall time/RSS/output size.

Keep legacy generator available as rollback/shadow comparator.

## Task 3B — spatial/query core

**Target responsibility:** spatial indexes, world-location queries, floor/region/chunk resolution and other Atlas-owned pure spatial primitives.

**Tests:**

- coordinate/floor/bounds edge cases;
- overflow/out-of-range rejection;
- deterministic query ordering where promised;
- parity against current browser/Python oracle fixtures;
- property tests for transform/query invariants;
- large-world benchmark.

No WebGL/DOM edits in this lane.

## Task 3C — search/intelligence core

**Target responsibility:** deterministic Atlas-owned search/index/ranking primitives that benefit from shared core execution.

**Tests:**

- stable query normalization/results under fixed fixture;
- public-fact authority preserved;
- missing/partial capability remains truthful;
- parity with current accepted search journeys;
- performance/memory benchmark;
- no invented canonical gameplay facts.

### Wave 3 integration

Atlas provider integrator merge-refreshes each completed lane separately and reruns invalidated exact-head gates. Do not create one shared writable integration branch for active workers.

---

# 10. Wave 4 — Web/WASM and embedded bundle

## Task 4A — Atlas WASM adapter

**Dependency:** stable core APIs from required Wave 3 lanes.

**Deliver:**

- wasm-bindgen/equivalent provider-approved boundary;
- bounded serialization between JS and WASM;
- async/error mapping that preserves truthful capability state;
- compatibility wrapper so existing web UI does not need a simultaneous rewrite;
- unit/browser tests;
- startup/payload/runtime performance evidence.

Do not move trivial DOM glue into WASM.

## Task 4B — capability-level shadow/cutover adapters

For each migrated capability:

1. run current and Rust/WASM path against the same fixture/user action;
2. compare logical output/observable behavior;
3. collect failures and add permanent regressions;
4. expose a bounded feature/capability switch;
5. cut over only after required parity/performance/browser proof;
6. retain rollback path until later removal gate.

No global “Rust mode” switch that hides capability-level regressions.

## Task 4C — reusable web/embedded bundle v1

**Deliver:**

- deterministic local static bundle;
- manifest with exact Atlas/core/export/bridge compatibility identities;
- file digests;
- public-web mode and embedded-client mode flags without two codebases;
- embedded mode defaults to no arbitrary remote navigation/resource dependency;
- bridge JS endpoint disabled when not in embedded mode;
- public mode never expects private live state;
- packaging/verification tool that Game can consume by exact artifact identity.

Public Production UI Shell remains the UI composition authority.

---

# 11. Wave 5 — native client integration

Starts only after a host is accepted and Atlas bundle v1 is available as an immutable candidate artifact.

## Task 5A — Game Atlas host production adapter

**Repo:** Game

**Candidate ownership:** dedicated host crate/module plus bounded client composition change.

**Deliver:**

- open/close full Atlas panel;
- load only pinned local bundle under trusted origin/profile;
- no remote dependency for base functionality;
- clear error/degraded UI when host/bundle fails;
- process/resource cleanup;
- native gameplay/minimap continues when panel crashes/fails;
- package exact Atlas bundle digest into client candidate identity.

## Task 5B — local bridge native endpoint

**Repo:** Game

**Deliver:**

- version/capability handshake;
- allowlisted client→Atlas events;
- allowlisted Atlas→client UI intents;
- validation/size/rate/origin checks;
- no credentials/secrets;
- no gameplay/server mutation commands;
- disconnect/reconnect and mismatch behavior;
- privacy-safe diagnostics.

Security tests are RED first for forbidden capabilities and malformed messages.

## Task 5C — Atlas embedded-mode bridge endpoint

**Repo:** Atlas

May run in parallel with 5B after the wire/profile contract is frozen because repos are independent.

**Deliver:**

- explicit embedded-mode capability negotiation;
- live overlay state kept in ephemeral session memory only;
- no writes to public publication/build products;
- validated waypoint/focus intents;
- bridge absent/disabled in public web mode;
- malicious/malformed message tests;
- browser/embedded test fixtures.

## Task 5D — native minimap/waypoint interop

**Repo:** Game

Preserve native minimap ownership. Integrate only narrow local UX semantics such as a waypoint chosen in Atlas appearing on the native minimap.

Do not make the native minimap render through WebView/WASM.

---

# 12. Wave 6 — qualification lanes

After feature-complete candidate integration, freeze exact provider candidate heads/artifact digests. Qualification changes require a new candidate freeze.

Three evidence leads can work in parallel while provider test execution obeys constrained resources.

## Task 6A — security qualification

**Lifecycle:** META #77 + provider evidence.

Prove:

- trusted local origin;
- navigation/network default deny;
- CSP/resource restrictions;
- bridge origin/source validation;
- capability allowlist;
- message limits/flood handling;
- forbidden command rejection;
- no credential/session secret exposure;
- no private-state public artifact leakage;
- corrupt/malicious bundle behavior;
- host crash/hang isolation;
- dependency/supply-chain review.

Independent security reviewer must not be the bridge implementation worker.

## Task 6B — performance/resource qualification

**Lifecycle:** META #80 + provider evidence.

Record exact machine/profile and compare:

- current vs Rust generator/index jobs;
- JS vs WASM selected hot paths;
- bundle payload/startup;
- embedded host startup/RSS/CPU/GPU;
- interaction latency;
- large-world operations;
- native minimap unaffected baseline.

A regression requires explicit product justification or rework; it is not hidden by averaging unrelated metrics.

## Task 6C — cross-surface E2E

**Lifecycle:** META #78 + provider suites.

Required shared journeys:

1. open Atlas public and embedded from the same compatible world/export revision;
2. search a known entity;
3. verify same public identity/facts;
4. focus same location/floor;
5. exercise camera/floor state;
6. create/select a route/waypoint where the accepted capability exists;
7. confirm embedded client shows local player/floor state when bridge enabled;
8. confirm public web never receives that private state;
9. close/kill embedded host and confirm native gameplay/minimap remains usable;
10. run bridge/export/bundle mismatch negative cases.

Provider UI changes retain provider visual/accessibility acceptance.

---

# 13. Wave 7 — release compatibility and cutover

**Lifecycle:** META #79.

## Task 7A — freeze exact compatible tuple

Record exact immutable provider evidence for:

```text
Game export profile/version + producer revision/digest
world/content revision
Atlas Core/API identity
Atlas web/embedded bundle version + digest
bridge protocol/profile
Game client candidate/release identity
public Atlas candidate/release identity
```

No tuple contains floating refs.

## Task 7B — provider final integration

Each provider independently:

1. refresh current protected `main` as `integration_main_sha`;
2. merge-up normally;
3. review complete diff and changed files;
4. rerun invalidated exact-head tests/checks;
5. obtain required review;
6. protected squash merge;
7. verify resulting main SHA and post-merge checks.

Do not force provider merges into one transaction when their release models are independent.

## Task 7C — public Atlas cutover

Atlas follows its normal merged-main deployment/live acceptance. Verify exact deployed revision/bundle identity and rollback artifact.

## Task 7D — native client candidate acceptance

Game runs its provider-owned native client/release candidate acceptance with the exact embedded Atlas bundle digest. Prove offline/local Atlas startup, bridge behavior and native minimap fallback.

## Task 7E — META compatibility record

After both provider identities are immutable and independently proven, META records the compatible tuple using existing compatibility/release mechanisms. META does not copy the provider schemas.

---

# 14. Wave 8 — legacy path retirement

Legacy Python/JS computational paths are **not** removed as part of first Rust implementation unless the exact path has already met its removal gate.

A separate Atlas Issue/PR may remove a superseded path only when:

- the Rust path is the accepted default for that capability on protected main;
- parity tests no longer require the old path except as archived fixture/oracle;
- browser/live acceptance has passed on the new default;
- rollback to a prior release/artifact remains documented and proven;
- no active consumer still imports the old path;
- performance/security evidence has no unresolved blocker;
- complete changed-file/diff review proves removal scope is bounded.

Do not bundle broad cleanup/refactoring with migration closeout.

---

# 15. Rollback matrix

| Failure | Rollback/fallback |
| --- | --- |
| Rust compiler/index capability regression | capability-level switch/previous accepted generator until removal gate |
| WASM adapter failure | capability-specific JS/current path where still retained and compatible |
| public Atlas deployment regression | Atlas provider deployment rollback to prior accepted main/artifact |
| embedded Atlas bundle incompatible/corrupt | client disables full Atlas panel or repins prior compatible bundle in a new client candidate; native minimap remains |
| bridge mismatch/failure | disable live overlay and native intents; no guessed compatibility |
| embedded host crash/hang | tear down/disable Atlas host; gameplay/native minimap remains |
| private-state leak evidence | fail release, disable bridge profile, sanitize evidence/logging and require security requalification |
| Game export incompatibility | Atlas rejects/marks unavailable; never falls back to legacy runtime truth |

---

# 16. Definition of Done

The programme is not `DONE` until all statements below are proven with immutable evidence:

- ADR 0005 is canonical on protected META main.
- Game #191 and Atlas #188 required provider child lifecycles are terminal or explicitly `NO_CHANGE_REQUIRED` with evidence.
- Game remains sole canonical world/content/gameplay authority.
- Atlas Rust Core is real, tested and owns accepted derived capabilities without importing arbitrary Game internals.
- selected migrated capabilities have parity and bounded rollback evidence.
- public Atlas uses the accepted shared Atlas Core/bundle architecture.
- native client can open the locally packaged full Atlas product without remote dependency.
- native gameplay minimap/HUD remains native and independent.
- bridge protocol/profile is versioned, default-deny and security-qualified.
- private/live state is visible only in the local embedded session and absent from public publication artifacts.
- cross-surface search/location/floor/waypoint journeys are compatible.
- embedded host failure does not make gameplay unavailable.
- exact performance/resource evidence exists for migrated paths and selected host.
- exact provider protected-main checks/reviews are green.
- public Atlas merged-main live acceptance is green for the final Atlas identity.
- native client candidate/release acceptance is green for the exact embedded bundle digest.
- META records a non-floating compatible release tuple.
- legacy paths are retained or removed truthfully according to their own removal gate.
- no unresolved security, authority, provenance or compatibility conflict is hidden as PASS.

# 17. Coordinator completion report

The final coordinator returns:

- parent/child Issue numbers and terminal states;
- META ADR merge SHA;
- exact Game and Atlas final main SHAs;
- exact provider PRs and merge SHAs;
- Game export profile/version and source digest/revision;
- Atlas Core/API identity;
- Atlas embedded bundle version/digest;
- bridge protocol/profile version;
- Game client identity that pins the bundle;
- public Atlas deployed identity;
- verification/security/performance evidence references;
- rollback evidence;
- any deliberately retained legacy path and why;
- final verdict: `DONE`, `WAITING_EXTERNAL`, `BLOCKED`, or `STALLED` with exact material reason.
