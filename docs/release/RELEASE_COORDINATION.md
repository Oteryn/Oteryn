# Ecosystem Release Coordination

## Ownership model

Each product repository builds, tests, signs/publishes and owns its own release artifacts. `Oteryn/Oteryn` records which immutable product identities are approved to operate together; it does not become a second build authority for Game, Platform or Atlas.

## Release identity

Future ecosystem release records belong under:

```text
ecosystem/releases/<release-id>.json
```

Each release record must validate against `ecosystem/compatibility.schema.json` and pin the exact participating component commit SHA. Tags are human-friendly aliases only; artifact digests are preferred whenever an external artifact is part of the compatibility boundary.

## Minimum release record

A release set must identify:

- `release_id` and schema version;
- Game repository and exact commit SHA;
- Platform repository and exact commit SHA;
- Atlas repository and exact commit SHA;
- optional product tags;
- immutable artifact digests when artifacts cross repository boundaries;
- explicit provider/consumer contracts and their versions;
- evidence references sufficient to locate the exact provider validation used for the release decision.

## Structure is not release approval

`tools/governance/validate_release_manifests.py` applies the complete local JSON
Schema draft 2020-12 contract, including unknown-property rejection. Committed
records also require a matching filename/release ID and `compatible` status for
every declared contract. Contracts and evidence lists must be non-empty. No
release manifests existed when this minimum was introduced; there is no legacy
release record migration.

The validator is offline and reports `STRUCTURE_VALID`, never provider adoption,
compatibility verification or deployment readiness. It does not fetch schemas,
run product E2E, authenticate evidence references or assert that a referenced
check passed. A string in an evidence list is only a locator.

Before approving a release, its owner must read back: (1) each component's required
provider checks on its recorded exact SHA; (2) producer and consumer contract-test
evidence for each declared boundary/version; (3) artifact IDs and SHA-256 digests
when artifacts cross that boundary; and (4) rollout/rollback evidence for any
non-backward-compatible change. Evidence must identify repository, exact tested
revision and durable run/check/artifact or committed-file locator. A moved tag,
older-head result, unverified summary or missing provider-side proof is not a pass.
Record that review in the release PR. This is a release-specific owner action,
not another META service, copied provider schema, global test or required status.

## Provider/consumer examples

Typical durable boundaries include:

```text
Game -> Atlas semantic export
Platform -> Game authentication/session contract
Game <-> Platform protocol or gateway compatibility
```

The provider owns the normative schema/implementation. META records compatible combinations and rollout order without copying provider source of truth.

## Release procedure

1. Freeze exact provider candidate heads.
2. Verify required provider CI/tests on those unchanged heads.
3. Verify cross-repository contracts and compatibility evidence.
4. Record immutable SHAs/digests in the ecosystem release manifest.
5. Run META `meta-gate` on the release-manifest change.
6. Merge the manifest only when no release-scope material `UNKNOWN` or `CONFLICT` remains.
7. Treat deployment/production activation as a separate protected operation with its own authority and evidence.

## Rollback

Rollback is defined by an earlier known-compatible ecosystem release set, not by an unpinned branch name. Any release that introduces a non-backward-compatible contract must record provider/consumer sequencing and the compatible rollback window before it is treated as deployable.

## Repository migration interaction

Repository transfer or rename must not rewrite historical provenance. New release records use the current canonical repository coordinates after cutover; old evidence continues to reference the coordinates and immutable identities that were truthful when the evidence was produced.
