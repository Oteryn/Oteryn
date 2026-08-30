# Chat-first Persistent Autonomy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a thin organization continuation layer that keeps owner-visible tasks durable across worker/session/tool/context boundaries while preserving `#69/#71` bounded-execution authority, `#102/#103` merge-integration authority, provider-owned orchestration and explicit provider write-authority boundaries.

**Architecture:** META will publish one versioned continuation policy plus deterministic validation for task/session/tool/wait/retry/context separation, executor selection, truthful resume mechanisms and checkpoint semantics. Game and Atlas may adopt the minimum by reference only after explicit current-task owner authorization for that provider; Platform may map it into its existing Control Room/checkpoint model under the same authorization rule rather than creating a second schema.

**Tech Stack:** Markdown governance contracts, JSON machine policy, Python deterministic validators/tests, GitHub Actions, provider root agent instructions and existing Platform agent tooling.

**Spec:** `docs/superpowers/specs/2026-08-30-chat-first-persistent-autonomy-design.md`

## Global Constraints

- `Oteryn/Oteryn#69` / PR `#71` remains the sole bounded-autonomous-execution lifecycle authority.
- `Oteryn/Oteryn#104` / PR `#107` remains scoped to effort-aware routing, Remote Desktop exact-call binding and provider execution-policy drift; it must not establish a second bounded lifecycle.
- `Oteryn/Oteryn#102` / PR `#103` remains the sole candidate/integration-head, review-fingerprint and Merge Queue authority.
- Do not copy `RUNNING`, `WAITING_EXTERNAL`, `BLOCKED`, `STALLED`, `READY`, `DONE`, retry budgets, candidate-freeze rules or `LOOP_BREAKER_AUDIT` into a second lifecycle schema.
- Do not create a second Platform Control Room/checkpoint schema; broader Platform schema-first migration remains owned by `Oteryn/Oteryn-Platform#1009`.
- Effort and execution surface are independent; `high` effort alone must never require Work/Codex.
- Automatic continuation may be claimed only when a real configured mechanism and concrete locator exist and the locator is verified live at release/checkpoint and again at resumption.
- `rotate_resumable` is valid only with a worker-launching/preserving mechanism: `scheduled_task`, `work_event_trigger` or `work_persistent`; `same_session`, `github_native`, `owner_reinvoke` and `none_terminal` must fail closed for that disposition.
- Worker/session, command, wait or context exhaustion alone must not terminate the owner-visible task.
- Continuation must never reset canonical bounded-execution retry/evidence counters; the validator resolves the latest durable predecessor inside the trusted control-plane boundary and never accepts caller-selected predecessor history as authority.
- `release_waiting + github_native` requires authoritative remaining-work proof that no later agent-worker action exists anywhere in the remaining task, not a checkpoint-provided boolean.
- Work/Codex selection requires a capability reason plus current verified availability and authorization; an unavailable/unauthorized surface must fail closed as `BLOCKED_CAPABILITY_UNAVAILABLE`.
- Frozen candidates must not receive empty/no-op/checkpoint/retrigger commits.
- META write authority does not extend to Game, Platform or Atlas. Provider Issue/PR/design references do not confer write authority. Before any provider mutation in Tasks 5-7, the owner must explicitly authorize writes to that exact provider repository for the current task; absent authorization, only read-only preflight/reconciliation analysis is allowed.
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

Read current protected META `main`, Issues `#69`, `#104`, `#108`, `#102`, PRs `#71`, `#107`, `#110`, `#103`, their exact heads, draft/readiness state, review threads and required checks. Treat closed PR `#109` as transport-only predecessor provenance for `#110`.

Expected: no hidden successor Issue/PR has taken ownership of the same semantics.

- [ ] **Step 2: Record the approved ownership split**

Add one concise durable comment to `#108` and, if live overlap still exists, cross-reference it from `#69/#71` and `#104/#107`:

