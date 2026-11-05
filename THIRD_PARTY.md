# Third-party credits

PicoCalc UF2 firmware builds on:

- **zenodante/PicoCalc-micropython-driver** — ILI9488 display C module (`picocalcdisplay`), VT100 terminal C module (`vtterminal`), and PicoCalc MicroPython hardware bindings (`picocalc.py`, `vt.py`, SD helpers).  
  https://github.com/zenodante/PicoCalc-micropython-driver

- **robert-hh/Micropython-Editor (pye)** — on-device text editor core, adapted with keyword highlighting.  
  https://github.com/robert-hh/Micropython-Editor

- **MicroPython** — Python runtime for RP2040 / RP2350.  
  https://github.com/micropython/micropython

- **micropython-lib `sdcard.py`** — SD card driver.  
  https://github.com/micropython/micropython-lib

UF2-firmware-specific additions (this repository): enhanced syntax highlighter, `gpio_hw` servo/GPIO API, `uf2_shell` launcher, apps, host test suite, and build packaging.
