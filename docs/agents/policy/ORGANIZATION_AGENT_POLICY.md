# Oteryn Organization Agent Policy

Policy ID: `OTERYN_ORGANIZATION_AGENT_POLICY`
Policy version: `3.0.0`

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

Protected GitHub enforcement and Merge Queue, where configured, remain integration authority. Before selecting any integration route, require a fresh target-bound authorization/eligibility observation for the exact repository, PR number, base branch and qualified/frozen head; cached authorization for another candidate or an older head is not transferable. The preferred agent submission route is GitHub's native REST `merge-async` operation for the exact qualified/frozen PR head, with the full current `sha` supplied explicitly and `merge_action="merge_queue"` selected explicitly. `merge_action="default"` is not sufficient authority for an agent because it can choose a different merge behavior, and `direct_merge` is forbidden. A newly accepted asynchronous request (`202`) proves only that GitHub accepted the request; retain its asynchronous merge request UUID and independently verify the resulting live Merge Queue / async-result state, the repository's normal `merge_group` aggregate gate, and protected-main readback before declaring integration complete. A `200` or `409` response is not by itself a terminal success claim; reconcile it against current GitHub state and the returned/current request identity.

If the execution surface does not expose safe `merge-async`, fall back only to another queue-specific exact-head-fenced operation: native GraphQL `enqueuePullRequest` with `expectedHeadOid` equal to the exact qualified PR head, or the protected-default-branch META submission executor at Issue #190. The permanent agent-callable command is `/oteryn-mq-submit <attempt_id> <owner/repo> <pr_number> <exact_head_sha>`. The protected workflow must authenticate the current control-endpoint actor on META **and independently require that same actor's current `write`, `maintain` or `admin` permission on the exact target repository** before queue mutation. It must allow only the four permanent Oteryn repositories, re-read the same-repository open non-draft PR with base `main`, exact current head and required exact-head aggregate gate, and mint a short-lived GitHub App installation token scoped to that single target repository only after META authorization. Its only integration mutation is GraphQL `enqueuePullRequest(expectedHeadOid=<exact head>)`; it requires the exact returned Merge Queue entry and queue identity, is idempotent for an already-enqueued exact head, executes no candidate-controlled code, and gains no direct-merge, bypass, approval, protection-changing or unrelated repository-write authority. Success receipts prove submission only; normal `merge_group` validation and protected-main readback remain terminal authority.

Keep the dedicated Merge Queue App least-privilege. Its target token is limited to checks read, pull requests read and merge queues write; the private key exists only as a protected Actions secret and is never emitted into repository content, comments or logs. The protected executor deliberately uses GraphQL enqueue instead of REST `merge-async` because GitHub currently documents `merge-async` fine-grained authorization as requiring broader Contents write permission. Direct connector-native `merge-async` remains preferred when the connector itself exposes the exact `sha` and explicit `merge_queue` action, while the protected executor provides the durable current-surface adapter without giving candidate workflows that broader credential.

`enablePullRequestAutoMerge` is not a governed agent enqueue capability. It may remain a GitHub UI/CLI convenience where GitHub itself applies repository rules, but a generic connector wrapper that does not expose an explicit queue action and exact-head binding must not substitute for the native queue-specific routes above. No bypass, direct merge, generic auto-merge, no-op commit or protection change substitutes for an unavailable safe route. If none of `merge-async` with explicit `merge_action="merge_queue"` + exact `sha`, exact GraphQL enqueue, or the authorized protected executor is callable, integration is `BLOCKED_CAPABILITY_UNAVAILABLE`; continue other safe path-disjoint work rather than weakening Merge Queue authority. Historical `added_to_merge_queue` events alone are not terminal integration proof. ADR 0005's retired custom review fingerprints, envelopes, attestations and `ai-review-gate` must not be recreated as merge authority.

## Adoption and authoring

Use `docs/agents/policy/PROMPTING_STANDARD.md` when authoring prompts and `docs/agents/policy/PROMPT_EVAL_STANDARD.md` for material instruction/harness evaluation. Neither is mandatory background reading for unrelated product tasks.

Merge the reviewed META contract first, then migrate each provider's binding, instructions and consuming validators together. Retire conflicting legacy checks in that same coherent change; preserve local product constraints and current maintenance restrictions. Qualify actual delivery and representative behavior before broadening adoption. Do not equate text lint, green bundle CI or a binding with a completed provider migration.

The central validator checks structure and known legacy duplication patterns, not arbitrary prose semantics or tool authorization. Plain references and inert examples are not local policy controllers; their acceptance does not prove that an agent will ignore their contents. Machine safety gates and independent review remain necessary. Historical evidence stays available but is not an active dispatch surface.
