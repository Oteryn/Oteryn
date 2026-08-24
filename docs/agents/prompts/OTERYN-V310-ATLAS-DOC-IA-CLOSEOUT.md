# OTERYN-V310-ATLAS-DOC-IA-CLOSEOUT

PROMPT_ID: `OTERYN-V310-ATLAS-DOC-IA-CLOSEOUT`
PROMPT_VERSION: `1.0`
STATUS: `READY`
PROGRAMME: `OTERYN-ORG-AUDIT-v3.10`

Repository: `https://github.com/Oteryn/Oteryn-Atlas`
Mode: autonomous bounded remediation + verification + PR + merge.

## Objective

Terminally close only the Atlas-owned Documentation/Agent Information Architecture gaps from v3.10 using evidence from the exact current Atlas head.

Target Atlas evidence families:
- Atlas slice of `GAP-DOCS-PROVIDER-CURRENT-001`;
- `GAP-DOCS-ATLAS-ARCH-001`;
- `GAP-DOCS-ATLAS-CONTRACT-001`;
- `GAP-DOCS-ATLAS-GOV-001` when still applicable on live state;
- `GAP-DOCS-ATLAS-POLICY-001` when still applicable on live state;
- `GAP-DOCS-ATLAS-TEST-001`;
- `GAP-DOCS-ATLAS-OPS-001`;
- `GAP-DOCS-ATLAS-RECOVERY-001`;
- `GAP-PROMPT-ATLAS-001`;
- `GAP-TASK-ATLAS-001`;
- Atlas-applicable portions of `REC-DOCS-001`, `REC-DOCS-003`, `REC-DOCS-004`, `REC-DOCS-005`, `REC-DOCS-007`.

Atlas migration/extraction is already a separate completed programme and is not reopened by this task.

## HARD SCOPE LOCK — HIGHEST PRIORITY

Only the Atlas Documentation/Agent IA gaps above are authorized.

Do not treat discovery as authorization. Unrelated product, map, publication, rendering, performance, migration, runner, security, dependency or CI findings must not be repaired.

Record only:

`OUT_OF_SCOPE_FINDING: <exact factual description>`

If an out-of-scope dependency prevents truthful closure, stop with `BLOCKED_BY_OUT_OF_SCOPE_DEPENDENCY`. Do not create extra Issues for unrelated findings.

## Repository boundary

WRITE ACCESS: `Oteryn/Oteryn-Atlas` only.

META may be read only for the v3.10 contract/current organization evidence. Do not write Game, Platform, META, `blakinio/Otheryn`, other legacy sources or external repositories.

The historical Atlas source is read-only provenance and must not be modified.

## Authorized write surfaces

Only as directly needed:
- `AGENTS.md`;
- `docs/**` for Atlas-owned architecture/contracts/governance/test/operations/recovery/prompt/task decisions and evidence classification;
- `tools/governance/**` for deterministic Documentation/Agent IA validation;
- `.github/CODEOWNERS` only to protect a newly proven canonical documentation/governance path;
- `.github/dependabot.yml` only if the v3.10 IA evidence proves a documentation-policy metadata correction is directly required;
- `.github/workflows/ci.yml` only to wire a bounded deterministic documentation/agent subcheck into the existing Atlas stable gate.

Forbidden writes:
- `src/**`, `web/**`, `e2e/**` executable/product code except documentation files already located there;
- generated Atlas products/assets/index data;
- migration provenance facts except links/classification necessary for IA documentation;
- runner configuration or Synology state;
- publication/deployment execution;
- branch protection/rulesets;
- secrets/credentials;
- dependency upgrades;
- Game/Platform contracts or runtime.

## Evidence-first canonical-path rule

Do NOT create `docs/architecture`, `docs/contracts`, `docs/operations`, recovery folders or any other taxonomy merely because v3.10 listed a class.

For each Atlas GAP, inspect current recurring need and existing authority, then choose exactly one evidence-backed disposition:
- `KEEP_EXISTING`;
- `CREATE_CANONICAL_ARTIFACT` because a recurring normative need is proven;
- `NOT_NEEDED` because current repository behavior does not require a separate normative class;
- `BLOCKED` with exact missing owner decision/evidence.

`OPTIONAL` is not terminal unless the audit contract accepts it with an explicit trigger and no current need. Never invent content to make Matrix L look symmetrical.

## Atlas acceptance

1. Rebuild the relevant provider material inventory from the exact current protected Atlas head.
2. Resolve architecture/contract/governance/policy/test classes with explicit canonical owner/path or evidence-backed `NOT_NEEDED`.
3. Resolve operations/recovery classes based on actual recurring FullWorld/publication/local-E2E operational need; one-off evidence remains evidence, not automatically a runbook.
4. Classify retained prompts with stable identity/version/status/owner and terminal one-shot semantics.
5. Reconcile active task packets to live GitHub Issue/PR lifecycle authority; stale terminal packets cannot remain active.
6. Preserve the historical FullWorld handoff as evidence if it is already terminal; do not rewrite it into live authority.
7. Add high-signal deterministic checks to the existing Atlas gate only where needed to prevent known IA drift.
8. Preserve extraction/provenance and publication-rights facts unchanged.

## Parallel-work safety

Game, Platform and Recovery agents may run simultaneously. Do not touch their repositories/branches/Issues/PRs. Inspect Atlas live task ownership before editing and use exactly one dedicated Issue/task, branch and PR for this work.

## Validation

Before completion:
- current-head material inventory has exact SHA binding;
- every targeted GAP has one explicit terminal disposition;
- no empty taxonomy was created for symmetry;
- prompt/task lifecycle validators pass;
- any new canonical doc has owner/scope/lifecycle/supersession metadata appropriate to its class;
- full diff contains no product/runtime/generated-data changes;
- `atlas-gate` and `provenance-gate` remain green on the exact final head when required by live policy;
- reviews/threads are clean;
- squash merge and source-branch cleanup are verified;
- resulting `main` contains the terminal IA state.

Product/browser/runtime E2E is `NOT_APPLICABLE` unless this task improperly changes executable behavior; executable behavior changes are forbidden.

## Completion definition

DONE requires all Atlas-targeted IA GAPs in this prompt to be closed by current-head evidence, explicit canonical artifacts, or valid `NOT_NEEDED` dispositions. Do not claim migration, Recovery or whole-v3.10 completion.

## Final response

Return only:

STATUS: DONE | BLOCKED
ALIAS: OTERYN-V310-ATLAS-DOC-IA-CLOSEOUT
ISSUE: <url/number>
PR: <url/number>
MERGE_COMMIT: <sha or NONE>
ATLAS_HEAD_AUDITED: <sha>
GAP_DISPOSITIONS: <GAP -> disposition>
CANONICAL_ARTIFACTS_CREATED: <list or NONE>
NOT_NEEDED_DECISIONS: <list or NONE>
CHANGED_PATHS: <exact list>
VALIDATION: <exact evidence>
OUT_OF_SCOPE_FINDINGS: <list or NONE>
BLOCKERS: <list or NONE>
SCOPE_CONFIRMATION: No work outside the bounded Atlas v3.10 Documentation/Agent IA scope was performed.
