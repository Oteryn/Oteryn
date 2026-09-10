#!/usr/bin/env python3
"""Fail-closed verifier for the META R6 prompt-family lifecycle DIRECT candidate."""
from __future__ import annotations
import argparse, contextlib, csv, hashlib, io, json, subprocess, tempfile
from pathlib import Path
import organization_audit
import verify_report

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE_REL = Path('docs/evidence/organization-audit-20260907/r3-meta-r6-prompts-direct-candidate.json')
CANDIDATE_SHA256 = '62b7f49af1434667f9ed293c896bc7f9b285cb8652883f00915607f0ce65381a'
REPORT_REL = Path('docs/evidence/OTERYN-ORGANIZATION-COMPREHENSIVE-AUDIT-20260907.json')
PLAN_REL = Path('docs/evidence/organization-audit-20260907/collection-plan.json')
FINDINGS_REL = Path('docs/evidence/organization-audit-20260907/finding-register.tsv')
SOURCE = '1a01c5b3e08666a82245b1cac78da3736c65e785'
SOURCE_TREE = 'f084e824ec5e14d5909c9750d906d91d51425fd5'
SUBTREE = 'docs/agents/prompts'
SUBTREE_TREE = '0b825e18cde3cd928dfe569acf9ce6c0dc71cfe5'
DATED_MAIN = '3b39e0be05aef008f1bd442821daefa898a201dd'
LEDGER_SHA = '27654f5f724d9857912e69fd036712dd00d63882ebf8e9c1411c26c66eaeef41'
INVENTORY_IDS = {'meta', 'game', 'platform', 'atlas', 'migration_archive'}
EXPECTED_META_AUD_05 = {'id':'META-AUD-05','priority':'P2','repository':'meta','state':'PARTIALLY_REPAIRED','scope':'governance','title':'Historical authority and merge-up conflict','evidence':'META-153 | Current access policy separates MQ candidate refresh from source-head churn. Historical/open PR authority liveness is not exhaustively revalidated.','owner_route':'Oteryn/Oteryn#153; evidence continuation #186','closure_condition':'Classify remaining operative-looking documents/PRs against current v3 authority without deleting historical evidence.'}

def require(value, message):
    if not value: raise ValueError(message)

def json_exact(actual, expected, path='root'):
    require(type(actual) is type(expected), path + ' JSON type drift')
    if isinstance(expected, dict):
        require(list(actual) == list(expected), path + ' key set/order drift')
        for key in expected: json_exact(actual[key], expected[key], path + '.' + key)
    elif isinstance(expected, list):
        require(len(actual) == len(expected), path + ' list length drift')
        for index, (item, wanted) in enumerate(zip(actual, expected)): json_exact(item, wanted, f'{path}[{index}]')
    else: require(actual == expected, path + ' value drift')

def read_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate JSON key: ' + key); result[key] = value
        return result
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=pairs)

def expected_candidate(root=ROOT):
    raw = (root / CANDIDATE_REL).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == CANDIDATE_SHA256, 'candidate complete-file SHA drift')
    return read_json(root / CANDIDATE_REL)

def validate_candidate(candidate, expected=None):
    json_exact(candidate, expected or expected_candidate(), 'candidate')

def git(root, *args):
    return subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', *args], cwd=root, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60).stdout.strip()

def validate_source(root, candidate):
    require(git(root, 'rev-parse', SOURCE + '^{tree}') == SOURCE_TREE, 'source tree drift')
    require(git(root, 'rev-parse', SOURCE + ':' + SUBTREE) == SUBTREE_TREE, 'source subtree drift')
    expected_paths = [row['path'] for row in candidate['paths']]
    actual_paths = git(root, 'ls-tree', '-r', '--name-only', SOURCE, SUBTREE).splitlines()
    require(actual_paths == sorted(expected_paths + [row['path'] for row in candidate['excluded_already_direct_paths']]) and len(set(expected_paths)) == 11, 'exact ordered family path set drift')
    for row in candidate['paths']:
        spec = SOURCE + ':' + row['path']
        require(git(root, 'cat-file', '-t', spec) == 'blob', 'source object type drift: ' + row['path'])
        blob = git(root, 'rev-parse', spec)
        data = subprocess.run(['git', 'cat-file', 'blob', blob], cwd=root, check=True, stdout=subprocess.PIPE, timeout=60).stdout
        require(blob == row['blob_sha'], 'source blob drift: ' + row['path'])
        require(hashlib.sha256(data).hexdigest() == row['full_file_sha256'], 'source byte digest drift: ' + row['path'])
        require(git(root, 'rev-parse', DATED_MAIN + ':' + row['path']) == blob, 'dated-main identity drift: ' + row['path'])

