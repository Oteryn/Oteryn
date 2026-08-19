# OTERYN-ORG-GOVERNANCE-ARCHITECTURE-ULTRA-AUDIT-v3.10-DOCUMENTATION-AGENT-IA-ADDENDUM

## ORGANIZATION / GOVERNANCE / CODEX / GITHUB / CI / TEST / SECURITY / ARCHITECTURE AUDIT

**Base contract:** `OTERYN-ORG-GOVERNANCE-ARCHITECTURE-ULTRA-AUDIT-v3.9-EXECUTION-OPTIMIZED-FINAL`

**Revision intent:** extend the v3.9 audit contract with a mandatory, implementation-ready **Documentation & Agent Information Architecture** audit. This revision does not rewrite or retroactively change the historical v3.9 audit result. A previous v3.9 `PASS`, report, recommendation ledger, evidence ledger or migration verdict is evidence only; it does **not** automatically satisfy the new v3.10 requirements below.

All v3.9 requirements remain mandatory unless this addendum explicitly strengthens them. Where this addendum conflicts with v3.9, the stricter v3.10 requirement wins for a v3.10 execution.

Use:

```text
AUDIT_CONTRACT_VERSION = v3.10
BASE_AUDIT_CONTRACT_VERSION = v3.9
```

---

## 0D. DOCUMENTATION & AGENT INFORMATION ARCHITECTURE — GLOBAL INVARIANT

The audit must produce a concrete information architecture for durable repository documentation and autonomous-agent operating material across:

```text
Oteryn/Oteryn
Oteryn/Oteryn-Game
Oteryn/Oteryn-Platform
Oteryn/Oteryn-Atlas
```

and the bounded historical source estate already required by v3.9.

Do not stop at statements such as:

```text
keep root AGENTS short
put procedures in Skills/scripts
use Issues as lifecycle authority
keep META thin
```

Those remain valid but are insufficient for v3.10.

The final audit must determine, from live repository evidence, **where every materially relevant documentation/agent artifact class belongs, who owns it, how it is named, how long it lives, what may duplicate it, how it is superseded or archived, and what deterministic checks prevent drift**.

The target must remain lean. Do **not** create empty directory taxonomies merely for symmetry.

---

## 0E. DOCUMENTATION/AGENT MATERIALITY AND ENUMERATION

For every permanent repository, enumerate materially relevant Markdown and adjacent machine-readable governance/agent artifacts, including when present:

```text
README.md
AGENTS.md
AGENTS.override.md
nested AGENTS.md / AGENTS.override.md
CONTRIBUTING.md
SECURITY.md

docs/architecture/**
docs/contracts/**
docs/governance/**
docs/ci/**
docs/testing/**
docs/release/**
docs/operations/**
docs/recovery/**
docs/agents/**
docs/evidence/**
docs/generated/**

task packets
programme/epic documents
handovers/checkpoints
prompt libraries
prompt aliases/indexes
runbooks
operator/recovery procedures
audit/review instructions
review evidence
release/migration evidence
generated indexes/reports
human-only reference documentation

machine-readable policy/config/manifest files that are normative companions to prose
deterministic validators/generators that enforce documentation or agent contracts
```

Do not infer absence from a shallow directory listing. Use the v3.9 completeness, pagination, access-gap and evidence rules.

If a repository or control-plane surface cannot be fully inspected, record:

```text
UNKNOWN (GAP-ID: exact missing path, object, API visibility or permission)
```

rather than inferring a compliant structure.

---

## 10A. DOCUMENTATION/AGENT ARTIFACT CLASSIFICATION

In addition to v3.9's context-loading classification, classify every materially relevant documentation/agent artifact into exactly one primary operational class:

```text
NORMATIVE_AGENT_INSTRUCTION
GOVERNANCE_POLICY
MACHINE_READABLE_POLICY
ARCHITECTURE_ADR
CROSS_REPO_CONTRACT
PROVIDER_CONTRACT
CI_POLICY
TEST_STRATEGY
RUNBOOK_OPERATIONAL
RUNBOOK_RECOVERY
PROMPT_REUSABLE
PROMPT_TASK_EXECUTION
PROMPT_ONE_SHOT
TASK_PACKET_ACTIVE
TASK_PACKET_ARCHIVED
PROGRAMME_OBJECT
HANDOVER_CACHE
EVIDENCE_REVIEW
EVIDENCE_RELEASE
EVIDENCE_MIGRATION
GENERATED_REFERENCE
HUMAN_REFERENCE
HISTORICAL_ARCHIVE
OBSOLETE_DELETE
UNKNOWN
```

