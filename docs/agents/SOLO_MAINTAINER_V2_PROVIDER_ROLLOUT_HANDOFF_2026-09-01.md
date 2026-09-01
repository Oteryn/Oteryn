# Solo-Maintainer Governance V2 — Provider Rollout Handoff

Status: **ACTIVE CONTINUATION CHECKPOINT**  
Continuation alias: **`OTERYN-SOLO-MAINTAINER-GOVERNANCE-V2-PROVIDER-CLOSEOUT`**  
Recorded: **2026-09-01**  
Coordinator repository: `Oteryn/Oteryn`

## Absolute continuation rule

**GitHub live state is the only source of truth.** Every SHA, PR number, workflow run, ruleset value and status below is a locator/evidence snapshot only. Before the next mutation, refresh the exact repository default branch, governing authority, PR head, required checks, review threads, rulesets/classic protection, Merge Queue state and current authorization.

This handoff is not a new authorization grant. It records work already performed so the next agent can resume without reconstructing the programme from chat history.

Use the GitHub control plane first. Do not route ordinary repository work through Work mode or Remote Desktop. Do not create no-op/retrigger/merge-up/checkpoint commits merely to make CI or review run again. The checkpoint commit containing this file exists only because the owner explicitly requested a durable handoff.

Canonical authority remains:

- `AGENTS.md`;
- `docs/architecture/adr/0005-solo-maintainer-governance-v2-simplification-reset.md`;
- `ecosystem/governance-desired-state.json`;
- `docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md`.

## Target state

For every permanent repository:

- pull requests required;
- exactly one externally required aggregate gate: `meta-gate`, `game-gate`, `platform-gate`, or `atlas-gate`;
- the aggregate gate fails closed for ordinary PR qualification and native `merge_group` qualification;
- GitHub Merge Queue is the integration/freshness authority after a successful real canary;
- strict status-check freshness is disabled only **after** that repository's successful Merge Queue canary;
- required approving reviews = `0`;
- CODEOWNER review is not required;
- review-thread/conversation resolution remains required;
- linear history remains required and normal merge method is squash;
- no broad bypass, force pushes or deletions.

AI review is advisory. Do not restore formal R0/R1/R2, `ai-review-gate`, review fingerprints, attestations, lifecycle databases, comment-proof parsers or standing review controllers as merge authority.

## META — complete

Current snapshot at handoff:

- `main`: `690158f94c9f272a840ec8bc4c4fe3b642faa547`;
- PR #125 proved the real moving-base Merge Queue canary and merged through the queue;
- PR #129 (`governance: remove legacy AI review machinery`) is merged on current `main`;
- branch readback exposes only `meta-gate` as required;
- `ecosystem/governance-desired-state.json` records META `rollout_state: COMPLETE`, Merge Queue `true`, strict freshness `false`, approvals `0`, CODEOWNER `false`.

Do not redo META canary or recreate deleted legacy review machinery. If a future decision depends on a live setting not exposed by the connector, verify it directly from current GitHub UI/API rather than inferring from this checkpoint.

## GAME — implementation candidate green, final review/cutover still pending

Repository: `Oteryn/Oteryn-Game`

Snapshot:

- current `main`: `c52e45aac123507ea9aa1b45791674db2de14f7d`;
- active repository ruleset: ID `20991995`, `Protect main`;
- live ruleset currently has approvals `0`, CODEOWNER review **true**, conversation resolution true, squash only, strict required status checks **true**, sole required status `game-gate`, no bypass actors, deletion/non-fast-forward blocked;
- PR **#265**: `https://github.com/Oteryn/Oteryn-Game/pull/265`;
- branch: `governance/solo-maintainer-v2-merge-queue`;
- exact PR head at handoff: `7a966fbd3ac9bf97fc2bdc8df6d3633bc4b87c1e`;
- current exact-head workflows are green:
  - Merge gate run `33510962541` — SUCCESS;
  - Architecture semantic audit `33510962572` — SUCCESS;
  - Agent governance `33510962769` — SUCCESS.

PR #265 currently:

- preserves the existing PR-only `merge-gate.yml`;
- adds a disjoint `merge_group`-only path that publishes the same external `game-gate` context;
- retires the non-required duplicate merge-authority audit;
- encodes the solo-maintainer target for the repository configuration workflow/policy;
- moves active root AI-review authority to the META advisory policy;
- hardens the existing repository-policy validator for the new Merge Queue gate;
- retires active local standing-Codex-controller enforcement rather than merely hiding it behind prose.

