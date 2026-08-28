# Remote Desktop per-action enforcement design

**Status:** approved design for implementation planning
**Governing issue:** `Oteryn/Oteryn#85`
**Authority repository:** `Oteryn/Oteryn` (META)
**Admission main:** `6999c8c42492f578e8a0a0c8b4b664c798c0c242`

## Problem

Oteryn already has a default-deny Remote Desktop/Desktop Commander policy and a deterministic routing-packet validator. That validator proves that a declared task packet is valid, but it does not by itself prove that every later Remote Desktop tool call was checked against the packet immediately before host contact.

The current capability-discovery language also permits broad inspection of available tools without an explicit distinction between connector-schema discovery and operations that contact a real remote host. This makes it possible for an agent to treat actions such as device enumeration, host configuration reads, filesystem/process inspection or test execution as harmless discovery even though they cross the Remote Desktop boundary.

The required correction is to make host contact explicit, least-privilege and fail-closed at the Oteryn policy level, then bind reusable provider prompts and governance validation to that decision contract. Oteryn cannot truthfully claim to be a physical firewall in front of an externally operated connector unless the connector/router exposes an enforcement hook; this design therefore defines the mandatory decision interface that such a hook must consume and enforces all repository-controlled surfaces now.

## Security invariant

An agent may inspect the existence and schema of a Remote Desktop connector without a host exception only when that operation is satisfied entirely by local tool registration metadata and does not enumerate, select, query or otherwise contact a remote device.

Every operation that contacts a remote host is denied unless a fresh execution-routing packet has already validated a matching `host_exception` and the concrete requested action is authorized for that exception.

This includes read-only host contact. `list_devices`, host/session enumeration, `get_config`, filesystem reads, process inspection, terminal execution, Docker/container inspection, log reads, test execution and equivalent actions are not exempt merely because they do not mutate the host.

## Action classes

The canonical policy will distinguish two top-level classes:

### `connector_schema_discovery`

No host contact. Examples are reading connector registration metadata, tool names, descriptions and JSON argument schemas supplied by the current client/runtime without asking the connector to enumerate or inspect devices.

This class is allowed without `remote_desktop: exception` because it does not touch a remote execution plane.

### `remote_host_contact`

Any operation whose implementation reaches a remote device, session, filesystem, process table, shell, service, runtime, network-visible host resource or host configuration.

Representative operations include:

- device or session enumeration;
- host configuration reads;
- filesystem list/read/write/search;
- process listing, output polling or process control;
- terminal/shell execution;
- Docker/container inspection or execution;
- test/build execution on the remote host;
- LAN/hardware acceptance performed from the remote host;
- host-only service inspection;
- self-hosted runner diagnosis.

This class requires an already validated host exception and a concrete least-privilege action identifier.

## Canonical per-action decision interface

META will extend `tools/governance/agent_execution_routing.py` with a deterministic decision function:

```python
def validate_remote_desktop_action(
    action: str,
    *,
    packet: dict[str, object] | None,
    live_state: dict[str, object] | None,
    policy: dict[str, object],
) -> list[str]:
    """Return an empty list only when this exact Remote Desktop action is allowed."""
```

Decision semantics:

1. If `action` is a policy-declared schema-only discovery action, return `ALLOW` only when it is explicitly classified as non-host-contacting.
2. Every other known Remote Desktop action is treated as host-contacting.
3. Unknown actions fail closed as host-contacting and are denied unless the policy is deliberately updated to classify them.
4. A host-contacting action requires a complete current routing packet and live-state snapshot.
5. The packet must independently pass the existing `validate_packet(...)` contract.
6. `execution_target` must be `host_exception`, `remote_desktop` must be `exception`, `equivalent_ci` must be `null`, and the closed exception reason must be valid.
7. The concrete action must be present in `requested_host_actions` and permitted for the selected exception reason.
8. A valid packet for one action does not authorize a different action.
9. Any missing, malformed, stale or contradictory state returns a deterministic denial error.

The function is pure and must not itself call GitHub, a host, Remote Desktop, a service or another tool.

## Reason-to-action compatibility

The machine-readable policy will make reason/action compatibility explicit instead of treating all permitted host actions as interchangeable.

The minimum mapping remains:

- `host_only_service` -> `inspect_host_only_service`;
- `lan_or_hardware` -> `perform_lan_or_hardware_acceptance`;
- `self_hosted_runner_diagnosis` -> `diagnose_self_hosted_runner`.

