# Solo-Maintainer Governance V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace moving-head/enterprise-style governance with a solo-maintainer model that preserves deterministic security and integration safeguards while making GitHub Merge Queue and one aggregate gate per repository the normal merge authority.

**Architecture:** META owns the small cross-repository desired-state contract; providers keep their own test implementations. Every permanent repository emits one stable aggregate gate on both `pull_request` and `merge_group`, and GitHub Merge Queue validates the synthetic integration candidate. Human/CODEOWNER approval is not required in a one-person team, AI review becomes risk-based evidence rather than a fragile required status, and moving-head review-envelope/fingerprint machinery is retired only after the replacement integration path is proven.

**Tech Stack:** GitHub Actions, GitHub branch protection/rulesets/Merge Queue, Python governance validators, repository-local CI, JSON desired-state contracts.

**Spec:** `docs/superpowers/specs/2026-08-31-solo-maintainer-governance-v2-design.md`

## Global Constraints

- Live GitHub state is the only authority for current branch protection, rulesets, Merge Queue state, required checks and current SHAs.
- Do not disable an existing required check before its replacement behavior has been proven on a representative PR and, where applicable, a real Merge Queue synthetic candidate.
- Do not disable strict freshness for a repository until its real Merge Queue canary has passed and post-mutation settings readback is green.
- Do not use direct pushes to protected `main`, force pushes, ref rewrites or destructive branch changes as the normal rollout path.
- Do not create no-op/retrigger/checkpoint commits solely to make CI or review machinery run again.
- Preserve secret scanning/push protection, dependency/security scanning, least-privilege Actions permissions and immutable action pinning where currently applicable.
- Preserve Atlas extraction provenance until a separate migration-terminal decision proves that invariant obsolete or narrows its lifecycle.
- A failed canary triggers rollback to the previous settings, not a new bypass exception.
- The break-glass path is recovery-only and must never bypass a legitimate failing product/security test.
- Provider rollout is serial: META -> Game -> Platform -> Atlas.

---

### Task 1: Make Solo-Maintainer Governance V2 the canonical META target

**Files:**
- Modify: `docs/architecture/adr/0002-organization-governance-operating-model.md`
- Modify: `ecosystem/governance-desired-state.json`
- Modify: `tools/governance/audit_github_readonly_core.py`
- Modify: `tools/governance/test_audit_github_readonly.py`
- Modify: `tools/governance/test_audit_github_readonly_terminal.py`
- Read/adjust if required by existing contract tests: `docs/ci/CI_CONTRACT.md`

**Interfaces:**
- Consumes: the approved V2 design in `docs/superpowers/specs/2026-08-31-solo-maintainer-governance-v2-design.md`.
- Produces: a small desired-state schema in which each permanent repository has exactly one stable required external gate and Merge Queue/freshness state can be represented without encoding transient review generations.

- [ ] **Step 1: Refresh live protection/ruleset/Merge Queue state for all four permanent repositories**

Record exact current `main` SHA, required contexts, strict-freshness setting, PR requirement, force-push/deletion state, approval/CODEOWNER requirement, bypass/admin enforcement, merge methods and Merge Queue state. Any unreadable field remains `UNKNOWN` and blocks mutation of that field until readback is available.

- [ ] **Step 2: Write failing desired-state tests for the V2 external-gate contract**

The tests must assert this exact required context map:

```python
EXPECTED_REQUIRED_CONTEXTS = {
    "Oteryn/Oteryn": ["meta-gate"],
    "Oteryn/Oteryn-Game": ["game-gate"],
    "Oteryn/Oteryn-Platform": ["platform-gate"],
    "Oteryn/Oteryn-Atlas": ["atlas-gate"],
}
```

They must also reject a desired state that requires CODEOWNER approval as a universal solo-maintainer baseline.

- [ ] **Step 3: Run the focused governance tests and verify RED**

