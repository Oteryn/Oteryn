# Publication Integrity Policy

Status: active contract after reviewed integration to protected META `main` and explicit provider adoption.

## Purpose

This contract governs publication of an already-prepared material local Git candidate to its allocated canonical task branch. It prevents a transport or credential failure from silently changing the candidate, rewriting branch history, publishing adjacent repositories/refs, or destroying the only recoverable copy of useful work.

It is not a merge authority, does not replace repository CI/review/Merge Queue, and does not globally forbid repository-native API writes for operations that are not publishing an existing material local candidate.

## Exact-candidate invariant

Once a material local commit is selected as the publication candidate, publication must preserve that exact commit identity. The publication operation must not reconstruct the candidate from files, patches, prose, test output, or manually assembled Git objects.

Before mutation, bind and verify:

- repository plus exactly one configured, credential-free approved push target;
- the approved push target is not also a configured Git remote name whose alias resolution could redirect the repository operand;
- no effective Git `url.*.insteadOf` or `url.*.pushInsteadOf` rewrite rule, so the approved endpoint cannot be redirected after validation;
- no executable `filter.<driver>.clean` or `filter.<driver>.process` configuration for a filter driver actually assigned by Git attributes to any tracked path in the publication workspace;
- no Git replacement refs, graft metadata, or replacement-ref namespace override; ancestry must be evaluated against the unmodified object graph;
- canonical task branch;
- exact candidate commit SHA;
- exact expected current remote branch SHA;
- checked-out local branch/head when a local Git workspace is used;
- all repository-wide safety scans are anchored at the actual top-level Git worktree even if the caller supplies a nested `--cwd`;
- no tracked `skip-worktree` or `assume-unchanged` index flags that could hide local bytes from the clean-worktree probe;
- tracked gitlinks must not have a populated/initialized submodule worktree in the publisher workspace;
- a clean isolated worktree, so the recovery artifact contains all intended work;
- the expected remote SHA is an ancestor of the candidate, so the update is fast-forward.

A separately authorized normal merge-up may create a new candidate before this freeze. It does not authorize rewriting the frozen candidate during publication.

## Recovery preservation

Before the first publication attempt, create a verified recovery artifact for a material unpublished candidate when the execution environment can be disposed, lost, or handed off. The artifact must preserve the exact Git objects needed to recover the candidate and must advertise that exact candidate head. Record its digest and any prerequisite commit required for incremental recovery.

`git bundle` is the preferred Git-native representation. A bundle stored only inside the disposable worktree is insufficient. The caller/executor remains responsible for placing the verified artifact on an authorized durable surface before it treats workspace disposal or custody release as safe.

A patch, prose summary, file list, diff excerpt, or test log is evidence but is not an exact-candidate recovery substitute. Submodule-local work is separate repository work and is never implicitly published or treated as part of the superproject recovery artifact.

## Publication route

For a local Git candidate, the selected route is a single Git ref update of the exact candidate to the canonical task branch followed by live remote-head readback. `tools/governance/publication_integrity.py` implements the deterministic local guard and transport wrapper when a Git workspace is available. The helper first resolves any supplied working directory to `git rev-parse --show-toplevel`; a nested invocation must therefore receive the same repository-wide filter/index/gitlink checks as an invocation from the repository root.

The selected remote must resolve to exactly one configured push URL and that URL must equal the approved publication target. Effective Git URL rewrite rules are rejected rather than reimplemented or partially interpreted. An endpoint string that is itself another configured remote name is rejected rather than left to Git's remote-name/URL ambiguity. Preflight readback, mutation and post-mutation readback all use the same resolved push endpoint; a distinct fetch URL is not publication evidence, multiple push URLs fail closed before mutation, and no `insteadOf`/`pushInsteadOf` chain may redirect the endpoint.

Candidate ancestry is checked with replacement objects disabled after replacement refs and graft metadata are rejected. The helper uses an explicit expected-old-value `--force-with-lease=<ref>:<expected_sha>` only as compare-and-swap protection against movement between preflight and mutation. It independently requires `expected_sha` to be an ancestor of the exact candidate before the push. Therefore the authorized update remains fast-forward; the lease does **not** authorize a non-fast-forward update, history rewrite, reset, rebase, or ordinary force-push.

The clean-worktree probe resolves the effective `filter` attribute for every tracked path without converting file contents. It rejects only filter drivers that are actually active on tracked paths and have an executable `clean` or `process` command; unrelated global filter configuration such as an unused Git LFS driver does not block publication. The probe rejects tracked `skip-worktree` and `assume-unchanged` index flags. It also requires tracked submodule worktrees to be deinitialized/empty, then runs top-level `git status` with `--ignore-submodules=all`, optional index locking disabled, `core.fsmonitor=false`, and `core.hooksPath` pointed at a fresh trusted empty directory. This prevents repository-controlled active filters, submodule-local filters, fsmonitor or index hooks from executing code or publishing elsewhere during the safety check.

The guarded push uses `--no-verify`, `--recurse-submodules=no`, `--no-follow-tags` and `--no-signed`. Therefore repository-local `pre-push` hooks cannot run, configured recursive-submodule publication cannot widen the operation to another repository, `push.followTags=true` cannot add tag refs, and `push.gpgSign` cannot invoke a repository-configured `gpg.program` or add signed-push side effects. The only intended ref update is the exact candidate to the canonical task branch guarded by the expected-old-value lease.

If the normal Git publication path is unavailable, do not use ad-hoc Git Data API blob/tree/commit/ref construction, per-file Contents API reconstruction, reset, rebase, non-fast-forward push, or manual ref replacement to synthesize a remote substitute for the existing candidate. Preserve the candidate/recovery artifact and classify the lane as blocked by the exact observed publication capability failure.

This restriction is candidate-specific. It does not prohibit an independently authorized API-native edit whose intended operation is itself the API write and which is not pretending to publish an already-prepared local commit.

## Ambiguous outcomes

A nonzero push exit, timeout, interrupted client, or lost response is an ambiguous transport result, not proof that the server rejected the mutation. Before retrying or attempting recovery, read the live canonical branch through the same approved push endpoint used for the mutation:

- remote head equals candidate: publication succeeded; continue from that exact remote candidate;
- remote head equals expected predecessor: publication was not applied; retain recovery and diagnose the exact capability failure before another attempt;
- remote head is a third SHA: stop with remote-head drift and reconcile writer/ownership/live state before mutation;
- remote head cannot be read: remain blocked with an ambiguous outcome; do not retry or rewrite the ref blindly.

No automatic force update, rollback, no-op commit, replacement commit, or destructive cleanup is permitted as ambiguity recovery.

## Completion boundary

A verified recovery artifact protects work from loss but does not make local work delivered. Repository lifecycle evidence begins only when the intended exact candidate is durably present on the approved GitHub branch/PR. Readiness, review and integration continue to use the repository's existing exact-head gates and protected Merge Queue path.
