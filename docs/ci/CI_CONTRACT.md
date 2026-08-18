# META CI Contract

## Purpose

`Oteryn/Oteryn` is a coordination repository, so its continuous-integration contract is intentionally small. META CI validates ecosystem metadata, repository-boundary invariants and release/compatibility manifest structure. It does not build or test Game, Platform or Atlas runtime code.

## Stable merge gate

The stable aggregate check name is:

```text
meta-gate
```

Repository protection should require `meta-gate` on the exact pull-request head before merge. Internal steps may evolve without changing that public gate name.

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
- candidate-range whitespace validation fails.

## Trigger and runner policy

- Pull requests targeting `main` run the gate.
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

Once `meta-gate` has successfully run on `main`, configure the default branch so ordinary changes require a pull request and the `meta-gate` status check. Force-push and deletion of `main` should remain disabled. Review-count policy may be tightened independently when organization staffing makes mandatory reviewers practical.

Changing branch/ruleset settings is an administrative GitHub operation, not something this workflow attempts to perform with `GITHUB_TOKEN`.
