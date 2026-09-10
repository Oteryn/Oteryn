# Unified Oteryn World Atlas release compatibility contract

Lifecycle: `Oteryn/Oteryn#79` under parent programme `Oteryn/Oteryn#75`.

Status: proposed until protected-merged with the World Atlas architecture packet; after merge this contract is the canonical META definition of the exact compatibility tuple and terminal cutover evidence.

## Purpose

This contract closes the release-evidence boundary between Game, Atlas and META. It prevents terminal compatibility from being inferred when provider gate identity, artifact provenance, qualification, bridge compatibility, public deployment, or the canonical META record is not independently bound to the released tuple.

It refines shorthand in the implementation plan, coordinator and auditor. Where shorthand omits a field required here, this contract wins. META records immutable provider identities/evidence only and does not duplicate provider schemas/runtime.

## 1. Required immutable tuple

The final record independently preserves at least:

```text
game_provider_pr_head_sha
game_main_or_release_commit_sha
game_provider_merge_evidence_ref
game_provider_required_check_set_evidence_ref
game_provider_required_check_refs[]
game_provider_review_evidence_refs[]
game_atlas_export_build_source_commit_sha
game_atlas_export_profile_version
game_atlas_export_producer_revision
game_atlas_export_artifact_manifest_digest
game_atlas_export_payload_digest_or_root
game_atlas_export_build_evidence_ref
game_world_content_revision
game_client_release_or_candidate_identity
game_client_pinned_atlas_bundle_digest

atlas_provider_pr_head_sha
atlas_main_or_release_commit_sha
atlas_provider_merge_evidence_ref
atlas_provider_required_check_set_evidence_ref
atlas_provider_required_check_refs[]
atlas_provider_review_evidence_refs[]
atlas_embedded_bundle_build_source_commit_sha
atlas_core_api_identity
atlas_web_embedded_bundle_version
atlas_web_embedded_bundle_digest
atlas_embedded_bundle_build_evidence_ref
atlas_accepted_game_export_artifact_manifest_digest
atlas_accepted_game_export_payload_digest_or_root
public_atlas_release_or_deployment_identity
public_atlas_deployed_bundle_version
public_atlas_deployed_bundle_digest
public_atlas_bundle_relation_to_embedded
public_atlas_deployment_bundle_evidence_ref

atlas_bridge_protocol_version
atlas_bridge_capability_profile
atlas_bridge_compatibility_handshake_evidence_ref

qualification_candidate_evidence_manifest_ref
security_evidence_refs[]
performance_evidence_refs[]
cross_surface_e2e_refs[]
rollback_evidence_refs[]
```

Provider PR-head identity and resulting protected-main/release identity are distinct. Required checks/reviews bind to the exact pre-squash PR head; immutable merge evidence binds that head to the exact resulting protected-main/release commit. Post-merge/live evidence binds the resulting commit. Neither stage substitutes for another.

## 2. Required chain of custody

For each provider:

```text
provider PR head
  -> complete required-check set + accepted exact-head review
  -> immutable merge evidence
  -> exact resulting protected-main/release commit
  -> required post-merge/live evidence
```

Artifact chains are separately bound to the provider gate chain:

```text
Game authorized build source SHA
  -> producer/profile/world inputs
  -> Game export-build evidence
  -> exact manifest/payload digests
  -> Atlas accepted digests

Atlas authorized build source SHA
  -> accepted Game digests + Atlas Core identity
  -> Atlas bundle-build evidence
  -> exact embedded bundle
  -> exact client pin
  -> bridge compatibility/handshake evidence

public deployment identity
  -> exact public deployed bundle version/digest
```

`game_atlas_export_build_source_commit_sha` must equal either the recorded final `game_provider_pr_head_sha` or its exact `game_main_or_release_commit_sha`. `atlas_embedded_bundle_build_source_commit_sha` must likewise equal either `atlas_provider_pr_head_sha` or `atlas_main_or_release_commit_sha`. Build evidence must resolve to that exact authorized source SHA. Any artifact built from an unrelated/stale revision is blocking unless a later accepted contract explicitly introduces and validates another authorized derivation mode.