Run the repository's existing governance test commands for `test_audit_github_readonly.py` and `test_audit_github_readonly_terminal.py`. Expected result: failure because the current desired-state JSON still encodes `ai-review-gate`, separate `provenance-gate`, transitional Game context and strict freshness as the target.

- [ ] **Step 4: Amend ADR 0002 with a dated V2 decision section**

The amendment must state:

```text
Solo-maintainer baseline:
- exactly one stable required aggregate gate per permanent repository;
- zero mandatory human approvals and no required CODEOWNER approval while the organization has one human maintainer;
- Merge Queue owns integration freshness after a repository canary;
- strict branch freshness is transitional and removed after that canary;
- AI review is risk-based evidence, not an independent required status;
- provider-internal provenance/security/test jobs feed the aggregate gate rather than expanding branch-protection contexts;
- one narrow auditable owner break-glass recovery mechanism is required.
```

The amendment must explicitly supersede conflicting moving-head/enterprise-style clauses without erasing historical rationale.

- [ ] **Step 5: Change `ecosystem/governance-desired-state.json` to the V2 target shape**

Set the long-term `required_checks` arrays to exactly the four aggregate contexts above. Preserve main protection, squash-only, branch deletion-on-merge preference and security baseline. Extend the schema/validator only as much as necessary to represent `merge_queue` and transitional `strict_required_status_checks` state without embedding transient PR/review data.

- [ ] **Step 6: Update the read-only audit validator to understand transitional rollout state**

The validator must distinguish:

```text
TARGET      replacement gate/MQ proven and desired state active
TRANSITION  old protection intentionally retained while replacement is being canaried
DRIFT       live state differs without an authorized transition record
UNKNOWN     required live field could not be read
```

It must never classify an explicitly authorized serial cutover as compliant before its repository canary succeeds.

- [ ] **Step 7: Run all focused META governance tests and verify GREEN**

Run the same focused suites plus `python3 tools/governance/audit_github_readonly.py --offline`. Expected result: all pass against the new schema/desired-state contract.

- [ ] **Step 8: Run META CI-equivalent local deterministic suites**

Run the governance tests invoked by `.github/workflows/ci.yml`, including merge-queue workflow contract tests and AI-review-policy tests that remain applicable. Any test that exists only to enforce a superseded design should be changed in the same reviewed task rather than bypassed.

- [ ] **Step 9: Commit Task 1 as one authority change**

Suggested commit:

```bash
git commit -m "docs(governance): adopt solo-maintainer governance v2"
```

---

### Task 2: Collapse META protection to `meta-gate` and retire required AI-review authority

**Files:**
- Modify: `.github/workflows/ci.yml`
- Modify or retire after proof: `.github/workflows/governance-ai-review.yml`
- Retire after proof: `.github/workflows/merge-group-ai-review-adapter.yml`
- Modify: `ecosystem/ai-review-policy.json`
- Modify/remove only after dependency search: `tools/governance/verify_ai_review_evidence.py`
- Modify/remove only after dependency search: `tools/governance/trusted_review_attestation.py`
- Modify corresponding `tools/governance/test_*` files
- Modify if it still describes `ai-review-gate` as external authority: `docs/ci/CI_CONTRACT.md`

**Interfaces:**
- Consumes: canonical V2 desired state from Task 1.
- Produces: `meta-gate` as the only required META merge status, with deterministic PR and merge-group validation; the canonical policy still requires R1/R2 external review evidence, but no separate AI-review status or comment/reaction grammar can deadlock protected integration.

- [ ] **Step 1: Enumerate every repository reference to `ai-review-gate`, trusted review envelopes, attestation verification, review fingerprints and the merge-group AI adapter**

Classify each reference as one of: `external_required_authority`, `advisory_review`, `independent_security_boundary`, `historical_documentation`, `test_only`. Do not remove any `independent_security_boundary` reference until its threat is documented and replaced.

- [ ] **Step 2: Add/adjust tests proving `meta-gate` handles both PR and `merge_group` candidates**

