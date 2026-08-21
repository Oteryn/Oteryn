# Oteryn organization recovery and break-glass contract

Status date: 2026-08-20
Lifecycle authority: GitHub Issue #10
Governance authority: `docs/architecture/adr/0002-organization-governance-operating-model.md`

This is an organization-level recovery contract. Provider repositories remain authoritative for provider-specific databases, deployments, applications and production recovery. A canonical GitHub repository is primary storage, not a backup by definition. `UNKNOWN` is intentional where current evidence does not prove a recovery property.

## Recovery inventory

### Current permanent Git repository/history

- `BACKUP_SCOPE`: current Git objects and refs for `Oteryn/Oteryn`, `Oteryn/Oteryn-Game`, `Oteryn/Oteryn-Platform` and `Oteryn/Oteryn-Atlas`.
- `OWNER`: Oteryn organization owner/maintainer.
- `LOCATION/MECHANISM`: canonical GitHub remotes are primary storage. No independent recurring restore-tested backup covering the current heads of all four permanent repositories is proven.
- `RPO`: `UNKNOWN`.
- `RTO`: `UNKNOWN`.
- `RETENTION`: `UNKNOWN` for an independent current-history backup.
- `WHAT_IS_NOT_BACKED_UP`: GitHub Issues/PRs/comments/settings/rulesets/environments/secrets, packages/release assets and production data are outside Git history unless separately captured.
- `RESTORE_PROCEDURE`: restore only into an isolated scratch/private target first; run `git fsck --full`; compare every expected protected/default branch and tag by exact object ID; verify required current head SHAs; only then authorize controlled replacement/rebinding.
- `LAST_RESTORE_TEST`: `UNKNOWN` for a backup covering the current heads of all four permanent repositories.
- `RESTORE_VALIDATION`: `UNKNOWN`.

`blakinio/Oteryn-v2` and bounded `blakinio/Otheryn` history are migration/reference provenance, not complete backups of later target-only history. The current machine-readable inventory still classifies the former Game migration source as retirement-pending; its final archival/source-retirement state is therefore `UNKNOWN` in this recovery contract until the manifest and live proof are reconciled.

### Platform transfer-cut Git-history artifact

- `BACKUP_SCOPE`: historical Platform Git state pinned to pre-transfer source `main=c567da9d9ae444110262774f8febf5a5abab2a90`, including a full Git bundle, mirror tarball and exact source ref snapshot.
- `OWNER`: Oteryn Platform migration closeout under organization governance.
- `LOCATION/MECHANISM`: durable GitHub Release `platform-transfer-cut-2026-08-18` in archived administrative repository `Oteryn/Oteryn-Platform-Migration-Backup-20260818` (repository ID `1338405017`). The original Actions artifact `9325655630` from run `32140475110` is historical source evidence only and is no longer the retention dependency.
- `RPO`: exact only for pinned pre-transfer cut `c567da9d9ae444110262774f8febf5a5abab2a90`; it is not current Platform RPO.
- `RTO`: `UNKNOWN`; the restore drill proves correctness, not a production recovery-time objective.
- `RETENTION`: durable Release assets retained with the archived read-only evidence repository; no dependency on the Actions artifact expiry of `2026-08-25T13:06:44Z` remains.
- `WHAT_IS_NOT_BACKED_UP`: post-transfer commits/settings, Issues/PR metadata, environments, secret values, packages/GHCR, deployment-provider state and production databases.
- `RESTORE_PROCEDURE`:
  1. initialize an isolated scratch directory, for example `WORKDIR="$(mktemp -d)"`, then download the six assets from Release `platform-transfer-cut-2026-08-18` into `"$WORKDIR"`;
  2. verify asset basenames against the exact SHA-256 identities below and GitHub Release digest readback;
  3. run `tar -tzf "$WORKDIR/Oteryn-Platform-mirror.git.tar.gz"`;
  4. clone `Oteryn-Platform-full.bundle` into a new isolated repository, for example `git clone "$WORKDIR/Oteryn-Platform-full.bundle" "$WORKDIR/restored-platform"`;
  5. run `git -C "$WORKDIR/restored-platform" fsck --full` and `git -C "$WORKDIR/restored-platform" bundle verify "$WORKDIR/Oteryn-Platform-full.bundle"`;
  6. compare restored heads/tags against `"$WORKDIR/source-refs.txt"` by exact object ID;
  7. require restored `refs/heads/main=c567da9d9ae444110262774f8febf5a5abab2a90` before treating the cut as valid recovery evidence;
  8. never overwrite canonical `Oteryn/Oteryn-Platform` from this historical cut without a separately authorized recovery incident.
- `LAST_RESTORE_TEST`: isolated restore drill on 2026-08-19 plus independent re-download/hash/readback and durable Release publication on 2026-08-20.
- `RESTORE_VALIDATION`: `PASS` for the historical transfer cut: tar integrity, bundle clone/verify, `git fsck --full`, exact 11/11 ref comparison and exact restored main passed; durable Release asset identities were read back after upload.

Exact durable asset identities:

| Asset | Size | SHA-256 |
| --- | ---: | --- |
| `Oteryn-Platform-full.bundle` | 13,604,250 | `dcd54ab36459db447087fff5490e06d643478f01e441fd5f65cfe061df8c5d60` |
| `Oteryn-Platform-mirror.git.tar.gz` | 14,411,720 | `0ff51dd0226595adfd2ffc505f1997cfb344cbb41f992642d3e0f6bb8ee33409` |
| `source-refs.txt` | 978 | `f97a8f859d2896c69f25668f179d2933d5862012ed5c5c8e753bc6d60d8f886a` |
| `source-refs.snapshot.txt` | 978 | `f97a8f859d2896c69f25668f179d2933d5862012ed5c5c8e753bc6d60d8f886a` |
| `manifest.txt` | 215 | `6852fb3c058a7142f003c0b788fed6764a23e332c3b060811a7a128e35eb09fe` |
| `SHA256SUMS.txt` | 274 | `c1afbfcb98a34593378e31173bc922166960151894548be45679e61346e9e188` |

