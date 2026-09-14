# AUDIT186-SEMANTIC-01

Governing Issue: Oteryn/Oteryn#186
Canonical audit PR: Oteryn/Oteryn#185
Released baseline: `1008886c0aec2db6b8588a3131a83829eff06e67`
Released baseline tree: `9f32fb6a2debb09483bab478e1ec2d5a05cbf9db`
Programme authority: `Oteryn/Oteryn#203@82bc113797ecdc70d79aee628d339136b816e15d`
Release checkpoint: Issue #186 comment `5666964258` (`AUDIT186_PARALLEL_RELEASE_READY`)
Lane: `AUDIT186-SEMANTIC`

## Mission
Reduce `SEMANTIC-COVERAGE` UNVERIFIED scope through one bounded, coherent semantic family. Start with the 26 historical leaves under `docs/evidence/repository-audit-2026-09-06/**` only if they can be qualified strictly as inert historical provenance without converting historical assertions into current runtime truth. If that family cannot be qualified cleanly, leave it UNVERIFIED and select the next smallest coherent family.

## Current boundaries
- Provider repositories are read-only.
- Historical pinned audit evidence remains historical; current-main claims require explicit rebind/revalidation.
- Current provider main coordinates at release: Game `775a09091743af395ecb8f1e440cb9c286bc0dd2`, Platform `84d504c98acc8134eb4c9545711010b74c987974`, Atlas `bf57f1ca5193112dc8d1951638c300e167032010`.
- Do not mutate canonical audit accounting/report/README/coverage-summary/coverage-review/coverage-groups/unknowns/verification-index/collection-plan surfaces. Those remain lead-only.
- Lane output may add lane-specific candidate/revalidation evidence, verifier code and focused tests on this branch only.
- Current canonical accounting before this candidate is `4361 / 309 DIRECT / 113 GROUPED / 3939 UNVERIFIED / 422 classified`; META is `96 DIRECT / 114 UNVERIFIED`.
- The later semantic-03 overlay contains only `meta\tdocs/ci/CI_CONTRACT.md`; it does not overlap or adopt any of this family's 26 historical leaves, which remain canonically UNVERIFIED.
- Any accounting effect is `PROJECTION_ONLY` until adopted by `AUDIT186-LEAD`; the conditional projection is `4361 / 335 DIRECT / 113 GROUPED / 3913 UNVERIFIED / 448 classified`, with META at `122 DIRECT / 88 UNVERIFIED`.
- No product readiness, runtime readiness, organization-wide completion, merge, queue, mark-ready, protection/ruleset, secrets/environment, production or provider mutation authority.

## Required handoff
Produce one independently reviewable bounded packet containing exact baseline/source coordinates, exact path/blob set, proposed disposition, review depth/scope/limitations, GROUPED equivalence proof when applicable, negative/adversarial tests, projected accounting delta, paths intentionally left UNVERIFIED, and exact recheck triggers. Stop after one coherent family is complete and hand it to `AUDIT186-LEAD`; do not append unrelated families merely to enlarge the batch.
