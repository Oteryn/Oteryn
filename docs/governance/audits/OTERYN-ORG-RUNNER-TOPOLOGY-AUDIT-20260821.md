# Oteryn Organization Runner Topology Audit — 2026-08-21

Audit owner: `Oteryn/Oteryn#32`
Platform live-evidence owner: `Oteryn/Oteryn-Platform#1194`
Platform evidence PR: `Oteryn/Oteryn-Platform#1198`
Audit contract context: `OTERYN-ORG-AUDIT-v3.10`

## Verdict

`KEEP_REPOSITORY_SCOPED_PLATFORM_RUNNER`

The current organization generation does **not** need one self-hosted runner per repository and does **not** benefit from migrating the existing privileged Synology runner to organization scope.

Desired state:

| Repository | Default execution | Self-hosted desired state |
| --- | --- | --- |
| `Oteryn/Oteryn` | GitHub-hosted | `NOT_NEEDED` |
| `Oteryn/Oteryn-Game` | GitHub-hosted | `NOT_NEEDED` |
| `Oteryn/Oteryn-Platform` | GitHub-hosted for ordinary CI/test/security | keep the existing repository-scoped Synology runner for trusted Synology/staging operations only |
| `Oteryn/Oteryn-Atlas` | GitHub-hosted | `NOT_NEEDED` |
| `Oteryn/Oteryn-Platform-Migration-Backup-20260818` | none | `NOT_NEEDED`; repository is archived/read-only |

Do not create Game or Atlas Synology runners merely for symmetry. Do not move the current Platform runner to an organization runner group without a new workload/trust-boundary audit.

## Evidence basis

### Organization workflow inventory

Current retained workflow search found `oteryn-staging` / self-hosted routing only in `Oteryn/Oteryn-Platform`. No retained `oteryn-staging` or `self-hosted` routing was found in META, Game or Atlas.

Game's current Atlas semantic-search workflow, for example, runs on GitHub-hosted `ubuntu-24.04`. Atlas and META likewise have no proven host-local workload requiring the Synology runner.

### Platform registration and scheduling boundary

The accepted post-transfer Platform evidence records `oteryn-synology-staging` as repository-scoped. Current runner source reinforces that boundary:

- `deploy/synology/runner/entrypoint.sh` accepts an exact repository-shaped `RUNNER_URL`;
- registration uses the single custom label `oteryn-staging`;
- registration uses `--no-default-labels`;
- no organization URL / runner-group registration path is present.

The Actions job field `runner_group_name=Default` is only a group-display value and is not used to infer organization scope against the stronger registration/source evidence.

### Live Synology proof

Trusted-main Platform run `32454899481`, job `96690198992`, reported:

- runner name `oteryn-synology-staging`;
- Actions Runner version `2.336.0`;
- successful scheduling and execution on the existing Synology runner.

A bounded read-only Platform probe, run `32460223728`, job `96705516889`, additionally proved the current live execution boundary:

- Linux/X64;
- container `oteryn-synology-staging-runner`;
- container user `0:0`;
- restart policy `always`;
- Docker client `29.6.2`, server `24.0.2`, Compose `5.3.1`;
- read-write `/runner` and `/work` volumes;
- read-write `/var/run/docker.sock` bind mount;
- read-write staging-state bind mount;
- live runner image reference `ghcr.io/blakinio/oteryn-deploy-runner:main`;
- live image ID `sha256:bad8dc119e39553f5a9d958834562a44add4978e16f9a46df7c89507c06c24b8`.

The temporary probe did not publish environment dumps, credentials, secret values or application data. Its final non-zero result came only from attempting to parse a UTF-8-BOM-prefixed `.runner` JSON file after all required host/container facts had already been emitted. The temporary workflow changes were removed from the Platform evidence branch before closeout.

## Trust-boundary finding

The Platform runner is not a general-purpose compute worker. Root execution plus read-write Docker socket access makes jobs on it effectively Docker-host privileged, and the staging-state mount adds direct staging-state exposure.

