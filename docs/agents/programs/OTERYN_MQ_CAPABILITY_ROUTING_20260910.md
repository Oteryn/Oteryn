# Oteryn Merge Queue capability routing repair

Governing Issue: #194
Admission META main: `3b39e0be05aef008f1bd442821daefa898a201dd`
Branch: `fix/194-capability-aware-mq-routing`
Status: `IMPLEMENTING`

## Problem

The current organization policy correctly fails closed when a session cannot invoke the selected native exact-head `merge-async` operation, but execution routing does not determine that integration capability before an implementation worker is released. A candidate can therefore finish implementation, validation and handoff before the coordinator discovers that its current tool surface cannot submit the PR to Merge Queue.

## Intended repair

1. Model protected integration capability separately from ordinary implementation execution targets.
2. Require a verified integration-capability preflight before releasing mutating work that is expected to require autonomous protected integration.
3. Preserve three deterministic states: `DIRECT_CAPABLE`, `DELEGATED_CAPABLE`, `BLOCKED_CAPABILITY_UNAVAILABLE`.
4. Keep authority separate from capability: a delegated executor may execute only a previously authorized exact-target queue mutation and does not become a coordinator or merge authority.
5. Provide one META-owned bounded executor for the already-selected native `merge-async` route. Do not recreate provider-specific custom-App bridges.
6. Keep direct merge, generic auto-merge, GraphQL enqueue, bypass, force, default merge action, no-op/retrigger commits and ambiguous dequeue forbidden.
7. Keep built-in `GITHUB_TOKEN` read-only for queue mutation. The delegated executor may use only a separately provisioned fine-grained credential already permitted by META 3.1; no credential value is created, read or stored by this change.

## Planned owned paths

- `ecosystem/agent-execution-routing-policy.json`
- `tools/governance/integration_capability_routing.py`
- `tools/governance/test_integration_capability_routing.py`
- `tools/governance/governed_merge_queue_executor.py`
- `tools/governance/test_governed_merge_queue_executor.py`
- `.github/workflows/governed-merge-queue-executor.yml`
- `docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md`
- `docs/agents/operations/MERGE_QUEUE_EXECUTOR.md`
- `docs/agents/programs/OTERYN_MQ_CAPABILITY_ROUTING_20260910.md`

## Excluded scope

No provider runtime/product implementation, production action, branch protection/ruleset/required-check mutation, secret value, credential provisioning, direct merge, provider-specific bridge duplication or Remote Desktop route.

## Validation target

- deterministic capability-routing tests;
- deterministic executor tests with mocked GitHub responses only;
- repository META CI on the exact published head;
- full-diff self-review;
- independent review according to current AI review policy before integration.

No merge authorization is inferred from this task record.
