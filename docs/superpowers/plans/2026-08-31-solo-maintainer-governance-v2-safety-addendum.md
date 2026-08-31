# Solo-Maintainer Governance V2 — Safety Implementation Addendum

> **For agentic workers:** Read this addendum together with `docs/superpowers/plans/2026-08-31-solo-maintainer-governance-v2.md` and `docs/superpowers/specs/2026-08-31-solo-maintainer-governance-v2-safety-amendment.md`. The safety amendment is normative where any conflict exists.

**Goal:** Make the Solo-Maintainer Governance V2 rollout prove the historical moving-head failure mode is eliminated, prevent aggregate-gate false positives, bound temporary transitions, and prevent governance self-modification from autonomously authorizing itself.

**Architecture:** Keep the original V2 architecture. Add a small global safety contract and deterministic acceptance tests; do not introduce a new governance service, transition database, attestation bridge or second required status.

**Tech Stack:** GitHub Actions, GitHub Merge Queue, repository-local deterministic tests, META read-only drift auditor, GitHub Issues/PRs for durable transition/owner receipts.

**Spec:** `docs/superpowers/specs/2026-08-31-solo-maintainer-governance-v2-safety-amendment.md`

## Global Safety Contract

Every task in the base implementation plan implicitly includes these invariants:

```text
GS-1  No moving-head governance dependency
GS-2  No mandatory second-human dependency in solo-maintainer mode
GS-3  Required aggregate gate cannot pass via skipped/neutral
GS-4  No governance retrigger/no-op commits
GS-5  Control-plane changes cannot autonomously self-authorize
GS-6  Every TRANSITION is bounded and expiring
GS-7  MQ canary must include a moving-base scenario
GS-8  Break-glass restoration must be independently verifiable
GS-9  Exactly one externally required aggregate gate per permanent repo
GS-10 New governance mechanisms require explicit threat justification
```

A task is not complete merely because its local tests are green if it violates one of these invariants.

---

### Addendum Task A: Encode the Global Safety Contract in META authority

**Applies before:** Base Plan Task 1 terminalization.

**Files:**
- Modify: `docs/architecture/adr/0002-organization-governance-operating-model.md`
- Modify: `ecosystem/governance-desired-state.json` only for stable target fields
- Modify: `tools/governance/audit_github_readonly_core.py`
- Modify: `tools/governance/test_audit_github_readonly.py`
- Modify: `tools/governance/test_audit_github_readonly_terminal.py`

**Required implementation:**

