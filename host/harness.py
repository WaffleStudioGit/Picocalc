"""Load firmware modules with machine/micropython mocks."""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / "firmware" / "frozen"
MOCKS = Path(__file__).resolve().parent / "mocks"


def _ensure(p: Path):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)


def install_mocks(reset_hardware=True):
    for name, file in (("machine", "machine.py"), ("micropython", "micropython.py")):
        spec = importlib.util.spec_from_file_location(name, MOCKS / file)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        sys.modules[name] = mod
    if reset_hardware and hasattr(sys.modules["machine"], "reset_all"):
        sys.modules["machine"].reset_all()
    return sys.modules["machine"]


def setup_firmware_path():
    _ensure(FROZEN)
    _ensure(ROOT / "apps")


def load_module(name, reload=True):
    setup_firmware_path()
    install_mocks()
    if name in sys.modules and reload:
        return importlib.reload(sys.modules[name])
    return importlib.import_module(name)


def load_gpio_hw():
    return load_module("gpio_hw")


def load_highlighter_stack():
    setup_firmware_path()
    install_mocks(reset_hardware=False)
    style = load_module("default_style")
    hl = load_module("highlighter")
    return hl, style, hl.Highlighter, style.syntax_style


def load_shell():
    setup_firmware_path()
    install_mocks()
    load_module("gpio_hw")
    return load_module("uf2_shell")
