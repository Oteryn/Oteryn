# Oteryn risk-based AI review policy

Status: proposed bootstrap policy for Issue #12.

## Objective

External AI review is a scarce verification resource. Oteryn must spend it where semantic risk justifies it, not on every pull request, formatting change, evidence refresh, generated report, branch cleanup, or immutable Action pin refresh.

This policy separates deterministic validation from external AI review. Required CI, exact-diff self-review, repository scope checks, tests, static analysis, security scanning, and lifecycle closeout remain mandatory when applicable even when external AI review is not required.

## Review tiers

### R0 — deterministic validation only

No Codex/Spark review is required.

R0 is appropriate when the change has no plausible runtime, security, authority, persistence, production, deployment, cross-repository, or control-plane semantic effect and deterministic validation is stronger than an AI review for the change.

Typical examples:

- evidence under `docs/evidence/**`;
- archived task records under `docs/agents/tasks/archive/**`;
- generated reports/checksums whose source and validator are unchanged;
- non-authoritative prose, spelling, formatting, and comment-only changes;
- exact deletion of an unprotected branch proven fully represented by protected `main` by ancestry/tree/patch equivalence;
- a Dependabot-style immutable GitHub Action pin refresh when the Action identity and annotated major version are unchanged, both old and new references are full 40-hex SHAs, and no trigger, permissions, inputs, environment, runner, shell, or job semantics change.

R0 is not permission to weaken CI. Required deterministic checks must still pass on the final head.

### R1 — fast external review

Use the configured fast reviewer once for a stable review fingerprint.

R1 is the default for ordinary executable code that can affect behavior but does not cross an R2 boundary: normal runtime logic, algorithms, ordinary refactors, testable internal API changes, non-sensitive tooling, and dependency manifest/lockfile updates. Dependency updates are not treated as prose merely because only a lockfile changed.

Current reviewer preference is `Codex Spark` when available, with ordinary `Codex` as fallback. Provider/model names are configuration, not architectural authority.

### R2 — deep external review

Use the configured deep reviewer on the complete risk-bearing diff and directly relevant contracts/tests.

R2 is mandatory for changes that can affect any of:

- authentication, authorization, identity, session or entitlement correctness;
- secrets, credentials, tokens, cryptography, security policy, vulnerability handling or privacy boundaries;
- database migrations, durable state, destructive operations, backup/restore or data-loss behavior;
- production deployment, protected environments, DNS/network edge, runners or release authority;
- GitHub Actions permissions/triggers, CODEOWNERS, branch protection, rulesets, required checks or repository security settings;
- cross-repository authority, provider/consumer contracts, protocol/schema compatibility or migration cutover;
- `AGENTS.md`, runnable agent instructions/prompts, or policy that can broaden autonomous write/execution authority;
- payment/commercial entitlement effects;
- a large or structurally broad diff that exceeds the configured deep-review threshold.

The preferred deep reviewer is ordinary Codex. A fast reviewer must not silently substitute for R2 unless the policy configuration explicitly declares that reviewer deep-capable for the current invocation.

## Spend-control rules

External review must not run while a PR is Draft/WIP, while required deterministic CI is red, or while the risk-bearing diff is still changing. Classification and deterministic CI happen first; external review is the final scarce verification step.

For one review fingerprint:

- invoke at most one primary external review;
- do not run periodic/repeated reviews merely to see whether the result changes;
- do not run a second reviewer after PASS unless a separate policy explicitly requires it for that risk class;
- after FAIL, repair findings first and invoke again only when the risk fingerprint changes;
- if quota/capacity is unavailable, record `WAITING_REVIEW_QUOTA` rather than retrying in a loop or silently bypassing the required tier.

## Review fingerprint and no-re-review rule

The review classifier computes `review_fingerprint` from the base revision plus the complete diff for all paths that are not explicitly review-neutral.

A previous external review remains valid for a later final head only when all of the following are true:

1. the reviewed commit is an ancestor of the final head;
2. the final classifier emits the same review tier;
3. the final classifier emits exactly the same `review_fingerprint`;
4. every commit after the reviewed head changes only paths explicitly classified `review_neutral`;
5. all required deterministic checks pass on the final head.

This allows evidence/report/checksum refreshes after review without paying for another Codex invocation while preventing runtime, contract, workflow, policy, or ordinary documentation changes from hiding behind an older review.

A rebase onto a different base invalidates the fingerprint unless a future deterministic policy proves base-equivalence safely.

## Review-neutral paths

Review-neutral is intentionally narrower than R0. The default organization policy permits only bounded evidence/archive/generated-result paths. Ordinary README, architecture, contract, governance, workflow and source changes are not review-neutral even if a standalone change could be R0.

## Structured review evidence

An external review record must contain at least:

```text
REVIEW_TIER: R1 | R2
REVIEW_FINGERPRINT: <sha256>
REVIEWED_HEAD: <40-hex SHA>
REVIEWER_CLASS: fast | deep
REVIEWER: <provider/model or product reviewer identity>
RESULT: PASS | FAIL | BLOCKED
FINDINGS: <count and concrete references>
```

Do not treat free-form approval language without the fingerprint/head binding as a valid review gate.

## Bootstrap rule

Issue #12 and the PR that first installs this policy are the one-time bootstrap exception: they may be merged with owner self-review plus deterministic exact-head CI and full-diff inspection, without consuming Codex/Spark. Requiring the not-yet-installed policy to review its own installation would create a circular dependency.

After bootstrap merge, modifications to this policy, its classifier, its reviewer mapping, or its authority boundaries are R2 and require deep external review.

## Repository adoption

`Oteryn/Oteryn` owns the organization default and semantics. Game, Platform and Atlas may add stricter path rules or repository-specific R2 triggers, but may not downgrade an organization R2 trigger without an explicit META governance change.

Product repositories should enforce the local classifier before invoking any external reviewer and should pass only the risk-bearing diff plus directly relevant context to the reviewer. Repository-wide search is reserved for R2 or a concrete finding that requires expansion.

## Reusable enforcement action

Product repositories consume the META-owned composite action at `.github/actions/ai-review-gate/action.yml` using a full 40-hex META commit SHA. The action classifies the caller repository, not META, so Game, Platform and Atlas share one versioned policy implementation instead of copying classifier logic.

- `R0`: pass after deterministic checks; no external AI is requested.
- `R1`/`R2` while Draft: report tier/fingerprint and pass so deterministic CI can stabilize without spending AI quota.
- `R1`/`R2` when Ready: fail closed until a trusted structured PASS record matches the current fingerprint. A deep reviewer may satisfy a fast-review requirement; a fast reviewer never satisfies `R2`.

A structured record is a maintainer attestation to an actually completed external review and points to its GitHub PR review/comment source:

```text
<!-- OTERYN_AI_REVIEW_V1 -->
REVIEW_TIER: R1 | R2
REVIEW_FINGERPRINT: <sha256>
REVIEWED_HEAD: <40-hex SHA>
REVIEWER_CLASS: fast | deep
REVIEWER_ID: codex_spark | codex
RESULT: PASS
REVIEW_SOURCE_URL: https://github.com/<owner>/<repo>/pull/<n>#...
FINDINGS: <integer or concise resolved summary>
```

For review reuse after review-neutral commits, `REVIEWED_HEAD` may be an ancestor of the final head only when the final fingerprint remains identical. The gate verifies both ancestry and fingerprint.
