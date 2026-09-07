# Context optimization behavioral qualification handoff

Status: **FINAL_BEHAVIORAL_SCORING_PENDING_EXTERNAL_REVIEW**.

This record completes the bounded C1-C8 collection requested by
`OTERYN-CONTEXT-OPTIMIZATION-QUALIFICATION`. It does not declare an A/B
winner, adopt either candidate, authorize merge/deployment, or prove
organization-wide token or cost savings.

## Collection result

| Population | Expected | Completed | Valid | Inconclusive | Unavailable |
|---|---:|---:|---:|---:|---:|
| GPT-5.6 Sol / LOW-LIGHT | 16 | 16 | 16 | 0 | 0 |
| GPT-6 Astra / LOW-LIGHT | 16 | 16 | 16 | 0 | 0 |
| **Total** | **32** | **32** | **32** | **0** | **0** |

The coordinator used the current Work runtime. Worker requests explicitly selected
GPT-5.6 Sol or GPT-6 Astra with `low` reasoning effort, the available
LOW/LIGHT setting. Runtime model/effort identity was not independently exposed, so
every arm records `REQUESTED_ONLY / RUNTIME_NOT_ATTESTED`. Token, cache, API,
billing and end-to-end timing telemetry remain `NOT_MEASURED`.

Maximum observed behavioral-worker parallelism was six. Each retained record came
from a fresh one-arm worker with child delegation disabled. Workers received one
case, one baseline or candidate source coordinate, the neutral output contract and
only the relevant immutable source files. They did not receive sibling results,
the reviewer rubric, historical R5Q conclusions or the full #166 programme.

## Frozen source identities

| Provider / arm | Commit | Tree | Tested instruction blobs |
|---|---|---|---|
| META baseline | `4fa4d81d55fee44aa21f2a1d80e4a883b6024982` | `ff7b69c94fcdc942a35778e4cf4da30a9141487d` | root `bc7bede1e31a4b55639c5f34a4b7629094d35e80` |
| META candidate | `6a0efb6c3c0130f527bdee814e817fe67c0677a8` | `5646dfa16a37ce83dc089d4cf39b0aa37ef7876f` | root `a3c50c14b0fdb18a7aec42bd43310e38ffe34134`; runner route `b27eca659051ecacb3a06e7d0ebb43c7d763b7a7` when triggered |
| Atlas baseline | `1443615e10cec21d481380b289dcbb742415d709` | `9bee955f9222139345d124a963a72c46118e790e` | root `92f8b48bd68ce415dc3911519e562e54e6c68804` |
| Atlas candidate | `adaeb4ec31d2309a812f5c4c20ef423540d9c2b5` | `09b886770bc41e9917e5901f4d4ec07c1d3a76ec` | root `9c713a3265227278c1afd0c1230a1bf7ecc36c10`; verification route `0c075021edb0b43db64cf1afb7bce43061886d7b` when triggered |

The evidence-only commit that contains this report must be recorded separately
after publication. None of the tested instruction blobs may change in that commit.

## Integrity disposition

- All 32 expected aliases are present exactly once in
  `behavioral-trials.jsonl`; Sol and Astra each contribute C1A-C8B.
- A/B task semantics, requested effort and tool class were held constant within
  each population and pair.
- Immutable local `git show <commit>:<path>` reads replaced the initial
  per-worker network transport after it proved unreliable.
- Six initial Sol transport attempts (C1A-C3B) were excluded and rerun in fresh
  contexts. They are not counted among the 32 retained arms and are recorded only
  as prior invalid attempts in the replacement records.
- No Terra output is counted as Sol or Astra evidence. No final model reviewer was
  started.
- All retained arms are classified `VALID` for external comparative scoring.
  The normalized JSONL preserves exact coordinator-supplied source identities and
  observable worker results; it does not turn unexposed runtime metadata into
  attestation.

## External-review boundary

The evidence is sufficient for the separately authorized external reviewer to
score correctness and comparative behavior. This handoff itself makes no A/B
winner claim. Adoption, Ready-for-Review status, Merge Queue enqueue, merge,
closure of #166/#315, Atlas verification restoration, runtime changes and
deployment remain outside this invocation.

Exact remaining telemetry limitations:

- runtime model identity: `NOT_ATTESTED`;
- runtime effort identity: `NOT_ATTESTED`;
- tokens/cache/API/billing: `NOT_MEASURED`;
- wall-clock and queue latency: `NOT_MEASURED`.

**READY_FOR_EXTERNAL_REVIEW**
