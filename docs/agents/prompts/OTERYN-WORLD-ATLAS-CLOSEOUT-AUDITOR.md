# OTERYN-WORLD-ATLAS-CLOSEOUT-AUDITOR

ALIAS:
`OTERYN-WORLD-ATLAS-CLOSEOUT-AUDITOR`

MODE:
Independent provider-read-only / META closeout-evidence-only audit.

REASONING EFFORT:
Extra High.

## Independence, routing and evidence lifecycle

Audit whether `OTERYN-WORLD-ATLAS-PROGRAMME-COORDINATOR` may truthfully report `DONE`. Do not share a mutable implementation branch and do not repair product code from this audit.

This is a substantial task and therefore **not routing-lifecycle-free**. Before the audit begins or resumes:

1. create/refresh a fresh META closeout-evidence child Issue under #75/#81 for the exact terminal candidate/release;
2. assign a dedicated META branch/worktree and PR/task head;
3. assign exactly one report path under `docs/evidence/world-atlas/closeout/<release-id-or-candidate>.md` or coordinator-recorded equivalent;
4. create/refresh a normal PR-backed execution-routing packet whose sole writable owned path is that closeout report;
5. validate the packet against a fresh GitHub live-state snapshot with the canonical routing validator;
6. permit mutation only of that META closeout report while provider/META product/config/runtime surfaces remain read-only.

There is no PR-less closeout route and no borrowed/fabricated provider PR identity. If product/provider evidence must change, return `NOT_DONE` and create a separate owning lifecycle; do not repair it from the auditor branch.

After the audit report is complete, preserve the closeout report PR/head/check/review/merge/readback identity according to current META evidence policy before the coordinator uses it as terminal evidence.

## Canonical inputs

From protected META `main` read ADR 0001/0004/0005, programme index, implementation plan, risk register, release compatibility contract, coordinator/parallel suite, META #75–#81/#84 and release evidence under #79. From providers read current protected Game/Atlas state, Game #191, Atlas #188, linked child PRs, required-check/protection snapshots, reviews, merge evidence, artifacts and deployment evidence.

## A0. Architecture packet canonicalization

Require exact architecture PR number, accepted PR head SHA, successful exact-head `meta-gate` + `ai-review-gate`, accepted R2/deep review, protected squash-merge SHA, and immutable protected-main readback of all eight packet artifacts at that exact merge SHA:

1. `docs/architecture/WORLD_ATLAS_PROGRAMME_INDEX.md`;
2. `docs/architecture/adr/0005-unified-world-atlas-surfaces-and-reuse.md`;
3. `docs/superpowers/plans/2026-08-26-unified-world-atlas-convergence.md`;
4. `docs/architecture/WORLD_ATLAS_RISK_REGISTER.md`;
5. `docs/architecture/WORLD_ATLAS_RELEASE_COMPATIBILITY_CONTRACT.md`;
6. `docs/agents/prompts/OTERYN-WORLD-ATLAS-PROGRAMME-COORDINATOR.md`;
7. `docs/agents/prompts/OTERYN-WORLD-ATLAS-PARALLEL-AGENT-SUITE.md`;
8. `docs/agents/prompts/OTERYN-WORLD-ATLAS-CLOSEOUT-AUDITOR.md`.

Partial/later/floating readback, bypass merge or stale review is blocking.

## A. Authority boundary

Require Game as sole canonical World/Content/gameplay-fact authority; Game owns public Atlas export/profile/allowlist/provenance; Atlas consumes only accepted public-safe artifacts; no normative Game schema copy in Atlas/META and no arbitrary Game-internal crate as cross-repo public API.

## B. Atlas Rust Core

Require protected-main Atlas-owned Rust Core, accepted dependency direction, permanent tests, parity for migrated capabilities, bounded resource/error handling, performance evidence and truthful legacy retention/removal.

## C. Public web product

Require accepted Atlas web product/Production UI Shell, bounded WASM interfaces, accessibility/visual/geometry/performance proof and no public dependency on private bridge state.

## D. Embedded client reuse

Require pinned local Atlas bundle, offline/base operation, host origin/navigation/resource controls, failure containment and independent native gameplay/minimap operation.

## E. Bridge security/privacy

Require #77 default-deny origin/source/schema/size/rate/capability controls, no movement/combat/use/arbitrary server mutation, no credentials/session secrets, local-session-only private state, no public publication leakage, negative tests and dependency/host isolation. Require immutable bridge compatibility/handshake evidence binding exact Game client + exact pinned embedded bundle version/digest + supported bridge range/profile + selected protocol/profile + relevant world/content identity.

