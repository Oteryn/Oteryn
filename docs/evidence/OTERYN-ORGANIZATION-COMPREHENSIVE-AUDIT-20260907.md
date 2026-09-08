# Oteryn organization audit — R3 post-review hardening

**Opinion:** `QUALIFIED_AUDIT_WITH_EXPLICIT_OPEN_SCOPE`
**Authority:** existing META Issue #186 / PR #185; provider implementation remains with its owners.
**Production readiness:** NOT CLAIMED. **Independent acceptance/10-of-10:** NOT ESTABLISHED.

R3 preserves the original immutable source cut while adding native Platform evidence, bounded semantic review, later lifecycle observations and a fail-closed correction pass after independent review. It does not relabel a complete inventory as a completed organization audit. The machine-readable companion and registers are canonical for counts; `r3-independent-review-corrections.json` is the explicit correction layer for statements invalidated by the independent review of head `9096edd135d42f31da4824f4c4fb50ee187de2c9`.

## 1. Source identity and actual coverage

The source set remains META@`1a01c5b3e08666a82245b1cac78da3736c65e785`, Game@`4d6139083179b8fd8c5d0497b2abf8c2545de599`, Platform@`de917b3477a1de0667531380de3660e8b2ab59aa`, Atlas@`f00815858bb5b031c502ad19fb96a05ff66b4d84`, plus migration archive@`6da4f83ef6a35afbab3332f90d7c7f171d23d235`. Companion JSON supplies all root-tree identities. Eight acquired current/supporting trees and 4641 unique blobs were hash-verified; source code is not copied here as product authority.

| Source | Tracked leaves | Explicit scoped reviews | Semantics not adopted/established |
|---|---:|---:|---:|
| meta | 174 | 20 | 154 |
| game | 830 | 34 | 796 |
| platform | 2165 | 137 | 2028 |
| atlas | 1155 | 10 | 1145 |
| migration_archive | 1 | 1 | 0 |
| **Total** | **4325** | **202** | **4123** |

`DIRECT` is a bounded review with the stated scope, not full approval of the entire file or every dependency. R2 had 65 scoped entries; R3 adds 137 distinct paths and extends some existing scopes. In particular, R3 reads all 50 Platform migration files and the control fields of all 77 workflow files. It does not claim that every workflow step body was reviewed. All unadopted semantics stay UNVERIFIED; grouping/N/A are not used to inflate coverage. Full CSV is reproducible from immutable inventories, `coverage-review.tsv` and the committed ledger digest.

The original unresolvable Game coordinate `3327db49c0c3e2d90afe6a74954c579a36aba2a5` remains explicitly recorded as a corrected input. Its cause is unknown; no motive or fabricated history is inferred. R2's historical source discussion remains available in this PR at `f9de42c75e25627a424d429434c4922f399965e6`.

## 2. Native evidence actually acquired and rechecked

All six public archives are bound by collector commit, workflow run, artifact ID, archive SHA-256 and inner-file digests in `r3-native-manifest.json`. `verify_r3_evidence.py` re-parses them and fails closed if the recomputed summary differs semantically from committed `r3-native-results.json`.

| Check | Observed result | Essential limit |
|---|---|---|
| PHP Unit/Feature, no-env and empty-env control | Each 618 selected / 614 executed / 4 skipped; 5194 assertions; 0 failures/errors; both exit 0 | Two repetitions of the same identity set, not 1236 distinct tests. |
| Dedicated MariaDB concurrency | Exactly the four skipped identities execute; 4/4, 63 assertions, 0 skips/errors/failures | Together the profiles cover 618 distinct identities; not one all-green full Integration run. |
| PHP PCOV | 14414/17674 statements = 81.55%, 491 files | Branch coverage NOT_MEASURED; report-only policy is not automatically repaired by measurement. |
| Locked Composer audit | 0 advisories, 0 abandoned at recorded execution | Not current all-ecosystem advisory/SBOM/provenance/history clearance. |
| Gateway | 56 top-level tests + 59 nested pass events, 7 packages; race tests, vet, build succeed | 115 is not 115 independent top-level tests. Covered statements 484/602 = 80.40%. |
| Anonymous browser | 12 routes × 4 viewports = 48 cases; 40 HTTP 200 + 8 intended 404 | English synthetic SQLite fixture; no forms/mutations/authenticated/native journeys. |
| Migration setup | Exactly 50 source-bound migration names appear once as `DONE` in the bound fixture setup log | No down/current-data upgrade/production restore qualification. |

PHP run `34169555626` / artifacts `10035282589` and `10035263247` bind the locked native environment. Concurrency artifact `10035749457` comes from run `34171157669`: its concurrency job succeeded while the overall run failed due to the original browser oracle. Do not replace a job result with a whole-run success claim.

