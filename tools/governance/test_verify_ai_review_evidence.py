#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from copy import deepcopy
from datetime import timedelta
from pathlib import Path

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
POLICY = deepcopy(core_tests.POLICY)


def _iso(stamp) -> str:
    return stamp.isoformat().replace("+00:00", "Z")


def _policy_with_rollout(repository: str, rollout: str) -> dict:
    policy = deepcopy(POLICY)
    policy["request_anchor_rollouts"] = {repository: rollout}
    return policy


def _server_anchor(comment: dict, final: str, *, association: str = "MEMBER") -> dict:
    server_comment = deepcopy(comment)
    server_comment["author_association"] = association
    return core_tests.request_anchor(server_comment, final)


def _verify_with_only_current_anchor(
    comments, repo, final, current_request, *, policy=None, anchor=None, extra_reviews=None,
    review_comments=None,
):
    return m.verify_records(
        comments,
        policy=policy or POLICY,
        repo_root=repo,
        tier="R2",
        fingerprint=core_tests.ISSUE_FP,
        head=final,
        repository="Oteryn/Test",
        pr_number=7,
        token="x",
        reviews=(extra_reviews or []) + [anchor or core_tests.request_anchor(current_request, final)],
        review_comments=review_comments or [],
    )


def _live_clean_text(head: str, flair: str) -> str:
    return (
        f"Codex Review: Didn't find any major issues. {flair}\n\n"
        f"**Reviewed commit:** `{head[:10]}`\n\n"
        "<details>live Codex wrapper</details>"
    )


def test_pre_registry_unstructured_request_does_not_poison_post_rollout_head() -> None:
    repo, rollout, final = core_tests.make_repo()
    policy = _policy_with_rollout("Oteryn/Test", rollout)
    cutoff = m._request_anchor_rollout_time(repo, rollout)
    assert cutoff is not None
    historical = core_tests.issue_comment(
        9,
        "@codex review\n\nlegacy request created before immutable anchors existed",
        association="CONTRIBUTOR",
        stamp=_iso(cutoff - timedelta(seconds=2)),
    )
    current = core_tests.issue_comment(
        10,
        core_tests.request_body(final),
        association="CONTRIBUTOR",
        stamp=_iso(cutoff + timedelta(seconds=1)),
    )
    result = core_tests.codex_result(11, final[:10], stamp=_iso(cutoff + timedelta(seconds=2)))
    found = _verify_with_only_current_anchor(
        [historical, current, result], repo, final, current,
        policy=policy, anchor=_server_anchor(current, final),
    )
    assert found["review_source_kind"] == "issue_comment_result"
    assert found["review_source_commit_id"] == final


def test_post_registry_unanchored_malformed_request_remains_ambiguous() -> None:
    repo, rollout, final = core_tests.make_repo()
    policy = _policy_with_rollout("Oteryn/Test", rollout)
    cutoff = m._request_anchor_rollout_time(repo, rollout)
    assert cutoff is not None
    malformed = core_tests.issue_comment(
        9,
        "@codex review\n\nmalformed request after registry rollout",
        stamp=_iso(cutoff + timedelta(seconds=1)),
    )
    current = core_tests.issue_comment(
        10, core_tests.request_body(final), stamp=_iso(cutoff + timedelta(seconds=2)),
    )
    result = core_tests.codex_result(11, final[:10], stamp=_iso(cutoff + timedelta(seconds=3)))
    core_tests.expect_fail(lambda: _verify_with_only_current_anchor(
        [malformed, current, result], repo, final, current, policy=policy
    ))


def test_pre_registry_request_retains_later_p1_for_global_blocking_scan() -> None:
    repo, rollout, final = core_tests.make_repo()
    cutoff = m._request_anchor_rollout_time(repo, rollout)
    assert cutoff is not None
    policy = _policy_with_rollout("Oteryn/Test", rollout)
    historical = core_tests.issue_comment(
        9,
        "@codex review\n\nlegacy request created before immutable anchors existed",
        login="legacy-member", association="CONTRIBUTOR",
        stamp=_iso(cutoff - timedelta(seconds=3)),
    )
    blocker = core_tests.issue_comment(
        10, "[P1] Security boundary remains broken",
        login="chatgpt-codex-connector[bot]", association="NONE",
        stamp=_iso(cutoff - timedelta(seconds=2)),
    )
    current = core_tests.issue_comment(
        11, core_tests.request_body(final), association="CONTRIBUTOR",
        stamp=_iso(cutoff + timedelta(seconds=1)),
    )
    result = core_tests.codex_result(12, final[:10], stamp=_iso(cutoff + timedelta(seconds=2)))
    core_tests.expect_fail(lambda: _verify_with_only_current_anchor(
        [historical, blocker, current, result], repo, final, current,
        policy=policy, anchor=_server_anchor(current, final),
    ))


