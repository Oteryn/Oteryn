# Oteryn organization audit — evidence-reconciled revision R2

**Status: `QUALIFIED_AUDIT_WITH_EXPLICIT_OPEN_SCOPE`.**
**Governing continuation:** META Issue #186, existing PR #185.
**Source acquisition:** 2026-09-07 22:06:16 UTC.
**Product/production readiness:** not claimed. **Independent score:** not assigned.

## 1. Executive opinion

The original report is useful as a programme summary but cannot stand as an exhaustive completion certificate. This revision replaces unsupported completion assertions with immutable source identities, individual finding dispositions, a reproducible path ledger, explicit domain criteria and actual scoped test results.

**Four P1 findings are supported on the pinned main-source snapshots:** Platform change routing, Platform exact-candidate fan-in, Platform email-change delivery durability, and Game's existing PREPARE/COMMIT phase implementation. A separate retired-session nonreuse P1 is reported against unmerged Game PR #361. It is not interchangeable with the Game defect still present on the audited main. These are known findings, not a proof that the entire organization contains only four or five serious risks.

The repository split should be preserved while these finite gaps are addressed. That is a recommendation based on the inspected provider/META boundaries, not a certification of every implementation or a reason to defer a concrete architecture contradiction.

The strongest evidence acquired in this continuation is:

- 4,325 exact leaf identities across four active repositories and one archive; all eight collected source/supporting root trees and 4,641 distinct Git blobs independently hash-verified;
- 76 individually accounted findings/notes/follow-ups, with current-source, candidate, recorded closure, qualification and unknown-live states kept separate;
- 77 active workflow definitions inventoried, with 150 declared jobs; these are not matrix-expanded executions;
- two unsafe routing cases freshly reproduced against exact Platform source, despite the existing tests passing;
- successful focused META, Platform, Game and Atlas checks, with their scope and limitations recorded below.

**Full semantic coverage is still not established.** The new ledger records 65 fresh scoped review entries; other paths retain `UNVERIFIED` in this continuation rather than inheriting an unsupported all-line approval. Some of those paths have useful earlier provider evidence, but that evidence must retain its actual scope and source validity. This is not a claim that every such file was never audited. The remaining semantic and live-state work is named, counted and assigned to existing programme routes, not hidden behind `COMPLETE`.

## 2. Immutable scope and coordinate correction

| Repository | Source commit | Root tree | Leaves |
|---|---|---|---:|
| META | `1a01c5b3e08666a82245b1cac78da3736c65e785` | `f084e824ec5e14d5909c9750d906d91d51425fd5` | 174 |
| Game | `4d6139083179b8fd8c5d0497b2abf8c2545de599` | `49cabfccf7d4876e5bc9276fc5963caa33dab8a5` | 830 |
| Platform | `de917b3477a1de0667531380de3660e8b2ab59aa` | `ffdf2a286d3a39f2344cf2ff53b28e4ef7369a8e` | 2,165 |
| Atlas | `f00815858bb5b031c502ad19fb96a05ff66b4d84` | `a1009378f8d3950a5ee62fb3ee65041f7d53a1e0` | 1,155 |
| Migration archive | `6da4f83ef6a35afbab3332f90d7c7f171d23d235` | `dbf8349a21e432df47d1475b8431939bbe94d6e1` | 1 |

The active-repository total is **4,324**, plus the one archive evidence file. The archive is provenance, not an active product.

The original Game commit `3327db49c0c3e2d90afe6a74954c579a36aba2a5` could not be resolved: hosted Git fetch failed, and the native GitHub Git-commit endpoint returned 404. The repository's main ref and replacement commit/tree above resolved and were independently verified. The reason for the original bad coordinate is **unknown**; no intent, fabricated-work allegation or simple upstream-movement explanation is inferred. Claims attached to the old coordinate are not silently carried forward.

Supporting audit publications remain separately pinned:

| Source | Publication commit | Use |
|---|---|---|
| META PR #153 | `eae38fa0963bd3b6ebb5e090f079944b5a1892db` | 14 historical findings; prior 78-path source generation |
| Game PR #360 | `d8a69a2fda51a8882c2e0d9bae61204f9cde163b` | 20 calibrated findings and phase-aware controls |
| Platform PR #1294 | `3fe7df5330deb9ed38cc17ae1710f0cb4159019b` | 16 findings plus unresolved H02; expressly incomplete audit |
| Atlas PR #342 | `0f62cba3fdbb56af0a01ae7c0b4587b66d1923fc` | F01–F16; historical audited main `5ea38a62...`, denominator 1,140 |