- [ ] Add a dated ADR amendment that references all GS-1..GS-10 invariants.
- [ ] Keep desired state small: do not store transient review generations, transient PR heads or a permanent transition database in `governance-desired-state.json`.
- [ ] Add audit tests that fail if a permanent repository's target required-status set contains anything other than its single aggregate gate.
- [ ] Add audit tests that reject a solo-maintainer baseline requiring human/CODEOWNER approval.
- [ ] Add audit tests for `TRANSITION` expiry: an active transition past `expires_at` without terminal success/rollback must classify as `DRIFT`, and a receipt whose `closed_at > expires_at` must remain `DRIFT` even if it later declares success or rollback.
- [ ] Add audit tests that a serially unstarted repository is explicit `PENDING`, not `DRIFT` or `TRANSITION`, only when a canonical-rollout pending baseline with `repository`, `captured_at`, `pre_state_fingerprint`, and `pre_state_readback` recomputes correctly and matches current live state; its unique top-level GitHub lifecycle record must direct-read `created_at == updated_at`. Missing, edited, duplicate, malformed, or mismatching baseline is `DRIFT`; an unreadable required live field is `UNKNOWN`. `PENDING` authorizes no settings deviation and blocks terminal V2 closeout.
- [ ] Add audit tests that a restored failed cutover is `ROLLED_BACK` only with `terminal_status = ROLLED_BACK`, timely `closed_at <= expires_at`, matching pre/post-state fingerprints and positive readback; otherwise classify `DRIFT`, and reject `ROLLED_BACK` at terminal V2 closeout.
- [ ] Add validation that an active transition is a unique, unedited top-level pre-transition GitHub lifecycle record with `transition_id`, `repository`, `issue_or_pr`, `expires_at`, `pre_state_fingerprint`, `allowed_deviations`, `success_condition`, and `rollback_condition`; direct readback must prove its ID and `created_at == updated_at`, and derive canonical `started_at` solely from that server timestamp. The one serial settings writer must create and directly read back this record before the first mutation; that ordering is a trusted-boundary operating rule, not an audit-proof requirement. Missing, edited, duplicate, or malformed evidence is `DRIFT`; an unreadable required live field is `UNKNOWN` before mutation.
- [ ] Add validation that terminal evidence is a separate unique, unedited top-level record linked by exact `transition_id` and `pre_transition_comment_id`, containing machine-readable `terminal_status`, `post_state_fingerprint`, and `post_state_readback`; direct readback must prove its ID and `created_at == updated_at`, and derive canonical `closed_at <= expires_at` solely from that server timestamp. Recompute the post-state fingerprint from readback. A `SUCCESS` must additionally match the repository desired target and satisfy its `success_condition` through the complete GS-7 moving-base receipt, while `ROLLED_BACK` must match pre-state. Missing, edited, duplicate, mis-linked, or late evidence is `DRIFT`; an unreadable required live field is `UNKNOWN`.
- [ ] Store these existing Issue/PR lifecycle records rather than inventing a new persistent transition subsystem, status, writer, or merge authority.

`PENDING` and `ROLLED_BACK` are classifications in the existing read-only audit model, not new governance authorities: a `PENDING` baseline prevents both false `DRIFT` for an untouched serially deferred repository and false `PENDING` after its legacy state has changed, while `ROLLED_BACK` prevents a restored failed cutover from being misread as an active transition or target. The baseline is a direct-readback entry in the existing rollout Issue/PR, not a transition receipt, status, writer, or bypass; both classifications are invalid at terminal closeout.

**Verification:**

```text
RED: current desired-state/auditor does not enforce all GS invariants
GREEN: focused governance tests + offline audit all pass with explicit expiry/drift coverage
```

---

### Addendum Task B: Prove aggregate-gate terminal semantics in all four repositories

**Applies to:** Base Plan Tasks 2, 3, 4 and 5.

Each repository must implement and test this contract before live required-check cutover:

```text
aggregate gate is always created
aggregate gate always executes
aggregate gate uses if: always() or equivalent
aggregate gate explicitly evaluates required internal states
aggregate gate SUCCESS only on complete applicable PASS set
aggregate gate FAILURE on missing/unknown/cancelled/timed-out/unexpected state
internal skipped is acceptable only with explicit NOT_APPLICABLE evidence
aggregate gate itself must not be intentionally skipped/neutral
```

#### META

- [ ] Add a deterministic test asserting `meta-gate` is present for both `pull_request` and `merge_group`.
- [ ] Add a regression fixture where one required internal check is failed/cancelled/missing and prove `meta-gate` fails.
- [ ] Add a regression fixture where an internal job is skipped without explicit N/A classification and prove failure.
- [ ] Add a positive fixture where an internal job is deterministically N/A and prove aggregate success is still possible.

#### Game

- [ ] Refactor current PR-specific resolution so `game-gate` can always fan in on `merge_group`.
- [ ] Preserve dependency/CodeQL/Rust/Linux/Windows/product jobs as internal applicability-aware inputs.
- [ ] Test that missing PR payload on `merge_group` causes broader safe validation, not aggregate skip.

#### Platform

- [ ] Preserve current conservative broad merge-group classification.
- [ ] Add explicit aggregate fan-in tests proving `platform-gate` cannot be satisfied by a skipped/neutral terminal job.

#### Atlas

