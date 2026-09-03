# Oteryn Organization Agent Policy

Policy ID: `OTERYN_ORGANIZATION_AGENT_POLICY`  
Policy version: `3.0.0`

This is the organization-wide semantic entry point for agent execution when it is present on protected META `main`. The governing principle is **one rule, one authority**: organization semantics live in META, provider repositories bind to an immutable META commit, and task prompts carry only task-specific deltas.

## Authority model

`Oteryn/Oteryn` owns organization-wide agent execution semantics. Game, Platform and Atlas may add repository/domain restrictions that are genuinely local and may narrow authority, but they must not broaden, fork or restate global policy.

A provider adopts this policy through `docs/agents/META_AGENT_POLICY_BINDING.json`. The binding names one immutable META commit and the canonical policy paths. A provider never follows a moving META `main` implicitly and never copies the policy body to compensate for a stale binding.

A prompt alias, handoff, Issue, PR or tool capability does not itself grant write, production, merge or cross-repository authority. Resolve the current task and repository authority before mutation.

## Live state

GitHub live repository, branch, Issue, PR, review and check state is authoritative for lifecycle facts. Cached SHAs, prior chat, handoffs and task prose are locators/evidence only and must be refreshed before a material decision when they can have changed.

Protected `main` movement alone does not invalidate still-applicable work. Reconcile only the authority, contracts, tests and integration evidence affected by the upstream change; do not restart useful work merely because a SHA changed.

## Execution shape

Use `single_agent` when one capable worker is proportionate. Use `parallel_when_beneficial` only when at least two materially independent workstreams justify coordination cost. One mutating owner per writable lane remains the default safety boundary; read-only analysis may fan out when it has clear value.

Parallelism is an optimization, not a completion criterion. Serial work does not require an apology or a fabricated exception.

## Execution surfaces and Remote Desktop

The canonical machine authority for execution routing is `ecosystem/agent-execution-routing-policy.json`, with supporting rules in `docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md`.

Repository-native GitHub/GitHub Actions and an authorized isolated workspace are preferred execution surfaces. Remote Desktop/Desktop Commander remains exception-only under the machine gate; provider roots and task prompts do not reproduce its per-call contract. A Remote Desktop denial is not automatically a blocker when another authorized execution path can continue useful work.

## Bounded autonomy, retry and continuation

`ecosystem/bounded-autonomous-execution-policy.json` and `docs/agents/contracts/BOUNDED_AUTONOMOUS_EXECUTION_POLICY.md` own bounded retry/progress semantics. Continue while a safe authorized next action exists. Do not create no-op/retrigger commits, repeated unchanged heavy validation or owner questions merely to demonstrate activity.

A checkpoint is durable recovery state, not a mandatory pause. Generic handoffs record coordinates and material state only; they do not contain copies of organization policy.

## AI review

`docs/governance/AI_REVIEW_POLICY.md` is the organization review-routing authority. Default external AI review is none; use the lightest useful independent review for the risk class defined there. AI review is advisory and never a second required GitHub merge authority.

Provider instructions and task prompts may identify task-specific risk facts, but they do not reproduce a full Codex/OpenAI review controller.

## Integration

GitHub protected-branch enforcement, the repository's single aggregate gate and GitHub Merge Queue are integration authority where configured. Deterministic CI qualifies the applicable exact candidate; custom review fingerprints, envelopes, attestations, formal R0/R1/R2 states, `ai-review-gate` as merge authority and custom proof ledgers remain retired by ADR 0005.

Do not bypass Merge Queue or replace it with a direct merge merely because a connector lacks an enqueue operation.

## Prompt and handoff policy

Use `docs/agents/policy/PROMPTING_STANDARD.md` for task instructions and `docs/agents/policy/PROMPT_EVAL_STANDARD.md` for material prompt/harness changes.

A normal task prompt states only its role/outcome, authority/scope delta, live locators, domain constraints/dependencies, acceptance/validation delta and stop/handoff delta. A normal handoff stores task/repository coordinates, exact branch/PR/head, material completed/remaining work, evidence, blocker/disposition and one next safe action.

Global GitHub, Remote Desktop, AI-review, concurrency, retry, merge and continuation policy must not be copied into provider prompts or handoffs.

## Provider adoption

Provider adoption is explicit and versioned:

1. META merges a reviewed central policy candidate.
2. The provider updates `META_AGENT_POLICY_BINDING.json` to that exact immutable META commit.
3. The provider keeps only bootstrap plus domain-specific invariants and local validation/deployment facts.
4. Exact-head provider validation proves the overlay still satisfies its own domain contract.
5. Existing admitted work preserves unaffected implementation; newly applicable safety/authority changes are reconciled rather than ignored.

If the immutable META commit cannot be resolved through an authorized repository-native path, provider mutation fails closed while safe read-only inspection may continue.
