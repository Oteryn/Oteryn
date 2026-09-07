# Oteryn Context & Overconstraint Optimization Programme

Lifecycle authority: `Oteryn/Oteryn#166`.

This programme is a post-policy-v3 optimization pass. It reduces unnecessary instruction exposure and behavioral micromanagement for GPT-6 Astra and GPT-5.6 Sol while preserving real safety, product authority, durable domain invariants and protected GitHub enforcement.

It does not replace `OTERYN_ORGANIZATION_AGENT_POLICY@3.0.0`, reopen completed #142, or create another governance operating system.

## 1. Why this programme exists

The first instruction-debt programme removed large duplicated policy families and centralized shared semantics. The remaining problem is subtler: an instruction can be correct and still be harmful when it is loaded too early, too broadly or repeatedly.

Current OpenAI guidance for GPT-6 Astra warns that the model is more sensitive to instructions in `AGENTS.md`, skills and other accessible files, and that unclear or conflicting guidance can cause early pauses or blocked work. OpenAI's Codex harness guidance reports that a large monolithic `AGENTS.md` crowded out relevant task/code context and recommends a short map with progressive discovery of deeper sources. OpenAI's current testing guidance also recommends proportional verification instead of repeated broad testing after the required checks already pass.

The target is therefore not minimum Markdown. The target is the smallest context and control surface that still produces correctly authorized, correctly implemented and correctly verified work.

## 2. Source basis

Primary sources:

- OpenAI, GPT-6 Astra model guidance: <https://developers.openai.com/api/docs/guides/latest-model>
- OpenAI, Harness engineering: leveraging Codex in an agent-first world: <https://openai.com/index/harness-engineering/>
- OpenAI, Using skills: <https://openai.com/academy/skills/>

Secondary cross-check:

- Anthropic, Effective context engineering for AI agents: <https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents>

Existing Oteryn sources remain the organization baseline:

- `docs/agents/policy/ORGANIZATION_AGENT_POLICY.md`
- `docs/agents/policy/PROMPTING_STANDARD.md`
- `docs/agents/policy/PROMPT_EVAL_STANDARD.md`
- `docs/evidence/OTERYN-INSTRUCTION-DEBT-AUDIT-20260906.md`
- `docs/evidence/OTERYN-AGENT-INSTRUCTION-OPTIMIZATION-RESEARCH-20260907.md`
- `docs/evidence/agent-optimization-20260907/REPORT.md`
- `docs/agents/evals/r5-instruction-efficiency/**`

The old audits are evidence baselines, not authority to replay their implementation.

## 3. Design principles

### 3.1 Outcome over procedure

Give capable agents the observable outcome, real constraints and acceptance evidence. Do not prescribe a detailed sequence unless ordering protects correctness, safety or a proven evaluation result.

### 3.2 One rule, one authority

A rule should have one semantic owner. Provider overlays may narrow central policy and preserve local invariants, but must not fork shared execution/review/retry/merge/tool policy.

### 3.3 Progressive disclosure

Ordinary work should begin with the smallest useful map. Specialist procedures, temporary programmes, deployment instructions, verification depth and uncommon capabilities should be discovered only when a concrete trigger makes them relevant.

### 3.4 Enforce invariants mechanically where possible

Prefer rulesets, permissions, schemas, validators, linters and CI for deterministic constraints. Retain prose when the agent needs the rule to choose a safe action before the machine gate is reached; otherwise avoid repeating the same constraint in multiple instruction layers.

### 3.5 Preserve thinking room

Do not turn useful heuristics into universal `MUST`/`NEVER` rules. Reserve absolute language for actual authority, safety, integrity and accepted product invariants. Let the agent choose implementation and investigation strategy inside those boundaries.

### 3.6 Proportional verification

Required repository checks remain required. Focused checks should match the change. Broaden or repeat verification only after a material change, a failure, unresolved risk, or a concrete requirement justifies it.

### 3.7 No optimization by deletion alone

A smaller file is not automatically better. Preserve unique product knowledge, security boundaries and architecture invariants. Record `UNKNOWN_NEEDS_EVAL` rather than deleting a rule whose behavioral role is unclear.

## 4. Target context architecture

The intended default chain is:

```text
platform/system instructions
        ↓
short repository AGENTS.md map + durable invariants
        ↓
nearest local AGENTS.md delta, when applicable
        ↓
live Issue / PR / task-specific prompt
        ↓
routed specialist sources discovered on concrete triggers
        ↓
deterministic repository enforcement
```

### ALWAYS

Keep only information that an ordinary task in that scope may need before it knows which specialist route to take:

- repository/product identity and authority boundary;
- minimal safety/credential/production boundary needed before a write;
- durable product invariants that cannot be inferred safely;
- how to locate deeper authority;
- one short statement preserving repository protection/integration authority where necessary.

### ROUTED

Typical candidates:

- deployment and production procedures;
- unusual credentials/capability routing;
- detailed runner topology;
- specialist verification profiles and FullWorld rules;
- migrations/recovery;
- security-sensitive specialist workflows;
- architecture domain procedures;
- temporary maintenance programme detail.

