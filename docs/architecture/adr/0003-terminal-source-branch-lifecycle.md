# ADR 0003: Repository-local terminal source-branch lifecycle

- Status: Accepted
- Date: 2026-08-23
- Decision owner: repository owner
- Lifecycle issue: #51
- Organization implementation: `Oteryn/Oteryn-Platform@e145f7c03bd0b15f0b0fecc0f6fae7884fe3e0db`

## Context

GitHub's `delete_branch_on_merge` covers accepted same-repository pull requests, but it does not close the lifecycle of deliberately closed-unmerged, superseded, diagnostic, or historically orphaned branches. Oteryn Platform already implements the exact-head, fail-closed Terminal Branch Lifecycle and exposes it as reusable workflows.

## Decision

META adopts that lifecycle through a thin repository-local workflow pinned to the exact merged Platform SHA above. Live inventory and deletion use only this repository's `GITHUB_TOKEN`; no organization-wide destructive credential is introduced.

Read-only inventory uses the physically separate Platform read reusable workflow. Write-capable close/apply operations use the separate write reusable workflow. A same-repository pull request intentionally closed without merge must state exactly one `Branch-Disposition: delete` or `Branch-Disposition: retain` plus a non-empty `Branch-Disposition-Reason`. `delete` is only authorization to attempt cleanup: trusted-main automation must still prove exact branch/head/PR identity, absence of an open PR or active claim, protection and retention safety, and reserved-name safety at deletion time.

Merged PR branches remain handled by `delete_branch_on_merge=true`. Scheduled/manual inventory is read-only. Historical orphan cleanup requires a separately reviewed manifest/approval bound to the exact live candidate set; adoption does not automatically delete pre-existing ambiguous refs.

## Shared policy compatibility

`docs/agents/BRANCH_LIFECYCLE_POLICY.json` intentionally preserves the shared Platform classifier schema, including its schema compatibility marker `issue: 658`. That field is not META lifecycle authority; META adoption lifecycle authority is Issue #51 and this ADR.

## Consequences

Branch accumulation becomes a visible closeout defect rather than normal repository state, while ambiguous, protected, recovery-sensitive, active, or retained refs remain fail-closed. Upgrading the implementation requires a normal PR that changes both reusable workflow references and all `platform_ref` values to the same reviewed merged Platform SHA.
