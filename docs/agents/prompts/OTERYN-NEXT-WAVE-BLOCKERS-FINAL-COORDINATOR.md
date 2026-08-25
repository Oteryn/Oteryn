# OTERYN-NEXT-WAVE-BLOCKERS-FINAL-COORDINATOR

PROMPT_ID: `OTERYN-NEXT-WAVE-BLOCKERS-FINAL-COORDINATOR`
PROMPT_VERSION: `1.0`
STATUS: `READY`
ALIAS: `OTERYN-NEXT-WAVE-BLOCKERS-FINAL-COORDINATOR`
STORAGE_REPOSITORY: `Oteryn/Oteryn`
TARGET_REPOSITORY: `Oteryn/Oteryn-Game`

This is a META-owned cross-repository orchestration prompt. Its presence in `Oteryn/Oteryn` does **not** itself grant write authority to `Oteryn/Oteryn-Game`. At invocation time, verify current explicit owner/user authorization and the target repository's live governance before any mutation.

## Mode

Autonomous coordinator + integrator + verifier + PR/CI/merge/closeout owner.

## Primary goal

Finish the already-started programme:

`Oteryn: close next-wave blockers`

Do not stop at audit, implementation, PR creation, CI, or merge of the implementation PR. Continue until the whole programme is terminally closed, including Issue #115 and coordinator Issue #131, unless a genuine owner-only external decision is unavoidable.

## Starting context — verify, do not blindly trust

- #93, #116 and #123 were already closed after the resource-limit / registry lifecycle.
- Registry PR #144 was previously merged.
- Issue #115 was the sole remaining next-wave blocker.
- Allocation PR #145 was previously merged.
- intended implementation branch: `feat/fnd04-verifier-consumer-115`.
- previous implementation work already exists locally and includes a partially implemented `apps/game-server/src/foundation/fnd04_verifier.rs`.
- the latest known TDD finding was an integer-overflow panic in NumericDate validation around expressions equivalent to `iat - 1` / `iat + 1` for extreme `i64` values.
- focused FND-04 verifier tests had reached at least eight passing tests before further adversarial work.
- current repository / GitHub / worktree state is authoritative. Re-read it before acting.

## Coordinator responsibility

You are the coordinator. Do not behave as one monolithic implementation agent if subagents are available. You retain responsibility for task decomposition, overlap prevention, independent verification, integration, PR/CI state, merge, and terminal programme closeout.

## Mandatory parallel decomposition

Dispatch exactly THREE bounded subagents initially.

### Agent A — Implementation Writer

Role: sole mutating implementation worker.

Scope:
- canonical branch `feat/fnd04-verifier-consumer-115`;
- only currently allocated Issue #115 paths;
- FND-04 verifier code;
- module exposure;
- allowed Cargo/Cargo.lock dependency wiring;
- Issue #115 delivery evidence;
- Issue #115 active task record.

Agent A is the ONLY subagent allowed to mutate the implementation branch.

### Agent B — Security / Contract Auditor

Role: read-only independent adversarial auditor.

Must review:
- Issue #115;
- Issue #128 authorization;
- current implementation;
- `docs/contracts/FND-04_PRE_ADMISSION_GRANT_PROFILE_V1.md`;
- `docs/contracts/FND-04_REAUTHENTICATED_RECOVERY_GRANT_PROFILE_V1.md`;
- accepted FND-04A / FND-04B / FND-04C architecture;
- error precedence;
- parser/resource limits;
- key trust and purpose separation;
- security-evidence age and anti-rollback;
- current authoritative game-fact validation;
- replay/non-authority semantics.

Must return P0/P1/P2 findings with exact path + relevant code/contract location and missing tests.

MUST NOT edit code or the implementation branch.

### Agent C — Governance / Closeout Auditor

Role: read-only lifecycle and verification auditor.

Must determine:
- exact required local gates;
- current ownership/lease state;
- task-record requirements;
- PR requirements;
- exact-head CI requirements;
- `game-gate` requirements;
- independent-review requirements;
- Issue #115 terminal closure requirements;
- Issue #131 terminal closeout requirements;
- lawful post-blocker readiness per lane.

MUST NOT edit implementation or coordinator files while Issue #115 is still being authored.

## Parallelism rule