```text
OWNER-APPROVED AUTHORITY SPLIT — 2026-08-30
- #69/#71: sole bounded autonomous lifecycle / retries / freeze / LOOP_BREAKER_AUDIT
- #104/#107: effort-aware routing, Remote Desktop exact-call binding, provider execution-policy drift only
- #102/#103: candidate/integration head, review fingerprint, Merge Queue only
- #108/#110: task-vs-worker/tool/wait/retry/context continuation, executor selection, checkpoint/resume/user-notification semantics only
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
- Consumes: canonical bounded policy identity from the eventual protected-main `#69/#71` merge; current `ecosystem/agent-execution-routing-policy.json` from protected `main`; authoritative checkpoint-lineage lookup; authoritative remaining-work lookup; live resume-mechanism verification; current execution-surface capability/authorization facts.
- Produces: `load_policy(path) -> dict`, `validate_policy(policy) -> None`, `validate_continuation_snapshot(policy, snapshot, *, lineage_authority, mechanism_verifier, remaining_work_authority) -> None`, `select_execution_surface(policy, facts) -> str`; typed `ExecutionSurfaceUnavailable` for no safe execution surface.

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

Also assert that the JSON policy references, rather than duplicates, the canonical bounded policy ID and merge-integration authority, declares live verification mandatory for automatic resume locators, and declares `BLOCKED_CAPABILITY_UNAVAILABLE` as the fail-closed no-surface result.

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
  "execution_surfaces": ["chat", "github_native", "work", "codex"],
  "automatic_resume_requires_live_verification": true,
  "no_execution_surface_result": "BLOCKED_CAPABILITY_UNAVAILABLE"
}
```

Add machine-readable disposition/mechanism compatibility and the invariants for the tests below; do not copy bounded retry numbers or bounded lifecycle state definitions into this file.

- [ ] **Step 4: Implement fail-closed policy loading and validation**

In `tools/governance/agent_continuation_policy.py`, implement:

```python
class ExecutionSurfaceUnavailable(RuntimeError): ...

class CheckpointLineageAuthority(Protocol):
    def latest_predecessor(
        self,
        repository: str,
        task_id: str,
        lineage_token: str,
    ) -> dict | None: ...

    def proves_no_predecessor(
        self,
        repository: str,
        task_id: str,
        lineage_token: str,
    ) -> bool: ...

class ResumeMechanismVerifier(Protocol):
    def is_live(self, mechanism: str, locator: str) -> bool: ...

class RemainingWorkAuthority(Protocol):
    def all_remaining_work_can_complete_without_agent_worker(
        self,
        repository: str,
        task_id: str,
        lineage_token: str,
    ) -> bool: ...

def load_policy(path: Path) -> dict: ...
def validate_policy(policy: dict) -> None: ...
def validate_continuation_snapshot(
    policy: dict,
    snapshot: dict,
    *,
    lineage_authority: CheckpointLineageAuthority,
    mechanism_verifier: ResumeMechanismVerifier,
    remaining_work_authority: RemainingWorkAuthority,
) -> None: ...
def select_execution_surface(policy: dict, facts: dict) -> str: ...
```

Reject unknown schema versions, missing authority references, duplicate vocabulary values, unknown dispositions/mechanisms/surfaces, invalid disposition/mechanism pairings, missing mandatory checkpoint semantics, malformed exact-head identities, empty/multiple `next_action` values and malformed booleans/integers where the schema expects another type.

The validator MUST resolve the latest predecessor itself by calling `lineage_authority.latest_predecessor(repository, task_id, checkpoint_lineage_token)`. A raw prior snapshot, caller-selected predecessor SHA/digest, caller-provided `None`, or self-declared prior counters are never authoritative inputs. When the adapter returns no predecessor, the validator may treat the snapshot as first-generation only if `lineage_authority.proves_no_predecessor(...)` independently returns true; lookup failure, stale lineage, ambiguous lineage, or unverifiable absence fails closed. For automatic waiting/rotation mechanisms, require `mechanism_verifier` and fail closed when the locator is absent, deleted, disabled, paused, fabricated, inaccessible, or otherwise not verifiably live. For `release_waiting + github_native`, ignore/reject any caller-supplied completion boolean and require `remaining_work_authority.all_remaining_work_can_complete_without_agent_worker(...)` to prove the whole remaining task can reach a canonical terminal state without any later agent worker.

- [ ] **Step 5: Add fail-closed disposition/resume compatibility and checkpoint-minimum tests**

Test these exact failures:

```python
# rotate_resumable requires a worker-launching/preserving automatic mechanism plus non-empty locator
{"worker_disposition": "rotate_resumable", "resume_mechanism": "owner_reinvoke", "resume_locator": None}
{"worker_disposition": "rotate_resumable", "resume_mechanism": "owner_reinvoke", "resume_locator": "owner"}
{"worker_disposition": "rotate_resumable", "resume_mechanism": "same_session", "resume_locator": "current"}
{"worker_disposition": "rotate_resumable", "resume_mechanism": "github_native", "resume_locator": "workflow:ci"}

