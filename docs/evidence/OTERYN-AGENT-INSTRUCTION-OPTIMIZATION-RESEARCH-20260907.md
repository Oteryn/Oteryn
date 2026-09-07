# Oteryn — agent instruction optimization research

Date: 2026-09-07
Class: **AUDIT_EVIDENCE / RECOMMENDATION**
Status: **NON-NORMATIVE**
Related: `Oteryn/Oteryn#140`, Draft PR `#145`, Draft PR `#151`

This document records a research synthesis for simplifying Oteryn agent instructions, prompts, skills and governance across META, Game, Platform and Atlas. It is evidence and design guidance only. It does not adopt a new policy, change provider repositories, alter permissions, change CI, modify branch protection, enable a model, or authorize production operations.

## 1. Decision summary

The target should be the **smallest persistent instruction surface that prevents real mistakes or repeated waste**.

Persistent instructions should contain only rules that are both:

1. broadly applicable to the scope in which they are loaded; and
2. valuable enough that omitting them can materially change correctness, authority, safety or recurring execution cost.

Everything else should be one of:

- task-routed documentation loaded only when relevant;
- a focused skill loaded only when selected;
- a task-specific prompt delta;
- deterministic CI/configuration rather than natural-language policy;
- historical evidence that is not an active instruction surface.

The optimization objective is not minimum Markdown bytes in Git. It is minimum **cost of a correctly completed task**, including instruction context, repository traversal, tool calls, tests, retries, review, coordination and owner interaction.

## 2. Source hierarchy for this research

### 2.1 Primary: official OpenAI documentation

1. **GPT-6 Astra model guidance**
   <https://developers.openai.com/api/docs/guides/latest-model>
   Material observation: Astra has stronger instruction following and can be more sensitive to instructions in skills and files such as `AGENTS.md`; OpenAI explicitly recommends auditing accessible skills and instruction files for guidance that can influence behavior.

2. **Codex / ChatGPT `AGENTS.md` configuration**
   <https://learn.chatgpt.com/docs/agent-configuration/agents-md>
   Material observations:
   - project instructions are discovered from repository root down to the current working directory;
   - in each directory at most one instruction file is selected, with `AGENTS.override.md` preferred over `AGENTS.md`;
   - files are concatenated root-to-current-directory;
   - closer instructions appear later and therefore override broader guidance;
   - empty files are skipped;
   - combined project instruction content stops at `project_doc_max_bytes`, which is 32 KiB by default;
   - nested instructions should be placed close to specialized work;
   - review rules should be concise and formatting/lint checks should normally be left to CI.

3. **OpenAI skills documentation**
   <https://learn.chatgpt.com/docs/build-skills>
   Material observations:
   - skills use progressive disclosure: name/description are initially visible and full `SKILL.md` is loaded after selection;
   - `SKILL.md` requires `name` and `description`;
   - descriptions should be concise with clear scope and trigger boundaries;
   - a skill should be focused on one job;
   - `agents/openai.yaml` can set `policy.allow_implicit_invocation: false`, leaving explicit invocation available;
   - repository skills may be scoped to the root or a narrower working directory.

4. **Reasoning-model prompting best practices**
   <https://developers.openai.com/api/docs/guides/reasoning-best-practices>
   Material observations:
   - keep prompts straightforward and direct;
   - do not routinely instruct reasoning models to expose or perform chain-of-thought step-by-step prompting;
   - use delimiters only when they improve separation of distinct input parts;
   - start zero-shot and add examples only when needed;
   - state specific constraints and a concrete success target.

5. **OpenAI harness engineering**
   <https://openai.com/index/harness-engineering/>
   Material observation: OpenAI describes an internal architecture where a short `AGENTS.md` is a map/table of contents and deeper knowledge lives in structured documentation. The roughly 100-line example is an implementation example, not a universal size requirement.

### 2.2 Secondary: external research

1. **Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?**
   <https://arxiv.org/abs/2602.11988>
   Reported result: in that experimental setting repository context files tended to reduce task success and increased inference cost by more than 20%; the authors attribute part of the effect to unnecessary requirements causing broader exploration and recommend minimal human-written requirements.

2. **On the Impact of AGENTS.md Files on the Efficiency of AI Coding Agents**
   <https://arxiv.org/abs/2601.20404>
   Reported result: in 124 PRs across 10 repositories, the presence of `AGENTS.md` was associated with lower median runtime and lower output-token consumption while completion behavior remained comparable.

3. **Do Context Files Help Coding Agents? A Two-Agent Ablation Study on Real Repositories**
   <https://arxiv.org/abs/2607.27250>
   Reported result: the controlled study found no measurable correctness improvement from context strategy in its tested tasks, emphasizing that context files do not compensate for implementation-skill failures.

