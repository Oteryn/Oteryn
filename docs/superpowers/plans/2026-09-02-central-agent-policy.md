# Central Agent Policy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make META the sole owner of organization-wide agent semantics, with immutable provider bindings, thin provider overlays and task-delta prompts.

**Architecture:** META owns one human policy bundle plus existing focused machine modules. Each provider pins one immutable merged META commit in `docs/agents/META_AGENT_POLICY_BINDING.json` and keeps only repository bootstrap/domain-specific rules locally. Provider validators fail closed on mutable/stale-shaped bindings and on reintroduced copies of global policy; prompt migration is canary-first and evaluated by ablation.

**Tech Stack:** Markdown, JSON, Python 3.12 governance validators/tests, GitHub Actions, existing repository aggregate gates and Merge Queue.

**Spec:** `docs/superpowers/specs/2026-09-02-central-agent-policy-design.md`

## Global Constraints

- `Oteryn/Oteryn#140` cleanup slices must be terminally reconciled before provider-centralization mutation is integrated.
- Do not overwrite active root/prompt/registry ownership; refresh live PR changed-file inventories before every provider lane.
- No new orchestration service, second merge authority, required status, attestation system or policy-copy generator.
- Provider bindings pin a full immutable 40-character merged META commit SHA; never `main`, a tag or an abbreviated SHA.
- Provider overlays may narrow organization policy but cannot broaden authority or fork global semantics.
- Safety-critical prompt/model-eval regression tolerance is zero.
- Existing aggregate gates and Merge Queue remain integration authority.

---

### Task 1: Establish the canonical META agent-policy bundle

**Files:**
- Create: `docs/agents/policy/ORGANIZATION_AGENT_POLICY.md`
- Create: `docs/agents/policy/PROMPTING_STANDARD.md`
- Create: `docs/agents/policy/PROMPT_EVAL_STANDARD.md`
- Create: `ecosystem/organization-agent-policy.json`
- Create: `tools/governance/organization_agent_policy.py`
- Create: `tools/governance/test_organization_agent_policy.py`
- Modify: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: current protected-main `AGENTS.md`, ADR 0004/0005, execution-routing policy, bounded autonomous execution policy, continuation policy and AI review policy.
- Produces: `OTERYN_ORGANIZATION_AGENT_POLICY` v3 as the only human semantic entry point plus a closed machine contract used by provider bindings.

- [ ] **Step 1: Re-read live authority after #140 and #139 terminal reconciliation**

Run GitHub readback for protected META `main`, open governance PRs and the exact current versions of the policies named above. Do not begin this task while another open PR owns any target file.

- [ ] **Step 2: Write failing policy-contract tests**

Add tests that require the central bundle and reject retired governance concepts:

```python
class OrganizationAgentPolicyTests(unittest.TestCase):
    def test_machine_policy_has_closed_v3_identity(self):
        policy = load_policy(ROOT / "ecosystem/organization-agent-policy.json")
        self.assertEqual(1, policy["schema_version"])
        self.assertEqual("OTERYN_ORGANIZATION_AGENT_POLICY", policy["policy_id"])
        self.assertEqual("3.0.0", policy["policy_version"])

    def test_human_policy_rejects_retired_merge_authority(self):
        text = (ROOT / "docs/agents/policy/ORGANIZATION_AGENT_POLICY.md").read_text()
        for retired in ("formal R0/R1/R2", "ai-review-gate as merge authority", "review fingerprint authority"):
            self.assertNotIn(retired, text)
```

The production policy files do not exist yet, so the focused suite must fail because required artifacts are missing.

- [ ] **Step 3: Verify RED**

Run:

```bash
python tools/governance/test_organization_agent_policy.py
```

Expected: failure caused by missing central policy artifacts, not syntax/import errors.

- [ ] **Step 4: Implement the minimal machine policy**

Create `ecosystem/organization-agent-policy.json` with closed coordinates:

```json
{
  "schema_version": 1,
  "policy_id": "OTERYN_ORGANIZATION_AGENT_POLICY",
  "policy_version": "3.0.0",
  "provider_binding_schema_version": 1,
  "execution_shapes": ["single_agent", "parallel_when_beneficial"],
  "prompt_contract_sections": [
    "role_outcome",
    "authority_scope_delta",
    "live_locators",
    "domain_constraints_dependencies",
    "acceptance_validation_delta",
    "stop_handoff_delta"
  ],
  "provider_may_narrow": true,
  "provider_may_broaden": false,
  "provider_may_copy_global_policy": false
}
```

- [ ] **Step 5: Implement the three human policy surfaces**

`ORGANIZATION_AGENT_POLICY.md` must state each global rule once and delegate closed predicates to existing machine modules. `PROMPTING_STANDARD.md` must define task-delta prompts and one-rule/one-authority. `PROMPT_EVAL_STANDARD.md` must require current-vs-lean ablation/model trials for material prompt changes and zero safety regression.

Do not copy the full bodies of execution-routing, continuation or AI-review policies into the new contract; reference their canonical paths.

- [ ] **Step 6: Implement the validator**

`organization_agent_policy.py` must verify:

```python
REQUIRED_HUMAN = (
    "docs/agents/policy/ORGANIZATION_AGENT_POLICY.md",
    "docs/agents/policy/PROMPTING_STANDARD.md",
    "docs/agents/policy/PROMPT_EVAL_STANDARD.md",
)
FORBIDDEN_AUTHORITY = (
    "review fingerprints are merge authority",
    "ai-review-gate is merge authority",
    "formal R0/R1/R2 is required",
)
```

It must parse the JSON, enforce the exact closed values above, require all three human files, and fail when a forbidden authority statement appears.

- [ ] **Step 7: Wire the focused suite into META CI**

Add exactly one focused step to the existing aggregate-gate path:

```yaml
- name: Validate organization agent policy
  run: |
    python tools/governance/test_organization_agent_policy.py
    python tools/governance/organization_agent_policy.py
```

Do not add a new required status.

- [ ] **Step 8: Verify GREEN and full META governance**

Run the repository-equivalent focused suite and the existing governance/merge-queue tests required by `.github/workflows/ci.yml`. Expected: all pass with no new required status.

- [ ] **Step 9: Open a META PR and qualify it**

Treat the change as material control-plane governance. Require deterministic exact-head CI, one independent deep review when current policy selects it, explicit owner authorization if current policy requires it, normal Merge Queue integration and protected-main readback.

---

### Task 2: Convert META root instructions to a thin bootstrap

**Files:**
- Modify: `AGENTS.md`
- Modify: `tools/governance/test_organization_agent_policy.py`

**Interfaces:**
- Consumes: merged Task 1 policy bundle on protected META `main`.
- Produces: short META root bootstrap that points to the canonical bundle and keeps only META-repository-specific instructions.

- [ ] **Step 1: Write a failing duplication-budget regression**

Add a test that requires root `AGENTS.md` to name all three central policy paths and forbids root copies of provider-generic section headings such as `## Remote Desktop execution routing` or a full local AI-review routing block when the central contract owns them.

- [ ] **Step 2: Verify RED against the current large root file**

Run:

```bash
python tools/governance/test_organization_agent_policy.py
```

Expected: failure identifying duplicated global policy in root `AGENTS.md`.

- [ ] **Step 3: Reduce root `AGENTS.md`**

Keep only:

```text
repository identity / META authority role
central policy bundle pointers
local META-only path/scope notes
precedence and fail-closed bootstrap
```

Do not remove a rule unless its surviving authority is named in the central bundle or existing machine policy.

- [ ] **Step 4: Verify GREEN and exact-head META CI**

Run the focused suite plus full applicable META CI. Inspect the final diff to confirm no execution/merge/production authority was broadened.

- [ ] **Step 5: Integrate through normal META protection**

Use the current review/owner/Merge Queue rules. Verify protected-main content after merge.

---

### Task 3: Adopt the central policy in Game

**Files:**
- Create: `docs/agents/META_AGENT_POLICY_BINDING.json`
- Modify: `AGENTS.md`
- Modify: `docs/agents/PROMPTING_STANDARD.md`
- Modify: `docs/agents/PROMPT_EVAL_STANDARD.md`
- Modify: `tools/agents/validate_governance.py` or create one focused binding validator following current repository patterns
- Modify: existing binding/governance tests
- Modify: `docs/agents/prompts/OTV2_IMPL_DURABILITY.md` only if #272 did not already produce the canonical canary

