# Oteryn META — repository audit, current revision R4

This directory is inert audit evidence, not an agent policy, skill, permission grant or implementation plan to execute automatically.

Start with [the R4 current-main delta closeout](OTERYN-REPOSITORY-AUDIT-R4-CURRENT-MAIN-DELTA-CLOSEOUT-20260907.md). It promotes the audit baseline to current protected `main@d0d5a54c5f06db9423d14b17e7f8eadefd15c6fb` after auditing the complete one-commit delta from R3. Then read [the complete R3 report](OTERYN-REPOSITORY-AUDIT-COMPLETED-R2-20260906.md) for the full findings, architecture assessment and remediation roadmap. Its filename remains stable for existing links; its content is revision R3.

[The original prompt](AUDIT-PROMPT-ORIGINAL.md) is preserved unchanged. [The compliance matrix](PROMPT-COMPLIANCE-MATRIX.md) reconciles that original prompt step by step, and [the R3 change log](CHANGELOG-R3.md) records the corrections to R2.

## Revision boundaries

- Audited repository: `Oteryn/Oteryn`.
- Full R3 audit baseline: `0c493896040072badeff1f333eb83d7114a993ff`, tree `77c33f4c2d3bffcd5983e35928d870d618cb5f68`.
- R4 current baseline: `d0d5a54c5f06db9423d14b17e7f8eadefd15c6fb`, tree `1d723da118fb72ad7dd6b39e3e39a3d4284d18a8`.
- R3→R4 delta: one commit, one modified path, 21 additions and no path additions/removals.
- Current coverage: 78 tracked paths; R3 cumulative direct inspection plus complete R4 delta inspection, not a claim of defect-free code.
- Publication uses existing PR #153. It does not implement recommendations or merge the PR.
- `PUBLICATION-RECEIPT.json` records the R3 material commit and its successful exact-head publication CI without embedding the later receipt commit itself.

## Evidence map

| ID | File / meaning |
|---|---|
| R4 | `OTERYN-REPOSITORY-AUDIT-R4-CURRENT-MAIN-DELTA-CLOSEOUT-20260907.md` — formal current-main baseline transition and disposition of #152 |
| E01 | `evidence/live-governance-readback.json` — historical structured transcription of returned settings, not raw signed API data |
| E02 | `evidence/workflow-inventory.json` — source workflows, backend records and retained history |
| E03 | `evidence/ci-run-index.json` and `evidence/ci-meta-times-{1,2,3}.csv` — 268 indexed runs and 165 exact META timing/head rows |
| E04 | `evidence/prior-native-verification.json`, `evidence/prior-linux-bounded.log` — prior actual native verification; not represented as repeated in R3/R4 |
| E05 | `evidence/instruction-sources.json` — scope, full entrypoint/invocation metadata reads, hashes, limits |
| E07 | `evidence/current-work.json` — work state at the historical R3 snapshot, not a substitute for future readback |
| E08 | `evidence/ci-recalculation.json`, `evidence/coverage-reconciliation.json` — independently recomputed counts, statistics and R3 inventory |
| E09 | `evidence/native-probe-results.json` — seven diagnostic invocations of unchanged validators, exact inputs/output/exit codes |
| E10 | `evidence/revision-provenance.json` — R3 source revisions, original-prompt identity and correction map |
| E11 | `PUBLICATION-RECEIPT.json` — R3 material commit/tree, exact-head `meta-gate` receipt and publication boundary |

`VERIFICATION-SUMMARY.md` distinguishes historical execution, fresh diagnostics and publication checks. `REPRODUCE.md` gives safe isolated reproduction instructions. `COVERAGE-LEDGER.md` contains every R3-audited path and immutable source locator; R4 records the one blob replacement required to reach current `main`.

The public evidence excludes private host identifiers, absolute user paths, credentials and machine-specific configuration values. Security implications and limits remain in the report. No claim of 100% coverage of all clients, infrastructure, production, secrets history or hypothetical defects is made.
