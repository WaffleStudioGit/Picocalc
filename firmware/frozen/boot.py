"""
PicoCalc UFO boot — bring up display, keyboard, SD, VT terminal, editor.
"""

import picocalc
from picocalc import PicoDisplay, PicoKeyboard, PicoSD, PicoSpeaker
import os
import sys
import vt
from picocalc_system import run, files, memory, disk
from pye import pye_edit

# GPIO / servo API available as soon as boot completes
try:
    import gpio_hw
except ImportError:
    gpio_hw = None

try:
    pc_display = PicoDisplay(320, 320)
    pc_keyboard = PicoKeyboard()
    pc_sd = PicoSD()
    pc_sd.mount()
    pcs_L = PicoSpeaker(26)
    pcs_R = PicoSpeaker(27)
    pc_terminal = vt.vt(pc_display, pc_keyboard, sd=pc_sd())

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
        """Open the UFO Python editor with syntax highlighting."""
        pc_terminal.dryBuffer()
        return pye_edit(args, tab_size=tab_size, undo=undo, io_device=pc_terminal)

    picocalc.edit = edit

    # Re-export helpers into builtins for convenient REPL use
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

    os.dupterm(pc_terminal)
    pc_sd.check_mount()

except Exception as e:
    sys.print_exception(e)
    try:
        os.dupterm(None).write(b"[UFO boot.py error]\n")
    except Exception:
        pass
