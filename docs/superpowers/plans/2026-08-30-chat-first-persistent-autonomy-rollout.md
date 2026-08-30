# Chat-first Persistent Autonomy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a thin organization continuation layer that keeps owner-visible tasks durable across worker/session/tool/context boundaries while preserving `#69/#71` bounded-execution authority, `#102/#103` merge-integration authority, and provider-owned orchestration.

**Architecture:** META will publish one versioned continuation policy plus deterministic validation for task/session/tool/wait/retry/context separation, executor selection, truthful resume mechanisms and checkpoint semantics. Game and Atlas will adopt the minimum by reference; Platform will map it into its existing Control Room/checkpoint model rather than creating a second schema.

**Tech Stack:** Markdown governance contracts, JSON machine policy, Python deterministic validators/tests, GitHub Actions, provider root agent instructions and existing Platform agent tooling.

**Spec:** `docs/superpowers/specs/2026-08-30-chat-first-persistent-autonomy-design.md`

## Global Constraints

- `Oteryn/Oteryn#69` / PR `#71` remains the sole bounded-autonomous-execution lifecycle authority.
- `Oteryn/Oteryn#104` / PR `#107` remains scoped to effort-aware routing, Remote Desktop exact-call binding and provider execution-policy drift; it must not establish a second bounded lifecycle.
- `Oteryn/Oteryn#102` / PR `#103` remains the sole candidate/integration-head, review-fingerprint and Merge Queue authority.
- Do not copy `RUNNING`, `WAITING_EXTERNAL`, `BLOCKED`, `STALLED`, `READY`, `DONE`, retry budgets, candidate-freeze rules or `LOOP_BREAKER_AUDIT` into a second lifecycle schema.
- Do not create a second Platform Control Room/checkpoint schema; broader Platform schema-first migration remains owned by `Oteryn/Oteryn-Platform#1009`.
- Effort and execution surface are independent; `high` effort alone must never require Work/Codex.
- Automatic continuation may be claimed only when a real configured mechanism and concrete locator exist.
- Worker/session, command, wait or context exhaustion alone must not terminate the owner-visible task.
- Continuation must never reset canonical bounded-execution retry/evidence counters.
- Frozen candidates must not receive empty/no-op/checkpoint/retrigger commits.
- No product runtime, deployment, production, credential, secret or live-data mutation is part of this rollout.
- GitHub live state must be refreshed before every task; historical Issue/PR/SHA references in this plan are locators only.

---

### Task 1: Freeze the authority split before implementation

**Files:**
- No repository code changes.
- Durable control-plane updates: `Oteryn/Oteryn#69`, `#104`, `#108` and the relevant PR conversations.

**Interfaces:**
- Consumes: owner-approved design in `docs/superpowers/specs/2026-08-30-chat-first-persistent-autonomy-design.md`.
- Produces: unambiguous live ownership record: `#69/#71 = bounded lifecycle`, `#104/#107 = routing/RDC/provider-drift`, `#102/#103 = merge integration`, `#108 = persistent continuation`.

- [ ] **Step 1: Refresh the four authority lifecycles**

Read current protected META `main`, Issues `#69`, `#104`, `#108`, `#102`, PRs `#71`, `#107`, `#109`, `#103`, their exact heads, draft/readiness state, review threads and required checks.

Expected: no hidden successor Issue/PR has taken ownership of the same semantics.

- [ ] **Step 2: Record the approved ownership split**

Add one concise durable comment to `#108` and, if live overlap still exists, cross-reference it from `#69/#71` and `#104/#107`:

```text
OWNER-APPROVED AUTHORITY SPLIT — 2026-08-30
- #69/#71: sole bounded autonomous lifecycle / retries / freeze / LOOP_BREAKER_AUDIT
- #104/#107: effort-aware routing, Remote Desktop exact-call binding, provider execution-policy drift only
- #102/#103: candidate/integration head, review fingerprint, Merge Queue only
- #108/#109: task-vs-worker/tool/wait/retry/context continuation, executor selection, checkpoint/resume/user-notification semantics only
No lineage may silently absorb another authority surface.
```

- [ ] **Step 3: Verify no conflicting writer is allowed to merge as a second authority**

