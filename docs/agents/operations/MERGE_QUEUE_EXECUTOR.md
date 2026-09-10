# Governed Merge Queue Executor

Governing design: `docs/agents/contracts/INTEGRATION_CAPABILITY_ROUTING_POLICY.md`
Control surface: `Oteryn/Oteryn#196`
Implementation: `tools/governance/governed_merge_queue_executor.py`
Workflow: `.github/workflows/governed-merge-queue-executor.yml`

## Purpose

Provide one organization-owned bounded actuator for the already-selected META
native exact-head Merge Queue route when the active coordinator can create
repository comments but does not itself expose native `merge-async`.

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

## Authorization record

The owning provider coordinator first records exact integration authorization
on the target PR:

```text
OTERYN_MQ_AUTHORIZATION_V1
repository: Oteryn/Oteryn-Game
pull_request: 528
base: main
head_sha: 97fcf72a2f29a8fc134c97dd3cdaf9237be7c6d3
integration_authorized: true
```

That comment must be created only after the coordinator's normal fresh
repository/PR/head/review/check/eligibility preflight. Its numeric comment ID is
then passed to the control request.

## Control request

Post exactly one comment to META Issue #196:

```text
/oteryn-mq-submit Oteryn/Oteryn-Game 528 97fcf72a2f29a8fc134c97dd3cdaf9237be7c6d3 <authorization-comment-id>
```

The protected default-branch workflow parses this command with a closed regex.
Anything else is ignored. OWNER/MEMBER/COLLABORATOR association is required on
the control comment.

The executor independently re-reads and validates the target authorization
comment, target PR and exact-head required gate immediately before mutation.
Changing any bound coordinate makes the request fail closed.

## Native mutation

The only positive mutation is:

```text
PUT /repos/{owner}/{repo}/pulls/{pull_number}/merge-async
sha=<exact qualified head>
merge_action=merge_queue
```

HTTP 202 produces a non-terminal receipt. The executor binds the returned
server UUID to sequence 1, performs UUID-addressed status readback and fresh
target identity readback, and requires a strictly later executor sequence.

HTTP 200/409 is reconciliation only. HTTP 400/422 is rejection. HTTP 403/404 is
a precise native capability/credential blocker. There is no direct merge,
generic auto-merge, GraphQL enqueue, default merge action, automated dequeue,
force, protection change, or no-op/retrigger fallback.

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

If the credential is absent/denied, the executor is not operational. Continue
safe path-disjoint work; do not weaken protections or resurrect the retired
provider-local custom-App bridge.