# release_waiting with a configured automatic mechanism must remain locatable
{"worker_disposition": "release_waiting", "resume_mechanism": "scheduled_task", "resume_locator": None}
{"worker_disposition": "release_waiting", "resume_mechanism": "scheduled_task", "resume_locator": ""}
{"worker_disposition": "release_waiting", "resume_mechanism": "work_event_trigger", "resume_locator": None}
{"worker_disposition": "release_waiting", "resume_mechanism": "work_event_trigger", "resume_locator": ""}
{"worker_disposition": "release_waiting", "resume_mechanism": "work_persistent", "resume_locator": None}
{"worker_disposition": "release_waiting", "resume_mechanism": "work_persistent", "resume_locator": ""}
{"worker_disposition": "release_waiting", "resume_mechanism": "github_native", "resume_locator": None}
{"worker_disposition": "release_waiting", "resume_mechanism": "github_native", "resume_locator": ""}

# terminal task cannot advertise scheduled continuation
{"worker_disposition": "terminal", "resume_mechanism": "scheduled_task", "resume_locator": "task-1"}
```

Test these exact structurally valid pairings:

```python
{"worker_disposition": "continue_current", "resume_mechanism": "same_session", "resume_locator": None}
{"worker_disposition": "release_waiting", "resume_mechanism": "github_native", "resume_locator": "merge-queue:pr-123"}
{"worker_disposition": "release_waiting", "resume_mechanism": "scheduled_task", "resume_locator": "scheduled-task:abc"}
{"worker_disposition": "release_waiting", "resume_mechanism": "work_event_trigger", "resume_locator": "work-trigger:def"}
{"worker_disposition": "release_waiting", "resume_mechanism": "work_persistent", "resume_locator": "work-task:ghi"}
{"worker_disposition": "rotate_resumable", "resume_mechanism": "scheduled_task", "resume_locator": "scheduled-task:abc"}
{"worker_disposition": "rotate_resumable", "resume_mechanism": "work_event_trigger", "resume_locator": "work-trigger:def"}
{"worker_disposition": "rotate_resumable", "resume_mechanism": "work_persistent", "resume_locator": "work-task:ghi"}
{"worker_disposition": "stop_reinvoke_required", "resume_mechanism": "owner_reinvoke", "resume_locator": None}
{"worker_disposition": "terminal", "resume_mechanism": "none_terminal", "resume_locator": None}
```

For every automatic mechanism above, validity requires a trusted verifier returning live/active for the exact locator at checkpoint/release. Add parameterized negative cases where the locator is syntactically non-empty but the verifier reports deleted, disabled, paused, unknown, inaccessible or mismatched identity. Add a positive verifier fixture for each automatic mechanism. Repeat the live verification at resumption before allowing a replacement worker to rely on it; if verification fails at either boundary, degrade to `stop_reinvoke_required`/`owner_reinvoke` and require truthful owner notification rather than preserving an automatic-resume claim.

For `release_waiting + github_native`, the snapshot MUST NOT be trusted to assert that no future worker is needed. Add a fake `RemainingWorkAuthority` and require its whole-task proof to return true; if it returns false, unknown, stale, or unavailable, fail closed to `stop_reinvoke_required` rather than claiming automatic worker continuation. For `release_waiting` paired with `scheduled_task`, `work_event_trigger`, or `work_persistent`, require the same concrete-locator and live-verification invariant as `rotate_resumable` so a purported waiting continuation can always be re-established and audited.

Build one valid baseline snapshot containing at least these always-required checkpoint fields:

```python
{
    "repository": "Oteryn/Oteryn",
    "task_id": "Oteryn/Oteryn#108",
    "checkpoint_lineage_token": "checkpoint-lineage:Oteryn/Oteryn#108",
    "task_branch": "governance/example",
    "task_head_sha": "0123456789abcdef0123456789abcdef01234567",
    "pr_applicable": True,
    "pr_id": "110",
    "phase": "qualification",
    "bounded_lifecycle_state": "RUNNING",
    "last_material_progress": "focused tests green",
    "completed_material_work": ["policy draft"],
    "validation_evidence_refs": ["check:meta-gate"],
    "blockers": [],
    "worker_disposition": "continue_current",
    "resume_mechanism": "same_session",
    "resume_locator": None,
    "next_action": "run exact-head qualification",
}
```

Parameterize deletion of every always-required field, including `checkpoint_lineage_token` and `pr_applicable`, and assert `validate_continuation_snapshot(...)` rejects the snapshot. Require `checkpoint_lineage_token` to be non-empty and bound by the authoritative adapter to the exact repository/task lineage. Require `pr_applicable` to be a real boolean in every snapshot. When `pr_applicable=true`, require a non-empty canonical `pr_id`; when `pr_applicable=false`, `pr_id` is not required and must not be fabricated. Also reject an invalid/non-40-hex `task_head_sha`, empty or non-string `next_action`, multiple next actions encoded as a list, non-list `completed_material_work`/`validation_evidence_refs`/`blockers`, and a missing/empty `pr_id` when `pr_applicable=true`. Conditionally required evidence such as first material failure, rejected hypotheses, bounded retry/evidence-generation state and context-pressure classification must be required when the corresponding condition/fact says that semantic applies; the validator must not require fabricated values when it does not apply.

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

- [ ] **Step 7: Add trusted retry-preservation tests**

Construct a fake `CheckpointLineageAuthority` whose authoritative latest predecessor contains a bounded generation and non-zero canonical retry/evidence counters. Call:

```python
validate_continuation_snapshot(
    policy,
    resumed_snapshot,
    lineage_authority=lineage_authority,
    mechanism_verifier=verifier,
    remaining_work_authority=remaining_work_authority,
)
```

Prove that worker rotation, execution-surface change or resume firing cannot reduce/reset the predecessor generation or any canonical counters resolved internally from the lineage authority. Test a caller snapshot that lowers both current and self-declared previous counters, omits self-declared previous fields entirely, names an older predecessor, supplies a fabricated predecessor digest, or uses a stale lineage token; none may change which predecessor the validator obtains from the authority. If the authority says a predecessor exists but it cannot be loaded/verified, fail closed rather than treating the resumed snapshot as first-generation. A genuinely new task may have no predecessor only when `proves_no_predecessor(...)` independently succeeds. The continuation validator compares preserved values but must not reinterpret the canonical bounded counter scopes.

- [ ] **Step 8: Add executor-selection tests**

Prove:

```python
assert select_execution_surface(policy, {
    "effort": "high",
    "chat_tools_sufficient": True,
    "heavy_deterministic_compute": False,
    "persistent_capability_required": False,
    "work_available": False,
    "work_authorized": False,
    "codex_available": False,
    "codex_authorized": False,
}) == "chat"

