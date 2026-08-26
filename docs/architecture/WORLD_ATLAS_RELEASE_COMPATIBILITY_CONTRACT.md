# Unified Oteryn World Atlas release compatibility contract

Lifecycle: `Oteryn/Oteryn#79` under parent programme `Oteryn/Oteryn#75`.

Status: proposed until protected-merged with the World Atlas architecture packet; after merge this contract is the canonical META definition of the exact compatibility tuple and terminal cutover evidence.

## Purpose

This contract closes the release-evidence boundary between Game, Atlas and META. It prevents a programme from being declared compatible merely because producer code, world revision and consumer code are known while the exact Game-produced public Atlas artifact consumed by Atlas is not cryptographically identified, or because a compatibility tuple exists only in an Issue comment/unmerged PR.

This file normatively refines the shorthand tuple lists in:

- `docs/superpowers/plans/2026-08-26-unified-world-atlas-convergence.md`, especially Wave 7 Tasks 7A and 7E;
- `docs/agents/prompts/OTERYN-WORLD-ATLAS-PROGRAMME-COORDINATOR.md`;
- `docs/agents/prompts/OTERYN-WORLD-ATLAS-CLOSEOUT-AUDITOR.md`.

Where a shorthand list omits a field required here, this contract wins. It does not duplicate provider schemas; it records immutable provider identities/evidence only.

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
atlas_bridge_protocol_version
atlas_bridge_capability_profile
game_client_release_or_candidate_identity
public_atlas_release_or_deployment_identity
```

`game_atlas_export_artifact_manifest_digest` identifies the exact immutable manifest/envelope emitted by Game for the Atlas input consumed by the accepted Atlas build. `game_atlas_export_payload_digest_or_root` identifies the exact produced payload bytes or deterministic root referenced by that manifest. Producer source SHA/profile/world revision are not substitutes for produced-artifact identity.

The Atlas consumer/build evidence must prove that the exact produced Game artifact digest/root in the tuple was the input accepted by Atlas, and the final Atlas bundle evidence must prove the exact Atlas bundle digest resulting from that accepted input and Atlas revision/configuration.

## 2. Required chain of custody

Terminal evidence must establish:

```text
Game producer revision/profile + world/content revision
        -> exact produced Game Atlas manifest/payload digest
        -> Atlas verified ingestion/build evidence
        -> Atlas Core/API identity + exact web/embedded bundle digest
        -> Game client candidate/release pinning that bundle digest
        + public Atlas release/deployment identity
