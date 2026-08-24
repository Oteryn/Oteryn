# OTERYN-V310-ORGANIZATION-RECOVERY-CLOSEOUT

PROMPT_ID: `OTERYN-V310-ORGANIZATION-RECOVERY-CLOSEOUT`
PROMPT_VERSION: `1.0`
STATUS: `READY`
PROGRAMME: `OTERYN-ORG-AUDIT-v3.10`

Primary repository: `https://github.com/Oteryn/Oteryn`
Mode: autonomous bounded recovery evidence/implementation closeout, fail-closed on owner decisions.

## Objective

Close only the organization-recovery portion of v3.10, specifically `GAP-RECOVERY-001` through `GAP-RECOVERY-006`, to the maximum truthfully achievable state under current authorization.

Target gaps:
- `GAP-RECOVERY-001`: independent recurring restore-tested backup for current heads of all four permanent repositories;
- `GAP-RECOVERY-002`: GitHub control-plane / Issue / PR metadata backup and restore;
- `GAP-RECOVERY-003`: GHCR/package/release-asset recovery inventory and restore;
- `GAP-RECOVERY-004`: independent recovery source for GitHub/environment secret values;
- `GAP-RECOVERY-005`: second-owner/account-recovery redundancy;
- `GAP-RECOVERY-006`: Platform production backup/restore RPO/RTO evidence.

`GAP-RECOVERY-007` is already terminal historical transfer-cut evidence and must not be reopened.

## HARD SCOPE LOCK — HIGHEST PRIORITY

You are authorized to work ONLY on recovery GAPs 001..006 and their deterministic META evidence/validation.

Do not fix Documentation/Agent IA, Game/Platform/Atlas product work, migrations, runner topology, CI architecture, security findings, dependencies, releases or production issues merely because they are observed during recovery analysis.

Out-of-scope discoveries are recorded only as:

`OUT_OF_SCOPE_FINDING: <exact factual description>`

Do not create new unrelated tasks. If a provider/external requirement is necessary to close a recovery GAP but is outside current authority, classify it as an exact blocker/owner decision; do not silently broaden scope.

## Repository and mutation boundary

META WRITE ACCESS: `Oteryn/Oteryn` only.

Provider repositories may be inspected read-only for existing recovery evidence/contracts. Do not write Game, Platform or Atlas from this prompt.

External systems may be inspected read-only when authorized and available. Do NOT create or delete cloud accounts, storage, organization owners, credentials, secrets, production backups, databases, protected-environment state, billing resources or external recovery infrastructure without a separate explicit owner decision authorizing that exact mutation.

Do not read or expose secret values. Secret metadata is not a secret backup.

## Authorized META write surfaces

Only when directly required for recovery closeout:
- `docs/recovery/**`;
- `docs/evidence/**` for sanitized immutable recovery evidence;
- `ecosystem/**` only for machine-readable recovery/desired-state facts that belong in META;
- `tools/governance/**` and `tools/recovery/**` for deterministic read-only/export/validation logic;
- `.github/workflows/organization-recovery-*.yml` only for safe, non-production recovery evidence collection that does not pretend same-control-plane storage is an independent backup.

Do not modify the open v3.10 terminal report/PR in this workstream. The later final coordinator will reconcile the report after all parallel workstreams merge.

## Recovery evidence rules

1. A canonical GitHub repository is primary storage, not an independent backup.
2. A backup claim requires an independent recovery copy appropriate to the failure mode being claimed.
3. A desired-state manifest is not a backup of Issues/PRs/settings/packages/secrets.
4. A successful export is not a restore test. Each completed recovery class needs an isolated restore/reconstruction validation.
5. Staging restore evidence does not prove production RPO/RTO.
6. Secret names/scopes do not prove recoverable secret values.
7. Second-owner redundancy requires actual independent owner/account recovery proof, not a policy sentence.
8. Do not invent RPO/RTO targets. Business-impact targets are owner decisions unless already accepted in authoritative provider policy.
9. `UNKNOWN` is mandatory when proof is unavailable; never close a GAP by wording alone.

## Gap-specific acceptance

### GAP-RECOVERY-001
Prove or establish a recurring independent backup for the current Git history of META/Game/Platform/Atlas, with owner, mechanism, retention, schedule/RPO intent, restore procedure and at least one isolated restore validation bound to current or explicitly measured backup-generation heads.

