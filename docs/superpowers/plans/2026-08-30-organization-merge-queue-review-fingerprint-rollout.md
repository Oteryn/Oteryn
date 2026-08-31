# Organization Merge Queue + Review Fingerprint Rollout Plan

> **For the rollout agent:** execute this plan from live GitHub state. Issue/PR/SHA values mentioned here are locators only. Do not treat this document as lifecycle authority.

**Goal:** Replace loop-prone author-managed branch freshness and exact-SHA-only review invalidation with one organization-wide model: candidate-head review by risk fingerprint, Merge Queue integration, exact merge-group CI, and bounded anti-loop execution.

**Design:** `docs/superpowers/specs/2026-08-30-organization-merge-queue-review-fingerprint-design.md`

**Binding amendment:** `docs/superpowers/specs/2026-08-30-organization-merge-queue-review-fingerprint-amendment.md` — part of this plan's governing architecture and higher precedence than conflicting clauses below.

**Governing Issue:** `Oteryn/Oteryn#102`

**Repositories:**
- `Oteryn/Oteryn`
- `Oteryn/Oteryn-Game`
- `Oteryn/Oteryn-Platform`
- `Oteryn/Oteryn-Atlas`

## Global constraints

- GitHub live state is the source of truth.
- Apply the binding amendment before executing this plan; if a clause below conflicts with it, the amendment wins.
- Do not disable an existing protection before its replacement is proven.
- Do not mutate product/runtime/deployment/secret/live-data surfaces.
- Do not use no-op/retrigger commits to obtain new CI/review evidence.
- Do not require fresh external review solely because a SHA changed; run the canonical fingerprint-reuse verifier first.
- Do require fresh external review after a risk-bearing fingerprint change.
- P0/P1 block. A P2 is non-blocking only after its exact current-generation trusted finding thread is resolved and contains exactly one unedited `OWNER`, `MEMBER` or `COLLABORATOR` disposition whose entire body is `Tracked in #<issue>.`, where that reference is an open Issue—not a pull request—in the same repository. Missing, duplicate, edited, stale, cross-repository or closed evidence fails closed; the executing agent cannot accept the deferral without that maintainer-owned disposition.
- Provider repositories may be stricter on tests/risk classification but may not fork review-reuse or integration semantics.
- The one protected META organization-ruleset workflow must support disjoint, fail-closed `pull_request` admission and `merge_group` integration jobs. A target-local `merge_group` workflow is candidate-controlled and cannot be required integration authority; require the protected META workflow by source repository/path, never a same-name status.
- The PR admission job binds the GitHub PR merge-ref/check-suite head `Hpr` to server-current candidate `C`, verifies the unique trusted PR #111 envelope (`Q`, `R`, exact tier/fingerprint and `R -> C`), and never receives secrets, OIDC, attestation writes or checks/status writes. Candidate contents are inert; candidate tests, if needed, are separate unprivileged jobs. A PR-stage result can never satisfy the distinct exact-`I` merge-group stage.
- Resolve trusted helpers/actions only from exact protected META `T` in a separate trusted path; never use `./...` from a candidate/default workspace, and pin every external action by full SHA. Do not rely on event filters, whole-workflow skips, `cancel-in-progress`, no-op commits or candidate-controlled helpers.
- Before any branch, PR or settings mutation in Game, Platform or Atlas, record explicit current-task owner authorization for the exact repository and mutation scope. Target-repository lists, META authority, Issues/PRs and tool/admin capability do not grant that authority.
- Prefer proportional parallelism: META policy work and each provider rollout may be separate lanes when their owned paths/settings are disjoint; ruleset cutovers for a repository are serialized with that repository's gate rollout.

---

## Phase 0 — Reconstruct live authority and overlap