If PR `#107` still contains bounded-execution contract/workflow files, classify that as `RECONCILIATION_REQUIRED`, not as permission for `#108` to edit `#107`'s branch.

Expected next state: the `#107` owner must either drop the duplicate bounded-execution material or reconcile it into the sole `#69/#71` lineage before protected-main admission.

- [ ] **Step 4: Persist the dependency gate**

Record on `#108`:

```text
Implementation of the canonical continuation contract may begin only after the live META overlap between #71 and #107 is terminally reconciled and protected-main authority is unambiguous. Documentation/design work may continue meanwhile; no competing AGENTS/CI/policy writer is allowed.
```

- [ ] **Step 5: Commit**

No Git commit is created for control-plane-only comments.

---

### Task 2: Add the thin META continuation machine policy with TDD

**Prerequisite:** Task 1 is terminal and the live META bounded/routing ownership conflict is resolved. Refresh `main` before branching.

**Files:**
- Create: `ecosystem/agent-continuation-policy.json`
- Create: `tools/governance/agent_continuation_policy.py`
- Create: `tools/governance/test_agent_continuation_policy.py`

**Interfaces:**
- Consumes: canonical bounded policy identity from the eventual protected-main `#69/#71` merge; current `ecosystem/agent-execution-routing-policy.json` from protected `main`.
- Produces: `load_policy(path) -> dict`, `validate_policy(policy) -> None`, `validate_continuation_snapshot(policy, snapshot) -> None`, `select_execution_surface(policy, facts) -> str`.

- [ ] **Step 1: Write failing policy-schema tests**

Add tests that require exactly these closed vocabularies:

```python
WORKER_DISPOSITIONS = {
    "continue_current",
    "release_waiting",
    "rotate_resumable",
    "stop_reinvoke_required",
    "terminal",
}

RESUME_MECHANISMS = {
    "same_session",
    "github_native",
    "scheduled_task",
    "work_event_trigger",
    "work_persistent",
    "owner_reinvoke",
    "none_terminal",
}

EXECUTION_SURFACES = {
    "chat",
    "github_native",
    "work",
    "codex",
}
```

Also assert that the JSON policy references, rather than duplicates, the canonical bounded policy ID and merge-integration authority.

- [ ] **Step 2: Run the focused tests and prove RED**

Run:

```bash
python3 -m unittest tools.governance.test_agent_continuation_policy -v
```

Expected: FAIL because `agent_continuation_policy.py` and `agent-continuation-policy.json` do not exist.

- [ ] **Step 3: Create the minimal JSON policy**

The machine policy must contain:

```json
{
  "schema_version": 1,
  "policy_id": "oteryn-agent-continuation-v1",
  "lifecycle_authority": "Oteryn/Oteryn#108",
  "bounded_execution_authority": "Oteryn/Oteryn#69",
  "merge_integration_authority": "Oteryn/Oteryn#102",
  "coordinates": ["task", "worker_session", "tool_command", "external_wait", "retry_no_progress", "context_pressure"],
  "worker_dispositions": ["continue_current", "release_waiting", "rotate_resumable", "stop_reinvoke_required", "terminal"],
  "resume_mechanisms": ["same_session", "github_native", "scheduled_task", "work_event_trigger", "work_persistent", "owner_reinvoke", "none_terminal"],
  "execution_surfaces": ["chat", "github_native", "work", "codex"]
}
```

Add machine-readable invariants for the tests below; do not copy bounded retry numbers or bounded lifecycle state definitions into this file.

- [ ] **Step 4: Implement fail-closed policy loading and validation**

In `tools/governance/agent_continuation_policy.py`, implement:

```python
def load_policy(path: Path) -> dict: ...
def validate_policy(policy: dict) -> None: ...
def validate_continuation_snapshot(policy: dict, snapshot: dict) -> None: ...
def select_execution_surface(policy: dict, facts: dict) -> str: ...
```

Reject unknown schema versions, missing authority references, duplicate vocabulary values, unknown dispositions/mechanisms/surfaces and malformed booleans/integers where the schema expects another type.

- [ ] **Step 5: Add false-auto-resume tests**

Test these exact failures:

```python
# rotate_resumable requires an automatic mechanism plus non-empty locator
{"worker_disposition": "rotate_resumable", "resume_mechanism": "owner_reinvoke", "resume_locator": None}

# owner_reinvoke must be explicit stop, not resumable rotation
{"worker_disposition": "rotate_resumable", "resume_mechanism": "owner_reinvoke", "resume_locator": "owner"}

# terminal task cannot advertise scheduled continuation
{"worker_disposition": "terminal", "resume_mechanism": "scheduled_task", "resume_locator": "task-1"}
```

Expected: all fail closed.

- [ ] **Step 6: Add task-lifetime separation tests**

Reject snapshots whose sole terminal reason is one of:

```python
{
    "worker_session_timeout",
    "tool_timeout",
    "foreground_budget_exhausted",
    "context_rotation",
}
```

unless the snapshot also carries an independently valid canonical bounded-lifecycle terminal condition.

- [ ] **Step 7: Add retry-preservation tests**

Given `previous_bounded_generation` and `previous_retry_counters`, ensure worker rotation, execution-surface change or resume firing cannot reduce or reset the canonical counters. The continuation validator should compare values but must not reinterpret the bounded counter scopes.

- [ ] **Step 8: Add executor-selection tests**

Prove:

```python
assert select_execution_surface(policy, {
    "effort": "high",
    "chat_tools_sufficient": True,
    "heavy_deterministic_compute": False,
    "persistent_capability_required": False,
}) == "chat"

assert select_execution_surface(policy, {
    "effort": "medium",
    "chat_tools_sufficient": True,
    "heavy_deterministic_compute": True,
    "repository_runner_available": True,
    "persistent_capability_required": False,
}) == "github_native"

assert select_execution_surface(policy, {
    "effort": "low",
    "chat_tools_sufficient": False,
    "persistent_capability_required": True,
    "required_capability": "event_triggered_connected_app",
}) == "work"
```

Also reject a Work/Codex selection whose only reason is `effort=high`.

- [ ] **Step 9: Run focused GREEN validation**

Run:

```bash
python3 -m unittest tools.governance.test_agent_continuation_policy -v
python3 -m py_compile tools/governance/agent_continuation_policy.py tools/governance/test_agent_continuation_policy.py
```

Expected: PASS.

- [ ] **Step 10: Commit**

```bash
git add ecosystem/agent-continuation-policy.json tools/governance/agent_continuation_policy.py tools/governance/test_agent_continuation_policy.py
git commit -m "feat(governance): define persistent continuation policy"
```

---

### Task 3: Publish the human contract and bind META CI

**Files:**
- Create: `docs/agents/contracts/PERSISTENT_AUTONOMOUS_CONTINUATION_POLICY.md`
- Modify: `AGENTS.md`
- Modify: `.github/workflows/ci.yml`
- Test: `tools/governance/test_agent_continuation_policy.py`

**Interfaces:**
- Consumes: `ecosystem/agent-continuation-policy.json` and `validate_continuation_snapshot(...)` from Task 2.
- Produces: protected-META human authority that references `#69` and `#102` rather than redefining them, plus required `meta-gate` execution of the focused tests.

- [ ] **Step 1: Write contract-consistency RED tests**

Add tests that require the Markdown contract to contain these exact concepts:

```text
Chat-first, GitHub-native async, Work-by-exception
worker/session timeout != task timeout
tool timeout != task timeout
context rotation != task timeout
automatic continuation requires a real configured mechanism
```

Also require explicit references to `Oteryn/Oteryn#69` and `Oteryn/Oteryn#102`.

- [ ] **Step 2: Run tests and prove RED**

```bash
python3 -m unittest tools.governance.test_agent_continuation_policy -v
```

Expected: FAIL because the human contract and META bindings do not yet exist.

- [ ] **Step 3: Write the human contract**

Create `docs/agents/contracts/PERSISTENT_AUTONOMOUS_CONTINUATION_POLICY.md` using the approved spec. Keep the canonical bounded states/retry numbers as references only. Define:

- six coordinates;
- worker dispositions;
- executor-selection order;
- truthful resume mechanisms;
- checkpoint semantic minimum;
- context compaction/rotation;
- user-notification semantics;
- provider override rule: stricter local safety is allowed, but a local worker/invocation budget cannot silently become whole-task termination.

