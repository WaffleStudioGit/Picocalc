"""Host tests for anti burn-in / display care and Gruvbox theme helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from host.harness import setup_firmware_path, install_mocks  # noqa: E402


class FakeKeyboard:
    def __init__(self, level=40):
        self.level = level

    def backlight(self):
        return self.level

    def setBacklight(self, value):
        self.level = int(value)


class BurninTests(unittest.TestCase):
    def setUp(self):
        setup_firmware_path()
        install_mocks(reset_hardware=False)
        import importlib

        if "burnin" in sys.modules:
            self.burnin = importlib.reload(sys.modules["burnin"])
        else:
            self.burnin = importlib.import_module("burnin")
        self.kb = FakeKeyboard(40)
        self.burnin.care.bind_keyboard(self.kb)
        self.burnin.care.configure(
            idle_dim_ms=1_000,
            idle_off_ms=2_000,
            dim_level=5,
            session_chrome_after_ms=5_000,
            chrome_period_ms=1_000,
            chrome_hidden_ms=400,
            shift_period_ms=1_000,
            enabled=True,
        )
        self.burnin.care.session_start = 0
        self.burnin.care.last_input = 0
        self.burnin.care.blanked = False
        self.burnin.care.dimmed = False
        self.burnin.care._saved_bkl = 40

    def test_chrome_visible_early_session(self):
        with mock.patch.object(self.burnin, "_ticks", return_value=100):
            self.burnin.care.session_start = 0
            self.assertTrue(self.burnin.care.chrome_visible())

    def test_chrome_hides_on_long_session(self):
        # session > 5s, phase in hidden window (0..400 of 1000)
        with mock.patch.object(self.burnin, "_ticks", return_value=5_100):
            self.burnin.care.session_start = 0
            self.assertFalse(self.burnin.care.chrome_visible())
        with mock.patch.object(self.burnin, "_ticks", return_value=5_700):
            self.burnin.care.session_start = 0
            self.assertTrue(self.burnin.care.chrome_visible())

    def test_pixel_shift_toggles(self):
        with mock.patch.object(self.burnin, "_ticks", return_value=500):
            self.burnin.care.session_start = 0
            self.assertEqual(self.burnin.care.pixel_shift(), 0)
        with mock.patch.object(self.burnin, "_ticks", return_value=1_500):
            self.burnin.care.session_start = 0
            self.assertEqual(self.burnin.care.pixel_shift(), 1)

    def test_idle_dims_then_blanks(self):
        self.burnin.care.last_input = 0
        with mock.patch.object(self.burnin, "_ticks", return_value=1_500):
            self.burnin.care.tick()
            self.assertTrue(self.burnin.care.dimmed)
            self.assertEqual(self.kb.level, 5)
        with mock.patch.object(self.burnin, "_ticks", return_value=2_500):
            self.burnin.care.tick()
            self.assertTrue(self.burnin.care.blanked)
            self.assertEqual(self.kb.level, 0)

    def test_input_restores_backlight(self):
        self.burnin.care.last_input = 0
        with mock.patch.object(self.burnin, "_ticks", return_value=3_000):
            self.burnin.care.tick()
            self.assertTrue(self.burnin.care.blanked)
        with mock.patch.object(self.burnin, "_ticks", return_value=3_100):
            self.burnin.care.note_input()
            self.assertFalse(self.burnin.care.blanked)
            self.assertEqual(self.kb.level, 40)


class ThemeTests(unittest.TestCase):
    def setUp(self):
        setup_firmware_path()
        import importlib

        if "theme" in sys.modules:
            self.theme = importlib.reload(sys.modules["theme"])
        else:
            self.theme = importlib.import_module("theme")

    def test_lut_has_16_entries(self):
        lut = self.theme.gruvbox_lut16()
        self.assertEqual(len(lut), 16)

    def test_rgb565_swapped_roundtrip_shape(self):
        c = self.theme.rgb565_swapped(40, 40, 40)
        self.assertIsInstance(c, int)
        self.assertTrue(0 <= c <= 0xFFFF)

    def test_apply_gruvbox_with_stub_display(self):
        class Disp:
            def __init__(self):
                self.lut = None

            def setLUT(self, lut):
                self.lut = lut

        d = Disp()
        self.assertTrue(self.theme.apply_gruvbox(d))
        self.assertIsNotNone(d.lut)
        self.assertGreaterEqual(len(d.lut), 16)


class StyleGruvboxTests(unittest.TestCase):
    def test_no_background_highlights(self):
        """Burn-in friendly: styles should be foreground-only (no 4xm backgrounds)."""
        setup_firmware_path()
        import importlib

        style = (
            importlib.reload(sys.modules["default_style"])
            if "default_style" in sys.modules
            else importlib.import_module("default_style")
        )
        for key, val in style.syntax_style.items():
            self.assertNotIn(";4", val, msg="%s uses a background color" % key)
            self.assertTrue(val.startswith("\x1b["), msg=key)


if __name__ == "__main__":
    unittest.main()
