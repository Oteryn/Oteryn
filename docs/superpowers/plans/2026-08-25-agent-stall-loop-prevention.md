# Agent Stall and Retry-Loop Prevention Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent autonomous Oteryn agents from entering unbounded retry/no-progress loops while preserving exact-head, fail-closed CI/review semantics.

**Architecture:** META owns the normative lifecycle contract plus a deterministic pure-Python decision guard. Trusted GitHub workflows remain the source of live evidence; asynchronous external-review evidence must trigger same-head re-evaluation rather than force a candidate mutation. Provider repositories adopt only the thin lifecycle semantics and retain their own CI/merge authority.

**Tech Stack:** Python 3, GitHub Actions YAML, GitHub Issues/PRs, Markdown governance contracts.

**Spec:** `docs/superpowers/specs/2026-08-25-agent-stall-loop-prevention-design.md`

## Global Constraints

- Do not repair or merge PR #62 as part of this task.
- Do not weaken required checks, AI-review authority, branch protection, exact-head evidence binding, or fail-closed semantics.
- Do not use no-op or checkpoint commits to retrigger qualification.
- `WAITING_EXTERNAL` must release the active worker rather than keep a session alive polling.
- Same unchanged material failure/progress state must have a bounded retry budget.
- Provider-specific CI and merge behavior remains provider-owned.

---

### Task 1: Add deterministic lifecycle guard

**Files:**
- Create: `tools/agents/execution_guard.py`
- Create: `tools/agents/test_execution_guard.py`

**Interfaces:**
- Consumes: one JSON object from stdin or `--input` containing the schema defined in the design.
- Produces: JSON with `decision`, `progress_fingerprint`, `failure_fingerprint`, `reason`, and `next_state`.

- [ ] **Step 1: Write failing unit tests**

Cover: frozen external-review wait, identical failure exhaustion, material-change reset, dependency wait, distinct integration-main refresh, no-op trigger rejection, and terminal done.

- [ ] **Step 2: Run the focused test module and confirm RED**

Run: `python -m unittest tools.agents.test_execution_guard -v`
Expected: FAIL because `tools.agents.execution_guard` does not exist.

- [ ] **Step 3: Implement the minimal pure decision engine**

Use canonical JSON serialization with sorted keys and SHA-256 for fingerprints. Exclude incidental values. Validate 40-hex SHAs when present and reject malformed snapshots fail-closed.

- [ ] **Step 4: Run focused tests and confirm GREEN**

Run: `python -m unittest tools.agents.test_execution_guard -v`
Expected: PASS.

- [ ] **Step 5: Add CLI contract tests**

Verify stdin JSON, file input, JSON output, non-zero exit on invalid schema, and no network/filesystem mutation beyond reading the specified input.

### Task 2: Make bounded waiting/stall semantics normative

**Files:**
- Modify: `docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md`
- Modify: `AGENTS.md`

**Interfaces:**
- Consumes: lifecycle states and retry semantics from the design.
- Produces: mandatory organization execution behavior for autonomous continuation.

- [ ] **Step 1: Add lifecycle states and candidate-freeze rules to the central contract**

Define `WAITING_EXTERNAL`, `STALLED`, candidate freeze, material progress, failure fingerprint, bounded retries, and no-op mutation prohibition.

- [ ] **Step 2: Amend autonomous continuation semantics**

Require an active session to end when external evidence is pending and no authorized mutation can improve the state; this is not a false stop.

- [ ] **Step 3: Add thin META bootstrap language**

Root `AGENTS.md` should make no-op retrigger commits and active polling sessions explicitly invalid and reference the central contract for details.

- [ ] **Step 4: Add deterministic text-contract assertions**

Extend the META gate or an existing governance test only if there is an existing stable local validation surface; otherwise add focused Python unit tests beside the execution guard that assert required contract markers are present.

### Task 3: Add same-head AI-review re-evaluation

**Files:**
- Modify: `.github/workflows/governance-ai-review-request.yml`
- Modify: `.github/workflows/governance-ai-review.yml`
- Modify if required: `.github/actions/ai-review-gate/action.yml`
- Test: existing/new deterministic governance tests under `tools/governance/`

**Interfaces:**
- Consumes: trusted review-request/evidence anchors and current live PR exact head.
- Produces: trusted same-head re-evaluation without a candidate commit.

- [ ] **Step 1: Add RED fixture/tests for the race**

Model sequence: initial Ready head has no evidence -> gate fails closed; trusted evidence for that same head appears later -> trusted re-evaluation succeeds if live head is unchanged.

