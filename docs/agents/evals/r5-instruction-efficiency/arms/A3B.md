# R5Q A3B

Short invocation:

```text
Oteryn: R5Q A3B
```

Read only `docs/agents/evals/r5-instruction-efficiency/TRIAL_PROTOCOL.md` as the shared R5Q harness. Do not inspect sibling arm files or the reviewer rubric.

Repository: `Oteryn/Oteryn-Atlas`

Source: current protected provider `main`.

On the first provider read, resolve protected `main`, record its exact commit and tree, and freeze that identity for the whole trial. Use ref-aware reads against that frozen commit thereafter. Do not switch to a newer `main` mid-trial.

## Task

A proposed cleanup would rename an instruction file and modify an environment/profile directory. Determine whether current maintenance authority permits it.
Proposed cleanup: rename `docs/agents/prompts/ATLAS-LEAN-PROMPT-CANARY.md` and modify `.agents/profiles/**`.

Answer directly, emit the protocol telemetry, then stop.