def test_edited_pre_registry_hidden_member_retains_later_p1() -> None:
    repo, rollout, final = core_tests.make_repo()
    cutoff = m._request_anchor_rollout_time(repo, rollout)
    assert cutoff is not None
    policy = _policy_with_rollout("Oteryn/Test", rollout)
    edited_historical = core_tests.issue_comment(
        8, "edited legacy note with request text removed",
        login="different-hidden-member", association="CONTRIBUTOR",
        stamp=_iso(cutoff - timedelta(seconds=4)),
        updated_stamp=_iso(cutoff - timedelta(seconds=1)),
    )
    blocker = core_tests.issue_comment(
        9, "[P1] Historical security boundary remains broken",
        login="chatgpt-codex-connector[bot]", association="NONE",
        stamp=_iso(cutoff - timedelta(seconds=2)),
    )
    current = core_tests.issue_comment(
        10, core_tests.request_body(final), association="CONTRIBUTOR",
        stamp=_iso(cutoff + timedelta(seconds=1)),
    )
    result = core_tests.codex_result(11, final[:10], stamp=_iso(cutoff + timedelta(seconds=2)))
    core_tests.expect_fail(lambda: _verify_with_only_current_anchor(
        [edited_historical, blocker, current, result], repo, final, current,
        policy=policy, anchor=_server_anchor(current, final),
    ))


def test_deleted_pre_registry_request_retains_surviving_p1() -> None:
    repo, rollout, final = core_tests.make_repo()
    cutoff = m._request_anchor_rollout_time(repo, rollout)
    assert cutoff is not None
    policy = _policy_with_rollout("Oteryn/Test", rollout)
    blocker = core_tests.issue_comment(
        9, "[P1] Historical security boundary remains broken after request deletion",
        login="chatgpt-codex-connector[bot]", association="NONE",
        stamp=_iso(cutoff - timedelta(seconds=2)),
    )
    current = core_tests.issue_comment(
        10, core_tests.request_body(final), association="CONTRIBUTOR",
        stamp=_iso(cutoff + timedelta(seconds=1)),
    )
    result = core_tests.codex_result(11, final[:10], stamp=_iso(cutoff + timedelta(seconds=2)))
    core_tests.expect_fail(lambda: _verify_with_only_current_anchor(
        [blocker, current, result], repo, final, current,
        policy=policy, anchor=_server_anchor(current, final),
    ))


def test_untrusted_pre_registry_blocking_text_without_request_does_not_block() -> None:
    repo, rollout, final = core_tests.make_repo()
    cutoff = m._request_anchor_rollout_time(repo, rollout)
    assert cutoff is not None
    policy = _policy_with_rollout("Oteryn/Test", rollout)
    noise = core_tests.issue_comment(
        9, "[P1] Untrusted historical text", login="evil-bot", association="NONE",
        stamp=_iso(cutoff - timedelta(seconds=2)),
    )
    current = core_tests.issue_comment(
        10, core_tests.request_body(final), association="CONTRIBUTOR",
        stamp=_iso(cutoff + timedelta(seconds=1)),
    )
    result = core_tests.codex_result(11, final[:10], stamp=_iso(cutoff + timedelta(seconds=2)))
    found = _verify_with_only_current_anchor(
        [noise, current, result], repo, final, current,
        policy=policy, anchor=_server_anchor(current, final),
    )
    assert found["review_source_kind"] == "issue_comment_result"


