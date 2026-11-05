"""Validate sample apps compile and run against mocked hardware (no upload)."""

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


class AppSourceTests(unittest.TestCase):
    def test_all_apps_parse(self):
        apps = sorted(APPS.glob("*.py"))
        self.assertTrue(apps, "expected sample apps")
        for path in apps:
            src = path.read_text(encoding="utf-8")
            try:
                ast.parse(src, filename=str(path))
            except SyntaxError as e:
                self.fail("%s: %s" % (path.name, e))

    def test_apps_import_gpio_hw(self):
        for path in APPS.glob("*.py"):
            src = path.read_text(encoding="utf-8")
            self.assertIn(
                "gpio_hw",
                src,
                msg="%s should use gpio_hw" % path.name,
            )


class AppExecutionTests(unittest.TestCase):
    def setUp(self):
        self.gpio = load_gpio_hw()
        setup_firmware_path()

    def test_hello_gpio_runs(self):
        path = APPS / "hello_gpio.py"
        ns = {
            "__name__": "__main__",
            "__file__": str(path),
            "gpio_hw": self.gpio,
        }
        # Patch time.sleep so the script is instant
        with mock.patch("time.sleep", return_value=None):
            # Ensure imports inside the script resolve to our loaded gpio_hw
            sys.modules["gpio_hw"] = self.gpio
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = compile(path.read_text(encoding="utf-8"), str(path), "exec")
                exec(code, ns, ns)
            out = buf.getvalue()
        self.assertIn("PicoCalc UF2 GPIO demo", out)
        self.assertIn("done", out)
        machine = sys.modules["machine"]
        self.assertIn(21, machine.Pin.registry)

    def test_blink_finite_with_interrupt(self):
        path = APPS / "blink_header.py"
        sys.modules["gpio_hw"] = self.gpio
        machine = sys.modules["machine"]

        sleeps = {"n": 0}

        def sleep(_t):
            sleeps["n"] += 1
            if sleeps["n"] >= 4:
                raise KeyboardInterrupt

        ns = {"__name__": "__main__", "__file__": str(path)}
        with mock.patch("time.sleep", side_effect=sleep):
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = compile(path.read_text(encoding="utf-8"), str(path), "exec")
                exec(code, ns, ns)
        self.assertIn(28, machine.Pin.registry)
        # After KeyboardInterrupt handler, pin should be low
        self.assertEqual(machine.Pin.registry[28].value(), 0)

    def test_servo_sweep_finite(self):
        path = APPS / "servo_sweep.py"
        sys.modules["gpio_hw"] = self.gpio
        machine = sys.modules["machine"]
        sleeps = {"n": 0}

        def sleep(_t):
            sleeps["n"] += 1
            if sleeps["n"] >= 6:
                raise KeyboardInterrupt

        ns = {"__name__": "__main__", "__file__": str(path)}
        with mock.patch("time.sleep", side_effect=sleep):
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = compile(path.read_text(encoding="utf-8"), str(path), "exec")
                exec(code, ns, ns)
            out = buf.getvalue()
        self.assertIn("Pins", out)
        self.assertTrue(machine.PWM.registry)
        self.assertIn("stopped", out)


if __name__ == "__main__":
    unittest.main()
