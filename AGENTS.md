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
- Protected-integration scheduling: before releasing a mutating worker expected to
  require autonomous protected integration, apply
  `docs/agents/contracts/INTEGRATION_CAPABILITY_ROUTING_POLICY.md` through
  `tools/governance/integration_capability_routing.py` using fresh typed
  current-session capability evidence; an installed trusted observer remains an
  optional compatibility adapter, not a required wrapper. Never use caller-created
  dictionaries or JSON as authority. Only `DIRECT_CAPABLE` or verified
  `DELEGATED_CAPABLE` permits that worker release; capability is not merge authority.
  Without valid fresh typed evidence, fail closed.
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

## Specialist operation routes

Before using CLI/Git credential compatibility for an authorized publication, read
`docs/agents/operations/RESTRICTED_PUBLISHING.md`. Credentials do not expand
authority. Never embed a token in a remote URL or persist a new credential
helper to bypass that boundary.

Before selecting or changing an Actions runner, migrating a legacy runner workload,
or considering a host-local META workload, read
`docs/agents/operations/RUNNER_ROUTING.md`. META remains GitHub-hosted unless a
separate host-local workload is explicitly proven and authorized.

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

## Jira programme coordination

Oteryn programme coordination is mirrored in Jira project `KAN` at `https://oteryn.atlassian.net`; `KAN-23` is the programme overview. When an Atlassian/Jira connector is available in the current session, use it as a bounded programme-coordination surface.

- After the normal GitHub preflight for a substantial start or resume, resolve an **existing mapped Jira Story** for the current workstream. Prefer a native GitHub source link on the Jira item; otherwise require an exact repository/workstream label match. Do not map work by a similar title alone.
- Read only the mapped Story, its parent Epic, priority, status, fixVersion/milestone and readiness labels needed for the current decision. Do not bulk-load unrelated Jira history.
- **GitHub remains repository lifecycle and technical source of truth** for repository identity, Issues/tasks, branches, PRs, exact SHAs, checks, review, Merge Queue and integration. Repository contracts/task records remain implementation authority. Jira is the programme roadmap/readiness/milestone view and never grants repository, merge, production, secret or cross-repository mutation authority.
- Ordinary repository workers may update only their already-mapped programme Story after a verified material state transition. Broad Jira restructuring, new programme Epics/Versions, cross-workstream reprioritization and edits to `KAN-23` belong to the programme coordinator unless the owner explicitly delegates them.
- Use the established programme state convention: queued/blocked/stalled work stays `Do zrobienia` with the matching `readiness-queued`, `readiness-blocked` or `readiness-stalled` label; active work is `W toku` with `readiness-active`; completed work is `Gotowe` with `readiness-complete` only after the Story's full acceptance is verified. Use `W trakcie weryfikacji` when implementation is complete but required review/qualification is still pending.
- Fresh-read both Jira and the linked GitHub state before a Jira mutation. Do not spam comments or rewrite unchanged fields. A closed individual GitHub Issue/PR does not make an aggregate Jira Story complete while another linked acceptance source remains open.
- If the Jira connector is unavailable, the mapping is absent, or Jira write capability is unavailable, continue otherwise-authorized repository work. Record Jira synchronization as pending/unknown rather than inventing a mapping, creating duplicate programme items, or treating Jira availability as an implementation blocker.