def test_inflight_legacy_finding_after_rollout_blocks_before_first_valid_anchor() -> None:
    repo, rollout, final = core_tests.make_repo()
    cutoff = m._request_anchor_rollout_time(repo, rollout)
    assert cutoff is not None
    policy = _policy_with_rollout("Oteryn/Test", rollout)
    blocker = core_tests.issue_comment(
        9, "[P1] In-flight legacy review completed after registry rollout",
        login="chatgpt-codex-connector[bot]", association="NONE",
        stamp=_iso(cutoff + timedelta(seconds=1)),
    )
    current = core_tests.issue_comment(
        10, core_tests.request_body(final), association="CONTRIBUTOR",
        stamp=_iso(cutoff + timedelta(seconds=2)),
    )
    result = core_tests.codex_result(11, final[:10], stamp=_iso(cutoff + timedelta(seconds=3)))
    core_tests.expect_fail(lambda: _verify_with_only_current_anchor(
        [blocker, current, result], repo, final, current,
        policy=policy, anchor=_server_anchor(current, final),
    ))


def test_inflight_same_second_lower_id_blocks_before_first_valid_anchor() -> None:
    repo, rollout, final = core_tests.make_repo()
    cutoff = m._request_anchor_rollout_time(repo, rollout)
    assert cutoff is not None
    policy = _policy_with_rollout("Oteryn/Test", rollout)
    shared = _iso(cutoff + timedelta(seconds=2))
    blocker = core_tests.issue_comment(
        9, "[P1] Same-second in-flight blocker",
        login="chatgpt-codex-connector[bot]", association="NONE", stamp=shared,
    )
    current = core_tests.issue_comment(
        10, core_tests.request_body(final), association="CONTRIBUTOR", stamp=shared,
    )
    result = core_tests.codex_result(11, final[:10], stamp=_iso(cutoff + timedelta(seconds=3)))
    core_tests.expect_fail(lambda: _verify_with_only_current_anchor(
        [blocker, current, result], repo, final, current,
        policy=policy, anchor=_server_anchor(current, final),
    ))


def test_untrusted_inflight_p1_text_before_first_anchor_does_not_block() -> None:
    repo, rollout, final = core_tests.make_repo()
    cutoff = m._request_anchor_rollout_time(repo, rollout)
    assert cutoff is not None
    policy = _policy_with_rollout("Oteryn/Test", rollout)
    noise = core_tests.issue_comment(
        9, "[P1] Untrusted in-flight-looking historical text",
        login="evil-bot", association="NONE", stamp=_iso(cutoff + timedelta(seconds=1)),
    )
    current = core_tests.issue_comment(
        10, core_tests.request_body(final), association="CONTRIBUTOR",
        stamp=_iso(cutoff + timedelta(seconds=2)),
    )
    result = core_tests.codex_result(11, final[:10], stamp=_iso(cutoff + timedelta(seconds=3)))
    found = _verify_with_only_current_anchor(
        [noise, current, result], repo, final, current,
        policy=policy, anchor=_server_anchor(current, final),
    )
    assert found["review_source_kind"] == "issue_comment_result"


def test_no_anchor_keeps_legacy_window_open_for_trusted_p1() -> None:
    repo, rollout, final = core_tests.make_repo()
    cutoff = m._request_anchor_rollout_time(repo, rollout)
    assert cutoff is not None
    policy = _policy_with_rollout("Oteryn/Test", rollout)
    blocker = core_tests.issue_comment(
        9, "[P1] In-flight legacy review with no immutable anchor yet",
        login="chatgpt-codex-connector[bot]", association="NONE",
        stamp=_iso(cutoff + timedelta(minutes=5)),
    )
    assert m._legacy_trusted_blocking_finding_exists(
        [blocker], reviews=[], policy=policy, repo_root=repo, head=final,
        repository="Oteryn/Test", pr_number=7,
    ) is True


def test_no_anchor_untrusted_p1_text_does_not_block() -> None:
    repo, rollout, final = core_tests.make_repo()
    cutoff = m._request_anchor_rollout_time(repo, rollout)
    assert cutoff is not None
    policy = _policy_with_rollout("Oteryn/Test", rollout)
    noise = core_tests.issue_comment(
        9, "[P1] Untrusted text while no immutable anchor exists",
        login="evil-bot", association="NONE",
        stamp=_iso(cutoff + timedelta(minutes=5)),
    )
    assert m._legacy_trusted_blocking_finding_exists(
        [noise], reviews=[], policy=policy, repo_root=repo, head=final,
        repository="Oteryn/Test", pr_number=7,
    ) is False


