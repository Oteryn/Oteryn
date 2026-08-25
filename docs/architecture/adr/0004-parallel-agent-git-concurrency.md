# ADR 0004: Parallel-agent Git concurrency and late integration

- Status: Proposed
- Date: 2026-08-25
- Decision owner: repository owner
- Lifecycle issue: #61
- Admission META base: `3f154b32ab1dc9fd3437fb4976691b16f50e2e5d`
- Scope: all permanent Oteryn repositories (`Oteryn/Oteryn`, `Oteryn/Oteryn-Game`, `Oteryn/Oteryn-Platform`, `Oteryn/Oteryn-Atlas`)
- Excludes: archived migration/backup repositories unless separately reactivated and governed

## Context

Oteryn intentionally runs multiple autonomous agents in parallel. Each substantial task already uses a dedicated branch/PR, and Platform additionally states that one active agent uses one task branch/worktree. The remaining organization-wide gap is the meaning of a moving default branch while those workers are still implementing.

Without an explicit concurrency contract, an agent can incorrectly treat any advance of `main` as if its implementation were invalid, restart from the new head, discard durable work, or repeatedly redo expensive verification. That interpretation conflates three different facts:

1. the default branch advanced because another task integrated;
2. this task's implementation assumptions were materially changed;
3. the final merge/qualification base is no longer current.

Only (2) can invalidate affected implementation. (1) is normal parallel progress. (3) requires late integration refresh and renewed exact-head evidence, not a restart.

The organization therefore needs one cross-repository semantic contract for task admission, worker durability and final integration, while preserving provider-owned CI, tests and merge gates.

## Decision

Oteryn adopts **immutable task admission + isolated worker branches + late integration refresh** as the default parallel-agent Git model.

### 1. Three distinct revision coordinates

Every substantial mutating task must distinguish:

- `admission_main_sha`: the exact protected default-branch SHA from which the task branch was admitted. It is immutable historical provenance for that task.
- `task_head_sha`: the current exact SHA of the task branch. It changes only through authorized work on that branch, including a later integration refresh.
- `integration_main_sha`: the exact current protected default-branch SHA selected when the task enters final integration. It may equal `admission_main_sha`, but normally advances when other tasks merge first.

Agents must not overwrite one coordinate with another or use a single ambiguous `base/head` statement for all three lifecycle meanings.

### 2. A moving `main` does not automatically invalidate work

If `main` advances after task admission, the worker records `UPSTREAM_ADVANCED` (or an equivalent local state) and continues on its dedicated branch/worktree.

The agent MUST NOT solely because `main` moved:

- restart the task from the new `main`;
- reset or recreate the branch;
- discard commits, files, test evidence or investigation that remains applicable;
- copy the work onto a fresh branch as a substitute for reconciliation;
- stop useful implementation that is independent of the upstream change.

The admission SHA remains valid provenance even when it is no longer the current integration base.

The worker must still inspect whether the upstream delta changed a governing instruction or authority surface material to the task. If the delta includes applicable `AGENTS.md`/override instructions, safety/security policy, lifecycle authority, provenance authority, or a contract/invariant the task depends on, the agent reloads and reconciles that changed authority before further mutation. A changed authority surface may require focused rework or blocking, but it still does not justify blindly discarding unaffected work.

### 3. One active worker owns one branch/worktree

For substantial mutating work:

- one independently mergeable task maps to one canonical task branch and one PR;
- one active worker owns one writable worktree for that branch;
- agents do not share a writable branch/worktree concurrently;
- unrelated dirty state is preserved rather than absorbed, reset or cleaned;
- durable checkpoints are pushed to the authorized remote branch so work is not dependent on one local execution environment;
- path/task ownership remains an advisory overlap detector, not authority to modify another task.

Read-only scouts/reviewers create no branch unless they receive a separate mutating task.

### 4. Published task history is preserved by default

Once a task branch has been pushed or a PR exists, organization default is **merge-up refresh**, not history rewriting:

1. read the latest protected `main` from GitHub;
2. record it as `integration_main_sha`;
3. merge that exact current `main` into the task branch using a normal non-force update;
4. resolve only task-relevant conflicts within authorized scope;
5. push the resulting task head normally;
6. verify the remote head equals the intended local commit.

