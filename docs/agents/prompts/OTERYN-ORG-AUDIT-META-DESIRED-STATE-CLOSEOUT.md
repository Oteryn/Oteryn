# Alias: OTERYN-ORG-AUDIT-META-DESIRED-STATE-CLOSEOUT

MODE: Autonomous terminal closeout.

Repository: `https://github.com/Oteryn/Oteryn`
Primary PR: `Oteryn/Oteryn#37`
Primary lifecycle: organization governance desired-state / drift audit successor.

## Mission

Finish PR #37 completely and safely. Do not stop at audit, review findings, a green CI run, or a mergeability report. The workstream is complete only when the exact final candidate is independently reviewed under the repository AI-review policy, required protected checks pass, the PR is merged normally to `main`, `main` is refreshed, and superseded predecessor PR/task evidence is reconciled without deleting unique history.

## Mandatory first reads

1. `/AGENTS.md`
2. `/docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md`
3. `/docs/governance/AI_REVIEW_POLICY.md`
4. `/ecosystem/ai-review-policy.json`
5. current PR #37 conversation, reviews, inline threads and checks
6. current `main` protection and exact head/base state

Live state outranks this prompt. Treat all SHAs below as checkpoints to verify, not authority.

## Last verified checkpoint

As of 2026-08-22:

- PR #37 is open, non-draft, mergeable.
- base checkpoint: `main@3447e1f5432ca1fc2ac72a7396704408606bf56b`.
- candidate checkpoint: `ced3b2e469e1a742603a882d96738795454e2a76`.
- exact-head META CI run: `32548979533`, job `96972469543`, conclusion `success`.
- governance live-audit regression tests: `18/18 PASS`.
- terminal live-audit tests: `3/3 PASS`.
- AI review policy tests: `46/46 PASS`.
- AI review git metadata tests: `11/11 PASS`.
- AI review evidence verifier tests: `24/24 PASS`.
- exact classification: `R2`, reviewer class `deep`.
- checkpoint fingerprint: `2c186d51535b020fe0bf1a4f8f659c20a1506ccb00e249844556982d8c279b47`.

The last pre-checkpoint Codex generation reviewed `e25738fb...` and raised two findings that were subsequently repaired on `ced3b2e4...`: `pull_request_target` evidence must be read from the current base SHA, and transport `URLError` must become fail-closed `UNKNOWN` rather than an uncaught traceback. Dedicated terminal regressions exist for both repairs.

## Hard constraints

- Do not modify Game, Platform or Atlas repositories from this workstream.
- Do not force-push or bypass branch protection.
- Do not merge with unresolved material P0/P1/P2 findings.
- Do not invoke Codex repeatedly for the same stable fingerprint.
- Do not send external AI review while Draft/WIP or before required CI is green.
- Do not reuse an earlier review unless the exact policy reuse rules are proven.
- Do not turn `UNKNOWN` migration/recovery facts into PASS.
- Preserve historical evidence; close superseded predecessors only after the successor is durably merged.

## Required execution sequence

1. Refresh `main`, PR #37 head, diff, branch protection, required checks, reviews and unresolved threads.
2. If `main` moved in a risk-bearing way, update the candidate without force-push, rerun exact-head CI and recompute classification/fingerprint.
3. Verify the two latest review findings are actually fixed by current code/tests before resolving their threads.
4. Confirm exact-head CI is green and obtain the classifier output from the final run.
5. Determine whether a valid current-generation R2 already exists for the exact current head/fingerprint. If not, send exactly one deep review request using the repository request-anchor contract.
6. Inspect the resulting Codex review, all new inline threads and issue-comment result. Repair every material finding. Any risk-bearing repair requires a new exact-head CI classification and, when policy requires, one new review generation for the new fingerprint.
7. When the final review is clean, run/retrigger only the official `ai-review-gate` verifier as designed; do not generate duplicate AI review merely to retrigger a check.
8. Verify `meta-gate` + `ai-review-gate` on the exact final head.
9. Squash-merge #37 with `expected_head_sha` or equivalent race protection.
10. Refresh `main`, protection and dependent evidence after merge.
11. Reconcile superseded PRs #23/#9 only if live inspection confirms they contain no unique unmerged authority; close as superseded rather than deleting history.
12. Record final merge SHA, exact review head/fingerprint, CI run/job IDs and protection proof to the owning Issue/PR evidence.

## Completion contract

Return DONE only with directly verified:

- `PR_37_MERGED = YES`
- exact merge SHA
- exact reviewed head and fingerprint
- exact successful `meta-gate` and `ai-review-gate` evidence
- no unresolved material review threads
- refreshed post-merge `main`
- predecessor disposition recorded

If a required permission/capability is unavailable, follow the access-discovery contract first and continue every safe useful action before reporting a specific blocker.