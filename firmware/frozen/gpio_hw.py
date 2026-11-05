"""Header GPIO / PWM / servo / ADC. Safe pins: 2-5, 21, 28."""

HEADER_PINS = (2, 3, 4, 5, 21, 28)
RECOMMENDED_IO = (21, 28)
_SYSTEM = frozenset((6, 7, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20))
_AUDIO = frozenset((26, 27))
_SERVO_PERIOD = 20_000


def _machine():
    import machine

    return machine.Pin, machine.PWM, machine.ADC


def _check(pin, allow_audio=False, allow_system=False):
    p = int(pin)
    if not 0 <= p <= 28:
        raise ValueError("pin 0..28")
    if not allow_system and p in _SYSTEM:
        raise ValueError("GP%d reserved; use %s" % (p, list(HEADER_PINS)))
    if not allow_audio and p in _AUDIO:
        raise ValueError("GP%d audio; allow_audio=True to override" % p)
    return p


def list_pins():
    return {
        "header": list(HEADER_PINS),
        "recommended": list(RECOMMENDED_IO),
        "audio": list(_AUDIO),
        "reserved_system": sorted(_SYSTEM),
    }


class GPIO:
    OUT, IN, IN_PULLUP, IN_PULLDOWN = 0, 1, 2, 3

    def __init__(self, pin, mode=OUT, value=0, allow_audio=False, allow_system=False):
        Pin, _, __ = _machine()
        self.pin_num = _check(pin, allow_audio, allow_system)
        self._mode = mode
        if mode == self.OUT:
            self._pin = Pin(self.pin_num, Pin.OUT, value=value)
        elif mode == self.IN:
            self._pin = Pin(self.pin_num, Pin.IN)
        elif mode == self.IN_PULLUP:
            self._pin = Pin(self.pin_num, Pin.IN, Pin.PULL_UP)
        elif mode == self.IN_PULLDOWN:
            self._pin = Pin(self.pin_num, Pin.IN, Pin.PULL_DOWN)
        else:
            raise ValueError("mode")

    def high(self):
        self._pin.value(1)

    def low(self):
        self._pin.value(0)

    def toggle(self):
        self._pin.value(1 - self._pin.value())

    def value(self, v=None):
        return self._pin.value() if v is None else self._pin.value(1 if v else 0)

    def on(self):
        self.high()

    def off(self):
        self.low()


class SoftPWM:
    def __init__(self, pin, freq=1000, duty_u16=0, allow_audio=False, allow_system=False):
        Pin, PWM, _ = _machine()
        self.pin_num = _check(pin, allow_audio, allow_system)
        self._pwm = PWM(Pin(self.pin_num))
        self._pwm.freq(int(freq))
        self._pwm.duty_u16(int(duty_u16) & 0xFFFF)

    def freq(self, hz=None):
        return self._pwm.freq() if hz is None else self._pwm.freq(int(hz))

    def duty_u16(self, level=None):
        if level is None:
            return self._pwm.duty_u16()
        self._pwm.duty_u16(max(0, min(65535, int(level))))

    def duty_percent(self, pct=None):
        if pct is None:
            return self._pwm.duty_u16() * 100.0 / 65535.0
        self._pwm.duty_u16(int(max(0.0, min(100.0, float(pct))) * 65535.0 / 100.0))

    def duty_us(self, us=None, period_us=None):
        if period_us is None:
            period_us = 1_000_000 // max(1, self._pwm.freq())
        if us is None:
            return int(self._pwm.duty_u16() * period_us / 65535.0)
        self._pwm.duty_u16(int(max(0, min(period_us, int(us))) * 65535 / period_us))

    def deinit(self):
        try:
            self._pwm.deinit()
        except Exception:
            pass


