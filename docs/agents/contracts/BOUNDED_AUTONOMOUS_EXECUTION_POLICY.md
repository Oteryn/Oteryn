# Bounded Autonomous Execution Policy

Status: active upon merge to protected `main`.

Lifecycle authority: `Oteryn/Oteryn#69`.

Machine-readable authority: `ecosystem/bounded-autonomous-execution-policy.json`.

## Purpose

Autonomous execution must be persistent without becoming unbounded. A worker is required to continue useful authorized work, but it must not repeat an unchanged action chain, keep an active session while only an external event can make progress, or mutate a stable candidate merely to retrigger CI, review or other evidence.

This contract complements the central execution/access/routing policy. Provider repositories may impose stricter validation, safety or retry limits, but may not weaken these minimum anti-loop semantics.

The policy addresses two different loop classes:

1. **no-progress execution loops** — unchanged failure, CI/review waiting, repeated heavy validation, no-op/retrigger commits;
2. **late-finding closeout loops** — final candidate → late material finding → repair → full qualification → another late finding → another full qualification.

Both classes are bounded and fail closed.

## Canonical lifecycle states

Every substantial autonomous task must be classifiable as one of:

- `RUNNING` — useful authorized local work is actively progressing;
- `WAITING_EXTERNAL` — no local mutation is justified and progress depends only on an external event such as CI completion, authenticated review evidence, another task, a provider result or an observation window;
- `BLOCKED` — progress requires a missing permission, owner/policy decision, unsafe or irreversible choice, contradictory authority resolution or another dependency that cannot progress autonomously;
- `STALLED` — an allowed local retry budget was exhausted without a material progress/failure change;
- `READY` — the coherent implementation may enter or continue final qualification/integration;
- `DONE` — completion has been independently verified against the applicable repository/control-plane requirements.

`WAITING_EXTERNAL` is not a failure and is not an invitation to poll. `STALLED` is not permission to bypass a gate. `DONE` is never inferred from worker narrative.

## Material progress and evidence generations

Progress is measured from durable facts, not activity volume. The organization progress fingerprint is computed from the machine policy's selected fields, including repository/task identity, exact task head, phase, blocking dependency, dependency kind, gate state, the trusted review-binding scope, and first material failure. Raw caller-supplied `review_generation` and `evidence_generation` labels are retained only as descriptive checkpoint coordinates; they are not progress or retry-budget authority.

Material non-repository progress must be represented by a trusted durable coordinate, such as a changed canonical review binding or verified material-fact envelope. Examples include:

- a required dependency advances;
- authenticated review evidence arrives;
- an unresolved material finding is resolved or the material finding set changes;
- a required external gate changes state for reasons not caused by candidate mutation.

Timestamps, chat narration, repeated status prose, tool-call count and session duration are deliberately excluded. If only those facts changed, there was no material progress.

A worker must not claim progress merely because it repeated a command, re-read unchanged state, produced another summary or created a checkpoint with no new lifecycle fact.

## Candidate freeze

When implementation is coherent and final qualification begins, the candidate is frozen.

While `candidate_frozen=true`:

- do not create empty/no-op/checkpoint commits;
- do not change the task head only to retrigger CI, review, mergeability, polling or evidence collection;
- do not refresh a stable candidate merely because an asynchronous dependency has not completed yet;
- persist waiting/session state in an authorized task/control-plane metadata surface instead of altering the candidate tree;
- preserve exact-head evidence until a material reason requires a real technical change.

A frozen candidate may be changed only for a material reason such as:

- a review finding;
- a failing required test;
- semantic reconciliation with authoritative upstream change;
- changed governing authority that materially affects the task.

A legitimate repair is an atomic control-plane transition, not a worker assertion. `observe` may not alter freeze, material-fact, repair, counter, review-binding, completion or risk-ledger fields. Opening `open_material_repair` requires a `MaterialFactEnvelope` verified by a trusted authority and canonically tied to the repository, task, exact frozen head, immutable policy ID/digest, allowlisted reason and source evidence. The durable checkpoint/outbox must then compare-and-swap the prior checkpoint while it creates the one repair reservation. No snapshot boolean such as `material_fact_verified`, nor a proposed `material_change=true`, is evidence or authority. The committed repair checkpoint records the envelope ID as its `repair_generation_id`, retains `repair_base_head`, and increments `post_freeze_material_head_changes` exactly once.

While that repair generation is open, its verified envelope and base coordinates remain immutable; one or more real technical changes may be made without consuming a second generation. Refreezing is a reserved transition and is allowed only after the candidate has a new technical head **and** a changed trusted review-risk binding. `retrigger` is never a material repair action. The worker then freezes the new candidate before final qualification resumes.

