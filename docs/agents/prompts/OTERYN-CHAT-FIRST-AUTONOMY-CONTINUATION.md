# OTERYN-CHAT-FIRST-AUTONOMY-CONTINUATION

Task template for `Oteryn/Oteryn#108`, not standing authorization. Alias:
`OTERYN-CHAT-FIRST-AUTONOMY-CONTINUATION`.

## Outcome

Continue the smallest remaining adoption or correctness delta for the organization
continuation layer. Preserve one owner-visible task across worker/session/tool/wait/
context boundaries without creating a second bounded lifecycle. The central
implementation already exists; do not create a replacement branch or implementation
merely because the historical design described those steps.

## Task authority and dependencies

Resolve the live #108 task and current implementation/adoption PRs. Relevant task
locators are #69 (bounded execution), #104/#107 (routing/provider convergence) and
the current provider adoption tasks. Their historical status is not current evidence.

Use the applicable `AGENTS.md` and
`docs/agents/contracts/PERSISTENT_AUTONOMOUS_CONTINUATION_POLICY.md` with
`ecosystem/agent-continuation-policy.json`. They own the six execution coordinates,
closed disposition/mechanism pairs, lineage, checkpoint/resume verification and
capability selection. Do not copy their enums, retry counters or procedures here.

META scope does not authorize Game, Platform or Atlas mutation. Resolve explicit
owner authorization for each exact provider and current adoption task before writes.
A provider defer/exclusion must satisfy the continuation contract's
`OTERYN_PROVIDER_SCOPE_DECISION_V1` evidence; missing permission is not an implicit
defer. Preserve the complete record fields and owner/supersession checks defined by
the accepted #108 design and the retained decision handoff.

## Acceptance

- Preserve bounded retry/evidence continuity across worker and surface changes.
- Qualify changed continuation behavior with the contract's focused RED → GREEN
  regressions and existing aggregate-gate wiring; do not introduce another gate.
- Verify actual provider delivery and representative resume behavior separately
  from static binding/schema checks.
- Close the programme only after protected-main readback and provider adoption or
  valid scope decisions prove the remaining #108 scope complete.

Keep active context minimal and durable state in GitHub. Checkpoint after material
milestones and before long/failure-prone operations, context rotation, external
waiting or worker release, not after every tool call. Record exact completed/
remaining work, evidence, blockers and one next action; do not use checkpoint-only
commits to perturb a frozen candidate. Rotate only with a real successor mechanism.

Keep owner-facing noise low: notify for verified completion, a genuine owner/
permission/safety decision, or a required owner reinvocation when no automatic
continuation exists. Report STALLED when no verified mechanism can await changed
material facts and resume, and report an unavoidable protected-integration capability
gap after safe alternatives are exhausted. Routine checkpoints and recoverable
failures are not reasons to interrupt the owner. Apply the canonical resume rules to
worker release; do not claim background execution without a verified mechanism.