### TASK_ONLY

- observable outcome;
- writable scope and task-specific prohibited effects;
- live Issue/PR/contract locators;
- unique domain dependencies;
- result-specific acceptance evidence;
- exceptional stop/handoff conditions.

### DETERMINISTIC

Prefer machine enforcement for closed predicates such as:

- branch/ruleset required checks;
- path/mode allowlists;
- schema/version validity;
- exact machine-readable states;
- mechanically provable duplication or lifecycle contracts;
- credential/tool argument gates where already implemented.

### ARCHIVE / INERT

Historical prompts, plans and evidence remain readable provenance but must not look dispatchable or compete with current authority.

## 5. Classification test

Every active/reachable instruction should receive exactly one working disposition:

- `KEEP_ALWAYS`
- `ROUTE`
- `TASK_ONLY`
- `DETERMINISTIC`
- `ARCHIVE_INERT`
- `REMOVE_DUPLICATE`
- `UNKNOWN_NEEDS_EVAL`

Primary decision test:

> Would omitting this instruction from an ordinary task materially increase the risk of an incorrect result or unauthorized effect before a routed source or deterministic control can handle it?

If **no**, it does not belong in `ALWAYS`.

Additional tests:

1. Is the same semantic rule already owned elsewhere?
2. Is this product knowledge or agent-operating procedure?
3. Is the rule current, or transient programme state?
4. Does the agent need it before it can identify a trigger?
5. Can a deterministic control enforce it more reliably?
6. Does the wording force a method where only the outcome matters?
7. Does it introduce permission checks, pauses or reviews beyond real authority?
8. Does it cause repeated reads/tests/reconciliation without new information?
9. Could a negative/example/historical mention accidentally appear operative?
10. Is its behavioral value unknown enough to require matched evaluation before removal?

## 6. Design budgets

These are review heuristics, not hard pass/fail limits.

- Root `AGENTS.md`: prefer a short map comparable in spirit to OpenAI's roughly 100-line Codex example; exceed it only for demonstrated always-needed invariants.
- Nested `AGENTS.md`: local delta only; do not repeat root/global policy.
- Reusable task prompt: normally short enough to express only task-specific deltas; long specifications are allowed when the specification itself changes the correct result.
- Historical prompt discovery: ordinary active discovery should not require scanning large retired prompt families.
- Skills: zero generic governance skills; add only a repeatable specialized workflow with a precise trigger and on-demand details.

Do not create automated failure thresholds from these heuristics without evaluation evidence.

## 7. Work packages

### WP0 — live baseline and ownership map

For META, Game, Platform and Atlas:

- refresh protected `main`, applicable `AGENTS.md`, current policy binding, live ownership/PR overlaps and maintenance constraints;
- inventory active/reachable instruction surfaces separately from historical evidence;
- record which sources are actually delivered automatically, explicitly loaded, routed or merely present in Git;
- record source bytes/lines and ordinary effective bootstrap where measurable;
- preserve `UNKNOWN` for client loader behavior or token telemetry that cannot be observed.

Exit: one evidence-backed instruction-load map per permanent repository.

### WP1 — always-loaded surface audit

Classify every clause in root and applicable high-frequency nested `AGENTS.md` using section 5.

Do not begin by rewriting. First identify:

- durable invariants;
- transient programme detail;
- specialist procedures;
- duplicated global policy;
- deterministic rules restated in prose;
- over-broad permission/confirmation language;
- sequencing that unnecessarily constrains implementation strategy.

Exit: approved candidate disposition with no unique invariant lost.

### WP2 — META map reduction

Evaluate META `AGENTS.md` against the map-not-manual target. Likely candidates for routing include detailed runner and restricted-publishing procedure, but no move is authorized by this plan until WP1 proves the destination and delivery are safe.

Preserve central policy ownership and the ability to discover every routed authority.

Exit: META root contains only justified `KEEP_ALWAYS` material plus routing.

### WP3 — provider overlay reduction

Treat each provider independently.

- Game: expect a small delta because current root is already thin; make no change when evidence does not justify one.
- Platform: preserve bounded instruction loading; remove only remaining unnecessary high-frequency procedure.
- Atlas: highest expected leverage. Separate durable Atlas authority/rendering invariants from temporary maintenance and specialist verification/deployment detail, subject to Issue #315 and current ownership.

No cross-provider mass rewrite. One writer per repository.

Exit: each provider has a justified ordinary bootstrap and no copied central operating system.

### WP4 — prompt discovery and historical separation

Inventory reusable/current prompts separately from historical/suspended prompts.

Prefer structural non-dispatchability over repeated warning prose. Do not rename/move files when active validators, maintenance allowlists, links or owners make the change unsafe; in that case use the smallest compatible lifecycle marker and defer structural relocation.

Large historical specifications may remain in Git without counting as a defect if ordinary agents do not load or mistake them for current authority.

Exit: active discovery has a clear current set; history cannot masquerade as current execution authority.

### WP5 — prose control to deterministic enforcement

For each repeated rule, identify its actual enforcing mechanism.

