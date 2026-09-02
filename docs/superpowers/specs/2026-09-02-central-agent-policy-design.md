# Central Agent Policy Design

Status: proposed design for `Oteryn/Oteryn#142`; non-authoritative until separately reviewed and merged to protected `main`.

## Problem

Oteryn currently stores organization-wide agent behavior in several places and then repeats parts of it in Game, Platform, Atlas and task prompts. The result is semantic drift, stale pinned assumptions, duplicated safety prose, larger prompts, avoidable precedence reasoning and a growing tendency to repair agent behavior by adding another local rule or another specialized prompt.

Repository instructions do not automatically inherit across repositories, so every provider needs a small local bootstrap. That limitation does **not** require each provider to own a copy of organization policy.

## Design objective

Create one organization agent-policy bundle owned by `Oteryn/Oteryn` (META). Provider repositories keep only a thin bootstrap plus domain-specific invariants. Task prompts and handoffs carry only the delta that is specific to one task.

The target rule is:

> **Global semantics live once in META. Providers bind to them; prompts do not restate them.**

## Non-goals

- no new orchestration service or second control plane;
- no weakening of branch protection, Merge Queue, aggregate gates, exact-head validation, security, production authorization or E2E;
- no implicit cross-repository write authority;
- no mass rewrite of historical evidence;
- no dynamic unreviewed policy inheritance from a moving META head;
- no single giant natural-language file that replaces every machine-readable policy module.

## Target architecture

### 1. META policy bundle

META owns these canonical human-facing surfaces:

- `docs/agents/policy/ORGANIZATION_AGENT_POLICY.md` — organization execution/authority contract;
- `docs/agents/policy/PROMPTING_STANDARD.md` — one outcome-first prompt construction standard;
- `docs/agents/policy/PROMPT_EVAL_STANDARD.md` — one behavioral/evaluation standard.

META may retain focused machine-readable modules such as execution routing, bounded lifecycle and continuation policy when closed enums/predicates are better represented in code/JSON. The human contract is the single semantic entry point and names those modules rather than copying them.

Organization-wide concerns owned only by META include:

- GitHub/live-state source of truth;
- authority and cross-repository boundaries;
- branch/worktree ownership and moving-main reconciliation;
- `single_agent` versus `parallel_when_beneficial` execution shape;
- capability discovery and execution-surface routing;
- Remote Desktop exception semantics;
- bounded retry/anti-loop and continuation semantics;
- AI-review routing and reviewer authority;
- integration/merge fundamentals;
- prompt construction and prompt evaluation principles;
- generic handoff/continuation semantics.

### 2. Immutable provider binding

Each provider stores one small machine-readable binding, for example:

`docs/agents/META_AGENT_POLICY_BINDING.json`

with this shape:

```json
{
  "schema_version": 1,
  "policy_id": "OTERYN_ORGANIZATION_AGENT_POLICY",
  "policy_version": "3.0.0",
  "authority_repository": "Oteryn/Oteryn",
  "authority_commit": "<full merged META commit SHA>",
  "organization_policy_path": "docs/agents/policy/ORGANIZATION_AGENT_POLICY.md",
  "prompting_standard_path": "docs/agents/policy/PROMPTING_STANDARD.md",
  "prompt_eval_standard_path": "docs/agents/policy/PROMPT_EVAL_STANDARD.md"
}
```

The binding pins an immutable merged META commit. Provider adoption therefore changes only when a provider deliberately adopts a newer central policy. This prevents a moving META `main` from silently changing execution semantics inside an already-admitted provider task.

The provider root `AGENTS.md` tells an agent to resolve the pinned META policy before material mutation. If the pinned policy cannot be resolved through an authorized repository-native path, mutation fails closed; read-only inspection may continue.

A stale binding is an explicit adoption state, not a hidden fork. Providers must not copy the central policy body to compensate for a stale binding.

### 3. Thin provider overlays

Provider `AGENTS.md` files contain only:

1. repository identity and bootstrap to `META_AGENT_POLICY_BINDING.json`;
2. precedence rule: current local domain/safety restrictions may narrow central policy but cannot broaden organization authority;
3. repository-specific domain invariants;
4. repository-specific validation/deployment facts that genuinely differ from other providers;
5. links to local contracts required for those domain facts.

Examples of local content that remains valid:

- Game: native Rust/protocol authority, server/session/fencing, persistence/value invariants;
- Platform: auth/RBAC/session/payment/database/public-edge and protected-environment boundaries;
- Atlas: Game-owned world/content authority, derived projection, provenance, geometry/render/browser/FullWorld and deployment-revision invariants.

Global GitHub, retry, Remote Desktop, AI-review, concurrency or generic continuation prose is removed from provider overlays after adoption.

### 4. Task-delta prompts

A reusable or one-shot execution prompt contains only task-specific information that changes behavior:

1. `ROLE / OUTCOME`;
2. `AUTHORITY / SCOPE DELTA`;
3. `LIVE LOCATORS`;
4. `DOMAIN CONSTRAINTS / DEPENDENCIES`;
5. `ACCEPTANCE / VALIDATION DELTA`;
6. `STOP / HANDOFF DELTA`.

