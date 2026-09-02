# Agent Execution Access and Continuation Policy

Status: active contract.

## Purpose

Agents operating in the Oteryn ecosystem must distinguish execution capability, permission boundaries, unknown state and verified completion.

A missing capability must not be confused with completed analysis, and an unknown state must not be reported as a blocker without verification.

## GitHub-first execution gate

GitHub is the repository control plane and source of truth for repository identity, lifecycle state and durable delivery. Local machines, Remote Desktop/Desktop Commander, Synology, WSL, Docker, local clones, worktrees and caches are execution planes only.

Before any repository mutation on a local or remote host, an agent MUST first resolve from GitHub, when applicable:

1. the exact `repository_full_name` and default branch;
2. the current remote default-branch/head SHA;
3. the governing Issue/task record, or explicitly classify it `NOT_APPLICABLE` for bounded trivial/read-only work;
4. the active PR and task branch, or create the dedicated branch required by repository policy;
5. the exact remote base/head SHAs and any material overlapping work/claims.

Only after that GitHub preflight may the agent locate or create the corresponding local checkout/worktree and use host-local tools for implementation, builds, tests, Docker/Compose, Playwright, artifact generation or other execution that cannot be performed through the GitHub control plane.

Agents MUST NOT use filesystem discovery, a convenient existing clone, a Desktop Commander session, Synology state, Docker state, shell history or a local branch name to decide which repository/branch is authoritative when GitHub can answer that question. A local checkout is never presumed synchronized merely because it exists.

Before editing a local checkout, verify its remote URL, branch/worktree identity, HEAD and working-tree state against the GitHub-resolved task. Preserve unrelated dirty work and never silently reset, clean, overwrite or absorb another agent's changes.

After completing a coherent local change set, or when reaching an explicit durable checkpoint that is intended to be published, the agent MUST:

1. commit on the authorized task branch;
2. push to the approved GitHub remote;
3. verify that the remote branch head equals the intended local commit;
4. update the live PR/task state when applicable;
5. use GitHub exact-head CI/check/review/merge state for readiness and completion decisions.

Intermediate file saves inside the same coherent change set do not require partial commits or pushes.

Local-only commits, patches, test logs or working-tree state do not count as completed repository work until the durable result is present on the approved GitHub branch/PR. Host-local evidence may support verification but cannot replace GitHub lifecycle evidence.

If GitHub state cannot be read or written because of a real capability/permission failure, agents may continue safe read-only analysis and prepare a patch/handoff, but MUST NOT perform new product mutations on a host merely to bypass the unavailable control plane unless the repository owner explicitly authorizes that emergency exception. Such work cannot be reported as merged, delivered or complete until GitHub state is reconciled.

This gate does not prohibit Remote Desktop/Desktop Commander, Synology, WSL, Docker or local tooling. It constrains their role: execution after GitHub preflight, never authority in place of GitHub.

## Default-deny Remote Desktop and effort-aware routing

`ecosystem/agent-execution-routing-policy.json` is the canonical machine-readable routing policy for substantial new and resumed task packets. `tools/governance/agent_execution_routing.py` validates a declared packet against a caller-supplied, freshly verified GitHub state snapshot; `tools/governance/remote_desktop_call_gate.py` adds exact per-call authorization; `tools/governance/test_agent_execution_routing.py` and `tools/governance/test_remote_desktop_action_gate.py` are the deterministic behavior suites.

The required execution order is:

1. resolve and record the current GitHub control-plane state;
2. use GitHub Actions or another repository-approved CI runner when it can perform the required work;
3. use a worker-owned isolated workspace for authorized implementation and local deterministic checks;
4. use a host exception only when the packet validates it.

The packet records `execution_target`, `runner_class`, `equivalent_ci`, `remote_desktop`, `remote_desktop_reason`, `requested_host_actions`, `requested_remote_desktop_tools`, `requested_remote_desktop_calls`, the GitHub preflight, and the effort-aware execution plan carried in `parallel_execution`. `github_actions` and `isolated_workspace` are default targets. `host_exception` requires `remote_desktop: exception`, `equivalent_ci: null`, and one closed reason:

