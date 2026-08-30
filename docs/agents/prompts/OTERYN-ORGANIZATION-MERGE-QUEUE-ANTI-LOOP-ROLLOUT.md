# OTERYN-ORGANIZATION-MERGE-QUEUE-ANTI-LOOP-ROLLOUT

PROMPT_ID: `OTERYN-ORGANIZATION-MERGE-QUEUE-ANTI-LOOP-ROLLOUT`
PROMPT_VERSION: `1.0`
STATUS: `READY`
ALIAS: `Oteryn: merge queue rollout`
STORAGE_REPOSITORY: `Oteryn/Oteryn`
TARGET_REPOSITORIES: `Oteryn/Oteryn`, `Oteryn/Oteryn-Game`, `Oteryn/Oteryn-Platform`, `Oteryn/Oteryn-Atlas`
GOVERNING_ISSUE: `Oteryn/Oteryn#102`
DESIGN: `docs/superpowers/specs/2026-08-30-organization-merge-queue-review-fingerprint-design.md`
PLAN: `docs/superpowers/plans/2026-08-30-organization-merge-queue-review-fingerprint-rollout.md`

## Mode

Autonomous supervising governance coordinator + implementation integrator + verification owner.

Use proportional agent planning under the current canonical META execution-routing policy. Parallelize only genuinely independent provider lanes; serialize shared META policy changes and each repository's protection/ruleset cutover.

Do not use Remote Desktop/Desktop Commander for ordinary repository, GitHub Actions, ruleset, review or merge work. Repository-native GitHub/GitHub Actions/admin APIs are the preferred control plane.

## Primary goal

Bring the Oteryn organization to one terminal integration model that prevents branch-freshness/review retry loops without weakening merge safety:

- PR candidate work is reviewed by canonical META risk fingerprint;
- GitHub Merge Queue owns latest-`main` integration;
- required deterministic CI qualifies the exact merge-group integration candidate;
- unrelated `main` movement does not by itself cause a fresh external review or task-branch mutation;
- risk-bearing fingerprint changes do require fresh review;
- P0/P1 block; P2 is follow-up unless correctly escalated to P1 because it proves a merge-blocking invariant violation;
- unchanged candidates never receive no-op/retrigger/checkpoint commits merely to wake CI/review;
- META owns semantics and Game/Platform/Atlas consume thin provider configuration.

Do not stop after writing policy or enabling one repository. Continue until the organization rollout is terminal or a precisely evidenced owner/admin capability blocker prevents further authorized work.

## Source of truth

GitHub live state is the sole lifecycle authority. Before every material phase and before every mutation:

1. refresh protected `main` in all four repositories;
2. refresh Issue `Oteryn/Oteryn#102`;
3. refresh META Issue #69 / PR #71 and any superseding bounded-autonomous work;
4. refresh Game Issue #148 and equivalent Platform/Atlas adoption work;
5. resolve open PRs touching root `AGENTS.md`, AI-review policy/actions, aggregate gates, rulesets/branch protection or merge settings;
6. read the current protected-main META AI-review policy, machine policy, execution-routing policy, bounded-autonomous policy if merged, and applicable provider root instructions;
7. inspect live required checks, branch protection/rulesets, merge methods, queue state and admin capability.

Any SHA, PR number or status written in this prompt/design/plan is a locator only. Do not trust cached checkouts, previous handoffs, old task prose or stale review summaries over live GitHub.

## Governing architecture

Resolve and follow:

- `docs/superpowers/specs/2026-08-30-organization-merge-queue-review-fingerprint-design.md`;
- `docs/superpowers/plans/2026-08-30-organization-merge-queue-review-fingerprint-rollout.md`;
- current protected-main `docs/governance/AI_REVIEW_POLICY.md`;
- current protected-main `ecosystem/ai-review-policy.json`;
- current canonical bounded-autonomous execution contract/policy after determining whether META #69/#71 is merged or superseded;
- each provider repository's current `AGENTS.md` and nearer instructions.

