# ADR 0002 — Oteryn organization governance operating model and migration baseline

## Status

Accepted upon merge to `main` — 2026-08-19.

- Decision owner: Oteryn repository owner
- Scope: organization governance, agent/Codex operating model, lifecycle authority, GitHub enforcement model, CI/security baseline, and migration-completion criteria for Game, Platform and Atlas
- Extends: ADR 0001 for governance and operating-model scope
- Does not replace: provider-specific architecture, schemas, tests, runtime implementation or deployment authority
- Does not authorize: product-repository mutation, destructive cleanup, migration completion, branch deletion, production changes, secret access or GitHub-setting changes outside a separately authorized implementation task

## Audit basis

This decision records the durable conclusions of `OTERYN-ORG-GOVERNANCE-ARCHITECTURE-ULTRA-AUDIT-v3.9-EXECUTION-OPTIMIZED-FINAL`.

The audit was read-only and completed with:

```text
AUDIT_CONTRACT_VERSION=v3.9
AUDIT_STARTED_UTC=2026-08-18T21:08:48.378574Z
FINAL_CONTROL_PLANE_REFRESH_UTC=2026-08-18T22:08:20.233279Z
SNAPSHOT_COHERENT=YES
REPORT_VALIDATION=PASS
audit-report.md SHA-256=f9d9378623bff987f102e972ab6ae264f12d4f2f704c1b5e6c8d30eebffbb41a
```

The audit found material access gaps for some organization-admin, audit-log, packages, runner-isolation, Projects/sub-issue, external identity, restore-test and managed-Codex-policy surfaces. Those gaps remain `UNKNOWN` rather than inferred absence. Live GitHub state always outranks this historical snapshot.

## Decision

### 1. Permanent repository topology remains four product roles

The permanent product topology remains exactly:

```text
Oteryn/Oteryn          META
Oteryn/Oteryn-Game     Game
Oteryn/Oteryn-Platform Platform
Oteryn/Oteryn-Atlas    Atlas
```

Temporary/admin repositories are infrastructure, not product topology. Every temporary repository requires a purpose, owner, terminal gate and final disposition.

META remains intentionally thin. It owns ecosystem topology, cross-repository ADRs, compatibility/release composition and organization-wide governance minimums. Product schemas, tests, implementation, deployment operations and provider task databases remain with their provider repositories.

### 2. GitHub Issues are the lifecycle authority

For implementation and governance work, GitHub Issues are canonical for:

- lifecycle state;
- work type;
- owner/assignee;
- dependencies;
- acceptance criteria.

A Markdown task packet is optional durable technical detail. It must not become a second status database. A Project is an optional view/index only unless a future ADR explicitly promotes it to authority.

A PR owns the implementation/review integration state and current-head checks own validation truth. A handover is only a compact continuation cache and never outranks live Issue/PR/check state.

### 3. Agent and Codex instructions must be small and stable

Each repository should have one short root `AGENTS.md` containing only durable repository-specific authority, safety boundaries, routing, minimum preflight and minimum validation.

Nested `AGENTS.md` is used only for real path-specific rules. `AGENTS.override.md` is retained only when true replacement semantics are intentionally required. Same-directory base-plus-override prose must not be treated as sequentially cumulative when the runtime semantics do not support that model.

Repeated procedures belong in:

- Skills for reusable judgment-heavy procedures;
- deterministic scripts for machine-checkable validation, cleanup and generation;
- task packets for bounded task-specific contracts;
- normal documentation for human/reference explanation.

Transient task/branch/PR/head/CI/migration status must not live in permanent root instructions.

Repository-local `.codex/config.toml` is not required by default. User/global or managed policy owns general model, permission and network behavior. Repository-local Codex config is added only for durable shared behavior that is supported, trusted and testable.

### 4. GitHub-native protection is the enforcement boundary

The target enforcement model is `RULESETS_PRIMARY` for permanent repositories.

Each permanent repository should converge on one protected `main` ruleset and one stable externally required status context:

```text
META     meta-gate
Game     game-gate
Platform platform-gate
Atlas    atlas-gate
```

The stable gate must always emit for protected flows and fail closed when blocking internal checks fail. Volatile internal job names must not become the long-term external protection contract.

