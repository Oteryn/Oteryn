# R5Q P3A

Short invocation:

```text
Oteryn: R5Q P3A
```

Read only `docs/agents/evals/r5-instruction-efficiency/TRIAL_PROTOCOL.md` as the shared R5Q harness. Do not inspect sibling arm files or the reviewer rubric.

Repository: `Oteryn/Oteryn-Platform`

Historical provider commit: `3557085c20512d25576d8884cc54471665784b00`
Historical provider tree: `67dd1ef42dc0f6b247fbc5538214ebe35bcc5352`

Use ref-aware immutable reads for provider files. Do not use default-branch code search or another primitive that silently searches current provider `main`. If a needed search primitive cannot target this historical ref, record `SEARCH_UNAVAILABLE_FOR_FAIRNESS` and use bounded ref-aware tree/directory inspection.

Follow provider instructions as they existed at this ref, including immutable external references they explicitly require. Do not substitute current provider or current META policy.

## Task

Determine the minimum authoritative sources required before implementing an authenticated idempotent webhook write involving transaction boundaries and reconciliation. Do not implement it.

Answer directly, emit the protocol telemetry, then stop.
