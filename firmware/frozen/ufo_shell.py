"""
PicoCalc UFO — interactive launcher shell.

Shown after boot. Lets you browse files, open the syntax-highlighted editor,
run scripts, and poke GPIO / servos without memorizing APIs.
"""

import gc
import os
import sys

try:
    import picocalc
except ImportError:
    picocalc = None

try:
    from colorer import Fore, Style, print, autoreset
except ImportError:
    class _C:
        CYAN = GREEN = YELLOW = RED = MAGENTA = WHITE = BLUE = ""
        RESET_ALL = ""

    Fore = Style = _C()

    def print(*a, **k):
        __builtins__["print"](*a, **k)

    def autoreset(_):
        pass


autoreset(True)

BANNER = r"""
  ____  _           ____      _         _   _ _____ ___
 |  _ \(_) ___ ___ / ___|__ _| | ___   | | | |  ___/ _ \
 | |_) | |/ __/ _ \ |   / _` | |/ __|  | | | | |_ | | | |
 |  __/| | (_| (_) | |__| (_| | | (__  | |_| |  _|| |_| |
 |_|   |_|\___\___/ \____\__,_|_|\___|  \___/|_|   \___/
"""

HELP = """
UFO commands
  help                 this text
  pins                 show safe GPIO header pins
  edit [path]          open Python editor (syntax highlighting on)
  new [path]           create/edit a new script (default /apps/untitled.py)
  run <path>           execute a .py file
  ls [path]            list files
  cat <path>           print a file
  cd <path>            change directory
  pwd                  print working directory
  mem                  memory info
  repl                 drop to raw Python REPL (Ctrl-D to return if hosted)
  servo <pin> <angle>  quick servo move (e.g. servo 21 90)
  high <pin> / low <pin>
  quit                 leave the shell (keeps REPL alive)
"""


def _isdir(path):
    try:
        return (os.stat(path)[0] & 0x4000) != 0
    except OSError:
        return False


def _listdir(path="."):
    try:
        return sorted(os.listdir(path))
    except OSError as e:
        print(Fore.RED + "ls failed:" + Style.RESET_ALL, e)
        return []


def _ensure_apps():
    for d in ("/apps", "/sd/apps", "apps"):
        try:
            os.mkdir(d)
        except OSError:
            pass


def cmd_pins():
    try:
        import gpio_hw
    except ImportError:
        print("gpio_hw module missing")
        return
    info = gpio_hw.list_pins()
    print(Fore.CYAN + "Header pins (safe):" + Style.RESET_ALL, info["header"])
    print(Fore.GREEN + "Recommended I/O:" + Style.RESET_ALL, info["recommended"])
    print(Fore.YELLOW + "Audio (opt-in):" + Style.RESET_ALL, info["audio"])
    print(Fore.RED + "Reserved:" + Style.RESET_ALL, info["reserved_system"])
    print("Example:  from gpio_hw import Servo; s=Servo(21); s.write(90)")


def cmd_edit(path=None):
    if picocalc is None or not hasattr(picocalc, "edit"):
        print("Editor not bound — is the PicoCalc terminal up?")
        return
    if not path:
        path = "/apps/main.py"
        _ensure_apps()
    print(Fore.CYAN + "Opening editor:" + Style.RESET_ALL, path)
    print("  Ctrl-S save   Ctrl-Q quit   syntax highlighting enabled")
    picocalc.edit(path)


def cmd_new(path=None):
    _ensure_apps()
    if not path:
        path = "/apps/untitled.py"
    try:
        os.stat(path)
    except OSError:
        try:
            with open(path, "w") as f:
                f.write(
                    "# PicoCalc UFO script\n"
                    "from gpio_hw import Servo, GPIO, list_pins\n"
                    "import time\n\n"
                    "print(list_pins())\n"
                    "# s = Servo(21)\n"
                    "# s.write(90)\n"
                )
        except OSError as e:
            print("Could not create", path, e)
            return
    cmd_edit(path)


def cmd_run(path):
    if not path:
        print("usage: run <path.py>")
        return
    print(Fore.GREEN + "Running" + Style.RESET_ALL, path)
    gc.collect()
    try:
        # Execute in a fresh-ish namespace with gpio helpers preloaded
        ns = {"__name__": "__main__", "__file__": path}
        try:
            import gpio_hw

            ns["gpio_hw"] = gpio_hw
            ns["Servo"] = gpio_hw.Servo
            ns["GPIO"] = gpio_hw.GPIO
            ns["Analog"] = gpio_hw.Analog
        except ImportError:
            pass
        with open(path) as f:
            code = f.read()
        exec(compile(code, path, "exec"), ns, ns)
    except KeyboardInterrupt:
        print("\n^C interrupted")
    except Exception as e:
        try:
            sys.print_exception(e)
        except Exception:
            print("Error:", e)
    gc.collect()


