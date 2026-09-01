# Oteryn

Oteryn ecosystem coordination, compatibility and release authority.

This repository is the thin **META / coordination plane** for the Oteryn ecosystem. It does **not** contain Game, Platform or Atlas runtime source code.

## Repository topology

| Responsibility | Target repository | Current transition state |
| --- | --- | --- |
| META / ecosystem coordination | `Oteryn/Oteryn` | canonical authority active |
| Game product | `Oteryn/Oteryn-Game` | migration terminal; legacy source archived read-only; source work/refs reconciled |
| Web / application platform | `Oteryn/Oteryn-Platform` | migration terminal; stable repository ID `1305155726`; post-transfer control plane and GHCR linkage revalidated; backup archived |
| Spatial / map product | `Oteryn/Oteryn-Atlas` | migration terminal; bounded selective extraction/provenance and publication-rights closeout complete |

Provider-owned schemas, generated product artifacts and runtime implementation remain in their provider repositories. META may reference provider contracts by immutable coordinate/version/digest but must not duplicate provider ownership. `ecosystem/repositories.json` applies the ADR 0002 completion invariant and now records `MIGRATION_COMPLETE=YES` for Game, Platform and Atlas from terminal provider evidence; this does not rewrite the historical v3.9 audit snapshot or the later v3.10 audit/addendum state.

## Canonical authority

`docs/architecture/adr/0001-ecosystem-topology-authority.md` is the canonical ecosystem-topology authority after merge `a2672baac544ada81c526e92f0517903865a9ad0`. The machine-readable repository inventory is `ecosystem/repositories.json`.

## CI, testing and releases

- `docs/ci/CI_CONTRACT.md` defines the stable META required-check contract.
- `docs/testing/ECOSYSTEM_TEST_STRATEGY.md` defines ecosystem metadata and compatibility proof layers.
- `docs/release/RELEASE_COORDINATION.md` defines release-manifest ownership and immutable identity rules.
- `ecosystem/compatibility.schema.json` defines the machine-readable shape for future compatible release sets.
- `ecosystem/governance-desired-state.json` records the small ADR 0005 target merge contract; current enforcement is read directly from GitHub live state.

META CI deliberately validates coordination metadata only. Product builds and product-specific tests remain in Game, Platform and Atlas.

## Security

No secrets, credentials, private deployment state, production/live-state data, proprietary runtime assets, database dumps or product runtime source belong in this repository. See `SECURITY.md`.