## F. Cross-surface parity

Require #78 proof for compatible public facts, location/floor/camera/routing semantics, embedded-only local state and negative bundle/export/bridge/WASM/host/offline journeys.

## G. Performance/resources

Require #80 exact-profile evidence for Rust migrations, selected WASM/browser paths, embedded host startup/RSS/CPU/GPU/input, large-world scaling and native minimap baseline.

## H. Provider gate chain and complete required-check sets

For **Game and Atlas independently** require:

```text
provider_pr_head_sha
  -> immutable provider_required_check_set_evidence_ref
  -> complete exact-head provider_required_check_refs[]
  -> accepted exact-head provider_review_evidence_refs[]
  -> immutable provider_merge_evidence_ref
  -> provider_main_or_release_commit_sha
  -> provider_post_merge_evidence_refs[]
```

The required-check-set evidence must be an immutable snapshot of the provider's applicable final PR/base protection/ruleset state and enumerate the full expected required-check set. Recorded check refs must cover that set completely; a non-empty subset is insufficient. Checks/reviews bind to the exact pre-squash PR head. Merge evidence binds that exact head to the exact resulting protected-main/release commit. Reject stale, missing, subset, wrong-stage, wrong-result or cross-provider evidence.

## I. Artifact build provenance bound to provider revisions

Require Game `GAME_ATLAS_EXPORT_BUILD_SOURCE_COMMIT_SHA` to equal either the exact final Game provider PR head or resulting Game main/release SHA. Game export-build evidence must bind that authorized source SHA plus producer/profile/world identity to exact manifest/payload digests.

Require Atlas `ATLAS_EMBEDDED_BUNDLE_BUILD_SOURCE_COMMIT_SHA` to equal either the exact final Atlas provider PR head or resulting Atlas main/release SHA. Atlas build evidence must bind that authorized source SHA plus exact accepted Game digests and Core identity to exact embedded bundle version/digest.

Reject artifacts from unrelated/stale source revisions even when their standalone digests/build manifests are valid.

## J. Qualification evidence bound to released candidate

Require immutable `QUALIFICATION_CANDIDATE_EVIDENCE_MANIFEST_REF` binding the final qualification generation to the exact released candidate identities: both provider PR heads, exact Game export build source/profile/world/digests, exact Atlas build source/Core/bundle, exact client/pin and bridge tuple; post-deployment/live evidence additionally binds exact public deployment/bundle identity.

Every security, performance, cross-surface E2E and rollback evidence ref must resolve directly to those exact candidate identities or be explicitly bound by that manifest. Evidence from a previous candidate invalidated by product/config/head/artifact/bundle/client/bridge/deployment change is blocking.

## K. Release/compatibility tuple

Require `WORLD_ATLAS_RELEASE_COMPATIBILITY_CONTRACT.md` exactly, including provider PR heads, complete required-check-set snapshots, required checks/reviews, merge bindings, resulting main/release SHAs, authorized Game/Atlas artifact build source SHAs, export/build chains, exact bundles, bridge handshake, qualification manifest/evidence arrays and public deployment/bundle relation.

`SAME_BUNDLE` requires public/embedded digest equality. `COMPATIBLE_INDEPENDENT` requires separately immutable compatibility/deployment evidence.

## L. META compatibility record

Require canonical #84 schema/validator/meta-gate mechanism and final record at `ecosystem/world-atlas/releases/<release_id>.json`. Require exact record PR head/check/review, protected squash merge, exact record-path readback at that merge SHA and post-merge `meta-gate`. Issue text, generic record, Draft/unmerged PR or floating main is insufficient.

## M. Parallel-agent/routing hygiene

Require fresh routing validation for every substantial task. Wave-0 scouts use real PR-backed META evidence-only lifecycles. `WA-6Q` uses a real META qualification-evidence PR/report lane. This terminal auditor itself uses the closeout-evidence lifecycle defined above. Provider test/evidence mutations require separate provider child tasks. No PR-less, borrowed or fabricated routing identity is acceptable.

## N. Risk register

Re-read exact final risk state. Every triggered risk needs immutable disposition/evidence. Any unresolved cutover-blocking risk, including every unresolved Critical risk, forces `NOT_DONE`. CI alone is not risk closure.

## Risk/unknown classification

