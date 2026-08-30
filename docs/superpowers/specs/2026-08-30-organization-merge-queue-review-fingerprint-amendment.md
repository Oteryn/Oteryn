# Organization Merge Queue + Review Fingerprint — Binding Safety Amendment

**Status:** binding amendment to the Issue #102 target architecture carried by PR #117. Where this file conflicts with the original design, rollout plan, or reusable rollout prompt in the same PR, this amendment wins. Implementation must fail closed until these amended invariants are satisfied by protected-main code and the applicable staged canary evidence.

## Why this amendment exists

Live review of the approved design against current GitHub Merge Queue and Actions behavior exposed several implementation-critical assumptions that are too weak or ambiguous for a security-sensitive rollout. This amendment narrows those assumptions without changing the programme goal: candidate qualification remains fingerprint-bound, GitHub Merge Queue remains the intended integration authority, and strict freshness is not removed until the replacement path is proven.

## 1. Queue topology is event/queue-state authority, not `maximumEntriesToMerge`

`maximumEntriesToMerge = 1` controls how many successful queue entries GitHub may merge to the base branch at once. It is **not** proof that a speculative `merge_group` build contains only one pull request.

GitHub may construct a later queue candidate from the selected base plus changes from entries ahead of it. Therefore:

- never infer `single PR in I` from `maximumEntriesToMerge` alone;
- bind `B` to the exact `merge_group.base_sha` from the event and independently verify that `B` is the actual parent/base used to construct `I`;
- bind the active queue entry/entries from server-side Merge Queue state, including PR object identity, `baseCommit`, `headCommit`, position/state, configured merge method, grouping strategy, build concurrency and merge limit;
- require the method-aware independently reproduced integration tree to equal `tree(I)` exactly;
- do not assume `B == protected main`; for a later queue entry, `B` may reflect a speculative predecessor that already represents entries ahead of it;
- if the implementation only supports a single-entry topology initially, reject any live event whose queue state contains an unmodelled predecessor/prefix. Do not silently treat unsupported multi-entry topology as equivalent.

Phase C must provide deterministic fixtures for the supported topology and fail-closed unsupported cases. The live topology proof belongs to the staged post-enablement canary described below, because no real `merge_group` event exists before Merge Queue is enabled.

## 2. Historical review evidence requires a successful issuer run, not only a valid signature

A GitHub artifact attestation can remain valid even if the workflow run that created it later fails. Therefore a cryptographically valid PR #111-format attestation is necessary but not sufficient for admission.

Every consumer of a historical review envelope must re-fetch and require all of the following for the exact recorded issuer coordinates:

- source workflow identity/path is the expected protected META workflow;
- exact source repository and protected source SHA/ref match the envelope policy;
- exact workflow `run_id` and `run_attempt` match the envelope;
- the source workflow run is terminal with `status == completed` and `conclusion == success`;
- the exact issuer job is terminal with `status == completed` and `conclusion == success`;
- the exact associated check run/check suite is terminal successful and bound to the recorded candidate head/repository coordinates;
- the artifact/attestation was produced by that exact successful run/attempt and is not from a failed, cancelled, timed-out, superseded or ambiguous generation.

An attestation produced before a later self-verification failure is **not admissible** review evidence. A failed issuer generation must be treated as failed even when its signed statement is otherwise cryptographically valid.

## 3. Durable envelope locator is mandatory and must be emitted only after self-verification

The canonical review envelope must be discoverable later without guessing its nondeterministic bytes or relying on an ephemeral runner filesystem.

The protected issuer must publish the verified envelope as a GitHub Actions artifact **after** its attestation and live-coordinate self-verification succeed. The durable locator contract is:

- exact source run ID and run attempt;
- deterministic artifact name scoped to PR, candidate head, run and attempt;
- GitHub artifact ID and server-reported artifact digest;
- canonical envelope SHA-256;
- artifact contents consisting of the exact canonical envelope bytes that were attested and self-verified.

The consumer must enumerate artifacts only from the exact successful issuer run/attempt, require exactly one matching non-expired artifact, verify the server artifact digest, verify the canonical envelope digest/JSON, and then verify the attestation against those exact bytes and signer coordinates.

Missing, expired, deleted, duplicate or ambiguous artifact evidence fails closed. Recovery is a same-head trusted re-evaluation/reissuance of evidence, never a no-op candidate commit.

## 4. Trusted bridge and provider-contract self-updates require versioned activation

A candidate must never become the next merge authority merely because it passed the old authority.

For the META ruleset workflow and provider aggregate test contracts:

1. keep the currently Active protected source version pinned as authority;
2. review/test a proposed new version as candidate code;
3. where supported, run the proposed version in Evaluate/shadow mode with no authority to merge;
4. merge it through the old authority;
5. read back the resulting protected source SHA/blob;
6. only then advance the active ruleset/contract pin to the new protected version and run an enforced canary;
7. retain the prior protected version as the rollback pin until the new version is proven.

