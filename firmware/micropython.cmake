# PicoCalc UFO — USER_C_MODULES entry for MicroPython rp2 port
# Usage (from micropython/ports/rp2/build):
#   cmake .. -DUSER_C_MODULES=/path/to/firmware/micropython.cmake \
#            -DMICROPY_BOARD=RPI_PICO2

include(${CMAKE_CURRENT_LIST_DIR}/c_modules/picocalcdisplay/micropython.cmake)
include(${CMAKE_CURRENT_LIST_DIR}/c_modules/vtterminal/micropython.cmake)
