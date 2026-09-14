# ADR 0005 — Unified Oteryn World Atlas surfaces and reuse architecture

## Status

Proposed for owner acceptance through `Oteryn/Oteryn#75`; canonical only after protected merge to `main`.

- Date: 2026-08-26
- Decision owner: Oteryn repository owner
- Lifecycle: `Oteryn/Oteryn#75`
- Game programme: `Oteryn/Oteryn-Game#191`
- Atlas programme: `Oteryn/Oteryn-Atlas#188`
- Security programme: `Oteryn/Oteryn#77`
- Verification programme: `Oteryn/Oteryn#78`
- Release/cutover programme: `Oteryn/Oteryn#79`
- Performance programme: `Oteryn/Oteryn#80`
- Extends: ADR 0001 ecosystem topology authority and ADR 0004 parallel-agent Git concurrency
- Preserves: Game ADR-0005 native world/content authority and Atlas Game→Atlas artifact-first boundary
- Does not authorize: provider runtime mutation, production deployment, secret access, live-state publication, provider schema duplication or a big-bang rewrite

## Context

Oteryn has three facts that should be treated as one architecture problem rather than three unrelated implementation choices:

1. `Oteryn-Game` is a native Rust product containing the authoritative game server, native client, canonical World/Content model and Game-owned public Atlas export semantics.
2. `Oteryn-Atlas` is already a substantial derived world product with full-world browsing, search, layers, creature/NPC/item intelligence, map interaction, WebGL rendering, testing, deployment and an evolving production web shell.
3. Reimplementing a second independent Atlas inside the native game client would duplicate search, navigation, map state, entity inspection, routes, overlays, interaction rules and future intelligence features, creating long-term semantic drift and twice the verification burden.

The desired product therefore is not “a web map plus a separate in-game map”. It is one **Oteryn World Atlas capability** exposed through multiple surfaces while preserving provider ownership and independent failure/release boundaries.

The architecture must also account for an important constraint: sharing the Rust language does not justify importing Game-internal crates into Atlas or making Atlas a second owner of canonical world semantics. Likewise, making the game client depend on a remote web deployment would create an unacceptable gameplay availability and security dependency.

## Decision

Oteryn adopts a **unified World Atlas, multi-surface architecture** with a Game-owned authoritative source boundary, an Atlas-owned derived Rust Core, a reusable locally packaged web product surface, a native gameplay minimap/HUD, and a narrow local bridge for explicitly allowlisted ephemeral client state.

The target architecture is:

```text
                    OTERYN-GAME
              canonical World/Content
                  + gameplay facts
                         │
                         │ Game-owned, explicit,
                         │ versioned public-safe export
                         ▼
              ┌──────────────────────┐
              │ immutable Atlas input │
              │ artifact + provenance │
              └──────────┬───────────┘
                         │
                         ▼
                OTERYN-ATLAS CORE
                      Rust
          derived ingest/index/query/state
                         │
              ┌──────────┴───────────┐
              │                      │
              ▼                      ▼
      Atlas Web/WASM bundle      stable surface API
              │                      │
        ┌─────┴──────┐               │
        │            │               │
        ▼            ▼               ▼
 Public Web     Client-embedded   optional future
    Atlas        local Atlas      native adapter
                   │
                   │ versioned local bridge
                   ▼
             Native Game Client
              Rust + wgpu/DX12
                   │
           native minimap/HUD
```

### 1. Game remains the only canonical World/Content authority

This ADR does not move canonical world, content, gameplay, persistence or server truth into Atlas.

`Oteryn-Game` owns:

- canonical World/Content semantics;
- world/content stable identity;
- authoritative gameplay facts;
- public Atlas export schema/profile and public allowlist;
- deterministic Atlas exporter and producer provenance;
- any Game-side compatibility identity required to consume the export safely;
- native-client gameplay state and authoritative session context.

`Oteryn-Atlas` consumes only the accepted public-safe producer boundary for canonical facts. It may derive indexes, rankings, search products, presentation metadata and cache structures, but those derived products do not become canonical Game truth.

### 2. Cross-repository coupling remains contract/artifact-first

