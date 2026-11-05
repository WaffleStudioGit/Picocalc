"""
PicoCalc UFO — Python syntax highlighting styles (VT100 / 16-color terminal).

Colors map to the PicoCalc ILI9488 VT100 LUT used by the on-device editor.
"""

# ANSI SGR fragments. Foreground-only where possible so text stays readable
# on the PicoCalc's dark terminal background.
syntax_style = {
    # Definitions / imports
    "def": "\x1b[37;44m",
    "class": "\x1b[37;45m",
    "lambda": "\x1b[37;44m",
    "import": "\x1b[37;44m",
    "from": "\x1b[37;44m",
    "as": "\x1b[37;44m",
    "global": "\x1b[37;44m",
    "nonlocal": "\x1b[37;44m",
    # Control flow
    "if": "\x1b[37;46m",
    "elif": "\x1b[37;46m",
    "else": "\x1b[37;46m",
    "while": "\x1b[37;46m",
    "for": "\x1b[37;46m",
    "in": "\x1b[37;46m",
    "match": "\x1b[37;46m",
    "case": "\x1b[37;46m",
    "try": "\x1b[37;46m",
    "except": "\x1b[37;46m",
    "finally": "\x1b[37;46m",
    "with": "\x1b[37;46m",
    "and": "\x1b[37;46m",
    "or": "\x1b[37;46m",
    "not": "\x1b[37;46m",
    "is": "\x1b[37;46m",
    # Returns / jumps
    "return": "\x1b[37;45m",
    "yield": "\x1b[37;45m",
    "raise": "\x1b[37;45m",
    "pass": "\x1b[37;45m",
    "break": "\x1b[37;45m",
    "continue": "\x1b[37;45m",
    "await": "\x1b[37;45m",
    "async": "\x1b[37;45m",
    "assert": "\x1b[37;45m",
    "del": "\x1b[37;45m",
    # Literals / constants
    "True": "\x1b[36m",
    "False": "\x1b[31m",
    "None": "\x1b[35m",
    # Special token classes (not keywords)
    "#": "\x1b[32m",
    "string": "\x1b[33m",
    "number": "\x1b[36m",
    "builtin": "\x1b[34m",
    "decorator": "\x1b[35m",
    "multiline": "\x1b[32m",
}
