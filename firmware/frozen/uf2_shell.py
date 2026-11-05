"""Minimal PicoCalc UF2 shell: edit / run / gpio helpers."""

import gc
import os
import sys

try:
    import picocalc
except ImportError:
    picocalc = None

HELP = "help pins edit [f] new [f] run <f> ls cat cd pwd mem servo <p> <a> high/low <p> quit"


def _gpio():
    import gpio_hw

    return gpio_hw


def handle_line(line, state):
    line = (line or "").strip()
    if not line:
        return True
    parts = line.split()
    cmd, args = parts[0].lower(), parts[1:]

    if cmd in ("help", "?"):
        print(HELP)
    elif cmd == "pins":
        print(_gpio().list_pins())
    elif cmd == "edit":
        if not picocalc or not hasattr(picocalc, "edit"):
            print("editor unavailable")
        else:
            picocalc.edit(args[0] if args else "/apps/main.py")
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
        return handle_line("edit " + path, state)
    elif cmd == "run":
        if not args:
            print("run <file>")
        else:
            g = {"__name__": "__main__"}
            try:
                hw = _gpio()
                g.update(gpio_hw=hw, Servo=hw.Servo, GPIO=hw.GPIO)
            except ImportError:
                pass
            with open(args[0]) as f:
                exec(compile(f.read(), args[0], "exec"), g, g)
    elif cmd == "ls":
        path = args[0] if args else "."
        print("\n".join(sorted(os.listdir(path))))
    elif cmd == "cat":
        if not args:
            print("cat <file>")
        else:
            with open(args[0]) as f:
                print(f.read())
    elif cmd == "cd":
        os.chdir(args[0]) if args else print("cd <path>")
    elif cmd == "pwd":
        print(os.getcwd())
    elif cmd == "mem":
        gc.collect()
        free = gc.mem_free() if hasattr(gc, "mem_free") else -1
        print("free", free)
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
    print("PicoCalc UF2 — type help")
    state = {"ns": {}, "hold": None}
    while True:
        try:
            line = input("uf2> ")
        except (EOFError, KeyboardInterrupt):
            break
        if not handle_line(line, state):
            break
