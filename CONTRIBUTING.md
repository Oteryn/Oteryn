# Contributing to Oteryn META

## Scope

Contributions to this repository must remain ecosystem-level coordination work. Product runtime implementation, provider-owned schemas, generated product artifacts and product-specific secrets/configuration belong in the owning Game, Platform or Atlas repository.

## Workflow

1. Start from current `main` and read `AGENTS.md` plus the nearest governing instructions for the changed path.
2. Use a dedicated task branch; do not push ordinary changes directly to `main`.
3. Keep the change narrowly scoped and preserve truthful migration/provenance history.
4. Open a pull request targeting `main`.
5. Inspect the complete changed-file list and diff.
6. Ensure the exact pull-request head passes the stable `meta-gate` check.
7. Resolve material review findings before merge. A P2 may proceed only after its thread is resolved and its required same-repository follow-up Issue is recorded; P0/P1, escalated and unclassified findings block.
8. Prefer squash merge unless repository policy changes deliberately.

## Architecture and contracts

- Long-lived ecosystem architecture decisions belong under `docs/architecture/adr/`.
- Repository coordinates and migration state belong in `ecosystem/repositories.json`.
- Compatible release sets belong under `ecosystem/releases/` and follow `ecosystem/compatibility.schema.json`.
- Provider schemas stay canonical in provider repositories; META references immutable versions/digests instead of copying them.

## Validation

For metadata/documentation changes, run or observe the repository `meta-gate`. Product runtime tests are not duplicated here. Cross-repository compatibility claims require exact provider/consumer evidence; a narrative summary is not enough.

## Safety

Never commit secrets, credentials, `.env`, private deployment state, production data, database dumps, raw proprietary runtime assets or product runtime package roots. A repository migration or release record does not authorize a production deployment or other protected live operation.