Atlas's historical 1,140-path count is not reused as the current 1,155-path denominator. Publication-branch audit files are also not mistaken for product files added to or removed from main.

## 3. Method, assurance levels and limits

The evidence model distinguishes **direct source inspection**, **executed controlled reproduction**, **executed scoped regression**, **recorded upstream closure**, **inference**, and **unknown**. A prior assertion is not upgraded simply because it appears in an Issue body or a newer report.

`DIRECT` in the path ledger means the recorded property or source range was inspected. It does not assert all-line review of a large source file. Unmatched paths remain `UNVERIFIED`; no ordinary authored runtime code is hidden under a generated-data grouping. Automated tree enumeration and YAML parsing establish inventory properties, not behavioral correctness.

An unchanged blob supports carrying forward a fact about that blob. It does not automatically preserve a system-level result when callers, dependencies, configuration, workflow selection, accepted contracts or mutable lifecycle state have changed. The expanded delivery records old/current source identities for the Game finding paths; changed or uncertain items remain explicit.

Priority is engineering triage, not CVSS. Closed historical P1 rows retain their original priority for traceability but do not count as current defects. `NOTE` and `UNRATED` are not zero risk. A four-entry current-main P1 list is not an exhaustive organization-wide severity census.

No provider files, runtime state, deployment, credentials, secret values, protected settings or provider Issues were mutated by this audit. The temporary META hosted collector used read-only public source fetches and was removed after acquisition. It is not a permanent workflow or a new required gate.

## 4. Material corrections to the original report

| Original problem | R2 disposition |
|---|---|
| Unresolvable Game source coordinate | Corrected with explicit failure history and verified replacement; no silent carry-forward. |
| Platform incompleteness described only as a numeric-export limitation | Exact 2,165-path inventory now exists. Remaining semantic review is still explicit, not explained away as counting. |
| A–W labelled audited without per-domain criteria/evidence | 23-row matrix now specifies criterion, method, opinion, remaining limit and references. |
| Historical/current finding reconciliation asserted complete without a map | All 74 identified historical source IDs plus two follow-ups have individual dispositions and closure conditions. Unknown outcomes stay unknown. |
| Game main defect and unmerged repair-candidate defect conflated | `GAME-F20` and `GAME-CANDIDATE-361` are separate scope-qualified rows. |
| Atlas F01–F16 closure presented without separate follow-up context | Existing #376 routing and #343/#344 UI acceptance obligations are retained; restoration remains paused. |
| Recovery summarized largely as migration provenance | Seven GAP-RECOVERY IDs from #59 are individually retained, including metadata, packages, secret-recovery governance and current production restore. |
| Approximate workflow count and broad cost recommendations | Exact static census supplied; performance/cost savings remain unmeasured. |

## 5. Current main-source P1 register

### PLATFORM-F16 — runtime change can become docs-only

**Evidence:** `scripts/ci/classify_changes.py`, blob `8f194c0c0a9967d9dc8dc3fbe228984e56b8f82a`; `scripts/ci/required_test_gate.py`, blob `3d61ff97df7fdfed01bb2ef3104aeff7b7f4e3bf`, at the Platform source cut.

The classifier consumes `git diff --name-only --diff-filter=ACMRD`. A type change can be excluded, and a rename can lose the original runtime path. Fresh temporary Git repositories reproduced both **runtime regular-file to symlink plus docs edit** and **runtime-to-docs rename plus docs edit** as `ci=false`. Feeding those successful classifications and skipped runtime status to the real gate CLI returned exit zero and `NOT_APPLICABLE`.

All 28 declared routing fixtures passed. All 29 existing tests in the two executed Platform files passed. The eight real-Git cases produced six expected routing decisions and two false negatives. This is evidence of a missing test/selection contract, not evidence that a malicious protected merge or production incident occurred.

**Closure:** preserve status and both rename/copy sides using a NUL-delimited diff; handle type/mode/symlink transitions; reject unsupported or incomplete status input; retain real Git boundary-crossing and passing-control fixtures. Historical H01 is an alias of F16, not another finding.

### PLATFORM-F01 — required aggregate does not prove every selected profile

