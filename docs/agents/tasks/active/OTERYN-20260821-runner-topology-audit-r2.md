# OTERYN-20260821-runner-topology-audit

Issue: #32
Repository: Oteryn/Oteryn
Status: PARTIAL — implementation observed; routing and GitHub control-plane scope still require proof
Mode: live evidence audit; no destructive runner mutation

## Objective

Record the current runner ownership, image provenance, scope evidence and migration status for META, Platform, Atlas and Game. This task is evidence only; it does not authorize changes to product repositories or runner registrations.

## Live checkpoint — 2026-08-21

The three named organization runner registrations and their running Synology containers are now observed:

| Workload | Registration | Group / pool observed | Image identity observed | State |
| --- | --- | --- | --- | --- |
| Platform | `oteryn-synology-platform` | `platform-runners` | immutable GHCR digest | running |
| Atlas | `oteryn-synology-atlas` | `atlas-runners` | immutable GHCR digest | running |
| Game | `oteryn-synology-game` | `game-runners` | immutable GHCR digest | running |

These registrations use the Oteryn organization URL and Actions Runner `2.336.0`. The new containers use separate registration/config/work state. This proves the runner-split implementation exists; it does **not** prove selected-repository restrictions, workflow routing, or successful workload execution.

## Current facts

- META remains GitHub-hosted; no local-runtime need is proven.
- The legacy `oteryn-synology-staging` runner is still present as rollback/bootstrap and still points at a mutable pre-transfer image/legacy source coordinate.
- A legacy Atlas/Game runner container remains observable. Its presence must not be treated as a replacement-path proof.
- Local inspection cannot read GitHub organization runner-group selected-repository restrictions. Until a GitHub organization control-plane readback proves each group is restricted to its intended repository, that property is `UNKNOWN`.
- No post-cutover repository workflow/job evidence proves that Atlas and Game workloads now run through their own registrations. That property is `UNKNOWN`.

## Findings

| ID | Severity | State | Finding |
| --- | --- | --- | --- |
| RUNNER-001 | HIGH | PARTIAL | New Platform/Atlas/Game runner containers use an immutable image digest; the retained legacy staging/legacy container path is still mutable and must be retired only after replacement proof. |
| RUNNER-002 | MEDIUM | UNKNOWN | The new image digest is immutable, but this audit has no independently verified base-image build provenance/readback. |
| RUNNER-003 | INFO | DONE | Observed runner version `2.336.0` meets the Node.js 24 Actions-runner prerequisite. |
| RUNNER-004 | INFO | UNKNOWN | Named groups/registrations exist, but selected-repository restriction and effective label scope need GitHub organization control-plane readback. |
| RUNNER-005 | HIGH | PARTIAL | Atlas-owned boundary is provisioned; no successful Atlas-owned preview/deploy/E2E job proves that cross-repository Platform execution has stopped. |
| RUNNER-006 | MEDIUM | PARTIAL | Game-owned boundary is provisioned; no successful Game-owned local runtime/integration job proves that Platform coupling has stopped. |
| RUNNER-007 | INFO | UNKNOWN | No live workflow-routing review establishes that arbitrary pull-request code cannot reach privileged local runners. |

## Required closeout evidence

1. Read back each GitHub organization runner group and prove selected-repository restriction, labels and membership.
2. Capture successful exact-head job evidence for Platform, Atlas and Game on their intended registrations, including label/provider identity.
3. Verify Atlas preview/deploy/E2E and Game local integration no longer execute from Platform workflows.
4. Confirm least-privilege mounts/capabilities for each runner image; do not copy Platform state access by default.
5. Retire the legacy mutable runner/container only after steps 1–4 and a bounded rollback decision.
6. Update #32 with exact evidence URLs/identifiers and re-evaluate all findings.

## Non-destructive rule

Do not unregister, remove, restart, alter, or delete the legacy rollback path or new registrations merely because they look old. Their replacement status is not yet proven.