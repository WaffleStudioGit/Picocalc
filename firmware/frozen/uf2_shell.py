"""PicoCalc UF2 shell: browse / edit / run / jump / status (burn-in safe)."""

import gc
import os
import sys

try:
    import picocalc
except ImportError:
    picocalc = None

HELP = (
    "help browse [dir] edit [f] new [f] run <f> jump status "
    "pins ls cat cd pwd servo high/low quit | Ctrl-C stops run"
)

_FIRMWARE = "PicoCalc UF2"


def _gpio():
    import gpio_hw

    return gpio_hw


def _edit(path, line=None):
    if not picocalc or not hasattr(picocalc, "edit"):
        print("editor unavailable")
        return
    if line is not None:
        try:
            picocalc.edit(path, line=line)
            return
        except TypeError:
            pass
    picocalc.edit(path)


def _run_path(path, state):
    import errjump

    errjump.clear()
    g = {"__name__": "__main__", "__file__": path}
    try:
        hw = _gpio()
        g.update(
            gpio_hw=hw,
            Servo=hw.Servo,
            GPIO=hw.GPIO,
            Analog=hw.Analog,
            i2c=hw.i2c,
            uart=hw.uart,
        )
    except ImportError:
        pass
    try:
        import softbreak

        g["check_break"] = softbreak.check
        g["softbreak"] = softbreak
    except ImportError:
        softbreak = None
    try:
        with open(path) as f:
            code = f.read()

        def _exec():
            exec(compile(code, path, "exec"), g, g)

        if softbreak:
            softbreak.run_guarded(_exec)
        else:
            _exec()
        print("ok")
    except KeyboardInterrupt:
        print("interrupted (Ctrl-C) — use check_break() in tight loops")
    except Exception as e:
        text = errjump.record(e, default_file=path)
        print(text)
        if errjump.LAST.get("file") and errjump.LAST.get("line"):
            print("jump →", errjump.LAST["file"], "L" + str(errjump.LAST["line"]))


def cmd_browse(path, state):
    """Numbered .py picker: number opens edit; r<n> runs. One-shot list (no sticky UI)."""
    path = path or "."
    try:
        names = sorted(
            n for n in os.listdir(path) if n.endswith(".py") or _isdir(path, n)
        )
    except OSError as e:
        print(e)
        return
    if not names:
        print("empty")
        return
    entries = []
    for n in names:
        full = n if path == "." else (path.rstrip("/") + "/" + n)
        entries.append(full)
        mark = "/" if _isdir_path(full) else ""
        print("%2d %s%s" % (len(entries), n, mark))
    try:
        raw = input("browse#> ").strip()
    except (EOFError, KeyboardInterrupt):
        return
    if not raw:
        return
    run = False
    if raw[0] in ("r", "R") and len(raw) > 1:
        run = True
        raw = raw[1:]
    try:
        idx = int(raw)
    except ValueError:
        print("cancel")
        return
    if not 1 <= idx <= len(entries):
        print("bad #")
        return
    target = entries[idx - 1]
    if _isdir_path(target):
        os.chdir(target)
        print(os.getcwd())
        return
    if run:
        _run_path(target, state)
    else:
        _edit(target)


def _isdir(path, name):
    return _isdir_path(name if path == "." else path.rstrip("/") + "/" + name)


def _isdir_path(path):
    try:
        return (os.stat(path)[0] & 0x4000) != 0
    except OSError:
        return False


def cmd_status():
    """One-shot about + battery/backlight/RAM/care (no lingering menu)."""
    print(_FIRMWARE)
    gc.collect()
    free = gc.mem_free() if hasattr(gc, "mem_free") else -1
    print("ram_free", free)
    try:
        print("cwd", os.getcwd())
    except OSError:
        pass
    sd_ok = False
    try:
        os.listdir("/sd")
        sd_ok = True
    except OSError:
        pass
    print("sd", "mounted" if sd_ok else "no")
    kb = getattr(picocalc, "keyboard", None) if picocalc else None
    if kb is not None:
        try:
            print("battery", kb.battery())
        except Exception:
            pass
        try:
            print("backlight", kb.backlight())
        except Exception:
            pass
    try:
        import care

        s = care.settings()
        dim_e, off_e = care.effective_idle_ms()
        print(
            "care dim/off",
            s["dim_ms"],
            s["off_ms"],
            "eff",
            dim_e,
            off_e,
            "shift",
            s["shift_ms"],
            "autosave",
            s["autosave_ms"],
        )
        print(
            "batt_low",
            s["batt_low_mv"],
            "mV → dim/off",
            s["batt_low_dim_ms"],
            s["batt_low_off_ms"],
        )
    except Exception:
        pass
    try:
        import errjump

        if errjump.LAST.get("file"):
            print("last_err", errjump.LAST["file"], "L" + str(errjump.LAST["line"]))
    except Exception:
        pass


