# OTERYN-20260821-runner-topology-audit

Issue: #32
Repository: Oteryn/Oteryn
Status: VALIDATING
Mode: audit + migration design; no destructive runner mutation

## Objective

Establish exact current and desired GitHub Actions runner topology for Oteryn/Oteryn, Oteryn-Game, Oteryn-Platform and Oteryn-Atlas, including Synology execution boundaries, workload ownership, runner scope, labels, isolation, routing and rollback.

## Corrected verdict

`SEPARATE_REPOSITORY_SCOPED_LOCAL_RUNNERS_BY_WORKLOAD_OWNER`

The earlier interim conclusion was invalid because it inferred local-runner need only from where `runs-on` appears. Live source proves Platform's `oteryn-staging` runner currently executes Atlas-owned and Game-owned local work.

Desired state:

- `Oteryn/Oteryn`: GitHub-hosted; no current local runtime requirement.
- `Oteryn/Oteryn-Platform`: GitHub-hosted by default + repo-scoped `oteryn-platform` for Platform staging/control-plane.
- `Oteryn/Oteryn-Atlas`: GitHub-hosted by default + repo-scoped `oteryn-atlas` for FullWorld local state, LAN preview, live Chromium E2E and cutover/rollback.
- `Oteryn/Oteryn-Game`: GitHub-hosted for non-local builds/exports/tests + repo-scoped `oteryn-game` for Game-owned local runtime/integration work.
- archived Platform migration backup: no runner.

Canonical report:
`docs/governance/audits/OTERYN-ORG-RUNNER-TOPOLOGY-AUDIT-20260821.md`

## Corrected evidence

Platform live evidence is owned by `Oteryn/Oteryn-Platform#1194` / PR #1198.

- live runner `oteryn-synology-staging`, Actions Runner `2.336.0`, root container, RW Docker socket and Platform staging-state access;
- Platform `repair-synology-autostart.yml` runs on that runner and fetches exact Atlas/Game revisions;
- it runs the Game-owned creature producer, builds Atlas indices, operates persistent Atlas revision roots, controls `oteryn-atlas-fullworld-preview`, serves `192.168.1.2:8097`, and performs Atlas live cutover/rollback + real Chromium E2E;
- Platform Synology Compose also runs the local `canary` Game runtime;
- Atlas authority says Platform may coordinate contracts but is not an Atlas runtime data source;
- Game authority says Game owns native runtime and Game-owned export contracts.

Therefore absence of direct `self-hosted` selectors in Atlas/Game is a current topology/coupling symptom, not proof of no local requirement.

## Findings

- `RUNNER-001` HIGH: mutable pre-transfer live runner image; Platform #1199.
- `RUNNER-002` MEDIUM: mutable actions-runner base; Platform #1199.
- `RUNNER-003` PASS: runner version is current enough for Node.js 24 actions.
- `RUNNER-004` PASS: current custom-label-only routing avoids generic self-hosted selection.
- `RUNNER-005` HIGH: Atlas-owned local runtime/deploy/E2E currently executes through Platform runner.
- `RUNNER-006` MEDIUM: Game-owned local producer/runtime integration is mixed into Platform execution boundary.
- `RUNNER-007` PASS: permanent arbitrary PR code is not currently routed to privileged Synology execution.

## Migration rule

Keep the working `oteryn-staging` runner as bootstrap/rollback until replacements are proven. Create Atlas first, then Game, then narrow the existing Platform runner to Platform-only ownership. Use separate registration/config/work volumes and least-privilege mounts per repo; do not copy Platform staging-state access to Atlas/Game by default.

## Current closeout dependencies

META PR #30 still owns active AI-review-gate hardening. PR #33 remains Draft until that dependency is terminal and normal protected gates can run. Platform evidence PR #1198 is also Draft pending unrelated Platform lifecycle cleanup #1191/#1193. No bypass is authorized.

## Next action

After governance/lifecycle dependencies are terminal, refresh PR #33 and #1198, pass exact-head gates, merge the corrected audit, then execute the runner-split migration as a governed implementation slice with rollback.