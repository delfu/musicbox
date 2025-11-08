#!/usr/bin/env python3
"""
Standalone test script for rotary encoder using gpiozero
Tests the Adafruit 377 encoder with proper debouncing
"""

from gpiozero import RotaryEncoder, Button
import time
import sys
import signal

# Pin definitions
ENCODER_A_PIN = 5
ENCODER_B_PIN = 6
ENCODER_SW_PIN = 13

class EncoderTest:
    def __init__(self):
        self.position = 0  # Track encoder position
        
        # Setup rotary encoder with gpiozero
        # gpiozero handles all the quadrature decoding automatically
        self.encoder = RotaryEncoder(
            ENCODER_A_PIN, 
            ENCODER_B_PIN, 
            bounce_time=0.001,  # 1ms debounce
            max_steps=1000      # Allow position to grow
        )
        
        # Setup button
        self.button = Button(ENCODER_SW_PIN, pull_up=True, bounce_time=0.2)
        
        # Setup callbacks
        self.encoder.when_rotated_clockwise = self._rotated_cw
        self.encoder.when_rotated_counter_clockwise = self._rotated_ccw
        self.button.when_pressed = self._button_pressed
        
        print("=" * 50)
        print("Rotary Encoder Test (gpiozero)")
        print("=" * 50)
        print(f"Encoder A: GPIO {ENCODER_A_PIN}")
        print(f"Encoder B: GPIO {ENCODER_B_PIN}")
        print(f"Encoder Button: GPIO {ENCODER_SW_PIN}")
        print()
        print("Rotate the encoder and watch the position change")
        print("Press the encoder button to reset position")
        print("Press Ctrl+C to exit")
        print("=" * 50)
        print(f"Position: {self.position}")
        
    def _rotated_cw(self):
        """Called when encoder rotates clockwise"""
        self.position += 1
        print(f"Position: {self.position:4d}  CW ➡")
    
    def _rotated_ccw(self):
        """Called when encoder rotates counter-clockwise"""
        self.position -= 1
        print(f"Position: {self.position:4d}  ⬅ CCW")
    
    def _button_pressed(self):
        """Called when encoder button is pressed"""
        print("\n[Button pressed - Reset position to 0]\n")
        self.position = 0
        print(f"Position: {self.position}")
    
    def run(self):
        """Main loop - just wait for events"""
        def signal_handler(sig, frame):
            print("\n\nTest complete!")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        try:
            while True:
                time.sleep(0.1)  # Low CPU usage, just keeping script alive
        except KeyboardInterrupt:
            print("\n\nTest complete!")


if __name__ == "__main__":
    print("\nInitial setup:")
    print("  Using gpiozero RotaryEncoder - automatic quadrature decoding")
    print("  Pins configured with internal pull-ups")
    print()
    
    time.sleep(1)
    
    # Run the test
    test = EncoderTest()
    test.run()