`complete` is admitted only from `final_qualification` with that exact candidate frozen; verified completion evidence alone cannot bypass either invariant.

Every consuming or security-sensitive action requires an injected durable checkpoint/outbox adapter. It atomically advances checkpoint `R → R+1`, creates one deterministic unique reservation, and permits dispatch only after that reservation committed; a CAS loser cannot dispatch and a replay can claim dispatch at most once. A standalone guard/CLI with no such adapter returns `allowed=false` with `reservation_required`. Snapshot revision/reservation fields are never a substitute for this protocol.

## No-op and retrigger prohibition

The following are invalid execution strategies:

- empty commits;
- commits whose sole purpose is to wake or retrigger a workflow;
- metadata/checkpoint commits on the technical candidate whose only purpose is to record that an external event is pending;
- repeated reviewer invocation for an unchanged review generation beyond the configured budget;
- repeated full/heavy validation after the configured budget without first isolating or materially changing the failure path.

Control-plane rerun/re-evaluation facilities must be preferred when the candidate itself did not change.

## Retry budgets and generation scopes

The canonical organization defaults are machine-readable in `ecosystem/bounded-autonomous-execution-policy.json`:

- identical unchanged failure cycles: `2`;
- full/heavy validation attempts for one exact technical head: `2`;
- primary external-review invocations for one trusted canonical review binding: `1`;
- same-head external-evidence re-evaluations for one exact head/evidence generation: `1`.

Durable counters may reset only when **their own generation scope** changes. Unrelated phase, status, narration or gate-field changes do not reset a consumed budget.

The policy's `progress_fingerprint_fields` is a closed organization-owned material field set. Providers may not append timestamps, narration, or other nonmaterial fields, nor omit a canonical field, because doing so could manufacture apparent progress.

Canonical scopes are:

- `identical_failure_cycles` — exact task head plus failure fingerprint;
- `heavy_validation_runs` — exact task head;
- `external_review_invocations` — trusted canonical review-binding scope (repository/task, tier, immutable policy ID/digest, classifier revision and risk fingerprint), never SHA alone;
- `same_head_gate_rechecks` — exact task head plus trusted canonical review-binding scope.

A continuation/takeover may not bypass an exhausted budget by omitting a previous snapshot. Exhaustion recorded in the current durable state is authoritative. Each bounded action reserves exactly one increment in a proposed current checkpoint relative to its durable previous checkpoint; a replay without that increment is denied. A generation reset is a separate transition that resets only its own counter to zero. Boolean JSON values are not valid integer counters and fail closed.

A zero-retry policy means no retry after a failed attempt; it does not prevent the initial attempt when no failure exists yet.

A repository may lower these limits. Increasing them requires explicit provider justification and must not create an unbounded loop.

## Trusted review bindings

`review_fingerprint` supplied in a task snapshot is opaque legacy data and has no authorization or reset authority. A `ReviewBinding` is accepted only when its canonical digest validates and an injected trusted classifier/attestation authority verifies it. It binds repository, task, base/head, tier, policy ID/digest, classifier revision and risk fingerprint. The immutable tier/policy identity is included in the external-review generation scope. An arbitrary binding change fails closed; a trusted canonical risk change is the only path that can reset that review budget.

The standalone guard is intentionally unable to manufacture these proofs. It may observe an unchanged snapshot, but it cannot execute a consuming or security-sensitive transition without both the trusted evidence authority and the durable checkpoint/outbox adapter.

## External waiting and session release

A task in `WAITING_EXTERNAL`, `BLOCKED`, `STALLED` or `DONE` has no reason to keep an active mutating worker session.

Before releasing the session, persist:

- exact repository/task/branch/PR identity;
- exact task head;
- current lifecycle state and phase;
- blocking dependency or first material failure;
- progress/failure fingerprint when available;
- evidence generation and canonical review fingerprint when applicable;
- verified material-fact and repair-generation coordinates when a frozen candidate has been reopened;
- consumed retry counters;
- loop-breaker counters/ledger when applicable;
- one concrete next action triggered by a changed material fact or future takeover.

A replacement/continuation session re-verifies live state and resumes from the durable checkpoint. It does not replay the same unchanged action chain.

## LOOP_BREAKER_AUDIT for repeated late closeout findings

Ordinary serial closeout is no longer permitted after evidence shows that the final-candidate review model is missing material defect classes.

A `LOOP_BREAKER_AUDIT` becomes mandatory when **either** of these conditions is reached after the candidate first entered final qualification/freeze:

- `late_material_findings >= 2`; or
- `post_freeze_material_head_changes >= 2`.

A late material finding is a `P0`, `P1`, `P2`, or repository-equivalent material/blocking review finding discovered after final-candidate entry. A post-freeze material head change is a genuine technical repair/reconciliation commit after freeze; no-op/retrigger/metadata churn is forbidden rather than counted.

