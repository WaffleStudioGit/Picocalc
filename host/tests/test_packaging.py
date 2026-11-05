"""Firmware layout sanity checks."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FROZEN = ROOT / "firmware" / "frozen"

REQUIRED = {
    "boot.py",
    "main.py",
    "gpio_hw.py",
    "uf2_shell.py",
    "care.py",
    "highlighter.py",
    "default_style.py",
    "pye.py",
    "picocalc.py",
    "vt.py",
}


class PackagingTests(unittest.TestCase):
    def test_core_files(self):
        names = {p.name for p in FROZEN.glob("*.py")}
        self.assertEqual(REQUIRED - names, set())
        self.assertTrue((ROOT / "firmware" / "c_modules" / "picocalcdisplay" / "picocalcdisplay.c").is_file())
        for tool in ("build_uf2.sh", "pack_sdcard.sh", "run_tests.sh"):
            self.assertTrue((ROOT / "tools" / tool).is_file())
        self.assertIn("pico1-apps", (ROOT / "sdcard" / "README.md").read_text())
        self.assertIn("uf2_shell", (FROZEN / "main.py").read_text())
        self.assertIn("care", (FROZEN / "boot.py").read_text())


if __name__ == "__main__":
    unittest.main()
