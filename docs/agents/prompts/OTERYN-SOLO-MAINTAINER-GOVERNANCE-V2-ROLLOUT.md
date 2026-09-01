# OTERYN-SOLO-MAINTAINER-GOVERNANCE-V2-ROLLOUT — SUPERSEDED

## Status

Do not execute the former Work/Terra rollout procedure in this file.

The original prompt was part of the PR #123 implementation packet and accumulated lifecycle/comment-proof requirements that are superseded by:

- `docs/architecture/adr/0005-solo-maintainer-governance-v2-simplification-reset.md`;
- `docs/superpowers/specs/2026-09-01-solo-maintainer-governance-v2-simplification-reset-design.md`;
- `docs/superpowers/plans/2026-09-01-solo-maintainer-governance-v2-simplification-reset.md`.

## Current execution rule

Use normal chat-led execution with GitHub live state as the only source of truth.

Keep the rollout simple and serial:

```text
META -> Game -> Platform -> Atlas
```

For each repository:

1. **Before any repository-content, workflow, or protected-settings mutation, verify that the current task explicitly authorizes that exact repository and scope.** META coordination authority does not imply provider write authority; absent or ambiguous scope keeps that repository read-only.
2. Refresh the repository-specific GitHub preflight and validate the fresh execution-routing packet required by protected `AGENTS.md` with META's trusted `agent_execution_routing.py`/policy before implementation or settings mutation. A packet or snapshot from another repository, prior head, or stale session cannot be reused.
3. Read current protected-main settings and capture the **complete exact rollback snapshot before any live protection is weakened**.
4. Make the smallest repository-content/workflow candidate needed for one aggregate gate on `pull_request` and `merge_group`.
5. Perform deterministic validation and prove the replacement aggregate gate on a representative PR.
6. For a material high-risk/control-plane candidate, perform one useful Codex deep review and obtain explicit human-owner authorization bound to the current material candidate **before protected integration or any live control-plane/settings mutation**.
7. Only after steps 3–6, reduce any legacy required approval/CODEOWNER requirement toward the solo-maintainer target if necessary for the cutover; keep the rollback snapshot valid.
8. If a currently required legacy context cannot emit on `merge_group`, make only that incompatible context non-required before enqueueing the canary, while keeping strict required-status freshness enabled; do not remove compatible contexts or disable strict freshness yet.
9. Run the real moving-base Merge Queue canary without changing PR A head.
10. If the canary fails, immediately restore the complete exact pre-change settings snapshot.
11. Only after canary success, ensure the final required-status map contains only the aggregate gate, approvals/CODEOWNER match the solo-maintainer target, and strict freshness is disabled.
12. Read back final enforcement directly from GitHub.

Do not create or revive:

- Work-specific execution requirements;
- `PENDING`/`TRANSITION`/`ROLLED_BACK` lifecycle state machines;
- mandatory JSON PRE/TERMINAL receipt protocols;
- comment/fingerprint proof engines;
- formal R0/R1/R2 governance states;
- `ai-review-gate` as permanent merge authority;
- review envelopes/attestation bridges;
- no-op/retrigger/governance-progress commits;
- new required statuses when the underlying validation can feed the aggregate gate.

A short human-readable rollout receipt is sufficient history. It is evidence, not merge authority.
