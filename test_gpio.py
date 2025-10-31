#!/usr/bin/env python3
"""Test script for GPIO buttons and encoder"""

import RPi.GPIO as GPIO
import time

# Pin definitions
PLAY_PAUSE_PIN = 17
NEXT_PIN = 27
PREV_PIN = 22
ENCODER_A_PIN = 5
ENCODER_B_PIN = 6
ENCODER_SW_PIN = 13

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Setup all pins
pins = {
    "Play/Pause": PLAY_PAUSE_PIN,
    "Next": NEXT_PIN,
    "Previous": PREV_PIN,
    "Encoder A": ENCODER_A_PIN,
    "Encoder B": ENCODER_B_PIN,
    "Encoder Button": ENCODER_SW_PIN
}

for name, pin in pins.items():
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    print(f"{name:15} on GPIO {pin:2} - Press to test")

print("\nPress Ctrl+C to exit")
print("-" * 40)

last_states = {pin: GPIO.input(pin) for pin in pins.values()}

try:
    while True:
        for name, pin in pins.items():
            current = GPIO.input(pin)
            if current != last_states[pin]:
                if current == 0:
                    print(f"✓ {name} pressed!")
                last_states[pin] = current
        time.sleep(0.01)
except KeyboardInterrupt:
    print("\nTest complete!")
finally:
    GPIO.cleanup()