Examples include GitHub required checks, Merge Queue, path validators, schemas, branch protection, credential gates and permission scopes.

Remove or shorten duplicate prose only when the remaining agent-facing rule still tells the model enough to choose a safe action before deterministic enforcement.

Exit: no important invariant is defended mainly by many natural-language copies when a canonical semantic owner plus machine gate exists.

### WP6 — verification and continuation proportionality

Audit active instructions for patterns that can cause verification spirals or false stopping:

- repeated full-suite instructions after unchanged successful checks;
- independent review requirements duplicated across layers;
- stale candidate refresh rules that reset unrelated progress;
- generic permission prompts for safe reversible work;
- retry/checkpoint language that turns recovery state into a pause;
- false universal blockers when only one operation is affected.

Preserve all real required gates and fail-closed behavior for the affected operation.

Exit: the agent is directed to finish the task, not to repeat process without new evidence.

### WP7 — Sol/Astra matched behavior evaluation

Follow `PROMPT_EVAL_STANDARD.md` and reuse the existing R5 evaluation assets where suitable.

At minimum include representative cases for:

1. small local code/documentation fix;
2. domain-contract change;
3. high-risk control-plane decision;
4. task with an unrelated unavailable source;
5. stale live-state reconciliation;
6. required verification after a successful focused iteration;
7. historical/inert instruction containing imperative language;
8. explicit user request that is safe but conflicts with a generic workflow preference.

Compare baseline and candidate on the same task inputs, tools, model and effort where the surface exposes them.

Observe where available:

- accepted task outcome quality;
- safety/domain invariant preservation;
- false blockers;
- unnecessary permission/confirmation requests;
- repeated reads of the same sources;
- repeated/broadened tests without new justification;
- tool calls and child-agent work;
- owner interventions;
- elapsed execution/wait time;
- input/output/reasoning/cache tokens only when the platform exposes truthful telemetry.

Use Sol and Astra as separate evaluation populations. Do not infer Astra behavior from Sol or vice versa. Requested model/effort configuration is not runtime attestation when the client does not expose the resolved runtime.

Safety-critical regression tolerance is zero.

Exit: candidate is at least non-inferior on correctness/safety and demonstrates a credible reduction in false control or unnecessary work before broad rollout.

### WP8 — rollout and closeout

Integrate accepted changes through each repository's normal protected PR/Merge Queue path. Respect Atlas maintenance restrictions and Game/Platform live ownership.

After each provider integration:

- read back protected `main`;
- verify binding/consumer integrity where applicable;
- rerun only the evaluation needed to establish that the delivered instruction surface matches the reviewed candidate;
- roll back the coherent instruction/consumer change if a material safety or behavioral regression is demonstrated.

Final closeout must distinguish:

- source-volume reduction;
- effective delivered context;
- deterministic contract/adoption proof;
- observed Sol behavior;
- observed Astra behavior;
- CI/tool-work reduction;
- unavailable token or financial telemetry.

## 8. Repository priority

Priority is based on expected leverage, not a mandate to change files:

1. Atlas — largest remaining prompt/instruction corpus and temporary maintenance detail.
2. META — central map should model the desired architecture.
3. Platform — already strong bounded loading; likely small residual cleanup.
4. Game — current root is already thin; change only on concrete evidence.

Live overlap and safety can reorder execution. A repository that is already proportionate should receive a truthful `NO_CHANGE_REQUIRED` rather than churn.

## 9. Execution shape

Operator recommendation, outside the semantic task prompt:

- primary implementation surface: ChatGPT Work;
- primary implementation model: GPT-6 Astra;
- default reasoning: Medium for inventory and bounded provider work; use High only where the actual decision complexity warrants it;
- prefer one capable primary worker;
- delegate only independent read-only inventory/evaluation/review work where parallelism has clear net value;
- use GPT-5.6 Sol as a separate matched behavior/review population, not as a substitute runtime attestation for Astra.

These are execution recommendations, not repository authority and not permanent model hardcodes.

## 10. Non-goals

- no weakening of branch protection, required checks, Merge Queue, authentication, secrets, production or destructive-operation boundaries;
- no deletion of unique domain knowledge to meet a size target;
- no new universal registry, manifest or per-task bureaucracy;
- no generic Oteryn skill;
- no automatic high/max effort requirement;
- no mass rewrite of historical evidence;
- no product/runtime mutation under this governance programme;
- no claims of token or financial savings without actual telemetry.

## 11. Terminal conditions

Issue #166 may close only when:

1. all four permanent repositories have a current instruction-load/disposition assessment;
2. every justified active cleanup is either integrated with protected-main readback or explicitly deferred to a named live owner/constraint;
3. retained `ALWAYS` rules have concrete justification;
4. historical/current prompt discovery is unambiguous;
5. deterministic enforcement is not weakened;
6. matched Sol/Astra evidence records correctness, false blocking and unnecessary-work behavior at the level actually observable;
7. no unresolved safety-critical regression remains;
8. final evidence clearly separates source size, delivered context, observed behavior and unavailable telemetry.

A smaller repository is not the terminal condition. A less constrained agent that still reliably respects real boundaries is.