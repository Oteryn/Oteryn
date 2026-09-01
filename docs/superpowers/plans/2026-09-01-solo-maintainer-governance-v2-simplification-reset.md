# Solo-Maintainer Governance V2 Simplification Reset Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the over-specified V2 lifecycle/AI-review governance with the approved native-GitHub model, then implement the minimal META Merge Queue cutover separately.

**Architecture:** PR #125 changes only durable authority/policy/prompt documentation and does not mutate live GitHub settings or machine enforcement. The follow-up META PR changes the legacy machine policy/workflows and performs the real moving-base canary before weakening strict freshness.

**Tech Stack:** GitHub branch protection, GitHub Actions, Merge Queue, Markdown authority/policy, existing META CI.

**Spec:** `docs/superpowers/specs/2026-09-01-solo-maintainer-governance-v2-simplification-reset-design.md`

## Global Constraints

- GitHub live state is the only authority for current enforcement.
- No live branch-protection, ruleset, Merge Queue, provider, production, or break-glass mutation in PR #125.
- Do not create a lifecycle database, comment-proof parser, attestation subsystem, second required status, or second-human dependency.
- Keep current `meta-gate` + legacy `ai-review-gate` enforcement unchanged until the follow-up META implementation proves the replacement path.
- Use at most one useful deep external review for the final stable PR #125 candidate because current protected `main` still requires the legacy review path.
- No Work handoff; execution is chat-led.

---

### Task 1: Make the reset authoritative

**Files:**
- Create: `docs/architecture/adr/0003-solo-maintainer-governance-v2-simplification-reset.md`
- Keep: `docs/superpowers/specs/2026-09-01-solo-maintainer-governance-v2-simplification-reset-design.md`

**Interfaces:**
- Consumes: approved reset design.
- Produces: explicit later authority that supersedes conflicting lifecycle/comment-proof, formal R0/R1/R2, `ai-review-gate`-as-target-authority, and Work-specific clauses from PR #123 while retaining non-conflicting safety invariants.

- [x] **Step 1:** Add ADR 0003 with the native-GitHub permanent merge contract.
- [x] **Step 2:** State exact supersession scope and retain the moving-base canary, fail-closed aggregate gate, rollback, no-second-human, no-bypass, and direct-readback invariants.

### Task 2: Simplify active review/execution guidance without breaking current protection

**Files:**
- Replace: `docs/governance/AI_REVIEW_POLICY.md`
- Replace: `docs/agents/prompts/OTERYN-SOLO-MAINTAINER-GOVERNANCE-V2-ROLLOUT.md`

**Interfaces:**
- Consumes: reset AI-routing rule.
- Produces: concise target policy while explicitly leaving legacy machine enforcement untouched until the follow-up META PR.

- [x] **Step 1:** Replace the long AI-review policy with default-no-review / Spark-when-useful / one-deep-review-for-high-risk guidance.
- [x] **Step 2:** Mark `ai-review-gate`, R0/R1/R2 machine configuration, fingerprints/envelopes and attestations as transition-only legacy rather than target architecture.
- [x] **Step 3:** Replace the old Work rollout prompt with a superseded chat-led rollout notice.

### Task 3: Verify and integrate PR #125 under current protection

**Files:**
- Inspect: full PR #125 diff and changed-file list.

**Interfaces:**
- Consumes: stable PR #125 candidate.
- Produces: merged authority reset without live settings changes.

- [ ] **Step 1:** Verify the exact changed-file list contains only the reset spec/plan/ADR/policy/prompt and no workflow, Python, JSON desired-state, AGENTS, or live-settings mutation.
- [ ] **Step 2:** Verify `meta-gate` on the exact final head.
- [ ] **Step 3:** Mark the PR Ready only after the candidate is stable; satisfy the currently configured legacy review path at most once for that stable candidate.
- [ ] **Step 4:** Resolve only concrete material findings; do not start a review-fix loop for theoretical hardening.
- [ ] **Step 5:** Merge through the currently permitted protected path and confirm the reset authority on protected `main`.

### Task 4: Follow-up minimal META implementation

**Files:**
- Modify only as required: `AGENTS.md`, `ecosystem/governance-desired-state.json`, `.github/workflows/ci.yml`, legacy AI-review enforcement files, and small focused governance tests/docs.

**Interfaces:**
- Consumes: canonical reset authority.
- Produces: META with one required `meta-gate`, Merge Queue integration freshness, zero required approvals/CODEOWNER approval, conversation resolution and linear history retained, strict freshness off only after moving-base canary.

- [ ] **Step 1:** Create a fresh branch/PR from protected `main` after PR #125 merges.
- [ ] **Step 2:** Remove the legacy R0/R1/R2 and `ai-review-gate` machine/agent enforcement while preserving only the simple advisory routing rule.
- [ ] **Step 3:** Make the smallest workflow/desired-state diff that makes `meta-gate` the only target required status and validates `pull_request` plus `merge_group` candidates.
- [ ] **Step 4:** Run focused deterministic tests and exact-head `meta-gate`.
- [ ] **Step 5:** Capture current live protection as rollback state and run the real moving-base PR A / PR B Merge Queue canary without changing PR A head.
- [ ] **Step 6:** Only after canary success, make `meta-gate` the required external status and disable strict freshness while preserving the other baseline protections.
- [ ] **Step 7:** Re-read live protection, resulting `main`, checks and queue integration directly from GitHub; rollback if the canary or final readback fails.
