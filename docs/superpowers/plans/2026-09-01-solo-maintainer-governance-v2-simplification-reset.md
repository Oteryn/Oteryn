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
- [x] Exact-head `meta-gate` passed on the reviewed candidates.
- [x] Concrete review findings were addressed without adding new governance subsystems: ADR identity, incompatible-context canary ordering, repository authorization/routing preflight, and rollback/owner-authorization ordering.
- [ ] Final exact-head legacy checks pass after the last material review fix.
- [ ] The final material repair is re-reviewed once under the still-active legacy enforcement path.
- [ ] PR is merged through the currently permitted protected path and ADR 0005 is confirmed on protected `main`.

## Follow-up minimal META PR

- [ ] Create a fresh branch/PR from protected `main` after PR #125 merges.
- [ ] Before any META repository-content/workflow mutation, refresh exact `main`/Issue/PR/task-head state, verify the current task authorizes the META implementation scope, and validate a fresh META-specific execution-routing packet with protected-main META `agent_execution_routing.py` and policy. Do not reuse the PR #125 packet/snapshot.
- [ ] Remove legacy R0/R1/R2 and `ai-review-gate` machine/agent enforcement in the candidate while preserving only the simple advisory review routing.
- [ ] Make the smallest desired-state/workflow diff that makes `meta-gate` the only target required status and validates both `pull_request` and `merge_group`.
- [ ] Run focused deterministic tests and exact-head `meta-gate`; prove replacement coverage on a representative PR.
- [ ] Perform the one useful Codex deep review for the stable material control-plane candidate and obtain explicit human-owner authorization bound to that current candidate before protected integration or any live branch-protection/Merge Queue/settings mutation.
- [ ] Immediately before the first live settings mutation, re-read and capture the complete exact META protection/required-context/Merge Queue/approval/CODEOWNER/strictness state as the rollback snapshot.
- [ ] Only after replacement proof and owner authorization, reduce any legacy required approval/CODEOWNER requirement if necessary for the solo-maintainer cutover; keep strict freshness enabled at this stage.
- [ ] If a currently required legacy context cannot emit on `merge_group`, make only that incompatible context non-required while strict freshness remains enabled; preserve all compatible contexts and the exact rollback snapshot.
- [ ] Run the real moving-base PR A / PR B Merge Queue canary without changing PR A head.
- [ ] If canary fails, immediately restore the complete exact pre-change settings snapshot.
- [ ] Only after canary success, make `meta-gate` the sole required external status, ensure approvals/CODEOWNER match the solo-maintainer target, and disable strict freshness while preserving the other baseline protections.
- [ ] Re-read live protection, resulting `main`, checks and queue integration directly from GitHub; rollback if final readback fails.
