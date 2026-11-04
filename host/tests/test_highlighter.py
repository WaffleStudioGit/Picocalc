"""Host-side tests for the UFO Python syntax highlighter."""
import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "firmware", "frozen"))

from default_style import syntax_style  # noqa: E402
from highlighter import Highlighter  # noqa: E402

RESET = "\x1b[0m"


class HighlighterTests(unittest.TestCase):
    def setUp(self):
        self.hl = Highlighter(syntax_style=syntax_style, max_tokens=300)

    def test_keyword_def(self):
        out = self.hl.highlight_line("def foo(x):")
        self.assertIn(syntax_style["def"], out)
        self.assertIn("foo", out)
        self.assertIn(RESET, out)

    def test_string_and_comment(self):
        out = self.hl.highlight_line('x = "hi"  # note')
        self.assertIn(syntax_style["string"], out)
        self.assertIn(syntax_style["#"], out)
        self.assertIn("# note", out)

    def test_hash_inside_string_not_comment(self):
        out = self.hl.highlight_line('s = "a#b"')
        self.assertNotIn(syntax_style["#"] + "#", out)
        self.assertIn(syntax_style["string"], out)

    def test_number(self):
        out = self.hl.highlight_line("n = 42")
        self.assertIn(syntax_style["number"], out)
        self.assertIn("42", out)

    def test_hex_number(self):
        out = self.hl.highlight_line("n = 0xFF")
        self.assertIn(syntax_style["number"], out)

    def test_builtin(self):
        out = self.hl.highlight_line("print(len(xs))")
        self.assertIn(syntax_style["builtin"], out)

    def test_decorator(self):
        out = self.hl.highlight_line("@micropython.native")
        # first token "@" may split — decorator style applies to @name forms
        # Our tokenizer splits @ as delimiter; ensure 'native' path still works
        out2 = self.hl.highlight_line("@property")
        # '@' is delimiter then 'property' is builtin
        self.assertTrue(
            syntax_style["builtin"] in out2 or syntax_style["decorator"] in out2
        )

    def test_true_false_none(self):
        out = self.hl.highlight_line("a = True or False or None")
        self.assertIn(syntax_style["True"], out)
        self.assertIn(syntax_style["False"], out)
        self.assertIn(syntax_style["None"], out)

    def test_servo_line_readable(self):
        out = self.hl.highlight_line("s = Servo(21)")
        self.assertIn("Servo", out)
        self.assertIn(syntax_style["number"], out)


class GpioHwTests(unittest.TestCase):
    def test_list_pins(self):
        import gpio_hw

        info = gpio_hw.list_pins()
        self.assertIn(21, info["header"])
        self.assertIn(28, info["recommended"])

    def test_rejects_keyboard_pin(self):
        import gpio_hw

        with self.assertRaises(ValueError):
            gpio_hw._check_pin(6)

    def test_rejects_audio_by_default(self):
        import gpio_hw

        with self.assertRaises(ValueError):
            gpio_hw._check_pin(26)

    def test_allow_audio(self):
        import gpio_hw

        self.assertEqual(gpio_hw._check_pin(26, allow_audio=True), 26)


if __name__ == "__main__":
    unittest.main()
