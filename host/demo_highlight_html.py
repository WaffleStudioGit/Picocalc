#!/usr/bin/env python3
"""Write an HTML preview of UFO syntax highlighting for docs/screenshots."""
import html
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "firmware", "frozen"))

from default_style import syntax_style
from highlighter import Highlighter

SAMPLE = """\
# PicoCalc UF2 — servo + GPIO sample
from gpio_hw import Servo, GPIO, list_pins

def sweep(pin=21):
    s = Servo(pin)
    for angle in range(0, 181, 10):
        s.write(angle)  # 0..180 degrees
    return True

print(list_pins())
sweep(21)
"""

# Map a few SGR codes used in default_style to CSS colors (dark editor theme)
_SGR_CSS = {
    "\x1b[37;44m": "color:#e8e8e8;background:#1e3a8a",
    "\x1b[37;45m": "color:#e8e8e8;background:#7e22ce",
    "\x1b[37;46m": "color:#0b1020;background:#22d3ee",
    "\x1b[36m": "color:#22d3ee",
    "\x1b[31m": "color:#f87171",
    "\x1b[35m": "color:#e879f9",
    "\x1b[32m": "color:#4ade80",
    "\x1b[33m": "color:#fbbf24",
    "\x1b[34m": "color:#60a5fa",
}


def ansi_to_html(s):
    out = []
    i = 0
    while i < len(s):
        if s.startswith("\x1b[0m", i):
            out.append("</span>")
            i += 4
            continue
        matched = False
        for code, css in _SGR_CSS.items():
            if s.startswith(code, i):
                out.append(f'<span style="{css}">')
                i += len(code)
                matched = True
                break
        if matched:
            continue
        if s[i] == "\x1b":
            # skip unknown SGR
            m = re.match(r"\x1b\[[0-9;]*m", s[i:])
            if m:
                i += len(m.group(0))
                continue
        out.append(html.escape(s[i]))
        i += 1
    return "".join(out)


def main():
    hl = Highlighter(syntax_style=syntax_style)
    rows = []
    for i, line in enumerate(SAMPLE.splitlines(), 1):
        rows.append(
            f'<div class="line"><span class="ln">{i:3}</span>'
            f'<code>{ansi_to_html(hl.highlight_line(line))}</code></div>'
        )
    doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/>
<title>PicoCalc UF2 — Python editor syntax highlighting</title>
<style>
  body {{ margin:0; background:#0b1020; color:#d6d6d6;
         font: 15px/1.55 "IBM Plex Mono", "Cascadia Code", ui-monospace, monospace; }}
  .wrap {{ max-width: 820px; margin: 2rem auto; padding: 0 1rem; }}
  h1 {{ font: 600 1.4rem/1.2 "IBM Plex Sans", system-ui, sans-serif; color:#f8fafc; }}
  p {{ font: 14px/1.4 "IBM Plex Sans", system-ui, sans-serif; color:#94a3b8; }}
  .editor {{ background:#111827; border:1px solid #1f2937; border-radius:8px;
             padding:1rem 0.75rem; box-shadow: 0 20px 50px rgba(0,0,0,.45); }}
  .line {{ white-space: pre; }}
  .ln {{ display:inline-block; width:3ch; color:#4b5563; margin-right:1ch; user-select:none; }}
  .badge {{ display:inline-block; margin-top:1rem; padding:.25rem .6rem; border:1px solid #334155;
            color:#93c5fd; border-radius:4px; font-size:12px; }}
</style></head><body><div class="wrap">
<h1>PicoCalc UF2 firmware — on-device Python editor</h1>
<p>Syntax highlighting for keywords, strings, comments, numbers, and builtins.
Control servos and GPIO from the same editor via <code>gpio_hw</code>.</p>
<div class="editor">
{''.join(rows)}
</div>
<div class="badge">edit('/apps/servo_sweep.py') · Ctrl-S save · Ctrl-Q quit</div>
</div></body></html>
"""
    out = os.path.join(ROOT, "docs", "editor_preview.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(doc)
    print("wrote", out)


if __name__ == "__main__":
    main()
