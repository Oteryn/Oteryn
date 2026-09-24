# Publication Integrity Provider Rollout

Status: ACTIVE CONTRACT; this revision requires protected META integration and exact provider rebinding before provider use.

Governing META Issue: #212.

## Activation gate

No provider mutation is authorized by this document alone. A new publication-policy revision becomes active for a provider only after all of:

1. the revision is integrated through the governed META Merge Queue path;
2. the real `merge_group` `meta-gate` succeeds for that integration candidate;
3. protected META `main` readback proves the revision is present;
4. that exact protected META commit is selected as the provider's new `authority_commit`;
5. a separately authorized provider task/branch/PR performs and validates the rebind.

## Rollout order

Adopt in `Oteryn/Oteryn-Game` first because #356 supplied the motivating failure evidence. After Game adoption is verified, adopt the same protected META authority in Platform and Atlas through their own repository governance.

Each provider adoption must:

- update `docs/agents/META_AGENT_POLICY_BINDING.json` to the exact protected META authority commit while preserving the central policy identity/version contract;
- re-read the provider bootstrap and remove or narrow any publication wording that conflicts with the new central contract, without duplicating the full META procedure;
- verify the provider's policy-consumption validator against the exact bound META revision;
- execute representative behavior checks proving all publication boundaries: guarded local Git preserves exact candidate identity; preferred API-native publication accepts an atomic expected-head one-commit mutation; connector-compatible publication accepts exactly one new Git Data candidate commit plus one non-force (`force=false`) task-branch update only with fresh single-writer allocation and immediate predecessor/candidate live readbacks; protected/shared/uncertain branches, pre-readback drift, third-SHA outcomes, sequential per-file API writes, multiple candidate commits and force/ref replacement remain rejected;
- preserve repository-specific Merge Queue, review, CI and production boundaries.

## Task-branch protection follow-up

Non-fast-forward protection for canonical agent/task branches is a defense-in-depth follow-up, not a substitute for publication integrity. Before adding a branch ruleset, verify the provider's branch naming and terminal deletion lifecycle so protection does not silently break legitimate merge-up or source-branch cleanup. Any ruleset mutation requires separate repository-administration authority, desired-state representation, deterministic verification and live readback.

Do not add required linear history to active task branches merely to prevent this incident family: authorized normal merge-up commits may be two-parent commits. Do not add heavyweight required CI to every intermediate task-branch push solely for publication integrity.

## Completion

Organization rollout is complete only when Game, Platform and Atlas each bind the protected META revision and their representative behavior/validator checks pass. A merged META contract alone is not provider adoption.