- [ ] **Step 4: Bind the contract from root META instructions**

Add a narrow paragraph to `AGENTS.md` after the bounded execution reference:

```text
For long-lived task continuation, agents MUST also follow docs/agents/contracts/PERSISTENT_AUTONOMOUS_CONTINUATION_POLICY.md and ecosystem/agent-continuation-policy.json. Task lifetime, worker/session lifetime, command timeout, external waiting, retry/no-progress and context pressure are separate coordinates. Chat is the default execution surface when current tools are sufficient; Work/Codex requires a capability reason. Automatic resume may be claimed only when a real configured continuation mechanism exists.
```

Do not alter the current effort-aware routing or Remote Desktop policy in this task.

- [ ] **Step 5: Bind deterministic validation into `meta-gate`**

Add to `.github/workflows/ci.yml` in the governance validation section:

```bash
python3 -m unittest tools.governance.test_agent_continuation_policy -v
python3 -m py_compile tools/governance/agent_continuation_policy.py
```

Do not remove or weaken existing checks.

- [ ] **Step 6: Run the complete applicable META validation**

Run the focused continuation suite plus the existing routing/bounded-execution suites that are present on the refreshed protected main.

Expected: all PASS. If the exact suite names changed after prerequisite merges, use the protected-main equivalents and record the exact commands.

- [ ] **Step 7: Commit**

```bash
git add docs/agents/contracts/PERSISTENT_AUTONOMOUS_CONTINUATION_POLICY.md AGENTS.md .github/workflows/ci.yml tools/governance/test_agent_continuation_policy.py
git commit -m "docs(governance): publish persistent continuation contract"
```

---

### Task 4: Qualify and merge the META continuation contract

**Files:**
- No new implementation paths unless review identifies a real defect inside the Task 2/3 owned set.

**Interfaces:**
- Consumes: exact META candidate from Tasks 2/3.
- Produces: protected-main canonical continuation policy and exact merge/readback identity.

- [ ] **Step 1: Open or update the dedicated `#108` implementation PR**

Do not reuse another lifecycle's writable branch. If PR `#109` has already merged as the design packet, create a fresh implementation branch from current protected `main`; if repository policy explicitly converts `#109` into the implementation vehicle without overlapping writers, record that decision first.

- [ ] **Step 2: Inspect the exact full diff**

Require the changed set to be limited to the Task 2/3 META paths plus any separately justified review repair.

- [ ] **Step 3: Run risk classification**

Use the current protected-main AI review classifier. Do not assume R0/R1/R2 from this plan.

- [ ] **Step 4: Freeze the exact candidate and obtain required checks/review**

No no-op/retrigger commits. Use same-head re-evaluation when external review evidence arrives after a failed gate and current canonical policy supports it.

- [ ] **Step 5: Merge only through the current protected-main authority**

If `#102` Merge Queue is canonical by this time, use it. Otherwise use the current protected repository merge path. Never weaken current protection to finish `#108`.

- [ ] **Step 6: Verify protected-main readback**

Confirm the merged contract/policy/tests exist at the resulting exact `main` SHA and applicable `meta-gate` succeeds.

---

### Task 5: Reconcile and adopt Game continuation semantics

**Prerequisite:** Task 4 protected-main readback PASS.

**Files:**
- Modify: `Oteryn/Oteryn-Game:AGENTS.md`
- Reconcile existing provider PR/Issue lineage: `Oteryn/Oteryn-Game#148`, existing stale/superseded bounded-execution PRs such as `#150` if still open.
- Test: repository-selected Agent governance / policy validation on the exact final head.

**Interfaces:**
- Consumes: exact merged META continuation policy/version and exact merged bounded-execution authority.
- Produces: Game root policy that adopts both by reference and no longer contains stale `parallel-first`, superseded `#72/#73`, or session-limit-as-task-limit semantics.

- [ ] **Step 1: Refresh Game live state and root ownership**

Verify current `main`, root `AGENTS.md`, Issue `#148`, stale provider PRs, current execution-policy adoption and any newer root-policy owner.

- [ ] **Step 2: Do not merge historical `#72/#73` provider lineage as-is**

