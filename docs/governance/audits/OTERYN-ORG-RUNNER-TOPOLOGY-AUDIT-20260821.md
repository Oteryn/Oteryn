# Oteryn Organization Runner Topology Audit — 2026-08-21

Audit owner: `Oteryn/Oteryn#32`
Platform live-evidence owner: `Oteryn/Oteryn-Platform#1194`
Platform evidence PR: `Oteryn/Oteryn-Platform#1198`
Audit contract context: `OTERYN-ORG-AUDIT-v3.10`

## Corrected verdict

`SEPARATE_REPOSITORY_SCOPED_LOCAL_RUNNERS_BY_WORKLOAD_OWNER`

The previous interim verdict was wrong because it classified runner need from the repository containing `runs-on`, rather than from the repository that owns the workload actually executed on Synology.

Live source proves that the current Platform runner executes Atlas-owned and Game-owned local work. The fact that Atlas/Game do not currently declare `runs-on: oteryn-staging` themselves is therefore a symptom of cross-repository execution coupling, not proof that they do not need a local execution surface.

## Proven workload ownership

### Platform

Platform has a direct local requirement for Synology staging/control-plane operations and currently owns the privileged `oteryn-synology-staging` runner.

### Atlas

Atlas has a direct, proven local requirement. Platform's `repair-synology-autostart.yml`, running on `oteryn-staging`, currently:

- fetches exact Atlas source;
- builds/stages Atlas products;
- reads/writes persistent Atlas revision roots;
- controls `oteryn-atlas-fullworld-preview`;
- serves the LAN endpoint `192.168.1.2:8097`;
- performs live Atlas cutover/rollback;
- runs real desktop/mobile Chromium acceptance against that local endpoint.

The active deployment record states explicitly that the registered Synology self-hosted runner is the trusted path for the LAN-only Atlas preview.

Atlas `AGENTS.md` says Platform may coordinate Atlas contracts but is not an Atlas runtime data source. Therefore long-lived Atlas runtime/deployment/E2E execution should be moved to an Atlas-owned runner boundary.

### Game

Game also has a local footprint. The same Synology job currently executes the Game-owned creature export producer from exact `Oteryn/Oteryn-Game` source, and the Synology staging Compose stack runs the `canary` game runtime with local DB/network/runtime state.

Pure Game build/export CI should remain GitHub-hosted when locality is unnecessary. Game-owned live runtime/integration validation on Synology should have a separate Game-owned execution boundary rather than sharing the privileged Platform registration/workspace.

Game `AGENTS.md` establishes `Oteryn/Oteryn-Game` as the canonical native game server/runtime and Game-owned export authority.

### META

No current host-local runtime requirement is proven for `Oteryn/Oteryn`; META remains GitHub-hosted.

## Correct desired state

| Repository | Default execution | Self-hosted Synology desired state |
| --- | --- | --- |
| `Oteryn/Oteryn` | GitHub-hosted | none currently |
| `Oteryn/Oteryn-Platform` | GitHub-hosted for ordinary CI | **repo-scoped `oteryn-platform`** for Platform staging/control-plane |
| `Oteryn/Oteryn-Atlas` | GitHub-hosted for ordinary CI/build | **repo-scoped `oteryn-atlas`** for FullWorld local state, preview, live E2E and cutover/rollback |
| `Oteryn/Oteryn-Game` | GitHub-hosted for ordinary build/export/tests | **repo-scoped `oteryn-game`** for Game-owned local runtime/integration work |
| archived migration backup | none | none |

A local runner is an additional execution surface, not the default for every job. Jobs that do not require Synology/local state remain GitHub-hosted.

## Why per repository, not one organization-wide privileged runner

The live `oteryn-synology-staging` runner is high privilege:

- container user `0:0`;
- RW `/var/run/docker.sock`;
- RW `/runner` and `/work`;
- RW Platform staging-state mount;
- Actions Runner `2.336.0`.

One organization-wide runner would collapse Platform, Atlas and Game trust boundaries onto a host-equivalent credential/execution surface. That is the wrong direction.

For the current scale, prefer repository-scoped registrations with custom labels only:

- `oteryn-platform` -> `Oteryn/Oteryn-Platform` only;
- `oteryn-atlas` -> `Oteryn/Oteryn-Atlas` only;
- `oteryn-game` -> `Oteryn/Oteryn-Game` only.

Use separate config/work volumes and expose only the host mounts/Docker capability each workload proves it needs. Do not grant Atlas/Game Platform's staging-state mount merely because they share the same Synology.

Organization runner groups restricted one-to-one are technically possible, but do not currently improve least privilege over repository-scoped registration.

## Current architectural defect

The current Platform runner is functioning as a de facto multi-project execution broker. This was useful as a bootstrap path but is not the desired steady state.

Current coupling:

```text
Oteryn-Platform workflow
      |
      +-- Platform operations
      +-- fetch/run Game producer
      +-- fetch/build/deploy Atlas
      +-- local Atlas browser E2E
      +-- local Game/Canary integrated runtime
      |
      v
single privileged oteryn-synology-staging runner
```

Desired ownership:

```text
Synology
|
+-- oteryn-platform  -> Platform repo only
+-- oteryn-atlas     -> Atlas repo only
+-- oteryn-game      -> Game repo only

GitHub-hosted remains default for non-local CI.
```

## Migration sequence

1. Preserve the working `oteryn-staging` runner unchanged as bootstrap/rollback.
2. Create `oteryn-atlas` first; Atlas has the clearest directly proven LAN/persistent-runtime requirement.
3. Move Atlas preview/deployment/live E2E out of Platform into Atlas-owned workflow and validate the same exact endpoint/state/rollback behavior.
4. Create `oteryn-game` for Game-owned local runtime/integration acceptance; keep non-local Game jobs hosted.
5. Refactor/rename the current Platform runner to Platform-only responsibility after Atlas/Game replacement paths are proven.
6. Remove cross-repository runtime execution from Platform only after live E2E and rollback pass for each replacement.
7. Harden image provenance and pinning without destroying persistent registration state.

## Findings

| ID | Severity | State | Finding |
| --- | --- | --- | --- |
| `RUNNER-001` | HIGH | OPEN | Current privileged runner image is mutable/pre-transfer `ghcr.io/blakinio/oteryn-deploy-runner:main`. |
| `RUNNER-002` | MEDIUM | OPEN | Runner build base uses mutable `ghcr.io/actions/actions-runner:latest`. |
| `RUNNER-003` | INFO | PASS | Current runner `2.336.0` satisfies the Node.js 24 runner prerequisite. |
| `RUNNER-004` | INFO | PASS | Current custom-label-only registration avoids generic self-hosted scheduling. |
| `RUNNER-005` | HIGH | OPEN | Atlas-owned local runtime/deployment/E2E is currently executed through Platform's privileged runner. |
| `RUNNER-006` | MEDIUM | OPEN | Game-owned local producer/runtime integration work is mixed into Platform's runner boundary. |
| `RUNNER-007` | INFO | PASS | Permanent arbitrary pull-request code is not currently routed onto the privileged Platform runner. |

`RUNNER-001`/`RUNNER-002` are tracked by `Oteryn/Oteryn-Platform#1199`. `RUNNER-005`/`RUNNER-006` are topology migration findings under META #32.

## Audit status

This corrected verdict supersedes the earlier `KEEP_REPOSITORY_SCOPED_PLATFORM_RUNNER` conclusion. META PR #33 remains Draft while active META governance PR #30 is terminalized; no branch-protection or review bypass is authorized.