- [ ] Refresh protected `main` in all four repositories.
- [ ] Refresh META Issue #69 / PR #71 and determine whether bounded autonomous execution is merged, still active, or superseded.
- [ ] Refresh Game Issue #148 and equivalent Platform/Atlas provider-adoption work.
- [ ] Resolve open PRs touching root `AGENTS.md`, AI-review policy/actions, aggregate gates, branch protection/rulesets or merge settings.
- [ ] Read current META `docs/governance/AI_REVIEW_POLICY.md`, `ecosystem/ai-review-policy.json`, bounded-autonomous policy (if canonical), root `AGENTS.md`, and provider root instructions.
- [ ] Snapshot live branch-protection/ruleset settings and required check names for all four repos.
- [ ] Record capability for GitHub Merge Queue, organization **Require workflows to pass before merging**, protected cross-repository source-workflow access and administrative ruleset updates; if any required capability is unavailable, stop the settings cutover and report the exact gap rather than weakening safety.
- [ ] For each of Game, Platform and Atlas, record the exact evidence of explicit owner authorization granted for this current task and its allowed branch/PR/settings mutation scope, or record `READ-ONLY — AUTHORIZATION MISSING`. An explicit current user instruction covering all four repositories may satisfy this gate within its stated scope; do not infer authorization from this reusable plan or any target list, META role, Issue/PR or tool access.

**Exit:** one live-state matrix showing authoritative policy versions, current aggregate gates, strict-freshness state, queue state, review model, overlapping writers and per-provider current-task mutation authorization plus scope. Until a provider row records that authorization, its lane is limited to read-only inventory and owner handoff.

---

## Phase 1 — Canonicalize META integration semantics

Create/extend META machine and human governance so there is one authoritative contract for:

- `candidate_head_sha`;
- `reviewed_head_sha`;
- `review_fingerprint`;
- `integration_head_sha` / merge-group identity;
- `Hpr`, the GitHub PR merge-ref/check-suite head used only for PR admission;
- protected source-workflow SHA and ruleset workflow identity;
- durable discovery and verification of the PR #111-format review envelope/attestation;
- fingerprint reuse/invalidation;
- blocking severities P0/P1;
- P2 follow-up/escalation rule;
- queue-required integration;
- same-head re-evaluation and no-op/retrigger prohibition.

### TDD

- [ ] Add failing deterministic tests first for:
  - unrelated trusted `main` advance preserving review qualification when fingerprint/reuse conditions hold;
  - risk-bearing base change invalidating fingerprint;
  - risk-bearing candidate change invalidating review;
  - clean trusted-base merge/merge-group reuse under allowed conditions;
  - no-op/retrigger commit rejection;
  - a P2 being non-blocking only with its exact resolved unedited finding thread, exactly one trusted maintainer `Tracked in #<issue>.` disposition, and an open same-repository Issue;
  - P1 remaining blocking;
  - provider config being unable to override META reuse semantics;
  - a missing/duplicate commit-to-PR mapping, queue entry or attestation artifact failing closed;
  - a candidate workflow attempting to reproduce the required result name remaining non-authoritative;
  - `Hpr -> C` admission rejecting a stale, mismatched or ambiguous PR/check-suite binding;
  - a PR-stage success being unable to satisfy an exact-`I` merge-group requirement;
  - a malicious local helper shadowing a trusted helper path failing closed;
  - every legacy required status context having an explicit protected replacement mapping before it may become non-required.
- [ ] Run the focused tests and prove RED for intended missing semantics.
- [ ] Implement the minimum canonical policy/validator changes.
- [ ] Prove GREEN plus existing META governance tests.

**Important:** if PR #71 already implements part of this contract, integrate/reuse it. Do not create a competing bounded-autonomous schema.

---

## Phase 2 — Publish the protected dual-event workflow

All Phase-2 implementation must satisfy the binding amendment. In particular, do not infer speculative group cardinality from `maximumEntriesToMerge`; historical review evidence must come from an exact terminal-success issuer generation; durable envelope artifacts are emitted only after issuer self-verification; trusted bridge/provider-contract changes use versioned protected activation; and #114 must be complete before provider consumption.