Run A, B and C concurrently where possible.

Do NOT create multiple implementation writers.

ONE ACTIVE MUTATING WORKER PER CANONICAL TASK BRANCH/WORKTREE.

No two agents may edit `fnd04_verifier.rs`, `Cargo.toml`, `Cargo.lock`, the same task record, or the same coordinator document at the same time.

Read-only auditing may run concurrently with implementation.

When Agent B identifies a finding:
1. coordinator verifies it independently;
2. only Agent A repairs it;
3. repair uses TDD where behavior changes;
4. applicable verification is rerun.

Do not cherry-pick conflicting independently authored implementations.

## Implementation requirements — Issue #115

Continue the already-started implementation rather than restarting it blindly.

Read:
- `AGENTS.md`;
- `apps/game-server/AGENTS.md`;
- `docs/agents/AGENTS.md`;
- Issue #115;
- current live allocations;
- current implementation task record;
- existing implementation plan for close-next-wave-blockers;
- FND-04 A/B/C contracts and both security profiles.

Preserve the allocated boundary.

NO:
- gameplay listener/socket bind;
- production port;
- TLS private key/certificate provisioning;
- KMS/HSM/vendor selection;
- production secrets;
- production deployment/config mutation;
- durable reconnect journal implementation;
- gameplay implementation;
- client implementation;
- Platform mutation;
- external repository mutation beyond the explicitly authorized target task.

The verifier must remain a trust-boundary consumer, not authority creation.

## TDD — mandatory

Use strict RED -> GREEN -> REFACTOR.

Never write a behavioral production fix without first observing the focused test fail for the intended reason.

Immediately address the known NumericDate overflow case test-first.

Adversarial coverage must include, at minimum:

1. token hard bounds;
2. exactly three compact-JWS segments;
3. canonical unpadded base64url;
4. decoded header/payload hard bounds;
5. invalid UTF-8;
6. JSON nesting bound;
7. duplicate JSON members, including nested objects;
8. protected header exact membership;
9. forbidden JOSE key-discovery/header fields;
10. exact `alg = Ed25519`;
11. no `EdDSA`/`none`/algorithm negotiation;
12. fixed verifier trust context;
13. fresh/recovery key-purpose separation;
14. unknown/untrusted `kid`;
15. signature failure precedence over semantic payload disclosure;
16. authenticated schema defect -> MALFORMED;
17. authenticated binding mismatch;
18. authenticated unsupported profile;
19. NumericDate lifetime/skew boundaries;
20. extreme `i64` NumericDate values fail closed without panic/overflow;
21. trust evidence source age <= 5 seconds;
22. account-security evidence source age <= 5 seconds;
23. current authoritative game evidence freshness where required by accepted contract;
24. anti-rollback floors;
25. equal-revision contradictory evidence fail-closed;
26. account-security generation floor;
27. account disabled/revoked;
28. exact current route/runtime/scope checks;
29. each independent authoritative revision dimension;
30. ownership-before-world classification;
31. world stale classification;
32. fresh/recovery purpose separation;
33. valid fresh material maps only to `FreshAdmissionFacts`;
34. valid recovery material maps only to non-authoritative `ReauthenticatedRecoveryFacts`;
35. verification alone consumes no replay nonce;
36. verification alone creates/revives/rebinds no `GameSession`.

Do not weaken an accepted contract merely to make a test pass.

## Dependencies

Only direct standards-conformant dependencies genuinely required by the verifier are allowed.

Verify all current dependency additions. Pin through workspace/app Cargo as required by repository policy.

Review base64, JSON/serde usage, Ed25519 implementation, and transitive supply-chain impact.

Do not introduce a generic JWT framework if direct bounded parsing is safer and sufficient.

## Integration of subagent results

You are responsible for checking every subagent result. Never accept `agent says PASS` as sufficient evidence.

Inspect:
- Git status;
- branch;
- exact diff;
- changed paths;
- test output;
- lints;
- dependency diff;
- review findings.

Any P0/P1/P2 finding from Agent B must be dispositioned explicitly.

For a genuine material finding:
1. add/adjust failing test;
2. observe RED;
3. repair through Agent A;
4. focused GREEN;
5. full applicable validation;
6. repeat audit as necessary.

## Local final gate before PR freeze

