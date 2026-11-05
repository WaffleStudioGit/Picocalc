"""Intro script — edit this on-device with: edit('/apps/hello_gpio.py')"""
from gpio_hw import Servo, GPIO, Analog, list_pins
import time

print("PicoCalc UFO GPIO demo")
print(list_pins())

# Digital out on GP21
out = GPIO(21, mode=GPIO.OUT)
out.high()
time.sleep(0.2)
out.low()

# Uncomment when a servo is connected:
# s = Servo(28)
# s.write(0); time.sleep(0.5)
# s.write(90); time.sleep(0.5)
# s.write(180); time.sleep(0.5)
# s.detach()

# Uncomment for analog read on GP28:
# a = Analog(28)
# print("ADC volts:", a.read_volts())

print("done — open the editor with: edit('/apps/hello_gpio.py')")
