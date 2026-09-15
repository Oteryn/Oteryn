# R3 source review and evidence boundaries

This is audit-author work on the five immutable generations in the main JSON, not independent review or approval of all behavior. The exact path/blob/range ledger is `coverage-review.tsv`. Counts are derived, not estimated.

## Scope keys used by the compact ledger

`R3-WF`: only the workflow control declarations described below, not all step bodies or live enforcement. `R3-DB`: entire migration source for the listed schema/data/rollback concerns, not down execution or data-conservation proof. `R3-ID`: identity/session component boundaries, including a controlled characterization whose mechanism must now be treated as publicly disclosed because it appeared in public ancestor history/artifacts; no live/full acceptance. `R3-F17`: only the recorded Announcements translation-consumer/profile/assertion ranges; not full locale or browser qualification. Each row binds its exact source blob and inspected line ranges; these keys are expanded here instead of duplicating the same paragraph in every row.

## Platform persistence: all 50 migrations

Read all authored `database/migrations/*.php` up/down bodies. Assessed creation/removal ordering, foreign keys and deletion behavior, uniqueness/idempotency constraints, nullable/default states, generation/replay fields, data conversions, and explicit refusal of lossy reverse transformations. `r3-migration-review.json` binds the complete 50-path/blob ledger subset and total line count.

All 50 migration names occur in the successful `migrations.log` from the isolated SQLite public-UI fixture, native artifact 10043048175. Post-review hardening makes this claim reproducible: `verify_r3_evidence.py` reconstructs the exact 50 Platform migration paths/blobs from `coverage-review.tsv`, validates their committed digest, parses the bound log and requires exactly 50 unique `DONE` names equal to that source set. This demonstrates fresh-schema up execution only. No down execution, current-data upgrade, production/MariaDB schema matrix, rollback data conservation, or RPO/RTO is claimed.

Important observations: game-catalog reverse ordering respects declared dependencies; verified-content/loot conversion reverse paths explicitly reject incompatible data; refund/reconciliation reverse paths guard retained settlement/resolution evidence. Passport migration field declarations do not all imply constrained foreign keys. SQL uniqueness alone does not prove cross-service exactly-once behavior. RBAC seed reversal is migration behavior, not proof that arbitrary later operator edits are preserved.

## All 77 workflow control surfaces

Read the event/path/input declarations, top-level permissions/concurrency and job conditions, needs, runner selection, permission overrides, reusable workflow invocation, secret/environment declarations and matrices across all 77 workflow files. Exact ranges record those fields; general step/run bodies have NOT thereby received full semantic approval. Live environment/reviewer/protection enforcement is a separate evidence surface.

Platform's required aggregate still does not acquire separate Gateway and dedicated concurrency results on its pinned generation (F01). The actual-Git classification failure remains F16. The new F17 is narrower: Announcements consumes EN/PL locale keys, while its dedicated automatic workflow excludes those paths. Eight source-bound probes preserve four controls and four counterexamples; no live merge bypass is claimed.

Game's declaration graph distinguishes PR impact selection from its full merge-group graph. Atlas's three declared maintenance/lifecycle workflows are not restoration or full product qualification. Operations workflows using host runners and protected environments were inspected as declarations only: this audit did not dispatch them or certify every privileged command.

## Identity/session and public UI contracts

Read the nine named identity/session component sources in the path ledger. A controlled source-pinned characterization exists, but independent review established that its mechanism was present in public ancestor commits and public Actions artifacts. It must therefore be handled as already disclosed; the current report intentionally does not repeat the mechanism or PoC. Further assessment/remediation is routed through Platform `SECURITY.md` private vulnerability reporting. Current live reachability, artifact deletion/expiry, private-advisory submission and remediation remain unverified. Deleting the scripts from the final tree does not erase Git history or restore confidentiality.

Separately, historical direct-read coverage for four account/Canary/profile/character families was reused only after fail-closed revalidation: `app/Accounts/**` (7), `app/CanaryIntegration/**` (8), `app/CharacterProfiles/**` (4), and `app/Characters/**` (12) are byte-identical between the historical audited Platform generation and frozen `de917b3…`. The candidate binds exactly 23 dependent blobs and an ordered 15-file test set; hosted PHP 8.5.10/MariaDB 11.8.9 qualification produced exactly 86 cases / 586 assertions / zero failures/errors/skips. These 31 leaves are bounded GROUPED carry-forward, not DIRECT current review, later-main acceptance, complete identity/security approval, or product readiness.

Separately, the historical 49-file Marketplace/Payments/Wallet production batch was reused only after exact family reconstruction: `app/Marketplace/**` (21), `app/Payments/**` (24), and `app/Wallet/**` (4) are byte-identical between the historical audited generation and frozen `de917b3…`. The candidate binds exactly 23 dependent config/route/toolchain/test blobs and an ordered 13-file qualification; PHP 8.5.10/MariaDB 11.8.9 produced 45 cases / 444 assertions / zero failures/errors/skips, including real Marketplace transfer integration/concurrency and Payment event/refund concurrency. These 49 leaves are bounded GROUPED carry-forward, not DIRECT current review, later-main acceptance, payment security approval, or product readiness.

Read the Announcements ticker, browser profile, acceptance spec and only the relevant EN/PL translation ranges. The static trigger probe binds six exact source blobs. No fresh Announcements full-browser suite is inferred from the unrelated anonymous 48-case UI acquisition.

Eight actual full images from the corrected public-UI artifact were inspected by this audit author. Observations and digests are in `r3-visual-review.json`; empty Wiki/unpublished editorial states are not working-content acceptance.

## Evidence-tool defects fixed before accepting the recount

The browser oracle rejects another local route and credential-bearing URLs and checks complete source bindings for current-schema evidence. The results parser independently recomputes raw DOM criteria rather than trusting recorded green flags. After independent review, the original failed browser capture is also parsed directly: the matrix must be exactly 48 cases and the failure signature exactly eight `http_ok` failures for `/support` and `/legal/privacy` across four viewports, with no hidden ninth failure; its replay is explicitly offline/legacy, not a new browser execution.

Negative per-case assertions cannot cancel positive counts. Go event histories must have one package lifecycle, bound test-package identity and correctly ordered starts/ends; duplicate starts and out-of-order terminals fail. The migration log must equal the exact 50-path source ledger, and the entire recomputed native summary must equal committed `r3-native-results.json` or verification fails. The CI collector creates result/error files exclusively so existing files and final-path symlinks cannot be overwritten. RED/GREEN regression evidence is supplied with the delivery.

These checks protect accounting and evidence interpretation. They are not proof that no application defect exists, nor a substitute for another independent reviewer. The final accounting test deliberately refuses exhaustive completion, a self-awarded score, a fabricated product PASS or hiding unverified coverage.

## Reuse and missing coverage

No generated files, suspended controllers, historic prompts or source directories were automatically marked GROUPED/N/A merely to improve a percentage. Existing narrow R2 evidence is retained. Unreviewed paths remain UNVERIFIED. Prior provider coverage can be reused only when its actual scope, exact identity and dependent configuration/consumer validity are established. Source enumeration and even a tested generator do not automatically prove every semantic contract of generated outputs.
