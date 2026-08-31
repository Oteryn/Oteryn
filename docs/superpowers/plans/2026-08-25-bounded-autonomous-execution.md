# Bounded Autonomous Execution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent autonomous Oteryn workers from looping on unchanged CI/review/external blockers by adding a progress-sensitive execution state machine, candidate freeze, bounded retry policy, and same-head asynchronous review re-evaluation.

**Architecture:** META owns a human contract, machine-readable policy, and two small deterministic Python helpers. One helper validates execution progress/transition invariants; the other performs a tightly bounded trusted same-head rerun of the existing AI review gate when authenticated external review evidence arrives. Provider repositories adopt only the bootstrap/runtime-control pieces they need after META is merged.

**Tech Stack:** Python 3 standard library, GitHub Actions, GitHub REST API, JSON, Markdown.

**Spec:** `docs/superpowers/specs/2026-08-25-bounded-autonomous-execution-design.md`

## Global Constraints

- Scope is agent execution/governance only; no product/runtime/deployment/secret/database/game-state behavior changes.
- Existing provider validation remains authoritative.
- No no-op/checkpoint/retrigger commits may be introduced as an execution mechanism.
- Exact-head and external-review requirements remain fail-closed.
- Retry-budget exhaustion changes lifecycle state; it never bypasses a required check.
- Provider root `AGENTS.md` surfaces are not mutated concurrently with active overlapping workers.
- META admission head is `b34c94e17c0bcce11ae2caced70295930f27bb34`.

---

### Task 1: Publish the bounded-execution contract and machine policy

**Files:**
- Create: `docs/agents/contracts/BOUNDED_AUTONOMOUS_EXECUTION_POLICY.md`
- Create: `ecosystem/bounded-autonomous-execution-policy.json`
- Modify: `AGENTS.md`

**Interfaces:**
- Consumes: existing execution/continuation and AI review policies.
- Produces: canonical states, freeze rules, fingerprint fields and retry budgets consumed by Task 2 and provider adoption.

- [ ] **Step 1: Write the machine policy** with schema version 1, exact state set, progress fields, retry budgets and forbidden frozen-candidate actions copied from the spec.
- [ ] **Step 2: Write the normative contract** explaining state semantics, candidate freeze, material-progress definition, retry exhaustion, waiting/session release and fail-closed boundaries.
- [ ] **Step 3: Add a concise bootstrap requirement to META `AGENTS.md`** that makes the new contract mandatory without duplicating its body.
- [ ] **Step 4: Parse the JSON policy** using Python's standard `json` module and verify the human contract names every machine state/budget.

---

### Task 2: TDD the deterministic progress guard

**Files:**
- Create: `tools/governance/test_bounded_execution_guard.py`
- Create: `tools/governance/bounded_execution_guard.py`

**Interfaces:**
- Consumes: `ecosystem/bounded-autonomous-execution-policy.json`.
- Produces: `progress_fingerprint(snapshot, policy) -> str`, `failure_fingerprint(snapshot) -> str`, and `decide(previous, current, requested_action, policy) -> Decision`.

- [ ] **Step 1: RED — write tests for fingerprint stability.** Assert timestamps/narration do not change the progress fingerprint and material head/gate/failure changes do.
- [ ] **Step 2: Run `python3 tools/governance/test_bounded_execution_guard.py` and verify the test fails because the implementation module is absent.**
- [ ] **Step 3: GREEN — implement canonical JSON hashing and strict snapshot validation** using only the Python standard library.
- [ ] **Step 4: Re-run the focused test and verify fingerprint tests pass.**
- [ ] **Step 5: RED — add transition tests** for frozen no-op mutation denial, external waiting, identical local-failure exhaustion and verified-DONE requirement.
- [ ] **Step 6: Run the focused test and verify the new transition cases fail for missing behavior.**
- [ ] **Step 7: GREEN — implement the minimal `Decision`/`decide` state machine** required by those tests.
- [ ] **Step 8: Re-run the full focused suite and verify zero failures.**

---

### Task 3: TDD same-head AI review re-evaluation

**Files:**
- Create: `tools/governance/test_ai_review_recheck.py`
- Create: `tools/governance/ai_review_recheck.py`
- Create: `.github/workflows/governance-ai-review-recheck.yml`

**Interfaces:**
- Consumes: `ecosystem/ai-review-policy.json`, GitHub event JSON, and GitHub REST API.
- Produces: a no-content-mutation helper that re-runs at most one failed attempt-1 `governance-ai-review.yml` run for the current exact PR head when a trusted reviewer result arrives.

- [ ] **Step 1: RED — write pure selector tests** for trusted actor, current review commit, exact repository identity, failed attempt-1 selection, and no-op behavior for success/in-progress/attempt>1.
- [ ] **Step 2: Run `python3 tools/governance/test_ai_review_recheck.py` and verify failure because the helper is absent.**
- [ ] **Step 3: GREEN — implement event normalization and pure run-selection functions** with injectable API operations.
- [ ] **Step 4: Re-run focused tests and verify selector cases pass.**
- [ ] **Step 5: RED — add CLI/API adapter tests** using a fake API client for list-runs and rerun calls; assert exactly one rerun call is emitted for an eligible generation.
- [ ] **Step 6: Run tests and verify the new adapter case fails before the adapter exists.**
- [ ] **Step 7: GREEN — implement the minimal REST adapter** using `urllib.request`, exact repo/head checks, trusted reviewer logins from the policy, and `run_attempt == 1` enforcement.
- [ ] **Step 8: Re-run focused tests and verify zero failures.**
- [ ] **Step 9: Add the trusted workflow** for `pull_request_review: submitted` and reviewer-bot `issue_comment: created`, with only `actions: write`, `contents: read`, `issues: read`, and `pull-requests: read`; never check out candidate code.

