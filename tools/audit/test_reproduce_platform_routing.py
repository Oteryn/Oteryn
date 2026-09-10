import os
from pathlib import Path
import tempfile
import unittest
from reproduce_platform_routing import write_new


class OutputTests(unittest.TestCase):
    def test_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'result.json';path.write_text('preserve',encoding='utf-8')
            with self.assertRaises(ValueError):write_new(path,'new')
            self.assertEqual(path.read_text(encoding='utf-8'),'preserve')

    def test_dangling_symlink_is_not_followed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);target=root/'target.json';link=root/'result.json'
            try:link.symlink_to(target.name)
            except (OSError,NotImplementedError):self.skipTest('symlink unavailable')
            with self.assertRaises(ValueError):write_new(link,'new')
            self.assertFalse(target.exists())

    def test_symlinked_parent_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);real=root/'real';real.mkdir();link=root/'link'
            try:link.symlink_to(real.name,target_is_directory=True)
            except (OSError,NotImplementedError):self.skipTest('symlink unavailable')
            with self.assertRaises(ValueError):write_new(link/'result.json','new')
            self.assertFalse((real/'result.json').exists())

    def test_new_regular_file_is_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'result.json';write_new(path,'ok\n')
            self.assertEqual(path.read_text(encoding='utf-8'),'ok\n')
            self.assertFalse(path.is_symlink())


if __name__=='__main__':unittest.main()
