# OTERYN-CONTEXT-OPTIMIZATION-QUALIFICATION

Short invocation:

```text
Oteryn: context qualification
```

## Outcome

Autonomously complete the missing behavioral qualification for `Oteryn: context optimization` using current authority in:

- `Oteryn/Oteryn#166`;
- `Oteryn/Oteryn#168`;
- `Oteryn/Oteryn-Atlas#349`.

Do not redesign the programme, repeat the instruction-debt audit, or broaden the task. Optimize for correct uncontaminated evidence with minimum practical token/context use.

## Hard execution budget

This invocation is cost-sensitive.

- GPT-5.6 Sol: **LOW / LIGHT effort only**.
- GPT-6 Astra: **LOW / LIGHT effort only**.
- LOW/LIGHT is the hard maximum for Sol/Astra. Never escalate them to Medium, High, Extra High, Max or highest-available.
- If effort labels differ, use the lowest available setting and record the requested setting separately from any runtime attestation.
- Never invent model/effort attestation. If the required model/effort cannot be controlled, mark the affected arm truthfully and continue independent valid work.

Preferred Work coordinator: GPT-5.6 Sol at LOW/LIGHT, coordination only.

Use GPT-5.6 Terra at LOW/LIGHT for mechanical support where delegation has clear net value: one-time source inspection, fixture preparation, source-identity checks, result parsing, integrity/completeness checks, normalization and handoff assembly. Do not spend Sol/Astra on work Terra can do.

Terra support is not Sol/Astra behavioral evidence.

## Prior R5Q evidence — do not rerun

Historical R5Q Issue #164 / PR #165 and its persisted result candidate in `Oteryn/Oteryn#170` (`docs/evidence/OTERYN-R5Q-RESULTS.md`) are **prior regression evidence only**.

Do not rerun or count those 22 historical arms toward #166.

Use #170 only as context that the earlier R5 optimization produced a final reviewer verdict `UNDER_LOADED_REGRESSION`, including a Game authority-context regression and an Atlas governing-evidence regression. Its behavioral workers were requested as GPT-5.6 Terra / Medium, final reviewer as Sol / High, and Astra was not used. Therefore those results must not be represented as Sol or Astra behavioral qualification for the current #166 candidate.

If #170 is still unmerged, read it from its current PR/head; do not require its integration before continuing #166 qualification.

## Freeze the current candidate once

Before behavioral workers start, perform one bounded refresh of #166, #168 and Atlas #349. Read only the current qualification inputs needed to freeze the tested instruction identities:

- `docs/evidence/context-optimization-20260907/README.md`;
- `docs/evidence/context-optimization-20260907/source-evidence.json`;
- `docs/agents/evals/r5-instruction-efficiency/TRIAL_PROTOCOL.md`.

`REVIEWER.md` may be read by coordinator/support only; never expose it to behavioral workers.

Freeze the current META and Atlas candidate instruction blob identities. If a later PR head changes only evidence/metadata and the tested blobs remain byte-identical, keep completed trials. If a tested instruction blob changes materially, invalidate only affected trials.

Do not make every expensive worker re-read live GitHub state.

## Required matrix

Use exactly the existing C1-C8 families recorded in PR #168 evidence:

1. small local work;
2. domain-contract handling;
3. high-risk/control-plane decision;
4. unrelated unavailable source;
5. stale-state reconciliation;
6. proportional verification;
7. historical/inert imperative text;
8. safe explicit owner request conflicting only with a generic workflow preference.

Each family has A = baseline and B = candidate.

Current #166 requires separate populations:

- Sol: C1A-C8A + C1B-C8B = 16 arms;
- Astra: C1A-C8A + C1B-C8B = 16 arms.

Total: **32 behavioral arms**. Do not add a full Terra behavioral matrix.

## Minimal isolated fixtures

Prepare the smallest sufficient per-arm input before launching expensive workers. A worker should receive only:

1. neutral trial protocol;
2. exact task text for its case;
3. relevant baseline **or** candidate instruction material;
4. exact source identity;
5. minimum tools needed by that case.

Do not provide the sibling arm, reviewer rubric, expected answer, prior worker output, historical R5Q output, whole #166 programme, whole repository corpus or coordinator prompt unless the specific case truly requires it.

The experiment measures instruction behavior, not repository-search endurance.

## Behavioral workers

Sol arms:

- GPT-5.6 Sol;
- LOW/LIGHT;
- fresh isolated context;
- no child-agent delegation.

