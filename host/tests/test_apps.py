"""Sample apps parse and run against mocks."""

from __future__ import annotations

import ast
import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from host.harness import load_gpio_hw, setup_firmware_path  # noqa: E402

APPS = ROOT / "apps"


class AppTests(unittest.TestCase):
    def test_parse_and_hello(self):
        apps = list(APPS.glob("*.py"))
        self.assertTrue(apps)
        for p in apps:
            ast.parse(p.read_text())
            self.assertIn("gpio_hw", p.read_text())

        hw = load_gpio_hw()
        setup_firmware_path()
        sys.modules["gpio_hw"] = hw
        path = APPS / "hello_gpio.py"
        with mock.patch("time.sleep"):
            buf = io.StringIO()
            with redirect_stdout(buf):
                exec(compile(path.read_text(), str(path), "exec"), {"__name__": "__main__"})
        self.assertIn("GPIO demo", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
