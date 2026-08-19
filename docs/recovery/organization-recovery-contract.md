# Oteryn organization recovery and break-glass contract

Status date: 2026-08-19
Lifecycle authority: GitHub Issue #10
Governance authority: `docs/architecture/adr/0002-organization-governance-operating-model.md`

This is an organization-level recovery contract. Provider repositories remain authoritative for provider-specific database, deployment and application recovery. A canonical GitHub repository is a primary copy, not a backup by definition. `UNKNOWN` means that this audit did not prove the required recovery evidence.

## Recovery inventory

### Current permanent Git repository/history

- `BACKUP_SCOPE`: current Git objects and refs for `Oteryn/Oteryn`, `Oteryn/Oteryn-Game`, `Oteryn/Oteryn-Platform` and `Oteryn/Oteryn-Atlas`.
- `OWNER`: Oteryn organization owner/maintainer.
- `LOCATION/MECHANISM`: canonical GitHub remotes are primary storage. No independent, recurring, restore-tested backup covering the current heads of all four permanent repositories is proven.
- `RPO`: `UNKNOWN`.
- `RTO`: `UNKNOWN`.
- `RETENTION`: `UNKNOWN` for an independent current-history backup.
- `WHAT_IS_NOT_BACKED_UP`: GitHub Issues/PRs/comments/settings/rulesets/environments/secrets, packages/release assets and production data are outside Git history unless separately captured.
- `RESTORE_PROCEDURE`: restore only into an isolated scratch/private target first; run `git fsck --full`; compare every expected protected/default branch and tag by exact object ID; verify required current head SHAs; only then authorize controlled replacement/rebinding.
- `LAST_RESTORE_TEST`: `UNKNOWN` for a backup that covers the current heads of all four permanent repositories.
- `RESTORE_VALIDATION`: `UNKNOWN`.

`blakinio/Oteryn-v2` and bounded `blakinio/Otheryn` history are migration/reference provenance, not complete backups of later target-only history.

### Platform transfer-cut Git-history artifact

- `BACKUP_SCOPE`: the historical Platform Git repository state pinned to source `main=c567da9d9ae444110262774f8febf5a5abab2a90`, including a full Git bundle, mirror tarball and source head/tag snapshot.
- `OWNER`: Oteryn Platform migration closeout; terminal lifecycle remains coordinated by `Oteryn/Oteryn` and `Oteryn/Oteryn-Platform`.
- `LOCATION/MECHANISM`: Actions artifact `9325655630`, name `Oteryn-Platform-full-git-backup-2026-08-18`, from successful run `32140475110` in `Oteryn/Oteryn-Platform-Migration-Backup-20260818`; workflow repository `main=db381488697eee315bdf5840ab0d4f8807f7bfb0`.
- `RPO`: exact only for the pinned pre-transfer source cut `c567da9d9ae444110262774f8febf5a5abab2a90`; it is not a current Platform RPO.
- `RTO`: `UNKNOWN`; the restore drill proves correctness, not a contractual recovery-time objective.
- `RETENTION`: GitHub reports `expires_at=2026-08-25T13:06:44Z` for artifact `9325655630`. The temporary repository must not be archived merely because the artifact exists.
- `WHAT_IS_NOT_BACKED_UP`: post-transfer commits/settings, Issues/PR metadata, environments, secret values, packages/GHCR, deployment provider state and production databases.
- `RESTORE_PROCEDURE`:
  1. download artifact `9325655630` from run `32140475110` into an isolated scratch directory;
  2. verify bundle SHA-256 `dcd54ab36459db447087fff5490e06d643478f01e441fd5f65cfe061df8c5d60` and mirror-tar SHA-256 `0ff51dd0226595adfd2ffc505f1997cfb344cbb41f992642d3e0f6bb8ee33409` by artifact basename;
  3. run `tar -tzf` on the mirror archive;
  4. mirror-clone `Oteryn-Platform-full.bundle` into a new scratch repository;
  5. run `git fsck --full` and `git bundle verify`;
  6. compare restored `refs/heads` and `refs/tags` against `source-refs.txt` by exact object ID;
  7. assert restored `refs/heads/main=c567da9d9ae444110262774f8febf5a5abab2a90` before any recovery decision.
- `LAST_RESTORE_TEST`: `2026-08-19T09:31:15.6370182+02:00`, isolated operator scratch restore from artifact `9325655630`.
- `RESTORE_VALIDATION`: `PASS_WITH_KNOWN_PORTABILITY_DEFECT` for the artifact content: both recorded SHA-256 values matched, tar integrity passed, bundle mirror-clone succeeded, `git fsck --full` and `git bundle verify` passed, `11/11` recorded branch/tag refs matched exactly, and restored `main` matched `c567da9d9ae444110262774f8febf5a5abab2a90`.

Known defect: the artifact's `SHA256SUMS.txt` records absolute GitHub-runner paths under `/home/runner/work/_temp/platform-backup/`, so a literal `sha256sum -c SHA256SUMS.txt` is not portable after download. The drill verified the same hashes against artifact basenames instead. The artifact manifest also records `head_push_rc=1`; therefore this artifact proves rollback/reference content, not a successful target reseed operation.

