# Oteryn Organization Agent Policy

Policy ID: `OTERYN_ORGANIZATION_AGENT_POLICY`
Policy version: `3.1.0`

Effective after reviewed integration to protected META `main` and explicit provider adoption. The principle is **one rule, one authority**: META owns shared semantics; providers own product knowledge and implementation; prompts add only task-specific requirements.

## Authority and delivery

A provider adopts one immutable META commit through `docs/agents/META_AGENT_POLICY_BINDING.json`. It does not follow moving META `main` implicitly. Tool access, a binding, alias, Issue, PR or handoff does not grant repository, cross-repository, production or merge permission. Providers may narrow authority, not broaden it.

Policy ownership and instruction delivery are different. A binding identifies a version; it does not prove that a client loads remote instructions. Keep a small local bootstrap containing necessary authority/safety boundaries and durable product invariants. Controlled duplication of that minimum is allowed; independent copies of full global procedures are not.

Classify content by when it is needed:

- **ALWAYS:** the local bootstrap and invariants material to ordinary work in its scope.
- **ROUTED:** specialist knowledge/procedures loaded when the affected domain or operation requires them.
- **TASK_ONLY:** temporary scope, acceptance and output requirements in the current task.
- **DETERMINISTIC:** rules enforced by existing schemas, configuration and platform gates.

A normal product task need not fetch the complete META bundle over the network. Reuse verified immutable sources by their exact revision. Resolve the applicable authority through an authorized source when needed; fail closed for an operation whose required authority cannot be established, while continuing safe independent work. Missing unrelated context is not a universal blocker. Verify actual instruction delivery during provider/client adoption rather than requiring a large manifest for every task.

## Live state and execution

GitHub live state governs repository lifecycle facts. Refresh facts that can have changed before relying on them for a material mutation or integration decision. Upstream movement alone does not invalidate useful work: reconcile affected authority, contracts and evidence without resetting unrelated progress. Preserve unrelated changes and one active writer per writable branch/workspace.

Use `single_agent` when one capable worker is proportionate. Use `parallel_when_beneficial` only for independent work whose benefit exceeds coordination/integration cost. Model, effort and concurrency belong in supported execution configuration, not fixed maximum-effort role prose. A default is not proof of a hard limit.

For execution routing, `ecosystem/agent-execution-routing-policy.json` and `docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md` remain authoritative. Prefer repository-native GitHub/CI and an authorized isolated workspace. Remote Desktop remains exception-only under its existing exact per-call machine gate; availability is not permission. A denied route does not block another authorized route.

## Progress and recovery

`ecosystem/bounded-autonomous-execution-policy.json` and `docs/agents/contracts/BOUNDED_AUTONOMOUS_EXECUTION_POLICY.md` own lifecycle, freeze and retry semantics. `ecosystem/agent-continuation-policy.json` and `docs/agents/contracts/PERSISTENT_AUTONOMOUS_CONTINUATION_POLICY.md` own resume mechanics subordinate to them. Do not reproduce their counters or enums in each prompt.

Continue useful authorized work without a generic fixed worker lifetime. Preserve bounded retries and candidate freeze: no-op/retrigger commits, checkpoint-only churn or unchanged heavy validation are not progress. `WAITING_EXTERNAL` and `STALLED` release active ownership under the bounded contract; neither means ready to merge. A checkpoint is recovery state, not a mandatory pause. Never claim background continuation without a verified resume mechanism.

Skills and plugins are subordinate execution aids. They must not weaken safety or add additional approval gates, duplicate planning artifacts, or re-open an already approved design merely because a generic workflow expects them.

## Validation and integration

Use focused checks while iterating, broader tests when affected behavior requires them, and the repository-required exact-candidate gate at integration. Do not suppress required tests to reduce cost. Reuse unchanged evidence only within its valid scope; a different integration candidate still needs its required proof. Prefer focused log excerpts while retaining full evidence outside the active context.

`docs/governance/AI_REVIEW_POLICY.md` owns risk-based independent review. Default external AI review is none; use the lightest applicable review, and repeat it only for a material risk-bearing change. AI review is advisory, not a new required status.

Protected GitHub enforcement and Merge Queue, where configured, remain integration authority. Before selecting an autonomous integration route, require fresh target-bound authorization/eligibility for the exact repository, PR number, `base=main` and qualified/frozen head. Stale or cross-target authorization fails closed. Ordinary protected-`main` movement does not invalidate a qualified head by itself; Merge Queue owns composition against current `main` and the resulting `merge_group` verification.

