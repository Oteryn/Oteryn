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

## Bounded autonomous execution and no-progress control

Autonomous execution MUST distinguish productive work from passive external waiting and repeated no-progress cycles. Substantial tasks use these normalized lifecycle states when applicable:

- `RUNNING`: an active worker is making material progress;
- `READY`: the coherent implementation may enter final qualification;
- `WAITING_EXTERNAL`: no active worker should remain attached because CI, authenticated review evidence, another dependency, quota or another external event must change before useful execution can continue;
- `BLOCKED`: progress requires a missing permission, owner decision, safety authorization or contradictory authority resolution;
- `STALLED`: the same material state exceeded its bounded retry budget without new evidence;
- `DONE`: terminal completion is verified.

`WAITING_EXTERNAL` is a valid autonomous outcome and is not a false stop. When no authorized repository mutation can improve the current state, the worker MUST persist the waiting reason and next event, release ownership/lease where the repository uses one, and must end the active session rather than poll, narrate, or mutate merely to provoke another check.

### Candidate freeze

Before expensive final qualification, an agent SHOULD record `candidate_frozen: true` and the exact `candidate_head_sha`. While `candidate_frozen` is true, the branch MUST NOT be changed solely to retrigger CI, external review, status calculation, polling or checkpoint publication. A candidate may change only for a material reason such as a verified finding, semantic conflict, required integration refresh, changed authority, or an implementation/test repair. The resulting new head starts a new qualification generation.

### Material progress and failure identity

For repeated execution cycles, agents and repository tooling SHOULD compute or record a stable `progress_fingerprint` from material state: repository/PR identity, `task_head_sha`, `integration_main_sha` when applicable, current action, required/failing gate, waiting reason, first material error/finding and dependency state. Incidental values such as timestamps, run IDs, comment IDs, narration and log ordering MUST NOT manufacture progress.

A `failure_fingerprint` identifies the current failed action using the same stable material coordinates. If the same `progress_fingerprint` and action recur without material repository/evidence change, retries are bounded. The organization default is:

- external evidence absent for a frozen candidate: zero mutating retries; transition to `WAITING_EXTERNAL` after a valid request is dispatched;
- dependency not ready: zero active-worker retries; transition to `WAITING_EXTERNAL`;
- identical CI/test failure: one retry only after focused diagnosis; a further identical cycle becomes `STALLED` unless new evidence changes the fingerprint;
- transient transport/API failure: at most two attempts total before durable waiting/blocker classification;
- integration refresh: at most one refresh per distinct `integration_main_sha`.

Repository-local rules may be stricter but MUST NOT authorize unbounded retries.

### No-op/retrigger mutation prohibition

A no-op/retrigger commit is forbidden. Agents MUST NOT create an empty commit, semantic no-op edit, checkpoint-only churn, or unrelated documentation mutation whose only purpose is to change Git identity so CI, review, mergeability or another external system runs again. Qualification must be re-evaluated on the same exact head when the external evidence system supports it. If same-head re-evaluation is unavailable, classify the precise limitation as `WAITING_EXTERNAL` or `BLOCKED`; do not manufacture a new candidate.

Durable execution/checkpoint state SHOULD live outside the qualified candidate diff when the repository provides a task record/control-room mechanism. Updating agent bookkeeping does not justify invalidating otherwise-current exact-head evidence.

## Access discovery before blocking

Before reporting:

- "I don't have access";
- "I cannot inspect the repository";
- "execution is blocked";

an agent MUST:

1. inspect available tools and execution capabilities;
2. check available authentication/context;
3. determine whether the limitation is:
   - missing tool;
   - missing permission;
   - temporary failure;
   - repository policy restriction.

A generic access disclaimer without capability discovery is invalid.

Capability and authentication discovery is observational only. Tool availability, authentication, repository visibility, a successful check, or apparent technical ability to perform an action NEVER grants or broadens authority to perform that action.

## Capability classification

Agents must classify the current environment:

### Execution available

The agent may inspect, modify, test and perform repository operations only within the authority already granted by applicable system/safety rules, explicit owner/user authorization and repository/organization policy.

### Read-only

The agent may inspect, audit and report findings but MUST NOT claim implementation completion.

### No external capability

The agent may prepare patches, commands and handoff instructions, but must state the exact missing capability.

## Autonomous continuation mode

When instructed to continue, finish, complete or proceed autonomously, an agent MUST:

1. verify current repository truth;
2. continue from the current state;
3. perform safe reversible actions only within existing authorization;
4. avoid restarting completed work;
5. transition to `WAITING_EXTERNAL` and end the active session when an external event is the only thing that can change the material state; otherwise stop only after verified completion, for missing permissions, safety boundaries, irreversible owner decisions, contradictory authority sources, a verified `STALLED` state, or when a missing capability leaves no further useful authorized work that can be completed or prepared.

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
