# Reproduce the evidence without changing the repository

Use a separate temporary directory and the exact audited source. Do not run these commands in a dirty user worktree, update system Python aliases, install tools into the user's environment, dispatch GitHub workflows, or change settings. The snippets are audit reproduction instructions, not new repository tests or automatic execution authority.

## 1. Source identity

With an existing readable clone, use `git show` to obtain source bytes; no checkout or branch change is needed. A new temporary clone is also acceptable. The audited commit is `0c493896040072badeff1f333eb83d7114a993ff`, not moving `main`.

```text
git rev-parse 0c493896040072badeff1f333eb83d7114a993ff^{tree}
# 77c33f4c2d3bffcd5983e35928d870d618cb5f68

git rev-parse 0c493896040072badeff1f333eb83d7114a993ff:tools/governance/governance_drift_audit.py
# 8f165e91ad0bb06131f1955264a873a487369ae5

git rev-parse 0c493896040072badeff1f333eb83d7114a993ff:ecosystem/governance-desired-state.json
# 049a3fff02451fdbc8ec75dd6bc017466911bb94

git rev-parse 0c493896040072badeff1f333eb83d7114a993ff:.github/workflows/ci.yml
# a198350259d8f9d082732cb0c4d99f90c6bf389c
```

These identities and the before/after byte checks distinguish unchanged native validation from a rewritten substitute.

## 2. Recalculate the CI observations

From this evidence directory, use only Python's standard library. This operates on the retained historical data; it performs no API requests.

```python
import csv, json, math, statistics
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime
root = Path('.')
index = json.loads((root/'evidence/ci-run-index.json').read_text())
rows = [dict(zip(index['columns'], r)) for r in index['rows']]
assert len(rows) == len({r['id'] for r in rows}) == 268
times = []
for i in (1, 2, 3):
    with (root/f'evidence/ci-meta-times-{i}.csv').open(newline='') as f:
        times.extend(csv.DictReader(f))
by_id = {int(r['id']): r for r in times}
meta = [r for r in rows if r['workflow_id'] == 336924336]
assert len(times) == len(by_id) == 165
assert set(by_id) == {r['id'] for r in meta}
for r in meta:
    r.update({k: v for k, v in by_id[r['id']].items() if k != 'id'})
def dt(s):
    return datetime.fromisoformat(s.replace('Z', '+00:00'))
values = sorted((dt(r['updated_at'])-dt(r['created_at'])).total_seconds()
                for r in meta)
groups = defaultdict(set)
for r in meta:
    groups[(r['workflow_id'], r['event'], r['head_sha'])].add(r['conclusion'])
print(Counter(r['conclusion'] for r in rows))
print(Counter(r['conclusion'] for r in meta))
print(statistics.median(values), values[math.ceil(.95*len(values))-1], max(values))
print([key for key, states in groups.items() if {'success','failure'} <= states])
```

Expected: total 183 success/68 failure/12 cancelled/5 skipped; META 112/45/8; latency proxy `12.0, 27.0, 37.0`; empty list of META mixed success/failure groups. This proves neither universal absence of flakes nor that every failing PR was intentional TDD.

## 3. Reproduce AUD-10 and AUD-11

The following extraction was checked independently against the exact Git workflow: the extracted 1,980 bytes have SHA-256 `ca07ab50e7032d51af4322d1c1af6ed8520209f0719473adaf6115ca5b00a7ef`. Only YAML indentation is removed.

Run with `repo` pointing to a readable clone; all diagnostic files are written to a newly allocated temporary directory, not to that clone. The original implementation and policy are never edited.

