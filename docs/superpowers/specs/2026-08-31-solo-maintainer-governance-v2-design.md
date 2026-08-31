# Solo-Maintainer Governance V2 — audit and target design

## Status

**PROPOSED — owner-approved direction, not yet live enforcement authority.**

This document records the 2026-08-31 read-only audit of organization governance and the proposed target operating model for Oteryn as a one-person engineering organization.

Merging this document does **not** by itself authorize GitHub settings changes, branch-protection changes, ruleset changes, Merge Queue activation, provider-repository mutation, deletion of legacy workflow machinery, or weakening of a currently required check. Those changes require the implementation sequence and live readbacks defined below.

Live GitHub state always outranks historical SHA values and audit snapshots in this document.

## Owner outcome

Oteryn needs rational safeguards that materially reduce the probability of bad code, accidental main-branch damage, secret exposure, unsafe dependency changes, and untested integration — without creating a procedural control plane that assumes multiple human reviewers or repeatedly blocks the sole maintainer.

The target is:

> **Solo-maintainer security + deterministic CI + GitHub Merge Queue, with one stable aggregate gate per repository.**

The system should protect code and integration, not require the owner to satisfy process loops created by the governance machinery itself.

## Audit scope

Repositories:

- `Oteryn/Oteryn` — META
- `Oteryn/Oteryn-Game` — Game
- `Oteryn/Oteryn-Platform` — Platform
- `Oteryn/Oteryn-Atlas` — Atlas

Read-only surfaces inspected during the audit included:

- current protected `main` branch state and required status contexts;
- repository rulesets where visible;
- `.github/workflows/` inventories and merge-related workflows;
- `.github/CODEOWNERS`;
- `ecosystem/governance-desired-state.json`;
- `ecosystem/ai-review-policy.json`;
- ADR 0002 governance baseline;
- current Merge Queue rollout state and issue/PR evidence around moving-head, review-fingerprint and trusted-evidence machinery.

### Audit limitation

The available GitHub integration exposed required status contexts and repository rulesets but did not provide a complete readback of every classic branch-protection field for META, Platform and Atlas. Full review/admin/bypass/settings state must therefore be refreshed immediately before any mutation. Missing readback is `UNKNOWN`, never assumed safe or unsafe.

## Verified audit snapshot

At the time of the final audit refresh:

- META protected `main` was `74bd48f2b511265c7a97d24dae66fe066c2e1976`, requiring `meta-gate` and `ai-review-gate`.
- META `ci.yml` already handled `merge_group: checks_requested` and validated the merge-group candidate identity.
- META also had a separate `merge-group-ai-review-adapter.yml` that emitted the required `ai-review-gate` name for merge groups while performing only merge-group lifecycle/SHA checks.
- Game `main` used repository ruleset `Protect main`; the ruleset required `game-gate`, strict required-status freshness, squash-only PR integration, linear history, review-thread resolution and CODEOWNER approval, with no bypass actors.
- Game `.github/CODEOWNERS` assigned the protected merge-authority paths only to `@blakinio`.
- Platform protected `main` required only `platform-gate`; its CI already had a `merge_group` trigger and intentionally failed closed to broad validation when a PR-specific changed-file range was unavailable.
- Atlas protected `main` required both `atlas-gate` and `provenance-gate`.
- Atlas extraction provenance was a real deterministic test of target material against a pinned legacy source, but it was exposed as a second external required status instead of being an internal dependency of the aggregate Atlas gate.
- `ecosystem/governance-desired-state.json` still encoded strict required-status freshness for all four permanent repositories, two required checks for META, and two required checks for Atlas.
- ADR 0002 already specified the healthier target shape of one stable externally required context per repository: `meta-gate`, `game-gate`, `platform-gate`, `atlas-gate`, with small governance-as-code and provider-owned internal CI.

## Root cause of the current complexity

A substantial part of the current merge/review machinery grew while Oteryn did not have a usable Merge Queue path and still needed to defend against a moving protected `main`.

The old failure mode was structurally understandable:

```text
PR candidate C is reviewed
        |
        v
main advances A -> B
        |
        v
strict freshness requires the branch to catch up
        |
        v
PR head changes C -> C'
        |
        v
review/gate identity changes
        |
        v
prove whether C' is materially the same reviewed change
```

That pressure produced mechanisms such as:

