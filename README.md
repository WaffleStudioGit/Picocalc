# PicoCalc UF2

MicroPython UF2 for ClockworkPi PicoCalc: on-device Python editor (syntax highlight), GPIO/servos, Gruvbox + anti burn-in.

## Test (no upload)

```bash
./tools/run_tests.sh
```

## Build → SD launcher

```bash
./tools/build_uf2.sh RPI_PICO2
./tools/pack_sdcard.sh
```

Copy `sdcard/pico1-apps` or `sdcard/pico2-apps` onto the MicroSD (keep `BOOT2040.UF2` / `BOOT2350.UF2` on SD root). Hold **F1** at power-on → **PicoCalc_Python**.

Or BOOTSEL-flash `firmware/dist/picocalc_uf2_*.uf2`.

## On device

```
edit /apps/hello_gpio.py
from gpio_hw import Servo; Servo(21).write(90)
```

Idle dims/off the backlight; status bar hides on long sessions. Header pins: **GP21 / GP28** (see `pins`).

Credits: [THIRD_PARTY.md](THIRD_PARTY.md).
