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

### Produced Game export artifact identity

`game_atlas_export_artifact_manifest_digest` identifies the exact immutable manifest/envelope emitted by the Game-owned producer for the Atlas input consumed by the accepted Atlas build.

`game_atlas_export_payload_digest_or_root` identifies the exact produced payload bytes or deterministic Merkle/root digest referenced by that manifest. If the accepted Game contract uses one digest that unambiguously binds both manifest and all payload bytes, one value may satisfy both fields only when the provider contract explicitly proves that property; otherwise both are required.

Producer source SHA/profile/world revision are not substitutes for produced-artifact identity. Two outputs from the same producer/profile/revision that differ because of nondeterminism, mutable inputs or corruption must have distinguishable artifact evidence and cannot both satisfy the same final tuple.

The Atlas consumer/build evidence must prove that the exact produced Game artifact digest/root in the tuple was the input accepted by Atlas. The final Atlas bundle evidence must in turn prove the exact Atlas bundle digest resulting from the accepted input and Atlas revision/configuration.

## 2. Required chain of custody

Terminal evidence must establish this immutable chain:

```text
Game producer revision/profile
        +
world/content revision
        |
        v
exact produced Game Atlas manifest/payload digest
        |
        v
Atlas verified ingestion/build evidence
        |
        v
Atlas Core/API identity
        +
exact web/embedded bundle digest
        |
        v
Game client candidate/release pinning that bundle digest
        +
public Atlas release/deployment identity
```

A broken or inferred link is `UNKNOWN_BLOCKING`; it is never repaired by matching display names, timestamps, floating branches or a narrative assertion.

## 3. META compatibility record must be canonical

Issue #79 may coordinate and stage the tuple, but an Issue comment, Draft, unmerged PR, local file or floating branch is not terminal release authority.

Before the programme may report `DONE`, the final compatibility record must:

1. exist at an exact canonical path under the existing META compatibility/release mechanism;
2. be proposed through a dedicated META PR whose head SHA is recorded;
3. pass the current exact-head required META checks/review policy for that PR;
4. be protected-squash-merged to `Oteryn/Oteryn:main`;
5. have the exact squash-merge SHA recorded;
6. be read back from that protected-main SHA at the canonical path;
7. pass the applicable post-merge `meta-gate` on that exact protected-main merge SHA;
8. contain no floating `main`, `latest`, mutable URL or undocumented compatibility guess as an identity.

The canonical record may reference provider evidence by immutable repository/PR/run/check/artifact/deployment IDs and digests. It must not copy normative Game or Atlas provider schemas into META.

## 4. Required META cutover evidence identifiers

The independent closeout must record at least:

```text
meta_compatibility_record_path
meta_compatibility_pr_number
meta_compatibility_pr_head_sha
meta_compatibility_pr_required_check_refs
meta_compatibility_squash_merge_sha
meta_compatibility_post_merge_meta_gate_run_or_check_ref
```

The exact compatibility record content must be read from `meta_compatibility_squash_merge_sha` or a later protected `main` descendant that preserves the same record bytes/identity. If a later change alters the tuple, the prior closeout evidence is superseded and requalification is required.

## 5. Provider evidence requirements

### Game

Evidence must bind:

- export profile/version;
- producer revision;
- exact world/content revision;
- exact produced export manifest digest;
- exact produced payload digest/root;
- deterministic producer/validation tests;
- exact provider PR/merge/check evidence when implementation changed;
- client candidate/release identity and the exact Atlas bundle digest it packages/pins.

### Atlas

Evidence must bind:

- exact Game export manifest/payload digest accepted by ingestion;
- Atlas Core/API identity;
- exact Atlas source/release identity;
- exact web/embedded bundle version and digest;
- public deployment identity;
- exact provider PR/merge/check/live-acceptance evidence.

## 6. Failure semantics

Return `NOT_DONE` / `UNKNOWN_BLOCKING` when any of these applies:

- producer revision is known but exact produced Game export artifact digest is missing;
- world/content revision is known but the artifact bytes/root consumed by Atlas are not bound;
- Atlas bundle digest is known but its accepted Game input artifact identity is not proven;
- Game client release is known but its packaged/pinned Atlas bundle digest is not proven;
- tuple exists only in Issue/PR/local evidence and is not protected-merged to META `main`;
- exact-head META checks/review or post-merge `meta-gate` evidence is missing;
- a tuple field uses a floating/mutable reference where an immutable identity is required.

No coordinator, provider worker or auditor may waive these conditions by narration.

## 7. Relationship to independent closeout

`OTERYN-WORLD-ATLAS-CLOSEOUT-AUDITOR` is the terminal verifier of this contract. Its `FINAL_VERDICT: DONE` is valid only when the auditor returns the immutable Game artifact, Atlas bundle, Game client, public Atlas and canonical META compatibility-record evidence required here.

The programme coordinator may not report terminal `DONE` before that independent verdict.