- [ ] Inventory every required `main` check and current workflow/ruleset authority in META; explicitly classify target-local `merge_group` workflows as non-authoritative and classify every required legacy context as `merge_group-capable` or `PR-only/incompatible`.
- [ ] Implement one META-owned organization-ruleset workflow, stored and protected on META `main`, with disjoint fail-closed `pull_request` and `merge_group: checks_requested` jobs; select it later by source repository/workflow path, not by result name.
- [ ] In the `pull_request` job, bind GitHub's PR merge-ref/check-suite head `Hpr` to server-current candidate `C`, require exactly one trusted PR #111 envelope, and verify `Q`, `R`, exact tier/fingerprint and canonical `R -> C` qualification. Use read-only permissions: no secrets, OIDC, attestation writes, checks/status writes or candidate execution. Run any candidate test only in a separate unprivileged job. Do not introduce `pull_request_target` as this admission leg.
- [ ] Resolve workflow helpers/actions in a separate trusted path from exact protected META `T`, never from candidate/default-workspace `./...`; pin every external action by full SHA and prove a malicious local-helper shadow cannot alter either event leg.
- [ ] Extend the PR #111 trusted review gate, if necessary, to upload the canonical envelope as an immutable artifact **after successful self-verification** and expose its server-verifiable successful run/attempt, artifact digest and envelope digest. Preserve the predicate, signer/source SHA, issuer and live-coordinate verification contract.
- [ ] In protected code define `T` (current bridge source), `Q` (protected source recorded by the candidate review envelope), `B` (merge-group event-selected base/parent), `I` (integration), the server-bound queue entry/entries and current candidate `C`, `R` (reviewed head) and `M` (live configured merge method, required here to equal `squash`).
- [ ] Implement fail-closed mapping from exact `merge_group` event + live server-side Merge Queue state. REST `commits/{I}/pulls` may be a canary-proven locator/cross-check but is not sole authority. Bind queue entry identity, `baseCommit`/`headCommit`, position/state, configured merge method, grouping strategy, build concurrency and merge limit. Never infer a single-PR synthetic build from `maximumEntriesToMerge == 1`.
- [ ] Fetch the exact inert Git objects required by the supported topology and require exact equality between `tree(I)` and the independently reproduced method-aware integration result. For required `M = squash`, do not require original `C` ancestry into `I`; reject unsupported predecessor/prefix topology rather than approximating it. Keep future merge/rebase or wider topology unsupported until versioned deterministic fixtures exist.
- [ ] Locate exactly one non-superseded trusted review-envelope artifact from the server-derived `pull_request_target` issuer generation; require the exact source run/attempt/job/check to be terminal `success`, then verify artifact/envelope digests, canonical JSON, repository/PR IDs, evidence source and GitHub attestation constrained to the PR #111 predicate plus signer/ref/digest `Q`. A valid signature from a failed issuer run is inadmissible.
- [ ] Run canonical reuse validation for `R -> C` plus the supported method-aware integration topology, trusted-base lineage and exact integration tier/fingerprint equality. Run provider aggregate tests against exact `I` in a separate credential-free, unprivileged job.
- [ ] In a fresh mediator job that never executes candidate code or consumes candidate artifacts/caches, re-fetch the test job/check conclusion and exact head from the Actions API; emit and immediately verify an integration envelope binding repository/PR/queue identities, `T/Q/M/B/C/R/I`, tier/fingerprint, evidence and run/job/check-suite identities. Assert the ruleset workflow's own check suite has `head_sha == I`; rely on that GitHub-published required workflow result, not a manually named candidate status.
- [ ] Give candidate workflows and the integration test job read-only/no-secret permissions and no `checks`, `statuses`, OIDC or attestation writes. Give only the isolated mediator job `actions/checks/contents/issues/pull-requests: read` plus `id-token`, `attestations` and `artifact-metadata: write` for its own envelope; no contents/checks/statuses write and no shared caches/artifacts from candidate execution. Do not use event filters, whole-workflow skips or `cancel-in-progress` to couple or suppress the two proof stages.
- [ ] Add deterministic fixtures for the supported squash topology plus zero/multiple/foreign/stale mappings; wrong base/head; unsupported predecessor/prefix/extra-member shapes; non-reproducible integration result; merge-method mismatch/ambiguity; stale/duplicate/missing artifact; invalid signer/source; valid attestation from a failed issuer generation; fingerprint drift; wrong check-suite head; stale/mismatched `Hpr -> C`; PR-stage/merge-group result confusion; malicious local-helper shadowing; and incomplete/ambiguous replacement coverage for legacy required contexts.
- [ ] Prove existing PR flow remains green, merge the complete bridge/capability code, then read the exact files and SHA back from protected `main`.

Do not change queue, ruleset enforcement or strict freshness in this phase. **No live `merge_group` canary is required to exit Phase 2.** A live canary belongs to Phase 3, after the capable code is already protected and while strict freshness remains active.

---

## Phase 3 — META queue cutover

Only after Phase 2 is proven:

