# OTERYN-ORG-AUDIT-v3.10 — final terminal audit report

Audit contract: `OTERYN-ORG-AUDIT-v3.10`
Base contract: `OTERYN-ORG-GOVERNANCE-ARCHITECTURE-ULTRA-AUDIT-v3.9-EXECUTION-OPTIMIZED-FINAL`
Report date: 2026-08-22
Lifecycle authority: GitHub Issues and protected pull requests
Evidence policy: fail closed; `UNKNOWN` is retained where the connected surfaces cannot prove a fact

This report is the full v3.10 execution artifact. The accompanying Documentation & Agent IA addendum is preserved byte-for-byte from its validated successor branch; this report does not rewrite the historical v3.9 result. Its own byte-bound validation record is `OTERYN-v3.10-FINAL-TERMINAL-REPORT-VALIDATION.json`, verified by `tools/governance/validate_v310_audit_docs.py`; the addendum validation is not evidence for this report.

## 1. Executive verdict

**Current terminal verdict: `INCOMPLETE`.**

The organization has a coherent four-repository authority model, protected META governance, a merged organization recovery contract, a merged desired-state/drift audit, an immutable organization-runner image, a proven Atlas replacement route, and implemented Platform/Game runner routes. The audit cannot truthfully return `COMPLETE` while the following acceptance facts remain unproved or blocked:

1. organization runner-group `Selected repositories` ACLs cannot be read back through the connected GitHub surface;
2. the Platform replacement workload is merged, but the trusted-main push-run result is not readable through the available run-list surfaces in this session;
3. the Game replacement candidate is hosted-CI green but cannot be merged without an independent review; Game policy separately prohibits owner-funded metered AI/Codex without explicit authorization;
4. Game and Platform migration verdicts remain `UNKNOWN`, and Atlas migration remains `NO`, because their mode-specific terminal evidence is not complete;
5. legacy runner retirement is intentionally blocked until the replacement/ACL gates above close;
6. organization-wide recurring current-state backup/control-plane/package/secret/owner-redundancy recovery remains unproved.

These are evidence gaps, not inferred failures. No blocker is converted to PASS merely to close the programme.

## 2. Verified live organization and migrated-source estate state

| Object | Verified state | Evidence / boundary |
| --- | --- | --- |
| `Oteryn/Oteryn` | permanent META repository | repository ID `1338152366`; protected `main`; required `meta-gate` + `ai-review-gate` |
| `Oteryn/Oteryn-Game` | permanent Game authority | repository ID `1338291140`; current source authority for Game |
| `Oteryn/Oteryn-Platform` | permanent Platform authority | stable repository ID `1305155726`; transferred identity; protected `main` |
| `Oteryn/Oteryn-Atlas` | permanent Atlas authority | repository ID `1337995824`; protected `main`; `atlas-gate` + `provenance-gate` |
| `Oteryn/Oteryn-Platform-Migration-Backup-20260818` | administrative historical evidence | repository ID `1338405017`; live `archived=true`; terminal disposition `ARCHIVED_READ_ONLY` |
| `blakinio/Oteryn-v2` | legacy Game migration source | live archived read-only; not normative target authority |
| `blakinio/Otheryn` | mixed-content legacy parent | remains live; bounded Atlas extraction material is non-authoritative; unrelated content is not retired by Atlas migration |
| META desired-state/drift successor | PR #37 squash-merged as `c0dbad93f791953d5efcc6b556e6be73693f0a4f` after exact-head `meta-gate` and `ai-review-gate` success; predecessors #23 and #9 closed as superseded | live GitHub revalidation on 2026-08-22 |

Current provider heads and mutable check state must always be refreshed before a terminal decision; SHAs recorded in evidence are checkpoints, not permanent authority.

## 3. Current authority graph

```text
Oteryn/Oteryn (META)
  owns: topology, ecosystem governance, cross-repo minimums,
        compatibility/release composition, audit/recovery authority
  does not own: provider runtime implementation

Oteryn/Oteryn-Game
  owns: Game source, Game provider contracts/tests/runtime integration

Oteryn/Oteryn-Platform
  owns: Platform source, deployment/runtime operations, Platform runner image/bootstrap

Oteryn/Oteryn-Atlas
  owns: Atlas source, publication, FullWorld products, Atlas local preview/E2E

GitHub Issues
  own: mutable task/programme lifecycle

Protected PRs + required checks
  own: exact-head integration/review truth

Historical repositories/evidence
  prove history only; they do not regain current authority
```

No mutable canonical category is intentionally assigned to two repositories.

## 4. Current source and target governance/document inventory

| Repository | Durable root | Main governance/document families | Authority verdict |
| --- | --- | --- | --- |
| META | `README.md`, `AGENTS.md`, `CONTRIBUTING.md`, `SECURITY.md` | `docs/architecture/adr/`, `docs/ci/`, `docs/testing/`, `docs/release/`, `docs/recovery/`, `docs/governance/`, `docs/agents/`, `ecosystem/`, `tools/governance/` | cross-repo only |
| Game | provider root instructions/security/contribution docs | provider architecture, CI/test, tasks and Game-owned runtime/integration material | repository canonical |
| Platform | provider root instructions/security/contribution docs | provider architecture, deployment/operations, CI/test, runner/runbook/task material | repository canonical |
| Atlas | provider root instructions/security/contribution docs | provider architecture, publication/provenance, CI/test, FullWorld and local-E2E material | repository canonical |

