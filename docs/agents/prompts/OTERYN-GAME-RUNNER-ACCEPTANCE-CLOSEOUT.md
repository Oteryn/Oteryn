# Alias: OTERYN-GAME-RUNNER-ACCEPTANCE-CLOSEOUT

MODE: Autonomous Game runner acceptance closeout with independent-review separation.

Repository: `https://github.com/Oteryn/Oteryn-Game`
Primary lifecycle: `Oteryn/Oteryn-Game#34`
Primary PR checkpoint: `Oteryn/Oteryn-Game#36`
Parent lifecycle: `Oteryn/Oteryn#34`

META #37 and Platform runner work are owned by separate workstreams and are READ-ONLY here except for dependency observation.

## Mission

Finish the Game organization-runner replacement route without weakening the deliberate least-privilege boundary. Obtain a policy-permitted independent exact-head review of PR #36, merge it normally only when all required conditions are satisfied, run the trusted-main acceptance workload on the replacement Game runner, verify the real local Canary integration boundary, and record sanitized terminal evidence to Game #34 and META #34.

Do not use a pull-request event to execute arbitrary PR code on the self-hosted Game runner.

## Mandatory first reads

1. `/AGENTS.md`
2. any applicable nested `/AGENTS.md` or `AGENTS.override.md` for `.github/workflows/`
3. current Game AI/review policy and merge-gate documentation
4. current Issue #34
5. current PR #36: exact diff, hosted checks, reviews and threads
6. current Platform-owned runner contract/runbook only as read-only dependency evidence where it defines the intended Game privilege boundary

Live repository policy outranks this prompt. Do not interpret this prompt as permission to spend metered AI if Game policy forbids it.

## Last verified checkpoint

As of 2026-08-22:

- PR #36 is open, non-draft and mergeable.
- candidate checkpoint: `081c79cebd2d706b45bf8d90a6382b8c7ccd3cca`.
- changed scope: one workflow, `.github/workflows/synology-game-runner-acceptance.yml`.
- observed exact-head hosted workflows were all `success`, including Architecture Integrity, Agent Governance, Architecture Semantic Review, Merge Authority and Merge Gate.
- workflow target route: `game-runners + oteryn-game`.
- expected runner identity: `oteryn-synology-game`.
- intended least-privilege boundary: UID/GID `1001:1001`, persistent separate `/runner` and `/work`, no usable Docker host control/socket.
- acceptance performs bounded private TCP reachability to existing Canary login/game endpoints without authentication, runtime mutation or environment dump.
- self-hosted acceptance is trusted-main/manual only; no `pull_request` trigger.
- coordinator found no independent review submission on #36.
- root Game policy was previously read as requiring independent review while separately prohibiting owner-funded metered AI/Codex without separate explicit authorization.

## Independent-review rule

This executor did not author the existing #36 branch and may perform an independent **read-only** technical review only if current Game policy recognizes that reviewer/evidence form. Do not self-approve using the PR author's GitHub identity and do not fabricate approval evidence.

Required sequence:

1. Refresh exact Game policy governing independent review and paid/metered AI.
2. Determine the allowed reviewer/evidence classes.
3. If an independent non-metered agent review is policy-compliant, perform a fresh exact-head read-only review and record findings/evidence in the permitted GitHub object without modifying the branch during the review.
4. If only a human/GitHub reviewer is permitted, request the smallest valid reviewer request through GitHub and continue all other useful validation.
5. Do NOT invoke owner-funded Codex/Spark or other metered AI unless current policy plus explicit owner authorization for that use is directly present.
6. If review finds material defects, do not approve. Repair on the existing task branch only if repository ownership/one-agent rules allow it; after any repair, a new independent reviewer must review the new exact head.

## Merge sequence

When independent review is valid and clean:

1. Refresh PR #36 head and `main`.
2. Ensure branch ancestry/base is current enough for repository policy.
3. Re-run/verify required exact-head hosted checks after any change.
4. Confirm no unresolved material review threads.
5. Squash-merge normally with race protection; no bypass/force.
6. Refresh Game `main` and verify the merged workflow content.

## Trusted-main acceptance sequence

After merge only:

1. Observe the trusted-main `Synology Game Runner Acceptance` run triggered by the merged workflow or use a policy-permitted trusted manual dispatch if needed.
2. Verify exact run/job conclusion `success`.
3. Verify sanitized evidence proves:
   - runner name `oteryn-synology-game`;
   - route `game-runners / oteryn-game`;
   - organization registration state;
   - UID/GID `1001:1001`;
   - separate `/runner` and `/work`;
   - absence of usable Docker-host control;
   - Canary login reachability PASS;
   - Canary game reachability PASS;
   - runtime mutation NONE;
   - environment values exposed NONE.
4. Record exact run/job IDs and merged SHA to Game #34 and parent META #34.
5. Close Game #34 only when the above is directly verified.

## Hard constraints

- Do not grant Game Docker socket/root merely to make validation easy.
- Do not mutate Canary, MariaDB, Synology deployment state, secrets or production data.
- Do not execute PR code on self-hosted Game runner.
- Do not touch Platform/Atlas runner branches.
- Do not retire the legacy staging runner from this workstream; the runner/ACL executor owns that final dependency-aware cleanup.

## Completion contract

Return DONE only with:

- valid independent exact-head review evidence;
- PR #36 merged normally with exact merge SHA;
- trusted-main Game acceptance exact run/job IDs and `success`;
- Game #34 updated/closed truthfully;
- parent META #34 updated with the same exact evidence.

If policy prevents every available independent-review route, report the exact policy restriction and reviewer capability required, after completing all other safe validation. Do not merge around the review requirement.