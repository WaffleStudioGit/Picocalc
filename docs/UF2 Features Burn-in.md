---
title: PicoCalc UF2 — Features & Burn-in
aliases:
  - UF2 burn-in
  - PicoCalc UF2 features
tags:
  - picocalc
  - uf2
  - micropython
  - firmware
  - burn-in
  - editor
created: 2026-11-04
updated: 2026-11-08
repo: WaffleStudioGit/Picocalc
branch: cursor/uf2-find-break-batt-19c7
---

# PicoCalc UF2 — Features & Burn-in

Lean MicroPython UF2 for ClockworkPi PicoCalc: on-device editor, shell, GPIO helpers, and **aggressive display care** so static UI does not ghost the LCD.

> [!important] Extreme anti burn-in
> Defaults are aggressive on purpose: dim ~30s, backlight off ~60s, status chrome mostly hidden after ~1 min, 1-column content shift ~2 min. Syntax highlight stays **foreground-only** (no sticky background fills). Tune on the SD card via [[#Care config `uf2_care.json`]].

## Feature map

| # | Feature | Where |
|---|---------|--------|
| 1 | File browser in shell | `browse` / `files` / `fb` |
| 2 | Autosave every **5 minutes** | Editor + `care.autosave_ms` |
| 3 | Run from editor | **Ctrl-R** / **F5** (save + run) |
| 4 | Error jump after failed run | `jump` + `errjump` |
| 7+12 | About + diagnostics (one menu) | `status` (also `mem`) |
| 8 | Care config loader | `/sd/uf2_care.json` |
| 9 | I2C / UART pin helpers | `gpio_hw.i2c` / `gpio_hw.uart` |
| — | Find `/` + `n`/`N` (replace opt-in) | Editor Ctrl-F / Ctrl-H |
| — | Soft-break Ctrl-C on run | `softbreak` + `check_break()` |
| — | Battery-low earlier dim | `batt_low_*` in care JSON |

## Quick start (device)

```text
browse                 # pick .py — number = edit, r2 = run #2
status                 # about + battery / backlight / RAM / SD / care
edit /apps/hello_gpio.py
jump                   # open last traceback file:line
from gpio_hw import Servo, i2c, uart
```

Editor keys:

| Key | Action |
|-----|--------|
| Ctrl-S | Save |
| Ctrl-R / F5 | Save + run buffer (Ctrl-C soft-break) |
| Ctrl-F | Find — prompt is `/`; then bare `n` / `N` for next / prev |
| Ctrl-H | Replace (opt-in; yes/No/all/quit per match) |
| (idle) | Autosave dirty named file every 5 min |

Build / SD / tests → see repo root `README.md`.

---

## 1 — File browser

Shell: `browse [dir]` (aliases: `files`, `fb`).

- Lists `.py` files with numbers (one-shot list — no sticky full-screen UI).
- Enter a number → open in editor.
- Enter `rN` → run file N (errors feed [[#4 — Error jump]]).

Source: `firmware/frozen/uf2_shell.py` → `cmd_browse`.

---

## 2 — Autosave (5 minutes)

- Interval default: **300_000 ms** (`care._AUTOSAVE_MS`).
- Editor polls on idle timeout; if the buffer is dirty and has a path, writes and shows `autosaved`.
- Override key in care JSON: `autosave_ms`.

Sources: `firmware/frozen/care.py`, `firmware/frozen/pye.py` (`_maybe_autosave`).

---

## 3 — Run from editor

- **Ctrl-R** or **F5** → save (if needed) then execute the buffer’s file.
- Failures are recorded for `jump`.

Source: `firmware/frozen/pye.py` (`KEY_RUN`).

---

## 4 — Error jump

After `run`, browse-run, or editor run fails:

1. Traceback is parsed into `errjump.LAST` (`file`, `line`).
2. Shell prints a hint: `jump → path Lnn`.
3. `jump` opens the editor at that line.

Source: `firmware/frozen/errjump.py`, shell `cmd_jump`.

---

## 7 + 12 — Unified `status` menu

One command for about **and** diagnostics (no separate about/diag menus):

- Firmware / identity
- Battery / backlight (when available)
- RAM / filesystem hints
- SD presence
- Care timings (dim / off / shift / autosave)
- Last error file:line (if any)

`mem` is an alias that folds into the same output.

Source: `firmware/frozen/uf2_shell.py` → `cmd_status`.

---

## 8 — Care config loader

Looks for JSON in order:

1. `/sd/uf2_care.json`
2. `uf2_care.json`
3. `/uf2_care.json`

Shipped example: `sdcard/uf2_care.json` (copy onto MicroSD root or keep with the pack).

### Care config `uf2_care.json`

```json
{
  "dim_ms": 30000,
  "off_ms": 60000,
  "dim_level": 4,
  "chrome_after_ms": 60000,
  "chrome_period_ms": 60000,
  "chrome_hide_ms": 50000,
  "shift_ms": 120000,
  "autosave_ms": 300000,
  "batt_low_mv": 3500,
  "batt_low_dim_ms": 10000,
  "batt_low_off_ms": 25000,
  "enabled": true
}
```

| Key | Default | Meaning |
|-----|---------|---------|
| `dim_ms` | 30000 | Idle → dim backlight |
| `off_ms` | 60000 | Idle → backlight off / blank |
| `dim_level` | 4 | Dim brightness step |
| `chrome_after_ms` | 60000 | Start chrome-hide cycle |
| `chrome_period_ms` | 60000 | Chrome show/hide period |
| `chrome_hide_ms` | 50000 | How long chrome stays hidden in cycle |
| `shift_ms` | 120000 | 1-column content nudge interval |
| `autosave_ms` | 300000 | Editor autosave interval |
| `batt_low_mv` | 3500 | Below this mV, use batt_low_* timings |
| `batt_low_dim_ms` | 10000 | Dim sooner when battery low |
| `batt_low_off_ms` | 25000 | Blank sooner when battery low |
| `enabled` | true | Master care switch |

### Soft-break (Ctrl-C)

During `run` / editor Ctrl-R, `softbreak` arms a keyboard poll and breakable `time.sleep`. Tight loops should call `check_break()` (injected into the run namespace):

```python
while True:
    check_break()
    # work...
```

Source: `firmware/frozen/softbreak.py`.

> [!tip] Soften burn-in
> Raise `dim_ms` / `off_ms` / `shift_ms` if the aggressive defaults feel too twitchy. Set `enabled` to `false` only if you accept ghosting risk on a static UI.

### Burn-in behaviors (code)

- Idle activity resets timers (`care.Care.touch` / tick path).
- Editor status bar / chrome respects `chrome_visible()`.
- Long sessions nudge content by **one column** (`pixel_shift`) so glyphs do not sit on the same pixels forever.
- Gruvbox LUT via `care.apply_gruvbox`; highlighter prefers **fg-only** colors.

Source: `firmware/frozen/care.py`.

---

## 9 — I2C / UART helpers

```python
from gpio_hw import i2c, uart, Servo, list_pins

bus = i2c()                 # SDA=GP4, SCL=GP5
print(bus.scan())

ser = uart()                # TX=GP21, RX=GP28
ser.write(b"hi\n")
```

- Safe header pins: **GP2–5, 21, 28** (system SPI/I2C for display/SD blocked by default).
- `list_pins()` / shell `pins` show header vs reserved vs audio.
- Servo / GPIO / PWM / ADC helpers live in the same module.

Source: `firmware/frozen/gpio_hw.py`.

---

## Shell command cheat sheet

```text
help | ?
browse [dir] | files | fb
edit [file] | new [file]
run <file>
jump
status | mem
pins
ls | cat | cd | pwd
servo <pin> <angle>
high <pin> | low <pin>
quit | exit | repl
```

Arbitrary Python also evaluates in the shell namespace (`Servo`, `GPIO`, `i2c`, `uart` preloaded when available).

---

## Repo layout (this work)

| Path | Role |
|------|------|
| `firmware/frozen/care.py` | Burn-in + config + autosave + batt-low dim |
| `firmware/frozen/pye.py` | Editor: autosave, find n/N, Ctrl-R/F5, chrome/shift |
| `firmware/frozen/softbreak.py` | Ctrl-C soft-break during run |
| `firmware/frozen/uf2_shell.py` | browse / status / jump / run |
| `firmware/frozen/errjump.py` | Last traceback file:line |
| `firmware/frozen/gpio_hw.py` | GPIO + Servo + I2C + UART |
| `sdcard/uf2_care.json` | Tunable care defaults for SD |
| `host/tests/` | Host unit tests (mocks) |

```bash
./tools/run_tests.sh
./tools/build_uf2.sh RPI_PICO2
./tools/pack_sdcard.sh
```

---

## Related

- Root overview: [[README]]
- SD pack notes: [[sdcard/README]]
- Credits: [[THIRD_PARTY]]

#picocalc #uf2 #burn-in
