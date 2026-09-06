# Oteryn META — repository audit, final revision R3

This directory is inert audit evidence, not an agent policy, skill, permission grant or implementation plan to execute automatically.

Start with [the complete report](OTERYN-REPOSITORY-AUDIT-COMPLETED-R2-20260906.md). Its filename remains stable for existing links; the content is revision R3. [The original prompt](AUDIT-PROMPT-ORIGINAL.md) is preserved unchanged. [The compliance matrix](PROMPT-COMPLIANCE-MATRIX.md) reconciles it step by step, and [the change log](CHANGELOG-R3.md) records the corrections to R2.

## Revision boundaries

- Audited repository: `Oteryn/Oteryn`.
- Audited commit: `0c493896040072badeff1f333eb83d7114a993ff`.
- Audited tree: `77c33f4c2d3bffcd5983e35928d870d618cb5f68`.
- Coverage: 78 tracked paths; cumulative direct inspection, not a claim of defect-free code.
- Later main: `d0d5a54c5f06db9423d14b17e7f8eadefd15c6fb` (#152, one documentation change), inspected as a separate delta.
- Publication uses existing PR #153. It does not implement recommendations or merge the PR.

## Evidence map

| ID | File / meaning |
|---|---|
| E01 | `evidence/live-governance-readback.json` — historical structured transcription of returned settings, not raw signed API data |
| E02 | `evidence/workflow-inventory.json` — source workflows, backend records and retained history |
| E03 | `evidence/ci-run-index.json` and `evidence/ci-meta-times-{1,2,3}.csv` — 268 indexed runs and 165 exact META timing/head rows |
| E04 | `evidence/prior-native-verification.json`, `evidence/prior-linux-bounded.log` — prior actual native verification; not represented as repeated in R3 |
| E05 | `evidence/instruction-sources.json` — scope, full entrypoint/invocation metadata reads, hashes, limits |
| E07 | `evidence/current-work.json` — work state at the historical audit snapshot, not a substitute for future readback |
| E08 | `evidence/ci-recalculation.json`, `evidence/coverage-reconciliation.json` — independently recomputed counts, statistics and inventory |
| E09 | `evidence/native-probe-results.json` — seven fresh diagnostic invocations of unchanged validators, exact inputs/output/exit codes |
| E10 | `evidence/revision-provenance.json` — source revisions, original-prompt identity and correction map |

`VERIFICATION-SUMMARY.md` distinguishes historical execution, fresh diagnostics and publication checks. `REPRODUCE.md` gives safe isolated reproduction instructions. `COVERAGE-LEDGER.md` contains every audited path and immutable source locator.

The public evidence excludes private host identifiers, absolute user paths, credentials and machine-specific configuration values. Security implications and limits remain in the report. No claim of 100% coverage of all clients, infrastructure, production, secrets history or hypothetical defects is made.
