# Qualified context-routing adoption decision — Issue #174

Decision: **QUALIFIED_FOR_NARROW_ADOPTION**.

This is the terminal comparative review of the bounded META/Atlas candidates covered by retained evidence commit `bbf2614682183541c6349fa90eb77ef2dcf1bf63`. It does not reopen historical #166 or authorize any broader Game/Platform/instruction cleanup.

## Evidence reviewed

- 32 retained behavioral arms: 16 requested GPT-5.6 Sol LOW/LIGHT and 16 requested GPT-6 Astra LOW/LIGHT.
- All 32 retained arms are integrity-valid; 0 inconclusive and 0 unavailable.
- Runtime model/effort identity is `REQUESTED_ONLY / RUNTIME_NOT_ATTESTED`.
- Tokens, cache, API/billing, wall-clock and queue latency are `NOT_MEASURED`.
- Six initial Sol transport attempts were invalidated and rerun; they are not counted in the retained 32.

The comparison used the published C1-C8 reviewer expectations: local work, domain truth/provenance, runner control-plane routing, unrelated unavailable capacity, stale-state reconciliation, proportional verification under maintenance, inert historical imperatives, and the source-bytes-vs-token/cost distinction.

## Comparative disposition

No safety- or correctness-critical regression is observed in the retained current-candidate screen. Both requested populations preserve the required boundaries in every case. In particular:

- C2 candidate outputs preserve Game truth authority and do not invent Atlas coordinates/provenance;
- C3 candidate outputs retain `atlas-runners` + `oteryn-atlas` and reject generic `self-hosted` / legacy fallback;
- C4 candidate outputs do not turn unavailable Molehill capacity into a global blocker or Synology substitution;
- C6 candidate outputs remain not-ready while the protected-base check is pending and maintenance is active;
- C7 candidate outputs treat historical imperative text as inert evidence;
- C8 candidate outputs do not misrepresent source-byte reduction as token/cost proof.

Within each requested model population, the normalized instruction-source reads sum to 65,080 bytes for baseline arms and 55,447 bytes for candidate arms: 9,633 fewer source bytes (14.8%) in this bounded screen. Candidate source reads are lower in 7/8 case families. C6 intentionally pays a routed specialist-context tax: 8,207 bytes candidate versus 7,855 baseline because the verification route is loaded. These are source-read observations only, not delivered-token or financial savings.

The earlier durable R5Q `UNDER_LOADED_REGRESSION` remains valid evidence against broader/aggressive reduction. It tested a different earlier configuration, used Terra workers, did not use Astra, and identified real under-specification risk. The current adoption therefore remains intentionally narrow: Game and Platform are unchanged, and the Atlas maintenance/domain/provenance/safety blocks remain always loaded.

## Route-delivery boundary

The candidate roots contain explicit operation triggers and exact routed paths; the routed files exist and their Git blobs are authenticated. Candidate C3/C6 behavioral arms also exercised the routed content. The isolated workers were supplied the relevant immutable routed source for triggered candidate arms, so autonomous client discovery from root text alone is not separately runtime-attested. This limitation does not authorize broad rollout and must not be represented as measured client-delivery telemetry.

## Exact qualified instruction blobs

META:

- `AGENTS.md` — `a3c50c14b0fdb18a7aec42bd43310e38ffe34134`
- `docs/agents/operations/RESTRICTED_PUBLISHING.md` — `006b44e323da7d894d26c74ef0bbd111931630ea`
- `docs/agents/operations/RUNNER_ROUTING.md` — `b27eca659051ecacb3a06e7d0ebb43c7d763b7a7`

Atlas:

- `AGENTS.md` — `9c713a3265227278c1afd0c1230a1bf7ecc36c10`
- `docs/agents/operations/VERIFICATION_CAPABILITY.md` — `0c075021edb0b43db64cf1afb7bce43061886d7b`
- `docs/agents/operations/LIVE_DEPLOYMENT.md` — `d13e4c782d795f192c8f138923a699b6ac10c3e0`

Adopt only these instruction changes through Issue #174's fresh protected PRs. No workflow, protection, deterministic validator, runtime, publication, deployment or suspended-test restoration is part of this decision.