assert select_execution_surface(policy, {
    "effort": "medium",
    "chat_tools_sufficient": True,
    "heavy_deterministic_compute": True,
    "repository_runner_available": True,
    "persistent_capability_required": False,
    "work_available": False,
    "work_authorized": False,
    "codex_available": False,
    "codex_authorized": False,
}) == "github_native"

assert select_execution_surface(policy, {
    "effort": "low",
    "chat_tools_sufficient": False,
    "persistent_capability_required": True,
    "required_capability": "event_triggered_connected_app",
    "work_available": True,
    "work_authorized": True,
    "work_capability_reason": "event_triggered_connected_app",
    "codex_available": False,
    "codex_authorized": False,
}) == "work"
```

Also reject a Work/Codex selection whose only reason is `effort=high`. Add fail-closed cases for both ordinary exhaustion and persistent-capability exhaustion:

```python
with self.assertRaisesRegex(ExecutionSurfaceUnavailable, "BLOCKED_CAPABILITY_UNAVAILABLE"):
    select_execution_surface(policy, {
        "effort": "high",
        "chat_tools_sufficient": False,
        "heavy_deterministic_compute": True,
        "repository_runner_available": False,
        "persistent_capability_required": False,
        "work_available": False,
        "work_authorized": False,
        "codex_available": False,
        "codex_authorized": False,
        "codex_capability_reason": None,
        "work_capability_reason": None,
    })

with self.assertRaisesRegex(ExecutionSurfaceUnavailable, "BLOCKED_CAPABILITY_UNAVAILABLE"):
    select_execution_surface(policy, {
        "effort": "low",
        "chat_tools_sufficient": False,
        "persistent_capability_required": True,
        "required_capability": "event_triggered_connected_app",
        "work_available": False,
        "work_authorized": False,
        "work_capability_reason": "event_triggered_connected_app",
        "codex_available": False,
        "codex_authorized": False,
    })