Historical/archive paths may contain old coordinates and state as evidence. Mutable root/governance/active-task paths must not present historical coordinates as current authority.

## 5. Critical inconsistencies and risks

| ID | Severity | State | Finding |
| --- | --- | --- | --- |
| V310-RUNNER-ACL | HIGH | UNKNOWN | selected-repository ACLs for `platform-runners`, `atlas-runners`, `game-runners` cannot be read back from the connected org control-plane surface |
| V310-RUNNER-PLATFORM | HIGH | PARTIAL | Platform route is merged; trusted-main push workload result remains unreadable in this session |
| V310-RUNNER-GAME | HIGH | PARTIAL | Game route is hosted-CI green but independent-review policy blocks merge |
| V310-RUNNER-LEGACY | HIGH | NOT DONE | legacy `oteryn-synology-staging` deliberately retained until all replacement/security gates close |
| V310-MIG-GAME | HIGH | UNKNOWN | target authority and archived source are known; exhaustive final ref/tag/stale-coordinate closure remains unproved |
| V310-MIG-PLATFORM | HIGH | UNKNOWN | identity transfer is complete; full package/control-plane/external-identity/migration-machinery closure is unproved |
| V310-MIG-ATLAS | HIGH | NOT DONE | target is authoritative, but mode-specific selective-extraction/source-disposition acceptance is not fully proved in META |
| V310-RECOVERY | HIGH | PARTIAL | historical transfer-cut recovery is proved; current recurring organization recovery is not |
| V310-ACTIONS-POLICY | MEDIUM | PARTIAL | live governance audit records broad Actions-policy surfaces as warnings rather than silently promoting them |

## 6. Agent and Codex instruction architecture

- Root `AGENTS.md` files are durable routing/safety authority only; they must not carry current PR/SHA/CI/session state.
- Nested `AGENTS.md` / `AGENTS.override.md` exist only for bounded path-specific rules where justified by provider structure.
- GitHub Issues own mutable lifecycle (`status`, owner, dependencies, acceptance).
- Optional Markdown task packets cache execution detail and must link to their Issue; they are not a second status database.
- Reusable judgment-heavy procedures belong in skills/runbooks when supported; deterministic rules belong in scripts/CI.
- AI review is risk-classified. META uses its machine-readable R0/R1/R2 policy and fail-closed exact-head evidence verifier.
- Provider AI usage remains provider-policy-controlled. No organization audit may override a provider prohibition on paid/metered AI.
- A review result, comment or evidence artifact cannot broaden repository authority.

## 7. Tasks, programmes, handovers, prompts, branches and worktrees

Canonical model:

```text
GitHub Issue = lifecycle authority
one independently mergeable task = one branch = one PR
optional task packet = execution cache/detail
handover = expiring cache, never authority
PR/checks = exact-head integration truth
```

Task packets, if present:
- active: provider/META canonical `docs/agents/tasks/active/` convention where that repository uses it;
- terminal: archive or delete according to repository policy;
- must not remain active after a terminal Issue/PR outcome;
- cached SHAs/checks are advisory and must be refreshed from GitHub.

Prompts:
- reusable prompts require stable identity/version/owner/input/output/prohibited-actions/validation metadata;
- one-shot prompts terminate as delete, historical archive, reusable template, or retained evidence;
- `final`, `latest`, `v2`, `new` naming alone is not a lifecycle mechanism.

## 8. Architecture, ADR and contract ownership

META ADRs own ecosystem topology and organization operating model. Provider architecture and runtime contracts remain provider-owned. Cross-repository contracts are referenced by immutable coordinate/version when possible rather than copied into META. Evidence proves an architecture decision but does not become the decision unless an accepted policy explicitly promotes it.

## 9. GitHub organization governance

Verified design:
- protected default branch `main` for all permanent repositories;
- squash-oriented merge discipline;
- stable required-check identities or explicit transition state;
- GitHub Issues as lifecycle authority;
- read-only governance drift audit by default;
- CODEOWNERS/security/dependency baseline where supported;
- organization runner groups are intended to be selected-repository-only; this remains `UNKNOWN` until direct ACL readback is available.

No general auto-rewriter is authorized as the baseline drift mechanism.

## 10. CI target architecture

| Repository | Current required gate contract | Target / state |
| --- | --- | --- |
| META | `meta-gate`, `ai-review-gate` | stable |
| Game | `Merge gate / validate` | transition to stable `game-gate` |
| Platform | `classify-changes`, `test` | transition to stable `platform-gate` |
| Atlas | `atlas-gate`, `provenance-gate` | stable |

The META live-audit candidate verifies:
- main-applicable rulesets only;
- expected required-check GitHub App identity;
- representative emission only from protected `push`, matching `pull_request`, or matching `pull_request_target` flows;
- PR-head ancestry against current `main`;
- no union of evidence across unrelated/stale PR heads;
- fail-closed handling of incomplete code-search evidence.

Provider-specific tests feed provider-owned gates; the organization does not create redundant externally-required check names for every subcheck.

## 11. Test target architecture

