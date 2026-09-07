# Game R5 central-policy residue review

## Review coordinates and scope

- Repository: `Oteryn/Oteryn-Game`
- Requested protected-main snapshot: `10446c31b2508ccf6b65cc609a35246bf2666567`
- Previously reviewed PR #373 evidence head: `7e70330e7eab43c9bb0acd82c00e2296bd6c46c5`
- Previously reviewed #373 instruction head/tree: `ebe152af34bd003dd5c41b38eb550f10944be988` / `7adcaa9f1f7a4c8067bed4be1cbd4a6d3a55b687`
- Bound META authority: `Oteryn/Oteryn@5ed3f14400af450b5875c091e443da70f2d67ab9`
- External Draft PR #379 was observed at `cd9d0168d1bc2a738f4857036d94feb17ac84d94` / tree `ae60afdf5f563eabe671a927703045081ef49d62`, then moved to `b210ab4da087fbed99ded92b59014c35b6a4ec8a` while this review was running.

This is a read-only review of concrete residue in merged #373/current-main content. It does not qualify, authorize, mutate, or recommend wholesale integration of the moving external Draft PR #379. No repository or GitHub state was changed.

## Verdict

**WITHDRAW the broad `ROLLOUT_QUALIFIED` acceptance pending repair of the two P1 findings below.**

Preserve the W1 16/16 result as honest bounded evidence for the five tested case types and the tested instruction-delivery path. No hidden failure was found in those recorded trials. The problem is that the broad rollout conclusion exceeded their coverage: they did not exercise the still-operative owner-funded/review controller or conflicting lifecycle/retry surfaces.

The current evidence artifact overstates the disposition at:

- `docs/agents/evidence/OTV2-20260907-meta-agent-policy-v3/evaluation.json:70`
- `docs/agents/tasks/active/OTV2-20260907-meta-agent-policy-v3.md:27,31-35,43-50`

## Blocking findings

### P1 — Retired local review controller still grants authority and controls routing

`docs/agents/CODEX_REVIEW_POLICY.json:4-14` declares the Game policy `RETIRED`, disables standing-review-controller status, and names the bound META review policy as successor. However, the active `docs/agents/OWNER_FUNDED_AI_POLICY.md` still makes that retired policy normative:

- line 9 grants owner-funded use through the retired policy's standing authorization;
- line 16 declares Issue #229 standing authorization effective;
- lines 36 and 68 apply the old `CODEX_REQUIRED`/optional routing matrix and constrain the control plane through it;
- line 46 makes the retired policy determine qualifying review evidence;
- line 66 directs use of the standing-authorized path;
- line 72 names the retired policy as normative enforcement text.

This is not cosmetic. It grants continuing owner-funded review authority and a mandatory local review route that the bound META policy superseded. Bound META `docs/governance/AI_REVIEW_POLICY.md:9-20,43-53` makes external AI review advisory, defaults to none, and selects the lightest useful review without recreating the retired controller.

Minimum repair: rewrite `OWNER_FUNDED_AI_POLICY.md` as a permission-only, deny-by-default extension. It must not create review routing, a merge gate, or standing authorization from the retired Game policy. Current owner/user authorization can cover an exact use, but any new same-session authorization-retention rule should be adopted only if deliberately defined; it is not required to close this finding.

### P1 — Game locally conflicts with META lifecycle, retry, and release states

`docs/agents/ANTI_STALL_AND_EXECUTION_BUDGET.md` still owns shared lifecycle semantics:

- lines 15-16 define local generic repair/retry limits;
- line 110 emits `BLOCKED` or `WAITING` for unavailable CI recovery;
- line 148 uses three repair cycles and returns `BLOCKED` or `ROTATE`;
- lines 161, 164, and 171 use local task/result states including `WAITING` and `ROTATE`.

`docs/agents/GOVERNANCE_CONTRACT.json:77-81` also encodes `DONE | WAITING | BLOCKED | ROTATE`.

Bound META `docs/agents/policy/ORGANIZATION_AGENT_POLICY.md:33-35`, `docs/agents/contracts/BOUNDED_AUTONOMOUS_EXECUTION_POLICY.md:39-50,84-106`, and `ecosystem/bounded-autonomous-execution-policy.json:5-11,23-25,37-42` own these semantics. They require `WAITING_EXTERNAL` and `STALLED`, classify unchanged retry exhaustion as `STALLED`, and release ownership in `WAITING_EXTERNAL`, `BLOCKED`, `STALLED`, and `DONE`.

This can change retry behavior, lifecycle classification, and whether ownership is released. Minimum repair: delegate generic lifecycle/retry/freeze semantics to the bound META authority, retain only Game-specific CI observation/recovery thresholds, and update the Game contract/report vocabulary to the central states.

## Concrete non-blocking findings

### P2 — Raw-token firewall is overinclusive and misses active consumers

`tools/agents/validate_inherited_prompt_policy.py:23-39,117-124,165-174` lowercases complete reusable prompt text and rejects raw substrings. It therefore rejects negative instructions, quotations, fenced examples, historical evidence, and even legitimate references to the active owner-funded permission file. At the same time, it scans only lifecycle-reusable prompts, so the operative `OWNER_FUNDED_AI_POLICY.md` controller passed.

That conflicts with bound META `ORGANIZATION_AGENT_POLICY.md:53`, which distinguishes operative controllers from inert references/examples.