Terminal gate for `Oteryn/Oteryn-Platform-Migration-Backup-20260818`: **RETAIN / DO NOT ARCHIVE YET** until Platform migration acceptance is independently proven, artifact retention/provenance is deliberately dispositioned and the checksum-portability defect has a durable resolution or replacement procedure. Never delete the repository or artifact as part of routine cleanup.

### Platform production data

- `BACKUP_SCOPE`: production database/application state.
- `OWNER`: `Oteryn/Oteryn-Platform` operations authority.
- `LOCATION/MECHANISM`: `UNKNOWN` at organization-governance level.
- `RPO`: `UNKNOWN`.
- `RTO`: `UNKNOWN`.
- `RETENTION`: `UNKNOWN`.
- `WHAT_IS_NOT_BACKED_UP`: not proven here.
- `RESTORE_PROCEDURE`: provider repository procedures remain authoritative.
- `LAST_RESTORE_TEST`: `UNKNOWN` for production. Platform documents controlled staging restore evidence, but explicitly states that staging timing is not production RPO/RTO evidence.
- `RESTORE_VALIDATION`: `UNKNOWN` for production.

### Packages, release assets and GitHub control plane

- `BACKUP_SCOPE`: GHCR/packages/release assets and repository/org settings, rulesets, environments, runner registrations/groups, deployments and Issue/PR lifecycle metadata.
- `OWNER`: repository owners plus organization governance.
- `LOCATION/MECHANISM`: `UNKNOWN`; current Git manifests/drift checks can describe expected state but do not constitute backups.
- `RPO`: `UNKNOWN`.
- `RTO`: `UNKNOWN`.
- `RETENTION`: `UNKNOWN`.
- `WHAT_IS_NOT_BACKED_UP`: secret values are never recoverable from GitHub metadata APIs; a separately governed source of truth is required.
- `RESTORE_PROCEDURE`: recreate first from accepted machine-readable desired state/provider IaC where available, then read back exact settings and validate required gates; packages/assets require content-identity proof before republishing.
- `LAST_RESTORE_TEST`: `UNKNOWN`.
- `RESTORE_VALIDATION`: `UNKNOWN`.

## Break-glass minimum

Break-glass is for containment and recovery, never a normal bypass path. Record the incident, affected repository/object identities, exact pre/post settings and validation evidence.

1. **Compromised PAT, GitHub App credential or deploy key** — freeze affected mutation/deployment paths; revoke the credential first; identify its scopes/installations; rotate dependent credentials; inspect audit/deployment history; re-enable only after exact-scope readback and validation. Never publish secret values in Issues or logs.
2. **Compromised self-hosted runner** — stop scheduling to the runner; remove/disable its registration or access before re-use; rotate credentials/secrets that could have reached it; preserve logs/evidence; rebuild/re-register from a trusted image; verify exact repository/group/label scope before accepting jobs.
3. **Compromised third-party Action** — stop workflows that consume it; pin/remove the affected action by immutable commit; reduce token permissions; invalidate exposed credentials; re-run on a trusted exact head before restoring required-gate status.
4. **Ruleset/protection weakened accidentally** — pause merges; capture current settings/audit evidence; restore the accepted protection contract; prove the stable required gate emits successfully on an exact representative head; read back the final ruleset/protection before resuming merges.
5. **Repository/package/environment deletion** — stop replacement writes; restore into an isolated/private target first; verify Git/package content identities and environment policy from accepted authority; perform controlled rebind/recreate only after review. Secret values require their independent source of truth.
6. **Loss of owner access** — do not add broad bypass credentials as a workaround. Use GitHub organization/account recovery/support and an independently governed second-owner/recovery path when one is proven. Current second-owner/recovery redundancy is `UNKNOWN`.
7. **Secret exposure** — revoke/disable before analysis when feasible; rotate every dependent credential/token; invalidate sessions; audit use; redeploy only from the independent secret source of truth; remove leaked material from current surfaces without destroying required incident evidence.

## Open recovery gaps

- `GAP-RECOVERY-001`: no independent recurring restore-tested backup is proven for current heads of all four permanent repositories.
- `GAP-RECOVERY-002`: GitHub control-plane/Issue/PR metadata backup and restore are unproven.
- `GAP-RECOVERY-003`: GHCR/package/release-asset recovery inventory and restore are unproven at organization level.
- `GAP-RECOVERY-004`: independent recovery source for GitHub/environment secret values is unproven.
- `GAP-RECOVERY-005`: second-owner/account-recovery redundancy is unproven.
- `GAP-RECOVERY-006`: Platform production backup/restore RPO/RTO remains unproven; staging evidence must not be promoted to production evidence.
- `GAP-RECOVERY-007`: Platform transfer artifact checksum manifest is not path-portable and expires on 2026-08-25 unless separately dispositioned.