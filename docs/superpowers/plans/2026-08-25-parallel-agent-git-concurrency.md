# Parallel-Agent Git Concurrency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Roll out the accepted organization-wide Git concurrency model so parallel agents preserve valid task work across unrelated `main` advancement and reconcile only at the integration boundary.

**Architecture:** `Oteryn/Oteryn` remains the canonical META authority. The normative procedure lives in `docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md`; Game, Platform and Atlas keep only a thin bootstrap rule in root `AGENTS.md` because instructions do not inherit across repositories. Each repository uses its normal Issue -> task branch -> PR -> exact-head CI/review -> squash-merge lifecycle.

**Tech Stack:** GitHub Issues, branches, pull requests, Markdown policy/ADR files, repository-native GitHub Actions gates.

**Spec:** `docs/architecture/adr/0004-parallel-agent-git-concurrency.md`

## Global Constraints

- Permanent repositories in scope: `Oteryn/Oteryn`, `Oteryn/Oteryn-Game`, `Oteryn/Oteryn-Platform`, `Oteryn/Oteryn-Atlas`.
- Archived migration/backup repositories remain untouched.
- No provider runtime, product behavior, deployment, runner configuration, secrets or branch-protection settings are changed.
- `admission_main_sha` is immutable provenance; `task_head_sha` is the task branch head; `integration_main_sha` is the current default-branch SHA selected at final integration.
- `main` movement alone is `UPSTREAM_ADVANCED`, never automatic work invalidation.
- Published task branches use non-destructive merge-up refresh by default; no generic reset/restart/force-push to chase `main`.
- Changed governing authority must be reloaded before further mutation when upstream changes touch it.
- After a refresh, renew deterministic exact-head CI. Reuse AI review only when the trusted review gate proves the configured clean-reuse conditions on the new task head; otherwise obtain fresh exact-head AI review. A changed head alone does not authorize duplicate review invocation when the gate-valid reuse path applies.
- Only verified task supersession, incompatible authority/safety change, semantic conflict or failed reconciliation invalidates affected work.

---

### Task 1: Make META contract normative

**Files:**
- Modify: `docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md`
- Existing spec: `docs/architecture/adr/0004-parallel-agent-git-concurrency.md`
- Existing plan: `docs/superpowers/plans/2026-08-25-parallel-agent-git-concurrency.md`

**Interfaces:**
- Consumes: ADR 0004 terminology and lifecycle semantics.
- Produces: canonical organization-wide agent execution procedure referenced by META root instructions and provider bootstrap rules.

- [x] **Step 1: Refresh META authority and overlap state**

Read current protected `main`, Issue #61, PR #62, open PR changed-file overlap and the current contract blob SHA. If `main` advanced, classify the delta under ADR 0004 rather than recreating the task.

- [x] **Step 2: Add the normative concurrency section**

Add a focused section that defines the three revision coordinates, `UPSTREAM_ADVANCED`, authority reload triggers, one-agent/one-writable-worktree ownership, durable checkpoints, late merge-up integration, lost-merge-race handling, evidence supersession and material invalidation criteria.

- [x] **Step 3: Verify the exact diff**

Use GitHub compare/PR diff to prove the META PR changes only the ADR, implementation plan and central execution contract. Confirm there are no runner/recovery/provider-runtime changes.

- [ ] **Step 4: Run repository-required validation**

Mark PR #62 Ready only after the exact final META head is stable. Require `meta-gate` and `ai-review-gate` as configured on protected `main`; inspect review threads/comments before merge.

- [ ] **Step 5: Squash-merge META**

Merge PR #62 only with the expected exact head SHA after required checks/reviews pass. Verify merged `main` contains ADR 0004 and the updated central contract.

---

### Task 2: Roll out Game bootstrap rule

**Files:**
- Modify: `Oteryn/Oteryn-Game:AGENTS.md`

**Interfaces:**
- Consumes: merged META ADR 0004 and central execution contract.
- Produces: Game bootstrap-visible minimum concurrency semantics without changing Game runtime or validation ownership.

- [ ] **Step 1: Refresh Game `main`, instructions and overlaps**

Read current Game `main`, root `AGENTS.md`, open Issues/PRs and changed files for any PR touching root `AGENTS.md` or the same governance semantics.

- [ ] **Step 2: Create Game lifecycle records**

Create one Game Issue linked to META #61, one dedicated branch from the exact current Game `main`, and one PR.

- [ ] **Step 3: Add the thin concurrency section**

