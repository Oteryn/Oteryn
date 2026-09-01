# Oteryn META Agent Instructions

## Purpose

`Oteryn/Oteryn` is the thin ecosystem **META / coordination** repository. It owns cross-repository topology authority, ecosystem-level ADRs, repository and release manifests, compatibility metadata, and bounded cross-repository orchestration contracts.

It does **not** own Game, Platform or Atlas runtime implementation.

## Agent execution discipline

Agents MUST follow `docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md`.

Agents MAY use the `synology oteryn` developer MCP when it is available and the current task authorizes the relevant operation. They MUST follow `docs/agents/contracts/SYNOLOGY_MCP_EXECUTION_POLICY.md`: Synology MCP is an additional runtime/local evidence and execution path, not a replacement for GitHub. GitHub live state remains authoritative for repository, branch, commit, PR, issue, review, CI/check and release facts, and required GitHub verification/workflows MUST NOT be skipped because MCP access exists.

Before declaring a task blocked because of access limitations, agents must discover available capabilities, distinguish tool absence from permission/policy restrictions, and continue useful work when any safe execution path remains.

Completion claims require verified evidence. `UNKNOWN` is not automatically a `BLOCKER`, and a generic access disclaimer without capability discovery is invalid.

## External execution-skill precedence

Repository and user authority govern execution. Agent skills, plugins and workflow frameworks such as Superpowers are subordinate execution aids, not independent task or lifecycle authority.

For an already-authorized Oteryn programme or task with an approved canonical design, implementation plan, checkpoint, or explicit continuation directive, Superpowers workflows MUST NOT introduce additional approval gates, re-brainstorm an approved design, require duplicate planning artifacts, replace canonical authority, or interrupt autonomous continuation solely because the skill's default workflow would do so. Relevant skills MAY still be used internally for implementation, testing, debugging, review, isolation, or verification when they do not conflict with the governing Oteryn authority.

A skill or plugin MUST NOT weaken repository safety, validation, review, GitHub-first, or authorization requirements. When a skill workflow conflicts with applicable user instructions, this `AGENTS.md`, repository policy, or canonical task authority, the applicable higher-priority Oteryn authority controls.

## GitHub-first execution gate

GitHub is the authoritative repository control plane for repo identity, default branch, Issue/task, PR, task branch, exact remote SHA, checks, reviews and merge state.

Agents MUST complete the GitHub preflight defined in `docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md` before mutating any local/remote checkout or starting host-local implementation/execution that can change repository or external state. If GitHub preflight is genuinely unavailable, host-local tools may still be used for the safe read-only analysis and patch/handoff preparation permitted by the central contract, but not to mutate or bypass GitHub lifecycle authority.

Host-local filesystems, clones, worktrees, containers and shells are execution/cache planes only. They MUST NOT be used to select authoritative repository state or bypass GitHub lifecycle. Durable local changes receive no completion credit until committed, pushed to the approved GitHub branch/PR and verified against the remote exact head.

## Execution-routing policy

`ecosystem/agent-execution-routing-policy.json` is the canonical machine-readable policy for substantial new or resumed task packets. Validate a packet against a freshly obtained GitHub snapshot with:

```text
python3 tools/governance/agent_execution_routing.py --policy ecosystem/agent-execution-routing-policy.json --packet <packet.json> --live-state <fresh-github-state.json>
```

Use this execution order: current GitHub state; GitHub Actions or another repository-approved CI runner; a worker-owned isolated workspace; then, only when validated, a narrowly authorized host exception. Remote Desktop/Desktop Commander is **default-deny**. It may be used only when the packet sets `remote_desktop: exception`, `execution_target: host_exception`, no equivalent CI exists, and `remote_desktop_reason` is exactly one of `host_only_service`, `lan_or_hardware`, or `self_hosted_runner_diagnosis`.