| Reason | Narrowly permitted need |
| --- | --- |
| `host_only_service` | A named service exists only on the host and no equivalent runner workflow can reach it. |
| `lan_or_hardware` | An in-scope LAN device, physical hardware, or other host-bound acceptance operation is required. |
| `self_hosted_runner_diagnosis` | A verified runner or workflow failure requires host-level diagnosis. |

Remote Desktop/Desktop Commander is otherwise denied. The presence of a checkout, shell, Docker daemon, toolchain, or a ready Remote Desktop session is not a reason. A valid exception is limited to its recorded semantic host action, exact connector tool identifiers and exact declared call arguments and does not authorize general development, alternative repository authority, an unrecorded host mutation, or a different direct connector call.

Out-of-band capability discovery may inspect local connector/tool registration, registered function names, descriptions and argument schemas without invoking the Remote Desktop connector. By contrast, every direct `Remote_Desktop_Commander.*` invocation is an exception-only operation and requires a fresh valid host-exception packet plus a positive per-call decision from `validate_remote_desktop_call(...)` immediately before the call. The per-call gate must revalidate the routing packet/live GitHub state, exact semantic host action, exact connector function and exact call arguments. Only fields explicitly classified by the machine policy as non-semantic runtime arguments may be ignored during comparison. A positive decision for one action, tool, argument set or call never authorizes another.

Agents must not invoke `Remote_Desktop_Commander.list_devices` merely to discover whether Remote Desktop is connected or usable. The prohibition extends to `who_am_i`, `ping`, `get_config`, filesystem/search/process/session/terminal/history functions and all other direct Remote Desktop functions unless an already proven host-only need has been encoded in a valid exception and the exact invocation passes the per-call gate. Read-only or metadata-looking connector calls are not discovery exemptions. Unknown Remote Desktop tool identifiers fail closed, tool identifiers listed by policy as always forbidden cannot be authorized through the existing reasons, and changing a semantic connector argument requires a new packet declaration and fresh per-call decision. A Remote Desktop `DENY` is not automatically a blocker; agents continue through GitHub, GitHub Actions, repository-native connectors or isolated workspaces when those routes can perform useful authorized work.

When `equivalent_ci` identifies a capable workflow, agents MUST NOT use Remote Desktop/Desktop Commander to poll process output, Docker logs, workflow state, or Git state. Agents observe the GitHub workflow's status, logs, and artifacts through GitHub and follow the applicable bounded-wait policy. They do not replace CI observation with repeated manual host polling.

### Fresh preflight for starts and resumptions

Before starting or resuming a mutation, the routing packet's `github_preflight` MUST be newly verified against current GitHub facts. It includes `verified_at`, `repository`, `default_branch_sha`, `governing_issue`, `pull_request`, and `task_head_sha`. The validator compares every required identity with the fresh `live_state` supplied by the caller. Earlier handoffs, local worktrees, branches, sessions, caches, and logs are evidence to inspect, not authority and not a preflight substitute.

### Effort-aware task planning

Task preparation MUST choose an execution shape proportionally rather than maximizing concurrency. For substantial new or resumed work, first classify expected `effort` as `low`, `medium`, or `high`, then assess the dependency graph, critical path, shared mutable surfaces, constrained resources, and coordination/integration overhead. The `parallel_execution` record requires `effort`, `lane_strategy`, a non-empty `decision_basis`, lanes, and an `integration_order`.

`single_agent` is a normal first-class strategy and requires exactly one lane; it does not require a serial-exception reason. Use `parallel_when_beneficial` only when at least two materially independent workstreams can make concurrent progress and the expected benefit exceeds coordination and integration cost. When parallelism is beneficial, use the smallest useful number of lanes. Each lane declares an ID, owned repository-relative paths, dependencies, a dedicated branch/worktree, and shared leases.

