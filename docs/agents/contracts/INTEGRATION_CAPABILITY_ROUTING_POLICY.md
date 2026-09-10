# Integration Capability Routing Policy

Status: active after protected integration of the governing META change.

## Purpose

Prevent a protected-integration task from reaching the end of implementation and
only then discovering that the active session cannot invoke the organization
Merge Queue primitive. Execution capability and integration authority are
different facts and MUST remain separate.

This contract is subordinate to `docs/agents/policy/ORGANIZATION_AGENT_POLICY.md`.
It does not grant merge authority and does not replace repository protection,
required checks, Merge Queue, review policy, or provider ownership.

## Machine authority

`ecosystem/agent-execution-routing-policy.json` owns the closed machine-readable
capability route. `tools/governance/integration_capability_routing.py` validates
and classifies the current execution-capability snapshot.

For a substantial mutating task that is expected to require autonomous protected
integration, capability preflight is required **before releasing the worker**.
Do not wait until `READY_FOR_COORDINATOR_INTEGRATION`.

The capability snapshot is observational only. It must come from current-session
tool/action discovery plus protected executor operational readback; a task,
prompt, caller boolean, comment, or previous session assertion is not capability
evidence.

## States

The only states are:

- `NOT_REQUIRED` — this bounded task is not expected to require autonomous
  protected integration.
- `DIRECT_CAPABLE` — the current session exposes the selected native exact-head
  `merge-async` operation.
- `DELEGATED_CAPABLE` — the current session can write the bounded META control
  request and the protected META delegated executor has been independently
  verified operational.
- `BLOCKED_CAPABILITY_UNAVAILABLE` — neither positive route is currently proven.

For work that requires autonomous protected integration, only `DIRECT_CAPABLE`
or `DELEGATED_CAPABLE` permits release of a new mutating worker. This is a
scheduling gate, not merge authorization.

If a task is already in progress when the capability route becomes unavailable,
preserve valid work and the qualified candidate. Do not create no-op/retrigger
commits merely to change capability state.

## Direct route

`DIRECT_CAPABLE` means the execution surface exposes the governed native
operation selected by META:

`PUT /repos/{owner}/{repo}/pulls/{pull_number}/merge-async`

with the exact qualified `sha` and explicit `merge_action="merge_queue"`.

All target-bound authorization, eligibility, receipt/readback and terminal
proof requirements from the organization policy remain unchanged.

## Delegated route

`DELEGATED_CAPABLE` does **not** transfer coordinator, repository, architecture,
review or merge authority. The organization-owned executor
`meta.governed_merge_queue_executor.v1` is a bounded actuator for one
already-authorized exact-target request.

The control transport is META Issue #196. An ordinary repository-native session
may use it only when it can create the exact bounded request comment. The
executor workflow must already exist on protected META `main` and its mutation
credential must have been operationally verified. An unmerged PR containing the
executor is not a verified route.

A delegated submission requires two durable records:

1. a target-PR authorization comment with exactly:

   ```text
   OTERYN_MQ_AUTHORIZATION_V1
   repository: <allowed owner/repo>
   pull_request: <positive integer>
   base: main
   head_sha: <exact 40-lowercase-hex head>
   integration_authorized: true
   ```

2. a META Issue #196 request comment with exactly:

   ```text
   /oteryn-mq-submit <allowed owner/repo> <pr-number> <exact-head> <authorization-comment-id>
   ```

The transport request is not authority by itself. The executor must fetch the
authorization comment live and bind it to the exact target PR, OWNER/MEMBER actor association, repository, PR number, `base=main` and head.

## Executor invariants

The protected META executor:

- accepts only the four permanent Oteryn repositories and their canonical source
  gates (`meta-gate`, `game-gate`, `platform-gate`, `atlas-gate`);
- requires target PR `open`, unmerged, non-Draft, `base=main`, same-repository
  head, exact requested SHA;
- requires the latest matching exact-head provider gate to be
  `completed/success`;
- performs only native `merge-async` with exact `sha` and
  `merge_action="merge_queue"`;
- treats HTTP 202 as acceptance only and requires its server UUID plus a
  strictly later UUID-bound status/target readback;
- treats HTTP 200/409 as reconciliation, never a fabricated new acceptance;
- treats denied/unavailable native mutation as
  `BLOCKED_CAPABILITY_UNAVAILABLE`;
- never performs direct merge, generic auto-merge, GraphQL enqueue, bypass,
  force, protection changes, default merge action, no-op/retrigger commits or
  ambiguous automated dequeue.

The executor intentionally stops after accepted request/readback. The owning
coordinator remains responsible for real `merge_group` aggregate success and
protected-main readback before any task archive, lease release or completion
claim.

## Credential boundary

The workflow's built-in repository token stays read-only and is never the queue
mutation credential. The mutation route uses only the separately provisioned
fine-grained credential permitted by the bound organization policy.

Credential provisioning and secret values are outside this repository change.
Until the secret exists and a real bounded canary proves the executor route,
`meta.governed_merge_queue_executor.v1` MUST NOT be listed in a capability
snapshot's `operational_executor_routes`.

Do not create a custom GitHub App merely for this executor and do not recreate
provider-local Merge Queue bridges.

## Provider adoption

After this contract is protected-integrated, a provider adopts it only through
its normal immutable META repin and local delivery reconciliation. Do not
silently treat a moving META branch as provider authority.

Provider workers do not need Merge Queue mutation capability themselves. The
preflight requirement belongs to the active scheduling/integration control
plane that releases work expected to need autonomous protected integration.
