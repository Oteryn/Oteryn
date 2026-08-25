# OTERYN-V310-ORGANIZATION-RECOVERY-AUTHORIZED-CONTINUATION

PROMPT_ID: `OTERYN-V310-ORGANIZATION-RECOVERY-AUTHORIZED-CONTINUATION`
PROMPT_VERSION: `1.0`
STATUS: `READY`
PROGRAMME: `OTERYN-ORG-AUDIT-v3.10`
CONTINUES: `OTERYN-V310-ORGANIZATION-RECOVERY-CLOSEOUT`
PRIMARY_LIFECYCLE: `Oteryn/Oteryn#59`
CURRENT_DRAFT_PR: `Oteryn/Oteryn#60`

Primary repository: `https://github.com/Oteryn/Oteryn`
Mode: autonomous bounded recovery implementation + evidence + closeout.

## Objective

Continue the already-started v3.10 organization recovery workstream and finish every technically achievable scoped recovery GAP without reopening unrelated work.

Required target state:
- `GAP-RECOVERY-001`: `PASS`;
- `GAP-RECOVERY-002`: `PASS`;
- `GAP-RECOVERY-003`: `PASS`;
- `GAP-RECOVERY-004`: `PASS` if recoverable secret-value source exists or can be established safely from an already authorized readable source; otherwise report the exact additional blocker without exposing any value;
- `GAP-RECOVERY-005`: `BLOCKED_EXTERNAL_PREREQUISITE` because only one organization owner/account currently exists;
- `GAP-RECOVERY-006`: `PASS` using non-destructive production backup/restore evidence.

`GAP-RECOVERY-005` is a known external prerequisite. DO NOT stop the whole invocation merely because it cannot pass. Finish `001..004` and `006` first.

`GAP-RECOVERY-007` remains terminal historical evidence and MUST NOT be reopened.

## OWNER AUTHORIZATION — CURRENT INVOCATION

The repository owner has already authorized this recovery implementation with the following exact constraints:

1. Implement recovery work for `GAP-RECOVERY-001..006`.
2. Use Synology as independent recovery storage where appropriate.
3. Grant/use only the minimum GitHub permissions strictly required for the recovery evidence or backup operation.
4. Never expose secret values in chat, logs, issues, PRs, commits, artifacts, command output or screenshots.
5. Do not perform a destructive restore into production.
6. Do not invent, create or add a second organization owner/account. The current absence of a second owner is accepted as an external prerequisite for `GAP-RECOVERY-005`.
7. Do not ask again whether to continue merely because `GAP-RECOVERY-005` is blocked.

This authorization does NOT grant general production, security, migration, CI, runner or product-change authority.

## HARD SCOPE LOCK — HIGHEST PRIORITY

You are authorized to work ONLY on v3.10 organization recovery `GAP-RECOVERY-001..006` and the exact implementation/evidence required to terminalize those GAPs under the authorization above.

Anything unrelated is OUT OF SCOPE.

Do not repair unrelated product defects, documentation IA, migrations, branch protection, runner topology, dependencies, release process, CI architecture or general security findings.

Record unrelated discoveries only as:

`OUT_OF_SCOPE_FINDING: <exact factual description>`

Do not create new unrelated tasks.

If a newly discovered dependency truly prevents a target GAP from closing, record:

`BLOCKED_BY_OUT_OF_SCOPE_DEPENDENCY: <exact dependency>`

and continue every other independent recovery GAP that remains executable.

## Existing lifecycle — reuse, do not fork

- Continue `Oteryn/Oteryn#59` as the recovery lifecycle authority.
- Continue/reconcile Draft PR `Oteryn/Oteryn#60` when technically safe.
- Do NOT create a second organization-recovery programme merely to avoid the existing blocker history.
- Refresh both against current protected `main` before new mutations.
- Preserve the existing fail-closed evidence; update/supersede stale blocker statements only with new direct evidence.
- Do not modify the separate v3.10 final audit successor/report PR. Final coordination happens later.

