import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from closed_pr_cleanup import CleanupError, parse_disposition, process_event, run_cli

SHA = "a" * 40


def event(body="", branch="feat/demo", sha=SHA, merged=False, head_repo="Oteryn/Demo"):
    return {
        "repository": {"full_name": "Oteryn/Demo"},
        "pull_request": {
            "number": 7, "state": "closed", "merged": merged,
            "merged_at": "2026-08-22T00:00:00Z" if merged else None,
            "body": body,
            "head": {"ref": branch, "sha": sha, "repo": {"full_name": head_repo}},
        },
    }


def live(evt):
    return json.loads(json.dumps(evt["pull_request"]))


class GH:
    def __init__(self, evt=None, *, protected=False, open_pulls=None, default="main"):
        self.evt, self.protected, self.open_pulls, self.default = evt, protected, open_pulls or [], default
        self.calls = []
    def get_repository(self):
        self.calls.append("repo"); return {"full_name": "Oteryn/Demo", "default_branch": self.default}
    def get_pull(self, number):
        self.calls.append("pull"); return live(self.evt)
    def get_branch(self, branch):
        self.calls.append("branch"); return {"protected": self.protected}
    def get_open_pulls_for_branch(self, branch):
        self.calls.append("open"); return self.open_pulls


class Git:
    def __init__(self, sha=SHA): self.sha, self.deletes = sha, []
    def remote_ref_sha(self, branch): return self.sha
    def delete_with_lease(self, branch, expected_sha):
        if self.sha != expected_sha: raise CleanupError("lease mismatch")
        self.deletes.append((branch, expected_sha)); self.sha = None


class CleanupTests(unittest.TestCase):
    def delete_event(self, branch="feat/demo"):
        return event("Branch-Disposition: delete\nBranch-Disposition-Reason: superseded", branch=branch)

    def test_disposition_contract(self):
        self.assertEqual(parse_disposition(""), (None, None))
        self.assertEqual(parse_disposition("Branch-Disposition: RETAIN\nBranch-Disposition-Reason: provenance"), ("retain", "provenance"))
        with self.assertRaisesRegex(CleanupError, "requires exactly one"):
            parse_disposition("Branch-Disposition: delete")
        with self.assertRaisesRegex(CleanupError, "invalid Branch-Disposition value"):
            parse_disposition("Branch-Disposition: delete after merge\nBranch-Disposition-Reason: old")
        with self.assertRaisesRegex(CleanupError, "exactly one Branch-Disposition"):
            parse_disposition("Branch-Disposition: delete\nBranch-Disposition: retain\nBranch-Disposition-Reason: conflict")

    def test_no_marker_and_retain_are_non_destructive(self):
        for body, expected in [("", "NOT_APPLICABLE"), ("Branch-Disposition: retain\nBranch-Disposition-Reason: keep", "RETAIN")]:
            gh, git = GH(), Git()
            self.assertEqual(process_event(event(body), "Oteryn/Demo", gh, git)["result"], expected)
            self.assertEqual(git.deletes, []); self.assertEqual(gh.calls, [])

    def test_delete_exact_head(self):
        evt = self.delete_event(); gh, git = GH(evt), Git()
        out = process_event(evt, "Oteryn/Demo", gh, git)
        self.assertEqual(out["result"], "DELETED"); self.assertTrue(out["deleted"])
        self.assertEqual(git.deletes, [("feat/demo", SHA)])

    def test_cross_repo_or_merged_is_not_applicable(self):
        for evt in [event("Branch-Disposition: delete\nBranch-Disposition-Reason: old", head_repo="fork/repo"), event("Branch-Disposition: delete\nBranch-Disposition-Reason: old", merged=True)]:
            git = Git(); self.assertEqual(process_event(evt, "Oteryn/Demo", GH(), git)["result"], "NOT_APPLICABLE"); self.assertEqual(git.deletes, [])

    def test_sha_or_live_identity_drift_blocks(self):
        evt = self.delete_event()
        with self.assertRaisesRegex(CleanupError, "head SHA drift"):
            process_event(evt, "Oteryn/Demo", GH(evt), Git("b" * 40))
        changed = self.delete_event(); changed["pull_request"]["head"]["sha"] = "b" * 40
        gh = GH(evt); gh.evt = changed
        with self.assertRaisesRegex(CleanupError, "live pull request identity drift"):
            process_event(evt, "Oteryn/Demo", gh, Git())

    def test_protected_open_default_and_reserved_are_blocked(self):
        evt = self.delete_event()
        cases = [
            (evt, GH(evt, protected=True), "protected"),
            (evt, GH(evt, open_pulls=[{"number": 9}]), "open pull request"),
            (self.delete_event("main"), GH(self.delete_event("main"), default="main"), "default branch"),
            (self.delete_event("rollback/last-good"), GH(self.delete_event("rollback/last-good")), "recovery-sensitive"),
        ]
        for candidate, gh, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(CleanupError, message):
                process_event(candidate, "Oteryn/Demo", gh, Git())

    def test_absent_is_idempotent(self):
        evt = self.delete_event(); out = process_event(evt, "Oteryn/Demo", GH(evt), Git(None))
        self.assertEqual(out["result"], "ALREADY_ABSENT"); self.assertFalse(out["deleted"])

    def test_cli_evidence_and_blocked_error(self):
        for body, code, expected in [
            ("Branch-Disposition: delete\nBranch-Disposition-Reason: superseded", 0, "DELETED"),
            ("Branch-Disposition: delete", 1, "BLOCKED"),
        ]:
            evt = event(body); gh, git = GH(evt), Git()
            with tempfile.TemporaryDirectory() as td:
                ep, op = pathlib.Path(td) / "event.json", pathlib.Path(td) / "out.json"
                ep.write_text(json.dumps(evt), encoding="utf-8")
                self.assertEqual(run_cli(["--event", str(ep), "--repository", "Oteryn/Demo", "--output", str(op)], github=gh, git=git), code)
                self.assertEqual(json.loads(op.read_text())["result"], expected)


if __name__ == "__main__": unittest.main()
