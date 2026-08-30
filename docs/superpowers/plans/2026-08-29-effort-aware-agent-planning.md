# Effort-Aware Agent Planning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Oteryn's organization-wide `parallel-first` routing preference with effort-aware proportional planning that chooses single-agent or parallel execution based on real expected benefit.

**Architecture:** Keep the existing `parallel_execution` packet container for compatibility, but change its planning semantics and machine policy to schema v2. The deterministic validator will require `effort` plus a symmetric `decision_basis`, enforce exactly one lane for `single_agent`, at least two lanes for `parallel_when_beneficial`, and retain all existing lane/preflight/Remote-Desktop safety invariants.

**Tech Stack:** Markdown governance contracts, JSON policy, Python 3 deterministic validator/tests, GitHub Actions `meta-gate`.

**Spec:** `docs/superpowers/specs/2026-08-29-effort-aware-agent-planning-design.md`

## Global Constraints

- Governing Issue: `Oteryn/Oteryn#94`.
- Admission protected `main`: `e002fc7532188e73a0f495da3e20710541ed50e0`.
- Task branch: `governance/effort-aware-agent-planning`.
- Effort: `medium`.
- Execution strategy for this implementation: `single_agent` because all modified surfaces describe one shared governance contract and parallel writers would create coordination/integration overhead.
- Do not modify Game, Platform, Atlas runtime, deployment, runner configuration, secrets, production state, or branch protection.
- Preserve GitHub-first routing, fresh preflight, Remote Desktop default-deny/per-action gating, one-writer-per-lane, path isolation, leases, dependency ordering, and late-integration semantics.
- Open PRs `#71` and `#73` are overlap records only; do not mutate their branches.

---

### Task 1: Specify the new routing behavior with failing tests

**Files:**
- Modify: `tools/governance/test_agent_execution_routing.py`

**Interfaces:**
- Consumes: `routing.validate_packet(packet, live_state=..., policy=...) -> list[str]`.
- Produces: executable behavior requirements for policy schema v2 and the new planning strategies.

- [ ] **Step 1: Change the canonical packet fixture to the desired single-agent shape**

Change `default_packet()['parallel_execution']` to:

```python
"parallel_execution": {
    "effort": "medium",
    "lane_strategy": "single_agent",
    "decision_basis": "one shared governance contract is faster with one writer",
    "lanes": [lane("policy", ["docs/agents/schemas/**"])],
    "integration_order": ["policy"],
},
```

- [ ] **Step 2: Replace the obsolete serial-exception regression and add focused planning regressions**

Add tests equivalent to:

```python
def test_single_agent_is_a_first_class_strategy_without_serial_exception() -> None:
    packet = default_packet()
    parallel = packet["parallel_execution"]
    assert isinstance(parallel, dict)
    assert "serial_reason" not in parallel
    assert routing.validate_packet(packet, live_state=live_state(), policy=policy()) == []


def test_parallel_when_beneficial_requires_at_least_two_lanes() -> None:
    packet = default_packet()
    parallel = packet["parallel_execution"]
    assert isinstance(parallel, dict)
    parallel["lane_strategy"] = "parallel_when_beneficial"
    errors = routing.validate_packet(packet, live_state=live_state(), policy=policy())
    assert "parallel_when_beneficial requires at least two lanes" in errors


def test_parallel_when_beneficial_accepts_two_independent_lanes() -> None:
    packet = default_packet()
    parallel = packet["parallel_execution"]
    assert isinstance(parallel, dict)
    parallel["lane_strategy"] = "parallel_when_beneficial"
    parallel["decision_basis"] = "two disjoint workstreams can progress independently"
    parallel["lanes"] = [lane("one", ["src/one/**"]), lane("two", ["src/two/**"])]
    parallel["integration_order"] = ["one", "two"]
    assert routing.validate_packet(packet, live_state=live_state(), policy=policy()) == []


def test_effort_and_decision_basis_are_required() -> None:
    for field, expected in (
        ("effort", "parallel_execution.effort is not allowed"),
        ("decision_basis", "parallel_execution.decision_basis is required"),
    ):
        packet = default_packet()
        parallel = packet["parallel_execution"]
        assert isinstance(parallel, dict)
        del parallel[field]
        assert expected in routing.validate_packet(packet, live_state=live_state(), policy=policy())


def test_single_agent_requires_exactly_one_lane() -> None:
    packet = default_packet()
    parallel = packet["parallel_execution"]
    assert isinstance(parallel, dict)
    parallel["lanes"] = [lane("one", ["src/one/**"]), lane("two", ["src/two/**"])]
    parallel["integration_order"] = ["one", "two"]
    assert "single_agent requires exactly one lane" in routing.validate_packet(
        packet, live_state=live_state(), policy=policy()
    )
```