Once either threshold is reached:

1. ordinary external-review/final-validation/final-qualification cycling is denied;
2. enter explicit `LOOP_BREAKER_AUDIT` phase;
3. construct one bounded batched risk ledger for the **whole technical diff**;
4. audit independent risk classes together rather than rediscovering them serially;
5. repair all material findings from that audit generation coherently;
6. complete technical freeze before final metadata/evidence freeze;
7. authorize at most **one new final qualification generation** for that completed audit generation.

A material finding after that final qualification generation invalidates the generation and reopens `LOOP_BREAKER_AUDIT`; the worker does not continue an ordinary finding→CI→finding→CI loop.

## Canonical risk ledger

The loop-breaker ledger contains exactly these organization risk classes:

1. `identity_binding`
2. `authority_relay`
3. `epoch_deadline`
4. `retry_budget`
5. `concurrency_replay`
6. `transaction_persistence`
7. `negative_paths`
8. `ci_governance`

Each class is one of:

- `PENDING` — not yet proven clear;
- `AUDITED_PASS` — reviewed against the exact current technical candidate with no unresolved material finding;
- `NOT_APPLICABLE` — genuinely outside this task's semantics, with a non-empty reason.

The ledger is terminal only when every class is `AUDITED_PASS` or justified `NOT_APPLICABLE` **and** the audit counters match the current late-finding/head-change generation. If a new material finding or post-freeze technical change appears after the audit, the audit is stale and must be renewed before another final qualification.

`all review threads resolved` is necessary but **not sufficient** for READY/DONE. Thread cleanliness cannot substitute for risk-ledger completeness, exact-head required checks, required review evidence, repository-specific merge predicates or protected-main readback.

## Batched review and parallelism

`LOOP_BREAKER_AUDIT` is batched, not blindly parallel.

Independent risk classes should be reviewed in separate lanes only when the current central execution-routing/effort authority determines that separation is safe and provides real benefit. Do not create parallel agents merely to satisfy a parallelism preference. Do not assign overlapping writable paths or the same critical workflow to independent writers without an explicit integration reason.

The coordinator owns deduplication and synthesis of findings. Review lanes report findings; they do not independently declare terminal completion.

## Technical freeze before metadata freeze

Technical evidence and metadata have different purposes.

Before final qualification:

1. complete implementation and material repair work;
2. complete the applicable risk ledger on the exact technical candidate;
3. freeze the technical tree;
4. only then update final task/evidence metadata if repository policy requires it;
5. do not create additional metadata commits merely to record waiting/retrigger state;
6. run the final exact-head qualification once on the final candidate.

If task metadata itself is a required tracked file, combine its final truthful evidence update with the last necessary candidate generation whenever safe. Never use metadata movement as a workflow wake-up mechanism.

## One final qualification generation

After a current `LOOP_BREAKER_AUDIT`, the policy authorizes exactly one new final qualification generation. That generation may contain all required exact-head checks and required reviewer evidence, but it must not be multiplied by no-op head changes or duplicate reviewer invocations.

If a material finding appears:

- record it;
- invalidate the qualification generation;
- return to the loop-breaker ledger;
- batch the newly exposed risk before another qualification generation.

If only external evidence is pending, enter `WAITING_EXTERNAL` and preserve the head.

## Same-head asynchronous evidence

When authenticated external evidence arrives after a gate evaluated the same exact candidate head, prefer one bounded same-head control-plane re-evaluation over Git mutation. This is a generic orchestration constraint, not a required-status implementation or external-review merge authority. META does not own a scheduler, poller, reviewer-result parser, or dedicated review gate for this behavior.

## Heavy validation

Full builds, E2E, soak or similarly expensive validation should normally run after coherent implementation. When a heavy attempt fails:

1. record the first material failure;
2. reproduce/isolate with the cheapest focused check available;
3. repair or materially change the failure path;
4. run the next heavy attempt only after that focused progress.

Two unchanged heavy failures are sufficient to prohibit a third blind full run under the organization default.

## Completion

`DONE` requires current, observable completion evidence appropriate to the repository. Depending on the task this can include:

- terminal risk ledger when loop-breaker semantics apply;
- exact-head required CI/checks;
- required authenticated review evidence;
- no unresolved material findings;
- required review threads resolved;
- merge state;
- resulting protected-main state/readback;
- terminal branch/task lifecycle;
- provider-specific verification.

A `DONE` snapshot is terminal: it cannot be paired with a retrigger/no-op operational intent.

A worker that reaches `WAITING_EXTERNAL`, `BLOCKED` or `STALLED` truthfully ends the current session without claiming the overall task is complete. Autonomous continuation resumes only when a material fact changes or a takeover has a new authorized action.
