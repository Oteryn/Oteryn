# Remote Desktop Per-Action Enforcement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every direct `Remote_Desktop_Commander.*` invocation fail closed unless the exact call is covered by a fresh, valid META host-exception packet.

**Architecture:** Extend the existing execution-routing policy with exact reason/action compatibility and a closed set of Remote Desktop tool identifiers. Add a pure `validate_remote_desktop_action(...)` decision function that reuses `validate_packet(...)`, then remove the capability-discovery ambiguity from canonical instructions. Provider adoption is deliberately deferred until this META change is protected-merged.

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

---

### Task 1: Encode exact Remote Desktop authority in the machine-readable policy

**Files:**
- Modify: `ecosystem/agent-execution-routing-policy.json`
- Modify: `tools/governance/agent_execution_routing.py`
- Modify: `tools/governance/test_agent_execution_routing.py`

**Interfaces:**
- Consumes: existing `remote_desktop_reasons`, `remote_desktop_actions`, `validate_packet(...)`.
- Produces policy keys `remote_desktop_reason_action_compatibility`, `known_remote_desktop_tools`, `always_forbidden_remote_desktop_tools` and packet field `requested_remote_desktop_tools`.

- [ ] **Step 1: Add RED tests for the new policy shape**

Add these tests:

```python
def test_remote_desktop_policy_has_exact_reason_action_mapping() -> None:
    current = policy()
    assert current["remote_desktop_reason_action_compatibility"] == {
        "host_only_service": ["inspect_host_only_service"],
        "lan_or_hardware": ["perform_lan_or_hardware_acceptance"],
        "self_hosted_runner_diagnosis": ["diagnose_self_hosted_runner"],
    }


def test_remote_desktop_tool_sets_are_closed_and_disjoint() -> None:
    current = policy()
    known = current["known_remote_desktop_tools"]
    forbidden = current["always_forbidden_remote_desktop_tools"]
    assert isinstance(known, list) and known
    assert isinstance(forbidden, list) and forbidden
    assert len(set(known)) == len(known)
    assert len(set(forbidden)) == len(forbidden)
    assert set(known).isdisjoint(forbidden)
    assert all(tool.startswith("Remote_Desktop_Commander.") for tool in [*known, *forbidden])
```

- [ ] **Step 2: Extend valid exception fixtures with exact connector tools**

Update `exception_packet(...)` so each valid fixture has both semantic action and exact connector tool:

```python
actions_by_reason = {
    "host_only_service": ["inspect_host_only_service"],
    "lan_or_hardware": ["perform_lan_or_hardware_acceptance"],
    "self_hosted_runner_diagnosis": ["diagnose_self_hosted_runner"],
}
tools_by_reason = {
    "host_only_service": ["Remote_Desktop_Commander.get_config"],
    "lan_or_hardware": ["Remote_Desktop_Commander.ping"],
    "self_hosted_runner_diagnosis": ["Remote_Desktop_Commander.list_processes"],
}
execution["requested_remote_desktop_tools"] = tools_by_reason[reason]
```

- [ ] **Step 3: Add RED packet-validation tests**

Add:

```python
def test_remote_desktop_exception_requires_exact_remote_tool_set() -> None:
    packet = exception_packet("lan_or_hardware")
    execution = packet["execution_routing"]
    assert isinstance(execution, dict)
    del execution["requested_remote_desktop_tools"]
    errors = routing.validate_packet(packet, live_state=live_state(), policy=policy())
    assert "remote_desktop exception requires non-empty requested_remote_desktop_tools" in errors


def test_unknown_remote_desktop_tool_is_rejected_by_packet_validation() -> None:
    packet = exception_packet("lan_or_hardware")
    execution = packet["execution_routing"]
    assert isinstance(execution, dict)
    execution["requested_remote_desktop_tools"] = ["Remote_Desktop_Commander.future_unknown_tool"]
    errors = routing.validate_packet(packet, live_state=live_state(), policy=policy())
    assert "requested_remote_desktop_tools must contain only known permitted tool identifiers" in errors


def test_reason_action_mismatch_is_rejected_by_packet_validation() -> None:
    packet = exception_packet("lan_or_hardware")
    execution = packet["execution_routing"]
    assert isinstance(execution, dict)
    execution["requested_host_actions"] = ["inspect_host_only_service"]
    errors = routing.validate_packet(packet, live_state=live_state(), policy=policy())
    assert "requested_host_actions are incompatible with remote_desktop_reason" in errors
```

- [ ] **Step 4: Run the focused suite and confirm RED**

Run:

```bash
python3 tools/governance/test_agent_execution_routing.py
```

