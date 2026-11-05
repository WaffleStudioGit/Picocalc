"""
PicoCalc UF2 — Gruvbox-leaning syntax styles (VT100 / 16-color).

Foreground-only SGR (no bright keyword backgrounds) so long edit sessions
do not stamp colored blocks into the panel. Works with theme.apply_gruvbox().
"""

# Mapped onto the Gruvbox LUT installed at boot (see theme.py).
syntax_style = {
    # Definitions / imports — yellow / orange family
    "def": "\x1b[33m",
    "class": "\x1b[33m",
    "lambda": "\x1b[33m",
    "import": "\x1b[33m",
    "from": "\x1b[33m",
    "as": "\x1b[33m",
    "global": "\x1b[33m",
    "nonlocal": "\x1b[33m",
    # Control flow — purple
    "if": "\x1b[35m",
    "elif": "\x1b[35m",
    "else": "\x1b[35m",
    "while": "\x1b[35m",
    "for": "\x1b[35m",
    "in": "\x1b[35m",
    "match": "\x1b[35m",
    "case": "\x1b[35m",
    "try": "\x1b[35m",
    "except": "\x1b[35m",
    "finally": "\x1b[35m",
    "with": "\x1b[35m",
    "and": "\x1b[35m",
    "or": "\x1b[35m",
    "not": "\x1b[35m",
    "is": "\x1b[35m",
    # Returns / jumps — red
    "return": "\x1b[31m",
    "yield": "\x1b[31m",
    "raise": "\x1b[31m",
    "pass": "\x1b[31m",
    "break": "\x1b[31m",
    "continue": "\x1b[31m",
    "await": "\x1b[31m",
    "async": "\x1b[31m",
    "assert": "\x1b[31m",
    "del": "\x1b[31m",
    # Literals
    "True": "\x1b[32m",
    "False": "\x1b[31m",
    "None": "\x1b[35m",
    # Special token classes
    "#": "\x1b[32m",  # comments — muted green
    "string": "\x1b[36m",  # aqua
    "number": "\x1b[35m",
    "builtin": "\x1b[34m",
    "decorator": "\x1b[35m",
    "multiline": "\x1b[32m",
}