A force-push/rebase of a published task branch is not the organization default because it rewrites durable checkpoint SHAs, can invalidate review anchors and complicates multi-session continuation. A repository/task may explicitly permit rebase before publication or in a narrowly documented case, but it must never be used to erase unexplained work.

Squash-only merge policy into protected `main` remains unchanged; merge-up commits on the task branch do not alter the final squash history of `main`.

### 5. Integration happens late

Workers implement and run targeted/local validation on their isolated branch without repeatedly chasing unrelated `main` movement.

A task enters final integration only after its own implementation is coherent and self-review is complete enough to justify the expensive final cycle. At that point the agent:

1. refreshes GitHub lifecycle state and current protected `main`;
2. records `integration_main_sha`;
3. performs the merge-up refresh when `main` advanced;
4. reviews the complete post-refresh diff and changed-file set;
5. reruns every validation layer invalidated by the refresh;
6. obtains repository-required exact-`task_head_sha` CI/review evidence;
7. attempts merge only through the normal protected repository gate.

This concentrates expensive reconciliation at the integration boundary while allowing implementation to remain parallel.

### 6. Lost merge races return to integration, not implementation

If another PR merges after a task's integration refresh and the repository's protection/merge rules now require another current-base refresh, the task returns to the integration step.

The previous implementation is not invalidated merely by that race. The agent refreshes again, reconciles the new delta, reruns invalidated exact-head checks and proceeds. Repeated refresh is bounded to the integration/qualification cycle.

### 7. Exact-head evidence and work validity are different

Exact-head CI/review evidence is always bound to the exact task head on which it ran. When an integration refresh changes `task_head_sha`, evidence that depends on the old head becomes superseded and must be regenerated where required.

Superseded evidence does not imply the underlying implementation was wrong. Agents must distinguish:

- `WORK_VALID`: implementation still applies;
- `EVIDENCE_SUPERSEDED`: final proof must be rerun on the new task head;
- `RECONCILIATION_REQUIRED`: upstream changes materially intersect the task;
- `TASK_INVALIDATED`: the governing task is superseded/cancelled or its assumptions/authority can no longer be truthfully preserved.

### 8. Material invalidation is fail-closed and specific

An upstream change invalidates affected work only when verified evidence shows at least one of:

- the governing Issue/task was cancelled, superseded or materially re-scoped;
- an authority, safety, security, provenance or compatibility contract governing the task changed incompatibly;
- upstream changes alter the same semantics/data contract/API/schema/invariant that the task depends on;
- reconciliation produces a semantic conflict that cannot be resolved within the task's authorization;
- required tests demonstrate that prior task assumptions no longer hold.

A textual overlap or changed file name alone is not automatically semantic invalidation. Conversely, a non-overlapping filename set does not prove semantic independence when shared contracts are involved.

When only part of a task is invalidated, preserve unaffected work and rework the smallest affected portion.

### 9. Conflict handling

During merge-up refresh:

- trivial textual conflicts inside owned scope may be resolved and then fully revalidated as appropriate;
- overlap with another active task must be reconciled against live Issue/PR ownership before editing;
- semantic conflict with newly merged authority requires `RECONCILIATION_REQUIRED` and focused review of impacted assumptions;
- a conflict outside authorization is a blocker to that integration, not permission for cross-scope cleanup;
- agents must never use `reset --hard`, blanket checkout, broad clean or force-push as a generic conflict shortcut on shared execution hosts.

### 10. Cross-repository rollout model

META owns the canonical contract in `docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md`.

Because root `AGENTS.md` does not inherit across repositories, each permanent provider root must also contain a short mandatory parallel-work section that makes the critical behavior visible at bootstrap:

- record immutable `admission_main_sha`;
- one active agent per task branch/worktree;
- `main` movement alone does not invalidate work;
- no reset/restart solely to chase the moving default branch;
- reload changed governing instruction/authority surfaces before further mutation when the upstream delta touches them;
- perform late merge-up refresh to current `integration_main_sha`;
- rerun invalidated exact-head validation on the resulting `task_head_sha`;
- treat only verified semantic/authority conflict or task supersession as invalidation.

