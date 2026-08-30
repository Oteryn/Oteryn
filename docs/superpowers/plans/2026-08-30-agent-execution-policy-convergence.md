# Agent Execution Policy Convergence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Converge all Oteryn providers on current effort-aware META authority, bind every permitted Remote Desktop call to its exact approved arguments, and preserve bounded autonomous execution without duplicate governance writers.

**Architecture:** META adds a pure deterministic per-call wrapper around the existing routing/action validator plus a pure provider-adoption validator. The previously separate META stall-loop PR #73 is superseded by this rollout: its executable guard/state/workflow/test work is preserved, while bounded lifecycle authority is modularized into a dedicated contract. Provider repositories retain their local product rules and reuse their already-active root-`AGENTS.md` PRs while replacing stale historical execution-policy pins and parallel-first requirements with live protected-META effort-aware adoption.

**Tech Stack:** Python 3, JSON policy, Markdown repository instructions, GitHub Actions / repository-native CI.

**Spec:** `docs/superpowers/specs/2026-08-30-agent-execution-policy-convergence-design.md`

## Global Constraints

- GitHub live state is authoritative for repository, Issue, PR, branch, SHA, check, review and merge facts.
- Preserve `single_agent` and `parallel_when_beneficial` effort-aware routing; do not restore parallel-first semantics.
- Preserve one active writer per writable branch/worktree. Game PR #150, Platform PR #1270 and Atlas PR #182 already own their provider root `AGENTS.md` paths.
- Remote Desktop remains default-deny; always-forbidden tools remain always forbidden.
- No production, deployment, host, secret, ruleset or branch-protection mutation is authorized by this plan.

---

### Task 1: Specify RED regressions

**Files:**
- Modify: `tools/governance/test_remote_desktop_action_gate.py`

**Interfaces:**
- Consumes: existing `agent_execution_routing.validate_remote_desktop_action`.
- Produces: executable expectations for `validate_remote_desktop_call(...)` and `validate_provider_agents_text(...)`.

- [x] **Step 1: Add failing exact-call argument tests**
- [x] **Step 2: Add failing stale-provider adoption tests**
- [x] **Step 3: Run META CI on the exact head and confirm failure is caused by missing new production modules**
- [x] **Step 4: Record RED head `2a4a44fe1bd8f68b99ecc8af1d8f6f1c07f48007`**

### Task 2: Implement exact Remote Desktop call binding

**Files:**
- Create: `tools/governance/remote_desktop_call_gate.py`
- Modify: `ecosystem/agent-execution-routing-policy.json`
- Modify: `AGENTS.md`
- Modify: `docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md`

**Interfaces:**
- Consumes: `validate_remote_desktop_action(host_action, remote_tool, packet=..., live_state=..., policy=...) -> list[str]`.
- Produces: `validate_remote_desktop_call(host_action, remote_tool, tool_arguments, *, packet, live_state, policy) -> list[str]`.

- [x] **Step 1: Add call-binding policy schema with `deviceId` as the only non-semantic argument**
- [x] **Step 2: Require exact `{tool, arguments}` declarations and normalized exact argument comparison at the direct-call boundary**
- [x] **Step 3: Update META instructions and central access contract to require the per-call gate immediately before invocation**
- [x] **Step 4: Run routing/action regressions and confirm GREEN**

### Task 3: Consolidate bounded autonomous execution

**Files:**
- Preserve/adapt: `.github/workflows/governance-ai-review-recheck.yml`
- Create: `docs/agents/contracts/BOUNDED_AUTONOMOUS_EXECUTION_POLICY.md`
- Preserve/update: `docs/agents/EXECUTION_STATE_CONTRACT.json`
- Preserve: `tools/agents/execution_guard.py`
- Preserve: `tools/agents/execution_state.py`
- Preserve/adapt: bounded-execution tests and META CI step.

**Interfaces:**
- Produces: deterministic `RUNNING` / `WAITING_EXTERNAL` / `STALLED` lifecycle, candidate freeze, bounded retries and same-head review recheck without no-op commits.

