# Oteryn AI review policy

## Status

Active target policy upon merge of PR #125. The legacy `ai-review-gate` and machine review-tier implementation may remain temporarily only until the minimal META follow-up removes them from protected merge enforcement.

## Purpose

AI review is optional engineering assistance. It is not a GitHub merge authority and must not become a second required status, second-human dependency, review-envelope system, or source of governance loops.

The objective is simple: use external review when it adds meaningful value, avoid spending review capacity on trivial changes, and prefer the lightest capable reviewer.

## Routing

Use these rules:

- **Default:** no external AI review.
- **Ordinary code change with clear review value:** prefer Codex Spark when available.
- **Material high-risk/control-plane change:** use one Codex deep review on a stable material candidate.
- **Trivial docs, formatting, generated evidence, metadata, or other low-risk change:** no external AI review.

Material high-risk/control-plane work includes changes that materially affect authentication, authorization, permissions, secrets/security boundaries, deployment/production authority, recovery/restore, GitHub Actions workflows or token permissions, branch protection, repository rulesets, required checks, Merge Queue, or governance that can alter autonomous write/integration authority.

If Spark is unavailable for low-risk work, do not automatically escalate to deep Codex. Continue with deterministic validation/self-review unless the change independently meets the high-risk rule.

## Review economy

- Run deterministic validation first.
- Review only a stable material candidate.
- Do not repeatedly invoke a reviewer merely because a head changed cosmetically or because governance needs a retrigger.
- Re-review only when a material risk-bearing change makes the previous review no longer representative.
- One useful independent deep review is enough for a stable high-risk/control-plane candidate unless a concrete finding requires a material repair.

## Enforcement boundary

No external AI result belongs in the permanent required-status map.

Permanent required statuses are only the repository aggregate gates:

```text
Oteryn/Oteryn          -> meta-gate
Oteryn/Oteryn-Game     -> game-gate
Oteryn/Oteryn-Platform -> platform-gate
Oteryn/Oteryn-Atlas    -> atlas-gate
```

The existing `ai-review-gate`, R0/R1/R2 classifier, review fingerprint/reuse rules, structured review evidence, request/result parsers, envelopes and attestations are legacy transition machinery. They may continue only as needed to pass the currently configured protected path while the simplification reset is integrated. They are not target architecture and must be retired by the minimal META follow-up after the replacement path is proven.

## Control-plane owner decision

A candidate-controlled mechanism must not be the sole authority for integrating its own material control-plane change. For such changes use deterministic validation, one independent deep review, explicit human-owner authorization, Merge Queue validation where already canonical, and post-change GitHub readback.

Do not build a JSON authorization parser, duplicate-comment proof engine, second required status, or new attestation subsystem for this decision.

## Precedence

This policy implements ADR 0005 and supersedes the formal R0/R1/R2 target policy and `ai-review-gate`-as-permanent-authority model previously documented by PR #123 and earlier governance bootstrap work. Historical documents remain evidence of how the legacy mechanism was built, not current target authority.
