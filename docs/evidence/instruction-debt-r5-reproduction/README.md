# R5 reproduction evidence correction — 2026-09-07

This is an evidence addendum for PR151-02 from META remediation #154, not an operational policy or a new provider audit.

## Correction to section E of the R5 audit

The original R5 report refers to a companion pack containing `probes/liveness_probe.py`, `probes/atlas_allowlist_probe.mjs`, result files and a manifest, but supplies no durable locator. That original pack was not recovered from the accessible uploaded files or PR discussion. Its original bytes and execution record therefore remain **NOT_AUTHENTICATED**; this addendum does not claim to recover them or retrospectively qualify the original harness.

A **new reproducibility replacement** is committed beside this README: [reproduce.py](reproduce.py), [results.json](results.json) and [manifest.json](manifest.json). On 2026-09-07 it reproduced all 13 cases described in section E using the exact historical provider source blobs identified by that report. This closes the missing durable reproducer; it does not assert that current provider runtime still behaves that way.

## Scope and reproduction

The Python part executes only the original `Policy`, `Finding`, `TaskResult` and `evaluate_tasks` definitions. Its task evaluator is deliberately stubbed to isolate directory handling and error aggregation. The JavaScript part executes only `allowedNormal`, with its original archive constant and throwing `fail` helper. No CLI, GitHub client, Git mutation, provider CI or runtime is executed. The harness performs no network requests and writes fixtures only to a temporary directory.

Download the following public files at their immutable revisions, then run the harness. It refuses any source whose Git blob identity differs from the recorded snapshot.

```sh
curl -fL 'https://raw.githubusercontent.com/Oteryn/Oteryn-Platform/3b2ea1c7392187d5d22488673073dc8f8305a374/tools/agents/task_issue_liveness.py' -o /tmp/task_issue_liveness.py
curl -fL 'https://raw.githubusercontent.com/Oteryn/Oteryn-Atlas/51623c7dab2346cee39cd51e3caa845bf4b65426/tools/maintenance/verify-maintenance-diff.mjs' -o /tmp/verify-maintenance-diff.mjs
python reproduce.py --platform-source /tmp/task_issue_liveness.py --atlas-source /tmp/verify-maintenance-diff.mjs
```

Recorded environment: Python 3.13.5, Node v22.16.0. Result: **13/13 match the reported isolated behavior**. L01/L02 expose success for missing/non-directory roots; L03/L04 are empty/readme controls; L05/L06 exercise controlled error aggregation. A01–A07 exercise the snapshot maintenance allowlist. Passing reproduction is not a statement that the counterexamples are safe or repaired.

The manifest records SHA-256 hashes of all three evidence files and exact provider commit/path/blob identities. Use the immutable commit locator in the updated PR #151 description, not a temporary sandbox or expiring Actions artifact.
