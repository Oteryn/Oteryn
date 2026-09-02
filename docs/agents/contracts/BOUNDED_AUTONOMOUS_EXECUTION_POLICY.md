# Bounded Autonomous Execution Policy

Status: active upon merge to protected `main`.

Lifecycle authority: `Oteryn/Oteryn#69`.

Machine policy: `ecosystem/bounded-autonomous-execution-policy.json`.

## Purpose and scope

Autonomous work must continue while useful authorized progress is possible, without
repeating an unchanged action chain. This is a deterministic coordination policy,
not an external service or repository lifecycle authority. GitHub and the repository's
current governance remain
authoritative for repository lifecycle facts.

## Lifecycle

The canonical states are:

- `RUNNING`: useful authorized work is progressing;
- `WAITING_EXTERNAL`: progress depends on an external dependency;
- `BLOCKED`: an owner, permission or policy decision is required;
- `STALLED`: a bounded local retry budget was exhausted unchanged;
- `READY`: the candidate is ready for applicable qualification;
- `DONE`: a caller-provided completion-verification fact has been accepted.

`WAITING_EXTERNAL`, `BLOCKED`, `STALLED` and `DONE` release active worker ownership.
Observation remains allowed. Operational work may resume from a released nonterminal
state only after the material progress fingerprint changes. `DONE` is terminal.

## Material fingerprints

The progress fingerprint is the deterministic digest of repository, task, exact
technical head, phase, dependency, dependency kind, gate state and first material
failure. The failure fingerprint uses the same material facts. Timestamps, narration,
session duration and tool-call volume are excluded and never establish progress.

Changing `main` alone is not a material task invalidation and is not a fingerprint
coordinate. Late integration is governed by the current canonical integration policy.

## Candidate freeze

A candidate freezes when final qualification begins. An unchanged frozen candidate
must not be mutated or retriggered. `mutate` may proceed only when the material
fingerprint actually changes and a permitted material reason is recorded, such as a
review finding, failing required test, semantic reconciliation or changed authority.
`retrigger` is never justified by empty, no-op, checkpoint or narration-only churn.

## Bounded local retries

The organization defaults are:

- two identical unchanged failure retries;
- two heavy/full validation attempts for one exact technical head.

Exhaustion produces `STALLED` and releases ownership. A configured zero retry budget
allows no retry after the initial failed attempt. Counters are durable caller facts;
they cannot be negative, boolean, or reset by narration or timestamps.

## Dependencies and completion

An external dependency produces `WAITING_EXTERNAL`. An owner, permission or policy
dependency produces `BLOCKED`. Only observation is allowed while the unchanged
dependency remains.

`DONE` requires an explicit caller-provided completion-verification fact and is
terminal. This module deliberately does not recreate GitHub merge, review, check or
attestation authority; callers obtain and verify the applicable completion fact under
current repository governance before presenting it to the guard.
