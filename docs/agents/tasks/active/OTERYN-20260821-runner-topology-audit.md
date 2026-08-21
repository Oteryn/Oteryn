# OTERYN-20260821-runner-topology-audit

Issue: #32
Repository: Oteryn/Oteryn
Status: VALIDATING
Mode: read-only audit; no runner mutation

## Objective

Establish exact current and desired GitHub Actions runner topology for Oteryn/Oteryn, Oteryn-Game, Oteryn-Platform and Oteryn-Atlas, including Synology execution boundaries, bootstrap feasibility, runner scope, groups, labels, version compatibility, isolation, routing and rollback.

## Verdict

`KEEP_REPOSITORY_SCOPED_PLATFORM_RUNNER`

Current desired state:

- `Oteryn/Oteryn`: GitHub-hosted only.
- `Oteryn/Oteryn-Game`: GitHub-hosted only.
- `Oteryn/Oteryn-Platform`: GitHub-hosted by default; keep the existing repository-scoped `oteryn-synology-staging` for trusted Synology/staging operations only.
- `Oteryn/Oteryn-Atlas`: GitHub-hosted only.
- archived Platform migration backup: no runner.

Do not create Game/Atlas self-hosted runners now. Do not migrate the current privileged Platform runner to organization scope merely for symmetry.

Canonical META report candidate:
`docs/governance/audits/OTERYN-ORG-RUNNER-TOPOLOGY-AUDIT-20260821.md`

## Verified evidence

Platform live evidence is owned by `Oteryn/Oteryn-Platform#1194` / PR #1198.

- trusted-main run `32454899481`, job `96690198992`: runner `oteryn-synology-staging`, Actions Runner `2.336.0`;
- bounded live probe run `32460223728`, job `96705516889`: Linux/X64, container user `0:0`, state running, restart always, Docker client `29.6.2`, server `24.0.2`, Compose `5.3.1`;
- read-write runner mounts include `/runner`, `/work`, `/var/run/docker.sock` and staging state;
- live image is `ghcr.io/blakinio/oteryn-deploy-runner:main` at image ID `sha256:bad8dc119e39553f5a9d958834562a44add4978e16f9a46df7c89507c06c24b8`;
- current Platform registration source is repository-shaped and uses `--no-default-labels` with custom label `oteryn-staging`;
- no retained `oteryn-staging`/`self-hosted` routing was found in META, Game or Atlas;
- permanent Platform pull-request code is not routed onto the privileged Synology runner.

The temporary read-only probe changes were removed before Platform evidence closeout. No runner registration, Docker resource, staging runtime, secret or protected setting was changed by the audit.

## Findings

- `RUNNER-001` HIGH: mutable pre-transfer live runner image coordinate. Tracked by `Oteryn/Oteryn-Platform#1199`.
- `RUNNER-002` MEDIUM: runner Dockerfile base uses mutable `ghcr.io/actions/actions-runner:latest`. Tracked by #1199.
- `RUNNER-003` PASS: live runner `2.336.0` satisfies the current Node.js 24 runner-version prerequisite.
- `RUNNER-004` PASS: `--no-default-labels` + `oteryn-staging` isolates generic self-hosted routing.
- `RUNNER-005` PASS: no retained self-hosted routing in META/Game/Atlas.
- `RUNNER-006` PASS: permanent Platform PR paths do not execute on the privileged Synology runner.

## Current closeout dependencies

- META PR #30 is still open and owns active AI-review gate hardening. PR #33 must remain Draft until that governance dependency is terminal and then pass the normal protected path.
- Platform evidence PR #1198 is Draft. Its own CI is green; Agent Governance remains red only because the already-merged Atlas deployment task for PR #1192 has stale lifecycle state. That cleanup is already owned by Platform #1191 / PR #1193. No bypass is authorized.

## Safety

Do not modify, remove, re-register, broaden or replace the working runner as part of this audit. The topology audit concludes that no scope migration is needed. Runner image/provenance hardening is a separate Platform task (#1199) and must preserve working registration/config and rollback state.

## Next action

After META #30 and Platform #1191/#1193 are terminal, refresh PR #33 and Platform PR #1198 onto their current mains, run exact-head required checks/reviews, merge normally, archive task records and close Issues #32/#1194. The technical topology verdict itself is complete.