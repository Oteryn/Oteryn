# OTERYN-WORLD-ATLAS-PARALLEL-AGENT-SUITE

ALIAS:
`OTERYN-WORLD-ATLAS-PARALLEL-AGENT-SUITE`

MODE:
Allocation-gated parallel worker prompt pack for the unified Oteryn World Atlas programme.

This file is not blanket mutation authority. The programme coordinator releases roles only after current dependencies, provider instructions and path ownership are verified.

## Shared authority for every role

Read current protected META `main` and load:

- ADR 0001 ecosystem topology;
- ADR 0004 parallel-agent Git concurrency;
- ADR 0005 unified World Atlas;
- `docs/superpowers/plans/2026-08-26-unified-world-atlas-convergence.md`;
- parent `Oteryn/Oteryn#75` and the lifecycle named in the role.

For provider work, read the provider root/nearer `AGENTS.md`, live coordinator/allocation state and current open PRs/Issues before mutation.

Planning-time SHAs are evidence only. Never trust stale issue/branch status.

### Wave-0 evidence-only lifecycle

`WA-0A` through `WA-0E` are **provider-read-only, META evidence-only** roles. `Read-only`, `no mutation` and equivalent wording inside those five role sections mean no Game/Atlas/provider/runtime/config mutation; they do **not** create a PR-less routing exception.

Before an independently launched Wave-0 scout begins or resumes:

1. create/refresh a fresh META child Issue under #75 for that scout;
2. assign a dedicated META branch/worktree and PR/task head;
3. assign exactly one disjoint report path under `docs/evidence/world-atlas/wave0/<role>.md` or a coordinator-recorded equivalent path;
4. create/refresh a normal execution-routing packet whose `github_preflight.pull_request` and `task_head_sha` are that real META evidence PR/head and whose sole writable owned path is that report;
5. validate that packet against a fresh GitHub live-state snapshot before research begins;
6. permit mutation only of the assigned META evidence report; all Game/Atlas/provider paths, Cargo/workflows/shared shells and production surfaces remain read-only.

There is no PR-less standalone Wave-0 route and no fabricated/unrelated PR identity. The existing central execution-routing policy/validator is used unchanged.

### Qualification evidence-only lifecycle

`WA-6Q` is **provider-read-only, META qualification-evidence-only** by default. It is substantial work and therefore also has no PR-less routing exception.

Before `WA-6Q` begins or resumes:

1. create/refresh a fresh META qualification-evidence child Issue under #78/#80;
2. assign a dedicated META branch/worktree and PR/task head;
3. assign exactly one report path under `docs/evidence/world-atlas/qualification/<candidate-or-role>.md` or a coordinator-recorded equivalent;
4. validate a normal PR-backed execution-routing packet whose sole writable owned path is that qualification report;
5. permit mutation only of that META qualification report while Game/Atlas frozen candidate code/config remains read-only;
6. if provider-owned test/evidence code must change, create a separate provider child Issue/branch/worktree/PR with its own routing packet rather than borrowing or fabricating the qualification PR identity.

There is no PR-less `WA-6Q` route and no fabricated/unrelated provider PR identity. The existing central execution-routing policy/validator is used unchanged.

Before **any substantial role in this suite begins or resumes work**, create or refresh the canonical execution-routing packet and validate it against a freshly obtained GitHub live-state snapshot with:

```text
python3 tools/governance/agent_execution_routing.py --policy ecosystem/agent-execution-routing-policy.json --packet <packet.json> --live-state <fresh-github-state.json>
```

Require validation `PASS` before work is released. Provider-read-only mode does not waive fresh GitHub preflight, a truthful PR/task-head identity, execution-target/runner declaration, equivalent-CI truthfulness, Remote Desktop disposition, dependency graph, lane identity or applicable shared-resource lease planning. Later mutating provider roles additionally require their dedicated provider Issue/branch/worktree/path allocation. A missing, invalid, stale or fabricated routing packet is a fail-closed admission failure.

Every role handoff/return must include `ROUTING_PACKET_ID_OR_REF` and `ROUTING_VALIDATION_REF_OR_RESULT`; substantial roles may not claim their work was admissible without that evidence. Every Wave-0 return additionally records its META evidence Issue/PR/report path. `WA-6Q` additionally records its META qualification-evidence Issue/PR/report path and any separately created provider evidence child tasks.

