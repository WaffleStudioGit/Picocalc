"""
CPython stand-in for MicroPython's ``machine`` module.

Tracks pin/PWM/ADC state so host tests can assert hardware side-effects
without a PicoCalc.
"""

from __future__ import annotations


class Pin:
    IN = 0
    OUT = 1
    OPEN_DRAIN = 2
    PULL_UP = 1
    PULL_DOWN = 2
    PULL_HOLD = 3

    # Shared registry so tests can inspect every allocated pin.
    registry: dict[int, "Pin"] = {}

    def __init__(self, id, mode=OUT, pull=None, value=None):
        self.id = int(id)
        self.mode = mode
        self.pull = pull
        self._value = 0 if value is None else (1 if value else 0)
        Pin.registry[self.id] = self

    def init(self, mode=None, pull=None, value=None):
        if mode is not None:
            self.mode = mode
        if pull is not None:
            self.pull = pull
        if value is not None:
            self._value = 1 if value else 0

    def value(self, v=None):
        if v is None:
            return self._value
        self._value = 1 if v else 0

    def on(self):
        self._value = 1

    def off(self):
        self._value = 0

    def toggle(self):
        self._value = 1 - self._value

    @classmethod
    def reset_registry(cls):
        cls.registry.clear()


class PWM:
    registry: list["PWM"] = []

    def __init__(self, pin):
        self.pin = pin
        self._freq = 1000
        self._duty_u16 = 0
        self.deinitialized = False
        PWM.registry.append(self)

    def freq(self, hz=None):
        if hz is None:
            return self._freq
        self._freq = int(hz)

    def duty_u16(self, level=None):
        if level is None:
            return self._duty_u16
        self._duty_u16 = max(0, min(65535, int(level)))

    def duty_ns(self, ns=None):
        # Minimal stub — firmware helpers use duty_u16 / duty_us.
        if ns is None:
            return 0
        return None

    def deinit(self):
        self.deinitialized = True
        self._duty_u16 = 0

    @classmethod
    def reset_registry(cls):
        cls.registry.clear()


class ADC:
    registry: list["ADC"] = []

    def __init__(self, pin):
        # Accept Pin instance or raw channel int.
        self.pin = pin
        self._raw = 32768  # mid-scale default (~1.65V at 3.3V ref)
        ADC.registry.append(self)

    def read_u16(self):
        return self._raw

    def set_raw(self, value):
        self._raw = max(0, min(65535, int(value)))

    @classmethod
    def reset_registry(cls):
        cls.registry.clear()


class I2C:
    registry = []

    def __init__(self, id=0, sda=None, scl=None, freq=100000):
        self.id = id
        self.sda = sda
        self.scl = scl
        self.freq = freq
        self._mem = {}
        I2C.registry.append(self)

    def scan(self):
        return list(self._mem.keys())

    def writeto(self, addr, buf, stop=True):
        self._mem.setdefault(addr, b"")
        return len(buf)

    def readfrom(self, addr, nbytes, stop=True):
        return bytes(nbytes)

    def writeto_mem(self, addr, memaddr, buf, addrsize=8):
        self._mem[(addr, memaddr)] = bytes(buf)
        return len(buf)

    def readfrom_mem(self, addr, memaddr, nbytes, addrsize=8):
        data = self._mem.get((addr, memaddr), bytes(nbytes))
        return data[:nbytes]


class UART:
    registry = []

    def __init__(self, id=0, baudrate=115200, tx=None, rx=None, **kw):
        self.id = id
        self.baudrate = baudrate
        self.tx = tx
        self.rx = rx
        self.buf = bytearray()
        UART.registry.append(self)

    def write(self, data):
        if isinstance(data, str):
            data = data.encode()
        self.buf.extend(data)
        return len(data)

    def read(self, nbytes=-1):
        if nbytes < 0:
            out = bytes(self.buf)
            self.buf = bytearray()
            return out
        out = bytes(self.buf[:nbytes])
        self.buf = self.buf[nbytes:]
        return out

    def any(self):
        return len(self.buf)


def reset_all():
    Pin.reset_registry()
    PWM.reset_registry()
    ADC.reset_registry()
    I2C.registry.clear()
    UART.registry.clear()
