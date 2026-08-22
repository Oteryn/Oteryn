# Oteryn v3.10 parallel closeout agent prompts

**Status:** `HISTORICAL / COMPLETED - DO NOT EXECUTE`

These files preserve the executor instructions used during the 2026-08-22 closeout. All three workstreams are terminal; their checkpoint commands and mutable-state instructions are superseded by live GitHub/provider state, `docs/evidence/OTERYN-ORG-RUNNER-ACL-LIVE-CLOSEOUT-20260822.md`, and the final v3.10 report.

## Historical executor aliases

| Alias | Primary repository | Primary lifecycle | Ownership |
| --- | --- | --- | --- |
| `OTERYN-ORG-AUDIT-META-DESIRED-STATE-CLOSEOUT` | `Oteryn/Oteryn` | PR #37 | finish META desired-state/drift audit, exact-head R2, protected merge and predecessor reconciliation |
| `OTERYN-ORG-RUNNERS-PLATFORM-ACL-LEGACY-CLOSEOUT` | `Oteryn/Oteryn` + `Oteryn/Oteryn-Platform` | META #34 / Platform #1215 | Platform trusted-main proof, runner-group ACL readback, dependency-aware legacy retirement |
| `OTERYN-GAME-RUNNER-ACCEPTANCE-CLOSEOUT` | `Oteryn/Oteryn-Game` | Game #34 / PR #36 | policy-permitted independent review, merge and trusted-main Game runner acceptance |

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