- review fingerprints;
- reviewed-head ancestry rules;
- review-neutral path classification;
- trusted-base merge-up reuse;
- exact review generations and anchors;
- same-head recheck budgets;
- trusted review envelopes;
- custom attestations and artifact locators;
- merge-group review adapters and bridge concepts;
- compatibility grammars for external reviewer output.

These mechanisms were not created arbitrarily: they attempted to retain review assurance while branch freshness repeatedly changed candidate identities. However, once GitHub Merge Queue becomes the normal integration authority, the underlying problem changes.

The PR head should no longer need to move merely because `main` moved. GitHub can construct and validate the synthetic integration candidate in the queue.

The target responsibility split becomes:

```text
PR review / PR CI
  answers: is the proposed change itself acceptable?

Merge Queue / merge_group CI
  answers: is the proposed change acceptable on the current integration base?
```

Therefore an unrelated advance of `main` must not by itself force a new PR review generation or a branch merge-up.

## Design principles

### 1. One external merge decision per repository

GitHub protection should require exactly one stable repository-specific aggregate status:

| Repository | Required external status |
| --- | --- |
| META | `meta-gate` |
| Game | `game-gate` |
| Platform | `platform-gate` |
| Atlas | `atlas-gate` |

Internal jobs remain provider-owned and may be numerous. The aggregate gate fails closed when a blocking internal job fails.

GitHub branch/ruleset configuration should not need to know the names of volatile internal jobs such as provenance, CodeQL, browser E2E, Rust workspace jobs, classifiers or AI-review helpers.

### 2. Merge Queue owns integration freshness

After a repository has passed a real Merge Queue canary and settings readback:

- Merge Queue becomes the normal protected-main integration path;
- required workflows emit the aggregate gate for both `pull_request` and `merge_group`;
- the merge-group run validates/tests the exact synthetic integration candidate;
- strict `Require branches to be up to date before merging` / strict required-status freshness is disabled;
- agents do not merge or rebase `main` into a stable candidate solely to satisfy moving-head freshness.

Initial queue configuration should favor correctness and simplicity over throughput. For a one-person team, a conservative single-entry merge-group policy is sufficient unless later evidence shows a reason to increase grouping.

### 3. No required human approval for the sole maintainer

The organization has one human maintainer. A rule that requires another human approval or CODEOWNER approval creates an unsatisfiable or self-blocking control rather than meaningful peer review.

Target policy:

- `required_approving_review_count = 0`;
- `require_code_owner_review = false`;
- CODEOWNERS may remain as ownership/documentation and risk-path metadata;
- unresolved blocking review conversations may still block merge where the platform supports that cleanly.

High-risk changes are protected by deterministic tests, security tooling, optional independent AI review, deliberate owner confirmation for rare dangerous control-plane mutations, and Merge Queue integration testing — not by pretending a second human maintainer exists.

### 4. AI review remains useful but stops being a fragile merge authority

AI review is valuable as an independent analysis signal, especially for security, authentication, payment, deployment, migration, GitHub workflow and branch-protection changes.

It should not require GitHub to mechanically interpret an evolving product-output grammar of reviewer comments, reactions and presentation phrases in order to decide whether a correct PR may merge.

Target risk model:

- **R0:** prose/generated/evidence-only low-risk changes — no independent AI review required.
- **R1:** ordinary code/config/dependency work — normal CI is authoritative; fast AI review is optional/recommended according to risk and cost.
- **R2:** security/auth/payment/deployment/migration/governance/workflow/protection changes — independent deep AI review is strongly recommended before merge, but its comment-envelope parser is not a separate required branch-protection status.

P0/P1/P2 remains useful as review vocabulary. P0/P1 findings should be addressed before deliberate owner integration. P2 can be tracked as follow-up. This is a human/agent decision contract, not a second cryptographic merge control plane.

### 5. Retire moving-head review machinery when no independent threat remains

The following mechanisms are candidates for retirement after Merge Queue is proven and no separate security requirement remains:

- trusted-base merge-up review reuse;
- reviewed-generation ancestry needed only for merge-up commits;
- branch-freshness-driven review fingerprints;
- trusted review envelope publication used only to bridge PR review into merge-group authority;
- custom review attestations used only by that bridge;
- compatibility parsing of external reviewer flair/reaction output for required-check authority;
- same-head recheck machinery whose sole purpose is to make the required AI-review parser become green;
- `merge-group-ai-review-adapter.yml` once `ai-review-gate` is no longer required.