The test contract must require:

```yaml
on:
  pull_request:
    branches: [main]
  merge_group:
    types: [checks_requested]
```

and must require the merge-group path to validate `github.sha == github.event.merge_group.head_sha` and target `refs/heads/main` before testing the candidate.

- [ ] **Step 3: Simplify AI-review implementation while preserving canonical R1/R2 invocation**

Retain R0/R1/R2 classification, sensitive-path detection, and the canonical requirement for one configured external review per stable R1/R2 fingerprint. Remove only requirements whose purpose is making an independent `ai-review-gate` status mechanically green, including external-output flair/reaction grammar and bridge-specific envelope requirements. Do not weaken the review-invocation requirement without a separately reviewed canonical policy amendment.

- [ ] **Step 4: Keep privileged workflow boundaries safe during retirement**

Before deleting any trusted-base workflow, verify that no remaining PR-context workflow obtains `actions: write`, repository-content write or other privileged mutation authority from candidate-controlled YAML. Preserve or strengthen least-privilege behavior even while simplifying review enforcement.

- [ ] **Step 5: Verify a normal META PR with only `meta-gate` as the intended replacement authority**

Do not change protection yet. The candidate workflow must be green under the still-existing old protection. Record the exact head and successful `meta-gate` run.

- [ ] **Step 6: Run a real META Merge Queue canary while old protection remains recoverable**

The canary must produce `meta-gate` on the actual synthetic merge-group SHA and prove the candidate is tested on the integration commit. If the current protection cannot admit the canary because `ai-review-gate` is still required, use only an explicitly approved bounded settings transition that removes the obsolete context after the PR-stage replacement proof exists; restore immediately if the queue canary fails.

- [ ] **Step 7: Change META live required contexts to exactly `meta-gate`**

After successful canary, remove `ai-review-gate` from required contexts. Confirm normal direct push remains blocked and no force-push/deletion/broad bypass was introduced.

- [ ] **Step 8: Disable strict freshness only after the real META queue canary passes**

Read back the final setting and record the exact successful merge-group run and resulting `main` commit.

- [ ] **Step 9: Retire the merge-group AI adapter and bridge-only review machinery**

Delete `merge-group-ai-review-adapter.yml` once no branch/ruleset requires `ai-review-gate`. Remove envelope/attestation/fingerprint machinery only where the dependency inventory proves it has no independent security consumer.

- [ ] **Step 10: Run META regression and post-cutover drift validation**

Expected state: one required `meta-gate`, Merge Queue active, strict freshness off, protection otherwise intact, governance desired state green.

---

### Task 3: Convert Game to a satisfiable solo-maintainer Merge Queue gate

**Files in `Oteryn/Oteryn-Game`:**
- Modify: `.github/workflows/merge-gate.yml`
- Modify: `.github/CODEOWNERS` only if comments/ownership wording must reflect non-required approval
- Modify: `.github/repository-policy.json` if it encodes review/title/body/merge constraints
- Modify: `tools/repository/validate_repository_policy.py` if it enforces superseded process requirements
- Modify corresponding repository-policy/governance tests
- Preserve and reuse: product/security jobs already feeding `game-gate`

**Interfaces:**
- Consumes: V2 authority and one-gate contract.
- Produces: `game-gate` for both PR and merge-group candidates, with no second-person approval dependency and no strict freshness after canary.

- [ ] **Step 1: Refresh Game ruleset `Protect main` and save an exact rollback snapshot**

Capture every rule, including required contexts, strict freshness, CODEOWNER approval, review-thread resolution, allowed merge methods, deletion/non-fast-forward and bypass actors.

- [ ] **Step 2: Write RED workflow-contract tests for `merge_group` support**

The tests must fail against the current PR-only `merge-gate.yml` and require a resolver that can operate without `github.event.pull_request.number` on merge-group events.

- [ ] **Step 3: Separate candidate identity/range resolution from PR metadata validation**