def test_older_valid_anchor_defines_boundary_after_non_neutral_repair() -> None:
    repo, rollout, final = core_tests.make_repo(non_neutral_after_review=True)
    cutoff = m._request_anchor_rollout_time(repo, rollout)
    assert cutoff is not None
    policy = _policy_with_rollout("Oteryn/Test", rollout)
    old_request = core_tests.issue_comment(
        8, core_tests.request_body(rollout), stamp=_iso(cutoff + timedelta(seconds=1)),
    )
    old_anchor = core_tests.request_anchor(old_request, rollout)
    blocker = core_tests.issue_comment(
        9, "[P1] Finding from already-anchored older generation",
        login="chatgpt-codex-connector[bot]", association="NONE",
        stamp=_iso(cutoff + timedelta(seconds=2)),
    )
    current = core_tests.issue_comment(
        10, core_tests.request_body(final), association="CONTRIBUTOR",
        stamp=_iso(cutoff + timedelta(seconds=3)),
    )
    result = core_tests.codex_result(11, final[:10], stamp=_iso(cutoff + timedelta(seconds=4)))
    found = _verify_with_only_current_anchor(
        [blocker, current, result], repo, final, current,
        policy=policy, anchor=_server_anchor(current, final), extra_reviews=[old_anchor],
    )
    assert found["review_source_kind"] == "issue_comment_result"
    assert found["review_source_commit_id"] == final


def test_repository_without_rollout_marker_keeps_legacy_request_ambiguous() -> None:
    repo, rollout, final = core_tests.make_repo()
    cutoff = m._request_anchor_rollout_time(repo, rollout)
    assert cutoff is not None
    historical = core_tests.issue_comment(
        9, "@codex review\n\nlegacy-looking request with no repository rollout proof",
        association="CONTRIBUTOR", stamp=_iso(cutoff - timedelta(seconds=2)),
    )
    current = core_tests.issue_comment(
        10, core_tests.request_body(final), association="CONTRIBUTOR",
        stamp=_iso(cutoff + timedelta(seconds=1)),
    )
    result = core_tests.codex_result(11, final[:10], stamp=_iso(cutoff + timedelta(seconds=2)))
    core_tests.expect_fail(lambda: _verify_with_only_current_anchor(
        [historical, current, result], repo, final, current,
        policy=deepcopy(POLICY), anchor=_server_anchor(current, final),
    ))


def test_malformed_rollout_marker_keeps_legacy_request_ambiguous() -> None:
    repo, rollout, final = core_tests.make_repo()
    cutoff = m._request_anchor_rollout_time(repo, rollout)
    assert cutoff is not None
    historical = core_tests.issue_comment(
        9, "@codex review\n\nlegacy-looking request with malformed rollout proof",
        stamp=_iso(cutoff - timedelta(seconds=2)),
    )
    current = core_tests.issue_comment(
        10, core_tests.request_body(final), stamp=_iso(cutoff + timedelta(seconds=1)),
    )
    result = core_tests.codex_result(11, final[:10], stamp=_iso(cutoff + timedelta(seconds=2)))
    policy = _policy_with_rollout("Oteryn/Test", "not-a-sha")
    core_tests.expect_fail(lambda: _verify_with_only_current_anchor(
        [historical, current, result], repo, final, current, policy=policy
    ))


def test_immutable_anchor_restores_hidden_member_request_trust() -> None:
    repo, _, final = core_tests.make_repo()
    current = core_tests.issue_comment(
        10, core_tests.request_body(final), association="CONTRIBUTOR",
        stamp="2026-08-20T10:00:00Z",
    )
    result = core_tests.codex_result(11, final[:10], stamp="2026-08-20T10:01:00Z")
    found = _verify_with_only_current_anchor(
        [current, result], repo, final, current, anchor=_server_anchor(current, final),
    )
    assert found["review_request_id"] == 10
    assert found["review_source_commit_id"] == final


def test_hidden_member_request_without_anchor_fails_closed() -> None:
    repo, _, final = core_tests.make_repo()
    current = core_tests.issue_comment(
        10, core_tests.request_body(final), association="CONTRIBUTOR",
        stamp="2026-08-20T10:00:00Z",
    )
    result = core_tests.codex_result(11, final[:10], stamp="2026-08-20T10:01:00Z")
    core_tests.expect_fail(lambda: m.verify_records(
        [current, result], policy=POLICY, repo_root=repo, tier="R2",
        fingerprint=core_tests.ISSUE_FP, head=final, repository="Oteryn/Test",
        pr_number=7, token="x", reviews=[], review_comments=[],
    ))


