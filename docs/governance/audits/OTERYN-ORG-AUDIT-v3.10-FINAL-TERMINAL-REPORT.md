# OTERYN-ORG-AUDIT-v3.10 — final terminal audit report

Audit contract: `OTERYN-ORG-AUDIT-v3.10`
Base contract: `OTERYN-ORG-GOVERNANCE-ARCHITECTURE-ULTRA-AUDIT-v3.9-EXECUTION-OPTIMIZED-FINAL`
Report date: 2026-08-22
Lifecycle authority: GitHub Issues and protected pull requests
Evidence policy: fail closed; `UNKNOWN` is retained where the connected surfaces cannot prove a fact

This report is the full v3.10 execution artifact. The accompanying Documentation & Agent IA addendum is preserved byte-for-byte from its validated successor branch; this report does not rewrite the historical v3.9 result.

## 1. Executive verdict

**Current terminal verdict: `INCOMPLETE`.**

The organization has a coherent four-repository authority model, protected META governance, a merged organization recovery contract, an immutable organization-runner image, and a terminal product-isolated Synology runner estate. Direct organization API readback proves one selected repository per runner group, all three provider-owned trusted-main acceptance workloads passed, and the legacy staging runner was retired only after those gates closed. The audit cannot truthfully return `COMPLETE` while the following independent acceptance facts remain unproved or incomplete:

1. Game and Platform migration verdicts remain `UNKNOWN`, and Atlas migration remains `NO`, because their mode-specific terminal evidence is not complete;
2. organization-wide recurring current-state backup/control-plane/package/secret/owner-redundancy recovery remains unproved;
3. the Game and Platform stable gate-name transitions remain non-terminal governance work.

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

### Material documentation/agent inventory

Each row assigns one primary class to a material current path/object family. `Normative = YES` means the row has exactly one canonical authority; non-normative evidence/cache rows cannot broaden authority.

| Repository | Current path/object | Primary class | Normative | Canonical authority | Lifecycle / disposition | Context cost |
| --- | --- | --- | --- | --- | --- | --- |
| META | `/AGENTS.md` | root AGENTS | YES | META | durable routing policy | always loaded; bounded root context |
| META | `docs/architecture/adr/**` | architecture/ADR | YES | META | durable/versioned | routed |
| META | `docs/governance/**` | governance policy | YES | META | durable/protected | routed |
| META | `docs/ci/**` | CI policy | YES | META | durable/protected | routed |
| META | `docs/testing/**` | test strategy | YES | META | durable/protected | routed |
| META | `docs/recovery/**` | recovery/break-glass | YES | META | durable; incident-driven | routed |
| META | `ecosystem/**` | machine-readable policy companions | YES | META | current authority | machine-read |
| META | `tools/governance/**` | documentation/agent validators | YES | META | versioned with policy | CI-loaded |
| META | `docs/agents/prompts/OTERYN-*.md` | one-shot prompts | NO | META | historical/completed; do not execute | on-demand provenance |
| META | `docs/evidence/**` | review evidence | NO | META | retained by evidence policy | on-demand |
| Game | `/AGENTS.md` | root AGENTS | YES | Game | durable routing policy | always loaded; 3,267-byte live baseline |
| Game | `apps/game-server/AGENTS.md`; `crates/simulation-determinism/AGENTS.md`; `docs/agents/AGENTS.md` | nested AGENTS/override | YES | Game | path-scoped; no override file | path-loaded |
| Game | `docs/architecture/**` | architecture/ADR | YES | Game | provider canonical | routed |
| Game | `docs/contracts/**`; `crates/platform-contracts/**` | contracts | YES | Game | provider canonical | routed |
| Game | `.github/repository-policy.json`; `docs/agents/GOVERNANCE_CONTRACT.json` | governance policy | YES | Game | provider canonical | CI/machine-read |
| Game | `.github/workflows/**` | CI policy | YES | Game | current provider workflows | CI-loaded |
| Game | `docs/agents/BUILD_TEST_MATRIX.md`; `tests/**` | test strategy | YES | Game | provider canonical | routed/test-loaded |
| Game | `docs/agents/prompts/**` | reusable prompts | NO | Game | retained; per-file metadata verification gap `GAP-PROMPT-GAME-001` | on-demand |
| Game | `docs/agents/tasks/{active,archive}/**` | task packets | NO | Game | Issue authority; packet cache | on-demand |
| Game | `docs/agents/programs/**` | programmes | NO | Game | Issue authority; programme cache | on-demand |
| Game | `docs/agents/evidence/**` | review evidence | NO | Game | retained provider evidence | on-demand |
| Platform | `/AGENTS.md` | root AGENTS | YES | Platform | durable routing policy | always loaded; 22,157-byte live baseline |
| Platform | `docs/agents/AGENTS.md` | nested AGENTS/override | YES | Platform | path-scoped; no override file | path-loaded |
| Platform | `docs/architecture/adr/**` | architecture/ADR | YES | Platform | provider canonical | routed |
| Platform | `docs/contracts/**` | contracts | YES | Platform | provider canonical | routed |
| Platform | `docs/agents/GOVERNANCE_CONTRACT.json`; `BRANCH_LIFECYCLE_POLICY.json` | governance policy | YES | Platform | provider canonical | machine-read |
| Platform | `.github/workflows/**`; `docs/agents/CI_WORKFLOW_LIFECYCLE.*` | CI policy | YES | Platform | provider canonical | CI-loaded |
| Platform | `docs/testing/**`; `docs/agents/BUILD_TEST_MATRIX.md` | test strategy | YES | Platform | provider canonical | routed/test-loaded |
| Platform | `docs/agents/prompts/**` | reusable prompts | NO | Platform | retained; per-file lifecycle/metadata gap `GAP-PROMPT-PLATFORM-001` | on-demand |
| Platform | `docs/agents/tasks/active/**` | task packets | NO | Platform | Issue authority; packet cache | on-demand |
| Platform | `docs/agents/programs/**` | programmes | NO | Platform | Issue authority; programme cache | on-demand |
| Platform | `docs/operations/**`; `deploy/synology/**` | operations runbooks | YES | Platform | provider operations authority | operator-routed |
| Platform | `docs/agents/evidence/**` | review evidence | NO | Platform | retained provider evidence | on-demand |
| Atlas | `/AGENTS.md` | root AGENTS | YES | Atlas | durable routing policy | always loaded; 2,917-byte live baseline |
| Atlas | `docs/agents/prompts/**` | reusable prompts | NO | Atlas | retained; per-file metadata gap `GAP-PROMPT-ATLAS-001` | on-demand |
| Atlas | `docs/agents/tasks/{active,archive}/**` | task packets | NO | Atlas | Issue authority; packet cache | on-demand |
| Atlas | `docs/evidence/**` | release evidence | NO | Atlas | retained publication/runtime evidence | on-demand |
| Atlas | `docs/migration/**` | migration evidence | NO | Atlas | retained extraction provenance | on-demand |
| Atlas | `tools/governance/**` | documentation/agent validators | YES | Atlas | provider validator authority | CI-loaded |
| Atlas | `README.md`; `SECURITY.md`; `e2e/README.md` | human reference docs | YES | Atlas | provider canonical | human-routed |
| META | `docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md`; `docs/ci/CI_CONTRACT.md` | contracts | YES | META | durable while authoritative; update through protected provider process | on-demand/routed |
| META | `docs/governance/audits/**`; `docs/evidence/**`; `ecosystem/repositories.json` | migration evidence | NO | META | append/retain by evidence or migration provenance policy | on-demand/routed |
| META | `README.md`; `CONTRIBUTING.md`; `SECURITY.md`; `docs/**` | human reference docs | YES | META | durable while authoritative; update through protected provider process | on-demand/routed |
| Game | historical prompt/task/evidence files under `docs/agents/tasks/archive/**` and `docs/agents/evidence/**` | one-shot prompts | NO | Game | historical retained by provenance rule | on-demand/routed |
| Game | `docs/agents/CONTEXT_HANDOFF.md`; handoff evidence/reports | handovers | NO | Game | active only while linked lifecycle is live; archive/delete on supersession | on-demand/routed |
| Game | `docs/agents/EXECUTION_PROTOCOL.md`; `GITHUB_ONLY_EXECUTION.md`; related agent procedures | agent runbooks | YES | Game | durable while authoritative; update through protected provider process | on-demand/routed |
| Game | `docs/architecture/ADR-0009-game-node-execution-capacity-deployment-and-recovery-baseline.md`; `docs/agents/SESSION_RECOVERY_AND_ORPHANED_EXECUTION.md` | recovery/break-glass | YES | Game | durable while authoritative; update through protected provider process | operator-routed |
| Game | `docs/agents/evidence/OTV2-20260818-*`; migration ADRs | migration evidence | NO | Game | append/retain by evidence or migration provenance policy | on-demand/routed |
| Game | `README.md`; `CONTRIBUTING.md`; `SECURITY.md`; provider docs | human reference docs | YES | Game | durable while authoritative; update through protected provider process | on-demand/routed |
| Game | `.github/repository-policy.json`; `docs/agents/GOVERNANCE_CONTRACT.json`; `PROJECT_LANES.json` | machine-readable policy companions | YES | Game | durable while authoritative; update through protected provider process | machine-read |
| Game | `.github/workflows/agent-governance.yml`; `architecture-semantic-audit.yml`; `merge-gate.yml`; `repository-configuration.yml` | documentation/agent validators | YES | Game | durable while authoritative; update through protected provider process | CI-loaded |
| Platform | `docs/agents/CONTEXT_HANDOFF.md`; provider evidence handoffs | handovers | NO | Platform | active only while linked lifecycle is live; archive/delete on supersession | on-demand/routed |
| Platform | `docs/agents/**` execution/governance procedures | agent runbooks | YES | Platform | durable while authoritative; update through protected provider process | on-demand/routed |
| Platform | `docs/operations/INCIDENT_RECOVERY_RUNBOOK.md`; `SYNOLOGY_ROLLBACK_SCHEMA_SAFETY.md`; `deploy/synology/scripts/rollback.sh`; `recover-schema.sh` | recovery/break-glass | YES | Platform | durable while authoritative; update through protected provider process | operator-routed |
| Platform | `deploy/synology/release-contract.env`; release/deployment workflow evidence | release evidence | NO | Platform | append/retain by evidence or migration provenance policy | on-demand/routed |
| Platform | provider migration/audit evidence; historical branch audit; META reconciliation | migration evidence | NO | Platform | append/retain by evidence or migration provenance policy | on-demand/routed |
| Platform | `docs/agents/evidence/**/index.md`; machine-generated evidence manifests | generated docs/indexes | NO | Platform | regenerate from authoritative inputs; output non-authoritative unless promoted | on-demand/routed |
| Platform | `README.md`; `CONTRIBUTING.md`; `SECURITY.md`; `docs/**` | human reference docs | YES | Platform | durable while authoritative; update through protected provider process | on-demand/routed |
| Platform | `docs/agents/*.json`; release/deployment contract data | machine-readable policy companions | YES | Platform | durable while authoritative; update through protected provider process | machine-read |
| Platform | `.github/workflows/agent-governance.yml`; `historical-branch-audit.yml`; prompt-eval/governance checks | documentation/agent validators | YES | Platform | durable while authoritative; update through protected provider process | CI-loaded |
| Atlas | `.github/workflows/ci.yml`; `extraction-provenance.yml`; `synology-live-acceptance.yml`; `synology-runner-health.yml` | CI policy | YES | Atlas | durable while authoritative; update through protected provider process | CI-loaded |
| Atlas | `docs/evidence/DYN-ATLAS-001-target-gui-execution-prompt.md` and bounded execution evidence | one-shot prompts | NO | Atlas | historical retained by provenance rule | on-demand/routed |
| Atlas | `docs/evidence/ATLAS-FULLWORLD-PROGRAMME-LEDGER.md` | programmes | NO | Atlas | active only while linked lifecycle is live; archive/delete on supersession | on-demand/routed |
| Atlas | `docs/evidence/fullworld-generation/handoff-summary.json` | handovers | NO | Atlas | historical retained by provenance rule | on-demand/routed |
| Atlas | `docs/agents/SYNOLOGY_DESKTOP_COMMANDER_ACCESS.md`; prompt/task routing docs | agent runbooks | YES | Atlas | durable while authoritative; update through protected provider process | on-demand/routed |
| Atlas | `docs/evidence/ISSUE-*.md`; GitHub PR/review/check objects | review evidence | NO | Atlas | append/retain by evidence or migration provenance policy | on-demand/routed |
| Atlas | `web/semantic-search/index.json`; FullWorld generated evidence/index outputs | generated docs/indexes | NO | Atlas | regenerate from authoritative inputs; output non-authoritative unless promoted | on-demand/routed |