Expected: non-zero exit because the new policy keys and validation do not exist yet.

- [ ] **Step 5: Add the exact policy mappings**

Add:

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

- [ ] **Step 6: Make `_policy_errors(...)` fail closed**

Validate all of these conditions:

```python
reasons = _closed_values(policy, "remote_desktop_reasons")
actions = _closed_values(policy, "remote_desktop_actions")
compatibility = _mapping(policy.get("remote_desktop_reason_action_compatibility"))
known_tools = policy.get("known_remote_desktop_tools")
forbidden_tools = policy.get("always_forbidden_remote_desktop_tools")
```

Require `set(compatibility) == reasons`; each compatibility value must be a non-empty unique string list and a subset of `actions`; `known_tools` and `forbidden_tools` must each be non-empty unique string lists; every tool must start with `Remote_Desktop_Commander.`; the two sets must be disjoint.

Use deterministic messages:

```text
policy remote_desktop_reason_action_compatibility must map every and only remote_desktop reason
policy remote_desktop_reason_action_compatibility contains an action outside remote_desktop_actions
policy known_remote_desktop_tools must be a non-empty list of unique tool identifiers
policy always_forbidden_remote_desktop_tools must be a non-empty list of unique tool identifiers
policy remote desktop tool identifiers must use Remote_Desktop_Commander prefix
policy known and always-forbidden remote desktop tools must be disjoint
```

- [ ] **Step 7: Validate `requested_remote_desktop_tools` and reason/action compatibility**

In `validate_packet(...)` enforce:

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

Then enforce:

```python
reason = execution.get("remote_desktop_reason")
compatibility = _mapping(policy.get("remote_desktop_reason_action_compatibility"))
allowed_for_reason = set(_list(compatibility.get(reason)))
if remote_desktop == "exception" and any(action not in allowed_for_reason for action in requested_actions):
    errors.append("requested_host_actions are incompatible with remote_desktop_reason")
```

- [ ] **Step 8: Run GREEN verification**

Run:

```bash
python3 tools/governance/test_agent_execution_routing.py
python3 -c "import json; json.load(open('ecosystem/agent-execution-routing-policy.json', encoding='utf-8'))"
```

Expected: both commands exit 0.

- [ ] **Step 9: Commit Task 1**

```bash
git add ecosystem/agent-execution-routing-policy.json tools/governance/agent_execution_routing.py tools/governance/test_agent_execution_routing.py
git commit -m "feat(governance): constrain Remote Desktop tool authority"
```

---

### Task 2: Add the pure per-action decision gate

**Files:**
- Modify: `tools/governance/agent_execution_routing.py`
- Modify: `tools/governance/test_agent_execution_routing.py`

**Interfaces:**
- Consumes: policy fields from Task 1 and `validate_packet(...)`.
- Produces exactly this function:

```python
def validate_remote_desktop_action(
    host_action: str,
    remote_tool: str,
    *,
    packet: dict[str, object] | None,
    live_state: dict[str, object] | None,
    policy: dict[str, object],
) -> list[str]:
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

- [ ] **Step 1: Add RED direct-call tests**

Add:

```python
def test_list_devices_without_exception_is_denied() -> None:
    errors = routing.validate_remote_desktop_action(
        "perform_lan_or_hardware_acceptance",
        "Remote_Desktop_Commander.list_devices",
        packet=default_packet(), live_state=live_state(), policy=policy(),
    )
    assert "remote desktop direct call requires validated host_exception" in errors


def test_get_config_without_exception_is_denied() -> None:
    errors = routing.validate_remote_desktop_action(
        "inspect_host_only_service",
        "Remote_Desktop_Commander.get_config",
        packet=default_packet(), live_state=live_state(), policy=policy(),
    )
    assert "remote desktop direct call requires validated host_exception" in errors


def test_unknown_remote_tool_fails_closed() -> None:
    errors = routing.validate_remote_desktop_action(
        "perform_lan_or_hardware_acceptance",
        "Remote_Desktop_Commander.future_unknown_tool",
        packet=exception_packet("lan_or_hardware"), live_state=live_state(), policy=policy(),
    )
    assert errors == ["remote desktop tool is not policy-known"]


def test_always_forbidden_remote_tool_is_denied_even_with_exception() -> None:
    errors = routing.validate_remote_desktop_action(
        "perform_lan_or_hardware_acceptance",
        "Remote_Desktop_Commander.shutdown",
        packet=exception_packet("lan_or_hardware"), live_state=live_state(), policy=policy(),
    )
    assert errors == ["remote desktop tool is always forbidden by policy"]