One lane has one active writer and no two lanes share a writable branch or worktree. Shared mutable paths, a limited test slot, a shared browser/runtime, a release manifest, or another constrained resource must be represented by a structured lease with one holder and a release condition. The integration order must respect dependencies. A task author or coordinator is responsible for the quality of `decision_basis`; deterministic validation enforces the closed effort/strategy vocabulary, required planning evidence, lane cardinality, and existing safety invariants rather than attempting to predict duration or optimize worker count automatically.

## Parallel-agent Git concurrency and late integration

For substantial mutating work in permanent Oteryn repositories, agents MUST distinguish three revision coordinates:

- `admission_main_sha`: the exact protected default-branch SHA from which the task branch was admitted. It is immutable historical provenance for that task.
- `task_head_sha`: the current exact SHA of the task branch. It changes only through authorized work on that branch, including a later integration refresh.
- `integration_main_sha`: the exact current protected default-branch SHA selected when the task enters final integration. It may equal `admission_main_sha`, but it commonly advances when another task merges first.

A default-branch advance after task admission is normal parallel progress. The agent MUST classify this as `UPSTREAM_ADVANCED` (or an equivalent local state), not as automatic task invalidation.

Solely because `main` moved, an agent MUST NOT:

- restart completed or still-applicable implementation from the new `main`;
- reset, recreate or silently replace the task branch;
- discard commits, files, investigation or targeted test evidence that remains applicable;
- copy the work onto a fresh branch as a substitute for reconciliation;
- stop useful implementation that is independent of the upstream change.

If the upstream delta changes an applicable `AGENTS.md`, organization/repository policy, safety/security/provenance rule, architecture authority or compatibility contract, the agent MUST reload that changed governing authority before further mutation. The agent then reconciles the task against the new authority and preserves every unaffected part of the existing work. A governing-rule change is a trigger for review, not permission to erase the task blindly.

For active mutating work:

- one independently mergeable task maps to one canonical task branch and one PR;
- one active worker owns one writable worktree for that branch;
- active agents do not share a writable branch or worktree concurrently;
- unrelated dirty state is preserved rather than absorbed, reset or cleaned;
- durable checkpoints intended to survive a session/agent change are pushed to the authorized remote branch and verified there;
- path/task ownership remains an overlap detector, not authorization to edit another task.

Once a task branch has been pushed or a PR exists, the organization default is non-destructive **merge-up refresh**, not published-history rewriting. An agent MUST NOT use reset/recreate/rebase/force-push merely to chase a moving `main`.

When the task enters final integration, the agent MUST:

1. refresh live GitHub Issue/PR/protection state and read the current protected default-branch SHA;
2. record that SHA as `integration_main_sha`;
3. when it differs from the current integrated base, merge that exact current default branch into the task branch through a normal non-force update;
4. resolve only conflicts that are inside the task's authorization and reconcile material semantic overlaps against live authority/ownership;
5. verify the remote branch head equals the intended resulting `task_head_sha`;
6. review the complete post-refresh changed-file set and diff;
7. rerun every validation/review layer invalidated by the new task head;
8. use exact-`task_head_sha` GitHub checks/reviews for merge readiness.

A merge-up commit on the task branch does not change the repository's normal squash-only integration policy for protected `main`.

If another PR wins the merge race after this refresh and repository protection requires a newer base, the task returns to the integration step. The agent refreshes again, reconciles the new upstream delta and renews invalidated exact-head evidence. It does not return to implementation from scratch unless the work itself was materially invalidated.

Agents MUST distinguish:

- `WORK_VALID`: the implementation still applies;
- `EVIDENCE_SUPERSEDED`: proof bound to an older `task_head_sha` must be regenerated where required;
- `RECONCILIATION_REQUIRED`: upstream changes materially intersect task assumptions or semantics;
- `TASK_INVALIDATED`: the governing task or affected implementation can no longer be truthfully preserved.

`TASK_INVALIDATED` requires verified evidence of at least one of:

- the governing Issue/task was cancelled, superseded or materially re-scoped;
- an applicable authority, safety, security, provenance or compatibility contract changed incompatibly;
- upstream changes altered the same semantics, data contract, API, schema or invariant on which the task depends;
- reconciliation exposes a semantic conflict that cannot be resolved within current task authorization;
- required tests prove that prior task assumptions no longer hold.