A file may have secondary tags, but it must have one primary operational class so that ownership, lifecycle and validation are deterministic.

For each material artifact record at minimum:

```text
REPOSITORY
CURRENT_PATH
PRIMARY_CLASS
AUTHORITY_OWNER
CANONICAL_REPOSITORY
CANONICAL_TARGET_PATH
PURPOSE
CONSUMERS
NORMATIVE=YES|NO
MUTABLE_STATE_ALLOWED=YES|NO
LOCAL_COPY_ALLOWED=YES|NO
OVERRIDE_OR_PRECEDENCE_RULE
REQUIRED_METADATA
LIFECYCLE
RETENTION_OR_EXPIRY
SUPERSESSION_OR_ARCHIVE_RULE
CI_OR_DRIFT_ENFORCEMENT
MIGRATION_ACTION
EVIDENCE_ID
```

If the file is not canonical, state the exact canonical object it references.

---

## 10B. ROOT AND NESTED INSTRUCTION CONTRACT

Retain v3.9's short/stable root `AGENTS.md` model and make its placement mechanically auditable.

For every permanent repository decide and report:

```text
ROOT_AGENTS_PATH
ROOT_AGENTS_MAXIMUM_DURABLE_SCOPE
NESTED_AGENTS_ALLOWED_PATHS
WHY_EACH_NESTED_FILE_EXISTS
AGENTS_OVERRIDE_ALLOWED=YES|NO
IF_YES: EXACT_REPLACEMENT_SEMANTICS_AND_PATH
FALLBACK_INSTRUCTION_FILES
ROUTING_ENTRYPOINTS
```

Root `AGENTS.md` must not become a directory index dump. It should route only to the smallest durable set needed before task-specific discovery.

Explicitly detect and classify as drift when permanent root/nested instruction files contain transient mutable state such as:

```text
one-shot task IDs
current branch
current PR
current head SHA
current CI result
temporary migration phase
session handover
temporary owner allocation
one-shot AI authorization
temporary runtime endpoint
historical source coordinate presented as current authority
```

Allowed durable examples are stable repository identity, authority boundary, safety boundary, canonical routing location, required merge discipline and invariant validation rules.

---

## 11A. DOCUMENTATION & AGENT SOURCE-OF-TRUTH CONTRACT

Extend v3.9 section 11.

For each artifact class select one authority pattern:

```text
ORG_CANONICAL
ORG_BASELINE_WITH_LOCAL_EXTENSION
META_CANONICAL
REPOSITORY_CANONICAL
TASK_LOCAL
GITHUB_NATIVE
GENERATED
HISTORICAL_ONLY
NOT_NEEDED
UNKNOWN
```

The audit must explicitly enforce these ownership principles unless live evidence proves a better model:

```text
META
  owns only genuinely cross-repository governance, topology, ecosystem ADRs,
  compatibility/release composition and organization-wide minimums.

GAME / PLATFORM / ATLAS
  own provider-specific architecture, prompts, runbooks, operational docs,
  implementation contracts, provider tests and provider evidence.

GITHUB ISSUES
  own mutable lifecycle state: status, owner, dependencies and acceptance.

PULL REQUESTS + CHECKS
  own implementation/review integration and exact-head validation truth.

ROOT/NESTED AGENTS
  own durable pre-routing normative agent instructions only.

SKILLS
  own reusable on-demand judgment-heavy procedures when the runtime supports them.

DETERMINISTIC SCRIPTS
  own machine-checkable validation, generation and cleanup mechanics.

EVIDENCE
  proves a fact or historical result but does not silently become normative policy.

GENERATED DOCUMENTS
  are non-authoritative unless a separate explicit contract promotes them.
```

Do not copy provider-owned normative documentation into META for convenience. Prefer immutable references/coordinates when META must consume provider authority.

---

## 11B. CENTRAL VS LOCAL DOCUMENTATION RULE