**Evidence:** `.github/workflows/ci.yml`, blob `2943cfc2220a6ddd72c99336500f2ef339d23b84`; `game-gateway-ci.yml`, blob `4457167367a8ab20fbf81b18ab1663930450126c`.

The current `platform-gate` depends on classification and the core test aggregate. The separately defined Gateway workflow handles PR/push, not `merge_group`; the source classifier deliberately leaves Gateway work outside its five core gate flags. Thus the required aggregate is not, by itself, proof that all material Gateway qualification succeeded on the exact Merge Queue candidate.

**Closure:** use one impact-class-to-profile contract for PR/MQ selection and one stable terminal aggregate. Required failure, cancellation, missing execution or unjustified skip must block. Explicit N/A must be justified. Do not replace selective correctness with running every heavy workflow for every change.

### PLATFORM-F02 — durable security operation, non-durable notification delivery

**Evidence:** `app/Identity/Email/RequestIdentityEmailChange.php`, blob `06f81e0db11405233b15f056dc3d7cb1cd35e133`, transaction at lines 30–81 and subsequent notifications at 83–86; the two current notification classes were inspected.

The request commits security state, then sends the verification and old-address messages separately. A transport failure can leave committed state and partial delivery. `Queueable` on the notification classes is not proof of a transactionally coordinated durable per-message delivery model. **Live SMTP/DB fault injection was not performed.**

**Closure:** transactional outbox or equivalent; one durable intent per message, idempotency, delivery state, bounded retry/backoff, terminal/dead-letter handling and restart safety. Test first/second-message failure, crash after commit, retry, expiry and revocation.

### GAME-F20 — accepted PREPARE semantics are not implemented on the source cut

**Evidence:** `apps/game-server/src/foundation/admission_recovery_inner.rs:4281–4338`, `admission_authority_publication.rs:2300–2314`, and accepted terminal replacement decision §3.2 at lines 181–239. These three source identities are unchanged from the historical finding.

The effect projection initially copies the predecessor session/claims. Successor identity/claims changes and mutations of the original commit occur under `if commit`; final current-claim validation expects predecessors. The accepted model requires predecessor fencing and successor actor-anchor establishment at PREPARE without premature controller activation, with immutable original provenance preserved.

This is a source-level contradiction in an additive, unactivated bridge, not an allegation of live data corruption. The existing repair is Game #353 / PR #361, coordinated through #364/#162. Rust/native recovery execution was not repeated in this environment.

**Closure:** independently sourced PREPARE successor/fencing evidence, COMMIT-only activation, immutable historical receipt, lost-response/reload/replay/predecessor-negative tests and exact-candidate integration proof. Do not compensate by inventing authority in SQL or Server Seam.

## 6. Candidate-only and remaining historical work

The complete machine register is [finding-register.tsv](organization-audit-20260907/finding-register.tsv). It contains evidence and a measurable closure condition for every row, not just titles.

**Game #361:** its recorded retired-session nonreuse P1 requires full persisted/reloaded authority across `S0 → S1 → S2 → reject S1`. The Issue/PR history is not a fresh acceptance review of every later candidate head. It remains separate from F20 on main. WP3, WP4, real authority producers and G0/G1 remain programme obligations, not implicitly completed by WP1 or component tests.

**Repaired source is not all unqualified work.** Current Game PKCE, shell error handling, AI uniqueness and Ability magnitude deltas were inspected. Current semantic dispatcher tests passed. WP1's upstream closeout records exact protected PR/MQ evidence. These facts are retained instead of reopening already repaired defects. They do not establish a current native product/G1 run.

**Platform** retains individual P2 rows for Gateway deadlines/shutdown, image provenance/context/publication dependency, coverage baseline, setup, recovery input and lifecycle/governance evidence. H02 login/revocation interleaving is a hypothesis requiring a controlled reproduction, not an invented confirmed vulnerability.

**Atlas** current Issue #315 records F01–F16 protected remediation complete and restoration paused. Fresh isolated regressions provide additional scoped evidence for canonical identity, output safety, cache/read/path behavior and CDP deadlines. Other closure rows explicitly say `REPORTED_CLOSED`. #376 remains separate routing debt; #343/#344 is actual product/UI acceptance work. Neither is cancelled by F01–F16 closure.

**META recovery #59/#60:** the latest retained handoff reports repository backups implemented but not freshly requalified here; metadata/package recovery and independent secret recovery remain open, a second recovery identity needs owner disposition, and current production restore/RPO/RTO are unproven. Already terminal GAP007 is not reopened. No secret values or host state were accessed.

