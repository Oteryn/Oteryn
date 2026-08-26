# Remote Desktop and Parallel Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make META's GitHub-first execution policy machine-checkable, default-deny Remote Desktop/Desktop Commander, and require safe parallel-first planning for substantial task packets.

**Architecture:** META owns a versioned JSON policy and focused Python validator. The root instructions and execution contract reference that source of truth. The validator compares a declared execution packet with an explicit GitHub preflight snapshot, keeping the test suite deterministic and independent from host state.

**Tech Stack:** Markdown, JSON, Python 3.12 standard library, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-26-remote-desktop-parallel-routing-design.md`

## Global Constraints

- GitHub is authoritative for repository, branch, Issue, PR, SHA, check and review facts.
- Default routes are `github_actions` and `isolated_workspace`; RDC is default-deny.
- Only `host_only_service`, `lan_or_hardware`, and `self_hosted_runner_diagnosis` may justify RDC.
- Equivalent CI forbids RDC polling.
- Every resumed task compares its preflight against current GitHub facts.
- One parallel lane has one writer, branch and worktree; overlap and constrained resources require a lease.
- Existing META PRs #71 and #73 are separate; do not modify them.

---

### Task 1: Define the machine-readable policy and red tests

**Files:**
- Create: `ecosystem/agent-execution-routing-policy.json`
- Create: `tools/governance/test_agent_execution_routing.py`

**Interfaces:**
- Produces policy keys `execution_targets`, `runner_classes`, `remote_desktop_reasons`, `resume_preflight_required_fields`, and `parallel_lane_rules`.
- Tests will call `validate_packet(packet, live_state=..., policy=...) -> list[str]`.

- [ ] **Step 1: Write failing behavior tests**

```python
def test_default_actions_packet_passes() -> None:
    assert routing.validate_packet(default_packet(), live_state=live_state(), policy=policy()) == []

def test_undeclared_remote_desktop_exception_fails() -> None:
    packet = default_packet()
    packet["execution_routing"]["execution_target"] = "host_exception"
    assert "host_exception requires remote_desktop=exception" in routing.validate_packet(packet, live_state=live_state(), policy=policy())

def test_equivalent_ci_forbids_rdc_polling() -> None:
    packet = exception_packet("self_hosted_runner_diagnosis")
    packet["execution_routing"]["equivalent_ci"] = ".github/workflows/ci.yml:meta-gate"
    packet["execution_routing"]["requested_host_actions"] = ["poll_docker_logs"]
    assert "equivalent_ci prohibits RDC polling" in routing.validate_packet(packet, live_state=live_state(), policy=policy())
```

- [ ] **Step 2: Run red tests**

Run: `python tools/governance/test_agent_execution_routing.py`

Expected: fails because the validator module does not exist.

- [ ] **Step 3: Add the versioned policy**

```json
{
  "schema_version": 1,
  "execution_targets": ["github_actions", "isolated_workspace", "host_exception"],
  "remote_desktop_reasons": ["host_only_service", "lan_or_hardware", "self_hosted_runner_diagnosis"],
  "forbidden_remote_desktop_actions_when_equivalent_ci": ["poll_process_output", "poll_docker_logs", "poll_workflow_state", "poll_git_state"]
}
```

Add the six GitHub preflight fields and the lane/lease rules from the approved specification.

- [ ] **Step 4: Parse and commit the schema/test package**

Run: `python -c "import json; json.load(open('ecosystem/agent-execution-routing-policy.json', encoding='utf-8'))"`

```bash
git add ecosystem/agent-execution-routing-policy.json tools/governance/test_agent_execution_routing.py
git commit -m "test(governance): specify execution routing contract"
```

### Task 2: Implement the validator through green tests

**Files:**
- Create: `tools/governance/agent_execution_routing.py`
- Modify: `tools/governance/test_agent_execution_routing.py`

**Interfaces:**
- `load_policy(path: Path) -> dict[str, object]`
- `validate_packet(packet: dict[str, object], *, live_state: dict[str, object], policy: dict[str, object]) -> list[str]`
- CLI options: `--policy`, `--packet`, `--live-state`; exit 0 only for no errors.

- [ ] **Step 1: Add red resume and parallel tests**

```python
def test_resume_preflight_mismatch_fails() -> None:
    packet = default_packet()
    packet["execution_routing"]["github_preflight"]["default_branch_sha"] = "a" * 40
    assert "github_preflight.default_branch_sha does not match live_state" in routing.validate_packet(packet, live_state=live_state(), policy=policy())

