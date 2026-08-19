#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, json, subprocess, tempfile
from pathlib import Path
SCRIPT=Path(__file__).with_name('verify_ai_review_evidence.py')
spec=importlib.util.spec_from_file_location('verify_ai_review_evidence',SCRIPT); assert spec and spec.loader
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
POLICY=json.loads((Path(__file__).resolve().parents[2]/'ecosystem/ai-review-policy.json').read_text(encoding='utf-8'))

def git(repo: Path,*args: str)->str:
    return subprocess.check_output(['git',*args],cwd=repo,text=True).strip()

def make_repo()->tuple[Path,str,str]:
    repo=Path(tempfile.mkdtemp(prefix='oteryn-review-evidence-')); git(repo,'init')
    git(repo,'config','user.email','test@example.invalid'); git(repo,'config','user.name','test')
    (repo/'a.txt').write_text('one\n',encoding='utf-8'); git(repo,'add','a.txt'); git(repo,'commit','-m','one'); first=git(repo,'rev-parse','HEAD')
    (repo/'a.txt').write_text('two\n',encoding='utf-8'); git(repo,'commit','-am','two'); second=git(repo,'rev-parse','HEAD')
    return repo,first,second

def body(head: str,fp: str,tier='R2',klass='deep',reviewer='codex',source='https://github.com/Oteryn/Test/pull/7#issuecomment-9')->str:
    return '\n'.join(['<!-- OTERYN_AI_REVIEW_V1 -->',f'REVIEW_TIER: {tier}',f'REVIEW_FINGERPRINT: {fp}',f'REVIEWED_HEAD: {head}',f'REVIEWER_CLASS: {klass}',f'REVIEWER_ID: {reviewer}','RESULT: PASS',f'REVIEW_SOURCE_URL: {source}','FINDINGS: 0'])

def attestation(head: str,fp: str,**kw)->dict:
    return {'id':1,'author_association':kw.pop('association','OWNER'),'user':{'login':kw.pop('attestor','blakinio')},'body':body(head,fp,**kw)}

def source(head: str,fp: str,**kw)->dict:
    return {'html_url':'https://github.com/Oteryn/Test/pull/7#issuecomment-9','issue_url':'https://api.github.com/repos/Oteryn/Test/issues/7','user':{'login':kw.pop('login','chatgpt-codex-connector[bot]')},'body':body(head,fp,**kw)}

def run_verify(comment: dict,src: dict,repo: Path,final: str,tier='R2',fp='abc'):
    original=m.fetch_review_source
    m.fetch_review_source=lambda repository,pr_number,source_url,token: ('issue_comment',src)
    try:
        return m.verify_records([comment],policy=POLICY,repo_root=repo,tier=tier,fingerprint=fp,head=final,repository='Oteryn/Test',pr_number=7,token='x')
    finally:
        m.fetch_review_source=original

def expect_fail(fn):
    try: fn()
    except RuntimeError: return
    raise AssertionError('verification unexpectedly passed')

def test_matching_authenticated_source_passes():
    repo,reviewed,final=make_repo(); found=run_verify(attestation(reviewed,'abc'),source(reviewed,'abc'),repo,final)
    assert found['review_source_author']=='chatgpt-codex-connector[bot]'

def test_self_authored_external_source_fails():
    repo,reviewed,final=make_repo(); expect_fail(lambda: run_verify(attestation(reviewed,'abc'),source(reviewed,'abc',login='blakinio'),repo,final))

def test_untrusted_source_author_fails():
    repo,reviewed,final=make_repo(); expect_fail(lambda: run_verify(attestation(reviewed,'abc'),source(reviewed,'abc',login='evil-bot'),repo,final))

def test_source_body_mismatch_fails():
    repo,reviewed,final=make_repo(); expect_fail(lambda: run_verify(attestation(reviewed,'abc'),source(reviewed,'wrong'),repo,final))

def test_untrusted_attestor_fails():
    repo,reviewed,final=make_repo(); expect_fail(lambda: run_verify(attestation(reviewed,'abc',association='NONE'),source(reviewed,'abc'),repo,final))

def test_spark_cannot_satisfy_r2():
    repo,reviewed,final=make_repo(); c=attestation(reviewed,'abc',reviewer='codex_spark'); s=source(reviewed,'abc',reviewer='codex_spark')
    expect_fail(lambda: run_verify(c,s,repo,final))

def test_deep_codex_can_satisfy_r1():
    repo,reviewed,final=make_repo(); c=attestation(reviewed,'abc',tier='R1',klass='deep'); s=source(reviewed,'abc',tier='R1',klass='deep')
    assert run_verify(c,s,repo,final,tier='R1')['reviewer_id']=='codex'

def test_duplicate_fields_are_rejected():
    text=body('a'*40,'abc')+'\nRESULT: PASS'
    assert m.parse_record(text) is None

def test_source_url_must_be_exact_same_pr_object():
    for url in ['https://github.com/Oteryn/Test/pull/7x#issuecomment-9','https://github.com/Oteryn/Test/pull/8#issuecomment-9','https://github.com/Oteryn/Test/pull/7#issuecomment-9/evil']:
        try: m.fetch_review_source('Oteryn/Test',7,url,'x')
        except RuntimeError: continue
        raise AssertionError(url)

def main()->int:
    tests=[v for n,v in sorted(globals().items()) if n.startswith('test_') and callable(v)]
    for test in tests: test(); print('PASS',test.__name__)
    print(f'ai review evidence tests PASS: {len(tests)}'); return 0

if __name__=='__main__': raise SystemExit(main())
