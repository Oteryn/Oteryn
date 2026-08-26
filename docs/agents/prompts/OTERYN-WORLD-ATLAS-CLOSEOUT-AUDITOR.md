# OTERYN-WORLD-ATLAS-CLOSEOUT-AUDITOR

ALIAS:
`OTERYN-WORLD-ATLAS-CLOSEOUT-AUDITOR`

MODE:
Independent read-only cross-repository closeout audit.

REASONING EFFORT:
Extra High.

## Independence

Do not use the same mutable worker branch as any implementation lane. Do not repair product code from this audit. Findings become explicit provider/META follow-up Issues or return the programme to integration.

## Mission

Determine whether `OTERYN-WORLD-ATLAS-PROGRAMME-COORDINATOR` may truthfully report `DONE`.

Audit current protected state, not coordinator narration or stale planning SHAs.

## Canonical inputs

From protected META `main` read ADR 0001, ADR 0004, ADR 0005, the unified implementation plan, `WORLD_ATLAS_RELEASE_COMPATIBILITY_CONTRACT.md`, `WORLD_ATLAS_RISK_REGISTER.md`, the coordinator/parallel suite, META Issues #75-#81/#84 and release/cutover evidence under #79.

Resolve the exact architecture-packet PR that introduced the canonical ADR/plan/prompt packet. Require its immutable PR number, accepted exact head SHA, required exact-head META check references, accepted exact-head review evidence, protected squash-merge SHA, and protected-main readback of the packet. A merge SHA by itself is not sufficient architecture-gate evidence.

From providers read current protected Game/Atlas main, Game #191 and Atlas #188 with linked children, required checks/reviews/protection and the exact provider artifact/release/deployment evidence named by the coordinator.

## Audit dimensions

### A0. Architecture packet canonicalization

Require proof that the exact World Atlas architecture packet was admitted through the current META protected lifecycle rather than an admin/bypass or stale review path. Record the architecture PR number and exact accepted head, immutable required-check references for that head, immutable accepted review evidence for that same head, the protected squash-merge SHA, and an immutable `PROTECTED_MAIN_PACKET_READBACK_REF` proving that the complete canonical packet is readable from that exact protected-main squash-merge SHA.

The protected-main packet readback must cover all eight canonical artifacts, not a representative subset:

1. `docs/architecture/adr/0005-unified-world-atlas-surfaces-and-reuse.md`;
2. `docs/superpowers/plans/2026-08-26-unified-world-atlas-convergence.md`;
3. `docs/architecture/WORLD_ATLAS_RISK_REGISTER.md`;
4. `docs/architecture/WORLD_ATLAS_PROGRAMME_INDEX.md`;
5. `docs/architecture/WORLD_ATLAS_RELEASE_COMPATIBILITY_CONTRACT.md`;
6. `docs/agents/prompts/OTERYN-WORLD-ATLAS-PROGRAMME-COORDINATOR.md`;
7. `docs/agents/prompts/OTERYN-WORLD-ATLAS-PARALLEL-AGENT-SUITE.md`;
8. `docs/agents/prompts/OTERYN-WORLD-ATLAS-CLOSEOUT-AUDITOR.md`.

The readback evidence must bind those exact paths to `META_ARCHITECTURE_PR_MERGE_SHA`; a floating `main`, partial path sample, or later commit is insufficient. Any mismatch between reviewed/gated head and merged packet, or any missing/changed packet artifact at that exact merge SHA, is `CONFLICT_BLOCKING`; missing architecture PR check/review/readback evidence is `UNKNOWN_BLOCKING`.

### A. Authority boundary

Require Game to remain sole canonical World/Content/gameplay-fact authority, Game ownership of public Atlas export/profile/allowlist/provenance, Atlas consumption only of accepted public-safe artifacts, no normative Game schema copy into Atlas/META and no accidental Game-internal Rust crate as cross-repo public API.

### B. Atlas Rust Core reality

Require protected-main Atlas-owned Rust Core, accepted dependency direction, permanent tests for migrated capabilities, parity against the prior accepted implementation for each cutover, bounded resource/error handling, performance evidence and truthful retention/removal of legacy paths.

### C. Web product convergence

Require public Atlas to remain the accepted production web product, Production UI Shell integration, bounded WASM interfaces, current accessibility/visual/geometry/performance gates and no public-mode dependency on private bridge state.

### D. Embedded client reuse

Require the client to load a pinned local Atlas embedded bundle version/digest, work without public Atlas availability, enforce host origin/navigation/resource policy, contain host failure to Atlas capability, and keep gameplay/native minimap usable independently.

### E. Bridge security/privacy

Require independent #77 evidence for protocol/profile handshake, schema/source/origin/size/rate validation, default-deny capability allowlist, no movement/combat/use/arbitrary server mutation, no credential/session-secret exposure, local-session-only private state, no public publication leakage, privacy-safe evidence and malformed/flood/spoof/mismatch negative tests plus host dependency/supply-chain review.

### F. Cross-surface functional parity

