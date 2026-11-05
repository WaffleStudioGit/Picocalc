# SD card (uf2loader)

```
BOOT2040.UF2 / BOOT2350.UF2   # from pelrun/uf2loader — SD root
pico1-apps/PicoCalc_Python.uf2
pico2-apps/PicoCalc_Python.uf2
```

```bash
./tools/build_uf2.sh RPI_PICO2 && ./tools/pack_sdcard.sh
```

Hold **F1** at power-on → select **PicoCalc_Python**.
