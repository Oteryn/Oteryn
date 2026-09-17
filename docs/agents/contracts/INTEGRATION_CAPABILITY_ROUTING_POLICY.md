# Integration Capability Routing Policy

Status: active after protected integration of the governing META change.

## Purpose

Prevent a protected-integration task from reaching the end of implementation and
only then discovering that the active session cannot invoke the organization
Merge Queue primitive. Execution capability and integration authority are
different facts and MUST remain separate.

This contract is subordinate to `docs/agents/policy/ORGANIZATION_AGENT_POLICY.md`.
It does not grant merge authority and does not replace repository protection,
required checks, Merge Queue, review policy, or provider ownership.

## Machine authority

`ecosystem/agent-execution-routing-policy.json` owns the closed machine-readable
capability route. `tools/governance/integration_capability_routing.py` validates
typed current-session evidence and deterministically classifies it.

For a substantial mutating task that is expected to require autonomous protected
integration, capability preflight is required **before releasing the worker**.
Do not wait until `READY_FOR_COORDINATOR_INTEGRATION`.

The worker-release authority function accepts typed `AcquiredCapabilityEvidence`
assembled from current-session tool/action discovery and live protected-executor
readback. A dedicated `TrustedCapabilityObserver` or sealed observation wrapper is
not required. A `Mapping`, JSON document, operation string, timestamp, label,
boolean, task/prompt assertion, comment, serialized fixture or previous-session
assertion is not capability evidence and is not accepted by the classifier as a
substitute. Missing, malformed, stale or incomplete typed evidence classifies as
`BLOCKED_CAPABILITY_UNAVAILABLE`.

This typed-evidence boundary is intentionally a scheduling/correctness boundary,
not a cryptographic attestation boundary. It does not claim to prove how arbitrary
same-process Python code obtained each field. The active coordinator remains
responsible for assembling the typed value from the current session's live reads,
and the protected executor independently revalidates all mutation-sensitive facts
before any queue mutation. Capability classification still does not grant merge
authority.

The authoritative classification API returns a sealed capability decision. For a
delegated route that decision retains the exact canary-qualified protected-META
`main` SHA from the typed evidence, and canonical control-request construction
must consume that retained binding. A caller-provided current-main SHA cannot
replace it. The enum-only compatibility view is diagnostic and is not sufficient
to construct a delegated request. Direct capability has no delegated canary
binding and remains independent of this rule.

Every capable evidence value carries an observation timestamp and is valid only
for the finite freshness interval in the machine policy. Future, stale or malformed
evidence fails closed. `DELEGATED_CAPABLE` additionally requires a fresh
protected-META `refs/heads/main` readback bound to the canonical executor workflow
path and exact blob, the exact current protected-main commit SHA,
credential-operational proof and retained terminal canary evidence bound to that
same protected-main SHA. Any protected-main movement invalidates the retained
canary even when the workflow YAML blob itself is unchanged.

The current-session discovery evidence also carries the actual human actor identity
used by its control-comment operation, and the protected-executor readback carries
the human principal identity of the fine-grained mutation credential. Delegated
capability requires both identities to be present, well formed and equal. A
caller-supplied actor string without the corresponding live discovery/readback is
not sufficient evidence. This check is independent of the direct-native route and
cannot block an otherwise verified direct capability.

Raw serialized snapshots may be retained as diagnostics or test fixtures, but are
never accepted by `validate_worker_release` or interpreted as scheduling authority.
The standalone CLI intentionally has no authoritative `--snapshot` path and fails
closed because no typed current-session capability evidence is supplied to it.

## States

The only states are:

- `NOT_REQUIRED` — this bounded task is not expected to require autonomous
  protected integration.
- `DIRECT_CAPABLE` — the current session exposes the selected native exact-head
  `merge-async` operation.
- `DELEGATED_CAPABLE` — the current session can create the bounded META control
  request and the protected META delegated executor has been independently
  verified operational.
- `BLOCKED_CAPABILITY_UNAVAILABLE` — neither positive route is currently proven.

For work that requires autonomous protected integration, only `DIRECT_CAPABLE`
or `DELEGATED_CAPABLE` permits release of a new mutating worker. This is a
scheduling gate, not merge authorization.

If a task is already in progress when capability becomes unavailable, preserve
valid work and the qualified candidate. Do not create no-op/retrigger commits
merely to change capability state.

## Direct route

`DIRECT_CAPABLE` means fresh current-session discovery evidence observed the
execution surface exposing the governed native operation selected by META:

`PUT /repos/{owner}/{repo}/pulls/{pull_number}/merge-async`

with the exact qualified `sha` and explicit `merge_action="merge_queue"`.