Rust is the strategic implementation language for the Atlas computational core, but language uniformity does not weaken repository ownership.

Atlas MUST NOT directly depend on arbitrary Game-internal crate paths as its public contract.

The normal boundary remains:

```text
Game internal model
      │
      ▼
Game-owned public Atlas contract/export
      │
      ▼
versioned immutable artifact
      │
      ▼
Atlas consumer validation
```

A small provider-owned public Rust contract/codec crate may be accepted later only when it is explicitly designed as a stable public provider contract, versioned independently where necessary, and does not expose unstable Game runtime layouts. Its acceptance is a provider decision, not an implicit consequence of this ADR.

The permanent public format MUST NOT be an unstable Rust memory representation.

### 3. Atlas owns a Rust computational core

`Oteryn-Atlas` will introduce an Atlas-owned Rust workspace/core through a strangler migration.

The target Atlas Rust Core owns derived concerns such as:

- validated ingestion of Game-owned public Atlas exports;
- deterministic derived compilation;
- spatial indexes and region/chunk query structures;
- map/query primitives;
- derived search/index structures;
- route/path query products where Atlas semantics own them;
- map-facing capability/state primitives that are independent of DOM/UI implementation;
- deterministic artifact generation and validation;
- bounded parsers, codecs and resource limits for Atlas-owned formats;
- performance-critical computational paths proven appropriate for Rust/WASM.

Candidate Atlas-owned crate boundaries for provider design are:

```text
crates/
  atlas-model/
  atlas-ingest/
  atlas-core/
  atlas-spatial/
  atlas-search/
  atlas-publication/
  atlas-wasm/
  atlas-cli/
```

These names describe intended responsibility, not immediate file-creation authority. The Atlas provider plan must resolve current repository state and freeze exact names/dependencies before workspace mutation.

The core should prefer pure/data-oriented APIs, deterministic behavior, bounded allocation and platform-neutral code. DOM, WebView, native window ownership, SQL and deployment concerns do not belong in the pure core.

### 4. No big-bang rewrite

Existing Atlas behavior remains the accepted baseline while Rust capabilities are introduced incrementally.

For every migrated capability, the lifecycle is:

```text
current accepted implementation
        │
        ├── representative fixtures / golden behavior
        ▼
new Rust implementation in shadow/parity mode
        │
        ├── logical/byte parity where the contract permits
        ├── negative/failure parity
        ├── benchmark/resource evidence
        └── browser/E2E evidence when user-visible
        ▼
feature-level cutover
        │
        └── old path retained as bounded rollback until stability gate
        ▼
separate removal lifecycle
```

Migration order is evidence-driven. Rust is the strategic core choice because of reuse, safety, deterministic data processing and ecosystem coherence; a specific speedup multiplier is not required to justify the architecture. Benchmarks determine which paths migrate first and whether a particular JS path belongs in WASM.

### 5. Public web Atlas remains a first-class product surface

The public web Atlas remains Atlas-owned and independently deployable.

Browser UI ownership remains primarily TypeScript/JavaScript, HTML and CSS for:

- DOM composition;
- accessibility semantics;
- responsive UI;
- product shell/navigation;
- panels/cards/forms;
- browser lifecycle and integration glue.

Rust/WASM is used for Atlas Core functionality when it materially improves reuse, determinism or measured runtime characteristics. This ADR rejects rewriting UI/DOM code into Rust merely for language uniformity.

The already accepted Atlas Production UI Shell V1 remains the web product shell direction. Unified Atlas work must integrate with that product rather than create a second browser application.

### 6. The native client reuses the full Atlas product instead of recreating it

The native game client must not independently rebuild the full Atlas feature set.

The target full-screen/in-depth Atlas experience inside the game client is the **same Atlas web product bundle**, packaged locally with the client or its verified content distribution, and hosted in a bounded embedded web surface.

Initial target properties:

- the embedded Atlas bundle is local and pinned by immutable identity/digest;
- it is usable without remote Atlas availability;
- arbitrary remote navigation is disabled by default;
- its Atlas data artifacts are version-compatible with the client/world profile;
- it uses the same Atlas Core/WASM and web UI semantics as the public product where applicable;
- client-specific live overlays arrive only through the local bridge;
- embedded-surface failure never makes core gameplay unavailable.

