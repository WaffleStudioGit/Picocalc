"""Tests for care.py (Gruvbox + anti burn-in)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "firmware" / "frozen"))


class FakeKB:
    def __init__(self, level=40):
        self.level = level

    def backlight(self):
        return self.level

    def setBacklight(self, v):
        self.level = int(v)


class CareTests(unittest.TestCase):
    def setUp(self):
        import importlib
        import care

        self.care = importlib.reload(care)
        # shorten timings via module constants
        self.care._DIM_MS = 1000
        self.care._OFF_MS = 2000
        self.care._CHROME_AFTER = 5000
        self.care._CHROME_PERIOD = 1000
        self.care._CHROME_HIDE = 400
        self.care._SHIFT_MS = 1000
        self.kb = FakeKB()
        self.care.care.bind(self.kb)
        self.care.care.session_start = 0
        self.care.care.last_input = 0
        self.care.care.blanked = self.care.care.dimmed = False
        self.care.care._bkl = 40

    def test_chrome_and_shift(self):
        with mock.patch.object(self.care, "_ticks", return_value=100):
            self.assertTrue(self.care.care.chrome_visible())
            self.assertEqual(self.care.care.pixel_shift(), 0)
        with mock.patch.object(self.care, "_ticks", return_value=5100):
            self.assertFalse(self.care.care.chrome_visible())
        with mock.patch.object(self.care, "_ticks", return_value=1500):
            self.assertEqual(self.care.care.pixel_shift(), 1)

    def test_idle_and_wake(self):
        with mock.patch.object(self.care, "_ticks", return_value=1500):
            self.care.care.tick()
            self.assertEqual(self.kb.level, 8)
        with mock.patch.object(self.care, "_ticks", return_value=2500):
            self.care.care.tick()
            self.assertEqual(self.kb.level, 0)
        with mock.patch.object(self.care, "_ticks", return_value=2600):
            self.care.care.note()
            self.assertEqual(self.kb.level, 40)

    def test_gruvbox_lut(self):
        class D:
            def __init__(self):
                self.lut = None

            def setLUT(self, lut):
                self.lut = lut

        d = D()
        self.assertTrue(self.care.apply_gruvbox(d))
        self.assertEqual(len(d.lut), 16)

    def test_styles_fg_only(self):
        import default_style

        for k, v in default_style.syntax_style.items():
            self.assertNotIn(";4", v, msg=k)


if __name__ == "__main__":
    unittest.main()
