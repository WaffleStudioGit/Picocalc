#!/usr/bin/env bash
# Pack built UF2 images into a PicoCalc uf2loader SD-card tree.
#
# SD layout (pelrun/uf2loader / Clockwork SD v0.6+):
#   /BOOT2040.UF2 or BOOT2350.UF2   (menu UI — from uf2loader release)
#   /pico1-apps/*.uf2               (Pico / Pico W apps)
#   /pico2-apps/*.uf2               (Pico 2 / Pico 2 W apps)
#
# Usage:
#   ./tools/build_uf2.sh RPI_PICO2
#   ./tools/pack_sdcard.sh
# Then copy sdcard/pico*-apps onto the PicoCalc MicroSD.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/sdcard"
DIST="$ROOT/firmware/dist"

mkdir -p "$OUT/pico1-apps" "$OUT/pico2-apps"

copy_named() {
  local src="$1" dest="$2"
  if [[ -f "$src" ]]; then
    cp -f "$src" "$dest"
    echo "  + $(basename "$dest")  ←  $(basename "$src")"
    return 0
  fi
  return 1
}

echo "Packing SD launcher tree → $OUT"
found=0
copy_named "$DIST/picocalc_uf2_RPI_PICO.uf2" \
  "$OUT/pico1-apps/PicoCalc_Python.uf2" && found=1 || true
copy_named "$DIST/picocalc_uf2_RPI_PICO2.uf2" \
  "$OUT/pico2-apps/PicoCalc_Python.uf2" && found=1 || true
copy_named "$DIST/picocalc_uf2_RPI_PICO2_W.uf2" \
  "$OUT/pico2-apps/PicoCalc_Python_W.uf2" && found=1 || true

shopt -s nullglob
for f in "$DIST"/*.uf2; do
  base=$(basename "$f")
  case "$base" in
    PicoCalc_Python*.uf2) ;;
    *PICO2_W*|*pico2w*|*PICO2W*)
      copy_named "$f" "$OUT/pico2-apps/PicoCalc_Python_W.uf2" && found=1 || true
      ;;
    *PICO2*|*pico2*)
      copy_named "$f" "$OUT/pico2-apps/PicoCalc_Python.uf2" && found=1 || true
      ;;
    *PICO*|*pico*)
      copy_named "$f" "$OUT/pico1-apps/PicoCalc_Python.uf2" && found=1 || true
      ;;
  esac
done
shopt -u nullglob

write_placeholder() {
  local dir="$1"
  cat > "$dir/PUT_UF2_HERE.txt" <<'EOF'
Build the firmware first, then re-run ./tools/pack_sdcard.sh:

  ./tools/build_uf2.sh RPI_PICO2   # or RPI_PICO / RPI_PICO2_W
  ./tools/pack_sdcard.sh

Place the resulting PicoCalc_Python*.uf2 in this folder on the PicoCalc SD card
(alongside any other uf2loader apps).
EOF
}

for d in pico1-apps pico2-apps; do
  if compgen -G "$OUT/$d/*.uf2" > /dev/null; then
    rm -f "$OUT/$d/PUT_UF2_HERE.txt"
  else
    write_placeholder "$OUT/$d"
  fi
done

echo
if [[ "$found" -eq 0 ]]; then
  echo "No built UF2 found in firmware/dist/ — placeholders written."
  echo "Run ./tools/build_uf2.sh first, then pack_sdcard.sh again."
else
  echo "SD tree ready:"
fi
find "$OUT" -type f | sort
echo
echo "Copy pico1-apps / pico2-apps onto the MicroSD (keep BOOT2040/BOOT2350 on SD root)."
echo "Power on holding F1 → select PicoCalc_Python."