Therefore organization-wide sharing would broaden the trust boundary without a demonstrated execution requirement. The correct default is GitHub-hosted execution; self-hosted is an exception for jobs that genuinely require the Synology control plane.

Permanent Platform workflows preserve this boundary: pull-request validation is GitHub-hosted where present, while live Synology jobs are bounded to `workflow_dispatch`, trusted `main` operations and/or the `synology-staging` environment. No permanent arbitrary pull-request job is routed onto `oteryn-staging`.

## Version compatibility

The live runner version is `2.336.0`. This is newer than the `2.327.1` minimum recorded for current Node.js 24 based Actions upgrades in the pending dependency evidence. Runner age therefore does not block those Platform workflows.

Runner freshness remains operationally important: GitHub documents that self-hosted runner software must remain updated for new Actions features and may stop receiving jobs when required updates are missed.

## Organization runner groups

GitHub supports organization self-hosted runner groups and can restrict a group to selected repositories. GitHub also recommends self-hosted runners primarily for private repositories because public-repository fork pull requests can be dangerous when workflows allow untrusted code onto the runner.

Those capabilities do not justify an organization migration by themselves. In the current Oteryn topology only Platform has a proven Synology workload, so repository scope is the smaller and safer trust boundary.

If another repository later proves a host-local workload, re-open the decision and evaluate a separate least-privilege runner/container plus repository-restricted organization group. Do not share the existing root/Docker-socket Platform runner across public repositories.

## Control-plane capability

GitHub's organization runner registration API requires organization `Self-hosted runners: write` permission. The currently connected GitHub action surface exposes repository and workflow operations but no organization runner/group/registration-token mutation action.

This is `NOT_BLOCKING` for the chosen desired state because no organization-runner migration is required. It becomes relevant only if a later approved topology change requires organization-scoped runner creation.

## Findings

| ID | Severity | State | Finding |
| --- | --- | --- | --- |
| `RUNNER-001` | HIGH | OPEN | The privileged live runner still uses mutable pre-transfer image coordinate `ghcr.io/blakinio/oteryn-deploy-runner:main`. |
| `RUNNER-002` | MEDIUM | OPEN | `deploy/synology/runner/Dockerfile` uses mutable base `ghcr.io/actions/actions-runner:latest`. |
| `RUNNER-003` | INFO | PASS | Runner `2.336.0` satisfies the current Node.js 24 runner-version prerequisite. |
| `RUNNER-004` | INFO | PASS | `--no-default-labels` + `oteryn-staging` prevents generic `self-hosted` scheduling. |
| `RUNNER-005` | INFO | PASS | No retained self-hosted routing was found in META, Game or Atlas. |
| `RUNNER-006` | INFO | PASS | Permanent Platform pull-request paths do not execute on the privileged Synology runner. |

`RUNNER-001` and `RUNNER-002` are tracked by `Oteryn/Oteryn-Platform#1199`. Their remediation must preserve the existing repository registration/config volume, custom-label-only routing and rollback identity; they do not justify changing runner scope.

## Final architecture

```text
Oteryn organization
|
+-- Oteryn/Oteryn
|   +-- GitHub-hosted only
|
+-- Oteryn/Oteryn-Game
|   +-- GitHub-hosted only
|
+-- Oteryn/Oteryn-Platform
|   +-- GitHub-hosted: ordinary CI/test/security
|   +-- repository-scoped: oteryn-synology-staging
|       +-- custom label: oteryn-staging
|       +-- trusted Synology/staging operations only
|       +-- root + Docker socket = privileged boundary; do not share
|
+-- Oteryn/Oteryn-Atlas
|   +-- GitHub-hosted only
|
+-- archived Platform migration backup
    +-- no runner
```

## Audit closeout status

The technical runner-topology decision is complete. Publication/merge of the audit records remains subject to the normal repository governance path; no branch-protection, review or CI bypass is authorized. Platform evidence PR #1198 is intentionally held while an unrelated pre-existing Platform live-task liveness defect is being closed by its existing owner (#1191 / PR #1193). META PR #33 remains Draft while the active META AI-review hardening dependency (#30) is terminalized.
