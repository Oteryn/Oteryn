# Oteryn risk-based AI review policy

Status: enforcement-bootstrap candidate for Issue #14 / PR #15; base risk-tier policy was bootstrapped by Issue #12 / PR #13.

## Objective

External AI review is a scarce verification resource. Oteryn must spend it where semantic risk justifies it, not on every pull request, formatting change, bounded evidence refresh, or non-authoritative generated report.

This policy separates deterministic validation from external AI review. Required CI, exact-diff self-review, repository scope checks, tests, static analysis, security scanning, and lifecycle closeout remain mandatory when applicable even when external AI review is not required.

## Review tiers

### R0 — deterministic validation only

No Codex/Spark review is required.

R0 is appropriate when the change has no plausible runtime, security, authority, persistence, production, deployment, cross-repository, or control-plane semantic effect and deterministic validation is stronger than an AI review for the change.

Typical examples:

- bounded evidence/archive/generated/checksum data under configured R0 globs only when the file extension is explicitly listed as safe data and is not executable/configuration content;
- non-authoritative prose, spelling, formatting, and comment-only changes outside protected governance paths.

R0 is not permission to weaken CI. Required deterministic checks must still pass on the final head. Rename/copy classification includes both source and destination paths, so moving a protected file cannot downgrade its risk tier or remove its base blob from the fingerprint.

The Action-pin, active-task lifecycle and Composer dev-patch R0 optimizations are disabled fail-closed. Workflow/Action and active-task changes therefore remain R2; Composer manifest/lockfile changes are at least R1 and security-sensitive dependency changes are R2. They may only regain R0 status through a future R2 policy change backed by a stronger deterministic proof.

### R1 — fast external review

Use the configured fast reviewer once for a stable review fingerprint.

R1 is the default for ordinary executable code that can affect behavior but does not cross an R2 boundary: normal runtime logic, algorithms, ordinary refactors, testable internal API changes, non-sensitive tooling, and dependency manifest/lockfile updates. Dependency updates are not treated as prose merely because only a lockfile changed. Security-sensitive dependency changes (for example MFA/auth/crypto/payment libraries matched by the policy) escalate to R2.


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

The review classifier computes `review_fingerprint` from the complete risk-bearing diff plus the current base blob identity for every risk-bearing path. An unrelated advance of the base branch therefore does not spend another review, while a base change touching a reviewed path invalidates the fingerprint.

A previous external review remains valid for a later final head only when all of the following are true:

1. the reviewed commit is an ancestor of the final head;
2. the final classifier emits the same review tier;
3. the final classifier emits exactly the same `review_fingerprint`;
4. every commit after the reviewed head changes only paths explicitly classified `review_neutral`;
5. all required deterministic checks pass on the final head.

This allows evidence/report/checksum refreshes after review without paying for another Codex invocation while preventing runtime, contract, workflow, policy, or ordinary documentation changes from hiding behind an older review.

A base-branch advance outside risk-bearing paths preserves the fingerprint. A rebase still requires the reviewed-head ancestry rule; rebasing/recreating the reviewed commits therefore requires a fresh review even when the textual patch is equivalent.

## Review-neutral paths

Review-neutral is intentionally narrower than R0. A path must match a configured review-neutral glob, use an explicitly safe data extension, and not be executable/configuration content. Both source and destination of renames/copies participate in this decision. Ordinary README, architecture, contract, governance, workflow and source changes are not review-neutral even if a standalone change could be R0.

## Structured review evidence

The gate supports two server-verified external evidence envelopes. Both are bound to the same repository, pull request, review tier, review fingerprint and reviewed head, and neither makes maintainer-authored text external review authority.

The legacy envelope keeps the authenticated Pull Request Review model:

```text
<!-- OTERYN_AI_REVIEW_V1 -->
REVIEW_TIER: R1 | R2
REVIEW_FINGERPRINT: <sha256>
REVIEWED_HEAD: <40-hex SHA>
REVIEWER_CLASS: fast | deep
REVIEWER_ID: codex_spark | codex
RESULT: PASS
REVIEW_SOURCE_URL: https://github.com/<owner>/<repo>/pull/<n>#pullrequestreview-<id>
FINDINGS: 0
```

The Codex interoperability envelope starts with one exact maintainer-authored request on the pull request:

```text
@codex review

<!-- OTERYN_AI_REVIEW_REQUEST_V1 -->
REVIEW_TIER: R1 | R2
REVIEW_FINGERPRINT: <sha256>
REVIEWED_HEAD: <40-hex SHA>
REVIEWER_CLASS: fast | deep
REVIEWER_ID: codex_spark | codex
```

