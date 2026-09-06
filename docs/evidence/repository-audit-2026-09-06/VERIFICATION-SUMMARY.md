# Verification record — R3

Audited commit: `0c493896040072badeff1f333eb83d7114a993ff`. Three categories below must not be conflated.

## A. Prior actual execution, preserved rather than rerun

`evidence/prior-native-verification.json` gives commands, scope, process-result locators, counts and failure classes from R2. These are structured records of returned tool output, not invented raw logs.

| Native suite | Result |
|---|---|
| `test_agent_execution_routing.py` | Windows PASS / 0 |
| `test_remote_desktop_action_gate.py` | Windows PASS / 0 |
| `test_merge_queue_workflow_contract.py` | Windows PASS / 0 |
| `test_agent_continuation_policy.py` | Windows 26/26 PASS / 0 |
| `test_agent_continuation_review_repairs.py` | Windows 4/4 PASS / 0 |
| `test_bounded_execution_guard.py` | Windows 20 PASS + 1 ERROR / 1; hardcoded python3 child / 9009 |
| `test_verify_ai_review_evidence_compat_v1.py` | Import error before tests / 1; outside active CI |

The same unchanged bounded suite passed 21/21 on Linux using three exact source blobs. Full prior log: `evidence/prior-linux-bounded.log`. This is not a full six-suite local Linux execution.

Additional prior checks: both original Python CI blocks PASS; JSON 7 parse, Python 14 AST, YAML 3 parse, schema declaration validity, auxiliary Ruff E9/F63/F7/F82, fsck and clean diff/status. Schema declaration validity does not repair missing instance validation; auxiliary lint is not CodeQL.

Historical successful exact-snapshot GitHub evidence: merge_group run `33751703790`, job `100636500304`; push run `33751753882`. No fresh dispatch is claimed.

## B. Fresh R3 diagnostics and evidence checks

`evidence/native-probe-results.json` records exact inputs, commands, stdout/stderr and exit status for seven calls to original code:

| Case | Exit | Interpretation |
|---|---:|---|
| Empty expected and observed arrays | 0 | TARGET with no repositories: AUD-10 |
| Missing expected array | 3 | INVALID control |
| Four expected, no observations | 2 | UNKNOWN control |
| Four expected, matching synthetic observations | 0 | TARGET control, not real GitHub compliance |
| Original inline block, canonical policy | 0 | Baseline control |
| Same block, only META merge_queue changed true → 1 | 0 | Numeric value accepted: AUD-11 |
| Original CLI, numeric policy versus boolean observations | 1 | Typed mismatch DRIFT: AUD-11 |

CLI Git blob: `8f165e91ad0bb06131f1955264a873a487369ae5`. Canonical policy blob: `049a3fff02451fdbc8ec75dd6bc017466911bb94`. Source workflow blob: `a198350259d8f9d082732cb0c4d99f90c6bf389c`. Extracted inline Python SHA-256: `ca07ab50e7032d51af4322d1c1af6ed8520209f0719473adaf6115ca5b00a7ef`. Extraction removes only YAML indentation; independently matched a read-only `git show` extraction from the exact source commit.

Temporary synthetic data were outside the audited repository. Original source bytes were unchanged before/after. No regression-test source, implementation repair, entire altered CI run, bypass experiment, package installation or new model execution occurred.

Historical CI export recovery: original file SHA-256 `24775c60ffbb0944e9170896483badcf773f07ac519950c3a63dd1dd6073029a`; three CSV parts verified separately and joined by exact ID. `evidence/ci-recalculation.json` recomputes 268 total / 165 META records, META 112 success / 45 failure / 8 cancelled, and latency proxy 12 s median / 27 s p95 nearest-rank / 37 s maximum. These are not CPU time, billing or a forecast. No same META workflow/event/head group contains both success and failure; this is not proof of universal absence of flakes.

The retained audit clone was read again: HEAD `0c493896...`, tree `77c33f4...`, empty porcelain, diff exit 0 (read-only process result 32792). Seven SKILL bodies and seven invocation metadata files were fully read cumulatively and hashed; no skill was activated just because it was audited.

## C. Publication verification

R3 publication is a separately authorized documentation operation on PR #153. It changes only audit material, not product code, tests, policy, workflow or protected settings. Exact prepared content hashes and a docs-only diff are checked against the remote commit. Existing PR-triggered META CI is read, not manually dispatched.

A new commit or green publication check does not make historical settings current, prove an absent transport firewall, perform a production restore, or implement the recommended fixes.