## Capability discovery — mandatory

Before declaring any recovery GAP blocked by access:

- inspect GitHub connector/actions and current authenticated capabilities;
- inspect authorized Remote Desktop / Synology execution paths;
- inspect repository-owned recovery tooling and current host-local capabilities;
- distinguish missing tool, missing permission, missing secret source, policy restriction and genuinely absent recovery asset;
- use the safest available authorized path.

Do not say `NO ACCESS` or `BLOCKED` while a safe authorized execution path remains untested.

## Mutation boundaries

### META repository

Writes are allowed only when directly required for this recovery work:
- `docs/recovery/**`;
- `docs/evidence/**` with sanitized immutable evidence only;
- `tools/recovery/**`;
- `tools/governance/**` only when recovery validation integration strictly requires it;
- `ecosystem/**` only for canonical recovery facts/desired state;
- `.github/workflows/organization-recovery-*.yml` only for bounded recovery automation that preserves current required-check contracts.

Do not change unrelated META governance or the v3.10 final report branch.

### Provider repositories

Default: read-only.

A provider write is allowed ONLY if direct recovery implementation for that provider cannot otherwise satisfy the scoped GAP and ONLY on recovery-specific surfaces such as existing `docs/recovery/**`, `docs/operations/**`, `tools/recovery/**`, or narrowly named recovery workflows.

If a provider write is needed:
- use its own Issue/branch/PR lifecycle;
- read that repository's `AGENTS.md` first;
- never touch runtime/product/gameplay/content/application source;
- never absorb unrelated provider work;
- keep the change independently reviewable and merge it before claiming recovery PASS.

### Synology / external recovery plane

Authorized only for recovery implementation:
- independent backup storage;
- isolated restore/reconstruction drills;
- encrypted recovery material;
- checksums/manifests;
- recovery-specific scheduled jobs;
- isolated local registry/container/archive validation where needed.

Do not delete or overwrite unrelated data. Do not expose private payloads.

### GitHub permissions

You may add/use only the smallest permission needed for a scoped recovery operation.

Requirements:
- prefer read-only scopes;
- record permission purpose without recording tokens/secrets;
- do not grant broad admin scopes when a narrower package/repository scope is sufficient;
- do not weaken branch protection/rulesets;
- do not change organization ownership;
- remove temporary elevated capability after validation when it is no longer required.

## GAP-RECOVERY-001 — independent recurring Git backup

Establish and prove independent recurring Git-history backup for all four permanent repositories:
- `Oteryn/Oteryn`;
- `Oteryn/Oteryn-Game`;
- `Oteryn/Oteryn-Platform`;
- `Oteryn/Oteryn-Atlas`.

Preferred independent destination: authorized Synology storage.

Acceptance requires:
1. exact source repository identities and protected-main heads recorded per generation;
2. complete recoverable Git refs/history appropriate to the failure mode;
3. deterministic manifest/checksum;
4. recurring schedule and retention policy;
5. generation result that fails closed on incomplete repositories;
6. isolated restore drill into a disposable location;
7. restored refs/objects verified against the backup manifest;
8. no push/restore into production GitHub during the drill.

A local clone alone is not PASS. A backup without restore validation is not PASS.

## GAP-RECOVERY-002 — GitHub control-plane and lifecycle metadata

Establish recurring independent export/recovery for applicable GitHub control-plane metadata, including at minimum:
- repository identity/default branch;
- protection/rulesets and required-check contracts;
- Issues and relevant metadata;
- Pull Requests, reviews/comments and lifecycle evidence needed for reconstruction;
- labels/milestones/settings that are materially part of recovery;
- other recoverable in-scope administrative metadata discovered by the existing audit tooling.

Store sanitized independent recovery copies on Synology where appropriate.

