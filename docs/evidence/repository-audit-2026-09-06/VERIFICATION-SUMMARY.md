# Verification summary — Oteryn repository audit 2026-09-06

This file contains the public-safe verification evidence supporting the repository audit. It intentionally omits local host identifiers, credentials, token values, private filesystem paths, and raw client configuration.

## Snapshot integrity

- repository: `Oteryn/Oteryn`
- audited revision: `0c493896040072badeff1f333eb83d7114a993ff`
- audited tree: `77c33f4c2d3bffcd5983e35928d870d618cb5f68`
- tracked files: `78`
- tracked bytes: `844834`
- independent blob comparison: `0` mismatches
- Python syntax parse: `14/14`
- JSON parse: `7/7`
- YAML parse: `.github/dependabot.yml`, `.github/workflows/ci.yml`, `.github/workflows/terminal-branch-lifecycle.yml` PASS
- `git fsck`: PASS
- final tracked working tree: clean
- final diff check: PASS

## Repository-native test execution

| Test surface | Result |
|---|---|
| `tools/governance/test_agent_execution_routing.py` | PASS |
| `tools/governance/test_remote_desktop_action_gate.py` | PASS |
| `tools/governance/test_merge_queue_workflow_contract.py` | PASS |
| `tools/governance/test_agent_continuation_policy.py` | 26/26 PASS |
| `tools/governance/test_agent_continuation_review_repairs.py` | 4/4 PASS |
| `tools/governance/test_bounded_execution_guard.py` | Windows: 20 PASS + 1 harness ERROR because child process invokes literal `python3`; Linux: 21/21 PASS |
| `tools/governance/test_verify_ai_review_evidence_compat_v1.py` | does not start: `ModuleNotFoundError` for removed `test_verify_ai_review_evidence_core` |

The last test is outside the active `meta-gate`; its failure is evidence of an orphaned compatibility test, not a failure of the current required gate.

## Native CI validation blocks

The unchanged validation logic from `.github/workflows/ci.yml` was executed against the audited checkout:

- META repository contract: PASS (`7` JSON files, `4` repository entries, `0` release manifests)
- simplified governance desired state: PASS
- compatibility JSON Schema declaration: valid Draft 2020-12
- limited Ruff check over authored Python: PASS

No release manifest existed, so this does not constitute end-to-end release-instance validation.

## CI history inspected

Audit-period inventory reconciled `268` workflow runs. For current `META CI` during the inspected window:

- total: `165`
- success: `112`
- failure: `45`
- cancelled: `8`
- `merge_group`: `12/12` success
- `push`: `13/13` success

Observed wall-clock proxy (`updated_at - created_at`) for the 165 META CI runs:

- median: `12 s`
- p95 nearest-rank: `27 s`
- max: `37 s`

This is not billed duration or CPU time.

## Live repository governance readback at audit close

- protected branch: `main`
- required status: `meta-gate`, GitHub Actions App id `15368`
- strict required-status freshness: `false`
- required approving reviews: `0`
- required CODEOWNER review: `false`
- stale-review dismissal: `false`
- admin enforcement: `true`
- linear history: `true`
- conversation resolution: `true`
- force pushes: disabled
- protected-branch deletion: disabled
- merge method: squash only; merge/rebase disabled
- repository auto-merge: enabled
- delete source branch on merge: enabled
- Merge Queue observed: `SQUASH`, `ALLGREEN`, maximum build entries `5`, maximum merge entries `5`, minimum `1`, wait `300 s`, check response timeout `3600 s`, zero queued entries at readback
- Actions: enabled; default workflow token `read`; Actions may not approve PR reviews
- secret scanning: enabled
- secret scanning push protection: enabled
- Dependabot security updates: enabled
- private vulnerability reporting: disabled
- CodeQL default setup: not configured; code-scanning analyses endpoint returned no analysis
- environments: `0`
- deployments: `0`
- releases: `0`
- tags: `0`
- repository webhooks visible through the inspected endpoint: `0`

## Publication drift note

After the audit closed, protected `main` advanced from `0c493896040072badeff1f333eb83d7114a993ff` to `d0d5a54c5f06db9423d14b17e7f8eadefd15c6fb` through PR #152. The audit report is intentionally snapshot-bound to the earlier revision; the publication PR is based on the later `main` and does not claim to have semantically re-audited PR #152.

## Limits

The audit did not perform destructive or mutating governance canaries, did not read secret values, did not certify every possible bypass path, did not re-test production recovery, and did not measure billing/token A/B or all client platforms.
