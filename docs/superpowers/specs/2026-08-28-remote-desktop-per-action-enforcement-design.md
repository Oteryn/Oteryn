# Remote Desktop per-action enforcement design

**Status:** approved design for implementation planning
**Governing issue:** `Oteryn/Oteryn#85`
**Authority repository:** `Oteryn/Oteryn` (META)
**Admission main:** `6999c8c42492f578e8a0a0c8b4b664c798c0c242`

## Problem

Oteryn already has a default-deny Remote Desktop/Desktop Commander policy and a deterministic routing-packet validator. That validator proves that a declared task packet is valid, but it does not by itself prove that every later Remote Desktop tool call was checked against the packet immediately before the call.

The current capability-discovery language also does not draw a hard enough boundary between local tool-schema discovery and invoking a Remote Desktop connector function. That ambiguity allows an agent to treat device enumeration, host configuration reads, filesystem/process inspection or test execution as harmless discovery even though a direct connector action has begun.

The correction is to make every direct Remote Desktop/Desktop Commander invocation exception-gated, least-privilege and fail-closed at the Oteryn policy level, then bind reusable provider prompts and governance validation to that decision contract. Oteryn cannot truthfully claim to be a physical firewall in front of an externally operated connector unless the connector/router exposes an enforcement hook; this design therefore defines the mandatory decision interface that such a hook must consume and enforces all repository-controlled surfaces now.

## Security invariant

An agent may inspect that a Remote Desktop connector exists and read its registered tool names, descriptions and argument schemas without a host exception only through local connector/tool registration metadata that does not invoke a `Remote_Desktop_Commander.*` function.

Every direct `Remote_Desktop_Commander.*` invocation requires a previously validated host exception. There are no direct-call discovery exemptions.

This includes read-only or metadata-looking connector calls such as `list_devices`, `who_am_i`, `ping`, `get_config`, `get_usage_stats` and `get_recent_tool_calls`, as well as filesystem, process, terminal, Docker, search, test/build and configuration operations. Tool availability or an existing session is never authorization.

## Two execution classes

### `connector_schema_discovery`

This is out-of-band local registration discovery, for example loading the connector's exposed function schemas through the current tool/plugin registry. It does not invoke a Remote Desktop function and does not enumerate or query remote devices.

It is allowed without `remote_desktop: exception` because it does not enter the Remote Desktop execution path.

### `remote_desktop_direct_call`

Any invocation of a `Remote_Desktop_Commander.*` function. This class is exception-only, including functions that appear observational or metadata-only.

A direct call requires:

- a fresh valid routing packet;
- `execution_target: host_exception`;
- `remote_desktop: exception`;
- `equivalent_ci: null`;
- one valid closed exception reason;
- one declared semantic host action compatible with that reason;
- the exact connector tool name declared for the exception;
- a positive per-action decision immediately before the call.

## Canonical per-action decision interface

META will extend `tools/governance/agent_execution_routing.py` with a deterministic decision function:

```python
def validate_remote_desktop_action(
    host_action: str,
    remote_tool: str,
    *,
    packet: dict[str, object] | None,
    live_state: dict[str, object] | None,
    policy: dict[str, object],
) -> list[str]:
    """Return no errors only when this exact direct Remote Desktop call is allowed."""
```

An empty error list means `ALLOW`; any returned error means `DENY`.

Decision semantics:

1. `remote_tool` names the exact `Remote_Desktop_Commander` function that is about to be invoked.
2. Unknown tool names fail closed.
3. A direct call requires a complete current routing packet and live-state snapshot.
4. The packet must independently pass the existing `validate_packet(...)` contract.
5. `execution_target` must be `host_exception`, `remote_desktop` must be `exception`, `equivalent_ci` must be `null`, and the closed exception reason must be valid.
6. `host_action` must be present in `requested_host_actions` and compatible with the selected exception reason.
7. `remote_tool` must be present in the packet's exact requested Remote Desktop tool set and in the policy's closed known-tool set.
8. A valid packet for one semantic action or connector tool does not authorize another.
9. Missing, malformed, stale or contradictory state returns deterministic denial errors.

The function is pure and must not itself call GitHub, a host, Remote Desktop, a service or another tool.

## Machine-readable policy changes

`ecosystem/agent-execution-routing-policy.json` will keep the existing three exception reasons and semantic host actions while adding:

- `remote_desktop_reason_action_compatibility`: closed mapping from exception reason to allowed semantic host action;
- `known_remote_desktop_tools`: closed set of connector tool identifiers admitted by the current policy version;
- `always_forbidden_remote_desktop_tools`: connector administrative/destructive functions that repository agents may not authorize through these three existing reasons;
- packet validation for `requested_remote_desktop_tools`, which must be a non-empty unique subset of known tools only when `remote_desktop: exception`.

Unknown connector tools are denied until META deliberately classifies them. This makes connector growth fail closed rather than silently broadening agent authority.

The initial policy will not use the three existing reasons to authorize connector administration, host shutdown, Desktop Commander configuration changes, feedback/onboarding operations or equivalent unrelated administrative actions. If a future task genuinely needs such authority, it requires a separately reviewed policy change rather than semantic stretching of an existing reason.

## Reason-to-action compatibility

The existing semantic mapping becomes machine-checkable:

- `host_only_service` -> `inspect_host_only_service`;
- `lan_or_hardware` -> `perform_lan_or_hardware_acceptance`;
- `self_hosted_runner_diagnosis` -> `diagnose_self_hosted_runner`.

Host/device discovery is not a fourth exception reason. If one of these operations genuinely requires `list_devices`, `ping`, `get_config`, process inspection or another connector tool, the exact tool name must be included in `requested_remote_desktop_tools` for that already valid exception before it is called.