Bridge evidence must bind exact client identity, exact pinned embedded bundle version/digest, supported bridge protocol range/profile, selected protocol/profile and relevant world/content compatibility identity. Strings without that immutable binding are insufficient.

## 3. Dedicated canonical META record mechanism V1

World Atlas terminal cutover uses the dedicated mechanism owned by `Oteryn/Oteryn#84`:

```text
ecosystem/world-atlas/compatibility.schema.json
ecosystem/world-atlas/releases/<release_id>.json
tools/governance/validate_world_atlas_compatibility.py
```

#84 must integrate the validator into stable `meta-gate` with deterministic positive/negative regressions. Until canonical, Wave 7 Task 7E is `WAITING_EXTERNAL: WORLD_ATLAS_COMPATIBILITY_RECORD_MECHANISM_NOT_CANONICAL`.

### 3.1 Required V1 semantics

The dedicated schema must represent the identities in section 1 as separately typed fields. In particular, it must not collapse:

- provider PR head and resulting main/release SHA;
- expected complete required-check set and observed check refs;
- Game and Atlas provider evidence;
- provider build source SHA and artifact digest;
- embedded and public bundle identities;
- bridge protocol/profile and handshake evidence;
- qualification evidence arrays and the candidate manifest that binds them.

Every required evidence array is semantically non-empty.

### 3.2 Required validator invariants

The validator fails closed unless all applicable rules hold:

#### Provider gate completeness

- Game required-check/review refs resolve to exact `game_provider_pr_head_sha`; Atlas equivalents resolve to exact `atlas_provider_pr_head_sha`.
- `game_provider_required_check_set_evidence_ref` and `atlas_provider_required_check_set_evidence_ref` are immutable provider-owned protection/required-check snapshots bound to the relevant final provider PR/base-policy state and enumerate the **complete** expected required-check set.
- Each recorded provider required-check-ref set exactly covers its snapshot's expected required checks. A non-empty subset is insufficient; omission of any required check fails.
- Provider check/review evidence from another provider, another PR head, an older/stale head, or only the resulting squash SHA fails.
- Provider merge evidence proves exact `provider_pr_head_sha -> provider_main_or_release_commit_sha` for that provider.
- Merge evidence never substitutes for required checks/review, and PR-head checks/review never substitute for the head→resulting-main binding.

#### Game artifact provenance

- `game_atlas_export_build_source_commit_sha` equals `game_provider_pr_head_sha` or `game_main_or_release_commit_sha`.
- `game_atlas_export_build_evidence_ref` immutably binds that exact source SHA plus producer revision, export profile/version and world/content revision to the exact manifest digest and payload digest/root.
- Digests or producer/profile/world identities from another source revision fail.

#### Atlas artifact provenance

- Atlas accepted Game manifest/payload identities exactly equal Game produced identities.
- `atlas_embedded_bundle_build_source_commit_sha` equals `atlas_provider_pr_head_sha` or `atlas_main_or_release_commit_sha`.
- `atlas_embedded_bundle_build_evidence_ref` immutably binds that exact source SHA plus exact accepted Game digests and Atlas Core/API identity to the exact embedded bundle version/digest.
- Bundle evidence from another source revision/export/Core identity fails.
- Game client pinned bundle digest equals the recorded embedded bundle digest.

#### Bridge and deployment

- Bridge handshake evidence binds exact recorded client identity, pinned embedded bundle version/digest, supported bridge range/profile, selected protocol/profile and relevant Game world/content identity.
- Wrong client, bundle/version, unsupported protocol/profile or wrong world/content identity fails.
- Public relation is exactly `SAME_BUNDLE` or `COMPATIBLE_INDEPENDENT`.
- `SAME_BUNDLE` requires public and embedded bundle digest equality.
- `COMPATIBLE_INDEPENDENT` requires immutable deployment evidence plus explicit compatibility evidence for the independently deployed public bundle.
- Public deployment evidence binds exact public deployment identity to exact public bundle version/digest.

#### Qualification evidence binding

