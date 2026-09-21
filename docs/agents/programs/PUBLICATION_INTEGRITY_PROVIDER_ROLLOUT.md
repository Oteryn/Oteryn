# Publication Integrity Provider Rollout

Status: PREPARED / NOT ACTIVE until PR #213 is integrated to protected META `main`.

Governing META Issue: #212.

## Activation gate

No provider mutation is authorized by this document. Activation requires all of:

1. PR #213 integrated through the governed META Merge Queue path;
2. successful real `merge_group` `meta-gate` for that integration candidate;
3. protected META `main` readback proving the publication-integrity contract is present;
4. the exact protected META commit selected as the new provider `authority_commit`;
5. a separately authorized provider task/branch/PR for each repository.

## Rollout order

Adopt in `Oteryn/Oteryn-Game` first because #356 supplied the motivating failure evidence. After Game adoption is verified, adopt the same protected META authority in Platform and Atlas through their own repository governance.

Each provider adoption must:

- update `docs/agents/META_AGENT_POLICY_BINDING.json` to the exact protected META authority commit while preserving the central policy identity/version contract;
- re-read the provider bootstrap and remove or narrow any publication wording that conflicts with the new central contract, without duplicating the full META procedure;
- verify the provider's policy-consumption validator against the exact bound META revision;
- execute representative behavior checks proving both boundaries: a prepared local candidate is preserved/reported blocked when neither guarded Git nor an authorized atomic expected-head API candidate-creation primitive is available, while an API-native route is accepted only as a new candidate when one server-side mutation fences the exact expected branch head and creates one complete successor commit; ancestry-only `force=false` ref updates, raw Git Data object/ref assembly and sequential per-file API writes remain rejected;
- preserve repository-specific Merge Queue, review, CI and production boundaries.

## Task-branch protection follow-up

Non-fast-forward protection for canonical agent/task branches is a defense-in-depth follow-up, not a substitute for publication integrity. Before adding a branch ruleset, verify the provider's branch naming and terminal deletion lifecycle so protection does not silently break legitimate merge-up or source-branch cleanup. Any ruleset mutation requires separate repository-administration authority, desired-state representation, deterministic verification and live readback.

Do not add required linear history to active task branches merely to prevent this incident family: authorized normal merge-up commits may be two-parent commits. Do not add heavyweight required CI to every intermediate task-branch push solely for publication integrity.

## Completion

Organization rollout is complete only when Game, Platform and Atlas each bind the protected META revision and their representative behavior/validator checks pass. A merged META contract alone is not provider adoption.
