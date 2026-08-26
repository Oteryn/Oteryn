# Unified Oteryn World Atlas Convergence Implementation Plan

> Execute task-by-task with isolated branches/worktrees and the current repository governance. Parallel work is allowed only when the dependency and ownership rules below permit it.

**Goal:** converge Oteryn World Atlas into one reusable product capability: Game-owned authoritative exports feed an Atlas-owned Rust Core and one web product lineage that serves both public Atlas and a locally packaged embedded native-client Atlas, while gameplay minimap/HUD stays native Rust/wgpu and private live state stays local.

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
- Full embedded Atlas content is local/pinned/digest-bound; public Atlas availability is not a gameplay dependency.
- Native gameplay minimap/HUD remains native and usable when the embedded Atlas host is absent, incompatible, crashed or disabled.
- Private/live client state is local-session-only and never a public Atlas publication input.
- Bridge V1 is non-authoritative UI integration only; no movement/combat/item-use/arbitrary server mutation.
- Every substantial new/resumed task gets a fresh GitHub snapshot and a passing canonical execution-routing packet before work is released.
- One mutating task = one Issue, one branch/worktree, one PR, exact owned paths and immutable `admission_main_sha`.
- Moving `main` is `UPSTREAM_ADVANCED`, not a reason to restart; integrate late and rerun only invalidated proof.
- Shared Cargo/workspace/toolchain, Game client composition, Atlas FullWorld/shared shell, workflows/CI, META compatibility record and final integration are serialized leases.
- `WORLD_ATLAS_RISK_REGISTER.md` is re-read at provider design freeze, host selection, candidate freeze and final cutover. Triggered unresolved Critical risks block; triggered High risks require explicit mitigation evidence.
- No provider production/live deployment is authorized by this META architecture packet itself.

Planning SHAs in this document are provenance only. All execution resolves live state.

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

## 3. Required immutable identity model

Keep the stages below separate for **each provider**:

```text
provider_pr_head_sha
        |
        +--> exact-head required checks
        +--> exact-head accepted review
        |
        v
immutable provider_merge_evidence_ref
        |
        v
provider_main_or_release_commit_sha
        |
        +--> post-merge checks/live acceptance/deployment evidence as applicable
```

Never bind pre-squash check/review evidence to the resulting squash/main SHA. Never let a reviewed PR head prove a different merge result. The final record therefore preserves, independently:

```text
game_provider_pr_head_sha
game_main_or_release_commit_sha
game_provider_merge_evidence_ref
atlas_provider_pr_head_sha
atlas_main_or_release_commit_sha
atlas_provider_merge_evidence_ref

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
atlas_bridge_compatibility_handshake_evidence_ref
game_client_release_identity
public_atlas_release_or_deployment_identity
```

Additional chain-of-custody evidence is mandatory:

- Game export-build evidence binds producer revision + export profile/version + world/content revision → exact produced manifest/payload digests.
- Atlas embedded-bundle build evidence binds exact accepted Game digests + Atlas Core/API identity → exact embedded bundle version/digest.
- Game client pins the exact embedded bundle digest.
- Bridge compatibility/handshake evidence binds exact client identity + pinned embedded bundle version/digest + supported bridge range/profile + selected protocol/profile + world/content compatibility identity.
- Public deployment evidence binds the named public deployment identity → exact public deployed bundle version/digest.

## 4. Stable conceptual interfaces

### 4.1 Game → Atlas artifact

Must carry producer revision, export profile version, world/content revision, public capabilities, payload manifest/digests, provenance and minimum consumer requirements. Only Game-selected public-safe facts are allowed.

### 4.2 Atlas Core

Provider design freezes bounded deterministic operations equivalent to verified artifact ingestion, world/spatial queries, search/intelligence, entity/location resolution, routing/path products and capability-state reporting. DOM/browser state is not a second authority.

### 4.3 Embedded bundle

Manifest identifies exact bundle version/digest, Atlas Core/API identity, supported Game export profiles, supported bridge range/profile, required host capabilities and file/asset digests.

### 4.4 Local bridge

Handshake binds protocol, capability profile, exact Game client identity, exact pinned Atlas bundle and world/content compatibility identity. Mismatch disables the bridge/live overlay fail-closed.

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
Wave 6 qualification evidence lane + provider qualification
                  v
Wave 7 provider integration/cutover + #84 V1 record
                  v
independent closeout auditor
                  v