Capability discovery may inspect local connector/tool registration and argument schemas without invoking Remote Desktop. By contrast, every direct `Remote_Desktop_Commander.*` invocation requires a fresh valid host-exception packet and a positive per-action decision from `validate_remote_desktop_action(...)` for both the exact semantic host action and exact connector tool identifier immediately before that call. The packet must declare that connector function in `requested_remote_desktop_tools`; a prior positive decision for a different action or tool does not carry forward.

Agents must not invoke `Remote_Desktop_Commander.list_devices` merely to prove that Remote Desktop is reachable. The same rule applies to `who_am_i`, `ping`, `get_config`, filesystem/search/process/session/terminal/history functions and any other direct connector call: metadata-looking or read-only calls are still exception-only. Unknown connector functions fail closed, and functions classified by policy as always forbidden cannot be admitted through the three existing reasons. A Remote Desktop `DENY` is not automatically a blocker; continue through GitHub, GitHub Actions or an isolated workspace whenever those routes can perform useful authorized work.

The exception authorizes the minimum recorded host action and exact requested connector tools, not a replacement source of truth. A convenient local checkout, shell, Docker daemon, toolchain, or available Remote Desktop session is never an exception reason. When an equivalent CI workflow exists, agents MUST NOT use Remote Desktop/Desktop Commander to poll process output, Docker logs, workflow state, or Git state; inspect the equivalent GitHub workflow, its logs, status, and artifacts instead.

Before resuming work, obtain and record a new GitHub preflight with the repository, current default-branch SHA, governing Issue, PR, task-head SHA, and verification timestamp. A prior handoff, local branch, worktree, session, cache, or log is evidence only and cannot satisfy that preflight.

Project task preparation is **effort-aware and proportional**. Before choosing an execution shape for substantial work, classify expected effort as `low`, `medium`, or `high` and assess the dependency graph, critical path, shared mutable surfaces, constrained resources, and coordination/integration overhead. `single_agent` is a normal first-class strategy and requires no serial exception. Use `parallel_when_beneficial` only when at least two materially independent workstreams can make concurrent progress and the expected benefit exceeds coordination and integration cost; use the smallest useful lane count rather than maximizing concurrency. Record a short `decision_basis` for the chosen shape. Parallel lanes retain an ID, owned paths, one isolated branch/worktree, dependencies, shared-resource leases, and an integration order; lanes MUST NOT share writable branches or worktrees, and shared mutable or constrained resources require an explicit lease with one holder and a release condition.

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

## Owner-funded AI and review economy

External AI review is governed by `docs/governance/AI_REVIEW_POLICY.md` and `ecosystem/ai-review-policy.json`. Do not spend Codex/Spark quota on every PR. Classify the final diff deterministically first.

- `R0` requires deterministic validation and exact-diff self-review only; do not invoke external AI review.
- `R1` uses one fast reviewer invocation per stable review fingerprint after required CI is green.
- `R2` uses one deep reviewer invocation per stable review fingerprint after required CI is green.
- Never invoke an external reviewer for Draft/WIP state or repeatedly poll/re-run a reviewer for an unchanged fingerprint.
- A prior review may be reused only under the policy's exact fingerprint/ancestor/review-neutral rules.
- Issue #12 and its bootstrap PR are the one-time no-external-review bootstrap for this policy. After bootstrap, changes to the review policy/classifier/authority mapping are `R2`.

The repository owner has standing authorization for external AI consumption only when the merged risk policy requires `R1` or `R2` review and its invocation budget is respected. Other owner-funded AI/API use still requires explicit authorization for that task.

## Architecture handover

The initial ecosystem-topology ADR in this repository becomes META's topology authority only when its PR is merged to `main`. Until then, the previously accepted Platform topology ADR remains the temporary authority.

After META authority becomes canonical, product repositories retain authority over their own implementation, provider schemas and runtime behavior. A META ADR can coordinate boundaries and sequencing but does not silently transfer those product responsibilities.
