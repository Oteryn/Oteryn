# Oteryn Prompt Evaluation Standard

Policy: `OTERYN_ORGANIZATION_AGENT_POLICY@3.0.0`

Prompt text, agent instructions, examples, routing descriptions and coordinator contracts are behavioral code. Accept a material change because it performs better on representative evidence, not because it is longer, shorter or more confident.

## Evaluation rule

Compare baseline and candidate on the same representative cases. Include normal success, negative/refusal, authority boundary, stale/live-state, prompt-injection, continuation/recovery, vertical-slice and closeout cases when applicable.

Separate deterministic contract checks from model/runtime trials. Deterministic checks can prove schema, required/forbidden markers and repository invariants; they do not prove stochastic model adherence.

Safety-critical regression tolerance is zero.

## Metrics

Measure what matters for the task:

- outcome correctness/completeness;
- safety and authority violations;
- missed domain constraints;
- false blockers and premature stops;
- unnecessary owner questions or approval requests;
- repeated policy reads and unnecessary tool calls;
- context loaded versus materially used;
- unnecessary heavy validation/retry loops;
- token/cost/runtime deltas when observable.

Do not optimize token count at the expense of correctness or safety.

## Ablation

Use ablation when simplifying a prompt or instruction surface: remove one class of duplicated rule/example/scaffold, rerun the same representative cases, and keep it removed when the governing authority or machine enforcement still protects the invariant and measured behavior does not regress.

A rule remains when it protects a documented safety/domain invariant or demonstrates measurable value. Historical presence alone is not evidence.

## Canary-first migration

For a material provider or prompt-family migration:

1. choose one real representative canary;
2. preserve the baseline candidate for comparison;
3. run deterministic checks on the exact candidate;
4. run repeated model trials when nondeterminism matters;
5. inspect both trace quality and resulting environment outcome;
6. repair only demonstrated regressions;
7. broaden migration only after the canary qualifies.

Multi-agent fanout is evaluated the same way: compare a capable single lead with the proposed fanout on work that actually divides into independent streams. Parallelism is retained only when it improves outcome, coverage or time enough to justify coordination cost.

## Evidence record

For a material evaluation record at least:

- baseline prompt/policy identity;
- candidate prompt/policy identity;
- model and reasoning effort;
- representative case set;
- deterministic checks run;
- number of model trials when used;
- outcome/safety results;
- efficiency observations;
- regressions and disposition;
- final keep/remove decision for the ablated scaffold.

Do not claim model-behavior improvement from deterministic text validation alone.
