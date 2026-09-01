# ADR 0005 — Solo-Maintainer Governance V2 simplification reset

## Status

Accepted upon merge to `main` — approved by the repository owner on 2026-09-01 in the PR #125 implementation conversation.

## Decision

Oteryn returns Solo-Maintainer Governance V2 to a small GitHub-native enforcement model.

The permanent merge contract is:

- pull requests required;
- exactly one externally required aggregate gate per permanent repository: `meta-gate`, `game-gate`, `platform-gate`, `atlas-gate`;
- the aggregate gate executes and fails closed on both `pull_request` and `merge_group` candidates;
- GitHub Merge Queue owns integration freshness after a real moving-base canary;
- strict required-status freshness is removed only after that canary succeeds;
- required approving review count is `0` while there is one human maintainer;
- required CODEOWNER approval is disabled;
- review-thread/conversation resolution remains required;
- linear history remains required;
- force push and protected-branch deletion remain disabled;
- broad bypass/admin exemption must not weaken the baseline;
- squash remains the normal merge method;
- existing security scanning and least-privilege workflow controls remain intact.

GitHub live state is the source of truth for enforcement. Repository documentation and rollout receipts record intent/history but do not become a second merge authority.

## Moving-base canary

Before strict freshness is disabled for a repository, first prove the replacement aggregate gate on a representative PR. If a currently required legacy context cannot emit on `merge_group`, capture the exact rollback state and make only that incompatible context non-required before enqueueing the canary, while keeping strict required-status freshness enabled. Do not remove compatible required contexts or disable strict freshness at this stage. If the canary fails, restore the exact pre-change required-context/settings state.

Then prove the moving-base scenario:

1. PR A reaches a stable green head X.
2. PR B advances protected `main`.
3. PR A remains exactly at X; do not merge/rebase the new `main` into A.
4. PR A enters GitHub Merge Queue.
5. GitHub creates the synthetic merge-group candidate against the advanced base.
6. The repository aggregate gate succeeds on that merge-group SHA.
7. PR A integrates through Merge Queue.
8. Final protected-main and settings state are read back directly from GitHub.

If this fails, restore the captured pre-change settings. Do not create no-op, retrigger, checkpoint, or merge-up commits merely to progress governance state.

## Rollout evidence

Keep one small human-readable receipt in the existing rollout Issue/PR with the pre-change settings, PR A/head, PR B/main advance, merge-group SHA, gate result, resulting protected-main commit, and final settings or rollback readback.

The receipt is evidence only. It is not a database, state machine, required status, parser input, identity authority, or merge authority.

## Retired V2 mechanisms

The following requirements introduced by the PR #123 safety packet are superseded and are no longer mandatory V2 governance mechanisms:

- `PENDING` / `TRANSITION` / `ROLLED_BACK` / `SUCCESS` / `DRIFT` lifecycle state-machine authority;
- mandatory `PENDING_BASELINE`, `PRE_TRANSITION`, and `TERMINAL` JSON comment protocols;
- rollout fingerprints as merge or terminal-closeout authority;
- malformed/duplicate lifecycle-comment parsing and heuristics;
- cross-repository comment-ledger chronology enforcement;
- terminal closeout dependent on parsing that ledger;
- custom proof machinery whose only purpose is to reproduce facts directly readable from GitHub.

A small read-only desired-state audit may continue to report target mismatch or `UNKNOWN` directly from GitHub without recreating the retired subsystem.

## AI review

External AI review is optional review assistance, not GitHub merge enforcement.

Formal `R0`, `R1`, and `R2` governance states are retired as the target model. The permanent routing rule is:

- default: no external AI review;
- ordinary code change where independent review has clear value: prefer Codex Spark when available;
- material security, authentication, permissions, deployment, recovery, workflow, branch-protection, Merge Queue, or governance/control-plane change: one Codex deep review on a stable material candidate;
- trivial docs, formatting, generated evidence, metadata, or other low-risk changes: no external AI review;
- Spark unavailability for low-risk work does not automatically escalate to deep Codex;
- re-review is justified only by a material risk-bearing change, not by cosmetic or governance-retrigger changes.

No AI-review result is part of the permanent required-status map.

The existing `ai-review-gate`, review-tier machine configuration, review fingerprints/envelopes, and related implementation may remain temporarily only as legacy transition machinery while current protected `main` still requires them. They are not target authority and must be retired by the minimal META follow-up after the replacement path is proven.

## Control-plane owner boundary

An agent or automation must not autonomously authorize a material change to the mechanism that governs its own integration. For such a change, require deterministic validation, one useful independent deep review, explicit human-owner authorization, Merge Queue validation where already canonical, and post-change GitHub readback.

This does not require a JSON authorization parser, duplicate-comment proof engine, attestation bridge, second-human approval, or separate required status.

## Precedence

This ADR and `docs/superpowers/specs/2026-09-01-solo-maintainer-governance-v2-simplification-reset-design.md` supersede conflicting lifecycle/proof, formal R0/R1/R2, `ai-review-gate`-as-target-authority, and Work-specific execution clauses in the V2 documents merged through PR #123, including:

- `docs/superpowers/specs/2026-08-31-solo-maintainer-governance-v2-design.md`;
- `docs/superpowers/specs/2026-08-31-solo-maintainer-governance-v2-safety-amendment.md`;
- `docs/superpowers/plans/2026-08-31-solo-maintainer-governance-v2.md`;
- `docs/superpowers/plans/2026-08-31-solo-maintainer-governance-v2-safety-addendum.md`;
- `docs/agents/prompts/OTERYN-SOLO-MAINTAINER-GOVERNANCE-V2-ROLLOUT.md`.

Non-conflicting safety requirements remain in force, especially one aggregate gate, fail-closed gate semantics, no moving-head/no-op governance dependency, moving-base Merge Queue proof before strict-freshness removal, no second-human dependency, no broad bypass, rollback capability, and direct GitHub readback.
