# AUDIT186-SEMANTIC-03

Governing Issue: Oteryn/Oteryn#186
Canonical audit PR: Oteryn/Oteryn#185
Released baseline: `2d877271afa8f177983f3c6147472372adca0ed1`
Programme authority: `Oteryn/Oteryn#203@82bc113797ecdc70d79aee628d339136b816e15d`
Accepted prior packet: `Oteryn/Oteryn#204@d11bf85619b15fc627adaa889f9f686d74d8a165` (`+26 DIRECT / -26 UNVERIFIED`, still PROJECTION_ONLY)
Rejected prior packet: `Oteryn/Oteryn#207@44f3dc7a68a283d3fbb56b14816a95026cf32529` (projection VOID)
Lane: `AUDIT186-SEMANTIC`

## Mission
Select exactly one next-smallest coherent semantic family from the remaining canonical `SEMANTIC-COVERAGE` UNVERIFIED population.

Before any semantic qualification, prove for every selected leaf that:
1. the path and blob belong to the released canonical source inventory at its repository/source coordinate;
2. the leaf is part of the canonical 4,361-leaf accounting population;
3. its current canonical disposition is `UNVERIFIED` (not DIRECT/GROUPED and not an audit-branch-only addition).

A path that cannot satisfy all three predicates is ineligible for this batch. Do not rebaseline source inventory merely to create work.

## Boundaries
- Exclude the 26 historical leaves frozen in #204.
- Exclude the two audit-branch-only report leaves rejected in #207; their `+2/-2` projection is void.
- Provider repositories are read-only.
- Do not mutate canonical audit report/accounting/README/coverage-review*/coverage-groups/coverage-summary/unknowns/verification-index/collection-plan surfaces.
- Add only batch-specific candidate evidence, verifier code and focused adversarial tests on this branch.
- Any valid accounting effect remains `PROJECTION_ONLY` and must remain separate from the still-unadopted #204 projection.
- No product/runtime/admin/readiness/completion inference; no merge/queue/mark-ready/protection/secrets/provider mutation.

## Required verifier invariants
The verifier must fail closed if a selected path is absent from canonical source inventory, has a different canonical blob, is already DIRECT/GROUPED, is audit-branch-only, overlaps #204, or attempts a source rebaseline. Bind the exact canonical source coordinates/ledger identity used to establish membership and disposition.

## Handoff
Stop after one coherent family. Record exact repository/path/blob set, proof of canonical inventory membership and UNVERIFIED disposition, proposed DIRECT/GROUPED disposition, review depth/scope/limitations, GROUPED equivalence proof if applicable, adversarial tests, projected delta, deliberately unverified claims and recheck triggers. Keep PR Draft and hand off to `AUDIT186-LEAD`; do not integrate into #185.