If the old design conflicts with newer merged META authority, update Issue #102 with the conflict and apply the newer canonical authority. Do not fork the policy locally.

## Non-negotiable model

### Candidate head vs integration head

Treat these as different objects:

- `candidate_head_sha`: exact PR head containing task changes;
- `reviewed_head_sha`: exact ancestor actually reviewed externally;
- `review_fingerprint`: canonical META risk-bearing identity;
- `integration_head_sha`: exact GitHub Merge Queue `merge_group` candidate representing latest trusted `main` + candidate.

External review is not valid merely because an old review exists, and it is not invalid merely because the final SHA differs. Run the canonical fingerprint/ancestry/review-neutral/trusted-base verifier.

### Exact-head rules that remain mandatory

Require exact current integration-head evidence for deterministic merge checks. The actual `merge_group` candidate that can enter `main` must pass the required repository aggregate gate.

Do not reuse old CI for a different integration SHA unless the repository's machine policy explicitly provides a deterministic equivalent proof.

### Review reuse

Do **not** request fresh external review solely because:

- protected `main` advanced on unrelated paths;
- a clean trusted-base integration merge changed SHA;
- Merge Queue rebuilt the synthetic integration candidate;
- review/check evidence arrived late for the unchanged candidate.

Reuse review only when the canonical META verifier proves the same tier/fingerprint plus all required ancestry/review-neutral/trusted-base/final-CI conditions.

If risk-bearing candidate content changes, or a trusted-base change changes the risk-bearing fingerprint, fresh review is required.

### Review findings

- P0: blocking.
- P1: blocking.
- P2: non-blocking follow-up by default.

If a P2 actually proves a merge-blocking security, authority, durability, protocol/contract or acceptance invariant violation, reclassify/escalate it to P1 with evidence. Do not create an infinite `P2 -> repair -> new review -> another P2` loop by treating every hypothetical hardening improvement as mandatory before merge.

For a legitimate deferred P2, create/link a durable follow-up Issue and resolve any required review thread with that explicit deferral evidence.

## Execution sequence

### Phase A — live-state matrix

Build one compact table for META/Game/Platform/Atlas containing:

- protected `main` SHA;
- required check names;
- aggregate gate workflow path;
- `pull_request` support;
- `merge_group` support;
- strict branch freshness state;
- Merge Queue state;
- allowed merge methods;
- external-review mechanism/policy version;
- anti-loop adoption state;
- overlapping PR/task owners;
- admin/ruleset write capability.

Do not mutate until this matrix is complete.

### Phase B — META canonical policy

If current merged META already provides all required candidate/integration/fingerprint/anti-loop semantics, reuse it and make only the missing delta. If open PR #71 or a successor owns the bounded-autonomous surfaces, do not create competing schema/policy work; reconcile through its live lifecycle.

Use strict TDD for new machine semantics. Add failing focused regressions before production validator/policy changes, then implement the smallest fail-closed repair and prove GREEN with existing governance suites.

### Phase C — `merge_group` gate capability

Before touching branch protection:

- make each required aggregate gate capable of running on `merge_group`;
- make event parsing valid for both PR and merge-group events;
- prove the exact integration SHA/base is validated;
- preserve trusted-base review-policy execution and candidate-code isolation;
- test event fixtures deterministically;
- prove a real canary produces the required status for a Merge Queue candidate.

A required workflow that only handles `pull_request` is a hard blocker to disabling strict freshness.

### Phase D — staged queue cutover

For META first, then a provider canary, then remaining providers:

1. merge and read back the `merge_group`-capable gate from protected `main`;
2. enable Merge Queue;
3. configure squash and one PR per merge group initially;
4. require the queue integration path and required aggregate gate;
5. execute one real canary queue merge;
6. read back protected `main`;
7. only then disable strict `Require branches to be up to date before merging`;
8. verify no ordinary direct merge path bypasses queue policy.