The governed native autonomous queue-submission standard is REST `PUT /repos/{owner}/{repo}/pulls/{pull_number}/merge-async` with the exact qualified head in `sha` and explicit `merge_action="merge_queue"`. The exact `sha` fence is mandatory and `merge_action="default"` is insufficient. This policy deliberately accepts that current `merge-async` does **not** expose an expected base/queue precondition. The residual retarget race is narrow but real: an authorized actor could retarget a PR after the fresh preflight and before GitHub applies the request while leaving the head unchanged. Oteryn accepts that operational risk in exchange for a native, queue-specific, exact-head route.

Authentication is subordinate to that native route and must not create a second merge authority. Oteryn does **not** require or authorize creating a dedicated custom GitHub App, App client ID, or private key merely to call `merge-async`. An execution surface is operationally acceptable only when it either exposes the exact native `merge-async` operation directly with the required target/head fencing, or uses a fine-grained personal access token scoped to the necessary repository set with only the permissions required by the endpoint. Repository workflows should keep built-in `GITHUB_TOKEN` read-only for ordinary PR/check reads and use a separate fine-grained mutation token only for `merge-async` and its async-status readback. Do not use `GITHUB_TOKEN` as the queue mutation credential when terminal authority requires a new `merge_group` workflow: GitHub suppresses most workflow runs caused by `GITHUB_TOKEN`, so that route cannot prove the required independent aggregate gate. Missing or denied native mutation credentials are `BLOCKED_CAPABILITY_UNAVAILABLE`; custom-App bootstrap, GraphQL, generic auto-merge and direct merge are not fallbacks.

Mitigate the missing mutation-time base fence with mandatory fresh target validation immediately before and immediately after accepted submission. The preflight must bind repository, PR number, `base=main`, exact head, authorization and eligibility. After HTTP `202`, the executor must first capture the server-returned async UUID and an executor-owned monotonic receipt sequence, then start the live PR readback. The post-submission proof must bind that exact accepted-request UUID and carry an executor sequence strictly greater than the receipt sequence; whole-second wall-clock timestamps are freshness evidence only and are not causal-order authority. The live readback must require the same repository, PR number, `base=main` and exact head before any autonomous lifecycle closeout continues. Same-second pre-receipt or equal-sequence evidence fails closed. Post-mutation readback is detection rather than retroactive atomic prevention; if it observes a changed base/head or stale state, stop with a target-mismatch blocker and require human reconciliation. Do not issue ambiguous automated `dequeuePullRequest` cleanup.

HTTP `202` from `merge-async` is request acceptance only. Preserve the returned async UUID and reconcile the async request/status. HTTP `200` or `409` may indicate an already-merged, already-queued or existing async state and therefore require live reconciliation rather than being treated as terminal success by themselves. A queue/submission receipt is never integration proof: require the normal `merge_group` aggregate gate and protected-main readback before archive/release/Issue closeout. Historical `added_to_merge_queue` events alone are not terminal proof.

GraphQL `enqueuePullRequest(expectedHeadOid=...)` remains a documented queue-specific head-fenced primitive, but it is not the selected native Oteryn route in this policy revision. A later reviewed policy change may approve it separately if its operational contract and reconciliation semantics are desired. Do not infer authority from caller-provided capability booleans or self-asserted receipts.

`enablePullRequestAutoMerge` is not a governed agent enqueue capability. `direct_merge`, immediate/direct merge APIs, `merge_action="direct_merge"`, bypass, force push, no-op/retrigger commits and protection changes are forbidden substitutes. If the active execution surface cannot invoke the exact native `merge-async` operation with `sha` plus `merge_action="merge_queue"`, integration is `BLOCKED_CAPABILITY_UNAVAILABLE`; continue other safe path-disjoint work rather than weakening Merge Queue authority. ADR 0005's retired custom review fingerprints, envelopes, attestations and `ai-review-gate` must not be recreated as merge authority.

## Adoption and authoring

Use `docs/agents/policy/PROMPTING_STANDARD.md` when authoring prompts and `docs/agents/policy/PROMPT_EVAL_STANDARD.md` for material instruction/harness evaluation. Neither is mandatory background reading for unrelated product tasks.

Merge the reviewed META contract first, then migrate each provider's binding, instructions and consuming validators together. Retire conflicting legacy checks in that same coherent change; preserve local product constraints and current maintenance restrictions. Qualify actual delivery and representative behavior before broadening adoption. Do not equate text lint, green bundle CI or a binding with a completed provider migration.

The central validator checks structure and known legacy duplication patterns, not arbitrary prose semantics or tool authorization. Plain references and inert examples are not local policy controllers; their acceptance does not prove that an agent will ignore their contents. Machine safety gates and independent review remain necessary. Historical evidence stays available but is not an active dispatch surface.