## 5. Critical inconsistencies and risks

| ID | Severity | State | Finding |
| --- | --- | --- | --- |
| V310-RUNNER-ACL | HIGH | DONE | direct organization API readback proves `platform-runners` -> `Oteryn/Oteryn-Platform`, `atlas-runners` -> `Oteryn/Oteryn-Atlas`, and `game-runners` -> `Oteryn/Oteryn-Game`, exactly one selected repository each |
| V310-RUNNER-PLATFORM | HIGH | DONE | trusted-main run/job `32567509732` / `97018190282` passed on `platform-runners` + `oteryn-platform` + `oteryn-synology-platform` |
| V310-RUNNER-GAME | HIGH | DONE | trusted-main run/job `32566399984` / `97015531724` passed on `game-runners` + `oteryn-game` + `oteryn-synology-game` with UID/GID `1001:1001` and no Docker-host control |
| V310-RUNNER-LEGACY | HIGH | DONE | Platform #1221 removed retained `oteryn-staging` selectors; legacy runner id `21` was deregistered and its container removed after replacement proof, while rollback state was preserved |
| V310-MIG-GAME | HIGH | UNKNOWN | target authority and archived source are known; exhaustive final ref/tag/stale-coordinate closure remains unproved |
| V310-MIG-PLATFORM | HIGH | UNKNOWN | identity transfer is complete; full package/control-plane/external-identity/migration-machinery closure is unproved |
| V310-MIG-ATLAS | HIGH | NOT DONE | target is authoritative, but mode-specific selective-extraction/source-disposition acceptance is not fully proved in META |
| V310-RECOVERY | HIGH | PARTIAL | historical transfer-cut recovery is proved; current recurring organization recovery is not |
| V310-ACTIONS-POLICY | MEDIUM | PARTIAL | live governance audit records broad Actions-policy surfaces as warnings rather than silently promoting them |

Durable runner closeout evidence: `docs/evidence/OTERYN-ORG-RUNNER-ACL-LIVE-CLOSEOUT-20260822.md`.

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

### Prompt/task/handover lifecycle verification

The table is the deterministic audit ledger for the 30A prompt/task/handover invariants. A non-PASS row is an explicit audit gap and constrains G11; it is not silently accepted.

| Repository | Artifact family | Required invariant | Verification state | Lifecycle authority / supersession |
| --- | --- | --- | --- | --- |
| META | reusable prompts | stable identity/version/status for every retained reusable prompt | PASS - active reusable prompt library is `NOT_NEEDED`; retained executor prompts are classified one-shot historical | META policy; live GitHub state outranks historical prompts |
| META | one-shot prompts | terminal prompts cannot remain executable | PASS | `docs/agents/prompts/OTERYN-*.md` marked `HISTORICAL / COMPLETED - DO NOT EXECUTE`; final report supersedes |
| Game | reusable prompts | stable identity/version/status for every retained reusable prompt | UNKNOWN (`GAP-PROMPT-GAME-001`: per-file metadata not exhaustively reverified) | Game provider authority; remediation in section 19 |
| Platform | reusable prompts | stable identity/version/status for every retained reusable prompt | UNKNOWN (`GAP-PROMPT-PLATFORM-001`: 22 prompt files not exhaustively classified/metadata-verified) | Platform provider authority; remediation in section 19 |
| Atlas | reusable prompts | stable identity/version/status for every retained reusable prompt | UNKNOWN (`GAP-PROMPT-ATLAS-001`: per-file metadata not exhaustively reverified) | Atlas provider authority; remediation in section 19 |
| META | active task packets | explicit lifecycle authority | PASS - no active META task packet required for this terminal closeout | GitHub Issue/PR; optional packet only as cache |
| Game | active task packets | explicit lifecycle authority on every active packet | UNKNOWN (`GAP-TASK-GAME-001`: per-file Issue linkage not exhaustively reverified) | GitHub Issues are authority; packet is cache |
| Platform | active task packets | explicit lifecycle authority on every active packet | UNKNOWN (`GAP-TASK-PLATFORM-001`: per-file Issue linkage not exhaustively reverified) | GitHub Issues are authority; packet is cache |
| Atlas | active task packets | explicit lifecycle authority on every active packet | UNKNOWN (`GAP-TASK-ATLAS-001`: active coordinator packet linkage not exhaustively reverified) | GitHub Issues are authority; packet is cache |
| META | handovers | explicitly non-authoritative plus expiry/supersession | PASS - none retained as current authority | GitHub Issue/PR/live checks supersede any session cache |
| Game | handovers | explicitly non-authoritative plus expiry/supersession | UNKNOWN (`GAP-HANDOVER-GAME-001`: retained handoff evidence not exhaustively metadata-verified) | live Issue/PR/provider state outranks handover |
| Platform | handovers | explicitly non-authoritative plus expiry/supersession | UNKNOWN (`GAP-HANDOVER-PLATFORM-001`: retained handoff evidence not exhaustively metadata-verified) | live Issue/PR/provider state outranks handover |
| Atlas | handovers | explicitly non-authoritative plus expiry/supersession | PASS for `docs/evidence/fullworld-generation/handoff-summary.json` as historical evidence | live Issue/PR/provider state supersedes retained handoff evidence |

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
- organization runner groups are selected-repository-only and directly re-verified on 2026-08-22: `platform-runners` -> Platform only, `atlas-runners` -> Atlas only, `game-runners` -> Game only; the organization `Default` group has no runners.

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
- Platform trusted-main run/job `32567509732` / `97018190282`: PASS on `platform-runners` + `oteryn-platform`;
- Game trusted-main run/job `32566399984` / `97015531724`: PASS on `game-runners` + `oteryn-game`;
- direct organization readback on 2026-08-22 shows exactly three organization runners, each online on Actions Runner `2.336.0`, and zero runners in the `Default` group.

## 12. Security, dependency and supply-chain baseline

