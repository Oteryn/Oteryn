# Organization audit checkpoint — 2026-09-14 current-main delta revalidation

Purpose: durable continuation evidence for META Issue #186 / PR #185 after protected META `main` advanced beyond the source snapshot pinned by the organization audit. This checkpoint records bounded read-only source/history revalidation. It does not replace canonical R6 accounting, does not claim organization-wide audit completion, and does not authorize integration or provider mutation.

## Fresh lifecycle and source-identity readback

- PR #185 remains **OPEN / DRAFT / unmerged** on branch `docs/20260907-org-comprehensive-audit`.
- PR #185 head before this checkpoint lane: `b1eb407c4bbd9526d7a5c54d4e1fadb68e8311c9`.
- PR #185 and protected `main` share branch merge-base `6496ed7f96f80d3dc2e64529c3a09a18c99215fb`.
- Fresh protected META `main`: `23b21e9b1b2d4b6c3a5cac3d4c7a18747804c090`, tree `b8ebb8e50bce14a736fa65590ac121655c52fd12`.
- The authoritative audit `collection-plan.json` still pins META audited source to `1a01c5b3e08666a82245b1cac78da3736c65e785`, tree `f084e824ec5e14d5909c9750d906d91d51425fd5`.

These are different coordinates and must not be conflated:

- **branch drift** from PR merge-base `6496ed7f...` to current protected `main`: 4 commits / 19 effective changed paths;
- **audited-source drift** from canonical META source snapshot `1a01c5b...` to current protected `main`: 6 commits / 45 effective changed paths, consisting of 36 added paths and 9 modified paths, with no deleted path in that compare.

The six protected-main commits after the pinned META source snapshot are:

1. `d1caa3adba0fa4b32b84985bf1d6dcbe8055858c` — `fix(agents): require atomic exact-target Merge Queue submission (#188)`.
2. `6496ed7f96f80d3dc2e64529c3a09a18c99215fb` — `docs(audit): complete R4 current-main repository audit (#153)`.
3. `ed6c8c98605a7fbfea858e0ef616f89baa617262` — `fix(agents): adopt native exact-head Merge Queue submission (#192)`.
4. `3b39e0be05aef008f1bd442821daefa898a201dd` — `fix(agents): make native merge-async auth app-free (#193)`.
5. `ce20300aa8a9e1017aff722fe0cd628587fadf63` — `fix(agents): route protected integration by verified capability (#195)`.
6. `23b21e9b1b2d4b6c3a5cac3d4c7a18747804c090` — `fix(governance): preserve trusted issue-comment actor (#199)`.

## Current-main delta interpretation

### #188 — intermediate atomic-fence MQ contract

#188 introduced `tools/governance/merge_queue_submission_routing.py`, its tests, CI coverage and policy text that required an atomic mutation-time fence over both exact head and base/queue. Under that revision the documented GitHub primitives were intentionally classified as insufficient for autonomous submission and callers could not self-assert a hypothetical capability.

This is important history but it is **not the final current-main MQ semantic**, because #192 later changed the organization policy to accept native exact-head `merge-async` without an expected-base precondition under an explicitly accepted residual race and mandatory pre/post validation. A refreshed current-main audit must preserve #188 as historical lineage without treating its superseded atomic-base-fence prohibition as present authority.

### #153 — repository-audit evidence publication

#153 added the `docs/evidence/repository-audit-2026-09-06/**` evidence packet and its R4 current-main closeout. Its commit explicitly describes the material as documentation/evidence and not a code, workflow, policy, provider, or protected-setting change.

The existing organization-audit R4 candidate already treats #153 publication coordinates as **corroborating historical provenance, not source identity or live truth**. That temporal role remains correct for current-main rebaseline: these newly present tracked evidence files must be inventoried as current tree leaves, but their historical statements must not silently become present runtime/admin/governance authority.

### #192 — native exact-head Merge Queue submission

The organization policy moved from requiring a mutation-time head-and-base/queue fence to explicitly accepting GitHub REST `merge-async` with exact `sha` plus `merge_action="merge_queue"`, while acknowledging the residual retarget race. The accepted mitigation is fresh exact-target preflight, UUID-bound request acceptance, strictly later target readback, real `merge_group` aggregate success and protected-main readback. Generic auto-merge/direct merge remain forbidden substitutes.

This is a material governance semantic change relative to both the pinned source snapshot and the intermediate #188 state.

### #193 — app-free mutation authentication

The selected native route no longer requires or authorizes a custom GitHub App bootstrap. Operational mutation authentication is restricted to a directly exposed native route or a bounded fine-grained PAT; built-in workflow `GITHUB_TOKEN`, custom-App fallback, GraphQL substitution and generic auto-merge remain non-operational/forbidden routes for this contract.

This changes authentication semantics but does not itself prove a credential exists or that the route is operational.

### #195 — capability-aware integration routing and delegated executor

Protected integration capability became an explicit scheduling input with states `NOT_REQUIRED`, `DIRECT_CAPABLE`, `DELEGATED_CAPABLE`, and `BLOCKED_CAPABILITY_UNAVAILABLE`. A substantial mutating worker expected to require autonomous protected integration must pass trusted capability observation before release. The change also introduced the META-owned governed Merge Queue executor, control transport on Issue #196, exact request grammar, protected-main/canary binding, target allowlist, source-workflow qualification and deterministic executor tests.