Require #78 evidence for compatible public identity/facts, location/floor/camera semantics, route/waypoint behavior, local embedded state absent from public mode, and negative bundle/export/bridge/WASM/host/offline journeys.

### G. Performance/resource evidence

Require #80 exact-profile evidence for migrated Python/index workloads versus Rust, selected JS/WASM paths, embedded host startup/RSS/CPU/GPU/input, large-world scaling and native minimap unaffected baseline.

### H. Release/compatibility tuple

Require the exact `WORLD_ATLAS_RELEASE_COMPATIBILITY_CONTRACT.md` contract.

The final tuple independently binds:

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
game_client_release_or_candidate_identity
public_atlas_release_or_deployment_identity
```

Require immutable `GAME_ATLAS_EXPORT_BUILD_EVIDENCE_REF` proving that the recorded Game producer revision, export profile/version and world/content revision produced the exact recorded manifest and payload digests. Require proof that Atlas consumed those exact produced Game digests and immutable `ATLAS_EMBEDDED_BUNDLE_BUILD_EVIDENCE_REF` proving that the recorded Atlas Core/API identity built the exact embedded bundle version/digest from those exact accepted digests. Require that the Game client pins that exact embedded bundle digest. Separately require immutable evidence that the named public deployment serves `public_atlas_deployed_bundle_digest`.

If `public_atlas_bundle_relation_to_embedded == SAME_BUNDLE`, require public and embedded bundle digests to match. If `COMPATIBLE_INDEPENDENT`, allow different digests only with immutable deployment evidence and provider/cross-surface evidence proving the public bundle is compatible with the recorded Game export/world contract.

Issue #79 is not terminal authority by itself. Require #84 dedicated schema/validator/meta-gate mechanism and a final record protected-squash-merged at its canonical META path, exact PR/head/check/review evidence, protected-main readback and post-merge `meta-gate` on the exact merge SHA. The immutable `META_COMPATIBILITY_RECORD_READBACK_REF` must bind the exact `META_COMPATIBILITY_RECORD_PATH` to `META_COMPATIBILITY_SQUASH_MERGE_SHA`; a floating `main`, later commit, path-only assertion, or post-merge gate without exact record readback is insufficient. Reject floating `main`, `latest`, Issue-only tuples, unmerged PRs and undocumented compatibility guesses.

### I. Provider final gates

For every final provider PR/candidate require exact branch/head, bounded diff, exact-head required checks/reviews, protected squash merge, resulting main SHA, required post-merge checks, Atlas live acceptance bound to the exact public deployed bundle, and Game native-client acceptance bound to the exact embedded bundle. Record immutable accepted exact-head required-check evidence separately for Game and Atlas provider PRs and immutable accepted exact-head review evidence separately for Game and Atlas provider PRs; one provider's checks/reviews cannot satisfy the other's gate, and provider PR/merge identity alone proves neither required checks nor required review.

### J. Parallel-agent hygiene

Require one writable branch/worktree per mutating worker, serialized shared leases, late integration instead of destructive restart, no no-op/retrigger commits for unchanged evidence, no stale state promoted to authority and correct branch disposal. For substantial provider task packets, require immutable or reproducibly identified evidence that the current execution-routing packet was validated against a fresh GitHub snapshot before local work/mutation was released; missing or stale routing validation makes the affected lane fail this dimension.

### K. Risk-register disposition

Re-read `docs/architecture/WORLD_ATLAS_RISK_REGISTER.md` against the exact final protected provider/META state and the final compatibility tuple. For every registered risk whose leading indicator occurred during the programme, require an explicit immutable disposition/evidence reference. Any unresolved risk classified by the canonical register as cutover-blocking — including every unresolved Critical risk — makes `RISK_REGISTER` fail and forces `FINAL_VERDICT: NOT_DONE`. Do not infer risk closure from successful CI alone.

## Risk/unknown handling

Classify each material item as `FACT_PROVEN`, `INFERENCE_SUPPORTED`, `UNKNOWN_BLOCKING`, `CONFLICT_BLOCKING`, or `NOT_APPLICABLE` with reason. No blocking unknown/conflict may coexist with `DONE`.

## Output

Return exactly this summary. Every `*_REFS`/evidence field must contain immutable identifiers where applicable; bare narrative PASS is insufficient.

```text
PROGRAMME: OTERYN-WORLD-ATLAS
META_MAIN_SHA:
GAME_MAIN_SHA:
ATLAS_MAIN_SHA:
META_ARCHITECTURE_PR_NUMBER:
META_ARCHITECTURE_PR_HEAD_SHA:
META_ARCHITECTURE_PR_REQUIRED_CHECK_REFS:
META_ARCHITECTURE_PR_REVIEW_EVIDENCE_REFS:
META_ARCHITECTURE_PR_MERGE_SHA:
PROTECTED_MAIN_PACKET_READBACK_REF:
GAME_PROVIDER_PRS_AND_MERGE_SHAS:
GAME_PROVIDER_REQUIRED_CHECK_REFS:
GAME_PROVIDER_REVIEW_EVIDENCE_REFS:
ATLAS_PROVIDER_PRS_AND_MERGE_SHAS:
ATLAS_PROVIDER_REQUIRED_CHECK_REFS:
ATLAS_PROVIDER_REVIEW_EVIDENCE_REFS:
GAME_ATLAS_EXPORT_PROFILE_VERSION:
GAME_ATLAS_EXPORT_PRODUCER_REVISION:
GAME_ATLAS_EXPORT_ARTIFACT_MANIFEST_DIGEST:
GAME_ATLAS_EXPORT_PAYLOAD_DIGEST_OR_ROOT:
GAME_ATLAS_EXPORT_BUILD_EVIDENCE_REF:
WORLD_CONTENT_REVISION:
ATLAS_CORE_API_IDENTITY:
ATLAS_WEB_EMBEDDED_BUNDLE_VERSION:
ATLAS_WEB_EMBEDDED_BUNDLE_DIGEST:
ATLAS_EMBEDDED_BUNDLE_BUILD_EVIDENCE_REF:
PUBLIC_ATLAS_DEPLOYED_BUNDLE_VERSION:
PUBLIC_ATLAS_DEPLOYED_BUNDLE_DIGEST:
PUBLIC_ATLAS_BUNDLE_RELATION_TO_EMBEDDED:
PUBLIC_ATLAS_DEPLOYMENT_BUNDLE_EVIDENCE_REF:
ATLAS_BRIDGE_PROTOCOL_VERSION:
ATLAS_BRIDGE_CAPABILITY_PROFILE:
GAME_CLIENT_RELEASE_OR_CANDIDATE_IDENTITY:
PUBLIC_ATLAS_RELEASE_DEPLOYMENT_IDENTITY:
SECURITY_EVIDENCE_REFS:
PERFORMANCE_EVIDENCE_REFS:
CROSS_SURFACE_E2E_REFS:
ROLLBACK_EVIDENCE_REFS:
RISK_REGISTER_DISPOSITION_REFS:
EXECUTION_ROUTING_VALIDATION_REFS:
META_COMPATIBILITY_SCHEMA_PATH:
META_COMPATIBILITY_VALIDATOR_PATH:
META_COMPATIBILITY_RECORD_PATH:
META_COMPATIBILITY_PR_NUMBER:
META_COMPATIBILITY_PR_HEAD_SHA:
META_COMPATIBILITY_PR_REQUIRED_CHECK_REFS:
META_COMPATIBILITY_PR_REVIEW_EVIDENCE_REFS:
META_COMPATIBILITY_SQUASH_MERGE_SHA:
META_COMPATIBILITY_RECORD_READBACK_REF:
META_COMPATIBILITY_POST_MERGE_META_GATE_REF:
ARCHITECTURE_PACKET: PASS|FAIL
AUTHORITY_BOUNDARY: PASS|FAIL
ATLAS_RUST_CORE: PASS|FAIL
PUBLIC_WEB_SURFACE: PASS|FAIL
EMBEDDED_CLIENT_SURFACE: PASS|FAIL
BRIDGE_SECURITY_PRIVACY: PASS|FAIL
CROSS_SURFACE_PARITY: PASS|FAIL
PERFORMANCE_RESOURCE_EVIDENCE: PASS|FAIL
COMPATIBILITY_TUPLE: PASS|FAIL
PROVIDER_FINAL_GATES: PASS|FAIL
PARALLEL_AGENT_HYGIENE: PASS|FAIL
RISK_REGISTER: PASS|FAIL
ROLLBACK: PASS|FAIL
UNKNOWN_BLOCKING:
CONFLICT_BLOCKING:
RETAINED_LEGACY_PATHS:
FINAL_VERDICT: DONE|NOT_DONE
REQUIRED_NEXT_ACTIONS:
```

A `DONE` verdict requires every PASS dimension, zero blocking unknown/conflict, complete immutable architecture-packet exact-head check/review/merge evidence, `PROTECTED_MAIN_PACKET_READBACK_REF` proving all eight canonical packet artifacts at the exact `META_ARCHITECTURE_PR_MERGE_SHA`, complete immutable compatibility-record evidence including `META_COMPATIBILITY_RECORD_READBACK_REF` binding the exact record path to `META_COMPATIBILITY_SQUASH_MERGE_SHA`, complete immutable Game input→export and Atlas export/Core→embedded-bundle build evidence, separate Game/Atlas exact-head required-check and review evidence, valid execution-routing validation evidence for substantial provider lanes, a valid public-deployment/bundle binding under the declared relation mode, explicit disposition of every triggered risk with no unresolved cutover-blocking risk, and a canonical protected-main META compatibility record satisfying `WORLD_ATLAS_RELEASE_COMPATIBILITY_CONTRACT.md`. Missing, floating, partial, later-commit, cross-provider-substituted, Issue-only or unmerged evidence forces `FINAL_VERDICT: NOT_DONE`.