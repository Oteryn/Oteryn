# OTERYN-SOLO-MAINTAINER-GOVERNANCE-V2-ROLLOUT

## Execution profile

- Product surface: **ChatGPT Work**
- Primary agent: **Terra**
- Reasoning / effort: **EXTRA HIGH**
- Role: **Supervising Execution Coordinator**
- Mutation topology: **one settings writer at a time**
- Repository rollout order: **META -> Game -> Platform -> Atlas**
- Parallelism: read-only analysis, tests and independent review may run in parallel; live GitHub settings mutations must remain serial

## Mission

Implement and terminally verify `Solo-Maintainer Governance V2` for the four permanent Oteryn repositories without reintroducing the moving-head, review-envelope, second-human or governance-self-deadlock failure modes that the redesign exists to remove.

Repositories:

- `Oteryn/Oteryn` — META
- `Oteryn/Oteryn-Game` — Game
- `Oteryn/Oteryn-Platform` — Platform
- `Oteryn/Oteryn-Atlas` — Atlas

## Absolute source-of-truth rule

**GitHub live state is the only source of truth for current repository settings, branch protection, rulesets, Merge Queue state, PR/head/base coordinates, required contexts, workflow runs and merge results.**

Historical SHA values, issue comments, chat summaries and this prompt are locators only unless re-read from live GitHub state.

Do not claim a blocker, successful mutation, successful rollback, canary success or terminal closeout without current direct evidence.

## Binding authority

Before implementation, read the following from protected `main` after PR #123 is merged:

1. `docs/superpowers/specs/2026-08-31-solo-maintainer-governance-v2-design.md`
2. `docs/superpowers/specs/2026-08-31-solo-maintainer-governance-v2-safety-amendment.md`
3. `docs/superpowers/plans/2026-08-31-solo-maintainer-governance-v2.md`
4. `docs/superpowers/plans/2026-08-31-solo-maintainer-governance-v2-safety-addendum.md`
5. `docs/architecture/adr/0002-organization-governance-operating-model.md`
6. `ecosystem/governance-desired-state.json`

The safety amendment is normative over conflicting or weaker clauses in the base design/plan.

If PR #123 is not yet merged, first refresh its live state. Do not bypass current required checks to merge it. The implementation phase begins only after the authority packet is canonical on protected `main`.

## Global Safety Contract

Every implementation step must satisfy all of the following:

- **GS-1** No moving-head governance dependency.
- **GS-2** No mandatory second-human dependency in solo-maintainer mode.
- **GS-3** Required aggregate gate cannot pass via `skipped` or `neutral`.
- **GS-4** No governance retrigger/no-op/checkpoint commits.
- **GS-5** Control-plane changes cannot autonomously self-authorize.
- **GS-6** Every `TRANSITION` is bounded and expiring.
- **GS-7** Merge Queue canary must include a moving-base scenario.
- **GS-8** Break-glass restoration must be independently verifiable.
- **GS-9** Exactly one externally required aggregate gate per permanent repository.
- **GS-10** Any new governance mechanism requires explicit threat justification.

A local test suite being green does not make a task complete if any GS invariant is violated.

## Target external merge contract

The terminal required-status map is exactly:

```text
Oteryn/Oteryn          -> meta-gate
Oteryn/Oteryn-Game     -> game-gate
Oteryn/Oteryn-Platform -> platform-gate
Oteryn/Oteryn-Atlas    -> atlas-gate
```

No second external required status may be added merely because an internal validation is important. Important validations must feed the repository aggregate gate unless an independently documented threat proves that a separate external authority is necessary.

Normal protected integration target:

```text
feature branch
  -> PR
  -> repository deterministic validation
  -> one aggregate gate
  -> GitHub Merge Queue
  -> same aggregate gate on exact synthetic merge-group candidate
  -> squash into protected main
```

## Aggregate-gate invariant

For every permanent repository, the required aggregate gate must:

- always be created on supported protected PR and `merge_group` flows;
- always execute;
- terminate explicitly as success or failure;
- never satisfy protection because the aggregate job itself was `skipped` or `neutral`;
- run final fan-in using an unconditional terminal evaluator such as `if: always()` where appropriate;
- explicitly inspect every required internal job result;
- allow an internal `skipped` result only where a deterministic applicability contract says that job is `NOT_APPLICABLE` for the exact candidate;
- fail closed on missing, unknown, unexpected or ambiguous internal state.

## Control-plane self-modification rule

The following are `CONTROL_PLANE_R2` surfaces at minimum:

- `.github/workflows/**`;
- aggregate-gate implementation or gate fan-in logic;
- branch protection, repository rulesets and Merge Queue configuration;
- `ecosystem/governance-desired-state.json`;
- Actions permissions or privileged workflow boundaries;
- break-glass machinery;
- auth/security/credential/deployment control-plane changes where the provider threat model classifies them as equivalent risk.

A candidate-controlled version of a governance mechanism must not be the sole authority that approves its own change.

Before any terminal integration of a `CONTROL_PLANE_R2` change require:

1. deterministic candidate validation;
2. independent deep review of the material change;
3. **explicit owner authorization bound to the current material head / live PR state**;
4. protected Merge Queue integration when available;
5. post-integration live readback.

Do not recreate the retired `ai-review-gate`, reaction parser, review-envelope or attestation bridge merely to satisfy this rule.

The authorization is valid only when it is a new, unedited top-level comment on the canonical current PR/Issue by a human whose present repository-owner authority is verified by direct GitHub readback. Record and verify the immutable comment ID, author login and actor type, the independently read owner role, `created_at == updated_at`, repository, PR, exact material head, control-plane scope, and positive integration authorization. A bot, coordinator, ordinary contributor, stale/head-mismatched, edited, or unverifiable actor is `UNKNOWN`, not owner authorization; a comment's text or `author_association` alone is insufficient.

This prompt itself does **not** constitute blanket owner authorization for future live `CONTROL_PLANE_R2` mutations. Pause only when explicit owner authorization is actually required by GS-5 or when a genuine safety/policy blocker exists.

## Writer and parallelism rules

Use one supervising coordinator for the full rollout.

Allowed parallel work:

- read-only repository inspection;
- test analysis;
- independent code/security review;
- documentation cross-checks;
- non-mutating GitHub state refreshes.

Forbidden parallel work:

- two agents changing the same repository settings;
- parallel branch-protection/ruleset/Merge Queue mutations;
- independent workers each interpreting and altering the global desired state;
- concurrent break-glass or rollback transactions.

For GitHub settings, there is exactly **one writer lane** at a time.

## Rollout sequence

### Phase 0 — Canonical authority and preflight

1. Refresh PR #123 and protected META `main`.
2. Confirm the V2 design, safety amendment, base plan, safety addendum and this prompt are canonical on protected `main` before implementation.
3. For each repository, record the current task's explicit authorization and its exact permitted scope before any repository-content, workflow, branch, PR, live-settings, or break-glass mutation. Repository visibility, organization membership, or authorization for META does not imply authorization for Game, Platform, or Atlas. If the current task does not explicitly cover a repository/scope, keep that repository read-only. This scope record does not replace the distinct current-material-head owner authorization required for `CONTROL_PLANE_R2` integration.
4. Refresh current `main` SHA and live protection/settings for all four repositories.
5. Use a separate execution-routing packet and fresh GitHub-state snapshot for each repository. Immediately before META implementation, and again immediately before the Game, Platform, and Atlas implementation/settings phases, validate that repository's packet with `python3 tools/governance/agent_execution_routing.py --policy ecosystem/agent-execution-routing-policy.json --packet <packet.json> --live-state <fresh-github-state.json>`. The validator and policy are canonical META authority: run that command only from an `Oteryn/Oteryn` checkout or trusted workflow verified at protected `main`. For Game, Platform, and Atlas, `<packet.json>` and `<fresh-github-state.json>` are provider-specific inputs passed to META's validator, not files assumed to exist in the provider checkout. Do not copy, replace, or rely on a provider or candidate-controlled validator/policy. `execution_routing.github_preflight` must contain only `verified_at`, `repository`, `default_branch_sha`, `governing_issue`, `pull_request`, and `task_head_sha`; place execution target/runner, equivalent-CI availability, and Remote Desktop/host restrictions in `execution_routing`, then place high-effort decision basis, lane strategy, and the one settings-writer lane in `parallel_execution`. A passing packet for an earlier repository cannot authorize or validate a later repository; refresh and revalidate after resumption or a material head/state change.
6. Classify every unreadable field as `UNKNOWN`; do not guess.
7. Classify each repository whose own serial cutover has not begun as `PENDING` only after recording in the canonical rollout Issue/PR a direct-readback pending baseline with `repository`, `captured_at`, `pre_state_fingerprint`, and `pre_state_readback`. Recompute the fingerprint and compare current live state to that baseline whenever accepting `PENDING`; missing, malformed, or mismatching evidence is `DRIFT`. The baseline is not a `TRANSITION` receipt, needs no expiry, carries no V2 settings deviation, and cannot count toward terminal closeout.
8. Record rollback snapshots before the first mutation in each repository.