Generic curiosity, convenience, repository discovery, ordinary testing, capability probing, a missing local CLI or an available Remote Desktop session is not a reason.

## Capability discovery correction

`docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md` and root `AGENTS.md` will be clarified so that capability discovery proceeds in this order:

1. inspect locally exposed connector/tool registration and schemas without invoking Remote Desktop;
2. inspect repository-native GitHub capabilities and authenticated permission evidence;
3. use repository-native reads for repository state;
4. do not invoke `Remote_Desktop_Commander.list_devices`, `who_am_i`, `ping`, `get_config` or any other direct connector function merely to discover whether Remote Desktop is usable;
5. if progress actually requires a host-only operation, construct and validate the narrow exception before the first direct connector call.

A rejected Work-mode handoff, missing local CLI or unavailable repository command remains insufficient justification for Remote Desktop.

## Provider binding

`Oteryn/Oteryn-Game` adopts the META decision contract by reference and must not fork it.

Game root instructions and reusable execution/control-plane prompts must state that no `Remote_Desktop_Commander.*` call may occur before a positive per-action decision. The provider may be stricter, but it may not create a direct-call discovery exemption, invent a broader exception reason or classify an unknown connector tool as allowed.

Provider governance validation will inspect reusable execution/control-plane prompts and fail when a prompt:

- authorizes Remote Desktop as a generic fallback;
- permits direct connector calls as ordinary capability discovery;
- permits routine repository tests, Git inspection or CI polling through Remote Desktop;
- omits the positive per-action gate for a role that can invoke execution tools;
- broadens the exception set beyond META authority.

This is a repository-controlled regression guard; it is not represented as a physical connector firewall.

## External connector enforcement boundary

The desired terminal architecture is a real choke point in the connector/router that evaluates the same META policy immediately before forwarding a direct Remote Desktop call.

A compliant connector-side integration must:

1. receive the semantic host action, exact connector tool identifier and current validated authorization context;
2. call or faithfully implement the semantics of `validate_remote_desktop_action(...)`;
3. forward only when the decision is `ALLOW`;
4. fail closed on missing, unknown or malformed context;
5. emit an audit record for both `ALLOW` and `DENY` without leaking secrets;
6. never infer authorization from tool availability, an existing session or a previously allowed different call.

Until such an enforcement hook exists in the actual Remote Desktop transport, Oteryn completion language must say `repository-enforced policy and prompt gate`, not `connector-enforced firewall`.

## Audit semantics

Repository-controlled decision logs and test fixtures may record only non-sensitive authorization metadata:

- semantic host-action identifier;
- connector tool identifier;
- decision (`ALLOW` or `DENY`);
- exception reason or `not_applicable`;
- repository coordinate;
- governing issue/PR identifiers;
- task-head SHA;
- preflight verification timestamp;
- deterministic denial code when denied.

They must not contain credentials, command output, filesystem contents, host secrets, private configuration values or live user data.

## Failure behavior

The gate is default-deny and fail-closed.

Examples:

- local connector schema lookup without invoking RDC -> `ALLOW`;
- `Remote_Desktop_Commander.list_devices` without a validated exception -> `DENY`;
- `Remote_Desktop_Commander.get_config` without a validated exception -> `DENY`;
- remote terminal/test execution without a validated exception -> `DENY`;
- `lan_or_hardware` paired with `inspect_host_only_service` -> `DENY`;
- valid `lan_or_hardware` packet requesting `perform_lan_or_hardware_acceptance` but not declaring the exact connector tool -> `DENY`;
- valid exception packet with stale GitHub preflight -> `DENY`;
- unknown connector tool -> `DENY`;
- valid reason, semantic action and exact declared known tool -> `ALLOW`.

A denial is not a blocker by itself. The agent must continue through GitHub, GitHub Actions, repository-native connectors or isolated workspaces when those routes can perform useful authorized work.

## Verification

META deterministic tests will cover at least:

- out-of-band schema discovery is outside the direct-call gate;
- every representative direct connector discovery/metadata call is denied without an exception;
- `list_devices`, `who_am_i`, `ping` and `get_config` are denied without an exception;
- filesystem/process/terminal/test representative tools are denied without an exception;
- unknown tool names fail closed;
- missing packet/live state fails closed;
- stale or mismatched preflight denies the direct call;
- valid reason with wrong semantic action denies;
- exact tool omitted from `requested_remote_desktop_tools` denies;
- valid reason, semantic action and declared known tool allows;
- equivalent CI remains incompatible with a Remote Desktop exception;
- malformed reason/action/tool policy mappings fail closed;
- always-forbidden connector administrative tools cannot be admitted through the existing exception reasons.

Game governance tests will cover reusable prompt regressions that attempt to:

- enumerate remote devices as ordinary capability discovery;
- call any direct RDC tool before a positive gate;
- use Remote Desktop for routine repository tests or Git inspection;
- skip the per-action authorization requirement;
- broaden the exception set beyond META authority.

META exact-head `meta-gate` and provider exact-head governance/merge checks must pass before merge.

## Scope boundaries

This change does not:

- change product runtime code;
- change deployments, secrets, branch protection or production systems;
- authorize new host access;
- change the three existing exception reasons;
- make Remote Desktop a repository source of truth;
- claim connector-level physical enforcement without a real connector/router integration;
- use the remote host to implement or validate this governance change.

## Rollout

1. META adds reason/action/tool classification, per-action validation, contract clarifications and deterministic tests.
2. META is independently validated and protected-merged under existing risk/review policy.
3. Game refreshes to the merged META authority and adopts the stricter prompt/governance binding on a separate provider branch/PR.
4. Platform and Atlas may adopt equivalent thin bindings independently when their current governance state is refreshed.
5. A future connector/router integration may consume the same decision semantics to make the policy physically non-bypassable at transport time.
