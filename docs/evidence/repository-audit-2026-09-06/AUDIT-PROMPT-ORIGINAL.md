# GPT-6 ASTRA — COMPLETE REPOSITORY AUDIT

Perform a comprehensive, evidence-backed, read-only audit of the repository currently available to you.

Your objective is to determine the actual state, quality, architecture, correctness, maintainability, operational readiness, verification quality, governance quality, and instruction quality of this repository.

This is an audit task.

Do not implement fixes, modify repository files, create commits, push branches, open or modify pull requests or issues, change repository settings, weaken protections, change CI, or make external mutations.

Temporary files or build artifacts produced naturally by safe repository-native inspection or verification are acceptable, but do not overwrite user work and leave all tracked files unchanged.

---

# 1. OUTCOME

Produce a professional repository audit that is sufficiently complete that another senior engineer could use it to understand:

- what this repository is intended to do;
- what it actually does;
- how it is architected;
- whether the implementation matches the intended architecture and product goals;
- what is healthy;
- what is broken;
- what is incomplete;
- what is unnecessarily complicated;
- what is duplicated;
- what is obsolete;
- what creates operational, maintenance, security, performance, CI, testing, build, governance, or agent-context cost;
- what should be changed;
- in what order it should be changed;
- what was actually verified;
- what could not be verified.

Do not optimize for producing a quick answer.

Do not stop after finding several important problems.

Do not stop after an architecture overview.

Do not stop after reviewing only the most obvious directories.

Do not treat a representative sample as complete repository coverage unless the corresponding material is genuinely repetitive, generated, vendored, binary, or otherwise unsuitable for individual semantic review.

Persist until the completion criteria defined below are satisfied.

---

# 2. AUTONOMY AND FOLLOW-THROUGH

Infer routine details from the repository, its current state, its documentation, and available tools.

Bias toward inspection and completion.

Do not ask the user whether you should continue.

Do not stop at a plan.

Do not stop at a partial or "good enough" audit to save time, tokens, or effort.

Before asking any clarifying question, complete all useful work that is already possible without the answer.

Ask a question only when missing information genuinely prevents a material part of the audit from being evaluated.

If something cannot be accessed, do not guess.

Record it as `UNVERIFIED`, explain exactly why, and continue auditing everything else.

---

# 3. READ-ONLY BOUNDARY

This audit is read-only.

Allowed activities include, where available and safe:

- reading repository files;
- inspecting Git history and metadata;
- inspecting current branches and commits;
- inspecting repository instructions;
- inspecting GitHub state;
- inspecting workflows, rulesets, branch protections, Merge Queue and required checks;
- inspecting Issues and Pull Requests where relevant;
- running repository-native static analysis;
- running repository-native validation;
- running appropriate tests;
- running appropriate builds;
- inspecting dependency metadata;
- using read-only GitHub/API/CLI operations;
- using read-only external documentation where needed to validate current technology behavior.

Do not perform remote writes.

Do not change repository configuration.

Do not modify code to make a test or build pass.

Do not weaken a check because it fails.

Do not delete or overwrite existing user files or untracked work.

Before finishing, verify that the tracked working tree has not been changed by the audit.

---

# 4. ESTABLISH CURRENT AUTHORITY

Determine the repository identity and current state rather than assuming it.

Establish, when accessible:

- repository root;
- remote repository;
- current branch;
- current HEAD SHA;
- default/protected branch;
- current default-branch SHA;
- working-tree status;
- relevant recent history;
- repository type and primary languages;
- main applications, libraries, services, packages, tools, or deployable artifacts.

Discover all instruction sources that can influence the agent, including where applicable:

- `AGENTS.md`;
- `AGENTS.override.md`;
- nested agent instructions;
- skills and `SKILL.md`;
- skill descriptions;
- hooks;
- agent definitions;
- prompt files;
- reusable workflows;
- automation instructions;
- repository-level AI instructions;
- tool or permission configuration;
- relevant Markdown governance or execution documents.

