#!/usr/bin/env python3
"""
Display module for the music player using Adafruit 2.8" TFT LCD
"""

import time
import busio
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.ili9341 as ili9341
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
import io

class MusicDisplay:
    def __init__(self):
        """
        Initialize the 2.8" TFT display
        """
        # Configuration for display
        # CS pin will be tied to GND and is always active. tying it to CE0 causes GPIO busy, im not sure why
        cs_pin = None# digitalio.DigitalInOut(board.CE0)
        dc_pin = digitalio.DigitalInOut(board.D25)  # GPIO 25
        reset_pin = digitalio.DigitalInOut(board.D24)  # GPIO 24
        
        # Setup SPI bus
        spi = busio.SPI(clock=board.SCK, MOSI=board.MOSI, MISO=board.MISO)
        
        # Create the display object
        self.display = ili9341.ILI9341(
            spi,
            cs=cs_pin,
            dc=dc_pin,
            rst=reset_pin,
            width=240,
            height=320,
            rotation=90
        )
        
        self.width = 320
        self.height = 240
            
        # Create drawing objects
        self.image = Image.new("RGB", (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)
        
        # Load fonts
        try:
            self.font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            self.font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
            self.font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except:
            # Fallback to default font
            self.font_large = ImageFont.load_default()
            self.font_medium = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
            
        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.BLUE = (0, 0, 255)
        self.GREEN = (0, 255, 0)
        self.RED = (255, 0, 0)
        
        # Clear display
        self.clear()
        
    def clear(self):
        """Clear the display"""
        self.draw.rectangle((0, 0, self.width, self.height), fill=self.BLACK)
        self.display.image(self.image)
        
    def show_splash(self):
        """Show splash screen"""
        self.clear()
        self.draw.text((self.width//2 - 60, self.height//2 - 20), 
                      "Music Box", font=self.font_large, fill=self.WHITE)
        self.draw.text((self.width//2 - 40, self.height//2 + 10), 
                      "Loading...", font=self.font_medium, fill=self.BLUE)
        self.display.image(self.image)
        
    def update_now_playing(self, filename, state="PLAYING", volume=80, 
                           current_index=0, total_tracks=0):
        """
        Update the now playing screen
        
        Args:
            filename: Current song filename
            state: Player state (PLAYING, PAUSED, STOPPED)
            volume: Current volume percentage
            current_index: Current track number
            total_tracks: Total number of tracks
        """
        self.clear()
        
        # Extract song name without path and extension
        song_name = filename.split('/')[-1].rsplit('.', 1)[0]
        
        # Truncate long names
        if len(song_name) > 25:
            song_name = song_name[:22] + "..."
            
        # Draw UI elements
        # Title bar
        self.draw.rectangle((0, 0, self.width, 30), fill=self.BLUE)
        self.draw.text((10, 5), "Now Playing", font=self.font_medium, fill=self.WHITE)
        
        # Track info
        track_info = f"Track {current_index + 1}/{total_tracks}"
        self.draw.text((self.width - 80, 7), track_info, font=self.font_small, fill=self.WHITE)
        
        # Song name
        self.draw.text((10, 50), song_name, font=self.font_medium, fill=self.WHITE)
        
        # State indicator
        state_color = self.GREEN if state == "PLAYING" else self.RED if state == "PAUSED" else self.WHITE
        state_text = "▶" if state == "PLAYING" else "⏸" if state == "PAUSED" else "■"
        self.draw.text((10, 90), state_text, font=self.font_large, fill=state_color)
        self.draw.text((40, 95), state.title(), font=self.font_medium, fill=self.WHITE)
        
        # Volume bar
        self.draw.text((10, 130), f"Volume: {volume}%", font=self.font_small, fill=self.WHITE)
        # Draw volume bar background
        self.draw.rectangle((10, 150, 310, 165), outline=self.WHITE)
        # Draw volume bar fill
        vol_width = int((volume / 100) * 300)
        self.draw.rectangle((10, 150, 10 + vol_width, 165), fill=self.GREEN)
        
        # Control hints at bottom
        self.draw.text((10, 200), "Play/Pause | Next | Prev | Volume", 
                      font=self.font_small, fill=(128, 128, 128))
        
        # Update display
        self.display.image(self.image)
        
    def show_album_art(self, mp3_file):
        """
        Extract and display album art from MP3 file
        
        Args:
            mp3_file: Path to MP3 file
        """
        try:
            audio = ID3(mp3_file)
            
            # Look for album art in APIC frames
            for tag in audio.values():
                if isinstance(tag, APIC):
                    # Load image from tag data
                    artwork = Image.open(io.BytesIO(tag.data))
                    
                    # Resize to fit display (leaving room for controls)
                    artwork = artwork.resize((160, 160), Image.LANCZOS)
                    
                    # Paste onto display image
                    self.image.paste(artwork, (self.width - 170, 40))
                    self.display.image(self.image)
                    return True
        except:
            pass
        return False