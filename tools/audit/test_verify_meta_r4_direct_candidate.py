#!/usr/bin/env python3
"""Adversarial tests for the 25-path META R4-correlated DIRECT candidate."""
from copy import deepcopy
from pathlib import Path
import csv, json, shutil, tempfile, unittest
import verify_meta_r4_direct_candidate as verifier

class MetaR4DirectCandidateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate=verifier.expected_candidate()
        cls.tmp=tempfile.TemporaryDirectory(prefix='meta-r4-ledger-')
        cls.inventory=verifier.collect_inventories(verifier.ROOT,Path(cls.tmp.name)/'audit')
    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()
    def reject(self,mutation):
        value=deepcopy(self.candidate); mutation(value)
        with self.assertRaises(ValueError): verifier.validate_candidate(value)
    def mutate_accounting(self,mutation):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t); shutil.copytree(verifier.ROOT/'docs/evidence',root/'docs/evidence'); mutation(root)
            with self.assertRaises(ValueError): verifier.validate_accounting(root,self.candidate,self.inventory)
    def mutate_finding(self,mutation):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t); path=root/verifier.FINDINGS_REL; path.parent.mkdir(parents=True)
            with (verifier.ROOT/verifier.FINDINGS_REL).open(encoding='utf-8',newline='') as f:
                reader=csv.DictReader(f,delimiter='\t'); fields=reader.fieldnames; rows=list(reader)
            mutation(rows)
            with path.open('w',encoding='utf-8',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=fields,delimiter='\t',lineterminator='\n'); writer.writeheader(); writer.writerows(rows)
            with self.assertRaises(ValueError): verifier.validate_finding(root,self.candidate)
    def test_committed_candidate_and_rebuilt_ledger_pass(self):
        verifier.validate_candidate(deepcopy(self.candidate)); verifier.validate_source(verifier.ROOT,self.candidate)
        verifier.validate_finding(verifier.ROOT,self.candidate); verifier.validate_accounting(verifier.ROOT,self.candidate,self.inventory)
    def test_missing_duplicate_extra_and_blob_drift_fail(self):
        self.reject(lambda c:c['paths'].pop())
        self.reject(lambda c:c['paths'].append(deepcopy(c['paths'][0])))
        self.reject(lambda c:c['paths'].append({'path':'extra','blob_sha':'0'*40,'semantic_note':'x'}))
        self.reject(lambda c:c['paths'][6].update(blob_sha='0'*40))
    def test_source_tree_and_historical_coordinates_fail_closed(self):
        self.reject(lambda c:c['source'].update(tree_sha='0'*40))
        self.reject(lambda c:c['historical_r4_provenance'].update(audited_source_commit='0'*40))
        self.reject(lambda c:c['historical_r4_provenance'].update(coverage_ledger_publication_blob='0'*40))
    def test_temporal_authority_cannot_be_promoted(self):
        for key in ('retired_prompts_dispatchable','superpowers_material_dispatchable','historical_closeouts_are_current_live_proof','recovery_contract_is_current_live_qualification','desired_state_is_live_enforcement_proof','mutable_github_admin_provider_runtime_state_reviewed'):
            self.reject(lambda c,key=key:c['temporal_authority'].update({key:True}))
    def test_meta_aud_05_cannot_be_dropped_closed_downgraded_or_duplicated(self):
        self.reject(lambda c:c.pop('reconfirmed_finding'))
        self.reject(lambda c:c['reconfirmed_finding'].update(status='CLOSED'))
        self.reject(lambda c:c['reconfirmed_finding'].update(severity='P3'))
        self.reject(lambda c:c['reconfirmed_finding'].update(id='META-AUD-NEW'))
        self.reject(lambda c:c['reconfirmed_finding'].update(duplicate_id='META-AUD-05'))
        self.mutate_finding(lambda rows:rows.append(deepcopy(next(r for r in rows if r['id']=='META-AUD-05'))))
    def test_meta_aud_05_complete_canonical_row_is_bound(self):
        mutations={
            'repository':'game',
            'scope':'resolved; no further action required',
            'evidence':'resolved; no further action required',
            'owner_route':'Oteryn/Oteryn-Game#1',
            'closure_condition':'resolved; no further action required',
        }
        for field,value in mutations.items():
            with self.subTest(field=field):
                def mutate(rows,field=field,value=value):
                    next(r for r in rows if r['id']=='META-AUD-05')[field]=value
                self.mutate_finding(mutate)
    def test_adoption_readiness_completion_and_live_claims_fail(self):
        self.reject(lambda c:c.update(coverage_adopted=True))
        self.reject(lambda c:c.update(disposition='DIRECT'))
        self.reject(lambda c:c['limitations'].append('Adoption is guaranteed next.'))
        self.reject(lambda c:c['limitations'].append('This establishes product readiness and independent 10/10.'))
        self.reject(lambda c:c.update(live_enforcement=True))
    def test_types_keys_notes_and_accounting_are_exact(self):
        self.reject(lambda c:c.update(schema_version=True))
        self.reject(lambda c:c['paths'][0].update(semantic_note='Readiness proven.'))
        self.reject(lambda c:c['canonical_accounting_unchanged'].update(direct_paths=258))
        self.reject(lambda c:c['source'].update(extra=False))
    def test_candidate_paths_must_remain_unverified(self):
        def mutation(root):
            # Introducing this source path as canonical DIRECT must alter the authoritative ledger.
            path=root/'docs/evidence/organization-audit-20260907/coverage-review-canonical-additions.tsv'
            with path.open(encoding='utf-8',newline='') as f: reader=csv.DictReader(f,delimiter='\t'); fields=reader.fieldnames; rows=list(reader)
            rows.append({'repository':'meta','path':self.candidate['paths'][0]['path'],'blob_sha':self.candidate['paths'][0]['blob_sha'],'depth':'FULL_FILE','scope':'bad promotion','line_ranges':'[]','execution_evidence':'none'})
            with path.open('w',encoding='utf-8',newline='') as f: w=csv.DictWriter(f,fieldnames=fields,delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)
        self.mutate_accounting(mutation)
    def test_non_candidate_accounting_drift_fails(self):
        def mutation(root):
            path=root/'docs/evidence/organization-audit-20260907/coverage-groups.json'; data=json.loads(path.read_text()); data['groups'][0]['scope']='drift'; path.write_text(json.dumps(data))
        self.mutate_accounting(mutation)

if __name__=='__main__': unittest.main()
