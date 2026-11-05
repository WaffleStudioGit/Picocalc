# PicoCalc SD card — UF2 launcher apps

This tree is for **pelrun/uf2loader** (Clockwork PicoCalc SD v0.6+).

## Layout

```
SD card root/
  BOOT2040.UF2          # menu UI for Pico 1  (from uf2loader release)
  BOOT2350.UF2          # menu UI for Pico 2  (from uf2loader release)
  pico1-apps/
    PicoCalc_Python.uf2 # ← this firmware (RP2040)
  pico2-apps/
    PicoCalc_Python.uf2 # ← this firmware (RP2350)
    PicoCalc_Python_W.uf2
```

## Build & pack

```bash
./tools/build_uf2.sh RPI_PICO2    # needs Docker
./tools/pack_sdcard.sh            # copies into sdcard/pico*-apps/
```

Copy the `pico1-apps` / `pico2-apps` folder(s) onto the MicroSD (keep existing apps).

## Boot

1. Flash `bootloader_pico.uf2` or `bootloader_pico2.uf2` once (BOOTSEL), if not already.
2. Insert SD, hold **F1** (or Up) while powering on → launcher menu.
3. Select **PicoCalc_Python**.

## Notes

- Filename is what appears in the menu — keep it short.
- Pico 1 and Pico 2 app folders can coexist on one card.