At minimum run fresh:
- focused FND-04 verifier tests;
- `cargo test` for `oteryn-game-server`;
- `cargo test --workspace --all-targets`;
- strict `cargo clippy` using repository lint policy;
- `cargo fmt --all --check`;
- repository architecture check;
- `python tools/agents/validate_governance.py`;
- `git diff --check`;
- changed-path / allocation compliance check;
- full diff self-review.

Fix warnings if repository policy treats them as failures. No completion claim based on an earlier run.

## Delivery evidence

Complete/update:

`docs/architecture/reviews/OTERYN_GAME_FND04_VERIFIER_CONSUMER_DELIVERY_2026-08-25.md`

and the Issue #115 active task record.

Record exact base SHA, exact final head SHA, TDD RED/GREEN evidence, changed paths, dependency changes, test commands/results, security invariants, excluded scope, review requirements, no-authority proof, and zero remaining material findings before merge.

## Exact-head independent security review

After the LAST semantic/test/task-record change, freeze the exact head.

The independent reviewer must be fresh, non-authoring, exact-head bound, independent of Agent A, and based only on exact Git blobs/diff/contracts for that frozen SHA.

Use the repository-approved local non-owner-funded reviewer mechanism where available, including local `qwen2.5-coder:14b` if that remains the current documented mechanism.

Require structured P0/P1/P2, exact path/line, contract violated, and final SHA-bound verdict.

If any material finding exists: DO NOT merge. Return to TDD repair, create a new head, rerun full validation, and obtain a new exact-head independent review. A verdict for an old head is invalid after head movement.

## PR / CI / merge — Issue #115

Push the implementation branch. Create or update the Issue #115 PR.

Verify:
- exact head;
- expected base;
- correct changed paths;
- zero unrelated changes;
- zero unresolved review threads;
- independent exact-head security verdict;
- required GitHub Actions;
- canonical `game-gate`;
- governance/architecture/merge-authority gates as applicable.

Do not rerun unrelated successful jobs unnecessarily.

If CI fails, diagnose the exact failure. Do not weaken tests or governance. Repair only genuine problems.

Merge only with expected-head fencing after all required checks are green, using the repository-required merge method.

After merge:
- verify the actual merge SHA on `main`;
- verify Issue #115 acceptance against merged `main`;
- close #115 only with concrete PR/head/merge/review/CI evidence;
- verify merged task branch disposition.

## Final programme closeout — Issue #131

Do NOT stop after #115 merges.

Start from fresh current `main`. Re-read #93, #115, #116, #123, #131, the Movement successor issue, all relevant merged PRs, live allocations, task records, and current branch/CI state.

Create the final bounded coordinator closeout lifecycle required by the existing plan.

Recompute readiness separately for Ability, Interaction, AI, Movement, Durability, Server Seam, Client, and QA.

Do NOT equate `blocker removed` with `implementation automatically authorized`.

Release completed shared-path leases. Archive/reconcile completed task records according to repository policy. Create/update the final next-wave blockers closeout evidence document if required by the current plan.

Run fresh governance validation, architecture/policy validation, diff check, whole-diff review, exact-head CI, and `game-gate`.

Merge the closeout PR only when all required gates pass.

Then verify final `main`, verify #131 acceptance boxes, close #131 as completed, and verify no stale active ownership remains from this programme.

## Autonomy

Do not stop merely because one subagent finished, tests are locally green, a PR exists, CI is running, or #115 merged.

Continue through all reachable work in the current session.

Only stop early for a TRUE blocker that cannot lawfully be resolved using existing authorization, such as a missing owner-only credential/permission, a new architecture/product decision outside current authority, or a protected operation explicitly requiring owner action.

If one exists, state the exact blocker, affected step, and exact owner action required. Otherwise finish the complete programme.

## Final response

Return concise verified evidence:
- Issue #115 implementation PR number;
- final implementation head SHA;
- independent-review verdict;
- required CI/`game-gate` result;
- implementation merge SHA;
- #115 final state;
- closeout PR number;
- closeout head SHA;
- closeout merge SHA;
- #131 final state;
- remaining active shared leases;
- remaining next-wave blockers;
- newly lawful next aliases/lanes.

Never claim DONE without fresh direct verification of final `main` and both issue states.