- [ ] Internalize provenance into `atlas-gate` applicability/fan-in.
- [ ] Ensure PR-only risk classification/E2E semantics have an explicit merge-group equivalent or safe broad fallback.
- [ ] Prove `atlas-gate` fails if provenance is applicable but absent/failed.

**Cross-repository acceptance:** no branch/ruleset change may make an aggregate gate required until the above repository-local terminal-semantics tests are green.

---

### Addendum Task C: Require a moving-base Merge Queue canary per repository

**Applies before:** disabling strict freshness in Base Plan Tasks 2-5.

A standard canary is necessary but not sufficient. Each repository must complete the following real sequence:

1. Create PR A and reach a stable green exact head `A_HEAD`.
2. Record `A_HEAD` in the rollout receipt.
3. Integrate a safe independent PR B into `main` after A is already green.
4. Re-read PR A and prove its head is still exactly `A_HEAD`.
5. Do not merge/rebase the advanced `main` into A.
6. Admit A to Merge Queue.
7. Record the synthetic `MERGE_GROUP_SHA` and event `base_sha`.
8. Verify the repository aggregate gate executes on `MERGE_GROUP_SHA` and terminates `SUCCESS`.
9. Verify A integrates through the queue.
10. Record resulting `MAIN_AFTER_A`.

The durable receipt must contain:

```text
repository
PR_A
A_HEAD
main_before_B
PR_B
main_after_B
proof A_HEAD unchanged
MERGE_GROUP_SHA
aggregate_gate_run
MAIN_AFTER_A
```

**Failure handling:** if any step fails, keep/restore strict freshness and repair the candidate workflow. Do not mutate A merely to retrigger the test.

---

### Addendum Task D: Add the control-plane self-modification gate

**Applies to:** every V2 implementation PR that changes governance/control-plane code or settings.

A candidate is classified `CONTROL_PLANE_R2` when it materially changes at least one of:

```text
.github/workflows/**
aggregate gate implementation/fan-in
branch protection / ruleset / Merge Queue configuration
ecosystem/governance-desired-state.json
GitHub Actions permissions / token trust boundary
break-glass machinery
auth/security/deployment authorization control plane
```

For such a change, terminal integration requires:

```text
candidate deterministic CI PASS
independent deep review of current material candidate
explicit owner authorization
Merge Queue integration validation where MQ is already canonical
```

- [ ] Define a deterministic classifier or conservative path contract for `CONTROL_PLANE_R2`.
- [ ] Add a regression proving a candidate that modifies its own aggregate-gate/workflow cannot be terminally marked autonomous solely by candidate-controlled gate success.
- [ ] Preserve trusted-base/default-branch boundaries for privileged write-capable workflows.
- [ ] Record owner authorization as a new, unedited top-level comment on the canonical current GitHub PR/Issue by a human whose present repository-owner authority is independently verified by direct live GitHub readback. Bot/coordinator accounts, ordinary contributors, task text, and `author_association` alone are insufficient.
- [ ] Bind owner authorization to the current material head SHA.
- [ ] Record/validate authorization comment ID, author login/type, direct-read owner role, `created_at == updated_at`, repository, PR, material head SHA, scope, and positive integration authorization; an edited or missing comment, unreadable or non-owner authority, stale scope, or head mismatch is `UNKNOWN` and blocks integration.
- [ ] Invalidate authorization after material candidate change.
- [ ] Do not create a new `ai-review-gate`, review-envelope bridge, CODEOWNER requirement or second human dependency for this purpose.

