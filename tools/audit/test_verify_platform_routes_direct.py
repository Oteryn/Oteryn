#!/usr/bin/env python3
"""Adversarial tests for the frozen Platform routes candidate."""
from copy import deepcopy
from pathlib import Path
import csv
import json
import shutil
import subprocess
import sys
import tempfile
import unittest

import verify_platform_routes_direct as verifier


class PlatformRoutesCandidateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate = verifier.read_json(verifier.ROOT / verifier.CANDIDATE_REL)
        cls.inventory_tmp = tempfile.TemporaryDirectory(prefix="routes-ledger-inventory-")
        cls.inventory_dir = verifier.collect_canonical_inventories(
            verifier.ROOT, Path(cls.inventory_tmp.name) / "audit")

    @classmethod
    def tearDownClass(cls):
        cls.inventory_tmp.cleanup()

    def reject(self, mutate):
        candidate = deepcopy(self.candidate)
        mutate(candidate)
        with self.assertRaises(ValueError):
            verifier.validate_candidate(candidate)

    def test_committed_revalidation_passes(self):
        verifier.validate_candidate(deepcopy(self.candidate))
        verifier.validate_current_accounting(verifier.ROOT, self.inventory_dir)

    def test_cli_stdout_is_exactly_one_verifier_json_document(self):
        script = """
import sys
from unittest import mock
import verify_platform_routes_direct as verifier

with mock.patch.object(verifier, "validate_source"):
    raise SystemExit(verifier.main())
"""
        completed = subprocess.run(
            [sys.executable, "-c", script, "--audit-root", str(verifier.ROOT),
             "--platform-root", str(verifier.ROOT)],
            cwd=Path(__file__).resolve().parent,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=180,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        parsed = json.loads(completed.stdout)
        self.assertEqual(parsed["result"], "PLATFORM_ROUTES_DIRECT_EXISTING_REVALIDATION_VALID")
        self.assertEqual(completed.stdout, json.dumps(parsed, sort_keys=True) + "\n")

    def mutate_accounting(self, mutation):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(verifier.ROOT / "docs/evidence", root / "docs/evidence")
            mutation(root)
            with self.assertRaises(ValueError):
                verifier.validate_current_accounting(root, self.inventory_dir)

    def test_direct_grouped_overlap_detection_is_exact(self):
        groups = {"groups": [{"repository": "platform", "disposition": "GROUPED",
                              "path_prefix": "routes/"}]}
        prefixes = verifier.grouped_prefixes(groups)
        self.assertTrue(any(path.startswith(prefix) for path in verifier.PATH_BLOBS for prefix in prefixes))

    def test_missing_duplicate_and_extra_paths_fail(self):
        self.reject(lambda c: c["paths"].pop())
        self.reject(lambda c: c["paths"].append(deepcopy(c["paths"][0])))
        self.reject(lambda c: c["paths"].append({"path": "routes/extra.php", "blob_sha": "0" * 40}))

    def test_path_blob_and_tree_drift_fail(self):
        self.reject(lambda c: c["paths"][0].update(blob_sha="0" * 40))
        self.reject(lambda c: c["source"].update(routes_tree_sha="0" * 40))
        self.reject(lambda c: c["source"].update(commit_sha="0" * 40))

    def test_rejected_21_claim_cannot_be_accepted_or_used(self):
        self.reject(lambda c: c["rejected_history"].update(accepted_as_evidence=True))
        self.reject(lambda c: c["rejected_history"].update(used_for_revalidation=True))
        self.reject(lambda c: c["source"].update(regular_file_count=21))

    def test_semantic_scope_cannot_be_weakened(self):
        self.reject(lambda c: c["semantic_boundary"]["included"].pop())
        self.reject(lambda c: c["semantic_boundary"]["excluded"].pop())
        self.reject(lambda c: c["semantic_boundary"]["excluded"].remove("production reachability"))

    def test_re_adoption_and_future_promotion_semantics_fail(self):
        self.reject(lambda c: c.update(re_adoption_permitted=True))
        self.reject(lambda c: c.update(disposition="DIRECT_ADOPTED"))
        self.reject(lambda c: c.update(future_adoption=True))
        self.reject(lambda c: c.update(coverage_delta=19))
        self.reject(lambda c: c["canonical_accounting_unchanged"].update(direct_paths=252))
        self.reject(lambda c: c["limitations"].append("Adopt these 19 paths in a future phase."))

    def test_readiness_completion_and_finding_closure_fail(self):
        self.reject(lambda c: c["limitations"].append("This establishes product readiness."))
        self.reject(lambda c: c["review_result"].update(existing_provider_findings_closed=True))
        self.reject(lambda c: c.update(audit_complete=True))

    def test_accounting_drift_fails(self):
        self.reject(lambda c: c["canonical_accounting_unchanged"].update(ledger_sha256="0" * 64))

    def test_deleting_unrelated_original_direct_row_fails(self):
        def mutation(root):
            path = root / verifier.REVIEW_REL
            lines = path.read_text(encoding="utf-8").splitlines()
            header, rows = lines[0], lines[1:]
            rows.remove(next(row for row in rows if "\troutes/" not in row))
            path.write_text("\n".join([header, *rows]) + "\n", encoding="utf-8")
        self.mutate_accounting(mutation)

    def test_route_scope_line_ranges_and_execution_evidence_drift_fail(self):
        for field, value in (("scope", "adopt again"), ("line_ranges", "[[1,1]]"),
                             ("execution_evidence", "This establishes product readiness.")):
            def mutation(root, field=field, value=value):
                path = root / verifier.REVIEW_REL
                with path.open(encoding="utf-8", newline="") as handle:
                    reader = csv.DictReader(handle, delimiter="\t")
                    fieldnames, rows = reader.fieldnames, list(reader)
                rows[next(i for i, row in enumerate(rows) if row["path"] == "routes/api.php")][field] = value
                with path.open("w", encoding="utf-8", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
                    writer.writeheader(); writer.writerows(rows)
            self.mutate_accounting(mutation)

    def test_canonical_totals_and_ledger_digest_drift_fail(self):
        def totals(root):
            path = root / "docs/evidence/organization-audit-20260907/coverage-summary.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["scoped_review_paths"] = 252
            path.write_text(json.dumps(data), encoding="utf-8")
        self.mutate_accounting(totals)

        def digest(root):
            path = root / "docs/evidence/organization-audit-20260907/coverage-summary.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["ledger_sha256"] = "0" * 64
            path.write_text(json.dumps(data), encoding="utf-8")
        self.mutate_accounting(digest)

    def test_non_route_canonical_addition_scope_drift_fails(self):
        def mutation(root):
            path = root / "docs/evidence/organization-audit-20260907/coverage-review-canonical-additions.tsv"
            with path.open(encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle, delimiter="\t")
                fieldnames, rows = reader.fieldnames, list(reader)
            row = next(row for row in rows if not row["path"].startswith("routes/"))
            row["scope"] = "Contradictory non-route canonical scope."
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
                writer.writeheader(); writer.writerows(rows)
        self.mutate_accounting(mutation)

    def test_accepted_grouped_scope_drift_fails(self):
        def mutation(root):
            path = root / verifier.GROUPS_REL
            data = json.loads(path.read_text(encoding="utf-8"))
            accepted = next(row for row in data["groups"] if row["disposition"] == "GROUPED")
            accepted["scope"] = "Contradictory accepted GROUPED accounting scope."
            path.write_text(json.dumps(data), encoding="utf-8")
        self.mutate_accounting(mutation)

    def test_type_and_extra_key_drift_fail(self):
        self.reject(lambda c: c.update(schema_version=True))
        self.reject(lambda c: c["source"].update(readiness=False))


if __name__ == "__main__":
    unittest.main()
