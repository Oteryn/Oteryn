# Organization Merge Queue + Review Fingerprint Integration Design

**Status:** approved target architecture for Issue #102; implementation is not canonical until the relevant META and provider PRs merge to protected `main`.

## Problem

Oteryn currently has several individually sensible safety rules that can combine into a retry loop:

1. a PR candidate passes deterministic CI and external review;
2. protected `main` advances;
3. strict branch freshness forces a merge-up/update of the PR branch;
4. the PR head SHA changes;
5. local repository policy or prompt wording treats the new SHA as automatic loss of review qualification;
6. the full CI/review cycle repeats even when the risk-bearing candidate did not materially change.

The opposite extreme is also unsafe: accepting old CI/review after arbitrary candidate changes can merge code that was never tested or reviewed in its final integration context.

The organization needs one system-level distinction between **candidate qualification** and **integration qualification**.

## Decision

Adopt this organization-wide model for `Oteryn/Oteryn`, `Oteryn/Oteryn-Game`, `Oteryn/Oteryn-Platform` and `Oteryn/Oteryn-Atlas`:

1. **PR candidate head** owns implementation, deterministic PR checks, risk classification and external review.
2. **Review qualification** is bound to the META risk-bearing `review_fingerprint`, not to SHA equality alone.
3. **GitHub Merge Queue** is the default protected-`main` integration authority.
4. **Merge-group integration head** (`latest trusted main + candidate`) must pass the repository's required deterministic integration gate.
5. A `main` advance by itself does not force a new external review. Review is reused only when the machine policy proves the same tier/fingerprint and all ancestry/review-neutral/trusted-base conditions.
6. A change to risk-bearing candidate content or a base change that changes the risk-bearing fingerprint requires fresh external review.
7. Empty/no-op/checkpoint/retrigger commits are forbidden as evidence-refresh mechanisms.
8. P0/P1 findings are merge-blocking. P2 findings are non-blocking follow-up unless the finding actually proves a merge-blocking security, authority, durability, contract or acceptance-invariant violation; such a finding must be escalated to P1 instead of creating an unbounded P2 repair loop.

## Terminology

### Candidate head

The exact PR head SHA containing the task author's changes. It is the source for:

- TDD RED/GREEN evidence;
- author self-review;
- risk classification;
- external AI review request/evidence;
- candidate-local deterministic tests.

### Review fingerprint

The META-computed identity of the complete risk-bearing diff plus the relevant trusted-base identities required by the canonical AI-review policy.

A SHA change is not itself evidence that review became invalid. The fingerprint/ancestry policy decides that.

### Integration head

The synthetic GitHub Merge Queue `merge_group` candidate containing the current trusted `main` plus the candidate PR (and, by default for Oteryn, no additional unrelated PR in the same merge group).

This is the exact code combination that is eligible to enter protected `main`.

## Safety invariants

### Deterministic checks

Required repository checks remain exact-integration-head requirements. A prior PR-head build is not a substitute for a required `merge_group` build when the repository uses Merge Queue.

Each required gate must support both:

- `pull_request` for candidate qualification; and
- `merge_group` for integration qualification.

The final required status reported to the Merge Queue must prove the exact merge-group SHA it evaluated.

### External review

External review must not be rerun merely because `main` advanced or a clean trusted-base integration merge changed SHA.

Reuse is permitted only when the canonical META verifier proves all applicable conditions, including:

- reviewed head ancestry;
- same review tier;
- identical review fingerprint;
- only configured review-neutral task commits after review, except for the explicitly validated clean trusted-base integration sequence;
- final deterministic checks green.

If the risk-bearing fingerprint changes, fresh review is mandatory.

The merge-group gate must verify that external review evidence still qualifies the integration candidate under the same canonical reuse rules. A reviewed PR head does not automatically qualify an integration head.

### Review severities

- **P0:** blocking.
- **P1:** blocking.
- **P2:** non-blocking improvement/follow-up by default.

A reviewer must not label a merge-blocking correctness/security/authority defect as P2 merely to avoid blocking. If a P2 is deferred, create or link a durable follow-up Issue and resolve the PR thread as an explicit policy-compliant deferral; do not leave required review-thread resolution ambiguous.

### Protected branch

The target protected branch keeps:

- pull-request-only ordinary integration;
- required status checks;
- squash merge / linear history policy;
- force-push/deletion protections as applicable;
- required review-thread resolution;
- CODEOWNERS/human approval requirements where repository policy needs them.

Once Merge Queue is proven and required for `main`, disable strict `Require branches to be up to date before merging`. Merge Queue, not repeated author merge-ups, owns latest-main integration testing.

`expected_head_sha` remains useful for exceptional direct merge APIs where repository policy permits direct merge, but it is not the primary integration mechanism once Merge Queue is required.

## Merge Queue standard

Use Merge Queue as the normal integration path for all four active Oteryn repositories.

Initial safety configuration:

- merge method: squash;
- one PR per merge group unless later measured evidence justifies batching;
- required repository aggregate gate must run for `merge_group`;
- do not enable queue-required enforcement until the merge-group workflow has been proven on a canary;
- do not disable strict branch freshness until queue-required enforcement is active and verified.