**Threat justification for the owner-authorship trusted boundary:** the concrete threat is a coordinator, bot, or ordinary contributor posting an authorization-shaped comment and treating its own text as the GS-5 owner decision. A current comment body, `author_association`, and candidate-controlled checks do not prove the actor's present owner authority. The minimal control is direct live verification of the human owner's present role plus a new, unedited top-level comment bound to the repository, PR, material head SHA, scope, and positive integration authorization. The V2 trusted boundary deliberately trusts that authenticated human owner and the one serial settings writer; it does not require organization audit-log proof of comment creation/order and must not be replaced by an attestation, audit, or proof subsystem. The operational cost is one owner-role and comment readback per `CONTROL_PLANE_R2` integration; its retirement condition is the durable integrated-PR evidence. It adds no required status, writer, database, merge authority, second-human dependency, or identity provider; unavailable direct owner/comment evidence is `UNKNOWN` and blocks integration.

---

### Addendum Task E: Bound all rollout transitions

**Applies to:** every temporary settings deviation during cutover.

Before a live transition begins, create one durable, unedited top-level pre-transition record in the existing canonical rollout Issue/PR. Derive canonical `started_at` only from its GitHub server `created_at`; do not supply `started_at` in its body. The one serial settings writer must create and directly read back this record before the first settings mutation. The body contains:

```text
transition_id
repository
issue_or_pr
expires_at
pre_state_fingerprint
allowed_deviations
success_condition
rollback_condition
```

On terminal success or rollback, create a separate durable, unedited top-level terminal record that references the exact `transition_id` and GitHub `pre_transition_comment_id`. Derive canonical `closed_at` only from its GitHub server `created_at`; do not supply `closed_at` in its body, which then records:

```text
transition_id
pre_transition_comment_id
terminal_status  # SUCCESS or ROLLED_BACK
post_state_fingerprint
post_state_readback
```

**Rules:**

- [ ] `expires_at` must be set before the first mutation.
- [ ] The expiry window must be only as long as necessary for the concrete canary/rollback operation; do not use an indefinite or convenience horizon.
- [ ] Any live deviation not listed in `allowed_deviations` is `DRIFT` immediately.
- [ ] Direct GitHub readback must prove both record IDs are present, unique, top-level, and unedited (`created_at == updated_at`); derive canonical `started_at` and `closed_at` solely from their respective GitHub creation timestamps, never from comment-body fields. The one serial settings writer creates and reads back the pre-transition record before mutation; a terminal record cannot retroactively validate a missing pre-transition record. Missing, edited, duplicate, or mis-linked evidence is `DRIFT`; an unreadable required live field is `UNKNOWN` and blocks mutation. This trusted-boundary model does not require independent audit-log proof of comment creation or mutation ordering.
- [ ] If the transition expires before success/rollback with valid, timely (`closed_at <= expires_at`) terminal evidence, classify `DRIFT`; a late closure is also `DRIFT`.
- [ ] Terminal success closes the receipt toward `TARGET` only when timely `closed_at <= expires_at`, the auditor recomputes `post_state_fingerprint` from `post_state_readback`, the readback matches desired target state, and `success_condition` is proven by the complete Addendum Task C moving-base receipt. Terminal rollback is `ROLLED_BACK` only when timely `closed_at <= expires_at`, `post_state_fingerprint` matches `pre_state_fingerprint`, and readback proves restoration.
- [ ] The read-only auditor must surface active/expired/terminal/rolled-back transition state without becoming a settings writer.

**Threat justification for the pending baseline and terminal evidence:** the concrete threats are false `DRIFT` after a completed serial cutover when `expires_at` later passes, false `PENDING` after an untouched provider's legacy settings drift, and false `SUCCESS` after a canary or target-state failure. The minimal controls are direct GitHub readback of unique, unedited lifecycle-record IDs and server timestamps, the baseline/state fingerprints and readbacks, expiry, terminal readback/fingerprint validation, and the GS-7 moving-base receipt. Within the explicit V2 trusted boundary, the one serial settings writer is trusted to create the pre-transition record before mutation and not replace lifecycle evidence; organization audit-log creation/order proof is intentionally not required and no replacement evidence subsystem may be introduced. Their operational cost is one baseline readback per pending provider plus one pre-transition and one terminal readback per cutover; their retirement condition is terminal closeout, with records retained only as evidence. They add no new status, writer, database, merge authority, or identity provider. If required direct live comment or settings readback is unavailable, classify the affected field as `UNKNOWN` and do not mutate.