---

### Task 4: Wire deterministic validation into META CI

**Files:**
- Modify: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: Task 1 policy and Task 2/3 test files.
- Produces: exact-head CI enforcement that the new guard and recheck helper stay deterministic.

- [ ] **Step 1: Add both new test files to the META governance validation step.**
- [ ] **Step 2: Add a small inline policy-contract check** for exact state names and positive retry budgets.
- [ ] **Step 3: Run all governance tests locally/in an isolated execution tree.**
- [ ] **Step 4: Validate workflow YAML parses and `git diff --check` equivalent whitespace checks are clean.**

---

### Task 5: Exact-head META qualification and merge

**Files:**
- No new files unless a review finding requires a material repair.

**Interfaces:**
- Consumes: Tasks 1-4.
- Produces: merged canonical META authority for provider adoption.

- [ ] **Step 1: Open/refresh the META PR for Issue #69 and freeze the candidate head.**
- [ ] **Step 2: Inspect the exact changed-file list/full diff and confirm no product/runtime surface changed.**
- [ ] **Step 3: Require `meta-gate` on the exact frozen head.**
- [ ] **Step 4: Obtain the policy-required external AI review once for the stable fingerprint; do not mutate the branch merely to retrigger the gate.**
- [ ] **Step 5: If asynchronous evidence arrives after an initial failure before this recheck workflow is merged, rerun the existing exact-head workflow directly rather than changing Git.**
- [ ] **Step 6: Merge only after exact-head required checks/reviews are terminal green and all material review findings are resolved.**
- [ ] **Step 7: Verify protected `main` contains the new contract, policy, helpers and workflow.**

---

### Task 6: Platform reference adoption

**Files:**
- Modify: `Oteryn/Oteryn-Platform:docs/agents/EXECUTION_PROTOCOL.md`
- Modify: `Oteryn/Oteryn-Platform:tools/agents/control_room.py`
- Modify: `Oteryn/Oteryn-Platform:tools/agents/test_control_room.py` or the repository's current control-room test file after live inspection.
- Later bootstrap modification: `Oteryn/Oteryn-Platform:AGENTS.md` only after overlapping PR #1265 is terminal.

**Interfaces:**
- Consumes: merged META bounded-execution policy.
- Produces: concrete `candidate_frozen`, progress/failure fingerprint and retry-exhaustion visibility in the existing Platform Control Room without a second orchestration system.

- [ ] **Step 1: Refresh current Platform main/PR #1265 and inspect the current Control Room tests.**
- [ ] **Step 2: Use TDD to add normalized `WAITING_EXTERNAL`/`STALLED` visibility and candidate-freeze/retry fields to existing control-room parsing/output.**
- [ ] **Step 3: Extend `EXECUTION_PROTOCOL.md` with the META minimum while preserving existing session rotation/heavy-validation rules.**
- [ ] **Step 4: After root `AGENTS.md` overlap is terminal, add only the thin bootstrap reference if still necessary.**
- [ ] **Step 5: Run Platform's exact required governance/tests and merge independently under Issue #1266.**

---

### Task 7: Game and Atlas thin adoption

**Files:**
- Modify after overlap clears: `Oteryn/Oteryn-Game:AGENTS.md`
- Modify after overlap clears: `Oteryn/Oteryn-Atlas:AGENTS.md`

**Interfaces:**
- Consumes: merged META bounded-execution policy.
- Produces: bootstrap-visible minimum state/freeze/no-progress semantics without changing product behavior.

- [ ] **Step 1: Wait for existing overlapping root-instruction PRs (#147 Game, #172 Atlas) to become terminal; do not share their writable branches.**
- [ ] **Step 2: Create provider task branches from fresh protected main for Issues Game #148 and Atlas #176.**
- [ ] **Step 3: Add the minimum bootstrap semantics: `WAITING_EXTERNAL`, `STALLED`, candidate freeze, no no-op retrigger commits, identical-failure budget, and material-progress requirement.**
- [ ] **Step 4: Run each repository's exact-head required governance/CI and merge independently.**

---

### Task 8: Organization closeout

**Files:**
- No product files.

**Interfaces:**
- Consumes: merged META + provider adoption PRs.
- Produces: terminal evidence for Issue #69.

- [ ] **Step 1: Read back protected main in all four permanent repositories.**
- [ ] **Step 2: Verify all four bootstrap/execution surfaces agree on state, freeze and no-progress semantics.**
- [ ] **Step 3: Verify provider Issues #148/#1266/#176 and their PRs are terminal.**
- [ ] **Step 4: Close #69 only when all required provider adoption is merged; otherwise record the exact waiting/blocking provider without claiming organization-wide completion.**