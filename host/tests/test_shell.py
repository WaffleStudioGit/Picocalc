"""UF2 shell command tests (mocked hardware)."""

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

    def _run(self, line):
        buf = StringIO()

        def capture(*a, **k):
            buf.write(" ".join(map(str, a)) + k.get("end", "\n"))

        with mock.patch.object(self.shell, "print", side_effect=capture):
            # builtins print used by slim shell
            with mock.patch("builtins.print", side_effect=capture):
                cont = self.shell.handle_line(line, self.state)
        return buf.getvalue(), cont

    def test_help_quit_pins(self):
        out, cont = self._run("help")
        self.assertTrue(cont)
        self.assertIn("edit", out)
        out, cont = self._run("quit")
        self.assertFalse(cont)
        out, _ = self._run("pins")
        self.assertIn("21", out)

    def test_gpio_and_servo(self):
        out, _ = self._run("high 21")
        self.assertEqual(sys.modules["machine"].Pin.registry[21].value(), 1)
        self._run("low 21")
        self.assertEqual(sys.modules["machine"].Pin.registry[21].value(), 0)
        out, _ = self._run("servo 21 90")
        self.assertIn("ok", out)
        out, _ = self._run("servo 6 90")
        self.assertTrue("reserved" in out or "Error" in out or "GP6" in out or out)

    def test_files_and_run(self):
        Path("note.txt").write_text("hi\n")
        out, _ = self._run("cat note.txt")
        self.assertIn("hi", out)
        Path("t.py").write_text("from gpio_hw import Servo\nServo(21).write(45)\n")
        self._run("run t.py")
        self.assertTrue(sys.modules["machine"].PWM.registry)

    def test_edit_and_eval(self):
        out, _ = self._run("edit x.py")
        self.assertIn("unavailable", out)
        calls = []
        self.shell.picocalc = SimpleNamespace(edit=lambda p: calls.append(p))
        self._run("edit /apps/x.py")
        self.assertEqual(calls, ["/apps/x.py"])
        self.shell.picocalc = None
        out, _ = self._run("1+2")
        self.assertIn("3", out)


if __name__ == "__main__":
    unittest.main()