Testing follows ownership:
- META: deterministic governance/schema/policy/verifier regression tests;
- Game: Game build/runtime/integration tests;
- Platform: application/deployment/staging tests;
- Atlas: publication/provenance/FullWorld/browser acceptance tests.

Self-hosted privileged workloads are trusted-path only. A pull request must not execute arbitrary untrusted code on the local privileged runner merely to prove routing.

Current runner replacement proof:
- Atlas trusted-main acceptance: PASS;
- Platform trusted-main result: UNKNOWN in available read surface;
- Game trusted-main acceptance: not reachable until independently reviewed PR can merge.

## 12. Security, dependency and supply-chain baseline

- secret scanning and push protection are organization desired-state minimums where supported;
- Dependabot security updates are checked through the dedicated automated-security-fixes endpoint; HTTP 204 is enabled and 404 is disabled;
- required-check name alone is insufficient: expected GitHub App identity is part of the proof;
- Actions changes are risk-bearing and reviewed accordingly;
- self-hosted runner base image is immutable and runner version is 2.336.0;
- raw Docker socket is host-equivalent privilege, never described as container isolation;
- Platform and Atlas have proved local workloads requiring Docker-host capability; Game target remains non-root without Docker socket;
- secrets, `.credentials`, environment dumps and private runtime data must not be committed as audit evidence.

## 13. Target repository trees and migrated-source disposition

The tree below is need-based; absent categories are not created for symmetry.

### META

```text
/                         [KEEP] root durable routing/security/contribution docs
/docs/architecture/adr/   [KEEP] ecosystem architecture authority
/docs/ci/                 [KEEP] META CI contract
/docs/testing/            [KEEP] ecosystem test strategy
/docs/release/            [KEEP] composition/release coordination
/docs/recovery/           [KEEP] organization recovery/break-glass
/docs/governance/         [KEEP] cross-repository governance
/docs/governance/audits/  [KEEP] durable audit contracts/results
/docs/agents/             [KEEP] META agent/task material when actually used
/ecosystem/               [KEEP] machine-readable topology/policy/release composition
/tools/governance/        [KEEP] deterministic validators/drift checks
```

### Game

```text
/                         [KEEP] provider durable routing/security/contribution docs
/.github/workflows/       [KEEP] Game-owned hosted/local integration gates
/docs/architecture/       [KEEP] Game architecture
/docs/agents/             [KEEP] Game task/agent material where repository convention uses it
provider source/tests     [KEEP] Game authority
META copies of Game docs  [NOT_NEEDED]
```

### Platform

```text
/                         [KEEP] provider durable routing/security/contribution docs
/.github/workflows/       [KEEP] Platform gates, deployment and bounded diagnostics
/docs/architecture/       [KEEP] Platform architecture
/docs/operations/         [KEEP] Platform operations/runner runbooks
/docs/agents/             [KEEP] Platform task/agent protocol
/deploy/                   [KEEP] Platform deployment authority
META copies               [NOT_NEEDED]
```

### Atlas

```text
/                         [KEEP] provider durable routing/security/contribution docs
/.github/workflows/       [KEEP] Atlas gate/provenance/local acceptance
/docs/architecture/       [KEEP] Atlas architecture
/docs/agents/             [KEEP] Atlas task/agent material where used
Atlas source/products     [KEEP] Atlas authority
META copies               [NOT_NEEDED]
```

### Migrated sources

- `blakinio/Oteryn-v2`: `[HISTORICAL_ARCHIVE]`, archived read-only, non-authoritative.
- `blakinio/Otheryn`: `[HISTORICAL/BOUNDED SOURCE]` for extracted Atlas lineage only; do not retire unrelated content by inference.
- Platform transfer backup: `[HISTORICAL_ARCHIVE]`, archived read-only, durable release/restore evidence retained.

## 14. Source-of-truth matrix

| Artifact/state class | Canonical authority | Mutable state allowed | Local copy rule |
| --- | --- | --- | --- |
| ecosystem topology/governance | META | yes, through protected PR | providers reference; no independently edited copy |
| provider architecture/runtime docs | owning provider | yes | META may reference, not duplicate normatively |
| repository task lifecycle | GitHub Issue in owning repo | yes | task packet is cache only |
| implementation/review integration | PR + required checks | yes | Markdown may link, not override |
| root/nested agent instructions | owning repo | durable rules only | no transient task/CI/SHA state |
| reusable prompts | owning repo/user config according to scope | versioned | one canonical mutable owner |
| evidence | owning evidence path/GitHub object | append/retention controlled | cannot broaden authority |
| generated reference | generator + source inputs | generated only | manual edits non-authoritative |
| runner-group ACL | GitHub organization settings | yes, owner-controlled | repository docs state desired intent only |
| recovery secret values | independent governed secret source | yes | never reconstructed from metadata APIs |

## 15. Migrated-source/current-file to target/disposition matrix

