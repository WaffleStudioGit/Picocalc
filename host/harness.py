"""
Test harness: put firmware modules on ``sys.path`` and install hardware mocks
before importing anything that needs ``machine`` / ``micropython``.
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / "firmware" / "frozen"
APPS = ROOT / "apps"
MOCKS = Path(__file__).resolve().parent / "mocks"


def _ensure_path(p: Path):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)


def _load_mock(mod_name: str, filename: str):
    path = MOCKS / filename
    spec = importlib.util.spec_from_file_location(mod_name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    sys.modules[mod_name] = mod
    return mod


def install_mocks(reset_hardware: bool = True):
    """Install ``machine`` + ``micropython`` stubs into ``sys.modules``."""
    machine = _load_mock("machine", "machine.py")
    _load_mock("micropython", "micropython.py")
    if reset_hardware and hasattr(machine, "reset_all"):
        machine.reset_all()
    return machine


def setup_firmware_path():
    _ensure_path(FROZEN)
    _ensure_path(APPS)


def load_module(name: str, reload: bool = True):
    """
    Import a firmware frozen module with mocks installed.

    Always call this (not bare ``import gpio_hw``) from tests that need PWM/GPIO.
    """
    setup_firmware_path()
    install_mocks(reset_hardware=True)
    if name in sys.modules and reload:
        return importlib.reload(sys.modules[name])
    return importlib.import_module(name)


def load_gpio_hw():
    return load_module("gpio_hw")


def load_highlighter_stack():
    """Return (highlighter_mod, style_mod, Highlighter, syntax_style)."""
    setup_firmware_path()
    install_mocks(reset_hardware=False)
    style = (
        importlib.reload(sys.modules["default_style"])
        if "default_style" in sys.modules
        else importlib.import_module("default_style")
    )
    hl_mod = (
        importlib.reload(sys.modules["highlighter"])
        if "highlighter" in sys.modules
        else importlib.import_module("highlighter")
    )
    return hl_mod, style, hl_mod.Highlighter, style.syntax_style


def load_shell():
    setup_firmware_path()
    install_mocks(reset_hardware=True)
    # Ensure gpio_hw is bound to the mock machine.
    if "gpio_hw" in sys.modules:
        importlib.reload(sys.modules["gpio_hw"])
    else:
        importlib.import_module("gpio_hw")
    # Reload colorer before the shell so its print() picks up call-time stdout.
    if "colorer" in sys.modules:
        importlib.reload(sys.modules["colorer"])
    else:
        importlib.import_module("colorer")
    for name in ("uf2_shell", "uf2_shell"):
        if name in sys.modules:
            return importlib.reload(sys.modules[name])
    try:
        return importlib.import_module("uf2_shell")
    except ImportError:
        return importlib.import_module("uf2_shell")