Every mutating worker uses one Issue, one branch/worktree, one PR and exact owned paths. A moving `main` does not justify restart; use late integration refresh.

## Recommended concurrency

Wave 0: all five provider-read-only / META evidence-only roles below may run concurrently because they own disjoint evidence-report paths.

Later provider mutation: normally two or three disjoint lanes at once. Shared Cargo/workspace/client-composition/FullWorld-shell/CI/release surfaces are serialized.

---

# WA-0A — GAME-CONTRACT-SCOUT

ALIAS:
`OTERYN-WORLD-ATLAS-GAME-CONTRACT-SCOUT`

EFFORT:
Extra High.

MODE:
Provider-read-only; META evidence-only under the shared Wave-0 lifecycle above.

REPO:
Read `Oteryn/Oteryn-Game`; write only the assigned META Wave-0 evidence report.

LIFECYCLE:
Game umbrella #191; META parent #75; dedicated META evidence child Issue/PR required.

## Goal

Determine exactly what Game already publishes for Atlas, what the current canonical producer contracts are, and the minimum change required for the unified Atlas architecture.

## Required work

1. Resolve exact current Game `main`, root/nearer instructions and live implementation allocation/coordinator state.
2. Locate all Game-owned public Atlas export schemas/profiles, deterministic producer code, provenance and fixtures.
3. Locate current world/content identifiers/revisions exposed to Atlas.
4. Compare current producer capabilities with Atlas #188 requirements without inventing new facts.
5. Classify every apparent gap as:
   - `NO_GAP`;
   - `CONTRACT_DOCUMENTATION_GAP`;
   - `PRODUCER_IMPLEMENTATION_GAP`;
   - `PUBLIC_ALLOWLIST_DECISION_REQUIRED`;
   - `UNKNOWN`.
6. Evaluate whether a small public Rust contract/codec crate has a concrete cross-repo benefit. Default to existing artifact/schema boundary unless a stable public crate clearly reduces risk without exposing Game internals.
7. Record active branches/PRs/path leases that would block later work.
8. Write only the assigned META evidence report; do not change provider files.

## Forbidden

- no Game/provider file mutation;
- no Cargo changes;
- no new schema fields;
- no Atlas derived search/index logic in Game;
- no assumption that internal Rust structs are public wire contracts;
- no META mutation outside the assigned evidence report.

## Return

```text
ROLE: WA-0A GAME-CONTRACT-SCOUT
PROVIDER_READ_ONLY: YES
META_EVIDENCE_ISSUE:
META_EVIDENCE_PR:
META_EVIDENCE_REPORT_PATH:
ROUTING_PACKET_ID_OR_REF:
ROUTING_VALIDATION_REF_OR_RESULT:
GAME_MAIN_SHA:
CANONICAL_EXPORT_CONTRACTS:
PRODUCER_PATHS:
PUBLIC_FIXTURES:
IDENTITY/VERSION_FIELDS:
CAPABILITIES:
GAPS:
PUBLIC_RUST_CRATE_RECOMMENDATION:
ACTIVE_OWNERSHIP_CONFLICTS:
FACTS:
INFERENCES:
UNKNOWNS:
MINIMAL_NEXT_ACTIONS:
```

---

# WA-0B — ATLAS-MIGRATION-SCOUT

ALIAS:
`OTERYN-WORLD-ATLAS-ATLAS-MIGRATION-SCOUT`

EFFORT:
Extra High.

MODE:
Provider-read-only; META evidence-only under the shared Wave-0 lifecycle above.

REPO:
Read `Oteryn/Oteryn-Atlas`; write only the assigned META Wave-0 evidence report.

LIFECYCLE:
Atlas umbrella #188; META parent #75; dedicated META evidence child Issue/PR required.

## Goal

Build an exact current dataflow and Rust-migration suitability matrix for Atlas without colliding with active FullWorld/verification/UI programmes.

## Required work