```

Add equivalent negative coverage for `work_available=true/work_authorized=false`, `codex_available=false`, and `codex_available=true/codex_authorized=false` whenever the corresponding surface would otherwise be selected. Availability/authorization facts must come from current capability discovery/control-plane evidence, not from effort or the requested capability string. The selector must not invent Work/Codex availability or silently choose an unusable surface. The typed blocker is a task/control-plane fact to persist and route; it is not permission to mark the task `DONE`.

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
automatic resume locator must be live-verified at release and resumption
retry continuity resolves the latest durable predecessor inside the trusted control-plane boundary
GitHub-only release requires authoritative proof that no later agent-worker action remains
Work/Codex selection requires verified availability and authorization
rotate_resumable requires a worker-launching/preserving mechanism
no safe execution surface => BLOCKED_CAPABILITY_UNAVAILABLE
provider write authority must be explicitly authorized for the current task
```

Also require explicit references to `Oteryn/Oteryn#69` and `Oteryn/Oteryn#102`, plus a disposition/mechanism compatibility table equivalent to the approved spec.

- [ ] **Step 2: Run tests and prove RED**

```bash
python3 -m unittest tools.governance.test_agent_continuation_policy -v
```

Expected: FAIL because the human contract and META bindings do not yet exist.

- [ ] **Step 3: Write the human contract**

Create `docs/agents/contracts/PERSISTENT_AUTONOMOUS_CONTINUATION_POLICY.md` using the approved spec. Keep the canonical bounded states/retry numbers as references only. Define:

- six coordinates;
- worker dispositions;
- executor-selection order, verified Work/Codex capability availability/authorization, and the typed fail-closed no-surface result;
- truthful resume mechanisms, live locator verification at release and resumption, and the fail-closed disposition/mechanism compatibility matrix;
- checkpoint semantic minimum and internal authoritative predecessor-lineage resolution for canonical bounded counters/generations;
- authoritative whole-task remaining-work proof before `release_waiting + github_native`;
- context compaction/rotation;
- user-notification semantics;
- provider write-authority boundary: META coordination/design/provider Issue references never authorize provider mutation; explicit current-task owner authorization for the exact provider is required;
- provider override rule: stricter local safety is allowed, but a local worker/invocation budget cannot silently become whole-task termination.

- [ ] **Step 4: Bind the contract from root META instructions**

Add a narrow paragraph to `AGENTS.md` after the bounded execution reference:

```text
For long-lived task continuation, agents MUST also follow docs/agents/contracts/PERSISTENT_AUTONOMOUS_CONTINUATION_POLICY.md and ecosystem/agent-continuation-policy.json. Task lifetime, worker/session lifetime, command timeout, external waiting, retry/no-progress and context pressure are separate coordinates. Chat is the default execution surface when current tools are sufficient; Work/Codex requires a capability reason plus current verified availability/authorization. Automatic resume may be claimed only when a real configured continuation mechanism exists and its locator is live-verified. Cross-repository provider writes remain separately authorized per the existing META authority boundary.
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

- [ ] **Step 1: Open the dedicated `#108` implementation PR after the design packet is terminal**

Do not reuse another lifecycle's writable branch. PR `#110` is the design/plan vehicle (with `#109` only its closed transport predecessor); after it is terminally merged/closed according to live policy and Task 1 prerequisites are satisfied, create a fresh implementation branch from current protected `main`. Do not silently convert the reviewed design branch into a canonical implementation writer.

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

**Prerequisite:** Task 4 protected-main readback PASS. Read-only Game preflight is permitted from the META task, but **no Game mutation may begin until the owner explicitly authorizes writes to `Oteryn/Oteryn-Game` for the current adoption task**. Issue `Oteryn/Oteryn-Game#148`, existing PRs, META design text and tool access do not satisfy this authorization gate.

**Files:**
- Modify only after authorization: `Oteryn/Oteryn-Game:AGENTS.md`
- Reconcile existing provider PR/Issue lineage: `Oteryn/Oteryn-Game#148`, existing stale/superseded bounded-execution PRs such as `#150` if still open.
- Test: repository-selected Agent governance / policy validation on the exact final head.

**Interfaces:**
- Consumes: exact merged META continuation policy/version, exact merged bounded-execution authority, and explicit current-task Game write authorization.
- Produces: Game root policy that adopts both by reference and no longer contains stale `parallel-first`, superseded `#72/#73`, or session-limit-as-task-limit semantics.

