#!/usr/bin/env python3
"""Positive fixture and adversarial accounting mutations; no network or provider code."""
import csv
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import verify_report as audit

ROOT=Path(__file__).resolve().parents[2]
REPORT='OTERYN-ORGANIZATION-COMPREHENSIVE-AUDIT-20260907.json'
EVIDENCE='organization-audit-20260907'

class AuditValidationTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='audit-contract-')
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.path=self.root/REPORT
        shutil.copy2(ROOT/'docs/evidence'/REPORT,self.path)
        self.base=self.root/EVIDENCE;self.base.mkdir()
        for name in ['finding-register.tsv','domain-matrix.tsv','unknowns.json','coverage-review.tsv','coverage-summary.json','workflow-inventory.tsv','verification-index.json']:
            shutil.copy2(ROOT/'docs/evidence'/EVIDENCE/name,self.base/name)
    def mutate(self,path,func):
        data=audit.read_json(path);func(data);path.write_text(json.dumps(data))
    def reject(self):
        with self.assertRaises(ValueError):audit.validate(self.path)
    def test_current_report_validates_as_accounting_only(self):
        result=audit.validate(self.path)
        self.assertEqual(result['result'],'ACCOUNTING_VALID_NOT_SEMANTIC_PASS')
        self.assertEqual(result['findings'],77)
        self.assertFalse(result['tree_and_ledger_verified'])
    def test_boolean_schema_rejected(self):
        self.mutate(self.path,lambda d:d.update(schema_version=True));self.reject()
    def test_production_claim_rejected(self):
        self.mutate(self.path,lambda d:d.update(production_readiness_claimed=True));self.reject()
    def test_self_awarded_score_rejected(self):
        self.mutate(self.path,lambda d:d.update(independent_score=10));self.reject()
    def test_exhaustive_severity_claim_rejected(self):
        self.mutate(self.path,lambda d:d.update(severity_counts_exhaustive=True));self.reject()
    def test_unqualified_completion_rejected(self):
        self.mutate(self.path,lambda d:d.update(status='COMPLETE'));self.reject()
    def test_duplicate_finding_rejected(self):
        p=self.base/'finding-register.tsv';lines=p.read_text().splitlines();p.write_text('\n'.join(lines+[lines[1]])+'\n');self.reject()
    def test_missing_domain_rejected(self):
        p=self.base/'domain-matrix.tsv';p.write_text('\n'.join(p.read_text().splitlines()[:-1])+'\n');self.reject()
    def test_historical_candidate_counted_as_snapshot_rejected(self):
        self.mutate(self.path,lambda d:d['known_source_snapshot_p1_ids'].append('GAME-CANDIDATE-361'));self.reject()
    def test_hidden_unverified_paths_rejected(self):
        self.mutate(self.base/'coverage-summary.json',lambda d:d['per_repository']['platform'].update(unverified_semantics=0));self.reject()
    def test_reproduction_called_pass_rejected(self):
        self.mutate(self.base/'verification-index.json',lambda d:d.update(routing_product_verdict='PASS'));self.reject()
    def test_unbound_execution_source_rejected(self):
        self.mutate(self.base/'verification-index.json',lambda d:d['results'][0].update(source_commit='0'*40));self.reject()
    def test_path_escape_rejected(self):
        self.mutate(self.path,lambda d:d.update(evidence_directory='../other'));self.reject()
    def test_duplicate_json_key_rejected(self):
        self.path.write_text('{"schema_version":2,"schema_version":2}')
        self.reject()
    def test_duplicate_tsv_header_rejected(self):
        p=self.base/'finding-register.tsv';p.write_text('id\tid\na\ta\n');self.reject()
    def test_missing_unknown_rejected(self):
        self.mutate(self.base/'unknowns.json',lambda d:d['items'].pop());self.reject()
    def test_workflow_count_inflation_rejected(self):
        self.mutate(self.path,lambda d:d['workflow_census'].update(total_workflows=78));self.reject()
    def test_tree_digest_matches_native_git(self):
        oid='d670460b4b4aece5915caf5c68d12f560a9fe3e4'
        raw=b'100644 a.txt\0'+bytes.fromhex(oid)
        expected=subprocess.run(['git','hash-object','-t','tree','--stdin'],input=raw,stdout=subprocess.PIPE,check=True,timeout=5).stdout.decode().strip()
        self.assertEqual(audit.tree_sha([{'path':'a.txt','mode':'100644','object_sha':oid}]),expected)
    def test_duplicate_inventory_path_rejected(self):
        row={'path':'a','mode':'100644','object_sha':'a'*40}
        with self.assertRaises(ValueError):audit.tree_sha([row,row])
    def test_unsafe_inventory_path_rejected(self):
        with self.assertRaises(ValueError):audit.tree_sha([{'path':'../bad','mode':'100644','object_sha':'a'*40}])
    def test_ledger_requires_inventories(self):
        with self.assertRaises(ValueError):audit.validate(self.path,ledger_output=self.root/'ledger.csv')

if __name__=='__main__':unittest.main()
