# Oteryn Organization Runner Topology Audit — 2026-08-21 (terminal evidence checkpoint)

Audit owner: `Oteryn/Oteryn#32`
Audit contract context: `OTERYN-ORG-AUDIT-v3.10`
Evidence date: 2026-08-21
Scope: META governance evidence and read-only runtime/GitHub observation. Product-repository mutation is out of scope.

## Authority and lifecycle

GitHub Issue #32 is the sole lifecycle authority for the runner-topology migration. This report is a durable technical observation only; it intentionally does not carry a mutable lifecycle status and does not declare the migration complete.

Primary durable implementation checkpoint: [Issue #32 comment 5374400776](https://github.com/Oteryn/Oteryn/issues/32#issuecomment-5374400776). Organization-control-plane limitation checkpoint: [Issue #34 comment 5374532953](https://github.com/Oteryn/Oteryn/issues/34#issuecomment-5374532953). Atlas replacement-route terminal evidence: [Atlas #35 comment 5375783558](https://github.com/Oteryn/Oteryn-Atlas/issues/35#issuecomment-5375783558) and [Issue #34 comment 5375785211](https://github.com/Oteryn/Oteryn/issues/34#issuecomment-5375785211).

## Observed runner implementation

| Workload owner | Observed registration | Observed group/pool | Runner version | Container/image result |
| --- | --- | --- | --- | --- |
| Platform | `oteryn-synology-platform` | `platform-runners` | `2.336.0` | running; immutable GHCR digest |
| Atlas | `oteryn-synology-atlas` | `atlas-runners` | `2.336.0` | running; immutable GHCR digest |
| Game | `oteryn-synology-game` | `game-runners` | `2.336.0` | running; immutable GHCR digest |

The observed replacement image identity is `ghcr.io/oteryn/oteryn-deploy-runner@sha256:f0c452798a17df09006a12d437e83a72d681dcd338ef22ed01fca329d1bbab8d`. The Issue #32 checkpoint records distinct registration/config/work state and runner agent IDs `44`/`45`/`46` in pools `3`/`4`/`5`. These facts prove provisioning/identity only; they do not independently prove selected-repository restrictions or successful provider workloads.

A direct read-only Synology compose/runtime inspection during this audit also observed distinct intended capability shapes: Platform has Platform state plus Docker-host access; Atlas has Docker-host access without the Platform staging-state mount; Game runs as `1001:1001` without a Docker socket. That observation is useful least-privilege evidence, but it is not a substitute for GitHub runner-group policy readback or a successful workload.

## GitHub workflow/job evidence

| Provider | Exact observed evidence | Result | What it proves | What it does not prove |
| --- | --- | --- | --- | --- |
| Platform | Actions run `32524055762`, job `96902275070` | FAILURE | scheduling reached `oteryn-synology-platform` through `platform-runners` / `oteryn-platform` | no successful replacement workload |
| Platform legacy | Actions run `32524055889` | SUCCESS | legacy `oteryn-synology-staging` path still works/exists | does not satisfy replacement acceptance |
| Atlas | trusted-main Actions run `32526864123`, job `96911114022` | SUCCESS | scheduling, exact runner identity, separate Atlas state, Docker/local capability, exact live publication, seven FullWorld roots, HTTP Range and real Chromium desktop/mobile acceptance all passed | selected-repository ACL exclusivity is still not readable from this session |
| Atlas artifact | artifact `9463015639`, digest `sha256:9582ac4fa7b388498aab22f64911f66e53ed3c5059ff0eef505065ba8beeece0` | SUCCESS | bounded browser evidence from the successful trusted-main route | does not establish organization ACL policy |
| Atlas cross-provider retirement | Platform PR #1212, merge `a8d46c91571a8df5193d6ddd2c28b35db2e85934` | MERGED | Platform-owned Atlas live scaffold removed; Platform workflow restored without Atlas live job | Platform's own replacement workload still requires independent successful proof |
| Game | no qualifying dedicated local Actions job found | NOT PROVEN | nothing beyond provisioning | workflow routing and successful runtime/integration remain unproven |

The Atlas main workflow selects `group: atlas-runners` and `labels: oteryn-atlas`; the successful trusted-main run above proves the replacement route and local Atlas capability. Platform owner-local replacement scheduling exists but the dedicated replacement job observed in this audit failed. No qualifying Game-owned workflow/job using `game-runners` + `oteryn-game` was found in the evidence reviewed here.

## Control-plane isolation

A named group/label is not a security boundary by itself. The authenticated execution token available to this audit has repository/workflow/read-org scopes but not organization-administration permission; organization runner-group selected-repository membership readback returned an authorization failure. The connector surface likewise exposes no organization runner-group membership action.

Therefore the following remain `UNKNOWN` and are not inferred from labels:

- `platform-runners` selected repositories equal exactly `Oteryn/Oteryn-Platform`;
- `atlas-runners` selected repositories equal exactly `Oteryn/Oteryn-Atlas`;
- `game-runners` selected repositories equal exactly `Oteryn/Oteryn-Game`;
- no cross-provider repository can schedule onto another provider group.

Atlas functional routing and post-cutover ownership are proven independently; the remaining Atlas control-plane UNKNOWN is specifically group ACL exclusivity.

## Legacy / supply-chain state

The replacement containers are pinned to the immutable Oteryn GHCR digest above. The legacy `oteryn-synology-staging` container/registration remains present and uses the mutable pre-transfer coordinate/image `ghcr.io/blakinio/oteryn-deploy-runner:main`. It MUST NOT be retired until all replacement routes, successful workloads and control-plane restrictions are proven. Consequently legacy mutable-image retirement is `NOT DONE`, not silently converted to DONE.

The replacement runtime digest itself is proven immutable. Independent full build/base-image provenance, including the complete immutable base chain, is not established by the available organization-level evidence and remains `UNKNOWN`.

## Findings

| ID | Severity | State | Evidence-backed conclusion |
| --- | --- | --- | --- |
| RUNNER-001 | HIGH | PARTIAL | Replacement containers use one immutable Oteryn digest; legacy mutable `blakinio/...:main` remains pending safe retirement. |
| RUNNER-002 | MEDIUM | UNKNOWN | Replacement digest is immutable, but complete reviewed build/base provenance is not independently established here. |
| RUNNER-003 | INFO | DONE | Three replacement registrations and distinct workload identities are durably evidenced. |
| RUNNER-004 | HIGH | UNKNOWN | Selected-repository runner-group isolation cannot be read back with available authenticated authority. |
| RUNNER-005 | HIGH | PARTIAL | Platform replacement scheduling is proven, successful replacement workload is not. |
| RUNNER-006 | HIGH | DONE | Atlas trusted-main dedicated routing, exact runner identity, required local capability and full live/browser acceptance passed in run `32526864123` / job `96911114022`; Platform cross-provider Atlas execution was removed by #1212. |
| RUNNER-007 | HIGH | NOT DONE | No qualifying Game-owned local runtime/integration job is proven. |
| RUNNER-008 | HIGH | NOT DONE | Legacy staging registration/routing/image is not retired because prerequisite replacement proof is incomplete. |
| RUNNER-009 | MEDIUM | UNKNOWN | Cross-provider effective group access cannot be proven without organization runner-group membership readback. |

## Acceptance matrix for Issue #32

| Gate | Verdict | Evidence / blocker |
| --- | --- | --- |
| A. Control-plane isolation | UNKNOWN | exact selected-repository membership cannot be read with current organization permission surface |
| B. Workflow routing | PARTIAL | Atlas route DONE and Platform Atlas scaffold retired; Platform successful own replacement remains absent; Game local routing not proven |
| C. Live execution — Platform | NOT DONE | dedicated job `96902275070` failed |
| C. Live execution — Atlas | DONE | trusted-main run `32526864123`, job `96911114022` succeeded on `atlas-runners` / `oteryn-synology-atlas` and passed local/live/browser acceptance |
| C. Live execution — Game | NOT DONE | no qualifying dedicated local job found |
| D. Legacy retirement | NOT DONE | deliberately retained because A/B/C are incomplete |
| E. Supply chain | PARTIAL | replacement digest immutable; mutable legacy image and full base provenance remain unresolved |

Issue #32 and parent implementation Issue #34 must remain open until their acceptance criteria are genuinely satisfied. The runner evidence work in this PR is terminal as a truthful audit record even though the underlying runner migration is not terminally complete.
