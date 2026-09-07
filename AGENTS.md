# Oteryn META Agent Instructions

## Purpose

`Oteryn/Oteryn` is the thin ecosystem **META / coordination** repository. It owns cross-repository topology authority, ecosystem-level ADRs, repository and release manifests, compatibility metadata, and bounded cross-repository orchestration contracts.

It does **not** own Game, Platform or Atlas runtime implementation.

## Agent execution discipline

Use `docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md` for
GitHub preflight, authorized execution, Remote Desktop exact-call gating, isolation,
proportionate lane planning, late integration and truthful completion.
`docs/agents/contracts/BOUNDED_AUTONOMOUS_EXECUTION_POLICY.md` owns bounded retries,
freeze and no-progress decisions; productive work has no generic elapsed-time stop.
For work crossing session/context/wait boundaries, additionally load
`docs/agents/contracts/PERSISTENT_AUTONOMOUS_CONTINUATION_POLICY.md` and
`ecosystem/agent-continuation-policy.json`. Never invent automatic continuation.

Only when a current task needs and authorizes Synology access, load
`docs/agents/contracts/SYNOLOGY_MCP_EXECUTION_POLICY.md`. GitHub remains repository
and required-check authority; tools do not grant permission.

## Skills and historical material

Skills and plugins are optional execution aids, subordinate to current user and
repository authority. They must not add approval lifecycles, duplicate planning,
expand scope or interrupt useful authorized work. Files marked historical/retired,
old task prompts and retained `docs/superpowers/` plans are evidence, not dispatchable
execution authority. A historical invocation's permission grant is not reusable.

## GitHub-first execution gate

Complete the canonical contract's GitHub preflight before mutation and verify the
remote exact head after publication. Local clones/worktrees/caches are execution
planes, not repository authority. Local-only patches and tests are not delivered work.

## Restricted publishing-credential compatibility

This profile applies only after the repository lifecycle has allocated an approved
task branch and existing PR. It does not grant PR-write permission to a restricted
publishing credential; PR creation remains a separately authorized control-plane action.

For an authorized write to that branch/PR, when `GH_TOKEN` and `GITHUB_TOKEN` are
unset but agent-visible `GH` is present, it may be passed transiently as
`GH_TOKEN="$GH"` to the exact authorized `gh` command. Environment mapping alone
does not authenticate `git push`: verify that the existing remote/credential path
can consume the authorized identity without exposing or persisting it. Otherwise
use another authorized repository-native write path or report the exact limitation.
Never embed the token in a remote URL or persist a new credential helper to bypass
that boundary. Credential presence expands no repository/path/task/merge/production
permission. Do not force-push; verify the remote exact head after publishing.

## Execution-routing policy

For substantial new/resumed task packets, use
`ecosystem/agent-execution-routing-policy.json` through
`tools/governance/agent_execution_routing.py`. The canonical access contract defines
its arguments and execution order. Remote Desktop is default-deny, including
metadata-looking direct calls; only a fresh positive exact-call authorization admits
an actual host exception. Discover registration/schema metadata without invoking it.

## Organization runner routing

Product-owned host-local GitHub Actions workloads MUST use the product-isolated organization runner group and product label together:

- Platform: `platform-runners` + `oteryn-platform`;
- Atlas: `atlas-runners` + `oteryn-atlas`;
- Game: `game-runners` + `oteryn-game`.

Agents MUST NOT route new workloads by a custom label alone, MUST NOT add generic `self-hosted` eligibility, and MUST NOT introduce new workflow dependencies on the legacy `oteryn-staging` selector. `oteryn-synology-staging` is rollback-only while the organization-runner migration remains open and may be retired only after the provider closeout gates prove that it has no retained workload owner. META remains GitHub-hosted unless a separate host-local META workload is explicitly proven and authorized.

When migrating an existing `oteryn-staging` workflow, replace it with the owning product's group+label selector; do not preserve the legacy selector as a fallback in new code.

The detailed operational contract and live rollout evidence are provider-owned in `Oteryn/Oteryn-Platform/docs/operations/SYNOLOGY_ORGANIZATION_RUNNERS.md`; live GitHub organization state and provider workflow state outrank stale documentation.

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
7. merge only when repository-required exact-head checks pass and there are no unresolved review findings; a P2 may be non-blocking only after its exact review thread is resolved and a trusted maintainer has recorded the required same-repository follow-up Issue;
8. use squash merge unless a future repository policy explicitly requires another method;
9. delete the source branch after successful merge when it has no continuing purpose.

Do not push ordinary feature/governance work directly to `main`.

### Initial-bootstrap exception

The one direct `main` commit that created `README.md` in the previously empty repository is the bootstrap anchor required to make branching possible. It is not standing permission for future direct-to-main writes. The bootstrap is historical evidence only; normal current task branches and PRs govern all subsequent changes.

## Validation and evidence

Completion claims require observable evidence, not worker narrative. At minimum:

- inspect the exact changed-file list and full diff;
- parse/validate machine-readable files with an appropriate deterministic parser when tooling exists;
- check that repository coordinates and migration states do not contradict known live state;
- verify any repository-required CI/checks on the exact final head;
- inspect reviews, inline threads and PR comments before merge;
- record `NOT_APPLICABLE` explicitly when a runtime/E2E check genuinely does not apply to documentation/metadata-only work.

Missing or inaccessible CI is not a pass. `meta-gate` and GitHub Merge Queue remain the current required verification/integration path; local checks do not substitute for their exact-head evidence.

## Security and sensitive data

- Never commit secrets, credentials, tokens, private keys, cookies, production connection strings, personal data, database dumps, backups or private deployment state.
- Do not put sensitive material in ADRs, manifests, PR bodies, comments or logs.
- Deny by default when authorization is ambiguous.
- Production or destructive external mutations require separate explicit owner authority even if META documentation describes them.

## AI review economy

Use `docs/governance/AI_REVIEW_POLICY.md` for risk-proportionate independent review.
External AI is advisory, never a required status or merge authority. Do not restore
retired review fingerprints, formal R0/R1/R2 states, envelopes or attestation bridges.

## Architecture handover

Accepted `docs/architecture/adr/0001-ecosystem-topology-authority.md` records META topology authority. Historical bootstrap/handover conditions are not a pending transition on current `main`.

Product repositories retain authority over their own implementation, provider schemas and runtime behavior. A META ADR can coordinate boundaries and sequencing but does not silently transfer those product responsibilities.