- secret scanning and push protection are organization desired-state minimums where supported;
- Dependabot security updates are checked through the dedicated automated-security-fixes endpoint; HTTP 204 is enabled and 404 is disabled;
- required-check name alone is insufficient: expected GitHub App identity is part of the proof;
- Actions changes are risk-bearing and reviewed accordingly;
- self-hosted runner base image is immutable and runner version is 2.336.0;
- raw Docker socket is host-equivalent privilege, never described as container isolation;
- Platform and Atlas have proved local workloads requiring Docker-host capability; Game proved its least-privilege local route at UID/GID `1001:1001` without Docker-host control;
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
/docs/architecture/       [OPTIONAL] only after `GAP-DOCS-ATLAS-ARCH-001` is closed with a proven provider need; do not pre-create
/docs/agents/             [KEEP] Atlas task/agent material where used
Atlas source/products     [KEEP] Atlas authority
META copies               [NOT_NEEDED]
```

### Section-26A placement decision matrix

Every answer uses an allowed target-tree disposition. `[OPTIONAL]` never authorizes pre-creating an empty path; the path/object is created only when the stated need exists.

| Placement question | META | Game | Platform | Atlas |
| --- | --- | --- | --- | --- |
| Where does a new reusable prompt go? | `[OPTIONAL] docs/agents/prompts/<ID>.md` only for a demonstrated META-owned reusable need | `[KEEP] docs/agents/prompts/<ID>.md` | `[KEEP] docs/agents/prompts/<ID>.md` | `[KEEP] docs/agents/prompts/<ID>.md` |
| Where does a one-shot prompt go while active? | `[OPTIONAL] owning GitHub Issue/PR or optional task packet; not the reusable library by default` | `[KEEP] GitHub Issue + optional docs/agents/tasks/active/<ID>.md` | `[KEEP] GitHub Issue + optional docs/agents/tasks/active/<ID>.md` | `[KEEP] GitHub Issue + optional docs/agents/tasks/active/<ID>.md` |
| What happens to a one-shot prompt when complete? | `[KEEP] mark historical/completed when retained as provenance, otherwise delete with Issue history preserved` | `[KEEP] archive/delete under provider task/evidence policy` | `[KEEP] archive/delete under provider task/evidence policy` | `[KEEP] archive/delete under provider task/evidence policy` |
| Where does an optional task packet go? | `[OPTIONAL] docs/agents/tasks/active/<ID>.md only if GitHub Issue needs durable detail` | `[KEEP] docs/agents/tasks/active/<ID>.md` | `[KEEP] docs/agents/tasks/active/<ID>.md` | `[KEEP] docs/agents/tasks/active/<ID>.md` |
| Where does it go when the Issue closes? | `[KEEP] archive/delete according to retention; Issue remains authority` | `[KEEP] docs/agents/tasks/archive/** or delete if no provenance need` | `[KEEP] archive/delete according to provider policy` | `[KEEP] docs/agents/tasks/archive/** or delete if no provenance need` |
| Where does a handover live and when does it expire? | `[OPTIONAL] Issue/PR/session cache; expires on supersession/terminal PR` | `[KEEP] provider handoff/evidence cache; live Issue/PR supersedes` | `[KEEP] provider handoff/evidence cache; live Issue/PR supersedes` | `[KEEP] retained handoff evidence; live Issue/PR supersedes` |
| Where does operational/recovery procedure live? | `[KEEP] docs/recovery/**` | `[OPTIONAL] provider-owned runbook only when recurring need is proven; recovery ADR remains current durable baseline` | `[KEEP] docs/operations/** and deploy/synology/**` | `[OPTIONAL] provider-owned operations/recovery runbook when recurring need is proven; current gaps remain explicit` |
| Where does review/release/migration evidence live? | `[KEEP] docs/evidence/** and docs/governance/audits/**` | `[KEEP] docs/agents/evidence/** plus GitHub PR/check objects` | `[KEEP] docs/agents/evidence/** plus GitHub PR/check/release objects` | `[KEEP] docs/evidence/** and docs/migration/**` |
| Where does generated documentation live? | `[NOT_NEEDED] no generated documentation is normative META authority` | `[NOT_NEEDED] generated product artifacts remain provider outputs, not normative docs` | `[GENERATED] bounded generator/evidence index outputs under provider-owned evidence paths` | `[GENERATED] provider generated indexes such as web/semantic-search/index.json with source provenance` |
| Which documents belong only in META? | `[KEEP] ecosystem topology, cross-repository governance/ADR, composition/recovery authority` | `[NOT_NEEDED] do not copy META normative authority` | `[NOT_NEEDED] do not copy META normative authority` | `[NOT_NEEDED] do not copy META normative authority` |
| Which remain provider-local? | `[NOT_NEEDED] provider implementation/operations docs are referenced, not copied` | `[KEEP] Game architecture/contracts/tests/runtime/agent material` | `[KEEP] Platform architecture/contracts/tests/operations/deployment/agent material` | `[KEEP] Atlas publication/provenance/FullWorld/runtime/agent material` |
| Which paths are checked by CI? | `[KEEP] AGENTS.md, ecosystem/**, tools/governance/** and audit artifacts through meta-gate` | `[KEEP] provider governance/merge/architecture workflows` | `[KEEP] Agent Governance, CI, historical-branch/prompt lifecycle checks` | `[KEEP] atlas/provenance gates plus extraction-provenance validators` |

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

### Product/migration objects

| Source/current object | Target / disposition | Current verdict |
| --- | --- | --- |
| `blakinio/Oteryn-v2` Game lineage | `Oteryn/Oteryn-Game`; legacy source archived | authority DONE; full migration completion UNKNOWN |
| `blakinio/Otheryn` bounded Atlas lineage | `Oteryn/Oteryn-Atlas`; source material historical/non-authoritative | selective extraction completion NOT DONE |
| transferred Platform identity | `Oteryn/Oteryn-Platform`, stable repo ID preserved | identity DONE; complete migration UNKNOWN |
| Platform transfer-cut backup | archived administrative repository | terminal disposition DONE |
| historical runner image/tag | immutable `ghcr.io/oteryn/...@sha256:f0c452...` | new supply chain DONE; legacy staging runner retired |
| Platform-owned Atlas execution | Atlas-owned local runner/workflows | DONE |
| Game local integration execution | Game-owned runner/workflow | DONE |

### Material documentation/agent file-path disposition

| Repository | Current file/path | Primary class | Target / disposition | Authority | Acceptance / evidence |
| --- | --- | --- | --- | --- | --- |
| META | `/AGENTS.md` | root AGENTS | `[KEEP]` current material family at owning repository authority | META | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| META | `docs/architecture/adr/**` | architecture/ADR | `[KEEP]` current material family at owning repository authority | META | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| META | `docs/governance/**` | governance policy | `[KEEP]` current material family at owning repository authority | META | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| META | `docs/ci/**` | CI policy | `[KEEP]` current material family at owning repository authority | META | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| META | `docs/testing/**` | test strategy | `[KEEP]` current material family at owning repository authority | META | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| META | `docs/recovery/**` | recovery/break-glass | `[KEEP]` current material family at owning repository authority | META | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| META | `ecosystem/**` | machine-readable policy companions | `[KEEP]` current material family at owning repository authority | META | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| META | `tools/governance/**` | documentation/agent validators | `[KEEP]` current material family at owning repository authority | META | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| META | `docs/agents/prompts/OTERYN-*.md` | one-shot prompts | `[KEEP]` historical/non-executable provenance only | META | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| META | `docs/evidence/**` | review evidence | `[KEEP]` retain under evidence/provenance policy; cannot broaden authority | META | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Game | `/AGENTS.md` | root AGENTS | `[KEEP]` current material family at owning repository authority | Game | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Game | `apps/game-server/AGENTS.md`; `crates/simulation-determinism/AGENTS.md`; `docs/agents/AGENTS.md` | nested AGENTS/override | `[KEEP]` current material family at owning repository authority | Game | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Game | `docs/architecture/**` | architecture/ADR | `[KEEP]` current material family at owning repository authority | Game | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Game | `docs/contracts/**`; `crates/platform-contracts/**` | contracts | `[KEEP]` current material family at owning repository authority | Game | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Game | `.github/repository-policy.json`; `docs/agents/GOVERNANCE_CONTRACT.json` | governance policy | `[KEEP]` current material family at owning repository authority | Game | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Game | `.github/workflows/**` | CI policy | `[KEEP]` current material family at owning repository authority | Game | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Game | `docs/agents/BUILD_TEST_MATRIX.md`; `tests/**` | test strategy | `[KEEP]` current material family at owning repository authority | Game | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Game | `docs/agents/prompts/**` | reusable prompts | `[KEEP/CLEANUP]` retained; per-file metadata verification gap `GAP-PROMPT-GAME-001` | Game | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Game | `docs/agents/tasks/{active,archive}/**` | task packets | `[KEEP/CLEANUP]` cache only; GitHub Issue/PR lifecycle remains authoritative | Game | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Game | `docs/agents/programs/**` | programmes | `[KEEP/CLEANUP]` cache only; GitHub Issue/PR lifecycle remains authoritative | Game | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Game | `docs/agents/evidence/**` | review evidence | `[KEEP]` retain under evidence/provenance policy; cannot broaden authority | Game | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Platform | `/AGENTS.md` | root AGENTS | `[KEEP]` current material family at owning repository authority | Platform | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Platform | `docs/agents/AGENTS.md` | nested AGENTS/override | `[KEEP]` current material family at owning repository authority | Platform | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Platform | `docs/architecture/adr/**` | architecture/ADR | `[KEEP]` current material family at owning repository authority | Platform | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Platform | `docs/contracts/**` | contracts | `[KEEP]` current material family at owning repository authority | Platform | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Platform | `docs/agents/GOVERNANCE_CONTRACT.json`; `BRANCH_LIFECYCLE_POLICY.json` | governance policy | `[KEEP]` current material family at owning repository authority | Platform | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Platform | `.github/workflows/**`; `docs/agents/CI_WORKFLOW_LIFECYCLE.*` | CI policy | `[KEEP]` current material family at owning repository authority | Platform | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Platform | `docs/testing/**`; `docs/agents/BUILD_TEST_MATRIX.md` | test strategy | `[KEEP]` current material family at owning repository authority | Platform | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Platform | `docs/agents/prompts/**` | reusable prompts | `[KEEP/CLEANUP]` retained; per-file lifecycle/metadata gap `GAP-PROMPT-PLATFORM-001` | Platform | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Platform | `docs/agents/tasks/active/**` | task packets | `[KEEP/CLEANUP]` cache only; GitHub Issue/PR lifecycle remains authoritative | Platform | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Platform | `docs/agents/programs/**` | programmes | `[KEEP/CLEANUP]` cache only; GitHub Issue/PR lifecycle remains authoritative | Platform | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Platform | `docs/operations/**`; `deploy/synology/**` | operations runbooks | `[KEEP]` current material family at owning repository authority | Platform | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Platform | `docs/agents/evidence/**` | review evidence | `[KEEP]` retain under evidence/provenance policy; cannot broaden authority | Platform | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Atlas | `/AGENTS.md` | root AGENTS | `[KEEP]` current material family at owning repository authority | Atlas | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Atlas | `docs/agents/prompts/**` | reusable prompts | `[KEEP/CLEANUP]` retained; per-file metadata gap `GAP-PROMPT-ATLAS-001` | Atlas | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Atlas | `docs/agents/tasks/{active,archive}/**` | task packets | `[KEEP/CLEANUP]` cache only; GitHub Issue/PR lifecycle remains authoritative | Atlas | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Atlas | `docs/evidence/**` | release evidence | `[KEEP]` retain under evidence/provenance policy; cannot broaden authority | Atlas | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Atlas | `docs/migration/**` | migration evidence | `[KEEP]` retain under evidence/provenance policy; cannot broaden authority | Atlas | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Atlas | `tools/governance/**` | documentation/agent validators | `[KEEP]` current material family at owning repository authority | Atlas | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Atlas | `README.md`; `SECURITY.md`; `e2e/README.md` | human reference docs | `[KEEP]` current material family at owning repository authority | Atlas | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| META | `docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md`; `docs/ci/CI_CONTRACT.md` | contracts | `[KEEP]` current material family at owning repository authority | META | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| META | `docs/governance/audits/**`; `docs/evidence/**`; `ecosystem/repositories.json` | migration evidence | `[KEEP]` retain under evidence/provenance policy; cannot broaden authority | META | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| META | `README.md`; `CONTRIBUTING.md`; `SECURITY.md`; `docs/**` | human reference docs | `[KEEP]` current material family at owning repository authority | META | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Game | historical prompt/task/evidence files under `docs/agents/tasks/archive/**` and `docs/agents/evidence/**` | one-shot prompts | `[KEEP]` historical/non-executable provenance only | Game | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Game | `docs/agents/CONTEXT_HANDOFF.md`; handoff evidence/reports | handovers | `[KEEP/CLEANUP]` cache only; GitHub Issue/PR lifecycle remains authoritative | Game | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Game | `docs/agents/EXECUTION_PROTOCOL.md`; `GITHUB_ONLY_EXECUTION.md`; related agent procedures | agent runbooks | `[KEEP]` current material family at owning repository authority | Game | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Game | `docs/architecture/ADR-0009-game-node-execution-capacity-deployment-and-recovery-baseline.md`; `docs/agents/SESSION_RECOVERY_AND_ORPHANED_EXECUTION.md` | recovery/break-glass | `[KEEP]` current material family at owning repository authority | Game | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Game | `docs/agents/evidence/OTV2-20260818-*`; migration ADRs | migration evidence | `[KEEP]` retain under evidence/provenance policy; cannot broaden authority | Game | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Game | `README.md`; `CONTRIBUTING.md`; `SECURITY.md`; provider docs | human reference docs | `[KEEP]` current material family at owning repository authority | Game | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Game | `.github/repository-policy.json`; `docs/agents/GOVERNANCE_CONTRACT.json`; `PROJECT_LANES.json` | machine-readable policy companions | `[KEEP]` current material family at owning repository authority | Game | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Game | `.github/workflows/agent-governance.yml`; `architecture-semantic-audit.yml`; `merge-gate.yml`; `repository-configuration.yml` | documentation/agent validators | `[KEEP]` current material family at owning repository authority | Game | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Platform | `docs/agents/CONTEXT_HANDOFF.md`; provider evidence handoffs | handovers | `[KEEP/CLEANUP]` cache only; GitHub Issue/PR lifecycle remains authoritative | Platform | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Platform | `docs/agents/**` execution/governance procedures | agent runbooks | `[KEEP]` current material family at owning repository authority | Platform | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Platform | `docs/operations/INCIDENT_RECOVERY_RUNBOOK.md`; `SYNOLOGY_ROLLBACK_SCHEMA_SAFETY.md`; `deploy/synology/scripts/rollback.sh`; `recover-schema.sh` | recovery/break-glass | `[KEEP]` current material family at owning repository authority | Platform | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Platform | `deploy/synology/release-contract.env`; release/deployment workflow evidence | release evidence | `[KEEP]` retain under evidence/provenance policy; cannot broaden authority | Platform | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Platform | provider migration/audit evidence; historical branch audit; META reconciliation | migration evidence | `[KEEP]` retain under evidence/provenance policy; cannot broaden authority | Platform | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Platform | `docs/agents/evidence/**/index.md`; machine-generated evidence manifests | generated docs/indexes | `[GENERATED]` regenerate from authoritative inputs; manual output remains non-authoritative | Platform | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Platform | `README.md`; `CONTRIBUTING.md`; `SECURITY.md`; `docs/**` | human reference docs | `[KEEP]` current material family at owning repository authority | Platform | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Platform | `docs/agents/*.json`; release/deployment contract data | machine-readable policy companions | `[KEEP]` current material family at owning repository authority | Platform | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Platform | `.github/workflows/agent-governance.yml`; `historical-branch-audit.yml`; prompt-eval/governance checks | documentation/agent validators | `[KEEP]` current material family at owning repository authority | Platform | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Atlas | `.github/workflows/ci.yml`; `extraction-provenance.yml`; `synology-live-acceptance.yml`; `synology-runner-health.yml` | CI policy | `[KEEP]` current material family at owning repository authority | Atlas | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Atlas | `docs/evidence/DYN-ATLAS-001-target-gui-execution-prompt.md` and bounded execution evidence | one-shot prompts | `[KEEP]` historical/non-executable provenance only | Atlas | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Atlas | `docs/evidence/ATLAS-FULLWORLD-PROGRAMME-LEDGER.md` | programmes | `[KEEP/CLEANUP]` cache only; GitHub Issue/PR lifecycle remains authoritative | Atlas | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Atlas | `docs/evidence/fullworld-generation/handoff-summary.json` | handovers | `[KEEP]` historical provenance; live Issue/PR/provider state supersedes | Atlas | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Atlas | `docs/agents/SYNOLOGY_DESKTOP_COMMANDER_ACCESS.md`; prompt/task routing docs | agent runbooks | `[KEEP]` current material family at owning repository authority | Atlas | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Atlas | `docs/evidence/ISSUE-*.md`; GitHub PR/review/check objects | review evidence | `[KEEP]` retain under evidence/provenance policy; cannot broaden authority | Atlas | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |
| Atlas | `web/semantic-search/index.json`; FullWorld generated evidence/index outputs | generated docs/indexes | `[GENERATED]` regenerate from authoritative inputs; manual output remains non-authoritative | Atlas | section 4 inventory + Matrix L; exact section-15 coverage enforced by terminal-report validator |

## 16. GitHub settings, protection and ruleset matrix

| Repository | Main protection | Required checks | Merge target | Live gap |
| --- | --- | --- | --- | --- |
| META | protected | `meta-gate`, `ai-review-gate` | stable | none in known protection contract |
| Game | protected/transition governance | `Merge gate / validate` | `game-gate` | transition not terminal |
| Platform | protected | `classify-changes`, `test` | `platform-gate` | transition not terminal |
| Atlas | protected | `atlas-gate`, `provenance-gate` | stable | none in known check contract |
| runner groups | organization control plane | selected-repository-only | exact one-provider repository each | direct ACL readback PASS |

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
3. Runner split closeout is terminal: Platform, Atlas and Game trusted-main acceptance passed, selected-repository ACLs were read back directly, no retained workflow requires `oteryn-staging`, and the legacy registration/container was retired with rollback state preserved.
4. Re-run full stale-coordinate/ref/tag/source-disposition checks.
5. Promote Game/Platform/Atlas migration verdicts only when every acceptance item has direct evidence.

No source or rollback object is removed merely because it looks old.

## 19. Ordered implementation backlog

### Programme/runner/migration backlog

| Order | Item | Owner | State / acceptance |
| ---: | --- | --- | --- |
| 1 | merge terminal desired-state/drift audit | META | DONE: PR #37 merged as `c0dbad93f791953d5efcc6b556e6be73693f0a4f` after exact-head `meta-gate` + `ai-review-gate` PASS |
| 2 | obtain Platform trusted-main diagnostics run/job readback | Platform | DONE: `32567509732` / `97018190282` |
| 3 | merge Game runner acceptance candidate through its provider policy | Game | DONE |
| 4 | run trusted-main Game acceptance | Game | DONE: `32566399984` / `97015531724` |
| 5 | read runner-group selected-repository ACLs | organization owner/control plane | DONE: exactly one provider repository per group |
| 6 | retire legacy staging runner after 2–5 PASS | organization/Platform | DONE: selector removed; runner deregistered; container removed; rollback state preserved |
| 7 | close migration-specific Game/Platform/Atlas evidence | each provider + META reconciliation | UNKNOWN/NO |
| 8 | implement recurring current-state recovery/control-plane/package/secret-owner recovery evidence | organization/providers | PARTIAL |
| 9 | terminalize stable `game-gate` / `platform-gate` transitions | Game/Platform | PARTIAL |
| 10 | re-run v3.10 final acceptance and close remaining Issues | META | blocked by preceding independent programme gaps |

### Mandatory documentation/agent implementation backlog

Every row contains the required v3.10 backlog fields. These are remediation items discovered by the audit; this META report does not mutate provider repositories.

| Order | Type | CURRENT_PATHS | TARGET_PATHS | AUTHORITY_OWNER | MIGRATION/DISPOSITION | BACKWARD_LINK_OR_REDIRECT_PLAN | ACCEPTANCE_CRITERIA | DETERMINISTIC_VALIDATION | ROLLBACK |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 11 | DOCUMENTATION_IA | Atlas lacks dedicated architecture/contracts/governance/test/operations/recovery policy paths; Matrix L GAPs | only provider-owned paths justified by recurring need; no empty taxonomy | Atlas | resolve `GAP-DOCS-ATLAS-ARCH-001`, `GAP-DOCS-ATLAS-CONTRACT-001`, `GAP-DOCS-ATLAS-GOV-001`, `GAP-DOCS-ATLAS-POLICY-001`, `GAP-DOCS-ATLAS-TEST-001` with evidence-backed KEEP/OPTIONAL/NOT_NEEDED decisions | retain existing evidence/README links until replacement authority is merged; no blind moves | every Atlas Matrix L UNKNOWN either becomes evidence-backed canonical target or explicit NOT_NEEDED | provider tree inventory + Matrix L validator + Atlas gate | revert documentation-only PR; existing provider evidence remains authority until successor merge |
| 12 | AGENT_INSTRUCTION | Platform `/AGENTS.md` 22,157-byte live baseline; Game nested AGENTS; current provider roots | short durable root plus bounded path-scoped nested AGENTS only where justified | each provider | compact transient/repeated procedure text without changing runtime authority | preserve anchors/links from moved procedures; live root remains authority until replacement merge | no transient task/PR/head state in root; context budget measured; effective chain documented | root/nested AGENTS inventory + provider Agent Governance | revert instruction-only PR; no product behavior changes |
| 13 | PROMPT_LIFECYCLE | Game/Platform/Atlas `docs/agents/prompts/**`; META executor prompts historical | one canonical provider/user scope; historical one-shot prompts status-marked or archived | owning provider/META | close `GAP-PROMPT-GAME-001`, `GAP-PROMPT-PLATFORM-001`, `GAP-PROMPT-ATLAS-001`, `GAP-DOCS-PLATFORM-PROMPT-001` | preserve historical prompt IDs and links; do not rewrite completed provenance | every retained reusable prompt has stable ID/version/status/owner; one-shot terminal prompts non-executable | prompt metadata/lifecycle validator in owning repo | restore prior prompt file from Git history; no runtime rollback needed |
| 14 | TASK_LIFECYCLE | Game/Platform/Atlas active task packet trees; GitHub Issues | GitHub Issue lifecycle authority + optional active packet cache; archive/delete on terminal Issue | owning provider | close `GAP-TASK-GAME-001`, `GAP-TASK-PLATFORM-001`, `GAP-TASK-ATLAS-001`, `GAP-HANDOVER-GAME-001`, `GAP-HANDOVER-PLATFORM-001` | keep Issue/PR links from archived packets; no second status database | every active packet names owning Issue and acceptance; no packet stays active after terminal Issue | task-liveness/Issue-link validator + branch/PR reconciliation | restore packet from Git history if provenance needed; Issue remains authority |
| 15 | RUNBOOK | Game/Atlas recurring local runner/publication/recovery procedures are not fully classified; Platform `docs/operations/**` established | provider-owned operations/recovery runbooks only for recurring procedures | owning provider | resolve `GAP-DOCS-GAME-OPS-001`, `GAP-DOCS-ATLAS-OPS-001`, `GAP-DOCS-ATLAS-RECOVERY-001` | old evidence pages retain links until a runbook successor is merged | recurring procedure has one owner, preconditions, safety boundary, validation and rollback; otherwise mark NOT_NEEDED | provider docs validator + representative operation/recovery test where applicable | revert runbook-only PR; operational state is not mutated by docs migration |
| 16 | EVIDENCE_GOVERNANCE | META `docs/evidence/**`; Game/Platform agent evidence; Atlas evidence/migration | owning evidence paths with subject/source/time/identity/digest/retention metadata | owning repo; META reconciles cross-repo evidence | close `GAP-DOCS-GAME-RELEASE-001`; retain unique provenance; archive superseded evidence; never broaden authority | keep immutable GitHub object links and historical IDs | every retained evidence class has explicit retention/disposition; sanitized secrets boundary preserved | evidence metadata/digest validator; terminal report validator | recover from Git history/GitHub object; never recreate secret values from metadata |
| 17 | DOCS_CI | META meta-gate; provider governance/agent/provenance checks vary | deterministic checks in existing provider gates; no new external required check unless separately governed | owning repo | enforce canonical path/class/metadata/lifecycle invariants where high-signal | preserve existing required check names; add internal subchecks first | invariant violations fail existing stable gate or produce explicit GAP/UNKNOWN; no empty taxonomy generation | `tools/governance/validate_v310_terminal_report.py` in META + provider-local validators | revert internal subcheck while preserving stable required gate identity |

## 20. Owner decisions

Decisions that cannot be invented by an autonomous audit:
- whether/when provider policy may authorize paid/metered AI review in Game;
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

The architecture is coherent and the runner/control-plane workstream is terminal; the programme is not terminally complete while independent migration/recovery evidence remains UNKNOWN/PARTIAL/NO.

# Matrix A0–L — execution coverage ledger

The labels below are the v3.10 completeness index used by this execution. They do not rename or retroactively alter the historical v3.9 result; they identify the evidence family exercised by this report.

| Matrix | Evidence family | State | Key result |
| --- | --- | --- | --- |
| A0 | scope, access and evidence coherence | PARTIAL | permanent repos and runner control plane inspected; independent migration/recovery evidence remains incomplete |
| A | repository identity and topology | DONE | four permanent authorities and admin backup identity verified |
| B | authority/source-of-truth | DONE | META/provider/GitHub-native authority boundaries explicit |
| C | migration/source retirement | NOT DONE | Game/Platform UNKNOWN; Atlas NO |
| D | branch protection/merge governance | PARTIAL | stable META/Atlas; Game/Platform transitions remain |
| E | CI/check architecture | PARTIAL | stable identities plus transition targets recorded |
| F | test/runtime acceptance | PARTIAL | Platform/Atlas/Game runner replacement acceptance PASS; broader migration-mode acceptance remains incomplete |
| G | security/dependency/supply chain | PARTIAL | immutable runner supply chain; remaining governance warnings/gaps |
| H | agents/Codex/instruction loading | PARTIAL | durable model defined; provider-wide final hygiene not fully re-proved here |
| I | documentation/source ownership | DONE | central-vs-provider ownership defined without duplicate mutable authority |
| J | task/prompt/handover/evidence lifecycle | PARTIAL | runner lifecycle tasks terminalized; broader stale-task/PR cleanup remains successor-dependent |
| K | recovery/break-glass | PARTIAL | historical transfer cut PASS; current org recovery gaps remain |
| L | Documentation & Agent IA | PARTIAL | full Matrix L/H14 present; G11 cannot PASS while terminal blockers remain |

# H1-H14 - inherited regression hypothesis ledger

Inherited H1-H13 wording is restored from `OTERYN-ORG-GOVERNANCE-ARCHITECTURE-ULTRA-AUDIT-v3.9-EXECUTION-OPTIMIZED-FINAL` (recovered source copy SHA-256 `653955e655d6cf1b6c77f0ba1ccdfa9044b0d9b3b12b59398809de2bfc20bce4`). PR #8 preserves the validated v3.9 baseline and historical report SHA-256 `f9d9378623bff987f102e972ab6ae264f12d4f2f704c1b5e6c8d30eebffbb41a`. H14 is the v3.10 addendum hypothesis.

| ID | Hypothesis to reverify | Verdict | Current evidence / limitation |
| --- | --- | --- | --- |
| H1 | Platform stable ID `1305155726` transferred from `blakinio/Oteryn-Platform` to `Oteryn/Oteryn-Platform`; temporary migration backup existed. | CONFIRMED | Stable ID/transfer and archived backup are directly reconciled; full Platform migration acceptance remains `UNKNOWN`. |
| H2 | META still contained old Platform coordinate/NO_GO around cutover. | RESOLVED | Current META manifests/desired state use `Oteryn/Oteryn-Platform`; old coordinate is historical provenance only. |
| H3 | Game/Oteryn-v2 had same-directory `AGENTS.md` + `AGENTS.override.md` while prose treated them as sequential. | RESOLVED | No `AGENTS.override.md` exists in any current permanent target tree; Game nested AGENTS are path-scoped and the legacy source is archived. |
| H4 | Game/Platform bootstrap policy was large. | CONFIRMED | Live root AGENTS sizes: Game 3,267 bytes; Platform 22,157 bytes. Platform bootstrap remains materially large. |
| H5 | Permanent instructions contained transient task/migration state. | CHANGED | Candidate META removes open runner-migration state and keeps a durable retired-runner prohibition; provider roots retain only bounded migration/history rules where inspected. |
| H6 | Game/Platform/Atlas had repeated final/v2/v3/restack/noop/tmp branch families. | CONFIRMED | Live branch readback still shows Game `final/noop/tmp` families, Atlas `noop-*`, and META multiple `final/r2/terminal` audit branches; cleanup is not terminal. |
| H7 | Markdown policy could differ from effective GitHub enforcement. | CONFIRMED | Game/Platform required checks remain in explicit transition states while target gate names differ; live-state auditor treats that drift separately from prose. |
| H8 | Mutable work state was duplicated across tasks/programmes/PR prose/manifests. | CONFIRMED | Game/Platform still retain active task/programme/prompt structures plus GitHub lifecycle objects; successor cleanup remains required. |
| H9 | Oteryn-v2 HEAD was an ancestor of Game; sampled Game was +14/-0. | CHANGED | Historical lineage remains provenance, but Game has advanced and `blakinio/Oteryn-v2` is archived; the sampled +14/-0 relation is no longer a current head delta. |
| H10 | No migrated product repo had repo-scoped `.codex/config.toml`. | CONFIRMED | Direct current-tree readback finds no `.codex/config.toml` in META, Game, Platform or Atlas. |
| H11 | Repeated procedures lived as large Markdown policies. | CONFIRMED | Game and Platform retain substantial `docs/agents/**` procedure surfaces; reclassification/compaction is not terminal. |
| H12 | Platform workflow surface was broad; Game/Atlas also had migration/proof workflows. | CONFIRMED | Current workflow counts are Platform 53, Game 14 and Atlas 9; proof/acceptance workflows remain present even after runner migration closeout. |
| H13 | Old/new coordinates could both appear authoritative during cutover. | CHANGED | Current authority graph makes Oteryn targets authoritative and old coordinates historical, but exhaustive stale-coordinate/source-disposition proof remains a migration gate. |
| H14 | Organization-wide documentation/agent IA lacked fully explicit canonical paths, classes, metadata, retention, duplication rules, evidence placement and deterministic enforcement. | CHANGED | v3.10 now defines target IA and full Matrix L coverage, while explicit provider GAP-IDs preserve missing/unfinished classes instead of asserting completion. |

# G1-G11 - final audit gates

The final-gate state vocabulary is exactly `PASS`, `FAIL`, or `UNKNOWN (GAP-ID: missing evidence)`. `FAIL` means a required condition is directly known not to be satisfied; `UNKNOWN` means required proof is unavailable/incomplete.

| Gate | State | Reason |
| --- | --- | --- |
| G1 Codex/instructions | UNKNOWN (GAP-CODEX-001: current product-wide effective instruction/context-load and `project_doc_max_bytes` behavior not exhaustively reverified) | Sections 6-7 define the model; current trees were inspected, but the complete runtime/context-budget proof required by v3.9 G1 is missing. |
| G2 Lifecycle/concurrency/hygiene | FAIL | Known stale branch/PR/task families remain: Game has 41 branches including `final/noop/tmp`; META and Atlas also retain superseded audit/probe branches pending successor cleanup. |
| G3 Architecture/contracts | UNKNOWN (GAP-CONTRACT-001: provider-wide contract owner/fixture/test/version/supersession inventory not exhaustively reverified) | Authority boundaries are explicit, but the full provider contract-evidence inventory required by v3.9 G3 is not complete. |
| G4 GitHub/control plane | UNKNOWN (GAP-GH-CONTROL-001: remaining identity-sensitive Apps/webhooks/audit-log/environment surfaces and Game/Platform stable-gate transitions lack terminal proof) | Runner ACLs are PASS and META/Atlas gates are stable; other required control-plane surfaces remain incomplete. |
| G5 `.github`/CI/tests/security | UNKNOWN (GAP-CI-SECURITY-001: provider release/security completeness plus current recurring backup/restore proof is incomplete) | Runner trust/supply-chain proof is terminal, but v3.9 G5 also requires release and backup/restore state that is not fully proven. |
| G6 Drift/migration | UNKNOWN (GAP-MIGRATION-001: Game/Platform completion evidence is missing and exhaustive stale-coordinate/ref/source disposition is not closed) | META drift checks are deterministic; the migration evidence family remains non-terminal. |
| G7 Three migrated product lines | FAIL | Game and Platform remain `MIGRATION_COMPLETE=UNKNOWN`; Atlas remains `MIGRATION_COMPLETE=NO`. |
| G8 Oteryn regressions | PASS | The inherited H1-H13 ledger is restored below and each hypothesis has an explicit current `CONFIRMED|RESOLVED|CHANGED|UNKNOWN` verdict. |
| G9 Implementation readiness | PASS | Sections 17-20 provide ordered backlog, safe sequencing, owner decisions, rollback constraints and non-goals; runner implementation is already terminal. |
| G10 Deliverable integrity | PASS | The candidate contains 21 required report sections, Matrix A0-L, restored H1-H14 ledger, G1-G11, three migration verdicts and a new mechanical terminal-report validation record. |
| G11 Documentation/agent IA | UNKNOWN (GAP-DOCS-IA-001: Matrix L exposes unresolved provider classes, especially Atlas architecture/contracts/governance/test/recovery and selected Game/Platform prompt/operations/release classifications) | Matrix L explicitly covers every required class for all four permanent repositories; unresolved classes are GAP-ID entries, not empty cells. |

# Matrix L - Documentation & Agent Information Architecture

Every mandatory 29L artifact class is represented for every permanent repository. `NOT_NEEDED`/`NOT_APPLICABLE` are intentional dispositions; `UNKNOWN (GAP-ID: ...)` constrains G11 and is never treated as PASS. Live-tree evidence baseline: META `c0dbad93`, Game `fd39c6aa`, Platform `8e609f05`, Atlas `a1b5fea1`; META PR #43 candidate paths are identified separately where not yet on main.

| Repository | Artifact class | Current path(s) | Canonical target path / GitHub object | Authority owner | Consumer | Required metadata | Lifecycle / retention | Local copy / override rule | CI / drift enforcement | Migration action | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| META | root AGENTS | `/AGENTS.md` | `/AGENTS.md` | META | agents/humans/CI as applicable | scope; precedence; durable status | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | `meta-gate` / protected review | KEEP | live tree `c0dbad93` |
| META | nested AGENTS/override | `NOT_NEEDED` - current tree has no nested/override file | `NOT_NEEDED` | META | agents/humans/CI as applicable | scope; precedence; durable status | NOT_NEEDED | NOT_NEEDED | `meta-gate` / protected review | NOT_NEEDED | live tree `c0dbad93` |
| META | architecture/ADR | `docs/architecture/adr/**` | `docs/architecture/adr/**` | META | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | `meta-gate` / protected review | KEEP | live tree `c0dbad93` |
| META | contracts | `docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md`; `docs/ci/CI_CONTRACT.md` | `docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md`; `docs/ci/CI_CONTRACT.md` | META | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | `meta-gate` / protected review | KEEP | live tree `c0dbad93` |
| META | governance policy | `docs/governance/AI_REVIEW_POLICY.md`; ADR 0002 | `docs/governance/AI_REVIEW_POLICY.md`; ADR 0002 | META | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | `meta-gate` / protected review | KEEP | live tree `c0dbad93` |
| META | CI policy | `docs/ci/CI_CONTRACT.md`; `.github/workflows/ci.yml`; governance AI workflows | `docs/ci/CI_CONTRACT.md`; `.github/workflows/ci.yml`; governance AI workflows | META | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | `meta-gate` / protected review | KEEP | live tree `c0dbad93` |
| META | test strategy | `docs/testing/ECOSYSTEM_TEST_STRATEGY.md` | `docs/testing/ECOSYSTEM_TEST_STRATEGY.md` | META | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | `meta-gate` / protected review | KEEP | live tree `c0dbad93` |
| META | reusable prompts | `NOT_NEEDED` - no active META reusable prompt set in steady state | `NOT_NEEDED` | META | agents/humans/CI as applicable | stable ID; scope; status; supersession | NOT_NEEDED | NOT_NEEDED | `meta-gate` / protected review | NOT_NEEDED | live tree `c0dbad93` |
| META | one-shot prompts | `docs/agents/prompts/OTERYN-*.md` in PR #43, explicitly historical | historical provenance only | META | agents/humans/CI as applicable | stable ID; scope; status; supersession | historical retained by provenance rule | no independently edited cross-repo authority copy; declared path-scoped override only | `meta-gate` / protected review | ARCHIVE | PR #43 candidate |
| META | task packets | `NOT_NEEDED` at terminal closeout; Issue/PR owns lifecycle | optional `docs/agents/tasks/**` only when a future task needs detail | META | agents/humans/CI as applicable | Issue/PR link; owner; status; supersession/time | NOT_NEEDED | NOT_NEEDED | `meta-gate` / protected review | NOT_NEEDED | live tree `c0dbad93` |
| META | programmes | `NOT_NEEDED` for current META steady state | GitHub Issues unless a future programme requires a durable packet | META | agents/humans/CI as applicable | Issue/PR link; owner; status; supersession/time | NOT_NEEDED | NOT_NEEDED | `meta-gate` / protected review | NOT_NEEDED | live tree `c0dbad93` |
| META | handovers | `NOT_NEEDED` at terminal closeout | GitHub Issue/PR plus expiring cache only when needed | META | agents/humans/CI as applicable | Issue/PR link; owner; status; supersession/time | NOT_NEEDED | NOT_NEEDED | `meta-gate` / protected review | NOT_NEEDED | live tree `c0dbad93` |
| META | agent runbooks | `NOT_NEEDED` - root AGENTS plus execution-access contract route current META agent behavior | `NOT_NEEDED` until a reusable operational procedure is proven | META | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | NOT_NEEDED | NOT_NEEDED | `meta-gate` / protected review | NOT_NEEDED | live tree `c0dbad93` |
| META | operations runbooks | `NOT_APPLICABLE` - META has no product operations runtime | `NOT_APPLICABLE` | META | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | NOT_APPLICABLE | NOT_APPLICABLE | `meta-gate` / protected review | NOT_APPLICABLE | live tree `c0dbad93` |
| META | recovery/break-glass | `docs/recovery/organization-recovery-contract.md` | `docs/recovery/organization-recovery-contract.md` | META | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | `meta-gate` / protected review | KEEP | live tree `c0dbad93` |
| META | review evidence | GitHub PR/review/check objects; `docs/evidence/**` | GitHub objects plus durable sanitized evidence | META | agents/humans/CI as applicable | subject; source; identity; time; digest/retention where applicable | append/retain by evidence or migration provenance policy | copy may preserve provenance; must not broaden authority | `meta-gate` / protected review | KEEP | PR #43 / AI review verifier |
| META | release evidence | `NOT_NEEDED` - META owns composition policy, provider releases own release evidence | provider GitHub Releases/evidence | META | agents/humans/CI as applicable | subject; source; identity; time; digest/retention where applicable | NOT_NEEDED | NOT_NEEDED | `meta-gate` / protected review | NOT_NEEDED | live tree `c0dbad93` |
| META | migration evidence | `docs/governance/audits/**`; `docs/evidence/**`; `ecosystem/repositories.json` | `docs/governance/audits/**`; `docs/evidence/**`; `ecosystem/repositories.json` | META | agents/humans/CI as applicable | subject; source; identity; time; digest/retention where applicable | append/retain by evidence or migration provenance policy | copy may preserve provenance; must not broaden authority | `meta-gate` / protected review | KEEP | live tree `c0dbad93` |
| META | generated docs/indexes | `NOT_NEEDED` - no generated documentation is normative META authority | `NOT_NEEDED` | META | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | NOT_NEEDED | NOT_NEEDED | `meta-gate` / protected review | NOT_NEEDED | live tree `c0dbad93` |
| META | human reference docs | `README.md`; `CONTRIBUTING.md`; `SECURITY.md`; `docs/**` | `README.md`; `CONTRIBUTING.md`; `SECURITY.md`; `docs/**` | META | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | `meta-gate` / protected review | KEEP | live tree `c0dbad93` |
| META | machine-readable policy companions | `ecosystem/*.json`; `.github/dependabot.yml` | `ecosystem/*.json`; `.github/dependabot.yml` | META | agents/humans/CI as applicable | schema/version; owner; exact identities | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | `meta-gate` / protected review | KEEP | live tree `c0dbad93` |
| META | documentation/agent validators | `tools/governance/**`; `.github/workflows/ci.yml`; governance AI workflows | `tools/governance/**`; `.github/workflows/ci.yml`; governance AI workflows | META | agents/humans/CI as applicable | inputs; version; fail-closed result | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | `meta-gate` / protected review | KEEP | live tree `c0dbad93` |
| Game | root AGENTS | `/AGENTS.md` | `/AGENTS.md` | Game | agents/humans/CI as applicable | scope; precedence; durable status | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | Game governance/merge gates | KEEP | live tree `fd39c6aa` |
| Game | nested AGENTS/override | `apps/game-server/AGENTS.md`; `crates/simulation-determinism/AGENTS.md`; `docs/agents/AGENTS.md`; no override file | `apps/game-server/AGENTS.md`; `crates/simulation-determinism/AGENTS.md`; `docs/agents/AGENTS.md`; no override file | Game | agents/humans/CI as applicable | scope; precedence; durable status | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | Game governance/merge gates | KEEP | live tree `fd39c6aa` |
| Game | architecture/ADR | `docs/architecture/ADR-*.md` | `docs/architecture/ADR-*.md` | Game | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | Game governance/merge gates | KEEP | live tree `fd39c6aa` |
| Game | contracts | `docs/contracts/**`; `crates/platform-contracts/**` | `docs/contracts/**`; `crates/platform-contracts/**` | Game | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | Game governance/merge gates | KEEP | live tree `fd39c6aa` |
| Game | governance policy | `.github/repository-policy.json`; `docs/agents/GOVERNANCE_CONTRACT.json`; `docs/agents/OWNER_FUNDED_AI_POLICY.md` | `.github/repository-policy.json`; `docs/agents/GOVERNANCE_CONTRACT.json`; `docs/agents/OWNER_FUNDED_AI_POLICY.md` | Game | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | Game governance/merge gates | KEEP | live tree `fd39c6aa` |
| Game | CI policy | `.github/workflows/merge-gate.yml`; `agent-governance.yml`; `repository-configuration.yml` | `.github/workflows/merge-gate.yml`; `agent-governance.yml`; `repository-configuration.yml` | Game | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | Game governance/merge gates | KEEP | live tree `fd39c6aa` |
| Game | test strategy | `docs/agents/BUILD_TEST_MATRIX.md`; provider `tests/**` | `docs/agents/BUILD_TEST_MATRIX.md`; provider `tests/**` | Game | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | Game governance/merge gates | KEEP | live tree `fd39c6aa` |
| Game | reusable prompts | `docs/agents/prompts/**`; `PROMPTING_STANDARD.md`; `PROMPT_EVAL_STANDARD.md` | `docs/agents/prompts/**`; `PROMPTING_STANDARD.md`; `PROMPT_EVAL_STANDARD.md` | Game | agents/humans/CI as applicable | stable ID; scope; status; supersession | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | Game governance/merge gates | KEEP | live tree `fd39c6aa` |
| Game | one-shot prompts | historical prompt/task/evidence files under `docs/agents/tasks/archive/**` and `docs/agents/evidence/**` | historical archive only | Game | agents/humans/CI as applicable | stable ID; scope; status; supersession | historical retained by provenance rule | no independently edited cross-repo authority copy; declared path-scoped override only | Game governance/merge gates | ARCHIVE | live tree `fd39c6aa` |
| Game | task packets | `docs/agents/tasks/active/**`; `docs/agents/tasks/archive/**` | Issue authority plus provider packet cache | Game | agents/humans/CI as applicable | Issue/PR link; owner; status; supersession/time | active only while linked lifecycle is live; archive/delete on supersession | cache only; GitHub Issue/PR/live state outranks it | Game governance/merge gates | KEEP/CLEANUP | live tree `fd39c6aa` |
| Game | programmes | `docs/agents/programs/**` | Issue authority plus programme cache | Game | agents/humans/CI as applicable | Issue/PR link; owner; status; supersession/time | active only while linked lifecycle is live; archive/delete on supersession | cache only; GitHub Issue/PR/live state outranks it | Game governance/merge gates | KEEP/CLEANUP | live tree `fd39c6aa` |
| Game | handovers | `docs/agents/CONTEXT_HANDOFF.md`; handoff evidence/reports | expiring cache linked to Issue/PR | Game | agents/humans/CI as applicable | Issue/PR link; owner; status; supersession/time | active only while linked lifecycle is live; archive/delete on supersession | cache only; GitHub Issue/PR/live state outranks it | Game governance/merge gates | KEEP/CLEANUP | live tree `fd39c6aa` |
| Game | agent runbooks | `docs/agents/EXECUTION_PROTOCOL.md`; `GITHUB_ONLY_EXECUTION.md`; related agent procedures | `docs/agents/EXECUTION_PROTOCOL.md`; `GITHUB_ONLY_EXECUTION.md`; related agent procedures | Game | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | Game governance/merge gates | KEEP | live tree `fd39c6aa` |
| Game | operations runbooks | `UNKNOWN (GAP-DOCS-GAME-OPS-001: no docs/operations path despite local runtime/integration workload)` | provider-owned operations runbook if the live workload requires one | Game | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | Game governance/merge gates | UNKNOWN | live tree `fd39c6aa` |
| Game | recovery/break-glass | `docs/architecture/ADR-0009-game-node-execution-capacity-deployment-and-recovery-baseline.md`; `docs/agents/SESSION_RECOVERY_AND_ORPHANED_EXECUTION.md` | `docs/architecture/ADR-0009-game-node-execution-capacity-deployment-and-recovery-baseline.md`; `docs/agents/SESSION_RECOVERY_AND_ORPHANED_EXECUTION.md` | Game | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | Game governance/merge gates | KEEP | live tree `fd39c6aa` |
| Game | review evidence | `docs/agents/evidence/**`; GitHub PR/review/check objects | `docs/agents/evidence/**`; GitHub PR/review/check objects | Game | agents/humans/CI as applicable | subject; source; identity; time; digest/retention where applicable | append/retain by evidence or migration provenance policy | copy may preserve provenance; must not broaden authority | Game governance/merge gates | KEEP | live tree `fd39c6aa` |
| Game | release evidence | `UNKNOWN (GAP-DOCS-GAME-RELEASE-001: no dedicated release-evidence path located in current tree)` | provider GitHub Release/evidence authority when release flow is terminalized | Game | agents/humans/CI as applicable | subject; source; identity; time; digest/retention where applicable | append/retain by evidence or migration provenance policy | copy may preserve provenance; must not broaden authority | Game governance/merge gates | UNKNOWN | live tree `fd39c6aa` |
| Game | migration evidence | migration ADRs plus `docs/agents/evidence/**`; META migration manifest links | provider evidence plus META reconciliation | Game | agents/humans/CI as applicable | subject; source; identity; time; digest/retention where applicable | append/retain by evidence or migration provenance policy | copy may preserve provenance; must not broaden authority | Game governance/merge gates | KEEP | live tree `fd39c6aa` |
| Game | generated docs/indexes | `NOT_NEEDED` for normative docs; generated product exports are provider artifacts | `NOT_NEEDED` as documentation authority | Game | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | NOT_NEEDED | NOT_NEEDED | Game governance/merge gates | NOT_NEEDED | live tree `fd39c6aa` |
| Game | human reference docs | `README.md`; `CONTRIBUTING.md`; `SECURITY.md`; provider docs | `README.md`; `CONTRIBUTING.md`; `SECURITY.md`; provider docs | Game | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | Game governance/merge gates | KEEP | live tree `fd39c6aa` |
| Game | machine-readable policy companions | `.github/repository-policy.json`; `docs/agents/GOVERNANCE_CONTRACT.json`; `PROJECT_LANES.json` | `.github/repository-policy.json`; `docs/agents/GOVERNANCE_CONTRACT.json`; `PROJECT_LANES.json` | Game | agents/humans/CI as applicable | schema/version; owner; exact identities | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | Game governance/merge gates | KEEP | live tree `fd39c6aa` |
| Game | documentation/agent validators | `.github/workflows/agent-governance.yml`; `architecture-semantic-audit.yml`; `merge-gate.yml`; `repository-configuration.yml` | `.github/workflows/agent-governance.yml`; `architecture-semantic-audit.yml`; `merge-gate.yml`; `repository-configuration.yml` | Game | agents/humans/CI as applicable | inputs; version; fail-closed result | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | Game governance/merge gates | KEEP | live tree `fd39c6aa` |
| Platform | root AGENTS | `/AGENTS.md` | `/AGENTS.md` | Platform | agents/humans/CI as applicable | scope; precedence; durable status | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | Platform CI / Agent Governance | KEEP | live tree `8e609f05` |
| Platform | nested AGENTS/override | `docs/agents/AGENTS.md`; no override file | `docs/agents/AGENTS.md`; no override file | Platform | agents/humans/CI as applicable | scope; precedence; durable status | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | Platform CI / Agent Governance | KEEP | live tree `8e609f05` |
| Platform | architecture/ADR | `docs/architecture/adr/**` | `docs/architecture/adr/**` | Platform | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | Platform CI / Agent Governance | KEEP | live tree `8e609f05` |
| Platform | contracts | `docs/contracts/**`; deployment contract files | `docs/contracts/**`; deployment contract files | Platform | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | Platform CI / Agent Governance | KEEP | live tree `8e609f05` |
| Platform | governance policy | `docs/agents/GOVERNANCE_CONTRACT.json`; `BRANCH_LIFECYCLE_POLICY.json`; durable root/nested AGENTS | `docs/agents/GOVERNANCE_CONTRACT.json`; `BRANCH_LIFECYCLE_POLICY.json`; durable root/nested AGENTS | Platform | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | Platform CI / Agent Governance | KEEP | live tree `8e609f05` |
| Platform | CI policy | `docs/agents/CI_WORKFLOW_LIFECYCLE.md`; `CI_WORKFLOW_LIFECYCLE.json`; `CI_COVERAGE_POLICY.json`; `.github/workflows/ci.yml` | `docs/agents/CI_WORKFLOW_LIFECYCLE.md`; `CI_WORKFLOW_LIFECYCLE.json`; `CI_COVERAGE_POLICY.json`; `.github/workflows/ci.yml` | Platform | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | Platform CI / Agent Governance | KEEP | live tree `8e609f05` |
| Platform | test strategy | `docs/testing/**`; `docs/agents/BUILD_TEST_MATRIX.md` | `docs/testing/**`; `docs/agents/BUILD_TEST_MATRIX.md` | Platform | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | Platform CI / Agent Governance | KEEP | live tree `8e609f05` |
| Platform | reusable prompts | `docs/agents/prompts/**` | provider prompt library after status/classification cleanup | Platform | agents/humans/CI as applicable | stable ID; scope; status; supersession | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | Platform CI / Agent Governance | KEEP/CLEANUP | live tree `8e609f05` |
| Platform | one-shot prompts | `UNKNOWN (GAP-DOCS-PLATFORM-PROMPT-001: 22 provider prompt files are not exhaustively classified reusable vs one-shot/status)` | historical one-shot prompts archived or deleted; reusable prompts status-marked | Platform | agents/humans/CI as applicable | stable ID; scope; status; supersession | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | Platform CI / Agent Governance | UNKNOWN | live tree `8e609f05` |
| Platform | task packets | `docs/agents/tasks/active/**`; archived task packets | Issue authority plus provider packet cache | Platform | agents/humans/CI as applicable | Issue/PR link; owner; status; supersession/time | active only while linked lifecycle is live; archive/delete on supersession | cache only; GitHub Issue/PR/live state outranks it | Platform CI / Agent Governance | KEEP/CLEANUP | live tree `8e609f05` |
| Platform | programmes | `docs/agents/programs/**`; `OTERYN_PLATFORM_PROGRAM_SCOPE.md` | Issue authority plus programme cache | Platform | agents/humans/CI as applicable | Issue/PR link; owner; status; supersession/time | active only while linked lifecycle is live; archive/delete on supersession | cache only; GitHub Issue/PR/live state outranks it | Platform CI / Agent Governance | KEEP/CLEANUP | live tree `8e609f05` |
| Platform | handovers | `docs/agents/CONTEXT_HANDOFF.md`; provider evidence handoffs | expiring cache linked to live Issue/PR | Platform | agents/humans/CI as applicable | Issue/PR link; owner; status; supersession/time | active only while linked lifecycle is live; archive/delete on supersession | cache only; GitHub Issue/PR/live state outranks it | Platform CI / Agent Governance | KEEP/CLEANUP | live tree `8e609f05` |
| Platform | agent runbooks | `docs/agents/**` execution/governance procedures | smaller routed agent runbooks/skills where reusable | Platform | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | Platform CI / Agent Governance | KEEP/CLEANUP | live tree `8e609f05` |
| Platform | operations runbooks | `docs/operations/**`; `deploy/synology/README.md` | `docs/operations/**`; `deploy/synology/README.md` | Platform | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | Platform CI / Agent Governance | KEEP | live tree `8e609f05` |
| Platform | recovery/break-glass | `docs/operations/INCIDENT_RECOVERY_RUNBOOK.md`; `SYNOLOGY_ROLLBACK_SCHEMA_SAFETY.md`; `deploy/synology/scripts/rollback.sh`; `recover-schema.sh` | `docs/operations/INCIDENT_RECOVERY_RUNBOOK.md`; `SYNOLOGY_ROLLBACK_SCHEMA_SAFETY.md`; `deploy/synology/scripts/rollback.sh`; `recover-schema.sh` | Platform | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | Platform CI / Agent Governance | KEEP | live tree `8e609f05` |
| Platform | review evidence | `docs/agents/evidence/**`; GitHub PR/review/check objects | `docs/agents/evidence/**`; GitHub PR/review/check objects | Platform | agents/humans/CI as applicable | subject; source; identity; time; digest/retention where applicable | append/retain by evidence or migration provenance policy | copy may preserve provenance; must not broaden authority | Platform CI / Agent Governance | KEEP | live tree `8e609f05` |
| Platform | release evidence | `deploy/synology/release-contract.env`; release/deployment workflow evidence | provider release/deployment objects plus immutable provenance | Platform | agents/humans/CI as applicable | subject; source; identity; time; digest/retention where applicable | append/retain by evidence or migration provenance policy | copy may preserve provenance; must not broaden authority | Platform CI / Agent Governance | KEEP | live tree `8e609f05` |
| Platform | migration evidence | provider migration/audit evidence; historical branch audit; META reconciliation | provider evidence plus META migration authority | Platform | agents/humans/CI as applicable | subject; source; identity; time; digest/retention where applicable | append/retain by evidence or migration provenance policy | copy may preserve provenance; must not broaden authority | Platform CI / Agent Governance | KEEP/CLEANUP | live tree `8e609f05` |
| Platform | generated docs/indexes | `docs/agents/evidence/**/index.md`; machine-generated evidence manifests | generator-owned evidence/index outputs | Platform | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | regenerate from authoritative inputs; output non-authoritative unless promoted | no independently edited cross-repo authority copy; declared path-scoped override only | Platform CI / Agent Governance | GENERATED | live tree `8e609f05` |
| Platform | human reference docs | `README.md`; `CONTRIBUTING.md`; `SECURITY.md`; `docs/**` | `README.md`; `CONTRIBUTING.md`; `SECURITY.md`; `docs/**` | Platform | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | Platform CI / Agent Governance | KEEP | live tree `8e609f05` |
| Platform | machine-readable policy companions | `docs/agents/*.json`; release/deployment contract data | `docs/agents/*.json`; release/deployment contract data | Platform | agents/humans/CI as applicable | schema/version; owner; exact identities | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | Platform CI / Agent Governance | KEEP | live tree `8e609f05` |
| Platform | documentation/agent validators | `.github/workflows/agent-governance.yml`; `historical-branch-audit.yml`; prompt-eval/governance checks | `.github/workflows/agent-governance.yml`; `historical-branch-audit.yml`; prompt-eval/governance checks | Platform | agents/humans/CI as applicable | inputs; version; fail-closed result | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | Platform CI / Agent Governance | KEEP | live tree `8e609f05` |
| Atlas | root AGENTS | `/AGENTS.md` | `/AGENTS.md` | Atlas | agents/humans/CI as applicable | scope; precedence; durable status | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | `atlas-gate` / `provenance-gate` | KEEP | live tree `a1b5fea1` |
| Atlas | nested AGENTS/override | `NOT_NEEDED` - current tree has no nested/override AGENTS | `NOT_NEEDED` until path-specific rules are proven necessary | Atlas | agents/humans/CI as applicable | scope; precedence; durable status | NOT_NEEDED | NOT_NEEDED | `atlas-gate` / `provenance-gate` | NOT_NEEDED | live tree `a1b5fea1` |
| Atlas | architecture/ADR | `UNKNOWN (GAP-DOCS-ATLAS-ARCH-001: current tree has no docs/architecture path although section 13 targets one)` | provider-owned `docs/architecture/**` only if material architecture requires durable ADRs | Atlas | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | `atlas-gate` / `provenance-gate` | UNKNOWN | live tree `a1b5fea1` |
| Atlas | contracts | `UNKNOWN (GAP-DOCS-ATLAS-CONTRACT-001: no canonical docs/contracts path; runtime-contract material is currently evidence-scoped)` | provider canonical contract path selected by need | Atlas | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | `atlas-gate` / `provenance-gate` | UNKNOWN | live tree `a1b5fea1` |
| Atlas | governance policy | `UNKNOWN (GAP-DOCS-ATLAS-GOV-001: no dedicated governance-policy artifact identified in current tree)` | provider policy object/document only where needed | Atlas | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | `atlas-gate` / `provenance-gate` | UNKNOWN | live tree `a1b5fea1` |
| Atlas | CI policy | `.github/workflows/ci.yml`; `extraction-provenance.yml`; `synology-live-acceptance.yml`; `synology-runner-health.yml` | `.github/workflows/ci.yml`; `extraction-provenance.yml`; `synology-live-acceptance.yml`; `synology-runner-health.yml` | Atlas | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | `atlas-gate` / `provenance-gate` | KEEP | live tree `a1b5fea1` |
| Atlas | test strategy | `UNKNOWN (GAP-DOCS-ATLAS-TEST-001: tests exist but no dedicated test-strategy document identified)` | provider test-strategy artifact only if current tests need durable policy beyond workflows/tests | Atlas | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | `atlas-gate` / `provenance-gate` | UNKNOWN | live tree `a1b5fea1` |
| Atlas | reusable prompts | `docs/agents/prompts/**` | provider prompt library with stable status/ownership | Atlas | agents/humans/CI as applicable | stable ID; scope; status; supersession | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | `atlas-gate` / `provenance-gate` | KEEP | live tree `a1b5fea1` |
| Atlas | one-shot prompts | `docs/evidence/DYN-ATLAS-001-target-gui-execution-prompt.md` and bounded execution evidence | historical evidence only | Atlas | agents/humans/CI as applicable | stable ID; scope; status; supersession | historical retained by provenance rule | no independently edited cross-repo authority copy; declared path-scoped override only | `atlas-gate` / `provenance-gate` | ARCHIVE | live tree `a1b5fea1` |
| Atlas | task packets | `docs/agents/tasks/active/**`; `docs/agents/tasks/archive/**` | Issue authority plus provider packet cache | Atlas | agents/humans/CI as applicable | Issue/PR link; owner; status; supersession/time | active only while linked lifecycle is live; archive/delete on supersession | cache only; GitHub Issue/PR/live state outranks it | `atlas-gate` / `provenance-gate` | KEEP/CLEANUP | live tree `a1b5fea1` |
| Atlas | programmes | `docs/evidence/ATLAS-FULLWORLD-PROGRAMME-LEDGER.md` | GitHub Issue authority; ledger is non-authoritative cache/evidence | Atlas | agents/humans/CI as applicable | Issue/PR link; owner; status; supersession/time | active only while linked lifecycle is live; archive/delete on supersession | cache only; GitHub Issue/PR/live state outranks it | `atlas-gate` / `provenance-gate` | KEEP/CLEANUP | live tree `a1b5fea1` |
| Atlas | handovers | `docs/evidence/fullworld-generation/handoff-summary.json` | historical expiring/non-authoritative handover evidence | Atlas | agents/humans/CI as applicable | Issue/PR link; owner; status; supersession/time | historical retained by provenance rule | cache only; GitHub Issue/PR/live state outranks it | `atlas-gate` / `provenance-gate` | ARCHIVE | live tree `a1b5fea1` |
| Atlas | agent runbooks | `docs/agents/SYNOLOGY_DESKTOP_COMMANDER_ACCESS.md`; prompt/task routing docs | provider agent runbook only where reusable | Atlas | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | `atlas-gate` / `provenance-gate` | KEEP | live tree `a1b5fea1` |
| Atlas | operations runbooks | `UNKNOWN (GAP-DOCS-ATLAS-OPS-001: no docs/operations path; operational material is mixed into evidence documents)` | provider-owned operations runbook if preview/publication operations remain recurring | Atlas | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | `atlas-gate` / `provenance-gate` | UNKNOWN | live tree `a1b5fea1` |
| Atlas | recovery/break-glass | `UNKNOWN (GAP-DOCS-ATLAS-RECOVERY-001: no dedicated recovery/break-glass artifact identified)` | provider recovery/break-glass artifact if operationally required | Atlas | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | `atlas-gate` / `provenance-gate` | UNKNOWN | live tree `a1b5fea1` |
| Atlas | review evidence | `docs/evidence/**`; GitHub PR/review/check objects | `docs/evidence/**`; GitHub PR/review/check objects | Atlas | agents/humans/CI as applicable | subject; source; identity; time; digest/retention where applicable | append/retain by evidence or migration provenance policy | copy may preserve provenance; must not broaden authority | `atlas-gate` / `provenance-gate` | KEEP | live tree `a1b5fea1` |
| Atlas | release evidence | `docs/evidence/fullworld-publication/publication-summary.json`; publication workflow evidence | Atlas publication/release evidence authority | Atlas | agents/humans/CI as applicable | subject; source; identity; time; digest/retention where applicable | append/retain by evidence or migration provenance policy | copy may preserve provenance; must not broaden authority | `atlas-gate` / `provenance-gate` | KEEP | live tree `a1b5fea1` |
| Atlas | migration evidence | `docs/migration/legacy-atlas-extraction-provenance.json`; extraction-provenance workflow/evidence | `docs/migration/legacy-atlas-extraction-provenance.json`; extraction-provenance workflow/evidence | Atlas | agents/humans/CI as applicable | subject; source; identity; time; digest/retention where applicable | append/retain by evidence or migration provenance policy | copy may preserve provenance; must not broaden authority | `atlas-gate` / `provenance-gate` | KEEP | live tree `a1b5fea1` |
| Atlas | generated docs/indexes | `web/semantic-search/index.json`; FullWorld generated evidence/index outputs | generator-owned output with source/digest provenance | Atlas | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | regenerate from authoritative inputs; output non-authoritative unless promoted | no independently edited cross-repo authority copy; declared path-scoped override only | `atlas-gate` / `provenance-gate` | GENERATED | live tree `a1b5fea1` |
| Atlas | human reference docs | `README.md`; `SECURITY.md`; `e2e/README.md`; evidence/reference docs | `README.md`; `SECURITY.md`; `e2e/README.md`; evidence/reference docs | Atlas | agents/humans/CI as applicable | owner; scope; version/status where operationally needed | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | `atlas-gate` / `provenance-gate` | KEEP | live tree `a1b5fea1` |
| Atlas | machine-readable policy companions | `UNKNOWN (GAP-DOCS-ATLAS-POLICY-001: machine-readable evidence registries exist but no dedicated policy companion is identified)` | provider policy companion only when deterministic enforcement needs one | Atlas | agents/humans/CI as applicable | schema/version; owner; exact identities | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | `atlas-gate` / `provenance-gate` | UNKNOWN | live tree `a1b5fea1` |
| Atlas | documentation/agent validators | `tools/governance/verify_extraction_provenance.py`; `test_verify_extraction_provenance.py`; provider workflows/tests | `tools/governance/verify_extraction_provenance.py`; `test_verify_extraction_provenance.py`; provider workflows/tests | Atlas | agents/humans/CI as applicable | inputs; version; fail-closed result | durable while authoritative; update through protected provider process | no independently edited cross-repo authority copy; declared path-scoped override only | `atlas-gate` / `provenance-gate` | KEEP | live tree `a1b5fea1` |

## Mechanical completion statement

This report is intentionally capable of validating structurally while returning a non-terminal programme verdict. Structural completeness and programme completion are separate facts.

Mechanical validation record: `docs/evidence/OTERYN-ORG-AUDIT-v3.10-TERMINAL-REPORT-VALIDATION-20260822.json`.

`REPORT_STRUCTURE = COMPLETE`

`OTERYN_ORG_AUDIT_V3_10 = INCOMPLETE`
