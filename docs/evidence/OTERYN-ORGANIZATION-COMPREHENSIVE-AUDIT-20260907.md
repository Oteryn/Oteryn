# Oteryn organization comprehensive audit — 2026-09-07

Status: `COMPLETE_WITHIN_ACCESSIBLE_SCOPE`

Scope: organization-wide audit of active Oteryn repositories, current architecture, runtime boundaries, CI/test/build systems, deployment/recovery surfaces, security and supply-chain controls, governance/instruction architecture, documentation and known operational gaps.

This document is evidence and remediation guidance. It does not silently transfer implementation authority from provider repositories to META and does not claim production qualification where execution evidence is unavailable.

## 1. Executive verdict

Oteryn does **not** need another architectural reset or another governance framework. The current repository split is coherent enough to continue:

- `Oteryn/Oteryn` — META / organization governance / topology / shared contracts.
- `Oteryn/Oteryn-Game` — canonical game runtime and gameplay authority.
- `Oteryn/Oteryn-Platform` — web/platform/identity/control-plane authority.
- `Oteryn/Oteryn-Atlas` — Atlas/derived-data/public-safe artifact authority.
- `Oteryn/Oteryn-Platform-Migration-Backup-20260818` — archived migration/recovery provenance, not an active product repository.

The highest current organization risk is concentrated in **Platform verification integrity**, followed by **Game session-authority completion**. Atlas remediation F01–F16 is complete, but full verification restoration is intentionally paused by owner policy. META's primary remaining work is simplification, measurement and stale-authority cleanup rather than redesign.

### Current severity summary

- Confirmed P0: **0**.
- Confirmed current P1: **4**.
- Historical P1 findings already fixed are not carried forward.
- Production readiness is **not claimed** for the organization as a whole.

Current P1 register:

1. Platform CI change classifier can false-negative material runtime changes for rename/type-change combinations.
2. Platform required `platform-gate` does not provide complete exact-candidate fan-in for every relevant profile.
3. Platform identity email-change notifications lack a durable transactionally coordinated outbox/delivery model.
4. Game complete persisted/reloaded retired-session nonreuse authority is not yet terminally closed in the active remediation line.

## 2. Audit coordinates

The audit was rebound to the protected `main` generation of each active repository at closeout.

| Repository | Audited `main` | Audited tree | Coverage state |
| --- | --- | --- | --- |
| `Oteryn/Oteryn` | `1a01c5b3e08666a82245b1cac78da3736c65e785` | `f084e824ec5e14d5909c9750d906d91d51425fd5` | `COVERED` |
| `Oteryn/Oteryn-Game` | `3327db49c0c3e2d90afe6a74954c579a36aba2a5` | `fc0f18e4b67a2df16c4fb24ebf8933cf4c1714bf` | `COVERED` |
| `Oteryn/Oteryn-Platform` | `de917b3477a1de0667531380de3660e8b2ab59aa` | `ffdf2a286d3a39f2344cf2ff53b28e4ef7369a8e` | `COVERED_WITH_NUMERIC_LEDGER_LIMITATION` |
| `Oteryn/Oteryn-Atlas` | `f00815858bb5b031c502ad19fb96a05ff66b4d84` | `a1009378f8d3950a5ee62fb3ee65041f7d53a1e0` | `COVERED` |

The META source branch for publication of this report was admitted from `Oteryn/Oteryn@1a01c5b3e08666a82245b1cac78da3736c65e785`.

## 3. Method and truthfulness rules

Every repository surface was treated using one of these dispositions:

- `DIRECT` — content or material semantics directly inspected.
- `GROUPED` — deterministic family of repetitive/generated/data artifacts assessed through producer, contract and representative consumer evidence.
- `N/A` — no meaningful semantic review requirement for the artifact.
- `UNVERIFIED` — a real access/execution limitation remains.

`GROUPED` is not used to hide ordinary authored runtime code.