Use `FACT_PROVEN`, `INFERENCE_SUPPORTED`, `UNKNOWN_BLOCKING`, `CONFLICT_BLOCKING`, `NOT_APPLICABLE`. Blocking unknown/conflict cannot coexist with `DONE`.

## Required output

Return exactly:

```text
PROGRAMME: OTERYN-WORLD-ATLAS
META_MAIN_SHA:
GAME_MAIN_SHA:
ATLAS_MAIN_SHA:
META_CLOSEOUT_EVIDENCE_ISSUE:
META_CLOSEOUT_EVIDENCE_PR:
META_CLOSEOUT_EVIDENCE_PR_HEAD_SHA:
META_CLOSEOUT_REPORT_PATH:
META_CLOSEOUT_ROUTING_PACKET_REF:
META_CLOSEOUT_ROUTING_VALIDATION_REF:
META_ARCHITECTURE_PR_NUMBER:
META_ARCHITECTURE_PR_HEAD_SHA:
META_ARCHITECTURE_PR_REQUIRED_CHECK_REFS:
META_ARCHITECTURE_PR_REVIEW_EVIDENCE_REFS:
META_ARCHITECTURE_PR_MERGE_SHA:
PROTECTED_MAIN_PACKET_READBACK_REF:
GAME_PROVIDER_PR_HEAD_SHA:
GAME_PROVIDER_REQUIRED_CHECK_SET_EVIDENCE_REF:
GAME_PROVIDER_REQUIRED_CHECK_REFS:
GAME_PROVIDER_REVIEW_EVIDENCE_REFS:
GAME_MAIN_OR_RELEASE_COMMIT_SHA:
GAME_PROVIDER_MERGE_EVIDENCE_REF:
GAME_PROVIDER_POST_MERGE_EVIDENCE_REFS:
ATLAS_PROVIDER_PR_HEAD_SHA:
ATLAS_PROVIDER_REQUIRED_CHECK_SET_EVIDENCE_REF:
ATLAS_PROVIDER_REQUIRED_CHECK_REFS:
ATLAS_PROVIDER_REVIEW_EVIDENCE_REFS:
ATLAS_MAIN_OR_RELEASE_COMMIT_SHA:
ATLAS_PROVIDER_MERGE_EVIDENCE_REF:
ATLAS_PROVIDER_POST_MERGE_EVIDENCE_REFS:
GAME_ATLAS_EXPORT_BUILD_SOURCE_COMMIT_SHA:
GAME_ATLAS_EXPORT_PROFILE_VERSION:
GAME_ATLAS_EXPORT_PRODUCER_REVISION:
GAME_ATLAS_EXPORT_ARTIFACT_MANIFEST_DIGEST:
GAME_ATLAS_EXPORT_PAYLOAD_DIGEST_OR_ROOT:
GAME_ATLAS_EXPORT_BUILD_EVIDENCE_REF:
WORLD_CONTENT_REVISION:
ATLAS_EMBEDDED_BUNDLE_BUILD_SOURCE_COMMIT_SHA:
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
ATLAS_BRIDGE_COMPATIBILITY_HANDSHAKE_EVIDENCE_REF:
GAME_CLIENT_RELEASE_OR_CANDIDATE_IDENTITY:
PUBLIC_ATLAS_RELEASE_DEPLOYMENT_IDENTITY:
QUALIFICATION_CANDIDATE_EVIDENCE_MANIFEST_REF:
SECURITY_EVIDENCE_REFS:
PERFORMANCE_EVIDENCE_REFS:
CROSS_SURFACE_E2E_REFS:
ROLLBACK_EVIDENCE_REFS:
RISK_REGISTER_DISPOSITION_REFS:
EXECUTION_ROUTING_VALIDATION_REFS:
WAVE0_META_EVIDENCE_REFS:
QUALIFICATION_META_EVIDENCE_REF:
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

`DONE` requires every PASS dimension, zero blockers, complete architecture admission/readback, both providers' complete PR-head→required-check-set/checks/review→merge→resulting-main chains, build source revisions bound to those provider revisions, complete export/bundle/bridge/deployment chains, qualification evidence bound to the exact released candidate, valid Wave-0/WA-6Q/closeout PR-backed routing evidence, explicit risk dispositions, canonical V1 record with readback/post-merge gate, and truthful rollback/legacy state. Missing, floating, partial, subset, stale, wrong-stage, wrong-source, cross-provider, Issue-only or unmerged evidence forces `FINAL_VERDICT: NOT_DONE`.