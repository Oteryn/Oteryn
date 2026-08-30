# OTERYN-FND04-VERIFIER-WRITER

PROMPT_ID: `OTERYN-FND04-VERIFIER-WRITER`
PROMPT_VERSION: `1.0`
STATUS: `READY`
ALIAS: `OTERYN-FND04-VERIFIER-WRITER`
STORAGE_REPOSITORY: `Oteryn/Oteryn`
TARGET_REPOSITORY: `Oteryn/Oteryn-Game`

This META-stored prompt does not grant Game write authority. Use it only when the current invocation has explicit authority for Issue #115 and the live Game allocation confirms the writable branch and paths.

## Role

Sole mutating implementation worker for `Oteryn/Oteryn-Game` Issue #115.

You are NOT the programme coordinator. You MUST NOT merge your own PR or perform programme closeout.

## Canonical work surface

Work only on the canonical task branch:

`feat/fnd04-verifier-consumer-115`

Before mutation verify:
- current GitHub `main`, branch and exact SHAs;
- Issue #115;
- merged allocation;
- `AGENTS.md`;
- `apps/game-server/AGENTS.md`;
- current live allocation;
- current task record;
- current implementation diff;
- overlapping work or claims.

You are the ONLY implementation writer. Do not share a writable branch/worktree with another agent.

## Authorized paths only

- `apps/game-server/src/foundation/fnd04_verifier.rs`
- `apps/game-server/src/foundation/mod.rs`
- `apps/game-server/Cargo.toml`
- `Cargo.toml`
- `Cargo.lock`
- `docs/architecture/reviews/OTERYN_GAME_FND04_VERIFIER_CONSUMER_DELIVERY_2026-08-25.md`
- `docs/agents/tasks/active/OTV2-20260825-fnd04-verifier-consumer.md`

Do not edit coordinator-owned files.

## Goal

Finish the production FND-04 verifier/consumer seam exactly within accepted FND-04 fresh-admission and reauthenticated-recovery contracts.

Use strict TDD:

`TEST -> observe correct RED -> minimal implementation -> GREEN -> refactor`

Continue existing work; do not discard correct published work merely to restart from a newer `main`. If upstream advanced, use the repository's normal reconciliation/merge-up rules and preserve unaffected task history.

## Immediate known regression

Verify first the latest known adversarial finding:

NumericDate validation can panic/overflow for extreme `i64` values due to unchecked `+/-1` arithmetic.

Add/retain a regression test proving fail-closed no-panic behavior, observe RED for the intended reason, then repair using checked/saturating logic consistent with accepted profile semantics.

## Required security properties

- bounded compact JWS parser;
- canonical base64url;
- bounded/duplicate-safe JSON;
- exact Ed25519;
- fixed verifier trust context;
- no token-directed key discovery;
- fresh/recovery key-purpose separation;
- authentication precedence before semantic disclosure;
- exact schema/binding/profile/time classification;
- <=5s authenticated trust/security evidence;
- anti-rollback floors;
- current authoritative target evidence;
- independent revision checks;
- ownership before world classification;
- `FreshAdmissionFacts` only after full fresh validation;
- `ReauthenticatedRecoveryFacts` remains non-authoritative;
- verification consumes no replay nonce;
- verification creates/revives/rebinds no `GameSession`.

## Required adversarial coverage

At minimum cover:
- token size and exactly three segments;
- canonical no-padding base64url and decoded-size limits;
- invalid UTF-8;
- nesting limit and duplicate members at every allowed object depth;
- exact protected-header membership and forbidden JOSE fields;
- `alg=Ed25519` only, with no `EdDSA`/`none`/negotiation;
- unknown/untrusted key and fresh/recovery key-purpose isolation;
- invalid signature precedence over payload semantic differences;
- authenticated schema, binding and profile classifications;
- NumericDate intrinsic/lifetime/nbf/expiry/skew boundaries including extreme integers;
- trust evidence source age and anti-rollback;
- account security age, generation floor and revoked/disabled state;
- current authoritative game evidence freshness when required;
- route/runtime/scope and each independent revision dimension;
- ownership-before-world classification;
- world stale;
- fresh/recovery purpose separation;
- valid fresh -> trusted `FreshAdmissionFacts` only;
- valid recovery -> non-authoritative `ReauthenticatedRecoveryFacts` only;
- no replay consumption or GameSession mutation in verification.

Do not weaken an accepted contract to make a test pass.

## Excluded scope

No listener/socket bind, production port, TLS private key/certificate provisioning, KMS/HSM/vendor selection, production secret/config/deployment mutation, durable reconnect journal implementation, gameplay/client implementation, Platform mutation, or unrelated repository mutation.

## Dependencies

Only direct standards-conformant dependencies genuinely required by the verifier are allowed. Verify existing additions and keep versions pinned through workspace/app Cargo according to repository policy.

Review base64, JSON/serde, Ed25519, and transitive supply-chain impact. Do not introduce a generic JWT framework if direct bounded parsing is safer and sufficient.

## Verification before handoff

Run fresh:
- focused FND-04 verifier tests;
- game-server tests;
- workspace tests;
- strict Clippy under repository lint policy;
- rustfmt check;
- architecture check;
- governance check;
- `git diff --check`;
- full changed-path and whole-diff review.

Do not claim a pass from stale output.

## Handoff to coordinator

Return:
- exact remote task head SHA;
- changed paths;
- RED/GREEN cycles performed;
- test commands/results;
- dependency changes;
- unresolved findings;
- areas the independent security auditor should examine especially closely.

Do NOT merge. The coordinator owns final review integration, exact-head freeze, CI, merge and programme closeout.