The audit also uses generation reconciliation: a prior direct finding remains valid when the corresponding Git blob is unchanged; every materially changed surface is re-evaluated against the new `main` generation.

Audit coverage, product qualification and production readiness are intentionally separate concepts:

- `AUDITED` means the area was evaluated.
- `PASS` means the evaluated property passed its acceptance criterion.
- `NOT_QUALIFIED` means required execution/evidence is still missing.
- `UNKNOWN` means the current access plane cannot truthfully establish the state.

## 4. Organization architecture

### 4.1 What is working

The provider/META split is structurally sound:

- META coordinates ecosystem topology, compatibility and cross-repository contracts.
- Game owns gameplay/runtime semantics.
- Platform owns web, identity, control-plane and platform operations.
- Atlas consumes and publishes derived/public-safe data rather than becoming a second gameplay source of truth.

This should be preserved.

### 4.2 What should not be done

Do not:

- create another central framework that duplicates provider authority;
- copy provider schemas into META merely to make agents convenient;
- add another approval lifecycle in parallel with repository-native Merge Queue and required gates;
- restore retired prompt/governance mechanisms merely because they exist in historical evidence;
- treat old audit findings as current without revalidation.

## 5. META audit

### 5.1 State

META has a complete repository audit lineage and a thin v3 instruction architecture. Earlier full repository coverage accounted for the complete tracked set of that audited generation, and the later deltas were reconciled against subsequent protected-main updates.

The current root `AGENTS.md` correctly identifies META as the coordination repository and keeps provider runtime write authority out of scope unless explicitly authorized.

### 5.2 Instruction/governance architecture

The strongest current design principle is `one rule, one authority`:

- shared organization semantics live centrally;
- providers retain only thin local bootstraps and provider-specific differences;
- task-specific procedures/prompts are loaded only when relevant;
- retired prompt/superpowers material is evidence, not active dispatch authority.

This is preferable to large recursive instruction trees.

### 5.3 Remaining META risks

1. **Stale operative-looking material** remains a semantic risk. Old open PRs/documents can look like current authority even after the organization moved to a newer model. A notable example is META PR #89, which still represents the older `ai-review-gate` / deep-review fingerprint model and should not be mistaken for current v3 policy.
2. R5 instruction-efficiency evidence does **not** yet measure actual API billing tokens or wall-clock execution. The current evidence can demonstrate fewer instruction hops/files, but not prove cost savings.
3. Current organization/admin security settings are not fully visible through the available GitHub integration, so historical configuration must not be treated as current proof.

### 5.4 Recommendation

Keep the architecture. Finish stale-authority classification and add actual token/time/cost telemetry before claiming quantified agent-efficiency gains.

## 6. Game audit

### 6.1 Important closed findings

Several serious findings from the earlier Game audit have been fixed and must not be reported as current defects:

- client lifecycle error handling and PKCE bounds;
- AI `CandidateId` uniqueness independent of priority/order;
- Ability zero/negative magnitude validation;
- required PR/MQ gate credibility and fail-closed native-command execution;
- WP1/F01+F02 terminal verification.

The WP1 closure included exact Merge Queue verification with positive and injected-negative lifecycle tests, native command failure positions, workflow mutations and fan-in negative tests.

### 6.2 Current P1

The active line around PR #361 remains the material Game blocker.

The current representation does not yet prove complete persisted/reloaded retired-session nonreuse authority across more than one replacement. In the canonical example `S0 -> S1 -> S2`, rejecting a later reuse of retired `S1` requires durable authority beyond only the initial/current session pair.

The target is not simply an in-memory guard. WP4 must provide persisted and reloaded complete nonreuse authority, then qualify it through reconnect/restart without duplicate effects or authority rollback.

### 6.3 Programme state

The existing Game remediation programme should be completed rather than replaced by a new programme:

- WP1 — complete.
- WP2 — active session/reconnect authority work.
- WP3 — precise runtime-backend blocker work.
- WP4 — durable authority chain required.
- WP5 / G0 / G1 — final real-producer and native effect qualification.

