# Oteryn v3.10 parallel closeout agent prompts

These prompts split the remaining `OTERYN-ORG-AUDIT-v3.10` closeout into independent workstreams. Every executor must refresh live state before mutation; the checkpoint values in the prompt are starting evidence, not authority.

## Execution aliases

| Alias | Primary repository | Primary lifecycle | Ownership |
| --- | --- | --- | --- |
| `OTERYN-ORG-RUNNERS-PLATFORM-ACL-LEGACY-CLOSEOUT` | `Oteryn/Oteryn` + `Oteryn/Oteryn-Platform` | META #34 / Platform #1215 | **ONE_SHOT**; archive as historical evidence when its terminal contract closes — Platform trusted-main proof, runner-group ACL readback, dependency-aware legacy retirement |
| `OTERYN-GAME-RUNNER-ACCEPTANCE-CLOSEOUT` | `Oteryn/Oteryn-Game` | Game #34 / PR #36 | **ONE_SHOT**; archive as historical evidence when its terminal contract closes — policy-permitted independent review, merge and trusted-main Game runner acceptance |

## Parallelism rules

- One active owner per branch/PR.
- Executors must not modify another executor's active branch.
- Cross-workstream repositories/issues may be inspected read-only for dependency state.
- `UNKNOWN` remains `UNKNOWN` until direct evidence exists.
- Do not retire the legacy runner until all replacement-route and ACL prerequisites are terminal PASS.
- Do not consume owner-funded/metered AI outside the applicable repository policy and explicit authorization.

## Coordinator

The coordinator branch is `docs/issue-16-org-audit-v3-10-final`.

The coordinator owns:

- `docs/governance/audits/OTERYN-ORG-AUDIT-v3.10-FINAL-TERMINAL-REPORT.md`;
- the v3.10 documentation/agent IA addendum and deterministic validation record carried from the validated successor;
- `docs/governance/audits/OTERYN-ORG-AUDIT-v3.10-COORDINATOR-CHECKPOINT-20260822.md`;
- final evidence reconciliation after executor merges;
- final #38 runner-audit reconciliation, v3.10 PR readiness, cleanup and terminal verdict.

The coordinator must not rewrite executor-owned implementation branches while they are active.

## Historical one-shot prompt

`OTERYN-ORG-AUDIT-META-DESIRED-STATE-CLOSEOUT` is terminal and must not be invoked: PR #37 was squash-merged as `c0dbad93f791953d5efcc6b556e6be73693f0a4f`, and predecessors #23/#9 were closed as superseded. Its file is retained only as historical execution evidence.