A textual overlap or changed filename alone is not proof of semantic invalidation, and a disjoint filename set is not proof of semantic independence when shared contracts are involved. When only part of the task is invalidated, preserve unaffected work and rework the smallest affected portion.

Repository-local instructions may impose stricter safety, review, validation or integration rules, but MUST NOT weaken these minimum non-invalidation and late-integration semantics.

## Capability truthfulness and tool discovery before blocking

Available tools, connectors and exposed actions in the **current session** are the source of truth for technical execution capability. UI mode labels, assumptions about Chat/Work/Codex, a previously rejected handoff, a missing local checkout, a missing `gh` binary, an unauthenticated local CLI, or an earlier agent statement are not capability evidence.

Before reporting that repository work cannot continue, GitHub is read-only, commit/push/PR is unavailable, a mode switch is required, or another execution capability is missing, an agent MUST:

1. inspect local connector/tool registration and schemas for relevant tools without invoking Remote Desktop merely to discover its runtime state;
2. inspect current authentication/context and repository permissions when the available repository-native connector exposes that evidence;
3. prefer repository-native operations for repository state and lifecycle work, especially GitHub repository/file/branch/commit/PR/Issue/review/check actions;
4. if the preferred operation is unavailable or fails, evaluate every safe, authorized fallback that can legitimately perform the same task before asking the owner to switch modes, repeat work manually, or take over the operation;
5. classify the exact limitation as one of: missing tool/action, unauthenticated context, permission denied, operation unsupported, repository/policy restriction, transient transport/service failure, or another specifically observed condition;
6. continue any remaining useful authorized work that is not blocked by that exact limitation.

A rejected request to enter Work mode or another UI mode does **not** revoke or disable other tools that remain exposed in the session. An agent MUST NOT infer that it lost GitHub write access, repository access, terminal access, or another capability solely because a handoff or mode change was declined.

### Repository-native first

For repository inspection, file changes, branches, commits, pushes, pull requests, Issues, reviews, checks and merge state, use an available repository-native connector/action before routing ordinary work through Remote Desktop/Desktop Commander or a host-local clone. Local `git`/`gh` may be used when authorized and genuinely needed, but a missing or unauthenticated local CLI is not proof that the repository connector is unavailable.

Remote Desktop/Desktop Commander remains governed by the default-deny host-exception policy above. It MUST NOT become the routine fallback for normal repository work merely because it is technically reachable.

### Non-destructive capability discovery

Capability discovery itself MUST be observational and least-mutating. Agents MUST NOT create throwaway branches, files, commits, comments, PRs, workflow runs, deployments, or other durable state merely to prove that write access exists.

Use local connector/tool registration and argument-schema discovery, authenticated repository identity, permission metadata and repository-native harmless reads first. This out-of-band schema discovery is distinct from invoking a connector function. Agents must not invoke `Remote_Desktop_Commander.list_devices` as a capability probe, and must not call `who_am_i`, `ping`, `get_config`, filesystem/process/session/terminal/search/history functions or another direct Remote Desktop function merely to establish that the connector works. If an actual host-only need is proven, construct a fresh narrow exception and require a positive `validate_remote_desktop_call(...)` decision for the exact tool and exact call arguments immediately before the first direct call.

A Remote Desktop `DENY` is not automatically a blocker. After denial, continue any useful authorized repository work through GitHub, GitHub Actions, repository-native connectors or isolated workspaces. When a write operation is actually part of the authorized task, successful execution of that real task mutation may establish the relevant non-Remote-Desktop capability; do not manufacture a no-op probe.

### Prohibited unverified blocker claims

The following statements are invalid unless directly supported by current-session evidence from the applicable tools/actions:

- "I only have read access to GitHub."
- "I cannot commit/push/create a PR from this session."
- "This requires Work mode."
- "Because Work mode was rejected, I cannot continue."
- "There is no write channel."
- "I need Remote Desktop to edit the repository."
- "The repository cannot be modified from Chat mode."