Add a malformed-policy regression proving the validator rejects missing/invalid `effort_levels`, strategy/cardinality controls, or `decision_basis_required` rather than silently widening authority.

- [ ] **Step 3: Commit the RED test-only change**

Commit message:

```text
test(governance): specify effort-aware agent planning
```

- [ ] **Step 4: Run exact-head CI and verify RED for the intended reason**

Expected result: `meta-gate` fails in `Validate agent execution routing` because current schema v1 does not allow `single_agent`/`parallel_when_beneficial` and does not enforce the new required planning fields/cardinality. The failure must not be a syntax/import/infrastructure error.

---

### Task 2: Implement the machine policy and validator

**Files:**
- Modify: `ecosystem/agent-execution-routing-policy.json`
- Modify: `tools/governance/agent_execution_routing.py`

**Interfaces:**
- Consumes: the test contract from Task 1.
- Produces: schema-v2 machine policy and deterministic packet validation.

- [ ] **Step 1: Update the machine policy**

Set `schema_version` to `2` and replace the old parallel strategy controls with:

```json
"parallel_lane_rules": {
  "strategies": [
    "single_agent",
    "parallel_when_beneficial"
  ],
  "effort_levels": [
    "low",
    "medium",
    "high"
  ],
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
```

Remove `serial_requires_reason` and the old `parallel_first` / `serial_with_reason` strategy values.

- [ ] **Step 2: Make policy-shape validation fail closed**

In `_policy_errors`, validate the planning control surface before it can authorize a packet. Required behavior:

```python
lane_rules = policy.get("parallel_lane_rules")
if not isinstance(lane_rules, dict):
    errors.append("policy parallel_lane_rules must be an object")
else:
    if set(lane_rules.get("strategies", [])) != {"single_agent", "parallel_when_beneficial"}:
        errors.append("policy parallel_lane_rules.strategies must be the canonical effort-aware strategy set")
    if set(lane_rules.get("effort_levels", [])) != {"low", "medium", "high"}:
        errors.append("policy parallel_lane_rules.effort_levels must be the canonical effort set")
    if lane_rules.get("decision_basis_required") is not True:
        errors.append("policy parallel_lane_rules.decision_basis_required must be true")
    if lane_rules.get("single_agent_lane_count") != 1:
        errors.append("policy parallel_lane_rules.single_agent_lane_count must be 1")
    if lane_rules.get("parallel_minimum_lanes") != 2:
        errors.append("policy parallel_lane_rules.parallel_minimum_lanes must be 2")
    if lane_rules.get("unique_branch_and_worktree") is not True:
        errors.append("policy parallel_lane_rules.unique_branch_and_worktree must be true")
```

Retain the existing structural checks for lane fields and other policy sections.

- [ ] **Step 3: Enforce effort-aware packet semantics**

At the start of `_validate_lanes` add:

```python
effort_levels = {value for value in _list(rules.get("effort_levels")) if isinstance(value, str)}
effort = parallel.get("effort")
if not _is_closed_value(effort, effort_levels):
    errors.append("parallel_execution.effort is not allowed")

decision_basis = parallel.get("decision_basis")
if not isinstance(decision_basis, str) or not decision_basis.strip():
    errors.append("parallel_execution.decision_basis is required")
```

Replace the old strategy-specific checks with:

```python
if strategy == "single_agent" and len(lanes) != 1:
    errors.append("single_agent requires exactly one lane")
if strategy == "parallel_when_beneficial" and len(lanes) < 2:
    errors.append("parallel_when_beneficial requires at least two lanes")
if strategy == "parallel_when_beneficial" and not _list(parallel.get("integration_order")):
    errors.append("parallel_when_beneficial requires a non-empty integration_order")
```

