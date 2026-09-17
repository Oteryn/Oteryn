# Oteryn Merge Queue capability routing repair

Governing Issue: #194
Control request Issue: #196
Admission META main: `3b39e0be05aef008f1bd442821daefa898a201dd`
Branch: `fix/194-capability-aware-mq-routing`
PR: #195
Status: `HISTORICAL`

> Current authority note: this file records the #195 implementation state. The
> dedicated `TrustedCapabilityObserver` / sealed-observation provenance mechanism
> described below is superseded by #214 after that change reaches protected META
> `main`. #214 retains the capability preflight and all substantive direct/delegated
> route invariants while allowing fresh typed current-session evidence directly.

## Problem

The current organization policy correctly fails closed when a session cannot
invoke the selected native exact-head `merge-async` operation, but execution
routing does not determine that integration capability before an implementation
worker is released. A candidate can therefore finish implementation, validation
and handoff before the coordinator discovers that its current tool surface
cannot submit the PR to Merge Queue.

## Implemented repair

The following records the original #195 implementation state:

1. `ecosystem/agent-execution-routing-policy.json` now contains a closed
   `integration_capability_routing` contract for protected integration.
2. `tools/governance/integration_capability_routing.py` acquired evidence through
   an installed trusted observer and then deterministically classified the sealed
   observation as `NOT_REQUIRED`, `DIRECT_CAPABLE`, `DELEGATED_CAPABLE` or
   `BLOCKED_CAPABILITY_UNAVAILABLE`. Raw mappings/JSON were diagnostic fixtures only
   and could not authorize worker release. This provenance wrapper is the portion
   superseded by #214; the deterministic route checks remain.
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
10. The standalone router CLI had no authoritative serialized-snapshot input. It
    failed closed when no current-session discovery/readback observer was installed.
    #214 retains the no-snapshot rule but removes the observer-wrapper requirement.
11. Delegated preflight binds the current session's actual control-comment actor
    to the fine-grained credential principal; missing, malformed or mismatched
    identities block worker release while direct capability remains independent.
12. The request carries the exact canary-qualified protected META `main` SHA. The
    sealed capability decision retains that evidence-supplied SHA for canonical
    request construction; a caller-supplied current-main SHA cannot replace it.
    The executor checks out trusted `main`, fences it to the qualified SHA, and
    live-re-reads `main` immediately before mutation rather than trusting
    `github.sha`.
13. Atlas source qualification queries its canonical `pull_request_target` runs
    without a PR-head-SHA filter and binds each base-main run through a non-empty
    exact target-PR relation.

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
- HTTP 202 requires immediate durable emission of a non-secret UUID-bound
  `REQUEST_ACCEPTED_NON_TERMINAL` receipt before any status/target readback, then
  strictly-later UUID-bound readback. Later failure requires reconciliation by
  that UUID and never repetition of the request.
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
