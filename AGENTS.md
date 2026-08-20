# Oteryn META Agent Instructions

## Purpose

`Oteryn/Oteryn` is the thin ecosystem **META / coordination** repository. It owns cross-repository topology authority, ecosystem-level ADRs, repository and release manifests, compatibility metadata, and bounded cross-repository orchestration contracts.

It does **not** own Game, Platform or Atlas runtime implementation.

## Agent execution discipline

Agents MUST follow `docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md`.

Before declaring a task blocked because of access limitations, agents must discover available capabilities and distinguish:

- unavailable tool;
- unavailable permission;
- unknown state;
- repository policy restriction.

Missing execution capability does not terminate the task. Agents should continue useful analysis, validation and preparation until execution is possible.

Completion claims require verified evidence.

## Authority and repository scope

- Autonomous write operations governed by this file are limited to `Oteryn/Oteryn` unless the repository owner explicitly authorizes another repository for the current task.
- `Oteryn/Oteryn-Game`, `Oteryn/Oteryn-Platform`, `Oteryn/Oteryn-Atlas`, their current migration sources, and legacy repositories are read-only from a META task unless separately authorized.
- META coordination authority is **not** permission to mutate product repositories, production systems, deployments, DNS, databases, secrets, credentials, live services or live game state.

Provider-owned schemas and implementation remain canonical in their provider repositories.

## Truthful transition state

During repository migration, records must distinguish at least:

- `target_coordinate`;
- `current_coordinate`;
- `migration_state`;
- authority owner or provider;
- evidence needed before a pending state can advance.

Use explicit pending/unknown states rather than pretending future topology already exists. Live repository state outranks stale documentation.

## Work visibility

For substantial work:

1. use a dedicated task branch;
2. open a Draft PR early when practical;
3. keep changed paths narrowly scoped;
4. inspect the exact diff before readiness;
5. verify repository state and external coordinates when material;
6. mark Ready only after implementation/self-review;
7. merge only when required exact-head checks pass and review findings are resolved.

## Validation and evidence

Completion claims require observable evidence, not worker narrative.

At minimum:

- inspect exact changed files and full diff;
- validate machine-readable files deterministically;
- verify repository coordinates and migration states;
- verify required CI/checks on exact final head;
- inspect reviews, threads and PR comments before merge.

## Security and sensitive data

- Never commit secrets, credentials, tokens, private keys, cookies, production connection strings or private data.
- Deny by default when authorization is ambiguous.
- Production or destructive mutations require explicit owner authority.

## Owner-funded AI and review economy

External AI review is governed by `docs/governance/AI_REVIEW_POLICY.md` and `ecosystem/ai-review-policy.json`. Do not spend Codex/Spark quota on every PR. Classify the final diff deterministically first.

- `R0` requires deterministic validation and exact-diff self-review only.
- `R1` uses one fast reviewer invocation per stable fingerprint.
- `R2` uses one deep reviewer invocation per stable fingerprint.
- Never repeatedly invoke external review for unchanged fingerprints.

## Architecture handover

The initial ecosystem-topology ADR becomes META topology authority only when merged to `main`.
