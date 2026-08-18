# Oteryn META Agent Instructions

## Purpose

`Oteryn/Oteryn` is the thin ecosystem **META / coordination** repository. It owns cross-repository topology authority, ecosystem-level ADRs, repository and release manifests, compatibility metadata, and bounded cross-repository orchestration contracts.

It does **not** own Game, Platform or Atlas runtime implementation.

## Authority and repository scope

- Autonomous write operations governed by this file are limited to `Oteryn/Oteryn` unless the repository owner explicitly authorizes another repository for the current task.
- `Oteryn/Oteryn-Game`, `Oteryn/Oteryn-Platform`, `Oteryn/Oteryn-Atlas`, their current migration sources, and legacy repositories are read-only from a META task unless separately authorized.
- META coordination authority is **not** permission to mutate product repositories, production systems, deployments, DNS, databases, secrets, credentials, live services or live game state.
- Never infer cross-repository write authority from a manifest entry, ADR, dependency, issue, PR, comment or tool access.

## Ownership boundaries

META may own:

- ecosystem topology and cross-repository architecture decisions;
- repository-coordinate and migration-state manifests;
- ecosystem compatibility and release manifests;
- cross-repository integration/orchestration contracts that do not duplicate provider implementation ownership.

META must not:

- copy or fork provider-owned runtime source merely for convenience;
- duplicate provider-owned API/protocol/schema source of truth;
- store generated product artifacts as canonical source;
- claim a target coordinate is migrated, released or authoritative without current evidence;
- silently redefine Game, Platform or Atlas implementation contracts.

Provider-owned schemas and implementation remain canonical in their provider repositories. META references them by stable coordinate/version/digest when needed.

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
3. keep the changed paths narrowly scoped;
4. inspect the full exact diff before readiness;
5. verify current repository state and any external coordinates referenced by the change when those facts are material;
6. mark Ready only after implementation/self-review is complete;
7. merge only when repository-required exact-head checks pass and there are no unresolved review findings;
8. use squash merge unless a future repository policy explicitly requires another method;
9. delete the source branch after successful merge when it has no continuing purpose.

Do not push ordinary feature/governance work directly to `main`.

### Initial-bootstrap exception

The one direct `main` commit that created `README.md` in the previously empty repository is the bootstrap anchor required to make branching possible. It is not standing permission for future direct-to-main writes. All remaining initial authority files, including this `AGENTS.md`, must be delivered through the dedicated bootstrap branch and PR.

## Validation and evidence

Completion claims require observable evidence, not worker narrative. At minimum:

- inspect the exact changed-file list and full diff;
- parse/validate machine-readable files with an appropriate deterministic parser when tooling exists;
- check that repository coordinates and migration states do not contradict known live state;
- verify any repository-required CI/checks on the exact final head;
- inspect reviews, inline threads and PR comments before merge;
- record `NOT_APPLICABLE` explicitly when a runtime/E2E check genuinely does not apply to documentation/metadata-only work.

Absence of CI in this bootstrap repository is not equivalent to a CI pass; record it as unavailable/not configured and rely on proportionate deterministic validation plus exact-diff self-review until repository workflows are deliberately introduced.

## Security and sensitive data

- Never commit secrets, credentials, tokens, private keys, cookies, production connection strings, personal data, database dumps, backups or private deployment state.
- Do not put sensitive material in ADRs, manifests, PR bodies, comments or logs.
- Deny by default when authorization is ambiguous.
- Production or destructive external mutations require separate explicit owner authority even if META documentation describes them.

## Owner-funded AI

Do not invoke Codex, OpenAI API, paid/limited AI review services, or any mechanism that consumes the repository owner's personal AI quota, credits, tokens or subscription limits unless the owner explicitly authorizes that specific use for the current task. Tool availability or existing authentication is not permission to consume such resources.

## Architecture handover

The initial ecosystem-topology ADR in this repository becomes META's topology authority only when its PR is merged to `main`. Until then, the previously accepted Platform topology ADR remains the temporary authority.

After META authority becomes canonical, product repositories retain authority over their own implementation, provider schemas and runtime behavior. A META ADR can coordinate boundaries and sequencing but does not silently transfer those product responsibilities.