If PR `#150` or a successor still depends on `#73`, reconcile/close/supersede it through the provider lifecycle rather than layering another root writer on top.

- [ ] **Step 3: Write the minimal root adoption**

Root instructions must state:

```text
- adopt canonical META bounded execution by current protected-main reference;
- adopt canonical META persistent continuation by current protected-main reference;
- worker/session/tool/context boundaries do not by themselves terminate the Game task;
- Chat-first executor selection applies when current tools are sufficient;
- automatic continuation requires a real configured resume mechanism;
- Game-specific merge/review/security/test requirements remain controlling.
```

- [ ] **Step 4: Run exact-head provider governance**

Use the live Game-required policy/governance gate. Runtime/E2E should be `NOT_APPLICABLE` only if the live classifier agrees that the final diff is governance-only.

- [ ] **Step 5: Merge and verify Game protected main**

Use current Game protected merge authority and record exact resulting `main` SHA.

---

### Task 6: Map continuation into Platform Control Room without a second schema

**Prerequisite:** Task 4 protected-main readback PASS and live ownership reconciliation with Platform `#1009/#1266` plus any current root-policy PR such as `#1270`.

**Files:**
- Modify: `Oteryn/Oteryn-Platform:docs/agents/EXECUTION_PROTOCOL.md`
- Modify: `Oteryn/Oteryn-Platform:docs/agents/ANTI_STALL_AND_EXECUTION_BUDGET.md`
- Modify: `Oteryn/Oteryn-Platform:docs/agents/GOVERNANCE_CONTRACT.json`
- Modify: `Oteryn/Oteryn-Platform:tools/agents/checkpoint.py`
- Modify: `Oteryn/Oteryn-Platform:tools/agents/resume.py`
- Modify only if required for rendering/classification: `Oteryn/Oteryn-Platform:tools/agents/control_room.py`
- Test: current checkpoint/resume/control-room policy suites discovered from protected `main`.

**Interfaces:**
- Consumes: META continuation semantic minimum.
- Produces: additive Platform mapping; no new Platform orchestration schema.

- [ ] **Step 1: Write failing checkpoint/resume tests**

Require additive continuation fields or derived values that represent:

```yaml
worker_disposition: continue_current | release_waiting | rotate_resumable | stop_reinvoke_required | terminal
resume_mechanism: same_session | github_native | scheduled_task | work_event_trigger | work_persistent | owner_reinvoke | none_terminal
resume_locator: <non-empty only when an automatic mechanism requires it>
context_pressure: <existing Platform classification>
```

Do not change the existing canonical task-status vocabulary merely to mirror META names.

- [ ] **Step 2: Prove RED**

Run the exact existing Platform checkpoint/resume tests plus the new cases. Expected new cases fail before implementation.

- [ ] **Step 3: Add additive contract semantics**

Extend `GOVERNANCE_CONTRACT.json` only in a backward-compatible way if the fields can be additive. If the live `#1009` schema-first owner has already moved these values to a different canonical machine surface, update that surface instead and do not duplicate it.

- [ ] **Step 4: Map Platform foreground budgets correctly**

Update `ANTI_STALL_AND_EXECUTION_BUDGET.md` to say explicitly:

```text
normal/large foreground runtime, command timeout, terminal-CI wait and context-reconstruction budgets bound one Platform invocation/worker execution. Exhausting one of those budgets may require WAITING/ROTATE/BLOCKED, but does not by itself terminate the owner-visible task.
```

Preserve all existing numeric limits unless a separate owner-approved Platform task changes them.

- [ ] **Step 5: Update checkpoint/resume implementation**

Make `checkpoint.py` and `resume.py` validate truthful resume disposition without changing existing liveness/security behavior. `rotate_resumable` must fail closed without a supported mechanism/locator; `owner_reinvoke` must not render as automatic continuation.

- [ ] **Step 6: Update Control Room only if needed**

If `control_room.py` already exposes enough checkpoint information, do not modify it. If it needs a small additive display field, add only worker disposition/resume mechanism; do not add a second scheduler.

- [ ] **Step 7: Run Platform governance validation**