Map their scope and precedence.

The explicit request to perform this read-only audit is the task authority.

If a repository instruction, skill, hook, or other lower-level instruction causes you to:

- stop the audit;
- request unnecessary approval;
- skip authorized read-only inspection;
- leave work incomplete;
- perform unrelated work;
- or contradict another applicable instruction,

identify the exact file and instruction and include that conflict in the instruction-debt findings.

Do not silently allow an accidental repository instruction to reduce audit coverage.

---

# 5. LIVE STATE

When GitHub or the repository host is accessible, inspect current live state where it materially affects the repository.

Relevant surfaces include, when applicable:

- default/protected branch;
- branch protections;
- repository rulesets;
- required status checks;
- Merge Queue;
- GitHub Actions or equivalent CI;
- reusable workflows;
- workflow permissions;
- environments;
- deployment protections;
- release configuration;
- security scanning;
- dependency scanning;
- automated update configuration;
- CODEOWNERS;
- open Pull Requests relevant to current architecture or blocked work;
- important open Issues;
- current CI failures;
- recent repeated failures or flakes;
- release state.

Historical Issues, Pull Requests, audit reports, prompts, and design documents are evidence.

They are not automatically current authority.

Prefer current code, current configuration, current protected/default branch state, and current live repository settings.

If live repository state cannot be accessed, explicitly mark those surfaces `UNVERIFIED`.

---

# 6. COMPLETE REPOSITORY INVENTORY

Before considering the audit complete, create an inventory of the entire version-controlled repository.

Account for every tracked path.

Classify files or groups into meaningful categories such as:

- production/runtime code;
- frontend/client code;
- backend/server code;
- libraries;
- tests;
- fixtures;
- build configuration;
- CI configuration;
- deployment/infrastructure;
- scripts/tooling;
- dependency manifests and lock files;
- documentation;
- prompts;
- agent instructions;
- skills;
- generated code;
- vendored code;
- static assets;
- binaries/data;
- examples;
- migration files;
- legacy/deprecated material.

Every tracked file must ultimately have one of these coverage dispositions:

`DIRECT`
: its relevant content was directly inspected.

`GROUPED`
: it belongs to a repetitive/generated/vendored/data class that was evaluated as a group using an explicitly described method.

`N/A`
: it has no meaningful semantic audit requirement, with a reason.

`UNVERIFIED`
: it could not be inspected, with a precise reason.

Do not claim direct review of a file that was not actually inspected.

Do not read generated/vendor/data files line-by-line merely to inflate coverage.

Use an efficient group-level strategy where that produces equivalent audit value.

At the end, reconcile the repository inventory against the audit coverage.

---

# 7. AUDIT DOMAINS

Every domain below must receive an explicit final status:

`AUDITED`
`N/A`
or
`UNVERIFIED`

Do not silently omit a domain.

## A. Purpose and product intent

Determine:

- repository purpose;
- intended users or consumers;
- major product goals;
- documented requirements;
- current implementation scope;
- unfinished or abandoned scope;
- whether code, tests and documentation agree about what the repository is supposed to provide;
- whether the repository still has a coherent reason to exist independently.

Identify contradictions between stated goals and actual implementation.

---

## B. System architecture

Reconstruct the actual architecture from code and configuration.

Evaluate:

- major components;
- modules;
- layers;
- packages;
- services;
- client/server boundaries;
- runtime boundaries;
- dependency directions;
- control flow;
- data flow;
- integration points;
- ownership boundaries;
- public/private interfaces;
- architectural invariants;
- coupling;
- cohesion;
- cycles;
- hidden dependencies;
- boundary violations;
- inappropriate abstractions;
- missing abstractions;
- unnecessary indirection;
- unnecessary services or layers;
- architecture that exists only because of historical constraints.

Do not merely describe the architecture.

