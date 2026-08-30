# Agent Execution Policy Convergence Design

## Goal

Make Oteryn agent execution governance internally consistent and mechanically least-privileged across META, Game, Platform and Atlas without weakening GitHub-first authority, exact-head verification, task isolation or moving-main reconciliation.

## Authority model

META protected `main` owns the canonical execution-routing policy. Provider repositories adopt the current protected META policy by reference and must not pin a historical execution-policy commit as current authority. Historical SHAs remain provenance only.

Substantial work is effort-aware: classify `low`, `medium` or `high`; use `single_agent` when one worker is proportionate; use `parallel_when_beneficial` only when at least two materially independent streams can progress concurrently and the expected benefit exceeds coordination/integration cost. Parallelism uses the smallest useful lane count, one writer per branch/worktree and explicit leases for shared constrained resources.

## Remote Desktop call binding

The existing host-exception gate remains mandatory and fail-closed. A direct `Remote_Desktop_Commander.*` call must additionally pass a per-call gate immediately before invocation. The per-call gate validates the fresh routing packet/live GitHub state, semantic host action, exact connector tool identifier and exact call arguments.

Argument matching is exact after removing only policy-declared non-semantic runtime fields. The initial non-semantic set contains only `deviceId`, because device selection is transport/runtime identity rather than operation semantics. Command text, paths, timeouts, process identifiers and all other supplied arguments remain semantic unless policy explicitly classifies them otherwise.

A host-exception packet declares `requested_remote_desktop_calls` as exact `{tool, arguments}` records. An undeclared call, changed command, extra semantic argument, malformed declaration or unknown tool fails closed. The existing always-forbidden tool set remains always forbidden.

## Provider convergence and drift detection

A deterministic provider-adoption validator rejects:

- historical 40-hex META execution-policy pins presented as current authority;
- `parallel-first` / `parallel_first` requirements;
- serial-exception wording that contradicts effort-aware `single_agent`;
- provider text that lacks current protected META authority or the canonical `single_agent` and `parallel_when_beneficial` vocabulary.

META regression tests prove both stale and accepted provider text. After META becomes canonical, each provider updates only its root execution-routing section while preserving stricter provider-local safety/testing rules.

Platform currently has active PR #1270 writing root `AGENTS.md`; this rollout must not create a concurrent second writer for that path. Platform convergence is reconciled through the existing branch/PR or a formally superseding path only after preserving its unrelated anti-loop work.

## Validation

META requires RED/GREEN evidence for call binding and provider adoption, all existing routing regressions, full `meta-gate`, exact changed-file/diff review and required AI review according to the live risk classifier. Provider adoption requires repository-native exact-head CI/review gates and changed-file/diff review.

No host, deployment, production, secret, ruleset or branch-protection mutation is part of this change.