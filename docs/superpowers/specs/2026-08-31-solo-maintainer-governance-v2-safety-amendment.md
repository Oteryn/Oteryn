# Solo-Maintainer Governance V2 — Safety Amendment

## Status

**PROPOSED BINDING AMENDMENT FOR PR #123.**

If merged with PR #123, this amendment is normative for implementation of `Solo-Maintainer Governance V2` and supersedes any conflicting or weaker clause in:

- `docs/superpowers/specs/2026-08-31-solo-maintainer-governance-v2-design.md`
- `docs/superpowers/plans/2026-08-31-solo-maintainer-governance-v2.md`

This amendment does not authorize live GitHub settings changes by itself. Live GitHub state remains the source of truth, and every mutation still requires the staged canary/readback/rollback sequence in the implementation plan.

## Purpose

The V2 architecture is intentionally simpler than the historical moving-head/review-evidence control plane. This amendment prevents that complexity from regrowing and closes four specific future-risk classes:

1. aggregate required gates being satisfied through `skipped`/`neutral` behavior or incomplete fan-in;
2. Merge Queue adoption being declared successful without proving the exact moving-base failure mode that V2 exists to eliminate;
3. candidate-controlled governance changes autonomously authorizing themselves;
4. temporary rollout exceptions becoming permanent hidden state.

The objective is not more governance. The objective is a small set of invariants that bound future governance complexity.

## Global Safety Contract

The following invariants are mandatory across all permanent Oteryn repositories.

### GS-1 — No moving-head governance dependency

No protected workflow, policy, agent instruction or rollout procedure may require merge/rebase of protected `main` into an otherwise stable PR solely to satisfy freshness after Merge Queue has been proven for that repository.

A base advance by itself must not require mutation of the PR head. Integration freshness belongs to Merge Queue and its synthetic candidate.

### GS-2 — No mandatory second-human dependency in solo-maintainer mode

While Oteryn has exactly one human maintainer:

- `required_approving_review_count` must remain `0` for the baseline;
- required CODEOWNER approval must be disabled;
- no governance path may assume a second human approval exists.

CODEOWNERS may remain as ownership/risk metadata.

### GS-3 — Required aggregate gate cannot pass via `skipped` or `neutral`

Each permanent repository has exactly one externally required aggregate gate:

- META: `meta-gate`
- Game: `game-gate`
- Platform: `platform-gate`
- Atlas: `atlas-gate`

The aggregate gate MUST:

- always be created for every protected `pull_request` and `merge_group` candidate;
- always execute;
- terminate explicitly as `success` or `failure`;
- never intentionally satisfy branch protection through `skipped` or `neutral`;
- run with `if: always()` or an equivalent fail-closed topology so dependency failure does not suppress the final gate;
- explicitly evaluate every internal job that is required for that candidate;
- fail on missing, cancelled, timed-out, unexpected or otherwise unknown required internal-job state;
- accept an internal `skipped` state only when a deterministic applicability contract proves that job is `NOT_APPLICABLE` for that candidate.

A path filter or conditional internal job must therefore expose an explicit applicability result that the final aggregate gate consumes. Absence of execution is not itself proof of non-applicability.

### GS-4 — No governance retrigger/no-op commits

No empty, no-op, checkpoint-only, formatting-only, merge-up-only or otherwise materially irrelevant commit may be created solely to retrigger CI, review, Merge Queue or governance state for an unchanged candidate.

Asynchronous evidence must be handled through same-head/event-driven mechanisms, normal GitHub re-evaluation, or an explicitly bounded owner-approved recovery action.

### GS-5 — Control-plane changes cannot autonomously self-authorize

A candidate may not become merge-authoritative solely because the candidate-controlled version of the governance mechanism under change reports success.

This rule applies at minimum to changes affecting:

- `.github/workflows/**`;
- aggregate gate definitions or their required fan-in logic;
- branch protection, rulesets or Merge Queue configuration;
- `ecosystem/governance-desired-state.json`;
- GitHub Actions permissions or token trust boundaries;
- break-glass machinery;
- authentication/security/deployment control-plane surfaces where a candidate could change the mechanism that authorizes its own integration.

For these R2/control-plane changes, autonomous terminal merge requires all of:

1. deterministic candidate validation;
2. an independent deep review of the exact material change;
3. explicit owner authorization for integration of that control-plane change;
4. Merge Queue integration validation where the repository has completed MQ cutover.

The independent review is evidence for owner decision-making, not a fragile required status based on parsing reviewer comments/reactions.

Where candidate-controlled workflow code could otherwise grant itself privileged write authority, trusted-base/default-branch execution boundaries must be preserved or an equivalent independently trusted mechanism must be demonstrated.