The audit must decide separately for every artifact class whether it belongs in:

```text
ORGANIZATION GITHUB SETTINGS
OPTIONAL .github / .github-private
META
GAME
PLATFORM
ATLAS
PER TASK / ISSUE
GITHUB NATIVE OBJECT
USER/GLOBAL CODEX CONFIG
REPOSITORY-LOCAL CODEX CONFIG
GENERATED ARTIFACT STORAGE
HISTORICAL ARCHIVE
```

A single category must not be assigned to two mutable canonical authorities.

`.github` / `.github-private` may own only capabilities actually inherited/supported by GitHub and justified by the v3.9 section-25 decision. They must not become an invented organization-wide AGENTS/prompt/config inheritance mechanism.

---

## 12A. CANONICAL DOCUMENTATION/AGENT PATH DECISION

For each permanent repository, the audit must produce an **exact target tree based on actual need**, using existing conventions first.

Evaluate these candidate locations; adopt only those that have real content/ownership:

```text
/
├── README.md
├── AGENTS.md
├── CONTRIBUTING.md
├── SECURITY.md
└── docs/
    ├── architecture/
    │   └── adr/
    ├── contracts/
    ├── governance/
    ├── ci/
    ├── testing/
    ├── release/
    ├── operations/
    ├── recovery/
    ├── agents/
    │   ├── prompts/
    │   ├── tasks/
    │   │   ├── active/
    │   │   └── archive/
    │   └── runbooks/
    ├── evidence/
    └── generated/
```

This is a **candidate taxonomy, not a mandate to create all directories**.

The audit must choose exact canonical locations for at least:

```text
reusable prompts
one-shot prompts while active
completed one-shot prompts
active task packets
archived task packets
programmes
handovers
agent runbooks
general operational runbooks
recovery/break-glass runbooks
review evidence
release evidence
migration evidence
generated reports/indexes
human-only reference docs
```

Where two current conventions compete, compare them and select one. For example, explicitly decide whether agent-specific evidence belongs under `docs/agents/evidence/` or the repository-wide `docs/evidence/`; do not leave both as independent conventions.

---

## 12B. TASK / PROMPT / HANDOVER / EVIDENCE SEPARATION

Strengthen v3.9 section 12.

### Task packets

A Markdown task packet is optional execution detail. It must never become a second lifecycle database.

If task packets are retained, define:

```text
canonical directory
filename/ID convention
required Issue link
required owning repository
technical scope/acceptance fields
whether current SHA/branch/PR may be cached
how stale cached values are detected
active -> archive/delete transition
```

### Prompts

For every durable prompt define:

```text
PROMPT_ID
TITLE/ALIAS
CLASS
VERSION
STATUS
AUTHORITY_OWNER
SCOPE
INPUT_CONTRACT
OUTPUT_CONTRACT
PROHIBITED_ACTIONS
VALIDATION_CONTRACT
SUPERSEDES / SUPERSEDED_BY
```

Do not use filenames such as repeated `final`, `final2`, `v2`, `v3`, `new`, `latest` as the only lifecycle/version mechanism when a stable prompt identity can be used.

One-shot execution prompts must have a terminal disposition:

```text
DELETE
ARCHIVE_HISTORICAL
PROMOTE_TO_REUSABLE_TEMPLATE
KEEP_AS_EVIDENCE
```

### Handovers

A handover is a cache, not authority. Define:

```text
task/Issue identity
repository
PR when applicable
cached head SHA when useful
created/updated timestamp
author/agent
what remains
blockers/UNKNOWN
authoritative links
next action
expiry/supersession condition
```

A handover that has been superseded by live Issue/PR/check state must not remain discoverable as an active instruction.

### Evidence

Evidence must state:

```text
EVIDENCE_CLASS
SUBJECT
SOURCE
SOURCE_ID_OR_URL
REPOSITORY
COMMIT/HEAD/FINGERPRINT when applicable
CAPTURED_AT
VERIFIED_BY
IMMUTABLE_OR_MUTABLE
RETENTION_REASON
REDACTION_STATUS
```

Evidence may prove policy compliance but must not itself broaden authority.

---

## 12C. MINIMUM METADATA WITHOUT MARKDOWN BUREAUCRACY