### 6.4 Target completion proof

The final Game G1 should prove a real command through the logical owner to durable effect and visible projection, surviving reconnect/restart with:

- no duplicate effect;
- no stale-session reuse;
- no authority rollback;
- exact-candidate CI evidence.

## 7. Platform audit

Platform is the highest current organization remediation priority.

The previous audit PR #1294 was explicitly incomplete. This closeout extends the semantic inventory across the main authored/runtime/control-plane families and separates coverage from qualification.

### 7.1 Build/test roots

The main toolchains are:

1. Composer/Laravel application and tests.
2. Playwright acceptance suite under `scripts/acceptance`.
3. Go Game Gateway under `services/game-gateway`.
4. Docker/Synology build and deployment tooling.

No separate fifth application/build system was identified.

`composer verify` already composes key static/test/repository-contract checks. The main defect is therefore not a total absence of test entrypoints; it is whether the required gate selects and aggregates the right entrypoints for the exact candidate.

### 7.2 P1 — change classifier false negatives

Current `scripts/ci/classify_changes.py` uses a name-only diff path view equivalent to:

`git diff --name-only --diff-filter=ACMRD <base> <head>`

and then classifies the resulting path strings.

Real temporary-Git reproductions from the audit demonstrated false acceptance for at least:

- regular runtime file -> symlink at a runtime path plus docs-only edit;
- runtime file moved into docs plus docs-only edit.

The rename case exposes only the destination path when the classifier consumes the name-only view. The required test gate can therefore report runtime tests as not applicable when the semantic change is material.

#### Required fix

Use a status-aware diff representation such as `git diff --raw -z` or `--name-status -z`, preserve both source and destination for renames, detect type/mode/symlink transitions, and fail closed on unknown/unrecognized statuses.

Regression tests must use real temporary repositories and include:

- add/modify/delete;
- rename both directions across impact boundaries;
- copy where relevant;
- regular <-> symlink/type changes;
- mode changes where they can affect execution;
- unknown status fail-closed behavior.

### 7.3 P1 — incomplete exact-candidate fan-in

Protected Platform `main` requires `platform-gate`.

The central workflow handles PR/push/merge-group, but separate relevant workflows do not all bind to the same exact merge candidate:

- Game Gateway CI lacks `merge_group` coverage.
- Game Auth Ticket Concurrency lacks `merge_group` coverage.

Therefore green `platform-gate` is not currently a universal proof that every change-class-relevant profile ran successfully on the exact candidate that Merge Queue is integrating.

#### Required target

Create one manifest of impact class -> required qualification profile, use the same classification semantics for PR and `merge_group`, and terminate in one stable fan-in gate where:

- required success passes;
- failure blocks;
- cancelled blocks;
- missing blocks;
- unjustified skipped blocks;
- only explicitly justified N/A may pass.

Do not solve this by running every expensive workflow for every change.

### 7.4 P1 — durable identity email-change delivery

The current email-change request path persists the security operation inside the DB transaction, then sends verification and old-address notification as separate actions outside the transaction.

A mail transport failure can therefore produce durable security state with partial notification delivery.

#### Required target

Implement a transactional outbox or equivalent durable delivery model with:

- one durable message record per required notification;
- stable idempotency key;
- delivery state;
- bounded retry/backoff;
- terminal/dead-letter state;
- restart safety;
- explicit expiry/revocation behavior.

Tests should cover first-message failure, second-message failure, crash/restart after commit but before send, retry, expiry and revocation.

### 7.5 Current P2 families

The following remain material follow-up items unless independently closed on a later main:

- Game Gateway body/read deadline completeness.
- Platform image/build reproducibility and provenance debt.
- Coverage remains report-only without an enforcement threshold.
- Local README setup creates SQLite without an explicit migration step.
- Gateway graceful shutdown lacks a complete joined terminal synchronization proof.
- Synology path admission has coverage gaps such as root `lang/**` in relevant image-build routing.
- Docker build context remains broader than necessary.
- Recovery-password input should have an explicit reasonable upper bound.
- Current rollback code improvements do not by themselves prove current-release production rollback qualification.