The exact native web-host technology is a **provider benchmark/security gate**, not frozen by META. The Game programme must prototype only realistic supported-platform candidates and select one through packaging, memory, GPU, input, crash-isolation and security evidence. On Windows an OS-provided web runtime may be evaluated, but this ADR does not mandate a specific vendor/runtime.

### 7. Native gameplay minimap/HUD remains native

The full Atlas product and the moment-to-moment gameplay minimap have different failure/performance requirements.

The client-owned gameplay minimap/HUD remains native Rust and uses the native renderer/runtime so that:

- gameplay does not require a WebView;
- map HUD remains available if the embedded Atlas fails;
- input/render latency remains under native client control;
- gameplay-critical presentation does not acquire a browser-runtime dependency.

The native minimap should reuse canonical Game world/runtime structures and shared semantic identifiers available within Game. It may consume Atlas-derived non-authoritative products only through an explicit compatibility boundary.

A later optional native build/package of selected Atlas Core functionality may be accepted when a concrete client use case requires it and the cross-repository packaging/versioning cost is justified. It is not required for the first unified Atlas cutover.

### 8. Embedded Atlas uses a local versioned bridge

The native client may provide a narrow, versioned local bridge to the embedded Atlas surface.

The bridge is **default deny** and has two directions.

Client → Atlas may expose explicitly allowlisted ephemeral UI context such as:

- current player map position;
- current floor;
- selected/active route progress;
- party positions only when product/privacy policy permits;
- locale/display preferences needed for presentation;
- bounded quest/session context only when separately accepted as client-visible and privacy-safe.

Atlas → Client may initially emit non-authoritative UI intents such as:

- set/clear local waypoint;
- select/focus a map/entity target;
- request the native minimap to center on a validated coordinate;
- copy/open a product-safe local reference.

The first bridge profile MUST NOT grant Atlas direct authority to:

- move the character;
- attack or use an item;
- invoke arbitrary gameplay/server commands;
- access authentication/session secrets;
- access arbitrary files, processes or native APIs;
- bypass Game validation or server authority.

Every message requires a versioned schema/profile, bounded size/rate, validation and explicit capability negotiation. Unknown or incompatible messages fail closed.

### 9. Private/live client state is never Atlas publication input

The architecture distinguishes three data classes:

| Data class | Owner/source | Public web Atlas | Embedded Atlas | Publication permitted |
| --- | --- | --- | --- | --- |
| canonical public world/content facts | Game export | yes | yes | yes, through Game public-safe contract |
| Atlas derived public products | Atlas | yes | yes | yes, Atlas-owned derived artifact |
| player/session/private live state | Game client/runtime | no | local session only | no |

The local bridge must not write private/live values into the public Atlas build tree, publication datasets, caches intended for distribution, screenshots/evidence without sanitization, or telemetry without an explicit accepted privacy contract.

A public Atlas deployment must be capable of running with no knowledge that a particular player/session exists.

### 10. Embedded content is a release artifact, not a remote dependency

Atlas produces a versioned **web/embedded bundle** suitable for public deployment and client packaging.

The bundle manifest must eventually identify at least:

- Atlas bundle format/version;
- Atlas Core/API version or equivalent capability identity;
- supported Game Atlas-export schema/profile versions;
- source Atlas revision;
- derived source/export revision/digest where relevant;
- bridge protocol/profile compatibility range for embedded mode;
- content/file digests;
- security profile/CSP or equivalent host requirements;
- minimum host capabilities.

The Game client pins an exact compatible Atlas bundle identity for a release. Floating `main`/latest references are not release identities.

Public Atlas may deploy a newer compatible bundle independently. The client may intentionally lag, provided META compatibility evidence and provider policies describe the supported tuple.

### 11. Compatibility has explicit independent identities

At minimum the release/integration model distinguishes:

```text
game_atlas_export_profile/version
world/content revision
atlas_core_api identity
atlas_web_embedded_bundle identity + digest
atlas_bridge_protocol/profile version
game_client release identity
public_atlas release/deployment identity
```