### GAP-RECOVERY-002
Prove an export/recovery mechanism for applicable GitHub control-plane/lifecycle metadata (at minimum repository identity/protection/rulesets/Issues/PR metadata and other in-scope settings), plus deterministic reconstruction/readback validation. Explicitly list surfaces that GitHub/API access cannot export or restore.

### GAP-RECOVERY-003
Inventory current GHCR/package/release assets by immutable identity where accessible and prove a recovery/republish procedure with an isolated or non-destructive validation. Do not delete or overwrite current packages to prove recovery.

### GAP-RECOVERY-004
Identify the independently governed source of truth for required secret values and prove a safe recovery procedure without exposing values. If no independent secret source exists, this GAP requires an owner decision and must remain BLOCKED/UNKNOWN; do not create a secret store without authorization.

### GAP-RECOVERY-005
Verify actual second-owner/account-recovery redundancy. If adding/changing organization ownership is required, stop for explicit owner authorization; never self-authorize identity/ownership changes.

### GAP-RECOVERY-006
Read Platform provider recovery authority and verify whether production backup mechanism, retention, restore test, RPO and RTO are directly proven. Do not run destructive production restore tests. If production RPO/RTO targets or backup mechanism require owner/provider operational decisions, report the exact decision and leave the GAP fail-closed.

## Parallel-work safety

Game, Platform and Atlas Documentation/Agent IA agents may run concurrently. This Recovery agent must not edit their repositories or their task records. Read-only provider evidence is allowed only for recovery facts.

Use one META Issue/task, one branch and one PR for this work. Do not modify v3.10 PR #43 or its branch.

## Validation

Before completion:
- map GAP-RECOVERY-001..006 one-by-one to `PASS`, `UNKNOWN`, or `BLOCKED_OWNER_DECISION` with exact evidence;
- run deterministic validators for every machine-readable recovery artifact;
- verify no secrets/private payloads are committed or printed;
- verify any backup/restore claim includes both generation and restore/reconstruction evidence;
- inspect full diff and exact changed paths;
- run normal META required checks on the exact final head;
- obtain required review under current META policy;
- squash merge only if no material recovery `UNKNOWN` required for the claimed task completion remains;
- verify resulting `main` and branch cleanup.

If one or more GAPs genuinely require owner decisions that were not previously made, the correct terminal result for this invocation is BLOCKED with the smallest exact decisions required. Do not lower acceptance to obtain DONE.

## Completion definition

DONE requires `GAP-RECOVERY-001..006` all to have direct terminal recovery evidence satisfying their definitions. Historical `GAP-RECOVERY-007` remains preserved but is not part of the work.

Do not claim `OTERYN_ORG_AUDIT_V3_10=COMPLETE`; the final META coordinator runs only after all parallel workstreams finish.

## Final response

Return only:

STATUS: DONE | BLOCKED
ALIAS: OTERYN-V310-ORGANIZATION-RECOVERY-CLOSEOUT
ISSUE: <url/number>
PR: <url/number or NONE>
MERGE_COMMIT: <sha or NONE>
RECOVERY_GAPS:
- GAP-RECOVERY-001: PASS | UNKNOWN | BLOCKED_OWNER_DECISION
- GAP-RECOVERY-002: PASS | UNKNOWN | BLOCKED_OWNER_DECISION
- GAP-RECOVERY-003: PASS | UNKNOWN | BLOCKED_OWNER_DECISION
- GAP-RECOVERY-004: PASS | UNKNOWN | BLOCKED_OWNER_DECISION
- GAP-RECOVERY-005: PASS | UNKNOWN | BLOCKED_OWNER_DECISION
- GAP-RECOVERY-006: PASS | UNKNOWN | BLOCKED_OWNER_DECISION
OWNER_DECISIONS_REQUIRED: <exact list or NONE>
CHANGED_PATHS: <exact list or NONE>
VALIDATION: <exact evidence>
OUT_OF_SCOPE_FINDINGS: <list or NONE>
BLOCKERS: <list or NONE>
SCOPE_CONFIRMATION: No work outside v3.10 organization recovery GAP-RECOVERY-001..006 was performed.