Acceptance requires:
1. recurring export with exact generation identity and checksums;
2. no secret values in exports;
3. deterministic parser/validator;
4. non-destructive reconstruction drill into an isolated local representation or other safe target;
5. explicit inventory of API surfaces that cannot be reconstructed automatically;
6. proof that an export is not being confused with the primary GitHub control plane itself.

## GAP-RECOVERY-003 — GHCR/packages/releases

Use the minimum package capability required, including `read:packages` only if needed.

Acceptance requires:
1. current accessible GHCR/package inventory by immutable identity/digest;
2. current release/release-asset inventory, including explicit zero inventory where true;
3. independent recoverable copy or source for every asset class claimed recoverable;
4. Synology/independent storage where appropriate;
5. non-destructive validation of recovery, such as isolated OCI/archive verification or local isolated registry/load test;
6. no deletion/overwrite of current packages merely to prove recovery;
7. temporary package-read capability removed or reduced after use if it is not otherwise required.

If a private package remains unreadable after all authorized minimal-permission paths are exhausted, record the exact additional blocker; do not fake PASS.

## GAP-RECOVERY-004 — secret-value recovery

Secret metadata is NOT a secret backup.

Acceptance requires an independently governed recoverable source for required secret VALUES without exposing them.

Allowed behavior:
- discover an already authorized readable source of the required secret values;
- create/update an encrypted independent recovery copy on Synology or another already authorized independent recovery store;
- validate decryptability/recovery in a way that does not print values;
- validate identity/count metadata only through non-secret identifiers/counts or safe existence checks;
- if secret-value equality must be proven, use only a keyed HMAC whose key is independently held outside the evidence and is never persisted with the same recovery artifact;
- document key custody/recovery procedure without committing keys or values.

Forbidden:
- printing or logging secret values;
- putting secret values in GitHub Issues/PRs/artifacts/repository files;
- persisting raw or unkeyed secret-value digests/fingerprints in logs, artifacts, recovery evidence or Git history;
- treating GitHub secret names as recoverable values;
- extracting values from systems where the current authorization does not permit reading them.

If one or more required values exist only in a non-readable destination and no readable source-of-truth exists, mark only this GAP with the exact blocker and continue all others.

## GAP-RECOVERY-005 — second-owner redundancy

Known current fact: only one organization owner/account exists.

Therefore the required disposition for this invocation is:

`GAP-RECOVERY-005 = BLOCKED_EXTERNAL_PREREQUISITE`

Rules:
- do NOT create a second account;
- do NOT add/change organization owners;
- do NOT weaken the criterion to a policy sentence, token, collaborator, bot, runner or repository admin;
- do NOT repeatedly ask the owner to provide a second account during this invocation;
- record the smallest future prerequisite: a distinct, owner-approved independent recovery identity/account with actual tested owner/account-recovery capability.

This known blocker MUST NOT prevent execution, merge or closeout evidence for `001..004` and `006`.

## GAP-RECOVERY-006 — Platform production backup and RPO/RTO

Read current Platform recovery/operations authority first.

Implement/verify a real production-data recovery path without destructive production restore.

Acceptance requires:
1. actual production backup source/mechanism identified and protected;
2. independent backup generation stored appropriately, using Synology where suitable;
3. recurring schedule and retention;
4. safe isolated restore drill using production backup material but NOT restoring over production;
5. integrity/application-level validation appropriate to the restored material;
6. measured backup age at drill time and measured restore duration;
7. explicit recovery policy with RPO/RTO targets.

If authoritative RPO/RTO targets do not already exist, you are authorized for this recovery task to define initial technical operational targets only after measuring the implemented backup/restore path. The targets MUST NOT be more aggressive than demonstrated capability and MUST be clearly identified as technical recovery targets, not invented business-impact promises.

Do not restart, overwrite, restore into, or otherwise destructively mutate production to prove the drill.

## Evidence standard

Every PASS must contain direct evidence of BOTH:
- successful generation/export/backup; and
- successful isolated restore/reconstruction/recovery validation.

