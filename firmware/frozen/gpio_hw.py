"""
PicoCalc UF2 firmware — GPIO, PWM, ADC, and servo helpers for the exposed header.

Safe header pins on PicoCalc (Core GPIOs header):
  GP2, GP3, GP4, GP5, GP21, GP28   (+ 3V3 / GND)

Reserved / do-not-use from user scripts by default:
  GP6/7   keyboard I2C
  GP10-15 LCD SPI
  GP16-19 SD card SPI
  GP26/27 audio PWM (opt-in via allow_audio=True)

Typical servo wiring:
  signal -> GP21 or GP28
  V+     -> external 5V (preferred) or 3V3 for tiny servos
  GND    -> shared GND with PicoCalc
"""


def _machine_parts():
    """Import machine lazily so host tests can inject mocks first."""
    try:
        import machine
    except ImportError as exc:
        raise RuntimeError("machine module not available") from exc
    return machine.Pin, machine.PWM, machine.ADC


# Pins brought out on the PicoCalc "Core GPIOs" header.
HEADER_PINS = (2, 3, 4, 5, 21, 28)

# Commonly free for hobby PWM / digital I/O.
RECOMMENDED_IO = (21, 28)

# System pins — blocked unless explicitly overridden.
_SYSTEM_PINS = frozenset(
    (
        6,
        7,  # keyboard I2C
        10,
        11,
        12,
        13,
        14,
        15,  # LCD
        16,
        17,
        18,
        19,  # SD
        20,  # often PSRAM CS on some boards
    )
)
_AUDIO_PINS = frozenset((26, 27))

# Standard hobby-servo pulse widths at 50 Hz (microseconds).
_SERVO_FREQ_HZ = 50
_SERVO_MIN_US = 500
_SERVO_MAX_US = 2500
_SERVO_PERIOD_US = 20_000  # 1/50s


def _check_pin(pin, allow_audio=False, allow_system=False):
    p = int(pin)
    if p < 0 or p > 28:
        raise ValueError("GPIO pin must be 0..28, got %s" % pin)
    if (not allow_system) and p in _SYSTEM_PINS:
        raise ValueError(
            "GP%d is reserved for PicoCalc system hardware "
            "(keyboard/LCD/SD). Use header pins %s." % (p, list(HEADER_PINS))
        )
    if (not allow_audio) and p in _AUDIO_PINS:
        raise ValueError(
            "GP%d drives onboard audio. Pass allow_audio=True to override." % p
        )
    return p


def list_pins():
    """Return a dict summarizing usable vs reserved pins."""
    return {
        "header": list(HEADER_PINS),
        "recommended": list(RECOMMENDED_IO),
        "audio": list(_AUDIO_PINS),
        "reserved_system": sorted(_SYSTEM_PINS),
    }


class GPIO:
    """Digital input/output on a PicoCalc header pin."""

    OUT = 0
    IN = 1
    IN_PULLUP = 2
    IN_PULLDOWN = 3

    def __init__(self, pin, mode=OUT, value=0, allow_audio=False, allow_system=False):
        Pin, _PWM, _ADC = _machine_parts()
        self.pin_num = _check_pin(pin, allow_audio=allow_audio, allow_system=allow_system)
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
            raise ValueError("Unknown GPIO mode")

    def high(self):
        self._pin.value(1)

    def low(self):
        self._pin.value(0)

    def toggle(self):
        self._pin.value(1 - self._pin.value())

    def value(self, v=None):
        if v is None:
            return self._pin.value()
        self._pin.value(1 if v else 0)

    def on(self):
        self.high()

    def off(self):
        self.low()


class SoftPWM:
    """PWM wrapper with duty helpers (percent / u16 / microseconds)."""

    def __init__(self, pin, freq=1000, duty_u16=0, allow_audio=False, allow_system=False):
        Pin, PWM, _ADC = _machine_parts()
        self.pin_num = _check_pin(pin, allow_audio=allow_audio, allow_system=allow_system)
        self._pwm = PWM(Pin(self.pin_num))
        self._pwm.freq(int(freq))
        self._pwm.duty_u16(int(duty_u16) & 0xFFFF)

    def freq(self, hz=None):
        if hz is None:
            return self._pwm.freq()
        self._pwm.freq(int(hz))

    def duty_u16(self, level=None):
        if level is None:
            return self._pwm.duty_u16()
        self._pwm.duty_u16(max(0, min(65535, int(level))))

    def duty_percent(self, pct=None):
        if pct is None:
            return self._pwm.duty_u16() * 100.0 / 65535.0
        pct = max(0.0, min(100.0, float(pct)))
        self._pwm.duty_u16(int(pct * 65535.0 / 100.0))

    def duty_us(self, us=None, period_us=None):
        """Set high-time in microseconds for the current PWM frequency."""
        if period_us is None:
            period_us = 1_000_000 // max(1, self._pwm.freq())
        if us is None:
            return int(self._pwm.duty_u16() * period_us / 65535.0)
        us = max(0, min(period_us, int(us)))
        self._pwm.duty_u16(int(us * 65535 / period_us))

    def deinit(self):
        try:
            self._pwm.deinit()
        except Exception:
            pass


