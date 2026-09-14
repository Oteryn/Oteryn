# AUDIT186-SEMANTIC-04

## Authority

- Governing issue: `Oteryn/Oteryn#186`.
- Immutable programme authority: `Oteryn/Oteryn#203@82bc113797ecdc70d79aee628d339136b816e15d`.
- Canonical audit baseline: PR #185 exact head `2d877271afa8f177983f3c6147472372adca0ed1`.
- This branch is a worker branch only. `AUDIT186-LEAD` remains the sole writer to canonical #185 accounting/report surfaces.

## Prior semantic batches

- PR #204 exact head `d11bf85619b15fc627adaa889f9f686d74d8a165`: accepted/frozen handoff; proposed `+26 DIRECT / -26 UNVERIFIED` remains `PROJECTION_ONLY` until lead adoption.
- PR #207: rejected/frozen; its proposed `+2 / -2` effect is VOID and must never be counted.
- PR #209 exact head `9ad2942ba0dedb5b94e437c32b85161c6c59885a`: accepted/frozen; selected canonical leaf `docs/ci/CI_CONTRACT.md`; proposed `+1 DIRECT / -1 UNVERIFIED` remains `PROJECTION_ONLY` until lead adoption.

## Bounded mission

Select exactly one next-smallest coherent semantic family from the remaining canonical `SEMANTIC-COVERAGE` UNVERIFIED scope.

Before reviewing semantics, prove for every selected leaf that:

1. it belongs to the released canonical 4,361-leaf source inventory at the recorded provider/META source coordinate;
2. its canonical disposition at PR #185 baseline is exactly `UNVERIFIED`;
3. it is not one of PR #204's frozen 26 historical leaves;
4. it is not `docs/ci/CI_CONTRACT.md` from accepted PR #209;
5. it is not either audit-branch-only path rejected in PR #207.

Do not rebaseline source inventory. Do not classify audit-branch-only files. Do not mutate canonical coverage/accounting/report/README/unknowns/verification-index/collection-plan surfaces. Providers remain read-only.

## Required handoff

Produce one independently reviewable candidate packet containing exact selected path/blob identities, canonical inventory-membership and UNVERIFIED proofs, proposed DIRECT/GROUPED/N-A disposition with scope/depth/limitations, any grouping equivalence proof, adversarial tests, `PROJECTION_ONLY` accounting delta, intentionally unverified claims, and exact recheck triggers. Add only lane-local evidence/verifier/focused tests. Run applicable validation and `git diff --check`. Keep the PR Draft and stop after one bounded family; do not integrate into #185.