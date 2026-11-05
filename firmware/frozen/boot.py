"""
PicoCalc UF2 boot — display, keyboard, SD, VT terminal, editor, theme, burn-in.
"""

import picocalc
from picocalc import PicoDisplay, PicoKeyboard, PicoSD, PicoSpeaker
import os
import sys
import vt
from picocalc_system import run, files, memory, disk
from pye import pye_edit

try:
    import gpio_hw
except ImportError:
    gpio_hw = None

try:
    import theme
except ImportError:
    theme = None

try:
    import burnin
except ImportError:
    burnin = None

try:
    pc_display = PicoDisplay(320, 320)
    pc_keyboard = PicoKeyboard()
    pc_sd = PicoSD()
    pc_sd.mount()
    pcs_L = PicoSpeaker(26)
    pcs_R = PicoSpeaker(27)
    pc_terminal = vt.vt(pc_display, pc_keyboard, sd=pc_sd())

    # Gruvbox dark LUT — muted, easier on IPS panels than stock VT neon.
    if theme is not None:
        try:
            theme.apply_gruvbox(pc_display)
        except Exception:
            pass

    if burnin is not None:
        burnin.care.bind_keyboard(pc_keyboard)
        burnin.note_input()

    _usb = sys.stdout

    def usb_debug(msg):
        if isinstance(msg, str):
            _usb.write(msg)
        else:
            _usb.write(str(msg))
        _usb.write("\r\n")

    picocalc.usb_debug = usb_debug
    picocalc.display = pc_display
    picocalc.keyboard = pc_keyboard
    picocalc.terminal = pc_terminal
    picocalc.sd = pc_sd

    def edit(*args, tab_size=2, undo=50):
        """Open the UF2 Python editor with syntax highlighting."""
        pc_terminal.dryBuffer()
        if burnin is not None:
            burnin.note_input()
        return pye_edit(args, tab_size=tab_size, undo=undo, io_device=pc_terminal)

    picocalc.edit = edit

    import builtins

    builtins.edit = edit
    builtins.run = run
    builtins.files = files
    builtins.memory = memory
    builtins.disk = disk
    if gpio_hw is not None:
        builtins.gpio_hw = gpio_hw
        builtins.Servo = gpio_hw.Servo
        builtins.GPIO = gpio_hw.GPIO
        builtins.Analog = gpio_hw.Analog
    if burnin is not None:
        builtins.burnin = burnin

    os.dupterm(pc_terminal)
    pc_sd.check_mount()

except Exception as e:
    sys.print_exception(e)
    try:
        os.dupterm(None).write(b"[UF2 boot.py error]\n")
    except Exception:
        pass
