"""Sanity-check firmware packaging layout before any device flash."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FROZEN = ROOT / "firmware" / "frozen"
CMOD = ROOT / "firmware" / "c_modules"


REQUIRED_FROZEN = {
    "boot.py",
    "main.py",
    "gpio_hw.py",
    "uf2_shell.py",
    "highlighter.py",
    "default_style.py",
    "theme.py",
    "burnin.py",
    "pye.py",
    "picocalc.py",
    "vt.py",
    "sdcard.py",
    "colorer.py",
    "picocalc_system.py",
}


class PackagingTests(unittest.TestCase):
    def test_frozen_modules_present(self):
        names = {p.name for p in FROZEN.glob("*.py")}
        missing = REQUIRED_FROZEN - names
        self.assertEqual(missing, set(), "missing frozen modules")

    def test_c_modules_present(self):
        self.assertTrue((CMOD / "picocalcdisplay" / "picocalcdisplay.c").is_file())
        self.assertTrue((CMOD / "vtterminal" / "vtterminal.c").is_file())
        self.assertTrue((ROOT / "firmware" / "micropython.cmake").is_file())
        self.assertTrue((ROOT / "firmware" / "Dockerfile").is_file())

    def test_tools_executable_scripts_exist(self):
        for name in (
            "build_uf2.sh",
            "pack_filesystem.sh",
            "pack_sdcard.sh",
            "run_tests.sh",
        ):
            path = ROOT / "tools" / name
            self.assertTrue(path.is_file(), name)

    def test_sdcard_launcher_tree(self):
        sd = ROOT / "sdcard"
        self.assertTrue((sd / "README.md").is_file())
        self.assertTrue((sd / "pico1-apps").is_dir())
        self.assertTrue((sd / "pico2-apps").is_dir())
        readme = (sd / "README.md").read_text(encoding="utf-8")
        self.assertIn("pico1-apps", readme)
        self.assertIn("pico2-apps", readme)
        self.assertIn("PicoCalc_Python", readme)

    def test_main_starts_uf2_shell(self):
        src = (FROZEN / "main.py").read_text(encoding="utf-8")
        self.assertIn("uf2_shell", src)

    def test_boot_binds_edit_and_gpio(self):
        src = (FROZEN / "boot.py").read_text(encoding="utf-8")
        self.assertIn("pye_edit", src)
        self.assertIn("gpio_hw", src)
        self.assertIn("builtins.edit", src)

    def test_dockerfile_freezes_python_modules(self):
        src = (ROOT / "firmware" / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("USER_C_MODULES", src)
        self.assertIn("uf2_frozen", src)  # build copies frozen tree


if __name__ == "__main__":
    unittest.main()
