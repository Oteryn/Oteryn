# Publication Integrity Policy

Status: active contract after reviewed integration to protected META `main` and explicit provider adoption.

## Purpose

This contract governs publication of an already-prepared material local Git candidate to its allocated canonical task branch. It prevents a transport or credential failure from silently changing the candidate, rewriting branch history, or destroying the only recoverable copy of useful work.

It is not a merge authority, does not replace repository CI/review/Merge Queue, and does not globally forbid repository-native API writes for operations that are not publishing an existing material local candidate.

## Exact-candidate invariant

Once a material local commit is selected as the publication candidate, publication must preserve that exact commit identity. The publication operation must not reconstruct the candidate from files, patches, prose, test output, or manually assembled Git objects.

Before mutation, bind and verify:

- repository and approved remote;
- canonical task branch;
- exact candidate commit SHA;
- exact expected current remote branch SHA;
- checked-out local branch/head when a local Git workspace is used;
- the expected remote SHA is an ancestor of the candidate, so the update is non-force.

A separately authorized normal merge-up may create a new candidate before this freeze. It does not authorize rewriting the frozen candidate during publication.

## Recovery preservation

Before the first publication attempt, create a verified recovery artifact for a material unpublished candidate when the execution environment can be disposed, lost, or handed off. The artifact must preserve the exact Git objects needed to recover the candidate and must advertise that exact candidate head. Record its digest and any prerequisite commit required for incremental recovery.

`git bundle` is the preferred Git-native representation. A bundle stored only inside the disposable worktree is insufficient. The caller/executor remains responsible for placing the verified artifact on an authorized durable surface before it treats workspace disposal or custody release as safe.

A patch, prose summary, file list, diff excerpt, or test log is evidence but is not an exact-candidate recovery substitute.

## Publication route

For a local Git candidate, the selected route is one ordinary non-force Git push of the exact candidate to the canonical task branch, followed by live remote-head readback. `tools/governance/publication_integrity.py` implements the deterministic local guard and transport wrapper when a Git workspace is available.

If the normal Git publication path is unavailable, do not use ad-hoc Git Data API blob/tree/commit/ref construction, per-file Contents API reconstruction, reset, rebase, force-push, or manual ref replacement to synthesize a remote substitute for the existing candidate. Preserve the candidate/recovery artifact and classify the lane as blocked by the exact observed publication capability failure.

This restriction is candidate-specific. It does not prohibit an independently authorized API-native edit whose intended operation is itself the API write and which is not pretending to publish an already-prepared local commit.

## Ambiguous outcomes

A nonzero push exit, timeout, interrupted client, or lost response is an ambiguous transport result, not proof that the server rejected the mutation. Before retrying or attempting recovery, read the live canonical branch:

- remote head equals candidate: publication succeeded; continue from that exact remote candidate;
- remote head equals expected predecessor: publication was not applied; retain recovery and diagnose the exact capability failure before another attempt;
- remote head is a third SHA: stop with remote-head drift and reconcile writer/ownership/live state before mutation;
- remote head cannot be read: remain blocked with an ambiguous outcome; do not retry or rewrite the ref blindly.

No automatic force update, rollback, no-op commit, replacement commit, or destructive cleanup is permitted as ambiguity recovery.

## Completion boundary

A verified recovery artifact protects work from loss but does not make local work delivered. Repository lifecycle evidence begins only when the intended exact candidate is durably present on the approved GitHub branch/PR. Readiness, review and integration continue to use the repository's existing exact-head gates and protected Merge Queue path.
