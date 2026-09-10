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
3. `docs/agents/policy/ORGANIZATION_AGENT_POLICY.md` requires that classification
   before releasing substantial mutating work expected to require autonomous
   protected integration.
4. `ecosystem/organization-agent-policy.json` includes the new contract/router
   and executor in the immutable META machine-authority bundle.
5. `tools/governance/governed_merge_queue_executor.py` provides a bounded
   organization actuator for an already-authorized coordinator action.
6. META Issue #196 is a single transport surface. The executor live-re-reads the
   same control comment; no second comment/attestation/authorization proof
   engine is created.
7. `.github/workflows/governed-merge-queue-executor.yml` is default-branch
   `issue_comment` execution only and keeps normal workflow permissions read-only.
8. Existing required `meta-gate` now validates all new contract/code/test
   surfaces, so the repair does not add a second permanent required status.
9. The delegated mutation credential is a separately provisioned fine-grained
   secret `OTERYN_MQ_FINE_GRAINED_PAT`; its provisioning/value is outside this
   repository change. Until protected integration + credential provisioning + a
   real canary are proven, the delegated route must not be advertised as
   operational.

## Owned paths

- `AGENTS.md`
- `.github/workflows/ci.yml`
- `.github/workflows/governed-merge-queue-executor.yml`
- `docs/agents/contracts/INTEGRATION_CAPABILITY_ROUTING_POLICY.md`
- `docs/agents/operations/MERGE_QUEUE_EXECUTOR.md`
- `docs/agents/policy/ORGANIZATION_AGENT_POLICY.md`
- `docs/agents/programs/OTERYN_MQ_CAPABILITY_ROUTING_20260910.md`
- `ecosystem/agent-execution-routing-policy.json`
- `ecosystem/organization-agent-policy.json`
- `tools/governance/governed_merge_queue_executor.py`
- `tools/governance/integration_capability_routing.py`
- `tools/governance/test_governed_merge_queue_executor.py`
- `tools/governance/test_integration_capability_routing.py`

## Security / authority invariants

- No new merge authority is created.
- The delegated executor is not a second coordinator/control plane.
- A control comment is transport only and cannot broaden the caller's authority.
- Target repository is limited to the four permanent Oteryn repositories.
- Target PR must be open, unmerged, non-Draft, `base=main`,
  same-repository-head and exact-SHA bound.
- Target exact-head canonical provider gate must be `completed/success` and
  emitted by the GitHub Actions app.
- Positive mutation is only REST `merge-async` with exact `sha` and explicit
  `merge_action=merge_queue`.
- HTTP 202 requires server UUID and strictly-later UUID-bound status/target
  readback.
- HTTP 200/409 is reconciliation only.
- Direct merge, generic auto-merge, GraphQL enqueue, bypass, force, default
  merge action, no-op/retrigger commits and ambiguous dequeue remain forbidden.
- The built-in workflow token is never the queue mutation credential.
- No credential value or provider product/runtime mutation is present.

## Self-review repairs

The first material candidate `dbf4499d...` passed META CI and the temporary
path-scoped capability workflow, but whole-diff self-review found two hardening
gaps: trusted actor eligibility was too broad and same-name check-run spoofing
was not rejected. Head `a90fc145...` narrowed control actors to OWNER/MEMBER and
required the provider aggregate check to come from `github-actions`.

A subsequent policy review against `docs/governance/AI_REVIEW_POLICY.md` found
that the initial two-comment design was unnecessarily close to the retired
duplicate-comment proof-engine pattern. The final design uses one exact
Issue #196 request comment only. It remains transport, not merge authority; the
coordinator must already possess exact integration authority before creating it.

Focused local mocked validation on the final design produced 8 capability-routing
PASS and 12 governed-executor PASS; workflow and META CI YAML both parse.

The final design also folds deterministic capability/executor tests into the
existing required `meta-gate` instead of creating an additional persistent PR
status, reducing CI/control-plane duplication.

## Validation target

- exact-head `meta-gate` including:
  - existing META governance suites;
  - `test_integration_capability_routing.py`;
  - `test_governed_merge_queue_executor.py`;
- full-diff self-review;
- one independent Codex deep review because this materially changes GitHub
  Actions / token / Merge Queue execution routing;
- normal protected Merge Queue integration;
- protected-main readback;
- credential provisioning + real executor canary before
  `meta.governed_merge_queue_executor.v1` becomes `operational`.

No merge authorization is inferred.
