#!/usr/bin/env python3
"""Positive fixture and adversarial accounting mutations; no network or provider code."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock
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
        shutil.copy2(ROOT/'docs/evidence'/REPORT.replace('.json','.md'),self.path.with_suffix('.md'))
        self.base=self.root/EVIDENCE;self.base.mkdir()
        for name in ['finding-register.tsv','domain-matrix.tsv','unknowns.json','coverage-review.tsv','coverage-review-canonical-additions.tsv','coverage-review-meta-r4-direct-additions.tsv','coverage-review-meta-r5-instruction-efficiency-direct-additions.tsv','coverage-summary.json','coverage-groups.json','workflow-inventory.tsv','verification-index.json']:
            shutil.copy2(ROOT/'docs/evidence'/EVIDENCE/name,self.base/name)
    def mutate(self,path,func):
        data=audit.read_json(path);func(data);path.write_text(json.dumps(data))
    def reject(self):
        with self.assertRaises(ValueError):audit.validate(self.path)
    def mutate_companion(self, old, new, count=1):
        companion=self.path.with_suffix('.md')
        text=companion.read_text(encoding='utf-8')
        self.assertIn(old,text)
        companion.write_text(text.replace(old,new,count),encoding='utf-8')
    def test_current_report_validates_as_accounting_only(self):
        result=audit.validate(self.path)
        report=audit.read_json(self.path)
        summary=audit.read_json(self.base/'coverage-summary.json')
        groups=audit.read_json(self.base/'coverage-groups.json')['groups']
        grouped=sum(row['expected_count'] for row in groups)
        direct=report['scoped_review_paths']
        self.assertEqual(result['result'],'ACCOUNTING_VALID_NOT_SEMANTIC_PASS')
        self.assertEqual(result['findings'],78)
        self.assertEqual(result['grouped_revalidated_paths'],grouped)
        self.assertEqual(result['semantically_classified_paths'],direct+grouped)
        self.assertEqual(result['unverified_semantics'],summary['source_leaf_total']-direct-grouped)
        self.assertFalse(result['tree_and_ledger_verified'])
    def test_current_coverage_table_meta_drift_rejected(self):
        self.mutate_companion('| meta | 174 | 70 | 0 | 104 |','| meta | 174 | 45 | 0 | 129 |')
        self.reject()
    def test_current_coverage_table_total_drift_rejected(self):
        self.mutate_companion('| **Total** | **4325** | **283** | **113** | **3929** |',
                              '| **Total** | **4325** | **258** | **113** | **3954** |')
        self.reject()
    def test_current_history_annotation_present_count_drift_rejected(self):
        self.mutate_companion('present canonical 283-path state','present canonical 258-path state')
        self.reject()
    def test_current_r5_paragraph_deletion_or_mutation_rejected(self):
        for replacement in ('', audit.CURRENT_R5_ADOPTION_PARAGRAPH.replace('all 14','all 13')):
            with self.subTest(replacement=bool(replacement)):
                shutil.copy2(ROOT/'docs/evidence'/REPORT.replace('.json','.md'),self.path.with_suffix('.md'))
                self.mutate_companion(audit.CURRENT_R5_ADOPTION_PARAGRAPH,replacement)
                self.reject()
    def test_current_r5_readiness_append_or_replacement_rejected(self):
        for replacement in (
            audit.CURRENT_R5_ADOPTION_PARAGRAPH+' This establishes product and production readiness.',
            'This R5 adoption establishes product readiness and organization-wide audit completion.',
        ):
            with self.subTest(replacement=replacement[:20]):
                shutil.copy2(ROOT/'docs/evidence'/REPORT.replace('.json','.md'),self.path.with_suffix('.md'))
                self.mutate_companion(audit.CURRENT_R5_ADOPTION_PARAGRAPH,replacement)
                self.reject()
    def test_current_table_or_r5_paragraph_duplicate_rejected(self):
        table='\n'.join(audit._current_coverage_table())
        for original, duplicate in ((table,table+'\n\n'+table),
                                    (audit.CURRENT_R5_ADOPTION_PARAGRAPH,
                                     audit.CURRENT_R5_ADOPTION_PARAGRAPH+'\n\n'+audit.CURRENT_R5_ADOPTION_PARAGRAPH)):
            with self.subTest(original=original[:20]):
                shutil.copy2(ROOT/'docs/evidence'/REPORT.replace('.json','.md'),self.path.with_suffix('.md'))
                self.mutate_companion(original,duplicate)
                self.reject()
    def test_current_history_annotation_move_or_remove_rejected(self):
        for replacement in ('', audit.CURRENT_HISTORY_ANNOTATION+'\n\nUnrelated current status.'):
            with self.subTest(replacement=bool(replacement)):
                shutil.copy2(ROOT/'docs/evidence'/REPORT.replace('.json','.md'),self.path.with_suffix('.md'))
                self.mutate_companion(audit.CURRENT_HISTORY_ANNOTATION,replacement)
                self.reject()
    def test_current_ledger_digest_drift_rejected(self):
        self.mutate_companion('27654f5f724d9857912e69fd036712dd00d63882ebf8e9c1411c26c66eaeef41','0'*64)
        self.reject()
    def test_historical_223_snapshot_remains_accepted(self):
        text=self.path.with_suffix('.md').read_text(encoding='utf-8')
        self.assertIn('223 DIRECT / 113 GROUPED / 3,989 UNVERIFIED',text)
        self.assertIn('2d823435f76f0c08b118ccb5dc1c9ccf9ef4acc41bffdd447b260e82ea404b0f',text)
        self.assertEqual(audit.validate(self.path)['result'],'ACCOUNTING_VALID_NOT_SEMANTIC_PASS')
    def test_historical_snapshot_contradictory_current_state_insertion_rejected(self):
        insertion=' The present canonical state is 258 DIRECT / 113 GROUPED / 3954 UNVERIFIED and is product ready.'
        marker=' Full CSV is reproducible'
        self.mutate_companion(marker,insertion+marker)
        self.reject()
    def test_historical_snapshot_223_state_removal_or_replacement_rejected(self):
        historical_delta='the current revision adds 158 DIRECT paths'
        for replacement in ('', 'the current revision adds 159 DIRECT paths'):
            with self.subTest(replacement=replacement):
                shutil.copy2(ROOT/'docs/evidence'/REPORT.replace('.json','.md'),self.path.with_suffix('.md'))
                self.mutate_companion(historical_delta,replacement)
                self.reject()
    def test_historical_snapshot_digest_removal_or_replacement_rejected(self):
        digest='2d823435f76f0c08b118ccb5dc1c9ccf9ef4acc41bffdd447b260e82ea404b0f'
        for replacement in ('', '0'*64):
            with self.subTest(replacement=replacement):
                shutil.copy2(ROOT/'docs/evidence'/REPORT.replace('.json','.md'),self.path.with_suffix('.md'))
                self.mutate_companion(digest,replacement)
                self.reject()
    def test_historical_snapshot_arbitrary_status_append_rejected(self):
        self.mutate_companion(audit.EXPECTED_PRE_ANNOUNCEMENTS_MARKETPLACE_SNAPSHOT,
                              audit.EXPECTED_PRE_ANNOUNCEMENTS_MARKETPLACE_SNAPSHOT+' Arbitrary contradictory status.')
        self.reject()
    def test_historical_snapshot_truncation_rejected(self):
        snapshot=audit.EXPECTED_PRE_ANNOUNCEMENTS_MARKETPLACE_SNAPSHOT
        self.mutate_companion(snapshot,snapshot[:len(snapshot)//2])
        self.reject()
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
    def test_audit_completion_complete_rejected(self):
        self.mutate(self.path,lambda d:d.update(audit_completion='COMPLETE'));self.reject()
    def test_audit_completion_equivalent_false_claim_rejected(self):
        self.mutate(self.path,lambda d:d.update(audit_completion='PRODUCT_READY_AND_AUDIT_COMPLETE'));self.reject()
    def test_meta_r4_candidate_pointer_drift_rejected(self):
        self.mutate(self.path,lambda d:d.update(r3_meta_r4_direct_candidate='organization-audit-20260907/wrong.json'));self.reject()
    def test_meta_r4_overlay_pointer_drift_rejected(self):
        self.mutate(self.path,lambda d:d.update(r3_meta_r4_direct_adoption_overlay='organization-audit-20260907/wrong.tsv'));self.reject()
    def test_meta_r5_candidate_pointer_drift_rejected(self):
        self.mutate(self.path,lambda d:d.update(r3_meta_r5_instruction_efficiency_direct_candidate='organization-audit-20260907/wrong.json'));self.reject()
    def test_meta_r5_overlay_pointer_drift_rejected(self):
        self.mutate(self.path,lambda d:d.update(r3_meta_r5_instruction_efficiency_direct_adoption_overlay='organization-audit-20260907/wrong.tsv'));self.reject()

    def test_duplicate_finding_rejected(self):
        p=self.base/'finding-register.tsv';lines=p.read_text().splitlines();p.write_text('\n'.join(lines+[lines[1]])+'\n');self.reject()
    def test_missing_domain_rejected(self):
        p=self.base/'domain-matrix.tsv';p.write_text('\n'.join(p.read_text().splitlines()[:-1])+'\n');self.reject()
    def test_historical_candidate_counted_as_snapshot_rejected(self):
        self.mutate(self.path,lambda d:d['known_source_snapshot_p1_ids'].append('GAME-CANDIDATE-361'));self.reject()
    def test_hidden_unverified_paths_rejected(self):
        self.mutate(self.base/'coverage-summary.json',lambda d:d['per_repository']['platform'].update(unverified_semantics=0));self.reject()
    def test_summary_semantic_coverage_complete_rejected(self):
        self.mutate(self.base/'coverage-summary.json',lambda d:d.update(semantic_coverage='COMPLETE'));self.reject()
    def test_summary_semantic_completion_true_rejected(self):
        self.mutate(self.base/'coverage-summary.json',lambda d:d.update(semantic_completion_claimed=True));self.reject()
    def test_summary_durability_readiness_append_rejected(self):
        self.mutate(self.base/'coverage-summary.json',lambda d:d.update(durability=d['durability']+' This establishes product and production readiness.'));self.reject()
    def test_summary_dimension_note_readiness_replacement_rejected(self):
        self.mutate(self.base/'coverage-summary.json',lambda d:d.update(coverage_dimension_note='Audit completion and production readiness are established.'));self.reject()
    def test_summary_key_removal_rejected(self):
        self.mutate(self.base/'coverage-summary.json',lambda d:d.pop('new_scoped_paths_since_r2'));self.reject()
    def test_summary_extra_key_rejected(self):
        self.mutate(self.base/'coverage-summary.json',lambda d:d.update(product_ready=True));self.reject()
    def test_summary_type_drift_rejected(self):
        self.mutate(self.base/'coverage-summary.json',lambda d:d.update(rejected_group_candidates='1'));self.reject()
    def test_rejected_group_is_not_promoted_by_summary(self):
        self.mutate(self.base/'coverage-summary.json',lambda d:d['per_repository']['atlas'].update(grouped=508,unverified_semantics=637));self.reject()
    def test_rejected_candidate_is_preserved_but_not_counted(self):
        data=audit.read_json(self.base/'coverage-groups.json');rejected=data['rejected_candidates']
        self.assertEqual(len(rejected),1)
        self.assertEqual(rejected[0]['id'],'ATLAS-CREATURE-GAMEPLAY-SHARDS')
        self.assertEqual(rejected[0]['evaluation']['outcome'],'REJECTED_NOT_COUNTED_AS_GROUPED')
        self.assertNotIn(rejected[0]['id'],{row['id'] for row in data['groups']})
    def test_reproduction_called_pass_rejected(self):
        self.mutate(self.base/'verification-index.json',lambda d:d.update(routing_product_verdict='PASS'));self.reject()
    def test_unbound_execution_source_rejected(self):
        self.mutate(self.base/'verification-index.json',lambda d:d['results'][0].update(source_commit='0'*40));self.reject()
    def test_path_escape_rejected(self):
        self.mutate(self.path,lambda d:d.update(evidence_directory='../other'));self.reject()
    def test_duplicate_json_key_rejected(self):
        self.path.write_text('{"schema_version":2,"schema_version":2}');self.reject()
    def test_duplicate_tsv_header_rejected(self):
        p=self.base/'finding-register.tsv';p.write_text('id\tid\na\ta\n');self.reject()
    def test_missing_unknown_rejected(self):
        self.mutate(self.base/'unknowns.json',lambda d:d['items'].pop());self.reject()
    def test_missing_history_with_coordinated_count_rejected(self):
        self.mutate(self.base/'unknowns.json',lambda d:d.update(items=[row for row in d['items'] if row['id']!='HISTORY-REVALIDATION']))
        self.mutate(self.path,lambda d:d.update(unresolved_unknowns=13))
        self.reject()
    def test_expected_unknown_replacement_rejected(self):
        def replace(data):
            row=next(row for row in data['items'] if row['id']=='HISTORY-REVALIDATION')
            row['id']='UNEXPECTED-OPEN-OBLIGATION'
        self.mutate(self.base/'unknowns.json',replace)
        self.reject()
    def test_report_unknown_count_not_fourteen_rejected(self):
        self.mutate(self.path,lambda d:d.update(unresolved_unknowns=13))
        self.reject()
    def test_residual_obligations_paragraph_drift_rejected(self):
        companion=self.path.with_suffix('.md')
        companion.write_text(companion.read_text(encoding='utf-8').replace('FOURTEEN material residual obligations','Fifteen material residual obligations',1),encoding='utf-8')
        self.reject()
    def test_residual_obligation_id_drop_rejected(self):
        companion=self.path.with_suffix('.md')
        companion.write_text(companion.read_text(encoding='utf-8').replace(', `HISTORY-REVALIDATION`','',1),encoding='utf-8')
        self.reject()
    def test_false_professional_completion_replacement_rejected(self):
        companion=self.path.with_suffix('.md')
        text=companion.read_text(encoding='utf-8')
        text=text.replace(
            audit.EXPECTED_SECTION_7_PARAGRAPHS[-1],
            'This audit establishes organization-wide completion, product readiness, and an independent 10/10.',
            1,
        )
        companion.write_text(text,encoding='utf-8');self.reject()
    def test_adjacent_false_completion_paragraph_rejected(self):
        companion=self.path.with_suffix('.md')
        text=companion.read_text(encoding='utf-8').replace(
            audit.EXPECTED_SECTION_7_PARAGRAPHS[-1],
            audit.EXPECTED_SECTION_7_PARAGRAPHS[-1] +
            '\n\nThis audit establishes organization-wide completion, product readiness, and an independent 10/10.',
            1,
        )
        companion.write_text(text,encoding='utf-8');self.reject()
    def test_section_7_missing_access_limit_rejected(self):
        companion=self.path.with_suffix('.md')
        text=companion.read_text(encoding='utf-8').replace(
            audit.EXPECTED_SECTION_7_PARAGRAPHS[2] + '\n\n', '', 1)
        companion.write_text(text,encoding='utf-8');self.reject()
    def test_section_7_reordered_paragraphs_rejected(self):
        companion=self.path.with_suffix('.md')
        first,second=audit.EXPECTED_SECTION_7_PARAGRAPHS[2:]
        text=companion.read_text(encoding='utf-8').replace(first+'\n\n'+second,second+'\n\n'+first,1)
        companion.write_text(text,encoding='utf-8');self.reject()
    def test_section_7_truncated_paragraph_rejected(self):
        companion=self.path.with_suffix('.md')
        text=companion.read_text(encoding='utf-8').replace(
            ' No host/deploy action is authorized merely because a tool exists.', '', 1)
        companion.write_text(text,encoding='utf-8');self.reject()
    def mutate_semantic_coverage(self, func):
        def mutate(data):
            func(next(row for row in data['items'] if row['id']=='SEMANTIC-COVERAGE'))
        self.mutate(self.base/'unknowns.json',mutate)
    def test_stale_semantic_coverage_transition_rejected(self):
        self.mutate_semantic_coverage(lambda row:row.update(
            reason=row['reason'].replace('283 DIRECT', '258 DIRECT')
                                .replace('3929 paths', '3954 paths')))
        self.reject()
    def test_changed_semantic_coverage_total_rejected(self):
        self.mutate_semantic_coverage(lambda row:row.update(
            missing='3954 source leaves retain UNVERIFIED semantics; 371 of 4324 leaves are semantically classified'))
        self.reject()
    def test_changed_semantic_classified_count_rejected(self):
        self.mutate_semantic_coverage(lambda row:row.update(
            effect='Original exhaustive completeness cannot be claimed from 345 semantically classified leaves out of 4325.'))
        self.reject()
    def test_missing_marketplace_test_provenance_rejected(self):
        self.mutate_semantic_coverage(lambda row:row.update(
            reason=row['reason'].replace(' + 6 Marketplace tests', '')))
        self.reject()
    def test_missing_recorder_provenance_rejected(self):
        self.mutate_semantic_coverage(lambda row:row.update(
            reason=row['reason'].replace(' plus two app/Audit recorder paths', '')))
        self.reject()
    def test_missing_announcements_provenance_rejected(self):
        self.mutate_semantic_coverage(lambda row:row.update(
            reason=row['reason'].replace(' plus ten app/Announcements/** paths', '')))
        self.reject()
    def test_semantic_coverage_extra_key_rejected(self):
        self.mutate_semantic_coverage(lambda row:row.update(semantic_pass=False))
        self.reject()
    def test_semantic_coverage_nested_type_drift_rejected(self):
        self.mutate_semantic_coverage(lambda row:row.update(
            missing={'unverified': 3954, 'classified': 371, 'total': 4325}))
        self.reject()
    def test_each_retained_nonsemantic_unknown_substance_is_exact(self):
        ids=audit.EXPECTED_UNRESOLVED_IDS-{'SEMANTIC-COVERAGE'}
        for unknown_id in sorted(ids):
            with self.subTest(unknown_id=unknown_id):
                shutil.copy2(ROOT/'docs/evidence'/EVIDENCE/'unknowns.json',self.base/'unknowns.json')
                def alter(data):
                    row=next(row for row in data['items'] if row['id']==unknown_id)
                    row['closure_condition']='Closed; waived; no further action required.'
                self.mutate(self.base/'unknowns.json',alter)
                self.reject()
    def test_history_revalidation_false_closure_rejected(self):
        def alter(data):
            row=next(row for row in data['items'] if row['id']=='HISTORY-REVALIDATION')
            row.update(missing='Nothing remains',reason='Complete',effect='Product ready',
                       owner_route='Nobody',closure_condition='Closed; no further action required.')
        self.mutate(self.base/'unknowns.json',alter);self.reject()
    def test_nonsemantic_unknown_extra_key_rejected(self):
        def alter(data):
            next(row for row in data['items'] if row['id']=='ADMIN-STATE')['state']='OPEN'
        self.mutate(self.base/'unknowns.json',alter);self.reject()
    def test_nonsemantic_unknown_type_drift_rejected(self):
        def alter(data):
            next(row for row in data['items'] if row['id']=='INFRA-STATE')['reason']=['No host access']
        self.mutate(self.base/'unknowns.json',alter);self.reject()
    def test_resolved_independent_review_row_reintroduction_rejected(self):
        stale = {
            'id': 'INDEPENDENT-REVIEW',
            'missing': 'Independent review lifecycle/outcome for the adopted Platform audit-recorder and Announcements DIRECT slices',
            'reason': 'Fresh independent review remains pending.',
            'effect': 'Current exact-head review is not established.',
            'owner_route': 'PR185 reviewer',
            'closure_condition': 'Obtain review metadata.',
        }
        self.mutate(self.base/'unknowns.json',lambda data:data['items'].append(stale))
        self.reject()
    def test_resolved_independent_review_row_reintroduction_rejected_even_if_count_is_adjusted(self):
        stale = {'id':'INDEPENDENT-REVIEW','missing':'pending','reason':'pending','effect':'pending','owner_route':'PR185 reviewer','closure_condition':'pending'}
        self.mutate(self.base/'unknowns.json',lambda data:data['items'].append(stale))
        self.mutate(self.path,lambda data:data.update(unresolved_unknowns=15))
        self.reject()
    def test_stale_report_pending_review_state_rejected(self):
        self.mutate(self.path,lambda data:data['r3_review'].update(fresh_independent_rereview_required=True))
        self.reject()
    def test_reviewed_implementation_and_cleanup_heads_are_distinct_and_bound(self):
        self.mutate(self.path,lambda data:data['r3_review']['terminal_cleanup'].update(head='3eb62ef72c1e13412fa45d5b25d597d112d9ae7d'))
        self.reject()
    def test_external_review_provenance_type_drift_rejected(self):
        self.mutate(self.path,lambda data:data['r3_review']['latest_completed_rereview'].update(review_comment_id='5609072309'))
        self.reject()
    def test_workflow_count_inflation_rejected(self):
        self.mutate(self.path,lambda d:d['workflow_census'].update(total_workflows=78));self.reject()
    def test_direct_additions_binding_drift_rejected(self):
        self.mutate(self.path,lambda d:d.update(coverage_review_additions='organization-audit-20260907/other.tsv'));self.reject()
    def test_recorder_evidence_binding_drift_rejected(self):
        self.mutate(self.path,lambda d:d.update(coverage_review_recorder_additions='organization-audit-20260907/other.tsv'));self.reject()
    def test_announcements_evidence_binding_drift_rejected(self):
        self.mutate(self.path,lambda d:d.update(coverage_review_announcements_additions='organization-audit-20260907/other.tsv'));self.reject()
    def test_direct_additions_duplicate_base_path_rejected(self):
        base=(self.base/'coverage-review.tsv').read_text(encoding='utf-8').splitlines()
        p=self.base/'coverage-review-canonical-additions.tsv';header=p.read_text(encoding='utf-8').splitlines()[0]
        p.write_text(header+'\n'+base[1]+'\n',encoding='utf-8')
        self.reject()
    def test_direct_additions_missing_rejected(self):
        (self.base/'coverage-review-canonical-additions.tsv').unlink();self.reject()
    def test_tree_digest_matches_native_git(self):
        oid='d670460b4b4aece5915caf5c68d12f560a9fe3e4';raw=b'100644 a.txt\0'+bytes.fromhex(oid)
        expected=subprocess.run(['git','hash-object','-t','tree','--stdin'],input=raw,stdout=subprocess.PIPE,check=True,timeout=5).stdout.decode().strip()
        self.assertEqual(audit.tree_sha([{'path':'a.txt','mode':'100644','object_sha':oid}]),expected)
    def test_duplicate_inventory_path_rejected(self):
        row={'path':'a','mode':'100644','object_sha':'a'*40}
        with self.assertRaises(ValueError):audit.tree_sha([row,row])
    def test_unsafe_inventory_path_rejected(self):
        with self.assertRaises(ValueError):audit.tree_sha([{'path':'../bad','mode':'100644','object_sha':'a'*40}])
    def test_ledger_requires_inventories(self):
        with self.assertRaises(ValueError):audit.validate(self.path,ledger_output=self.root/'ledger.csv')

    def test_ledger_output_regular_create(self):
        path=self.root/'ledger.csv';audit.write_new_file_no_symlinks(path,b'ledger')
        self.assertEqual(path.read_bytes(),b'ledger')
    def test_ledger_output_existing_file_preserved(self):
        path=self.root/'ledger.csv';path.write_bytes(b'original')
        with self.assertRaises(ValueError):audit.write_new_file_no_symlinks(path,b'new')
        self.assertEqual(path.read_bytes(),b'original')
    def test_ledger_output_dangling_final_symlink_rejected(self):
        target=self.root/'target.csv';link=self.root/'ledger.csv';link.symlink_to(target)
        with self.assertRaises(ValueError):audit.write_new_file_no_symlinks(link,b'new')
        self.assertFalse(target.exists())
    def test_ledger_output_symlinked_ancestor_rejected(self):
        provider=self.root/'provider';provider.mkdir();link=self.root/'provider-link'
        link.symlink_to(provider,target_is_directory=True)
        with self.assertRaises(ValueError):audit.write_new_file_no_symlinks(link/'ledger.csv',b'new')
        self.assertFalse((provider/'ledger.csv').exists())
    def test_ledger_write_failure_preserves_concurrent_replacement(self):
        path=self.root/'ledger.csv';calls=0
        def replace_then_fail(_fd):
            nonlocal calls
            calls+=1
            path.write_bytes(b'unrelated replacement')
            raise OSError('simulated ledger write failure')
        with mock.patch.object(audit.os,'fsync',side_effect=replace_then_fail), \
             mock.patch.object(audit.os,'unlink',side_effect=AssertionError('pathname rollback is forbidden')):
            with self.assertRaisesRegex(ValueError,'refusing ledger'):
                audit.write_new_file_no_symlinks(path,b'generated ledger')
        self.assertEqual(calls,1)
        self.assertEqual(path.read_bytes(),b'unrelated replacement')

if __name__=='__main__':unittest.main()
