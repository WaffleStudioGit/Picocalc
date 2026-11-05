#!/usr/bin/env bash
# Build PicoCalc MicroPython UF2 images via Docker.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BOARD="${1:-RPI_PICO2}"
mkdir -p "$ROOT/firmware/dist"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required to cross-compile MicroPython UF2 images."
  echo "You can still deploy the Python overlay onto an existing PicoCalc"
  echo "MicroPython UF2 — run: ./tools/pack_filesystem.sh"
  exit 1
fi

docker build -t picocalc-uf2-build -f "$ROOT/firmware/Dockerfile" "$ROOT"
docker run --rm \
  -e "BOARD=${BOARD}" \
  -v "$ROOT/firmware/dist:/out" \
  picocalc-uf2-build

echo "UF2 + fs stub written to firmware/dist/"
ls -la "$ROOT/firmware/dist/"