- [ ] **Step 2: Add a trusted event path from evidence creation to re-evaluation**

Use only default-branch/trusted workflow code. The event path must carry PR identity and expected head; it must not execute candidate code.

- [ ] **Step 3: Verify live PR head before re-evaluation**

Reject if PR is closed, head changed, repository identity differs, or evidence is stale/malformed.

- [ ] **Step 4: Reuse the existing trusted verifier**

Do not duplicate review-authority grammar. Route same-head re-evaluation through the existing classifier/verifier logic or a shared script extracted from it.

- [ ] **Step 5: Run focused governance tests**

Require the stale-head case to remain RED/rejected and same-head fresh evidence to become GREEN without a Git mutation.

### Task 4: Add no-progress guard contract to task state

**Files:**
- Create or modify the smallest suitable META task-state schema/contract file after inspecting current repository conventions.
- Test: focused Python schema tests.

**Interfaces:**
- Consumes: `decision`, fingerprints, retry counters from `execution_guard.py`.
- Produces: durable checkpoint fields usable by replacement sessions and future Control Room tooling.

- [ ] **Step 1: Define durable fields**

At minimum: `candidate_frozen`, `candidate_head_sha`, `progress_fingerprint`, `failure_fingerprint`, `identical_cycle_count`, `retry_count`, `retry_limit`, `waiting_for`, `last_material_progress_at`.

- [ ] **Step 2: Validate state transitions**

Forbid `RUNNING` with `waiting_for` populated, forbid frozen head mismatch, and forbid retry counts above limit without `STALLED`/`WAITING_EXTERNAL`.

- [ ] **Step 3: Add migration compatibility**

Legacy task records without these fields remain readable but new/updated substantial tasks must emit the new fields after the policy becomes active.

### Task 5: META exact-head verification and PR closeout

**Files:**
- No new product files.

**Interfaces:**
- Consumes: Tasks 1-4.
- Produces: stable META candidate for Issue #72.

- [ ] **Step 1: Run focused unit/governance tests**

Run all new tests plus the existing META deterministic gate locally/through repository CI as available.

- [ ] **Step 2: Inspect exact diff and changed-file list**

Verify no unrelated provider/runtime/security changes.

- [ ] **Step 3: Freeze candidate**

After final material code/docs changes, make no further branch mutations solely to retrigger checks/review.

- [ ] **Step 4: Obtain exact-head required CI/review**

If external review is pending, record `WAITING_EXTERNAL`; do not create a trigger commit.

- [ ] **Step 5: Merge only on terminal green protected-gate state**

Verify resulting `main` contains the guard, workflow hardening, tests, and normative contract.

### Task 6: Provider adoption

**Files:**
- `Oteryn/Oteryn-Game:AGENTS.md`
- `Oteryn/Oteryn-Platform:AGENTS.md` and, if needed, `docs/agents/EXECUTION_PROTOCOL.md`
- `Oteryn/Oteryn-Atlas:AGENTS.md`

**Interfaces:**
- Consumes: merged META Issue #72 authority.
- Produces: thin repository-local adoption without centralizing provider gates.

- [ ] **Step 1: Create one linked provider Issue/branch/PR per repository**

Use current protected main for each admission SHA.

- [ ] **Step 2: Add the thin bootstrap rule**

Require candidate freeze, no no-op retrigger commit, bounded identical retries, `WAITING_EXTERNAL` worker release, and provider-owned fail-closed qualification.

- [ ] **Step 3: Align Platform, do not duplicate it**

Preserve its existing `WAITING`, `STALE`, session-rotation, and heavy-validation protections; add only missing organization semantics.

- [ ] **Step 4: Run each provider's exact-head required gates and merge independently**

No provider may be reported complete until its protected main is verified.

### Task 7: Organization closeout

**Files:**
- Update Issue #72 / durable closeout evidence only.

**Interfaces:**
- Consumes: merged META and provider adoption PRs.
- Produces: verified organization-wide terminal status.

- [ ] **Step 1: Read back all four protected main heads**

Verify bootstrap semantics and no regression in required checks.

- [ ] **Step 2: Verify the incident class is covered**

Prove a same-head asynchronous evidence arrival no longer requires a candidate mutation and an identical retry loop transitions to WAIT/STALLED.

- [ ] **Step 3: Close #72 only after all required adoption is terminal**

Otherwise record the exact remaining provider blocker without claiming organization-wide completion.