### 7.6 Platform workflow/control-plane complexity

The repository has approximately 55 registered workflow YAML files in the verified current architecture, covering acceptance, Cloudflare, auth, Gateway, Synology, CodeQL, outage, Playwright, portal and other lifecycle surfaces.

The recommendation is **not** to delete checks merely to reduce YAML count. The correct optimization pattern is:

- central impact classification;
- dependency-aware routing;
- reusable qualification profiles;
- exact-candidate fan-in;
- artifact/cache reuse;
- decoupling non-gating post-merge latency;
- metrics for queue time, CPU time and failure yield.

A good recent example is Platform PR #1323, which removed long Synology deploy waiting from the main image-build job and made staging dispatch asynchronous without deleting the build evidence.

## 8. Atlas audit

### 8.1 Repository audit coverage

The earlier full Atlas audit had an exact leaf denominator of 1140 paths:

- `DIRECT`: 131;
- `GROUPED`: 550;
- `NOT_APPLICABLE`: 459;
- `PARTIAL`: 0;
- `UNVERIFIED`: 0;
- `INACCESSIBLE`: 0.

### 8.2 Remediation state

Issue #315 records F01–F16 as complete on protected main, including:

- Python/JS canonical serialization parity;
- publication/output-root safety;
- precise obsolete-verification deletion authority;
- persistent cache degradation handling;
- bounded response reads;
- coordinate bounds;
- range cache accounting/in-flight semantics;
- URL confinement;
- E2E documentation;
- npm/Playwright update coverage;
- parser negative-floor behavior;
- CDP RPC deadlines;
- gameplay capability split;
- live ops/recovery docs;
- root README;
- lifecycle/current-state cleanup.

### 8.3 Current intentional stop

Atlas is `PAUSED_BEFORE_VERIFICATION_RESTORATION`.

The retired verification/E2E/publication/deployment stack remains suspended until explicit owner resume. This is a qualification state, not an unresolved F01–F16 audit defect.

Do not autonomously restore the old blocking verification stack merely because the code findings are closed.

## 9. CI, tests, builds and organization cost

### 9.1 Current structural problem

Across the organization, the main cost risk is not simply “too many tests”; it is inefficient selection and duplicated evidence.

A modern target is:

- stable small required aggregate per repository;
- fail-closed impact routing;
- exact-candidate Merge Queue qualification;
- heavy runners only for tests that truly need them;
- cheap deterministic checks first;
- reusable artifacts and dependency caches;
- separate post-merge/deploy observation from blocking source qualification;
- no workflow polling loops that hold runners for external latency.

### 9.2 Metrics required before claiming optimization

Collect per workflow/profile:

- invocation count;
- p50/p95 queue time;
- p50/p95 execution time;
- billable runner minutes or equivalent capacity;
- cache hit rate;
- artifact reuse rate;
- failure yield;
- flaky retry count;
- percent skipped by impact routing;
- false-negative/false-positive routing regression count;
- merge-group failure rate vs PR-source failure rate.

Without those metrics, “faster/cheaper” remains an inference rather than measured evidence.

## 10. Agent instructions, prompting and token efficiency

### 10.1 Current positive direction

The v3 instruction design is substantially healthier than the older large prompt/gate model:

- thin provider `AGENTS.md` files;
- central organization authority;
- provider-local implementation ownership;
- selective procedure loading;
- skills as aids rather than separate authority;
- historical prompts clearly non-authoritative where properly classified.

### 10.2 Remaining risks

1. Stale open PRs or historical docs can still look dispatchable.
2. Repeated semantics across policy/prompts can recreate instruction debt.
3. Agent cost claims lack real billing/token/wall-clock measurement.
4. Overly broad audit/implementation prompts can cause agents to load irrelevant context and over-verify unchanged surfaces.

### 10.3 Target model

