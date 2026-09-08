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
    def test_rejects_group_source_change_and_accepts_consumer_only_change(self):
        with tempfile.TemporaryDirectory(prefix='atlas-group-') as td:
            base=Path(td);current=base/'atlas';evidence=base/'evidence';audit_root=base/'audit'
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
            rules={'repository':'Oteryn/Oteryn-Atlas','main_sha':historical,'root_tree_sha':historical_tree,'grouped_rules':[{'pattern':'web/creature-gameplay/shards/**','count':2,'state':'GROUPED','basis':'manifest+digest+bounded-schema+consumer+4 edge samples'}]}
            write(evidence/rules_rel,json.dumps(rules));run(evidence,'add','.');run(evidence,'commit','-qm','evidence');publication=run(evidence,'rev-parse','HEAD')
            rules_blob=run(evidence,'rev-parse','HEAD:'+rules_rel.as_posix())
            blobs={p:run(current,'rev-parse',head+':'+p) for p in ['web/creature-gameplay/manifest.json','src/browser/creature-gameplay-profiles.mjs','src/browser/loader.mjs','tests/fullworld-runtime/creature-gameplay-runtime-safety.test.mjs','tests/verification/qualification-gameplay-contract.test.mjs']}
            group={'schema_version':1,'groups':[{'id':atlas.GROUP_ID,'repository':'atlas','disposition':'GROUPED','path_prefix':'web/creature-gameplay/shards/','expected_count':2,'historical_evidence':{'repository':'Oteryn/Oteryn-Atlas','publication_commit':publication,'coverage_rules_path':rules_rel.as_posix(),'coverage_rules_blob':rules_blob,'audited_main_sha':historical,'audited_main_tree':historical_tree,'pattern':'web/creature-gameplay/shards/**','count':2,'basis':'manifest+digest+bounded-schema+consumer+4 edge samples'},'current_revalidation':{'source_commit':head,'source_tree':head_tree,'current_blobs':blobs},'limitations':'fixture limitation'}]}
            write(audit_root/'docs/evidence/organization-audit-20260907/coverage-groups.json',json.dumps(group))
            result=atlas.verify(audit_root,current,evidence);self.assertEqual(result['grouped_paths'],2)
            write(current/'web/creature-gameplay/shards/a.json','{"changed":true}\n');run(current,'add','.');run(current,'commit','-qm','bad')
            bad=run(current,'rev-parse','HEAD')
            group['groups'][0]['current_revalidation']['source_commit']=bad;group['groups'][0]['current_revalidation']['source_tree']=run(current,'rev-parse','HEAD^{tree}')
            group['groups'][0]['current_revalidation']['current_blobs']={p:run(current,'rev-parse',bad+':'+p) for p in blobs}
            write(audit_root/'docs/evidence/organization-audit-20260907/coverage-groups.json',json.dumps(group))
            with self.assertRaisesRegex(ValueError,'grouped shard/manifest source changed|grouped tree identity changed'):
                atlas.verify(audit_root,current,evidence)

if __name__=='__main__':unittest.main()