Astra arms:

- GPT-6 Astra;
- LOW/LIGHT;
- fresh isolated context;
- no child-agent delegation.

Use one fixed lowest available effort inside each population. If exact child-model selection is unavailable, do not substitute Terra or another model; mark the affected arms truthfully.

Run independent arms at the maximum safe supported concurrency. If 32-way concurrency is unavailable, use deterministic batches without changing model, effort, tools, task text or source definitions. Never trade isolation/model correctness for parallelism.

Trial workers must stay small: no organization audit, unrelated history scan, broad web research, sibling inspection, reviewer invocation, delegation, repeated unchanged refresh or broad/full tests unless the case specifically requires them.

## Trial result

Each behavioral worker returns only:

1. concise visible task answer;
2. `trial_result` following `TRIAL_PROTOCOL.md`.

Record observable source identity, requested model/effort, runtime attestation when exposed, instruction reads, repeated reads, tool calls, clarification/confirmation requests, blocker claims, handoffs, verification and limitations.

Do not request or persist hidden reasoning. Do not estimate token/cache/API/financial cost when not exposed; use `NOT_MEASURED`, `NOT_ATTESTED` or `UNKNOWN`.

## Integrity and reruns

After collection, use Terra LOW/LIGHT where useful to check:

- all expected arms;
- correct model/effort request;
- isolated arm identity;
- identical A/B task text within each pair;
- correct source locator;
- no sibling/reviewer leakage;
- telemetry presence;
- no Terra output counted as Sol/Astra evidence.

Classify arms as `VALID`, `INCONCLUSIVE`, `INVALID_CONTAMINATED`, `NOT_EVALUATED_MODEL_CONTROL`, `NOT_EVALUATED_EFFORT_BUDGET`, or `NOT_EVALUATED_RUNTIME_LIMIT`.

Rerun only a concrete execution defect such as wrong model/source, missing fixture, transport failure or contamination. Do not rerun merely because A/B outputs differ.

Do not start an expensive final reviewer. Final comparative scoring happens externally after evidence handoff.

## Evidence delivery

Persist the current qualification centrally in META PR #168 without modifying the tested instruction blobs:

- `docs/evidence/context-optimization-20260907/behavioral-trials.jsonl`;
- `docs/evidence/context-optimization-20260907/behavioral-trials-summary.md`.

Keep Sol and Astra records separate; summarize Terra support separately. Do not commit hidden reasoning or unnecessary Work transcripts.

After evidence publication, verify the tested instruction blobs are unchanged and record the new evidence-only META head separately from the tested blob identities.

Run only repository-required checks applicable to the evidence-only change. Do not manually trigger unrelated broad suites or restore suspended Atlas verification.

Add one concise receipt to META PR #168 with tested META/Atlas blob identities, requested Sol/Astra model+effort, attestation availability, valid/inconclusive/missing counts, evidence paths/commit, required CI result, and:

`FINAL_BEHAVIORAL_SCORING_PENDING_EXTERNAL_REVIEW`

Add only a short pointer to Atlas #349 when useful.

## Boundaries and completion

This invocation does not authorize merging #168/#349, auto-merge/Merge Queue enqueue, closing #166/#315, workflow/protection changes, runtime/product changes, deployment or restoration of suspended Atlas verification.

Do not stop the whole task because one model/arm is unavailable. Continue all independent valid work and record the exact limitation, e.g. `MODEL_SELECTION_NOT_EXPOSED`, `ASTRA_NOT_AVAILABLE_ON_CHILD_WORKER`, `EFFORT_CONTROL_NOT_EXPOSED`, `CONCURRENCY_LIMIT`, or `TOOL_TRANSPORT_FAILURE`.

Continue until all executable Sol/Astra arms are collected, integrity-checked, persisted, required evidence-only CI is complete, the PR receipt exists, and a compact external-review handoff is ready.

Final response should contain only:

- expected arms: 32;
- Sol completed / valid / inconclusive / unavailable;
- Astra completed / valid / inconclusive / unavailable;
- coordinator and population requested model/effort;
- runtime attestation availability;
- maximum parallelism achieved;
- tested META/Atlas blob identities;
- evidence commit/paths;
- required CI result;
- PR receipt link/id;
- exact unresolved blockers;
- `READY_FOR_EXTERNAL_REVIEW` only when evidence is sufficient.

Do not declare an A/B winner.