Never create a window where neither strict freshness nor proven queue integration protects `main`.

### Phase E — provider semantic cleanup

In Game/Platform/Atlas:

- remove/supersede local rules equivalent to `every material head change invalidates review` where they conflict with canonical fingerprint reuse;
- remove instructions to merge-up merely because `main` moved when queue integration can handle it;
- retain exact-head deterministic CI and merge-group qualification;
- retain reviewed-head identity as evidence for ancestry/fingerprint verification;
- preserve repository-specific extra risk paths/tests without copying META review semantics;
- add governance tests that reject reintroduction of loop-prone exact-SHA-only review invalidation.

### Phase F — drift protection

Implement a deterministic organization/provider drift audit that detects at minimum:

- queue disabled unexpectedly after adoption;
- strict freshness re-enabled outside an explicit fallback state;
- required aggregate gate lacking `merge_group` support;
- required check names drifting from provider config;
- exact-SHA-only external-review invalidation returning;
- no-op/retrigger behavior returning;
- P2 becoming automatically merge-blocking;
- merge paths that can enter `main` without tested integration candidates.

If GitHub admin APIs are inaccessible, report the live-setting portion as `UNKNOWN/UNVERIFIED` with the exact missing capability. Do not claim PASS from repository declarations alone.

## Required end-to-end scenarios

Before terminal closeout, prove all of these with durable GitHub evidence:

1. **Normal:** candidate -> CI -> review -> queue -> merge-group CI -> squash merge.
2. **Unrelated main advance:** reviewed candidate stays unchanged; fingerprint remains valid; no fresh external review; queue rebuilds latest-main integration candidate; merge-group CI passes; merge succeeds.
3. **Risk-bearing base advance:** fingerprint reuse fails; integration waits; fresh review occurs only after required reconciliation.
4. **P1 repair:** TDD repair changes fingerprint; fresh review required; queue integration succeeds after PASS.
5. **P2 follow-up:** non-blocking P2 is tracked/deferrable without review-repair loop.
6. **Late review evidence:** same unchanged candidate is re-evaluated without a no-op Git commit.
7. **Queue failure:** real integration failure returns to the owning candidate; no branch mutation is performed merely to retrigger unchanged external state.

## Safety and authority

Do not:

- weaken required checks, review gates, CODEOWNERS, branch protection or thread resolution merely to make queue adoption pass;
- use candidate-controlled workflows as trusted review-policy authority;
- directly modify product runtime, production, deployments, secrets or live data;
- force-push/rebase published task history merely because `main` advanced;
- use Remote Desktop as a routine fallback for GitHub/settings/review work;
- fabricate Merge Queue capability, ruleset state or review evidence;
- disable strict branch freshness before merge-group proof exists;
- create no-op/retrigger commits.

If a repository/account cannot use Merge Queue, keep or restore strict freshness as an explicitly recorded fallback and report the smallest missing capability. Do not call that fallback the target architecture.

## Completion gate

Do not claim `DONE` until live protected-main and settings readback proves for all required repositories:

- canonical META candidate/integration/review-fingerprint semantics are merged;
- bounded autonomous anti-loop semantics are canonical/provider-adopted;
- required aggregate gates support `merge_group`;
- Merge Queue is required where supported;
- squash integration is preserved;
- strict branch freshness is no longer the ordinary integration mechanism where queue is active;
- qualifying unrelated `main` advances reuse external review without mutating the task branch;
- risk-bearing fingerprint changes still require fresh review;
- P0/P1 blocking and P2 follow-up semantics are deterministic;
- drift detection exists and passes/accurately reports inaccessible settings;
- canary merge/readback evidence is durable.

Close Issue #102 only after terminal provider readback. Return exact final policy coordinates, provider PR/merge SHAs, required-check/queue settings and canary evidence.
