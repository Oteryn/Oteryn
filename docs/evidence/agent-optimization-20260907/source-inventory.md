# Final instruction-source inventory

This inventory compares immutable tracked Git blobs. Its corpus is the union of the scoped paths present at either baseline or candidate revision; a new/deleted path contributes zero bytes and lines on the side where it is absent. Counts are source volume, not token, cache, billing, cost, productivity, or causal savings measurements.

| Repository | Immutable comparison | Scoped union | Before | After |
|---|---|---:|---:|---:|
| META | `5ed3f144…` → `da4cbbc…` | 9 paths | 79,894 B / 1,419 lines | 60,331 B / 1,121 lines |
| Game | `a6f69427…` → `6f9378e2…` (`7adcaa9f…`) | 58 paths | 679,113 B / 12,951 lines | 360,332 B / 8,547 lines |
| Platform | `3557085c…` → `bad2e5a2…` (`39342593…`) | 20 paths | 307,953 B / 5,277 lines | 106,829 B / 1,944 lines |
| Atlas | `51623c7d…` → `53527271…` | 45 paths | 445,757 B / 9,612 lines | 447,347 B / 9,915 lines |

The META row is a separate nine-path central-source delta from #159/#160/#162. Its retained central policy, machine-authority and validator bundle is organizational overhead, not a provider source-saving claim.

## Repository detail

- Game preserves 47 lifecycle-reusable prompts. The source subset (47 prompts, root, nearest bootstrap and two local prompt standards) is 539,335 B / 9,578 lines before and 346,532 B / 8,240 after. Its local validator subset is six present files before versus two after (seven-path union), 139,778 B / 3,373 lines versus 13,800 B / 307 lines. Five copied Remote Desktop/dedup validators were removed; `validate_inherited_prompt_policy.py` and the new central-adoption regression remain.
- Platform preserves dispatch semantics: `DOCUMENTATION_IA_CATALOG.json` still has 23 prompts, exactly ten active reusable and 13 `one_shot_historical`/`historical_do_not_run`. The 20-path corpus includes three root/bootstrap/nearest files, two standards, two validator/test files, ten active prompt bodies and three prompt text suites. The local policy-consistency validator/test were replaced in place by the central authenticated consumer boundary.
- Atlas preserves all 38 reusable prompts. Six W4 prompts removed duplicated procedure text; `ATLAS-E2E-VERIFICATION-OPTIMIZATION-IMPLEMENTATION.md` remains unchanged because open PR #346 owns it. Root plus nearest IA fell from 25,587 B / 195 lines to 11,208 B / 106. Prompt bodies changed from 403,160 B / 9,029 lines to 400,453 B / 8,969. Two provider validator files were added, so total scoped Atlas source grows slightly; that is retained delivery/validation overhead, not negative “savings.”

## Validator and controller disposition

Game removed `validate_remote_desktop_prompt_routing.py`, its three named routing suites, and `test_prompt_deduplication.py`. Platform removed copied organization execution, continuation, communication and model controllers from every active prompt while retaining domain deltas. Atlas retains one explicitly deferred duplicated GitHub-first procedure under live ownership; the bounded scan made no broader claim about the other 31 prompts.

No tracked files exist under `skills/`, `.agents/`, or `.codex/` at either compared revision in any of the four repositories. Atlas W3B is NOT_APPLICABLE: no existing configuration or live mandate requires repair. Optional introduction remains outside maintenance authority and is not recorded as required pending work.

The existing evaluation records provide the already-authorized behavioral qualification for Game and Platform. No new model trials are needed for this source inventory. Atlas records static/deterministic qualification only and does not claim new model behavior evidence.

## Final acceptance correction

The counts above are a bounded corpus inventory, not repository-wide policy consistency. Independent final review withdrew broad Game rollout qualification for two reachable P1 controller conflicts and identified Platform programme-level P1 specialist-controller residue. Active external PRs #379 and #1303 own these repairs. See the residue review files and REPORT; the original 16/16 screening per provider remains bounded evidence only.