Add only the bootstrap minimum: immutable `admission_main_sha`; one active agent per task branch/writable worktree; `main` movement alone does not invalidate work; reload changed governing authority; late merge-up to `integration_main_sha`; rerun invalidated exact-head proof on resulting `task_head_sha`; verified semantic/authority conflict or task supersession is required for invalidation.

- [ ] **Step 4: Verify and merge Game**

Inspect the exact one-file diff, require the current protected Game merge gate on the exact head, inspect reviews/threads, squash-merge with expected head SHA, and verify resulting Game `main` contains the rule.

---

### Task 3: Extend Platform multi-agent rule

**Files:**
- Modify: `Oteryn/Oteryn-Platform:AGENTS.md`

**Interfaces:**
- Consumes: Platform's existing `## Multi-agent concurrency` section plus merged META concurrency authority.
- Produces: Platform-specific extension without duplicating the full central contract.

- [ ] **Step 1: Refresh Platform `main`, instructions and overlaps**

Read current Platform `main`, root `AGENTS.md`, open Issues/PRs and changed files for any PR touching `AGENTS.md` or multi-agent policy.

- [ ] **Step 2: Create Platform lifecycle records**

Create one Platform Issue linked to META #61, one dedicated branch from current protected `main`, and one PR.

- [ ] **Step 3: Extend the existing section minimally**

Keep existing one-agent/one-branch/worktree and advisory `owned_paths` rules. Add the three revision coordinates, `UPSTREAM_ADVANCED` semantics, authority reload trigger, non-destructive late merge-up refresh and exact-head evidence renewal. Do not duplicate unrelated delivery/security text.

- [ ] **Step 4: Verify and merge Platform**

Inspect the exact one-file diff, run/require `platform-gate` and any repository-required review gate on the exact head, inspect reviews/threads, squash-merge with expected head SHA, and verify resulting Platform `main` contains the extension.

---

### Task 4: Roll out Atlas bootstrap rule

**Files:**
- Modify: `Oteryn/Oteryn-Atlas:AGENTS.md`

**Interfaces:**
- Consumes: merged META ADR 0004 and central execution contract.
- Produces: Atlas bootstrap-visible concurrency semantics that prevent current parallel agents from restarting work merely because Atlas `main` advances.

- [ ] **Step 1: Refresh Atlas `main`, instructions and overlaps**

Read current Atlas `main`, root `AGENTS.md`, open Issues/PRs and changed files for any PR touching root `AGENTS.md` or work-boundary/preflight/merge semantics.

- [ ] **Step 2: Create Atlas lifecycle records**

Create one Atlas Issue linked to META #61, one dedicated branch from current protected `main`, and one PR.

- [ ] **Step 3: Add the thin concurrency section**

Add the immutable admission SHA, one-agent/one-writable-worktree ownership, `UPSTREAM_ADVANCED` non-invalidation rule, governing-authority reload, late non-destructive merge-up integration, exact-head evidence renewal and specific material-invalidation rule.

- [ ] **Step 4: Verify and merge Atlas**

Inspect the exact one-file diff. Because this is root documentation/governance rather than safe lowercase Markdown under `docs/**`, follow the live Atlas gate classification rather than assuming heavy qualification is skippable. Require exact-head checks/reviews that live repository policy actually demands, squash-merge with expected head SHA, and verify resulting Atlas `main` contains the rule.

---

### Task 5: Cross-repository closeout

**Files:**
- No additional product files unless a repository-local merge conflict requires a scoped reconciliation commit.

**Interfaces:**
- Consumes: merged META, Game, Platform and Atlas heads.
- Produces: verified organization-wide rollout evidence and terminal lifecycle state.

- [ ] **Step 1: Read back all four protected `main` heads**

Verify each permanent repository contains its intended authority surface after merge.

- [ ] **Step 2: Verify semantic consistency**

Confirm all provider bootstrap rules agree with ADR 0004 on: moving `main` != invalid work; immutable admission coordinate; late integration; exact-head evidence renewal; specific invalidation criteria; non-destructive published-branch refresh.

- [ ] **Step 3: Close lifecycle Issues**

Close provider Issues and META #61 only after all four permanent repositories are merged and verified. Record any provider that cannot complete as an explicit blocker instead of claiming organization-wide completion.

- [ ] **Step 4: Verify branch/PR terminal state**

Confirm merged PRs and exact merge SHAs. Allow repository branch-cleanup automation to delete source branches under existing policy; do not introduce a new destructive cleanup path.
