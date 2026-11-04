"""
PicoCalc UFO — MicroPython-friendly Python syntax highlighter.

Tokenizes a single line for the on-device editor (pye). Highlights:
  keywords, strings, comments, numbers, builtins, and decorators.
"""

try:
    import micropython
except ImportError:
    class micropython:  # host / CPython shim
        @staticmethod
        def native(f):
            return f


_RESET = "\x1b[0m"

DELIMITERS = " \t\n+-*/=<>()[]{}:,;%&|^~@\"'#"

COMPOUND_DELIMITERS = (
    "==",
    "!=",
    "<=",
    ">=",
    "->",
    "+=",
    "-=",
    "*=",
    "/=",
    "//=",
    "%=",
    "**=",
    "&=",
    "|=",
    "^=",
    "<<",
    ">>",
    "**",
    "//",
    ":=",
)

# Common MicroPython / PicoCalc builtins shown distinctly from keywords.
_BUILTINS = frozenset(
    (
        "abs",
        "all",
        "any",
        "bin",
        "bool",
        "bytearray",
        "bytes",
        "callable",
        "chr",
        "dict",
        "dir",
        "divmod",
        "enumerate",
        "eval",
        "exec",
        "filter",
        "float",
        "format",
        "frozenset",
        "getattr",
        "globals",
        "hasattr",
        "hash",
        "help",
        "hex",
        "id",
        "input",
        "int",
        "isinstance",
        "issubclass",
        "iter",
        "len",
        "list",
        "locals",
        "map",
        "max",
        "memoryview",
        "min",
        "next",
        "object",
        "oct",
        "open",
        "ord",
        "pow",
        "print",
        "property",
        "range",
        "repr",
        "reversed",
        "round",
        "set",
        "setattr",
        "slice",
        "sorted",
        "staticmethod",
        "str",
        "sum",
        "super",
        "tuple",
        "type",
        "zip",
        # Pico / UFO helpers often used at the REPL
        "Pin",
        "PWM",
        "ADC",
        "I2C",
        "SPI",
        "UART",
        "Timer",
        "Servo",
        "GPIO",
    )
)

TOKEN_NORMAL = 0
TOKEN_STRING = 1
TOKEN_NUMBER = 2
TOKEN_BUILTIN = 3
TOKEN_DECORATOR = 4


def _is_digit(ch):
    return "0" <= ch <= "9"


def _is_ident_start(ch):
    return ("a" <= ch <= "z") or ("A" <= ch <= "Z") or ch == "_"


def _is_ident_body(ch):
    return _is_ident_start(ch) or _is_digit(ch)


def _looks_like_number(token):
    if not token:
        return False
    i = 0
    if token[0] in "+-" and len(token) > 1:
        i = 1
    if i >= len(token):
        return False
    # 0x / 0b / 0o
    if token[i] == "0" and i + 1 < len(token) and token[i + 1] in "xXoObB":
        return True
    if not _is_digit(token[i]):
        return False
    # plain int / float / scientific
    for ch in token[i:]:
        if not (_is_digit(ch) or ch in ".eE_+xXoObBabcdefABCDEF"):
            return False
    return True