META records compatible immutable combinations using its existing compatibility/release authority. It must not copy provider schemas into META.

A bridge or bundle version mismatch is a bounded feature failure, not permission to guess compatibility. Embedded live overlays disable fail-closed; static Atlas capability may remain available only if its own input/bundle compatibility is independently valid.

### 12. Failure domains remain explicit

The target failure behavior is:

- Game server failure: authoritative Game handling applies; Atlas cannot substitute authority.
- public Atlas deployment failure: native gameplay and client-bundled Atlas remain independent.
- embedded Atlas host failure: close/disable the full Atlas panel; native gameplay/minimap remains usable.
- Atlas Core/WASM load failure in web/embedded mode: show truthful degraded/unavailable capability; do not fabricate results.
- local bridge failure/mismatch: disable live overlay/commands; public/static Atlas data remains isolated.
- stale/incompatible Game export: Atlas consumer rejects or marks incompatible according to provider contract; no legacy-runtime fallback.

### 13. Security baseline for embedded mode

The implementation plan must prove at least:

- local/pinned content origin and digest verification appropriate to release packaging;
- arbitrary remote navigation blocked by default;
- strict CSP or equivalent resource policy;
- no ambient access to Game credentials/session secrets;
- no arbitrary native/file/process bridge;
- typed/versioned message validation;
- message size, frequency and recursion limits;
- origin/source validation for bridge messages;
- explicit command capability allowlist;
- no server/gameplay mutation authority in the first bridge profile;
- private-state retention/logging minimization;
- malicious/corrupt Atlas bundle and malformed-message negative tests;
- host crash/hang isolation and recovery path;
- dependency/license/supply-chain review for the selected embedded host.

Security Issue `Oteryn/Oteryn#77` owns the cross-product threat-model acceptance envelope; provider repositories own their implementation and tests.

### 14. Performance and resource policy

Performance Issue `Oteryn/Oteryn#80` owns ecosystem comparison evidence, while providers own benchmark implementation.

Representative evidence must measure:

- Python generator/index workloads versus Rust candidates;
- JS computational hot paths versus Rust/WASM candidates;
- browser/WASM startup and payload cost;
- embedded-host startup, idle/active memory, CPU/GPU impact and input latency;
- native minimap independently from full Atlas;
- large-world scaling and bounded memory behavior;
- determinism/output compatibility.

Performance evidence chooses migration priority and host implementation. It cannot waive authority, parity, accessibility or security requirements.

### 15. Verification is provider-local plus ecosystem composition

`Oteryn-Game` retains native-client, Rust, renderer and producer-contract tests.

`Oteryn-Atlas` retains Rust Core, browser, Playwright, visual, performance, publication and live-deployment tests.

META verification Issue `Oteryn/Oteryn#78` composes immutable evidence for cross-surface journeys and compatibility; it does not centralize provider tests.

The final programme must prove shared journeys such as:

```text
search entity
→ obtain the same public identity/facts
→ select the same map location/floor
→ preserve camera/floor semantics
→ create a route/waypoint where supported
→ public web ends with public state only
→ embedded client additionally displays allowlisted local player state
```

Required failure journeys include incompatible bundle/export, bridge mismatch, malformed messages, missing WASM/core capability, embedded-host failure, offline client mode and rollback.

### 16. Migration/cutover is phased and reversible

The programme has four architectural cutovers rather than one global switch:

1. **Atlas Core foundation** — Rust exists but current public behavior remains authoritative.
2. **Capability-level Atlas migration** — individual compiler/index/query paths switch after parity/benchmark evidence.
3. **Embedded client Atlas** — local packaged full Atlas ships behind a bounded client capability while native minimap remains independent.
4. **Legacy-path retirement** — superseded Python/JS computational paths are removed only in later dedicated lifecycles after rollback/stability criteria are met.

Every capability switch has an identified rollback to the last accepted compatible implementation/artifact.

The Game client must be able to disable the embedded Atlas capability without disabling gameplay. The public Atlas retains its independent deployment rollback.

### 17. Parallel implementation model

