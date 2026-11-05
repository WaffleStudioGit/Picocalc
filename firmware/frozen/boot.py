"""PicoCalc UF2 boot: display, keyboard, SD, terminal, Gruvbox, care."""

import os
import sys
import builtins
import picocalc
from picocalc import PicoDisplay, PicoKeyboard, PicoSD, PicoSpeaker
import vt
from picocalc_system import run, files, memory, disk
from pye import pye_edit
import care

try:
    import gpio_hw
except ImportError:
    gpio_hw = None

try:
    display = PicoDisplay(320, 320)
    keyboard = PicoKeyboard()
    sd = PicoSD()
    sd.mount()
    PicoSpeaker(26)
    PicoSpeaker(27)
    terminal = vt.vt(display, keyboard, sd=sd())

    care.apply_gruvbox(display)
    care.care.bind(keyboard)
    care.note_input()

    picocalc.display = display
    picocalc.keyboard = keyboard
    picocalc.terminal = terminal
    picocalc.sd = sd

    def edit(*args, tab_size=2, undo=50):
        terminal.dryBuffer()
        care.note_input()
        return pye_edit(args, tab_size=tab_size, undo=undo, io_device=terminal)

    picocalc.edit = edit
    builtins.edit = edit
    builtins.run = run
    builtins.files = files
    builtins.memory = memory
    builtins.disk = disk
    builtins.care = care
    if gpio_hw:
        builtins.gpio_hw = gpio_hw
        builtins.Servo = gpio_hw.Servo
        builtins.GPIO = gpio_hw.GPIO
        builtins.Analog = gpio_hw.Analog

    os.dupterm(terminal)
    sd.check_mount()
except Exception as e:
    sys.print_exception(e)
