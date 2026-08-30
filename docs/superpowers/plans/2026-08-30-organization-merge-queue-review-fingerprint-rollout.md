# Organization Merge Queue + Review Fingerprint Rollout Plan

> **For the rollout agent:** execute this plan from live GitHub state. Issue/PR/SHA values mentioned here are locators only. Do not treat this document as lifecycle authority.

**Goal:** Replace loop-prone author-managed branch freshness and exact-SHA-only review invalidation with one organization-wide model: candidate-head review by risk fingerprint, Merge Queue integration, exact merge-group CI, and bounded anti-loop execution.

**Design:** `docs/superpowers/specs/2026-08-30-organization-merge-queue-review-fingerprint-design.md`

**Governing Issue:** `Oteryn/Oteryn#102`

**Repositories:**
- `Oteryn/Oteryn`
- `Oteryn/Oteryn-Game`
- `Oteryn/Oteryn-Platform`
- `Oteryn/Oteryn-Atlas`

## Global constraints

- GitHub live state is the source of truth.
- Do not disable an existing protection before its replacement is proven.
- Do not mutate product/runtime/deployment/secret/live-data surfaces.
- Do not use no-op/retrigger commits to obtain new CI/review evidence.
- Do not require fresh external review solely because a SHA changed; run the canonical fingerprint-reuse verifier first.
- Do require fresh external review after a risk-bearing fingerprint change.
- P0/P1 block. P2 is follow-up unless the finding is escalated to P1 because it proves a merge-blocking invariant violation.
- Provider repositories may be stricter on tests/risk classification but may not fork review-reuse or integration semantics.
- Prefer proportional parallelism: META policy work and each provider rollout may be separate lanes when their owned paths/settings are disjoint; ruleset cutovers for a repository are serialized with that repository's gate rollout.

---

## Phase 0 — Reconstruct live authority and overlap

- [ ] Refresh protected `main` in all four repositories.
- [ ] Refresh META Issue #69 / PR #71 and determine whether bounded autonomous execution is merged, still active, or superseded.
- [ ] Refresh Game Issue #148 and equivalent Platform/Atlas provider-adoption work.
- [ ] Resolve open PRs touching root `AGENTS.md`, AI-review policy/actions, aggregate gates, branch protection/rulesets or merge settings.
- [ ] Read current META `docs/governance/AI_REVIEW_POLICY.md`, `ecosystem/ai-review-policy.json`, bounded-autonomous policy (if canonical), root `AGENTS.md`, and provider root instructions.
- [ ] Snapshot live branch-protection/ruleset settings and required check names for all four repos.
- [ ] Record capability for GitHub Merge Queue and administrative ruleset updates; if unavailable, stop the settings cutover and report the exact capability gap rather than weakening safety.

**Exit:** one live-state matrix showing authoritative policy versions, current aggregate gates, strict-freshness state, queue state, review model and overlapping writers.

---

## Phase 1 — Canonicalize META integration semantics

Create/extend META machine and human governance so there is one authoritative contract for:

- `candidate_head_sha`;
- `reviewed_head_sha`;
- `review_fingerprint`;
- `integration_head_sha` / merge-group identity;
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
  - P2 not being an automatic merge blocker;
  - P1 remaining blocking;
  - provider config being unable to override META reuse semantics.
- [ ] Run the focused tests and prove RED for intended missing semantics.
- [ ] Implement the minimum canonical policy/validator changes.
- [ ] Prove GREEN plus existing META governance tests.

**Important:** if PR #71 already implements part of this contract, integrate/reuse it. Do not create a competing bounded-autonomous schema.

---

## Phase 2 — Make META required gates Merge Queue aware

- [ ] Inventory every required `main` check in META.
- [ ] Update required workflows so they support both `pull_request` and `merge_group`.
- [ ] Refactor event parsing so `merge_group` does not dereference `github.event.pull_request`.
- [ ] Validate the exact integration SHA/base identities fail-closed.
- [ ] Ensure candidate-controlled code cannot select trusted review policy/reviewer identity for a `pull_request_target` review gate.
- [ ] Add regression tests for PR and merge-group event fixtures.
- [ ] Prove existing PR flow remains green.
- [ ] Create a disposable/canary PR and verify the required aggregate gate is emitted for a merge-group candidate.

Do not change branch protection yet.

---

## Phase 3 — META queue cutover

Only after Phase 2 is proven:

- [ ] Enable Merge Queue on protected `main`.
- [ ] Configure squash integration and one PR per merge group initially.
- [ ] Require the merge-group aggregate gate.
- [ ] Verify an actual canary enters the queue, receives a synthetic integration SHA, passes required checks and merges safely.
- [ ] Verify protected-main readback.
- [ ] Disable strict `Require branches to be up to date before merging` only after queue enforcement is confirmed live.
- [ ] Verify agents can leave a reviewed candidate unchanged while unrelated `main` advances and still integrate through the queue when fingerprint reuse remains valid.