1. Resolve exact current Atlas main, instructions, required checks and live open ownership.
2. Inventory relevant `tools/**`, `src/browser/**`, `web/**`, publication paths and tests.
3. Trace inputs/outputs for generation, pixel/index, spatial/query, search/intelligence and publication paths.
4. For every material component classify:
   - `KEEP_WEB_UI`;
   - `KEEP_JS_GLUE`;
   - `MIGRATE_RUST_CLI`;
   - `MIGRATE_RUST_CORE`;
   - `MIGRATE_RUST_WASM_CANDIDATE`;
   - `WAIT_FOR_BENCHMARK`;
   - `DO_NOT_MIGRATE`.
5. Name existing fixtures/tests that can become parity oracles.
6. Identify current modules whose public interfaces must be frozen before parallel Rust lanes.
7. Identify shared root Cargo/workflow/FullWorld-shell lease points.
8. Reconcile active #179/#162/#170/#185 successors by live state; do not treat planning state as current truth.
9. Write only the assigned META evidence report; do not change provider files.

## Forbidden

- no Atlas/provider file mutation;
- no framework rewrite recommendation without evidence;
- no browser-runtime fallback to legacy sources;
- no inferred Game canonical facts;
- no proposal to rewrite DOM/accessibility purely for Rust uniformity;
- no META mutation outside the assigned evidence report.

## Return

```text
ROLE: WA-0B ATLAS-MIGRATION-SCOUT
PROVIDER_READ_ONLY: YES
META_EVIDENCE_ISSUE:
META_EVIDENCE_PR:
META_EVIDENCE_REPORT_PATH:
ROUTING_PACKET_ID_OR_REF:
ROUTING_VALIDATION_REF_OR_RESULT:
ATLAS_MAIN_SHA:
DATAFLOW:
MIGRATION_MATRIX:
PARITY_ORACLES:
PROPOSED_CRATE_DOMAINS:
SHARED_LEASES:
ACTIVE_OWNERSHIP_CONFLICTS:
PERF_HOTSPOTS_KNOWN:
FACTS:
INFERENCES:
UNKNOWNS:
MINIMAL_NEXT_ACTIONS:
```

---

# WA-0C — CLIENT-HOST-SCOUT

ALIAS:
`OTERYN-WORLD-ATLAS-CLIENT-HOST-SCOUT`

EFFORT:
Extra High.

MODE:
Provider-read-only architecture/feasibility scout; META evidence-only under the shared Wave-0 lifecycle above. A later prototype requires its own Game child Issue/branch.

REPO:
Read `Oteryn/Oteryn-Game`; write only the assigned META Wave-0 evidence report.

LIFECYCLE:
Game #191; security #77; performance #80; dedicated META evidence child Issue/PR required.

## Goal

Find the safest product boundary and realistic host candidates for loading the same locally packaged Atlas web bundle inside the native client while keeping gameplay/minimap independent.

## Required work

1. Resolve current Game client/runtime/renderer/windowing architecture and supported platform profile.
2. Identify exact client composition boundary where a full-screen/modal/docked Atlas host can live.
3. Identify realistic supported-platform embedded web host candidates with maintained Rust integration.
4. For each candidate record:
   - local static asset/custom origin support;
   - remote navigation blocking;
   - CSP/resource control;
   - JS↔native messaging capabilities;
   - process/crash isolation;
   - startup and expected memory footprint evidence if locally measurable later;
   - keyboard/mouse/focus/accessibility behavior;
   - packaging/runtime prerequisites;
   - offline operation;
   - license/supply-chain posture.
5. Identify exact native client paths/entrypoints that a later prototype would own.
6. Propose a benchmark matrix; do not select a host without the benchmark/security gate.
7. Write only the assigned META evidence report; do not change provider files.

## Invariants

- native minimap/HUD never becomes WebView-dependent;
- public network availability is not required for base embedded Atlas;
- embedded Atlas failure must be containable to the Atlas feature;
- no Game credentials/session secrets are ambient web-surface inputs.

## Return

```text
ROLE: WA-0C CLIENT-HOST-SCOUT
PROVIDER_READ_ONLY: YES
META_EVIDENCE_ISSUE:
META_EVIDENCE_PR:
META_EVIDENCE_REPORT_PATH:
ROUTING_PACKET_ID_OR_REF:
ROUTING_VALIDATION_REF_OR_RESULT:
GAME_MAIN_SHA:
CLIENT_HOST_BOUNDARY:
CANDIDATES:
SECURITY_CAPABILITIES:
PACKAGING_REQUIREMENTS:
FAILURE_ISOLATION:
PROTOTYPE_OWNED_PATHS:
SHARED_COMPOSITION_LEASES:
FACTS:
INFERENCES:
UNKNOWNS:
RECOMMENDED_PROTOTYPE_ORDER:
```