Implementation follows ADR 0004.

One task maps to one branch/worktree/PR. `main` movement does not cause work restart. Final integration uses late merge-up refresh and exact-head validation.

Parallelism is constrained by **mutable ownership**, not by the number of available agents.

The coordinator may run multiple read-only/design/review agents concurrently. Normal provider-mutating concurrency is limited to two or three disjoint lanes unless the live coordinator proves more are safe.

Serialized leases include:

- root Cargo/workspace membership and shared dependency policy within one provider repo;
- shared Game client composition/entrypoint files;
- shared Atlas `web/fullworld*` shell/composition files;
- provider CI/workflow files;
- compatibility/release manifests;
- final integrator branches.

Agents working in independent crates, fixtures or test domains may proceed in parallel after interfaces are frozen.

### 18. Interaction with active programmes

This ADR is intentionally compatible with current work rather than a reason to restart it.

At planning admission:

- Game had an active durability architecture hold and coordinator work; unified Atlas client mutation must wait for a current allocation/ownership-safe window.
- Atlas had active E2E optimization and shared FullWorld/creature work; unified Atlas runtime/UI mutation must respect those current leases.
- Atlas Production UI Shell V1 is the intended production web shell and must be consumed rather than replaced.

These exact Issue/PR numbers are planning provenance, not permanent blockers. The implementation coordinator always resolves fresh GitHub state and releases lanes based on current semantic overlap.

## Rejected alternatives

### A. Build a second native Atlas from scratch inside Game

Rejected because it duplicates Atlas search/navigation/intelligence/state/UI behavior, doubles verification and creates semantic drift.

### B. Make the client open the public Atlas website remotely

Rejected as the primary architecture because game-client Atlas availability, privacy and version compatibility would depend on network/public deployment state.

### C. Rewrite all Atlas UI in Rust

Rejected. DOM/accessibility/product-shell work is better owned by the web stack; Rust is used where its core/reuse characteristics are valuable.

### D. Put Atlas Core inside Oteryn-Game

Rejected as the default because Atlas-specific derived indexing/query/presentation authority belongs to the Atlas product. Game remains provider of canonical public inputs.

### E. Let Atlas import Game-internal crates directly

Rejected because it turns internal Game implementation into an accidental cross-repository public API and weakens independent release boundaries.

### F. Make the gameplay minimap an embedded browser

Rejected because gameplay-critical HUD latency/availability should remain native and independent of the embedded full Atlas host.

### G. Remove Python/JS paths immediately after first Rust implementation

Rejected. Strangler/parity-first migration and rollback evidence are mandatory.

## Consequences

Positive:

- one full Atlas feature set can serve public web and native client;
- user-visible search/intelligence/map workflows stop being duplicated;
- Rust becomes a coherent derived computational core without stealing Game authority;
- native gameplay keeps low-latency/failure-isolated minimap behavior;
- the client can enrich Atlas locally with live context without leaking it into public data;
- web and client can release independently while pinning compatible artifacts;
- migration can proceed incrementally alongside current Atlas product work.

Costs:

- Oteryn introduces an embedded-web host dependency and security surface in the client;
- cross-repository release compatibility becomes more explicit and must be maintained;
- Atlas must support Rust/WASM build/test/tooling in addition to existing browser tooling during migration;
- a temporary dual implementation period increases verification cost;
- local bridge design requires strict capability/security discipline;
- some client-native features may still require narrow native adapters rather than zero duplication.

## Rollout authority

This ADR becomes canonical only after protected merge to META `main` with required META gates/review.

After acceptance, it authorizes **programme decomposition**, not arbitrary provider mutation. Provider runtime work remains gated by:

- current provider `AGENTS.md` and authority hierarchy;
- provider Issue/branch/PR lifecycle;
- current coordinator/allocation state;
- exact path leases and dependency readiness;
- provider exact-head CI/review;
- separate deployment/release authority.

The executable rollout is defined in `docs/superpowers/plans/2026-08-26-unified-world-atlas-convergence.md` and the coordinator prompt `docs/agents/prompts/OTERYN-WORLD-ATLAS-PROGRAMME-COORDINATOR.md`.