**Rollback:** if queue-required checks are not emitted or the repository cannot enqueue, restore/retain strict freshness. Never leave `main` without either queue integration proof or strict freshness.

---

## Phase 4 — Provider gate adoption

For each of Game, Platform and Atlas, create a separately owned provider branch/PR from current protected `main`.

### Required provider work

- [ ] Add/verify `merge_group` trigger on the aggregate required gate (`game-gate`, `platform-gate`, `atlas-gate`/`provenance-gate` as applicable).
- [ ] Make event parsing work for PR and merge group.
- [ ] Ensure integration candidate exact SHA is what required deterministic jobs actually test.
- [ ] Bind external review evidence to canonical META fingerprint semantics, not local `head_change_invalidates_prior_qualification` shortcuts.
- [ ] Remove/supersede reusable prompt/task wording that says every material SHA movement automatically requires new external review when canonical reuse conditions hold.
- [ ] Preserve repository-specific tests, CODEOWNERS, thread resolution and risk escalations.
- [ ] Add deterministic provider governance regressions that reject reintroduction of exact-SHA-only review invalidation.

Provider code/runtime is out of scope unless the existing aggregate workflow itself lives with tooling needed to run its tests.

### Rollout order

Use one provider as the first canary after META. Game is a strong candidate because its strict freshness/ruleset and pull-request-specific merge gate are known loop pressure points; refresh live state before selecting it.

After the first provider passes end-to-end, Platform and Atlas may proceed independently if their gate/settings owners do not overlap.

---

## Phase 5 — Provider queue cutover

For each provider, serialized per repository:

- [ ] Prove required aggregate gate on a `merge_group` canary.
- [ ] Enable Merge Queue.
- [ ] Configure squash and single-PR groups initially.
- [ ] Require queue integration for protected `main`.
- [ ] Execute one canary queue merge and protected-main readback.
- [ ] Disable strict up-to-date-before-merge only after the canary is terminally successful.
- [ ] Verify no direct merge path bypasses the queue except explicit documented emergency policy.

Do not perform all settings changes across all repositories simultaneously. One proven canary precedes broad rollout.

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
- aggregate required gate missing `merge_group` support;
- required check names diverging from provider config;
- local policy reintroducing exact-SHA-only external-review invalidation;
- no-op/retrigger allowance returning;
- P2 becoming an automatic blocking severity;
- queue configuration allowing an untested integration path.

The audit must distinguish observed GitHub settings from repository-declared expectations and must not fabricate success when admin APIs are inaccessible.

---

## Phase 8 — End-to-end qualification

For each repository prove these scenarios:

### Scenario A — unchanged main

Candidate CI -> required external review by fingerprint -> queue -> merge-group CI -> squash merge -> protected-main readback.

### Scenario B — unrelated main advance after review

Candidate reviewed -> unrelated `main` advance -> fingerprint remains reusable -> no new external review -> queue rebuilds integration candidate -> merge-group CI -> merge.

### Scenario C — risk-bearing main advance

Candidate reviewed -> base change touches reviewed risk-bearing path -> final fingerprint/reuse verification fails -> queue/qualification stops -> fresh review required after reconciliation.

### Scenario D — candidate repair after P1

P1 -> TDD repair -> fingerprint changes -> fresh review -> queue -> merge-group CI -> merge.

### Scenario E — P2 follow-up

P2 that does not violate a merge-blocking invariant -> durable follow-up Issue/explicit deferral -> required thread resolution -> no repair/re-review loop solely for P2.

### Scenario F — delayed review evidence

Stable unchanged candidate waits -> same-head re-evaluation/recheck -> no no-op commit -> qualification continues.

---

## Phase 9 — Closeout

- [ ] Read back protected `main` and live settings in all four repositories.
- [ ] Confirm aggregate gates support `merge_group` from protected main.
- [ ] Confirm queue is required and strict freshness is no longer the normal integration mechanism.
- [ ] Confirm canonical review fingerprint/reuse policy is the only authority for external-review invalidation.
- [ ] Confirm bounded-autonomous anti-loop policy is canonical and provider-adopted.
- [ ] Archive/close superseded provider tasks without rewriting historical evidence.
- [ ] Close Issue #102 only after all required provider adoption/readback is terminal.

## Definition of done

The rollout is terminal only when an agent can encounter an unrelated `main` advance after a valid review and correctly do **nothing to the PR branch**, reuse the external review through canonical fingerprint proof, allow Merge Queue to construct/test the latest-main integration candidate, and merge only after the exact merge-group checks pass.
