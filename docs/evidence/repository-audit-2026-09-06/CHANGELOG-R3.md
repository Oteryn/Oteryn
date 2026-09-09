# R3 correction and preservation record

Source of this revision is the complete 41,716-byte R2 delivered in the conversation, not the 20,763-byte abridged file published at `ad0680d838a8169bf244b46639486329d30e83a5`. Source identities are recorded in `evidence/revision-provenance.json`.

## Material corrections

1. Restore PR151-02 to **P2, domains J/P**, with FACT/UNKNOWN, impact and recommended direction. Its placement under P3 in the earlier publication had no justified severity change.
2. Preserve the original source findings, counterevidence, actual Windows errors, Linux limits, settings caveats, dependency ownership and roadmap. Do not replace them with an executive summary.
3. Add **AUD-10** (SCR-01, empty desired audit range succeeds) and **AUD-11** (SCR-02, boolean/integer disagreement), including seven diagnostic calls and explicit non-claims about entire CI/protection bypass.
4. Extend AUD-05 with the active access/continuation contract's generic merge-up requirement versus ADR 0005/Merge Queue. This is the same instruction-authority drift, not an inflated duplicate finding.
5. Recover historical META timing/head projections, verify hashes, join IDs and recompute counts/statistics. Publish the necessary input columns and reproduction method rather than only a narrative result.
6. Complete full reading of five previously metadata-only SKILL entrypoints and all seven invocation metadata files. Do not claim inspection of every conditional helper or prove runtime loading.
7. Replace the absolute claim that no further read-only audit could find a defect with a bounded completion reconciliation of the known gaps and original requirements.
8. Keep the audit snapshot separate from later #152 and the publication commit; label historical test/settings captures rather than silently refreshing their dates.

## Public-safe redactions

Removed only private absolute user paths, host identity and machine-specific client configuration values. Retained the material conclusion that the observed local profile did not mechanically impose read-only isolation. Preserved supported runtime versions, source revisions, commands with a neutral isolated-root placeholder, statuses, counts, evidence hashes and uncertainty.

Neither private credentials nor source code from provider products is included. No recommendation became policy or permission. The original prompt is unchanged; no criteria were relaxed. Old published revisions remain in Git history rather than being rewritten.

## Publication acceptance

The prepared file bytes must match the Git blobs read back from the new commit. The tree diff must remain inside this evidence directory. Existing META CI must be observed on the exact final PR head. A success there confirms publication validation, not semantic completeness or implementation of the recommendations. The PR is not merged by this task.