Retirement must be evidence-based. A mechanism that protects a separate privilege boundary, deployment credential, production mutation or supply-chain invariant is not removed merely because Merge Queue exists.

### 6. Keep high-value low-friction safeguards

The following remain baseline controls:

- PR required before protected `main` integration;
- squash merge / linear history;
- force-push disabled on `main`;
- branch deletion disabled on `main`;
- deterministic provider-owned CI;
- one stable aggregate gate;
- Merge Queue integration validation;
- secret scanning and push protection where available;
- Dependabot security/dependency updates where applicable;
- CodeQL/code scanning where useful for supported code;
- immutable full-SHA pinning for GitHub Actions;
- least-privilege `GITHUB_TOKEN` permissions;
- no candidate-controlled workflow with privileged write authority unless its trust model explicitly and safely permits it;
- explicit break-glass recovery design for a one-owner repository, instead of an absolute no-bypass model that can permanently lock the sole owner out of repairing the required gate itself.

### 7. Product validation outranks process-format validation

Required CI should answer whether a candidate is correct and safe enough to integrate.

Administrative conventions such as exact PR title length or mandatory `## Summary` / `## Scope` / `## Validation` headings may remain templates, lint warnings or contributor guidance, but should not normally be a hard merge blocker for a one-person project.

This specifically applies to the current Game merge gate, which mixes substantial product/security validation with PR metadata formatting requirements.

## Repository-specific target state

### META

Keep:

- `meta-gate` as the sole required external status;
- repository contract, JSON/schema validation, governance drift validation and other deterministic META checks that still catch real defects;
- `merge_group` candidate validation in META CI;
- least-privilege and action pinning controls.

Change:

- remove `ai-review-gate` from required status contexts after replacement safety is proven;
- keep AI review as risk-based advisory/owner evidence instead of independent merge authority;
- retire `merge-group-ai-review-adapter.yml` after it has no required consumer;
- retire review envelope/attestation/fingerprint bridge machinery that exists only to connect the old AI-review authority to Merge Queue;
- simplify `ecosystem/ai-review-policy.json` to the policy that remains useful after this retirement.

### Game

Keep:

- `game-gate` as the sole required external status;
- dependency review, CodeQL and real Rust/Linux/Windows/product tests as applicable;
- squash/linear-history/force-push/deletion protections;
- CODEOWNERS as ownership/risk metadata if desired.

Change:

- remove required CODEOWNER approval;
- retain required approval count at zero;
- extend/refactor `merge-gate.yml` so the aggregate gate is valid for both PR and `merge_group` candidates;
- remove strict freshness after a real Merge Queue canary;
- make PR title/body convention checks advisory rather than merge-blocking.

### Platform

Keep:

- `platform-gate` as the sole required external status;
- the current provider-owned test surface;
- conservative fail-closed merge-group behavior where exact PR-specific classification data is unavailable.

Change only where evidence requires it:

- verify a real Merge Queue canary on `platform-gate`;
- prefer running somewhat broader CI for merge groups over adding a complex optimizer solely to save CI minutes;
- remove strict freshness only after canary success and readback.

Platform is currently closest to the target external-gate model and should not be redesigned unnecessarily.

### Atlas

Keep:

- extraction provenance validation while it remains a real migration/source-integrity invariant;
- deterministic semantic/browser/project/E2E validation;
- `atlas-gate` as the sole required external status.

Change:

- make provenance an internal dependency of `atlas-gate` rather than a second branch-protection required context;
- ensure Atlas aggregate CI handles `merge_group` without weakening PR-only risk classification or E2E requirements;
- after Atlas migration is formally terminal, separately determine whether provenance still needs to run on every PR or can move to a narrower lifecycle.

## Desired-state changes

The canonical desired-state model must change before live settings change, otherwise the existing drift validator will correctly classify the simplified live state as a regression.

`ecosystem/governance-desired-state.json` should converge to:

- one required external check per permanent repository;
- `strict_required_status_checks = false` only after the corresponding Merge Queue canary is proven;
- no requirement for CODEOWNER approval in the solo-maintainer baseline;
- explicit Merge Queue state once the schema/validator is extended to represent it;
- preservation of main protection, squash-only, force-push/deletion blocking and the applicable security baseline.