All target-bound authorization, eligibility, receipt/readback and terminal proof
requirements from the organization policy remain unchanged.

## Delegated route

`DELEGATED_CAPABLE` does **not** transfer coordinator, repository, architecture,
review or merge authority. The organization-owned executor
`meta.governed_merge_queue_executor.v1` is only a bounded actuator for one action
that the active coordinator is already authorized to request.

The control transport is META Issue #196. The request comment is not merge
authority and does not broaden the caller's authority. A coordinator may create
it only after the normal fresh repository/PR/`base=main`/exact-head
authorization and eligibility preflight required by the organization policy.

The command is exactly:

```text
/oteryn-mq-submit <allowed owner/repo> <pr-number> <exact-40-lowercase-hex-head> <canary-qualified-protected-META-main-SHA>
```

The protected executor re-fetches this same comment from Issue #196 immediately
before target qualification and requires the closed command grammar and exact
agreement with the workflow-bound repository/PR/head. The authenticated
issue-comment event's OWNER/MEMBER association is ingress evidence only, not
current membership authority. This live re-read protects transport integrity;
it is not a second authorization proof or attestation system.
The final SHA is the exact protected META `main` commit bound to the retained
canary proof; it is not inferred from the workflow event's `github.sha`.

## Executor invariants

The protected META executor:

- accepts only the four permanent Oteryn repositories and their immutable
  source-workflow identities in the organization routing policy;
- admits only the first GitHub Actions run attempt for an Issue-comment event;
  workflow reruns are reconciliation-only and cannot replay the queue mutation;
- requires target PR `open`, unmerged, non-Draft, `base=main`, same-repository
  head, exact requested SHA;
- binds source qualification to exact repository, workflow path, event, stable
  workflow ID, PR head branch and SHA, plus target PR relation whenever GitHub
  supplies a non-empty relation. META, Game and Platform also bind the named gate
  check suite to that run. Atlas requires both canonical `pull_request_target`
  source workflows, queries them without a PR-head-SHA filter because those runs
  report the base SHA, and requires each run's non-empty PR relation to contain
  the exact target PR. Terminal `atlas-gate` remains merge-group proof;
- authenticates the fine-grained PAT human principal, requires it to equal the
  control-comment actor, revalidates that principal's current active `Oteryn`
  organization membership, and requires current target `admin` or `maintain`;
- immediately before mutation, re-reads comment, PR, eligibility and workflow
  evidence and consumes the canonical authorization/freeze/attempt route objects;
- immediately before mutation, live-reads `Oteryn/Oteryn` protected `main` and
  requires it still to equal the canary-qualified SHA carried by the request;
- performs only native `merge-async` with exact `sha` and
  `merge_action="merge_queue"`;
- treats HTTP 202 as acceptance only, creates the UUID-bound receipt immediately,
  and durably emits its non-secret machine record to stdout and
  `GITHUB_STEP_SUMMARY` before any fallible metadata validation or readback;
- requires a strictly later UUID-bound status/target readback; readback failure
  preserves the accepted receipt and requires UUID reconciliation without a
  repeated PUT, while persistence failure is a UUID-bearing
  `RECONCILIATION_REQUIRED` blocker;
- treats HTTP 200/409 as reconciliation, never a fabricated new acceptance;
- treats denied/unavailable native mutation as
  `BLOCKED_CAPABILITY_UNAVAILABLE`;
- never performs direct merge, generic auto-merge, GraphQL enqueue, bypass,
  force, protection changes, default merge action, no-op/retrigger commits or
  ambiguous automated dequeue.

The executor intentionally stops after accepted request/readback. The owning
coordinator remains responsible for real `merge_group` aggregate success and
protected-main readback before any task archive, lease release or completion
claim.

## Credential boundary

The workflow's built-in repository token stays read-only and is never the queue
mutation credential. The mutation route uses only the separately provisioned
fine-grained credential permitted by the bound organization policy.

Credential provisioning and secret values are outside this repository change.
Until the workflow is on protected META `main`, the fine-grained credential is
provisioned, and a real bounded canary proves the route for the exact current
protected-main SHA, current-session evidence MUST NOT report
`meta.governed_merge_queue_executor.v1` as operational.

Do not create a custom GitHub App merely for this executor and do not recreate
provider-local Merge Queue bridges.

## Provider adoption

After this contract is protected-integrated, a provider adopts it only through
its normal immutable META repin and local delivery reconciliation. Do not
silently treat a moving META branch as provider authority.

Provider workers do not need Merge Queue mutation capability themselves. The
preflight requirement belongs to the active scheduling/integration control
plane that releases work expected to need autonomous protected integration.