- [ ] Re-read the dual-event workflow and verifier from protected `main`; record source workflow SHA/path, current ruleset JSON, exact legacy required-context set and `strict freshness = true` as the rollback baseline.
- [ ] In Evaluate mode, save and read back the protected-source required-workflow configuration and verify source-repository/path access. If Team cross-repository required-workflow semantics fail, record the exact capability fallback and retain strict freshness.
- [ ] Activate/require the protected dual-event workflow **while strict freshness and every existing legacy required context remain active**. Prove its `pull_request` admission leg succeeds and positively read back the combined protected state.
- [ ] For each legacy required context, prove its deterministic/security coverage is preserved by the protected dual-event workflow or protected META/provider aggregate contract. Any missing coverage blocks cutover.
- [ ] Make every legacy context that cannot succeed on `merge_group` non-required while the protected dual-event workflow remains required and strict freshness remains enabled. META examples include current `meta-gate` / `ai-review-gate`; provider examples include current `game-gate`, `platform-gate`, and `atlas-gate` / `provenance-gate` unless a refreshed live implementation proves that exact context is deliberately `merge_group`-capable and remains part of the supported integration contract.
- [ ] Positively read back the exact **pre-canary** protection state: protected dual-event workflow required, strict freshness `true`, no incompatible PR-only legacy context still required, and merge method/thread/CODEOWNERS/force-push/deletion protections unchanged.
- [ ] Configure squash and the intended initial queue limits/topology, enable/require Merge Queue while strict freshness remains enabled, and positively read back queue-required + bridge-required + strict-freshness-active state before enqueue.
- [ ] Enqueue one fresh or reopened actual canary; prove PR-stage ineligible-before/eligible-after admission and a same-head late-review rerun without a commit, then prove the actual event/server queue topology, exact successful historical issuer/artifact evidence, supported method-aware integration-tree reproduction, aggregate tests and the distinct required workflow result on exact synthetic `I`.
- [ ] Verify the canary merge and protected-main SHA/readback.
- [ ] Disable strict `Require branches to be up to date before merging` only after that terminal success, then read back queue-required, bridge-required, incompatible-legacy-contexts-nonrequired and strict-freshness-disabled state together.
- [ ] Verify agents can leave a reviewed candidate unchanged while unrelated `main` advances and still integrate through the queue when fingerprint reuse remains valid.

**Rollback before strict-disable:** if required-context replacement, enqueue, queue topology/API mapping, issuer/artifact validation, required exact-`I` result, canary merge or pre-disable readback fails, retain/restore the captured legacy required-context set while strict freshness remains positively `true`, and positively read back that fallback before further mutation. Never remove the protected dual-event workflow first if doing so would create a protection gap.

**Recovery after strict-disable request:** once any request to disable strict freshness has been sent, or when the final combined readback is failed, missing or ambiguous, do not assume strict remains enabled. First explicitly re-enable strict freshness and require a positive `strict freshness = true` readback. Only after that proof may the queue/required-workflow/legacy-context configuration be restored to the captured safe baseline. If strict cannot be positively confirmed, stop in emergency `BLOCKED`, preserve the strongest remaining queue/workflow protection, and escalate; never leave an unprotected gap.

---

## Phase 4 — Provider gate adoption

**Hard authorization gate:** enter Phase 4 for a provider only when its Phase 0 matrix row records explicit current-task owner authorization for that exact repository and branch/PR mutation scope. Otherwise perform no provider mutation: retain read-only inventory, record the blocker and hand off to the owner.

For each authorized provider among Game, Platform and Atlas, create a separately owned provider branch/PR from current protected `main`.

### Required provider work

- [ ] Complete Issue #114's reusable caller-token permission contract and executed regression before any provider consumes the META gate/action.
- [ ] Add the provider's protected-base test contract/configuration consumed by the META ruleset workflow; target-local `game-gate`, `platform-gate` or `atlas-gate`/`provenance-gate` may continue for diagnostics but is not the required integration authority unless refreshed protected code proves that exact context intentionally supports `merge_group` and is part of the supported final requirement set.
- [ ] Make trusted bridge event parsing and provider selection work for the repository without reading authority from `I`.
- [ ] Ensure integration candidate exact SHA is what required deterministic jobs actually test.
- [ ] Bind external review evidence to canonical META fingerprint semantics, not local `head_change_invalidates_prior_qualification` shortcuts.
- [ ] Remove/supersede reusable prompt/task wording that says every material SHA movement automatically requires new external review when canonical reuse conditions hold.
- [ ] Preserve repository-specific tests, CODEOWNERS, thread resolution and risk escalations.
- [ ] Add deterministic provider governance regressions that reject reintroduction of exact-SHA-only review invalidation.
- [ ] Produce an explicit coverage map from each provider's current required aggregate/status contexts to the new protected provider aggregate contract before Phase 5 may make a legacy context non-required.

