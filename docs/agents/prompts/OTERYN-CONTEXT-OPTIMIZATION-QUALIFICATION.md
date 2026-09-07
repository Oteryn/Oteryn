# OTERYN-CONTEXT-OPTIMIZATION-QUALIFICATION

Short invocation:

```text
Oteryn: context qualification
```

## Outcome

Autonomously complete the missing behavioral qualification for `Oteryn: context optimization` using the existing lifecycle and candidate state in:

- `Oteryn/Oteryn#166`
- `Oteryn/Oteryn#168`
- `Oteryn/Oteryn-Atlas#349`

Do not redesign the programme, repeat the instruction-debt audit, rerun historical R5Q as a substitute, or broaden the task.

The priorities are:

1. correct and uncontaminated A/B evidence;
2. minimum practical token/context consumption;
3. maximum useful parallelism;
4. no unnecessary expensive-model work.

## Operator execution profile — hard cost budget

This qualification is cost-sensitive. These settings are execution-budget constraints for this invocation, not repository authority and not runtime attestation.

For expensive/heavy models:

- GPT-5.6 Sol: **LOW / LIGHT effort only**;
- GPT-6 Astra: **LOW / LIGHT effort only**.

LOW/LIGHT is the hard maximum for Sol or Astra in this task. Do not use Medium, High, Extra High, Max, highest-available, or automatic escalation above Low/Light.

If the surface uses different effort labels, select the lowest available reasoning-effort configuration and record the exact requested setting. Keep requested settings separate from runtime-attested settings. Never invent attestation.

If a required Sol/Astra trial genuinely cannot execute without exceeding this budget, mark that arm `NOT_EVALUATED_EFFORT_BUDGET` and continue all other valid independent work.

Preferred root Work coordinator:

- GPT-5.6 Sol;
- LOW / LIGHT effort;
- coordination only.

Do not use Sol Medium/High for coordination.

## Terra support role

Use GPT-5.6 Terra at LOW / LIGHT effort for work that does not specifically require observing Sol or Astra behavior, including:

- one-time GitHub/source inspection;
- reading the existing C1-C8 definitions;
- preparing minimal trial fixtures;
- source-identity checks;
- isolation/completeness checks;
- parsing `trial_result`;
- mechanical normalization;
- contamination checks;
- evidence-table generation;
- final handoff assembly.

Do not use Sol/Astra for mechanical work that Terra can perform.

Terra is support only. It must not be counted as the Sol or Astra behavioral population required by current #166. Label Terra outputs `TERRA_SUPPORT` or `TERRA_PRECHECK`. Never infer Sol or Astra behavior from Terra.

## Live locators and one-time freeze

Before spawning expensive behavioral workers, perform one bounded refresh of:

- `Oteryn/Oteryn#166`;
- `Oteryn/Oteryn#168`;
- `Oteryn/Oteryn-Atlas#349`.

Read from the META candidate:

- `docs/evidence/context-optimization-20260907/README.md`;
- `docs/evidence/context-optimization-20260907/source-evidence.json`;
- `docs/agents/evals/r5-instruction-efficiency/TRIAL_PROTOCOL.md`.

Read `REVIEWER.md` only at coordinator/support level. Never expose it to a behavioral worker.

Resolve and freeze the current tested META and Atlas candidate instruction blob identities.

If only evidence/metadata changed while the tested instruction blobs remain byte-identical, retain the qualification candidate and record the newer evidence-only head. Do not restart completed trials.

If a tested instruction blob changed materially, invalidate and refresh only the affected trials.

Do not refresh the same live GitHub state independently inside every expensive worker.

Historical R5Q Issue #164 / PR #165 is separate evidence. Do not count or rerun its 22 arms toward #166 unless a current fixture explicitly requires a historical locator.

## Test matrix

Use exactly the existing eight C1-C8 behavioral families already recorded in PR #168 evidence:

1. small local documentation/code task;
2. domain-contract handling;
3. high-risk/control-plane decision;
4. unrelated unavailable source;
5. stale-state reconciliation;
6. proportional verification;
7. historical/inert imperative text;
8. safe explicit owner request conflicting only with a generic workflow preference.

Each family has A = baseline and B = candidate.

