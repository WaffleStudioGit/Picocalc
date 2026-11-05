"""UF2 shell tests."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from host.harness import load_gpio_hw, load_shell  # noqa: E402


class ShellTests(unittest.TestCase):
    def setUp(self):
        load_gpio_hw()
        self.shell = load_shell()
        self.state = {"ns": {}, "hold": None}
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self._old = os.getcwd()
        os.chdir(self.tmp.name)
        self.addCleanup(os.chdir, self._old)

    def _run(self, line, inputs=None):
        buf = StringIO()
        inputs = list(inputs or [])

        def capture(*a, **k):
            buf.write(" ".join(map(str, a)) + k.get("end", "\n"))

        def fake_input(_prompt=""):
            if not inputs:
                raise EOFError
            return inputs.pop(0)

        with mock.patch.object(self.shell, "print", side_effect=capture):
            with mock.patch("builtins.print", side_effect=capture):
                with mock.patch("builtins.input", side_effect=fake_input):
                    cont = self.shell.handle_line(line, self.state)
        return buf.getvalue(), cont

    def test_help_status_browse(self):
        out, _ = self._run("help")
        self.assertIn("browse", out)
        self.assertIn("jump", out)
        self.assertIn("status", out)
        Path("a.py").write_text("x=1\n")
        out, _ = self._run("browse", inputs=["1"])
        # edit unavailable without picocalc
        self.assertTrue("1 a.py" in out or "unavailable" in out or "a.py" in out)
        out, _ = self._run("status")
        self.assertIn("PicoCalc UF2", out)

    def test_run_error_jump(self):
        Path("bad.py").write_text("raise ValueError('x')\n")
        out, _ = self._run("run bad.py")
        self.assertTrue("jump" in out.lower() or "ValueError" in out or "err" in out.lower() or "bad" in out)
        import errjump

        # record should have set something
        self.assertTrue(errjump.LAST.get("msg"))
        out, _ = self._run("jump")
        self.assertTrue("open" in out or "no error" in out or "unavailable" in out)

    def test_gpio_servo(self):
        self._run("high 21")
        self.assertEqual(sys.modules["machine"].Pin.registry[21].value(), 1)
        out, _ = self._run("servo 21 90")
        self.assertIn("ok", out)

    def test_quit(self):
        _, cont = self._run("quit")
        self.assertFalse(cont)


if __name__ == "__main__":
    unittest.main()
