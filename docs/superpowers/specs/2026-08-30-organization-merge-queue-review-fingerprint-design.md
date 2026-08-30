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
4. **Merge-group integration head** (`latest trusted main + candidate`) must be qualified by a META-owned organization-ruleset workflow whose source is protected META `main`; a workflow definition taken from the synthetic/candidate tree is not merge authority.
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

Required coverage must include both:

- `pull_request` for candidate qualification; and
- the protected-source ruleset workflow on `merge_group` for integration qualification.

The final required result reported to the Merge Queue must prove the exact merge-group SHA it evaluated. Configure the bridge with the ruleset's **Require workflows to pass before merging** rule, identified by source repository and workflow path, not as a loose required-status name that a candidate workflow could reproduce.

### Trusted merge-group qualification bridge

The integration authority is a META-owned organization-ruleset workflow triggered directly by `merge_group: checks_requested`. Its workflow and verifier are loaded from protected META `main` (the trusted source SHA `T`) and protected by the same R2/CODEOWNERS rules as the existing AI-review gate. Target-repository `merge_group` workflows execute from the synthetic tree and are candidate-controlled; they may provide non-authoritative diagnostics, but their conclusion alone cannot qualify the integration head.

The bridge uses these exact identities:

- `B`: `github.event.merge_group.base_sha`, the trusted base selected by the queue;
- `I`: `github.event.merge_group.head_sha`, the exact synthetic integration head and required-result target;
- `P`: the one same-repository, open, non-draft PR in the merge group;
- `C`: the current exact head of `P` recorded by its active queue entry;
- `R`: the externally reviewed head carried by the trusted review evidence;
- `Q`: the exact protected-base workflow/policy source recorded by the PR #111 review envelope when candidate qualification was issued;
- `T`: the protected META source SHA that supplied the ruleset workflow, policy and verifier.

The initial queue configuration is `maximumEntriesToMerge = 1`. On every run the trusted bridge must:

1. require `checks_requested`, exact repository ID/name, `refs/heads/main`, full SHAs and `github.sha == I`; re-fetch its own workflow run, jobs and check suite and require event `merge_group`, the configured source workflow identity and `check_suite.head_sha == I`;
2. call the paginated REST `GET /repos/{owner}/{repo}/commits/{I}/pulls` endpoint and require exactly one result; server-fetch that PR and cross-check its repository/object ID, number, state, Draft flag, base branch and `head.sha == C` with GraphQL `PullRequest.mergeQueueEntry`, including entry identity, `baseCommit == B`, `headCommit == C` and the live single-PR queue configuration;
3. fetch only `B`, `C`, `I` and required historical review objects into a credential-free bare Git object store; require `B` to be a protected-main ancestor, `C` and `B` to be ancestors of `I`, and `tree(I)` to equal the conflict-free merge tree independently reproduced from exactly `B + C` under the canonical clean-integration rule;
4. locate the unique non-superseded PR #111-format review-envelope artifact through the server-derived trusted `pull_request_target` run/attempt for `P` and `C`; verify the artifact digest, canonical JSON, predicate type, repository/PR IDs, policy/classifier digests, evidence source and GitHub attestation constrained to the envelope's signer workflow/ref/digest `Q`, then prove `Q` was a protected trusted source allowed by policy at issuance. The rollout must persist that immutable artifact plus its run/attempt and envelope digest from the trusted gate; a missing, expired, deleted, duplicate or ambiguous locator fails closed and is recovered only by a same-head trusted re-evaluation, never a candidate commit;
5. run the canonical reuse verifier from `T`: prove `R` is the attested reviewed ancestor of `C`, all `R..C` changes are permitted, `C` is the queued candidate inside `I`, the trusted-base lineage is valid, and classification of the exact `B..I` integration diff has the same tier and `review_fingerprint` as the attested qualification. A changed risk-bearing base/candidate, non-reproducible tree or any P0/P1 fails;
6. run the protected-base provider aggregate test contract against a credential-free checkout of exact `I` in a separate unprivileged test job. A fresh trusted mediator job must never execute candidate code or consume candidate artifacts/caches; it re-fetches the test job/check conclusion and exact head from the Actions API, then emits and immediately verifies a PR #111-compatible integration envelope binding `T`, `Q`, repository/PR IDs, `B`, `C`, `R`, fingerprint, `I`, run/attempt/job/check-suite IDs and deterministic results.

GitHub associates the required ruleset-workflow check suite with `I`; the workflow must assert that association before success. A skipped, cancelled, missing or non-success bridge run blocks the queue. Candidate workflows and the integration test job never receive `checks: write`, `statuses: write`, `id-token: write`, `attestations: write` or secrets. Only the isolated mediator job receives `actions: read`, `checks: read`, `contents: read`, `issues: read`, `pull-requests: read` and, solely for its own integration envelope, `id-token: write`, `attestations: write` and `artifact-metadata: write`; it does not need `contents: write`, `checks: write` or `statuses: write` because the ruleset workflow result is published by GitHub Actions.

If organization ruleset workflows or the required cross-repository source-workflow access are unavailable, treat that as a capability blocker and keep strict freshness. Do not fall back to a candidate workflow or a same-name status. An alternative requires a separately reviewed dedicated GitHub App with its own expected-source App ID and the same server-side validations; it is not an implicit fallback in this rollout.

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
- the trusted META ruleset workflow, not a candidate-local gate, is the required `merge_group` authority;
- first merge and read back the ruleset workflow, verifier and provider contract from protected `main`;
- then enable and require Merge Queue while strict branch freshness remains enabled;
- enqueue one live canary, prove the required bridge result on its exact `I`, and read back the protected-main merge;
- only after that proof disable strict branch freshness.

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

