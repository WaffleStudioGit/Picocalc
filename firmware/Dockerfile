# PicoCalc UF2 — MicroPython UF2 builder
# From repo root:
#   docker build -t picocalc-uf2-build -f firmware/Dockerfile .
#   docker run --rm \
#     -v "$PWD/firmware:/uf2" \
#     -v "$PWD/firmware/dist:/out" \
#     -e BOARD=RPI_PICO2 \
#     picocalc-uf2-build

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

# Freeze UF2 Python modules (not boot/main — those live on the filesystem)
COPY firmware/frozen /tmp/uf2_frozen
COPY apps /tmp/uf2_apps
RUN for f in /tmp/uf2_frozen/*.py; do \
      base=$(basename "$f"); \
      case "$base" in boot.py|main.py|boot_base.py) ;; *) cp "$f" modules/ ;; esac; \
    done \
 && ls modules/gpio_hw.py modules/uf2_shell.py modules/highlighter.py

COPY firmware/c_modules /uf2_c/c_modules
# CMake entry pointing at C modules inside the image
RUN printf '%s\n' \
  'include(/uf2_c/c_modules/picocalcdisplay/micropython.cmake)' \
  'include(/uf2_c/c_modules/vtterminal/micropython.cmake)' \
  > /uf2_c/micropython.cmake

ENV BOARD=RPI_PICO2
WORKDIR /micropython/ports/rp2
CMD bash -c 'make BOARD=${BOARD} USER_C_MODULES=/uf2_c/micropython.cmake -j$(nproc) \
  && mkdir -p /out/fs/apps \
  && cp build-${BOARD}/firmware.uf2 /out/picocalc_uf2_${BOARD}.uf2 \
  && cp /tmp/uf2_frozen/boot.py /tmp/uf2_frozen/main.py /out/fs/ \
  && cp /tmp/uf2_apps/*.py /out/fs/apps/ \
  && ls -la /out /out/fs /out/fs/apps'
