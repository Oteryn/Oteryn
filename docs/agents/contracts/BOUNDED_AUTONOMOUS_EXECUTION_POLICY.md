# Bounded Autonomous Execution Policy

Status: active upon merge to protected `main`.

Lifecycle authority: `Oteryn/Oteryn#69`.

## Purpose

Autonomous execution must be persistent without becoming unbounded. A worker is required to continue useful authorized work, but it is not required or allowed to remain active while the only possible next step is an unchanged external wait, nor may it mutate a stable candidate merely to retrigger CI, review or other evidence.

This contract complements the central execution/continuation policy. Provider repositories may impose stricter validation, safety or retry limits, but may not weaken these minimum anti-loop semantics.

## Canonical lifecycle states

Every substantial autonomous task must be classifiable as one of:

- `RUNNING` — useful authorized local work is actively progressing;
- `WAITING_EXTERNAL` — no local mutation is justified and progress depends only on an external event such as CI completion, authenticated review evidence, another task, a provider result or observation window;
- `BLOCKED` — progress requires a missing permission, owner/policy decision, unsafe or irreversible choice, contradictory authority resolution or other dependency that cannot progress autonomously;
- `STALLED` — the allowed local retry budget was exhausted without a changed material progress/failure fingerprint;
- `READY` — the current candidate is coherent and may enter or continue final qualification/integration;
- `DONE` — completion has been independently verified against the applicable repository/control-plane requirements.

`WAITING_EXTERNAL` is not a failure and is not an invitation to poll. `STALLED` is not permission to bypass a gate. `DONE` is never inferred from worker narrative.

## Material progress

Progress is measured from durable facts, not activity volume. The organization progress fingerprint is computed from the machine policy's selected fields, including repository/task identity, exact task head, phase, blocking dependency, dependency kind, gate state, review generation and first material failure.

Timestamps, chat narration, repeated status prose, tool-call count and session duration are deliberately excluded. If those are the only things that changed, there was no material progress.

A worker must not claim progress merely because it repeated a command, re-read unchanged state, produced another summary or created a checkpoint with no new lifecycle fact.

## Candidate freeze

When implementation is coherent and final qualification begins, the candidate is frozen.

While `candidate_frozen=true`:

- do not create empty/no-op/checkpoint commits;
- do not change the task head only to retrigger CI, review, mergeability, polling or evidence collection;
- do not refresh a stable candidate merely because an asynchronous dependency has not completed yet;
- persist waiting/session state in the authorized task/control-room metadata surface instead of altering the candidate tree;
- preserve exact-head evidence until a material reason requires a real change.

A frozen candidate may be changed only for a material reason such as:

- a review finding;
- a failing required test;
- semantic reconciliation with authoritative upstream change;
- changed governing authority that materially affects the task.

A legitimate repair explicitly unfreezes the candidate, records the material reason, performs the smallest repair, produces one new exact task head, and freezes that new candidate before final qualification resumes.

## No-op and retrigger prohibition

The following are invalid execution strategies:

- empty commits;
- commits whose sole purpose is to wake or retrigger a workflow;
- metadata/checkpoint commits on the product candidate whose only purpose is to record that an external event is pending;
- repeated reviewer invocation for an unchanged review fingerprint beyond the configured budget;
- repeated full/heavy validation after the configured budget without first isolating or materially changing the failure path.

Control-plane rerun/re-evaluation facilities must be preferred when the candidate itself did not change.

## Retry budgets

The canonical organization defaults are machine-readable in `ecosystem/bounded-autonomous-execution-policy.json`:

- identical unchanged failure cycles: `2`;
- full/heavy validation attempts in one coherent repair cycle: `2`;
- primary external-review invocations per stable review fingerprint: `1`;
- automatic same-head AI-review gate rechecks per evidence generation: `1`.

A repository may lower these limits. Increasing them requires explicit provider justification and must not create an unbounded loop.

After identical local-failure budget exhaustion, enter `STALLED`, persist the exact first material failure and release the worker session. After an external-review invocation budget is consumed while evidence is still pending, enter `WAITING_EXTERNAL` and release the worker session.

## External waiting and session release

A task in `WAITING_EXTERNAL`, `BLOCKED`, `STALLED` or `DONE` has no reason to keep an active mutating worker session.

Before releasing the session, persist:

- exact repository/task/branch/PR identity;
- exact task head;
- current lifecycle state and phase;
- the blocking dependency or first material failure;
- progress/failure fingerprint when available;
- consumed retry counters;
- one concrete next action triggered by a changed external fact or a future takeover.

A replacement/continuation session re-verifies live state and resumes from the durable checkpoint. It does not replay the same unchanged action chain.

## Same-head asynchronous evidence

When an external evidence object arrives after a required gate has already evaluated the same exact candidate head, the preferred recovery is same-head control-plane re-evaluation, not Git mutation.

META's AI-review implementation uses `.github/workflows/governance-ai-review-recheck.yml` and `tools/governance/ai_review_recheck.py`. The recheck path:

- accepts only configured trusted reviewer result identities;
- binds to the exact current same-repository PR head;
- rejects stale review commits;
- selects only the latest exact-head `pull_request_target` AI-review gate run;
- re-runs it only when it completed with failure on attempt `1`;
- performs at most one automatic same-head rerun for that result generation;
- never checks out or executes candidate code;
- never receives repository-content write authority.

The existing evidence verifier remains authoritative. Re-evaluation cannot manufacture review evidence or convert an invalid result into PASS.

## Heavy validation

Full builds, E2E, soak or similarly expensive validation should normally run after coherent implementation. When a heavy attempt fails:

1. record the first material failure;
2. reproduce/isolate with the cheapest focused check available;
3. repair or materially change the failure path;
4. run the next heavy attempt only after that focused progress.

Two unchanged heavy failures are sufficient to prohibit a third blind full run under the organization default.

## Completion

`DONE` requires current, observable completion evidence appropriate to the repository. Depending on the task this can include exact-head CI, required review, merge state, resulting protected-main state, terminal branch/task lifecycle and provider-specific verification.

A worker that reaches `WAITING_EXTERNAL`, `BLOCKED` or `STALLED` truthfully ends the current session without claiming the overall task is complete. Autonomous continuation resumes only when a material external fact changes or a takeover has a new authorized action.