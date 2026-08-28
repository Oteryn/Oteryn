# Remote Desktop Per-Action Enforcement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for this in-flight implementation. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every direct `Remote_Desktop_Commander.*` invocation fail closed unless the exact call is covered by a fresh, valid META host-exception packet.

**Architecture:** Extend the existing META routing policy with exact reason/action compatibility and a closed Remote Desktop tool set. Add a pure `validate_remote_desktop_action(...)` gate that reuses `validate_packet(...)`, bind it to canonical capability-discovery instructions, and keep a focused regression suite inside the existing protected `meta-gate`.

**Tech Stack:** JSON, Python 3.12 standard library, Markdown, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-28-remote-desktop-per-action-enforcement-design.md`

## Global Constraints

- GitHub remains the repository source of truth.
- Do not invoke Remote Desktop to implement, inspect, test or verify this change.
- Keep the exception reasons exactly `host_only_service`, `lan_or_hardware`, and `self_hosted_runner_diagnosis`.
- Every direct `Remote_Desktop_Commander.*` call is exception-only; there are no direct-call discovery exemptions.
- Out-of-band connector registration/schema inspection is outside the direct-call gate because it does not invoke Remote Desktop.
- Unknown Remote Desktop tool identifiers fail closed.
- Existing `validate_packet(...)` semantics remain authoritative for routing validity and preflight freshness.
- Do not claim connector-enforced firewalling until the external connector/router actually consumes this decision interface.
- Game rollout starts only after protected META merge and protected-main readback.
- Final exact-head SHA, review fingerprint, check/review evidence and merge evidence live in immutable GitHub PR/check/review state. Do not move a frozen candidate merely to copy those values back into this tracked plan.

## Execution adjustment

The original plan placed all new assertions in the existing `tools/governance/test_agent_execution_routing.py`. During execution that file was already over 1,000 lines, so the new per-action behavior was isolated in `tools/governance/test_remote_desktop_action_gate.py` while the old suite received only the minimum fixture update needed for the stricter packet contract. `.github/workflows/ci.yml` was therefore also added to scope so the focused suite runs under the existing protected `meta-gate`. This preserves the approved architecture and reduces regression risk without creating a new check or bypass path.

---

### Task 1: Encode exact Remote Desktop authority

**Files:**
- Modify: `ecosystem/agent-execution-routing-policy.json`
- Modify: `tools/governance/agent_execution_routing.py`
- Modify: `tools/governance/test_agent_execution_routing.py`
- Create: `tools/governance/test_remote_desktop_action_gate.py`
- Modify: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: existing `remote_desktop_reasons`, `remote_desktop_actions`, `validate_packet(...)`.
- Produces: `remote_desktop_reason_action_compatibility`, `known_remote_desktop_tools`, `always_forbidden_remote_desktop_tools`, packet field `requested_remote_desktop_tools`, and focused deterministic coverage.

- [x] **Step 1: Add RED policy/packet tests**

Focused tests require the exact reason/action mapping, a non-empty exact connector-tool declaration for host exceptions, rejection of unknown connector tools, and rejection of reason/action mismatches.

- [x] **Step 2: Prove RED through GitHub Actions**

Exact-head runs demonstrated failure before the policy/function existed; the old routing suite remained green while the new focused suite failed for the missing contract.

- [x] **Step 3: Add machine-readable policy fields**

The policy now contains exactly:

```json
"remote_desktop_reason_action_compatibility": {
  "host_only_service": ["inspect_host_only_service"],
  "lan_or_hardware": ["perform_lan_or_hardware_acceptance"],
  "self_hosted_runner_diagnosis": ["diagnose_self_hosted_runner"]
}
```

`known_remote_desktop_tools` is the closed set of currently policy-admitted connector functions. `always_forbidden_remote_desktop_tools` contains administrative/destructive functions that the three existing reasons cannot authorize. The sets are unique, Remote-Desktop-prefixed, and disjoint.

- [x] **Step 4: Fail closed on malformed policy**

`_policy_errors(...)` rejects missing/extra reason keys, empty/duplicate/unknown compatible actions, malformed tool identifiers, duplicate tool values and overlap between admitted and always-forbidden tools.

- [x] **Step 5: Tighten `validate_packet(...)`**

A host exception now requires:

```text
execution_target = host_exception
remote_desktop = exception
equivalent_ci = null
remote_desktop_reason in closed reason set
requested_host_actions = non-empty unique compatible actions
requested_remote_desktop_tools = non-empty unique subset of known_remote_desktop_tools
fresh matching github_preflight
```

A non-exception packet cannot carry requested Remote Desktop tools.

- [x] **Step 6: Preserve the old regression suite**

`exception_packet(...)` in the existing suite now declares representative exact tools:

```python
{
    "host_only_service": ["Remote_Desktop_Commander.get_config"],
    "lan_or_hardware": ["Remote_Desktop_Commander.ping"],
    "self_hosted_runner_diagnosis": ["Remote_Desktop_Commander.list_processes"],
}
```

No prior production validation was weakened.

- [x] **Step 7: Bind focused tests to the existing required gate**

`.github/workflows/ci.yml` requires the focused test file to exist and runs:

```bash
python3 tools/governance/test_agent_execution_routing.py
python3 tools/governance/test_remote_desktop_action_gate.py
```

No new status context, self-hosted route or Remote Desktop execution path is introduced.

---

### Task 2: Add the pure per-action direct-call gate

**Files:**
- Modify: `tools/governance/agent_execution_routing.py`
- Create/modify: `tools/governance/test_remote_desktop_action_gate.py`

**Interface:**

```python
def validate_remote_desktop_action(
    host_action: str,
    remote_tool: str,
    *,
    packet: dict[str, object] | None,
    live_state: dict[str, object] | None,
    policy: dict[str, object],
) -> list[str]:
    ...