Do not require YAML front matter on every Markdown file.

For each artifact class decide whether metadata belongs in:

```text
Markdown front matter
a small adjacent machine-readable registry
the GitHub Issue/PR object
the filename/path
no additional metadata
```

Prefer machine-readable metadata only where it prevents real drift.

At minimum, the audit must define deterministic identity for reusable prompts, active task packets, ADRs, handovers and retained evidence.

---

## 14A. DOCUMENTATION REPOSITORY HYGIENE

Extend v3.9 section 14 with documentation-specific hygiene.

Detect:

```text
duplicate canonical documents
duplicate prompt IDs/aliases
active and archived copies of the same task
orphan task packets with no live Issue when an Issue is required
orphan handovers
stale copied head/CI/review status
provider-owned docs copied into META
META-owned cross-repo policy copied and independently edited in providers
historical coordinates presented as current
broken canonical links
obsolete `final*` prompt/document families
generated output manually maintained as source of truth
evidence mixed into normative instructions
secrets/tokens/private data in docs/evidence
large binary/generated artifacts stored in documentation paths without purpose
```

Cleanup must remain evidence-based. Do not delete historical material solely because it is old.

---

## 16A. DOCUMENTATION/AGENT CI ENFORCEMENT

Extend the CI target architecture with a small, high-signal documentation/agent validation layer.

For each repository decide which of the following are justified and which are `NOT_NEEDED`:

```text
required root-file presence/non-empty checks
Markdown structural validation
machine-readable companion schema validation
duplicate prompt/task/ADR ID detection
canonical-path uniqueness
active-task packet -> live Issue consistency
closed Issue -> no authoritative active packet
stale cached head/PR/check detection where deterministic
forbidden transient-state patterns in root/nested AGENTS
forbidden historical coordinates in mutable active/governance paths
broken internal canonical links
generated-file provenance marker
no secrets/private material in committed docs/evidence
provider/META ownership boundary checks
obsolete legacy path detection
```

Rules:

1. Do not make prose CI brittle merely to enforce style.
2. Use deterministic checks for deterministic invariants.
3. Do not use an AI reviewer for a check a parser/script can prove.
4. CI enforcement must distinguish normative, active, archive, evidence and generated paths.
5. Historical/archive evidence may intentionally contain old coordinates; mutable authority paths may not.
6. Any live-GitHub consistency check must fail `UNKNOWN`/non-blocking or use a deliberately authorized read surface when API visibility is unavailable; it must not invent live state from Markdown.

Where the repository already has a stable gate (`meta-gate`, `game-gate`, `platform-gate`, `atlas-gate`), documentation/agent checks should feed the provider-owned gate rather than create unnecessary externally required check names.

---

## 17A. DOCUMENTATION/AGENT DRIFT DETECTION

Extend governance-as-code/drift detection to cover:

```text
artifact path drift
authority-owner drift
duplicate source-of-truth drift
prompt alias/version drift
AGENTS routing drift
nested AGENTS/override discovery drift
task packet <-> Issue drift
handover <-> current PR/head/check drift
active/archive split drift
runbook ownership drift
evidence retention/disposition drift
machine-readable policy <-> explanatory Markdown contradiction
legacy coordinate drift
generated/manual-state drift
```

The default drift checker is read-only.

Do not create a general GitHub/documentation auto-rewriter as part of the baseline.

---

## 19A. DOCUMENTATION/AGENT IMPLEMENTATION BACKLOG TYPE

Extend the v3.9 backlog item type enum with:

```text
DOCUMENTATION_IA
AGENT_INSTRUCTION
PROMPT_LIFECYCLE
TASK_LIFECYCLE
RUNBOOK
EVIDENCE_GOVERNANCE
DOCS_CI
```

Every documentation/agent backlog item must include:

```text
CURRENT_PATHS
TARGET_PATHS
AUTHORITY_OWNER
MIGRATION/DISPOSITION
BACKWARD_LINK_OR_REDIRECT_PLAN when applicable
ACCEPTANCE_CRITERIA
DETERMINISTIC_VALIDATION
ROLLBACK
```

Do not migrate documentation structure in the same PR as unrelated product behavior unless the changes are inseparable.

---