| Source/current object | Target / disposition | Current verdict |
| --- | --- | --- |
| `blakinio/Oteryn-v2` Game lineage | `Oteryn/Oteryn-Game`; legacy source archived | authority DONE; full migration completion UNKNOWN |
| `blakinio/Otheryn` bounded Atlas lineage | `Oteryn/Oteryn-Atlas`; source material historical/non-authoritative | selective extraction completion NOT DONE |
| transferred Platform identity | `Oteryn/Oteryn-Platform`, stable repo ID preserved | identity DONE; complete migration UNKNOWN |
| Platform transfer-cut backup | archived administrative repository | terminal disposition DONE |
| historical runner image/tag | immutable `ghcr.io/oteryn/...@sha256:f0c452...` | new supply chain DONE; legacy retirement pending |
| Platform-owned Atlas execution | Atlas-owned local runner/workflows | DONE |
| Game local integration execution | Game-owned runner candidate | PARTIAL / review blocked |

## 16. GitHub settings, protection and ruleset matrix

| Repository | Main protection | Required checks | Merge target | Live gap |
| --- | --- | --- | --- | --- |
| META | protected | `meta-gate`, `ai-review-gate` | stable | none in known protection contract |
| Game | protected/transition governance | `Merge gate / validate` | `game-gate` | transition not terminal |
| Platform | protected | `classify-changes`, `test` | `platform-gate` | transition not terminal |
| Atlas | protected | `atlas-gate`, `provenance-gate` | stable | none in known check contract |
| runner groups | organization control plane | selected-repository-only desired | exact one-provider repository each | direct ACL readback UNKNOWN |

## 17. Drift and governance-as-code

The read-only governance audit owns deterministic live checks for:
- repository identity/default branch/archive state;
- protection and required-check identity;
- required-check App binding and protected-flow emission;
- merge-policy baseline;
- security baseline;
- desired-state schema;
- administrative repository archive state;
- bounded historical-coordinate drift with complete/paginated search or `UNKNOWN`.

Documentation/agent drift additionally covers canonical path/ownership, root-instruction transient state, active/archive duplication, orphan task packets/handovers, provider/META authority duplication, generated/manual contradictions and evidence lifecycle. AI is not used for a fact a deterministic parser/API can prove.

## 18. Migration and source-retirement plan

1. Preserve current provider authorities and immutable provenance.
2. Close mode-specific migration evidence, not just repository existence.
3. Prove Platform and Game replacement runner workloads on trusted `main`.
4. Read back exact runner-group selected-repository ACLs.
5. Verify no workflow still requires the legacy staging runner.
6. Only then decide/remove legacy registration/container/state with bounded rollback evidence.
7. Re-run full stale-coordinate/ref/tag/source-disposition checks.
8. Promote Game/Platform/Atlas migration verdicts only when every acceptance item has direct evidence.

No source or rollback object is removed merely because it looks old.

## 19. Ordered implementation backlog

| Order | Item | Owner | State / acceptance |
| ---: | --- | --- | --- |
| 1 | merge terminal desired-state/drift audit | META | DONE — #37 squash-merged as `c0dbad93f791953d5efcc6b556e6be73693f0a4f`; #23 and #9 closed as superseded |
| 2 | obtain Platform trusted-main diagnostics run/job readback | Platform | UNKNOWN until direct run evidence |
| 3 | obtain permitted independent review and merge Game runner candidate | Game | BLOCKED by review authorization/surface |
| 4 | run trusted-main Game acceptance | Game | blocked by item 3 |
| 5 | read runner-group selected-repository ACLs | organization owner/control plane | UNKNOWN with current connector |
| 6 | retire legacy staging runner after 2–5 PASS | organization/Platform | NOT DONE by design |
| 7 | close migration-specific Game/Platform/Atlas evidence | each provider + META reconciliation | UNKNOWN/NO |
| 8 | implement recurring current-state recovery/control-plane/package/secret-owner recovery evidence | organization/providers | PARTIAL |
| 9 | terminalize stable `game-gate` / `platform-gate` transitions | Game/Platform | PARTIAL |
| 10 | re-run v3.10 final acceptance and close remaining Issues | META | blocked by preceding items |
| 11 | **DOCUMENTATION_IA**: complete provider path/owner/retention inventory against Matrix L | each provider + META reconciliation | UNKNOWN — direct provider inventory evidence is not complete (`V310-GAME-DOC-01`, `V310-PLATFORM-DOC-01`, `V310-ATLAS-DOC-01`) |
| 12 | **AGENT_INSTRUCTION**: revalidate root/nested instruction precedence and remove stale mutable routing | each repository owner | UNKNOWN — provider instruction inventories remain evidence-bound gaps |
| 13 | **PROMPT_LIFECYCLE**: classify reusable/one-shot prompts and prove unique canonical ownership | scope owner | PARTIAL — META terminal prompt disposition is recorded; provider lifecycle proof remains UNKNOWN |
| 14 | **TASK_LIFECYCLE**: reconcile active packets, handovers, Issues and terminal archive/delete states | each repository owner | UNKNOWN — active/terminal provider task inventories require direct evidence |
| 15 | **RUNBOOK**: inventory operations/recovery runbooks with owner, retention and tested recovery scope | provider owners + META recovery owner | UNKNOWN — current recurring recovery evidence is incomplete (`V310-RECOVERY-01`) |
| 16 | **EVIDENCE_GOVERNANCE**: bind subject/source/SHA/time/retention for durable audit evidence | META + provider evidence owners | PARTIAL — META exact-head/byte-bound evidence is enforced; provider evidence remains incomplete |
| 17 | **DOCS_CI**: require deterministic documentation/agent validation in governing CI | META + provider owners | PARTIAL — this report validator is required by META `meta-gate`; provider-equivalent coverage remains UNKNOWN |