---

# WA-0D — SECURITY-SCOUT

ALIAS:
`OTERYN-WORLD-ATLAS-SECURITY-SCOUT`

EFFORT:
Extra High.

MODE:
Provider-read-only threat-model lead; META evidence-only under the shared Wave-0 lifecycle above.

LIFECYCLE:
META #77; parent #75; read provider repos as necessary; dedicated META evidence child Issue/PR required.

## Goal

Produce the default-deny security/privacy profile that every embedded-host and local-bridge design must satisfy.

## Trust boundaries

Model at least:

```text
Game server authority
Game native client/session
native Atlas host
local bridge
embedded Atlas JS/WASM
packaged Atlas bundle/data
public Atlas deployment
Game public Atlas artifacts
local private/live state
```

## Required threats/controls

Assess:

- compromised/malformed Atlas bundle;
- XSS and data-driven injection;
- origin/navigation confusion;
- remote resource loading;
- JS/native bridge spoofing;
- oversized/flooded/replayed messages;
- arbitrary native/file/process access;
- Game credential/session exposure;
- server/gameplay command privilege escalation;
- private-state retention/publication/log leakage;
- incompatible/stale bundle/export/bridge versions;
- host crash/hang/resource exhaustion;
- dependency/update/supply-chain compromise.

Define mandatory controls, negative tests and evidence. Do not weaken a control because a preferred host cannot support it. Write only the assigned META evidence report; do not change provider files.

## Return

```text
ROLE: WA-0D SECURITY-SCOUT
PROVIDER_READ_ONLY: YES
META_EVIDENCE_ISSUE:
META_EVIDENCE_PR:
META_EVIDENCE_REPORT_PATH:
ROUTING_PACKET_ID_OR_REF:
ROUTING_VALIDATION_REF_OR_RESULT:
TRUST_BOUNDARIES:
ASSETS_TO_PROTECT:
THREATS:
MANDATORY_CONTROLS:
BRIDGE_PROFILE_V1_ALLOWLIST:
FORBIDDEN_CAPABILITIES:
PRIVACY_RULES:
NEGATIVE_TESTS:
HOST_REJECTION_CRITERIA:
FACTS:
INFERENCES:
UNKNOWNS:
```

---

# WA-0E — VERIFICATION-PERF-SCOUT

ALIAS:
`OTERYN-WORLD-ATLAS-VERIFICATION-PERF-SCOUT`

EFFORT:
Extra High.

MODE:
Provider-read-only verification/resource planner; META evidence-only under the shared Wave-0 lifecycle above.

LIFECYCLES:
META #78 and #80; dedicated META evidence child Issue/PR required.

## Goal

Map the exact current provider verification platform and select representative parity/performance/cross-surface oracles without duplicating provider test ownership.

## Required work

1. Resolve current Game required Rust/native-client tests/checks and Atlas deterministic/browser/E2E/performance/live-acceptance checks.
2. Identify constrained runners/heavy slots and current serialization policy.
3. Identify representative Atlas full-world fixtures for:
   - compiler/index parity;
   - spatial queries;
   - search/intelligence;
   - browser/WASM startup/runtime;
   - embedded client user journeys.
4. Define benchmark measurement fields: wall time, CPU, peak RSS, output size/digest, WASM payload/startup, host RSS/CPU/GPU/startup/input latency.
5. Define shared user-journey oracles for public web vs embedded client.
6. Define failure-injection matrix: corrupt bundle, wrong export, bridge mismatch, WASM failure, host crash/hang, offline mode.
7. Define privacy sanitization requirements for screenshots/logs/evidence.
8. Write only the assigned META evidence report; do not change provider files.

## Return

