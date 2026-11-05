"""Display care: Gruvbox + aggressive anti burn-in. Optional /sd/uf2_care.json."""

try:
    import array
    import time
except ImportError:
    array = time = None

# Aggressive defaults (ms) — override via load_config()
_DIM_MS = 30_000
_OFF_MS = 60_000
_DIM = 4
_CHROME_AFTER = 60_000  # hide status quickly
_CHROME_PERIOD = 60_000
_CHROME_HIDE = 50_000  # mostly hidden once session is long
_SHIFT_MS = 120_000  # shift every 2 min
_AUTOSAVE_MS = 300_000  # 5 min (feature #2)

_CFG_PATHS = ("/sd/uf2_care.json", "uf2_care.json", "/uf2_care.json")

_GRUV16 = (
    (40, 40, 40),
    (204, 36, 29),
    (152, 151, 26),
    (215, 153, 33),
    (69, 133, 136),
    (177, 98, 134),
    (104, 157, 106),
    (213, 196, 161),
    (146, 131, 116),
    (251, 73, 52),
    (184, 187, 38),
    (250, 189, 47),
    (131, 165, 152),
    (211, 134, 155),
    (142, 192, 124),
    (235, 219, 178),
)


def _ticks():
    if time and hasattr(time, "ticks_ms"):
        return time.ticks_ms()
    return int((time.time() if time else 0) * 1000)


def _diff(a, b):
    if time and hasattr(time, "ticks_diff"):
        return time.ticks_diff(a, b)
    return a - b


def _rgb565(r, g, b):
    c = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
    return ((c & 0xFF) << 8) | (c >> 8)


def apply_gruvbox(display=None):
    try:
        import picocalc
    except ImportError:
        picocalc = None
    disp = display or (getattr(picocalc, "display", None) if picocalc else None)
    if not disp or not hasattr(disp, "setLUT") or array is None:
        return False
    disp.setLUT(array.array("H", (_rgb565(*c) for c in _GRUV16)))
    return True


def _read_json(path):
    try:
        import ujson as json
    except ImportError:
        import json
    with open(path) as f:
        return json.load(f)


def load_config(path=None):
    """Load care timings from JSON. Keys match module knobs without _ prefix casing."""
    global _DIM_MS, _OFF_MS, _DIM, _CHROME_AFTER, _CHROME_PERIOD
    global _CHROME_HIDE, _SHIFT_MS, _AUTOSAVE_MS
    paths = (path,) if path else _CFG_PATHS
    data = None
    used = None
    for p in paths:
        if not p:
            continue
        try:
            data = _read_json(p)
            used = p
            break
        except Exception:
            continue
    if not data:
        return None
    def g(*keys, default=None):
        for k in keys:
            if k in data:
                return data[k]
        return default

    _DIM_MS = int(g("dim_ms", "idle_dim_ms", default=_DIM_MS))
    _OFF_MS = int(g("off_ms", "idle_off_ms", default=_OFF_MS))
    _DIM = int(g("dim_level", default=_DIM))
    _CHROME_AFTER = int(g("chrome_after_ms", default=_CHROME_AFTER))
    _CHROME_PERIOD = int(g("chrome_period_ms", default=_CHROME_PERIOD))
    _CHROME_HIDE = int(g("chrome_hide_ms", default=_CHROME_HIDE))
    _SHIFT_MS = int(g("shift_ms", default=_SHIFT_MS))
    _AUTOSAVE_MS = int(g("autosave_ms", default=_AUTOSAVE_MS))
    if "enabled" in data:
        care.enabled = bool(data["enabled"])
    return used


def settings():
    return {
        "dim_ms": _DIM_MS,
        "off_ms": _OFF_MS,
        "dim_level": _DIM,
        "chrome_after_ms": _CHROME_AFTER,
        "chrome_period_ms": _CHROME_PERIOD,
        "chrome_hide_ms": _CHROME_HIDE,
        "shift_ms": _SHIFT_MS,
        "autosave_ms": _AUTOSAVE_MS,
        "enabled": care.enabled,
    }


class Care:
    def __init__(self):
        t = _ticks()
        self.last_input = self.session_start = t
        self.blanked = self.dimmed = False
        self._bkl = 20
        self._kb = None
        self.enabled = True

    def bind(self, keyboard):
        self._kb = keyboard

    def note(self):
        self.last_input = _ticks()
        if self.blanked or self.dimmed:
            self._backlight(self._bkl or 20)
            self.blanked = self.dimmed = False

    def chrome_visible(self):
        if not self.enabled:
            return True
        age = _diff(_ticks(), self.session_start)
        if age < _CHROME_AFTER:
            return True
        # Prefer hidden: only show briefly each period
        return (age % _CHROME_PERIOD) >= _CHROME_HIDE

    def pixel_shift(self):
        if not self.enabled or _SHIFT_MS <= 0:
            return 0
        return (_diff(_ticks(), self.session_start) // _SHIFT_MS) % 2

    def autosave_due(self, last_save_ticks):
        if _AUTOSAVE_MS <= 0:
            return False
        return _diff(_ticks(), last_save_ticks) >= _AUTOSAVE_MS

    def _backlight(self, level):
        kb = self._kb
        if kb is None:
            try:
                import picocalc

                kb = getattr(picocalc, "keyboard", None)
            except ImportError:
                return
        if not kb or not hasattr(kb, "setBacklight"):
            return
        try:
            if not self.dimmed and not self.blanked and hasattr(kb, "backlight"):
                self._bkl = kb.backlight()
            kb.setBacklight(max(0, min(255, int(level))))
        except Exception:
            pass

    def tick(self):
        if not self.enabled:
            return
        idle = _diff(_ticks(), self.last_input)
        if idle >= _OFF_MS:
            if not self.blanked:
                self._backlight(0)
                self.blanked = self.dimmed = True
        elif idle >= _DIM_MS:
            if not self.dimmed:
                self._backlight(_DIM)
                self.dimmed = True


care = Care()


def note_input():
    care.note()


def tick():
    care.tick()


def chrome_visible():
    return care.chrome_visible()


def pixel_shift():
    return care.pixel_shift()


def autosave_ms():
    return _AUTOSAVE_MS