A provider-contract change must not weaken required capabilities simply by being present in the candidate tree. The old protected contract qualifies the current merge; the new contract becomes authority only after explicit protected-version promotion/readback.

## 5. Protected-source helper resolution remains mandatory

A protected ruleset workflow is not sufficient if it executes local helpers resolved from the target/candidate workspace.

Trusted bridge actions/helpers must resolve from the exact protected META source SHA `T` — for example by `$/...` source-relative local-action resolution when applicable or an explicit credential-free checkout of exact `T`. Plain candidate/default-workspace `./...` helper resolution is forbidden for trusted mediator logic.

External actions must remain pinned by full commit SHA.

## 6. Required workflow event model

The organization ruleset workflow remains a **dual-event** authority:

- a `pull_request` admission leg that is sufficient for queue eligibility and proves candidate/review qualification without pretending to prove exact integration;
- a distinct `merge_group: checks_requested` leg that alone qualifies exact integration head `I`.

The two legs must be disjoint, fail closed, and unable to satisfy one another by check-name reuse. A merge-group-only required workflow is not an acceptable design because it can create an admission chicken-and-egg before a PR can enter the queue.

Do not use `cancel-in-progress` on the required ruleset workflow in a way that can cancel an otherwise required queue proof.

## 7. Provider adoption prerequisite

Issue #114 is a hard provider-adoption prerequisite for this rollout. Before Game, Platform or Atlas consumes the reusable META gate/action, the caller token permission contract must explicitly and testably require the exact minimum read permissions needed by the trusted consumer. Provider rollout must remain read-only until the existing explicit owner-authorization gate for that repository/scope is satisfied.

## 8. #120 / #111 reconciliation guard

PR #120 repairs canonical duplicate-clean-result normalization on protected META. PR #111 touches the same verifier surface with an older copied-flair approach. After #120 becomes protected-main authority, reconciliation of #111 must preserve the canonical #120 parser/deduplication semantics; the older #111 hunk must not overwrite or regress them.

Any reconciliation that changes risk-bearing verifier semantics requires fresh exact-head classification/review according to the canonical fingerprint policy. Do not treat a textual merge-up as automatically review-neutral.

## Amended Phase-C acceptance gate

Phase C is complete only when protected-main readback proves the **capability code** required for later cutover, without requiring a live queue event that cannot exist yet. Before any queue/ruleset enforcement mutation, require all of the following:

- the dual-event protected META workflow exists at an exact protected source SHA;
- historical PR #111-format evidence is discoverable through the durable artifact locator;
- the consumer deterministically rejects valid attestations from non-success issuer runs/jobs/checks;
- queue identity/topology parsing is bound to event + server-side queue state and is not inferred from `maximumEntriesToMerge`;
- deterministic fixtures cover the supported queue topology, unsupported predecessor/prefix cases, and exact method-aware integration-tree reproduction;
- trusted helpers execute only from exact protected META source;
- bridge/provider authority updates use versioned protected activation;
- #114 permission contract is complete before provider consumption;
- the exact files, workflow path, source SHA, expected ruleset selector and rollback baseline are read back from protected `main`.

**No live `merge_group` canary is required to exit Phase C.** Queue/ruleset enforcement and the first real synthetic integration candidate belong to the staged cutover phase below. Until that phase begins, keep existing strict freshness and existing required checks in force.

## Amended Phase-D / Phase-3 live canary gate

Only after the complete Phase-C capability is merged and read back from protected `main`:

1. capture and positively read back the current protection/ruleset baseline with strict freshness still active;
2. configure the protected-source required workflow in Evaluate/shadow mode where supported and verify source access;
3. enable/require Merge Queue and activate the protected-source required workflow while **strict freshness remains enabled**;
4. positively read back queue-required + bridge-required + strict-freshness-active state;
5. enqueue one fresh/reopened real canary and prove the PR-admission leg followed by a distinct `merge_group` run on exact `I`;
6. on that real event, prove event/server queue topology, exact `B/C/I` identities, the supported predecessor/prefix model, successful #111 issuer coordinates + durable envelope artifact, exact method-aware `tree(I)` reproduction, provider aggregate tests, and the required workflow result on `I`;
7. verify the canary merge and protected-main readback;
8. **only then** request strict-freshness disable and positively read back the complete final protected state.

If the supported topology cannot be proven by the live canary, fail closed, keep/re-enable strict freshness, and do not widen the implementation by assumption. A two-entry/predecessor canary may be added later to widen supported topology, but unsupported live queue shapes remain blocked until explicitly modelled and proven.

Do not weaken protection to make the bridge easier to deploy.
