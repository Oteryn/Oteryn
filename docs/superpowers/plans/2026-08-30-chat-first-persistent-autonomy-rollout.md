# Chat-first Persistent Autonomy Implementation Plan

**Goal:** deliver the smallest deterministic continuation layer for `Oteryn/Oteryn#108` while preserving the bounded lifecycle, ADR 0005 GitHub-native integration model and provider ownership.

**Spec:** `docs/superpowers/specs/2026-08-30-chat-first-persistent-autonomy-design.md`

## Global constraints

- GitHub live state is authoritative; refresh before every material mutation/integration decision.
- Current protected-main `AGENTS.md` and ADR 0005 outrank historical plan text.
- The bounded lifecycle from `#69` is referenced, not copied. Under the current bounded contract `STALLED` is a released **nonterminal** state; only the bounded authority may declare terminality, and currently only `DONE` is terminal.
- `#107` may own routing/RDC/provider convergence only; no second bounded lifecycle.
- GitHub protected branch + aggregate gate + Merge Queue own integration enforcement.
- Do not recreate retired R0/R1/R2, review-fingerprint, `ai-review-gate`, attestation, outbox, custom merge-proof or `LOOP_BREAKER_AUDIT` machinery.
- One writer per branch/lane. Parallelize only independent repositories/read-only review.
- No no-op/checkpoint/retrigger commits.
- Provider writes require explicit owner authorization for the exact provider repository and current adoption task.
- No product runtime, production, secret, credential or live-data mutation is part of this rollout.
- Canonical implementation must use a fresh branch from then-current protected `main`; the design branch never becomes the implementation writer.

---

## Phase 0 — Terminalize prerequisites

### 0.1 Refresh live authority

Read:

- protected META `main` + `AGENTS.md` + ADR 0005;
- `#69` bounded survivor and its current delivery state;
- `#104/#107`;
- `#108/#110`;
- current required `meta-gate`, review threads and Merge Queue enforcement.

### 0.2 Bounded prerequisite

Require the surviving bounded contract to be canonical on protected main before the continuation implementation branch is created.

Do not copy a PR-only bounded implementation into the continuation branch.

### 0.3 Reconcile `#107`

After the bounded survivor is canonical:

- reconcile `#107` with current protected main;
- retain only effort-aware routing, Remote Desktop exception/exact-call binding and provider execution-policy convergence;
- delete/revert any duplicate bounded lifecycle, old review gate, outbox/attestation or retired ADR0005 machinery from its final diff;
- run its deterministic tests and required exact-head `meta-gate`;
- resolve all material review findings;
- integrate through current Merge Queue rules.

### 0.4 Terminalize design packet

Reconcile `#110` against current protected main. Final #110 must be documentation-only and describe the ADR0005-compatible continuation model. Run `meta-gate`, inspect exact diff/threads and integrate through Merge Queue.

---

## Phase 1 — Create the fresh #108 implementation branch

After Phase 0 is terminal:

1. refresh protected `main` and verify its exact SHA;
2. create one dedicated branch from that exact SHA;
3. open one PR tracking `#108`;
4. record the exact initial base/head and narrow intended paths.

Initial intended files:

```text
ecosystem/agent-continuation-policy.json
tools/governance/agent_continuation_policy.py
tools/governance/test_agent_continuation_policy.py
docs/agents/contracts/PERSISTENT_AUTONOMOUS_CONTINUATION_POLICY.md
AGENTS.md
.github/workflows/ci.yml
tools/governance/test_merge_queue_workflow_contract.py   # only if needed to prove CI wiring
```

Do not broaden scope unless a failing regression proves the need.

---

## Phase 2 — Machine policy with strict TDD

### 2.1 RED: policy/schema does not exist

Create focused tests first. They require closed vocabularies:

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

The machine policy must include:

- `policy_id = oteryn-agent-continuation-v1`;
- continuation authority `Oteryn/Oteryn#108`;
- reference to the current bounded execution authority from protected main;
- six independent coordinates: task, worker/session, tool/command, external wait, retry/no-progress, context pressure;
- the closed vocabularies above;
- fail-closed disposition/mechanism compatibility;
- automatic-resume release verification + task binding requirements;
- execution-surface capability mapping;
- no-safe-surface result `BLOCKED_CAPABILITY_UNAVAILABLE`.