Host metadata discovery is not a fourth exception reason. If a host-only service, LAN/hardware operation or runner diagnosis genuinely requires device/session/config discovery, the corresponding least-privilege action set must be declared as part of that already valid exception. Generic curiosity, convenience, repository discovery, ordinary testing or capability probing is not a reason.

## Capability discovery correction

`docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md` and root `AGENTS.md` will be clarified so that capability discovery proceeds in this order:

1. inspect locally exposed tool registration and schemas;
2. inspect repository-native GitHub capabilities and authenticated permission evidence;
3. use repository-native reads for repository state;
4. do not enumerate Remote Desktop devices or query any remote host merely to discover whether the connector works;
5. if progress actually requires a host-only operation, construct and validate the narrow exception before the first host-contacting call.

A rejected Work-mode handoff, missing local CLI or unavailable repository command remains insufficient justification for Remote Desktop.

## Provider binding

`Oteryn/Oteryn-Game` adopts the META decision contract by reference and must not fork it.

Game root instructions and reusable execution prompts must state that no host-contacting Remote Desktop action may be invoked before a positive per-action decision. The provider may be stricter, but it may not classify a META host-contacting action as schema-only discovery or invent a broader exception reason.

Provider governance validation will scan the reusable execution/control-plane prompt set and fail when a prompt authorizes Remote Desktop as a generic fallback, allows host-contacting capability discovery, or omits the per-action gate on roles that can invoke execution tools.

This provider validation is a repository-controlled guard against future prompt regression; it is not represented as a physical connector firewall.

## External connector enforcement boundary

The desired terminal architecture is a real choke point in the connector/router that evaluates the same META policy immediately before forwarding a host-contacting action.

A compliant connector-side integration must:

1. receive the concrete action identifier and current validated authorization context;
2. call or faithfully implement the semantics of `validate_remote_desktop_action(...)`;
3. forward only on `ALLOW`;
4. fail closed on missing/unknown/malformed context;
5. emit an audit record for both `ALLOW` and `DENY` without leaking secrets;
6. never infer authorization from tool availability, an existing session or a previously allowed different action.

Until such an enforcement hook is present in the actual Remote Desktop transport, Oteryn completion language must say `repository-enforced policy and prompt gate`, not `connector-enforced firewall`.

## Audit semantics

Repository-controlled decision logs and test fixtures may record only non-sensitive authorization metadata:

- action identifier;
- action class;
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

- connector schema lookup without host contact -> `ALLOW`;
- `list_devices` without a validated host exception -> `DENY`;
- `get_config` without a validated host exception -> `DENY`;
- remote terminal/test execution without a validated host exception -> `DENY`;
- `lan_or_hardware` packet requesting `inspect_host_only_service` -> `DENY`;
- valid `lan_or_hardware` packet requesting exactly `perform_lan_or_hardware_acceptance` -> `ALLOW`;
- valid exception packet with stale GitHub preflight -> `DENY`;
- unknown Remote Desktop action -> `DENY` unless explicitly classified by policy.

A denial is not a blocker by itself. The agent must continue through GitHub, GitHub Actions, repository-native connectors or isolated workspaces when those routes can perform useful authorized work.

## Verification

META deterministic tests will cover at least:

- schema-only discovery allowed without a host exception;
- host-contacting discovery denied without an exception;
- `list_devices` denied without an exception;
- `get_config` denied without an exception;
- filesystem/process/terminal/test representative actions denied without an exception;
- unknown action fails closed;
- missing packet/live state fails closed for host contact;
- stale or mismatched preflight denies host contact;
- valid reason with wrong action denies;
- valid reason with exact permitted action allows;
- an action not listed in `requested_host_actions` is denied even when another action is authorized;
- equivalent CI remains incompatible with a Remote Desktop exception;
- malformed policy reason/action mappings fail closed.

Game governance tests will cover reusable prompt regressions that attempt to:

- enumerate remote devices as ordinary capability discovery;
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

1. META adds the action classification, reason/action compatibility, per-action validator, contract clarifications and deterministic tests.
2. META is independently validated and protected-merged under existing risk/review policy.
3. Game refreshes to the merged META authority and adopts the stricter prompt/governance binding on a separate provider branch/PR.
4. Platform and Atlas may adopt equivalent thin bindings independently when their current governance state is refreshed.
5. A future connector/router integration may consume the same decision semantics to make the policy physically non-bypassable at transport time.