Run the live exact-head Agent Governance / CI and the focused checkpoint/resume/control-room tests. Runtime/browser E2E is `NOT_APPLICABLE` only if the live classifier and repository rules agree.

- [ ] **Step 8: Merge and verify Platform protected main**

Record exact merged `main` and verify `platform-gate` plus required governance checks.

---

### Task 7: Reconcile and adopt Atlas continuation semantics

**Prerequisite:** Task 4 protected-main readback PASS.

**Files:**
- Modify: `Oteryn/Oteryn-Atlas:AGENTS.md`
- Reconcile existing provider lineage: `Oteryn/Oteryn-Atlas#176` and stale/superseded provider PRs such as `#182` if still open.
- Test: live Atlas governance/merge gates selected for the exact final diff.

**Interfaces:**
- Consumes: exact protected META continuation and bounded-execution authorities.
- Produces: Atlas root adoption without weakening exact-head/provenance/E2E/specialist execution rules.

- [ ] **Step 1: Refresh Atlas root ownership and live gate classification**

Check current `main`, root `AGENTS.md`, Issue `#176`, stale provider PRs and active Atlas verification-policy owners.

- [ ] **Step 2: Remove superseded lineage dependence**

Do not terminally merge an existing provider PR whose dependency still says `#72/#73` is canonical. Reconcile or supersede it first.

- [ ] **Step 3: Add the minimal root adoption**

State that worker/session/tool/context boundaries do not themselves terminate Atlas tasks, Chat-first selection applies when current tools suffice, automatic continuation must be real, and all Atlas verification/provenance rules remain controlling.

- [ ] **Step 4: Run the live exact-head Atlas gate**

Do not infer a heavy-E2E waiver from this plan. Follow the live Atlas classifier exactly, including any required hosted/specialist proof.

- [ ] **Step 5: Merge and verify Atlas protected main**

Record exact merged `main` and verify required Atlas gates.

---

### Task 8: Add organization drift checks and close the programme

**Prerequisite:** Tasks 4-7 protected-main readbacks PASS.

**Files:**
- Modify: `Oteryn/Oteryn:tools/governance/audit_github_readonly.py` or its current protected-main successor if that audit has been split.
- Modify: corresponding live-audit regression tests discovered on protected `main`.
- Modify only if current architecture requires: `ecosystem/governance-desired-state.json`.

**Interfaces:**
- Consumes: exact protected-main META/Game/Platform/Atlas policy identities.
- Produces: deterministic live-state drift detection for continuation adoption without arbitrary prose parsing as primary authority.

- [ ] **Step 1: Write RED live-audit fixtures**

Add provider fixtures that fail for:

```text
- stale #72/#73 canonical dependency;
- stale parallel-first / serial-exception requirement where current META is effort-aware;
- provider statement that a local foreground/session/command/context limit terminates the whole task;
- provider statement that owner_reinvoke is automatic continuation;
- provider missing the protected META continuation policy reference/version after adoption.
```

- [ ] **Step 2: Prove RED**

Run the focused live-audit regression suite. Expected new drift cases fail before implementation.

- [ ] **Step 3: Implement exact structured drift checks**

Prefer machine policy references/versions and bounded explicit markers. Do not create a broad natural-language parser that attempts to infer arbitrary continuation semantics from free-form Markdown.

- [ ] **Step 4: Run full applicable META governance tests**

Require continuation tests, existing execution-routing/provider-adoption tests, bounded-execution tests, and live-audit regressions to pass together.

- [ ] **Step 5: Qualify and merge drift enforcement**

Use current protected META merge/review authority and exact-head checks.

- [ ] **Step 6: Final live readback**

Verify:

```text
META: continuation policy canonical and green
Game: continuation adoption canonical and green
Platform: additive mapping canonical and green
Atlas: continuation adoption canonical and green
#69/#71: sole bounded lifecycle
#102/#103: sole merge/review-fingerprint lifecycle
#104/#107: no competing bounded lifecycle
#108: all scoped acceptance criteria satisfied
```

- [ ] **Step 7: Close `#108` and terminalize the delivery lifecycle**

Update Issue/PR state, branch disposition and protected-main evidence according to the current terminal branch/task lifecycle. Do not claim `DONE` until the exact protected-main readback is complete.