Minimum repair: use the bound central operative-Markdown statement view for focused retired-controller terms; add positive and negative regressions for operative, negative, quoted, fenced, commented, and historical text; scan explicitly identified current review-policy consumers as well as reusable prompts. Do not blacklist `OWNER_FUNDED_AI_POLICY` itself merely because it is an active permission extension.

### P2 — Fixed model/effort configuration remains in semantic governance

Concrete locations include:

- `docs/agents/programs/OTERYN_GAME_AGENT_OPERATOR_RUNBOOK.md:20-41,55-58,168`
- `docs/agents/programs/OTERYN_V2_TERRA_SOL_EXECUTION_SCHEDULER.md:9,15-28`
- `docs/agents/prompts/OTV2_OWNER_EXECUTION_STATUS_ADVISOR.md:30,66,100-107`
- the owner-runbook/model-effort references around lines 28-29 in `OTV2_SOL_CLIENT_QA_LEAD.md`, `OTV2_SOL_COMBAT_LEAD.md`, `OTV2_SOL_DURABILITY_LEAD.md`, `OTV2_SOL_MOVEMENT_LEAD.md`, and `OTV2_SOL_SERVER_SEAM_LEAD.md`.

Bound META `ORGANIZATION_AGENT_POLICY.md:27` and `PROMPTING_STANDARD.md:30` place model/effort in supported execution configuration rather than fixed maximum-effort role prose.

Minimum repair: remove hard-coded model and effort choices and transitive instructions to use them. Preserve task aliases, ownership, independence, and topology; names such as `Sol`/`Terra` are not by themselves configuration defects.

### P2 — Mandatory unrelated reads contradict routed context loading

- `docs/agents/CONTEXT_ROUTING.md:5-7` requires root, docs-agent rules, an exact active task, and live PR/CI state for every operation.
- `docs/agents/README.md:5,29` presents a required core and says agents must read task/ADR/contract/live state before acting.

Bound META `ORGANIZATION_AGENT_POLICY.md:21,49` says unrelated context is not a universal blocker and prompting/evaluation documents are not mandatory background for unrelated product tasks.

Minimum repair: require root/nearest instructions, then route task/live state and specialist documents only when material to the operation. `GOVERNANCE_CONTRACT.json:18-44` currently functions as a file-existence inventory; its `required_documents` field name need not be changed if README/routing text makes clear that it is not a universal reading bundle.

## Residue that requires lifecycle-aware classification

- `docs/agents/tasks/active/OTV2-20260828-impl-durability-successor.md:109` is an operative old-controller sentence. The packet itself is stale (`WAITING_ALLOCATION_MERGE`) even though PR #241 merged. Live Issues #167 and #240 remain open, so it is not safe to dismiss this as historical solely from age or path.
- `docs/agents/tasks/active/OTV2-20260828-terminal-session-replacement-allocation.md:114` has the same old-controller wording, but live Issue #250 is closed/completed and records terminal delivery/archive through #290. This is stale active-path residue rather than current authority.
- `docs/architecture/reviews/OTERYN_GAME_TERMINAL_SESSION_REPLACEMENT_COLLISION_RECONCILIATION_DECISION_2026-08-28.md:96-98` records the review required for a completed architecture decision. The superpowers review-loop plans/specs likewise preserve historical design evidence. These are not current grants and need not be mass-rewritten merely to eliminate tokens.
- `tools/agents/validate_governance_core.py:188-467,477,482` retains the old validator implementation, but `tools/agents/validate_governance.py:21-25` explicitly replaces it with a no-op before running the core. That is latent cleanup/maintenance debt, not an active review controller. The retired JSON may remain as readable evidence.

Minimum lifecycle repair: reconcile/archive the two stale active packets under their owning control-plane authority and correct live Issue state where authorized. Do not disguise stale allocation state by changing only the review sentence. Historical evidence should remain readable and non-dispatchable.

## External PR #379 classification

The observed #379 repair direction was substantially correct for the main concrete surfaces: permission-only owner-funded policy, META-owned lifecycle/retry states, scoped context routing, removal of fixed model/effort instructions, and a semantic retired-controller validator.

It is not an integration candidate qualified by this review:

- its head moved during review;
- its body expressly says independent final review/checks remain pending and claims no merge authority;
- its branch history/diff includes upstream content and additional evaluation/bootstrap work beyond the minimum residue repair;
- it does not by itself reconcile all stale active-packet state;
- new evaluation evidence and exact bootstrap wording are separate claims, not prerequisites for the minimum fix.

Treat #379 as external review input owned by its independent writer. Do not cherry-pick, merge, or mutate it based on this report.

## Root-authorized minimum remediation boundary

Current scope authorizes actual Game governance repairs, not mutation/integration of external Draft #379 or unrelated task owners' lifecycle records. The minimum coherent repair is:

1. make `OWNER_FUNDED_AI_POLICY.md` permission-only and remove the retired standing authorization/risk router;
2. delegate shared lifecycle/retry/freeze semantics to META and adopt its state vocabulary;
3. replace raw substring lint with semantic operative-statement validation and focused regressions;
4. remove fixed model/effort choices while preserving aliases and ownership topology;
5. scope context reads to material operations;
6. mark the W1 result candidate-only/not rollout-qualified until the repaired instruction tree receives proportionate deterministic checks, actual delivery verification, representative behavior requalification, and exact-head independent review;
7. leave task-packet archival/live-Issue reconciliation to the authorized owning control plane, while treating those packets as unsafe residue until reconciled.

The previously reviewed 47 prompt deltas, Game domain invariants, immutable authenticated META binding, repository protection, and the raw W1 16/16 bounded evidence remain useful within their proven scope.