For `pull_request`, use exact PR head/base and changed-file APIs as today. For `merge_group`, bind to `github.event.merge_group.head_sha` and `base_sha`; do not call PR-only APIs as a prerequisite for the aggregate integration gate. If fine-grained changed-file classification is unavailable, fail closed to the broader applicable validation set rather than failing the queue solely because a PR number is absent.

- [ ] **Step 4: Make PR title/body convention checks advisory**

Remove hard failure solely for title length, conventional-title grammar, or missing `## Summary` / `## Scope` / `## Validation` headings. Preserve any metadata check that protects an actual automated release/security invariant and document that independent reason.

- [ ] **Step 5: Preserve real Game safety jobs**

Keep dependency review, CodeQL and applicable Rust/Linux/Windows/product tests feeding the final `game-gate`. The aggregate gate must fail if a required internal job fails.

- [ ] **Step 6: Verify PR-stage `game-gate` on an exact candidate**

Old ruleset remains in place for this proof.

- [ ] **Step 7: Change Game ruleset approval semantics for a one-person team**

Set:

```text
required_approving_review_count = 0
require_code_owner_review = false
```

Keep review-thread resolution if it remains practical and does not create an unsatisfiable self-approval requirement. Keep squash-only, linear history, deletion/force-push blocking.

- [ ] **Step 8: Enable/use Merge Queue and run a real Game canary**

Require the actual synthetic candidate to emit `game-gate`. On failure restore the saved ruleset snapshot.

- [ ] **Step 9: Disable strict freshness after canary success**

Read back that `game-gate` remains the sole required context and Merge Queue is the normal path.

- [ ] **Step 10: Run Game post-cutover tests and META drift audit**

Expected result: no required second-human approval, one aggregate gate, queue integration proven, security/product validation preserved.

---

### Task 4: Finish Platform Merge Queue adoption without redesigning its healthy gate

**Files in `Oteryn/Oteryn-Platform`:**
- Modify only if canary exposes a defect: `.github/workflows/ci.yml`
- Modify only if existing tests require correction: `tests/ci/test_push_change_routing.py`
- Modify only if existing tests require correction: `tests/ci/test_workflow_trigger_economy.py`
- Modify only if required by inventory semantics: `tools/validation/workflow_inventory.py`
- Modify only if required by inventory semantics: `tools/validation/test_workflow_inventory.py`

**Interfaces:**
- Consumes: existing `platform-gate` merge-group preparation already on `main`.
- Produces: verified Merge Queue integration with no new external gate or complex merge-group optimizer.

- [ ] **Step 1: Refresh current Platform protection and Merge Queue state**

Save the exact pre-cutover snapshot.

- [ ] **Step 2: Run focused existing CI routing tests**

Verify the current behavior intentionally treats a merge-group candidate without a PR-specific range as a broad/fail-closed validation case.

- [ ] **Step 3: Create a representative Platform canary PR with no production mutation**

The canary must exercise the current aggregate gate and be safe to integrate or revert as ordinary code/docs according to repository policy.

- [ ] **Step 4: Put the canary through the real Merge Queue**

Verify `platform-gate` is emitted on the synthetic merge-group SHA and all required internal jobs have the expected result.

- [ ] **Step 5: Do not add a fine-grained merge-group classifier unless the canary proves the broad path materially harmful**

Higher CI usage is acceptable when it buys simpler, more reliable integration logic for a one-person team.

- [ ] **Step 6: Disable strict freshness only after canary success and readback**

Keep `platform-gate` as the sole required external context.

- [ ] **Step 7: Run META drift audit and Platform post-cutover validation**

Expected result: Platform remains the simplest provider model rather than inheriting new META bridge complexity.

---

### Task 5: Internalize Atlas provenance and make `atlas-gate` Merge Queue safe