- [ ] **Step 1: Refresh Game live state and verify the authorization gate**

Verify current `main`, root `AGENTS.md`, Issue `#148`, stale provider PRs, current execution-policy adoption and any newer root-policy owner. Separately verify explicit owner authorization naming `Oteryn/Oteryn-Game` for this current adoption task before creating/updating branches, files, commits, PRs or other provider state.

Expected if authorization is absent: record `OWNER_PERMISSION_REQUIRED` for provider mutation, preserve read-only findings, perform no Game write and do not infer authority from `#148` or META.

- [ ] **Step 2: Do not merge historical `#72/#73` provider lineage as-is**

If PR `#150` or a successor still depends on `#73`, reconcile/close/supersede it through the provider lifecycle only after the provider write-authorization gate is satisfied; otherwise leave provider state read-only and record the required action.

- [ ] **Step 3: Write the minimal root adoption**

After authorization, root instructions must state:

```text
- adopt canonical META bounded execution by current protected-main reference;
- adopt canonical META persistent continuation by current protected-main reference;
- worker/session/tool/context boundaries do not by themselves terminate the Game task;
- Chat-first executor selection applies when current tools are sufficient;
- automatic continuation requires a real configured and live-verifiable resume mechanism;
- Game-specific merge/review/security/test requirements remain controlling.
```

- [ ] **Step 4: Run exact-head provider governance**

Use the live Game-required policy/governance gate. Runtime/E2E should be `NOT_APPLICABLE` only if the live classifier agrees that the final diff is governance-only.

- [ ] **Step 5: Merge and verify Game protected main**

Use current Game protected merge authority and record exact resulting `main` SHA.

---

### Task 6: Map continuation into Platform Control Room without a second schema

**Prerequisite:** Task 4 protected-main readback PASS and live ownership reconciliation with Platform `#1009/#1266` plus any current root-policy PR such as `#1270`. Read-only Platform preflight is permitted from the META task, but **no Platform mutation may begin until the owner explicitly authorizes writes to `Oteryn/Oteryn-Platform` for the current adoption task**. Provider Issues/PRs and META references do not satisfy this gate.

**Files:**
- Modify only after authorization: `Oteryn/Oteryn-Platform:docs/agents/EXECUTION_PROTOCOL.md`
- Modify only after authorization: `Oteryn/Oteryn-Platform:docs/agents/ANTI_STALL_AND_EXECUTION_BUDGET.md`
- Modify only after authorization: `Oteryn/Oteryn-Platform:docs/agents/GOVERNANCE_CONTRACT.json`
- Modify only after authorization: `Oteryn/Oteryn-Platform:tools/agents/checkpoint.py`
- Modify only after authorization: `Oteryn/Oteryn-Platform:tools/agents/resume.py`
- Modify only if required for rendering/classification and authorized: `Oteryn/Oteryn-Platform:tools/agents/control_room.py`
- Test: current checkpoint/resume/control-room policy suites discovered from protected `main`.

**Interfaces:**
- Consumes: META continuation semantic minimum and explicit current-task Platform write authorization.
- Produces: additive Platform mapping; no new Platform orchestration schema.

- [ ] **Step 1: Refresh Platform live state and verify the authorization gate**

Verify current `main`, the live `#1009/#1266` ownership surfaces, active root-policy PRs and exact checkpoint/resume schema owner. Separately verify explicit owner authorization naming `Oteryn/Oteryn-Platform` for this current adoption task before any provider mutation.

Expected if authorization is absent: record `OWNER_PERMISSION_REQUIRED`, preserve read-only reconciliation findings and perform no Platform write.

- [ ] **Step 2: Write failing checkpoint/resume tests**

After authorization, require additive continuation fields or derived values that represent:

```yaml
worker_disposition: continue_current | release_waiting | rotate_resumable | stop_reinvoke_required | terminal
resume_mechanism: same_session | github_native | scheduled_task | work_event_trigger | work_persistent | owner_reinvoke | none_terminal
resume_locator: <required for every configured automatic waiting/rotation continuation; otherwise per compatibility matrix>
context_pressure: <existing Platform classification>
```