Evaluate whether it is appropriate for the repository's real requirements.

---

## C. Implementation quality

Inspect implementation patterns across the repository.

Evaluate:

- correctness;
- maintainability;
- readability;
- consistency;
- duplication;
- unnecessary complexity;
- oversized modules;
- fragmented logic;
- inappropriate generic abstractions;
- hidden state;
- side effects;
- error handling;
- resource ownership;
- concurrency behavior;
- lifecycle management;
- data validation;
- edge cases;
- failure handling;
- TODO/FIXME/HACK debt;
- stale compatibility layers;
- deprecated paths;
- dead code;
- unreachable code;
- duplicated implementations;
- abandoned experimental code.

Distinguish stylistic preference from material engineering problems.

---

## D. Interfaces and contracts

Audit applicable:

- APIs;
- RPC;
- protocols;
- schemas;
- DTOs;
- serialization;
- command interfaces;
- library APIs;
- configuration interfaces;
- external integrations.

Evaluate:

- contract correctness;
- validation;
- compatibility;
- versioning;
- error semantics;
- undocumented behavior;
- duplicated schemas;
- weakly enforced invariants;
- accidental public surface;
- breaking-change risks.

---

## E. Data and persistence

Where applicable, inspect:

- database access;
- schemas;
- migrations;
- storage abstractions;
- caching;
- files;
- state management;
- transactions;
- consistency assumptions;
- backup/recovery expectations;
- migration rollback;
- retention;
- corruption handling.

Mark this domain `N/A` only when genuinely irrelevant.

---

## F. Dependencies and supply chain

Audit:

- dependency manifests;
- lock files;
- version constraints;
- duplicated dependencies;
- obsolete dependencies;
- unnecessary dependencies;
- dependency ownership;
- update strategy;
- package sources;
- build-time dependencies;
- runtime dependencies;
- dependency security configuration;
- dependency automation;
- reproducibility;
- relevant licensing concerns.

Do not claim that a dependency is vulnerable solely because it is old.

Use current authoritative vulnerability data when making vulnerability claims.

---

## G. Security and privacy

Evaluate relevant attack surfaces, including:

- authentication;
- authorization;
- privilege boundaries;
- input validation;
- injection;
- secret handling;
- credential exposure;
- unsafe logging;
- file/path handling;
- network exposure;
- deserialization;
- unsafe subprocess execution;
- workflow injection;
- excessive CI permissions;
- third-party actions;
- dependency risk;
- data exposure;
- trust boundaries;
- insecure defaults;
- privacy-sensitive data handling.

Separate verified vulnerabilities from possible risks requiring further validation.

---

## H. Reliability and resilience

Evaluate:

- failure modes;
- retries;
- timeouts;
- cancellation;
- cleanup;
- partial failure;
- idempotency;
- race conditions;
- concurrency;
- restart behavior;
- state recovery;
- graceful degradation;
- external dependency failure;
- network failure;
- crash behavior;
- resource exhaustion;
- operational recovery.

---

## I. Performance, scalability and resource cost

Evaluate actual evidence for:

- CPU;
- memory;
- disk;
- network;
- I/O;
- startup;
- build time;
- test time;
- CI duration;
- repeated work;
- caching;
- algorithmic hotspots;
- avoidable serialization;
- redundant network calls;
- unnecessary full rebuilds;
- scaling limits.

Do not invent performance problems from code appearance alone.

Clearly distinguish measured evidence from architectural inference.

---

## J. Test architecture

Inventory and evaluate the actual test system.

Include applicable:

- unit tests;
- component tests;
- integration tests;
- contract tests;
- E2E tests;
- smoke tests;
- regression tests;
- fixtures;
- mocks;
- test data;
- test infrastructure.

Evaluate:

