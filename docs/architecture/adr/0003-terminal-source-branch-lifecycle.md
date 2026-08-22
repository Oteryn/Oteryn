# ADR 0003: Organization terminal source-branch lifecycle

- Status: Accepted
- Date: 2026-08-22
- Decision owner: Oteryn repository owner
- Tracks: Oteryn/Oteryn#48

## Context

All active Oteryn repositories already delete ordinary merged pull-request source branches. That does not cover branches whose pull requests are intentionally closed without merge, including superseded, diagnostic, abandoned, or restacked work. Oteryn-Platform already has a stricter repository-local terminal branch lifecycle implementation, but the other providers do not share an equivalent close-event control.

Leaving those refs indefinitely makes branch inventory an unreliable signal of active work. Deleting them by age or naming convention is unsafe because a closed-unmerged branch may still contain unique or deliberately retained work.

## Decision

Oteryn adopts one organization-level terminal source-branch contract with repository-local execution.

For a same-repository pull request that is merged, the repository continues to rely on `delete_branch_on_merge=true` and normal protected-main merge gates.

For a same-repository pull request intentionally closed without merge, the pull request body may authorize one terminal disposition using exactly one of:

- `Branch-Disposition: delete`
- `Branch-Disposition: retain`

and exactly one non-empty `Branch-Disposition-Reason: ...` line.

`delete` is destructive authority only for that exact closed pull request head. The trusted cleanup implementation must revalidate immediately before deletion that:

1. the event and live repository identities match the caller repository;
2. the pull request remains closed, unmerged, same-repository, on the same source branch and exact head SHA;
3. the source ref still resolves to that exact SHA;
4. the source branch is neither the default branch nor protected;
5. no open pull request owns the same ref;
6. release, rollback, recovery, and backup-sensitive names are excluded;
7. the remote used for deletion resolves to the caller repository;
8. deletion uses an exact-SHA Git lease and the ref is verified absent afterwards.

`retain` is non-destructive and records the reason in cleanup evidence. Missing disposition metadata performs no destructive action. Malformed or conflicting disposition metadata fails closed.

The reusable implementation is owned by `Oteryn/Oteryn`. Product repositories consume it only from an immutable commit SHA. Each product executes it in its own trusted `pull_request_target: closed` workflow with that repository's own `GITHUB_TOKEN`; no organization-wide personal access token or cross-repository write token is introduced. The workflow checks out trusted `main` rather than pull-request code before invoking the action.

`Oteryn/Oteryn-Platform` retains its existing terminal lifecycle implementation as a compatible stricter superset. The archived migration-backup repository is excluded from automatic rollout.

Historical or no-PR orphan refs are not deleted by this event mechanism. They require separate reviewed reconciliation with exact current-ref evidence. Active/open PR branches are never historical cleanup candidates.

## Consequences

- Closed-unmerged task branches can be removed deterministically without merging obsolete work into `main`.
- A compromised product workflow token cannot delete branches in another Oteryn repository.
- A central action update is reviewable once and provider adoption is pinned to an exact merged revision.
- Missing or ambiguous historical evidence remains fail-closed and may require manual reconciliation.
- Branch cleanup becomes an explicit lifecycle outcome instead of an age- or prefix-based heuristic.