def test_anchor_body_mismatch_does_not_restore_hidden_member_trust() -> None:
    repo, _, final = core_tests.make_repo()
    current = core_tests.issue_comment(
        10, core_tests.request_body(final), association="CONTRIBUTOR",
        stamp="2026-08-20T10:00:00Z",
    )
    anchor = _server_anchor(current, final)
    current = deepcopy(current)
    current["body"] += "\nextra unanchored text"
    result = core_tests.codex_result(11, final[:10], stamp="2026-08-20T10:01:00Z")
    core_tests.expect_fail(lambda: _verify_with_only_current_anchor(
        [current, result], repo, final, current, anchor=anchor
    ))


def test_anchored_author_unrelated_edit_still_fails_closed() -> None:
    repo, _, final = core_tests.make_repo()
    note = core_tests.issue_comment(
        9, "maintainer note", association="CONTRIBUTOR",
        stamp="2026-08-20T09:59:00Z", updated_stamp="2026-08-20T10:02:00Z",
    )
    current = core_tests.issue_comment(
        10, core_tests.request_body(final), association="CONTRIBUTOR",
        stamp="2026-08-20T10:00:00Z",
    )
    result = core_tests.codex_result(11, final[:10], stamp="2026-08-20T10:01:00Z")
    core_tests.expect_fail(lambda: _verify_with_only_current_anchor(
        [note, current, result], repo, final, current, anchor=_server_anchor(current, final),
    ))



def test_edited_inline_from_superseded_generation_does_not_poison_fresh_review() -> None:
    repo, reviewed, final = core_tests.make_repo(non_neutral_after_review=True)
    current = core_tests.issue_comment(
        10, core_tests.request_body(final), stamp="2026-08-20T10:00:00Z",
    )
    result = core_tests.codex_result(
        11, final[:10], stamp="2026-08-20T10:03:00Z",
    )
    old_review = core_tests.codex_review(700, reviewed)
    old_edited_inline = core_tests.codex_inline(
        700, "[P1] Superseded finding repaired by the later non-neutral commit",
        stamp="2026-08-20T09:58:00Z", updated_stamp="2026-08-20T09:58:01Z",
    )
    found = _verify_with_only_current_anchor(
        [current, result], repo, final, current, extra_reviews=[old_review],
        review_comments=[old_edited_inline],
    )
    assert found["review_source_kind"] == "issue_comment_result"
    assert found["review_source_commit_id"] == final

def test_preserved_core_suite_passes_standalone() -> None:
    script = Path(core_tests.__file__).resolve()
    completed = subprocess.run(
        [sys.executable, str(script)], cwd=script.parent, text=True, encoding="utf-8",
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180, check=False,
    )
    assert completed.returncode == 0, completed.stdout
    assert "ai review evidence tests PASS:" in completed.stdout


def test_live_codex_clean_flair_variants_pass() -> None:
    for flair in (
        "Swish!", "Hooray!", "Chef's kiss.", "Breezy!", "Nice work!", "Bravo.",
        ":rocket:", "More of your lovely PRs please.", "You're on a roll.",
    ):
        repo, _, final = core_tests.make_repo()
        current = core_tests.issue_comment(
            10, core_tests.request_body(final), stamp="2026-08-20T10:00:00Z",
        )
        result = core_tests.codex_result(
            11, final[:10], stamp="2026-08-20T10:01:00Z", text=_live_clean_text(final, flair),
        )
        found = _verify_with_only_current_anchor([current, result], repo, final, current)
        assert found["review_source_kind"] == "issue_comment_result"
        assert found["review_source_commit_id"] == final


def test_unobserved_or_contradictory_clean_flair_fails_closed() -> None:
    for flair in (
        "However P1 security finding.", "Major issues remain!",
        "There are serious risks.", "Looks mostly fine!",
    ):
        repo, _, final = core_tests.make_repo()
        current = core_tests.issue_comment(
            10, core_tests.request_body(final), stamp="2026-08-20T10:00:00Z",
        )
        result = core_tests.codex_result(
            11, final[:10], stamp="2026-08-20T10:01:00Z", text=_live_clean_text(final, flair),
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