class Servo:
    """
    Hobby servo on a PWM-capable header pin (default 50 Hz).

    angle: 0..180 degrees (or custom min_angle/max_angle)
    """

    def __init__(
        self,
        pin,
        freq=_SERVO_FREQ_HZ,
        min_us=_SERVO_MIN_US,
        max_us=_SERVO_MAX_US,
        min_angle=0,
        max_angle=180,
        allow_audio=False,
        allow_system=False,
    ):
        self.min_us = int(min_us)
        self.max_us = int(max_us)
        self.min_angle = float(min_angle)
        self.max_angle = float(max_angle)
        self._angle = self.min_angle
        self._pwm = SoftPWM(
            pin,
            freq=freq,
            duty_u16=0,
            allow_audio=allow_audio,
            allow_system=allow_system,
        )
        self.pin_num = self._pwm.pin_num

    def _us_from_angle(self, angle):
        span = self.max_angle - self.min_angle
        if span == 0:
            return self.min_us
        t = (float(angle) - self.min_angle) / span
        if t < 0:
            t = 0.0
        elif t > 1:
            t = 1.0
        return int(self.min_us + t * (self.max_us - self.min_us))

    def write_us(self, us):
        us = max(self.min_us, min(self.max_us, int(us)))
        self._pwm.duty_us(us, period_us=_SERVO_PERIOD_US)
        span_us = self.max_us - self.min_us
        if span_us:
            t = (us - self.min_us) / span_us
            self._angle = self.min_angle + t * (self.max_angle - self.min_angle)

    def write(self, angle):
        """Set servo position in degrees."""
        self._angle = float(angle)
        self.write_us(self._us_from_angle(angle))

    def read(self):
        """Last commanded angle in degrees."""
        return self._angle

    def mid(self):
        self.write((self.min_angle + self.max_angle) / 2.0)

    def min(self):
        self.write(self.min_angle)

    def max(self):
        self.write(self.max_angle)

    def detach(self):
        """Stop driving the signal (servo may go limp depending on model)."""
        self._pwm.duty_u16(0)

    def deinit(self):
        self.detach()
        self._pwm.deinit()


class Analog:
    """ADC helper. On PicoCalc, GP28 is the header ADC-capable pin (ADC2)."""

    _ADC_PINS = {26: 0, 27: 1, 28: 2, 29: 3}

    def __init__(self, pin=28, allow_audio=False, allow_system=False):
        Pin, _PWM, ADC = _machine_parts()
        self.pin_num = _check_pin(pin, allow_audio=allow_audio, allow_system=allow_system)
        if self.pin_num not in self._ADC_PINS:
            raise ValueError(
                "GP%d is not an ADC pin. Use GP26/27/28/29 (GP28 preferred on header)."
                % self.pin_num
            )
        self._adc = ADC(Pin(self.pin_num))

    def read_u16(self):
        return self._adc.read_u16()

    def read_volts(self, vref=3.3):
        return self._adc.read_u16() * float(vref) / 65535.0


def servo(pin=21, **kwargs):
    return Servo(pin, **kwargs)


def output(pin, value=0, **kwargs):
    return GPIO(pin, mode=GPIO.OUT, value=value, **kwargs)


def input_pin(pin, pull=None, **kwargs):
    if pull == "up":
        mode = GPIO.IN_PULLUP
    elif pull == "down":
        mode = GPIO.IN_PULLDOWN
    else:
        mode = GPIO.IN
    return GPIO(pin, mode=mode, **kwargs)


def pwm(pin, freq=1000, duty_percent=0, **kwargs):
    p = SoftPWM(pin, freq=freq, **kwargs)
    p.duty_percent(duty_percent)
    return p
