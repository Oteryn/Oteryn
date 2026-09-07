# Persistent autonomous execution — historical decision handoff

Status: provenance only; not policy or a dispatchable task.
Governing task: `Oteryn/Oteryn#108`.

## Decision retained

One owner-visible task must survive worker/session/tool/context boundaries safely
and truthfully. The historical owner preference was “Chat-first, GitHub-native
async, Work-by-exception.” Current capability selection is governed by the merged
capability-based contract, not by that historical product-label preference.

The implementation is now in
`docs/agents/contracts/PERSISTENT_AUTONOMOUS_CONTINUATION_POLICY.md`,
`ecosystem/agent-continuation-policy.json` and
`tools/governance/agent_continuation_policy.py`. Bounded lifecycle semantics remain
owned by the bounded execution contract. Earlier duplicated enums, pairing tables,
checkpoint procedures and pre-implementation branch sequence remain in Git history.
They are not an instruction to rebuild completed work.

For an authorized continuation, use
`docs/agents/prompts/OTERYN-CHAT-FIRST-AUTONOMY-CONTINUATION.md` and the live task.

## Provider closeout evidence retained

META provenance does not authorize provider writes. A defer/exclusion counts only
when canonical #108 (or its explicitly named successor Issue) contains an
`OTERYN_PROVIDER_SCOPE_DECISION_V1` comment with:

- exact provider repository and exact current adoption task;
- `DEFER|EXCLUDE` and a non-empty reason;
- META main SHA and provider main SHA.

At closeout, re-read that exact comment, verify the author currently has sufficient
repository-admin/owner authority, confirm provider/task binding and reject a record
superseded by a later owner decision. Missing authorization, a generic handoff or
unknown permission is not implicit defer. This retained evidence detail supports the
canonical continuation contract; it does not grant authority or replace live facts.
