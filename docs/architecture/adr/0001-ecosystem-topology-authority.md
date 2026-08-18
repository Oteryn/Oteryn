# ADR 0001 — Oteryn ecosystem repository topology authority

## Status

Accepted upon merge to `main` — 2026-08-18

- Decision owner: Oteryn repository owner
- Supersedes: `blakinio/Oteryn-Platform` ADR 0041 for **ecosystem repository-topology and META coordination authority**
- Preserves: provider ownership boundaries and migration safety constraints established by Platform ADR 0041
- Does not authorize: product-repository mutation, production deployment, secret access, destructive live operations, or physical migration steps not separately authorized

## Context

Before this repository existed, `blakinio/Oteryn-Platform` ADR 0041 was the accepted temporary cross-repository topology authority. It established a four-repository target, provider ownership boundaries, Atlas extraction rules, cross-repository release/compatibility principles, and the requirement that the first accepted META topology ADR explicitly supersede Platform ADR 0041 for ecosystem scope.

The physical `Oteryn/Oteryn` repository now exists as the neutral META coordination plane. This ADR moves only ecosystem-level topology authority here. It does not transfer product implementation ownership into META.

## Decision

### 1. Permanent target topology

The target Oteryn GitHub organization topology is:

```text
Oteryn/
├── Oteryn
│   └── thin ecosystem META / coordination plane
├── Oteryn-Game
│   └── native playable game product and canonical game-content toolchain
├── Oteryn-Platform
│   └── web / application / control plane
└── Oteryn-Atlas
    └── derived spatial / browser-map product
```

Repository-per-bounded-context fragmentation remains rejected. A deployable, executable, bounded context or schema does not automatically justify its own repository.

### 2. `Oteryn` is deliberately thin

`Oteryn/Oteryn` may own:

- ecosystem repository topology;
- cross-repository ADRs whose authority genuinely spans products;
- repository-coordinate and migration-state manifests;
- compatibility matrices;
- ecosystem release manifests pinning immutable product identities such as SHAs, versions and artifact/image digests;
- cross-repository integration/release orchestration contracts;
- organization-wide governance that genuinely applies across repositories.

It must not become a source aggregator, schema mirror or runtime monorepo.

META must not normatively duplicate:

- Game protocol or canonical world/content schemas;
- Platform API, authentication, GameAuth or Gateway provider schemas;
- Atlas browser/runtime implementation;
- component-local architecture or CI implementation.

Provider schemas remain with their providers. META records discovery, exact identities and supported combinations.

### 3. `Oteryn-Game` owns the native game product

Target coordinate: `Oteryn/Oteryn-Game`.

The accepted source lineage is the existing Game source coordinate recorded by the previous topology authority. Physical migration is separate from this ADR and must remain truthful in the repository manifest until independently completed.

The Game boundary includes the native Client, authoritative Rust Game Server / GameNode, `protocol-oteryn`, shared native game/domain types, canonical World/Content model and toolchain, Studio, legacy import boundary, and Game-owned public Atlas export semantics.

Client, Server and `protocol-oteryn` remain together while atomic protocol/shared-type evolution provides more safety than repository-level version coordination.

One source repository does not imply one release identity. Client, Server, protocol/schema, world/content schema, World Bundle, Studio and Atlas-export revisions may require distinct compatibility identities.

### 4. `Oteryn-Platform` owns the web/application control plane

Target coordinate: `Oteryn/Oteryn-Platform`.

Until physical migration is completed, the current coordinate remains `blakinio/Oteryn-Platform`.

Platform retains Portal, Identity/authentication/security policy, Accounts, GameAuth, World Registry control-plane policy, Gateway semantics/source, and other Platform-owned application modules. Current evidence does not justify separate permanent repositories for Portal, Identity or Gateway.

### 5. `Oteryn-Atlas` is an independent derived product

Coordinate: `Oteryn/Oteryn-Atlas`.

Atlas owns browser-map runtime, navigation, map-specific search/details, layers/overlays, presentation of approved derived facts, Atlas-specific indexing/spatial projection/cache, application packaging, deployment artifacts, consumer-side validation and its independent release/rollback lifecycle.

Atlas is not a second world authority. It does not own OTBM parsing, canonical World/Content schema, Game persistence, World Bundle compilation, authoritative game rules, or a duplicate canonical copy of Game-owned schemas.

The existing Atlas extraction remains selectively gated. Existence of the target repository does not imply that path-level ownership separation, history extraction, deployment or publication is complete.

### 6. Game → Atlas remains artifact-first and producer-owned

The preferred architecture remains:

```text
canonical Game World/Content
        |
        v
Game-owned public Atlas projection/export
        |
        v
immutable versioned artifact + provenance
        |
        v
Oteryn-Atlas ingestion/index/cache/render
```

Game owns the export schema/public allowlist, deterministic exporter and producer provenance. Atlas owns consumer validation, indexing, derived caches and presentation. META may record a supported producer/consumer combination only when both sides provide evidence.

META never copies the Game export schema as a normative duplicate.

### 7. Platform and Atlas remain independent release/failure domains

Platform may own discovery/entry policy for the Map capability while Atlas owns its application/runtime/assets/release. Atlas failure must not make core Platform capabilities unavailable.

Independent Atlas executable code should remain an independently governed trust/release boundary unless a later explicit decision adopts same-origin execution with equivalent Platform security governance.

### 8. Cross-repository validation is risk-proportional

Product repositories retain their local tests and provider/consumer fixtures. META may compose immutable evidence and orchestrate ecosystem-level release/integration E2E, but it does not relocate every product test implementation.

Contract-affecting changes require producer/consumer evidence proportional to risk. Ecosystem release manifests should pin exact immutable identities rather than rely on floating branches.

### 9. Migration state must remain truthful

The machine-readable repository manifest must distinguish:

- target coordinate;
- current coordinate;
- migration state;
- provider/authority owner;
- evidence or gate needed before pending migration state advances.

A future coordinate must not be presented as already migrated merely because the target architecture has been accepted.

Physical rename, transfer, history extraction, CI/package reference changes and production/deployment changes remain separately gated operations.

### 10. Legacy sources are evidence, not target authority

`blakinio/canary` and `blakinio/otclient` remain legacy/transitional/reference sources rather than normative target-architecture authorities.

`blakinio/Otheryn` remains a legacy source for the bounded Atlas extraction/migration work until that work is completed and proven. Legacy placement or history never determines future provider ownership by itself.

### 11. Authority handover

This ADR becomes canonical only when merged to `Oteryn/Oteryn:main`.

At that point:

- this ADR is the ecosystem repository-topology/META coordination authority;
- `blakinio/Oteryn-Platform` ADR 0041 is superseded for that ecosystem scope and remains historical provenance;
- Platform, Game and Atlas continue to own their provider-specific implementation and schemas;
- a separate Platform reconciliation should mark ADR 0041 superseded for ecosystem scope without rewriting its historical decision record.

## Consequences

Positive consequences:

- ecosystem authority has a neutral home;
- product repositories remain independently owned and releasable;
- compatibility/release metadata can compose immutable product evidence without duplicating provider schemas;
- physical migrations can proceed independently without pretending target coordinates are already complete.

Costs and constraints:

- META must stay intentionally small;
- cross-repository facts require explicit evidence and version identities;
- repository migrations and Atlas extraction still require their own transactions and rollback/verification;
- provider repositories remain authoritative for provider implementation, so META cannot be used to bypass their governance.