A section is omitted when it has no task-specific content. Prompts do not copy global AI-review, Remote Desktop, GitHub-first, moving-main, retry, generic merge or generic continuation policy.

Prompt aliases grant no authority. Provider-local lifecycle registries remain local because the executable prompt inventory is repository-local; they implement the central lifecycle semantics rather than redefining them.

### 5. Handoffs

Handoffs are state deltas, not policy documents. A normal handoff stores only durable coordinates and material state:

- task/repository/Issue;
- branch/PR/exact head;
- completed material work;
- remaining work;
- material evidence;
- blocker/disposition;
- exactly one next safe action.

Global policy text is never copied into handoffs.

## Enforcement model

### META

META validators verify that the central human policy references the active machine modules and does not reintroduce ADR-0005-retired governance machinery.

The central prompting standard explicitly requires one-rule/one-authority and outcome-first task deltas. The central eval standard requires ablation and representative current-vs-lean model trials for material prompt changes.

### Providers

Each provider adds a small local validator that verifies:

- the binding file has the exact closed schema;
- `authority_repository` is `Oteryn/Oteryn`;
- the commit selector is a full immutable SHA, never `main`, a tag or an abbreviated SHA;
- root `AGENTS.md` names the binding and does not contain forbidden copies of organization-wide policy sections;
- provider-specific approved domain sections remain present;
- reusable prompts may inherit global policy and fail if they attempt to broaden it.

The validator does **not** copy the central policy body into provider code. It enforces the boundary between central and local responsibility.

## Policy update lifecycle

1. Change central policy in META with deterministic RED→GREEN tests when behavior/enforcement changes.
2. For material control-plane changes, obtain the independent review/owner authorization required by current policy before integration.
3. Merge through normal META protection/Merge Queue.
4. Provider adoption is an explicit PR that bumps `META_AGENT_POLICY_BINDING.json` to the new merged META commit and reconciles only provider-local impacts.
5. Provider exact-head CI proves the overlay remains valid.
6. Existing admitted work keeps its admission policy binding unless current repository rules require reloading a newly applicable safety/authority change; unaffected implementation is preserved.

This explicit adoption model prevents both silent global drift and copied-policy divergence.

## Migration strategy

### Phase 0 — finish #140

Do not merge provider-centralization changes on top of unresolved #140 prompt-cleanup ownership. Reuse the tested inherited-policy work from Game #272 and the lean Platform standard from #1289 after those lifecycles are terminally reconciled. Atlas waits for #182/#194/#279/#304 overlap to resolve.

### Phase 1 — META canonical bundle

After the active META root `AGENTS.md` owner (#139 or successor) is terminal, create the central policy bundle and machine schema/validator. Keep root `AGENTS.md` as a short META bootstrap pointing to the bundle rather than another policy copy.

### Phase 2 — Game canary/adoption

Adopt the immutable binding, shrink Game root instructions to the provider overlay, point local prompt lifecycle/eval machinery at the central standard, and use the already-tested Durability prompt as the canary. Do not mass-migrate every prompt until the canary passes deterministic gates plus the required model/runtime evaluation.

### Phase 3 — Platform adoption

Adopt the binding, retain Platform-only security/product invariants, replace local global prompting/eval rules with references to META, and keep Platform-specific eval scenario suites as data rather than a competing standard.

### Phase 4 — Atlas adoption

After current root/registry/prompt overlaps clear, adopt the binding and preserve Atlas-only provenance/browser/FullWorld/deployment invariants. Reconcile the existing Documentation/Agent IA registry instead of creating a competing lifecycle system.

### Phase 5 — retirement and convergence

Retire provider-local global-policy documents only after their replacement is canonical on protected provider `main`. Historical paths may become short provenance tombstones where stable references matter.

Run organization readback proving that each provider:

- binds to one merged META policy version;
- contains no active fork of organization semantics;
- retains only approved domain overlay content;
- passes its aggregate gate;
- has no falsely dispatchable superseded prompt created by the migration.

## Evaluation

Deterministic validators prove schema, references, forbidden duplication and existing repository invariants. They do not prove model behavior.

For each material prompt migration, compare the current and lean candidate on the same representative GPT-5.6 Sol cases. Measure at minimum:

- task completion/correctness;
- safety/authority violations;
- false blockers/premature stops;
- unnecessary owner questions/approval requests;
- repeated policy reads/tool calls;
- context loaded versus used;
- missed domain constraints;
- token/cost deltas where observable.

Safety-critical regression tolerance is zero. A duplicated rule stays removed only when governing instructions/machine enforcement still protect the invariant and the representative evals do not regress.

## Completion criteria

The programme is complete only when:

- the central META policy bundle is merged and protected-main readback is verified;
- Game, Platform and Atlas each bind to one immutable merged META policy version;
- provider root instructions contain only bootstrap + domain overlay semantics;
- provider-local copies of global prompting/review/RDC/concurrency/retry/continuation rules are retired or reduced to provenance tombstones;
- at least one real prompt canary per provider passes applicable deterministic and model/runtime evaluation;
- provider aggregate gates and Merge Queue integration remain intact;
- no active overlapping governance branch is overwritten;
- the parent #142 records final provider binding commits and terminal readback.
