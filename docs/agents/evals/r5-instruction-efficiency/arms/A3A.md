# R5Q A3A

Short invocation:

```text
Oteryn: R5Q A3A
```

Read only `docs/agents/evals/r5-instruction-efficiency/TRIAL_PROTOCOL.md` as the shared R5Q harness. Do not inspect sibling arm files or the reviewer rubric.

Repository: `Oteryn/Oteryn-Atlas`

Historical provider commit: `51623c7dab2346cee39cd51e3caa845bf4b65426`
Historical provider tree: `8d5b8f1ea3bf636698b8cf7cc81fe434f19f58df`

Use ref-aware immutable reads for provider files. Do not use default-branch code search or another primitive that silently searches current provider `main`. If a needed search primitive cannot target this historical ref, record `SEARCH_UNAVAILABLE_FOR_FAIRNESS` and use bounded ref-aware tree/directory inspection.

Follow provider instructions as they existed at this ref, including immutable external references they explicitly require. Do not substitute current provider or current META policy.

## Task

A proposed cleanup would rename an instruction file and modify an environment/profile directory. Determine whether current maintenance authority permits it.
Proposed cleanup: rename `docs/agents/prompts/ATLAS-LEAN-PROMPT-CANARY.md` and modify `.agents/profiles/**`.

Answer directly, emit the protocol telemetry, then stop.
