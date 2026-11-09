"""Editor find / n-N navigation (lightweight, no full TUI)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from harness import install_mocks, setup_firmware_path


class FakeIO:
    def wr(self, s):
        pass

    def rd(self, timeout_ms=None):
        return None

    def rd_raw(self):
        return "\x00"


class FindTests(unittest.TestCase):
    def setUp(self):
        setup_firmware_path()
        install_mocks(reset_hardware=False)
        # pye pulls in highlighter / styles
        import importlib

        for name in ("default_style", "highlighter", "colorer", "pye"):
            if name in sys.modules:
                importlib.reload(sys.modules[name])
        import pye

        self.pye = pye
        self.ed = pye.Editor(tab_size=4, undo_limit=8, io_device=FakeIO())
        self.ed.content = ["alpha foo", "bar foo baz", "foo end"]
        self.ed.total_lines = 3
        self.ed.cur_line = 0
        self.ed.col = 0
        pye.Editor.find_pattern = ""
        pye.Editor.case = "n"
        pye.Editor.height = 10

    def test_forward_and_nav_flag(self):
        n = self.ed.find_in_file("foo", 0, 3)
        self.assertEqual(n, 3)
        self.assertEqual(self.ed.cur_line, 0)
        self.assertEqual(self.ed.col, 6)
        self.assertTrue(self.ed.find_nav)
        self.ed.find_in_file("foo", self.ed.col + 1, 3)
        self.assertEqual(self.ed.cur_line, 1)
        self.assertEqual(self.ed.col, 4)

    def test_backwards(self):
        self.ed.cur_line = 2
        self.ed.col = 3
        n = self.ed.find_in_file("foo", self.ed.col, 0, backwards=True)
        self.assertEqual(n, 3)
        self.assertEqual(self.ed.cur_line, 2)
        self.assertEqual(self.ed.col, 0)
        n = self.ed.find_in_file("foo", self.ed.col, 0, backwards=True)
        self.assertEqual(self.ed.cur_line, 1)
        self.assertEqual(self.ed.col, 4)


if __name__ == "__main__":
    unittest.main()