### Phase 1 — META

1. Immediately before the first META implementation or settings mutation, refresh META live state and validate the META-specific routing packet required in Phase 0.
2. Make V2 the canonical desired-state contract and update deterministic validators/tests using RED -> GREEN TDD.
3. Make `meta-gate` the complete PR and merge-group aggregate authority.
4. Preserve existing protection while replacement behavior is being proven.
5. Retire `ai-review-gate` as an external required context only after the replacement path is proven.
6. Preserve the canonical R1/R2 review invocation and useful R0/R1/R2 risk classification as review evidence/decision support, without a separate required reaction/comment grammar.
7. Run the real moving-base canary.
8. Only after canary success, remove strict freshness for META.
9. Read back all changed settings.

### Phase 2 — Game

1. Immediately before Game implementation or settings mutation, refresh Game live state and validate a new Game-specific routing packet; do not reuse META's validation.
2. Refresh and save the complete `Protect main` ruleset snapshot.
3. Refactor `game-gate` so PR and merge-group identity/range resolution are safe and explicit.
4. Preserve real dependency, CodeQL, Rust/Linux/Windows and product validation.
5. Make PR title/body formatting advisory unless an independent product/release invariant proves otherwise.
6. Set the solo-maintainer target to zero required approvals and no required CODEOWNER approval.
7. Run the real moving-base canary.
8. Only after canary success, remove strict freshness.
9. Read back the final ruleset and required-status map.

### Phase 3 — Platform

1. Immediately before Platform implementation or settings mutation, refresh Platform live state and validate a new Platform-specific routing packet; do not reuse an earlier provider's validation.
2. Prefer the existing `platform-gate` design; do not redesign a healthy provider without evidence.
3. Verify broad/fail-closed merge-group validation rather than adding a complex optimizer merely to save CI minutes.
4. Run the real moving-base canary.
5. Only after canary success, remove strict freshness.
6. Read back the final settings.

### Phase 4 — Atlas

1. Immediately before Atlas implementation or settings mutation, refresh Atlas live state and validate a new Atlas-specific routing packet; do not reuse an earlier provider's validation.
2. Preserve extraction provenance while it remains a real source-integrity invariant.
3. Internalize provenance into `atlas-gate` rather than exposing `provenance-gate` as a second required context.
4. Make PR-only change classification/E2E applicability safe for merge-group candidates without weakening coverage.
5. Before canary admission, prove `provenance-gate` is produced on the exact merge-group candidate. If it is not, only after the replacement path is proven and explicit `CONTROL_PLANE_R2` owner authorization is recorded for the current material head/live PR, use one bounded transition to remove that legacy context, record the allowed deviation and readback, and restore it immediately if the canary fails.
6. Run the real moving-base canary.
7. Only after canary success, remove strict freshness and complete the desired-state removal of the obsolete second external provenance context.
8. Read back final settings.

### Phase 5 — Break-glass proof

