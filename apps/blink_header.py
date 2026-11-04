"""Blink an LED on GP28 (or any header output pin)."""
from gpio_hw import GPIO
import time

led = GPIO(28, mode=GPIO.OUT)
try:
    while True:
        led.toggle()
        time.sleep(0.25)
except KeyboardInterrupt:
    led.low()
