#!/usr/bin/env python3
"""Source-bound F17 characterization; not a GitHub event execution or general YAML parser."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re

BLOBS = {
    '.github/workflows/announcements-acceptance.yml': '399edcf4bbbbdf69d36f28d749cf32136848c4d7',
    'lang/en/public.php': '7cca711447330670cda8aa1d9f312f3c2e701c5e',
    'lang/pl/public.php': '7da6af62141283aad5669faf90379cb83bd98c6b',
    'resources/views/announcements/components/ticker.blade.php': 'b5ca83d179ac5dfeb90678f08f3487d242cae478',
    'scripts/acceptance/playwright.announcements.config.mjs': '2c8b23f0893c169452ca5e8c90a9b8a9fa55a521',
    'scripts/acceptance/tests/announcements-public-acceptance.spec.mjs': 'b993c495d68a7f0edaa86212356b5a42c099d47a',
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def json_bytes(raw):
    def pairs(items):
        out={}
        for key,value in items:
            require(key not in out,'duplicate JSON key')
            out[key]=value
        return out
    return json.loads(raw,object_pairs_hook=pairs)


def require_committed_result(generated, raw):
    committed=json_bytes(raw)
    require(generated==committed,'generated F17 trigger evidence differs from committed r3-trigger-evidence.json')
    return committed


def paths_for_event(text, event):
    # The exact source binding below fixes the admitted syntax to this closed shape.
    require(event in {'pull_request', 'push'}, 'event not admitted')
    blocks = re.findall(r'^  ' + event + r':\n(.*?)(?=^  \S|^\S|\Z)', text, re.M | re.S)
    require(len(blocks) == 1, 'event block absent or duplicated')
    block = re.findall(r'^    paths:\n((?:      - [^\n]+\n)+)', blocks[0], re.M)
    require(len(block) == 1, 'literal path list required')
    values = []
    for line in block[0].splitlines():
        match = re.fullmatch(r"      - '([A-Za-z0-9_./*-]+)'", line)
        require(match is not None, 'unsupported path syntax')
        values.append(match[1])
    require(len(values) == len(set(values)), 'duplicate path')
    return values


def matches(path, pattern):
    # Only literal paths and terminal /** are admitted; no negation/ordered rules.
    require(not any(x in pattern for x in ['!', '?', '[', ']', '\\']), 'unsupported glob')
    if pattern.endswith('/**'):
        prefix = pattern[:-2]
        require('*' not in prefix, 'unsupported glob')
        return path.startswith(prefix)
    require('*' not in pattern, 'unsupported glob')
    return path == pattern


def verify(source):
    text = {}
    for name, expected in BLOBS.items():
        path = source / name
        require(not path.is_symlink(), 'source symlink refused')
        raw = path.read_bytes()
        require(hashlib.sha1(f'blob {len(raw)}\0'.encode() + raw).hexdigest() == expected, 'wrong source: ' + name)
        text[name] = raw.decode()
    results = []
    for event in ['pull_request', 'push']:
        paths = paths_for_event(text['.github/workflows/announcements-acceptance.yml'], event)
        require(len(paths) == 13, 'unexpected source list length')
        for changed, expected_selection in [('lang/en/public.php', False), ('lang/pl/public.php', False), ('app/Announcements/Queries/Example.php', True), ('scripts/acceptance/tests/announcements-public-acceptance.spec.mjs', True)]:
            selected = any(matches(changed, pattern) for pattern in paths)
            require(selected is expected_selection, 'source counterexample/control changed')
            results.append({'event': event, 'changed_path': changed, 'selected': selected,
                            'role': 'counterexample' if changed.startswith('lang/') else 'positive_control'})
    require("__('public.announcements.title')" in text['resources/views/announcements/components/ticker.blade.php'], 'template consumer mismatch')
    spec = text['scripts/acceptance/tests/announcements-public-acceptance.spec.mjs']
    require("name: 'Announcements'" in spec and "name: 'Ogłoszenia'" in spec, 'localized assertion mismatch')
    return {'schema_version': 1, 'finding': 'PLATFORM-F17', 'source_sha': 'de917b3477a1de0667531380de3660e8b2ab59aa', 'blobs': BLOBS,
            'cases': results, 'verdict': 'STATIC_DEDICATED_WORKFLOW_FALSE_NEGATIVE',
            'limitation': 'Only Announcements auto-selection for a locale-only change. Other workflows may run. No live event, protected merge bypass or fresh Announcements lifecycle/browser acceptance is claimed.'}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root',type=Path,required=True)
    parser.add_argument('--expected',type=Path,default=Path(__file__).resolve().parents[2]/'docs/evidence/organization-audit-20260907/r3-trigger-evidence.json')
    args=parser.parse_args()
    generated=verify(args.source_root)
    require_committed_result(generated,args.expected.read_bytes())
    print(json.dumps(generated,ensure_ascii=False,indent=2))