### Game review state that MUST be refreshed

Codex previously found real P1s during this PR:

1. the new merge-group workflow could qualify itself because the validator initially did not validate it fail-closed;
2. fragment-only validation allowed behavioral modifiers such as `continue-on-error` to bypass qualification;
3. the old local standing Codex controller remained active in governance/scheduler semantics despite advisory-only root prose.

Those findings were repaired and the head advanced to `7a966f…`; all current PR workflows are green. **There is not yet a final Codex review recorded on exact current head `7a966f…`.** Existing review threads were still open at handoff:

- `PRRT_kwDOT8SzxM6eGk8_` — original merge-group validator P1;
- `PRRT_kwDOT8SzxM6eHBKC` — `continue-on-error`/canonical-structure P1 (outdated but unresolved at snapshot);
- `PRRT_kwDOT8SzxM6eHBKK` — still-active local Codex-controller P1.

### Next Game actions

1. Fresh-preflight #265 and verify the exact head is still the intended candidate.
2. Inspect the final diff specifically against the three P1s above.
3. Run **one final deep Codex review on the exact stable head** to confirm those material P1s are closed. Do not start another review loop unless a genuinely new P0/P1 is found.
4. If clean, reply with exact fix evidence and resolve the old P1 threads.
5. Refresh the current `Repository configuration` workflow and policy JSON. If it still safely supports the target, use that existing admin path rather than inventing a new settings writer.
6. Transition live Game protection while strict freshness remains on: CODEOWNER off, approvals 0, sole required `game-gate`, Merge Queue enabled, all other target protections retained.
7. Integrate #265 through a **real Merge Queue canary**. Do not use direct `merge_pull_request` once Merge Queue is required.
8. Only after successful native `merge_group` qualification and queue integration, disable strict freshness and positively read back the target state.
9. Mark Game `rollout_state: COMPLETE` in META only after the live target is actually verified.

## PLATFORM — candidate green and clean-reviewed; live cutover pending

Repository: `Oteryn/Oteryn-Platform`

Snapshot:

- current `main`: `0b7523793103bd8e2b402d1793d332a7ef58c1ae`;
- classic branch protection currently exposes sole required status `platform-gate`;
- repository rulesets endpoint returned none;
- PR **#1285**: `https://github.com/Oteryn/Oteryn-Platform/pull/1285`;
- branch: `governance/solo-maintainer-v2-provider-cleanup`;
- exact head: `817c55a6a3b76e77d0c2cfa4a0abf0136f723e31`;
- scope is root `AGENTS.md` only: retire duplicate Platform owner-funded/Spark standing AI policy and point to META advisory policy;
- exact-head runs are green:
  - CI `33506528721` — SUCCESS;
  - Agent Governance `33506528724` — SUCCESS;
  - Synology Container Hygiene `33506528757` — SUCCESS;
- one exact-head Codex deep review completed on `817c55a…` with **no major issues**.

Platform's existing `platform-gate` already supports native `pull_request` and `merge_group`; no additional workflow PR is justified solely for rollout.

### Next Platform actions

After Game is terminally verified (preserve provider order `META -> Game -> Platform -> Atlas`):

1. Fresh-preflight #1285 and current branch protection/Merge Queue state.
2. Do not add another review unless the head materially changes.
3. Enable Merge Queue while retaining strict freshness for the canary and keep `platform-gate` as the sole required status; align approvals/CODEOWNER and other target settings if current live values differ.
4. Integrate #1285 through the real Merge Queue canary.
5. After successful native merge-group qualification/integration, disable strict freshness and positively read back target state.
6. Mark Platform `rollout_state: COMPLETE` in META only after verified live completion.

The current GitHub connector did not expose a safe classic-branch-protection/Merge-Queue write action during this session. If that is still true after fresh capability discovery, use only the smallest necessary owner UI changes; do not build a new settings automation merely for this rollout.

## ATLAS — governance candidate blocked by independent qualification-product state

Repository: `Oteryn/Oteryn-Atlas`

Snapshot:

- current `main`: `2d6309a4df1580ce1a23be844b35c6a3b125b131`;
- no repository rulesets were returned;
- classic protection currently requires both `provenance-gate` and `atlas-gate`;
- provider PR **#281**: `https://github.com/Oteryn/Oteryn-Atlas/pull/281`;
- branch: `governance/solo-maintainer-v2-merge-queue`;
- exact head: `dbc56846bc9286888d4f43a6189ef0afb73fdaee`;
- PR #281 internalizes full pinned-source provenance into the aggregate path, retires the separate provenance workflow, and adds a `merge_group`-only `atlas-gate`; existing self-pinned `ci.yml` is intentionally byte-identical.

Current #281 verification state:

- CodeQL is green;
- deterministic/provenance/browser-semantic/WebGL/project/repository-contract layers reached green during diagnosis;
- CI is not terminal green because protected-hosted browser qualification failed;
- protected executor workflow run `33508457703` on exact #281 head classified the failure `HOSTED_BROWSER_ASSERTION_FAILED`;
- hosted shard ran 68 Playwright tests with 1 worker: 62 failed, 6 passed;
- repeated failure signals included:
  - `semantic search source authority invalid`;
  - `x is outside exported floor bounds`;
  - `requested floor is not exported`;
  - `Creature overlay disabled: animation Game SHA mismatch`;
  - `creature catalog contract unsupported`.

This is not evidence that #281's governance/provenance change itself should weaken browser assertions or mutate product behavior.

### Atlas prerequisite / likely root dependency

Open PR **#280**: `https://github.com/Oteryn/Oteryn-Atlas/pull/280`

- title: `fix(verification): repin functional qualification product`;
- branch: `fix/issue-179-protected-execution-contract-promotion`;
- exact head at handoff: `eeb0c3bb4dfd9ec4c327b6e14fd4466b6b8f1878`;
- it repins the protected functional qualification product to the corrected multi-chunk fixture and is independently scoped from the provider rollout.

On #280 head, deterministic verification, repository contract, semantic/browser/WebGL/project jobs and provenance were green in run `33506169612`; its `atlas-gate` failed because `Protected Hosted Playwright evidence` timed out waiting for an authoritative exact-candidate protected-hosted fan-in artifact. Before touching #281 product behavior, inspect the other current Actions runs for `head_sha=eeb0c3…` and resolve #280's protected-hosted qualification lifecycle/root cause.

### Next Atlas actions

1. Fresh-preflight #280 and #281 plus current #179/#272 verification ownership/state.
2. Resolve the independent #280 protected qualification-product path first if live evidence still confirms it is the prerequisite.
3. If #280 lands, refresh #281 against the resulting current protected Atlas `main` through the repository's normal non-destructive integration path and rerun exact-head validation.
4. Do not weaken browser assertions, provenance or product identity merely to make the governance PR green.
5. Once #281 is stable and green, perform at most one material deep review unless a real P0/P1 requires repair.
6. Then transition classic protection while strict freshness remains on: internalized provenance must be proven before removing external `provenance-gate`; retain only `atlas-gate`, enable Merge Queue, preserve all other target protections.
7. Integrate #281 through a real Merge Queue canary.
8. Only after success disable strict freshness, positively read back target state, then mark Atlas `rollout_state: COMPLETE` in META.

## Final META closeout

After Game, Platform and Atlas are each live-verified at target:

1. refresh all four permanent repositories from GitHub live state;
2. update only the provider `rollout_state` fields in `ecosystem/governance-desired-state.json` from `PENDING` to `COMPLETE` when the facts support it;
3. run focused META deterministic validation / `meta-gate`;
4. integrate that small closeout through the normal protected META path;
5. close/supersede only genuinely obsolete rollout follow-ups after checking their current live relevance;
6. report terminal completion using current GitHub facts, not this checkpoint.

## Resume command for the next agent

Use this alias:

`OTERYN-SOLO-MAINTAINER-GOVERNANCE-V2-PROVIDER-CLOSEOUT`

Then instruct the agent:

> Continue autonomously from the durable handoff in `Oteryn/Oteryn` at `docs/agents/SOLO_MAINTAINER_V2_PROVIDER_ROLLOUT_HANDOFF_2026-09-01.md`. GitHub live state is the only source of truth. Fresh-preflight all listed repositories/PRs before mutation, preserve the canonical target and provider order, do not resurrect legacy review/proof machinery, and continue until the rollout is terminally complete or a genuine owner-only authorization/capability boundary is reached.