def validate_finding(root, candidate):
    with (root / FINDINGS_REL).open(encoding='utf-8', newline='') as handle:
        rows = list(csv.DictReader(handle, delimiter='\t'))
    found = [row for row in rows if row['id'] == 'META-AUD-05']
    require(len(found) == 1, 'META-AUD-05 missing or duplicated')
    json_exact(found[0], EXPECTED_META_AUD_05, 'META-AUD-05 register row')
    expected_binding = dict(EXPECTED_META_AUD_05, candidate_disposition='RECONFIRMED_NOT_CLOSED_NOT_DOWNGRADED_NOT_DUPLICATED')
    json_exact(candidate['finding_bindings'], [expected_binding], 'candidate finding bindings')

def collect_inventories(root, output):
    plan = read_json(root / PLAN_REL)
    plan['snapshots'] = [item for item in plan['snapshots'] if item['id'] in INVENTORY_IDS]
    require({item['id'] for item in plan['snapshots']} == INVENTORY_IDS, 'inventory set drift')
    with contextlib.redirect_stdout(io.StringIO()): organization_audit.collect(plan, output)
    return output / 'inventories'

def validate_accounting(root, candidate, inventory_dir=None):
    temp = None
    if inventory_dir is None:
        temp = tempfile.TemporaryDirectory(prefix='meta-r6-')
        inventory_dir = collect_inventories(root, Path(temp.name) / 'audit')
    try:
        result = verify_report.validate(root / REPORT_REL, inventory_dir=inventory_dir)
        ledger, grouped = verify_report.rebuild_ledger(root / REPORT_REL, inventory_dir)
    finally:
        if temp: temp.cleanup()
    require(result.get('tree_and_ledger_verified') is True, 'authoritative ledger not rebuilt')
    require(hashlib.sha256(ledger).hexdigest() == LEDGER_SHA, 'canonical ledger SHA drift')
    expected = {'source_leaves':4325,'scoped_review_paths':283,'grouped_revalidated_paths':113,'unverified_semantics':3929,'semantically_classified_paths':396}
    for key, value in expected.items(): require(type(result.get(key)) is int and result[key] == value, 'canonical accounting drift: ' + key)
    rows = list(csv.DictReader(io.StringIO(ledger.decode())))
    wanted = {row['path']: row['blob_sha'] for row in candidate['paths']}
    selected = [row for row in rows if row['repository_id'] == 'meta' and row['path'] in wanted]
    require(len(selected) == 11 and {row['path'] for row in selected} == set(wanted), 'candidate ledger path set drift')
    require(all(row['object_sha'] == wanted[row['path']] for row in selected), 'candidate ledger blob drift')
    require(all(row['disposition'] == 'UNVERIFIED' and row['depth'] == 'IDENTITY_ONLY' for row in selected), 'candidate path is already classified')
    require(not any(row['disposition'] in {'DIRECT','GROUPED'} for row in selected), 'candidate overlaps classified coverage')
    excluded = {row['path']: row['blob_sha'] for row in candidate['excluded_already_direct_paths']}
    excluded_rows = [row for row in rows if row['repository_id'] == 'meta' and row['path'] in excluded]
    require(len(excluded_rows) == 2 and all(row['object_sha'] == excluded[row['path']] and row['disposition'] == 'DIRECT' for row in excluded_rows), 'R4 exclusions are not exact already-DIRECT rows')
    meta_rows = [row for row in rows if row['repository_id'] == 'meta']
    require(len(meta_rows) == 174 and sum(row['disposition'] == 'DIRECT' for row in meta_rows) == 70 and sum(row['disposition'] == 'UNVERIFIED' for row in meta_rows) == 104, 'META accounting drift')
    require(sum(grouped.values()) == 113, 'GROUPED accounting drift')
    return result

def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--audit-root', type=Path, default=ROOT); args = parser.parse_args()
    candidate = expected_candidate(args.audit_root)
    validate_candidate(candidate, candidate); validate_source(args.audit_root, candidate); validate_finding(args.audit_root, candidate); validate_accounting(args.audit_root, candidate)
    print(json.dumps({'result':'META_R6_PROMPTS_DIRECT_CANDIDATE_VALID_NOT_ADOPTED','family':candidate['family'],'candidate_paths':11,'candidate_sha256':CANDIDATE_SHA256,'coverage_delta':0,'coverage_adopted':False,'adoption_performed':False,'current_disposition':'UNVERIFIED','direct_paths':283,'grouped_paths':113,'unverified_paths':3929,'semantically_classified_paths':396,'ledger_sha256':LEDGER_SHA,'meta_aud_05_status':'PARTIALLY_REPAIRED','residual_obligations':14,'product_readiness_claimed':False,'audit_completion_claimed':False,'live_state_claimed':False}, sort_keys=True))
    return 0

if __name__ == '__main__': raise SystemExit(main())
