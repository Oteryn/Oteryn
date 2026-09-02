# META CI Contract

## Purpose

`Oteryn/Oteryn` is a coordination repository, so its continuous-integration contract is intentionally small. META CI validates ecosystem metadata, repository-boundary invariants and release/compatibility manifest structure. It does not build or test Game, Platform or Atlas runtime code.

## Stable merge gate

The stable aggregate check name is:

```text
meta-gate
```

Repository protection requires only `meta-gate`. The same gate runs on normal pull requests and on the exact GitHub Merge Queue `merge_group` candidate. Internal validation may evolve without creating another externally required status.

## Required validation

`meta-gate` must fail closed when any of these conditions is detected:

- required META authority, CI, testing or release documents are missing;
- committed JSON cannot be parsed;
- `ecosystem/repositories.json` no longer names exactly the four accepted target coordinates;
- META authority is no longer `Oteryn/Oteryn` without an accepted architecture change;
- a repository entry lacks product, current/target coordinate, migration state or authority owner;
- the compatibility schema is malformed or changes JSON Schema generation unexpectedly;
- a merged ecosystem release does not pin exact Game/Platform/Atlas repository coordinates and 40-hex commit SHAs;
- a release artifact digest is not an immutable `sha256:<64-hex>` value;
- a merged release contract is not explicitly `compatible`;
- raw map/client assets, database files or `.env` are committed into META;
- candidate-range whitespace validation fails;
- the read-only governance desired-state or execution-routing validation fails.

## Trigger and runner policy

- Pull requests targeting `main` run the gate.
- Merge Queue `checks_requested` events run the same gate against the exact merge-group candidate (`github.sha` equals `merge_group.head_sha`).
- Pushes to `main` run the same gate as post-merge verification.
- Pull-request runs use concurrency cancellation so superseded heads do not waste Actions capacity.
- The default runner is GitHub-hosted `ubuntu-latest`; META must not require a trusted self-hosted or production-connected runner for ordinary validation.
- Workflow permissions default to `contents: read`.

## Product CI ownership

META records compatible product identities but does not duplicate provider CI:

- Game owns Game build, protocol, world/content and exporter validation.
- Platform owns web/application, identity, persistence and browser/system validation.
- Atlas owns semantic-consumer, browser-map, search/index and derived-data validation.

A compatible ecosystem release may reference successful provider evidence by immutable SHA, tag, artifact ID and digest, but META CI must not convert missing provider evidence into a pass.

## Branch protection target

For the one-maintainer META model, protected `main` requires pull requests, `meta-gate`, Merge Queue, administrator enforcement, linear history and conversation resolution. Required approving review count and required CODEOWNER review are zero. Force push and deletion are disabled. After the successful moving-base Merge Queue canary recorded through PR #125, strict branch freshness is disabled because Merge Queue owns integration freshness.

External AI review is advisory under `docs/governance/AI_REVIEW_POLICY.md`; it is not a required status and has no workflow-based merge authority.

Changing branch/ruleset settings is an administrative GitHub operation, not something this workflow attempts to perform with `GITHUB_TOKEN`.
