# Central Merge Queue Broker

Use this route only when a target PR is already integration-authorized and the active client cannot itself issue the governed native `PUT .../merge-async` operation.

The broker does not replace Merge Queue and does not add another merge primitive. It only transports an exact target to the same native operation with `sha=<exact-qualified-head>` and `merge_action="merge_queue"`.

## Invocation

Post exactly this single-line comment to `Oteryn/Oteryn#187`:

`/oteryn-mq-enqueue <repository> <pr-number> <exact-head-sha>`

Allowed repositories are `Oteryn/Oteryn`, `Oteryn/Oteryn-Game`, `Oteryn/Oteryn-Platform`, and `Oteryn/Oteryn-Atlas`.

The request is valid only when the caller already has target integration authority for that exact PR/head. The broker independently re-reads GitHub and rejects draft/closed/moved targets, non-`main` bases, non-matching heads, failed or pending required checks, and unresolved current review threads.

A `202` response is non-terminal. The broker preserves the server UUID, performs a distinct async-status readback and fresh target readback, then emits a non-secret receipt. `200` or `409` requires reconciliation. Capability or credential denial fails closed. Terminal integration still requires the repository's real `merge_group` aggregate gate and protected-main readback.

Never substitute direct merge, generic auto-merge, GraphQL enqueue, bypass, protection weakening, force/rebase, or a no-op commit when this route is unavailable.
