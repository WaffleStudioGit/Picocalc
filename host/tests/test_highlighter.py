"""Host tests for the UF2 Python syntax highlighter."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from host.harness import load_highlighter_stack  # noqa: E402

RESET = "\x1b[0m"


class HighlighterTests(unittest.TestCase):
    def setUp(self):
        _mod, _style_mod, Highlighter, syntax_style = load_highlighter_stack()
        self.Highlighter = Highlighter
        self.syntax_style = syntax_style
        self.hl = Highlighter(syntax_style=syntax_style, max_tokens=300)

    def test_keyword_def(self):
        out = self.hl.highlight_line("def foo(x):")
        self.assertIn(self.syntax_style["def"], out)
        self.assertIn("foo", out)
        self.assertIn(RESET, out)

    def test_string_and_comment(self):
        out = self.hl.highlight_line('x = "hi"  # note')
        self.assertIn(self.syntax_style["string"], out)
        self.assertIn(self.syntax_style["#"], out)
        self.assertIn("# note", out)

    def test_hash_inside_string_not_comment(self):
        out = self.hl.highlight_line('s = "a#b"')
        self.assertNotIn(self.syntax_style["#"] + "#", out)
        self.assertIn(self.syntax_style["string"], out)

    def test_number(self):
        out = self.hl.highlight_line("n = 42")
        self.assertIn(self.syntax_style["number"], out)

    def test_hex_number(self):
        out = self.hl.highlight_line("n = 0xFF")
        self.assertIn(self.syntax_style["number"], out)

    def test_float_and_scientific(self):
        out = self.hl.highlight_line("x = 3.14 + 1e-3")
        self.assertIn(self.syntax_style["number"], out)

    def test_builtin(self):
        out = self.hl.highlight_line("print(len(xs))")
        self.assertIn(self.syntax_style["builtin"], out)

    def test_decorator_property_builtin(self):
        out = self.hl.highlight_line("@property")
        self.assertTrue(
            self.syntax_style["builtin"] in out or self.syntax_style["decorator"] in out
        )

    def test_true_false_none(self):
        out = self.hl.highlight_line("a = True or False or None")
        self.assertIn(self.syntax_style["True"], out)
        self.assertIn(self.syntax_style["False"], out)
        self.assertIn(self.syntax_style["None"], out)

    def test_control_flow_keywords(self):
        for kw in ("if", "elif", "else", "for", "while", "try", "except", "with"):
            out = self.hl.highlight_line(kw + " x:")
            self.assertIn(self.syntax_style[kw], out, msg=kw)

    def test_import_keywords(self):
        out = self.hl.highlight_line("from gpio_hw import Servo as S")
        self.assertIn(self.syntax_style["from"], out)
        self.assertIn(self.syntax_style["import"], out)
        self.assertIn(self.syntax_style["as"], out)
        self.assertIn(self.syntax_style["builtin"], out)  # Servo

    def test_servo_line_readable(self):
        out = self.hl.highlight_line("s = Servo(21)")
        self.assertIn("Servo", out)
        self.assertIn(self.syntax_style["number"], out)

    def test_compound_operators_do_not_break_tokens(self):
        out = self.hl.highlight_line("if a == b and c != d:")
        self.assertIn(self.syntax_style["if"], out)
        self.assertIn(self.syntax_style["and"], out)

    def test_escaped_quote_in_string(self):
        out = self.hl.highlight_line(r'x = "a\"b"  # c')
        self.assertIn(self.syntax_style["string"], out)
        self.assertIn(self.syntax_style["#"], out)

    def test_style_has_required_keys(self):
        required = {
            "def",
            "class",
            "string",
            "number",
            "builtin",
            "#",
            "True",
            "False",
            "None",
            "return",
            "import",
        }
        missing = required - set(self.syntax_style)
        self.assertEqual(missing, set())


class EditorHighlightIntegrationTests(unittest.TestCase):
    """Ensure pye still wires the highlighter (import-level contract)."""

    def test_pye_imports_highlighter(self):
        from host.harness import setup_firmware_path, install_mocks
        import importlib

        setup_firmware_path()
        install_mocks(reset_hardware=False)
        # pye imports heavy stuff; load source and check bindings without running Editor
        pye_path = ROOT / "firmware" / "frozen" / "pye.py"
        src = pye_path.read_text(encoding="utf-8")
        self.assertIn("from highlighter import Highlighter", src)
        self.assertIn("from default_style import syntax_style", src)
        self.assertIn("highlight_line", src)


if __name__ == "__main__":
    unittest.main()
