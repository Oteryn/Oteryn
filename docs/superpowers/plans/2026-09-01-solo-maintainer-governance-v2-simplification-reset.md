# Solo-Maintainer Governance V2 Simplification Reset Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the over-specified V2 lifecycle/AI-review governance with the approved native-GitHub model, then implement the minimal META Merge Queue cutover separately.

**Architecture:** PR #125 changes only durable authority/policy/prompt documentation and does not mutate live GitHub settings or machine enforcement. The follow-up META PR changes the legacy machine policy/workflows and performs the real moving-base canary before weakening strict freshness.

**Spec:** `docs/superpowers/specs/2026-09-01-solo-maintainer-governance-v2-simplification-reset-design.md`

## Constraints

- GitHub live state is the only authority for current enforcement.
- PR #125 makes no live branch-protection, ruleset, Merge Queue, provider, production, or break-glass mutation.
- No lifecycle database, comment-proof parser, attestation subsystem, second required status, or second-human dependency.
- Current `meta-gate` + legacy `ai-review-gate` enforcement remains unchanged until the follow-up META implementation proves the replacement path.
- At most one useful deep external review for a stable candidate, plus re-review only after a concrete material repair required by the still-active legacy path.
- No Work handoff; execution is chat-led.

## PR #125

- [x] ADR 0005 defines the native-GitHub merge contract and explicitly supersedes the over-specified PR #123 lifecycle/proof model.
- [x] AI review policy is default-no-review / Spark-when-useful / one-deep-review-for-high-risk, with legacy machine enforcement transition-only.
- [x] The old Work/Terra rollout prompt is superseded by short chat-led guidance.
- [x] Diff scope is spec/plan/ADR/policy/prompt only: no workflow, Python, JSON desired-state, `AGENTS.md`, or live-settings mutation.
- [x] Exact-head `meta-gate` passed on the pre-review stable candidate.
- [x] PR is Ready and Codex deep review was performed.
- [x] The first concrete review finding was addressed by assigning the reset ADR the next unused number (`0005`) and updating references.
- [x] The next concrete review finding was addressed by defining the minimal pre-canary path for legacy required contexts that cannot emit on `merge_group`: prove replacement PR coverage, remove only the incompatible context while strict freshness remains enabled, and restore exact settings if canary fails.
- [ ] Final exact-head legacy checks pass after the material review fix.
- [ ] The final material repair is re-reviewed once under the still-active legacy enforcement path.
- [ ] PR is merged through the currently permitted protected path and ADR 0005 is confirmed on protected `main`.

## Follow-up minimal META PR

- [ ] Create a fresh branch/PR from protected `main` after PR #125 merges.
- [ ] Remove legacy R0/R1/R2 and `ai-review-gate` machine/agent enforcement while preserving only the simple advisory review routing.
- [ ] Make the smallest desired-state/workflow diff that makes `meta-gate` the only target required status and validates both `pull_request` and `merge_group`.
- [ ] Run focused deterministic tests and exact-head `meta-gate` and prove replacement coverage on a representative PR.
- [ ] Capture current live protection as exact rollback state.
- [ ] If a currently required legacy context cannot emit on `merge_group`, make only that incompatible context non-required while strict freshness remains enabled; preserve all compatible contexts and the rollback snapshot.
- [ ] Run the real moving-base PR A / PR B Merge Queue canary without changing PR A head.
- [ ] If canary fails, immediately restore the exact pre-canary required-context/settings state.
- [ ] Only after canary success, make `meta-gate` the sole required external status and disable strict freshness while preserving the other baseline protections.
- [ ] Re-read live protection, resulting `main`, checks and queue integration directly from GitHub; rollback if final readback fails.