```python
import copy, hashlib, json, subprocess, sys, tempfile, textwrap
from pathlib import Path
repo = Path('/path/to/readable/clone')  # set this one path
commit = '0c493896040072badeff1f333eb83d7114a993ff'
def source(path):
    return subprocess.run(['git','-C',str(repo),'show',f'{commit}:{path}'],
                          check=True,capture_output=True).stdout
def git_blob(data):
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
module = source('tools/governance/governance_drift_audit.py')
policy_bytes = source('ecosystem/governance-desired-state.json')
workflow = source('.github/workflows/ci.yml').decode('utf-8')
assert git_blob(module) == '8f165e91ad0bb06131f1955264a873a487369ae5'
assert git_blob(policy_bytes) == '049a3fff02451fdbc8ec75dd6bc017466911bb94'
tail = workflow.split('      - name: Validate simplified governance desired state\n',1)[1]
tail = tail.split('\n      - name:',1)[0]
inline = textwrap.dedent(tail.split("python3 - <<'PY'\n",1)[1]
                        .split('\n          PY',1)[0])+'\n'
assert hashlib.sha256(inline.encode()).hexdigest() == 'ca07ab50e7032d51af4322d1c1af6ed8520209f0719473adaf6115ca5b00a7ef'
policy = json.loads(policy_bytes)
fields = ['required_gate','merge_queue','allow_auto_merge','strict_required_status_checks',
          'required_approvals','codeowner_review_required','conversation_resolution',
          'linear_history','force_pushes','deletions','broad_bypass']
observed = {'repositories': [dict(repository=r['repository'],
            **{k:r[k] for k in fields}) for r in policy['permanent_repositories']]}
with tempfile.TemporaryDirectory(prefix='oteryn-audit-reproduce-') as temp:
    root = Path(temp)
    (root/'governance_drift_audit.py').write_bytes(module)
    (root/'inline.py').write_text(inline,encoding='utf-8')
    (root/'ecosystem').mkdir()
    def write(name, value):
        (root/name).write_text(json.dumps(value),encoding='utf-8')
    def run(label, arguments):
        result = subprocess.run([sys.executable,'-B',*arguments],cwd=root,
                                capture_output=True,text=True,timeout=15)
        print(label, result.returncode, result.stdout, result.stderr)
    def cli(label, desired, live):
        write('desired.json',desired); write('live.json',live)
        run(label,['governance_drift_audit.py','--desired-state','desired.json',
                   '--live-state','live.json'])
    cli('empty',{'schema_version':2,'permanent_repositories':[]},{'repositories':[]})
    cli('missing',{'schema_version':2},{'repositories':[]})
    cli('four-without-observations',policy,{'repositories':[]})
    cli('four-matching-synthetic',policy,observed)
    write('ecosystem/governance-desired-state.json',policy)
    run('canonical-inline',['inline.py'])
    numeric = copy.deepcopy(policy)
    numeric['permanent_repositories'][0]['merge_queue'] = 1
    write('ecosystem/governance-desired-state.json',numeric)
    run('numeric-inline',['inline.py'])
    cli('numeric-versus-boolean',numeric,observed)
    assert (root/'governance_drift_audit.py').read_bytes() == module
```

Expected exits in order: `0,3,2,0,0,0,1`. The first result is TARGET with no assessed repository. The last is META DRIFT with expected integer 1 / actual boolean true. These are synthetic inputs, not real GitHub observations. The two inline results are not whole-workflow runs. Full recorded output is in `evidence/native-probe-results.json`.

## 4. Native-suite and server evidence

Prior commands and failure classes are retained in E04. Re-running the existing six suites in a safe exact checkout may reproduce current-environment behavior; do not change a test to obtain a green result. The seventh orphan test is expected to fail import. A current execution is new evidence and must not overwrite the historical outcome.

Read-only GitHub queries used or sufficient to refresh the corresponding settings include `gh api --method GET` on:

```text
repos/Oteryn/Oteryn
repos/Oteryn/Oteryn/branches/main/protection
repos/Oteryn/Oteryn/rulesets?includes_parents=true
repos/Oteryn/Oteryn/actions/workflows
repos/Oteryn/Oteryn/actions/permissions
repos/Oteryn/Oteryn/actions/permissions/workflow
repos/Oteryn/Oteryn/environments
repos/Oteryn/Oteryn/actions/runners
repos/Oteryn/Oteryn/private-vulnerability-reporting
repos/Oteryn/Oteryn/code-scanning/default-setup
repos/Oteryn/Oteryn/code-scanning/analyses
repos/Oteryn/Oteryn/dependabot/alerts?state=open
repos/Oteryn/Oteryn/releases
repos/Oteryn/Oteryn/tags
repos/Oteryn/Oteryn/deployments
repos/Oteryn/Oteryn/hooks
```

Some require permissions unavailable to a managed connector. Do not broaden credentials, expose tokens, read secret values, or call mutation endpoints merely to reproduce a snapshot. Later responses can legitimately differ. E01 records the historical responses and their limits. Queue configuration was read through GraphQL; no nonexistent `requiresMergeQueue` field or mutation-based bypass proof is invented.