Do not change the existing canonical task-status vocabulary merely to mirror META names. Require the same fail-closed compatibility matrix as META, including rejection of `rotate_resumable + same_session` and `rotate_resumable + github_native`, plus missing/empty or non-live locators for automatic `release_waiting` continuations.

- [ ] **Step 3: Prove RED**

Run the exact existing Platform checkpoint/resume tests plus the new cases. Expected new cases fail before implementation.

- [ ] **Step 4: Add additive contract semantics**

Extend `GOVERNANCE_CONTRACT.json` only in a backward-compatible way if the fields can be additive. If the live `#1009` schema-first owner has already moved these values to a different canonical machine surface, update that surface instead and do not duplicate it.

- [ ] **Step 5: Map Platform foreground budgets correctly**

Update `ANTI_STALL_AND_EXECUTION_BUDGET.md` to say explicitly:

```text
normal/large foreground runtime, command timeout, terminal-CI wait and context-reconstruction budgets bound one Platform invocation/worker execution. Exhausting one of those budgets may require WAITING/ROTATE/BLOCKED, but does not by itself terminate the owner-visible task.
```

Preserve all existing numeric limits unless a separate owner-approved Platform task changes them.

- [ ] **Step 6: Update checkpoint/resume implementation**

Make `checkpoint.py` and `resume.py` validate truthful resume disposition without changing existing liveness/security behavior. `rotate_resumable` must fail closed unless its mechanism is exactly `scheduled_task`, `work_event_trigger` or `work_persistent` with the required concrete locator; `same_session` and `github_native` must not qualify rotation. Automatic `release_waiting` mechanisms must also carry a concrete locator verified live at release and again at resumption. `owner_reinvoke` must not render as automatic continuation. Bounded retry/generation continuity must be resolved from Platform's authoritative latest checkpoint/control-plane lineage inside the trusted resume boundary, never from caller-supplied predecessor state. Platform must likewise derive any GitHub-only no-later-worker decision from its authoritative task/next-action state rather than trusting a checkpoint boolean.

- [ ] **Step 7: Update Control Room only if needed**

If `control_room.py` already exposes enough checkpoint information, do not modify it. If it needs a small additive display field, add only worker disposition/resume mechanism; do not add a second scheduler.

- [ ] **Step 8: Run Platform governance validation**

Run the live exact-head Agent Governance / CI and the focused checkpoint/resume/control-room tests. Runtime/browser E2E is `NOT_APPLICABLE` only if the live classifier and repository rules agree.

- [ ] **Step 9: Merge and verify Platform protected main**

Record exact merged `main` and verify `platform-gate` plus required governance checks.

---

### Task 7: Reconcile and adopt Atlas continuation semantics

**Prerequisite:** Task 4 protected-main readback PASS. Read-only Atlas preflight is permitted from the META task, but **no Atlas mutation may begin until the owner explicitly authorizes writes to `Oteryn/Oteryn-Atlas` for the current adoption task**. Issue `Oteryn/Oteryn-Atlas#176`, existing PRs, META design text and tool access do not satisfy this authorization gate.

**Files:**
- Modify only after authorization: `Oteryn/Oteryn-Atlas:AGENTS.md`
- Reconcile existing provider lineage: `Oteryn/Oteryn-Atlas#176` and stale/superseded provider PRs such as `#182` if still open.
- Test: live Atlas governance/merge gates selected for the exact final diff.

**Interfaces:**
- Consumes: exact protected META continuation and bounded-execution authorities, plus explicit current-task Atlas write authorization.
- Produces: Atlas root adoption without weakening exact-head/provenance/E2E/specialist execution rules.

- [ ] **Step 1: Refresh Atlas root ownership, gate classification and authorization**

Check current `main`, root `AGENTS.md`, Issue `#176`, stale provider PRs and active Atlas verification-policy owners. Separately verify explicit owner authorization naming `Oteryn/Oteryn-Atlas` for this current adoption task before any provider mutation.

Expected if authorization is absent: record `OWNER_PERMISSION_REQUIRED`, preserve read-only findings and perform no Atlas write.

- [ ] **Step 2: Remove superseded lineage dependence**

After authorization, do not terminally merge an existing provider PR whose dependency still says `#72/#73` is canonical. Reconcile or supersede it first.

- [ ] **Step 3: Add the minimal root adoption**

After authorization, state that worker/session/tool/context boundaries do not themselves terminate Atlas tasks, Chat-first selection applies when current tools suffice, automatic continuation must use a real configured and live-verifiable mechanism, and all Atlas verification/provenance rules remain controlling.