These studies are not directly comparable and do not establish a universal optimum. They support measuring Oteryn itself rather than assuming that either “more context” or “less context” always wins.

### 2.3 Tertiary: community observations

Representative Reddit discussions reviewed:

- <https://www.reddit.com/r/codex/comments/1w1j1qi/could_an_agentsmd_file_actually_reduce_codex/>
- <https://www.reddit.com/r/codex/comments/1ux5viv/56_started_using_more_quota_for_me_so_i/>
- <https://www.reddit.com/r/codex/comments/1ujw3ex/screw_token_maxxing_how_do_i_actually_limit_token/>

Recurring community themes include targeted searches, avoiding repeated reads, proportional validation, keeping `AGENTS.md` as a router, and moving one-off constraints into the task prompt. These are anecdotal observations, not normative evidence and not reliable cost benchmarks.

## 3. What should be persistent

Use four classes.

### A. ALWAYS — small persistent kernel

A rule belongs in the always-loaded kernel only if omitting it can repeatedly cause a material error across most tasks in that scope.

Examples for Oteryn:

- repository/product ownership boundary;
- explicit non-expansion of authority from tool availability;
- preservation of unrelated work;
- source-of-truth rule for current repository lifecycle facts;
- a small number of durable product invariants;
- required integration safety that is not already guaranteed by the platform;
- one rule directing the agent to load nearer instructions for specialized paths.

Avoid examples, historical explanations and compatibility prose in this layer unless they are necessary to interpret the rule correctly.

### B. ROUTED — load only when a trigger applies

Examples:

- database migration safety;
- deployment/rollback procedure;
- Atlas FullWorld/specialist verification placement;
- Game protocol/login compatibility;
- Remote Desktop host exception procedure;
- recovery/restore procedure;
- prompt-authoring standard;
- governance-authoring rules;
- visual acceptance;
- security-specific threat-model procedure.

A normal product-code task should not preload these documents merely because they exist.

### C. TASK_ONLY — put in the current prompt/Issue

Examples:

- one-off output format;
- temporary writable path allocation;
- exact investigation question;
- an exceptional test requested for this change;
- a temporary maintenance objective;
- a bounded comparison requested by the owner;
- a task-specific model or effort preference when the execution surface actually supports it.

A one-time requirement should not automatically become permanent policy.

### D. DETERMINISTIC — enforce in code/config, not repeated prose

Examples:

- required GitHub status names;
- path allowlists;
- branch/ruleset constraints;
- schema validation;
- formatting/lint rules;
- exact machine-readable contract shape;
- immutable digest/revision matching;
- test selection logic.

Human instructions may explain the intent briefly, but they should not reproduce the machine implementation line by line.

## 4. Recommended META/provider architecture

### 4.1 META owns organization-wide semantics

Recommended canonical human surfaces in `Oteryn/Oteryn`:

```text
docs/agents/policy/ORGANIZATION_AGENT_POLICY.md
docs/agents/policy/PROMPTING_STANDARD.md
```

Keep a separate prompt-evaluation document only if it contains a genuinely distinct evaluation method or has a real machine consumer. Otherwise consolidate the useful evaluation rules into the prompting standard or a task-routed evaluation guide.

META also owns organization-level machine policy that is genuinely shared, such as routing or bounded-lifecycle contracts, plus their deterministic validators.

META does **not** own provider runtime architecture, provider schemas or provider-specific build/test/deployment procedures.

### 4.2 Provider roots stay local and small

Each product repository should retain a short root `AGENTS.md` containing only:

1. repository role and ownership boundary;
2. minimal local authority/safety kernel needed in every task;
3. durable product invariants that materially affect ordinary work;
4. instruction-routing pointers for task classes;
5. the mechanism/version by which the provider adopts organization policy.

Do not copy organization-wide GitHub, Remote Desktop, generic concurrency, AI review, continuation and merge prose into every provider root unless the runtime cannot otherwise receive a safety-critical minimum.

### 4.3 Important limitation: a META binding is not automatic prompt injection

Official Codex instruction discovery walks the local project tree. A file such as `META_AGENT_POLICY_BINDING.json` can establish version/authority identity for tooling, but a link or commit coordinate in another repository does not by itself prove that the remote policy text is loaded into a worker prompt.

Therefore Oteryn must distinguish:

- **policy ownership** — where the canonical semantics are edited;
- **policy delivery** — how the relevant worker actually receives the necessary rules.

Recommended approach:

- keep canonical full organization semantics in META;
- keep only a tiny bootstrap safety kernel in provider root instructions when cross-repository automatic inheritance is unavailable;
- use the immutable META binding for versioning and governance validation;
- load the detailed central policy only for governance/cross-repository tasks or through a runtime-level/global mechanism whose instruction loading has been verified;
- do not force every product task to perform a network fetch of the entire META policy merely to claim centralization.

Small intentional duplication of a few safety-critical invariants is preferable to a complex mandatory fetch chain if the duplicate is generated or tightly controlled and has a clear reason. Large independently maintained copies are not.

## 5. Target shape of `AGENTS.md`

`AGENTS.md` is ordinary Markdown. Oteryn should not invent mandatory metadata unless a real consumer requires it.

Recommended provider root shape:

```md
# <Product> agent instructions

## Scope
<What this repository owns and does not own.>

## Always
- <Only high-value rules that apply to nearly every task here.>
- <Durable product invariants.>

## Context routing
- If touching <domain>, read <local source>.
- If touching <domain>, read <local source>.
- Read nearer AGENTS.md / AGENTS.override.md when it governs the working path.

## Validation
Use the repository-selected checks applicable to the change. Heavy or specialist validation is required only when the changed behavior/risk requires it or repository enforcement selects it.
```

This is a design pattern, not a mandatory section schema.

### Size rule

Do not create a correctness gate such as “AGENTS.md must be exactly N lines”. OpenAI documents a **32 KiB default combined project instruction cap**, not a recommended size.

As an Oteryn engineering target, root instructions should be small enough to scan immediately and should normally function as a map plus high-value invariants. If they grow because many task-specific procedures were added, route those procedures out rather than raising the context budget by default.

## 6. Nested instructions

Use nested `AGENTS.md` or `AGENTS.override.md` only when a directory has materially different instructions.

Good use:

- payment code with stronger transaction/security requirements;
- a persistence subsystem with specific migration/concurrency constraints;
- a deployment directory with release-specific safety;
- a specialized test harness.

Bad use:

- repeating root GitHub workflow;
- restating organization review policy;
- reproducing the same branch rules in every module;
- adding an override only because a historical template expected one.

Remember that `AGENTS.override.md` is selected instead of `AGENTS.md` in the same directory; it should be used deliberately.

## 7. Skill design

Create a skill only for a repeatable specialized job whose procedural knowledge is useful beyond one prompt.

Minimum form:

```md
---
name: migration-review
description: Review a database migration for data-loss, locking and rollback risk when explicitly asked to audit a migration.
---

Inspect the migration and affected schema/contracts.
Check destructive changes, locking/concurrency risk and rollback/recovery evidence.
Return findings with exact evidence and unresolved unknowns.
Do not execute the migration.
```

For a skill that should be explicit-only in Codex, use:

```yaml
policy:
  allow_implicit_invocation: false
```

in `agents/openai.yaml`.

Do not create skills that merely wrap generic software-engineering advice or duplicate whole repository governance. Skill descriptions consume discovery budget even before the full skill body is loaded, so large unused skill collections are not free.

## 8. Prompt design

A normal execution prompt should be a **task-specific delta**, not a second operating manual.

Recommended minimal structure when each item is material:

```text
OBJECTIVE
<Observable result.>

SCOPE
<Writable/affected boundary and important exclusions.>

LIVE LOCATORS
<Issue/PR/branch identifiers needed to refresh current truth.>

TASK-SPECIFIC CONSTRAINTS
<Only constraints not already provided by applicable instructions/contracts.>

SUCCESS
<Observable acceptance and validation specific to this task.>
```

Omit empty sections.

Do not routinely add:

- “think step by step” or requests to expose chain of thought;
- generic expert-persona praise;
- repeated GitHub/branch rules already supplied by the repository;
- a full review policy;
- a full Remote Desktop policy;
- arbitrary phase/checkpoint ceremonies;
- examples when zero-shot instructions are already sufficient;
- model/effort metadata that no runtime consumer reads.

Add details only when they alter the correct outcome or execution boundary.

## 9. Validation economy

Persistent policy should encourage **proportional validation**, not minimum validation.

Recommended sequence:

1. targeted search/read to identify the relevant seam;
2. smallest coherent implementation or analysis;
3. cheap focused validation while iterating;
4. broader/component/integration validation when affected behavior requires it;
5. repository-required exact-candidate gate at integration;
6. specialist/heavy validation only when selected by the change/risk or explicit acceptance.

Do not rerun an unchanged heavy suite merely because narration/checkpoint text changed. Do not suppress required tests to save tokens.