The original browser oracle wrongly demanded HTTP 200 from two deliberately unpublished editorial routes (`/support`, `/legal/privacy`) at four widths. Post-review verification now parses that original raw capture rather than merely hash-checking its archive. It requires the exact 48-case matrix and exactly eight stored `http_ok` failures — those two routes at 390/820/1440/1920 — with 404 on those cases, 200 on the other 40, no hidden additional criterion failure and the recorded no-JavaScript login control. Its Node replay is explicitly `REPLAY_OF_CAPTURED_OBSERVATIONS_NOT_NEW_BROWSER_EXECUTION`. The corrected collector `9a1383652aac31f0524f83e2dabf79bace40b73e` / run `34193488547` / artifact `10043048175` verifies the precise 404/missing-editorial state; it is not a general 404 exemption.

The migration execution claim is also fail-closed after review: the verifier reconstructs the exact 50 Platform `database/migrations/*.php` paths/blobs from `coverage-review.tsv`, validates the committed path/blob digest in `r3-migration-review.json`, then requires exactly 50 unique `DONE` names in the bound `migrations.log` equal to that source set. Up execution is synthetic SQLite only; down/current-data/MariaDB production recovery remains unexecuted.

The no-JavaScript login retains visible email/password controls. Tab order was observed, not accepted as a comprehensive accessibility assessment. Eight full-frame screenshots at 390/1440 widths were actually inspected by the audit author with source/result/digest binding in `r3-visual-review.json`. No independent visual approval, complete WCAG/contrast/screen-reader coverage, authenticated flows, Polish UI run, multi-browser or initialized Atlas world acceptance follows.

The earlier chat's broad warning-cause explanation is not adopted: this pinned PHPUnit comparison exits 0 in both conditions and does not explain every earlier Artisan display warning. Experiment identity and setup matter.

## 3. Findings, not inflated risk counts

`finding-register.tsv` accounts individually for **77 records**: 74 historical source IDs plus three explicit follow-ups/additions. A row is not necessarily a new defect; statuses distinguish repaired source, inherited allegations, live metadata, hypotheses/obligations and regressions. Full priority counts are not claimed exhaustive.

Four P1s remain documented on the **pinned source snapshot**, not automatically on later main revisions:

| ID | Scope of evidence | Existing closure route |
|---|---|---|
| GAME-F20 | PREPARE/COMMIT phase and immutable receipt mismatch in the old Game cut | Foundation 353 / PR 361 / Durability 329; later 361 integration recorded separately. |
| PLATFORM-F01 | Required classification/test aggregate does not compose separate Gateway/concurrency profiles on PR/MQ | Platform 451 / audit 1294. |
| PLATFORM-F02 | Email/security transaction and notification delivery do not establish durable per-message delivery | Platform 451 / audit 1294. |
| PLATFORM-F16 | Two unsafe runtime-skip decisions reproduced with actual Git type/rename fixtures | Platform 451 / audit 1294. |

**PLATFORM-F17 (P2):** Announcements' dedicated workflow excludes EN/PL locale files used by its ticker and browser assertions. `r3-trigger-evidence.json` binds six source blobs; eight static probes include four positive controls and four locale-selection counterexamples. This is a dedicated trigger gap, not a fresh Announcements-browser failure or demonstrated bypass of protected merging. Other workflows may still run.

**PLATFORM-H02 security handling correction:** a controlled source-pinned characterization exists. Independent review established that mechanism details were committed in public ancestor commits and exposed in public Actions artifacts. That material must therefore be treated as **already disclosed**. Removing characterization scripts from the final tree does not erase public Git history or restore confidentiality. The current report intentionally does not repeat mechanism/PoC details. Current live reachability, historical artifact deletion/expiry, private-advisory submission and remediation are NOT established. Further assessment/remediation must use the private vulnerability reporting route defined by Platform `SECURITY.md`. Until deletion/expiry is independently verified, historical artifacts must be treated as potentially downloadable/public.

The detailed source review also records what was not established: schema constraints alone do not prove exactly-once delivery; successful fresh-schema up is not reverse migration/data preservation; passing component tests is not full native G1. There is no invented percentage score or arbitrary coverage floor.

## 4. Measured CI observations

`r3-native-results.json` includes an 84-run/418-job cohort collected by `1204831962d9f6ff88ca8984028f6721f63889eb`, run `34194662737`, artifact `10043441892`. It selects the newest 12 completed runs in each of seven workflow strata and their latest attempts, not all workflows for 84 distinct PRs. There are 77 unique repository/event/source candidates and 95 read-only API calls.

