# Oteryn Prompt Evaluation Standard

Policy: `OTERYN_ORGANIZATION_AGENT_POLICY@3.0.0`

Evaluate material instruction/harness changes with the same representative cases before and after the change. Optimize the cost of correctly completed tasks, not Markdown size alone.

## Three distinct evidence levels

1. **Contract checks:** schemas, source identity, references and specific deterministic regressions. Text lint is not proof of semantic safety.
2. **Adoption/delivery:** the provider uses the intended consumer, and the actual client receives the required sources for its starting directory and task. A binding alone does not prove delivery.
3. **Behavior:** real task outcomes, repeated trials when nondeterminism matters, missed invariants, false blockers and unnecessary work. Static checks do not count as model trials.

Safety-critical regression tolerance is zero. This acceptance rule does not claim that finite trials prove absence of all future regressions. Record unavailable evidence as `NOT_EVALUATED`, not PASS.

## Comparison

Choose a representative canary before broad migration. Relevant cases include a local fix, a domain-contract change, a high-risk control-plane change, a documentation-only task and a continuation. Include refusal/authority boundaries, stale facts and prompt-injection cases when affected.

Preserve baseline and candidate revisions, task inputs, tools, environment and acceptance criteria. Hold model and effort constant while comparing instructions. Evaluate model, effort, delegation and CI changes separately; otherwise their effects cannot be attributed to instruction cleanup. Use ablation to remove one group at a time where practical.

A small initial comparison is screening, not a statistically established organization-wide saving. Repeat unstable or safety-relevant cases and inspect the resulting code/environment, not just the agent narrative. Keep a useful domain/safety rule unless its role is preserved or adequate evidence supports removal.

## Cost and evidence

Record outcome quality and all attempted work, including failed attempts and child agents. Where observable, record input/output/reasoning/cache usage, actual model/effort, tool calls, repeated reads, heavy test runs, elapsed execution/wait time and owner interventions. Measure CI across PR, Merge Queue and main rather than moving expense between them.

Report aggregate measured cost divided by accepted tasks with the sample size and uncertainty. Keep owner time separate unless a valuation is agreed. Do not turn subscription usage into a fictional API invoice, defaults into verified hard limits, or reduced bytes into a token-saving percentage.

Use one compact evaluation record: revisions, actual client/start directory/configuration, case set, checks, model-trial count, outcomes, efficiency observations, regressions and disposition. Do not add a mandatory per-task reporting system. Keep full logs outside the always-loaded instruction surface and redact sensitive data.

Broaden rollout only when applicable checks, actual adoption and representative behavior qualify. Preserve a coherent rollback for binding, instructions and their consumers; no rollback may waive current safety requirements.
