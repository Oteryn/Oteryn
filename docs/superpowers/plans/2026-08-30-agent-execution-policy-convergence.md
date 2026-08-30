# Agent Execution Policy Convergence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Converge all Oteryn providers on current effort-aware META authority and bind every permitted Remote Desktop call to its exact approved arguments.

**Architecture:** META adds a pure deterministic per-call wrapper around the existing routing/action validator plus a pure provider-adoption validator. Provider repositories retain their local product rules while replacing stale historical execution-policy pins and parallel-first requirements with live protected-META effort-aware adoption.

**Tech Stack:** Python 3, JSON policy, Markdown repository instructions, GitHub Actions / repository-native CI.

**Spec:** `docs/superpowers/specs/2026-08-30-agent-execution-policy-convergence-design.md`

## Global Constraints

- GitHub live state is authoritative for repository, Issue, PR, branch, SHA, check, review and merge facts.
- Preserve `single_agent` and `parallel_when_beneficial` effort-aware routing; do not restore parallel-first semantics.
- Preserve one active writer per writable branch/worktree and do not overlap Platform root `AGENTS.md` while PR #1270 owns it.
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

- [ ] **Step 1: Add policy call-binding schema with `deviceId` as the only non-semantic argument**
- [ ] **Step 2: Implement strict packet declaration and normalized exact argument comparison**
- [ ] **Step 3: Update META instructions to require the per-call gate immediately before invocation**
- [ ] **Step 4: Run routing/action regressions and confirm GREEN**

### Task 3: Implement deterministic provider-adoption validation

**Files:**
- Create: `tools/governance/provider_policy_adoption.py`
- Test: `tools/governance/test_remote_desktop_action_gate.py`

**Interfaces:**
- Produces: `validate_provider_agents_text(provider, text) -> list[str]` and CLI validation for supplied provider instruction files.

- [ ] **Step 1: Reject historical execution-policy authority pins**
- [ ] **Step 2: Reject parallel-first/serial-exception wording**
- [ ] **Step 3: Require current protected META authority and canonical effort-aware strategies**
- [ ] **Step 4: Run the stale/current text regressions and confirm GREEN**

### Task 4: Qualify and merge META authority

**Files:**
- Review: complete PR diff for the META convergence branch.

**Interfaces:**
- Produces: protected META `main` authority for provider adoption.

- [ ] **Step 1: Run complete exact-head `meta-gate`**
- [ ] **Step 2: Inspect all review submissions, inline threads and PR comments**
- [ ] **Step 3: Satisfy live AI-review policy for the final stable fingerprint**
- [ ] **Step 4: Reconcile protected `main` if it advanced and rerun invalidated evidence**
- [ ] **Step 5: Squash merge only with exact-head gates satisfied**

### Task 5: Adopt current META policy in Game and Atlas

**Files:**
- Modify: `Oteryn/Oteryn-Game:AGENTS.md`
- Modify: `Oteryn/Oteryn-Atlas:AGENTS.md`

**Interfaces:**
- Consumes: merged protected META execution policy and validator vocabulary.
- Produces: provider-local instructions that use current protected META authority, `single_agent`, and `parallel_when_beneficial`.

- [ ] **Step 1: Re-read each provider main/PR overlap state after META merge**
- [ ] **Step 2: Create one isolated task branch/PR per provider**
- [ ] **Step 3: Replace only stale execution-routing adoption text**
- [ ] **Step 4: Run provider exact-head gates and inspect full diffs/reviews**
- [ ] **Step 5: Merge independently when each provider gate is satisfied**

### Task 6: Reconcile Platform path ownership

**Files:**
- Reconcile: `Oteryn/Oteryn-Platform:AGENTS.md` through the currently owning PR #1270 unless live state changes.

**Interfaces:**
- Preserves: #1270 anti-loop additions and its governing dependency semantics.
- Adds: current protected META effort-aware adoption without creating a second active writer.

- [ ] **Step 1: Refresh Platform main and PR #1270 exact head/base/dependency state**
- [ ] **Step 2: Preserve all unrelated #1270 work while applying the execution-routing convergence on its existing branch**
- [ ] **Step 3: Resolve or truthfully preserve any upstream dependency blocker; do not bypass it**
- [ ] **Step 4: Run exact-head Platform gate/review and merge only when its full existing scope is legitimately ready**

### Task 7: Terminal organization verification

**Files:**
- Read-only verification across META, Game, Platform and Atlas protected main.

**Interfaces:**
- Produces: verified organization-level closeout evidence.

- [ ] **Step 1: Read all four protected main SHAs and root instructions**
- [ ] **Step 2: Confirm no provider presents a historical META execution-policy pin as current authority**
- [ ] **Step 3: Confirm no provider requires parallel-first/serial-exception planning**
- [ ] **Step 4: Confirm META exact-call binding tests and policy are canonical**
- [ ] **Step 5: Close Issue #104 only when all applicable repository states are terminal or record the exact remaining blocker**