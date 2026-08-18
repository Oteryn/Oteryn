# Ecosystem Release Coordination

## Ownership model

Each product repository builds, tests, signs/publishes and owns its own release artifacts. `Oteryn/Oteryn` records which immutable product identities are approved to operate together; it does not become a second build authority for Game, Platform or Atlas.

## Release identity

Future ecosystem release records belong under:

```text
ecosystem/releases/<release-id>.json
```

Each release record should validate against `ecosystem/compatibility.schema.json` and pin the exact participating component commit SHA. Tags are human-friendly aliases only; artifact digests are preferred whenever an external artifact is part of the compatibility boundary.

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