**Interfaces:**
- Consumes: exact merged META Task 2 commit and terminal Game #272 state.
- Produces: immutable Game binding, thin Game domain overlay and one real inherited-policy canary.

- [ ] **Step 1: Refresh overlaps and select exact META authority commit**

Verify no open Game PR owns the target governance files. Record the full merged META commit containing Tasks 1–2.

- [ ] **Step 2: Write RED tests for the provider binding**

Require:

```python
self.assertEqual("Oteryn/Oteryn", binding["authority_repository"])
self.assertRegex(binding["authority_commit"], r"^[0-9a-f]{40}$")
self.assertNotIn(binding["authority_commit"], {"main", "master"})
```

Also fail if Game root reintroduces organization-wide `parallel-first`, global RDC, global AI-review or generic retry/continuation policy text outside the approved bootstrap pointer.

- [ ] **Step 3: Verify RED**

Run the focused Game governance tests. Expected: missing binding and duplicated root/global standard text cause failure.

- [ ] **Step 4: Add the immutable binding**

Write `META_AGENT_POLICY_BINDING.json` using the exact merged META SHA and the three canonical policy paths from the spec.

- [ ] **Step 5: Reduce Game to the domain overlay**

Keep Game-specific Rust/protocol/server/session/fencing/persistence/value/resource invariants. Remove global scheduling/RDC/AI-review/retry/continuation copies. Replace local prompting/eval standards with short compatibility/bootstrap documents that point to the pinned META standards and retain only Game-specific prompt/eval additions.

- [ ] **Step 6: Preserve the Durability canary**

If #272 merged, verify the canary still contains only task-specific delta. If #272 was superseded, migrate `OTV2_IMPL_DURABILITY.md` using the six-section contract without changing Durability domain semantics.

- [ ] **Step 7: Verify Game GREEN**

Run all Agent Governance suites, repository policy validation, architecture semantic audit and `game-gate` on the exact final head. Run the required GPT-5.6 Sol current-vs-lean canary trials defined by the central eval standard; record correctness, safety, false blockers, unnecessary owner questions and tool/context waste.

- [ ] **Step 8: Integrate and read back protected Game main**

Use current independent review/owner/Merge Queue policy. Verify the binding SHA and thin overlay from protected `main` after merge.

---

### Task 4: Adopt the central policy in Platform

**Files:**
- Create: `docs/agents/META_AGENT_POLICY_BINDING.json`
- Modify: `AGENTS.md`
- Modify: `docs/agents/PROMPTING_STANDARD.md`
- Modify: `docs/agents/PROMPT_EVAL_STANDARD.md`
- Modify: `tools/agents/policy_consistency.py` and focused tests only as required to enforce the binding/no-fork boundary
- Keep: `docs/agents/evals/*.json` as Platform-specific scenario data

**Interfaces:**
- Consumes: merged META authority commit and terminal Platform #1289/#1270 state.
- Produces: thin Platform overlay; Platform scenario suites remain local data under the central eval standard.

- [ ] **Step 1: Refresh live ownership**

Do not touch root `AGENTS.md` until #1270 or its successor is terminal. Do not touch any file owned by active content/programme PRs.

- [ ] **Step 2: Add failing binding/no-fork regressions**

Require an immutable META binding and fail on copied global scheduling/RDC/AI-review/retry/continuation sections in Platform root or prompting standard.

- [ ] **Step 3: Verify RED**

Run:

```bash
python tools/agents/test_policy_consistency.py
python tools/agents/policy_consistency.py
python tools/validation/test_prompt_eval.py
python tools/validation/prompt_eval.py
```

Expected: new binding/no-fork assertions fail before implementation while existing prompt-eval cases remain otherwise valid.

- [ ] **Step 4: Implement binding and thin overlay**

Keep Platform-only auth/RBAC/session/payment/database/public-edge/production safety and product completeness invariants. Point prompt construction/evaluation to META. Keep local JSON eval suites because they are provider-specific test cases, not a competing standard.

