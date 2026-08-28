# Remote Desktop Per-Action Enforcement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every direct `Remote_Desktop_Commander.*` invocation fail closed unless the exact call is covered by a fresh, valid META host-exception packet.

**Architecture:** Extend the existing execution-routing policy with explicit reason/action compatibility and a closed set of known Remote Desktop tool identifiers, then add a pure `validate_remote_desktop_action(...)` decision function that reuses `validate_packet(...)`. Clarify capability discovery so only out-of-band tool-schema inspection is allowed without an exception; direct connector calls remain exception-only.

**Tech Stack:** JSON, Python 3.12 standard library, Markdown, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-28-remote-desktop-per-action-enforcement-design.md`

## Global Constraints

- GitHub is the repository source of truth; no Remote Desktop host is used to implement or validate this change.
- Keep the existing exception reasons exactly `host_only_service`, `lan_or_hardware`, and `self_hosted_runner_diagnosis`.
- Every direct `Remote_Desktop_Commander.*` call is exception-only; there are no direct-call discovery exemptions.
- Unknown connector tool identifiers fail closed.
- `connector_schema_discovery` means local registry/schema inspection without invoking any Remote Desktop function.
- Existing `validate_packet(...)` semantics remain authoritative for routing packet validity and fresh GitHub preflight.
- The implementation must not claim connector-enforced firewalling; it provides repository-enforced policy and a mandatory decision interface for future connector/router integration.
- Provider rollout starts only after this META change is protected-merged and read back from `main`.

---

### Task 1: Make the machine-readable policy express exact Remote Desktop authority

**Files:**
- Modify: `ecosystem/agent-execution-routing-policy.json`
- Modify: `tools/governance/test_agent_execution_routing.py`

**Interfaces:**
- Consumes: existing `remote_desktop_reasons`, `remote_desktop_actions`, `validate_packet(...)`.
- Produces: `remote_desktop_reason_action_compatibility`, `known_remote_desktop_tools`, `always_forbidden_remote_desktop_tools`, and packet field `requested_remote_desktop_tools`.

- [ ] **Step 1: Add failing policy-shape and packet tests**

Add deterministic tests asserting the canonical mapping and fail-closed tool declarations:

```python
def test_remote_desktop_policy_has_exact_reason_action_mapping() -> None:
    current = policy()
    assert current["remote_desktop_reason_action_compatibility"] == {
        "host_only_service": ["inspect_host_only_service"],
        "lan_or_hardware": ["perform_lan_or_hardware_acceptance"],
        "self_hosted_runner_diagnosis": ["diagnose_self_hosted_runner"],
    }


def test_remote_desktop_exception_requires_exact_remote_tool_set() -> None:
    packet = exception_packet("lan_or_hardware")
    execution = packet["execution_routing"]
    assert isinstance(execution, dict)
    execution.pop("requested_remote_desktop_tools", None)
    errors = routing.validate_packet(packet, live_state=live_state(), policy=policy())
    assert "remote_desktop exception requires non-empty requested_remote_desktop_tools" in errors


def test_unknown_remote_desktop_tool_is_rejected_by_packet_validation() -> None:
    packet = exception_packet("lan_or_hardware")
    execution = packet["execution_routing"]
    assert isinstance(execution, dict)
    execution["requested_remote_desktop_tools"] = ["Remote_Desktop_Commander.future_unknown_tool"]
    errors = routing.validate_packet(packet, live_state=live_state(), policy=policy())
    assert "requested_remote_desktop_tools must contain only known permitted tool identifiers" in errors