A required context or replacement ruleset must not be enabled or declared proven until a representative exact-head PR/merge-flow execution demonstrates that the current configuration emits/executes the required identity from the expected source App.

Target merge policy for permanent repositories is squash-only, with force-push and deletion blocked on protected `main`, no broad bypass, and head-branch deletion after successful merge when the branch has no continuing migration/provenance purpose.

### 5. Branch, worktree and PR lifecycle is one task → one branch → one PR

Default mapping:

```text
one independently mergeable task
-> one canonical branch
-> one PR
```

Read-only scouts, researchers and independent reviewers create zero branches by default. Disposable worktrees may isolate local parallel work but are not durable coordination state.

Branches are cleaned by evidence, not by age/name. `backup`, `tmp`, `noop`, `probe`, repeated `final*` and similar names are only candidate signals. Before deletion, ancestry, PR/Issue linkage, unique commits/content and provenance value must be checked.

### 6. CI remains provider-owned and lifecycle-classified

META must not centralize provider implementation tests. Each provider owns its local build/test workflows and stable gate.

Workflow primary lifecycle is exactly one of:

```text
PR_GATE
DEEP_VALIDATION
SCHEDULED_MAINTENANCE
RELEASE
DEPLOYMENT
MANUAL_OPERATION
SECURITY
MIGRATION_ONE_SHOT
HISTORICAL_OBSOLETE
```

Platform's large workflow surface must be reduced by lifecycle classification and proven purpose, not copied into META. Migration-only CI is removed only after the relevant migration/transfer acceptance gates are satisfied.

### 7. Security baseline is common; threat-model extensions stay local

Every public permanent repository should converge on the smallest applicable baseline:

- `SECURITY.md`;
- private vulnerability reporting;
- secret scanning and push protection;
- Dependabot alerts/security updates and GitHub Actions dependency updates;
- CODEOWNERS for critical governance/workflow/security/contract paths;
- CodeQL/code scanning where the repository contains supported code;
- least-privilege `GITHUB_TOKEN` permissions and full-SHA action pinning.

Platform-specific environments, deployment protection, self-hosted runners and production trust boundaries remain Platform-owned and require explicit blast-radius decisions.

Read access never implies permission to transmit private/repository data externally. Connector, MCP, plugin and GitHub App scopes must remain least-privilege and separately govern read, execute, write and external-send capabilities.

### 8. Governance as code stays small and read-only by default

META should maintain only the minimum desired-state topology/governance contract needed to catch real drift, plus a read-only validator.

The validator should focus on high-signal drift such as:

- wrong repository authority/coordinate;
- missing protection or stable gate;
- merge-policy mismatch;
- unexpectedly broad Actions permissions;
- missing security baseline;
- temporary repository without terminal lifecycle;
- stale migrated-source coordinates;
- stale task/head/branch mappings;
- Codex instruction-chain mismatch.

A GitHub settings writer is not part of the baseline. Any future writer requires separate explicit authorization, least privilege, deterministic diff and dry-run.

### 9. `.github` and `.github-private` are not needed now

Current decision:

```text
.github         DEFER_UNTIL_TRIGGER
.github-private DO_NOT_CREATE
```

Create `.github` only when at least two repositories demonstrably need the same public community-health defaults or curated workflow templates and the administrative repository reduces real duplication. It must remain administrative infrastructure, not a fifth product role or Codex instruction-inheritance mechanism.

Create `.github-private` only under a future explicit ADR if there is a real member-only organization-profile requirement; no such requirement is part of this baseline.

## Migration completion baseline

As of the validated v3.9 audit snapshot, all three migrated product lines remain incomplete:

```text
Game     MIGRATION_COMPLETE=NO
Platform MIGRATION_COMPLETE=NO
Atlas    MIGRATION_COMPLETE=NO
```

### Game

Continuity is proven: `blakinio/Oteryn-v2@16afdf31a15bd49d454cdbcdd98fa7ec72213ef9` is an ancestor of `Oteryn/Oteryn-Game@63a6cb8cb3e69b7c2f792475f24093e90bd7fd81`, with the audited target relation `+14/-0`.

The migration is still incomplete because the historical source remained ordinary-write capable/unarchived with open work and source-only branch residue, and copied migration refs in the target had not all been dispositioned. The terminal gate is explicit source retirement plus reconciliation of source-only work/refs and stale mutable coordinates.

