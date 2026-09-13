# Central Merge Queue Broker rollout

Goal: remove execution-surface dependence from protected integration without weakening exact-head Merge Queue semantics.

Scope: central META broker, policy 3.2.0 transport authorization, tests, and later provider adoption. No runtime, ruleset, protection, required-check, production, or credential-value mutation.

Acceptance: exact-target broker request; live target/check/thread preflight; only native `merge-async` with exact `sha` and `merge_action="merge_queue"`; UUID/readback semantics; fail-closed reconciliation; fresh `meta-gate`; clean review; normal Merge Queue; protected-main readback; provider repin only after META protection.

Refs #187.