### GS-6 — Every `TRANSITION` is bounded and expiring

`TRANSITION` is never an open-ended compliance state.

Every authorized transition record must include at least:

```text
transition_id
repository
issue_or_pr
started_at
expires_at
pre_state_fingerprint
allowed_deviations
success_condition
rollback_condition
```

Optional owner metadata may be included but must not become a second identity authority.

On terminal success or rollback/closure, the receipt must append machine-readable `terminal_status` (`SUCCESS` or `ROLLED_BACK`), `closed_at`, `post_state_fingerprint`, and `post_state_readback`. Terminal evidence is valid only when `closed_at <= expires_at`; a late closure is `DRIFT`, not a retroactively valid terminal state. The auditor must recompute `post_state_fingerprint` from the readback. For `SUCCESS`, it must also prove the readback matches the repository's desired target and that the receipt's `success_condition` is satisfied by the complete GS-7 moving-base canary evidence, including unchanged candidate head, intervening `main` advance, exact merge-group SHA, successful aggregate-gate run, and resulting protected-main integration. A self-declared status, a free-form success note, or a passing normal PR check is insufficient. The auditor must use these fields and direct GitHub evidence, not expiry passage or free-form prose, to distinguish a closed receipt from an active deviation. These fields are evidence for the existing receipt and read-only auditor, not a new governance authority, required status or database.

A transition record belongs in the canonical rollout Issue/PR or another existing durable lifecycle authority. It must not create a new permanent transition database unless a separate threat/operational requirement justifies one.

If `now > expires_at` and the transition has not reached its success condition or been explicitly rolled back/closed with valid, timely (`closed_at <= expires_at`) terminal evidence, the read-only auditor must classify the state as `DRIFT`, not `TRANSITION`.

A repository whose serial cutover has not begun is `PENDING`, not `TRANSITION` or `DRIFT`, only when the canonical rollout Issue/PR records a direct-readback pending baseline with `repository`, `captured_at`, `pre_state_fingerprint`, and `pre_state_readback`. The read-only auditor must recompute the baseline fingerprint and compare current live state to it; a missing, malformed, or mismatching baseline is `DRIFT`. The baseline is not a transition receipt and authorizes no V2 settings deviation. `PENDING` cannot satisfy target or terminal closeout and becomes `TRANSITION` only after a fresh matching readback and that repository's own bounded receipt exist immediately before its cutover.

A failed cutover is `ROLLED_BACK`, not `TRANSITION`, only when its closed receipt has `terminal_status = ROLLED_BACK`, timely `closed_at <= expires_at`, `post_state_fingerprint` matches `pre_state_fingerprint`, and positive `post_state_readback` proves restoration. `ROLLED_BACK` is terminal non-target evidence, authorizes no continued deviation or terminal closeout, and any retry requires a new bounded receipt; a missing or mismatched restoration proof is `DRIFT`.

### GS-7 — MQ canary must include a moving-base scenario

Before disabling strict branch freshness for a repository, a normal merge-group canary is insufficient. The repository must prove the exact historical failure mode V2 is intended to remove.

Required scenario:

```text
PR A reaches a green stable head X
PR B integrates into main after A is green
PR A head remains exactly X
PR A enters Merge Queue without merge/rebase of new main into A
Merge Queue creates a synthetic candidate using the advanced target state
required aggregate gate runs on that synthetic candidate
required aggregate gate terminates SUCCESS
PR A integrates through the queue
```

The canary receipt must record A's unchanged head SHA, the intervening `main` advance, the synthetic merge-group SHA, the aggregate-gate run, and the resulting integrated `main` commit.

Strict freshness may be disabled only after this scenario succeeds and live settings readback is green.

### GS-8 — Break-glass restoration must be independently verifiable

The owner break-glass contract must include:

- capability discovery/readback on the current GitHub plan;
- a non-destructive dry-run of the exact UI/API path;
- one real isolated exercise on a safe canary surface before the mechanism is declared `TESTED`;
- exact pre-state capture;
- minimal bounded relaxation;
- one bounded recovery transaction;
- immediate restoration;
- positive post-restore readback;
- durable receipt.

The real exercise must not be performed for the first time on production `main`. A temporary protected test branch, canary ruleset/surface or equivalently isolated mechanism must be used.

Break-glass remains forbidden for bypassing a legitimate failing product, security, dependency, provenance or integration test.

### GS-9 — Exactly one externally required aggregate gate per permanent repository

A new blocking check must normally be wired into the repository's existing aggregate gate rather than added as another branch-protection/ruleset required context.

Adding a second externally required status is allowed only if a separately documented threat model proves that the control cannot safely or meaningfully be represented inside the aggregate gate. The default answer is to internalize it.