**Files in `Oteryn/Oteryn-Atlas`:**
- Modify: `.github/workflows/ci.yml`
- Modify: `.github/workflows/extraction-provenance.yml` or fold its deterministic steps into a reusable/internal job consumed by CI
- Modify corresponding Atlas workflow/verification tests
- Preserve provenance implementation: `tools/governance/verify_extraction_provenance.py`
- Preserve provenance negative tests: `tools/governance/test_verify_extraction_provenance.py`

**Interfaces:**
- Consumes: existing Atlas deterministic test surface and extraction-provenance verifier.
- Produces: one externally required `atlas-gate` whose internal dependency graph includes provenance where applicable and runs safely for `merge_group`.

- [ ] **Step 1: Refresh Atlas live protection and save rollback state**

Capture both current required contexts (`atlas-gate`, `provenance-gate`) and all readable protection fields.

- [ ] **Step 2: Write RED tests requiring Atlas CI to handle `merge_group` without pretending a PR payload exists**

The test must cover the current `change-classification`/browser E2E branches that are PR-specific and prove the aggregate gate cannot silently skip required integration validation merely because the event is `merge_group`.

- [ ] **Step 3: Define merge-group classification behavior**

For merge groups, prefer a conservative validation set that does not depend on PR-only APIs. If an internal E2E path is required for any potentially affected candidate and exact path classification is unavailable, run it rather than weakening `atlas-gate`.

- [ ] **Step 4: Internalize provenance**

Make the provenance verifier a required internal dependency of `atlas-gate` for the lifecycle where it remains applicable. A provenance failure must make `atlas-gate` fail.

- [ ] **Step 5: Preserve the independent provenance threat model**

Do not remove the pinned legacy-source identity or negative provenance tests. This task changes the external branch-protection interface, not the source-integrity requirement.

- [ ] **Step 6: Verify `atlas-gate` on an ordinary PR while both old required contexts still exist**

Record the exact successful runs.

- [ ] **Step 7: Prove the legacy provenance context cannot deadlock a real Atlas Merge Queue canary**

Before admission, prove `provenance-gate` is produced and succeeds on the exact synthetic merge-group candidate. If that context does not support `merge_group`, do not leave the queue waiting: after Step 6 and only through an explicitly authorized, bounded settings transition, temporarily remove `provenance-gate` from required contexts, record the deviation in the transition receipt, and restore it immediately if the canary fails. The synthetic candidate must receive a successful `atlas-gate` and execute the conservative integration-safe internal validation set.

- [ ] **Step 8: Complete the desired-state removal of `provenance-gate` after canary success**

Keep only `atlas-gate`; verify provenance remains mechanically blocking inside that gate. If the bounded pre-canary transition was used, close its receipt only after positive readback of this target state; otherwise remove `provenance-gate` now after canary success.

- [ ] **Step 9: Disable strict freshness after queue proof and readback**

Preserve main force-push/deletion/squash/linear protections.

- [ ] **Step 10: Run Atlas post-cutover verification and META drift audit**

Expected result: one external gate with no loss of provenance assurance.

---

### Task 6: Establish the owner break-glass recovery contract

**Files:**
- Create: `docs/governance/SOLO_MAINTAINER_BREAK_GLASS.md`
- Modify: `ecosystem/governance-desired-state.json` only if a machine-readable break-glass marker is useful and stable
- Add focused governance tests if the repository already validates recovery contracts

**Interfaces:**
- Consumes: final live protection model from Tasks 2-5.
- Produces: one explicit recovery procedure for a broken required-gate/protection control plane; normal integration remains non-bypassable.

- [ ] **Step 1: Discover the exact GitHub capability available on the current plan**

Do not assume admin bypass, ruleset bypass or branch-protection mutation behavior. Verify which narrow control can be changed and restored by the owner.

- [ ] **Step 2: Document the only allowed break-glass trigger**

Use this exact semantic boundary:

```text
Break-glass is allowed only when the protection/required-gate control plane itself prevents any normal protected repair path. It is not allowed to bypass a legitimate failing product, security, dependency, provenance or integration test.
```