def test_exact_declared_reason_action_and_tool_is_allowed() -> None:
    assert routing.validate_remote_desktop_action(
        "perform_lan_or_hardware_acceptance",
        "Remote_Desktop_Commander.ping",
        packet=exception_packet("lan_or_hardware"), live_state=live_state(), policy=policy(),
    ) == []
```

- [ ] **Step 2: Add RED tests for representative host-contact surfaces**

Add:

```python
def test_representative_remote_tools_are_denied_without_exception() -> None:
    cases = (
        ("inspect_host_only_service", "Remote_Desktop_Commander.read_file"),
        ("diagnose_self_hosted_runner", "Remote_Desktop_Commander.list_processes"),
        ("diagnose_self_hosted_runner", "Remote_Desktop_Commander.start_process"),
        ("diagnose_self_hosted_runner", "Remote_Desktop_Commander.read_process_output"),
    )
    for host_action, remote_tool in cases:
        errors = routing.validate_remote_desktop_action(
            host_action, remote_tool,
            packet=default_packet(), live_state=live_state(), policy=policy(),
        )
        assert "remote desktop direct call requires validated host_exception" in errors
```

- [ ] **Step 3: Add RED tests for stale preflight and exact-tool scoping**

Add:

```python
def test_stale_preflight_denies_direct_call() -> None:
    packet = exception_packet("lan_or_hardware")
    execution = packet["execution_routing"]
    assert isinstance(execution, dict)
    current_preflight = execution["github_preflight"]
    assert isinstance(current_preflight, dict)
    current_preflight["default_branch_sha"] = "a" * 40
    errors = routing.validate_remote_desktop_action(
        "perform_lan_or_hardware_acceptance",
        "Remote_Desktop_Commander.ping",
        packet=packet, live_state=live_state(), policy=policy(),
    )
    assert "remote desktop direct call requires valid routing packet" in errors
    assert "github_preflight.default_branch_sha does not match live_state" in errors


def test_undeclared_exact_tool_is_denied() -> None:
    packet = exception_packet("lan_or_hardware")
    errors = routing.validate_remote_desktop_action(
        "perform_lan_or_hardware_acceptance",
        "Remote_Desktop_Commander.list_devices",
        packet=packet, live_state=live_state(), policy=policy(),
    )
    assert errors == ["remote desktop tool was not requested by the routing packet"]
```

- [ ] **Step 4: Run the focused suite and confirm RED**

Run:

```bash
python3 tools/governance/test_agent_execution_routing.py
```

Expected: non-zero exit because `validate_remote_desktop_action(...)` is absent.

- [ ] **Step 5: Implement the exact function from the Interfaces block**

Insert the function after `validate_packet(...)` and before CLI-only helpers. Do not add network, logging, filesystem or connector calls.

- [ ] **Step 6: Run GREEN verification**

Run:

```bash
python3 tools/governance/test_agent_execution_routing.py
```

Expected: exit 0.

- [ ] **Step 7: Commit Task 2**

```bash
git add tools/governance/agent_execution_routing.py tools/governance/test_agent_execution_routing.py
git commit -m "feat(governance): gate Remote Desktop calls per action"
```

---

### Task 3: Remove the capability-discovery ambiguity from canonical instructions

**Files:**
- Modify: `docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md`
- Modify: `AGENTS.md`
- Modify: `tools/governance/test_agent_execution_routing.py`

**Interfaces:**
- Consumes: `validate_remote_desktop_action(...)` from Task 2.
- Produces: canonical instructions that permit only out-of-band connector schema inspection without an exception and require a positive per-action gate before every direct Remote Desktop function call.

- [ ] **Step 1: Add RED text-contract tests**

Add:

```python
def test_canonical_contract_forbids_direct_rdc_capability_probes() -> None:
    repo_root = Path(__file__).parents[2]
    contract_text = (repo_root / "docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md").read_text(encoding="utf-8")
    root_agents = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
    for text in (contract_text, root_agents):
        assert "every direct `Remote_Desktop_Commander.*` invocation" in text
        assert "local connector/tool registration" in text
        assert "positive per-action" in text
    assert "must not invoke `Remote_Desktop_Commander.list_devices`" in contract_text
    assert "must not invoke `Remote_Desktop_Commander.get_config`" in contract_text
