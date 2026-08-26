# Default-deny Remote Desktop and parallel-first task routing

**Status:** proposed
**Governing issue:** `Oteryn/Oteryn#85`
**Authority repository:** `Oteryn/Oteryn` (META)

## Decision

Oteryn will adopt a central, versioned execution-routing contract. GitHub state is the control-plane authority. Ordinary repository work uses a GitHub-hosted runner, an owning product's isolated organization runner, or a worker-owned isolated checkout. Remote Desktop/Desktop Commander (RDC) is denied unless the task declares and validates a narrowly defined host-only exception.

The contract also makes task preparation parallel-first. A substantial task must be decomposed into independently mergeable lanes whenever that does not create a shared-surface hazard. Each lane gets one writer, one branch, one worktree, explicit owned paths, declared dependencies, and a defined integration order. Shared mutable surfaces and constrained resources are explicit serialized leases rather than implicit contention.

## Contract model

The META policy will define a stable `execution_routing` record for new or resumed substantial task packets:

```yaml
execution_routing:
  execution_target: github_actions # github_actions | isolated_workspace | host_exception
  runner_class: github_hosted # github_hosted | organization_product_isolated | isolated_workspace | not_applicable
  equivalent_ci: '.github/workflows/ci.yml:meta-gate'
  remote_desktop: denied # denied | exception
  remote_desktop_reason: not_applicable # host_only_service | lan_or_hardware | self_hosted_runner_diagnosis | not_applicable
  github_preflight:
    verified_at: '2026-08-26T12:00:00Z'
    repository: Oteryn/Oteryn
    default_branch_sha: d79df968c1aba98373455399732fc71ab71e6a5d
    governing_issue: 85
    pull_request: none
    task_head_sha: none
parallel_execution:
  lane_strategy: parallel_first # parallel_first | serial_with_reason
  lanes:
    - id: meta-policy
      owned_paths: ['docs/agents/contracts/**']
      depends_on: []
      branch_and_worktree: required
      shared_leases: []
  integration_order: [meta-policy]
```

The final field names may be adjusted to the existing provider packet style, but their semantics, closed sets and fail-closed behavior are fixed by this decision.

## Routing rules

1. GitHub remains authoritative for repository identity, default branch, issue, PR, exact head, checks, reviews and merge state.
2. Before starting or resuming mutation, the worker refreshes and records the GitHub preflight. Existing local branches, worktrees, sessions, logs and caches cannot satisfy it.
3. `github_actions` or `isolated_workspace` is the default. Product workflows must select the owning product's isolated runner group and label where an organization runner is needed.
4. `host_exception` is valid only with `remote_desktop: exception` and exactly one reason from this closed list:
   - `host_only_service`: a service exists only on the named host and no equivalent runner workflow can reach it;
   - `lan_or_hardware`: LAN device, physical hardware, or an otherwise host-bound acceptance operation is in scope;
   - `self_hosted_runner_diagnosis`: a verified runner/workflow failure requires host-level diagnosis.
5. RDC is never justified merely because a checkout, shell, Docker daemon, toolchain or runner happens to be available there.
6. If an equivalent Actions workflow can validate, observe, rerun or produce the required artifact, manual RDC polling of process output, Docker logs, workflow state, test progress or Git state is forbidden. The worker reads Actions status/logs/artifacts through GitHub and follows the existing bounded-wait policy.
7. An exception authorizes only the minimum host action. It does not make the host an alternative repository authority or general development environment.

## Parallel planning rules

Task preparation evaluates a dependency graph before implementation. It creates parallel lanes for independent analysis, implementation, tests, documentation and review preparation. It serializes a lane only when a concrete dependency, shared mutable path, limited runner/E2E capacity, or integration boundary requires it. `serial_with_reason` must name that constraint.

Every lane identifies owned paths and its inputs/outputs. Agents do not share branches or writable worktrees. A shared Cargo workspace, browser shell, workflow, release manifest, staging route or limited heavy-test slot is represented as a lease with one current holder and a release condition. Integration is a distinct final lane that refreshes GitHub state, reconciles current `main` with a non-destructive merge-up, and renews invalidated exact-head evidence.

## Enforcement and rollout

META owns the canonical policy, machine-readable schema, deterministic validator, regression tests and META CI integration. The validator rejects missing routing records for new substantial packets, unknown enums, unjustified RDC use, an RDC exception alongside equivalent CI, an incomplete/stale resume preflight, unsafe parallel-lane ownership, and serial work without a concrete reason.

Game, Platform and Atlas adopt thin local bindings after the META policy is protected-merged. Each provider adds its local task-packet/template fields, validator tests and governance workflow invocation without changing product runtime, deployment, secrets, runner configuration or branch protection. Provider policies may be stricter but cannot weaken META's default-deny behavior.

Existing open META PRs #71 and #73, plus their provider adoption PRs, remain separate bounded-execution work. This rollout neither rewrites their branches nor treats them as merged. It depends on their eventual terminal reconciliation where shared no-polling and lifecycle behavior overlaps.

## Verification

Deterministic tests cover allowed default routes, all three allowed exception reasons, forbidden generic RDC use, prohibited equivalent-CI polling, missing/invalid GitHub preflight, resumed-task refresh, safe independent lanes, overlapping path rejection, missing lease for constrained resources, and serial planning without justification.

META CI validates the central contract and its tests on the exact PR head. Each provider CI validates its binding on its exact provider PR head. The protected merge gates, review requirements and existing owner-funded AI review policy remain unchanged. The Windows local symlink limitation observed during baseline validation is not mitigated by changing the owner environment; the affected repository test is instead proven on GitHub-hosted Linux CI.
