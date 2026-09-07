# Oteryn Prompting Standard

Policy: `OTERYN_ORGANIZATION_AGENT_POLICY@3.0.0`

Write a **task-specific delta** over applicable repository instructions. Keep the observable objective, important boundaries, unique domain knowledge and acceptance evidence. Do not restate the agent operating system.

## Task content

Use only fields that materially affect the task; these labels are examples, not a required Markdown schema:

- `ROLE / OUTCOME`: one observable result and the responsibility needed to deliver it.
- `AUTHORITY / SCOPE DELTA`: writable scope and task-specific prohibited effects.
- `LIVE LOCATORS`: identifiers needed to resolve current task/repository facts.
- `DOMAIN CONSTRAINTS / DEPENDENCIES`: important knowledge and prerequisites not already supplied.
- `ACCEPTANCE / VALIDATION DELTA`: evidence specific to this result.
- `STOP / HANDOFF DELTA`: exceptional boundaries or recovery requirements not already governed.

Omit a section when it has no task-specific content. A long specification is appropriate when its details change the correct result; redundant global procedure is not.

## Inheritance and authority

A remote META binding identifies a version, not automatic instruction delivery. Rely on the verified local bootstrap and load relevant bound sources when needed. Do not copy full GitHub, concurrency, Remote Desktop, review, retry or merge procedures into each prompt. A plain source locator for a relevant task is allowed.

Aliases provide discovery, not authority. Refresh changing lifecycle facts rather than treating a pasted SHA/status as current truth. Do not ask the owner for a fact that an authorized read can resolve. State safe, reversible assumptions; never assume permission, destructive intent or waived acceptance.

## Execution guidance

Give direct instructions and a concrete success target. Prescribe a sequence only when ordering protects correctness/safety or evaluation demonstrates a need. Avoid generic expert praise, routine requests for exposed chain-of-thought, and examples that add no useful distinction.

One worker is normal; delegate only independent work with clear boundaries and worthwhile benefit. Keep model/effort settings outside the task's semantic contract and verify the actual configuration where supported. Do not invent a control merely by adding metadata or request the highest effort by template.

Create a skill for a repeatable specialized procedure, not generic engineering advice. Put a precise selection trigger in its description and load details on demand. Use explicit-only invocation where supported when accidental activation has no value; verify behavior on the actual client.

A handoff stores coordinates, material completed/remaining work, evidence, disposition and the next safe action. It is not another policy copy, a new authorization or a claim of background execution.