### Operator mutation authorization

Before any branch, PR or settings mutation in Game, Platform or Atlas, the operator must record explicit authorization granted for the current task, naming the exact repository and permitted mutation scope. Listing a repository as a rollout target, META policy ownership, an existing Issue/PR, or available tool/admin access is context or capability, not authorization. A current user instruction that explicitly authorizes all four repositories may be recorded as satisfying this gate for its stated scope, but reusable rollout documents must never infer or carry that authorization forward.

A provider without this recorded authorization remains read-only: inventory its live state, record the missing authority and hand off to its owner. It must not enter provider branch/PR work or settings/cutover phases.

META owns the semantics of:

- review tiers and risk fingerprint;
- review reuse/invalidation;
- blocking severity meaning;
- candidate vs integration-head distinction;
- bounded autonomous retry semantics;
- Merge Queue integration invariants;
- provider conformance requirements.

Game, Platform and Atlas may configure only repository-specific facts such as:

- aggregate test contracts and diagnostic check names;
- additional R2 path triggers;
- runner/test requirements;
- repository-specific merge-group validation.

They must not fork the organization rules for head invalidation, review reuse or anti-loop behavior.

Prefer a META-owned versioned machine policy/reusable action plus thin provider configuration. Local prose may summarize but must not become a competing policy source.

## Required provider behavior

For every active provider repository:

1. candidate CI supports `pull_request`, while the protected META ruleset workflow is the required `merge_group` authority;
2. bridge event parsing does not assume `github.event.pull_request` exists and uses the REST commit association plus GraphQL queue entry to resolve exactly one PR;
3. candidate, reviewed, base and integration SHA identities are validated fail-closed, including reproducible single-PR merge-tree proof;
4. the bridge consumes and verifies the canonical META attestation/evidence and fingerprint rather than local exact-SHA-only logic;
5. the organization ruleset binds the required workflow by protected source repository/path, not by a spoofable status name;
6. branch/ruleset settings require Merge Queue during the canary while strict freshness is still enabled;
7. strict up-to-date-before-merge is disabled only after the live canary merge and protected-main readback succeed;
8. no prompt/task may instruct an agent to merge-up solely because `main` moved when Merge Queue can perform final integration;
9. no prompt/task may require fresh external review solely because a SHA changed if canonical fingerprint reuse succeeds.

## Rollout order

Use staged migration, never a flag-day weakening of protection:

1. refresh and terminalize/supersede the bounded-autonomous META work without duplicating it;
2. publish canonical META merge-integration semantics and deterministic tests;
3. merge and read back the protected META ruleset workflow, attestation bridge and deterministic event/API fixtures while strict freshness remains active;
4. enable/require META Merge Queue with one-PR groups while strict freshness remains active, enqueue a live canary, verify exact-`I` bridge success and protected-main readback, and only then switch off strict freshness;
5. repeat provider adoption only in Game, Platform and Atlas repositories whose exact current-task mutation authorization is recorded, allowing independent provider work where paths and settings are disjoint; keep every other provider read-only and hand it off;
6. add an organization drift audit comparing expected policy with live repository settings/workflow capabilities;
7. remove/supersede stale local exact-head-only review language and close provider adoption Issues.

## Failure handling

- If `merge_group` CI fails because of an integration conflict/semantic regression, return to the candidate owner with the exact failure. A real risk-bearing repair changes fingerprint and triggers fresh review as required.
- If queue evidence is merely delayed, enter `WAITING_EXTERNAL`; do not commit to retrigger.
- If an unrelated base advance preserves the fingerprint, reuse review and let the queue rebuild the integration candidate.
- If a trusted-base change touches a reviewed risk-bearing path and changes fingerprint, require fresh review.
- If the canary, trusted bridge, API mapping or readback fails, remove/roll back the queue-required rule to its captured pre-cutover state while strict freshness is still active; verify that fallback state before further work. Never remove strict freshness as part of a failed canary cleanup.
- If Merge Queue, organization ruleset workflows or protected source-workflow access is unavailable for a repository/account capability reason, record the exact capability gap. Do not silently weaken integration safety; use the existing strict-up-to-date model only as an explicit temporary fallback until the capability exists.

## Current observed basis — locators only

At design time (2026-08-30), live inspection showed:

- META protected `main` already contains risk-based AI-review fingerprint/reuse semantics, including unrelated-base-advance reuse under strict conditions;
- META bounded-autonomous PR #71 was still open and Game adoption Issue #148 was still open;
- Game `main` ruleset required `game-gate`, used strict required-status freshness, squash-only integration and stale-review dismissal on push;
- Game `merge-gate.yml` was `pull_request`-specific; the provider therefore needs a protected-base test contract plus the trusted META ruleset bridge before Merge Queue can replace strict freshness. Merely adding a local `merge_group` trigger would not establish authority.

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
- a protected-source META ruleset workflow maps each single-PR group without ambiguity, verifies attested review/fingerprint/ancestry and publishes the required result on the exact integration SHA;
- required aggregate tests pass inside that trusted workflow on merge-group candidates;
- strict up-to-date-before-merge is no longer the normal author/agent integration mechanism;
- fingerprint reuse works across qualifying unrelated `main` advances;
- fingerprint changes still force fresh review;
- P0/P1 block and P2 follow-up behavior is deterministic;
- no-op/retrigger loops are deterministically prohibited;
- live configuration drift is detectable;
- canary PRs prove the end-to-end flow before old protections are removed.
- every provider branch/PR/settings mutation is preceded by recorded current-task owner authorization for that exact repository and scope; an unauthorized provider remains a read-only handoff and cannot be represented as rollout-complete.
