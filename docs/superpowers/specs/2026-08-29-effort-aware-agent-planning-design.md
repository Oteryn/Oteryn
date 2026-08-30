# Effort-Aware Agent Execution Planning Design

Status: owner-approved design for Oteryn/Oteryn#94.

## Context

Oteryn's current organization routing contract makes substantial task preparation `parallel-first`. The human contract requires independent lanes whenever they can be separated safely, while the machine policy exposes `parallel_first` and `serial_with_reason` and makes serial execution require a concrete exception reason.

That default is too aggressive. Safe separability is not the same as useful parallelism: a task can be technically splittable while coordination, shared-contract churn, merge ordering, duplicated context loading, or integration cost makes one worker faster and safer.

The owner-approved correction is to make execution planning effort-aware and proportional. Agents should choose the execution shape that minimizes expected completion cost while preserving correctness and repository safety, rather than maximizing the number of active workers.

## Goals

1. Require substantial-task planners to classify expected effort before choosing execution shape.
2. Make single-agent execution a normal first-class strategy, not an exception that needs a serial-specific justification.
3. Permit parallel agents only when at least two materially independent workstreams can make concurrent progress and the expected benefit exceeds coordination/integration overhead.
4. Require the smallest useful number of parallel lanes rather than maximizing concurrency.
5. Preserve all existing lane-isolation, path-ownership, lease, dependency, fresh-preflight, Remote Desktop, and late-integration safety rules.
6. Make the decision machine-readable enough for deterministic validation without building a scheduler or numeric scoring engine.
7. Require task/prompt authors to surface the recommended effort and the basis for choosing single-agent or parallel execution.

## Non-goals

- No product runtime, deployment, runner configuration, production, secret, or branch-protection changes.
- No automatic estimation model, duration prediction, token-budget model, or optimization solver.
- No removal of support for parallel-agent work.
- No weakening of one-writer-per-lane, isolated branch/worktree ownership, shared-resource leases, or integration-order validation.
- No provider-repository mutation in this META lifecycle. Provider adoption follows only after the META policy is canonical and each provider is freshly preflighted.

## Decision

### Human-facing rule

Replace `parallel-first` with **effort-aware proportional planning**.

Before starting or resuming substantial work, an agent must:

1. classify effort as `low`, `medium`, or `high`;
2. inspect the dependency graph, critical path, shared mutable surfaces, constrained resources, and likely integration overhead;
3. select `single_agent` when one worker is expected to be as fast or faster after coordination cost is included;
4. select `parallel_when_beneficial` only when two or more independent workstreams can progress concurrently and the expected benefit is material;
5. when parallelism is selected, use the smallest useful lane count and retain existing lane safety controls;
6. record a short `decision_basis` explaining the execution-shape assessment.

`decision_basis` is not a serial exception. It is a symmetric planning record required for both strategies so future agents can understand why the chosen shape was efficient.

### Machine-readable contract

Keep the existing top-level packet key `parallel_execution` for compatibility with current task packets and tooling. Its semantics become general execution planning rather than a parallelism mandate.

Bump `ecosystem/agent-execution-routing-policy.json` to schema version `2` and define:

```json
{
  "parallel_lane_rules": {
    "strategies": ["single_agent", "parallel_when_beneficial"],
    "effort_levels": ["low", "medium", "high"],
    "decision_basis_required": true,
    "single_agent_lane_count": 1,
    "parallel_minimum_lanes": 2,
    "required_lane_fields": [
      "id",
      "owned_paths",
      "depends_on",
      "branch_and_worktree",
      "shared_leases"
    ],
    "one_writer_per_lane": true,
    "unique_branch_and_worktree": true,
    "overlap_requires_lease": true,
    "constrained_resource_requires_lease": true,
    "integration_order_required": true
  }
}
```

A valid substantial-task packet therefore includes, within `parallel_execution`:

```json
{
  "effort": "medium",
  "lane_strategy": "single_agent",
  "decision_basis": "The contract, validator and policy form one shared critical path; splitting would add merge and context overhead.",
  "lanes": [
    {
      "id": "governance",
      "owned_paths": ["docs/agents/**", "ecosystem/agent-execution-routing-policy.json", "tools/governance/**"],
      "depends_on": [],
      "branch_and_worktree": "governance/effort-aware-agent-planning:repository-native-branch",
      "shared_leases": []
    }
  ],
  "integration_order": ["governance"]
}
```

### Validator behavior

`tools/governance/agent_execution_routing.py` will fail closed when:

- `parallel_execution.effort` is missing or outside the policy's closed effort set;
- `parallel_execution.decision_basis` is missing or empty;
- the strategy is outside the policy's closed strategy set;
- `single_agent` has anything other than exactly one lane;
- `parallel_when_beneficial` has fewer than two lanes;
- existing lane ownership, dependency, lease, constrained-resource, worktree-isolation, or integration-order rules fail;
- the policy's effort/strategy/cardinality controls are malformed.

The validator cannot prove that a subjective cost/benefit judgment is correct. Review and task authors remain responsible for the quality of `decision_basis`. Deterministic enforcement is intentionally limited to closed enums, required evidence fields, lane cardinality, and existing safety invariants.

## Documentation changes

- `AGENTS.md`: replace the `parallel-first` mandate with effort-aware proportional planning and explicitly make single-agent execution first-class.
- `docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md`: rename the relevant routing/planning language and define the new planning semantics while preserving all other authority and safety constraints.
- Historical design/ADR material that accurately describes prior decisions remains historical provenance unless it is itself normative current instruction. This change does not rewrite old design history merely to make it look current.

## TDD and validation

The behavioral change is implemented test-first in `tools/governance/test_agent_execution_routing.py`:

1. change the canonical fixture to the new single-agent packet shape;
2. prove single-agent packets no longer require a serial-exception field;
3. prove parallel execution requires at least two lanes;
4. prove a valid two-lane beneficial-parallel plan passes;
5. prove missing/invalid effort and missing decision basis fail;
6. prove malformed machine-policy planning controls fail closed;
7. preserve all existing Remote Desktop, preflight, path, lease, dependency, and integration-order regressions.

The first test-only commit must fail against the old implementation. The implementation commit then makes the suite green. Existing META CI already runs `tools/governance/test_agent_execution_routing.py`, so no workflow expansion is required unless the live repository proves otherwise.

## Execution-shape decision for this issue

Effort: `medium`.

Strategy: `single_agent`.

Decision basis: the root instructions, central execution contract, machine policy, routing validator, and routing tests describe one shared governance contract and will be edited/reviewed as one coherent change. Multiple writers would repeatedly touch the same semantics and would add branch/worktree/integration overhead without producing independent critical-path progress.

## Admission and overlap snapshot

- repository: `Oteryn/Oteryn`;
- protected default branch: `main`;
- admission main SHA: `e002fc7532188e73a0f495da3e20710541ed50e0`;
- governing Issue: `#94`;
- task branch: `governance/effort-aware-agent-planning`;
- active overlapping work observed at admission: PR `#71` and PR `#73` touch `AGENTS.md` and/or the central execution contract; they are not modified or superseded by branch mutation;
- current task must use normal late integration if protected `main` advances before merge.

## Rollout

1. Merge this META policy to protected `main` after exact-head tests/review pass.
2. Verify protected-main readback of the new policy and validator behavior.
3. Only then perform thin provider adoption in Game, Platform, and Atlas where their local agent instructions or packet fixtures still encode `parallel-first` semantics.
4. Provider adoption must preserve stricter local safety rules and must not be used to change product runtime behavior.