```

Update `exception_packet(...)` so valid fixtures declare one representative tool, for example `Remote_Desktop_Commander.ping` for `lan_or_hardware`, `Remote_Desktop_Commander.get_config` for `host_only_service`, and `Remote_Desktop_Commander.list_processes` for `self_hosted_runner_diagnosis`.

- [ ] **Step 2: Run the focused test file and confirm RED**

Run:

```bash
python3 tools/governance/test_agent_execution_routing.py
```

Expected: non-zero exit because the new policy keys and packet validation do not yet exist.

- [ ] **Step 3: Extend the JSON policy minimally**

Add these exact structures while preserving the existing three reasons/actions:

```json
"remote_desktop_reason_action_compatibility": {
  "host_only_service": ["inspect_host_only_service"],
  "lan_or_hardware": ["perform_lan_or_hardware_acceptance"],
  "self_hosted_runner_diagnosis": ["diagnose_self_hosted_runner"]
},
"known_remote_desktop_tools": [
  "Remote_Desktop_Commander.list_devices",
  "Remote_Desktop_Commander.who_am_i",
  "Remote_Desktop_Commander.ping",
  "Remote_Desktop_Commander.get_config",
  "Remote_Desktop_Commander.read_file",
  "Remote_Desktop_Commander.read_multiple_files",
  "Remote_Desktop_Commander.list_directory",
  "Remote_Desktop_Commander.start_search",
  "Remote_Desktop_Commander.get_more_search_results",
  "Remote_Desktop_Commander.stop_search",
  "Remote_Desktop_Commander.list_searches",
  "Remote_Desktop_Commander.get_file_info",
  "Remote_Desktop_Commander.start_process",
  "Remote_Desktop_Commander.read_process_output",
  "Remote_Desktop_Commander.interact_with_process",
  "Remote_Desktop_Commander.force_terminate",
  "Remote_Desktop_Commander.list_sessions",
  "Remote_Desktop_Commander.list_processes",
  "Remote_Desktop_Commander.kill_process",
  "Remote_Desktop_Commander.get_usage_stats",
  "Remote_Desktop_Commander.get_recent_tool_calls"
],
"always_forbidden_remote_desktop_tools": [
  "Remote_Desktop_Commander.shutdown",
  "Remote_Desktop_Commander.set_config_value",
  "Remote_Desktop_Commander.write_file",
  "Remote_Desktop_Commander.write_pdf",
  "Remote_Desktop_Commander.create_directory",
  "Remote_Desktop_Commander.move_file",
  "Remote_Desktop_Commander.edit_block",
  "Remote_Desktop_Commander.give_feedback_to_desktop_commander",
  "Remote_Desktop_Commander.get_prompts"
]
```

The known and always-forbidden sets must be disjoint. Always-forbidden functions are not authorizable through the current three reasons.

- [ ] **Step 4: Extend policy validation and packet validation**

In `_policy_errors(...)`, reject malformed reason/action mappings, duplicate/unknown semantic actions, duplicate tool names, overlap between known and always-forbidden tool sets, and tool identifiers not prefixed with `Remote_Desktop_Commander.`.

In `validate_packet(...)`, enforce:

```python
requested_tools_value = execution.get("requested_remote_desktop_tools")
requested_tools = _list(requested_tools_value)
known_tools = _closed_values(policy, "known_remote_desktop_tools")

if requested_tools_value is not None and (
    not isinstance(requested_tools_value, list)
    or not requested_tools
    or any(not isinstance(tool, str) or tool not in known_tools for tool in requested_tools)
    or len(set(requested_tools)) != len(requested_tools)
):
    errors.append("requested_remote_desktop_tools must contain only known permitted tool identifiers")

if remote_desktop == "exception" and not requested_tools:
    errors.append("remote_desktop exception requires non-empty requested_remote_desktop_tools")
elif remote_desktop != "exception" and requested_tools:
    errors.append("requested_remote_desktop_tools require remote_desktop=exception")
```

Also enforce reason/action compatibility using `remote_desktop_reason_action_compatibility`; a valid action from the global action list but wrong for the selected reason must fail.

- [ ] **Step 5: Run focused tests and confirm GREEN**

Run:

```bash
python3 tools/governance/test_agent_execution_routing.py
python3 -c "import json; json.load(open('ecosystem/agent-execution-routing-policy.json', encoding='utf-8'))"
```

Expected: both commands exit 0.

- [ ] **Step 6: Commit Task 1**

```bash
git add ecosystem/agent-execution-routing-policy.json tools/governance/test_agent_execution_routing.py tools/governance/agent_execution_routing.py
git commit -m "feat(governance): constrain Remote Desktop tool authority"
```

---

### Task 2: Add the pure per-action Remote Desktop decision function

**Files:**
- Modify: `tools/governance/agent_execution_routing.py`
- Modify: `tools/governance/test_agent_execution_routing.py`

**Interfaces:**
- Consumes: `validate_packet(packet, live_state=..., policy=...)` and the policy keys from Task 1.
- Produces:

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

- [ ] **Step 1: Add RED tests for direct-call denial and exact allow**

Add tests covering the user-visible failure mode:

```python
def test_list_devices_without_exception_is_denied() -> None:
    errors = routing.validate_remote_desktop_action(
        "perform_lan_or_hardware_acceptance",
        "Remote_Desktop_Commander.list_devices",
        packet=default_packet(),
        live_state=live_state(),
        policy=policy(),
    )
    assert "remote desktop direct call requires validated host_exception" in errors


def test_get_config_without_exception_is_denied() -> None:
    errors = routing.validate_remote_desktop_action(
        "inspect_host_only_service",
        "Remote_Desktop_Commander.get_config",
        packet=default_packet(),
        live_state=live_state(),
        policy=policy(),
    )
    assert "remote desktop direct call requires validated host_exception" in errors


