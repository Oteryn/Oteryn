# Oteryn/Oteryn — repository audit R4 current-main delta closeout

## Status

`COMPLETE_WITHIN_ACCESSIBLE_SCOPE`

R4 promotes the completed R3 audit from the historical baseline `main@0c493896040072badeff1f333eb83d7114a993ff` to the current protected `main@d0d5a54c5f06db9423d14b17e7f8eadefd15c6fb` by auditing the complete intervening delta. R3 remains the full body of the audit; this file is the formal current-main closeout and must be read with `OTERYN-REPOSITORY-AUDIT-COMPLETED-R2-20260906.md`.

This is audit evidence, not implementation authority. It does not apply any remediation finding or change repository settings.

## Baseline transition

| Coordinate | R3 baseline | R4 current baseline |
|---|---|---|
| `main` | `0c493896040072badeff1f333eb83d7114a993ff` | `d0d5a54c5f06db9423d14b17e7f8eadefd15c6fb` |
| tree | `77c33f4c2d3bffcd5983e35928d870d618cb5f68` | `1d723da118fb72ad7dd6b39e3e39a3d4284d18a8` |
| tracked paths | 78 | 78 |

Git comparison proves that the transition is exactly one commit and one modified tracked path, with no path additions or removals:

- commit: `d0d5a54c5f06db9423d14b17e7f8eadefd15c6fb`;
- source PR: `#152`;
- path: `docs/agents/contracts/BOUNDED_AUTONOMOUS_EXECUTION_POLICY.md`;
- old blob: `eae71b5fcf7adba37544387ac2b2a63ba9c004c2`;
- new blob: `90aaec728d0bf3f3e7e3a18b44cd61c063ba0085`;
- diff: 21 additions, 0 deletions.

No Python, JSON policy, GitHub Actions workflow, test source, release schema, provider coordinate, CODEOWNERS file, or product/runtime file changed between the two baselines.

## Delta assessment

The added section is `No fixed worker runtime boundary`. It establishes that elapsed time, including `60 minutes`, `120 minutes`, an `execution window`, or remaining productive minutes, is not by itself a generic stop, worker-rotation, task-split, re-admission, or fresh-grant condition. It preserves finite timeouts for individual commands and bounded wait/no-progress detection, and classifies historical fixed-runtime values as provenance rather than current execution authority.

### Classification

**FACT:** the delta changes only the bounded-execution human contract and adds the rule described above.

**INFERENCE — high confidence:** the delta reduces one class of instruction ambiguity and is directionally consistent with the R3 instruction-debt recommendation to prevent historical execution wording from silently becoming current authority.

**FACT:** the delta does not repair the separate active late-integration conflict recorded under AUD-05. `AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md` still contains a generic merge-up refresh requirement, while ADR 0005 assigns integration freshness to GitHub Merge Queue and specifies a moving-base canary where the stable PR head is not merged/rebased merely because `main` advanced. AUD-05 therefore remains current.

**FACT:** the delta does not touch the implementation surfaces behind AUD-01, AUD-02, AUD-03, AUD-04, AUD-07, AUD-10, or AUD-11 and does not change live repository settings behind AUD-08/AUD-09. Those findings therefore remain unresolved unless later live work independently changes them.

## Impact on R3 findings

No R3 finding is invalidated by #152 and no new actionable R4 finding is introduced.

- **AUD-01** branch/worktree identity: unchanged.
- **AUD-02** release-schema enforcement: unchanged.
- **AUD-03** orphan AI-review compatibility path: unchanged.
- **AUD-04** duplicated prose enforced by tests: unchanged.
- **AUD-05** superseded/historical instruction debt plus active merge-up conflict: remains; #152 improves runtime-stop precedence but does not close the finding.
- **AUD-06** capability mapping tied to named surfaces: unchanged.
- **AUD-07** Windows `python3` harness portability: unchanged.
- **AUD-08** private vulnerability reporting setting: no repository-file delta changes that live setting.
- **AUD-09** code-scanning state: no workflow/config delta adds scanning.
- **AUD-10** empty governance expected scope returns `TARGET`: unchanged.
- **AUD-11** boolean/integer validation inconsistency: unchanged.
- **PR151-01**, **PR151-02**, **PR145-01**: no #152 change touches their evidence or root causes.

The implementation programme must refresh live PRs, Issues and repository settings before acting on any finding. R4 is a current source-tree baseline, not a substitute for future live-state readback.

## A–W domain delta reconciliation

The path set is unchanged, so the R3 full inventory remains valid after replacing the one bounded-policy blob with its current blob. Domains A–W remain accounted for. #152 materially changes only instruction/documentation and execution-policy interpretation surfaces (primarily P/Q, with implications for H/R). It does not add a new runtime, service, test system, build system, dependency, deployment path, data store, API, workflow, or user-facing product.

The final domain status therefore remains:

- A–U and W: `AUDITED` through R3 plus this complete delta;
- V: `N/A` because META is not a user-facing product UI.

## Verification and limits

R4 used the exact Git compare between the R3 baseline and current `main`, inspected the full one-file commit delta, and checked the added terminology against the current default branch. The current `main` was re-read before publication and remained `d0d5a54c5f06db9423d14b17e7f8eadefd15c6fb`.

The unchanged limitations from R3 remain limitations rather than hidden PASS results: runtime instruction-loading traces across all clients, transport/scheduler enforcement, every possible merge bypass, production/NAS restore, complete secret/CVE history, organization-wide account/runner permissions, billing/model A/B, and every platform/runtime combination.

## R4 final reconciliation

- Current source baseline known: **yes** — `main@d0d5a54c5f06db9423d14b17e7f8eadefd15c6fb`.
- Complete R3→R4 Git delta accounted for: **yes** — one commit, one modified tracked path.
- Current tracked path set accounted for: **yes** — unchanged 78 paths; one blob identity updated.
- New build/test/CI/runtime system introduced by the delta: **no**.
- Existing findings invalidated: **no**.
- Existing finding materially narrowed: **AUD-05 only in the fixed-runtime subtopic; the finding itself remains open**.
- New R4 finding required: **no**.
- R3 limitations still explicit: **yes**.

## Current audit authority

For repository-source conclusions after this closeout, use:

1. this R4 delta closeout for the current baseline and delta disposition;
2. `OTERYN-REPOSITORY-AUDIT-COMPLETED-R2-20260906.md` (content revision R3) for the full audit, findings and remediation roadmap;
3. `PROMPT-COMPLIANCE-MATRIX.md` and the evidence directory for coverage and reproducibility.

**R4 conclusion:** the complete audit now covers the current protected `main@d0d5a54c5f06db9423d14b17e7f8eadefd15c6fb` within the stated accessible scope. The remediation programme should implement the still-open findings from the R3 report against fresh live state rather than re-auditing the old baseline.