Observed conclusions: 50 success, 27 failure, 7 cancelled. The sum of available job durations is 23295 seconds; 16 anomalous negative intervals are retained as UNKNOWN rather than zero. Two Atlas authority runs have no jobs/wall observation. Per-stratum medians/counts are provided instead of disguising heterogeneous runs as a representative global latency.

These data measure a bounded sample, not billing, paid minutes, monetary savings, pure runner queue, cache yield, flake rate, earlier retries or agent tokens. A failure count without attempt/cause qualification is not a flakiness estimate. The first collector failed on a negative timestamp; the repaired collector preserves the anomaly. Post-review hardening additionally makes normal and diagnostic output exclusive-create: an existing result/error file or final-path symlink is refused rather than overwritten/followed.

## 5. Later lifecycle reconciliation

`r3-lifecycle.json` stores fresh native metadata reads on 2026-09-08 separately from the immutable source cut.

Game PR 361 is merged at `3825e9c82ff388923f73548a807718807012f53f`, final candidate `444dddd6f5da6db934781b30615c23867b0381cf`. Its body still contains older draft prose. State/merged/head fields outrank that prose. The historical candidate-only nonreuse allegation is `REPORTED_IMPLEMENTED_NOT_REQUALIFIED`; it is not silently substituted for F20 or alleged freshly confirmed on current main.

Platform 1270 is closed **without merge**, with recorded successor 1304; 1304 is merged at `907546f193e91b0bed2f5f077ab5b874771929ef`. Issue 1267 closure is not inferred. Atlas 376 is closed/completed, but that fact neither restores workflows nor supplies later product acceptance. Provider source/config/consumer changes require scoped revalidation even when an individual inspected blob remains unchanged.

## 6. Independent review correction pass

Independent review of stable R3 head `9096edd135d42f31da4824f4c4fb50ee187de2c9` completed with four P1 and one P2 audit/evidence findings. They are preserved in `r3-independent-review-corrections.json`; author remediation is not itself independent acceptance.

The correction pass does five things:

1. treats the earlier security characterization mechanism as publicly disclosed rather than owner-private;
2. parses and requires the exact eight-case original browser failure signature and explicit legacy replay mode;
3. parses the bound migration log and requires exact name/count/source-ledger equality for all 50 migrations;
4. deep-compares the full raw-archive recount with committed `r3-native-results.json` and fails on semantic drift;
5. creates CI result/diagnostic evidence exclusively, refusing overwrite and final-path symlinks.

Targeted author tests for these repairs pass locally, including negative controls. The six real public archives also pass the prepared fail-closed recount. These facts must be rebound to the actual published post-review head, canonical `meta-gate`, complete diff/readback and a **fresh independent review** before the five prior review threads can be considered resolved.

## 7. Remaining obligations and closure conditions

All 23 A–W domains have a criterion, method, evidence, opinion and limitation in `domain-matrix.tsv`. Fifteen material residual obligations retain explicit owner routes and measurable closure conditions in `unknowns.json`: unadopted source semantics; unresolved historical outcomes; admin and production configuration; current data recovery; representative CI and actual agent costs; broader supply chain; native G1; initialized Atlas UI; OS/runtime portability; telemetry; rights/privacy; disclosed security disposition; independent semantic review.

These are not all access failures. Source bytes and native hosted execution are available. Missing semantic review must be completed or validly imported, not labelled inaccessible. Maintenance does not turn suspended authored code into tested code. No host/deploy action is authorized merely because a tool exists.

Professional completion requires every material scoped obligation to receive a defensible disposition and independent review of the stable candidate. It does not require fixing every discovered product defect inside this META audit. Conversely, an unreviewed source area cannot be called audited merely because its remediation has an owner.

## 8. Reproduction, retention and integration boundary

`README.md` gives offline checks and immutable inventory reconstruction. The expanded CSV, native public archives, relevant logs and author-viewed images are supplied in the audit delivery. GitHub Actions archives have short retention; hashes are not substitutes for unavailable raw bytes. Source inventories remain reconstructible from pinned Git objects.

Additional owner-held security material may exist separately, but that fact is **not** a basis for calling characterization details private when those details appeared in public ancestor commits/artifacts. This report avoids republishing mechanism details and routes current security handling through Platform `SECURITY.md`. Historical artifact deletion is not claimed.

The final task changes audit docs/evidence/tools only. Temporary acquisition workflow is removed, no new required check or provider/runtime/production change is introduced, and protected `meta-gate` / Merge Queue remain unchanged. Required CI and publication readback bind the actual final commit in the PR conversation; older green runs are not substituted. Author tests validate evidence/accounting, not independent acceptance. PR #185 remains Draft while material scope and review obligations remain open.