def test_unknown_remote_tool_fails_closed() -> None:
    packet = exception_packet("lan_or_hardware")
    errors = routing.validate_remote_desktop_action(
        "perform_lan_or_hardware_acceptance",
        "Remote_Desktop_Commander.future_unknown_tool",
        packet=packet,
        live_state=live_state(),
        policy=policy(),
    )
    assert "remote desktop tool is not policy-known" in errors


def test_wrong_semantic_action_for_reason_is_denied() -> None:
    packet = exception_packet("lan_or_hardware")
    errors = routing.validate_remote_desktop_action(
        "inspect_host_only_service",
        "Remote_Desktop_Commander.ping",
        packet=packet,
        live_state=live_state(),
        policy=policy(),
    )
    assert "host action is incompatible with remote_desktop_reason" in errors


def test_exact_declared_reason_action_and_tool_is_allowed() -> None:
    packet = exception_packet("lan_or_hardware")
    assert routing.validate_remote_desktop_action(
        "perform_lan_or_hardware_acceptance",
        "Remote_Desktop_Commander.ping",
        packet=packet,
        live_state=live_state(),
        policy=policy(),
    ) == []
```

Also add representative denial tests for `read_file`, `list_processes`, `start_process`, and stale GitHub preflight.

- [ ] **Step 2: Run the focused suite and confirm RED**

Run:

```bash
python3 tools/governance/test_agent_execution_routing.py
```

Expected: non-zero exit because `validate_remote_desktop_action` is not defined.

- [ ] **Step 3: Implement the minimal pure gate**

Implement the function with this order:

```python
def validate_remote_desktop_action(host_action, remote_tool, *, packet, live_state, policy):
    policy_errors = _policy_errors(policy)
    if policy_errors:
        return policy_errors
    if remote_tool in _closed_values(policy, "always_forbidden_remote_desktop_tools"):
        return ["remote desktop tool is always forbidden by policy"]
    if remote_tool not in _closed_values(policy, "known_remote_desktop_tools"):
        return ["remote desktop tool is not policy-known"]
    if not isinstance(packet, dict) or not isinstance(live_state, dict):
        return ["remote desktop direct call requires current packet and live_state"]

    packet_errors = validate_packet(packet, live_state=live_state, policy=policy)
    if packet_errors:
        return ["remote desktop direct call requires valid routing packet", *packet_errors]

    execution = _mapping(packet.get("execution_routing"))
    if execution.get("execution_target") != "host_exception" or execution.get("remote_desktop") != "exception":
        return ["remote desktop direct call requires validated host_exception"]

    reason = execution.get("remote_desktop_reason")
    compatibility = _mapping(policy.get("remote_desktop_reason_action_compatibility"))
    if host_action not in _list(compatibility.get(reason)):
        return ["host action is incompatible with remote_desktop_reason"]
    if host_action not in _list(execution.get("requested_host_actions")):
        return ["host action was not requested by the routing packet"]
    if remote_tool not in _list(execution.get("requested_remote_desktop_tools")):
        return ["remote desktop tool was not requested by the routing packet"]
    return []
