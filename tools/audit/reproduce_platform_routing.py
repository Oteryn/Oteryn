#!/usr/bin/env python3
"""Reproduce routing observations on exact source; never runs a provider workflow."""
import argparse, hashlib, importlib.util, json, os, pathlib, subprocess, sys, tempfile

def run(cmd, cwd):
    return subprocess.run(cmd,cwd=cwd,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=20).stdout.strip()
def load(path, name):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod
def blob(path):
    b=path.read_bytes();return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def write_new(path, text):
    path=pathlib.Path(path).absolute()
    parent=path.parent
    if not parent.is_dir() or parent.is_symlink() or pathlib.Path(os.path.realpath(parent))!=parent:
        raise ValueError('existing nonsymlink output parent required')
    flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,'O_NOFOLLOW',0)
    try:
        fd=os.open(path,flags,0o600)
    except FileExistsError as exc:
        raise ValueError('refusing output overwrite or symlink') from exc
    try:
        with os.fdopen(fd,'w',encoding='utf-8',newline='') as handle:
            handle.write(text)
    except Exception:
        try:path.unlink()
        except OSError:pass
        raise

def probe(root):
    gate=root/'scripts/ci/required_test_gate.py'
    sources={p:blob(root/p) for p in ('scripts/ci/classify_changes.py','scripts/ci/required_test_gate.py','tests/ci/fixtures/change-routing-cases.json')}
    expected={'scripts/ci/classify_changes.py':'8f194c0c0a9967d9dc8dc3fbe228984e56b8f82a','scripts/ci/required_test_gate.py':'3d61ff97df7fdfed01bb2ef3104aeff7b7f4e3bf','tests/ci/fixtures/change-routing-cases.json':'11a17e3f77cacf629281e39a8c50da3e81d99c95'}
    if sources!=expected:raise ValueError('source generation mismatch')
    classifier=load(root/'scripts/ci/classify_changes.py','audited_classifier')
    cases=[]
    for name, expected_ci in [('type_only',True),('type_and_docs',True),('modify_and_docs',True),('delete_and_docs',True),('rename_into_docs',True),('rename_within_runtime',True),('mode_and_docs',True),('docs_only',False)]:
        with tempfile.TemporaryDirectory(prefix='audit-routing-') as td:
            d=pathlib.Path(td);g=lambda *args:run(['git',*args],d)
            g('init','-q');g('config','user.name','Audit fixture');g('config','user.email','audit@example.invalid');g('config','commit.gpgsign','false');g('config','core.filemode','true');g('config','diff.renames','true')
            (d/'app/Identity').mkdir(parents=True);(d/'docs').mkdir(); runtime=d/'app/Identity/AuditFixture.php';docs=d/'docs/audit-fixture.md'
            runtime.write_text('<?php\n// deterministic fixture\nreturn 1;\n');docs.write_text('baseline\n');g('add','.');g('commit','-qm','base');base=g('rev-parse','HEAD')
            if name!='type_only':docs.write_text('changed\n')
            if name.startswith('type_'):runtime.unlink();runtime.symlink_to('../../docs/audit-fixture.md')
            elif name=='modify_and_docs':runtime.write_text('<?php\nreturn 2;\n')
            elif name=='delete_and_docs':runtime.unlink()
            elif name=='rename_into_docs':runtime.rename(d/'docs/AuditFixture.php')
            elif name=='rename_within_runtime':runtime.rename(d/'app/Identity/RenamedFixture.php')
            elif name=='mode_and_docs':runtime.chmod(0o755)
            g('add','-A');g('commit','-qm','case');head=g('rev-parse','HEAD')
            original=os.getcwd()
            try:
                os.chdir(d); paths=classifier.changed_paths(base,head)
            finally:os.chdir(original)
            classification=classifier.classify_paths(paths)
            ci=classification['gates']['ci']
            decision=subprocess.run([sys.executable,str(gate),'--classification-result','success','--ci-required',str(ci).lower(),'--runtime-tests-result','skipped'],capture_output=True,text=True,timeout=20)
            cases.append({'case':name,'full_status_diff':g('diff','--name-status','--find-renames',base,head).splitlines(),'classifier_input':paths,'classes':classification['classes'],'gates':classification['gates'],'expected_runtime_required':expected_ci,'routing_matches_expectation':ci==expected_ci,'skipped_runtime_gate_exit':decision.returncode,'gate_message':decision.stdout.strip()})
    fixture_count=classifier.validate_policy_contract(root/'tests/ci/fixtures/change-routing-cases.json')
    false_neg=[x['case'] for x in cases if x['expected_runtime_required'] and not x['gates']['ci']]
    if false_neg!=['type_and_docs','rename_into_docs']:raise AssertionError('characterization changed: '+repr(false_neg))
    if any(x['skipped_runtime_gate_exit']!=0 for x in cases if x['case'] in false_neg):raise AssertionError('gate did not reproduce unsafe N/A')
    return {'schema_version':1,'repository':'Oteryn/Oteryn-Platform','source_commit':'de917b3477a1de0667531380de3660e8b2ab59aa','source_blobs':sources,'python':sys.version.split()[0],'git':run(['git','--version'],root),'policy_fixture_count':fixture_count,'cases':cases,'false_negative_count':len(false_neg),'reproduction_result':'REPRODUCED','product_result':'FAIL_FOR_TWO_ROUTING_CASES','production_or_merge_bypass_tested':False,'isolation':'temporary local Git fixtures, no remote configured, deleted after probes'}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source-root',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
    data=probe(a.source_root.resolve());write_new(a.output,json.dumps(data,indent=2)+'\n');print(json.dumps({k:v for k,v in data.items() if k!='cases'},indent=2))