Historical defect resolution: the original `SHA256SUMS.txt` embeds absolute GitHub-runner paths. The defect is preserved as provenance rather than rewritten. The durable procedure validates by asset basename using the explicit identities above and Release digest readback, so the portability defect no longer blocks recovery. The historical manifest's `head_push_rc=1` remains evidence of a failed temporary reseed attempt, not proof of target seeding.

Terminal gate for `Oteryn/Oteryn-Platform-Migration-Backup-20260818`: **PARTIAL — ARCHIVED_READ_ONLY OBSERVED, MANIFEST RECONCILIATION PENDING**. Provider transfer acceptance, retention/provenance disposition and a durable checksum-portability procedure are recorded, but the current canonical inventory still says `terminal_disposition_required`. This contract does not override that machine-readable state. Reconcile the manifest against live repository evidence before declaring the terminal gate satisfied. The one-off seed workflow was removed before archival; deletion is not presumed required.

### Platform production data

- `BACKUP_SCOPE`: production database/application state.
- `OWNER`: `Oteryn/Oteryn-Platform` operations authority.
- `LOCATION/MECHANISM`: `UNKNOWN` at organization-governance level.
- `RPO`: `UNKNOWN`.
- `RTO`: `UNKNOWN`.
- `RETENTION`: `UNKNOWN`.
- `WHAT_IS_NOT_BACKED_UP`: not proven here.
- `RESTORE_PROCEDURE`: provider-repository procedures remain authoritative.
- `LAST_RESTORE_TEST`: `UNKNOWN` for production. Staging restore evidence is not production RPO/RTO evidence.
- `RESTORE_VALIDATION`: `UNKNOWN` for production.

### Packages, release assets and GitHub control plane

- `BACKUP_SCOPE`: GHCR/packages/release assets and repository/org settings, rulesets/protection, environments, runner registrations/groups, deployments and Issue/PR lifecycle metadata.
- `OWNER`: repository owners plus organization governance.
- `LOCATION/MECHANISM`: `UNKNOWN`; desired-state manifests/drift checks describe expected state but are not backups.
- `RPO`: `UNKNOWN`.
- `RTO`: `UNKNOWN`.
- `RETENTION`: `UNKNOWN`.
- `WHAT_IS_NOT_BACKED_UP`: secret values are never recoverable from GitHub metadata APIs; a separately governed source of truth is required.
- `RESTORE_PROCEDURE`: recreate first from accepted machine-readable desired state/provider IaC where available, then read back exact settings and validate required gates; packages/assets require content-identity proof before republishing.
- `LAST_RESTORE_TEST`: `UNKNOWN`.
- `RESTORE_VALIDATION`: `UNKNOWN`.

## Break-glass minimum

Break-glass is for containment and recovery, never a normal bypass path. Record incident identity, affected repository/object IDs, exact pre/post settings and validation evidence.

1. **Compromised PAT, GitHub App credential or deploy key** — freeze affected mutation/deployment paths; revoke first; identify scopes/installations; rotate dependent credentials; inspect audit/deployment history; re-enable only after exact-scope readback and validation. Never publish secret values in Issues or logs.
2. **Compromised self-hosted runner** — stop scheduling; remove/disable its registration or access before reuse; rotate reachable credentials/secrets; preserve logs/evidence; rebuild/re-register from a trusted image; verify exact repository/group/label scope before accepting jobs.
3. **Compromised third-party Action** — stop consuming workflows; pin/remove the affected action by immutable commit; reduce token permissions; invalidate exposed credentials; re-run on a trusted exact head before restoring required-gate status.
4. **Ruleset/protection weakened accidentally** — pause merges; capture live settings/audit evidence; restore the accepted protection contract; prove stable required gates on an exact representative head; read back final protection before resuming merges.
5. **Repository/package/environment deletion** — stop replacement writes; restore into isolated/private target first; verify content identities and environment policy; perform controlled rebind/recreate only after review. Secret values require their independent source of truth.
6. **Loss of owner access** — do not add broad bypass credentials. Use GitHub account/organization recovery/support and an independently governed second-owner/recovery path when proven. Current second-owner/recovery redundancy is `UNKNOWN`.
7. **Secret exposure** — revoke/disable before analysis when feasible; rotate every dependent credential/token; invalidate sessions; audit use; redeploy only from the independent secret source of truth; remove leaked material from current surfaces without destroying required incident evidence.

## Open recovery gaps

- `GAP-RECOVERY-001`: no independent recurring restore-tested backup is proven for current heads of all four permanent repositories.
- `GAP-RECOVERY-002`: GitHub control-plane/Issue/PR metadata backup and restore are unproven.
- `GAP-RECOVERY-003`: GHCR/package/release-asset recovery inventory and restore are unproven at organization level.
- `GAP-RECOVERY-004`: independent recovery source for GitHub/environment secret values is unproven.
- `GAP-RECOVERY-005`: second-owner/account-recovery redundancy is unproven.
- `GAP-RECOVERY-006`: Platform production backup/restore RPO/RTO remains unproven; staging evidence must not be promoted to production evidence.

`GAP-RECOVERY-007` is **PARTIAL**: the transfer-cut artifact and checksum-portability procedure are recorded, but the current machine-readable inventory still requires terminal-disposition reconciliation. This contract does not declare the administrative repository finally archived or the gap closed until that reconciliation has live evidence.
