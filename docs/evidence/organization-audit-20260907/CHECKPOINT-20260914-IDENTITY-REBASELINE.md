# Organization audit checkpoint — 2026-09-14 current-main identity rebaseline

This checkpoint records immutable identity rebaseline evidence for Issue #186 / PR #185 after the audit task branch was reconciled with protected META `main@23b21e9b1b2d4b6c3a5cac3d4c7a18747804c090`. It is identity/accounting projection evidence only. It is not a semantic PASS, product-readiness claim, organization-wide completion claim, or integration authorization.

## Exact execution evidence

Temporary read-only workflow `Organization Audit Current-Main Rebaseline` ran on PR head `be36df77fe53a38cb9606441834bbba0edb4f3c8`:

- workflow run: `34787598530`
- job: `103805803939`
- result: `SUCCESS`
- permissions: `contents: read`
- exact generated result: `CURRENT_MAIN_IDENTITY_REBASELINE_NOT_SEMANTIC_PASS`
- result SHA-256: `bb592edba0090a218b7c979791be495f59698112544c3768e4884c35e84ef5ea`
- companion exact-head META CI run `34787598536`: `SUCCESS`

The collector executed no provider code. It shallow-fetched the pinned immutable commits and enumerated Git leaves using the existing `tools/audit/organization_audit.py` identity collector.

## Reproduced snapshot identities

Pinned old META audited source:

- commit `1a01c5b3e08666a82245b1cac78da3736c65e785`
- tree `f084e824ec5e14d5909c9750d906d91d51425fd5`
- leaves `174`

Current protected META source:

- commit `23b21e9b1b2d4b6c3a5cac3d4c7a18747804c090`
- tree `b8ebb8e50bce14a736fa65590ac121655c52fd12`
- leaves `210`

Pinned non-META source plus migration archive remained exactly `4,151` leaves:

- Game `830`
- Platform `2,165`
- Atlas `1,155`
- migration archive `1`

Therefore the immutable source/archive identity total reproduces:

- old organization total: `4,325`
- current organization total: `4,361`

## Exact META identity delta

The collector independently reproduced exactly:

- `36` added leaves
- `9` modified leaves
- `0` removed leaves

The nine modified paths and old -> current blobs are:

1. `.github/workflows/ci.yml`: `ee7d5dee4b7aafb2601a25fbbe5d789ab4627687` -> `9a4e944d322b682a1cf61fa0110e69e69c8bb4ba`
2. `AGENTS.md`: `a3c50c14b0fdb18a7aec42bd43310e38ffe34134` -> `f093e904bba52eb8827a90b1024b7d21fa42d500`
3. `docs/agents/policy/ORGANIZATION_AGENT_POLICY.md`: `11f3d8e8f5f2150ae5ccb5c7bfd5d1e6ef2eb04a` -> `6902d9f4f28701d73240fb37a8104cbf349333e0`
4. `docs/agents/policy/PROMPTING_STANDARD.md`: `e9b7804075cb76c9676aca2cd1b2e554dcaff6b2` -> `1f47189ad7859534740ee844c787fa3b248304fe`
5. `docs/agents/policy/PROMPT_EVAL_STANDARD.md`: `1640aca80f0b5e300867499709277fd38b8fa80c` -> `af3e22cd36b3522b603be0c72d645b1b713b86dc`
6. `ecosystem/agent-execution-routing-policy.json`: `7f13ae5c1784a914eddccbb25c0cfb75e21551f7` -> `bd2a0a6cecaa474a6e3bb8902aa2e67be12fc0c1`
7. `ecosystem/organization-agent-policy.json`: `e02ebd429cc53bf53e54a5d5d86b18f51c2f6f73` -> `1bdae7e48a9d3d93bd8f8850b7610840cfeafa10`
8. `tools/governance/central_agent_policy.py`: `ce4da4bcd44306c8ae556e93532fa7724bb86900` -> `def581adb5dd26040ce2943491894908fcd1870d`
9. `tools/governance/test_central_agent_policy.py`: `e22c335e5cbdd2e38aab05bd49d858be96976323` -> `44f9940259f645652cfed0ea5e9595f37e111dcf`

The 36 added leaves divide into two bounded source families:

### Active governance / executable contract family — 10 leaves

- `.github/workflows/governed-merge-queue-executor.yml`
- `docs/agents/contracts/INTEGRATION_CAPABILITY_ROUTING_POLICY.md`
- `docs/agents/operations/MERGE_QUEUE_EXECUTOR.md`
- `docs/agents/programs/OTERYN_MQ_CAPABILITY_ROUTING_20260910.md`
- `tools/governance/governed_merge_queue_executor.py`
- `tools/governance/integration_capability_routing.py`
- `tools/governance/merge_queue_submission_routing.py`
- `tools/governance/test_governed_merge_queue_executor.py`
- `tools/governance/test_integration_capability_routing.py`
- `tools/governance/test_merge_queue_submission_routing.py`

### Repository-audit historical evidence family — 26 leaves

All 26 are under `docs/evidence/repository-audit-2026-09-06/**`, published by protected-main #153. Their presence is current source identity. Their historical assertions are not automatically current runtime/admin/governance truth.

## Fail-closed semantic carry-forward projection

R6 canonical semantic accounting was bound to the old exact blob identities. Of the nine modified leaves, exactly five had old exact-blob DIRECT evidence in the canonical coverage set:

- `.github/workflows/ci.yml`
- `AGENTS.md`
- `docs/agents/policy/ORGANIZATION_AGENT_POLICY.md`
- `ecosystem/agent-execution-routing-policy.json`
- `tools/governance/test_central_agent_policy.py`

The other four modified leaves were already UNVERIFIED in the R6 semantic accounting. No old exact-blob semantic evidence is silently transferred to a changed blob.

Therefore, **before any new current-blob semantic adoption**, the deterministic fail-closed projection is:

- source/archive leaves: `4,361`
- DIRECT: `289`
- GROUPED: `113`
- UNVERIFIED: `3,959`
- semantically classified: `402`
- META: `76 DIRECT / 134 UNVERIFIED` of `210`

This is a projection from verified identity change plus existing exact-blob evidence, not yet the new canonical ledger. The R6 canonical ledger and `4,325 / 294 / 113 / 3,918 / 407` remain historical snapshot accounting until a current-main semantic candidate is reviewed, adopted and the authoritative ledger is rebuilt.

## Next gate

1. Perform bounded full-file semantic review of the 19 active/current governance delta paths (9 modified + 10 added), bound to exact current blobs.
2. Treat the 26 `repository-audit-2026-09-06/**` leaves as a separate historical-evidence family; do not infer present authority from their contents or package name.
3. Build a current-main semantic candidate without double-adopting unchanged R4/R5/R6 paths.
4. Require exact-head validation and fresh independent review before any new DIRECT/GROUPED adoption.
5. Rebuild the canonical 4,361-row ledger only after those dispositions are accepted.

No provider write, production action, secret/environment change, protection/ruleset change, mark-ready, merge, queue or Merge Queue mutation is authorized by this checkpoint.
