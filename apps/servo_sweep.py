"""Sweep a hobby servo on the PicoCalc header (default GP21)."""
from gpio_hw import Servo, list_pins
import time

print("Pins:", list_pins())
s = Servo(21)  # change to 28 if you wired that pin
try:
    while True:
        for angle in range(0, 181, 5):
            s.write(angle)
            time.sleep(0.02)
        for angle in range(180, -1, -5):
            s.write(angle)
            time.sleep(0.02)
except KeyboardInterrupt:
    s.mid()
    s.detach()
    print("stopped")