```

- [ ] **Step 2: Run the focused suite and confirm RED**

Run:

```bash
python3 tools/governance/test_agent_execution_routing.py
```

Expected: non-zero exit because the canonical Markdown does not yet contain the required invariant.

- [ ] **Step 3: Correct the central capability-discovery contract**

In `Capability truthfulness and tool discovery before blocking`, require this exact order:

```text
1. inspect local connector/tool registration, descriptions and argument schemas without invoking Remote Desktop;
2. inspect repository-native GitHub capabilities and authenticated permission evidence;
3. use repository-native reads for repository facts;
4. must not invoke `Remote_Desktop_Commander.list_devices`, `Remote_Desktop_Commander.who_am_i`, `Remote_Desktop_Commander.ping`, `Remote_Desktop_Commander.get_config` or any filesystem/process/terminal/search/history Remote Desktop function merely to prove capability;
5. when an actual host-only need is proven, construct a fresh host-exception packet and require a positive per-action `validate_remote_desktop_action(...)` decision for the exact semantic action and exact connector tool before the direct call.
```

Also state: every direct `Remote_Desktop_Commander.*` invocation is execution, not schema discovery; a denial is not automatically a blocker; continue via GitHub, Actions or isolated workspaces when useful work remains.

- [ ] **Step 4: Add the root non-weakenable invariant**

Add this paragraph under execution routing/capability discovery in `AGENTS.md`:

```text
Out-of-band inspection of local connector/tool registration and schemas is capability discovery. Every direct `Remote_Desktop_Commander.*` invocation is execution and requires a fresh validated host exception plus a positive per-action `validate_remote_desktop_action(...)` decision for the exact semantic action and exact connector tool. `list_devices`, `who_am_i`, `ping` and `get_config` are not discovery exemptions.
```

- [ ] **Step 5: Run GREEN verification and whitespace check**

Run:

```bash
python3 tools/governance/test_agent_execution_routing.py
git diff --check
```

Expected: both commands exit 0.

- [ ] **Step 6: Commit Task 3**

```bash
git add AGENTS.md docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md tools/governance/test_agent_execution_routing.py
git commit -m "docs(governance): forbid ungated Remote Desktop discovery calls"
```

---

### Task 4: Exact-head META qualification and protected delivery

**Files:**
- Verify all changed files; do not add implementation paths during closeout unless a concrete failing check identifies a defect.

**Interfaces:**
- Consumes: final PR #93 head.
- Produces: exact-head deterministic checks, current risk-policy review evidence, protected squash merge and protected-main readback.

- [ ] **Step 1: Run all applicable deterministic META checks**

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

Expected: every command exits 0. Platform-specific evidence that cannot execute in the isolated implementation environment must be satisfied only by repository-approved GitHub CI; do not route it through Remote Desktop.

- [ ] **Step 2: Verify the exact changed-file set**

The final PR must contain exactly these paths:

```text
AGENTS.md
ecosystem/agent-execution-routing-policy.json
tools/governance/agent_execution_routing.py
tools/governance/test_agent_execution_routing.py
docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md
docs/superpowers/specs/2026-08-28-remote-desktop-per-action-enforcement-design.md
docs/superpowers/plans/2026-08-28-remote-desktop-per-action-enforcement.md
```

If the list differs, stop readiness and reconcile the additional/missing path before continuing.

- [ ] **Step 3: Freeze and read the exact PR head**

Read PR #93, record its exact head SHA and verify the full diff against `main`. Any subsequent content change invalidates this evidence and requires repeating Steps 1-3.

- [ ] **Step 4: Apply the current META AI review policy mechanically**

Run the repository's current risk classifier on the exact final diff. Follow the resulting `R0`/`R1`/`R2` requirement exactly; do not manually downgrade governance/authorization risk.

- [ ] **Step 5: Require current exact-head protected checks and review evidence**

Require the protected `meta-gate` and `ai-review-gate` for the exact frozen head. If review returns blocking findings, repair on the same branch, rerun affected deterministic checks, freeze the new head and obtain fresh review/check evidence.

- [ ] **Step 6: Mark the PR ready only after implementation self-review is complete**

Inspect every changed file and the complete diff, confirm no connector-level firewall claim was introduced, confirm no new exception reason exists, and confirm every direct-call test is fail-closed by default.

- [ ] **Step 7: Protected squash merge and readback**

Merge only with the expected exact head and only after current required checks/reviews pass. Read protected `main` after merge and verify the merged policy keys, `validate_remote_desktop_action(...)`, canonical contract wording and spec are present at the resulting squash-merge SHA.

- [ ] **Step 8: Start Game adoption from the merged META SHA**

Create a fresh Game issue/branch and a separate provider implementation plan referencing the exact protected META merge SHA. The provider change may add prompt/governance regression binding only; it must not copy/fork the META policy, change Game runtime/deployment/secrets/runner configuration, or touch live Remote Desktop state.