1. Discover the exact recovery capability available on the current GitHub plan; do not assume an API or bypass mode.
2. Keep the break-glass rule recovery-only: it may repair a broken protection/gate control plane but may never bypass a legitimate failing product/security/dependency/provenance/integration test.
3. Perform a non-destructive readback/dry-run.
4. Perform exactly one real **isolated** exercise on a safe canary surface, not production `main` protection.
5. Prove minimal relaxation, one bounded repair, immediate restoration and positive readback.
6. Record a durable receipt.

### Phase 6 — Cleanup

Only after all four repositories are stable:

- retire obsolete moving-head merge-up review machinery;
- retire required reaction/flair/comment grammar;
- retire bridge-only review envelopes/attestations/fingerprint code;
- retire `merge-group-ai-review-adapter.yml` once there is no required consumer;
- mark superseded historical design material as `SUPERSEDED`, preserving rationale and provenance;
- retain any mechanism that still protects an independently documented privilege, deployment, credential, supply-chain or migration invariant.

## Moving-base canary — mandatory exact failure-mode proof

A normal queue canary is insufficient for terminal V2 acceptance.

For each repository prove this scenario using safe, materially mergeable canary changes:

```text
A: PR candidate becomes green at unchanged head X
B: another approved change advances protected main
A: head remains X — do NOT merge/rebase main into A
A: enters Merge Queue after main advanced
GitHub creates the synthetic candidate from the new integration base + A
aggregate gate executes on that synthetic merge-group SHA
aggregate gate = SUCCESS
A integrates through the queue without mutating head X merely for freshness
```

Until the bounded canary either succeeds or restores, strict freshness stays enabled and the repository remains `TRANSITION`, not `TARGET`. If the canary fails and timely (`closed_at <= expires_at`) restoration readback matches the captured pre-state, close the receipt as `ROLLED_BACK`; it remains non-target and any retry requires a new bounded receipt. A late closure is `DRIFT` even if settings were ultimately restored.

## Transition contract

Do not build a permanent transition database.

Use the canonical rollout Issue/PR as the durable transition receipt, using distinct, unedited top-level comments rather than editing a record in place. The auditor derives canonical `started_at` solely from the pre-transition comment's GitHub server `created_at`; never put `started_at` in the comment body. The pre-transition comment, created before the first mutation, must record at least:

```text
transition_id
repository
issue_or_pr
expires_at
pre_state_fingerprint
allowed_deviations
success_condition
rollback_condition
```

At terminal success or rollback, create a separate terminal comment that references the exact `transition_id` and GitHub `pre_transition_comment_id`. The auditor derives canonical `closed_at` solely from that terminal comment's GitHub server `created_at`; never put `closed_at` in the comment body. The terminal comment then records:

```text
transition_id
pre_transition_comment_id
terminal_status  # SUCCESS or ROLLED_BACK
post_state_fingerprint
post_state_readback
```

The read-only auditor must directly read both GitHub comments and accept them only when their IDs are present and unique, they are top-level records, `created_at == updated_at`, and the pre-transition `created_at` and terminal `created_at` are the canonical `started_at` and `closed_at` respectively. The comments must not supply either timestamp field. A missing, deleted, edited, duplicated, mis-linked, or unreadable record is `DRIFT`; the same unedited-ID/timestamp proof is required for a `PENDING` baseline. This constrains the existing lifecycle record and read-only auditor; it is not a new status, writer, database, or merge authority.

If `now > expires_at` before the transition reaches its success condition or is explicitly rolled back/closed with valid, timely (`closed_at <= expires_at`) terminal evidence, the state is `DRIFT`, not an indefinitely valid transition. A receipt is terminal `ROLLED_BACK` only when its unedited terminal comment references the exact pre-transition record, has `terminal_status = ROLLED_BACK`, timely `closed_at <= expires_at`, `post_state_fingerprint` matches `pre_state_fingerprint`, and positive `post_state_readback` proves restoration; otherwise it is `DRIFT`. A terminal `SUCCESS` also requires the same record linkage and timely `closed_at <= expires_at`, a recomputed `post_state_fingerprint`, a `post_state_readback` that passes the repository desired-target validator, and `success_condition` proof from the complete moving-base canary receipt: unchanged candidate head, intervening protected-main advance, exact synthetic merge-group SHA, successful repository aggregate-gate run, and resulting protected-main integration. A self-declared success, normal PR green status, or free-form note is not enough. A successfully closed or validly rolled-back receipt with these machine-readable fields remains terminal and does not become `DRIFT` solely because its historical expiry passes.

