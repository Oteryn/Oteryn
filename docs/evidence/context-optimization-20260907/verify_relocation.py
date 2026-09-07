#!/usr/bin/env python3
"""Task-only source-preservation check for the #166 canary; not a CI policy.

Inputs are exact UTF-8 source snapshots. No network, model, credentials or writes.
This proves lossless relocation, not client delivery or behavioral correctness.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path

BASE_BLOBS = {
    'META': 'bc7bede1e31a4b55639c5f34a4b7629094d35e80',
    'Atlas': '92f8b48bd68ce415dc3911519e562e54e6c68804',
}
ROUTES = {
    'META': [
        ('docs/agents/operations/RESTRICTED_PUBLISHING.md', '## Restricted publishing-credential compatibility\n', '## Organization runner routing\n'),
        ('docs/agents/operations/RUNNER_ROUTING.md', '## Organization runner routing\n', '## Authority and repository scope\n'),
    ],
    'Atlas': [
        ('docs/agents/operations/VERIFICATION_CAPABILITY.md', '## Verification capability placement\n', '## Integration and live deployment\n'),
        ('docs/agents/operations/LIVE_DEPLOYMENT.md', '- Live deployment originates only', '## Safety\n'),
    ],
}


def blob(text: str) -> str:
    data = text.encode('utf-8')
    return hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest()


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def verify(provider: str, baseline: str, files: dict[str, str]) -> dict:
    require(blob(baseline) == BASE_BLOBS[provider], 'unauthenticated baseline')
    root = files['AGENTS.md']
    for path, start, end in ROUTES[provider]:
        require(path in files, f'missing routed source: {path}')
        require(f'`{path}`' in root, f'missing root route: {path}')
        source = baseline[baseline.index(start):baseline.index(end)]
        body = source.split('\n\n', 1)[1] if start.startswith('##') else source
        # Heading and selection metadata are deliberately outside the old body.
        require(files[path].split('\n\n', 2)[2] == body.rstrip()+'\n', f'changed or lost obligation: {path}')
        require(files[path].startswith('# ') and '\n\nLoad ' in files[path], f'missing selection metadata: {path}')
    if provider == 'META':
        old_start = baseline.index('## Restricted publishing-credential compatibility\n')
        old_end = baseline.index('## Authority and repository scope\n')
        new_start = root.index('## Specialist operation routes\n')
        new_end = root.index('## Authority and repository scope\n')
        require(root[:new_start] == baseline[:old_start] and root[new_end:] == baseline[old_end:], 'unrelated META root change')
        require('Before using CLI/Git credential compatibility' in root and 'Before selecting or changing an Actions runner' in root, 'missing pre-operation trigger')
    else:
        old_start = baseline.index('## Verification capability placement\n')
        old_end = baseline.index('## Integration and live deployment\n')
        new_start = root.index('## Verification capability route\n')
        new_end = root.index('## Integration and live deployment\n')
        old_deploy = baseline.index('- Live deployment originates only')
        new_deploy = root.index('\nBefore any separately authorized deployment,')
        require(root[:new_start] == baseline[:old_start], 'changed Atlas bootstrap/maintenance/invariants')
        require(root[new_end:new_deploy] == baseline[old_end:old_deploy], 'changed Atlas integration requirements')
        require(root[root.index('## Safety\n'):] == baseline[baseline.index('## Safety\n'):], 'changed Atlas safety')
        require('Before selecting a verification profile, data capability or runner' in root, 'missing verification trigger')
        require('active maintenance freeze' in root[new_start:new_end] and 'active maintenance freeze' in root[new_deploy:], 'route fails to preserve freeze priority')
    stats = {path: {'bytes': len(text.encode()), 'lines': len(text.splitlines()), 'blob': blob(text)} for path, text in files.items()}
    return {'provider': provider, 'verdict': 'PASS', 'baseline_root_bytes': len(baseline.encode()), 'candidate_files': stats,
            'instruction_union_bytes': sum(row['bytes'] for row in stats.values()), 'behavior': 'NOT_EVALUATED', 'tokens_cost': 'NOT_MEASURED'}


def negative_checks(provider: str, baseline: str, files: dict[str, str]) -> list[str]:
    cases: list[tuple[str, str, dict[str, str]]] = []
    for path, _, _ in ROUTES[provider]:
        changed = copy.deepcopy(files)
        body = changed[path].split('\n\n', 2)[2]
        changed[path] = changed[path][:-len(body)] + body.split('\n', 1)[1]
        cases.append(('lost-obligation:'+path, baseline, changed))
        changed = copy.deepcopy(files); del changed[path]
        cases.append(('missing-file:'+path, baseline, changed))
        changed = copy.deepcopy(files); changed['AGENTS.md'] = changed['AGENTS.md'].replace('`'+path+'`', '`missing.md`')
        cases.append(('missing-route:'+path, baseline, changed))
    changed = copy.deepcopy(files); changed['AGENTS.md'] = changed['AGENTS.md'].replace('## Safety\n' if provider == 'Atlas' else '## Security and sensitive data\n', '## Removed safety\n')
    cases.append(('unrelated-safety-change', baseline, changed))
    cases.append(('wrong-baseline', baseline+'\n', copy.deepcopy(files)))
    rejected = []
    for name, source, candidate in cases:
        try:
            verify(provider, source, candidate)
        except (ValueError, KeyError):
            rejected.append(name)
        else:
            raise ValueError('negative control was incorrectly accepted: '+name)
    return rejected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--provider', choices=BASE_BLOBS, required=True)
    parser.add_argument('--baseline-root', type=Path, required=True)
    parser.add_argument('--candidate-root', type=Path, required=True)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    try:
        baseline = (args.baseline_root/'AGENTS.md').read_bytes().decode('utf-8')
        paths = ['AGENTS.md', *[row[0] for row in ROUTES[args.provider]]]
        files = {path: (args.candidate_root/path).read_bytes().decode('utf-8') for path in paths}
        result = verify(args.provider, baseline, files)
        if args.self_test:
            result['negative_controls_rejected'] = negative_checks(args.provider, baseline, files)
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, UnicodeError, ValueError, KeyError, IndexError) as exc:
        print(json.dumps({'verdict': 'FAIL', 'error': str(exc)}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
