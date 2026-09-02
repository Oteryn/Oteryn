# Bounded Autonomous Execution Policy

Status: active upon merge to protected `main`.

Lifecycle authority: `Oteryn/Oteryn#69`.

Machine policy: `ecosystem/bounded-autonomous-execution-policy.json`.

## Purpose and scope

Autonomous work must continue while useful authorized progress is possible, without
repeating an unchanged action chain. This is a deterministic coordination policy,
not an external service or repository lifecycle authority. GitHub and the repository's
current governance remain authoritative for repository lifecycle facts.

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

## Durable predecessor binding

Every operational action (`mutate`, `retrigger`, `retry`, `run_heavy_validation` or
`complete`) requires a durable previous snapshot. The predecessor must belong to the
same stable task identity: repository plus task id. A missing predecessor cannot be
interpreted as material progress. Observation and fail-closed dependency
classification may still occur without a predecessor.

## Material fingerprints

The progress fingerprint is the deterministic digest of repository, task, exact
technical head, phase, dependency, dependency kind, gate state and first material
failure. The failure fingerprint uses the same material facts. Timestamps, narration,
session duration and tool-call volume are excluded and never establish progress.

Changing `main` alone is not a material task invalidation and is not a fingerprint
coordinate. Late integration is governed by the current canonical integration policy.

## Candidate freeze

A candidate freezes when final qualification begins. An unchanged frozen candidate
must not be mutated or retriggered. Freeze remains authoritative for the same exact
technical head: a caller cannot thaw a candidate by setting `candidate_frozen` to
false in a later snapshot. `mutate` may proceed only when the material fingerprint
actually changes and a permitted material reason is recorded, such as a review
finding, failing required test, semantic reconciliation or changed authority. Such an
admitted same-head mutation remains frozen. A new technical head may establish a new
freeze coordinate. `retrigger` is never justified by empty, no-op, checkpoint or
narration-only churn.

## Bounded local retries

The organization defaults are:

- two identical unchanged failure retries;
- two heavy/full validation attempts for one exact technical head.

Exhaustion produces `STALLED` and releases ownership. A configured zero retry budget
allows no retry after the initial failed attempt. Counters are durable caller facts;
they cannot be negative, boolean, or reset by narration or timestamps. The identical
failure counter cannot decrease while the failure fingerprint is unchanged. The heavy
validation counter cannot decrease while the exact technical head is unchanged. A
counter may reset only when its defining scope changes.

## Dependencies and completion

`dependency_kind` is a closed coordinate: `none`, `external`, `owner`, `permission`
or `policy`. Unsupported values fail closed rather than falling through to operational
work. A non-empty blocking dependency also requires a blocking dependency kind.

An external dependency produces `WAITING_EXTERNAL`. An owner, permission or policy
dependency produces `BLOCKED`. Only observation is allowed while the unchanged
dependency remains.

`DONE` requires an explicit caller-provided completion-verification fact and is
terminal. This module deliberately does not recreate GitHub merge, review, check or
attestation authority; callers obtain and verify the applicable completion fact under
current repository governance before presenting it to the guard.
