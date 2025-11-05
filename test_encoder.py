#!/usr/bin/env python3
"""
Standalone test script for rotary encoder using interrupts
Tests the Adafruit 377 encoder with proper debouncing
"""

import RPi.GPIO as GPIO
import time
import sys

# Pin definitions
ENCODER_A_PIN = 5
ENCODER_B_PIN = 6
ENCODER_SW_PIN = 13

class EncoderTest:
    def __init__(self):
        self.position = 0  # Track encoder position
        self.last_encoder_time = 0
        self.debounce_time = 0.010  # 10ms debounce (adjustable)
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Setup encoder pins with pull-ups (encoder is active-low)
        GPIO.setup(ENCODER_A_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(ENCODER_B_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(ENCODER_SW_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # Add interrupt on encoder A falling edge
        GPIO.add_event_detect(
            ENCODER_A_PIN,
            GPIO.FALLING,
            callback=self._encoder_callback,
            bouncetime=1  # Minimal hardware debounce
        )
        
        # Add interrupt for button press
        GPIO.add_event_detect(
            ENCODER_SW_PIN,
            GPIO.FALLING,
            callback=self._button_callback,
            bouncetime=200
        )
        
        print("=" * 50)
        print("Rotary Encoder Interrupt Test")
        print("=" * 50)
        print(f"Encoder A: GPIO {ENCODER_A_PIN}")
        print(f"Encoder B: GPIO {ENCODER_B_PIN}")
        print(f"Encoder Button: GPIO {ENCODER_SW_PIN}")
        print(f"Debounce time: {self.debounce_time*1000:.1f}ms")
        print()
        print("Rotate the encoder and watch the position change")
        print("Press the encoder button to reset position")
        print("Press Ctrl+C to exit")
        print("=" * 50)
        print(f"Position: {self.position}")
        
    def _encoder_callback(self, channel):
        """Called when encoder pin A falls (interrupt-driven)"""
        current_time = time.time()
        
        # Time-based debounce
        if current_time - self.last_encoder_time < self.debounce_time:
            return
        
        self.last_encoder_time = current_time
        
        # Read pin B to determine direction
        b_state = GPIO.input(ENCODER_B_PIN)
        
        if b_state == 1:
            # B is still high when A falls = Clockwise
            self.position += 1
            direction = "CW ➡"
        else:
            # B already low when A falls = Counter-clockwise
            self.position -= 1
            direction = "⬅ CCW"
        
        print(f"Position: {self.position:4d}  {direction}")
    
    def _button_callback(self, channel):
        """Called when encoder button is pressed"""
        print("\n[Button pressed - Reset position to 0]\n")
        self.position = 0
        print(f"Position: {self.position}")
    
    def run(self):
        """Main loop - just wait for interrupts"""
        try:
            while True:
                time.sleep(0.1)  # Low CPU usage, just keeping script alive
        except KeyboardInterrupt:
            print("\n\nTest complete!")
            self.cleanup()
    
    def cleanup(self):
        """Clean up GPIO"""
        GPIO.cleanup()
        sys.exit(0)


if __name__ == "__main__":
    # Check initial pin states
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(ENCODER_A_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(ENCODER_B_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    print("\nInitial pin states:")
    print(f"  A (GPIO {ENCODER_A_PIN}): {GPIO.input(ENCODER_A_PIN)} (should be 1)")
    print(f"  B (GPIO {ENCODER_B_PIN}): {GPIO.input(ENCODER_B_PIN)} (should be 1)")
    
    if GPIO.input(ENCODER_A_PIN) == 0 or GPIO.input(ENCODER_B_PIN) == 0:
        print("\n⚠ WARNING: One or both pins read LOW at rest!")
        print("  Check your wiring - encoder common should go to GND")
        print("  Continuing anyway...\n")
    
    time.sleep(1)
    GPIO.cleanup()
    
    # Run the test
    test = EncoderTest()
    test.run()