Wave 8 legacy retirement
```

Normal maximum reasoning/scout lanes: 5. Normal mutating provider lanes: 2–3 disjoint lanes.

## 6. Wave 0 — provider-read-only / META evidence-only discovery

Wave 0 starts only after the architecture packet is canonical on protected META `main`.

Each independently launched WA-0A..WA-0E gets:

- fresh META child Issue under #75;
- dedicated META branch/worktree and PR/task head;
- exactly one disjoint `docs/evidence/world-atlas/wave0/<role>.md` report path or coordinator-recorded equivalent;
- normal PR-backed routing packet validated against fresh GitHub state;
- write authority only to that META report.

Game/Atlas/provider runtime/config/Cargo/workflow/shared-shell/production paths remain read-only. There is no PR-less Wave-0 route.

### 0A Game contract scout

Inventory current public Atlas contracts/profiles, deterministic producer/provenance, world/content identities, fixtures, gaps, optional public Rust codec value and active ownership conflicts. Persist only the META report.

### 0B Atlas migration scout

Trace relevant `tools/**`, `src/browser/**`, `web/**`, publication and tests. Classify components as keep web/UI/glue, Rust CLI/Core/WASM candidate, benchmark-gated or do-not-migrate. Identify parity oracles, interfaces and shared leases.

### 0C Client-host scout

Identify client composition boundary and viable embedded web hosts. Compare local origin, navigation/CSP/resource controls, JS↔native messaging, crash isolation, packaging, accessibility/input, offline behavior, license/supply chain and benchmark plan.

### 0D Security scout

Threat-model malicious/corrupt bundle, XSS/navigation, bridge spoof/replay/flood, privilege escalation, credential leakage, private-state publication/log leakage, stale artifacts, host crash/resource exhaustion and dependency compromise.

### 0E Verification/performance scout

Map current provider gates, representative full-world/parity fixtures, cross-surface journeys, heavy-runner constraints and benchmark evidence format.

Wave-0 gate: review all five META evidence PR handoffs and freeze real gaps/unknowns before provider design mutation.

## 7. Wave 1 — provider design freeze

Game and Atlas designs may run concurrently. Before acceptance, execute the design-freeze risk checkpoint.

### 1A Game design

Freeze export gaps/identities, embedded-host adapter, native minimap independence, bridge native endpoint/profile, bundle pinning, failure behavior, tests and serialized Cargo/client-composition leases.

### 1B Atlas design

Freeze Rust workspace/crates, pure-core dependency direction, Game artifact consumer boundary, parity seams, Core/WASM APIs, embedded bundle manifest, bridge web endpoint, Production UI Shell integration, rollback/capability flags, tests and FullWorld/workflow leases.

### 1C Security profile

Freeze trusted origin, network/navigation/CSP policy, capability allowlist, message framing/version/size/rate validation, privacy/retention, crash behavior, supply-chain policy and negative tests. Reject hosts that cannot satisfy it.

## 8. Wave 2 — foundations

### 2A Atlas Rust foundation

Under serialized root lease add the Atlas Rust workspace/core/model foundation, deterministic bounded errors/resources, unit/property tests and CI/lint/security checks. No production capability cutover yet.

### 2B Game export gaps

Run only for proven gaps. Deliver provider-owned profile/schema evolution, producer changes, permanent tests, exact fixtures and Game export-build evidence. If no gap, record `NO_CHANGE_REQUIRED`; do not create a cosmetic branch.

### 2C Embedded host prototype

Prototype only isolated Game paths. Measure local content, navigation isolation, startup, RSS/CPU/GPU, input/focus, crash/hang isolation, offline operation, packaging and dependency security. Execute host-selection risk checkpoint before accepting a host.

## 9. Wave 3 — Atlas Core lanes

After the foundation/API is canonical, release up to three disjoint Atlas lanes:

- 3A verified ingestion/compiler/index parity;
- 3B spatial/query core;
- 3C search/intelligence core.

Every lane uses RED→GREEN permanent tests, current accepted oracle/parity, deterministic results, bounded resources, benchmark evidence and rollback/shadow path. Shared shell/CI edits require serialized leases.

## 10. Wave 4 — Web/WASM + reusable bundle

- Expose reusable core behavior through bounded WASM only where justified.
- Keep DOM/accessibility/UI in web technology.
- Cut over capability-by-capability with shadow/parity proof and rollback retained.
- Produce one deterministic public/embedded bundle lineage with exact manifest/file digests.
- Public mode has no private bridge dependency; embedded mode enables only accepted local bridge.
- Preserve immutable Atlas build evidence linking exact accepted Game digests + Core identity → exact embedded bundle version/digest.

## 11. Wave 5 — native client integration

Requires accepted host, immutable embedded bundle candidate and frozen bridge/security profile.

- production host loads only pinned local bundle and contains failures;
- native bridge validates handshake/source/size/rate/capabilities and exposes no gameplay mutation/credentials;
- Atlas embedded endpoint keeps local state ephemeral and unavailable in public mode;
- native minimap/waypoint interop stays narrow and native-minimap independent;
- produce immutable bridge handshake/compatibility evidence usable by final release record.

## 12. Wave 6 — qualification

Before expensive qualification, freeze exact provider candidate PR heads/artifact digests and execute the candidate-freeze risk checkpoint.

### 12.1 WA-6Q qualification-evidence lifecycle

`OTERYN-WORLD-ATLAS-QUALIFICATION-LEAD` is provider-read-only over frozen candidates but not lifecycle-free. Each qualification cycle gets:

- fresh META qualification-evidence child Issue under #78/#80;
- dedicated META branch/worktree and PR/task head;
- exactly one `docs/evidence/world-atlas/qualification/<candidate-or-role>.md` report path or recorded equivalent;
- normal PR-backed routing packet validated against fresh GitHub state;
- write authority only to that META report.

Game/Atlas frozen candidate code/config remains read-only for WA-6Q. If provider-owned test/evidence code must change, create a separate provider child Issue/branch/worktree/PR/routing packet, invalidate affected frozen evidence and return the candidate to integration. There is no PR-less WA-6Q route.

### 12.2 Qualification proof

- #77 security: origin/navigation/CSP, bridge limits/allowlist, secret/private-state protections, malicious input/host/dependency failures.
- #80 performance: exact machine/profile, Rust migration comparisons, WASM/bundle startup, host RSS/CPU/GPU/input and native minimap baseline.
- #78 cross-surface E2E: compatible public facts/location/floor/camera/routing, embedded-only local state, public no-private-state, host failure/minimap independence and negative bundle/export/bridge cases.

Any product/config change creates a new candidate and invalidates affected evidence.

## 13. Wave 7 — provider integration, cutover and V1 record

Execute final-cutover risk checkpoint first.

### 7A Candidate evidence freeze

Freeze pre-integration identities that already exist:

- exact Game provider PR-head candidate and its exact-head checks/review;
- exact Atlas provider PR-head candidate and its exact-head checks/review;
- Game export profile/producer/world revision + export-build evidence + exact produced digests;
- Atlas accepted Game digests + Core identity + embedded-bundle build evidence + exact bundle;
- candidate Game client + pinned bundle;
- bridge protocol/profile + immutable candidate handshake evidence;
- security/performance/E2E/rollback evidence.

Do not invent resulting squash/main SHAs or terminal public deployment identities before they exist.

### 7B Provider final integration

For **each provider independently**:

1. refresh protected `main`, merge-up if needed and rerun invalidated exact-head proof;
2. freeze the exact **pre-squash provider PR head SHA** that passed required checks/review;
3. record immutable required-check/review evidence resolving to that exact PR head;
4. protected-squash-merge the PR;
5. record the exact resulting protected `main`/release commit SHA;
6. record immutable provider merge evidence proving `provider_pr_head_sha -> provider_main_or_release_commit_sha`;
7. run required post-merge checks/live acceptance against the resulting main/release SHA.

Checks/reviews bound only to the post-squash SHA are invalid because that SHA was not the reviewed PR head. Conversely, a reviewed PR head without merge-binding evidence does not prove which protected-main commit was produced. Old/stale/cross-provider evidence is blocking.

### 7C Public Atlas cutover

Atlas performs merged-main deployment/live acceptance. Record exact public deployment identity, exact deployed public bundle version/digest, immutable deployment→bundle evidence, rollback artifact and declared relation to embedded bundle.

### 7D Native client acceptance

Game acceptance runs against exact embedded bundle digest and final bridge tuple. Preserve immutable handshake evidence binding accepted client + pinned bundle + supported/selected bridge protocol/profile + world/content identity.

### 7E Terminal refreeze + dedicated META World Atlas Compatibility Record V1

1. Refresh/reconcile #84; do not duplicate it.
2. Require canonical #84 schema, validator, deterministic regressions and `meta-gate` integration.
3. If absent, return `WAITING_EXTERNAL: WORLD_ATLAS_COMPATIBILITY_RECORD_MECHANISM_NOT_CANONICAL`.
4. After 7B–7D, terminally refreeze for Game and Atlas separately:
   - provider PR head SHA;
   - provider exact-head required-check refs;
   - provider exact-head review refs;
   - provider resulting protected-main/release SHA;
   - immutable head→resulting-main merge evidence;
   - provider post-merge/live evidence.
5. Refreeze exact Game export-build chain, Atlas embedded-bundle build chain, exact client+bundle bridge handshake chain and exact public deployment→bundle chain.
6. Create final record only at `ecosystem/world-atlas/releases/<release_id>.json` under the #84 schema.
7. Validate every cross-link and reject wrong-stage squash evidence, stale heads, wrong merge result, cross-provider substitution or floating refs.
8. Deliver the record through a dedicated META PR with exact-head checks/review.
9. Protected-squash-merge it, read exact record path back from exact merge SHA and require post-merge `meta-gate` on that SHA.

Issue #79 narration, generic releases, Draft/unmerged PRs or Markdown tuples are not terminal records.

## 14. Wave 8 — legacy retirement

Open separate bounded Atlas removal lifecycles only after the new default has parity/browser/live acceptance, rollback evidence, acceptable performance/security and zero active consumers. No opportunistic cleanup.

## 15. Rollback matrix

| Failure | Response |
| --- | --- |
| Rust compiler/index regression | restore previous accepted capability path until removal gate |
| WASM failure | use retained compatible current path for that capability |
| public deployment regression | Atlas rollback to prior exact public deployment/bundle pair |
| embedded bundle incompatible/corrupt | disable panel or repin prior compatible bundle in a new client candidate; native minimap stays |
| bridge mismatch/failure | disable bridge/live overlay; do not guess compatibility |
| embedded host crash/hang | tear down/disable host; gameplay/native minimap stays |
| private-state leak | fail release, disable bridge profile, sanitize evidence/logging, requalify security |
| Game export incompatible | Atlas rejects/marks unavailable; no legacy-runtime truth fallback |
| bad META compatibility record | retain prior canonical record; do not report DONE |

## 16. Definition of Done

Programme completion requires immutable proof that:

- architecture packet is canonical on protected META main;
- Game/Atlas child work is terminal or evidence-backed `NO_CHANGE_REQUIRED`;
- Game authority boundary remains intact;
- Atlas Rust Core is real, tested, parity-qualified and rollback-capable;
- public and embedded Atlas use the accepted shared Core/bundle architecture;
- embedded Atlas works locally/offline and native minimap remains independent;
- bridge is versioned/default-deny/security-qualified and private state remains local;
- cross-surface journeys and failure cases pass;
- performance/resource evidence exists;
- substantial task routing evidence is fresh and valid, including Wave-0 and WA-6Q PR-backed META evidence lanes;
- for each provider, required checks/review bind the exact pre-squash PR head, immutable merge evidence binds that head to the exact resulting protected-main/release SHA, and post-merge/live evidence binds the resulting SHA;
- Game export-build, Atlas embedded-bundle build, client bundle pin, bridge handshake and public deployment chains are immutable and exact;
- no triggered cutover-blocking risk remains unresolved;
- #84 V1 mechanism is canonical;
- final World Atlas compatibility record is exact-head reviewed/gated, protected-squash-merged, exact-record read back and post-merge `meta-gate` validated;
- fresh independent `OTERYN-WORLD-ATLAS-CLOSEOUT-AUDITOR` returns `FINAL_VERDICT: DONE`;
- retained/removed legacy paths are truthful.

## 17. Coordinator completion report

Return exact:

- META/Game/Atlas protected SHAs and implementation PR/merge identities;
- Game provider PR head, exact-head required-check/review refs, resulting main/release SHA and immutable merge-evidence ref;
- Atlas provider PR head, exact-head required-check/review refs, resulting main/release SHA and immutable merge-evidence ref;
- Game export profile/producer/world revision, exact produced digests and Game export-build evidence;
- Atlas Core/API identity, accepted Game digests, exact embedded bundle and Atlas build evidence;
- exact public deployed bundle/deployment/relation evidence;
- bridge protocol/profile, exact client+bundle handshake evidence and Game client identity;
- routing validation refs including Wave-0 and WA-6Q META evidence Issue/PR/report identities;
- #84 schema/validator/final-record PR/head/merge/readback/post-merge-gate refs;
- security/performance/E2E/rollback/risk disposition evidence;
- retained legacy paths/reasons;
- independent closeout verdict;
- final `DONE|WAITING_EXTERNAL|BLOCKED|STALLED` with exact reason.