For each task:

- load root/provider bootstrap;
- resolve exact task/Issue/PR authority;
- load only procedures relevant to the operation;
- reuse prior evidence when blob identity/semantics remain valid;
- revalidate only changed/invalidated evidence;
- use the smallest useful parallelism;
- store durable machine-readable state for long programmes.

## 11. Branch protection, review and integration

### 11.1 Current verified state

- META protected `main` requires `meta-gate`.
- Platform protected `main` requires `platform-gate`.
- Game ruleset requires `game-gate`, pull request, linear history and Merge Queue.
- Atlas uses protected merge-authority rules and Merge Queue.

The full legacy/admin protection endpoint is not available for every repository through the integration, so unseen settings must not be invented.

### 11.2 Review policy observation

Game and Atlas ruleset evidence shows `required_approving_review_count: 0` in the formal ruleset representation.

A blanket mandatory human approval for every change is not automatically the best optimization. Independent exact-head review is most valuable for high-risk surfaces such as:

- auth/session authority;
- persistence/migrations;
- payments;
- security/privacy boundaries;
- branch/ruleset/verification authority;
- deploy/rollback;
- cross-repository contracts.

The organization should avoid adding a second bespoke approval lifecycle that duplicates GitHub protections.

## 12. Supply chain and dependency management

Verified Dependabot families include:

- META: GitHub Actions and Python tooling under governance paths.
- Game: GitHub Actions and Cargo.
- Platform: Composer, acceptance npm and GitHub Actions.
- Atlas: GitHub Actions and npm/E2E.

No statement is made that the current organization is free of CVEs. A fresh complete SBOM/advisory/secret-history scan was not part of this audit and remains `UNKNOWN`.

Recommended policy:

- automated patch/minor updates where relevant gates prove compatibility;
- manual review for major updates;
- generated SBOMs at release boundaries;
- provenance/attestation for release artifacts where practical;
- periodic advisory scans recorded as durable evidence.

## 13. Recovery, backup and disaster recovery

The archived Platform migration-backup repository contains durable recovery evidence for the migration cut.

Its documented restore drill verified:

- release bundle integrity;
- mirror clone;
- `git fsck`;
- bundle verification;
- all expected refs;
- exact restored main.

This is good provenance and proves the transfer artifact can be restored.

It does **not** prove current-release operational disaster recovery for today's Platform/Game/Atlas state.

Current organization DR still needs a recurring qualification that records:

- current release coordinate;
- data snapshot coordinate;
- isolated restore;
- application startup;
- schema/migration state;
- critical read/write smoke;
- rollback/redeploy;
- measured RPO/RTO;
- cleanup and evidence retention.

## 14. Coverage closeout

### 14.1 Final status

`POINT_14_AUDIT_COVERAGE = COMPLETE_WITHIN_ACCESSIBLE_SCOPE`

All audit domains A–W are accounted for. No domain is silently omitted.

| Domain | State |
| --- | --- |
| A. Purpose/product | `AUDITED` |
| B. Architecture | `AUDITED` |
| C. Implementation | `AUDITED` |
| D. Interfaces/contracts | `AUDITED` |
| E. Data/persistence | `AUDITED` |
| F. Dependencies/supply chain | `AUDITED` |
| G. Security/privacy | `AUDITED` |
| H. Reliability/failure handling | `AUDITED` |
| I. Performance/cost | `AUDITED`, measurements partly `UNKNOWN` |
| J. Tests | `AUDITED` |
| K. Build | `AUDITED` |
| L. CI/verification | `AUDITED` |
| M. Release/deploy | `AUDITED`, current live proof partly `UNKNOWN` |
| N. Config/infrastructure | `AUDITED` in accessible configuration; admin-only state `UNKNOWN` |
| O. Operations/observability | `AUDITED`, live telemetry `UNKNOWN` |
| P. Documentation | `AUDITED` |
| Q. Instructions/skills/prompts | `AUDITED` |
| R. Developer/agent ergonomics | `AUDITED` |
| S. Repository governance | `AUDITED` within accessible GitHub state |
| T. Current work/drift | `AUDITED` |
| U. Portability | `AUDITED`, full latest matrix not executed |
| V. Product/UI | `AUDITED` |
| W. Simplification/technical debt | `AUDITED` |