- `qualification_candidate_evidence_manifest_ref` is an immutable manifest/evidence identity that binds the qualification generation to the exact released candidate identities applicable to that evidence: both provider PR heads, Game export build source/profile/world/digests, Atlas bundle build source/Core/bundle, client identity/pin, bridge protocol/profile/handshake identity, and, for post-deployment/live evidence, the exact public deployment/bundle identity.
- Every `security_evidence_ref`, `performance_evidence_ref`, `cross_surface_e2e_ref` and `rollback_evidence_ref` must either resolve directly to those same exact candidate identities or be explicitly included/bound by the immutable qualification candidate manifest.
- Evidence from a prior candidate generation, old provider head, old artifact/bundle/client/bridge/public deployment, or a candidate invalidated by product/config change fails.

#### Evidence integrity

- required evidence arrays are present and non-empty;
- references are immutable supported identities appropriate to their class;
- floating branches, `latest`, mutable aliases/URLs, narrative `PASS`, malformed refs, duplicates that mask omission, contradictory refs, or cross-provider substitution fail;
- required SHAs/digests use canonical immutable formats.

### 3.3 Required regressions

#84 must include negative tests for at least:

- missing/empty evidence arrays;
- missing required-check-set snapshot;
- omission of each required provider check one at a time;
- extra/wrong/cross-provider check-set substitution;
- stale/wrong provider PR-head review/check evidence;
- checks/review incorrectly pointed at resulting squash SHA;
- wrong PR-head→resulting-main merge evidence;
- Game build source not equal to recorded Game PR head/resulting main;
- Atlas build source not equal to recorded Atlas PR head/resulting main;
- Game/Atlas build evidence bound to wrong source revision, input, digest, Core or bundle;
- stale-candidate security/performance/E2E/rollback evidence;
- qualification manifest bound to a previous provider head/export/bundle/client/bridge/public deployment;
- wrong bridge client/bundle/version/protocol/profile/world identity;
- public deployment/bundle mismatch;
- mutable/malformed/floating evidence.

Positive fixtures must cover both public-bundle relation modes and complete provider PR-head→checks/review→merge/main, artifact-build, qualification, bridge and deployment chains.

### 3.4 No alternate terminal encoding

Generic release records, Issue text, Markdown tables or unvalidated JSON cannot substitute for V1.

## 4. META compatibility record canonicalization

Terminal `DONE` requires the final record to:

1. exist at `ecosystem/world-atlas/releases/<release_id>.json`;
2. validate with canonical #84 schema/validator;
3. be proposed through a dedicated META PR with exact head;
4. pass exact-head META checks/review including `meta-gate`;
5. protected-squash-merge to META `main`;
6. record exact squash-merge SHA;
7. be read back from that exact SHA/path;
8. pass post-merge `meta-gate` on that exact protected-main SHA.

## 5. Provider evidence requirements

Game final evidence preserves exact Game provider PR head, complete required-check-set snapshot, exact-head check/review evidence, merge evidence to exact resulting main/release SHA, authorized artifact-build source SHA, export-build chain, client identity and exact embedded bundle pin.

Atlas final evidence preserves exact Atlas provider PR head, complete required-check-set snapshot, exact-head check/review evidence, merge evidence to exact resulting main/release SHA, authorized bundle-build source SHA, accepted Game digests/Core→embedded bundle chain, public deployment/bundle evidence and live acceptance.

Qualification evidence must be bound to the exact released candidate through the immutable qualification candidate evidence manifest; stale candidate evidence cannot be carried forward after a product/config candidate change.

Bridge evidence separately proves exact client+bundle compatibility with selected protocol/profile and world identity.

## 6. Failure semantics

Return `NOT_DONE` / `UNKNOWN_BLOCKING` for any missing, floating, malformed, incomplete, stale, wrong-stage, wrong-source, cross-provider or contradictory provider gate, required-check-set, merge, build, qualification, bridge, deployment or META-record evidence. Narration cannot waive these conditions.

## 7. Relationship to independent closeout

`OTERYN-WORLD-ATLAS-CLOSEOUT-AUDITOR` is the terminal verifier. Its `DONE` is valid only with the complete immutable provider gate, build, qualification, bridge, deployment and canonical META record chains required here. The programme coordinator may not report terminal `DONE` before the independent closeout evidence is itself produced through its canonical routed META closeout-evidence lifecycle.