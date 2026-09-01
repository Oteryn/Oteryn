# Solo-Maintainer Governance V2 Simplification Reset Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the over-specified V2 lifecycle/AI-review governance with the approved native-GitHub model, then implement the minimal META Merge Queue cutover separately.

**Architecture:** PR #125 changes authority and active agent-facing policy only; it does not mutate live GitHub settings and deliberately leaves legacy machine enforcement in place until the follow-up META cutover PR. The follow-up PR changes the machine desired state/workflows and performs the real moving-base canary before weakening strict freshness.

**Tech Stack:** GitHub branch protection, GitHub Actions, Merge Queue, Markdown authority/policy, existing META CI.

**Spec:** `docs/superpowers/specs/2026-09-01-solo-maintainer-governance-v2-simplification-reset-design.md`

## Global Constraints

- GitHub live state is the only authority for current enforcement.
- No live branch-protection, ruleset, Merge Queue, provider, production, or break-glass mutation in PR #125.
- Do not create a lifecycle database, comment-proof parser, attestation subsystem, second required status, or second-human dependency.
- Keep `meta-gate` + legacy `ai-review-gate` live enforcement unchanged until the follow-up META implementation proves the replacement path.
- Use at most one useful deep external review for the final stable PR #125 candidate because current live protection still requires the legacy review path.
- No Work handoff; execution is chat-led.

---

### Task 1: Make the simplification reset the active authority

**Files:**
- Modify: `docs/architecture/adr/0002-organization-governance-operating-model.md`
- Modify: `docs/superpowers/specs/2026-08-31-solo-maintainer-governance-v2-safety-amendment.md`
- Modify: `docs/superpowers/plans/2026-08-31-solo-maintainer-governance-v2.md`
- Modify: `docs/superpowers/plans/2026-08-31-solo-maintainer-governance-v2-safety-addendum.md`

**Interfaces:**
- Consumes: approved reset design.
- Produces: unambiguous precedence: the 2026-09-01 reset supersedes conflicting lifecycle/comment-proof and formal R0/R1/R2 clauses from PR #123.

- [ ] **Step 1:** Add one dated ADR amendment that states the native-GitHub permanent merge contract and explicit supersession scope.
- [ ] **Step 2:** Add a short supersession notice near the top of each older V2 spec/plan so agents do not execute retired lifecycle machinery.
- [ ] **Step 3:** Re-read all four files and verify the notices do not claim live settings already changed.

### Task 2: Simplify active AI-review and execution guidance

**Files:**
- Replace: `docs/governance/AI_REVIEW_POLICY.md`
- Modify: `AGENTS.md`
- Replace: `docs/agents/prompts/OTERYN-SOLO-MAINTAINER-GOVERNANCE-V2-ROLLOUT.md`

**Interfaces:**
- Consumes: reset AI-routing rule.
- Produces: default no external review; Spark preferred for useful ordinary review; one Codex deep review for material high-risk/control-plane changes; no formal R0/R1/R2 governance state in active human/agent policy.

- [ ] **Step 1:** Replace the long AI-review policy with a concise advisory policy and mark legacy `ai-review-gate`/machine config as transition-only until the follow-up META PR.
- [ ] **Step 2:** Replace the R0/R1/R2 section in `AGENTS.md` with the same concise routing rules.
- [ ] **Step 3:** Replace the old Work rollout prompt with a superseded notice pointing to the reset design and chat-led execution.
- [ ] **Step 4:** Re-read all three files and verify no active instruction requires Work or makes AI review a permanent required GitHub status.

### Task 3: Verify and integrate PR #125 under current protection

**Files:**
- Inspect: full PR #125 diff and changed-file list.

**Interfaces:**
- Consumes: stable PR #125 candidate.
- Produces: merged authority reset without live settings changes.

- [ ] **Step 1:** Verify the exact changed-file list is limited to authority/policy/plan/prompt files and contains no workflow, Python, JSON desired-state, or live-settings mutation.
- [ ] **Step 2:** Verify `meta-gate` on the exact final head.
- [ ] **Step 3:** Because existing live `main` still requires legacy `ai-review-gate`, perform at most one required deep review on the final stable candidate and resolve only concrete material findings.
- [ ] **Step 4:** Merge through the currently permitted protected path; do not bypass a legitimate failing check.
- [ ] **Step 5:** Re-read protected `main` and confirm the reset authority is canonical.

### Task 4: Follow-up minimal META implementation

**Files:**
- Modify only as required: `ecosystem/governance-desired-state.json`, `.github/workflows/ci.yml`, legacy AI-review enforcement files, and small focused governance tests/docs.

**Interfaces:**
- Consumes: canonical reset authority.
- Produces: META with one required `meta-gate`, Merge Queue integration freshness, zero required approvals/CODEOWNER approval, conversation resolution and linear history retained, strict freshness off only after moving-base canary.

- [ ] **Step 1:** Create a fresh branch/PR from protected `main` after PR #125 merges.
- [ ] **Step 2:** Make the smallest machine-policy/workflow diff that removes `ai-review-gate` as target merge authority and makes `meta-gate` valid for `pull_request` and `merge_group`.
- [ ] **Step 3:** Run focused deterministic tests and exact-head `meta-gate`.
- [ ] **Step 4:** Capture current live protection as rollback state.
- [ ] **Step 5:** Run the real moving-base PR A / PR B Merge Queue canary without changing PR A head.
- [ ] **Step 6:** Only after canary success, set final META required context to `meta-gate` and disable strict freshness while preserving the other baseline protections.
- [ ] **Step 7:** Re-read live protection, resulting `main`, checks and queue integration directly from GitHub; rollback if the canary or final readback fails.
