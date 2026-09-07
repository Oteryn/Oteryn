# Organization audit R2 evidence

Governing continuation: META #186, existing PR #185. This directory is evidence, not a new approval framework. The main report/JSON one directory above owns the opinion. TSV registers are canonical compact records; expanded JSON, full logs and the 4,325-row CSV are included in the accompanying audit-only delivery.

## Offline checks

From the META repository root:

```sh
python3 tools/audit/test_organization_audit.py -v
python3 tools/audit/test_verify_report.py -v
python3 tools/audit/verify_report.py \
  --report docs/evidence/OTERYN-ORGANIZATION-COMPREHENSIVE-AUDIT-20260907.json
```

The result is `ACCOUNTING_VALID_NOT_SEMANTIC_PASS`, never product readiness.

## Reproduce the complete path ledger

On an authorized GitHub-hosted or isolated plane with read-only access to the pinned public repositories:

```sh
python3 tools/audit/organization_audit.py \
  --plan docs/evidence/organization-audit-20260907/collection-plan.json \
  --output /tmp/oteryn-audit-new-inventory
python3 tools/audit/verify_report.py \
  --report docs/evidence/OTERYN-ORGANIZATION-COMPREHENSIVE-AUDIT-20260907.json \
  --inventory-dir /tmp/oteryn-audit-new-inventory/inventories \
  --ledger-output /tmp/oteryn-audit-new-ledger.csv
```

Use new output paths: both tools refuse destructive overwrite. The verifier reconstructs each Git tree, checks exact review blob identities, emits one row per leaf and matches the committed ledger SHA-256. All unmatched paths are UNVERIFIED. Existing historical review evidence is not discarded, but its full validity is not automatically adopted.

The original temporary source artifact was transport only and expires. Immutable Git coordinates, collector code, review rules and the ledger digest reproduce the ledger without that artifact. No provider source is copied into META as product authority.

## Reproduce the Platform finding

With an isolated checkout of Platform at `de917b3477a1de0667531380de3660e8b2ab59aa`:

```sh
python3 tools/audit/reproduce_platform_routing.py \
  --source-root /path/to/exact-platform-checkout \
  --output /tmp/platform-routing-reproduction.json
```

The script first verifies the three source blobs, uses temporary repositories without a remote, and records eight cases. A successful characterization currently means **two product routing failures reproduced**, not that runtime tests ran or a real merge bypass occurred.

## Interpretation

`finding-register.tsv` accounts for 76 identifiers and their existing owner routes/closure conditions. `domain-matrix.tsv` records all A–W criteria and qualified opinions. `coverage-review.tsv` contains 65 newly scoped review entries, not a 65-file claim about the total history of previous audits. `workflow-inventory.tsv` is a complete static census, not 77 semantic workflow approvals. `verification-index.json` records actual commands/source/log digests; `unknowns.json` retains missing evidence and its effect.

No self-awarded score, background continuation, product deployment, provider mutation or new required gate is implied. The temporary acquisition workflow is absent from the final task tree.
