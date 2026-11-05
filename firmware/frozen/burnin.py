"""
PicoCalc UF2 — practical display care (anti burn-in).

Not a screensaver theme park: dim → blank on idle, periodically hide the
editor status chrome on long sessions, and nudge content by one column so
static UI edges do not sit on the same pixels forever.

Defaults are conservative; tweak via configure().
"""

try:
    import time
except ImportError:
    time = None

# Idle: dim then blank the LCD backlight (milliseconds).
IDLE_DIM_MS = 90_000  # 1.5 min
IDLE_OFF_MS = 180_000  # 3 min
DIM_LEVEL = 8
# Long-session chrome cycling (status line / "sidebar" chrome).
SESSION_CHROME_AFTER_MS = 10 * 60 * 1000  # after 10 min editing
CHROME_PERIOD_MS = 90_000  # 90s cycle
CHROME_HIDDEN_MS = 45_000  # hidden half of each cycle
# Content pixel shift (1 column) to smear static edges.
SHIFT_PERIOD_MS = 5 * 60 * 1000  # every 5 min


def _ticks():
    if time is None:
        return 0
    if hasattr(time, "ticks_ms"):
        return time.ticks_ms()
    return int(time.time() * 1000)


def _diff(now, then):
    if time is not None and hasattr(time, "ticks_diff"):
        return time.ticks_diff(now, then)
    return now - then


class DisplayCare:
    def __init__(self):
        now = _ticks()
        self.last_input = now
        self.session_start = now
        self.blanked = False
        self.dimmed = False
        self._saved_bkl = 20
        self._keyboard = None
        self.enabled = True

    def configure(
        self,
        idle_dim_ms=None,
        idle_off_ms=None,
        dim_level=None,
        session_chrome_after_ms=None,
        chrome_period_ms=None,
        chrome_hidden_ms=None,
        shift_period_ms=None,
        enabled=None,
    ):
        global IDLE_DIM_MS, IDLE_OFF_MS, DIM_LEVEL
        global SESSION_CHROME_AFTER_MS, CHROME_PERIOD_MS, CHROME_HIDDEN_MS
        global SHIFT_PERIOD_MS
        if idle_dim_ms is not None:
            IDLE_DIM_MS = int(idle_dim_ms)
        if idle_off_ms is not None:
            IDLE_OFF_MS = int(idle_off_ms)
        if dim_level is not None:
            DIM_LEVEL = int(dim_level)
        if session_chrome_after_ms is not None:
            SESSION_CHROME_AFTER_MS = int(session_chrome_after_ms)
        if chrome_period_ms is not None:
            CHROME_PERIOD_MS = int(chrome_period_ms)
        if chrome_hidden_ms is not None:
            CHROME_HIDDEN_MS = int(chrome_hidden_ms)
        if shift_period_ms is not None:
            SHIFT_PERIOD_MS = int(shift_period_ms)
        if enabled is not None:
            self.enabled = bool(enabled)

    def bind_keyboard(self, keyboard):
        self._keyboard = keyboard

    def note_input(self):
        self.last_input = _ticks()
        if self.blanked or self.dimmed:
            self._restore_backlight()

    def idle_ms(self):
        return _diff(_ticks(), self.last_input)

    def session_ms(self):
        return _diff(_ticks(), self.session_start)

    def chrome_visible(self):
        """Status / sidebar chrome — hidden for stretches during long sessions."""
        if not self.enabled:
            return True
        if self.session_ms() < SESSION_CHROME_AFTER_MS:
            return True
        phase = self.session_ms() % CHROME_PERIOD_MS
        # Hide for the first CHROME_HIDDEN_MS of each period.
        return phase >= CHROME_HIDDEN_MS

    def pixel_shift(self):
        """0 or 1 column offset to reduce edge burn-in."""
        if not self.enabled or SHIFT_PERIOD_MS <= 0:
            return 0
        return (self.session_ms() // SHIFT_PERIOD_MS) % 2

    def _get_keyboard(self):
        if self._keyboard is not None:
            return self._keyboard
        try:
            import picocalc

            return getattr(picocalc, "keyboard", None)
        except ImportError:
            return None

    def _restore_backlight(self):
        kb = self._get_keyboard()
        if kb is not None and hasattr(kb, "setBacklight"):
            try:
                kb.setBacklight(self._saved_bkl if self._saved_bkl else 20)
            except Exception:
                pass
        self.blanked = False
        self.dimmed = False

    def _set_backlight(self, level):
        kb = self._get_keyboard()
        if kb is None or not hasattr(kb, "setBacklight"):
            return False
        try:
            if not self.dimmed and not self.blanked:
                try:
                    self._saved_bkl = kb.backlight()
                except Exception:
                    self._saved_bkl = 20
            kb.setBacklight(max(0, min(255, int(level))))
            return True
        except Exception:
            return False

    def tick(self):
        """Call from idle wait loops (terminal / editor)."""
        if not self.enabled:
            return
        idle = self.idle_ms()
        if idle >= IDLE_OFF_MS:
            if not self.blanked:
                self._set_backlight(0)
                self.blanked = True
                self.dimmed = True
        elif idle >= IDLE_DIM_MS:
            if not self.dimmed:
                self._set_backlight(DIM_LEVEL)
                self.dimmed = True
        elif self.blanked or self.dimmed:
            self._restore_backlight()


# Module singleton used by vt / pye / shell
care = DisplayCare()


def note_input():
    care.note_input()


def tick():
    care.tick()


def chrome_visible():
    return care.chrome_visible()


def pixel_shift():
    return care.pixel_shift()
