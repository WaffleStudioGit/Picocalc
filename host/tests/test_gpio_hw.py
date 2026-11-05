"""Host tests for gpio_hw against mocked machine.Pin / PWM / ADC."""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from host.harness import install_mocks, load_gpio_hw  # noqa: E402


class PinSafetyTests(unittest.TestCase):
    def setUp(self):
        self.gpio = load_gpio_hw()

    def test_header_pins_listed(self):
        info = self.gpio.list_pins()
        for p in (2, 3, 4, 5, 21, 28):
            self.assertIn(p, info["header"])
        self.assertEqual(info["recommended"], [21, 28])

    def test_rejects_out_of_range(self):
        with self.assertRaises(ValueError):
            self.gpio._check_pin(-1)
        with self.assertRaises(ValueError):
            self.gpio._check_pin(29)

    def test_rejects_keyboard_lcd_sd(self):
        for pin in (6, 7, 10, 13, 15, 16, 19, 20):
            with self.assertRaises(ValueError, msg="pin %s" % pin):
                self.gpio._check_pin(pin)

    def test_rejects_audio_unless_allowed(self):
        with self.assertRaises(ValueError):
            self.gpio._check_pin(26)
        self.assertEqual(self.gpio._check_pin(26, allow_audio=True), 26)

    def test_system_override(self):
        self.assertEqual(self.gpio._check_pin(6, allow_system=True), 6)


class GPIOTests(unittest.TestCase):
    def setUp(self):
        self.gpio = load_gpio_hw()
        self.machine = install_mocks(reset_hardware=True)
        # Reload so constructors see fresh registry after reset
        self.gpio = load_gpio_hw()
        self.machine = sys.modules["machine"]

    def test_output_high_low_toggle(self):
        g = self.gpio.GPIO(21, mode=self.gpio.GPIO.OUT, value=0)
        self.assertEqual(g.value(), 0)
        g.high()
        self.assertEqual(g.value(), 1)
        g.low()
        self.assertEqual(g.value(), 0)
        g.toggle()
        self.assertEqual(g.value(), 1)
        g.on()
        g.off()
        self.assertEqual(g.value(), 0)
        self.assertIn(21, self.machine.Pin.registry)

    def test_output_helper(self):
        g = self.gpio.output(28, value=1)
        self.assertEqual(g.value(), 1)

    def test_input_pull_modes(self):
        up = self.gpio.input_pin(21, pull="up")
        down = self.gpio.input_pin(28, pull="down")
        plain = self.gpio.input_pin(2)
        self.assertEqual(up._mode, self.gpio.GPIO.IN_PULLUP)
        self.assertEqual(down._mode, self.gpio.GPIO.IN_PULLDOWN)
        self.assertEqual(plain._mode, self.gpio.GPIO.IN)

    def test_blocks_reserved_on_construct(self):
        with self.assertRaises(ValueError):
            self.gpio.GPIO(6, mode=self.gpio.GPIO.OUT)


class PWMTests(unittest.TestCase):
    def setUp(self):
        self.gpio = load_gpio_hw()
        self.machine = sys.modules["machine"]

    def test_duty_percent_roundtrip(self):
        p = self.gpio.SoftPWM(21, freq=1000)
        p.duty_percent(50)
        self.assertAlmostEqual(p.duty_percent(), 50.0, delta=0.01)
        self.assertEqual(p.freq(), 1000)

    def test_duty_u16_clamped(self):
        p = self.gpio.SoftPWM(21)
        p.duty_u16(999999)
        self.assertEqual(p.duty_u16(), 65535)
        p.duty_u16(-10)
        self.assertEqual(p.duty_u16(), 0)

    def test_duty_us(self):
        p = self.gpio.SoftPWM(21, freq=50)
        p.duty_us(1500, period_us=20_000)
        # 1500/20000 * 65535 ≈ 4915
        self.assertAlmostEqual(p.duty_u16(), int(1500 * 65535 / 20000), delta=1)
        self.assertAlmostEqual(p.duty_us(period_us=20_000), 1500, delta=1)

    def test_pwm_helper(self):
        p = self.gpio.pwm(21, freq=500, duty_percent=25)
        self.assertEqual(p.freq(), 500)
        self.assertAlmostEqual(p.duty_percent(), 25.0, delta=0.02)

    def test_deinit(self):
        p = self.gpio.SoftPWM(21)
        p.duty_percent(10)
        p.deinit()
        self.assertTrue(self.machine.PWM.registry[-1].deinitialized)


class ServoTests(unittest.TestCase):
    def setUp(self):
        self.gpio = load_gpio_hw()
        self.machine = sys.modules["machine"]

    def test_angle_extremes_and_mid(self):
        s = self.gpio.Servo(21)
        s.write(0)
        self.assertEqual(s.read(), 0)
        us0 = s._pwm.duty_us(period_us=20_000)
        self.assertAlmostEqual(us0, 500, delta=2)

        s.write(180)
        us180 = s._pwm.duty_us(period_us=20_000)
        self.assertAlmostEqual(us180, 2500, delta=2)

        s.mid()
        self.assertAlmostEqual(s.read(), 90.0, delta=0.01)
        us90 = s._pwm.duty_us(period_us=20_000)
        self.assertAlmostEqual(us90, 1500, delta=2)

    def test_clamp_angle(self):
        s = self.gpio.Servo(21)
        s.write(-40)
        self.assertAlmostEqual(s._pwm.duty_us(period_us=20_000), 500, delta=2)
        s.write(999)
        self.assertAlmostEqual(s._pwm.duty_us(period_us=20_000), 2500, delta=2)

    def test_write_us_updates_angle(self):
        s = self.gpio.Servo(21)
        s.write_us(1500)
        self.assertAlmostEqual(s.read(), 90.0, delta=0.5)

    def test_min_max_helpers(self):
        s = self.gpio.Servo(28)
        s.min()
        self.assertEqual(s.read(), 0)
        s.max()
        self.assertEqual(s.read(), 180)

    def test_detach_stops_pwm(self):
        s = self.gpio.Servo(21)
        s.write(90)
        s.detach()
        self.assertEqual(s._pwm.duty_u16(), 0)

    def test_servo_helper_default_pin(self):
        s = self.gpio.servo()
        self.assertEqual(s.pin_num, 21)

    def test_linear_us_mapping(self):
        s = self.gpio.Servo(21)
        for angle in (0, 45, 90, 135, 180):
            expected = 500 + (angle / 180.0) * 2000
            self.assertEqual(s._us_from_angle(angle), int(expected))


class AnalogTests(unittest.TestCase):
    def setUp(self):
        self.gpio = load_gpio_hw()
        self.machine = sys.modules["machine"]

    def test_read_volts(self):
        a = self.gpio.Analog(28)
        # default mock raw = 32768
        volts = a.read_volts(vref=3.3)
        self.assertTrue(math.isclose(volts, 32768 * 3.3 / 65535, rel_tol=1e-6))
        self.machine.ADC.registry[-1].set_raw(65535)
        self.assertAlmostEqual(a.read_volts(), 3.3, places=4)

    def test_rejects_non_adc_header_pin(self):
        with self.assertRaises(ValueError):
            self.gpio.Analog(21)

    def test_audio_adc_requires_allow(self):
        with self.assertRaises(ValueError):
            self.gpio.Analog(26)
        a = self.gpio.Analog(26, allow_audio=True)
        self.assertEqual(a.pin_num, 26)


if __name__ == "__main__":
    unittest.main()