- [ ] **Step 4: Run the live exact-head Atlas gate**

Do not infer a heavy-E2E waiver from this plan. Follow the live Atlas classifier exactly, including any required hosted/specialist proof.

- [ ] **Step 5: Merge and verify Atlas protected main**

Record exact merged `main` and verify required Atlas gates.

---

### Task 8: Add organization drift checks and close the programme

**Prerequisite:** Task 4 protected-main readback PASS. For each provider task in Tasks 5-7, require either (a) its protected-main adoption readback PASS, or (b) an explicit owner decision reducing `#108` final scope by deferring/excluding that provider. Absence of provider write authorization by itself is **not** an implicit scope reduction and must remain `OWNER_PERMISSION_REQUIRED` until the owner records a scope decision.

**Files:**
- Modify: `Oteryn/Oteryn:tools/governance/audit_github_readonly.py` or its current protected-main successor if that audit has been split.
- Modify: corresponding live-audit regression tests discovered on protected `main`.
- Modify only if current architecture requires: `ecosystem/governance-desired-state.json`.

**Interfaces:**
- Consumes: exact protected-main META identity plus exact protected-main identities for every provider that remains in the final `#108` scope, and the durable owner scope-reduction record for each excluded provider.
- Produces: deterministic live-state drift detection for in-scope continuation adoption without arbitrary prose parsing as primary authority, plus terminal evidence that distinguishes adopted providers from explicitly deferred/excluded providers.

- [ ] **Step 1: Write RED live-audit fixtures**

Add continuation-owned provider fixtures that fail for:

```text
- stale #72/#73 canonical dependency in the continuation-adoption reference;
- provider statement that a local foreground/session/command/context limit terminates the whole task;
- provider statement that owner_reinvoke is automatic continuation;
- provider statement that same_session or github_native alone qualifies rotate_resumable;
- provider missing the protected META continuation policy reference/version after adoption.
```

Execution-routing/provider-policy drift such as stale `parallel-first` / serial-exception requirements remains owned by `#104/#107`; do **not** add a duplicate Task 8 RED fixture for that behavior. Run the existing `#107` provider-drift tests only as regression coverage so this task proves coexistence without absorbing that authority.

Do not attempt to persist ephemeral per-task provider write authorization in desired-state policy; authorization must instead be verified at the provider mutation boundary by the executing task. Do not flag an explicitly owner-excluded provider for missing continuation adoption; verify the durable scope-reduction record instead.

- [ ] **Step 2: Prove RED**

Run the focused continuation-owned live-audit regression suite. Expected new continuation drift cases fail before implementation. Existing `#107` execution-policy drift tests are regression-only here and are expected to retain their current canonical behavior rather than become new RED cases for `#108`.

- [ ] **Step 3: Implement exact structured drift checks**

Prefer machine policy references/versions and bounded explicit markers. Do not create a broad natural-language parser that attempts to infer arbitrary continuation semantics from free-form Markdown. Apply adoption drift checks only to providers still in final scope; excluded providers require exact durable scope-decision evidence rather than synthetic adoption state.

- [ ] **Step 4: Run full applicable META governance tests**

Require continuation tests, existing `#107` execution-routing/provider-drift regressions, bounded-execution tests, and live-audit regressions to pass together. Passing another lifecycle's regression suite confirms non-regression only; it does not transfer its ownership into `#108`.

- [ ] **Step 5: Qualify and merge drift enforcement**

Use current protected META merge/review authority and exact-head checks.

- [ ] **Step 6: Final live readback**

Verify:

```text
META: continuation policy canonical and green
For each provider still IN_SCOPE: continuation adoption/mapping canonical and green at exact protected-main SHA
For each provider OUT_OF_SCOPE: explicit owner scope-reduction/defer decision recorded; no provider mutation or adoption is claimed
#69/#71: sole bounded lifecycle
#102/#103: sole merge/review-fingerprint lifecycle
#104/#107: no competing bounded lifecycle
#108: all remaining scoped acceptance criteria satisfied
```

- [ ] **Step 7: Close `#108` and terminalize the delivery lifecycle**

Update Issue/PR state, branch disposition and protected-main evidence according to the current terminal branch/task lifecycle. Do not claim `DONE` until the exact protected-main readback is complete and every provider is accounted for as either protected-main adopted or explicitly removed/deferred by owner scope decision.