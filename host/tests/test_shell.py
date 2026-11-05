"""Host tests for the UF2 interactive shell (no device upload)."""

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


class ShellCommandTests(unittest.TestCase):
    def setUp(self):
        self.gpio = load_gpio_hw()
        self.shell = load_shell()
        self.state = {"ns": {}, "hold": None}
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.cwd = self._tmpdir.name
        self._old = os.getcwd()
        os.chdir(self.cwd)
        self.addCleanup(os.chdir, self._old)

    def _run(self, line: str):
        buf = StringIO()

        def capture(*a, **k):
            sep = k.get("sep", " ")
            end = k.get("end", "\n")
            buf.write(sep.join(map(str, a)) + end)

        with mock.patch.object(self.shell, "print", side_effect=capture):
            cont = self.shell.handle_line(line, self.state)
        return buf.getvalue(), cont

    def test_help(self):
        out, cont = self._run("help")
        self.assertTrue(cont)
        self.assertIn("edit", out)
        self.assertIn("servo", out)

    def test_pins(self):
        out, cont = self._run("pins")
        self.assertTrue(cont)
        self.assertIn("21", out)
        self.assertIn("28", out)

    def test_pwd_cd_ls_cat(self):
        Path(self.cwd, "note.txt").write_text("hello uf2\n", encoding="utf-8")
        out, _ = self._run("pwd")
        self.assertIn(self.cwd, out)
        out, _ = self._run("ls")
        self.assertIn("note.txt", out)
        out, _ = self._run("cat note.txt")
        self.assertIn("hello uf2", out)

    def test_quit_returns_false(self):
        out, cont = self._run("quit")
        self.assertFalse(cont)
        self.assertIn("REPL", out)

    def test_unknown_command(self):
        out, cont = self._run("blorp")
        self.assertTrue(cont)
        self.assertIn("Unknown command", out)

    def test_python_eval_expression(self):
        out, cont = self._run("1 + 2")
        self.assertTrue(cont)
        self.assertIn("3", out)

    def test_python_eval_with_gpio(self):
        out, cont = self._run("Servo(21).pin_num")
        self.assertTrue(cont)
        self.assertIn("21", out)

    def test_high_low_drives_pin(self):
        machine = sys.modules["machine"]
        out, _ = self._run("high 21")
        self.assertIn("GP21", out)
        self.assertEqual(machine.Pin.registry[21].value(), 1)
        out, _ = self._run("low 21")
        self.assertEqual(machine.Pin.registry[21].value(), 0)

    def test_servo_command(self):
        machine = sys.modules["machine"]
        out, _ = self._run("servo 21 90")
        self.assertIn("90", out)
        self.assertTrue(machine.PWM.registry)
        pwm = machine.PWM.registry[-1]
        self.assertEqual(pwm.freq(), 50)
        # ~1500 us at 20ms period
        expected = int(1500 * 65535 / 20000)
        self.assertAlmostEqual(pwm.duty_u16(), expected, delta=2)

    def test_servo_rejects_bad_pin(self):
        out, _ = self._run("servo 6 90")
        self.assertIn("servo failed", out)

    def test_run_script(self):
        script = Path(self.cwd, "demo.py")
        script.write_text(
            "from gpio_hw import Servo\n"
            "s = Servo(21)\n"
            "s.write(45)\n"
            "MARKER = s.read()\n",
            encoding="utf-8",
        )
        out, _ = self._run("run demo.py")
        self.assertIn("Running", out)
        # side effect on hardware mock
        machine = sys.modules["machine"]
        self.assertTrue(machine.PWM.registry)

    def test_edit_without_picocalc(self):
        # picocalc is None on host
        out, _ = self._run("edit demo.py")
        self.assertIn("Editor not bound", out)

    def test_edit_with_stub_picocalc(self):
        calls = []

        def fake_edit(path):
            calls.append(path)

        self.shell.picocalc = SimpleNamespace(edit=fake_edit)
        out, _ = self._run("edit /apps/x.py")
        self.assertEqual(calls, ["/apps/x.py"])
        self.assertIn("Opening editor", out)
        self.shell.picocalc = None

    def test_mem_on_cpython(self):
        out, _ = self._run("mem")
        self.assertIn("RAM free", out)

    def test_new_creates_file_and_opens_editor(self):
        calls = []
        self.shell.picocalc = SimpleNamespace(edit=lambda p: calls.append(p))
        path = str(Path(self.cwd, "untitled.py"))
        out, _ = self._run("new " + path)
        self.assertTrue(Path(path).exists())
        self.assertEqual(calls, [path])
        text = Path(path).read_text(encoding="utf-8")
        self.assertIn("gpio_hw", text)
        self.shell.picocalc = None


if __name__ == "__main__":
    unittest.main()