def cmd_jump():
    import errjump

    f = errjump.LAST.get("file")
    line = errjump.LAST.get("line") or 0
    if not f:
        print("no error")
        return
    print("open", f, "L" + str(line))
    _edit(f, line=line if line else None)


def handle_line(line, state):
    line = (line or "").strip()
    if not line:
        return True
    parts = line.split()
    cmd, args = parts[0].lower(), parts[1:]

    if cmd in ("help", "?"):
        print(HELP)
    elif cmd in ("browse", "files", "fb"):
        cmd_browse(args[0] if args else ".", state)
    elif cmd == "status":
        cmd_status()
    elif cmd == "jump":
        cmd_jump()
    elif cmd == "pins":
        print(_gpio().list_pins())
    elif cmd == "edit":
        _edit(args[0] if args else "/apps/main.py")
    elif cmd == "new":
        path = args[0] if args else "apps/untitled.py"
        try:
            os.mkdir("apps")
        except OSError:
            pass
        try:
            os.stat(path)
        except OSError:
            with open(path, "w") as f:
                f.write("from gpio_hw import Servo\n# s=Servo(21); s.write(90)\n")
        _edit(path)
    elif cmd == "run":
        if not args:
            print("run <file>")
        else:
            _run_path(args[0], state)
    elif cmd == "ls":
        path = args[0] if args else "."
        try:
            print("\n".join(sorted(os.listdir(path))))
        except OSError as e:
            print(e)
    elif cmd == "cat":
        if not args:
            print("cat <file>")
        else:
            with open(args[0]) as f:
                print(f.read())
    elif cmd == "cd":
        if args:
            try:
                os.chdir(args[0])
            except OSError as e:
                print(e)
        else:
            print("cd <path>")
    elif cmd == "pwd":
        print(os.getcwd())
    elif cmd == "mem":
        cmd_status()  # mem folded into status; keep alias brief
    elif cmd == "servo":
        if len(args) < 2:
            print("servo <pin> <angle>")
        else:
            try:
                s = _gpio().Servo(int(args[0]))
                s.write(float(args[1]))
                state["hold"] = s
                print("ok")
            except Exception as e:
                print(e)
    elif cmd in ("high", "low"):
        if not args:
            print(cmd, "<pin>")
        else:
            try:
                state["hold"] = _gpio().GPIO(
                    int(args[0]), mode=_gpio().GPIO.OUT, value=1 if cmd == "high" else 0
                )
            except Exception as e:
                print(e)
    elif cmd in ("quit", "exit", "repl"):
        return False
    else:
        ns = state.setdefault("ns", {})
        try:
            hw = _gpio()
            ns.setdefault("Servo", hw.Servo)
            ns.setdefault("GPIO", hw.GPIO)
            ns.setdefault("gpio_hw", hw)
            ns.setdefault("i2c", hw.i2c)
            ns.setdefault("uart", hw.uart)
        except ImportError:
            pass
        try:
            r = eval(compile(line, "<uf2>", "eval"), ns, ns)
            if r is not None:
                print(r)
        except SyntaxError:
            try:
                exec(compile(line, "<uf2>", "exec"), ns, ns)
            except Exception as e:
                print(e)
        except NameError:
            print("unknown:", cmd)
        except Exception as e:
            print(e)
    return True


def run():
    try:
        os.mkdir("apps")
    except OSError:
        pass
    print("PicoCalc UF2 — help | status | browse")
    state = {"ns": {}, "hold": None}
    while True:
        try:
            try:
                import care

                care.tick()
            except ImportError:
                pass
            line = input("uf2> ")
            try:
                import care

                care.note_input()
            except ImportError:
                pass
        except (EOFError, KeyboardInterrupt):
            break
        if not handle_line(line, state):
            break
