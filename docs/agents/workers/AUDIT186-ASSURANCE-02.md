# AUDIT186-ASSURANCE-02

Governing Issue: Oteryn/Oteryn#186
Canonical audit PR: Oteryn/Oteryn#185
Released baseline: `2d877271afa8f177983f3c6147472372adca0ed1`
Programme authority: `Oteryn/Oteryn#203@82bc113797ecdc70d79aee628d339136b816e15d`
Prior HISTORY-REVALIDATION packet: `Oteryn/Oteryn#206@bc3c3339fe2ff39769872d843edf149bd56ff154` (frozen; final independent review still gates adoption)
Lane: `AUDIT186-ASSURANCE`
Obligation: `COST-CI`

## Mission
Produce exactly one bounded `COST-CI` assurance packet. Build a representative recent PR / merge-queue / push cohort and determine only what current CI cost, queueing and efficiency behavior can actually be supported by the observed data.

Canonical closure intent: collect a representative recent PR/MQ/push cohort with explicit sample criteria and timestamps, and record queue time, run time, capacity, cache behavior, retries and useful verification yield before asserting cost or efficiency conclusions.

## Boundaries
- GitHub/provider surfaces are read-only. Do not mutate workflows, runners, queue, protection, repository settings or provider state.
- State exact sampling window, inclusion/exclusion criteria, source coordinates and observation time.
- Separate observed facts from estimates. Do not infer cost savings, flake rate, queue health or runner capacity from incomplete timing data.
- Do not treat missing runs/checks as success, zero cost or zero retry.
- Do not mutate canonical audit report/accounting/README/coverage-review*/coverage-groups/coverage-summary/unknowns/verification-index/collection-plan surfaces.
- Add only obligation-specific evidence, bounded verifier/test support and methodology artifacts on this worker branch.
- No merge, queue, mark-ready, provider/admin/runner/protection/ruleset mutation authority.

## Required handoff
Record exact sampled run/PR/MQ/push identities and timestamps; sample-selection criteria; queue/run/capacity/cache/retry/yield observations; missing-data limitations; what is PROVEN versus UNKNOWN/BLOCKED; and exact recheck triggers. If available evidence cannot support a representative cohort, keep `COST-CI` open and state the smallest additional observation required. Keep PR Draft and hand off to `AUDIT186-LEAD`; do not integrate into #185.