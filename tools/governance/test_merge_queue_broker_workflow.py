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
        'COMMENT_ACTOR:',
        'REQUEST_ACTOR:',
        'collaborators/$REQUEST_ACTOR/permission',
        'permission" == admin || "$permission" == maintain',
        'BLOCKED_NOT_AUTHORIZED',
        '--request PUT',
        'merge_action:\"merge_queue\"',
        'gh pr checks',
        'reviewThreads(first:100)',
        'REQUEST_ACCEPTED_NON_TERMINAL',
        'executor_sequence',
        'os.fsync',
        'merge-async/$uuid',
        'live_post_submission_target_readback',
        'accepted_request_uuid',
        'observation_sequence > receipt_sequence',
        'MQ_ACCEPTED',
        'RECONCILE_REQUIRED',
    ]
    for marker in required:
        assert marker in text, marker

    authority_read = text.index('collaborators/$REQUEST_ACTOR/permission')
    allowed = text.index('allowed=true', authority_read)
    assert authority_read < allowed, 'target authority must be read before broker authorization'

    receipt = text.index("--arg event 'REQUEST_ACCEPTED_NON_TERMINAL'")
    readback = text.index('readback="$(gh api "repos/$TARGET_REPOSITORY/pulls/$TARGET_PR/merge-async/$uuid")"')
    observation = text.index('--arg accepted_request_uuid "$uuid"')
    assert receipt < readback < observation, 'receipt must be persisted before causal readback observation'

    assert text.count('collaborators/$REQUEST_ACTOR/permission') >= 2, 'target authority must be rebound before mutation'
    print('PASS central Merge Queue broker workflow contract')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
