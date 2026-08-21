# Oteryn Organization Runner Topology Audit — 2026-08-21 (live implementation checkpoint)

Audit owner: `Oteryn/Oteryn#32`
Audit contract context: `OTERYN-ORG-AUDIT-v3.10`
Evidence date: 2026-08-21
Scope: META governance evidence and read-only runtime observation. Product-repository mutation is out of scope.

## Technical observation

Separate Platform, Atlas and Game organization runner registrations/groups were observed as implemented and running, while secure effective routing and repository restriction are not yet proven.

Lifecycle authority remains GitHub Issue #32. This report is a durable technical observation, not a second lifecycle tracker or a declaration that the migration is complete.

## Observed runner implementation

| Workload owner | Observed registration | Observed group/pool | Runner version | Container/image result |
| --- | --- | --- | --- | --- |
| Platform | `oteryn-synology-platform` | `platform-runners` | `2.336.0` | running; immutable GHCR digest |
| Atlas | `oteryn-synology-atlas` | `atlas-runners` | `2.336.0` | running; immutable GHCR digest |
| Game | `oteryn-synology-game` | `game-runners` | `2.336.0` | running; immutable GHCR digest |

The observed new image identity is `ghcr.io/oteryn/oteryn-deploy-runner@sha256:f0c452798a17df09006a12d437e83a72d681dcd338ef22ed01fca329d1bbab8d`. The GitHub checkpoint records distinct local registration/config/work state and the evidence date. These are implementation-observation facts only; they do not independently prove group policy or successful routing.

## Boundary model

| Repository | Default execution | Local ownership target | Current evidence state |
| --- | --- | --- | --- |
| `Oteryn/Oteryn` | GitHub-hosted | none proven | DONE |
| `Oteryn/Oteryn-Platform` | GitHub-hosted where locality is unnecessary | Platform staging/control-plane | PARTIAL — new runner provisioned |
| `Oteryn/Oteryn-Atlas` | GitHub-hosted where locality is unnecessary | Atlas local preview/state/E2E/cutover | PARTIAL — new runner provisioned |
| `Oteryn/Oteryn-Game` | GitHub-hosted where locality is unnecessary | Game local runtime/integration | PARTIAL — new runner provisioned |

A named runner group is not by itself proof of repository isolation. The requisite GitHub organization control-plane readback for selected repositories, labels and membership was unavailable to this audit surface. Therefore every group restriction is `UNKNOWN` rather than assumed.

## Legacy/rollback state

The older `oteryn-synology-staging` registration/container remains an intentional bootstrap/rollback candidate. It is associated with a mutable pre-transfer image and legacy source coordinate. Legacy Atlas/Game containers are also still observable. None may be deleted or treated as retired until exact replacement jobs, workflow routing, group restrictions and rollback disposition are proven.

## Findings

| ID | Severity | State | Evidence-backed conclusion |
| --- | --- | --- | --- |
| RUNNER-001 | HIGH | PARTIAL | New workloads use an immutable digest; legacy mutable image path remains. |
| RUNNER-002 | MEDIUM | UNKNOWN | Immutable tag resolution is observed, but independent build/base-image provenance is not established here. |
| RUNNER-003 | INFO | DONE | New registrations report Actions Runner `2.336.0`. |
| RUNNER-004 | INFO | UNKNOWN | Group names exist; selected-repository restriction and effective labels require GitHub control-plane readback. |
| RUNNER-005 | HIGH | PARTIAL | Atlas runner provisioned; no post-cutover Atlas-owned preview/deploy/E2E job proves Platform cross-use has ceased. |
| RUNNER-006 | MEDIUM | PARTIAL | Game runner provisioned; no post-cutover Game-owned local job proves Platform cross-use has ceased. |
| RUNNER-007 | INFO | UNKNOWN | Privileged-runner exposure to arbitrary PR code has not been revalidated against live workflow routing. |

## Required evidence for Issue #32 closure

1. Organization-owner readback of each runner group: exact member runners, selected repositories and labels.
2. One successful exact-head Platform job, Atlas job and Game job showing the intended registration/provider.
3. Workflow/source evidence that Atlas preview/deploy/E2E and Game local integration no longer run via Platform.
4. Least-privilege capability and mount review of all three new runner containers.
5. A reviewed rollback/retirement record before removing legacy mutable runners or their state.

Until all five are proven, the technical evidence is incomplete. The authoritative lifecycle state and any closure decision remain in GitHub Issue #32.