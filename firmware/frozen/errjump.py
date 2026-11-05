"""Last traceback location for jump-to-error."""

try:
    import sys
except ImportError:
    sys = None

LAST = {"file": None, "line": 0, "msg": ""}


def clear():
    LAST["file"] = None
    LAST["line"] = 0
    LAST["msg"] = ""


def _parse(text, default_file=None):
    file = default_file
    line = 0
    for raw in text.split("\n"):
        s = raw.strip()
        # File "x.py", line N
        if 'File "' in s and ", line " in s:
            try:
                a = s.split('File "', 1)[1]
                file = a.split('"', 1)[0]
                rest = s.split(", line ", 1)[1]
                num = ""
                for ch in rest:
                    if ch.isdigit():
                        num += ch
                    else:
                        break
                if num:
                    line = int(num)
            except Exception:
                pass
    return file, line


def record(exc, default_file=None):
    """Capture exception → LAST; returns formatted text."""
    try:
        from uio import StringIO
    except ImportError:
        try:
            from io import StringIO
        except ImportError:
            StringIO = None
    text = repr(exc)
    if StringIO and sys is not None and hasattr(sys, "print_exception"):
        buf = StringIO()
        try:
            sys.print_exception(exc, buf)
            text = buf.getvalue()
        except Exception:
            pass
    f, line = _parse(text, default_file)
    LAST["file"] = f
    LAST["line"] = line
    LAST["msg"] = text
    return text
