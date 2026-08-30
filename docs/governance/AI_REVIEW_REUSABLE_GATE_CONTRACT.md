# Reusable AI Review Gate Caller Contract

Status: provider-consumption contract for the META trusted AI review gate.

The reusable action `.github/actions/ai-review-gate/action.yml` consumes GitHub server state only through a caller-supplied token. A provider wrapper that calls this action MUST grant exactly the minimum read scopes required by the trusted consumer:

- `contents: read`
- `actions: read`
- `checks: read`
- `issues: read`
- `pull-requests: read`

A provider wrapper MUST NOT broaden those scopes merely to consume the gate. In particular, the reusable consumer does not require `contents: write`, `actions: write`, `checks: write`, `issues: write`, `pull-requests: write`, `statuses: write`, repository secrets, or an OIDC token.

The protected META issuer workflow is a separate authority boundary. It may additionally receive the narrowly scoped `id-token: write`, `attestations: write`, and `artifact-metadata: write` permissions needed to attest and publish its own verified evidence. Those issuer-only permissions are not inherited by provider wrappers and must not be copied into candidate/test jobs.

Before Game, Platform, or Atlas consumes the META action, provider integration must prove that its wrapper permissions satisfy this exact minimum contract. Missing any required read scope fails closed; unnecessary write authority is a contract violation.
