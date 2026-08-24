# OTERYN-V310-GAME-DOC-IA-AND-GAME-GATE-CLOSEOUT

PROMPT_ID: `OTERYN-V310-GAME-DOC-IA-AND-GAME-GATE-CLOSEOUT`
PROMPT_VERSION: `1.0`
STATUS: `READY`
PROGRAMME: `OTERYN-ORG-AUDIT-v3.10`

Repository: `https://github.com/Oteryn/Oteryn-Game`
Mode: autonomous bounded remediation + verification + PR + merge.

## Objective

Terminally close only the Game-owned v3.10 Documentation/Agent IA gaps and, if still non-terminal in live GitHub state, the stable `game-gate` transition.

Target Game evidence families:
- current provider-head Documentation/Agent IA inventory (Game slice of `GAP-DOCS-PROVIDER-CURRENT-001`);
- `GAP-PROMPT-GAME-001`;
- `GAP-TASK-GAME-001`;
- `GAP-HANDOVER-GAME-001`;
- `GAP-DOCS-GAME-OPS-001`;
- `GAP-DOCS-GAME-RELEASE-001`;
- Game-applicable parts of `REC-DOCS-002`, `REC-DOCS-003`, `REC-DOCS-004`, `REC-DOCS-005`, `REC-DOCS-006`, `REC-DOCS-007`;
- stable `game-gate` only if live protection/check state still proves a transition is pending.

Do not implement any other v3.10 gate or any product feature.

## HARD SCOPE LOCK — HIGHEST PRIORITY

You are authorized to solve ONLY the Game scope listed above.

Anything else discovered is OUT OF SCOPE. Do not fix it, refactor it, create a new remediation task for it, or expand this task because it is convenient.

For an unrelated finding record only:

`OUT_OF_SCOPE_FINDING: <exact factual description>`

If it blocks this task, stop with `BLOCKED_BY_OUT_OF_SCOPE_DEPENDENCY` and the exact dependency. "While I am here" work is forbidden.

## Repository boundary

WRITE ACCESS: `Oteryn/Oteryn-Game` only.

READ-ONLY evidence may be taken from `Oteryn/Oteryn` for the v3.10 contract/current META state. Do not write META, Platform, Atlas, legacy `blakinio/*`, external repositories, Synology production state, or any other repository.

Do not inspect legacy migration sources unless a current Game-owned evidence file explicitly requires immutable provenance verification for this bounded task. Migration completion itself is OUT OF SCOPE.

## Authorized write surfaces

Only when directly necessary for the objective:
- `AGENTS.md` and existing nested `**/AGENTS.md`;
- `docs/agents/**` for prompt/task/handover/instruction lifecycle;
- `docs/operations/**` only if a recurring Game operation is proven to require a canonical runbook;
- `docs/release/**` only if a Game release-evidence authority is proven to require a canonical artifact;
- `.github/workflows/merge-gate.yml` only for the bounded stable-gate transition;
- `.github/repository-policy.json` only for the bounded stable-gate contract;
- `.github/CODEOWNERS` only when required to protect a newly canonical governance/runbook path;
- `tools/agents/**`, `tools/governance/**`, and governance-only tests solely for deterministic Documentation/Agent IA lifecycle validation.

Forbidden writes include product/runtime source, gameplay logic, protocol/runtime behavior, assets/content, migrations/databases, deployment runtime, secrets, runner configuration, packages/releases themselves, dependencies, unrelated workflows, and organization settings.

## Game Documentation/Agent IA acceptance

1. Refresh against the exact current protected `main`; frozen v3.10 snapshots are historical evidence, not current-head proof.
2. Inventory current material agent/document surfaces needed by the listed gaps and bind the result to the exact audited Game head.
3. Every retained reusable prompt has stable identity, version/status, owner/scope and supersession semantics; terminal one-shots cannot appear executable.
4. Every active task packet maps to a live owning GitHub Issue/PR and is only a cache; no terminal Issue leaves an unexplained active packet.
5. Retained handovers are explicitly non-authoritative and have expiry/supersession semantics.
6. Decide Game operations-runbook and release-evidence placement from demonstrated need. `NOT_NEEDED` is valid; creating empty taxonomy for symmetry is forbidden.
7. Root/nested AGENTS remain bounded path-specific authority with no transient PR/head/check/session state.
8. Add or tighten only high-signal deterministic lifecycle checks inside existing provider validation; do not create a new externally required check identity for docs hygiene.
9. Preserve historical evidence/provenance; do not rewrite immutable facts merely to make current structure look cleaner.

## Stable game-gate acceptance

First inspect live protection/rulesets/check emission. If `game-gate` is already the terminal protected contract, record `DONE_BY_EXISTING_STATE` and do not mutate settings.

If a transition is still required, you may change ONLY the Game `main` required-check identity needed to replace the prior transitional check with `game-gate`, and only after:
- the current workflow produces `game-gate` on a representative exact PR head from the expected GitHub Actions App;
- all current internal blocking checks feeding the aggregate gate remain fail-closed;
- strict status behavior, no-force-push/no-deletion and existing merge safety are not weakened;
- pre-change settings are recorded for rollback;
- post-change live readback proves the intended exact required check;
- a post-transition representative exact-head path proves the protected contract actually works.

Do not redesign CI, rename unrelated jobs or change any other repository/organization setting.

## Parallel-work safety

Platform Doc/IA, Atlas Doc/IA and organization Recovery agents may run concurrently. Do not touch their repositories, Issues, branches, PRs, task packets or owned surfaces.

Before mutation, inspect current Game Issues/PRs/branches for overlap. Use one dedicated Issue/task, one branch and one PR for this work. Do not absorb unrelated open work.

## Validation

Before completion:
- inspect the full changed-file list and diff;
- verify every changed path is authorized;
- run provider governance/prompt/task lifecycle validations applicable to the exact changes;
- verify current-head Documentation/Agent IA inventory deterministically;
- verify no terminal task/prompt/handover is left falsely active;
- if gate settings changed, verify exact pre/post protection and exact-head `game-gate` evidence;
- run repository-required CI on the exact final head;
- inspect reviews/threads/comments;
- merge only through normal protected policy, squash-only unless live policy says otherwise;
- verify resulting `main` and source-branch cleanup.

Runtime/gameplay E2E is `NOT_APPLICABLE` for documentation/governance-only changes. If gate implementation behavior changes, run the workflow-level representative proof required above.

## Completion definition

DONE requires all Game-targeted gaps in this prompt to have evidence-backed terminal dispositions and the stable Game gate to be either already terminal or safely terminalized. Do not claim organization-wide G1-G11 or v3.10 completion.

## Final response

Return only:

STATUS: DONE | BLOCKED
ALIAS: OTERYN-V310-GAME-DOC-IA-AND-GAME-GATE-CLOSEOUT
ISSUE: <url/number>
PR: <url/number>
MERGE_COMMIT: <sha or NONE>
GAME_HEAD_AUDITED: <sha>
GAPS_CLOSED: <exact list>
GAME_GATE: DONE_BY_EXISTING_STATE | TERMINALIZED | BLOCKED
CHANGED_PATHS: <exact list>
VALIDATION: <exact evidence>
OUT_OF_SCOPE_FINDINGS: <list or NONE>
BLOCKERS: <list or NONE>
SCOPE_CONFIRMATION: No work outside the bounded Game v3.10 scope was performed.