For that envelope, the PASS authority is the server-fetched result authored by the configured Codex bot, not the request. The result must chronologically follow the one matching request, explicitly report the accepted clean/no-major-issues outcome, and contain a reviewed-commit prefix that Git resolves uniquely to the full requested `REVIEWED_HEAD`. A newer request, multiple competing matching requests, another valid request for the same reviewed head that shares the same trusted source identity, multiple trusted result objects, malformed or missing commit identity, or a P0/P1 finding on the same reviewed generation fails closed. Same-PR and same-repository object identity is verified from GitHub API fields, preventing cross-PR and cross-repository replay.

Do not treat free-form maintainer approval, a maintainer-authored clean-result sentence, or an unattached bot response as valid review evidence. Editing a review request invalidates it as PASS evidence but does not erase a trusted P0/P1 result or same-head ambiguity that followed the original request. For edited trusted comments, the gate reconstructs prior request generations only from GitHub server-side `userContentEdits`, binds that history to the exact repository/PR/comment identity, and fails closed if the history is unavailable, malformed, or truncated; replacing or removing mutable request text therefore cannot erase blocker or ambiguity history.

## Bootstrap rule

Issue #12 / PR #13 bootstrapped the risk-tier policy text. Issue #14 / PR #15 is the one-time enforcement-bootstrap transition that publishes the authenticated reusable gate. Because the trusted-base gate cannot enforce the PR that creates it, PR #15 may substitute a separate independent read-only exact-head agent review for automated Codex evidence. This exception is scoped to repository `Oteryn/Oteryn`, PR #15 only, requires deterministic exact-head CI plus no unresolved HIGH/CRITICAL findings, and cannot be reused by any later PR.

Before PR #15 merges, `main` must already require pull requests and the existing `meta-gate` check with administrator enforcement. PR #15 installs the trusted-base `pull_request_target` gate; immediately after merge the required review check becomes `ai-review-gate`. No later modification to this policy, classifier, verifier, reviewer mapping, trusted workflow or authority boundaries may use the bootstrap exception; such changes are R2 and require authenticated deep external review.

## Repository adoption

`Oteryn/Oteryn` owns the organization default and semantics. Game, Platform and Atlas may add stricter path rules or repository-specific R2 triggers, but may not downgrade an organization R2 trigger without an explicit META governance change.

Product repositories should enforce the local classifier before invoking any external reviewer and should pass only the risk-bearing diff plus directly relevant context to the reviewer. Repository-wide search is reserved for R2 or a concrete finding that requires expansion.

## Reusable enforcement action

Product repositories must invoke the META-owned composite action from a trusted `pull_request_target` wrapper and pin `.github/actions/ai-review-gate/action.yml` to a full 40-hex META commit SHA; candidate-controlled `pull_request` workflows are not enforcement authority. The action classifies the caller repository, not META, so Game, Platform and Atlas share one versioned policy implementation instead of copying classifier logic. Security-critical caller inputs (base/head SHA, Draft state, repository and PR number) must exactly match immutable GitHub pull-request event context before classification or evidence verification runs.

META additionally owns `.github/workflows/governance-ai-review.yml`, triggered by `pull_request_target`. That workflow executes only the workflow/action/policy/verifier from the exact protected base SHA, checks out the candidate with credentials disabled as inert Git data, and never executes candidate scripts. Cross-repository PRs fail closed. This trusted-base check is the post-bootstrap merge authority for AI review evidence.

- `R0`: pass after deterministic checks; no external AI is requested.
- `R1`/`R2` while Draft: report tier/fingerprint and pass so deterministic CI can stabilize without spending AI quota.
- `R1`/`R2` when Ready: fail closed until trusted authenticated external PASS evidence matches the current fingerprint. A deep reviewer may satisfy a fast-review requirement; a fast reviewer never satisfies `R2`.

A structured legacy record is only a maintainer pointer to an external review; the referenced Pull Request Review remains the authority and is fetched server-side. For Codex issue-comment interoperability, the structured request is likewise only request metadata; the trusted Codex issue comment is fetched server-side and paired fail-closed to the single eligible request generation. The configured reviewer login and allowed source kind are always read from trusted-base policy. Candidate code cannot choose reviewer identity, evidence grammar, source kinds or authorization.

For review reuse after review-neutral commits, `REVIEWED_HEAD` may be an ancestor of the final head only when the final fingerprint remains identical. The gate verifies ancestry and fingerprint and traverses every intervening commit; each must be a single-parent commit touching only safe review-neutral data paths.