## 20. Owner decisions

Decisions that cannot be invented by an autonomous audit:
- whether/when provider policy may authorize paid/metered AI review in Game;
- organization-owner runner-group ACL visibility/change when the connector cannot read it;
- final legacy-runner retirement after all rollback gates pass;
- acceptable organization-wide current backup RPO/RTO and independent secret/owner-recovery mechanisms;
- any destructive retirement of mixed-content historical repositories not wholly owned by this migration.

## 21. Final architecture verdict

The target architecture is accepted as the direction of travel:

- **ORGANIZATION GITHUB SETTINGS** — org-level runner ACLs, organization security/inheritance features that GitHub actually supports;
- **OPTIONAL `.github`** — only GitHub-supported shared defaults/templates when a real inheritance use case exists; not an invented AGENTS inheritance layer;
- **META** — thin ecosystem topology/governance/compatibility/release/recovery authority;
- **GAME** — Game implementation, provider docs/tests/runbooks and Game local integration;
- **PLATFORM** — Platform implementation, operations/deployment, Platform local control-plane;
- **ATLAS** — Atlas implementation, publication/provenance, FullWorld local preview/E2E;
- **PER TASK** — GitHub Issue lifecycle plus optional bounded task packet/cache;
- **CODEX USER/REPOSITORY CONFIG** — reusable AI configuration only at its actual supported authority layer;
- **GITHUB-NATIVE ENFORCEMENT** — protected branches/rulesets/checks/reviews as merge truth.

The architecture is coherent; the programme is not terminally complete while required evidence remains UNKNOWN/PARTIAL/NO.

# Matrix A0–L — execution coverage ledger

The labels below are the v3.10 completeness index used by this execution. They do not rename or retroactively alter the historical v3.9 result; they identify the evidence family exercised by this report.

| Matrix | Evidence family | State | Key result |
| --- | --- | --- | --- |
| A0 | scope, access and evidence coherence | PARTIAL | permanent repos inspected; org runner ACL/read surfaces incomplete |
| A | repository identity and topology | DONE | four permanent authorities and admin backup identity verified |
| B | authority/source-of-truth | DONE | META/provider/GitHub-native authority boundaries explicit |
| C | migration/source retirement | NOT DONE | Game/Platform UNKNOWN; Atlas NO |
| D | branch protection/merge governance | PARTIAL | stable META/Atlas; Game/Platform transitions remain |
| E | CI/check architecture | PARTIAL | stable identities plus transition targets recorded |
| F | test/runtime acceptance | PARTIAL | Atlas PASS; Platform/Game replacement proof incomplete |
| G | security/dependency/supply chain | PARTIAL | immutable runner supply chain; remaining governance warnings/gaps |
| H | agents/Codex/instruction loading | PARTIAL | durable model defined; provider-wide final hygiene not fully re-proved here |
| I | documentation/source ownership | DONE | central-vs-provider ownership defined without duplicate mutable authority |
| J | task/prompt/handover/evidence lifecycle | PARTIAL | model defined; open runner tasks remain active by design |
| K | recovery/break-glass | PARTIAL | historical transfer cut PASS; current org recovery gaps remain |
| L | Documentation & Agent IA | PARTIAL | full Matrix L/H14 present; G11 cannot PASS while terminal blockers remain |

# H1–H14 — documentation and agent IA acceptance

| Gate | Requirement | State |
| --- | --- | --- |
| H1 | root instructions remain short/durable routing authority | YES |
| H2 | nested/override instructions are bounded and precedence-aware | YES, where inspected; no blanket inheritance invented |
| H3 | Issues are lifecycle authority; task packets are caches | YES |
| H4 | reusable vs one-shot prompt lifecycle is explicit | YES as target contract |
| H5 | handovers are expiring caches, not authority | YES as target contract |
| H6 | retained evidence has subject/source/identity/time/retention semantics | YES for new terminal evidence; historical evidence retains its original format |
| H7 | canonical documentation paths are selected by need, not symmetry | YES |
| H8 | provider-owned docs remain provider-owned; META stays thin | YES |
| H9 | generated references are non-authoritative unless explicitly promoted | YES |
| H10 | deterministic documentation/agent invariants feed existing repo gates | PARTIAL; final provider-wide implementation varies by repository |
| H11 | stale/duplicate active lifecycle and historical-coordinate drift is detectable | PARTIAL; deterministic META coverage exists, provider-specific hygiene remains provider-owned |
| H12 | archive/retention/supersession rules are explicit | YES |
| H13 | each permanent repository has a need-based target-tree disposition | YES in section 13 |
| H14 | full documentation/agent inventory decision + Matrix L + evidence-backed gaps | YES structurally; terminal verdict remains incomplete because live gaps are preserved |

# G1–G11 — final audit gates