Do not remove downstream lane ownership, overlap, lease, dependency, or integration-order checks.

- [ ] **Step 4: Run the focused tests until GREEN**

Run through exact-head CI or an equivalent repository-approved environment:

```text
python3 tools/governance/test_agent_execution_routing.py
python3 tools/governance/test_remote_desktop_action_gate.py
```

Expected: PASS.

- [ ] **Step 5: Commit the minimal implementation**

Commit message:

```text
feat(governance): make agent routing effort-aware
```

---

### Task 3: Update the canonical human governance contract

**Files:**
- Modify: `AGENTS.md`
- Modify: `docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md`

**Interfaces:**
- Consumes: schema-v2 strategy and effort names from Task 2.
- Produces: organization-readable instructions matching the enforced machine behavior.

- [ ] **Step 1: Replace the root `parallel-first` instruction**

The root instruction must state all of these facts in concise prose:

```text
Project task preparation is effort-aware and proportional. Before choosing an execution shape, classify substantial work as low/medium/high effort and assess dependencies, critical path, shared mutable surfaces, constrained resources, and coordination/integration overhead. `single_agent` is a normal first-class strategy and needs no serial exception. Use `parallel_when_beneficial` only when at least two materially independent workstreams can progress concurrently and the expected benefit exceeds coordination cost; use the smallest useful lane count. Parallel lanes retain isolated branch/worktree ownership, dependencies, path ownership, leases, and integration order.
```

- [ ] **Step 2: Reconcile the central contract**

Rename `Default-deny Remote Desktop and parallel-first routing` to `Default-deny Remote Desktop and effort-aware routing` and replace `Parallel-first task planning` with `Effort-aware task planning` that documents `effort`, `lane_strategy`, `decision_basis`, the two strategy values, and the unchanged lane-safety rules.

Do not alter unrelated GitHub-first, Remote Desktop, preflight, late-integration, capability, or blocker semantics.

- [ ] **Step 3: Deterministically check stale normative wording**

Verify current normative surfaces do not retain an instruction that makes parallelism mandatory by default. Historical design/spec/ADR provenance may still contain the old phrase when it is clearly describing the superseded decision.

- [ ] **Step 4: Commit the documentation reconciliation**

Commit message:

```text
docs(governance): require proportional agent planning
```

---

### Task 4: Final verification, review, and integration

**Files:**
- Review all changed files from the branch against protected `main`.

**Interfaces:**
- Consumes: exact final task-head SHA and live GitHub state.
- Produces: merge-ready exact-head evidence and protected-main readback.

- [ ] **Step 1: Refresh live GitHub state before final qualification**

Read current protected `main`, Issue `#94`, PR state, exact task-head SHA, branch protection, open overlapping PRs, and whether `main` advanced from admission SHA.

- [ ] **Step 2: Reconcile upstream movement without rewriting history**

If `main` advanced, perform the repository's normal late-integration merge-up/reconciliation. Preserve task work and rerun invalidated evidence on the new exact head.

- [ ] **Step 3: Inspect exact diff and machine-readable policy**

Verify:

```text
- only intended governance/spec/plan/test/policy/validator paths changed;
- JSON parses;
- no secret/private/live-state material was added;
- policy schema is 2 and strategy/effort sets are exact;
- current human contract and machine validator agree;
- runtime/E2E is NOT_APPLICABLE.
```

- [ ] **Step 4: Require exact-head gates**

Required protected-main contexts remain:

```text
meta-gate
ai-review-gate
```

Do not merge until the required exact-head checks/reviews are successful and no unresolved material review findings remain.

- [ ] **Step 5: Squash merge and verify protected-main readback**

Use squash merge with the expected final head SHA. Then verify the resulting protected `main` SHA contains the schema-v2 policy, updated validator/tests, and new human instructions.

- [ ] **Step 6: Close lifecycle records**

Close Issue `#94` only after protected-main verification. Record that the new issue supersedes only the parallel-first preference from `#85`; the remaining GitHub-first/RDC/preflight safety policy stays active. Delete the source branch when the repository's terminal branch lifecycle permits it.