```

A broken or inferred link is `UNKNOWN_BLOCKING`; matching display names, timestamps, floating branches or narrative assertions cannot repair it.

## 3. Dedicated canonical META record mechanism V1

The existing generic `ecosystem/compatibility.schema.json` / `ecosystem/releases/*.json` mechanism does **not** currently encode or validate every independent World Atlas tuple identity required by this contract. World Atlas terminal cutover MUST NOT hide these values in unlabeled artifact/evidence arrays or opaque strings merely to pass the generic release validator.

Before the first World Atlas compatibility record can become terminal, a dedicated META implementation lifecycle must add and protect:

```text
ecosystem/world-atlas/compatibility.schema.json
ecosystem/world-atlas/releases/<release_id>.json
tools/governance/validate_world_atlas_compatibility.py
```

That same lifecycle must integrate `validate_world_atlas_compatibility.py` into the stable `meta-gate` execution path and add deterministic validator regressions. Until the mechanism is protected-merged and its `meta-gate` integration is verified, Wave 7 Task 7E is `WAITING_EXTERNAL: WORLD_ATLAS_COMPATIBILITY_RECORD_MECHANISM_NOT_CANONICAL` and the programme cannot report `DONE`.

This dedicated mechanism stores only immutable release/contract/evidence identities owned by Game and Atlas; it is not a provider schema mirror.

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

Exact JSON spelling is frozen by the dedicated mechanism implementation PR, but every semantic field above must remain independently represented; required identities may not be collapsed into opaque notes.

### 3.2 Required validator invariants

The validator integrated into `meta-gate` must fail closed unless at least:

- schema/version/kind and canonical filename rules are satisfied;
- Game and Atlas repository coordinates are exact accepted permanent providers;
- required Git identities are lowercase 40-hex SHAs where applicable;
- every SHA-256 artifact field is `sha256:<64-lowercase-hex>`;
- required tuple fields are non-empty and independently represented;
- `atlas.accepted_game_export_artifact_manifest_digest == game.atlas_export_artifact_manifest_digest`;
- `atlas.accepted_game_export_payload_digest_or_root == game.atlas_export_payload_digest_or_root`;
- `game.client_pinned_atlas_bundle_digest == atlas.web_embedded_bundle_digest`;
- evidence-reference arrays are non-empty when the corresponding programme gate applies;
- unknown critical fields fail closed unless explicit compatible extension semantics allow them;
- floating `main`, `latest`, mutable URLs or unpinned aliases are rejected as terminal identities.

The mechanism implementation must include negative tests for each cross-link mismatch and missing/malformed required identity plus a positive canonical fixture.

### 3.3 No alternate terminal encoding

Until an explicit later accepted change supersedes this section, the terminal World Atlas tuple must use the dedicated V1 mechanism above. Generic `ecosystem/releases/*.json`, Issue bodies/comments, Markdown evidence tables or unvalidated JSON cannot substitute for it.

## 4. META compatibility record must be canonical

Issue #79 may coordinate and stage the tuple, but an Issue comment, Draft, unmerged PR, local file or floating branch is not terminal release authority.

Before `DONE`, the final record must:

1. exist at `ecosystem/world-atlas/releases/<release_id>.json` and validate against `ecosystem/world-atlas/compatibility.schema.json` through `tools/governance/validate_world_atlas_compatibility.py`;
2. be proposed through a dedicated META PR with exact head SHA;
3. pass current exact-head META checks/review including the dedicated validator through `meta-gate`;
4. be protected-squash-merged to `Oteryn/Oteryn:main`;
5. have the exact squash-merge SHA recorded;
6. be read back from that protected-main SHA at the exact canonical record path;
7. pass post-merge `meta-gate` on that exact protected-main merge SHA;
8. contain no floating or mutable identity.

The record may reference provider evidence by immutable repository/PR/run/check/artifact/deployment IDs and digests; it must not copy normative Game or Atlas schemas into META.

## 5. Required META cutover evidence identifiers

Independent closeout must record at least:

```text
meta_compatibility_schema_path
meta_compatibility_validator_path
meta_compatibility_record_path
meta_compatibility_pr_number
meta_compatibility_pr_head_sha
meta_compatibility_pr_required_check_refs
meta_compatibility_squash_merge_sha
meta_compatibility_post_merge_meta_gate_run_or_check_ref
```

If a later change alters the tuple, schema or validation semantics, prior closeout evidence is superseded as applicable and requalification is required.

## 6. Provider evidence requirements

Game evidence must bind export profile/version, producer revision, world/content revision, exact produced export manifest digest, exact produced payload digest/root, deterministic producer/validation tests, provider PR/merge/check evidence when implementation changed, and the client identity plus exact Atlas bundle digest it packages/pins.

Atlas evidence must bind the exact Game export manifest/payload digests accepted by ingestion, Atlas Core/API identity, Atlas source/release identity, exact web/embedded bundle version/digest, public deployment identity and provider PR/merge/check/live-acceptance evidence.

## 7. Failure semantics

Return `NOT_DONE` / `UNKNOWN_BLOCKING` if any required produced artifact, chain-of-custody link, dedicated V1 schema/validator/meta-gate integration, protected META compatibility merge/readback/check evidence, or immutable tuple field is absent, floating, malformed or contradictory. No coordinator, provider worker or auditor may waive these conditions by narration.

## 8. Relationship to independent closeout

`OTERYN-WORLD-ATLAS-CLOSEOUT-AUDITOR` is the terminal verifier of this contract. Its `FINAL_VERDICT: DONE` is valid only when the auditor returns the immutable Game artifact, Atlas bundle, Game client, public Atlas and canonical validated META World Atlas compatibility-record evidence required here.

The programme coordinator may not report terminal `DONE` before that independent verdict.