class Highlighter:
    def __init__(self, syntax_style=None, max_tokens=300):
        self.syntax_style = syntax_style or {}
        self.max_tokens = max_tokens
        self.token_boundaries = bytearray(max_tokens * 2)
        self.token_types = bytearray(max_tokens)

    @micropython.native
    def highlight_line(self, line):
        code_part, comment_part = self._strip_comment(line)
        token_count = self._tokenize(code_part)
        result = self._build_highlighted_output(code_part, token_count)
        if comment_part:
            comment_style = self.syntax_style.get("#", "")
            if comment_style:
                result += comment_style + comment_part + _RESET
            else:
                result += comment_part
        return result

    def _classify_normal(self, token):
        if not token:
            return TOKEN_NORMAL
        if token[0] == "@" and len(token) > 1 and _is_ident_start(token[1]):
            return TOKEN_DECORATOR
        if _looks_like_number(token):
            return TOKEN_NUMBER
        if token in _BUILTINS:
            return TOKEN_BUILTIN
        return TOKEN_NORMAL

    def _tokenize(self, text):
        i = 0
        token_idx = 0
        text_len = len(text)
        in_str = False
        str_char = None
        start_pos = 0

        while i < text_len and token_idx < self.max_tokens:
            char = text[i]
            if in_str:
                if char == str_char and (i == 0 or text[i - 1] != "\\"):
                    in_str = False
                    self.token_boundaries[token_idx * 2] = start_pos
                    self.token_boundaries[token_idx * 2 + 1] = i + 1
                    self.token_types[token_idx] = TOKEN_STRING
                    token_idx += 1
                    start_pos = i + 1
                i += 1
                continue

            if char in "\"'":
                if start_pos < i:
                    tok = text[start_pos:i]
                    self.token_boundaries[token_idx * 2] = start_pos
                    self.token_boundaries[token_idx * 2 + 1] = i
                    self.token_types[token_idx] = self._classify_normal(tok)
                    token_idx += 1
                in_str = True
                str_char = char
                start_pos = i
                i += 1
                continue

            # Longest-match compound operators (3 then 2 chars)
            is_compound = False
            for width in (3, 2):
                if i + width <= text_len:
                    possible = text[i : i + width]
                    if possible in COMPOUND_DELIMITERS:
                        if start_pos < i:
                            tok = text[start_pos:i]
                            self.token_boundaries[token_idx * 2] = start_pos
                            self.token_boundaries[token_idx * 2 + 1] = i
                            self.token_types[token_idx] = self._classify_normal(tok)
                            token_idx += 1
                        self.token_boundaries[token_idx * 2] = i
                        self.token_boundaries[token_idx * 2 + 1] = i + width
                        self.token_types[token_idx] = TOKEN_NORMAL
                        token_idx += 1
                        start_pos = i + width
                        i += width
                        is_compound = True
                        break
            if is_compound:
                continue

            if char in DELIMITERS:
                if start_pos < i:
                    tok = text[start_pos:i]
                    self.token_boundaries[token_idx * 2] = start_pos
                    self.token_boundaries[token_idx * 2 + 1] = i
                    self.token_types[token_idx] = self._classify_normal(tok)
                    token_idx += 1

                self.token_boundaries[token_idx * 2] = i
                self.token_boundaries[token_idx * 2 + 1] = i + 1
                self.token_types[token_idx] = TOKEN_NORMAL
                token_idx += 1
                start_pos = i + 1
                i += 1
                continue

            i += 1

        if start_pos < text_len and token_idx < self.max_tokens:
            tok = text[start_pos:text_len]
            self.token_boundaries[token_idx * 2] = start_pos
            self.token_boundaries[token_idx * 2 + 1] = text_len
            self.token_types[token_idx] = self._classify_normal(tok)
            token_idx += 1

        return token_idx

    def _style_for_token(self, token, token_type):
        if token_type == TOKEN_STRING:
            return self.syntax_style.get("string", "")
        if token_type == TOKEN_NUMBER:
            return self.syntax_style.get("number", "")
        if token_type == TOKEN_BUILTIN:
            return self.syntax_style.get("builtin", "")
        if token_type == TOKEN_DECORATOR:
            return self.syntax_style.get("decorator", "")
        return self.syntax_style.get(token, "")

    def _build_highlighted_output(self, text, token_count):
        result = ""
        for i in range(token_count):
            start = self.token_boundaries[i * 2]
            end = self.token_boundaries[i * 2 + 1]
            token = text[start:end]
            token_type = self.token_types[i]
            style = self._style_for_token(token, token_type)
            if style:
                result += style + token + _RESET
            else:
                result += token
        return result

    def _strip_comment(self, line):
        in_str = False
        esc = False
        quote = None

        for i, ch in enumerate(line):
            if esc:
                esc = False
                continue
            if ch == "\\":
                esc = True
                continue
            if ch in ("'", '"'):
                if not in_str:
                    in_str, quote = True, ch
                elif ch == quote:
                    in_str = False
            elif ch == "#" and not in_str:
                return line[:i], line[i:]

        return line, ""