## 26A. TARGET TREE COMPLETENESS REQUIREMENT

The v3.10 target-tree output is incomplete unless each of the four permanent repositories shows, with `[KEEP]`, `[MOVE]`, `[NEW]`, `[GENERATED]`, `[OPTIONAL]`, `[REMOVE_AFTER_MIGRATION]` or `[NOT_NEEDED]`, the disposition of all material documentation/agent classes that apply to that repository.

The tree must make it possible for an implementation agent to answer without inventing policy:

```text
Where does a new reusable prompt go?
Where does a one-shot prompt go while active?
What happens to it when complete?
Where does an optional task packet go?
Where does it go when the Issue closes?
Where does a handover live and when does it expire?
Where does operational/recovery procedure live?
Where does review/release/migration evidence live?
Where does generated documentation live?
Which documents belong only in META?
Which remain provider-local?
Which paths are checked by CI?
```

Do not add empty paths just to satisfy the diagram.

---

## 29L. REQUIRED MATRIX L — DOCUMENTATION & AGENT INFORMATION ARCHITECTURE

Add mandatory Matrix L:

| Repository | Artifact class | Current path(s) | Canonical target path / GitHub object | Authority owner | Consumer | Required metadata | Lifecycle / retention | Local copy / override rule | CI / drift enforcement | Migration action | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|

Matrix L must cover at minimum, for every permanent repository where applicable:

```text
root AGENTS
nested AGENTS/override
architecture/ADR
contracts
governance policy
CI policy
test strategy
reusable prompts
one-shot prompts
task packets
programmes
handovers
agent runbooks
operations runbooks
recovery/break-glass
review evidence
release evidence
migration evidence
generated docs/indexes
human reference docs
machine-readable policy companions
documentation/agent validators
```

No ambiguous empty cell is allowed. Use `NOT_APPLICABLE`, `NOT_NEEDED` or `UNKNOWN (GAP-ID: ...)` explicitly.

---

## 30A. v3.10 DELIVERABLE-INTEGRITY CHANGES

For a v3.10 execution, replace:

```text
all required matrices A0 through K are present
all regression hypotheses H1-H13 have explicit verdicts
```

with:

```text
all required matrices A0 through L are present
all regression hypotheses H1-H14 have explicit verdicts
```

Add mandatory mechanical validation:

```text
Matrix L exists
Matrix L covers all four permanent repositories
every material documentation/agent artifact has a primary class
every normative artifact has exactly one canonical authority
every retained reusable prompt has stable identity/version/status metadata
every active task packet has an explicit lifecycle authority
every handover is explicitly non-authoritative and has an expiry/supersession rule
every evidence class has a retention/disposition rule
target trees answer all section-26A placement questions or mark NOT_NEEDED
no target tree creates empty taxonomy merely for symmetry
documentation/agent access gaps are explicit
G11 result is present
```

The historical v3.9 `report-validation.json` cannot satisfy these new checks.

---

## 30B. REPORT-SECTION STRENGTHENING

Keep the same **exact 21 H1 report sections** from v3.9. Do not add a 22nd report H1.

Strengthen their mandatory content as follows:

```text
Section 4
  include complete material documentation/agent inventory,
  primary artifact classes, duplicate-authority findings and context cost.

Section 5
  include H14 and documentation/agent IA risks.

Section 6
  include exact root/nested/override target placement and routing.

Section 7
  include exact canonical locations/lifecycles for tasks, prompts,
  handovers, programmes and runbooks.

Section 8
  include documentation ownership at META/provider contract boundaries.

Section 10
  include documentation/agent deterministic CI checks.

Section 13
  include the section-26A exact target-tree answers.

Section 14
  include artifact-class source-of-truth decisions and Matrix L references.

Section 15
  include file-level migration/disposition for material docs/agent artifacts.

Section 17
  include documentation/agent drift detection.

Section 19
  include ordered DOCUMENTATION_IA / AGENT_INSTRUCTION /
  PROMPT_LIFECYCLE / TASK_LIFECYCLE / RUNBOOK /
  EVIDENCE_GOVERNANCE / DOCS_CI backlog items.

Section 21
  include a concise final documentation/agent responsibility allocation.
```

---