| Gate | Terminal condition | State | Reason |
| --- | --- | --- | --- |
| G1 | complete permanent/admin scope | PASS | four permanent repos plus bounded legacy/admin estate identified |
| G2 | access gaps explicit, no inferred PASS | PASS | missing proof remains explicit: `V310-RUNNER-ACL`, `V310-PLATFORM-RUN-01`, `V310-GAME-REVIEW-01` |
| G3 | authority graph/source-of-truth reconciled | PASS | sections 3 and 14 establish META/provider authority boundaries |
| G4 | migration completion mode-by-mode | UNKNOWN (GAP-ID: `V310-MIG-GAME-01`, `V310-MIG-PLATFORM-01`, `V310-MIG-ATLAS-01`) | required mode-specific acceptance evidence is incomplete |
| G5 | protection/check governance live-verified | UNKNOWN (GAP-ID: `V310-GAME-PROTECTION-01`, `V310-PLATFORM-PROTECTION-01`) | META is verified; current provider transition evidence is incomplete |
| G6 | CI/test/security target validated | UNKNOWN (GAP-ID: `V310-PLATFORM-RUN-01`, `V310-GAME-REVIEW-01`) | deterministic META proof exists; required provider trusted-main proof is missing |
| G7 | recovery/break-glass terminal | UNKNOWN (GAP-ID: `V310-RECOVERY-01`) | recurring current-state control-plane/package/secret/owner-redundancy proof is absent |
| G8 | runner topology/security/retirement terminal | UNKNOWN (GAP-ID: `V310-RUNNER-ACL`, `V310-PLATFORM-RUN-01`, `V310-GAME-REVIEW-01`) | selected-repository ACL and replacement/retirement proof remain incomplete |
| G9 | stale task/PR/branch/source cleanup terminal | UNKNOWN (GAP-ID: `V310-CLEANUP-01`) | cleanup is dependency-bound on successor merges and retained evidence |
| G10 | exact evidence/recommendation ledger and mechanical validation | UNKNOWN (GAP-ID: `V310-POSTMERGE-01`) | byte-bound report validation exists; final successor merge and post-merge refresh are pending |
| G11 | complete 21-section report + Matrix L + H14 with all terminal gates satisfied | UNKNOWN (GAP-ID: `V310-G4`, `V310-G5`, `V310-G6`, `V310-G7`, `V310-G8`, `V310-G9`, `V310-G10`) | report structure is mechanically validated, but dependent terminal gates are not PASS |

# Matrix L — Documentation & Agent Information Architecture

| Repository | Artifact class | Current paths / object | Canonical target / GitHub object | Authority owner | Consumer | Required metadata / invariant | Lifecycle / retention | Local copy / override | CI / drift enforcement | Migration action | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| META | NORMATIVE_AGENT_INSTRUCTION | `/AGENTS.md` | same | META | agents | durable routing/safety only | long-lived | provider copies forbidden as mutable authority | META gate/manual review | KEEP | current root contract |
| META | GOVERNANCE_POLICY | `docs/governance/**`, ADR 0002 | same | META | all repos/humans/agents | cross-repo only | versioned/protected | provider local extensions may reference | `meta-gate` + R2 where sensitive | KEEP | protected PR history |
| META | MACHINE_READABLE_POLICY | `ecosystem/**` | same | META | CI/drift/audit | schema + exact identities | current authority | no independent provider edits | deterministic validators | KEEP | desired-state workstream |
| META | RUNBOOK_RECOVERY | `docs/recovery/organization-recovery-contract.md` | same | META + provider delegation | owners/operators | UNKNOWN where unproved | durable; incident-driven update | provider recovery remains authoritative locally | protected review | KEEP | recovery PR #36 |
| META | TASK_PACKET_ACTIVE | `docs/agents/tasks/active/**` when used | Issue + optional packet | owning META task | agents | Issue link/scope/acceptance | archive/delete at terminal | no second status DB | lifecycle checks where deterministic | CLEANUP | current tasks |
| META | EVIDENCE_REVIEW | PR comments/checks + audit files | GitHub PR/check + durable audit | META | reviewers/auditors | head/fingerprint/source/time | retained for governance provenance | cannot broaden authority | AI evidence verifier | KEEP | META review gates |
| META | EVIDENCE_MIGRATION | `docs/governance/audits/**`, manifest | same / provider evidence links | META reconciliation | audit | exact repo/source identities | historical retention | provider evidence referenced | manual + drift | KEEP | this report |
| Game | NORMATIVE_AGENT_INSTRUCTION | root/nested AGENTS | provider canonical | Game | Game agents | provider safety/review rules | durable | META must not override | Game governance gate | KEEP | live root rules |
| Game | CI_POLICY | `.github/workflows/**` | provider workflows | Game | GitHub/agents | hosted/local trust boundary | current | no META copy | Game gates | KEEP/TRANSITION | Game PR #36 evidence |
| Game | RUNBOOK_OPERATIONAL | provider docs/tasks | provider canonical | Game | Game operators | local runtime scope | provider lifecycle | no META normative copy | provider tests | KEEP | Game repo |
| Platform | NORMATIVE_AGENT_INSTRUCTION | root/nested AGENTS | provider canonical | Platform | Platform agents | provider protocol/AI/resource rules | durable | META must not override | Agent Governance | KEEP | live root rules |
| Platform | RUNBOOK_OPERATIONAL | `docs/operations/**` | provider canonical | Platform | operators | runner/deploy safety | durable/versioned | no META normative copy | Platform CI | KEEP | runner runbook |
| Platform | CI_POLICY | `.github/workflows/**` | provider workflows | Platform | GitHub/operators | trusted path + workflow inventory | current | no META copy | Platform CI/workflow lifecycle | KEEP/TRANSITION | #1216 merge |
| Platform | TASK_PACKET_ACTIVE | `docs/agents/tasks/active/**` | Issue + provider packet | Platform | agents | Issue/PR/checkpoint | archive after terminal proof | no second lifecycle DB | Agent Governance | KEEP ACTIVE | #1215 |
| Atlas | NORMATIVE_AGENT_INSTRUCTION | root/nested AGENTS | provider canonical | Atlas | Atlas agents | provider publication/provenance safety | durable | META must not override | Atlas gates | KEEP | Atlas repo |
| Atlas | EVIDENCE_RELEASE | provider artifacts/workflow evidence | Atlas GitHub objects | Atlas | audit/consumers | exact revision/artifact digest | retained per provider policy | META references immutable IDs | `atlas-gate`/`provenance-gate` | KEEP | run `32526864123` |
| Atlas | RUNBOOK_OPERATIONAL | provider local preview/publication docs | Atlas | operators | local FullWorld ownership | provider lifecycle | no Platform mutable copy | Atlas acceptance | KEEP | post-#1212 ownership |
| all | HANDOVER_CACHE | session/task handovers when present | owning Issue/PR links | task owner | next agent | task/repo/PR/head/time/blocker/next action | expire on supersession | never authority | stale-cache checks where deterministic | ARCHIVE/DELETE | v3.10 contract |
| all | PROMPT_REUSABLE | provider/META/user prompt location by scope | exactly one owning layer | scope owner | agents | stable ID/version/status/contracts | versioned | local override only if declared | duplicate-ID/ownership checks where justified | KEEP/MOVE | v3.10 contract |
| all | GENERATED_REFERENCE | generated reports/indexes | generator-owned output | generator source owner | humans/agents | provenance marker/input identity | regenerate | manual copy non-authoritative | deterministic generation | GENERATED | v3.10 contract |
| historical | HISTORICAL_ARCHIVE | archived legacy/migration repos and evidence paths | historical only | provenance owner | audit/recovery | old coordinates allowed as history | retained by explicit reason | never current authority | exclusion-aware drift rules | ARCHIVE | live archive state |

