# R5Q isolated trial protocol

This file is evaluation harness input, not provider authority.

Run exactly one arm in a fresh ordinary Chat. Do not inspect sibling arm files, the reviewer rubric, R5 comparison evidence, #142/#151 evidence, or previous trial conclusions.

## Controls

- Read-only. Do not mutate repositories or external systems.
- Work only against the provider repository/source identity named by the arm prompt.
- Conceptual starting directory is the provider repository root.
- Use the same requested model and reasoning effort for every arm. Recommended owner configuration: GPT-5.6 Sol, Medium.
- Do not delegate.
- Use only the minimum instruction/domain evidence needed to answer the task.
- Do not ask the owner for facts that authorized repository reads can resolve.
- Do not reveal hidden chain-of-thought. Report only the task answer and externally observable source/tool telemetry.
- Tokens/API/billing are `NOT_MEASURED` unless directly exposed. Never estimate them from bytes.
- If runtime model/effort is not attested, record `REQUESTED_ONLY / RUNTIME_NOT_ATTESTED`.
- Do not score your own correctness.

## Telemetry

After the task answer emit:

```yaml
trial_result:
  alias:
  repository:
  source_commit:
  source_tree:
  requested_model_effort:
  runtime_attestation:
  instruction_reads:
    full_files: []
    full_read_count:
    full_read_bytes:
    partial_files: []
    partial_read_count:
    instruction_search_count:
    instruction_hops:
    repeated_unchanged_reads:
  domain_or_lifecycle_reads: []
  tool_usage:
    repository_fetches:
    searches:
    issue_pr_reads:
    capability_discovery_calls:
    delegated_workers: 0
  behavior:
    clarification_questions:
    handoff_attempts:
    blocker_claims:
  time:
    wall_clock: NOT_MEASURED
    api_or_queue_latency: NOT_MEASURED
  tokens_api_billing: NOT_MEASURED
  limitations: []
```

For `full_read_bytes`, sum exact source sizes only when exposed by repository metadata; otherwise use `NOT_MEASURED`. Do not count the R5Q arm file or this protocol as provider instruction retrieval.
