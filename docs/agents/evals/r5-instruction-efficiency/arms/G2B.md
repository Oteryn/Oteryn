# R5Q G2B

Short invocation:

```text
Oteryn: R5Q G2B
```

Read only `docs/agents/evals/r5-instruction-efficiency/TRIAL_PROTOCOL.md` as the shared R5Q harness. Do not inspect sibling arm files or the reviewer rubric.

Repository: `Oteryn/Oteryn-Game`

Source: current protected provider `main`.

On the first provider read, resolve protected `main`, record its exact commit and tree, and freeze that identity for the whole trial. Use ref-aware reads against that frozen commit thereafter. Do not switch to a newer `main` mid-trial.

## Task

Determine whether a named task packet whose owning Issue is terminal should remain active or become historical. Identify only the evidence required to decide. Do not modify anything.
Task ID: `OTV2-20260907-doc-consumer-snapshot-refresh`. Governing Issue: `Oteryn/Oteryn-Game#375`.

Answer directly, emit the protocol telemetry, then stop.