### Matrix L required-class completion ledger

The broad authority rows above are supplemented by this exhaustive disposition ledger. Every compact cell is `current path/object → canonical target; authority; lifecycle; enforcement; disposition`. Every `UNKNOWN` cell carries a `V310-*` gap identifier and means the repository remains provider-owned but its current inventory/canonical-path evidence was not directly revalidated; it is never an inferred PASS. `NOT_NEEDED` means no empty taxonomy is to be created.

| Required artifact class | META | Game | Platform | Atlas |
| --- | --- | --- | --- | --- |
| root AGENTS | `/AGENTS.md → same; META; durable; meta-gate; KEEP` | `UNKNOWN (V310-GAME-DOC-01): provider root instruction inventory` | `UNKNOWN (V310-PLATFORM-DOC-01): provider root instruction inventory` | `UNKNOWN (V310-ATLAS-DOC-01): provider root instruction inventory` |
| nested AGENTS/override | `NOT_NEEDED; no nested META authority` | `UNKNOWN (V310-GAME-DOC-01): provider override inventory` | `UNKNOWN (V310-PLATFORM-DOC-01): provider override inventory` | `UNKNOWN (V310-ATLAS-DOC-01): provider override inventory` |
| architecture/ADR | `docs/architecture/adr/** → META; retained; protected review; KEEP` | `UNKNOWN (V310-GAME-DOC-01): provider canonical ADR path` | `UNKNOWN (V310-PLATFORM-DOC-01): provider canonical ADR path` | `UNKNOWN (V310-ATLAS-DOC-01): provider canonical ADR path` |
| contracts | `docs/agents/contracts/** → META; retained; meta-gate; KEEP` | `UNKNOWN (V310-GAME-DOC-01): provider contract inventory` | `UNKNOWN (V310-PLATFORM-DOC-01): provider contract inventory` | `UNKNOWN (V310-ATLAS-DOC-01): provider contract inventory` |
| governance policy | `docs/governance/** → META; retained; R2 where sensitive; KEEP` | `provider local policy → Game; durable; local gate; KEEP` | `provider local policy → Platform; durable; local gate; KEEP` | `provider local policy → Atlas; durable; local gate; KEEP` |
| CI policy | `.github/workflows/** → META; current; meta-gate; KEEP` | `UNKNOWN (V310-GAME-PROTECTION-01): current workflow policy` | `UNKNOWN (V310-PLATFORM-PROTECTION-01): current workflow policy` | `provider workflows → Atlas; current; atlas/provenance gates; KEEP` |
| test strategy | `docs/testing/ECOSYSTEM_TEST_STRATEGY.md → META; retained; meta-gate; KEEP` | `UNKNOWN (V310-GAME-DOC-01): provider strategy/evidence` | `UNKNOWN (V310-PLATFORM-DOC-01): provider strategy/evidence` | `UNKNOWN (V310-ATLAS-DOC-01): provider strategy/evidence` |
| reusable prompts | `docs/agents/prompts/README.md → META; versioned; ownership index; KEEP` | `NOT_APPLICABLE; provider decides local reusable prompts` | `NOT_APPLICABLE; provider decides local reusable prompts` | `NOT_APPLICABLE; provider decides local reusable prompts` |
| one-shot prompts | `terminal #37 prompt → historical; do-not-invoke; ARCHIVE` | `UNKNOWN (V310-GAME-DOC-01): provider one-shot prompt lifecycle` | `UNKNOWN (V310-PLATFORM-DOC-01): provider one-shot prompt lifecycle` | `UNKNOWN (V310-ATLAS-DOC-01): provider one-shot prompt lifecycle` |
| task packets | `Issue + optional docs/agents/tasks/active → owner; expire on close; CLEANUP` | `UNKNOWN (V310-GAME-DOC-01): provider task lifecycle` | `docs/agents/tasks/active → Platform; archive on proof; KEEP ACTIVE` | `UNKNOWN (V310-ATLAS-DOC-01): provider task lifecycle` |
| programmes | `audit/report + GitHub Issues → META; retained; meta-gate; KEEP` | `NOT_APPLICABLE; no META programme copy` | `NOT_APPLICABLE; no META programme copy` | `NOT_APPLICABLE; no META programme copy` |
| handovers | `checkpoint → Issue/PR authority; supersede on merge; ARCHIVE` | `UNKNOWN (V310-GAME-DOC-01): provider handover rule` | `UNKNOWN (V310-PLATFORM-DOC-01): provider handover rule` | `UNKNOWN (V310-ATLAS-DOC-01): provider handover rule` |
| agent runbooks | `NOT_NEEDED; META has no host-local runtime` | `UNKNOWN (V310-GAME-DOC-01): provider agent-runbook inventory` | `UNKNOWN (V310-PLATFORM-DOC-01): provider agent-runbook inventory` | `UNKNOWN (V310-ATLAS-DOC-01): provider agent-runbook inventory` |
| operations runbooks | `docs/recovery/** only → META recovery coordination; retained; KEEP` | `UNKNOWN (V310-GAME-DOC-01): provider operations runbook` | `docs/operations/** → Platform; versioned; Platform CI; KEEP` | `UNKNOWN (V310-ATLAS-DOC-01): provider operations runbook` |
| recovery/break-glass | `docs/recovery/organization-recovery-contract.md → META; durable; protected review; KEEP` | `UNKNOWN (V310-RECOVERY-01): provider recovery proof` | `UNKNOWN (V310-RECOVERY-01): provider recovery proof` | `UNKNOWN (V310-RECOVERY-01): provider recovery proof` |
| review evidence | `PR reviews/checks → GitHub; immutable provenance; verifier; KEEP` | `UNKNOWN (V310-GAME-REVIEW-01): permitted independent review proof` | `UNKNOWN (V310-PLATFORM-PROTECTION-01): current review evidence` | `UNKNOWN (V310-ATLAS-DOC-01): current review evidence` |
| release evidence | `NOT_APPLICABLE; META is coordination authority` | `UNKNOWN (V310-GAME-DOC-01): provider release evidence` | `UNKNOWN (V310-PLATFORM-DOC-01): provider release evidence` | `artifacts/workflow evidence → Atlas; retained; provenance gate; KEEP` |
| migration evidence | `ecosystem/repositories.json + audit → META reconciliation; retained; KEEP` | `UNKNOWN (V310-MIG-GAME-01): mode-specific acceptance` | `UNKNOWN (V310-MIG-PLATFORM-01): mode-specific acceptance` | `UNKNOWN (V310-MIG-ATLAS-01): selective-extraction acceptance` |
| generated docs/indexes | `NOT_NEEDED unless generator is introduced; generator source authoritative` | `UNKNOWN (V310-GAME-DOC-01): generated-doc inventory` | `UNKNOWN (V310-PLATFORM-DOC-01): generated-doc inventory` | `UNKNOWN (V310-ATLAS-DOC-01): generated-doc inventory` |
| human reference docs | `README.md + docs/governance/** → META; versioned; meta-gate; KEEP` | `UNKNOWN (V310-GAME-DOC-01): provider reference-doc inventory` | `UNKNOWN (V310-PLATFORM-DOC-01): provider reference-doc inventory` | `UNKNOWN (V310-ATLAS-DOC-01): provider reference-doc inventory` |
| machine-readable policy companions | `ecosystem/*.json → META; schema/CI; KEEP` | `UNKNOWN (V310-GAME-DOC-01): provider machine policy` | `UNKNOWN (V310-PLATFORM-DOC-01): provider machine policy` | `UNKNOWN (V310-ATLAS-DOC-01): provider machine policy` |
| documentation/agent validators | `tools/governance/validate_v310_audit_docs.py + OTERYN-v3.10-*-VALIDATION.json → META; byte-bound; deterministic hash check; KEEP` | `UNKNOWN (V310-GAME-DOC-01): provider validator inventory` | `UNKNOWN (V310-PLATFORM-DOC-01): provider validator inventory` | `UNKNOWN (V310-ATLAS-DOC-01): provider validator inventory` |

## Mechanical completion statement

This report is intentionally capable of validating structurally while returning a non-terminal programme verdict. Structural completeness and programme completion are separate facts.

`REPORT_STRUCTURE = COMPLETE`

`OTERYN_ORG_AUDIT_V3_10 = INCOMPLETE`