`ecosystem/governance-desired-state.json` should contain stable target state, not transient PR heads, review generations or temporary exception history.

## Rollback rules

Before each settings mutation, capture the exact pre-state needed for restoration.

On canary failure:

1. stop further rollout in that repository;
2. restore the previous settings;
3. perform positive readback;
4. record first material failure and rejected hypotheses;
5. repair the implementation through normal reviewed code changes;
6. do not create no-op/retrigger commits;
7. do not add a new bypass or required status as a shortcut.
8. after a matching, timely (`closed_at <= expires_at`) restoration readback, close the receipt as `ROLLED_BACK`; any retry opens a new bounded receipt. A late closure is `DRIFT`.

Do not continue to the next repository until the current repository is verified `TARGET`. `ROLLED_BACK` is recovery evidence, not permission to advance the serial rollout.

## Anti-overengineering rule

When a new governance mechanism is proposed, require this written justification before implementation:

```text
THREAT:
CURRENT CONTROL GAP:
WHY EXISTING AGGREGATE GATE / MERGE QUEUE / OWNER AUTHORIZATION DOES NOT COVER IT:
MINIMAL NEW CONTROL:
REMOVAL OR REVIEW CONDITION:
```

If the proposer cannot identify a concrete uncovered threat, do not add the mechanism.

Prefer broader deterministic CI over a complex classifier when the additional CI cost is reasonable for a one-person team.

Do not optimize for large-enterprise separation of duties or high merge throughput unless the organization actually changes and a new ADR explicitly changes the operating model.

## Owner interruption policy

Do not ask the owner for routine technical decisions already resolved by the binding V2 documents.

Interrupt only for:

- explicit `CONTROL_PLANE_R2` owner authorization required by GS-5;
- a security/safety/policy decision not covered by current authority;
- a required live GitHub field that is unavailable and materially changes the safe mutation;
- a rollback decision where two materially different safe recovery paths remain after evidence gathering;
- terminal completion.

Do not stop merely because a worker/session/tool timeout occurred. Persist a durable checkpoint and continue through an actual supported resume mechanism.

## Terminal definition

Do not declare V2 complete until live evidence proves all of the following:

- META requires exactly `meta-gate`;
- Game requires exactly `game-gate`;
- Platform requires exactly `platform-gate`;
- Atlas requires exactly `atlas-gate`;
- every aggregate gate has proven explicit PR and merge-group terminal fan-in behavior;
- each repository passed the moving-base canary;
- Merge Queue is the normal integration authority in all four repositories;
- strict freshness is disabled only in repositories whose moving-base canary passed;
- Game has no mandatory second-human/CODEOWNER approval dependency;
- force-push and deletion of protected `main` remain blocked;
- squash/linear-history policy remains enforced where applicable;
- obsolete external `ai-review-gate` and `provenance-gate` contexts are gone after their useful semantics are retired/internalized;
- desired-state validation agrees with live settings;
- no temporary transition/bypass remains active;
- no permanent repository remains `PENDING` or `ROLLED_BACK`;
- break-glass has passed one isolated real exercise and restoration readback;
- superseded moving-head design material cannot be mistaken for current authority.

## Completion evidence

At terminal closeout report:

- exact final `main` SHA for each repository;
- exact required contexts for each repository;
- Merge Queue and strict-freshness state;
- approval/CODEOWNER state;
- moving-base canary PR/run/merge-group evidence;
- aggregate-gate fan-in evidence;
- final desired-state audit result;
- break-glass exercise receipt;
- list of retired vs intentionally retained legacy controls and the independent threat justifying each retained control.

No success claim without direct current evidence.