```

Empty errors mean `ALLOW`; any error means `DENY`.

- [x] **Step 1: Add RED direct-call tests**

The focused suite covers direct calls such as `list_devices`, `who_am_i`, `ping`, `get_config`, `read_file`, `list_processes` and `start_process` without an exception, plus unknown tools, missing state, stale preflight, wrong semantic action and omitted exact tool.

- [x] **Step 2: Implement the minimal pure decision function**

Decision order is fail-closed:

```text
validate policy
validate host_action / remote_tool identifiers
reject always-forbidden tool
reject unknown tool
require current packet + live_state
require validate_packet(...) success
require host_exception + remote_desktop=exception
require reason/action compatibility
require exact requested_host_action
require exact requested_remote_desktop_tool
ALLOW only after all checks
```

The function performs no GitHub, filesystem, network, service, host or connector call.

- [x] **Step 3: Add malformed-identifier regression**

Self-review identified that a non-string `remote_tool` could otherwise reach a set-membership check and raise rather than return a deterministic denial. RED coverage was added for `None`, list, dict and integer identifiers before adding the explicit type/empty checks.

- [x] **Step 4: Prove GREEN after each repair**

Exact-head GitHub Actions runs demonstrated the old routing suite and the focused suite green after implementation and after the malformed-identifier fix.

---

### Task 3: Remove capability-discovery ambiguity

**Files:**
- Modify: `AGENTS.md`
- Modify: `docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md`
- Modify: `tools/governance/test_remote_desktop_action_gate.py`

- [x] **Step 1: Add RED canonical-text assertions**

The focused suite requires both canonical instruction surfaces to state:

```text
every direct `Remote_Desktop_Commander.*` invocation
local connector/tool registration
positive per-action
must not invoke `Remote_Desktop_Commander.list_devices`
A Remote Desktop `DENY` is not automatically a blocker
```

- [x] **Step 2: Prove RED before changing the Markdown**

The exact-head CI run failed only the new canonical-instruction assertion while existing routing tests remained green.

- [x] **Step 3: Update canonical capability discovery**

The contract now distinguishes:

1. local out-of-band connector/tool registration and schema inspection;
2. repository-native capability/permission discovery;
3. repository-native reads and lifecycle operations;
4. no direct `Remote_Desktop_Commander.*` capability probes;
5. a fresh validated host exception plus positive exact per-action decision before the first necessary direct call.

`list_devices`, `who_am_i`, `ping`, `get_config`, filesystem/search/process/session/terminal/history and similar calls are not discovery exemptions.

- [x] **Step 4: Preserve continuation after denial**

The root and central contract explicitly state that a Remote Desktop `DENY` is not automatically a blocker; useful authorized work continues through GitHub, GitHub Actions, repository-native connectors or isolated workspaces.

---

### Task 4: Exact-head META qualification and protected delivery

**Files:**
- Verify the complete final PR diff. Do not add implementation scope during closeout unless a concrete finding requires a repair.

**Interfaces:**
- Consumes: final PR #93 exact head.
- Produces: exact-head deterministic checks, R2/deep review evidence, protected squash merge and protected-main readback.

- [x] **Step 1: Execute TDD qualification cycles**

Verified RED/GREEN cycles include:

```text
direct-action gate absent -> RED
policy/function implemented -> GREEN after fixture reconciliation
canonical instruction contract absent -> RED
canonical instruction contract implemented -> GREEN
malformed direct-call identifier -> RED
explicit identifier validation -> GREEN
```

Every cycle ran through the repository-approved GitHub-hosted `meta-gate`; Remote Desktop was not used.

- [x] **Step 2: Mechanically classify review risk**

The repository classifier reports `R2` / reviewer class `deep` because this change touches governance, `AGENTS.md`, `.github/workflows/**` and `tools/governance/**`. The exact final head and review fingerprint must be taken from the final GitHub Actions classification for the frozen PR head, not copied back into this file.

- [x] **Step 3: Define and verify the changed-file set**

The PR must contain exactly these nine paths:

```text
.github/workflows/ci.yml
AGENTS.md
docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md
docs/superpowers/plans/2026-08-28-remote-desktop-per-action-enforcement.md
docs/superpowers/specs/2026-08-28-remote-desktop-per-action-enforcement-design.md
ecosystem/agent-execution-routing-policy.json
tools/governance/agent_execution_routing.py
tools/governance/test_agent_execution_routing.py
tools/governance/test_remote_desktop_action_gate.py
```

Exact-diff review must confirm no product runtime/deployment/secret/runner-host/live-host mutation, no new exception reason, no Remote Desktop execution path and no connector-level firewall claim.

- [ ] **Step 4: Freeze and qualify the final exact head**

After the last tracked-file change, do not update this plan again. Resolve the PR head from GitHub, require `meta-gate` PASS for exactly that head, and take the `R2` / `deep` fingerprint from the same exact-head classifier output. Record those coordinates only in GitHub PR/check/review evidence.

- [ ] **Step 5: Request exactly one primary R2/deep review for the stable fingerprint**

Only after the PR is non-draft and the exact final head has green required CI, post the canonical review request matching the current policy:

```text
@codex review
<!-- OTERYN_AI_REVIEW_REQUEST_V1 -->
REVIEW_TIER: R2
REVIEW_FINGERPRINT: <exact classifier fingerprint>
REVIEWED_HEAD: <exact final head>
REVIEWER_CLASS: deep
REVIEWER_ID: codex
```

Do not request a reviewer for an obsolete fingerprint. Any material repair creates a new head/fingerprint and requires fresh qualification under the policy.

- [ ] **Step 6: Qualify review evidence and protected checks**

Require the exact-head `meta-gate`, `ai-review-gate`, qualifying R2/deep evidence, and zero unresolved blocking review findings/threads. Do not bypass, administratively override or substitute self-review for required independent review.

- [ ] **Step 7: Protected squash merge**

Merge PR #93 only with its expected exact head and only after every required gate passes. Use squash merge and do not rewrite/force the task branch.

- [ ] **Step 8: Protected-main readback**

After merge, read protected `main` at the resulting squash SHA and verify:

```text
remote_desktop_reason_action_compatibility
known_remote_desktop_tools
always_forbidden_remote_desktop_tools
validate_remote_desktop_action(...)
requested_remote_desktop_tools enforcement
canonical direct-call instruction wording
focused test included in meta-gate
```

Do not claim external connector/router firewall enforcement.

---

### Task 5: Game adoption after META is canonical

This task is intentionally blocked until Task 4 completes.

- [ ] **Step 1: Fresh Game preflight**

Resolve protected `Oteryn/Oteryn-Game/main`, current applicable issue/PR overlap and the exact merged META SHA from GitHub.

- [ ] **Step 2: Create a separate Game branch/PR and provider plan**

Game must adopt the merged META contract by exact reference; it must not copy or fork the META machine-readable policy.

- [ ] **Step 3: Add provider prompt/governance regression binding**

Provider checks must reject reusable execution/control-plane prompts that:

```text
enumerate remote devices as ordinary capability discovery
invoke a direct Remote Desktop tool before a positive per-action gate
use Remote Desktop for routine repository tests, Git inspection or CI polling
broaden the META exception reasons
```

- [ ] **Step 4: Qualify and merge Game independently**

Use Game's current exact-head deterministic checks/review policy. Do not mutate Game runtime, deployment, secrets, runner configuration or live Remote Desktop state as part of this governance adoption.