This invariant specifically prevents recurrence of independent external `ai-review-gate` / `provenance-gate` style layering when the underlying safety semantics can be represented by the aggregate gate or owner decision contract.

### GS-10 — New governance mechanisms require explicit threat justification

No new governance mechanism may be introduced merely because it is theoretically stronger, more enterprise-like, or described as generic defense in depth.

Every proposed new blocking mechanism must document:

```text
threat
existing controls that do not cover it
minimal new invariant/control
failure mode if omitted
operational cost / owner friction
retirement condition, if transitional
```

If the same threat is already adequately covered by an existing invariant, Merge Queue, deterministic CI, security scanning, owner confirmation or break-glass recovery, the new mechanism must not be added.

## Anti-Regression Prohibitions

The following are specifically prohibited unless a future reviewed amendment documents an independent threat that cannot be handled by the V2 controls:

- forcing merge/rebase of `main` into a stable PR solely for freshness;
- head-changing or no-op/retrigger commits solely for governance progression;
- mandatory self-review/CODEOWNER approval in solo-maintainer mode;
- externally required statuses whose pass/fail authority depends on parsing reviewer comments, reactions, presentation phrases or transient review-product grammar;
- transient review generation/fingerprint/envelope identifiers as normal branch-protection merge authority;
- adding another required external status instead of integrating the underlying blocking result into the aggregate gate;
- unbounded `TRANSITION` or exception states;
- candidate-controlled privileged workflow mutation authority without an independently trusted control-plane boundary;
- preserving transitional machinery after its documented threat/transition has ended.

## Aggregate Gate Contract

For each repository, the final aggregate job must use a deterministic fan-in contract with three concepts:

```text
APPLICABLE_PASS
NOT_APPLICABLE
BLOCKING_FAILURE
```

Every potentially blocking internal validation must be mapped to one of those states by explicit logic.

The final aggregate gate then applies:

```text
all required applicable validations == APPLICABLE_PASS
and every non-applicable validation has explicit NOT_APPLICABLE evidence
and no required validation is missing/unknown/cancelled/timed-out
=> SUCCESS

otherwise
=> FAILURE
```

The implementation may use repository-appropriate scripts/YAML, but the semantics above are invariant.

## Control-Plane Owner Confirmation Contract

For R2 control-plane changes covered by GS-5, owner authorization must be explicit and bound to the current material candidate. It may be recorded in the canonical PR/Issue or another existing authenticated GitHub surface.

It must identify at least:

```text
repository
pull_request
current material head (or equivalent immutable candidate coordinate)
control-plane scope being changed
owner authorization to integrate this change
```

A later material change invalidates that authorization. A pure target-base advance handled by Merge Queue does not require mutating the PR head solely to recreate authorization.

This contract intentionally does not require a second human, cryptographic review-envelope bridge, reviewer-flair parser or separate required AI-review status.

## Rollout Consequences

The implementation plan must treat the Global Safety Contract as project-wide acceptance criteria.

In particular:

- GS-3 must be proven by deterministic workflow-contract tests in all four repositories;
- GS-7 must be proven by a real moving-base canary before strict freshness is disabled in each repository;
- GS-5 must be used for every V2 task that changes the merge/control-plane mechanism itself;
- GS-6 transition expiry must be recognized by the read-only drift auditor;
- GS-8 must complete before final V2 closeout;
- GS-9/GS-10 must be checked during cleanup so legacy required contexts or new replacement layers do not survive without independent justification.

## Definition of done amendment

V2 cannot be declared terminal until, in addition to the original design's criteria:

- all four externally required aggregate gates have been proven to execute and terminate explicitly rather than satisfy protection through `skipped`/`neutral`;
- all four repositories have completed a moving-base MQ canary with unchanged PR head;
- no active transition is expired;
- no permanent repository remains `PENDING` or `ROLLED_BACK` at terminal closeout;
- no control-plane change in the rollout was terminally self-authorized only by its candidate-controlled governance implementation;
- the owner break-glass contract has passed one real isolated exercise and post-restore readback;
- exactly one externally required aggregate gate remains per permanent repository;
- every retained nontrivial governance mechanism has a documented current threat justification.

## Rationale

This amendment deliberately prefers a small number of strong invariants over additional services, databases, attestations or workflow layers.

The security model remains:

```text
PR
-> deterministic provider validation
-> one explicit aggregate gate
-> Merge Queue synthetic integration validation
-> protected squash integration
```

with an explicit owner decision boundary only for rare control-plane/self-modifying changes.

The intended result is a governance system that is hard to accidentally weaken but also hard to accidentally overgrow.
