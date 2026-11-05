#!/usr/bin/env bash
# Copy built UF2s into sdcard/pico{1,2}-apps for uf2loader.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/sdcard"
DIST="$ROOT/firmware/dist"
mkdir -p "$OUT/pico1-apps" "$OUT/pico2-apps"

put() { [[ -f "$1" ]] && cp -f "$1" "$2" && echo "  $(basename "$2")"; }
put "$DIST/picocalc_uf2_RPI_PICO.uf2"    "$OUT/pico1-apps/PicoCalc_Python.uf2" || true
put "$DIST/picocalc_uf2_RPI_PICO2.uf2"   "$OUT/pico2-apps/PicoCalc_Python.uf2" || true
put "$DIST/picocalc_uf2_RPI_PICO2_W.uf2" "$OUT/pico2-apps/PicoCalc_Python_W.uf2" || true

if ! compgen -G "$OUT/pico1-apps/*.uf2" >/dev/null && ! compgen -G "$OUT/pico2-apps/*.uf2" >/dev/null; then
  echo "No UF2 in firmware/dist — run ./tools/build_uf2.sh first."
  exit 1
fi
find "$OUT" -name '*.uf2' | sort
