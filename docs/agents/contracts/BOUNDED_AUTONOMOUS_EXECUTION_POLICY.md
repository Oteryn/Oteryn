Warning: truncated output (original token count: 3995)
Total output lines: 259

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

Progress is measured from durable facts, not activity volume. The organization progress fingerprint is computed from the machine policy's selected fields, including repository/task identity, exact task head, phase, blocking dependency, dependency kind, gate state, review generation, **evidence generation**, and first material failure.

`evidence_generation` is a stable normalized coordinate for material non-repository facts that can legitimately change while the Git head does not, for example:

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

A frozen candidate may be…1995 tokens truncated… they do not independently declare terminal completion.

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

## Same-head asynchronous review evidence

When authenticated external review evidence arrives after a required gate evaluated the same exact candidate head, the preferred recovery is same-head control-plane re-evaluation, not Git mutation.

META's implementation uses `.github/workflows/governance-ai-review-recheck.yml` and `tools/governance/ai_review_recheck.py`. The recheck path:

- accepts only configured trusted reviewer result identities;
- resolves the current same-repository PR from live GitHub state;
- binds candidate identity through the linked PR's exact head SHA and trusted base SHA;
- treats `pull_request_target` run-level `head_sha` as the trusted base context, not as the candidate head;
- paginates workflow-run discovery within a bounded scan;
- rejects stale review commits;
- selects only the latest exact-PR/exact-head/exact-base eligible failed attempt-1 gate;
- re-reads PR head/base immediately before rerun to reject races;
- performs at most one automatic same-head rerun per evidence generation;
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
