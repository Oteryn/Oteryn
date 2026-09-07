# Platform R5 specialist-controller residue review

Reviewed 2026-09-07, read-only, against Platform protected main `907546f193e91b0bed2f5f077ab5b874771929ef` and external draft PR #1303 head `ec473212e36b00e07154dcaf10a18d4e11d39235` (old base `3557085c20512d25576d8884cc54471665784b00`).

## Verdict

Merged #1304's bounded W2/W4 acceptance remains valid. It owned the root/bootstrap, active reusable prompts, provider consumer/evaluators, workflow and evidence; its adoption evidence limits the copied-controller removal claim to every active prompt and explicitly records broader routed continuation/closeout consolidation as W6 follow-up item 3.

The repository-wide programme must nevertheless remain nonterminal while the specialist-controller residue is active. This is externally owned by Issue #1302 / draft PR #1303.

## Exact current-main reachability

`git diff 3557085c20512d25576d8884cc54471665784b00..907546f193e91b0bed2f5f077ab5b874771929ef` shows that #1304 changed only root `AGENTS.md` and `docs/agents/AGENTS.md` among the reviewed surfaces. These remained unchanged from admission to current main:

- `docs/agents/ANTI_STALL_AND_EXECUTION_BUDGET.md`
- `docs/agents/AUTONOMOUS_PROGRAM_CONTINUATION.md`
- `docs/agents/DELIVERY_COMPLETENESS_AND_CLOSEOUT.md`
- `docs/agents/GITHUB_ONLY_EXECUTION.md`
- `docs/agents/PROMPTING_HANDOVER.md`
- `docs/agents/TERMINAL_ONLY_COMMUNICATION.md`
- `docs/agents/CONTEXT_ROUTING.md`
- `docs/agents/README.md`

Current `docs/agents/AGENTS.md` actively routes DELIVERY for substantial implementation/validation/closeout, ANTI_STALL for long-running/retry/CI wait/continuation, TERMINAL_ONLY for autonomous/scheduled work, GITHUB_ONLY when local execution is unavailable, and AUTONOMOUS_PROGRAM_CONTINUATION for programme start/continuation. They are therefore operative on their triggers, not inert history.

## Material residue

Severity: P1 for repository-wide programme closeout; not a retroactive defect in #1304's explicitly bounded acceptance.

Current `docs/agents/GITHUB_ONLY_EXECUTION.md` lines 83-100 permits direct squash merge when auto-merge is unavailable after listed checks pass. Bound META `docs/agents/policy/ORGANIZATION_AGENT_POLICY.md` lines 39-45 instead makes protected enforcement/Merge Queue integration authority and states that no bypass or direct merge substitutes for an unavailable enqueue tool. Current root Platform instructions also forbid protection bypass. This is an active competing global integration controller.

Current `docs/agents/TERMINAL_ONLY_COMMUNICATION.md` independently maps `low_noise` to `terminal_only`, forbids intermediate progress by default, and claims to control over broader keep-informed wording. That is another active global communication controller rather than a Platform domain delta.

Minimal remedy: keep the programme nonterminal until the independently owned #1302/#1303 cleanup is reconciled and integrated, or explicitly retain this as unresolved W6 debt without claiming repository-wide one-rule/one-authority completion.

## External draft semantic assessment

The exact #1303 head reductions of the eight requested files preserve the necessary Platform-specific deltas:

- local task-status/checkpoint mapping without copied retry counters;
- live programme selector, one-writer overlap check, and protected-operation exclusions;
- complete producer/consumer layers, real delivered-path E2E, exact-head `platform-gate`, findings/PR hygiene and task closeout;
- Platform-only repository scope, current GitHub state and no temporary-workflow workaround;
- prompt objective, writable scope, Platform constraints, current locators, material evidence/next action, Polish owner advice and concise-English worker prompts;
- durable evidence, material owner interruptions and no inflation of PR/static proof to product/production proof.

Branch disposition remains machine-owned by `TASK_TEMPLATE.md` / `GOVERNANCE_CONTRACT.json`. Detailed execution-resource safety remains in `EXECUTION_RESOURCE_HYGIENE.md`, and the draft adds the corresponding `execution-resources` route to `CONTEXT_ROUTING.md`. No unique Platform safety or domain invariant was lost in the reviewed reductions.

## Integration blocker for PR #1303

Severity: P1 before integration.

PR #1303 is behind current main by #1304 and diverged. Its root instruction blobs differ from the qualified main:

- root `AGENTS.md`: current main blob `4ed79b6095f72826a920740f2751f3d9297db466`, draft head blob `a9337518c499d63935c6eec0bb5deb721e588862`;
- `docs/agents/AGENTS.md`: current main blob `686df3386b39329bcd80946a3f6be8b137417eb2`, draft head blob `fd10b1df388f1ce92cffaa9572798d7ad0e5d1a2`.

Minimal remedy: non-force reconcile onto current main, preserve #1304's binding, loader, evaluator/prompt qualification, evidence and accepted root bootstrap unless a current change is independently justified, then review the exact current-main delta and run the required exact-head gate. The 27-file old-base PR diff is not the current candidate diff.
