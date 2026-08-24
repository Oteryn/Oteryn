# OTERYN-V310-PLATFORM-DOC-IA-CLOSEOUT

PROMPT_ID: `OTERYN-V310-PLATFORM-DOC-IA-CLOSEOUT`
PROMPT_VERSION: `1.0`
STATUS: `READY`
PROGRAMME: `OTERYN-ORG-AUDIT-v3.10`

Repository: `https://github.com/Oteryn/Oteryn-Platform`
Mode: autonomous bounded remediation + verification + PR + merge.

## Objective

Terminally close only the Platform-owned Documentation/Agent IA gaps remaining from v3.10 on the live current head.

Target Platform evidence families:
- current provider-head Documentation/Agent IA inventory (Platform slice of `GAP-DOCS-PROVIDER-CURRENT-001`);
- `GAP-PROMPT-PLATFORM-001`;
- `GAP-DOCS-PLATFORM-PROMPT-001`;
- `GAP-TASK-PLATFORM-001`;
- `GAP-HANDOVER-PLATFORM-001`;
- Platform-applicable portions of `REC-DOCS-002`, `REC-DOCS-003`, `REC-DOCS-004`, `REC-DOCS-007`.

Do not reopen completed migration, runner, workflow-lifecycle or v3.9 remediation work.

## HARD SCOPE LOCK — HIGHEST PRIORITY

Anything not required to close the exact Platform gaps above is OUT OF SCOPE.

Do not fix unrelated bugs, CI failures, security findings, migration state, deployment problems, product issues, dependencies or architecture opportunities.

Record unrelated findings only as:

`OUT_OF_SCOPE_FINDING: <exact factual description>`

Do not create a new Issue for an out-of-scope finding. If it is a true dependency, stop with `BLOCKED_BY_OUT_OF_SCOPE_DEPENDENCY`.

## Repository boundary

WRITE ACCESS: `Oteryn/Oteryn-Platform` only.

`Oteryn/Oteryn` may be read only for the v3.10 contract/current META evidence. Game, Atlas, legacy repositories and external repositories are not writable and should not be inspected unless an exact Platform-owned cross-reference requires read-only verification.

## Authorized write surfaces

Only when directly necessary:
- `AGENTS.md` and existing Platform nested `AGENTS.md`;
- `docs/agents/**` for instruction, prompt, task and handover lifecycle;
- `tools/agents/**` and governance-only validation helpers/tests;
- `.github/workflows/agent-governance.yml` only when needed to enforce a high-signal Documentation/Agent IA invariant inside the existing provider gate.

Explicitly forbidden:
- application/runtime source;
- `deploy/**`, production/staging operations and environments;
- general `.github/workflows/**` outside `agent-governance.yml`;
- runner configuration/groups/labels;
- GHCR/packages/releases;
- branch protection/rulesets/required-check settings;
- database migrations/data;
- secrets/credentials;
- dependency upgrades;
- migration manifests and completed transfer closeout evidence except read-only references;
- organization Recovery GAP work.

## Platform acceptance

1. Refresh from exact current protected `main`; do not reuse the frozen v3.10 provider snapshot as current-head completeness proof.
2. Capture deterministic current-head material inventory for the Platform Documentation/Agent surfaces relevant to this task.
3. Exhaustively classify the current Platform prompt library by reusable vs one-shot/historical status. Every retained reusable prompt must have stable identity, version/status, owner/scope and supersession semantics.
4. Terminal one-shot prompts must be archived/status-marked/non-executable according to current provider policy; preserve historical IDs/provenance.
5. Reconcile active task packets to live GitHub Issue/PR authority. Terminal Issues must not leave stale active packets; packets remain caches, never a second status database.
6. Reconcile retained handovers so they are explicitly non-authoritative and expire/supersede on live Issue/PR transitions.
7. Re-measure current root/nested instruction chain after the already-merged P1.1/P1.2 work. Change it only if a live v3.10 IA defect remains; do not perform stylistic compaction for its own sake.
8. Preserve established Platform operations/runbooks and completed migration/runner evidence; they are not targets of this task.
9. Add only deterministic high-signal lifecycle checks to existing Agent Governance when necessary. Do not create a new external required check or broaden runtime CI.
10. Close each Platform-targeted GAP with `PASS`, evidence-backed `NOT_NEEDED`, or an exact blocker. Never invent a canonical path merely for symmetry.

## Parallel-work safety

Game, Atlas and Recovery agents may run simultaneously. Do not touch their repositories, task branches, Issues, PRs or evidence ownership.

Before editing, inspect current Platform Issues/PRs and active task packets for overlapping ownership. Use one dedicated Issue/task, branch and PR. Preserve unrelated active work exactly.

## Validation

Before completion:
- full exact-head diff review;
- changed paths all inside the authorized surfaces;
- deterministic current-head inventory re-run;
- prompt metadata/classification validation;
- task-liveness and Issue-link validation;
- handover expiry/non-authority validation;
- Agent Governance focused tests and repository-required CI on the exact final head;
- zero unresolved review threads/requested changes;
- normal squash merge and source-branch cleanup;
- post-merge `main` readback.

Runtime/browser/product E2E: `NOT_APPLICABLE` because this task must not change executable product behavior.

## Completion definition

DONE means the Platform slices of current-provider inventory, prompt lifecycle, task lifecycle and handover lifecycle are terminally evidenced on current head, with any needed provider-local validator merged. Do not claim Game/Atlas/Recovery or whole-v3.10 completion.

## Final response

Return only:

STATUS: DONE | BLOCKED
ALIAS: OTERYN-V310-PLATFORM-DOC-IA-CLOSEOUT
ISSUE: <url/number>
PR: <url/number>
MERGE_COMMIT: <sha or NONE>
PLATFORM_HEAD_AUDITED: <sha>
GAPS_CLOSED: <exact list>
PROMPTS_CLASSIFIED: <count/status>
TASK_PACKETS_RECONCILED: <count/status>
HANDOVERS_RECONCILED: <count/status>
CHANGED_PATHS: <exact list>
VALIDATION: <exact evidence>
OUT_OF_SCOPE_FINDINGS: <list or NONE>
BLOCKERS: <list or NONE>
SCOPE_CONFIRMATION: No work outside the bounded Platform v3.10 Documentation/Agent IA scope was performed.