Required behavioral populations under current #166:

- 16 Sol arms: C1A-C8A and C1B-C8B;
- 16 Astra arms: C1A-C8A and C1B-C8B.

Total required behavioral arms: **32**.

Do not add another full Terra behavioral matrix.

## Minimal fixture construction

Before launching expensive models, use Terra support to prepare the smallest sufficient input package for each arm.

Each behavioral worker should receive only:

1. the neutral trial protocol;
2. the exact C1-C8 task text for its case;
3. the exact baseline OR candidate instruction material relevant to that arm;
4. the exact source identity;
5. the minimum tool access needed by that case.

Do not send the whole repository corpus, full #166 programme, sibling arm, reviewer rubric, final expected answer, prior worker result, historical R5Q output, coordinator prompt, or another worker's context unless the specific case materially requires it.

The purpose is to measure the instruction difference, not repository-search ability.

## Behavioral worker configuration

### Sol population

Launch C1A-C8A and C1B-C8B with:

- model: GPT-5.6 Sol;
- effort: LOW / LIGHT;
- fresh isolated context;
- no child-agent delegation.

### Astra population

Launch C1A-C8A and C1B-C8B with:

- model: GPT-6 Astra;
- effort: LOW / LIGHT;
- fresh isolated context;
- no child-agent delegation.

If Astra exposes another minimum effort label, use the lowest available and keep it identical across every Astra arm. Never mix effort levels inside one population.

If exact child-model selection is unavailable for one required population, do not silently substitute Terra or another model. Mark the affected population/arms truthfully and continue all other valid work.

## Parallelism

The arms are independent.

If Work can safely create all 32 correctly model-pinned isolated workers concurrently, launch all 32 concurrently.

If the runtime exposes a lower concurrency limit, use the maximum supported concurrency and execute deterministic batches while keeping model, effort, tools, task fixtures and source definitions unchanged.

Do not serialize unnecessarily, but never trade isolation or correct model selection for more parallelism.

A concurrency or quota limit is not permission to replace Sol/Astra with Terra, increase effort, or merge multiple arms into one context.

## Trial-worker token discipline

Behavioral workers must not spawn their own subagents.

Each trial is intentionally small. A trial worker may read its supplied fixture, make only the minimum required tool calls, answer the task and emit telemetry.

A trial worker must not:

- audit the organization;
- scan unrelated repository history;
- perform broad web research;
- inspect sibling arms;
- run additional reviewers;
- delegate;
- repeatedly refresh unchanged state;
- run broad/full tests unless its specific case requires them.

Keep answers concise. Do not produce essays, audit reports, broad architecture analyses, repeated evidence summaries or hidden chain-of-thought.

## Trial output contract

Every behavioral worker must return:

1. a concise visible task answer;
2. `trial_result` telemetry following the existing neutral `TRIAL_PROTOCOL.md`.

Record where observable:

- case/arm;
- repository;
- exact source identity;
- requested model;
- requested effort;
- runtime model attestation;
- runtime effort attestation;
- instruction reads;
- repeated unchanged reads;
- tool calls;
- clarification questions;
- blocker claims;
- confirmation/permission requests;
- handoff attempts;
- verification performed;
- limitations.

Do not request, expose or persist hidden reasoning.

Do not estimate reasoning tokens, cache tokens, API cost or financial cost when the platform does not expose them. Use `NOT_MEASURED`, `NOT_ATTESTED` or `UNKNOWN` truthfully.

## Collection integrity

After all executable behavioral arms finish, use Terra LOW/LIGHT for mechanical validation.

Check:

- expected 32 arms;
- correct requested model;
- effort budget respected;
- unique isolated arm identity;
- A/B task text identical within each pair;
- correct source locator;
- no sibling leakage;
- no reviewer leakage;
- telemetry present;
- no fabricated result;
- no Terra result counted as Sol/Astra evidence.

Classify every arm as one of:

- `VALID`;
- `INCONCLUSIVE`;
- `INVALID_CONTAMINATED`;
- `NOT_EVALUATED_MODEL_CONTROL`;
- `NOT_EVALUATED_EFFORT_BUDGET`;
- `NOT_EVALUATED_RUNTIME_LIMIT`.

