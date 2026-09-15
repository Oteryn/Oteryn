# Restricted publishing-credential compatibility

Load this procedure when an already-authorized GitHub publication needs CLI/Git credential compatibility. Ordinary API-backed documentation work that is not publishing an existing material local candidate does not require it.

This profile applies only after the repository lifecycle has allocated an approved task branch and existing PR. It does not grant PR-write permission to a restricted publishing credential; PR creation remains a separately authorized control-plane action.

## Existing local candidate publication

Once a material local candidate commit exists and is the intended payload for an allocated task branch, publication MUST preserve that exact candidate commit. The normal route is a fast-forward Git publication of that commit to exactly one approved configured push target after verifying the live head at that push endpoint is the expected predecessor and that the expected predecessor is an ancestor of the candidate on the unmodified Git object graph. A separately authorized normal merge-up is compatible with this rule because it produces the candidate before publication; publication itself must not rewrite that candidate.

Use `tools/governance/publication_integrity.py` when an isolated Git workspace is available. It requires the selected remote to resolve to exactly one credential-free configured push URL matching the approved target; rejects an endpoint that is itself another configured remote name; rejects effective `url.*.insteadOf` / `url.*.pushInsteadOf` rules; resolves the effective `filter` attribute for tracked paths and rejects active filter drivers with executable `clean` / `process` configuration; rejects replacement refs, graft metadata and replacement-ref namespace overrides; rejects tracked `skip-worktree` / `assume-unchanged` flags; and requires tracked gitlink worktrees to be deinitialized/empty before the clean probe. The top-level clean check ignores submodule contents, disables optional index writes/fsmonitor and binds `core.hooksPath` to a fresh trusted empty directory so repository-controlled filters, submodule-local filters, fsmonitor or index hooks cannot side-publish.

Before mutation the helper creates and verifies a recoverable Git bundle outside the disposable worktree. It performs one exact-candidate branch update guarded by an expected-old-value lease, bypasses `pre-push` hooks, explicitly disables recursive submodule publication and automatic follow-tags, and reads the branch back through the same push endpoint before reporting success.

A separate fetch URL is not publication evidence, multiple push URLs fail closed before mutation, Git URL rewrites are publication blockers until removed from the effective configuration, active executable clean/process filters are publication blockers while assigned to tracked paths, replacement/graft history cannot authorize ancestry, hidden index flags cannot suppress local recovery state, and an initialized submodule worktree must be handled separately rather than implicitly traversed by the superproject publisher. Unused global filter configuration does not block publication merely because it exists.

The helper's explicit `--force-with-lease=<ref>:<expected_sha>` is used only as compare-and-swap protection for the expected predecessor. Candidate ancestry is checked independently first with replacement objects disabled, so this does not authorize a non-fast-forward update or history rewrite. `--recurse-submodules=no` ensures `push.recurseSubmodules` cannot widen the operation to another repository, and `--no-follow-tags` ensures `push.followTags=true` cannot add tag refs. An agent must not weaken these command-line fences or treat the lease as a general force-push exception.

If the normal Git publication path is unavailable, do **not** reconstruct an already-prepared material candidate through ad-hoc Git Data blob/tree/commit/ref calls, per-file Contents API writes, a replacement commit, reset, rebase, non-fast-forward push, or ref rewrite. This is a publication-integrity boundary, not a global ban on repository-native API writes for other authorized operations.

## Ambiguous publication outcome

A failed, interrupted, timed-out, or otherwise ambiguous push is not evidence that GitHub rejected the candidate. Read the live canonical branch through the same approved push endpoint before any retry or recovery action:

- if the remote head equals the exact candidate, publication succeeded despite the ambiguous transport result;
- if the remote head still equals the expected predecessor, retain the candidate and recovery artifact and report the exact publication capability failure;
- if the remote head is any third SHA, stop with remote-head drift and reconcile ownership/state before another mutation.

Do not retry an ambiguous push until that readback has classified the remote state. Never use a force update as automatic cleanup.

## Recovery preservation

Before releasing or disposing of a writer/workspace that contains a material unpublished candidate, preserve a recovery artifact containing the exact Git objects required to recover that candidate. A Git bundle is preferred when Git is available. The artifact is evidence only after verification proves that it advertises the exact candidate head and records any prerequisite commit required for incremental recovery. A patch, prose summary, test log, or remembered edit is not an exact-candidate recovery substitute. Local submodule work is separate repository work and must not be assumed to be preserved by the superproject bundle.

Recovery preservation does not make local-only work delivered. The approved GitHub branch/PR remains lifecycle authority, and exact-head CI/review starts only after the intended candidate is durably present there.

## Credential compatibility

For an authorized write to that branch/PR, when `GH_TOKEN` and `GITHUB_TOKEN` are unset but agent-visible `GH` is present, it may be passed transiently as `GH_TOKEN="$GH"` to the exact authorized `gh` command. Environment mapping alone does not authenticate `git push`: verify that the existing remote/credential path can consume the authorized identity without exposing or persisting it. If the normal Git publication path is still unavailable, preserve the candidate/recovery artifact and report the exact limitation rather than inventing a lower-level publication route.

Never embed the token in a remote URL or persist a new credential helper to bypass that boundary. Credential presence expands no repository/path/task/merge/production permission. Do not perform a non-fast-forward update; verify the remote exact head after publishing.