A queue candidate that becomes invalid because trusted `main` changes again should be rebuilt/re-evaluated by GitHub. Agents must not mutate the task branch merely to wake the queue.

## Anti-loop execution semantics

The organization bounded-autonomous policy remains responsible for execution lifecycle:

- stable candidate freeze before scarce review/final qualification;
- `WAITING_EXTERNAL` when CI/review/queue evidence is pending and no material work remains;
- `STALLED` after bounded identical-failure retry exhaustion;
- same-head re-evaluation for asynchronous review/check evidence where supported;
- no empty/no-op/checkpoint/retrigger commits;
- progress/failure fingerprints exclude timestamps and narration.

META #69 / PR #71 are historical/live locators for this policy family and must be refreshed before implementation. Do not assume their current state from this design.

## Authority model

META owns the semantics of:

- review tiers and risk fingerprint;
- review reuse/invalidation;
- blocking severity meaning;
- candidate vs integration-head distinction;
- bounded autonomous retry semantics;
- Merge Queue integration invariants;
- provider conformance requirements.

Game, Platform and Atlas may configure only repository-specific facts such as:

- aggregate required check names;
- additional R2 path triggers;
- runner/test requirements;
- repository-specific merge-group validation.

They must not fork the organization rules for head invalidation, review reuse or anti-loop behavior.

Prefer a META-owned versioned machine policy/reusable action plus thin provider configuration. Local prose may summarize but must not become a competing policy source.

## Required provider behavior

For every active provider repository:

1. required aggregate CI supports `pull_request` and `merge_group`;
2. event parsing does not assume `github.event.pull_request` exists in a `merge_group` run;
3. candidate and merge-group SHA/base identities are validated fail-closed;
4. external-review gate consumes canonical META fingerprint evidence rather than local exact-SHA-only logic;
5. branch/ruleset settings require Merge Queue after canary proof;
6. strict up-to-date-before-merge is disabled after queue enforcement is active;
7. no prompt/task may instruct an agent to merge-up solely because `main` moved when Merge Queue can perform final integration;
8. no prompt/task may require fresh external review solely because a SHA changed if canonical fingerprint reuse succeeds.

## Rollout order

Use staged migration, never a flag-day weakening of protection:

1. refresh and terminalize/supersede the bounded-autonomous META work without duplicating it;
2. publish canonical META merge-integration semantics and deterministic tests;
3. add `merge_group` support to META required gates and prove a canary;
4. enable META Merge Queue and switch off strict branch freshness only after proof;
5. repeat provider adoption in Game, Platform and Atlas, allowing independent provider work where paths and settings are disjoint;
6. add an organization drift audit comparing expected policy with live repository settings/workflow capabilities;
7. remove/supersede stale local exact-head-only review language and close provider adoption Issues.

## Failure handling

- If `merge_group` CI fails because of an integration conflict/semantic regression, return to the candidate owner with the exact failure. A real risk-bearing repair changes fingerprint and triggers fresh review as required.
- If queue evidence is merely delayed, enter `WAITING_EXTERNAL`; do not commit to retrigger.
- If an unrelated base advance preserves the fingerprint, reuse review and let the queue rebuild the integration candidate.
- If a trusted-base change touches a reviewed risk-bearing path and changes fingerprint, require fresh review.
- If Merge Queue is unavailable for a repository/account capability reason, record the exact capability gap. Do not silently weaken integration safety; use the existing strict-up-to-date model only as an explicit temporary fallback until the capability exists.

## Current observed basis — locators only

At design time (2026-08-30), live inspection showed:

- META protected `main` already contains risk-based AI-review fingerprint/reuse semantics, including unrelated-base-advance reuse under strict conditions;
- META bounded-autonomous PR #71 was still open and Game adoption Issue #148 was still open;
- Game `main` ruleset required `game-gate`, used strict required-status freshness, squash-only integration and stale-review dismissal on push;
- Game `merge-gate.yml` was `pull_request`-specific and therefore requires explicit `merge_group` adaptation before Merge Queue can safely replace strict freshness.

These observations are not future authority. Every execution agent must refresh live GitHub before acting.

## Non-goals

- no product runtime behavior change;
- no deployment/production/secret/live-data mutation;
- no weakening of required tests or review authority;
- no assumption that a reviewed PR head alone proves latest-main integration safety;
- no organization-wide requirement to rerun expensive external review for non-risk-bearing SHA churn.

## Acceptance criteria

The programme is complete only when:

- all four active Oteryn repositories use the same canonical META candidate/integration/review semantics;
- Merge Queue is required for protected `main` where supported;
- required aggregate checks pass on merge-group candidates;
- strict up-to-date-before-merge is no longer the normal author/agent integration mechanism;
- fingerprint reuse works across qualifying unrelated `main` advances;
- fingerprint changes still force fresh review;
- P0/P1 block and P2 follow-up behavior is deterministic;
- no-op/retrigger loops are deterministically prohibited;
- live configuration drift is detectable;
- canary PRs prove the end-to-end flow before old protections are removed.
