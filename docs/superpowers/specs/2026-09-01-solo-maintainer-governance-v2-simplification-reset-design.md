# Solo-Maintainer Governance V2 Simplification Reset

## Status

Approved by the repository owner for implementation in PR #125 on 2026-09-01; canonical upon merge to protected `main`.

This design replaces the over-specified lifecycle and AI-review machinery introduced by the V2 authority packet merged in PR #123.

This design deliberately returns governance enforcement to native GitHub surfaces. It does not authorize live branch-protection, ruleset, Merge Queue, provider, production, or break-glass mutations by itself.

## Problem

The original V2 goal was simple: one aggregate required gate per repository, GitHub Merge Queue for integration freshness, zero mandatory second-human dependencies, and risk-based AI review that cannot deadlock merges.

The implementation path expanded into a large custom proof subsystem: lifecycle state machines, comment parsing, fingerprints, duplicate/malformed-record handling, cross-repository chronology, terminal closeout proofs, and repeated AI-review integration logic. That complexity is now larger than the control problem it was intended to solve.

The reset removes that custom governance layer while preserving the real enforcement invariants.

## Source of truth

GitHub live state is authoritative for:

- repository and default-branch identity;
- branch protection and repository rulesets;
- required status checks and App bindings;
- pull-request state and review-thread resolution;
- workflow/check runs;
- Merge Queue and merge-group candidates;
- resulting protected-main integration.

Repository documentation and receipts describe intent and history. They do not become a second merge authority.

## Permanent merge contract

Each permanent repository has exactly one externally required aggregate gate:

```text
Oteryn/Oteryn          -> meta-gate
Oteryn/Oteryn-Game     -> game-gate
Oteryn/Oteryn-Platform -> platform-gate
Oteryn/Oteryn-Atlas    -> atlas-gate
```

The baseline target is:

- pull requests required;
- exactly one aggregate required gate;
- aggregate gate runs on `pull_request` and `merge_group`;
- GitHub Merge Queue enabled;
- strict required-status freshness disabled only after a successful moving-base canary;
- required approving review count `0` while there is one human maintainer;
- required CODEOWNER approval disabled;
- review-thread/conversation resolution required;
- linear history required;
- force pushes disabled;
- protected-branch deletion disabled;
- no broad bypass or admin exemption that weakens the baseline;
- squash is the normal merge method;
- merged source branches may continue to be auto-deleted;
- existing security scanning and least-privilege workflow controls remain intact.

## Aggregate-gate semantics

The aggregate gate must fail closed. For every supported protected candidate it must:

- be created;
- execute;
- inspect all required applicable internal validation;
- succeed only when all required applicable validation passes;
- fail for missing, cancelled, timed-out, unknown, or failing required work;
- treat `skipped` as acceptable only when explicit deterministic logic proves `NOT_APPLICABLE`;
- never use a skipped or neutral aggregate job as a successful protection result.

No second externally required status is added merely to represent an internal validation.

## Moving-base Merge Queue canary

Before strict freshness is disabled for a repository, first prove the replacement aggregate gate on a representative PR. If a currently required legacy context cannot emit on `merge_group`, capture the exact rollback state and make only that incompatible context non-required before enqueueing the canary, while keeping strict required-status freshness enabled. Do not remove compatible required contexts or disable strict freshness at this stage. If the canary fails, restore the exact pre-change required-context/settings state.

Then prove the failure mode that Merge Queue is intended to replace:

1. PR A reaches a stable green head X.
2. A separate PR B advances protected `main`.
3. PR A still has exact head X; do not merge/rebase `main` into A.
4. PR A enters GitHub Merge Queue.
5. GitHub creates a synthetic merge-group candidate against the advanced base.
6. The repository aggregate gate succeeds on that exact merge-group SHA.
7. PR A integrates through Merge Queue.
8. Final live settings and protected `main` are read back.

If the canary fails, restore the captured pre-change settings. Do not create a no-op/retrigger/head-changing governance commit merely to progress the canary.

## Rollout evidence

Use a small human-readable receipt in the existing rollout Issue/PR. A receipt records only the facts needed to understand and independently re-check the operation, for example:

- repository;
- pre-change settings snapshot;
- PR A and its unchanged head;
- PR B / intervening main advance;
- merge-group SHA;
- aggregate-gate run/result;
- resulting protected-main commit;
- final settings readback or rollback result.