- [x] **Step 1: Reconcile old META PR #73 instead of restarting or discarding its work**
- [x] **Step 2: Preserve non-conflicting executable files by exact Git blob identity**
- [x] **Step 3: Modularize bounded lifecycle authority without weakening current effort-aware v2**
- [x] **Step 4: Bind `EXECUTION_STATE_CONTRACT.json` to the dedicated bounded policy and add regression coverage**
- [x] **Step 5: Close old PR #73 as superseded after preservation evidence is recorded**

### Task 4: Implement deterministic provider-adoption validation

**Files:**
- Create: `tools/governance/provider_policy_adoption.py`
- Test: `tools/governance/test_remote_desktop_action_gate.py`

**Interfaces:**
- Produces: `validate_provider_agents_text(provider, text) -> list[str]` and CLI validation for supplied provider instruction files.

- [x] **Step 1: Reject historical execution-policy authority pins**
- [x] **Step 2: Reject parallel-first/serial-exception wording**
- [x] **Step 3: Require current protected META authority and canonical effort-aware strategies**
- [x] **Step 4: Run stale/current adoption regressions and confirm GREEN**

### Task 5: Qualify and merge META authority

**Files:**
- Review: complete PR #106 diff for the META convergence branch.

**Interfaces:**
- Produces: protected META `main` authority for provider adoption.

- [x] **Step 1: Run complete exact-head `meta-gate` on the final implementation generation before durable-plan closeout**
- [x] **Step 2: Classify the candidate under the live AI-review policy (`R2`, deep review required)**
- [ ] **Step 3: Run exact-head `meta-gate` after this final durable-plan update and freeze the candidate**
- [ ] **Step 4: Inspect all review submissions, inline threads and PR comments**
- [ ] **Step 5: Satisfy live deep AI-review policy for the final stable fingerprint**
- [ ] **Step 6: Reconcile protected `main` if it advanced and rerun invalidated evidence**
- [ ] **Step 7: Squash merge only with exact-head gates satisfied**

### Task 6: Adopt current META policy in Game, Platform and Atlas

**Files:**
- Reconcile: `Oteryn/Oteryn-Game:AGENTS.md` through existing PR #150.
- Reconcile: `Oteryn/Oteryn-Platform:AGENTS.md` through existing PR #1270.
- Reconcile: `Oteryn/Oteryn-Atlas:AGENTS.md` through existing PR #182.

**Interfaces:**
- Consumes: merged protected META execution policy and validator vocabulary.
- Preserves: each provider PR's bounded-execution additions and provider-local stricter safety/testing rules.
- Produces: provider-local instructions that use current protected META authority, `single_agent`, `parallel_when_beneficial`, exact-call RDC binding and bounded autonomous execution.

- [ ] **Step 1: Re-read each provider protected main and owning PR exact head/base after META merge**
- [ ] **Step 2: Preserve existing anti-loop work while replacing only stale execution-routing adoption text on each existing branch**
- [ ] **Step 3: Replace historical dependency on META PR #73 with the merged protected-META authority from #106**
- [ ] **Step 4: Run provider exact-head gates and inspect full diffs/reviews**
- [ ] **Step 5: Merge each provider independently when its complete existing scope is legitimately ready**

### Task 7: Terminal organization verification

**Files:**
- Read-only verification across META, Game, Platform and Atlas protected main.

**Interfaces:**
- Produces: verified organization-level closeout evidence.

- [ ] **Step 1: Read all four protected main SHAs and root instructions**
- [ ] **Step 2: Confirm no provider presents a historical META execution-policy pin as current authority**
- [ ] **Step 3: Confirm no provider requires parallel-first/serial-exception planning**
- [ ] **Step 4: Confirm META exact-call binding, bounded execution and drift-detection regressions are canonical**
- [ ] **Step 5: Close Issue #104 only when all applicable repository states are terminal or record the exact remaining blocker**