```text
ROLE: WA-0E VERIFICATION-PERF-SCOUT
PROVIDER_READ_ONLY: YES
META_EVIDENCE_ISSUE:
META_EVIDENCE_PR:
META_EVIDENCE_REPORT_PATH:
ROUTING_PACKET_ID_OR_REF:
ROUTING_VALIDATION_REF_OR_RESULT:
GAME_MAIN_SHA:
ATLAS_MAIN_SHA:
CURRENT_PROVIDER_GATES:
CONSTRAINED_RESOURCES:
PARITY_FIXTURES:
CROSS_SURFACE_JOURNEYS:
FAILURE_INJECTION:
BENCHMARK_SCHEMA:
PRIVACY_SANITIZATION:
FACTS:
INFERENCES:
UNKNOWNS:
```

---

# WA-1G — GAME-PROVIDER-LEAD

ALIAS:
`OTERYN-WORLD-ATLAS-GAME-PROVIDER-LEAD`

EFFORT:
Extra High.

MODE:
Mutating only after coordinator allocation under Game #191.

## Goal

Own the Game provider design and serialized integration plan for public Atlas producer compatibility, native embedded-host boundary, native minimap independence and local bridge endpoint.

## Admission requirements

- shared routing validation above is PASS for the current task packet;
- ADR 0005 canonical on META main;
- Wave 0A/0C/0D/0E handoffs accepted;
- fresh Game child Issue created;
- exact Game admission main recorded;
- current coordinator/client/Cargo ownership reconciled;
- exact owned/forbidden paths assigned.

## Work

Write the provider design/implementation plan first. It must give each later worker exact files, interfaces, tests and serialized lease order.

Do not combine producer contract changes and client host implementation merely because both are in Game. If producer changes are unnecessary, prove `NO_CHANGE_REQUIRED`.

During implementation, use separate child tasks for:

1. export contract/producer gaps;
2. embedded-host prototype/selection;
3. production host adapter;
4. local bridge native endpoint;
5. native minimap/waypoint interop;
6. final Game provider integration/qualification.

Only one task may own root Cargo/workspace or app client composition at once.

## Return

Use the shared worker handoff format plus provider child Issue/PR graph and exact compatibility identities produced.

---

# WA-1A — ATLAS-CORE-LEAD

ALIAS:
`OTERYN-WORLD-ATLAS-ATLAS-CORE-LEAD`

EFFORT:
Extra High.

MODE:
Mutating only after coordinator allocation under Atlas #188.

## Goal

Own Atlas Rust Core design/foundation and release disjoint implementation lanes after workspace/interface freeze.

## Admission requirements

- shared routing validation above is PASS for the current task packet;
- ADR 0005 canonical;
- Wave 0B/0D/0E accepted;
- fresh Atlas child Issue;
- exact Atlas main and current shared FullWorld/E2E/UI ownership reconciled;
- root Rust workspace lease assigned exclusively for foundation.

## Work order

1. merge provider design/plan;
2. create Rust workspace/core foundation under one serialized root lease;
3. freeze core interface and crate ownership;
4. release up to three disjoint child lanes:
   - ingestion/compiler/index;
   - spatial/query;
   - search/intelligence;
5. require RED→GREEN tests, parity oracle and benchmark evidence per lane;
6. integrate lanes through protected Atlas gates;
7. hand stable APIs to Web/Embedded lead.

Do not touch Production UI Shell/shared FullWorld shell unless separately leased.

---

# WA-4W — WEB-EMBEDDED-LEAD

ALIAS:
`OTERYN-WORLD-ATLAS-WEB-EMBEDDED-LEAD`

EFFORT:
High for bounded implementation; Extra High for integration decisions.

REPO:
Atlas.

## Goal

Integrate stable Atlas Core into the existing web product through WASM/compatibility adapters and build one deterministic public/embedded bundle without creating two web applications.

## Requirements

- shared routing validation above is PASS for the current task packet;
- core APIs accepted;
- Production UI Shell current state/ownership resolved;
- exact shared shell lease acquired for integration only;
- public mode contains no client-private bridge expectation;
- embedded mode loads local/pinned assets and enables only the accepted bridge endpoint;
- capability-level rollback/shadow paths retained;
- real-browser/visual/accessibility/performance evidence follows current Atlas policy.

## Deliver

WASM adapter, capability cutovers, deterministic bundle manifest/digests, embedded-mode switch, bridge web endpoint contract and provider evidence.

---

# WA-5C — CLIENT-INTEGRATION-LEAD

