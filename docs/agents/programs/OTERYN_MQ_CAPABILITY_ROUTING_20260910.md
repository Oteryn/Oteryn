# Oteryn Merge Queue capability routing repair

Governing Issue: #194
Control request Issue: #196
Admission META main: `3b39e0be05aef008f1bd442821daefa898a201dd`
Branch: `fix/194-capability-aware-mq-routing`
PR: #195
Status: `VALIDATING`

## Problem

The current organization policy correctly fails closed when a session cannot
invoke the selected native exact-head `merge-async` operation, but execution
routing does not determine that integration capability before an implementation
worker is released. A candidate can therefore finish implementation, validation
and handoff before the coordinator discovers that its current tool surface
cannot submit the PR to Merge Queue.

## Implemented repair

1. `ecosystem/agent-execution-routing-policy.json` now contains a closed
   `integration_capability_routing` contract for protected integration.
2. `tools/governance/integration_capability_routing.py` classifies current
   capability as `NOT_REQUIRED`, `DIRECT_CAPABLE`, `DELEGATED_CAPABLE` or
   `BLOCKED_CAPABILITY_UNAVAILABLE`.
3. Worker release for expected autonomous protected integration is valid only
   after direct native capability or a verified operational META delegated route
   is observed.
4. `tools/governance/governed_merge_queue_executor.py` provides the bounded
   organization actuator for an already-authorized exact-target request.
5. META Issue #196 is transport only. Delegated execution additionally requires
   a live exact authorization comment on the target PR.
6. `.github/workflows/governed-merge-queue-executor.yml` keeps normal workflow
   permissions read-only, parses only the closed Issue #196 request command, and
   passes the exact target to the protected executor.
7. The same workflow runs deterministic capability/executor regressions on
   relevant pull-request changes.
8. The delegated mutation credential is a separately provisioned fine-grained
   secret `OTERYN_MQ_FINE_GRAINED_PAT`; its provisioning/value is not part of
   this repository change. Until protected integration + credential provisioning
   + a real canary are proven, the delegated route must not be advertised as
   operational.

## Owned paths

- `ecosystem/agent-execution-routing-policy.json`
- `tools/governance/integration_capability_routing.py`
- `tools/governance/test_integration_capability_routing.py`
- `tools/governance/governed_merge_queue_executor.py`
- `tools/governance/test_governed_merge_queue_executor.py`
- `.github/workflows/governed-merge-queue-executor.yml`
- `docs/agents/contracts/INTEGRATION_CAPABILITY_ROUTING_POLICY.md`
- `docs/agents/operations/MERGE_QUEUE_EXECUTOR.md`
- `docs/agents/programs/OTERYN_MQ_CAPABILITY_ROUTING_20260910.md`

## Security / authority invariants

- No new merge authority is created.
- The delegated executor is not a second coordinator/control plane.
- Target repository is limited to the four permanent Oteryn repositories.
- Target PR must be open, unmerged, non-Draft, `base=main`,
  same-repository-head and exact-SHA bound.
- Target exact-head canonical provider gate must be `completed/success`.
- Positive mutation is only REST `merge-async` with exact `sha` and explicit
  `merge_action=merge_queue`.
- HTTP 202 requires server UUID and strictly-later UUID-bound status/target
  readback.
- HTTP 200/409 is reconciliation only.
- Direct merge, generic auto-merge, GraphQL enqueue, bypass, force, default
  merge action, no-op/retrigger commits and ambiguous dequeue remain forbidden.
- The built-in workflow token is never the queue mutation credential.
- No credential value or provider product/runtime mutation is present.

## Focused validation before publication

Local deterministic fixture execution against the candidate source:

- `test_integration_capability_routing.py`: 8 PASS.
- `test_governed_merge_queue_executor.py`: 10 PASS.
- workflow YAML parses successfully as YAML.
- no network or live queue mutation was used by focused tests.

These local results are development evidence only. Exact published-head GitHub
CI and pull-request contract-test workflow are authoritative before readiness.

## Remaining gates

- exact-head META `meta-gate`;
- exact-head `capability-routing-tests`;
- full-diff self-review;
- independent review if current META risk policy requires it;
- normal protected Merge Queue integration;
- protected-main readback;
- credential provisioning + real executor canary before
  `meta.governed_merge_queue_executor.v1` becomes `operational`.

No merge authorization is inferred.
