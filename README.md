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
browse                 # pick .py to edit (r2 = run #2)
status                 # about + battery/backlight/RAM/care
edit /apps/hello_gpio.py
# editor: Ctrl-S save · Ctrl-R / F5 save+run · autosave every 5 min
#         Ctrl-F find (/prompt) · n/N next/prev · Ctrl-H replace (opt-in)
jump                   # open last traceback file:line
# run / Ctrl-R: Ctrl-C soft-break (check_break() in tight loops)
from gpio_hw import Servo, i2c, uart
```

Burn-in (aggressive): dim ~30s, off ~60s, status chrome mostly hidden after ~1 min, 1-col shift ~2 min. Battery below `batt_low_mv` (default 3500) dims/off sooner. Tune via `sdcard/uf2_care.json` on the SD card.

Credits: [THIRD_PARTY.md](THIRD_PARTY.md).