Provider sections may add stricter repository-specific gates but may not weaken those minimum semantics.

META root `AGENTS.md` already mandates the central execution/continuation contract, so no duplicate large section is required there.

### 11. Enforcement boundary

Version 1 is an instruction/lifecycle contract, not a new organization-wide settings writer or provider CI centralization.

Provider merge gates remain authoritative for provider validation. META may add a small deterministic governance check only if it can verify durable instruction/contract structure without creating a brittle cross-repository network dependency or conflicting with active governance work.

A future GitHub-native merge queue, ruleset automation or organization-level repository template may improve throughput, but is not required for this decision and must not be invented as an implicit fifth control plane.

## Alternatives considered

### A. Central META policy only

Rejected as insufficient. Product agents bootstrap from their own repository instructions; GitHub does not provide automatic inheritance of arbitrary root `AGENTS.md` content from META.

### B. Copy the full concurrency policy into every repository

Rejected because it creates four mutable sources, increases prompt/bootstrap size and will drift. ADR 0002 already prefers small stable root instructions and reusable procedures/contracts.

### C. Shared integration branch for all agents

Rejected. It couples otherwise independent work, recreates shared-writable-state hazards, obscures task ownership and makes one agent's partial work part of another's base.

### D. Constant rebasing against every new `main`

Rejected. It burns validation/review capacity during normal parallel progress, rewrites published history when force-pushed, and conflates current merge-base freshness with implementation validity.

## Rollout plan

After this ADR is approved:

1. update META `docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md` with the canonical normative protocol;
2. add thin compatible root `AGENTS.md` sections to Game, Platform and Atlas;
3. preserve Platform's existing `one agent = one branch/worktree` rule and extend it rather than duplicating it;
4. avoid unrelated runtime, workflow, runner, deployment or branch-protection changes;
5. create repository-local Issues/branches/PRs as required by each provider's lifecycle rules;
6. reconcile against any intervening `main` advancement using this protocol itself;
7. require exact-final-head CI/review and normal squash merge for each repository change.

The archived `Oteryn-Platform-Migration-Backup-20260818` is not modified.

## Verification requirements

The rollout must prove:

- all four permanent repositories have an unambiguous bootstrap path to the organization concurrency rule;
- Game, Platform and Atlas root instructions contain the minimum non-invalidation/late-integration semantics;
- the META contract explicitly distinguishes admission, task-head and integration revisions;
- no rule instructs an agent to discard/restart work solely because protected `main` moved;
- published task branches use non-destructive normal refresh by default;
- changed governing instructions/authority are reloaded before further mutation when material;
- exact-head validation remains required after the final refresh;
- no provider runtime/product behavior changes;
- exact changed-file lists, diffs, CI and review state are verified on every final PR head.

A deterministic policy test should be added only when it has a stable local oracle and materially reduces future drift.

## Consequences

Positive:

- parallel implementation survives unrelated merges;
- far less repeated implementation and expensive verification;
- clearer handoffs because admission and integration revisions are distinct;
- durable checkpoints remain reachable after session/agent replacement;
- provider gates remain exact-head and fail-closed;
- normal protected-branch Git semantics remain the final concurrency arbiter.

Costs:

- a ready PR may still need one or more late integration refreshes if many PRs merge ahead of it;
- final CI/review can legitimately rerun after each refresh;
- semantic conflicts still require real reconciliation rather than automatic conflict suppression;
- root instructions in permanent repositories must carry a small duplicated bootstrap minimum because cross-repository `AGENTS.md` inheritance does not exist.

## Authority and precedence

If accepted, this ADR extends ADR 0002's one-task/one-branch/one-PR operating model and is canonical for organization-wide parallel-agent Git concurrency semantics.

The central execution/continuation contract contains the normative agent procedure. Provider repositories retain implementation/test/runtime authority and may impose stricter local validation/safety requirements. Live GitHub Issue/PR/check/protection state remains authoritative for current lifecycle and merge truth.