```

Keep the implementation deterministic and side-effect free.

- [ ] **Step 4: Run RED-to-GREEN verification**

Run:

```bash
python3 tools/governance/test_agent_execution_routing.py
```

Expected: exit 0 and all new direct-call tests pass.

- [ ] **Step 5: Add CLI-free audit metadata helper only if needed by tests**

Do not introduce persistence/logging in this task. If audit representation is useful, expose a pure helper returning non-sensitive fields only; otherwise leave logging to the future connector integration described by the spec.

- [ ] **Step 6: Commit Task 2**

```bash
git add tools/governance/agent_execution_routing.py tools/governance/test_agent_execution_routing.py
git commit -m "feat(governance): gate Remote Desktop calls per action"
```

---

### Task 3: Remove the capability-discovery ambiguity from canonical instructions

**Files:**
- Modify: `docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md`
- Modify: `AGENTS.md`

**Interfaces:**
- Consumes: `validate_remote_desktop_action(...)` and the policy semantics from Tasks 1-2.
- Produces: canonical prose stating that local registration/schema inspection is allowed without exception, while every direct `Remote_Desktop_Commander.*` invocation requires a positive per-action gate.

- [ ] **Step 1: Add instruction assertions to the deterministic suite**

Extend `tools/governance/test_agent_execution_routing.py` with text-contract checks that read the two canonical Markdown files and assert all of these phrases/semantics are present:

```python
assert "every direct `Remote_Desktop_Commander.*` invocation" in contract_text
assert "local connector/tool registration" in contract_text
assert "must not invoke `Remote_Desktop_Commander.list_devices`" in contract_text
assert "positive per-action" in contract_text
```

The test should also assert that the contract does not describe `list_devices` or `get_config` as harmless capability discovery.

- [ ] **Step 2: Run tests and confirm RED**

Run:

```bash
python3 tools/governance/test_agent_execution_routing.py
```

Expected: non-zero exit because canonical prose has not yet been updated.

- [ ] **Step 3: Update the central contract**

In `Capability truthfulness and tool discovery before blocking`, replace broad Remote Desktop capability probing with this execution order:

1. inspect the locally exposed connector registration/tool schemas without invoking Remote Desktop;
2. inspect GitHub-native capabilities and permission evidence;
3. use GitHub-native reads for repository facts;
4. never call `Remote_Desktop_Commander.list_devices`, `who_am_i`, `ping`, `get_config`, filesystem/process/terminal/search/history functions merely to prove Remote Desktop capability;
5. when an actual host-only need is proven, build a fresh host-exception packet and require `validate_remote_desktop_action(...) == []` for the exact semantic action and exact connector tool immediately before the call.

State explicitly that a `DENY` is not automatically a blocker and ordinary work continues through GitHub, Actions or isolated workspaces.

- [ ] **Step 4: Update root `AGENTS.md` with the same non-weakenable invariant**

Add a concise mandatory rule under execution routing/capability discovery:

```text
Out-of-band inspection of registered Remote Desktop tool schemas is capability discovery. Invoking any `Remote_Desktop_Commander.*` function is execution and requires a fresh validated host exception plus a positive `validate_remote_desktop_action(...)` decision for the exact semantic action and exact tool. `list_devices`, `who_am_i`, `ping` and `get_config` are not discovery exemptions.
```

Do not duplicate the full policy; keep META policy/contract canonical.

- [ ] **Step 5: Run focused tests and diff checks**

Run:

```bash
python3 tools/governance/test_agent_execution_routing.py
git diff --check
```

Expected: both exit 0.

- [ ] **Step 6: Commit Task 3**

```bash
git add AGENTS.md docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md tools/governance/test_agent_execution_routing.py
git commit -m "docs(governance): forbid ungated Remote Desktop discovery calls"
```

---

### Task 4: Exact-head META qualification and protected delivery

**Files:**
- Verify all files changed by Tasks 1-3 plus the approved spec/plan.
- No additional implementation file is required unless verification finds a concrete defect.

**Interfaces:**
- Consumes: final META task head.
- Produces: exact-head CI/review evidence and protected merge prerequisite for provider adoption.

- [ ] **Step 1: Run the complete applicable META validation locally/in an isolated workspace**

Run:

```bash
python3 tools/governance/audit_github_readonly.py --offline
python3 tools/governance/test_audit_github_readonly.py
python3 tools/governance/test_audit_github_readonly_terminal.py
python3 tools/governance/test_agent_execution_routing.py
python3 tools/governance/test_ai_review_policy.py
python3 tools/governance/test_ai_review_git_metadata.py
python3 tools/governance/test_verify_ai_review_evidence.py
git diff --check main...HEAD
```

Expected: all applicable commands exit 0. If a command is platform-inapplicable, use the existing repository-approved CI proof rather than Remote Desktop.

- [ ] **Step 2: Inspect the exact changed-file set and full diff**

Confirm the PR contains only:

```text
AGENTS.md
ecosystem/agent-execution-routing-policy.json
tools/governance/agent_execution_routing.py
tools/governance/test_agent_execution_routing.py
docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md
docs/superpowers/specs/2026-08-28-remote-desktop-per-action-enforcement-design.md
docs/superpowers/plans/2026-08-28-remote-desktop-per-action-enforcement.md
```

Any additional path requires explicit reconciliation before readiness.

- [ ] **Step 3: Freeze the final head and require exact-head GitHub gates**

Read PR #93 and require the repository's current protected `meta-gate` and `ai-review-gate` on the exact final head. Do not reuse evidence from an older head.

- [ ] **Step 4: Apply the current AI review risk policy**

Because this change alters governance enforcement and authorization semantics, classify it using `ecosystem/ai-review-policy.json` on the final exact diff. Follow the resulting R-tier exactly; do not manually downgrade.

- [ ] **Step 5: Reconcile all review findings**

For every blocking review finding, repair on the same branch, rerun the invalidated tests, obtain a new exact head and repeat exact-head review/check qualification. Do not use Remote Desktop to inspect or rerun equivalent CI.

- [ ] **Step 6: Protected squash merge and readback**

Merge only after all current required exact-head checks/reviews pass. Then read protected `main` and verify the merged policy, validator function, canonical contract and spec are present at the resulting squash-merge SHA.

- [ ] **Step 7: Start the provider rollout only from the merged META SHA**

After successful readback, create a fresh Game issue/branch/plan that references the exact merged META commit. The provider plan must add prompt/governance regression binding without copying the META policy or changing Game runtime, deployment, secrets, runner configuration or live Remote Desktop state.
