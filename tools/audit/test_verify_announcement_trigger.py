from pathlib import Path
import tempfile
import unittest
from verify_announcement_trigger import paths_for_event, matches, verify

TEXT="on:\n  pull_request:\n    paths:\n      - 'app/Announcements/**'\n      - 'test.txt'\n  push:\n    paths:\n      - 'other.txt'\n"
class Tests(unittest.TestCase):
    def test_event_lists_do_not_bleed(self):
        self.assertEqual(paths_for_event(TEXT,'pull_request'),['app/Announcements/**','test.txt'])
        self.assertEqual(paths_for_event(TEXT,'push'),['other.txt'])
    def test_exact_and_prefix(self):
        self.assertTrue(matches('app/Announcements/Q.php','app/Announcements/**'))
        self.assertFalse(matches('lang/en/public.php','app/Announcements/**'))
        self.assertTrue(matches('test.txt','test.txt'))
        self.assertFalse(matches('other/test.txt','test.txt'))
    def test_unsupported_general_globs_are_not_guessed(self):
        for pattern in ['!lang/**','lang/?/*.php','[a-z]/**','lang/*/public.php']:
            with self.assertRaises(ValueError):matches('lang/en/public.php',pattern)
    def test_missing_or_duplicate_event_is_rejected(self):
        for text in ['',TEXT+TEXT]:
            with self.assertRaises(ValueError): paths_for_event(text,'push')
    def test_unknown_event_is_not_silent_no_selection(self):
        with self.assertRaises(ValueError): paths_for_event(TEXT,'merge_group')
    def test_wrong_source_fails_before_any_interpretation(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'.github/workflows';p.mkdir(parents=True);(p/'announcements-acceptance.yml').write_text(TEXT)
            with self.assertRaisesRegex(ValueError,'wrong source'):verify(Path(tmp))
if __name__=='__main__':unittest.main()