Provider code/runtime is out of scope unless the existing aggregate workflow itself lives with tooling needed to run its tests.

### Rollout order

Use one provider as the first canary after META. Game is a strong candidate because its strict freshness/ruleset and pull-request-specific merge gate are known loop pressure points; refresh live state before selecting it.

After the first provider passes end-to-end, Platform and Atlas may proceed independently if their gate/settings owners do not overlap.

---

## Phase 5 — Provider queue cutover

**Hard authorization gate:** enter Phase 5 for a provider only when its recorded current-task owner authorization explicitly includes the intended settings/queue cutover. Branch/PR authority alone is insufficient.

For each authorized provider, serialized per repository:

- [ ] Merge and read back the provider bridge contract/configuration from protected `main`; capture ruleset JSON, exact legacy required-context set and active strict freshness.
- [ ] Activate/require the protected META dual-event workflow while strict freshness and existing provider legacy required contexts remain active; prove/read back its provider PR-admission result.
- [ ] Verify the explicit coverage map, then make every provider legacy required context that cannot succeed on `merge_group` non-required while the protected META workflow remains required and strict freshness remains `true`.
- [ ] Positively read back the pre-canary state: protected META workflow required, strict freshness `true`, no incompatible provider legacy required context remains, and all other protections unchanged.
- [ ] Configure squash/intended queue topology and enable/require Merge Queue while strict freshness stays active; positively read back queue + protected workflow + strict freshness before enqueue.
- [ ] Enqueue one canary and prove actual live queue topology, exact successful historical issuer/artifact evidence, provider aggregate coverage and exact-`I` trusted bridge success; then verify merge and protected-main readback.
- [ ] Disable strict up-to-date-before-merge only after the canary is terminally successful, then read back queue-required, bridge-required, incompatible-legacy-contexts-nonrequired and strict-freshness-disabled state.
- [ ] Verify no direct merge path bypasses the queue except explicit documented emergency policy.

If provider required-context replacement or canary fails before any strict-disable request, restore/retain the captured legacy required-context set while the latest positive readback proves `strict freshness = true`, then positively verify the safe fallback. After any strict-disable request, or on a failed, missing or ambiguous final readback, first explicitly re-enable strict and obtain positive `strict freshness = true`; only then restore/remove queue or required-workflow rules or restore legacy context requirements. If that proof cannot be obtained, stop in emergency `BLOCKED` and preserve the strongest remaining queue/workflow protection. Do not perform all settings changes across all repositories simultaneously. One proven canary precedes broad rollout.

---

## Phase 6 — Review semantics cleanup

- [ ] Search META/Game/Platform/Atlas governance, reusable prompts and active-task templates for phrases equivalent to:
  - every head change invalidates review;
  - fresh exact-head review after unrelated base movement;
  - merge-up whenever `main` advances;
  - retrigger/checkpoint commits for unchanged evidence.
- [ ] Replace them with canonical fingerprint/queue semantics.
- [ ] Keep exact-head requirements where they are correct: deterministic CI and exact merge-group integration qualification.
- [ ] Keep reviewed-head identity in evidence; it is required for ancestry/fingerprint verification even though equality with final SHA is not always required.
- [ ] Ensure P2 handling cannot reintroduce an infinite review-repair loop.

---

## Phase 7 — Organization drift audit

Create a deterministic audit that compares expected repository policy with live GitHub state and/or machine-readable snapshots.

It should fail/report on at least:

- Merge Queue unexpectedly disabled after adoption;
- strict branch freshness re-enabled without a declared fallback state;
- trusted ruleset workflow or protected-base provider contract missing `merge_group` support;
- required check names diverging from provider config;
- a PR-only/non-`merge_group`-capable legacy context remaining required after queue cutover;
- local policy reintroducing exact-SHA-only external-review invalidation;
- no-op/retrigger allowance returning;
- P2 becoming an automatic blocking severity;
- queue configuration allowing an untested integration path;
- required authority reduced to a status name or a target-local candidate workflow instead of the configured protected source workflow;
- bridge permissions exceeding the read-only-plus-attestation set or a bridge check suite not bound to exact `I`;
- queue active without durable PR #111 artifact discovery, successful issuer verification and server-bound supported queue topology.

