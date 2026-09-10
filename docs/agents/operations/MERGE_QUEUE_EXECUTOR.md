# Governed Merge Queue Executor

Governing design: `docs/agents/contracts/INTEGRATION_CAPABILITY_ROUTING_POLICY.md`
Control surface: `Oteryn/Oteryn#196`
Implementation: `tools/governance/governed_merge_queue_executor.py`
Workflow: `.github/workflows/governed-merge-queue-executor.yml`

## Purpose

Provide one organization-owned bounded actuator for the already-selected META
native exact-head Merge Queue route when the active coordinator can create a
repository comment but does not itself expose native `merge-async`.

This executor is execution capability only. It is not a second coordinator,
review authority, architecture authority, protection bypass, or independent
permission to merge.

## Operational prerequisite

The route is not `DELEGATED_CAPABLE` merely because these files exist.

Before `meta.governed_merge_queue_executor.v1` may be advertised as operational:

1. this workflow/executor must be integrated to protected META `main`;
2. repository secret `OTERYN_MQ_FINE_GRAINED_PAT` must be provisioned with a
   fine-grained token scoped only to the required permanent repository set and
   the minimum permissions required by the native `merge-async` route;
3. no token value may be committed, printed, copied into an Issue/PR/comment, or
   exposed to provider code;
4. one real bounded canary must prove 202 UUID capture, strictly-later
   UUID-addressed readback, the normal provider `merge_group` aggregate gate and
   protected-main readback;
5. any denied credential/endpoint result keeps the delegated route
   `BLOCKED_CAPABILITY_UNAVAILABLE`.

The workflow's normal repository permissions are read-only. It never uses the
built-in workflow token as the queue mutation credential.

The mutation credential authenticates a human principal. The executor requires
that principal to equal the live control-comment actor and to have current
`admin` or `maintain` permission in the target repository. META organization
membership alone is transport eligibility, never cross-repository authority.

## Control request

The active provider coordinator must first perform the normal fresh
repository/PR/base/head/authorization/eligibility preflight required by META
policy. If the exact candidate remains authorized, post exactly one comment to
META Issue #196:

```text
/oteryn-mq-submit Oteryn/Oteryn-Game 528 97fcf72a2f29a8fc134c97dd3cdaf9237be7c6d3
```

The request does not grant authority. It is only the transport used by a
coordinator that already has authority for that exact integration decision.

The protected default-branch workflow accepts only the closed grammar above and
OWNER/MEMBER META actor association. The executor re-fetches the same comment
live and verifies that it is still on Issue #196 and still binds the same
repository, PR and exact head before it reads the target PR.

Immediately before the PUT it repeats that read and all target/source-workflow
qualification. Workflow proof binds exact repository, path, event, stable ID,
PR head branch/SHA and any non-empty PR relation. Atlas's two canonical
`pull_request_target` workflows may have empty relations; both identities must
still pass, and terminal `atlas-gate` is not source qualification.

## Native mutation

The executor independently requires target PR `open`, unmerged, non-Draft,
`base=main`, same-repository head, exact requested SHA and the immutable canonical
source-workflow evidence in `completed/success`.

The only positive mutation is:

```text
PUT /repos/{owner}/{repo}/pulls/{pull_number}/merge-async
sha=<exact qualified head>
merge_action=merge_queue
```

HTTP 202 produces a non-terminal receipt. The executor binds the returned server
UUID to sequence 1 and, before any fallible status or target readback, flushes a
machine-readable non-secret `REQUEST_ACCEPTED_NON_TERMINAL` record to stdout and
durably appends it to `GITHUB_STEP_SUMMARY`. The record carries the request comment
ID, repository, PR, base, exact head, merge action, UUID and receipt sequence. Only
then does it perform UUID-addressed status readback and fresh target identity
readback, requiring a strictly later executor sequence.

HTTP 200/409 is reconciliation only. HTTP 400/422 is rejection. HTTP 403/404 is a
precise native capability/credential blocker. There is no direct merge, generic
auto-merge, GraphQL enqueue, default merge action, automated dequeue, force,
protection change, or no-op/retrigger fallback.

## Terminal proof

Successful workflow execution does not mean the PR is integrated. The owning
provider coordinator must still prove:

- real `merge_group` run for the accepted queue candidate;
- canonical aggregate provider gate success;
- target PR merged state;
- protected provider `main` readback containing the accepted candidate.

Only then may normal task/lease/Issue closeout proceed.

## Failure handling

Do not repeat an identical request when an async UUID already exists or a
previous request is awaiting reconciliation. Preserve the candidate and inspect
the exact workflow result.

A failure after HTTP 202 does not invalidate or erase the accepted receipt. The
operator/coordinator must recover the persisted UUID, reconcile that exact async
request and must not repeat the PUT. If receipt persistence itself fails, the
executor stops with a UUID-bearing `RECONCILIATION_REQUIRED` blocker and never
issues another PUT as fallback.

If the credential is absent/denied, the executor is not operational. Continue
safe path-disjoint work; do not weaken protections or resurrect a provider-local
custom-App bridge.
