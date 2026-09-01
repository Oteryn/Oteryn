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

1. verify current protected-main settings and exact candidate state from GitHub;
2. make the smallest repository change needed for one aggregate gate on `pull_request` and `merge_group`;
3. keep zero required human/CODEOWNER approvals in solo-maintainer mode;
4. perform deterministic validation;
5. for a material high-risk/control-plane candidate, use one useful Codex deep review and explicit human-owner authorization;
6. capture rollback state;
7. run the real moving-base Merge Queue canary without changing PR A head;
8. only after success, make the single aggregate gate the required external status and disable strict freshness;
9. read back final enforcement directly from GitHub; rollback on failure.

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
