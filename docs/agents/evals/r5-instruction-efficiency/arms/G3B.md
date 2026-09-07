# R5Q G3B

Short invocation:

```text
Oteryn: R5Q G3B
```

Read only `docs/agents/evals/r5-instruction-efficiency/TRIAL_PROTOCOL.md` as the shared R5Q harness. Do not inspect sibling arm files or the reviewer rubric.

Repository: `Oteryn/Oteryn-Game`

Source: current protected provider `main`.

On the first provider read, resolve protected `main`, record its exact commit and tree, and freeze that identity for the whole trial. Use ref-aware reads against that frozen commit thereafter. Do not switch to a newer `main` mid-trial.

## Task

Determine the minimum authoritative sources required before changing a rule involving WorldId, ChannelId and session-generation fencing. Do not design or implement the change.

Answer directly, emit the protocol telemetry, then stop.
