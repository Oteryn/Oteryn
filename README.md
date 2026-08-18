# Oteryn

Oteryn ecosystem coordination, compatibility and release authority.

This repository is the thin **META / coordination plane** for the Oteryn ecosystem. It does **not** contain Game, Platform or Atlas runtime source code.

## Repository topology

| Responsibility | Target repository | Current transition state |
| --- | --- | --- |
| META / ecosystem coordination | `Oteryn/Oteryn` | canonical authority active |
| Game product | `Oteryn/Oteryn-Game` | authoritative migration remains pending from the existing Game source coordinate |
| Web / application platform | `Oteryn/Oteryn-Platform` | migration pending from `blakinio/Oteryn-Platform` |
| Spatial / map product | `Oteryn/Oteryn-Atlas` | repository exists; content and lifecycle work remain independently gated |

Provider-owned schemas, generated product artifacts and runtime implementation remain in their provider repositories. META may reference provider contracts by immutable coordinate/version/digest but must not duplicate provider ownership.

## Canonical authority

`docs/architecture/adr/0001-ecosystem-topology-authority.md` is the canonical ecosystem-topology authority after merge `a2672baac544ada81c526e92f0517903865a9ad0`. The machine-readable repository inventory is `ecosystem/repositories.json`.

## CI, testing and releases

- `docs/ci/CI_CONTRACT.md` defines the stable META required-check contract.
- `docs/testing/ECOSYSTEM_TEST_STRATEGY.md` defines ecosystem metadata and compatibility proof layers.
- `docs/release/RELEASE_COORDINATION.md` defines release-manifest ownership and immutable identity rules.
- `ecosystem/compatibility.schema.json` defines the machine-readable shape for future compatible release sets.

META CI deliberately validates coordination metadata only. Product builds and product-specific tests remain in Game, Platform and Atlas.

## Security

No secrets, credentials, private deployment state, production/live-state data, proprietary runtime assets, database dumps or product runtime source belong in this repository. See `SECURITY.md`.
