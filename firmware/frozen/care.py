"""Display care: Gruvbox LUT, idle auto-off, chrome hide, 1-col shift."""

try:
    import array
    import time
except ImportError:
    array = time = None

# Idle (ms)
_DIM_MS, _OFF_MS, _DIM = 90_000, 180_000, 8
# Long-session chrome / shift
_CHROME_AFTER, _CHROME_PERIOD, _CHROME_HIDE = 600_000, 90_000, 45_000
_SHIFT_MS = 300_000

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
    lut = array.array("H", (_rgb565(*c) for c in _GRUV16))
    disp.setLUT(lut)
    return True


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
        return (age % _CHROME_PERIOD) >= _CHROME_HIDE

    def pixel_shift(self):
        if not self.enabled:
            return 0
        return (_diff(_ticks(), self.session_start) // _SHIFT_MS) % 2

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