- [ ] **Step 5: Verify GREEN**

Run Agent Governance, policy consistency, prompt eval, Documentation/Agent IA, live task liveness and full `platform-gate` on exact head. Perform representative GPT-5.6 Sol current-vs-lean trials for a real Platform worker prompt.

- [ ] **Step 6: Integrate and read back protected Platform main**

Use current independent review/owner/Merge Queue rules and verify the exact binding plus overlay after merge.

---

### Task 5: Adopt the central policy in Atlas

**Files:**
- Create: `docs/agents/META_AGENT_POLICY_BINDING.json`
- Modify: `AGENTS.md`
- Modify: `docs/agents/DOCUMENTATION_AGENT_IA.json` only through its current canonical lifecycle after #194 or successor is terminal
- Modify: Atlas prompt/eval validation surfaces discovered from current protected main
- Canary: one current reusable Atlas prompt selected only after #304 or its successor is terminal

**Interfaces:**
- Consumes: merged META authority commit and cleared #182/#194/#279/#304 ownership.
- Produces: thin Atlas overlay preserving projection/provenance/browser/FullWorld/deployment semantics.

- [ ] **Step 1: Prove overlap clearance**

Read changed-file inventories for every open Atlas governance/prompt PR. If any target path remains owned, stay `WAITING_OVERLAP` and do not create a competing mutation branch.

- [ ] **Step 2: Write RED binding/no-fork tests**

Require immutable META binding and fail on copied organization-wide concurrency/RDC/AI-review/retry/continuation semantics while explicitly allowing Atlas-only provenance/browser/FullWorld/deployment terms.

- [ ] **Step 3: Verify RED**

Run current Atlas governance/documentation validation. Expected: new binding/no-fork assertions fail before implementation.

- [ ] **Step 4: Implement thin Atlas overlay and registry reconciliation**

Keep only Atlas-specific authority/provenance/render/browser/FullWorld/runner/deployment rules. Reconcile existing `DOCUMENTATION_AGENT_IA.json`; do not create a new prompt lifecycle registry.

- [ ] **Step 5: Migrate one Atlas canary prompt**

Select a live reusable prompt whose owner is terminal and remove copied global policy while keeping Atlas-specific acceptance and E2E requirements.

- [ ] **Step 6: Verify GREEN**

Run Atlas governance/documentation validators, applicable browser/visual/E2E classification, `atlas-gate` and representative GPT-5.6 Sol current-vs-lean trials on the canary.

- [ ] **Step 7: Integrate and read back protected Atlas main**

Use current review/owner/Merge Queue rules and verify binding/overlay/registry from protected main.

---

### Task 6: Retire provider global-policy copies and close the organization programme

**Files:**
- Modify or tombstone provider-local global policy documents only after each provider adoption is canonical
- Update: `Oteryn/Oteryn#142` durable closeout evidence

**Interfaces:**
- Consumes: terminal merged provider adoptions.
- Produces: organization-wide convergence with one global semantic authority.

- [ ] **Step 1: Build final readback matrix**

For META/Game/Platform/Atlas record protected `main` SHA, provider binding SHA/version, root overlay classification, prompt canary evidence, aggregate gate and open overlapping governance PRs.

- [ ] **Step 2: Retire obsolete provider-local global standards**

Where stable historical paths are referenced, replace them with short provenance tombstones pointing to the pinned META authority. Delete only files proven unreferenced by current repository validators/docs.

- [ ] **Step 3: Search for forbidden active duplication**

Search active instruction/prompt surfaces for global policy markers such as local `parallel-first` requirements, full RDC per-action blocks, full Codex review controllers and generic retry/continuation copies. Every match must be either META authority, an approved provider-domain exception, or historical/provenance-only content excluded from dispatch.

- [ ] **Step 4: Verify all four aggregate gates and protected-main readback**

Do not infer convergence from PR summaries. Read protected main in all four repositories and verify final files/settings directly.

- [ ] **Step 5: Close #142 only with terminal evidence**

The closeout comment must name exact merged META policy commit, exact provider binding commits, canary/eval evidence and any intentionally retained historical tombstones. Any provider still on an older binding keeps #142 nonterminal.
