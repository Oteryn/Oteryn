# Organization audit checkpoint — 2026-09-14 current-main delta revalidation

Purpose: durable continuation evidence for META Issue #186 / PR #185 after protected META `main` advanced beyond the R6 audit base. This checkpoint records a bounded read-only source/history revalidation. It does not replace the canonical R6 accounting, does not claim organization-wide audit completion, and does not authorize integration or provider mutation.

## Fresh lifecycle readback

- PR #185 remains **OPEN / DRAFT / unmerged** on branch `docs/20260907-org-comprehensive-audit`.
- PR #185 head before this checkpoint: `b1eb407c4bbd9526d7a5c54d4e1fadb68e8311c9`.
- The audit branch and protected `main` still share merge-base `6496ed7f96f80d3dc2e64529c3a09a18c99215fb`.
- Fresh protected META `main`: `23b21e9b1b2d4b6c3a5cac3d4c7a18747804c090`, tree `b8ebb8e50bce14a736fa65590ac121655c52fd12`.
- Protected `main` is four commits ahead of the audit merge-base; the audit branch has not incorporated those four commits.

The four protected-main commits are:

1. `ed6c8c98605a7fbfea858e0ef616f89baa617262` — `fix(agents): adopt native exact-head Merge Queue submission (#192)`.
2. `3b39e0be05aef008f1bd442821daefa898a201dd` — `fix(agents): make native merge-async auth app-free (#193)`.
3. `ce20300aa8a9e1017aff722fe0cd628587fadf63` — `fix(agents): route protected integration by verified capability (#195)`.
4. `23b21e9b1b2d4b6c3a5cac3d4c7a18747804c090` — `fix(governance): preserve trusted issue-comment actor (#199)`.

## Effective source delta

Comparing the R6 audit base `6496ed7f...` with protected `main@23b21e9...` yields 19 effective changed paths: 8 newly added paths and 11 modified paths, with no deleted path in this bounded delta.

New paths:

- `.github/workflows/governed-merge-queue-executor.yml`
- `docs/agents/contracts/INTEGRATION_CAPABILITY_ROUTING_POLICY.md`
- `docs/agents/operations/MERGE_QUEUE_EXECUTOR.md`
- `docs/agents/programs/OTERYN_MQ_CAPABILITY_ROUTING_20260910.md`
- `tools/governance/governed_merge_queue_executor.py`
- `tools/governance/integration_capability_routing.py`
- `tools/governance/test_governed_merge_queue_executor.py`
- `tools/governance/test_integration_capability_routing.py`

Modified paths:

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

## Semantic/history revalidation

### #192 — native exact-head Merge Queue submission

The organization policy moved from requiring a mutation-time head-and-base/queue fence to explicitly accepting GitHub REST `merge-async` with exact `sha` plus `merge_action="merge_queue"`, while acknowledging the residual retarget race. The accepted mitigation is fresh exact-target preflight, UUID-bound request acceptance, strictly later target readback, real `merge_group` aggregate success and protected-main readback. Generic auto-merge/direct merge remain forbidden substitutes.

This is a material governance semantic change relative to the R6 base and must be represented in any refreshed current-main audit.

### #193 — app-free mutation authentication

The selected native route no longer requires or authorizes a custom GitHub App bootstrap. Operational mutation authentication is restricted to a directly exposed native route or a bounded fine-grained PAT; built-in workflow `GITHUB_TOKEN`, custom-App fallback, GraphQL substitution and generic auto-merge remain non-operational/forbidden routes for this contract.

This changes authentication semantics but does not itself prove a credential exists or that the route is operational.

### #195 — capability-aware integration routing and delegated executor

Protected integration capability became an explicit scheduling input with states `NOT_REQUIRED`, `DIRECT_CAPABLE`, `DELEGATED_CAPABLE`, and `BLOCKED_CAPABILITY_UNAVAILABLE`. A substantial mutating worker expected to require autonomous protected integration must pass trusted capability observation before release. The change also introduced the META-owned governed Merge Queue executor, control transport on Issue #196, exact request grammar, protected-main/canary binding, target allowlist, source-workflow qualification and deterministic executor tests.

This is both a semantic-policy change and a new executable governance surface. It cannot be considered operational solely because source and tests exist.

### #199 — event actor and current-membership binding

The delegated executor now preserves the authenticated issue-comment event actor/association, requires live comment actor agreement, authenticates the fine-grained PAT principal, revalidates current active `Oteryn` organization membership, and requires current target `admin` or `maintain` permission before the queue mutation. Creation-time OWNER/MEMBER association is ingress evidence rather than sufficient current authorization.

This materially strengthens the #195 executor authorization contract and changes the protected workflow blob bound by capability policy.

## Live operational evidence

Issue #196 records the first provider canary against protected META `ce20300aa8a9e1017aff722fe0cd628587fadf63`. Workflow run `34754981088` parsed the bounded request and verified the protected-main SHA fence, then stopped before any queue mutation because `OTERYN_MQ_FINE_GRAINED_PAT` was not provisioned. No `merge-async` PUT and no async UUID were produced.

Protected META `main` later advanced to `23b21e9...`. The current integration-capability contract requires delegated capability/canary evidence to be bound to the exact current protected-main SHA; therefore the unsuccessful `ce20300...` canary cannot establish current `DELEGATED_CAPABLE` state for `23b21e9...`.

This checkpoint does not provision credentials and does not repeat the failed canary.

## Impact on canonical audit state

The R6 accounting remains the authoritative accounting for the pinned R6 snapshot:

- 4,325 source leaves
- 294 DIRECT
- 113 GROUPED
- 3,918 UNVERIFIED
- 407 semantically classified
- ledger SHA-256 `ff5c6621a78c14fc17802ecf01b4ef815867ccab95acce90c490973946d6279b`

It must not be silently relabeled as current-main accounting. The current protected-main delta contains eight new source paths and eleven modified paths. A new canonical current-main leaf count, disposition totals, and ledger digest require an actual refreshed source inventory plus authoritative ledger rebuild/verification; this checkpoint deliberately does not invent those values.

`HISTORY-REVALIDATION` therefore remains open: the four protected-main governance commits have now received bounded source-semantic revalidation, but current delegated-executor operational outcome is still unresolved and other historical/provider records remain outside this cycle.

`SEMANTIC-COVERAGE` also remains open: this checkpoint identifies and semantically classifies the bounded current-main governance delta as a delta record, but it does not adopt those paths into the existing R6 canonical ledger or claim that the wider 3,918-path R6 UNVERIFIED scope is closed.

No other residual obligation is closed by this checkpoint. In particular, no admin/security setting, provider runtime, production state, recovery, cost, supply-chain, native journey, UI, portability, live telemetry, privacy-rights or PLATFORM-H02 completion is established.

## Next gate

1. Rebuild a fresh current-main META source inventory against exact protected `main@23b21e9b1b2d4b6c3a5cac3d4c7a18747804c090` using the existing authoritative audit collector/ledger path.
2. Reconcile the resulting exact leaf set against R6 without double-adopting unchanged DIRECT/GROUPED semantics.
3. Bind the eight new paths and eleven changed paths to exact current blobs and explicit semantic dispositions.
4. Recompute current accounting and ledger digest only from that verified inventory.
5. Keep Issue #186 and PR #185 OPEN/DRAFT until the remaining canonical obligations are actually closed or dispositioned.

This checkpoint authorizes no merge, queue, mark-ready action, provider write, production action, secret/environment change, protection/ruleset change, credential provisioning or Merge Queue mutation.