## 7. CI/test/build inventory and cost opinion

| Source | Active workflows | Declared jobs | Workflows with `merge_group` |
|---|---:|---:|---:|
| META | 2 | 4 | 1 |
| Game | 17 | 41 | 1 |
| Platform | 55 | 100 | 1 |
| Atlas | 3 | 5 | 2 |
| Total | **77** | **150** | **5** |

Every file is listed with its blob SHA, trigger names and declared job count in [workflow-inventory.tsv](organization-audit-20260907/workflow-inventory.tsv). Parsing success is not semantic acceptance. Job totals do not count expanded matrices, repetitions or paid runner minutes.

The inspected Platform build workflow now separates staging dispatch from remote deployment duration, but image `build` still has no dependency on `validate-deployment`; the later `deploy-staging` job depends on both. This narrows the old sequencing concern without claiming it disappeared. Root `lang/**` is absent from relevant image path filters, and root `.dockerignore` is absent from the exact source inventory.

Dependabot definitions cover META Actions/Python, Game Actions/Cargo, Platform Composer/acceptance npm/Actions, and Atlas Actions/npm. The inspected Go module currently has no external module requirements. These are declared update scopes, not a fresh CVE scan or proof that every toolchain is supported and safe.

**No quantified savings are claimed.** A recommended measurement baseline should distinguish PR, MQ, push and deployment activity and capture invocation count, queue/run p50/p95, capacity/billable minutes, cache/artifact reuse, retry/flakiness, failure yield and routing false positives/negatives. A representative cohort and its exclusions must be stated. R5Q explicitly did not measure actual API billing tokens, cost or wall-clock savings.

## 8. Executed verification and what it does not prove

| Check | Observed result | Boundary |
|---|---|---|
| Bounded collector tests | 18 passed, locally and on hosted acquisition | Collector safety/accounting, not provider semantics |
| Source acquisition | Initial Game-coordinate failure retained; corrected run `34165469839`, artifact `10033995995` acquired | Public immutable source only |
| Independent integrity | 4,641 blobs and 8 collected root trees verified | Identity, not correctness |
| META source checks | Nine recorded commands exited zero | Routing/governance/schema behavior; release validator explicitly reported zero manifests and unauthenticated provider evidence |
| Platform existing checks | 17 + 12 tests passed | Includes four workflow-contract tests omitted from the older focused run |
| Platform real-Git probes | 8 cases; 2 false negatives reproduced | No real merge bypass or production operation attempted |
| Game dispatcher/oracles | 37 tests passed | Python dispatch/source assertions, not a Rust build or G1 |
| Atlas focused tests | 27 Node + 6 Python tests passed, no skips | Injected local fixtures; no restored workflow, real browser, publication or deployment |
| Audit accounting validator | 21 positive/adversarial tests passed; full tree/ledger validation passed | Rejects unsupported completion, candidate/main conflation and count tampering; not an independent semantic reviewer |

Environment: Python 3.13.5, Git 2.47.3 and Node 22.16.0. Local PHP 8.4.23 is **not** Platform's required PHP 8.5; Rust was unavailable. No unsupported-version runtime success is relabelled as canonical qualification.

Commands, source identities and log hashes are in [verification-index.json](organization-audit-20260907/verification-index.json). Full logs, expanded findings, source inventories and the complete CSV ledger accompany the audit-only delivery. The temporary acquisition artifact expires; reproducibility does not rely solely on that artifact. Source pins, collection plan, scoped review rules and the ledger digest are retained in the repository.

The ordinary PR `meta-gate` remains a separate integration check. A green gate does not certify the report's coverage or substantive claims.

## 9. Domain closeout and explicit unknowns

[domain-matrix.tsv](organization-audit-20260907/domain-matrix.tsv) contains **all 23 A–W rows**, each with an acceptance criterion, actual method/evidence, opinion, remaining limitation and references. Domains are not globally marked PASS merely because their names appear.

Current scoped failures occur in architecture/implementation, persistence, reliability, tests/CI and documentation. Performance/cost is unmeasured; full infrastructure/admin, portability and actual product/UI acceptance remain unverified or unqualified. Other domains have qualified, bounded opinions rather than blanket assurance.

