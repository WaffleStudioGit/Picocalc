"""Soft Ctrl-C during script run (shell / editor).

Arms a short Timer poll of the PicoCalc keyboard for 0x03 (Ctrl-C),
patches ``time.sleep`` / ``time.sleep_ms`` to be breakable, and exposes
``check()`` for cooperative long loops:

    from softbreak import check
    while True:
        check()
        ...
"""

_armed = False
_pending = False
_timer = None
_orig_sleep = None
_orig_sleep_ms = None


def _do_raise(_arg=None):
    global _pending
    _pending = False
    raise KeyboardInterrupt


def _schedule_raise():
    try:
        import micropython

        sched = getattr(micropython, "schedule", None)
        if callable(sched):
            sched(_do_raise, 0)
            return True
    except Exception:
        pass
    return False


def _ctrl_c_in_buf(buf, n):
    for i in range(n):
        if buf[i] == 3:
            return True
    return False


def poll(_t=None):
    """Check keyboard for Ctrl-C. Safe to call from Timer or sleep chunks."""
    global _pending
    if not _armed or _pending:
        return False
    try:
        import picocalc

        kb = getattr(picocalc, "keyboard", None)
        if kb is None or not hasattr(kb, "readinto"):
            return False
        buf = bytearray(16)
        n = kb.readinto(buf)
        if not n:
            return False
        if _ctrl_c_in_buf(buf, n):
            _pending = True
            _schedule_raise()
            return True
    except Exception:
        return False
    return False


def check():
    """Raise KeyboardInterrupt if Ctrl-C was seen while armed."""
    global _pending
    poll()
    if _pending:
        _pending = False
        raise KeyboardInterrupt


def _raw_sleep_ms(step):
    import time

    if _orig_sleep_ms is not None:
        _orig_sleep_ms(step)
        return
    fn = getattr(time, "sleep_ms", None)
    if fn is not None and fn is not sleep_ms:
        fn(step)
        return
    raw = _orig_sleep if _orig_sleep is not None else time.sleep
    raw(step / 1000.0)


def sleep_ms(ms):
    """Sleep in short chunks, polling for Ctrl-C."""
    left = max(0, int(ms))
    chunk = 50
    while left > 0:
        check()
        step = left if left < chunk else chunk
        _raw_sleep_ms(step)
        left -= step
    check()


def sleep(seconds):
    try:
        ms = int(float(seconds) * 1000.0)
    except Exception:
        ms = 0
    sleep_ms(ms)


def arm():
    """Start Ctrl-C watching for a script run."""
    global _armed, _pending, _timer, _orig_sleep, _orig_sleep_ms
    disarm()
    _armed = True
    _pending = False
    try:
        import time

        _orig_sleep = time.sleep
        _orig_sleep_ms = getattr(time, "sleep_ms", None)

        def _s(s):
            sleep(s)

        time.sleep = _s
        if _orig_sleep_ms is not None:

            def _sms(m):
                sleep_ms(m)

            time.sleep_ms = _sms
    except Exception:
        _orig_sleep = None
        _orig_sleep_ms = None
    try:
        import machine

        Timer = getattr(machine, "Timer", None)
        if Timer is not None:
            try:
                _timer = Timer(-1)
            except Exception:
                _timer = Timer()
            period = getattr(Timer, "PERIODIC", 1)
            _timer.init(period=100, mode=period, callback=poll)
    except Exception:
        _timer = None


def disarm():
    """Stop Ctrl-C watching; restore time.sleep."""
    global _armed, _pending, _timer, _orig_sleep, _orig_sleep_ms
    _armed = False
    _pending = False
    if _timer is not None:
        try:
            _timer.deinit()
        except Exception:
            pass
        _timer = None
    try:
        import time

        if _orig_sleep is not None:
            time.sleep = _orig_sleep
        if _orig_sleep_ms is not None:
            time.sleep_ms = _orig_sleep_ms
    except Exception:
        pass
    _orig_sleep = None
    _orig_sleep_ms = None


def run_guarded(fn):
    """Arm, call fn(), always disarm. Propagates KeyboardInterrupt."""
    arm()
    try:
        return fn()
    finally:
        disarm()
