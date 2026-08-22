# Alias: OTERYN-ORG-RUNNERS-PLATFORM-ACL-LEGACY-CLOSEOUT

MODE: Autonomous multi-surface runner terminal proof + cleanup closeout.

Primary repositories:
- `https://github.com/Oteryn/Oteryn`
- `https://github.com/Oteryn/Oteryn-Platform`

Primary lifecycle:
- `Oteryn/Oteryn#34`
- `Oteryn/Oteryn-Platform#1215`

Game PR #36 is owned by a separate workstream and is READ-ONLY here except for observing its terminal result as a dependency.

## Mission

Close the remaining organization-runner acceptance evidence that does not belong to the Game implementation workstream: prove the Platform trusted-main replacement workload, directly verify organization runner-group selected-repository ACLs if a safe control-plane surface exists, prove legacy-runner non-use, and retire the legacy staging runner only after every prerequisite gate is directly satisfied and policy/authorization permits the retirement action.

Do not stop at the fact that bootstrap/config PRs are merged. A runner is terminal only when the real workload and routing/security boundaries are directly evidenced.

## Mandatory first reads

META:
1. `/AGENTS.md`
2. `/docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md`
3. current `Oteryn/Oteryn#34` comments/evidence

Platform:
1. `/AGENTS.md`
2. `/docs/agents/PLATFORM_AGENT_BOOTSTRAP.md` if present
3. `/docs/agents/EXECUTION_RESOURCE_HYGIENE.md` if present
4. `/docs/operations/SYNOLOGY_ORGANIZATION_RUNNERS.md`
5. current `Oteryn/Oteryn-Platform#1215`
6. merged PR #1216 and current `main`

## Last verified checkpoint

As of 2026-08-22:

- runner supply-chain/bootstrap is merged and uses Actions Runner `2.336.0`.
- immutable runner image digest checkpoint: `ghcr.io/oteryn/oteryn-deploy-runner@sha256:f0c452798a17df09006a12d437e83a72d681dcd338ef22ed01fca329d1bbab8d`.
- Atlas replacement route is already proven by trusted-main run `32526864123`, job `96911114022`, on `atlas-runners / oteryn-atlas`, runner `oteryn-synology-atlas`.
- Platform PR #1216 is merged as `62d134a71fa5b480249ffbffbb81079aede4be34`.
- #1216 migrated the existing registered read-only `Synology Diagnostics` workflow from legacy `oteryn-staging` routing to `platform-runners + oteryn-platform` rather than increasing workflow inventory.
- hosted exact-head Platform gates were green before #1216 merge.
- the trusted-main `Synology Diagnostics` run/job result after #1216 merge was not readable through the connector surface used by the coordinator and therefore remains `UNKNOWN/PENDING`, not PASS.
- exact `Selected repositories` ACL readback for `platform-runners`, `atlas-runners`, `game-runners` remains UNKNOWN through the coordinator's current connector.
- legacy `oteryn-synology-staging` remains intentionally retained as rollback.
- Game replacement route depends on separate Game workstream; do not retire legacy while Game terminal proof is missing.

## Capability discovery requirements

Before reporting access blocked, inspect every available safe execution surface, including as applicable:

- GitHub connector/actions and organization settings APIs;
- authenticated `gh` CLI;
- local repository/worktree;
- Remote Desktop Commander;
- installed Synology/DSM integration;
- authorized SSH/terminal paths already configured by the owner.

Tool availability never grants authority. Do not expose secrets, tokens, runner credentials, `.credentials`, environment dumps or private runtime data.

## Platform proof sequence

1. Refresh Platform `main`, merged PR #1216 and `synology-diagnostics.yml`.
2. Locate the trusted-main push run caused by #1216 (or the first valid trusted manual run on the exact merged workflow if push evidence genuinely cannot exist).
3. Directly verify:
   - workflow/run/job identity;
   - `success` conclusion;
   - runner name `oteryn-synology-platform`;
   - route `platform-runners + oteryn-platform`;
   - organization registration identity;
   - expected Platform Docker/staging-state capability;
   - read-only behavior/no runtime mutation/no environment dump.
4. Record sanitized run/job evidence to Platform #1215 and parent META #34.
5. Close #1215 only after direct PASS evidence.

## Runner-group ACL sequence

1. Discover a read-only organization control-plane surface capable of listing runner groups and selected repositories.
2. Verify exact intended repository membership for each group. Do not infer ACL from successful routing alone.
3. Record group IDs/names and selected repository IDs/coordinates, sanitized and without credentials.
4. If exact ACL cannot be read after capability discovery, retain `UNKNOWN` and record the precise missing permission/surface.
5. Do not mutate ACLs merely to make the audit pass unless the current owner authorization and organization policy explicitly permit that specific change.

## Legacy retirement gate

Do NOT retire `oteryn-synology-staging` until all of the following are directly proven:

- Atlas replacement route PASS;
- Platform trusted-main replacement route PASS;
- Game replacement route + trusted-main acceptance PASS from the separate Game workstream;
- runner-group selected-repository ACLs PASS, or an explicit owner-approved alternative proof accepted by the governing audit contract;
- search proves no remaining active workflow/job depends on the legacy runner;
- rollback/evidence requirements are preserved;
- applicable repository/organization policy authorizes the retirement action.

If retirement is authorized and all gates pass, perform the smallest bounded cleanup, verify the old registration/container/state is no longer active where required, and record exact evidence. Do not touch unrelated Synology production services.

## Completion contract

Return DONE only when:

- `PLATFORM_RUNNER_ACCEPTANCE = PASS` with exact run/job IDs;
- `RUNNER_GROUP_ACL = PASS` with direct selected-repository evidence;
- Game dependency is terminal PASS;
- `LEGACY_RUNNER_RETIREMENT = DONE` and verified;
- META #34 and provider evidence are updated truthfully;
- no active workflow depends on the retired legacy route.

If Game remains pending, this workstream may complete all independent Platform/ACL work but must report `LEGACY_RUNNER_RETIREMENT = WAITING_ON_GAME`, not DONE.