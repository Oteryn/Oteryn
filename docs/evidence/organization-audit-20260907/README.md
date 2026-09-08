# Organization audit R3 evidence

Governing continuation: META#186, existing PR#185. The main report/JSON owns the scoped opinion; this is not another approval programme. R3 contains 77 finding records, 23 A–W domains, 15 residual obligations and 202 explicit scoped path reviews out of 4325 immutable leaves. `4123` leaves retain UNVERIFIED semantics. Full-file, control-field and translation-range reviews are intentionally distinguished.

## Local checks

From the META repository root with Python 3 and Node available:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/audit -p 'test_*.py' -v
node --test tools/audit/test-public-surface-contract.mjs tools/audit/test-public-surface-evidence-hardening.mjs
python3 tools/audit/verify_report.py --report docs/evidence/OTERYN-ORGANIZATION-COMPREHENSIVE-AUDIT-20260907.json
```

The accounting result is `ACCOUNTING_VALID_NOT_SEMANTIC_PASS`. Source and raw-evidence validation are separate:

```sh
python3 tools/audit/organization_audit.py --plan docs/evidence/organization-audit-20260907/collection-plan.json --output /tmp/audit-new-inventory
python3 tools/audit/verify_report.py --report docs/evidence/OTERYN-ORGANIZATION-COMPREHENSIVE-AUDIT-20260907.json --inventory-dir /tmp/audit-new-inventory/inventories --ledger-output /tmp/audit-new-ledger.csv
python3 tools/audit/reproduce_platform_routing.py --source-root /path/to/exact-platform-de917b3 --output /tmp/audit-new-routing.json
python3 tools/audit/verify_announcement_trigger.py --source-root /path/to/exact-platform-de917b3
python3 tools/audit/verify_r3_evidence.py --manifest docs/evidence/organization-audit-20260907/r3-native-manifest.json --archive-dir /path/to/public-native-archives
```

Use new output paths; acquisition requires its documented read-only consent/access. The routing characterization exits successfully when two product failures are reproduced, not when the product passes. The static Announcements probe is not a new browser run. Native raw ZIP filenames must match the manifest. The R3 parser rechecks raw observations and source identity, package/test event ordering, per-case counts and retained anomalies.

## Evidence map and durability

`r3-native-manifest.json` binds six public native archives; `r3-native-results.json` stores the independently recalculated summary. `r3-trigger-evidence.json` binds the locale-trigger finding. `r3-migration-review.json` binds the closed 50-path ledger subset and synthetic-up observation. `r3-visual-review.json` records eight actually inspected screenshot digests and limits. `r3-lifecycle.json` records later native state without rebasing the source cut. `r3-source-review.md` explains precise scope and negative evidence.

Full 4325-row CSV, native archives, original and corrected captures, red/green tool-regression logs and expanded checks accompany the downloadable audit delivery. Actions archives expire (dates in manifest); preserve the delivery. Committed immutable Git coordinates plus the collector reproduce source inventories, not historical runtime outputs after those outputs expire. Do not treat a digest alone as the raw evidence.

Restricted security details follow Platform SECURITY.md and are supplied separately to the owner, not in this public evidence directory. The final effective diff excludes the earlier two characterization scripts; historical commits/artifacts are not erased. No private advisory submission is claimed.

The temporary hosted collector is absent from the final task tree. No provider writes, deployment, new required gate, automatic background worker, full semantic completion or self-awarded score is implied.