[unknowns.json](organization-audit-20260907/unknowns.json) names 15 residual obligations, why evidence is missing, the effect on this report, the existing owner route and closure criteria. They include accessible-but-unreviewed semantics and unresolved historical outcomes as well as genuinely unavailable admin/runtime/billing evidence. **Accessible work is not falsely described as an access failure.**

Root licence-file inventory alone cannot establish legal compliance, asset rights or a complete privacy posture. Intended META/Atlas terms and third-party data/asset provenance require explicit owner disposition and appropriate review; no legal-compliance certificate is implied.

## 10. Prioritized continuation without a new competing programme

| Workstream | Existing authority route | Exit evidence |
|---|---|---|
| Finish audit semantic/history coverage | META #186/#153 and provider audit lineages | Exact prior ledger adoption/delta validity, remaining authored-family review, individual uncertain finding dispositions; no invented zero-unverified count |
| Platform verification integrity | Platform #451 / existing CI owners | Real-Git boundary suite, complete impact/profile mapping, exact PR/MQ fail-closed fan-in |
| Platform identity durability | Platform #451 / identity owner | Transactionally durable per-message state and real failure/restart/expiry/revocation qualification |
| Game authority/recovery/G1 | Game #364/#162, #353/#361 and existing WP3/WP4 allocations | Accepted phase model, complete retired authority, real producers and native durable journey; existing path custody retained |
| Atlas routing/restoration/UI | Atlas #315/#376 and #343/#344 | Applicable owner authority, minimum truthful data capability, shadow/canary only when resumed, actual UI acceptance; no old-stack wholesale restoration |
| Recovery and operations | META #59/#60 and provider operations | Independent data/metadata/artifact recovery, safe ownership, current release restore/rollback and measured RPO/RTO |
| Measured cost and supply-chain follow-up | Existing provider CI/security and META instruction programmes | Baselines, valid experiments, advisory/SBOM/provenance/rights records; no claimed savings from source-byte counts alone |

Independent, admitted work can proceed concurrently where coordination cost is justified. Acceptance dependencies are not a reason to stop all unrelated useful work, but this audit does not allocate a second writer or release retained product/control-plane restrictions.

## 11. Acceptance of this report

This revision is a verifiable evidence package, **not a self-awarded 10/10 or an exhaustive organization completion claim**. Before an independent reviewer can accept exhaustive completion, the remaining semantic coverage, uncertain historical dispositions and material domain evidence must be resolved or explicitly excluded by an approved scope. An author cannot erase those obligations by renaming the verdict.

The report validator checks bookkeeping and rejects several known overclaims. It cannot decide whether arbitrary source prose is true. Independent review must inspect the stable material head, trace critical claims to their exact evidence, challenge sampling and exclusions, verify source-versus-candidate separation, and check that no unqualified product or merge authority is inferred.

## 12. Source index and reproduction

Canonical evidence routes:

- META #153: `docs/evidence/repository-audit-2026-09-06/OTERYN-REPOSITORY-AUDIT-COMPLETED-R2-20260906.md` and R4 closeout, at the publication commit above.
- Game #360: `docs/agents/reports/repository-audit-20260906/findings.json` **and** `assessment.json`; use the calibrated F01–F20 set, not only the earlier 17-row file.
- Platform #1294: original report, continuation and `docs/testing/OTERYN_PLATFORM_REPOSITORY_AUDIT_2026-09-07-CHECKPOINT.md`; incomplete source coverage is not silently completed by this report.
- Atlas #342: `docs/evidence/repository-audit-2026-09-06/round-4/FINDINGS.md`; live milestone/authority is #315, with #376 and #343/#344 separate.
- Game #364: current protected WP1 closeout comment `5575092954`; recorded candidate-specific nonreuse review `3948631113` belongs to #361.
- Recovery #59: handoff comment `5560023706`; archive `RECOVERY_EVIDENCE.md` at the archive source cut is transfer provenance, not current DR.

Reproduce the accounting and complete ledger using the approved read-only acquisition plan and `tools/audit/verify_report.py`; rerun the bounded real-Git finding with `tools/audit/reproduce_platform_routing.py`. Exact commands and boundaries are in the evidence directory README. No command restores Atlas verification, authenticates private production or weakens a required gate.

**Authority:** provider implementation and live lifecycle remain canonical in provider repositories. Source/configuration/consumer/lifecycle changes can invalidate a prior result even when one inspected blob is unchanged. Refresh the affected facts before any later implementation or integration decision.