def test_overlapping_parallel_lanes_fail() -> None:
    packet = default_packet()
    packet["parallel_execution"]["lanes"] = [
        lane("contract", ["docs/agents/contracts/**"]),
        lane("specific-file", ["docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md"]),
    ]
    assert "parallel lanes have overlapping owned_paths" in routing.validate_packet(packet, live_state=live_state(), policy=policy())
```

- [ ] **Step 2: Run red tests**

Run: `python tools/governance/test_agent_execution_routing.py`

Expected: fails for missing resume and parallel validation.

- [ ] **Step 3: Implement minimal validation**

```python
def validate_packet(packet: dict[str, object], *, live_state: dict[str, object], policy: dict[str, object]) -> list[str]:
    errors: list[str] = []
    # Validate closed enums, exception pairing, CI/polling exclusion,
    # preflight identities, lane overlaps, dependencies, serial reasons, and leases.
    return errors
```

The validator must not call a host or GitHub; callers supply authenticated GitHub facts in `live_state`.

- [ ] **Step 4: Run green tests and commit**

Run: `python tools/governance/test_agent_execution_routing.py`

Expected: all cases pass.

```bash
git add tools/governance/agent_execution_routing.py tools/governance/test_agent_execution_routing.py
git commit -m "feat(governance): validate execution routing"
```

### Task 3: Bind the policy to agent instructions and CI

**Files:**
- Modify: `AGENTS.md`
- Modify: `docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md`
- Modify: `.github/workflows/ci.yml`
- Modify: `tools/governance/test_agent_execution_routing.py`

**Interfaces:**
- Contract uses exact default-deny and parallel-first terms from Task 1.
- META CI invokes `python3 tools/governance/test_agent_execution_routing.py`.

- [ ] **Step 1: Add the failing contract test**

```python
def test_contract_declares_default_deny_and_parallel_first() -> None:
    text = Path("docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md").read_text(encoding="utf-8")
    assert "Remote Desktop/Desktop Commander is default-deny" in text
    assert "parallel-first task plan" in text
```

- [ ] **Step 2: Run the test before editing the contract**

Run: `python tools/governance/test_agent_execution_routing.py`

Expected: failure for missing mandatory terms.

- [ ] **Step 3: Add the contract and CI binding**

Document the routing record, exception table, equivalent-CI polling prohibition, fresh resume preflight, lanes, shared leases and integration order. Add this workflow step after the existing governance tests:

```yaml
- name: Validate agent execution routing
  shell: bash
  run: python3 tools/governance/test_agent_execution_routing.py
```

- [ ] **Step 4: Run focused tests and commit**

Run: `python tools/governance/test_agent_execution_routing.py`

Expected: all routing and contract assertions pass.

```bash
git add AGENTS.md docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md .github/workflows/ci.yml tools/governance/test_agent_execution_routing.py
git commit -m "docs(governance): enforce RDC default deny"
```

### Task 4: Exact-head META verification and provider rollout gate

**Files:**
- Modify: `docs/superpowers/specs/2026-08-26-remote-desktop-parallel-routing-design.md`
- Modify: `docs/superpowers/plans/2026-08-26-remote-desktop-parallel-routing.md`

**Interfaces:**
- Consumes final META branch head and PR #87.
- Produces a protected META authority prerequisite for an independent adoption plan in Game, Platform and Atlas.

- [ ] **Step 1: Run complete META validation**

```bash
python tools/governance/audit_github_readonly.py --offline
python tools/governance/test_audit_github_readonly.py
python tools/governance/test_audit_github_readonly_terminal.py
python tools/governance/test_ai_review_policy.py
python tools/governance/test_ai_review_git_metadata.py
python tools/governance/test_verify_ai_review_evidence.py
python tools/governance/test_agent_execution_routing.py
```

Expected: all supported local tests exit 0. The known Windows symlink-permission case is proven on exact-head Linux Actions without changing the owner environment.

- [ ] **Step 2: Inspect and publish the final META head**

```bash
git diff --check origin/main...HEAD
git diff --name-status origin/main...HEAD
git push origin governance/rdc-parallel-routing
gh pr view 87 --repo Oteryn/Oteryn --json headRefOid,statusCheckRollup,reviewDecision,mergeStateStatus
```

Expected: only governance policy, validator, tests, workflow, spec and plan paths change; remote head matches local head.

- [ ] **Step 3: Require protected META merge before providers**

Require exact-head `meta-gate` and the existing review gate. After protected merge, refresh each provider's instructions, default branch, governing Issue, open governance PRs and ownership. Then use three separate branches/worktrees and provider-native task-packet/validator/workflow patterns for Game, Platform and Atlas; these adopters must not touch runtime code or host configuration.