def cmd_servo(pin, angle):
    try:
        import gpio_hw

        s = gpio_hw.Servo(int(pin))
        s.write(float(angle))
        print("Servo GP%s -> %s deg" % (pin, angle))
    except Exception as e:
        print("servo failed:", e)


def cmd_level(pin, level):
    try:
        import gpio_hw

        g = gpio_hw.GPIO(int(pin), mode=gpio_hw.GPIO.OUT, value=level)
        print("GP%s = %s" % (pin, level))
        return g  # keep reference briefly; caller may drop it
    except Exception as e:
        print("gpio failed:", e)


def cmd_mem():
    gc.collect()
    free = gc.mem_free()
    alloc = gc.mem_alloc()
    print("RAM free: %d  alloc: %d  total~: %d" % (free, alloc, free + alloc))


def _print_banner():
    print(Fore.CYAN + BANNER + Style.RESET_ALL)
    print(Fore.YELLOW + "Unified Firmware — On-device Python" + Style.RESET_ALL)
    print("Type 'help' for commands, 'edit' for the Python editor.\n")


def handle_line(line, state):
    line = (line or "").strip()
    if not line:
        return True
    parts = line.split()
    cmd = parts[0].lower()
    args = parts[1:]

    if cmd in ("help", "?"):
        print(HELP)
    elif cmd == "pins":
        cmd_pins()
    elif cmd == "edit":
        cmd_edit(args[0] if args else None)
    elif cmd == "new":
        cmd_new(args[0] if args else None)
    elif cmd == "run":
        cmd_run(args[0] if args else None)
    elif cmd == "ls":
        path = args[0] if args else "."
        for name in _listdir(path):
            target = name if path == "." else (path.rstrip("/") + "/" + name)
            mark = "/" if _isdir(target) else ""
            print("  " + name + mark)
    elif cmd == "cat":
        if not args:
            print("usage: cat <path>")
        else:
            try:
                with open(args[0]) as f:
                    print(f.read())
            except OSError as e:
                print(e)
    elif cmd == "cd":
        if not args:
            print("usage: cd <path>")
        else:
            try:
                os.chdir(args[0])
            except OSError as e:
                print(e)
    elif cmd == "pwd":
        print(os.getcwd())
    elif cmd == "mem":
        cmd_mem()
    elif cmd == "servo":
        if len(args) < 2:
            print("usage: servo <pin> <angle>")
        else:
            cmd_servo(args[0], args[1])
    elif cmd == "high":
        if not args:
            print("usage: high <pin>")
        else:
            state["hold"] = cmd_level(args[0], 1)
    elif cmd == "low":
        if not args:
            print("usage: low <pin>")
        else:
            state["hold"] = cmd_level(args[0], 0)
    elif cmd in ("quit", "exit", "repl"):
        print("Entering Python REPL. Import gpio_hw / use edit('file.py').")
        return False
    else:
        # Treat unknown input as Python if it looks like code; else hint.
        if any(ch in line for ch in ("=", "(", ".", "'", '"')):
            try:
                ns = state.setdefault("ns", {})
                try:
                    import gpio_hw

                    ns.setdefault("gpio_hw", gpio_hw)
                    ns.setdefault("Servo", gpio_hw.Servo)
                    ns.setdefault("GPIO", gpio_hw.GPIO)
                except ImportError:
                    pass
                result = eval(compile(line, "<ufo>", "eval"), ns, ns)
                if result is not None:
                    print(result)
            except SyntaxError:
                try:
                    exec(compile(line, "<ufo>", "exec"), state.setdefault("ns", {}))
                except Exception as e:
                    print(e)
            except Exception as e:
                print(e)
        else:
            print("Unknown command %r — try 'help'" % cmd)
    return True


def run():
    _ensure_apps()
    _print_banner()
    cmd_pins()
    print()
    state = {"ns": {"gc": gc, "os": os}, "hold": None}
    while True:
        try:
            try:
                cwd = os.getcwd()
            except OSError:
                cwd = "/"
            line = input(Fore.GREEN + "UFO:" + cwd + "> " + Style.RESET_ALL)
        except EOFError:
            break
        except KeyboardInterrupt:
            print("^C")
            continue
        if not handle_line(line, state):
            break
    gc.collect()
