#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess
import tempfile
import unittest
import verify_atlas_group as atlas


def run(root,*args):
    return subprocess.run(['git','-C',str(root),*args],check=True,stdout=subprocess.PIPE,text=True).stdout.strip()


def write(path,text):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)


class AtlasGroupTests(unittest.TestCase):
    def make_repo(self,root):
        subprocess.run(['git','init','-q',str(root)],check=True)
        run(root,'config','user.name','Audit fixture');run(root,'config','user.email','audit@example.invalid');run(root,'config','commit.gpgsign','false')

    def fixture(self,base):
        current=base/'atlas';evidence=base/'evidence';audit_root=base/'audit'
        self.make_repo(current)
        for name in ['web/creature-gameplay/shards/a.json','web/creature-gameplay/shards/b.json']:
            write(current/name,'{}\n')
        write(current/'web/creature-gameplay/manifest.json','{}\n')
        for name in ['src/browser/creature-gameplay-profiles.mjs','src/browser/loader.mjs','tests/fullworld-runtime/creature-gameplay-runtime-safety.test.mjs','tests/verification/qualification-gameplay-contract.test.mjs']:
            write(current/name,'export default 1;\n')
        run(current,'add','.');run(current,'commit','-qm','base');historical=run(current,'rev-parse','HEAD');historical_tree=run(current,'rev-parse','HEAD^{tree}')
        write(current/'src/browser/creature-gameplay-profiles.mjs','export default 2;\n');run(current,'add','.');run(current,'commit','-qm','consumer');head=run(current,'rev-parse','HEAD');head_tree=run(current,'rev-parse','HEAD^{tree}')
        self.make_repo(evidence)
        rules_rel=Path('docs/evidence/repository-audit-2026-09-06/round-4/coverage-rules.json')
        basis='manifest+digest+bounded-schema+consumer+4 edge samples'
        rules={'repository':'Oteryn/Oteryn-Atlas','main_sha':historical,'root_tree_sha':historical_tree,'grouped_rules':[{'pattern':'web/creature-gameplay/shards/**','count':2,'state':'GROUPED','basis':basis}]}
        write(evidence/rules_rel,json.dumps(rules));run(evidence,'add','.');run(evidence,'commit','-qm','evidence');publication=run(evidence,'rev-parse','HEAD')
        rules_blob=run(evidence,'rev-parse','HEAD:'+rules_rel.as_posix())
        paths=['web/creature-gameplay/manifest.json','src/browser/creature-gameplay-profiles.mjs','src/browser/loader.mjs','tests/fullworld-runtime/creature-gameplay-runtime-safety.test.mjs','tests/verification/qualification-gameplay-contract.test.mjs']
        blobs={p:run(current,'rev-parse',head+':'+p) for p in paths}
        candidate={'id':atlas.GROUP_ID,'repository':'atlas','disposition':'REVALIDATION_FAILED_NOT_ADOPTED','path_prefix':'web/creature-gameplay/shards/','expected_count':2,
                   'historical_evidence':{'repository':'Oteryn/Oteryn-Atlas','publication_commit':publication,'coverage_rules_path':rules_rel.as_posix(),'coverage_rules_blob':rules_blob,'audited_main_sha':historical,'audited_main_tree':historical_tree,'pattern':'web/creature-gameplay/shards/**','count':2,'basis':basis},
                   'current_revalidation':{'source_commit':head,'source_tree':head_tree,'current_blobs':blobs,'qualification_status':'FAILED_CURRENT_CONSUMER_IMPACT_ROUTING_1_PASS_1_FAIL'},
                   'depth':'GROUPED_REVALIDATION_CANDIDATE_REJECTED','scope':'Identity-only. Historical semantics are NOT carried forward; both leaves remain UNVERIFIED.','limitations':'fixture limitation',
                   'evaluation':{'qualification_run':1,'qualification_job':2,'focused_current_consumer_tests':{'passed':1,'failed':1},'outcome':'REJECTED_NOT_COUNTED_AS_GROUPED'}}
        group={'schema_version':1,'groups':[],'rejected_candidates':[candidate]}
        write(audit_root/'docs/evidence/organization-audit-20260907/coverage-groups.json',json.dumps(group))
        return current,evidence,audit_root,group,head,blobs

    def test_rejected_candidate_reproduces_identity_without_eligibility(self):
        with tempfile.TemporaryDirectory(prefix='atlas-group-') as td:
            current,evidence,audit_root,group,head,blobs=self.fixture(Path(td))
            result=atlas.verify(audit_root,current,evidence)
            self.assertEqual(result['result'],'REJECTED_GROUP_IDENTITY_REPRODUCED_NOT_SEMANTIC_COVERAGE')
            self.assertEqual(result['candidate_paths'],2)
            self.assertFalse(result['semantic_carry_forward'])
            self.assertFalse(result['adopted_grouped_coverage'])
            self.assertEqual(result['consumer_tests'],{'passed':1,'failed':1})

    def test_rejected_candidate_requires_failed_consumer_qualification(self):
        with tempfile.TemporaryDirectory(prefix='atlas-group-') as td:
            current,evidence,audit_root,group,head,blobs=self.fixture(Path(td))
            group['rejected_candidates'][0]['evaluation']['focused_current_consumer_tests']['failed']=0
            write(audit_root/'docs/evidence/organization-audit-20260907/coverage-groups.json',json.dumps(group))
            with self.assertRaisesRegex(ValueError,'failed current consumer qualification'):
                atlas.verify(audit_root,current,evidence)

    def test_rejected_candidate_cannot_be_moved_to_adopted_groups(self):
        with tempfile.TemporaryDirectory(prefix='atlas-group-') as td:
            current,evidence,audit_root,group,head,blobs=self.fixture(Path(td))
            group['groups']=group.pop('rejected_candidates')
            with write_context(audit_root/'docs/evidence/organization-audit-20260907/coverage-groups.json',json.dumps(group)):
                with self.assertRaisesRegex(ValueError,'must not be present in adopted groups|missing'):
                    atlas.verify(audit_root,current,evidence)

    def test_identity_change_still_fails_closed(self):
        with tempfile.TemporaryDirectory(prefix='atlas-group-') as td:
            current,evidence,audit_root,group,head,blobs=self.fixture(Path(td))
            write(current/'web/creature-gameplay/shards/a.json','{"changed":true}\n');run(current,'add','.');run(current,'commit','-qm','bad')
            bad=run(current,'rev-parse','HEAD')
            candidate=group['rejected_candidates'][0]
            candidate['current_revalidation']['source_commit']=bad;candidate['current_revalidation']['source_tree']=run(current,'rev-parse','HEAD^{tree}')
            candidate['current_revalidation']['current_blobs']={p:run(current,'rev-parse',bad+':'+p) for p in blobs}
            write(audit_root/'docs/evidence/organization-audit-20260907/coverage-groups.json',json.dumps(group))
            with self.assertRaisesRegex(ValueError,'identity changed'):
                atlas.verify(audit_root,current,evidence)


class write_context:
    def __init__(self,path,text): self.path=path;self.text=text;self.old=None
    def __enter__(self): self.old=self.path.read_text();self.path.write_text(self.text);return self
    def __exit__(self,*args): self.path.write_text(self.old)


if __name__=='__main__':unittest.main()