- [ ] **Step 3: Define exact transaction requirements**

The document must require expected head/repository binding, minimal single setting relaxation, one repair integration, immediate restoration, positive settings readback and durable Issue/PR receipt.

- [ ] **Step 4: Perform a non-destructive dry-run/readback exercise**

Do not actually relax protection merely to test the document. Verify the API/UI path, required fields and rollback state without mutating settings where possible.

- [ ] **Step 5: Add drift/audit awareness**

The read-only auditor should flag a break-glass relaxation that remains active after its authorized transaction.

---

### Task 7: Remove superseded moving-head governance after all four repositories are stable

**Files in META:**
- Review/mark superseded: `docs/superpowers/specs/2026-08-30-organization-merge-queue-review-fingerprint-design.md`
- Review/mark superseded: `docs/superpowers/specs/2026-08-30-organization-merge-queue-review-fingerprint-amendment.md`
- Review/mark superseded: `docs/superpowers/plans/2026-08-30-organization-merge-queue-review-fingerprint-rollout.md`
- Review/retire bridge/review-envelope files discovered in Task 2 dependency inventory
- Update related Issues/PRs with durable supersession disposition rather than deleting history

**Interfaces:**
- Consumes: proven V2 live state in all four repositories.
- Produces: a repository where future agents cannot accidentally resurrect the old moving-head architecture as current authority.

- [ ] **Step 1: Prove the V2 definition of done from live GitHub state**

Required proof:

```text
META     required: meta-gate     MQ proven, strict freshness off
Game     required: game-gate     MQ proven, strict freshness off, no required CODEOWNER approval
Platform required: platform-gate MQ proven, strict freshness off
Atlas    required: atlas-gate    MQ proven, strict freshness off, provenance still internally enforced
```

Also prove force-push/deletion protections and squash/linear policy remain intact.

- [ ] **Step 2: Build a reverse-dependency inventory for every candidate legacy governance file**

Delete only files whose consumers are all retired/superseded. Keep any component that still protects an independent privilege, production, secret, deployment or source-integrity boundary.

- [ ] **Step 3: Mark historical specs as superseded**

Add a prominent header pointing to `2026-08-31-solo-maintainer-governance-v2-design.md` and explaining that the old design remains historical rationale, not current execution authority.

- [ ] **Step 4: Remove unused merge-group AI adapter / envelope / attestation / fingerprint bridge code and tests**

Run the full META governance suite after each coherent removal group. Do not combine unrelated autonomy-lifecycle cleanup into this task.

- [ ] **Step 5: Close or reclassify obsolete rollout dependencies**

Issues whose only acceptance criterion was the superseded bridge should be closed as superseded with links to V2 proof. Independent defects remain open under their actual threat model.

- [ ] **Step 6: Run final organization read-only audit**

Expected result: desired state equals live state, no temporary bypass is active, no obsolete external required contexts remain, and all four queues/gates are healthy.

- [ ] **Step 7: Record terminal closeout**

The closeout must list exact final `main` SHAs, required contexts, Merge Queue settings, strict-freshness state, approval/CODEOWNER state, break-glass contract path and the final governance-audit result.

---

## Plan self-review result

- **Spec coverage:** target external gates, Merge Queue, strict freshness, CODEOWNER approval, AI review, provenance, process-format checks, desired-state ordering, break-glass and cleanup are each mapped to an implementation task.
- **Safety ordering:** replacement behavior is proven before old required checks/freshness are removed; provider cutover is serial with rollback snapshots.
- **Scope:** this plan intentionally does not redesign bounded-autonomy lifecycle policy (`#71/#107` family) or product/deployment architecture. That should be a later independent audit after merge/integration governance is simplified.
- **No placeholder implementation decisions:** any field that cannot be read from the current GitHub integration is explicitly required to be discovered from live state before mutation rather than guessed.
