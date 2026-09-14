# OTERYN CI + Merge Queue Canary V2 — META Ready hold

Governing META Issue: #200.
Cross-repository programme: Oteryn/Oteryn-Platform#1399.

This file is an inert documentation-only marker for the Ready-without-integration-authorization control.

Baseline protected `main`: `dcb71a131293128bf0a69959d78ae6390a0341fd`.

Expected behavior:

- the PR is opened Ready (non-Draft) from the start;
- ordinary exact-head qualification may run;
- no integration authorization is granted for this candidate during the hold;
- no Merge Queue enqueue, `merge_group`, merge, merge-up, rebase, no-op/retrigger commit, or protected-main integration should occur.

Any integration activity before a later explicit exact-head authorization is a V2 failure signal.

This marker changes no workflow, runtime, dependency, runner, protection, ruleset, secret, environment, deployment or production behavior.
