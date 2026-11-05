# PicoCalc UF2 Firmware

MicroPython **UF2** firmware for the [ClockworkPi PicoCalc](https://github.com/clockworkpi/PicoCalc) with:

- Full on-device **Python editor** (`edit`) with **syntax highlighting**
- **GPIO / PWM / ADC / servo** control on the Core GPIOs header
- Interactive **UF2 shell** launcher + normal MicroPython REPL
- PicoCalc display, keyboard, SD card, and speaker drivers

## Test before you flash (host suite)

Run the full suite on your PC — **no PicoCalc upload required**. Hardware is mocked:

```bash
./tools/run_tests.sh
# or:
python3 -m unittest discover -s host/tests -p 'test_*.py' -v
```

Covers:

| Area | What it proves |
|------|----------------|
| `test_highlighter.py` | Syntax colors for keywords, strings, numbers, builtins, comments |
| `test_gpio_hw.py` | Pin safety, GPIO/PWM/servo/ADC math & side-effects |
| `test_shell.py` | Shell commands: help/pins/servo/high/low/run/edit/… |
| `test_apps.py` | Sample apps parse and execute against mocks |
| `test_packaging.py` | Frozen modules, C drivers, tools layout |

Only flash after this is green.

## Theme & anti burn-in

- **Gruvbox dark** LUT + foreground-only syntax colors (no neon keyword blocks)
- **Auto dim → off** after idle (default ~1.5 min / 3 min); any key wakes
- **Status bar hides** for stretches during long edit sessions
- Occasional **1-column content shift** so edges do not stick on the same pixels

Tune at the REPL: `burnin.care.configure(idle_off_ms=120000)`

## Flash / SD launcher (UF2)

### A) PicoCalc SD uf2loader (recommended)

```bash
./tools/build_uf2.sh RPI_PICO2    # Docker
./tools/pack_sdcard.sh            # → sdcard/pico1-apps or pico2-apps
```

Copy `sdcard/pico1-apps` or `sdcard/pico2-apps` onto the MicroSD (keep `BOOT2040.UF2` / `BOOT2350.UF2` on the SD root from [uf2loader](https://github.com/pelrun/uf2loader)). Power on holding **F1**, select **PicoCalc_Python**.

### B) Direct BOOTSEL flash

| Board | Artifact |
|-------|----------|
| Pico (RP2040) | `firmware/dist/picocalc_uf2_RPI_PICO.uf2` |
| Pico 2 | `firmware/dist/picocalc_uf2_RPI_PICO2.uf2` |
| Pico 2 W | `firmware/dist/picocalc_uf2_RPI_PICO2_W.uf2` |

> Already on zenodante MicroPython? Use the **filesystem overlay** below instead of rebuilding.

## Filesystem overlay (no rebuild)

```bash
./tools/pack_filesystem.sh
# Then with mpremote / Thonny, copy lib/, boot.py, main.py, apps/
```

On first boot you get the UF2 shell:

```
help
edit /apps/hello_gpio.py
run /apps/servo_sweep.py
pins
servo 21 90
repl
```

```python
edit("apps/hello_gpio.py")
from gpio_hw import Servo, GPIO, Analog, list_pins
s = Servo(21)
s.write(90)
```

## Header pins (safe I/O)

| Pin | Notes |
|-----|--------|
| **GP2–GP5** | Header (prefer 21/28 for motors on boards with PSRAM) |
| **GP21** | Header — great for servo PWM |
| **GP28** | Header — digital I/O or ADC |
| GP6/7 | Keyboard I2C — blocked by default |
| GP10–15 | LCD — blocked |
| GP16–19 | SD — blocked |
| GP26/27 | Audio PWM — blocked unless `allow_audio=True` |

## Layout

```
firmware/
  c_modules/          # display + VT100 C modules
  frozen/             # Python (editor, gpio_hw, uf2_shell, …)
  Dockerfile          # UF2 build
apps/                 # example scripts
host/
  mocks/              # machine.Pin/PWM/ADC stubs
  harness.py          # loads firmware modules with mocks
  tests/              # full host suite — run before flashing
tools/
  run_tests.sh        # one-shot host verification
  build_uf2.sh
  pack_filesystem.sh
```

## Credits

See [THIRD_PARTY.md](THIRD_PARTY.md). Hardware drivers from zenodante’s PicoCalc MicroPython port; editor core from robert-hh’s Micropython-Editor.