### 14.2 Provider coverage state

#### META

Complete within accessible scope. Earlier exact tracked-path audit plus delta reconciliation covers the current repository generation. Runtime qualification is N/A for META coordination scope.

#### Game

Audit coverage is complete enough to identify the current material blocker. G1 product qualification remains not terminal.

#### Platform

The main authored/runtime/control-plane families are accounted for, including application code, tests, scripts, tools, resources, workflows, migrations, architecture/contracts, agent prompts, Laravel/Composer, Playwright, Go Gateway and Docker/Synology.

One formal evidence limitation remains: the available GitHub recursive tree is complete and immutable (`ffdf2a286d3a39f2344cf2ff53b28e4ef7369a8e`), but the current connector did not expose a convenient aggregate leaf-path count, and no authorized local execution plane was available to export the tree into a one-record-per-leaf machine ledger. Therefore this report does **not** invent `TOTAL_CURRENT_PLATFORM_LEAF_PATHS`.

This is a numeric-ledger/export limitation, not an unknown code family.

#### Atlas

Exact 1140-path audit baseline exists, F01–F16 remediation is complete, and current remaining limitation is intentionally paused verification restoration rather than repository coverage.

### 14.3 Explicit non-repository unknowns

The following are deliberately not converted into `PASS`:

- current private-production runtime state;
- current live production telemetry;
- latest complete deploy/restore/rollback proof;
- current full Game G1;
- Atlas restored verification qualification;
- organization Security Center/admin-only settings not exposed by the integration;
- secret values;
- current full CVE/SBOM/secret-history scan;
- GitHub Actions billing/minute totals;
- actual agent API token/billing cost and wall time;
- full current local build/test/migration execution on all repositories.

### 14.4 Coverage verdict

```text
POINT_14_AUDIT_COVERAGE = COMPLETE_WITHIN_ACCESSIBLE_SCOPE
REPOSITORY_FAMILY_COVERAGE = COMPLETE
AUDIT_DOMAINS_A_W = COMPLETE
CURRENT_FINDING_REVALIDATION = COMPLETE
HISTORICAL_FINDING_RECONCILIATION = COMPLETE

P0_CONFIRMED = 0
P1_CURRENT_CONFIRMED = 4

SILENTLY_OMITTED_DOMAINS = 0
UNCLASSIFIED_REPOSITORY_FAMILIES = 0
HIDDEN_PARTIALS = 0

PLATFORM_EXACT_NUMERIC_LEAF_LEDGER = NOT_EMITTED_DUE_CURRENT_TOOLING_LIMITATION
PRODUCTION_READINESS = NOT_CLAIMED
```

## 15. Licensing and repository policy hygiene

Current root-file inventory shows:

- Game: explicit `LICENSE`, `LICENSE-ASSETS.md`, `TRADEMARKS.md`.
- Platform: `LICENSE.md`, `THIRD_PARTY_NOTICES.md`.
- META: no explicit root license was observed in the audited inventory.
- Atlas: no explicit root license was observed in the audited inventory.

Absence of a root license is not automatically a security defect and does not by itself establish illegal use. It is a policy/compliance ambiguity.

Recommendation: explicitly state intended legal terms for META and Atlas, whether open source, source-available or all-rights-reserved, and keep third-party asset/data terms distinct from code licensing.

## 16. Prioritized remediation plan

### Priority 1 — Platform verification integrity

Fix classifier semantics and exact-candidate fan-in together as one verification-integrity programme.

Acceptance:

- rename/type/symlink regression suite passes on real Git fixtures;
- classification is fail-closed;
- every change class maps to explicit profiles;
- PR and merge-group use equivalent impact semantics;
- one stable `platform-gate` represents the exact candidate;
- no missing/cancelled/unjustified skipped required profile can produce green.

