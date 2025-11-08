#!/usr/bin/env python3
"""Test script for GPIO buttons and encoder using gpiozero"""

from gpiozero import Button
import time
import signal
import sys

# Pin definitions
PLAY_PAUSE_PIN = 17
NEXT_PIN = 27
PREV_PIN = 22
ENCODER_A_PIN = 5
ENCODER_B_PIN = 6
ENCODER_SW_PIN = 13

# Setup all button objects with pull-ups (active-low)
buttons = {
    "Play/Pause": Button(PLAY_PAUSE_PIN, pull_up=True, bounce_time=0.01),
    "Next": Button(NEXT_PIN, pull_up=True, bounce_time=0.01),
    "Previous": Button(PREV_PIN, pull_up=True, bounce_time=0.01),
    "Encoder A": Button(ENCODER_A_PIN, pull_up=True, bounce_time=0.01),
    "Encoder B": Button(ENCODER_B_PIN, pull_up=True, bounce_time=0.01),
    "Encoder Button": Button(ENCODER_SW_PIN, pull_up=True, bounce_time=0.01)
}

# Setup callbacks
def make_callback(name):
    """Create a callback function for each button"""
    def callback():
        print(f"✓ {name} pressed!")
    return callback

for name, button in buttons.items():
    button.when_pressed = make_callback(name)
    print(f"{name:15} on GPIO {button.pin.number:2} - Press to test")

print("\nPress Ctrl+C to exit")
print("-" * 40)

def signal_handler(sig, frame):
    print("\nTest complete!")
    # gpiozero handles cleanup automatically
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

try:
    # Keep the script running
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\nTest complete!")