class Servo:
    def __init__(self, pin, min_us=500, max_us=2500, min_angle=0, max_angle=180, **kw):
        self.min_us, self.max_us = int(min_us), int(max_us)
        self.min_angle, self.max_angle = float(min_angle), float(max_angle)
        self._angle = self.min_angle
        self._pwm = SoftPWM(pin, freq=50, **kw)
        self.pin_num = self._pwm.pin_num

    def _us_from_angle(self, angle):
        span = self.max_angle - self.min_angle
        t = 0.0 if span == 0 else max(0.0, min(1.0, (float(angle) - self.min_angle) / span))
        return int(self.min_us + t * (self.max_us - self.min_us))

    def write_us(self, us):
        us = max(self.min_us, min(self.max_us, int(us)))
        self._pwm.duty_us(us, period_us=_SERVO_PERIOD)
        span = self.max_us - self.min_us
        if span:
            self._angle = self.min_angle + (us - self.min_us) / span * (self.max_angle - self.min_angle)

    def write(self, angle):
        self._angle = float(angle)
        self.write_us(self._us_from_angle(angle))

    def read(self):
        return self._angle

    def mid(self):
        self.write((self.min_angle + self.max_angle) / 2)

    def min(self):
        self.write(self.min_angle)

    def max(self):
        self.write(self.max_angle)

    def detach(self):
        self._pwm.duty_u16(0)

    def deinit(self):
        self.detach()
        self._pwm.deinit()


class Analog:
    _ADC = {26: 0, 27: 1, 28: 2, 29: 3}

    def __init__(self, pin=28, allow_audio=False, allow_system=False):
        Pin, _, ADC = _machine()
        self.pin_num = _check(pin, allow_audio, allow_system)
        if self.pin_num not in self._ADC:
            raise ValueError("ADC pins: 26/27/28/29")
        self._adc = ADC(Pin(self.pin_num))

    def read_u16(self):
        return self._adc.read_u16()

    def read_volts(self, vref=3.3):
        return self._adc.read_u16() * float(vref) / 65535.0


def servo(pin=21, **kw):
    return Servo(pin, **kw)


def output(pin, value=0, **kw):
    return GPIO(pin, mode=GPIO.OUT, value=value, **kw)


def input_pin(pin, pull=None, **kw):
    mode = GPIO.IN_PULLUP if pull == "up" else GPIO.IN_PULLDOWN if pull == "down" else GPIO.IN
    return GPIO(pin, mode=mode, **kw)


def pwm(pin, freq=1000, duty_percent=0, **kw):
    p = SoftPWM(pin, freq=freq, **kw)
    p.duty_percent(duty_percent)
    return p


class BusI2C:
    """I2C on header pins (default GP4=SDA, GP5=SCL)."""

    def __init__(self, id=0, sda=4, scl=5, freq=100_000, allow_system=False):
        from machine import I2C, Pin

        self.sda = _check(sda, allow_system=allow_system)
        self.scl = _check(scl, allow_system=allow_system)
        self._i2c = I2C(id, sda=Pin(self.sda), scl=Pin(self.scl), freq=int(freq))

    def scan(self):
        return self._i2c.scan()

    def writeto(self, addr, buf, stop=True):
        return self._i2c.writeto(addr, buf, stop)

    def readfrom(self, addr, nbytes, stop=True):
        return self._i2c.readfrom(addr, nbytes, stop)

    def writeto_mem(self, addr, memaddr, buf, addrsize=8):
        return self._i2c.writeto_mem(addr, memaddr, buf, addrsize=addrsize)

    def readfrom_mem(self, addr, memaddr, nbytes, addrsize=8):
        return self._i2c.readfrom_mem(addr, memaddr, nbytes, addrsize=addrsize)


class BusUART:
    """UART on header pins (default GP21=TX, GP28=RX)."""

    def __init__(self, id=0, tx=21, rx=28, baudrate=115200, allow_system=False):
        from machine import UART, Pin

        self.tx = _check(tx, allow_system=allow_system)
        self.rx = _check(rx, allow_system=allow_system)
        self._uart = UART(id, baudrate=int(baudrate), tx=Pin(self.tx), rx=Pin(self.rx))

    def write(self, data):
        return self._uart.write(data)

    def read(self, nbytes=-1):
        return self._uart.read(nbytes)

    def any(self):
        return self._uart.any()


def i2c(sda=4, scl=5, **kw):
    return BusI2C(sda=sda, scl=scl, **kw)


def uart(tx=21, rx=28, **kw):
    return BusUART(tx=tx, rx=rx, **kw)


# tests use these names
_check_pin = _check
_SYSTEM_PINS = _SYSTEM
_AUDIO_PINS = _AUDIO