This is both a semantic-policy change and a new executable governance surface. It cannot be considered operational solely because source and tests exist.

### #199 — event actor and current-membership binding

The delegated executor now preserves the authenticated issue-comment event actor/association, requires live comment actor agreement, authenticates the fine-grained PAT principal, revalidates current active `Oteryn` organization membership, and requires current target `admin` or `maintain` permission before the queue mutation. Creation-time OWNER/MEMBER association is ingress evidence rather than sufficient current authorization.

This materially strengthens the #195 executor authorization contract and changes the protected workflow blob bound by capability policy.

## Branch-drift path set after #153

The four commits after PR merge-base `6496ed7f...` change 19 paths. Eight are new relative to that merge-base:

- `.github/workflows/governed-merge-queue-executor.yml`
- `docs/agents/contracts/INTEGRATION_CAPABILITY_ROUTING_POLICY.md`
- `docs/agents/operations/MERGE_QUEUE_EXECUTOR.md`
- `docs/agents/programs/OTERYN_MQ_CAPABILITY_ROUTING_20260910.md`
- `tools/governance/governed_merge_queue_executor.py`
- `tools/governance/integration_capability_routing.py`
- `tools/governance/test_governed_merge_queue_executor.py`
- `tools/governance/test_integration_capability_routing.py`

Eleven are modified relative to that merge-base:

- `.github/workflows/ci.yml`
- `AGENTS.md`
- `docs/agents/policy/ORGANIZATION_AGENT_POLICY.md`
- `docs/agents/policy/PROMPTING_STANDARD.md`
- `docs/agents/policy/PROMPT_EVAL_STANDARD.md`
- `ecosystem/agent-execution-routing-policy.json`
- `ecosystem/organization-agent-policy.json`
- `tools/governance/central_agent_policy.py`
- `tools/governance/merge_queue_submission_routing.py`
- `tools/governance/test_central_agent_policy.py`
- `tools/governance/test_merge_queue_submission_routing.py`

The larger 45-path audited-source delta additionally contains #153 historical evidence files and the #188 routing files that were absent from the pinned `1a01c5b...` source snapshot.

## Live operational evidence

Issue #196 records the first provider canary against protected META `ce20300aa8a9e1017aff722fe0cd628587fadf63`. Workflow run `34754981088` parsed the bounded request and verified the protected-main SHA fence, then stopped before any queue mutation because `OTERYN_MQ_FINE_GRAINED_PAT` was not provisioned. No `merge-async` PUT and no async UUID were produced.

Protected META `main` later advanced to `23b21e9...`. The current integration-capability contract requires delegated capability/canary evidence to be bound to the exact current protected-main SHA; therefore the unsuccessful `ce20300...` canary cannot establish current `DELEGATED_CAPABLE` state for `23b21e9...`.

This checkpoint does not provision credentials and does not repeat the failed canary.

## Impact on canonical audit state

The R6 accounting remains authoritative only for its pinned audit identity/accounting model:

- 4,325 source leaves
- 294 DIRECT
- 113 GROUPED
- 3,918 UNVERIFIED
- 407 semantically classified
- ledger SHA-256 `ff5c6621a78c14fc17802ecf01b4ef815867ccab95acce90c490973946d6279b`

It must not be silently relabeled as current protected-main accounting. The actual current-main META source delta from the pinned source snapshot is the full 45-path delta described above, not merely the later 19-path branch drift. A new canonical current-main leaf count, disposition totals and ledger digest require an actual refreshed source inventory plus authoritative ledger rebuild/verification; this checkpoint deliberately does not invent those values.

`HISTORY-REVALIDATION` therefore remains open. This cycle now identifies the complete six-commit META lineage from the pinned source identity and records the final current semantics of the MQ/capability changes, but current delegated-executor operational outcome is unresolved and other historical/provider records remain outside this cycle.

`SEMANTIC-COVERAGE` also remains open. The governance lineage above received bounded semantic review, and #153 evidence retains its historical-evidence role, but the 45 changed current-tree paths have not been adopted into a newly rebuilt canonical ledger. The wider R6 UNVERIFIED scope is not closed.

No other residual obligation is closed by this checkpoint. In particular, no admin/security setting, provider runtime, production state, recovery, cost, supply-chain, native journey, UI, portability, live telemetry, privacy-rights or PLATFORM-H02 completion is established.

## Next gate

1. Rebuild a fresh current-main META source inventory against exact protected `main@23b21e9b1b2d4b6c3a5cac3d4c7a18747804c090` using the existing authoritative audit collector/ledger path.
2. Reconcile the resulting exact leaf set against the pinned `1a01c5b...` source identity and the later R4/R5/R6 semantic overlays without double-adopting unchanged semantics.
3. Bind all current changed/new paths to exact current blobs and explicit dispositions, preserving #153 evidence as historical unless separately justified.
4. Recompute current accounting and ledger digest only from that verified inventory.
5. Keep Issue #186 and PR #185 OPEN/DRAFT until the remaining canonical obligations are actually closed or dispositioned.

This checkpoint authorizes no merge, queue, mark-ready action, provider write, production action, secret/environment change, protection/ruleset change, credential provisioning or Merge Queue mutation.
