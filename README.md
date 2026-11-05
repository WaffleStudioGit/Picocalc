# PicoCalc UFO Firmware

**U**nified **F**irmware with **O**n-device Python — a MicroPython UF2 firmware stack for the [ClockworkPi PicoCalc](https://github.com/clockworkpi/PicoCalc) with:

- Full on-device **Python editor** (`edit`) with **syntax highlighting**
- **GPIO / PWM / ADC / servo** control on the Core GPIOs header
- Interactive **UFO shell** launcher + normal MicroPython REPL
- PicoCalc display, keyboard, SD card, and speaker drivers

## Flash (UF2)

1. Hold **BOOTSEL** on the Pico module, plug USB, copy the matching UF2:

| Board | Artifact |
|-------|----------|
| Pico (RP2040) | `firmware/dist/picocalc_ufo_RPI_PICO.uf2` |
| Pico 2 | `firmware/dist/picocalc_ufo_RPI_PICO2.uf2` |
| Pico 2 W | `firmware/dist/picocalc_ufo_RPI_PICO2_W.uf2` |

2. Build images (Docker required):

```bash
chmod +x tools/build_uf2.sh
./tools/build_uf2.sh RPI_PICO2      # or RPI_PICO / RPI_PICO2_W
```

3. Power the PicoCalc from its own USB-C port after flashing.

> If you already run zenodante’s PicoCalc MicroPython UF2, skip rebuild and use the **filesystem overlay** below.

## Filesystem overlay (no rebuild)

```bash
chmod +x tools/pack_filesystem.sh && ./tools/pack_filesystem.sh
# Then with mpremote / Thonny, copy:
#   lib/*.py  → device /lib (or /)
#   boot.py, main.py → device /
#   apps/*.py → device /apps/
```

On first boot you get the UFO shell. Useful commands:

```
help
edit /apps/hello_gpio.py     # syntax-highlighted editor
run /apps/servo_sweep.py
pins
servo 21 90
repl
```

From the REPL:

```python
edit("apps/hello_gpio.py")
from gpio_hw import Servo, GPIO, Analog, list_pins
s = Servo(21)
s.write(90)
```

## Header pins (safe I/O)

| Pin | Notes |
|-----|--------|
| **GP2–GP5** | Header (some boards share with PSRAM — prefer 21/28 for motors) |
| **GP21** | Header — great for servo PWM |
| **GP28** | Header — digital I/O or ADC |
| GP6/7 | Keyboard I2C — blocked by default |
| GP10–15 | LCD — blocked |
| GP16–19 | SD — blocked |
| GP26/27 | Audio PWM — blocked unless `allow_audio=True` |

## Editor + syntax highlighting

The editor is based on `pye` and colors Python **keywords**, **strings**, **comments**, **numbers**, **builtins**, and **decorators** for the PicoCalc VT100 palette. Save with **Ctrl-S**, quit with **Ctrl-Q**.

## Layout

```
firmware/
  c_modules/          # display + VT100 C modules (PicoCalc)
  frozen/             # Python frozen into firmware / copied to device
  Dockerfile          # UF2 build
  micropython.cmake
apps/                 # example scripts (servos, blink, hello)
host/tests/           # highlighter + GPIO unit tests (run on PC)
tools/                # build_uf2.sh, pack_filesystem.sh
```

## Host tests

```bash
python3 -m unittest host.tests.test_highlighter -v
```

## Credits

See [THIRD_PARTY.md](THIRD_PARTY.md). Hardware drivers from zenodante’s PicoCalc MicroPython port; editor core from robert-hh’s Micropython-Editor.
