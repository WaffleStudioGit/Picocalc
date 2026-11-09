"""Soft Ctrl-C / breakable sleep tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from harness import install_mocks, load_module, setup_firmware_path


class FakeKB:
    def __init__(self, keys=b""):
        self._keys = bytearray(keys)

    def readinto(self, buf):
        if not self._keys:
            return None
        n = min(len(buf), len(self._keys))
        for i in range(n):
            buf[i] = self._keys[i]
        del self._keys[:n]
        return n

    def push(self, data):
        self._keys.extend(data)


class SoftBreakTests(unittest.TestCase):
    def setUp(self):
        setup_firmware_path()
        install_mocks()
        self.sb = load_module("softbreak")
        self.sb.disarm()
        self.kb = FakeKB()
        fake_pc = mock.MagicMock()
        fake_pc.keyboard = self.kb
        sys.modules["picocalc"] = fake_pc

    def tearDown(self):
        self.sb.disarm()

    def test_check_raises_on_ctrl_c(self):
        self.sb.arm()
        self.kb.push(b"\x03")
        with self.assertRaises(KeyboardInterrupt):
            self.sb.check()

    def test_sleep_interrupted(self):
        self.sb.arm()
        self.kb.push(b"\x03")
        with self.assertRaises(KeyboardInterrupt):
            self.sb.sleep(1.0)

    def test_disarm_restores_sleep(self):
        import time

        orig = time.sleep
        self.sb.arm()
        self.assertIsNot(time.sleep, orig)
        self.sb.disarm()
        self.assertIs(time.sleep, orig)

    def test_run_guarded_ok(self):
        out = []

        def fn():
            out.append(1)
            return 42

        self.assertEqual(self.sb.run_guarded(fn), 42)
        self.assertEqual(out, [1])
        self.assertFalse(self.sb._armed)


if __name__ == "__main__":
    unittest.main()
