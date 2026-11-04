#!/usr/bin/env python3
"""Render sample UFO editor lines with ANSI syntax highlighting."""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "firmware", "frozen"))

from default_style import syntax_style
from highlighter import Highlighter

SAMPLE = """\
# PicoCalc UFO — servo + GPIO sample
from gpio_hw import Servo, GPIO, list_pins

def sweep(pin=21):
    s = Servo(pin)
    for angle in range(0, 181, 10):
        s.write(angle)  # 0..180 degrees
    return True

@property
def ready():
    return None is not False

print(list_pins())
sweep(21)
"""


def main():
    hl = Highlighter(syntax_style=syntax_style)
    print("\x1b[1mPicoCalc UFO editor preview (syntax highlighting)\x1b[0m\n")
    for i, line in enumerate(SAMPLE.splitlines(), 1):
        print(f"\x1b[90m{i:3}\x1b[0m {hl.highlight_line(line)}")
    print()


if __name__ == "__main__":
    main()