No new transition microservice/database is permitted under this addendum without a separate GS-10 threat justification.

---

### Addendum Task F: Upgrade break-glass from documented to tested

**Applies to:** Base Plan Task 6.

The base plan's read-only dry-run remains required. Add one real isolated exercise before V2 terminal closeout.

- [ ] Discover exact current-plan recovery capability.
- [ ] Capture exact pre-state on an isolated canary surface.
- [ ] Create a safe protected test branch/ruleset/surface with an analogous repair condition.
- [ ] Exercise the minimal break-glass relaxation on that isolated surface.
- [ ] Perform one bounded repair transaction.
- [ ] Restore original protection immediately.
- [ ] Read back restoration and compare to exact pre-state.
- [ ] Record durable receipt including timestamps, changed setting(s), recovery action and final readback.
- [ ] Remove/retire the isolated test surface if it has no continuing purpose.

**Forbidden:** using production `main` as the first real exercise; using break-glass to bypass a genuine product/security/dependency/provenance/integration failure.

---

### Addendum Task G: Add governance-growth review to final cleanup

**Applies to:** Base Plan Task 7.

For every retained nontrivial governance mechanism after rollout, record a compact GS-10 justification:

```text
mechanism
threat
why existing controls are insufficient
operational cost
retirement condition or permanent rationale
```

- [ ] Remove/supersede any retained mechanism that exists only for historical moving-head/review-parser compatibility.
- [ ] Verify exactly one externally required aggregate gate per permanent repository.
- [ ] Verify no required status depends on comment/reaction/flair parsing.
- [ ] Verify no expired transition remains.
- [ ] Verify no permanent repository remains `PENDING` or `ROLLED_BACK`.
- [ ] Verify no control-plane PR was terminally self-authorized solely by candidate-controlled governance.
- [ ] Verify moving-base canary receipts exist for all four repositories.
- [ ] Verify break-glass isolated exercise receipt exists.
- [ ] Mark obsolete design/plan material `SUPERSEDED` rather than deleting historical rationale.

---

## Final V2 terminal checklist

V2 is terminal only when all items below are directly verified:

```text
[ ] META requires exactly meta-gate
[ ] Game requires exactly game-gate
[ ] Platform requires exactly platform-gate
[ ] Atlas requires exactly atlas-gate
[ ] each aggregate gate always executes and terminates explicit success/failure
[ ] skipped/neutral cannot accidentally satisfy the aggregate contract
[ ] each repo completed moving-base MQ canary with unchanged PR head
[ ] strict freshness disabled only after that repo's moving-base canary
[ ] no mandatory second-human/CODEOWNER approval remains in solo mode
[ ] no governance retrigger/no-op commit mechanism remains
[ ] CONTROL_PLANE_R2 owner-confirmation rule is active
[ ] no active transition is expired
[ ] no permanent repository remains PENDING or ROLLED_BACK
[ ] break-glass dry-run completed
[ ] break-glass real isolated exercise completed and restored cleanly
[ ] no required AI-review/comment/reaction parser authority remains
[ ] Atlas provenance remains protected through atlas-gate while applicable
[ ] all retained governance mechanisms satisfy GS-10 threat justification
[ ] desired-state audit matches live state
[ ] no temporary bypass/relaxation remains active
```

## Execution ordering

This addendum does not change the base serial rollout order:

```text
META -> Game -> Platform -> Atlas
```

It changes the acceptance threshold at each stage:

```text
workflow replacement proof
-> aggregate terminal-semantics proof
-> control-plane owner authorization where applicable
-> standard MQ canary
-> moving-base MQ canary
-> settings readback
-> strict-freshness removal
-> post-state audit
```

This ordering intentionally spends a small amount of additional canary effort to avoid rebuilding a large permanent governance control plane.
