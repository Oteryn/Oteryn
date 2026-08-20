#!/usr/bin/env python3
from __future__ import annotations

from datetime import timedelta

import test_verify_ai_review_evidence_core as core_tests


class _VerifierTestProxy:
    """Keep legacy test monkeypatches synchronized with the preserved core."""

    def __init__(self, module) -> None:
        object.__setattr__(self, "_module", module)

    def __getattr__(self, name: str):
        return getattr(object.__getattribute__(self, "_module"), name)

    def __setattr__(self, name: str, value) -> None:
        module = object.__getattribute__(self, "_module")
        setattr(module, name, value)
        core = getattr(module, "_core", None)
        if core is not None and hasattr(core, name):
            setattr(core, name, value)


m = _VerifierTestProxy(core_tests.m)
core_tests.m = m
POLICY = core_tests.POLICY


def _iso(stamp) -> str:
    return stamp.isoformat().replace("+00:00", "Z")


def _verify_with_only_current_anchor(comments, repo, final, current_request):
    return m.verify_records(
        comments,
        policy=POLICY,
        repo_root=repo,
        tier="R2",
        fingerprint=core_tests.ISSUE_FP,
        head=final,
        repository="Oteryn/Test",
        pr_number=7,
        token="x",
        reviews=[core_tests.request_anchor(current_request, final)],
        review_comments=[],
    )


def _live_clean_text(head: str, flair: str) -> str:
    return (
        f"Codex Review: Didn't find any major issues. {flair}\n\n"
        f"**Reviewed commit:** `{head[:10]}`\n\n"
        "<details>live Codex wrapper</details>"
    )


def test_pre_registry_unstructured_request_does_not_poison_post_rollout_head() -> None:
    repo, rollout, final = core_tests.make_repo()
    original_rollout = m.REQUEST_ANCHOR_ROLLOUT_COMMIT
    m.REQUEST_ANCHOR_ROLLOUT_COMMIT = rollout
    try:
        cutoff = m._request_anchor_rollout_time(repo)
        assert cutoff is not None
        historical = core_tests.issue_comment(
            9,
            "@codex review\n\nlegacy request created before immutable anchors existed",
            stamp=_iso(cutoff - timedelta(seconds=2)),
        )
        current = core_tests.issue_comment(
            10,
            core_tests.request_body(final),
            stamp=_iso(cutoff + timedelta(seconds=1)),
        )
        result = core_tests.codex_result(
            11,
            final[:10],
            stamp=_iso(cutoff + timedelta(seconds=2)),
        )
        found = _verify_with_only_current_anchor([historical, current, result], repo, final, current)
        assert found["review_source_kind"] == "issue_comment_result"
        assert found["review_source_commit_id"] == final
    finally:
        m.REQUEST_ANCHOR_ROLLOUT_COMMIT = original_rollout


def test_post_registry_unanchored_malformed_request_remains_ambiguous() -> None:
    repo, rollout, final = core_tests.make_repo()
    original_rollout = m.REQUEST_ANCHOR_ROLLOUT_COMMIT
    m.REQUEST_ANCHOR_ROLLOUT_COMMIT = rollout
    try:
        cutoff = m._request_anchor_rollout_time(repo)
        assert cutoff is not None
        malformed = core_tests.issue_comment(
            9,
            "@codex review\n\nmalformed request after registry rollout",
            stamp=_iso(cutoff + timedelta(seconds=1)),
        )
        current = core_tests.issue_comment(
            10,
            core_tests.request_body(final),
            stamp=_iso(cutoff + timedelta(seconds=2)),
        )
        result = core_tests.codex_result(
            11,
            final[:10],
            stamp=_iso(cutoff + timedelta(seconds=3)),
        )
        core_tests.expect_fail(lambda: _verify_with_only_current_anchor(
            [malformed, current, result], repo, final, current
        ))
    finally:
        m.REQUEST_ANCHOR_ROLLOUT_COMMIT = original_rollout


def test_pre_registry_request_retains_later_p1_for_global_blocking_scan() -> None:
    repo, rollout, final = core_tests.make_repo()
    original_rollout = m.REQUEST_ANCHOR_ROLLOUT_COMMIT
    m.REQUEST_ANCHOR_ROLLOUT_COMMIT = rollout
    try:
        cutoff = m._request_anchor_rollout_time(repo)
        assert cutoff is not None
        legacy = core_tests.attestation(rollout, "abc")
        historical = core_tests.issue_comment(
            9,
            "@codex review\n\nlegacy request created before immutable anchors existed",
            stamp=_iso(cutoff - timedelta(seconds=2)),
        )
        blocker = core_tests.issue_comment(
            10,
            "[P1] Security boundary remains broken",
            login="chatgpt-codex-connector[bot]",
            association="NONE",
            stamp=_iso(cutoff + timedelta(seconds=1)),
        )
        core_tests.expect_fail(lambda: core_tests.run_verify(
            legacy,
            core_tests.source(rollout, "abc"),
            repo,
            final,
            comments=[legacy, historical, blocker],
        ))
    finally:
        m.REQUEST_ANCHOR_ROLLOUT_COMMIT = original_rollout


def test_live_codex_clean_flair_variants_pass() -> None:
    for flair in ("Swish!", "Hooray!", "Chef's kiss."):
        repo, _, final = core_tests.make_repo()
        current = core_tests.issue_comment(
            10,
            core_tests.request_body(final),
            stamp="2026-08-20T10:00:00Z",
        )
        result = core_tests.codex_result(
            11,
            final[:10],
            stamp="2026-08-20T10:01:00Z",
            text=_live_clean_text(final, flair),
        )
        found = _verify_with_only_current_anchor([current, result], repo, final, current)
        assert found["review_source_kind"] == "issue_comment_result"
        assert found["review_source_commit_id"] == final


def test_unobserved_or_contradictory_clean_flair_fails_closed() -> None:
    for flair in (
        "However P1 security finding.",
        "Major issues remain!",
        "There are serious risks.",
        "Looks mostly fine!",
    ):
        repo, _, final = core_tests.make_repo()
        current = core_tests.issue_comment(
            10,
            core_tests.request_body(final),
            stamp="2026-08-20T10:00:00Z",
        )
        result = core_tests.codex_result(
            11,
            final[:10],
            stamp="2026-08-20T10:01:00Z",
            text=_live_clean_text(final, flair),
        )
        core_tests.expect_fail(lambda: _verify_with_only_current_anchor(
            [current, result], repo, final, current
        ))


def main() -> int:
    inherited = [
        value for name, value in sorted(vars(core_tests).items())
        if name.startswith("test_") and callable(value)
    ]
    local = [
        value for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    tests = inherited + local
    for test in tests:
        test()
        print("PASS", test.__name__)
    print(f"ai review evidence tests PASS: {len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
