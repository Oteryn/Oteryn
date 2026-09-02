# Oteryn AI review policy

## Status

Active. Implements ADR 0005.

## Purpose

AI review is optional engineering assistance. It is not GitHub merge authority and is never a required status check.

Use external review only when it adds meaningful value, and use the lightest capable reviewer.

## Routing

- **Default:** no external AI review.
- **Ordinary code change with clear review value:** prefer Codex Spark when available.
- **Material high-risk/control-plane change:** use one Codex deep review on a stable material candidate.
- **Trivial docs, formatting, generated evidence, metadata, or other low-risk change:** no external AI review.

Material high-risk/control-plane work includes changes that materially affect authentication, authorization, permissions, secrets/security boundaries, deployment/production authority, recovery/restore, GitHub Actions workflows or token permissions, branch protection, repository rulesets, required checks, Merge Queue, or governance that can alter autonomous write/integration authority.

If Spark is unavailable for low-risk work, do not automatically escalate to deep Codex. Continue with deterministic validation/self-review unless the change independently meets the high-risk rule.

## Review economy

- Run deterministic validation first.
- Review only a stable material candidate.
- Do not invoke a reviewer merely because a head changed cosmetically or to retrigger governance.
- Re-review only when a material risk-bearing change makes the previous review no longer representative.
- One useful independent deep review is enough for a stable high-risk/control-plane candidate unless a concrete finding requires a material repair.

## Enforcement boundary

No external AI result belongs in the required-status map. Permanent required statuses are only the repository aggregate gates:

```text
Oteryn/Oteryn          -> meta-gate
Oteryn/Oteryn-Game     -> game-gate
Oteryn/Oteryn-Platform -> platform-gate
Oteryn/Oteryn-Atlas    -> atlas-gate
```

Formal R0/R1/R2 classification, `ai-review-gate`, review fingerprints, request/result parsers, review envelopes and attestations are retired from active governance.

## Control-plane owner decision

A candidate-controlled mechanism must not be the sole authority for integrating its own material control-plane change. For such changes use deterministic validation, one independent deep review, explicit human-owner authorization, Merge Queue validation where canonical, and post-change GitHub readback.

Do not build a JSON authorization parser, duplicate-comment proof engine, second required status, or new attestation subsystem for this decision.

## Precedence

This policy implements ADR 0005 and supersedes the former formal R0/R1/R2 target policy and `ai-review-gate` authority model. Historical documents remain evidence only.