- whether important behavior is tested;
- whether tests test meaningful behavior rather than implementation details;
- missing negative and failure cases;
- duplicated tests;
- flaky tests;
- overly expensive tests;
- incorrectly broad tests;
- false confidence;
- obsolete tests;
- disabled tests;
- skipped tests;
- tests whose data or environment requirements make them impractical;
- correspondence between risk and test level.

Do not equate test count or coverage percentage with test quality.

---

## K. Build system

Audit:

- build entry points;
- build graph;
- configuration;
- generated outputs;
- reproducibility;
- caching;
- incremental behavior;
- platform handling;
- artifact creation;
- packaging;
- unnecessary rebuilds;
- duplicate build paths;
- stale build scripts;
- local vs CI discrepancies.

When practical, run the smallest meaningful repository-native build verification required to validate important findings.

Record the exact outcome.

---

## L. CI and verification architecture

Inspect every active workflow and reusable workflow relevant to this repository.

Evaluate:

- triggers;
- pull request behavior;
- push behavior;
- merge-group behavior;
- path filters;
- matrices;
- dependencies between jobs;
- permissions;
- concurrency;
- cancellation;
- caching;
- artifact passing;
- duplicated work;
- self-triggering behavior;
- possible loops;
- unnecessary full-suite execution;
- missing verification;
- inappropriate blocking checks;
- flaky blocking checks;
- GitHub-hosted vs self-hosted routing;
- expensive jobs;
- environment coupling;
- test selection;
- impact-based routing if present;
- failure semantics;
- fail-open/fail-closed behavior;
- required-check compatibility;
- Merge Queue compatibility.

Determine whether CI verifies risk efficiently or merely executes many jobs.

---

## M. Release, deployment and rollback

Where applicable, inspect:

- release process;
- versioning;
- artifact provenance;
- packaging;
- deployment workflow;
- environments;
- promotion;
- rollback;
- migration ordering;
- release validation;
- release automation;
- deployment safety;
- recovery procedures.

---

## N. Configuration and infrastructure

Where applicable, inspect:

- environment configuration;
- secrets references;
- containers;
- Docker;
- Compose;
- Kubernetes;
- Terraform;
- cloud configuration;
- runtime configuration;
- platform-specific configuration;
- development environments;
- production assumptions.

Identify configuration duplication and environment drift.

---

## O. Observability and operations

Where applicable, evaluate:

- logging;
- metrics;
- tracing;
- health checks;
- diagnostics;
- failure visibility;
- actionable errors;
- operational dashboards/configuration;
- alerts;
- auditability;
- debugging support.

---

## P. Documentation and knowledge architecture

Inspect relevant Markdown and documentation, including architectural and operational material.

Evaluate:

- correctness against current implementation;
- obsolete documentation;
- contradictory documentation;
- duplication;
- discoverability;
- excessive documentation;
- missing documentation;
- historical documents masquerading as current authority;
- source-of-truth ambiguity;
- documentation that creates agent context cost without delivering useful knowledge.

Do not assume documentation is correct because it is detailed.

Validate important claims against implementation.

---

## Q. Agent instructions, prompts, skills and instruction debt

Perform a dedicated instruction-debt audit.

Inspect applicable:

- root `AGENTS.md`;
- nested `AGENTS.md`;
- `AGENTS.override.md`;
- prompt registries;
- individual prompts;
- agent definitions;
- aliases;
- skills;
- skill descriptions;
- `SKILL.md`;
- hooks;
- completion rules;
- permission instructions;
- model-specific instructions;
- tool-specific instructions;
- historical compatibility workarounds.

Identify:

- duplicated instructions;
- conflicting authority;
- unnecessarily repeated context;
- stale requirements;
- broad skill triggers;
- accidental activation;
- ambiguous scope;
- unclear precedence;
- unclear mutation authority;
- premature stopping conditions;
- unnecessary approval requirements;
- excessive verification requirements;
- instructions that force irrelevant work;
- instructions that cause excessive CI/tool usage;
- historical model-specific workarounds that current models no longer require;
- content that should be normal documentation rather than always-loaded agent context;
- content that should be mechanically enforced rather than repeatedly explained to agents.

