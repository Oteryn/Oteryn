# Ecosystem Test Strategy

## Goal

Prove ecosystem coordination facts at the lowest deterministic layer that can establish them, while keeping product runtime validation in the provider repository that owns the behavior.

## META proof layers

### 1. Syntax and structure

Use deterministic parsers for JSON/YAML and exact-path checks for required authority documents. Parse failure is a hard failure.

### 2. Repository-contract validation

Verify the accepted four-repository topology, unique target coordinates, explicit current coordinates, migration states and provider ownership. META must preserve `UNKNOWN` or pending state instead of converting absent evidence into compatibility.

### 3. Compatibility-manifest validation

A release compatibility record must identify every participating component by immutable commit SHA and may additionally pin tags and artifact digests. Cross-repository contracts must identify a provider, consumer, contract name/version and evidence references.

### 4. Cross-repository evidence verification

When an ecosystem release is assembled, verify provider evidence against the exact recorded product heads. A provider CI result from an older head, a moved tag or an unverified summary does not prove the release set.

### 5. Ecosystem smoke / orchestration

Add cross-repository smoke only when a real composed journey exists and all required repositories and test environments are authorized. META orchestration should consume released/provider-owned artifacts rather than rebuild hidden product state or bypass provider gates.

## Product-owned validation

META does not replace these provider layers:

- **Game:** Rust formatting/static analysis, unit/integration tests, protocol compatibility, deterministic world/content validation, Game-to-Atlas exporter fixtures and native builds.
- **Platform:** application static analysis, unit/feature/database/contract tests, browser/system acceptance and security regression.
- **Atlas:** semantic fixture/determinism tests, corrupt-input negatives, browser loader/decoder tests, build, browser E2E and bounded visual/performance evidence.

The exact commands and required checks are provider-owned and must be discovered from each repository's current trusted workflows and test documentation.

## Cross-repository rules

- Provider-owned schemas remain canonical at the provider.
- Consumer fixtures must name the provider revision or immutable artifact they represent.
- Contract changes require explicit provider/consumer rollout ordering when compatibility is not symmetric.
- An ecosystem manifest may record compatibility only after both sides have exact evidence.
- A redirect, repository transfer or renamed coordinate is not itself compatibility proof.
- Production state is never inferred from repository CI.

## Release gate

An ecosystem release is eligible for publication only when the release manifest is structurally valid, every required provider identity is immutable, required provider checks/evidence are known for those exact identities, and no material compatibility state remains `UNKNOWN` or `CONFLICT` for the release scope.
