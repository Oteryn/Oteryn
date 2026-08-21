# OTERYN-20260821-runner-topology-audit

Issue: #32
Repository: Oteryn/Oteryn
Status: ACTIVE
Mode: read-only audit; no runner mutation

## Objective

Establish exact current and desired GitHub Actions runner topology for Oteryn/Oteryn, Oteryn-Game, Oteryn-Platform and Oteryn-Atlas, including Synology execution boundaries, bootstrap feasibility, runner scope, groups, labels, version compatibility, isolation, routing and rollback.

## Proven starting evidence

- `Oteryn/Oteryn-Platform/.github/workflows/repair-synology-autostart.yml` uses `runs-on: oteryn-staging`.
- That job can invoke Docker control-plane operations on the Synology host (`docker ps`, `inspect`, `update`, `start`, `run`, `build`, image inspection).
- It observes the compose service `oteryn-deploy-runner/runner` and the `oteryn-staging` service family.
- Therefore the existing runner is a potential bootstrap execution surface, but organization registration/group capability is not yet proven.

## Required evidence

See Issue #32. Record UNKNOWN rather than infer inaccessible runner API/control-plane state.

## Safety

Do not modify, remove, re-register, broaden or replace the working runner during this audit. Any implementation follows only after a desired-state verdict and rollback plan.
