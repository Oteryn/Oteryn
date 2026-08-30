# Bounded Autonomous Execution — 2026-08-30 Loop-Breaker Amendment

Status: approved owner-directed amendment to `2026-08-25-bounded-autonomous-execution-design.md`.

Authority: Issue `Oteryn/Oteryn#69`, normative contract `docs/agents/contracts/BOUNDED_AUTONOMOUS_EXECUTION_POLICY.md`, machine policy `ecosystem/bounded-autonomous-execution-policy.json`.

This amendment supersedes any conflicting pre-2026-08-30 design text. It was added after a real late-finding closeout loop in `Oteryn/Oteryn-Game` demonstrated that no-progress retry limits alone do not prevent repeated final-candidate → late finding → repair → full qualification cycles.

## Added failure class

The original design bounded unchanged retries and asynchronous waiting. The organization now also bounds **late-finding closeout churn**.

After either:

- the second late material `P0/P1/P2` (or repository-equivalent material/blocking finding) discovered after final-candidate entry; or
- the second genuine technical head change from a previously frozen candidate,

ordinary serial closeout is forbidden. The task enters `LOOP_BREAKER_AUDIT` before another final qualification generation.

## Batched risk audit

The coordinator audits the whole technical diff against the canonical risk classes:

- `identity_binding`
- `authority_relay`
- `epoch_deadline`
- `retry_budget`
- `concurrency_replay`
- `transaction_persistence`
- `negative_paths`
- `ci_governance`

Independent lanes may run in parallel only when the current central execution-routing/effort authority says that parallelism is safe and useful. The loop-breaker itself does not force parallel agents.

The ledger is required only when the loop-breaker threshold/audit state is reached (or audit/final-generation state has already been recorded). Ordinary pre-threshold snapshots remain compatible without an eight-class ledger.

A completed audit must cover the whole observed late-finding/head-change generation. `NOT_APPLICABLE` requires a reason. Audit counters may advance only through `LOOP_BREAKER_AUDIT`; a worker cannot self-certify an audit by editing counters during ordinary finalization.

## Frozen-head accounting

A durable transition from `candidate_frozen=true` to `candidate_frozen=false` opens one repair generation and increments `post_freeze_material_head_changes` exactly once, even if the technical head has not moved yet. It may open only from an already-recorded, independently verified material fact bound to the prior frozen head; a proposed `material_change=true` flag is not evidence. The generation retains immutable fact/base coordinates while repair is open, and refreezing requires both a new technical head and a changed canonical review/risk fingerprint.

This prevents the bypass `frozen A → unfrozen A → B` and makes the threshold enforceable from snapshot history rather than worker narration or SHA-only movement.

## Qualification-generation accounting

After a current loop-breaker audit, exactly one new final qualification generation is available.

The `enter_final_qualification` admission snapshot must durably consume that generation before the guard authorizes entry. Reusing an unchanged pre-admission snapshot does not authorize repeated qualifications. A renewed audit resets generation consumption to zero only when the audit itself advances to cover the current observed generation.

Any new material finding after qualification makes the audit stale and reopens `LOOP_BREAKER_AUDIT` instead of returning to an unbounded serial closeout cycle.

## Retry semantics amendment

Retry budgets are non-negative integers; Python booleans are invalid.

For `identical_failure_cycles`, a configured budget of `0` means **no retry after a material failure**. It does not suppress the initial attempt when no material failure exists yet. Heavy-validation/reviewer/recheck budgets of `0` mean those optional actions are not admitted for that policy generation.

Counters remain monotonic inside their true generation scopes and cannot be reset by unrelated phase/status/narration changes or by omitting a previous snapshot when current durable exhaustion is already recorded. A bounded action consumes exactly one action-specific counter increment from the durable previous checkpoint; the action must be dispatched through compare-and-swap persistence and an idempotency key so a replay cannot spend the same reservation twice.

Primary external review is scoped to the canonical review fingerprint, not task-head SHA. A review-neutral SHA move does not authorize a fresh Codex review or reset its budget.

## Same-head review amendment

For `pull_request_target`, the workflow run's top-level `head_sha` is the trusted base execution context, not the candidate identity.

Candidate authority is bound through the linked pull request using all of:

- exact PR number;
- exact linked PR head SHA;
- exact trusted base SHA.

Workflow-run discovery is bounded and paginated without filtering by candidate `head_sha`. Live PR coordinates are re-read immediately before the rerun. Stale head/base, cross-repository identity, malformed history, already-retried or non-failed runs fail closed.

## Freeze ordering and completion

Technical freeze precedes final metadata/evidence freeze. Metadata movement is not a retrigger mechanism.

Clean review threads are necessary but not sufficient. Terminal completion still requires the applicable risk ledger, exact-head required checks, authenticated required review evidence, repository merge predicates and protected-main readback.
