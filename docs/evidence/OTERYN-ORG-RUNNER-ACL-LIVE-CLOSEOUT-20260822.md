# Oteryn organization runner ACL live closeout — 2026-08-22

**Scope:** organization runner groups, selected-repository ACLs, live runner membership and terminal legacy-runner disposition.

**Evidence policy:** direct GitHub organization API readback outranks stale repository snapshots. No registration token, runner credential or secret value is recorded here.

Machine-readable provenance is retained beside this document in `OTERYN-ORG-RUNNER-ACL-LIVE-CLOSEOUT-20260822.json` with detached digest `OTERYN-ORG-RUNNER-ACL-LIVE-CLOSEOUT-20260822.json.sha256`. The sanitized capture was generated at `2026-08-22T16:48:42.564Z` by authenticated GitHub CLI account `blakinio`; credential values were not recorded. Capture SHA-256: `4d4c9c41d9b1e200e403f2607ea1a630453d25384fa42c1fa12050c15ad5c1d3`.

Recorded successful API surfaces: `GET /orgs/Oteryn/actions/runner-groups`, each selected group's `/repositories` and `/runners`, the default group's `/runners`, and `GET /orgs/Oteryn/actions/runners`. The JSON preserves the ACL-relevant response fields, repository IDs/full names, runner IDs/names/status/version/custom labels, counts, capture identity and timestamp.

## Direct organization API readback

An authenticated organization-admin GitHub CLI session successfully read `/orgs/Oteryn/actions/runner-groups`, each selected group's `/repositories` and `/runners`, the `Default` group's runners, and `/orgs/Oteryn/actions/runners`.

| Group | Visibility | Selected repository | Runner | State | Version | Custom label |
| --- | --- | --- | --- | --- | --- | --- |
| `platform-runners` | `selected` | `Oteryn/Oteryn-Platform` only | `oteryn-synology-platform` (id 44) | online, idle | `2.336.0` | `oteryn-platform` |
| `atlas-runners` | `selected` | `Oteryn/Oteryn-Atlas` only | `oteryn-synology-atlas` (id 45) | online, idle | `2.336.0` | `oteryn-atlas` |
| `game-runners` | `selected` | `Oteryn/Oteryn-Game` only | `oteryn-synology-game` (id 46) | online, idle | `2.336.0` | `oteryn-game` |

`Default` has zero runners. Organization runner inventory contains exactly the three product runners above.

`ORGANIZATION_RUNNER_SELECTED_REPOSITORY_ACL = PASS`

## Corroborating provider acceptance

- Platform organization seal: run/job `32512311186` / `96866035808`, source `efe35c1ffa4af5f10904580fe3a587aa5c343a50`, terminal marker `organization-runner-estate=PASS`.
- Atlas trusted-main acceptance: run/job `32526864123` / `96911114022`: PASS.
- Game trusted-main acceptance: run/job `32566399984` / `97015531724`: PASS.
- Platform trusted-main acceptance: run/job `32567509732` / `97018190282`: PASS.

## Legacy retirement

Platform PR #1221 merged as `1da7ba2d5cf698cd205c1c5ada2fa31da39520cd` and removed retained `runs-on: oteryn-staging` selectors. The legacy repository-scoped runner `oteryn-synology-staging` (id 21) was then deregistered and its runner container removed; config/work volumes and Platform state were preserved as bounded rollback evidence. Platform terminal archive/governance PR #1222 merged as `5591da8437995214b82f556992301f899cb91aa8`.

META Issue #32 is closed `completed`. Parent runner implementation Issue #34 is closed after terminal acceptance.

`RUNNER_TOPOLOGY_SECURITY_RETIREMENT = PASS`

This closes the runner/control-plane evidence family only. It does not promote unrelated migration or recurring organization-recovery gaps to PASS.