The desired state should stay small. It should not encode transient PR heads, review-generation identifiers, external reviewer output grammar or implementation details of internal provider jobs.

## Cutover strategy

Do not perform a big-bang organization-wide mutation.

The safe sequence is:

1. merge this design and its implementation plan as documentation only;
2. update the canonical ADR/desired-state/tests in META to define Solo-Maintainer Governance V2;
3. make all replacement aggregate gates merge-group safe while preserving existing protections;
4. cut over **META → Game → Platform → Atlas** serially;
5. for each repository, run a real canary through the actual Merge Queue;
6. only after the canary produces the expected aggregate gate on the synthetic merge-group candidate and integrates correctly, remove strict freshness/obsolete required contexts for that repository;
7. read back protected-main settings after every mutation;
8. if the canary fails, restore the previous settings and repair the workflow — do not create no-op commits or new governance exceptions merely to retrigger;
9. after all repositories are stable, remove superseded review/fingerprint/bridge machinery and clean historical documentation/issues as `SUPERSEDED`, not erased.

## Break-glass principle

A one-owner repository needs a recovery path for the case where the required workflow itself is broken.

The normal path must remain protected and non-bypassable during ordinary work. However, the design must include one narrow, auditable owner break-glass transaction with all of the following properties:

- invoked only for repair of the protection/gate control plane when normal protected integration is impossible;
- exact target repository and expected candidate/head bound;
- smallest possible protection relaxation;
- one bounded repair transaction;
- immediate restoration of the previous protection;
- positive settings readback after restoration;
- durable receipt in the relevant Issue/PR;
- never used merely to avoid a legitimate failing product/security test.

The exact mechanism must be selected from the live GitHub capabilities visible at implementation time. This design does not assume a bypass API that has not been verified.

## Explicit non-goals

This design does not:

- remove PRs;
- permit normal direct pushes to `main`;
- permit force-push or deletion of `main`;
- remove deterministic tests;
- remove security scanning, dependency review or CodeQL where they are useful;
- remove Atlas provenance while it remains a real source-integrity requirement;
- make production/deployment/secret changes;
- centralize provider test implementations into META;
- optimize CI throughput for a large engineering organization that Oteryn does not currently have;
- require organization-wide required-workflow infrastructure merely to imitate enterprise separation-of-duties in a one-person team.

## Definition of done

Solo-Maintainer Governance V2 is terminal only when all applicable conditions are directly verified from live state:

- META requires only `meta-gate` for normal protected integration;
- Game requires only `game-gate`;
- Platform requires only `platform-gate`;
- Atlas requires only `atlas-gate`;
- each required aggregate gate runs and passes on both a representative PR and a real `merge_group` synthetic candidate;
- Merge Queue is the normal integration authority for all four permanent repositories;
- strict branch freshness is disabled in each repository only after its Merge Queue canary succeeds;
- Game no longer requires CODEOWNER approval from a nonexistent second human;
- force-push and deletion of `main` remain blocked;
- squash/linear-history policy remains enforced;
- obsolete required `ai-review-gate` and `provenance-gate` contexts are removed only after their useful safety semantics are either retired or internalized into the aggregate gate;
- old review-fingerprint/envelope/attestation bridge machinery is removed or explicitly retained with a documented independent threat that still justifies it;
- desired-state validation agrees with live settings;
- no temporary bypass remains active;
- a documented, tested owner break-glass recovery contract exists;
- all superseded design material is marked as historical/superseded so future agents do not reintroduce the old moving-head model.

## Decision summary

The security boundary should move from a large procedural review-evidence control plane to a smaller set of direct invariants:

```text
feature branch
    -> PR
    -> provider deterministic validation
    -> one stable aggregate gate
    -> Merge Queue
    -> same aggregate gate on the synthetic integration candidate
    -> squash into protected main
```

For a one-person Oteryn organization, this model is more appropriate than mandatory peer-approval semantics or a cryptographic evidence bridge built primarily to survive moving-head freshness loops.

The expected outcome is fewer deadlocks, fewer bootstrap exceptions, less agent context spent reconstructing governance history, and stronger focus on controls that directly protect code, credentials, dependencies and integration correctness.