Receipts are operational evidence, not a database, state machine, required check, parser input, or merge authority.

The following are explicitly retired as mandatory V2 mechanisms:

- `PENDING`, `TRANSITION`, `ROLLED_BACK`, `SUCCESS`, `DRIFT` lifecycle state-machine authority;
- mandatory `PENDING_BASELINE`, `PRE_TRANSITION`, and `TERMINAL` JSON protocols;
- rollout fingerprints as merge/closeout authority;
- malformed/duplicate lifecycle-comment heuristics;
- cross-repository comment-ledger chronology enforcement;
- terminal closeout that depends on parsing that ledger;
- custom proof machinery whose only purpose is to reproduce facts already available from GitHub live state.

A normal read-only governance audit may still compare desired target settings with live GitHub state and report mismatch/unknown without recreating the retired lifecycle subsystem.

## Control-plane changes

Agents and automation may not self-authorize a change to the mechanism that governs their own integration.

For a material control-plane or high-risk change, require:

- deterministic CI/validation;
- one independent deep review when materially useful;
- explicit human owner authorization before integration or live control-plane mutation;
- Merge Queue validation where already canonical;
- post-change live readback.

The owner decision may be recorded durably on the canonical PR/Issue, but no JSON authorization parser, duplicate-comment proof engine, review envelope, attestation bridge, second-human approval, or separate required status is needed.

## AI review policy

AI review is optional review assistance, not GitHub merge enforcement.

Retire formal `R0` / `R1` / `R2` governance states and the separate `ai-review-gate` authority.

Use this simple routing rule:

- default: no external AI review;
- ordinary code change where an independent review has clear value: prefer Codex Spark when available;
- security, authentication, permissions, deployment, recovery, workflow, branch-protection, Merge Queue, or governance/control-plane change: one Codex deep review on a stable material candidate;
- trivial docs, formatting, generated evidence, metadata, and other low-risk changes: no external AI review;
- if Spark is unavailable for a low-risk change, do not automatically escalate to deep Codex;
- do not repeatedly re-run review for an unchanged or cosmetically changed candidate; re-review only when a material risk-bearing change justifies it.

No external AI review result is a required branch-protection status.

## Rollout shape

### PR 1 — simplification authority

This branch/PR will:

- make this reset canonical;
- supersede conflicting lifecycle/proof clauses from PR #123;
- simplify the AI review policy/instructions;
- remove `ai-review-gate` from the desired future governance contract;
- make no live GitHub settings mutation.

### PR 2 — minimal META implementation

After PR 1 is canonical:

- make META desired state require only `meta-gate`;
- ensure `meta-gate` is correct for both PR and merge-group candidates;
- retain only small deterministic tests for the permanent merge contract;
- remove legacy AI-review merge authority from META;
- if the legacy required context cannot emit on `merge_group`, prove `meta-gate` replacement coverage, make only that incompatible legacy context non-required while strict freshness remains enabled, and retain exact rollback state;
- perform the real META moving-base Merge Queue canary;
- if the canary fails, restore the exact pre-canary required-context/settings state;
- after success, make Merge Queue the freshness authority and disable strict freshness;
- verify final live META enforcement directly.

Then apply the same minimal pattern serially to Game, Platform, and Atlas.

## Explicit non-goals

Do not create:

- a new governance service;
- a lifecycle database;
- an attestation/proof subsystem;
- a new required external status;
- a new identity system;
- a second-human dependency;
- a parser whose purpose is to turn arbitrary comments into merge authority;
- generalized machinery for hypothetical future rollout cases that GitHub already exposes directly.

## Acceptance criteria

The reset is successful when:

1. the canonical authority describes the simple native-GitHub model above;
2. the formal R0/R1/R2 and `ai-review-gate` merge-authority model is retired;
3. the custom lifecycle/receipt state machine is no longer mandatory governance authority;
4. PR #124 remains closed and unmerged as historical evidence;
5. the next META implementation is materially smaller and contains only controls required for the permanent merge contract and canary;
6. no live protection is weakened before replacement PR coverage is proven, and any pre-canary removal is limited to a legacy context that cannot run on `merge_group`, with strict freshness retained and exact rollback available.