## H14. NEW REGRESSION HYPOTHESIS — DOCUMENTATION/AGENT IA

Add to the regression ledger:

| ID | Hypothesis to reverify | Required outcome |
|---|---|---|
| H14 | Oteryn has principles for AGENTS/tasks/prompts/provider ownership but no fully explicit organization-wide documentation/agent information architecture covering canonical paths, artifact classes, metadata, retention/archive, duplication, evidence placement and deterministic enforcement. | Inventory current reality across META/Game/Platform/Atlas; identify what is already coherent; select the smallest exact target structure per repository; define canonical authority/lifecycle/retention/CI drift rules; do not create empty taxonomy; emit Matrix L and implementation backlog. |

H14 is not automatically a defect. The audit may conclude `ALREADY_RESOLVED` for any dimension that current repository evidence proves.

---

## 31A. NEW FINAL GATE G11 — DOCUMENTATION/AGENT INFORMATION ARCHITECTURE

Add:

| Gate | Pass condition / authoritative sections |
|---|---|
| G11 Documentation/agent IA | Sections 4, 6, 7, 8, 10, 13, 14, 15, 17, 19 and 21 plus Matrix L prove exact canonical placement, authority, metadata where operationally needed, lifecycle/retention, duplication/override rules, target-tree disposition and deterministic CI/drift enforcement for material documentation/agent artifacts across META/Game/Platform/Atlas. H14 has an explicit verdict. Empty taxonomy is not created for symmetry. Material missing visibility is `UNKNOWN (GAP-ID)` and constrains dependent conclusions. |

For v3.10, the audit is incomplete until **G1 through G11** resolve to:

```text
PASS
FAIL
UNKNOWN (GAP-ID / missing evidence)
```

No gate passes merely because v3.9 previously passed.

Update G10 deliverable-integrity wording from:

```text
matrices A0-K
H1-H13
```

to:

```text
matrices A0-L
H1-H14
```

---

## 32A. DOCUMENTATION/AGENT QUALITY BAR

For every major documentation/agent recommendation, the existing `REC_ID` must be sufficient to answer:

```text
WHY
AUTHORITY_OWNER
CANONICAL_LOCATION_OR_GITHUB_SETTING
CONSUMER
ENFORCEMENT
DRIFT_PREVENTION
MIGRATION_IMPACT
TRADE_OFF

ARTIFACT_CLASS
CURRENT_PATHS
TARGET_PATH
LIFECYCLE_RETENTION
DUPLICATION_OVERRIDE_RULE
DETERMINISTIC_VALIDATION
```

The last six fields may be stored in the recommendation's structured detail rather than expanding unrelated recommendation records.

A recommendation is not implementation-ready if an implementer still has to invent:

```text
which repository owns the document
which directory is canonical
whether a local copy is allowed
how the file is named/identified
whether it is normative or evidence
what happens when the task/prompt/handover completes
how supersession/archive works
what CI/drift check protects the rule
```

Avoid a universal documentation monorepo and avoid four identical empty directory trees.

The smallest correct architecture wins.

---

## OPTIONAL SIDECAR FOR LARGE INVENTORIES

If Matrix L would become an unreadable data warehouse, persist full file-level enumeration in:

```text
documentation-ia-inventory.json
```

and keep Matrix L as the complete class/path/authority/lifecycle decision view.

If used, the sidecar must include:

```text
schema_version
audit_contract_version
repository
commit_sha
path
artifact_class
authority_owner
canonical_target
normative
lifecycle
retention
disposition
evidence_ids
```

The sidecar is evidence/inventory, not a second policy authority.

---

# v3.10 EXECUTION INVARIANT

A v3.10 audit may reuse verified immutable evidence from v3.9, but it must **re-run the Documentation & Agent Information Architecture analysis against current live repository state**.

The previous v3.9 report remains a historical snapshot and must not be edited to pretend the new scope was audited on 2026-08-18.

For v3.10, completion requires:

```text
G1-G11 resolved
H1-H14 resolved
Matrices A0-L present
exact 21 H1 report sections preserved
documentation/agent target structure decided per permanent repository
no material artifact class left with ambiguous authority/path/lifecycle
all material access gaps explicit
mechanical report validation PASS
final artifact SHA-256 computed after final bytes
```

# END
