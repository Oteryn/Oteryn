# OTERYN CI + Merge Queue Canary V2 — META R0

Governing META Issue: #200.
Cross-repository programme: Oteryn/Oteryn-Platform#1399.

This file is an inert documentation-only canary marker for the META R0 routing and authorization-hold experiment.

Baseline protected `main`: `23b21e9b1b2d4b6c3a5cac3d4c7a18747804c090`.

Expected first-stage behavior:

- normal pull-request qualification may run according to the current META workflow contract;
- required `meta-gate` must qualify the exact PR head;
- the source head must remain unchanged unless this file is materially edited;
- while integration authorization is deliberately withheld, no Merge Queue enqueue, `merge_group`, merge, merge-up, rebase, no-op/retrigger commit or protected-main integration is expected.

Any unexpected integration activity during the authorization hold is a V2 failure signal.

This marker changes no workflow, runtime, dependency, runner, protection, ruleset, secret, environment, deployment or production behavior.
