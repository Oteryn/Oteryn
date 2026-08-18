# Oteryn

Oteryn ecosystem coordination, compatibility and release authority.

This repository is the thin **META / coordination plane** for the Oteryn ecosystem. It does **not** contain Game, Platform or Atlas runtime source code.

## Repository topology

| Responsibility | Target repository | Current transition state |
| --- | --- | --- |
| META / ecosystem coordination | `Oteryn/Oteryn` | bootstrap in progress |
| Game product | `Oteryn/Oteryn-Game` | migration pending from the existing Game source coordinate |
| Web / application platform | `Oteryn/Oteryn-Platform` | migration pending from `blakinio/Oteryn-Platform` |
| Spatial / map product | `Oteryn/Oteryn-Atlas` | repository exists; selective content migration remains independently gated |

Provider-owned schemas, generated product artifacts and runtime implementation remain in their provider repositories. META may reference provider contracts but must not duplicate ownership of them.

## Bootstrap authority

Until the initial META topology ADR is merged here, `blakinio/Oteryn-Platform` ADR 0041 remains the temporary ecosystem-topology authority. The initial governed bootstrap will add repository-local agent rules, the topology authority ADR and a machine-readable repository manifest through a dedicated pull request.

No secrets, credentials, private deployment state or production/live-state data belong in this repository.
