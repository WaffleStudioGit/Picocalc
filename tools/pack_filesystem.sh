#!/usr/bin/env bash
# Pack the on-device Python filesystem overlay for Thonny / mpremote deploy.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/firmware/dist/ufo_fs"
rm -rf "$OUT"
mkdir -p "$OUT/apps" "$OUT/lib"

# Root entrypoints
cp "$ROOT/firmware/frozen/boot.py" "$OUT/"
cp "$ROOT/firmware/frozen/main.py" "$OUT/"

# Libraries (skip boot_base)
for f in "$ROOT"/firmware/frozen/*.py; do
  base=$(basename "$f")
  case "$base" in
    boot.py|main.py|boot_base.py) ;;
    *) cp "$f" "$OUT/lib/" ;;
  esac
done

cp "$ROOT"/apps/*.py "$OUT/apps/" 2>/dev/null || true

mkdir -p "$ROOT/firmware/dist"
(cd "$OUT/.." && tar czf ufo_fs.tar.gz ufo_fs)
echo "Filesystem overlay: $OUT"
echo "Archive: $ROOT/firmware/dist/ufo_fs.tar.gz"
echo
echo "Deploy with mpremote (device already running MicroPython + PicoCalc drivers):"
echo "  mpremote cp -r firmware/dist/ufo_fs/lib/ :"
echo "  mpremote cp firmware/dist/ufo_fs/boot.py :boot.py"
echo "  mpremote cp firmware/dist/ufo_fs/main.py :main.py"
echo "  mpremote mkdir apps || true"
echo "  mpremote cp -r firmware/dist/ufo_fs/apps/ :apps/"
