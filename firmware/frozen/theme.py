"""
PicoCalc UF2 — Gruvbox dark theme (display LUT + helpers).

Foreground-heavy styling (see default_style.py) avoids sticky bright
keyword backgrounds that burn into IPS panels during long edit sessions.
"""

try:
    import array
except ImportError:
    array = None

# Gruvbox dark — classic palette (RGB 0-255)
_GRUV = {
    "bg": (40, 40, 40),  # #282828
    "bg1": (60, 56, 54),
    "bg2": (80, 73, 69),
    "fg": (235, 219, 178),  # #ebdbb2
    "fg1": (213, 196, 161),
    "gray": (146, 131, 116),
    "red": (204, 36, 29),
    "green": (152, 151, 26),
    "yellow": (215, 153, 33),
    "blue": (69, 133, 136),
    "purple": (177, 98, 134),
    "aqua": (104, 157, 106),
    "orange": (214, 93, 14),
    "red_b": (251, 73, 52),
    "green_b": (184, 187, 38),
    "yellow_b": (250, 189, 47),
    "blue_b": (131, 165, 152),
    "purple_b": (211, 134, 155),
    "aqua_b": (142, 192, 124),
}


def rgb565_swapped(r, g, b):
    """RGB888 → PicoCalc display LUT entry (byte-swapped RGB565)."""
    c = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
    return ((c & 0xFF) << 8) | (c >> 8)


def gruvbox_lut16():
    """
    16-entry LUT matching VT100 indices, remapped toward Gruvbox dark.

    Index layout follows common VT / ANSI expectations used by the editor.
    """
    order = (
        "bg",  # 0 black
        "red",
        "green",
        "yellow",
        "blue",
        "purple",
        "aqua",
        "fg1",  # 7 light gray / default fg-ish
        "gray",  # 8 bright black
        "red_b",
        "green_b",
        "yellow_b",
        "blue_b",
        "purple_b",
        "aqua_b",
        "fg",  # 15 white
    )
    vals = [rgb565_swapped(*_GRUV[name]) for name in order]
    if array is None:
        return vals
    return array.array("H", vals)


def apply_gruvbox(display=None):
    """Push Gruvbox LUT onto the PicoCalc display if available."""
    try:
        import picocalc
    except ImportError:
        picocalc = None
    disp = display
    if disp is None and picocalc is not None:
        disp = getattr(picocalc, "display", None)
    if disp is None or not hasattr(disp, "setLUT"):
        return False
    lut = gruvbox_lut16()
    # setLUT accepts up to 256 entries; 16 is enough for GS4 VT mode
    if hasattr(lut, "extend"):
        # pad to keep driver happy if it expects more
        full = array.array("H", lut)
        while len(full) < 16:
            full.append(full[-1])
        disp.setLUT(full)
    else:
        disp.setLUT(lut)
    return True
