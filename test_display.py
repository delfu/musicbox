#!/usr/bin/env python3
"""
Simple display test without the full music player
"""

import time
import board
import busio
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.ili9341 as ili9341

def main():
    print("Initializing display...")
    
    # Setup pins
    # cs pin is tied to GND and always enabled. Connecting to CE0 causes a GPIO busy error, im not sure why
    # cs_pin = digitalio.DigitalInOut(board.CE0)
    dc_pin = digitalio.DigitalInOut(board.D25)
    reset_pin = digitalio.DigitalInOut(board.D24)
    
    # Setup SPI
    print("Setting up SPI...")
    spi = busio.SPI(clock=board.SCK, MOSI=board.MOSI, MISO=board.MISO)
    
    # Create display object
    print("Creating display object...")
    display = ili9341.ILI9341(
        spi,
        cs=None,
        dc=dc_pin,
        rst=reset_pin,
        width=240,
        height=320,
        rotation=90
    )
    
    print("Display initialized!")
    
    # Create image
    image = Image.new("RGB", (320, 240))
    draw = ImageDraw.Draw(image)
    
    # Test patterns
    print("Drawing test pattern...")
    
    # Fill with black
    draw.rectangle((0, 0, 320, 240), fill=(0, 0, 0))
    
    # Draw colored rectangles
    draw.rectangle((10, 10, 60, 60), fill=(255, 0, 0))  # Red
    draw.rectangle((70, 10, 120, 60), fill=(0, 255, 0))  # Green  
    draw.rectangle((130, 10, 180, 60), fill=(0, 0, 255))  # Blue
    draw.rectangle((190, 10, 240, 60), fill=(255, 255, 255))  # White
    
    # Draw text
    draw.text((10, 80), "TFT Display Test", fill=(255, 255, 255))
    draw.text((10, 100), "SPI Connection OK!", fill=(0, 255, 0))
    draw.text((10, 120), f"Time: {time.strftime('%H:%M:%S')}", fill=(255, 255, 0))
    
    # Display the image
    display.image(image)
    print("Test pattern displayed!")
    
    # Cycle through colors
    colors = [
        (255, 0, 0),    # Red
        (0, 255, 0),    # Green
        (0, 0, 255),    # Blue
        (255, 255, 0),  # Yellow
        (255, 0, 255),  # Magenta
        (0, 255, 255),  # Cyan
        (255, 255, 255) # White
    ]
    
    print("Starting color cycle (Ctrl+C to stop)...")
    try:
        while True:
            for color in colors:
                draw.rectangle((0, 0, 320, 240), fill=color)
                draw.text((10, 110), f"Color: {color}", fill=(0, 0, 0) if sum(color) > 384 else (255, 255, 255))
                display.image(image)
                time.sleep(1)
    except KeyboardInterrupt:
        print("\nTest complete!")
        # Clear to black
        draw.rectangle((0, 0, 320, 240), fill=(0, 0, 0))
        draw.text((100, 110), "Test Complete", fill=(255, 255, 255))
        display.image(image)

if __name__ == "__main__":
    main()