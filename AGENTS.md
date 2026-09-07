# Oteryn META Agent Instructions

## Purpose

`Oteryn/Oteryn` is the thin ecosystem **META / coordination** repository. It owns cross-repository topology authority, ecosystem-level ADRs, repository and release manifests, compatibility metadata, and bounded cross-repository orchestration contracts.

It does **not** own Game, Platform or Atlas runtime implementation.

## Policy and task routing

Follow `docs/agents/policy/ORGANIZATION_AGENT_POLICY.md` for shared execution
semantics. This repository owns that policy; the rules below retain META-specific
scope and the local bootstrap needed to deliver it.

Load the relevant procedure when performing its operation:

- Repository work: `docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md`
  owns GitHub preflight, isolation, execution routing and publication readback.
  GitHub is lifecycle authority; local clones are execution planes only.
- Substantial starts/resumptions: validate the routing packet through
  `tools/governance/agent_execution_routing.py` with
  `ecosystem/agent-execution-routing-policy.json` and freshly verified GitHub facts.
- Retry/freeze decisions: `docs/agents/contracts/BOUNDED_AUTONOMOUS_EXECUTION_POLICY.md`.
  Productive work has no generic elapsed-time stop.
- Session/context/wait transitions:
  `docs/agents/contracts/PERSISTENT_AUTONOMOUS_CONTINUATION_POLICY.md` and
  `ecosystem/agent-continuation-policy.json`. Do not invent automatic continuation.
- Review/integration: `docs/governance/AI_REVIEW_POLICY.md` and ADR 0005. Protected
  `meta-gate` and GitHub Merge Queue remain required; local checks are not substitutes.
- Prompt authoring/evaluation: `docs/agents/policy/PROMPTING_STANDARD.md` and
  `docs/agents/policy/PROMPT_EVAL_STANDARD.md`, respectively.
- Authorized Synology work only: `docs/agents/contracts/SYNOLOGY_MCP_EXECUTION_POLICY.md`.

Remote Desktop is default-deny, including metadata-looking direct calls; an actual
host exception requires the canonical contract's fresh positive exact-call gate.
Skills are optional aids, not additional authority or approval lifecycles. Retired
prompts and `docs/superpowers/` material are evidence, not dispatchable instructions.

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

## Delivery and acceptance

Use a dedicated task branch and an early Draft PR for substantial work. Inspect the
complete changed-file list and diff, validate affected machine-readable contracts,
and verify material repository coordinates and transition claims. Mark Ready only
when implementation/self-review is complete. Follow the routed review policy and
normal exact-candidate Merge Queue path; no ordinary direct-to-main writes, bypass,
force push or missing-check PASS. The initial repository bootstrap is historical,
not a standing exception.

Squash integration remains the default. Resolve every blocking review finding;
a non-blocking P2 requires its resolved exact thread and a trusted maintainer's
same-repository follow-up Issue. Verify protected-main readback and delete a terminal
source branch when it has no continuing purpose. Report runtime/E2E `NOT_APPLICABLE`
when warranted by documentation/metadata scope, never as a substitute for required CI.

## Security and sensitive data

- Never commit secrets, credentials, tokens, private keys, cookies, production connection strings, personal data, database dumps, backups or private deployment state.
- Do not put sensitive material in ADRs, manifests, PR bodies, comments or logs.
- Deny by default when authorization is ambiguous.
- Production or destructive external mutations require separate explicit owner authority even if META documentation describes them.

## Architecture handover

Accepted `docs/architecture/adr/0001-ecosystem-topology-authority.md` records META topology authority. Historical bootstrap/handover conditions are not a pending transition on current `main`.

Product repositories retain authority over their own implementation, provider schemas and runtime behavior. A META ADR can coordinate boundaries and sequencing but does not silently transfer those product responsibilities.