### Priority 2 — Platform identity email outbox

Implement durable transactionally coordinated delivery with idempotency, retries, terminal state and restart-safe tests.

### Priority 3 — Game WP2/WP4 authority closure

Finish durable retired-session nonreuse authority in the existing #361 programme line and prove reconnect/restart behavior.

### Priority 4 — Finish Platform audit artifact lineage

Update/close the existing Platform audit line with current-main generation reconciliation and, when a checkout/export plane is available, emit the exact per-leaf ledger rather than starting another independent audit.

### Priority 5 — Atlas verification restoration

Only after explicit owner resume:

1. restore shadow verification;
2. measure stability/cost;
3. canary selected blocking checks;
4. restore Merge Queue qualification incrementally;
5. restore publication/deployment only with explicit recovery evidence.

Do not restore the old stack wholesale.

### Priority 6 — Current-release DR qualification

Run recurring isolated restore drills against the current product release/data generation and record real RPO/RTO.

### Priority 7 — CI cost/latency optimization

Instrument workflow/profile cost and remove duplicated/idle waiting while preserving verification authority.

### Priority 8 — Governance cleanup

Close, supersede or clearly label old operative-looking PRs/docs and maintain a single current authority path.

### Priority 9 — Agent/token measurement

Extend R5Q with real wall-clock and token/billing telemetry before making quantitative savings claims.

### Priority 10 — Supply chain/compliance

Add repeatable SBOM/advisory/provenance evidence and make META/Atlas legal terms explicit.

## 17. Target organization state

The desired steady state is:

- one thin organization policy;
- thin provider bootstraps;
- one stable required aggregate per provider repo;
- fail-closed impact routing;
- exact Merge Queue candidate qualification;
- high-risk independent review where useful, not blanket duplicate approvals;
- heavy E2E only for tests whose oracle requires heavy/real-world data;
- reusable build/test artifacts;
- measured CI and agent cost;
- no historical instruction material masquerading as current authority;
- current restore/rollback proof for releases;
- machine-readable long-running programme state;
- explicit legal/supply-chain posture.

## 18. Final organization verdict

The organization architecture is sound enough to continue without a reset.

The shortest credible path to a modern, fast and cost-balanced Oteryn is:

`Platform P1 verification integrity -> Platform identity durability -> Game authority closure -> complete current Platform evidence -> Atlas restoration after owner resume -> current DR/production qualification -> measured CI/token optimization -> supply-chain/compliance hardening`

Do not launch another cross-organization redesign before these finite, already identified gaps are closed.

## 19. Existing evidence and live programme references

Important evidence/authority already present in the organization includes:

- `Oteryn/Oteryn` PR #153 — META current-main repository audit lineage.
- `Oteryn/Oteryn` `docs/evidence/OTERYN-INSTRUCTION-DEBT-AUDIT-20260906.md`.
- `Oteryn/Oteryn` `docs/evidence/OTERYN-AGENT-INSTRUCTION-OPTIMIZATION-RESEARCH-20260907.md`.
- `Oteryn/Oteryn` `docs/evidence/OTERYN-R5Q-RESULTS.md`.
- `Oteryn/Oteryn-Game` audit/remediation programme Issue #364 and audit PR #360.
- `Oteryn/Oteryn-Game` PR #361 — active session-authority line.
- `Oteryn/Oteryn-Platform` audit PR #1294.
- `Oteryn/Oteryn-Platform` programme Issue #451.
- `Oteryn/Oteryn-Atlas` Issue #315 — F01–F16 and verification-restoration state.
- `Oteryn/Oteryn-Platform-Migration-Backup-20260818/RECOVERY_EVIDENCE.md`.

Live provider repository state outranks this snapshot if it moves after the coordinates recorded in section 2. Future remediation work should refresh protected-main SHA, active Issue/PR ownership and exact candidate state before mutation.