The audit must distinguish observed GitHub settings from repository-declared expectations and must not fabricate success when admin APIs are inaccessible.

---

## Phase 8 — End-to-end qualification

For each repository prove these scenarios:

### Scenario A — unchanged main

Candidate CI -> required external review and successful PR #111 issuer/artifact -> protected PR-admission -> legacy-required-context replacement readback -> queue -> trusted server-bound queue topology -> exact-`I` aggregate CI/fingerprint qualification -> squash merge -> protected-main readback.

### Scenario B — unrelated main advance after review

Candidate reviewed -> unrelated `main` advance -> fingerprint remains reusable -> no new external review -> queue rebuilds integration candidate -> merge-group CI -> merge.

### Scenario C — risk-bearing main advance

Candidate reviewed -> base change touches reviewed risk-bearing path -> final fingerprint/reuse verification fails -> queue/qualification stops -> fresh review required after reconciliation.

### Scenario D — candidate repair after P1

P1 -> TDD repair -> fingerprint changes -> fresh review -> queue -> merge-group CI -> merge.

### Scenario E — P2 follow-up

P2 that does not violate a merge-blocking invariant -> exact current-generation trusted finding thread resolved -> exactly one unedited `OWNER`/`MEMBER`/`COLLABORATOR` `Tracked in #<issue>.` disposition for an open same-repository Issue -> no repair/re-review loop solely for P2. The executing agent cannot self-accept or self-resolve the deferral.

### Scenario F — delayed review evidence

Stable unchanged candidate waits -> same-head re-evaluation/recheck -> no no-op commit -> qualification continues.

### Scenario G — dual-event separation

Fresh or reopened canary is PR-stage ineligible before trusted review and eligible after it; the same head reruns admission without a commit. Before enqueue, incompatible legacy required contexts are replaced and the pre-canary readback proves protected workflow required + strict freshness active. Its later `merge_group` run uses a distinct exact `I`, and neither stage can satisfy the other. Evaluate-mode configuration save/readback/source access succeeds, strict freshness remains active through the canary, and a malicious candidate local-helper shadow fixture fails closed. If Team cross-repository required-workflow semantics are unavailable, record the capability fallback and retain strict freshness.

### Scenario H — queue topology and issuer failure

The live canary proves exactly the queue topology supported by protected code from event + server queue state. An unsupported predecessor/prefix shape fails closed. Separately, a validly signed review attestation from a failed/cancelled/timed-out issuer run is rejected, while the unique artifact from the exact successful issuer generation is accepted only after artifact/envelope digest and canonical-byte verification.

---

## Phase 9 — Closeout

- [ ] Read back protected `main` and live settings in all four repositories.
- [ ] Confirm the trusted ruleset workflow and protected-base provider contracts support `merge_group` from protected `main`.
- [ ] Confirm the same protected workflow file supplies both disjoint event jobs: `pull_request` binds `Hpr -> C` and verifies `Q`/`R`/tier/fingerprint/`R -> C`, while `merge_group` alone emits the exact-`I` integration qualification.
- [ ] Confirm the organization ruleset requires the protected META source workflow, its check suite targets exact `I`, and candidate-local same-name checks are non-authoritative.
- [ ] Confirm no incompatible PR-only legacy context remains required on a queue-enabled protected branch; any retained legacy workflow is diagnostic or deliberately proven `merge_group`-capable.
- [ ] Confirm queue is required and strict freshness is no longer the normal integration mechanism.
- [ ] Confirm canonical review fingerprint/reuse policy is the only authority for external-review invalidation.
- [ ] Confirm bounded-autonomous anti-loop policy is canonical and provider-adopted.
- [ ] Confirm every Game/Platform/Atlas branch, PR or settings mutation was preceded by recorded current-task owner authorization for that exact repository and scope; treat every unauthorized repository as read-only handoff/blocker, never as completed rollout.
- [ ] Archive/close superseded provider tasks without rewriting historical evidence.
- [ ] Close Issue #102 only after all required provider adoption/readback is terminal.

## Definition of done

The rollout is terminal only when an agent can encounter an unrelated `main` advance after a valid review and correctly do **nothing to the PR branch**, reuse the external review through canonical fingerprint proof, allow Merge Queue to construct/test the latest-main integration candidate, and merge only after the exact merge-group checks pass without any incompatible PR-only legacy requirement blocking the synthetic head.