### Platform

Stable repository identity is preserved at repository ID `1305155726`; the current coordinate is `Oteryn/Oteryn-Platform` and the historical coordinate was `blakinio/Oteryn-Platform`.

The transfer itself does not equal migration acceptance. Acceptance remains blocked until required runner, package/GHCR, environment/deployment, GitHub App/webhook/deploy-key and external owner/repo-sensitive identity surfaces are either proven preserved/rebound, intentionally retired or explicitly classified not applicable; stale mutable coordinates are removed; migration-only machinery is dispositioned; and the temporary backup reaches its terminal lifecycle.

The temporary repository `Oteryn/Oteryn-Platform-Migration-Backup-20260818` (repository ID `1338405017`) is `TEMPORARY_MIGRATION`, not a product role.

### Atlas

The historical source boundary is the bounded Atlas-owned material within `blakinio/Otheryn`, not the whole legacy repository.

The migration remains incomplete until selective extraction has a complete source-SHA/path/blob → target-path/blob/provenance mapping, remaining Atlas source work/branches are dispositioned, target `main` protection and stable-gate proof are established, and asset publication/provenance/rights decisions—including exact 15.32 publication constraints where applicable—are resolved.

## Migration completion invariant

No manifest entry may claim `MIGRATION_COMPLETE=YES` merely because the target repository exists or a repository was transferred.

`YES` requires all applicable proof:

- sole current product authority;
- mode-appropriate Git/transfer/content continuity;
- no undispositioned source-only active product work;
- no P0/P1 stale mutable coordinates;
- target merge requirement configured and proven on a representative exact head;
- GitHub control plane reconciled;
- identity-sensitive integrations reconciled or intentionally retired;
- packages/releases/runners/environments/deployments reconciled where applicable;
- explicit source/transfer retirement state;
- temporary migration infrastructure dispositioned;
- rollback/reference provenance preserved.

A proven blocking defect yields `MIGRATION_COMPLETE=NO`. Missing required evidence yields `MIGRATION_COMPLETE=UNKNOWN`, never a guessed `YES` or `NO`.

## Ordered implementation priorities

### P0

1. Prove stable `meta-gate` and `atlas-gate` execution on representative exact PR heads, then protect META and Atlas `main` with repository rulesets.
2. Stop ordinary product work in historical Game and Atlas sources; reconcile source-only work and copied refs before cleanup.
3. Finish Platform post-transfer validation for runners, packages and owner/repo-sensitive integrations; remove stale executable/governance coordinates.
4. Give the Platform migration backup an explicit owner, retention/terminal gate and final disposition.
5. Close the Atlas extraction/provenance map and publication-rights decision before declaring extraction complete.

### P1

1. Migrate lifecycle authority toward Issues and remove duplicated mutable Markdown status.
2. Shorten root instruction chains and remove same-directory overrides unless true replacement is intended.
3. Add/repair CODEOWNERS and the common public-repository security baseline.
4. Consolidate Platform workflows by lifecycle while retaining provider-specific validation.
5. Record tested backup/restore and minimal break-glass contracts.
6. Add the small read-only governance drift checker.

## Consequences

Positive consequences:

- one durable authority model for humans and autonomous agents;
- less always-loaded instruction context and less stale mutable prose;
- GitHub-native enforcement rather than documentation-only policy;
- provider-owned CI/tests and thinner META;
- explicit migration completion and retirement gates;
- branch/worktree cleanup based on evidence rather than naming heuristics.

Costs and constraints:

- several existing task/instruction/workflow structures need migration rather than wholesale preservation;
- exact-head gate proof is required before tightening protection;
- some organization-level/admin and external identity conclusions remain `UNKNOWN` until the required visibility exists;
- historical migration sources and temporary repositories cannot be deleted until their unique content/provenance and rollback obligations are resolved.

## Authority and precedence

After merge, this ADR is canonical for the cross-repository governance operating model and migration-completion criteria. ADR 0001 remains canonical for ecosystem topology and provider ownership boundaries.

Provider repositories remain authoritative for provider implementation and local architecture. GitHub live settings/checks are authoritative for live enforcement. GitHub Issues/PRs/checks are authoritative for current lifecycle/implementation/validation state. Historical audit facts are snapshots and must not be used as current live-state substitutes.