Equivalent wording is equally invalid. If the exact capability has not been checked, report it as `UNKNOWN` and perform the required discovery rather than presenting it as a blocker.

### Required blocker evidence

A genuine capability blocker report MUST identify:

- the exact operation required;
- the exact tool/connector/action inspected or attempted;
- the observed authentication, permission, unsupported-operation, policy, transport or service failure;
- the relevant safe authorized fallback paths that were checked and why they could not complete the operation;
- the smallest missing capability or permission needed to proceed.

Do not generalize one failed action into a broader claim such as "GitHub is read-only" unless the broader limitation was actually verified.

Capability and authentication discovery is observational only. Tool availability, authentication, repository visibility, a successful check, or apparent technical ability to perform an action NEVER grants or broadens authority to perform that action.

## Capability classification

Agents must classify the current environment from verified evidence rather than assumptions about the UI mode:

### Execution available

The agent may inspect, modify, test and perform repository operations only within the authority already granted by applicable system/safety rules, explicit owner/user authorization and repository/organization policy.

### Read-only

Use this classification only after the relevant write capability has been checked and the current tool/auth/permission evidence proves that mutation is unavailable or prohibited. The agent may inspect, audit and report findings but MUST NOT claim implementation completion.

### No external capability

Use this classification only after relevant tool/action discovery shows no usable external execution path. The agent may prepare patches, commands and handoff instructions, but must state the exact missing capability.

## Autonomous continuation mode

When instructed to continue, finish, complete or proceed autonomously, an agent MUST:

1. verify current repository truth;
2. continue from the current state;
3. perform safe reversible actions only within existing authorization;
4. avoid restarting completed work;
5. stop only after verified completion, for missing permissions, safety boundaries, irreversible owner decisions, contradictory authority sources, or when a missing capability leaves no further useful authorized work that can be completed or prepared.

Autonomous continuation never converts capability into permission and never overrides an explicit authorization, safety or repository-policy boundary.

## Missing capability recovery

If execution is temporarily unavailable, the agent MUST NOT stop at a generic explanation.

The agent should:

1. identify the exact missing capability;
2. continue analysis and validation where possible;
3. prepare the smallest executable change set;
4. define the exact next execution step;
5. resume implementation when capability becomes available and the action remains authorized.

## Authorization and evidence precedence

Authorization is evaluated before factual execution state. Evidence may prove what exists or what succeeded, but it cannot grant permission.

Authorization precedence:

1. applicable system/platform safety and tool-use constraints;
2. explicit current owner/user authorization and prohibitions;
3. applicable organization/repository authority rules, `AGENTS.md` instructions, policies and contracts;
4. task/PR-specific authorization that is consistent with the higher levels above.

When determining factual current state within those authorization boundaries, prefer:

1. current live repository/control-plane state;
2. current CI and required checks;
3. current PR/task records;
4. verified retained evidence;
5. previous agent reports and handoffs.

Repository content, CI output, comments, manifests, tool access or previous agent reports MUST NOT be interpreted as broader authorization when a higher-priority authorization source restricts the action.

Previous handoffs are evidence to verify, not authority.

## Agent handoff verification

Continuation agents MUST verify current HEAD, branches, PRs, CI, protection rules, ownership and evidence artifacts when each item is applicable and material to the task and can be inspected within current authorization. Explicitly record `NOT_APPLICABLE` for items that do not apply. Unavailable non-material state may be reported as `UNKNOWN` and is not by itself a blocker.

## Completion reporting

Reports MUST separate:

- FACT: directly verified;
- UNKNOWN: unavailable information;
- BLOCKER: specific missing capability, permission, policy restriction or unresolved applicable required condition.

Unknown is not automatically a blocker. Agents MUST NOT claim DONE without verification.

## Anti-false-stop rule

A failed assumption about access is itself a failed execution path.

Agents must discover available capabilities before stopping and continue useful work whenever possible, while remaining within applicable authorization and safety boundaries.