# PicoCalc UFO — MicroPython UF2 builder
# From repo root:
#   docker build -t picocalc-ufo-build -f firmware/Dockerfile .
#   docker run --rm \
#     -v "$PWD/firmware:/ufo" \
#     -v "$PWD/firmware/dist:/out" \
#     -e BOARD=RPI_PICO2 \
#     picocalc-ufo-build

FROM ubuntu:24.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    git cmake build-essential gcc-arm-none-eabi libnewlib-arm-none-eabi \
    python3 ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# MicroPython v1.25-era commit — stable USB on RP2350 PicoCalc boards
RUN git clone https://github.com/micropython/micropython.git /micropython \
 && cd /micropython && git checkout f187c77da

WORKDIR /micropython
RUN git submodule update --init --depth 1 lib/pico-sdk lib/tinyusb lib/mbedtls lib/micropython-lib \
 && cd lib/pico-sdk && git submodule update --init --depth 1

RUN make -C mpy-cross -j$(nproc)

WORKDIR /micropython/ports/rp2
RUN make BOARD=RPI_PICO submodules \
 && make BOARD=RPI_PICO2 submodules \
 && make BOARD=RPI_PICO2_W submodules || make BOARD=RPI_PICO2 submodules

# Freeze UFO Python modules (not boot/main — those live on the filesystem)
COPY firmware/frozen /tmp/ufo_frozen
COPY apps /tmp/ufo_apps
RUN for f in /tmp/ufo_frozen/*.py; do \
      base=$(basename "$f"); \
      case "$base" in boot.py|main.py|boot_base.py) ;; *) cp "$f" modules/ ;; esac; \
    done \
 && ls modules/gpio_hw.py modules/ufo_shell.py modules/highlighter.py

COPY firmware/c_modules /ufo_c/c_modules
# CMake entry pointing at C modules inside the image
RUN printf '%s\n' \
  'include(/ufo_c/c_modules/picocalcdisplay/micropython.cmake)' \
  'include(/ufo_c/c_modules/vtterminal/micropython.cmake)' \
  > /ufo_c/micropython.cmake

ENV BOARD=RPI_PICO2
WORKDIR /micropython/ports/rp2
CMD bash -c 'make BOARD=${BOARD} USER_C_MODULES=/ufo_c/micropython.cmake -j$(nproc) \
  && mkdir -p /out/fs/apps \
  && cp build-${BOARD}/firmware.uf2 /out/picocalc_ufo_${BOARD}.uf2 \
  && cp /tmp/ufo_frozen/boot.py /tmp/ufo_frozen/main.py /out/fs/ \
  && cp /tmp/ufo_apps/*.py /out/fs/apps/ \
  && ls -la /out /out/fs /out/fs/apps'