Tool-output economy matters too: prefer targeted search and focused log excerpts while retaining full logs/artifacts outside the active context when they are needed for evidence.

## 10. What to remove from active Oteryn instruction surfaces

Candidates for removal or routing, after checking their real consumers:

- historical fixed-runtime compatibility prose;
- duplicate descriptions of the same GitHub preflight;
- duplicate Remote Desktop per-call prose in multiple provider files;
- duplicate AI-review routing;
- mandatory “parallel-first” language where one capable worker is proportionate;
- verbose capability-discovery examples that restate one general rule;
- duplicated task-status vocabularies when a machine schema already owns them;
- lifecycle/status mirrors that duplicate live Issue/PR state;
- generic instructions to read broad indexes before targeted search;
- mandatory full-document loading chains that exist only because another policy links to them;
- large historical prompt libraries treated as active merely because they remain in Git.

Removal must update or retire validators that require the old duplicated text. A prose cleanup that leaves those consumers in place is incomplete.

## 11. What must remain

Do not remove unique knowledge merely because it is long.

Retain and route as needed:

- Game protocol/world/session/persistence invariants;
- Atlas projection/provenance/publication and specialist-verification facts;
- Platform auth/data/payment/deployment invariants;
- recovery evidence and restore contracts;
- architecture decisions with current normative value;
- durable cross-repository contracts;
- genuine safety/authority boundaries;
- deterministic tests that protect real behavior.

The optimization target is **activation**, not deletion of useful knowledge.

## 12. Recommended migration sequence

1. **Freeze the design target.** Use Draft PR #145 and this evidence to decide the minimal central semantic kernel before provider rewrites.
2. **Remove instruction-consumer debt first or in the same provider PR.** A provider cannot become lean while CI still requires duplicated legacy prose.
3. **META:** reduce the central organization policy to shared semantics; keep specialist contracts routed.
4. **Platform:** collapse root/bootstrap overlap and remove validators that require retired compatibility wording.
5. **Game:** replace exact copied Remote Desktop/prompt sections with semantic/binding validation; retain unique Game invariants.
6. **Atlas:** keep maintenance enforcement intact while simplifying only paths currently allowed by the maintenance gate; separate maintenance-mode instructions from normal product verification semantics.
7. **Prompts:** reduce reusable prompts to task deltas; move one-off requirements to Issues/current prompts.
8. **Skills:** inventory trigger descriptions, remove broad/overlapping skills, set explicit-only invocation where automatic activation has no clear value.
9. **Measure:** compare representative tasks with the same model, effort, repository state and acceptance criteria.
10. **Delete historical active surfaces only after proving no live consumer requires them.** Git history can preserve provenance.

## 13. Measurement plan

Do not claim a percentage token/cost saving before measuring it.

Use a small representative set:

- localized code fix;
- domain-contract change;
- high-risk/security or control-plane change;
- continuation/resume task;
- documentation/governance-only change.

Measure at least:

- task success / acceptance;
- safety/authority violations;
- total input/output/reasoning usage when observable;
- tool-call count;
- files/bytes read;
- repeated reads/searches;
- test/CI invocations;
- unnecessary subagent activations;
- false blockers/approval pauses;
- wall-clock completion time;
- owner interventions.

Use ablation: remove one instruction group at a time when practical and repeat comparable cases. Do not optimize for token count alone if correctness or safety regresses.

## 14. Current Oteryn disposition

### FACT

- Draft PR #145 already proposes a central organization policy plus immutable provider binding architecture.
- Draft PR #151 is the current instruction-debt audit publication branch.
- Current Oteryn provider instruction surfaces contain duplicated global procedures and validators that depend on some duplicated/legacy text; these dependencies are documented in the associated audit evidence.

### INFERENCE

- A “one rule, one authority” design is useful only if policy delivery is also solved. A remote META file referenced from a provider is not automatically part of Codex project instruction discovery.
- The largest likely savings will come from reducing **activation and mandated work**, not from Markdown minification alone.

### UNKNOWN

- Exact instruction sources loaded by every ChatGPT Work/Codex execution surface in Oteryn.
- Actual Oteryn token/cost savings after simplification.
- Whether each current provider validator can be removed, consolidated or must be rewritten until its consumers are traced.
- Whether every external/community observation generalizes to Oteryn workloads.

## 15. Proposed design principle

> **Permanent instructions are earned.** Keep a rule always loaded only when it protects a recurring material invariant or prevents recurring waste. Route specialized knowledge to the tasks that need it, keep one-off requirements in the task, and let deterministic systems enforce deterministic rules.

This principle should be evaluated by Oteryn-specific task outcomes before becoming normative governance.
