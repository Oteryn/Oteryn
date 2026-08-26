# Unified Oteryn World Atlas release compatibility contract

Lifecycle: `Oteryn/Oteryn#79` under parent programme `Oteryn/Oteryn#75`.

Status: proposed until protected-merged with the World Atlas architecture packet; after merge this contract is the canonical META definition of the exact compatibility tuple and terminal cutover evidence.

## Purpose

This contract closes the release-evidence boundary between Game, Atlas and META. It prevents terminal compatibility from being inferred when the exact produced Game artifact, the exact client-embedded Atlas bundle, the exact public deployed Atlas bundle, or the canonical META compatibility record is not independently identified.

It normatively refines the shorthand tuple lists in the implementation plan, programme coordinator and closeout auditor. Where a shorthand list omits a field required here, this contract wins. It records immutable provider identities/evidence only and does not duplicate provider schemas.

## 1. Required immutable tuple

The final compatible tuple must contain all applicable identities below as independent values:

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

Producer source/profile/world revision are not substitutes for produced-artifact identity. Atlas evidence must prove which exact Game artifact was consumed and which exact embedded bundle was built from the accepted input.

Public Atlas and the Game client remain independent release/failure domains. Therefore the tuple separately records the bundle actually served by the public deployment. `public_atlas_bundle_relation_to_embedded` is `SAME_BUNDLE` when both surfaces use the same bundle bytes, or `COMPATIBLE_INDEPENDENT` when public Atlas intentionally advances or rolls back independently. In the latter case the public bundle version/digest may differ, but immutable deployment and compatibility evidence are mandatory.

## 2. Required chain of custody

Terminal evidence must establish:

```text
Game producer revision/profile + world/content revision
        -> exact produced Game Atlas manifest/payload digest
        -> Atlas verified ingestion/build evidence
        -> Atlas Core/API identity
             |                         |
             v                         v
 exact embedded bundle          exact public deployed bundle
             |                         |
             v                         v
 Game client candidate      public Atlas deployment identity
 pinning embedded digest    bound to deployed bundle digest
```

A missing or inferred link is `UNKNOWN_BLOCKING`.

## 3. Dedicated canonical META record mechanism V1

The existing generic `ecosystem/compatibility.schema.json` / `ecosystem/releases/*.json` mechanism does not encode every independent World Atlas tuple identity required here. World Atlas terminal cutover must use a dedicated mechanism implemented under `Oteryn/Oteryn#84`:

```text
ecosystem/world-atlas/compatibility.schema.json
ecosystem/world-atlas/releases/<release_id>.json
tools/governance/validate_world_atlas_compatibility.py
```

The #84 lifecycle must integrate the validator into stable `meta-gate` and add deterministic validator regressions. Until #84 is protected-merged and the integration is verified, Wave 7 Task 7E is `WAITING_EXTERNAL: WORLD_ATLAS_COMPATIBILITY_RECORD_MECHANISM_NOT_CANONICAL` and the programme cannot report `DONE`.

### 3.1 Required V1 record semantics

The dedicated schema must require separately typed/validated fields equivalent to:

```text
schema_version = 1
record_kind = "oteryn-world-atlas-compatibility-v1"
release_id

game.repository
game.main_or_release_commit_sha
game.atlas_export_profile_version
game.atlas_export_producer_revision
game.atlas_export_artifact_manifest_digest
game.atlas_export_payload_digest_or_root
game.world_content_revision
game.client_release_or_candidate_identity
game.client_pinned_atlas_bundle_digest

atlas.repository
atlas.main_or_release_commit_sha
atlas.core_api_identity
atlas.web_embedded_bundle_version
atlas.web_embedded_bundle_digest
atlas.public_release_or_deployment_identity
atlas.public_deployed_bundle_version
atlas.public_deployed_bundle_digest
atlas.public_bundle_relation_to_embedded
atlas.public_deployment_bundle_evidence_ref
atlas.accepted_game_export_artifact_manifest_digest
atlas.accepted_game_export_payload_digest_or_root

bridge.protocol_version
bridge.capability_profile

security_evidence_refs[]
performance_evidence_refs[]
cross_surface_e2e_refs[]
rollback_evidence_refs[]
provider_required_check_refs[]
```

Exact JSON property spelling is frozen by #84, but every semantic field above must remain independently represented. Every required evidence-reference array is semantically a non-empty set of immutable evidence identities, not merely an array that may be present but empty.

### 3.2 Required validator invariants

The validator integrated into `meta-gate` must fail closed unless at least:

- schema/version/kind, filename and provider-coordinate rules are satisfied;
- required Git identities and SHA-256 artifact fields have the canonical immutable formats;
- required tuple fields are non-empty and independent;
- Atlas accepted Game manifest digest equals Game produced manifest digest;
- Atlas accepted Game payload digest/root equals Game produced payload digest/root;
- Game client pinned bundle digest equals Atlas embedded bundle digest;
- public bundle relation is exactly `SAME_BUNDLE` or `COMPATIBLE_INDEPENDENT`;
- for `SAME_BUNDLE`, public deployed bundle digest equals embedded bundle digest;
- for `COMPATIBLE_INDEPENDENT`, immutable evidence binds the named public deployment to its separately recorded public bundle digest and proves compatibility with the recorded Game export/world contract;
- every required evidence-reference array is present **and non-empty**;
- every evidence reference is validated as an immutable supported identity appropriate to its class, such as an exact repository + PR/review/run/job/check/artifact/deployment identifier, an exact 40-hex commit SHA, or a digest-bound artifact identity; floating branches, `latest`, mutable aliases/URLs, narrative `PASS`, or otherwise unpinned references are rejected;
- duplicate or contradictory references do not silently satisfy a required evidence class;
- floating or mutable release identities are rejected.

The #84 implementation must include negative tests for empty evidence arrays, mutable/malformed evidence references, duplicate/contradictory evidence where material, cross-link and deployment/bundle mismatches, plus positive fixtures for both bundle-relation modes.

### 3.3 No alternate terminal encoding

Until a later accepted change supersedes this contract, generic release records, Issue text, Markdown tables or unvalidated JSON cannot substitute for the dedicated World Atlas V1 record.

## 4. META compatibility record must be canonical

Issue #79 may coordinate and stage the tuple, but terminal `DONE` requires the final World Atlas record to:

1. exist under `ecosystem/world-atlas/releases/<release_id>.json`;
2. validate with the canonical schema/validator from #84;
3. be proposed through a dedicated META PR with exact head SHA;
4. pass current exact-head META checks/review, including the dedicated validator through `meta-gate`;
5. be protected-squash-merged to `Oteryn/Oteryn:main`;
6. have the exact squash-merge SHA recorded;
7. be read back from that protected-main SHA at the exact record path;
8. pass post-merge `meta-gate` on that exact protected-main SHA.

## 5. Required META cutover evidence identifiers

Independent closeout must record at least:

```text
meta_compatibility_schema_path
meta_compatibility_validator_path
meta_compatibility_record_path
meta_compatibility_pr_number
meta_compatibility_pr_head_sha
meta_compatibility_pr_required_check_refs
meta_compatibility_pr_review_evidence_refs
meta_compatibility_squash_merge_sha
meta_compatibility_post_merge_meta_gate_run_or_check_ref
```

## 6. Provider evidence requirements

Game evidence must bind export profile/version, producer revision, world/content revision, exact produced export manifest/payload digest, deterministic producer validation, provider merge/check evidence when applicable, immutable accepted exact-head provider review evidence for every provider PR whose policy requires review, and the client identity plus exact Atlas embedded bundle digest it packages/pins.

Atlas evidence must bind the exact Game export digests accepted by ingestion, Atlas Core/API identity, source/release identity, exact embedded bundle version/digest, exact public deployed bundle version/digest, immutable deployment evidence binding public deployment identity to its bundle, the declared public/embedded relation, provider merge/check/live-acceptance evidence, and immutable accepted exact-head provider review evidence for every provider PR whose policy requires review.

Provider PR/merge identity and required-check success do not substitute for required review evidence. Independent closeout must expose Game and Atlas provider review-evidence references separately so a terminal verdict can prove which exact review satisfied each provider gate.

## 7. Failure semantics

Return `NOT_DONE` / `UNKNOWN_BLOCKING` if any required artifact identity, chain-of-custody link, client/embedded binding, public-deployment/bundle binding, independent-bundle compatibility evidence, non-empty immutable evidence-reference class, required provider or META exact-head review evidence, #84 schema/validator/meta-gate integration, protected META compatibility merge/readback/check evidence, or immutable tuple field is absent, floating, malformed or contradictory. These conditions cannot be waived by narration.

## 8. Relationship to independent closeout

`OTERYN-WORLD-ATLAS-CLOSEOUT-AUDITOR` is the terminal verifier of this contract. Its `FINAL_VERDICT: DONE` is valid only when it returns the immutable Game artifact, embedded Atlas bundle, public deployed Atlas bundle, Game client, public deployment and canonical validated META record evidence required here.

The programme coordinator may not report terminal `DONE` before that independent verdict.