For each GAP record:
- exact source identity/head/generation;
- mechanism;
- independent destination class;
- timestamp;
- manifest/checksum/digest where applicable;
- restore/reconstruction drill evidence;
- residual limitations;
- exact PASS/BLOCKED status.

Never promote `UNKNOWN` or policy prose to PASS.

## Validation and security

Before finalizing:
- inspect the complete changed-file list and diff in every touched repository;
- run deterministic recovery validators and their regression tests;
- verify recurring jobs have fail-closed behavior;
- verify no secret values/private payloads entered Git history, Issue/PR bodies, Actions logs or artifacts;
- perform high-signal credential/secret leakage scans without printing matches containing values;
- verify exact protected-main and candidate heads;
- run repository-required exact-head checks;
- obtain required external review under each repository's current policy;
- inspect PR comments, reviews and unresolved threads;
- merge only by normal protected policy, no bypass;
- verify resulting main heads and branch cleanup.

## Closeout semantics

The whole invocation may return:

`STATUS: DONE_WITH_EXTERNAL_PREREQUISITE`

ONLY when:
- `GAP-RECOVERY-001 = PASS`;
- `GAP-RECOVERY-002 = PASS`;
- `GAP-RECOVERY-003 = PASS`;
- `GAP-RECOVERY-004 = PASS`;
- `GAP-RECOVERY-006 = PASS`;
- `GAP-RECOVERY-005 = BLOCKED_EXTERNAL_PREREQUISITE` for the already-known lack of a second owner account;
- all implemented work is merged and verified;
- the unresolved `005` prerequisite remains truthfully visible and is not disguised as PASS.

If an additional genuine blocker remains in `001..004` or `006`, return `STATUS: PARTIAL_BLOCKED` with exact evidence after completing every independent executable item.

Do NOT claim `OTERYN_ORG_AUDIT_V3_10 = COMPLETE`. A later META final coordinator decides the programme-level verdict using the explicit external prerequisite.

Do not close Issue #59 as fully complete unless its live lifecycle policy explicitly allows a `DONE_WITH_EXTERNAL_PREREQUISITE` terminal state without falsifying `GAP-RECOVERY-005`. It is acceptable to merge recovery implementation/evidence while leaving #59 open for the single external prerequisite.

## Final response contract

Return only:

STATUS: DONE_WITH_EXTERNAL_PREREQUISITE | PARTIAL_BLOCKED
ALIAS: OTERYN-V310-ORGANIZATION-RECOVERY-AUTHORIZED-CONTINUATION
ISSUE: Oteryn/Oteryn#59
META_PR: <#60 or successor if #60 cannot be safely reused>
META_MERGE_COMMIT: <sha or NONE>
PROVIDER_PRS: <list or NONE>
RECOVERY_GAPS:
- GAP-RECOVERY-001: PASS | BLOCKED
- GAP-RECOVERY-002: PASS | BLOCKED
- GAP-RECOVERY-003: PASS | BLOCKED
- GAP-RECOVERY-004: PASS | BLOCKED
- GAP-RECOVERY-005: BLOCKED_EXTERNAL_PREREQUISITE
- GAP-RECOVERY-006: PASS | BLOCKED
SYNOLOGY_RECOVERY: <exact sanitized evidence summary>
GITHUB_MINIMAL_PERMISSIONS: <exact scopes/permissions used, no token values>
RESTORE_DRILLS: <exact sanitized results>
RPO_RTO: <exact Platform targets + measured evidence or blocker>
CHANGED_PATHS: <exact list by repository>
VALIDATION: <exact evidence>
OUT_OF_SCOPE_FINDINGS: <list or NONE>
ADDITIONAL_BLOCKERS: <list or NONE>
SCOPE_CONFIRMATION: No work outside v3.10 organization recovery GAP-RECOVERY-001..006 was performed; GAP-RECOVERY-005 remains fail-closed because no second owner account currently exists.
