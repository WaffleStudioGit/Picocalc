"""Care / config / burn-in tests."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "firmware" / "frozen"))


class FakeKB:
    def __init__(self, level=40):
        self.level = level

    def backlight(self):
        return self.level

    def setBacklight(self, v):
        self.level = int(v)

    def battery(self):
        return 3700


class CareTests(unittest.TestCase):
    def setUp(self):
        import importlib
        import care

        self.care = importlib.reload(care)
        self.care._DIM_MS = 1000
        self.care._OFF_MS = 2000
        self.care._DIM = 4
        self.care._CHROME_AFTER = 5000
        self.care._CHROME_PERIOD = 1000
        self.care._CHROME_HIDE = 800
        self.care._SHIFT_MS = 1000
        self.care._AUTOSAVE_MS = 300000
        self.kb = FakeKB()
        self.care.care.bind(self.kb)
        self.care.care.session_start = 0
        self.care.care.last_input = 0
        self.care.care.blanked = self.care.care.dimmed = False
        self.care.care._bkl = 40
        self.care.care.enabled = True

    def test_aggressive_chrome_mostly_hidden(self):
        with mock.patch.object(self.care, "_ticks", return_value=5500):
            # phase 500 → hidden (hide first 800 of 1000)
            self.assertFalse(self.care.care.chrome_visible())
        with mock.patch.object(self.care, "_ticks", return_value=5900):
            self.assertTrue(self.care.care.chrome_visible())

    def test_idle_off_and_wake(self):
        with mock.patch.object(self.care, "_ticks", return_value=2500):
            self.care.care.tick()
            self.assertEqual(self.kb.level, 0)
        with mock.patch.object(self.care, "_ticks", return_value=2600):
            self.care.care.note()
            self.assertEqual(self.kb.level, 40)

    def test_load_config(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "uf2_care.json"
            path.write_text(
                json.dumps(
                    {
                        "dim_ms": 1111,
                        "off_ms": 2222,
                        "autosave_ms": 300000,
                        "chrome_hide_ms": 900,
                    }
                )
            )
            used = self.care.load_config(str(path))
            self.assertEqual(used, str(path))
            self.assertEqual(self.care._DIM_MS, 1111)
            self.assertEqual(self.care._OFF_MS, 2222)
            self.assertEqual(self.care._AUTOSAVE_MS, 300000)

    def test_autosave_due(self):
        self.care._AUTOSAVE_MS = 1000
        with mock.patch.object(self.care, "_ticks", return_value=2000):
            self.assertTrue(self.care.care.autosave_due(500))
            self.assertFalse(self.care.care.autosave_due(1500))

    def test_styles_fg_only(self):
        import default_style

        for k, v in default_style.syntax_style.items():
            self.assertNotIn(";4", v, msg=k)


class ErrJumpTests(unittest.TestCase):
    def test_parse_and_record(self):
        import importlib
        import errjump

        ej = importlib.reload(errjump)
        ej.clear()

        class E(Exception):
            pass

        # fabricate via record on a real raise
        try:
            raise ValueError("boom")
        except ValueError as e:
            ej.record(e, default_file="apps/x.py")
        # may or may not get line from traceback depending on host format
        self.assertTrue(ej.LAST["msg"])


if __name__ == "__main__":
    unittest.main()