Preserve useful project knowledge, intentional governance, safety constraints, and genuine architecture rules.

Do not recommend deleting instructions merely because they are long.

Evaluate whether each instruction earns the context and behavioral complexity it introduces.

---

## R. Developer experience and repository ergonomics

Evaluate:

- project setup;
- local development;
- common commands;
- scripts;
- task runners;
- environment setup;
- reproducibility;
- debugging;
- contribution workflow;
- discoverability;
- unnecessary manual steps;
- repeated setup cost;
- agent usability.

---

## S. Repository governance

Where live repository access permits, audit:

- branch protections;
- rulesets;
- Merge Queue;
- required checks;
- CODEOWNERS;
- review requirements;
- merge methods;
- status-check naming stability;
- workflow permissions;
- environment protections;
- dependency/security automation;
- repository settings that materially affect delivery.

Evaluate whether governance and CI agree with each other.

Identify impossible, redundant, circular, stale, or disproportionately expensive gates.

---

## T. Current work and repository drift

Inspect relevant open work where accessible.

Determine whether:

- current Issues still describe real problems;
- open Pull Requests conflict with current architecture;
- completed work has left stale tracking artifacts;
- current documentation references already-removed systems;
- old branches/configuration remain authoritative accidentally;
- current code and governance have drifted apart.

Do not turn the audit into an exhaustive historical review unless history is necessary to explain current state.

---

## U. Compatibility and portability

Where relevant, inspect:

- OS assumptions;
- architecture assumptions;
- browser/runtime versions;
- compiler/runtime support;
- API compatibility;
- backward compatibility;
- migration compatibility;
- platform-specific behavior.

---

## V. User-facing quality

For repositories with a user-facing product, evaluate applicable:

- UX consistency;
- accessibility;
- error states;
- loading states;
- resilience;
- navigation;
- configuration experience;
- user-visible failure handling.

For non-user-facing repositories, mark this `N/A`.

---

## W. Simplification opportunities

Across all previous domains, explicitly identify opportunities to reduce:

- code volume;
- number of abstractions;
- duplicate systems;
- duplicate workflows;
- duplicate documentation;
- duplicated prompts;
- duplicated verification;
- unnecessary infrastructure;
- CI time;
- compute cost;
- agent context/token cost;
- maintenance burden;
- operational complexity.

Simplification must preserve required functionality, safety and governance.

Prefer removing accidental complexity over merely reorganizing it.

---

# 8. VERIFICATION

Use repository-native checks when they materially improve confidence.

Examples may include:

- existing test commands;
- existing build commands;
- linters;
- type checking;
- static analysis;
- dependency validation;
- configuration validation;
- repository-specific verification scripts.

Calibrate verification to the question being tested.

Do not repeatedly run large suites without a reason.

Do not create new tests during this read-only audit.

Do not run expensive tests merely because they exist.

For every executed verification, record:

- command or mechanism;
- scope;
- result;
- relevant failures;
- whether the failure appears product-related, infrastructure-related, configuration-related, or unknown.

A passing test proves only what that test actually covers.

A failing test is evidence to investigate, not automatic proof that production code is wrong.

---

# 9. SUBAGENT POLICY

If subagent/collaboration tools are available, use them when independent audit lanes can be parallelized and this improves coverage or reduces completion time.

Good independent lanes include, depending on repository size:

- architecture and implementation;
- tests and verification;
- CI/build/release;
- security and dependencies;
- documentation and product intent;
- prompts/AGENTS/skills/instruction debt;
- GitHub governance and current live state.

Avoid two agents auditing the same surface without a specific cross-check reason.

Give each delegated lane explicit boundaries.

Require every subagent to return:

- inspected scope;
- concrete findings;
- evidence;
- unresolved questions;
- files/surfaces not inspected.

When effort selection for subagents is available, prefer low/light effort for bounded inventory and inspection tasks and increase effort only when the task genuinely requires deeper reasoning.

The lead agent remains responsible for:

- integrating results;
- detecting contradictions;
- verifying material claims;
- identifying gaps between lanes;
- completing the final coverage reconciliation.

Do not treat a subagent's statement as verified evidence without enough supporting detail to evaluate it.

If subagents are unavailable, perform the same lanes sequentially.

---

# 10. EVIDENCE STANDARD

Every material finding should distinguish:

`FACT`
: directly verified.

`INFERENCE`
: conclusion derived from verified evidence.

`ASSUMPTION`
: temporarily accepted but not verified.

`RECOMMENDATION`
: proposed change.

`UNKNOWN`
: required information is missing.

Reference precise evidence whenever possible:

- file path;
- relevant line or symbol;
- configuration entry;
- command result;
- test result;
- workflow/job;
- commit;
- PR;
- Issue;
- live repository setting;
- authoritative external documentation.

Do not invent evidence.

Do not convert absence of evidence into evidence of absence.

For uncertain findings, state the uncertainty.

---

# 11. FINDING SEVERITY

Classify actionable findings consistently:

`P0 — CRITICAL`
Immediate risk of serious security, data-loss, production, release, or governance failure.

`P1 — HIGH`
Material correctness, architecture, reliability, CI, security, or delivery problem that should be addressed soon.

`P2 — MEDIUM`
Meaningful maintainability, performance, testing, complexity, tooling, documentation, or efficiency problem.

`P3 — LOW`
Minor debt, cleanup, ergonomics, consistency, or optimization opportunity.

Do not inflate severity.

A large number of findings does not imply a poor repository.

---

# 12. CROSS-CHECK PASS

After the main audit, perform a separate reconciliation pass.

Specifically look for:

- directories not covered by any audit lane;
- tracked files not assigned a coverage disposition;
- build systems not evaluated;
- test suites not evaluated;
- workflows not evaluated;
- undocumented executables;
- duplicated configuration;
- hidden runtime entry points;
- nested instruction files;
- ignored architecture boundaries;
- generated/vendor code incorrectly treated as authored code;
- current GitHub state that contradicts local repository assumptions;
- findings supported only by inference but presented as facts;
- recommendations that contradict repository constraints;
- areas marked healthy without meaningful evidence.

The purpose of this pass is to find what the first audit missed.

Do not finish merely because the first-pass findings are substantial.

---

# 13. COMPLETION CONTRACT

The audit is complete only when all of the following are true:

1. The repository identity and audited revision are known, or explicitly `UNVERIFIED`.
2. The tracked repository inventory has been reconciled.
3. Every tracked path has a coverage disposition.
4. Every audit domain A–W has status:
   - `AUDITED`,
   - `N/A`,
   - or `UNVERIFIED`.
5. All applicable agent/instruction sources discovered during the audit have been included in the instruction-debt review.
6. All applicable CI/build/test systems discovered during the audit have been evaluated.
7. All accessible live governance surfaces material to the repository have been evaluated.
8. Material findings contain evidence.
9. The cross-check pass has been completed.
10. Remaining inaccessible surfaces are explicitly listed.

If these conditions are not satisfied and additional inspection is possible, continue working.

Do not produce a final completion claim while known audit work remains.

---

# 14. REQUIRED FINAL REPORT

Produce the final report in this structure.

## 1. Audit status

Exactly one of:

`COMPLETE_WITHIN_ACCESSIBLE_SCOPE`

or

`INCOMPLETE`

Never state "100% complete" when any material surface remains `UNVERIFIED`.

---

## 2. Repository snapshot

Include:

- repository;
- audited branch;
- audited SHA;
- live default branch/SHA if available;
- working-tree state;
- repository type;
- primary technologies;
- audit limitations.

