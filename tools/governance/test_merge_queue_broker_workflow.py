#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / '.github/workflows/merge-queue-broker.yml'


def main() -> int:
    text = WORKFLOW.read_text(encoding='utf-8')
    required = [
        'name: Oteryn Merge Queue Broker',
        'issue_comment:',
        '/oteryn-mq-enqueue',
        'OWNER|MEMBER|COLLABORATOR',
        'Oteryn/Oteryn-Game',
        'Oteryn/Oteryn-Platform',
        'Oteryn/Oteryn-Atlas',
        '--request PUT',
        'merge_action:\"merge_queue\"',
        'gh pr checks',
        'reviewThreads(first:100)',
        'merge-async/$uuid',
        'MQ_ACCEPTED',
        'RECONCILE_REQUIRED',
    ]
    for marker in required:
        assert marker in text, marker
    print('PASS central Merge Queue broker workflow contract')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
