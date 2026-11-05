#!/usr/bin/env bash
# Run the full PicoCalc UF2 host test suite (no device / no upload required).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

echo "==> PicoCalc UF2 host tests"
echo "    Root: $ROOT"
echo

python3 -m unittest discover -s host/tests -p 'test_*.py' -v

echo
echo "All host tests passed. Safe to build/flash when ready:"
echo "  ./tools/build_uf2.sh RPI_PICO2"
echo "  ./tools/pack_filesystem.sh"