---

## 3. Executive assessment

Give a concise professional assessment of:

- overall repository health;
- architecture;
- implementation;
- verification;
- CI/build/release;
- security/reliability;
- governance;
- documentation;
- agent/instruction quality;
- biggest current risks;
- biggest simplification opportunities.

---

## 4. Architecture assessment

Describe and evaluate the actual architecture.

Include major components and relationships.

Highlight architectural strengths, weaknesses, accidental complexity and drift.

---

## 5. Coverage ledger

Provide all domains A–W with:

- status;
- evidence summary;
- important limitations.

Also provide tracked-file coverage totals:

- total tracked files;
- `DIRECT`;
- `GROUPED`;
- `N/A`;
- `UNVERIFIED`.

Explain the `GROUPED` categories.

---

## 6. Findings

Provide findings ordered by severity.

For each finding include:

- ID;
- severity;
- domain;
- classification (`FACT`, `INFERENCE`, etc.);
- description;
- evidence;
- impact;
- recommended direction.

Avoid duplicate findings describing the same root cause.

---

## 7. Tests, CI and build assessment

Summarize:

- verification architecture;
- what was actually executed;
- failures;
- missing coverage;
- unnecessary verification;
- CI cost/complexity problems;
- Merge Queue/required-check compatibility where applicable;
- recommended verification architecture.

---

## 8. Security, reliability and performance assessment

Summarize verified and inferred risks separately.

---

## 9. Instruction-debt assessment

Summarize:

- instruction hierarchy;
- conflicts;
- duplicated rules;
- unnecessary always-loaded context;
- stale model-specific workarounds;
- prompt/skill overlap;
- premature stop/approval rules;
- recommendations for a simpler instruction architecture.

---

## 10. Documentation and repository knowledge assessment

Identify current sources of truth and important drift.

---

## 11. Governance assessment

Cover current repository protections and merge/release governance when accessible.

---

## 12. Simplification opportunities

Rank concrete opportunities to reduce:

- complexity;
- code;
- infrastructure;
- CI work;
- test work;
- documentation duplication;
- prompt/instruction context;
- maintenance cost;
- compute/token cost.

---

## 13. Remediation roadmap

Organize recommendations into:

### Immediate

Critical or blocking work.

### Near-term

High-value structural corrections.

### Medium-term

Optimization, simplification and debt removal.

### Optional

Useful but nonessential improvements.

For each material recommendation state relevant dependencies and sequencing.

Do not propose a rewrite when incremental simplification can achieve the same result.

---

## 14. Unverified and inaccessible surfaces

List exactly what could not be verified and why.

Explain how each gap affects confidence in the report.

If empty, say explicitly that no known material audit surface remains inaccessible.

---

## 15. Final coverage reconciliation

Answer explicitly:

- Are all tracked paths accounted for?
- Are all audit domains accounted for?
- Are all discovered instruction sources accounted for?
- Are all discovered active CI workflows accounted for?
- Are all discovered build/test systems accounted for?
- Are all accessible governance surfaces accounted for?
- Did the cross-check pass identify any remaining unexplored surface?
- Is further audit work currently possible with the available access?

Only after answering these questions may you declare the audit complete.

---

# 15. QUALITY BAR

The value of this task is not the length of the report.

The value is:

- coverage;
- correctness;
- evidence;
- detection of blind spots;
- architecture understanding;
- prioritization;
- actionable simplification;
- truthful reporting of uncertainty.

Do not manufacture findings to make the audit look comprehensive.

Do not call something healthy merely because no problem was found during a shallow inspection.

Do not call something broken without evidence.

A repository with no finding in a domain is acceptable if that conclusion is supported by meaningful inspection.

The final report should be concise relative to the amount of work performed, but the underlying audit must be comprehensive.

Continue until the completion contract is satisfied or a concrete external access limitation makes further progress impossible.