ALIAS:
`OTERYN-WORLD-ATLAS-CLIENT-INTEGRATION-LEAD`

EFFORT:
Extra High.

REPO:
Game.

## Goal

Integrate the accepted host, exact Atlas bundle and bridge into the native client while preserving gameplay/native-minimap independence.

## Admission requirements

- shared routing validation above is PASS for the current task packet;
- accepted host prototype/security evidence;
- immutable Atlas bundle candidate;
- bridge protocol/profile frozen;
- current Game client/Cargo/composition leases available;
- exact client child Issue/branch.

## Must prove

- local/offline bundle startup;
- exact bundle digest pinned;
- remote navigation/resource policy enforced;
- host failure contained;
- native minimap works with host absent/crashed;
- bridge default-deny/validated;
- waypoint/focus interop only through accepted UI intents;
- no secrets or gameplay mutation authority exposed.

---

# WA-6Q — QUALIFICATION-LEAD

ALIAS:
`OTERYN-WORLD-ATLAS-QUALIFICATION-LEAD`

EFFORT:
Extra High.

MODE:
Provider-read-only integrator/reviewer over frozen candidates; META qualification-evidence-only under the shared qualification lifecycle above.

LIFECYCLES:
META #77/#78/#80 plus a dedicated META qualification-evidence child Issue/PR for each frozen candidate qualification cycle.

## Goal

Coordinate independent security, performance and cross-surface proof on exact frozen provider candidates without changing product behavior to make tests easier.

## Admission requirements

Before this role begins or resumes:

- allocate the fresh META qualification-evidence child Issue, branch/worktree, PR/task head and exactly one qualification report path required by the shared lifecycle;
- validate the normal PR-backed execution-routing packet against fresh GitHub state, with that report as the sole writable path;
- keep Game/Atlas frozen candidate code/config strictly read-only from this qualification role;
- if qualification discovers that provider-owned test/evidence code must change, stop treating the candidate as frozen and create a separate provider child task with its own Issue/branch/worktree/PR/routing packet; never borrow or fabricate the META qualification PR identity.

A product or provider test/config change invalidates affected evidence and returns the candidate to integration.

Do not weaken retries, tolerances, browser coverage, privacy controls or resource assertions silently.

## Return

```text
ROLE: WA-6Q QUALIFICATION-LEAD
PROVIDER_READ_ONLY: YES
META_QUALIFICATION_EVIDENCE_ISSUE:
META_QUALIFICATION_EVIDENCE_PR:
META_QUALIFICATION_REPORT_PATH:
ROUTING_PACKET_ID_OR_REF:
ROUTING_VALIDATION_REF_OR_RESULT:
FROZEN_GAME_CANDIDATE:
FROZEN_ATLAS_CANDIDATE:
SECURITY_EVIDENCE:
PERFORMANCE_EVIDENCE:
CROSS_SURFACE_EVIDENCE:
PROVIDER_CHILD_TASKS_CREATED:
FACTS:
INFERENCES:
UNKNOWNS:
```

---

# WA-7I — FINAL-INTEGRATION-LEAD

ALIAS:
`OTERYN-WORLD-ATLAS-FINAL-INTEGRATION-LEAD`

EFFORT:
Extra High.

LIFECYCLE:
META #79 plus provider final integration Issues.

## Goal

Perform late integration and cutover only after Game/Atlas candidates, bundle/export/bridge identities, security, performance and cross-surface E2E are all compatible.

## Rules

- shared routing validation above is PASS for the current task packet;
- integrate Game and Atlas independently through their own protected gates;
- preserve each provider's exact pre-squash PR head separately from the resulting protected-main/release SHA;
- bind required checks/review to the pre-squash PR head and retain immutable merge evidence linking that exact head to the exact resulting main/release SHA;
- no force-push/rewrite of published task history by default;
- refresh current `main`, merge-up, rerun invalidated exact-head proof;
- record exact merge/main/deployed/candidate identities;
- public Atlas merged-main live acceptance remains Atlas-owned;
- native client acceptance remains Game-owned;
- META records the final non-floating tuple only after provider evidence is immutable;
- do not remove legacy paths during cutover unless their dedicated removal gate is independently satisfied.

Return the complete coordinator completion report defined by the main programme prompt.