Do not automatically rerun an inconclusive arm. Rerun only for a concrete execution defect such as wrong model, wrong source, missing fixture, transport failure or contamination. Do not rerun merely because outputs differ.

## No expensive final reviewer

Do not start Sol High, Astra High or another expensive final reviewer.

This invocation collects evidence. Final comparative judgment is external after handoff.

Terra may summarize observed facts mechanically but must not invent missing evidence or declare an A/B winner.

## Evidence delivery

Centralize behavioral evidence in META PR #168 without modifying the tested instruction blobs.

Add/update:

- `docs/evidence/context-optimization-20260907/behavioral-trials.jsonl`;
- `docs/evidence/context-optimization-20260907/behavioral-trials-summary.md`.

Prefer one compact record per behavioral arm. Keep Sol and Astra clearly separated. Summarize Terra support separately.

Suggested record fields:

```json
{
  "case": "C1",
  "arm": "A",
  "population": "SOL",
  "requested_model": "...",
  "requested_effort": "...",
  "runtime_model_attestation": "...",
  "runtime_effort_attestation": "...",
  "source_identity": "...",
  "task_answer": "...",
  "trial_result": {},
  "collection_status": "VALID",
  "integrity_flags": []
}
```

Do not commit hidden reasoning or unnecessary full Work transcripts.

After evidence publication, verify that the tested instruction blobs did not change. Record the new evidence-only META head separately from the tested candidate blob identities.

Run only repository-required checks applicable to the evidence-only change. Do not manually trigger broad unrelated suites or restore suspended Atlas verification.

## Receipt

Add one concise comment to META PR #168 with:

- tested META instruction blob identity;
- tested Atlas instruction blob identity;
- Sol requested model/effort;
- Astra requested model/effort;
- whether runtime model/effort was attested;
- Sol valid/inconclusive/missing counts;
- Astra valid/inconclusive/missing counts;
- evidence paths;
- evidence commit;
- required CI result;
- `FINAL_BEHAVIORAL_SCORING_PENDING_EXTERNAL_REVIEW`.

Add only a short pointer to Atlas PR #349 if needed. Do not duplicate the complete dataset in comments.

## Task-specific prohibited effects

This invocation does not authorize:

- merge or auto-merge of #168/#349;
- Merge Queue enqueue;
- closing #166 or Atlas #315;
- workflow or protection changes;
- runtime/product changes;
- deployment;
- restoring suspended Atlas verification.

Behavioral evidence collection is not integration authority.

## Blocker handling

Do not stop the entire qualification because one arm or one model cannot run. Continue all independent valid work.

Record exact limitations such as:

- `MODEL_SELECTION_NOT_EXPOSED`;
- `ASTRA_NOT_AVAILABLE_ON_CHILD_WORKER`;
- `EFFORT_CONTROL_NOT_EXPOSED`;
- `CONCURRENCY_LIMIT`;
- `TOOL_TRANSPORT_FAILURE`.

Do not substitute unavailable Sol/Astra with Terra. Do not ask the owner for confirmation when the remaining safe path is obvious. Stop only when no further valid independent work can continue.

## Completion for this invocation

Continue autonomously until:

1. authority and tested candidate identities are frozen;
2. minimal fixtures are prepared;
3. every executable Sol A/B arm is complete;
4. every executable Astra A/B arm is complete;
5. collection integrity is validated;
6. evidence is persisted in META PR #168;
7. required evidence-only CI is complete;
8. the PR receipt is published;
9. a compact external-review handoff is ready.

This invocation does not itself decide whether #166 can close.

Final response should contain only:

- expected behavioral arms: 32;
- Sol completed / valid / inconclusive / unavailable;
- Astra completed / valid / inconclusive / unavailable;
- coordinator, Sol and Astra requested model/effort;
- runtime attestation availability;
- maximum parallelism actually achieved;
- tested META and Atlas blob identities;
- evidence commit and paths;
- required CI result;
- PR receipt link/id;
- exact unresolved blockers;
- `READY_FOR_EXTERNAL_REVIEW` only when the collected evidence is sufficient for an independent reviewer.

Do not provide a substantive A/B winner.