Do not embed bounded retry counts or bounded lifecycle definitions in this JSON.

Prove RED before implementation.

### 2.2 Minimal implementation

Implement in `agent_continuation_policy.py` only the APIs needed to enforce the design:

```python
@dataclass(frozen=True)
class StableTaskLineageKey:
    repository: str
    task_id: str
    checkpoint_lineage_token: str

@dataclass(frozen=True)
class TrustedTaskIdentity:
    lineage_key: StableTaskLineageKey
    task_branch: str
    pr_applicable: bool
    pr_id: str | None
    task_head_sha: str
    expected_next_action: str

@dataclass(frozen=True)
class TrustedCapabilitySnapshot:
    observed_at: str
    required_capability: str | None
    compatible_surfaces: tuple[str, ...]
    available_surfaces: tuple[str, ...]
    authorized_surfaces: tuple[str, ...]
    safe_fallbacks_exhausted: bool
    evidence_refs: tuple[str, ...]

class CheckpointLineageAuthority(Protocol): ...
class CheckpointTransitionAuthority(Protocol): ...
class BoundedLifecycleAuthority(Protocol): ...
class ResumeMechanismVerifier(Protocol): ...
class RemainingWorkAuthority(Protocol): ...
class ExecutionCapabilityAuthority(Protocol):
    def current_snapshot(
        self,
        trusted_task: TrustedTaskIdentity,
        required_capability: str | None,
    ) -> TrustedCapabilitySnapshot: ...

class ExecutionSurfaceUnavailable(RuntimeError): ...

def load_policy(path: Path) -> dict: ...
def validate_policy(policy: dict) -> None: ...
def validate_continuation_snapshot(..., validation_mode: str) -> None: ...
def select_execution_surface(
    policy: dict,
    *,
    trusted_task: TrustedTaskIdentity,
    required_capability: str | None,
    capability_authority: ExecutionCapabilityAuthority,
) -> str: ...
```

`TrustedCapabilitySnapshot` is produced by the trusted authority from current-session/control-plane evidence. The caller cannot manufacture support/availability/authorization booleans and pass them as selection authority. Unknown/stale/unverifiable discovery fails closed. `BLOCKED_CAPABILITY_UNAVAILABLE` is valid only when the authority has evaluated the safe compatible fallback set and reports it exhausted.

Interfaces are trust boundaries, not permission to duplicate provider/control-plane storage.

### 2.3 GREEN

Run the focused suite and require deterministic PASS before expanding tests.

---

## Phase 3 — Continuation safety regressions

Add one failing regression at a time, then implement the smallest fix.

Required invariants:

### Stable lineage

- predecessor/no-predecessor lookup uses only `repository + task_id + checkpoint_lineage_token`;
- snapshot cannot self-select trusted task identity;
- branch/PR/head/next action may advance without changing lineage;
- immutable lineage mismatch fails closed.

### Checkpoint semantic minimum

Define one baseline valid checkpoint fixture containing at least:

```text
repository
task_id
checkpoint_lineage_token
task_branch
pr_applicable
pr_id                         # required iff pr_applicable=true
task_head_sha
phase
bounded_lifecycle_state
last_material_progress
completed_work
evidence_refs
bounded_continuity_ref
blockers
context_pressure              # may be null only when genuinely not relevant
worker_disposition
resume_mechanism
resume_locator                # required for mechanisms that require a locator
next_action
```

Before implementation, add parameterized RED tests that delete **each** always-required field one at a time and require rejection. Add malformed/type-shape tests proving at minimum:

- repository/task/lineage/branch/phase/lifecycle/next-action are non-empty strings;
- `pr_applicable` is an exact JSON/Python boolean, never an integer alias;
- `pr_id` is non-empty exactly when `pr_applicable=true`, and must not be fabricated for a non-PR checkpoint;
- `task_head_sha` is an exact lowercase 40-hex SHA;
- completed work, evidence references and blockers use deterministic list/tuple shapes with valid members;
- bounded continuity reference is present and non-empty but its internal retry schema remains owned by `#69`;
- exactly one concrete `next_action` exists;
- locator-dependent mechanisms reject missing/empty locators;
- context-pressure shape is validated when present and cannot invent an exact runtime token count the platform does not expose.

The same semantic-minimum validation applies to `checkpoint_write` and to authenticated historical checkpoints during `resume_read`.

### Checkpoint write

- latest predecessor is resolved by trusted lineage;
- missing predecessor is accepted only when the lineage authority independently proves none exists;
- first continuation checkpoint must match already-consumed current bounded state;
- existing predecessor continuity is delegated to bounded lifecycle authority;
- mutable checkpoint coordinates must match current `TrustedTaskIdentity`;
- semantic-minimum fields and conditional fields must already be valid before a release/rotation checkpoint is persisted;
- unknown/unavailable bounded authority fails closed.

### Resume read

- historical checkpoint integrity and semantic-minimum shape are verified before reconciliation;
- historical mutable coordinates are not rewritten to look current;
- automatic resume authenticates the actual historical mechanism/locator/event;
- owner re-invocation uses owner-authorized re-entry evidence, never fabricated automatic-event evidence;
- a trusted transition authority reconciles historical state to fresh GitHub/task context;
- a consumed one-shot mechanism need not remain live after firing;
- a successor checkpoint claiming future automatic resume must freshly verify that new mechanism.

### Disposition/mechanism matrix

- `continue_current` ↔ `same_session`;
- `rotate_resumable` ↔ only `scheduled_task|work_event_trigger|work_persistent` with non-empty verified locator;
- `stop_reinvoke_required` ↔ `owner_reinvoke`;
- `terminal` ↔ `none_terminal` plus independent bounded terminal state;
- under the current `#69` contract, `STALLED` + `terminal|none_terminal` is rejected because `STALLED` is released but nonterminal; only the bounded authority may report terminality;
- invalid pairings fail closed.

### GitHub-native waiting

`release_waiting + github_native` requires:

- concrete GitHub workflow/queue/control-plane locator;
- authoritative proof, before release, that all remaining task work can reach terminal state without any later agent worker.

If later worker action may be required, fail closed to a worker-capable mechanism or `stop_reinvoke_required`.

### Bounded continuity

Worker/session/context/surface changes must never reset or enlarge bounded retry/evidence state. The continuation layer delegates this decision to the bounded lifecycle authority.

### Execution surface

All selector tests obtain capability facts through `ExecutionCapabilityAuthority`; raw caller dictionaries are not accepted as authority.

Required RED/GREEN coverage:

- Chat is selected when current trusted capability evidence proves it can safely perform the required work;
- GitHub-native is preferred for deterministic compute/waiting when compatible and available;
- Work is selected only when the required capability is Work-compatible **and** current trusted evidence proves Work available and authorized;
- Codex is selected only for its compatible software-development capability case with current availability/authorization evidence;
- a surface that is available/authorized but incompatible with the required capability is rejected;
- stale, self-asserted, empty or unverifiable capability evidence is rejected;
- an unavailable/unauthorized preferred surface must cause evaluation of every safe compatible fallback before blocker classification;
- `BLOCKED_CAPABILITY_UNAVAILABLE` is raised/returned only when trusted evidence proves the safe compatible fallback set is exhausted.

Run focused tests after every material fix, then the full continuation suite.

---

## Phase 4 — Human contract and required-gate wiring

Create `PERSISTENT_AUTONOMOUS_CONTINUATION_POLICY.md` describing the same semantics in human-readable form.

Update `AGENTS.md` only with the minimum pointer/requirements needed to make the continuation contract discoverable.

Wire the continuation regression suite into the existing required `meta-gate`.

Add/extend a deterministic CI-contract regression that proves `meta-gate` actually invokes `test_agent_continuation_policy.py`. This prevents a false green where tests exist but are not executed.

TDD order for wiring:

1. contract test fails because CI does not invoke continuation tests;
2. add the invocation;
3. hosted `meta-gate` proves GREEN.

Do not create a second required status.

---

## Phase 5 — META qualification and integration

On one stable material candidate:

1. refresh protected main and PR exact head;
2. confirm intended changed-file set only;
3. inspect full exact diff;
4. run required exact-head `meta-gate` and confirm the continuation tests actually executed;
5. run broader governance regression suite where applicable;
6. inspect all review threads/comments;
7. use optional external AI review only if current `AGENTS.md` says its independent value justifies the cost; it remains advisory;
8. repair material findings with strict TDD;
9. require zero unresolved material threads;
10. integrate through current GitHub Merge Queue/protected-branch rules;
11. read back protected main and confirm the merged policy/contract exact state.

Do not chase moving main with no-op/retrigger commits.

---

## Phase 6 — Provider adoption

Provider work may proceed independently only after META continuation is canonical and only with explicit current-task write authorization for that exact provider.

### Game

Read-only preflight first. If authorized, add the minimum provider reference/adoption compatible with Game's existing controls and required `game-gate`.

### Platform

Read-only preflight first. If authorized, map organization continuation semantics into the existing Control Room/checkpoint/anti-stall model. Do not create a second Platform checkpoint schema or orchestration database.

### Atlas

Read-only preflight first. If authorized, add the minimum provider reference/adoption compatible with Atlas's existing controls and required `atlas-gate`.

Each provider lane owns its own branch/PR and may run in parallel with other provider lanes when there are no shared writable surfaces.

Absent exact provider authorization:

- do not mutate;
- record `OWNER_PERMISSION_REQUIRED` in the programme evidence;
- continue other authorized lanes.

Missing authorization is not implicit final defer.

A final provider defer/exclusion is valid only through this GitHub-authoritative record on `Oteryn/Oteryn#108` (or a canonical successor Issue explicitly named by `#108`):

```text
OTERYN_PROVIDER_SCOPE_DECISION_V1
provider_repository: Oteryn/<exact-provider-repo>
adoption_task: <exact current provider adoption Issue/task locator>
decision: DEFER|EXCLUDE
reason: <non-empty owner rationale>
meta_main_sha: <current protected META main SHA>
provider_main_sha: <current protected/default provider main SHA>
```

The decision comment is a durable locator, not self-authenticating authority. At closeout the coordinator must re-read that exact GitHub comment and verify its author currently has repository-admin/owner authority for the scoped decision, the provider/adoption-task coordinates still match live state, the recorded repository identities/SHA context remain coherent provenance, and no later owner decision supersedes it. Unknown permission, generic/stale handoffs, missing fields or a decision for a different provider/task fail closed.

---

## Phase 7 — Final drift and closeout

Refresh live GitHub state for META, Game, Platform and Atlas.

For every in-scope repository verify:

- expected protected-main adoption state;
- current required aggregate gate and relevant branch enforcement;
- no duplicate/competing continuation lifecycle;
- provider-local stronger controls were preserved;
- no retired ADR0005 machinery was reintroduced by this rollout.

For every provider not adopted, validate the `OTERYN_PROVIDER_SCOPE_DECISION_V1` record fail-closed:

1. fetch the exact comment from canonical `#108`/successor Issue;
2. verify marker and all required fields;
3. verify the author currently has admin/owner authority sufficient for the scope decision;
4. verify exact provider repository and current adoption-task binding;
5. refresh current META/provider main and confirm the record is provenance for the intended repository/task rather than a stale generic decision;
6. search later owner decisions for the same provider/task and reject a superseded record;
7. classify unknown/unverifiable proof as `OWNER_PERMISSION_REQUIRED`/not-terminal, never as an implicit defer.

Terminal programme result requires:

- META implementation merged and read back from protected main;
- each provider either merged/read back or has a currently verified GitHub-authoritative defer/exclusion record as defined above;
- all required checks/threads/queue integration terminal;
- no unaccounted writer/PR remains for the same continuation authority.

Only then close `#108` as complete and dispose of task branches according to current repository policy.